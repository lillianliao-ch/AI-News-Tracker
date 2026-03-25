#!/usr/bin/env python3
"""
腾讯 AI Lab 核心人物共作者挖掘脚本
=====================================
通过 Semantic Scholar API，抓取文章中提到的腾讯 AI Lab
核心人物的论文共作者，找出其一二度人脉网络中的 AI 人才。

目标人物：俞栋(Dong Yu)、薄列峰(Liefeng Bo)、
          张正友(Zhengyou Zhang)、张潼(Tong Zhang)

用法:
    # 完整运行（挖掘 + 去重 + 导入）
    python3 tencent_coauthor_miner.py

    # 只挖掘，不导入（用于预览）
    python3 tencent_coauthor_miner.py --dry-run

    # 指定某个人
    python3 tencent_coauthor_miner.py --targets "Dong Yu,Liefeng Bo"
"""

import os
import sys
import json
import time
import random
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple

import requests

# ============================================================
# 路径配置
# ============================================================
SCRIPT_DIR   = Path(__file__).parent
REPO_ROOT    = SCRIPT_DIR.parent.parent
DB_PATH      = REPO_ROOT / "personal-ai-headhunter" / "data" / "headhunter_dev.db"
OUTPUT_DIR   = SCRIPT_DIR.parent / "data" / "tencent_coauthor"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Semantic Scholar API
# ============================================================
S2_BASE = "https://api.semanticscholar.org/graph/v1"

AUTHOR_FIELDS  = "name,affiliations,hIndex,citationCount,paperCount,homepage,externalIds"
PAPER_FIELDS   = "title,year,venue,authors"

# ============================================================
# 目标人物（腾讯 AI Lab 核心）
# ============================================================
# s2_id 如果已知可直接填写，跳过搜索步骤（减少 API 调用）
# 通过 https://www.semanticscholar.org/author/ 手工确认后填入
TARGETS = [
    {
        "cn_name": "俞栋",
        "name": "Dong Yu",
        "affiliation_hint": "Tencent",
        "s2_id": "144580027",      # Dong Yu @ Tencent/MSR Speech (h-index=83)
        "paper_year_range": (2015, 2026),
        "note": "腾讯 AI Lab 二把手，语音方向，近期离职回西雅图",
    },
    {
        "cn_name": "薄列峰",
        "name": "Liefeng Bo",
        "affiliation_hint": "Tencent",
        "s2_id": "2275373104",     # Liefeng Bo (h-index=11, citations=588)
        "paper_year_range": (2018, 2026),
        "note": "TEG 多模态部门负责人，曾任 Amazon AI 首席科学家",
    },
    {
        "cn_name": "张正友",
        "name": "Zhengyou Zhang",
        "affiliation_hint": "Tencent",
        "s2_id": "51064498",       # Zhengyou Zhang (h-index=67)
        "paper_year_range": (2014, 2026),
        "note": "腾讯 AI Lab 前负责人，相机标定算法发明者",
    },
    {
        "cn_name": "张潼",
        "name": "Tong Zhang",
        "affiliation_hint": "Tencent",
        "s2_id": None,             # 待运行时自动搜索（同名太多）
        "paper_year_range": (2018, 2026),
        "note": "腾讯 AI Lab 历任负责人，现港科大教授",
    },
]

# ============================================================
# 工具函数
# ============================================================
def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def s2_get(endpoint: str, params: Dict = None, retries: int = 4) -> Optional[Dict]:
    """Semantic Scholar 请求，自动限流 & 重试"""
    url = f"{S2_BASE}/{endpoint}"
    headers = {"User-Agent": "TencentCoauthorMiner/1.0"}
    api_key = os.getenv("S2_API_KEY", "")
    if api_key:
        headers["x-api-key"] = api_key

    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 30)) + random.uniform(2, 8)
                log(f"  ⏳ 限流，等待 {wait:.0f}s…")
                time.sleep(wait)
            elif resp.status_code == 404:
                return None
            else:
                log(f"  ⚠️  HTTP {resp.status_code} {url}")
                time.sleep(3)
        except Exception as e:
            log(f"  ❌ 网络异常: {e}")
            time.sleep(5 * (attempt + 1))
    return None


def rate_sleep(has_key: bool = False):
    """无 key: 1 QPS；有 key: 最多 10 QPS"""
    if has_key:
        time.sleep(random.uniform(0.15, 0.3))
    else:
        time.sleep(random.uniform(1.1, 1.8))


# ============================================================
# Step 1: 解析目标人物的 Semantic Scholar 作者 ID
# ============================================================
def resolve_author_id(target: Dict) -> Optional[str]:
    """通过姓名搜索找到最匹配的 s2_id"""
    if target.get("s2_id"):
        return target["s2_id"]

    name = target["name"]
    hint = target.get("affiliation_hint", "")
    log(f"  🔍 搜索作者: {name} ({target['cn_name']})")

    result = s2_get("author/search", {
        "query": name,
        "fields": AUTHOR_FIELDS,
        "limit": 5
    })
    rate_sleep()

    if not result or not result.get("data"):
        log(f"  ❌ 未找到 {name}")
        return None

    candidates = result["data"]
    best = None
    best_score = -1

    for c in candidates:
        score = 0.0
        c_name = (c.get("name") or "").lower()
        if c_name == name.lower():
            score += 3.0
        elif name.lower() in c_name:
            score += 1.5

        affils = " ".join(c.get("affiliations") or []).lower()
        if hint.lower() in affils:
            score += 2.0

        score += min((c.get("hIndex") or 0) / 30.0, 2.0)

        if score > best_score:
            best_score = score
            best = c

    if best and best_score >= 1.0:
        log(f"  ✅ 匹配: {best.get('name')} | h-index={best.get('hIndex')} | "
            f"机构={best.get('affiliations', [])[:1]}")
        return best["authorId"]

    log(f"  ⚠️  {name} 未找到高置信度匹配（最高分={best_score:.1f}）")
    return None


# ============================================================
# Step 2: 拉取某作者的所有论文 & 共作者
# ============================================================
def fetch_papers_and_coauthors(
    author_id: str,
    year_range: Tuple[int, int],
    cache_path: Path
) -> List[Dict]:
    """
    返回论文列表，每篇带共作者信息。
    支持断点缓存。
    """
    cache_key = f"papers::{author_id}"

    # 读缓存
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
        except Exception:
            pass

    if cache_key in cache:
        log(f"  📦 命中缓存（{len(cache[cache_key])} 篇论文）")
        return cache[cache_key]

    papers = []
    offset = 0
    limit  = 100
    y_min, y_max = year_range

    log(f"  📄 拉取论文 authorId={author_id}，年份 {y_min}-{y_max}…")

    while True:
        result = s2_get(f"author/{author_id}/papers", {
            "fields": PAPER_FIELDS,
            "limit": limit,
            "offset": offset,
        })
        rate_sleep()

        if not result:
            break

        batch = result.get("data", [])
        if not batch:
            break

        for paper in batch:
            year = paper.get("year") or 0
            if y_min <= year <= y_max:
                papers.append(paper)

        offset += limit
        if offset >= result.get("total", 0):
            break

    log(f"  → 获得 {len(papers)} 篇（{y_min}-{y_max}）")

    cache[cache_key] = papers
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    return papers


# ============================================================
# Step 3: 从论文中提取共作者并评级
# ============================================================
def extract_coauthors(
    papers: List[Dict],
    target_author_id: str,
    tencent_only: bool = False,
) -> Dict[str, Dict]:
    """
    返回 {authorId: coauthor_record}
    """
    coauthors: Dict[str, Dict] = {}

    for paper in papers:
        paper_title = paper.get("title", "")
        paper_year  = paper.get("year", 0)
        paper_venue = paper.get("venue", "")

        for author in paper.get("authors", []):
            aid = author.get("authorId")
            if not aid or aid == target_author_id:
                continue

            affils = " ".join(author.get("affiliations") or []).lower()
            if tencent_only and "tencent" not in affils:
                continue

            if aid not in coauthors:
                coauthors[aid] = {
                    "s2_id":          aid,
                    "name":           author.get("name", ""),
                    "affiliations":   author.get("affiliations") or [],
                    "h_index":        0,  # 待后续查询
                    "citation_count": 0,  # 待后续查询
                    "homepage":       "",
                    "external_ids":   {},
                    "coauthor_papers": [],
                }

            coauthors[aid]["coauthor_papers"].append({
                "title": paper_title,
                "year":  paper_year,
                "venue": paper_venue,
            })

    return coauthors


def enrich_coauthors_batch(
    coauthors: Dict[str, Dict],
    min_papers: int = 3,
    cache_path: Path = None
) -> Dict[str, Dict]:
    """
    批量查询共作者的详细学术信息（h-index, citations 等）
    只查询合作论文数 >= min_papers 的共作者（减少 API 调用）
    """
    # 读缓存
    cache = {}
    if cache_path and cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
        except Exception:
            pass

    # 筛选需要查询的共作者
    to_query = [
        (aid, rec) for aid, rec in coauthors.items()
        if len(rec["coauthor_papers"]) >= min_papers
    ]

    log(f"\n🔬 批量查询共作者详情: {len(to_query)}/{len(coauthors)} 人（≥{min_papers}篇合作论文）")

    enriched_count = 0
    for i, (aid, rec) in enumerate(to_query):
        cache_key = f"author::{aid}"

        # 检查缓存
        if cache_key in cache:
            cached = cache[cache_key]
            rec["h_index"] = cached.get("h_index", 0)
            rec["citation_count"] = cached.get("citation_count", 0)
            rec["homepage"] = cached.get("homepage", "")
            rec["external_ids"] = cached.get("external_ids", {})
            rec["affiliations"] = cached.get("affiliations", rec["affiliations"])
            enriched_count += 1
            continue

        if i > 0 and i % 20 == 0:
            log(f"  进度: {i}/{len(to_query)}...")

        # 查询 S2
        result = s2_get(f"author/{aid}", {"fields": AUTHOR_FIELDS})
        rate_sleep(has_key=bool(os.getenv("S2_API_KEY")))

        if result:
            rec["h_index"] = result.get("hIndex") or 0
            rec["citation_count"] = result.get("citationCount") or 0
            rec["homepage"] = result.get("homepage") or ""
            rec["external_ids"] = result.get("externalIds") or {}
            rec["affiliations"] = result.get("affiliations") or rec["affiliations"]

            # 写缓存
            cache[cache_key] = {
                "h_index": rec["h_index"],
                "citation_count": rec["citation_count"],
                "homepage": rec["homepage"],
                "external_ids": rec["external_ids"],
                "affiliations": rec["affiliations"],
            }
            enriched_count += 1

            # 定期落盘
            if cache_path and i % 50 == 0:
                cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2))

    # 最终落盘
    if cache_path and enriched_count > 0:
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2))

    log(f"  ✅ 完成: {enriched_count} 人已补充学术信息")
    return coauthors


# ============================================================
# Step 4: 与现有 DB 去重
# ============================================================
def load_existing_names(db_path: Path) -> Set[str]:
    """返回已有候选人名字集合（小写）"""
    conn = sqlite3.connect(str(db_path))
    cur  = conn.cursor()
    cur.execute("SELECT name FROM candidates")
    names = {row[0].strip().lower() for row in cur.fetchall() if row[0]}
    conn.close()
    return names


def load_existing_s2_ids(db_path: Path) -> Set[str]:
    """返回已有候选人的 s2_id 集合（存在 structured_tags 里）"""
    conn = sqlite3.connect(str(db_path))
    cur  = conn.cursor()
    cur.execute("SELECT structured_tags FROM candidates WHERE structured_tags IS NOT NULL")
    ids = set()
    for (tags_str,) in cur.fetchall():
        try:
            tags = json.loads(tags_str)
            sid = tags.get("s2_id")
            if sid:
                ids.add(str(sid))
        except Exception:
            pass
    conn.close()
    return ids


# ============================================================
# Step 5: 评级 & 输出
# ============================================================
TOP_VENUES = {
    "NeurIPS", "ICML", "ICLR", "CVPR", "ECCV", "ICCV",
    "ACL", "EMNLP", "NAACL", "AAAI", "IJCAI", "INTERSPEECH",
    "ICASSP", "KDD", "WWW", "SIGIR", "ICDM", "MLSys",
}

def score_tier(record: Dict) -> str:
    h     = record.get("h_index", 0) or 0
    cites = record.get("citation_count", 0) or 0
    top   = sum(
        1 for p in record.get("coauthor_papers", [])
        if any(v in (p.get("venue") or "") for v in TOP_VENUES)
    )
    if h >= 30 or cites >= 10000 or top >= 10:
        return "S"
    elif h >= 20 or cites >= 5000 or top >= 5:
        return "A+"
    elif h >= 10 or cites >= 1000 or top >= 2:
        return "A"
    elif h >= 5 or cites >= 200 or top >= 1:
        return "B"
    else:
        return "C"


def build_import_record(record: Dict, source_target: str) -> Dict:
    """转换为猎头系统 candidates 表的导入格式"""
    tier     = score_tier(record)
    papers   = record.get("coauthor_papers", [])
    h        = record.get("h_index", 0)
    cites    = record.get("citation_count", 0)
    affils   = record.get("affiliations", [])
    homepage = record.get("homepage", "")

    # 从 externalIds 提取 GitHub / ORCID / DBLP
    ext       = record.get("external_ids", {})
    github    = None
    if homepage and "github.com" in homepage:
        github = homepage

    # 构建 notes
    notes_parts = [
        f"【来源】腾讯AI Lab共作者挖掘 | 关联人物: {source_target}",
        f"【学术】h-index={h} | 引用={cites} | 共同论文={len(papers)}篇",
    ]
    if affils:
        notes_parts.append(f"【机构】{', '.join(affils[:2])}")
    if papers:
        notes_parts.append(f"【合作论文】")
        for p in papers[:5]:
            notes_parts.append(f"  · {p['title']} ({p.get('venue','?')} {p.get('year','')})")
        if len(papers) > 5:
            notes_parts.append(f"  …另有 {len(papers)-5} 篇")

    structured_tags = {
        "academic_tier":    tier,
        "h_index":          h,
        "citation_count":   cites,
        "paper_count":      len(papers),
        "s2_id":            record.get("s2_id"),
        "source_target":    source_target,
        "conferences": list({
            p.get("venue", "") for p in papers
            if p.get("venue") and any(v in p["venue"] for v in TOP_VENUES)
        })[:10],
        "nationality_guess": "chinese",   # 通过 Tencent 共作者路径挖掘，大概率华人
    }

    return {
        "name":            record.get("name", ""),
        "current_company": (affils[0] if affils else ""),
        "current_title":   "Researcher",
        "talent_tier":     tier,
        "pipeline_stage":  "new",
        "source":          "academic",
        "source_file":     f"tencent_coauthor_{source_target.replace(' ','_')}",
        "personal_website": homepage or None,
        "github_url":      github,
        "linkedin_url":    None,
        "email":           None,
        "structured_tags": json.dumps(structured_tags, ensure_ascii=False),
        "ai_summary":      None,
        "notes":           "\n".join(notes_parts),
    }


# ============================================================
# Step 6: 写入数据库
# ============================================================
def import_to_db(records: List[Dict], db_path: Path, dry_run: bool = False) -> int:
    """批量插入新候选人，跳过已有的（按 name 去重）"""
    existing_names  = load_existing_names(db_path)
    existing_s2_ids = load_existing_s2_ids(db_path)

    new_records = []
    skipped = 0

    for r in records:
        name_lower = r["name"].strip().lower()
        s2_id = json.loads(r["structured_tags"]).get("s2_id", "")

        if name_lower in existing_names:
            skipped += 1
            continue
        if s2_id and str(s2_id) in existing_s2_ids:
            skipped += 1
            continue
        if not r["name"].strip():
            skipped += 1
            continue

        new_records.append(r)

    log(f"  📊 去重结果: {len(new_records)} 条新候选人，{skipped} 条已存在跳过")

    if dry_run:
        log(f"  🔍 Dry-run 模式：不写入数据库")
        return len(new_records)

    if not new_records:
        return 0

    conn = sqlite3.connect(str(db_path))
    cur  = conn.cursor()
    now  = datetime.now().isoformat()

    insert_sql = """
        INSERT INTO candidates (
            name, current_company, current_title, talent_tier, pipeline_stage,
            source, source_file, personal_website, github_url, linkedin_url,
            email, structured_tags, ai_summary, created_at, updated_at
        ) VALUES (
            :name, :current_company, :current_title, :talent_tier, :pipeline_stage,
            :source, :source_file, :personal_website, :github_url, :linkedin_url,
            :email, :structured_tags, :ai_summary, :created_at, :updated_at
        )
    """

    inserted = 0
    for r in new_records:
        r["created_at"] = now
        r["updated_at"] = now
        try:
            cur.execute(insert_sql, r)
            inserted += 1
        except sqlite3.IntegrityError as e:
            log(f"  ⚠️  插入失败 {r['name']}: {e}")

    conn.commit()
    conn.close()
    log(f"  ✅ 成功写入 {inserted} 条新候选人")
    return inserted


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="腾讯 AI Lab 共作者挖掘")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入数据库")
    parser.add_argument("--targets", type=str, default="",
                        help="逗号分隔的目标英文名，如 'Dong Yu,Liefeng Bo'；默认全部")
    parser.add_argument("--tencent-only", action="store_true",
                        help="只保留有 Tencent 机构标注的共作者（更精准但数量少）")
    parser.add_argument("--min-tier", type=str, default="B",
                        choices=["S", "A+", "A", "B", "C"],
                        help="最低导入级别（默认 B）")
    args = parser.parse_args()

    tier_order = {"S": 0, "A+": 1, "A": 2, "B": 3, "C": 4}
    min_tier_val = tier_order[args.min_tier]

    # 过滤目标
    targets = TARGETS
    if args.targets:
        wanted = {n.strip().lower() for n in args.targets.split(",")}
        targets = [t for t in TARGETS if t["name"].lower() in wanted]
        if not targets:
            log(f"❌ 未匹配任何目标: {args.targets}")
            return

    has_api_key = bool(os.getenv("S2_API_KEY"))
    log(f"🚀 开始腾讯 AI Lab 共作者挖掘")
    log(f"   目标人物: {', '.join(t['cn_name'] for t in targets)}")
    log(f"   API Key: {'有' if has_api_key else '无（1 QPS 限速）'}")
    log(f"   仅腾讯共作者: {args.tencent_only}")
    log(f"   最低入库级别: {args.min_tier}")
    log(f"   写入数据库: {'否（dry-run）' if args.dry_run else '是'}")

    paper_cache_path = OUTPUT_DIR / "s2_paper_cache.json"
    author_cache_path = OUTPUT_DIR / "s2_author_cache.json"

    # 汇总所有共作者
    all_coauthors: Dict[str, Dict] = {}
    coauthor_sources: Dict[str, List[str]] = {}   # s2_id -> [来源人名]

    for target in targets:
        log(f"\n{'='*50}")
        log(f"🎯 处理: {target['cn_name']} ({target['name']})")
        log(f"   备注: {target['note']}")

        # 1. 解析 author ID
        author_id = resolve_author_id(target)
        if not author_id:
            log(f"  ⛔ 跳过 {target['name']}（无法找到 S2 ID）")
            continue

        # 2. 拉取论文
        papers = fetch_papers_and_coauthors(
            author_id,
            target["paper_year_range"],
            paper_cache_path,
        )

        if not papers:
            log(f"  ⚠️  {target['name']} 无论文数据")
            continue

        # 3. 提取共作者
        coauthors = extract_coauthors(
            papers, author_id, tencent_only=args.tencent_only
        )
        log(f"  👥 共作者: {len(coauthors)} 人")

        # 合并到全局
        for aid, rec in coauthors.items():
            if aid not in all_coauthors:
                all_coauthors[aid] = rec
                coauthor_sources[aid] = []
            else:
                # 合并论文列表
                existing_titles = {p["title"] for p in all_coauthors[aid]["coauthor_papers"]}
                for p in rec["coauthor_papers"]:
                    if p["title"] not in existing_titles:
                        all_coauthors[aid]["coauthor_papers"].append(p)
            coauthor_sources[aid].append(target["name"])

    log(f"\n{'='*50}")
    log(f"📊 汇总: 共发现 {len(all_coauthors)} 位不重复共作者")

    # 4. 批量查询共作者详细信息（h-index, citations 等）
    all_coauthors = enrich_coauthors_batch(
        all_coauthors,
        min_papers=5,  # 只查询合作论文 ≥5 篇的共作者（减少 API 调用，聚焦核心合作关系）
        cache_path=author_cache_path
    )

    # 5. 评级 & 过滤
    import_records = []
    tier_stats = {"S": 0, "A+": 0, "A": 0, "B": 0, "C": 0}

    for aid, rec in all_coauthors.items():
        tier = score_tier(rec)
        tier_stats[tier] = tier_stats.get(tier, 0) + 1

        if tier_order.get(tier, 99) > min_tier_val:
            continue

        sources_str = " & ".join(set(coauthor_sources.get(aid, [])))
        import_rec  = build_import_record(rec, sources_str)
        import_records.append(import_rec)

    log(f"\n🏆 评级分布（全量）:")
    for t, cnt in tier_stats.items():
        log(f"   {t}: {cnt} 人")
    log(f"   → 达到 {args.min_tier}+ 标准，准备导入: {len(import_records)} 人")

    # 5. 保存原始结果（备查）
    raw_output = OUTPUT_DIR / f"coauthors_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    raw_output.write_text(json.dumps(list(all_coauthors.values()), ensure_ascii=False, indent=2))
    log(f"\n💾 原始数据已保存: {raw_output.name}")

    import_output = OUTPUT_DIR / f"coauthors_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import_output.write_text(json.dumps(import_records, ensure_ascii=False, indent=2))
    log(f"💾 导入数据已保存: {import_output.name}")

    # 6. 写入数据库
    if import_records:
        log(f"\n🗃️  写入数据库: {DB_PATH.name}")
        inserted = import_to_db(import_records, DB_PATH, dry_run=args.dry_run)
        log(f"\n✅ 完成！共新增 {inserted} 名候选人")
    else:
        log(f"\n⚠️  没有符合条件的候选人需要导入")

    # 7. 打印 Top20 预览
    top20 = sorted(
        [r for r in import_records],
        key=lambda r: (
            {"S": 0, "A+": 1, "A": 2, "B": 3, "C": 4}.get(r["talent_tier"], 9),
            -(json.loads(r["structured_tags"]).get("h_index") or 0)
        )
    )[:20]

    log(f"\n🌟 Top 20 候选人预览:")
    log(f"{'姓名':<30} {'机构':<35} {'级别':<5} {'h-index':<8} {'关联人物'}")
    log("-" * 100)
    for r in top20:
        tags   = json.loads(r["structured_tags"])
        log(f"{r['name']:<30} {r['current_company']:<35} "
            f"{r['talent_tier']:<5} {tags.get('h_index',0):<8} {tags.get('source_target','')}")


if __name__ == "__main__":
    main()
