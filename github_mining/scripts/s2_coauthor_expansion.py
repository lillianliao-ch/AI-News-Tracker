#!/usr/bin/env python3
"""
Semantic Scholar 共作者扩散脚本 — 学术人才库通用版
=====================================================
从数据库中已有的学术人才出发，通过 Semantic Scholar API
挖掘其 2021-2022 届共作者，找出已就职的 AI 人才。

特性:
  - 所有输出写入带时间戳的子目录，绝不覆盖已有数据
  - 支持断点续传（S2 API 缓存）
  - 工业界就职信号过滤（非 .edu 机构优先）
  - 与已有 DB 自动去重（name + s2_id 双重检查）

用法:
    # 基础运行（从 DB 中提取 S2 ID，扩散共作者）
    python3 s2_coauthor_expansion.py

    # 只预览，不写入 DB
    python3 s2_coauthor_expansion.py --dry-run

    # 限制处理的种子人数（测试用）
    python3 s2_coauthor_expansion.py --max-seeds 50 --dry-run

    # 指定论文年份范围（默认 2021-2022，扩大可改）
    python3 s2_coauthor_expansion.py --year-min 2019 --year-max 2023

    # 使用 S2 API Key（申请地址: https://www.semanticscholar.org/product/api）
    S2_API_KEY=xxx python3 s2_coauthor_expansion.py

环境变量:
    S2_API_KEY      Semantic Scholar API Key（可选，有 Key 则提速）
    DB_PATH         数据库路径（默认自动推断）
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
SCRIPT_DIR      = Path(__file__).parent
REPO_ROOT       = SCRIPT_DIR.parent.parent
DB_PATH_DEFAULT = REPO_ROOT / "personal-ai-headhunter" / "data" / "headhunter_dev.db"

# 所有输出都放在带时间戳的子目录 → 绝不覆盖
RUN_TS     = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = SCRIPT_DIR.parent / "data" / "s2_coauthor_expansion" / f"run_{RUN_TS}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 全局缓存目录（跨 run 复用，减少重复 API 调用）
CACHE_DIR = SCRIPT_DIR.parent / "data" / "s2_coauthor_expansion" / "_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Semantic Scholar API
# ============================================================
S2_BASE        = "https://api.semanticscholar.org/graph/v1"
AUTHOR_FIELDS  = "name,affiliations,hIndex,citationCount,paperCount,homepage,externalIds"
PAPER_FIELDS   = "title,year,venue,authors"

# ============================================================
# 顶级会议列表（用于评级）
# ============================================================
TOP_VENUES = {
    "NeurIPS", "ICML", "ICLR", "CVPR", "ECCV", "ICCV",
    "ACL", "EMNLP", "NAACL", "AAAI", "IJCAI", "INTERSPEECH",
    "ICASSP", "KDD", "WWW", "SIGIR", "ICDM", "MLSys", "COLM",
    "COLING", "RecSys", "SIGCOMM", "OSDI", "SOSP",
}

# 学术机构域名/关键词（用于识别仍在读/在校者）
ACADEMIC_INDICATORS = [
    ".edu", "university", "institute", "lab ", "laboratory",
    "college", "academia", "research center", "école", "école",
    "大学", "学院", "研究所", "实验室", "研究院",
]

# 已就职信号（工业界机构关键词）
INDUSTRY_COMPANIES = [
    # 中国顶级 AI 公司
    "bytedance", "tiktok", "alibaba", "aliyun", "tencent", "baidu",
    "huawei", "xiaomi", "meituan", "jd", "netease", "didi", "kuaishou",
    "sensetime", "商汤", "megvii", "旷视", "zhipu", "moonshot", "deepseek",
    "baichuan", "minimax", "01.ai", "stepfun", "modelbest", "zhijiang",
    # 国际
    "google", "microsoft", "meta", "amazon", "apple", "nvidia", "openai",
    "anthropic", "deepmind", "cohere", "mistral", "huggingface",
]


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ============================================================
# Semantic Scholar 请求（带限速 & 重试）
# ============================================================
def s2_get(endpoint: str, params: Dict = None, retries: int = 4) -> Optional[Dict]:
    url = f"{S2_BASE}/{endpoint}"
    headers = {"User-Agent": "S2CoauthorExpansion/1.0"}
    api_key = os.getenv("S2_API_KEY", "")
    if api_key:
        headers["x-api-key"] = api_key

    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=25)
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


def rate_sleep():
    has_key = bool(os.getenv("S2_API_KEY", ""))
    if has_key:
        time.sleep(random.uniform(0.12, 0.25))
    else:
        time.sleep(random.uniform(1.05, 1.8))


# ============================================================
# Step 1: 从数据库提取种子 S2 IDs
# ============================================================
def load_seeds_from_db(db_path: Path, max_seeds: int = None) -> List[Dict]:
    """
    从 candidates 表提取学术人才的 s2_id。
    只取 source='academic' 且 structured_tags 包含 s2_id 的候选人。
    """
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, structured_tags
        FROM candidates
        WHERE source = 'academic'
          AND structured_tags IS NOT NULL
    """)
    rows = cur.fetchall()
    conn.close()

    seeds = []
    for row_id, name, tags_str in rows:
        try:
            tags = json.loads(tags_str)
            s2_id = tags.get("s2_id")
            if s2_id and str(s2_id).strip():
                seeds.append({
                    "db_id": row_id,
                    "name": name,
                    "s2_id": str(s2_id).strip(),
                })
        except Exception:
            continue

    log(f"📦 从 DB 加载 {len(seeds)} 个有 S2 ID 的学术种子人才")
    if max_seeds and max_seeds < len(seeds):
        log(f"  ⚙️  限制为前 {max_seeds} 条（--max-seeds 参数）")
        seeds = seeds[:max_seeds]
    return seeds


# ============================================================
# Step 2: 拉取种子作者的论文 & 共作者
# ============================================================
def load_cache(cache_file: Path) -> Dict:
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(cache: Dict, cache_file: Path):
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_coauthors_for_seed(
    s2_id: str,
    year_min: int,
    year_max: int,
    paper_cache: Dict,
) -> Dict[str, Dict]:
    """
    给定一个 s2_id，拉取其 year_min-year_max 期间的论文，
    返回 {coauthor_s2_id: coauthor_record} 字典。
    """
    cache_key = f"papers::{s2_id}::{year_min}-{year_max}"
    if cache_key in paper_cache:
        papers = paper_cache[cache_key]
    else:
        papers = []
        offset = 0
        while True:
            result = s2_get(f"author/{s2_id}/papers", {
                "fields": PAPER_FIELDS,
                "limit": 100,
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
                if year_min <= year <= year_max:
                    papers.append(paper)
            offset += 100
            if offset >= result.get("total", 0):
                break
        paper_cache[cache_key] = papers

    # 提取共作者
    coauthors: Dict[str, Dict] = {}
    for paper in papers:
        for author in paper.get("authors", []):
            aid = author.get("authorId")
            if not aid or aid == s2_id:
                continue
            if aid not in coauthors:
                coauthors[aid] = {
                    "s2_id": aid,
                    "name": author.get("name", ""),
                    "affiliations": [],
                    "h_index": 0,
                    "citation_count": 0,
                    "homepage": "",
                    "external_ids": {},
                    "coauthor_papers": [],
                    "seed_names": [],
                }
            coauthors[aid]["coauthor_papers"].append({
                "title": paper.get("title", ""),
                "year": paper.get("year", 0),
                "venue": paper.get("venue", ""),
            })
    return coauthors


# ============================================================
# Step 3: 富化共作者（h-index, 机构, 主页）
# ============================================================
def enrich_coauthors(
    all_coauthors: Dict[str, Dict],
    min_papers: int,
    author_cache: Dict,
) -> Dict[str, Dict]:
    to_enrich = [
        (aid, rec) for aid, rec in all_coauthors.items()
        if len(rec["coauthor_papers"]) >= min_papers
    ]
    log(f"\n🔬 富化共作者详情: {len(to_enrich)}/{len(all_coauthors)} 人 (≥{min_papers}篇合作)")

    for i, (aid, rec) in enumerate(to_enrich):
        cache_key = f"author::{aid}"
        if cache_key in author_cache:
            cached = author_cache[cache_key]
            rec.update({k: cached[k] for k in cached if k in rec})
            continue

        if i > 0 and i % 30 == 0:
            log(f"  进度: {i}/{len(to_enrich)}…")

        result = s2_get(f"author/{aid}", {"fields": AUTHOR_FIELDS})
        rate_sleep()

        if result:
            rec["h_index"] = result.get("hIndex") or 0
            rec["citation_count"] = result.get("citationCount") or 0
            rec["homepage"] = result.get("homepage") or ""
            rec["external_ids"] = result.get("externalIds") or {}
            rec["affiliations"] = result.get("affiliations") or []
            author_cache[cache_key] = {
                "h_index": rec["h_index"],
                "citation_count": rec["citation_count"],
                "homepage": rec["homepage"],
                "external_ids": rec["external_ids"],
                "affiliations": rec["affiliations"],
                "name": result.get("name", rec["name"]),
            }
            if result.get("name"):
                rec["name"] = result["name"]

    log(f"  ✅ 富化完成")
    return all_coauthors


# ============================================================
# Step 4: 就职信号评估
# ============================================================
def has_industry_signal(rec: Dict) -> bool:
    """判断是否有工业界就职信号"""
    affils = " ".join(rec.get("affiliations") or []).lower()
    homepage = (rec.get("homepage") or "").lower()
    combined = affils + " " + homepage

    # 含工业界公司
    for kw in INDUSTRY_COMPANIES:
        if kw in combined:
            return True

    # 不含明显学术机构（即可能已就职）
    is_academic = any(kw in combined for kw in ACADEMIC_INDICATORS)
    # 如果机构信息为空，也视为"不确定"（不过滤）
    if not combined.strip():
        return False

    return not is_academic


def score_tier(rec: Dict) -> str:
    h = rec.get("h_index", 0) or 0
    cites = rec.get("citation_count", 0) or 0
    top = sum(
        1 for p in rec.get("coauthor_papers", [])
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


# ============================================================
# Step 5: DB 去重
# ============================================================
def load_existing_keys(db_path: Path) -> Tuple[Set[str], Set[str]]:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM candidates")
    existing_names = {row[0].strip().lower() for row in cur.fetchall() if row[0]}
    cur.execute("SELECT structured_tags FROM candidates WHERE structured_tags IS NOT NULL")
    existing_s2_ids = set()
    for (tags_str,) in cur.fetchall():
        try:
            sid = json.loads(tags_str).get("s2_id")
            if sid:
                existing_s2_ids.add(str(sid))
        except Exception:
            pass
    conn.close()
    log(f"🗃️  DB 现有: {len(existing_names)} 个姓名，{len(existing_s2_ids)} 个 S2 ID")
    return existing_names, existing_s2_ids


# ============================================================
# Step 6: 构建导入记录
# ============================================================
def build_import_record(rec: Dict) -> Dict:
    tier = score_tier(rec)
    affils = rec.get("affiliations") or []
    homepage = rec.get("homepage") or ""
    h = rec.get("h_index") or 0
    cites = rec.get("citation_count") or 0
    papers = rec.get("coauthor_papers") or []
    seeds = rec.get("seed_names") or []

    github_url = None
    if homepage and "github.com" in homepage:
        github_url = homepage

    notes_parts = [
        f"【来源】S2 共作者扩散 | 关联种子: {', '.join(seeds[:3])}",
        f"【学术】h-index={h} | 引用={cites} | 共同论文={len(papers)}篇",
    ]
    if affils:
        notes_parts.append(f"【机构】{', '.join(affils[:2])}")
    if papers:
        notes_parts.append("【合作论文】")
        for p in papers[:3]:
            notes_parts.append(f"  · {p['title']} ({p.get('venue','?')} {p.get('year','')})")
        if len(papers) > 3:
            notes_parts.append(f"  …另有 {len(papers)-3} 篇")

    industry_flag = has_industry_signal(rec)

    structured_tags = {
        "academic_tier": tier,
        "h_index": h,
        "citation_count": cites,
        "paper_count": len(papers),
        "s2_id": rec.get("s2_id"),
        "coauthor_seed_names": seeds[:5],
        "has_industry_signal": industry_flag,
        "conferences": list({
            p.get("venue", "") for p in papers
            if p.get("venue") and any(v in p["venue"] for v in TOP_VENUES)
        })[:10],
        "source_method": "s2_coauthor_expansion",
        "expansion_run_ts": RUN_TS,
    }

    return {
        "name": rec.get("name", ""),
        "current_company": (affils[0] if affils else ""),
        "current_title": "Researcher / Engineer",
        "talent_tier": tier,
        "pipeline_stage": "new",
        "source": "academic",
        "source_file": f"s2_coauthor_expansion_{RUN_TS}",
        "personal_website": homepage or None,
        "github_url": github_url,
        "linkedin_url": None,
        "email": None,
        "structured_tags": json.dumps(structured_tags, ensure_ascii=False),
        "ai_summary": None,
        "notes": "\n".join(notes_parts),
    }


# ============================================================
# Step 7: 写入数据库
# ============================================================
def import_to_db(records: List[Dict], db_path: Path, dry_run: bool) -> int:
    existing_names, existing_s2_ids = load_existing_keys(db_path)
    new_records = []
    skipped = 0

    for r in records:
        name_lower = r["name"].strip().lower()
        s2_id = json.loads(r["structured_tags"]).get("s2_id", "")

        if not r["name"].strip():
            skipped += 1
            continue
        if name_lower in existing_names:
            skipped += 1
            continue
        if s2_id and str(s2_id) in existing_s2_ids:
            skipped += 1
            continue
        new_records.append(r)

    log(f"  📊 去重结果: {len(new_records)} 条新候选人，{skipped} 条已存在跳过")

    if dry_run:
        log("  🔍 Dry-run 模式：不写入数据库")
        return len(new_records)

    if not new_records:
        return 0

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    now = datetime.now().isoformat()
    insert_sql = """
        INSERT INTO candidates (
            name, current_company, current_title, talent_tier, pipeline_stage,
            source, source_file, personal_website, github_url, linkedin_url,
            email, structured_tags, ai_summary, notes, created_at, updated_at
        ) VALUES (
            :name, :current_company, :current_title, :talent_tier, :pipeline_stage,
            :source, :source_file, :personal_website, :github_url, :linkedin_url,
            :email, :structured_tags, :ai_summary, :notes, :created_at, :updated_at
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
    parser = argparse.ArgumentParser(description="Semantic Scholar 共作者扩散 — 学术人才库通用版")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入数据库")
    parser.add_argument("--max-seeds", type=int, default=None,
                        help="最多处理多少个种子人才（测试用）")
    parser.add_argument("--year-min", type=int, default=2021,
                        help="论文年份下限（默认 2021）")
    parser.add_argument("--year-max", type=int, default=2022,
                        help="论文年份上限（默认 2022）")
    parser.add_argument("--min-papers", type=int, default=2,
                        help="最少共作论文数才会被富化和导入（默认 2）")
    parser.add_argument("--min-tier", type=str, default="B",
                        choices=["S", "A+", "A", "B", "C"],
                        help="最低导入级别（默认 B）")
    parser.add_argument("--industry-only", action="store_true",
                        help="只导入有工业界就职信号的共作者")
    parser.add_argument("--db-path", type=str, default=str(DB_PATH_DEFAULT),
                        help="数据库路径")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        log(f"❌ 数据库不存在: {db_path}")
        sys.exit(1)

    tier_order = {"S": 0, "A+": 1, "A": 2, "B": 3, "C": 4}
    min_tier_val = tier_order[args.min_tier]
    has_api_key = bool(os.getenv("S2_API_KEY", ""))

    log(f"🚀 S2 共作者扩散开始")
    log(f"   输出目录: {OUTPUT_DIR}")
    log(f"   年份范围: {args.year_min}-{args.year_max}")
    log(f"   最少共作论文: {args.min_papers}")
    log(f"   最低级别: {args.min_tier}")
    log(f"   仅工业界: {args.industry_only}")
    log(f"   API Key: {'有 (提速模式)' if has_api_key else '无 (1 QPS)'}")
    log(f"   写入 DB: {'否 (dry-run)' if args.dry_run else '是'}")

    # Step 1: 加载种子
    seeds = load_seeds_from_db(db_path, max_seeds=args.max_seeds)
    if not seeds:
        log("❌ 没有找到有 S2 ID 的学术种子，退出")
        sys.exit(1)

    # Step 2: 加载缓存
    paper_cache_file = CACHE_DIR / "paper_cache.json"
    author_cache_file = CACHE_DIR / "author_cache.json"
    paper_cache = load_cache(paper_cache_file)
    author_cache = load_cache(author_cache_file)

    log(f"\n📦 缓存: 论文={len(paper_cache)} 条, 作者={len(author_cache)} 条")

    # Step 3: 扩散
    all_coauthors: Dict[str, Dict] = {}
    progress_file = OUTPUT_DIR / "progress.json"
    done_s2_ids: Set[str] = set()

    # 断点续传支持
    if progress_file.exists():
        try:
            prog = json.loads(progress_file.read_text())
            done_s2_ids = set(prog.get("done_seeds", []))
            log(f"  🔄 断点续传: 已完成 {len(done_s2_ids)} 个种子")
        except Exception:
            pass

    log(f"\n🔍 扩散 {len(seeds)} 个种子 (年份 {args.year_min}-{args.year_max})…")

    save_interval = 100
    for i, seed in enumerate(seeds):
        s2_id = seed["s2_id"]
        name = seed["name"]

        if s2_id in done_s2_ids:
            continue

        if i % 20 == 0:
            log(f"  进度: {i}/{len(seeds)} | 共作者池: {len(all_coauthors)}")

        coauthors = fetch_coauthors_for_seed(s2_id, args.year_min, args.year_max, paper_cache)

        # 合并到全局池
        for aid, rec in coauthors.items():
            if aid not in all_coauthors:
                all_coauthors[aid] = rec
            else:
                # 合并论文列表（去重）
                existing_titles = {p["title"] for p in all_coauthors[aid]["coauthor_papers"]}
                for p in rec["coauthor_papers"]:
                    if p["title"] not in existing_titles:
                        all_coauthors[aid]["coauthor_papers"].append(p)
            # 记录关联种子
            if name not in all_coauthors[aid]["seed_names"]:
                all_coauthors[aid]["seed_names"].append(name)

        done_s2_ids.add(s2_id)

        # 定期保存缓存和进度
        if (i + 1) % save_interval == 0:
            save_cache(paper_cache, paper_cache_file)
            progress_file.write_text(json.dumps({"done_seeds": list(done_s2_ids)}, indent=2))
            log(f"  💾 缓存已保存 ({i+1} 个种子完成)")

    # 最终保存缓存
    save_cache(paper_cache, paper_cache_file)
    progress_file.write_text(json.dumps({"done_seeds": list(done_s2_ids)}, indent=2))

    log(f"\n✅ 扩散完成! 发现 {len(all_coauthors)} 位不重复共作者")

    # Step 4: 富化
    all_coauthors = enrich_coauthors(all_coauthors, args.min_papers, author_cache)
    save_cache(author_cache, author_cache_file)

    # Step 5: 评级 & 过滤
    import_records = []
    tier_stats = {"S": 0, "A+": 0, "A": 0, "B": 0, "C": 0, "skip": 0}
    industry_count = 0

    for aid, rec in all_coauthors.items():
        if len(rec["coauthor_papers"]) < args.min_papers:
            tier_stats["skip"] = tier_stats.get("skip", 0) + 1
            continue

        tier = score_tier(rec)
        tier_stats[tier] = tier_stats.get(tier, 0) + 1

        if tier_order.get(tier, 99) > min_tier_val:
            continue

        if args.industry_only and not has_industry_signal(rec):
            continue

        if has_industry_signal(rec):
            industry_count += 1

        import_records.append(build_import_record(rec))

    log(f"\n🏆 评级分布:")
    for t, cnt in tier_stats.items():
        log(f"   {t}: {cnt} 人")
    log(f"   → 工业界信号: {industry_count} 人")
    log(f"   → 准备导入: {len(import_records)} 人")

    # Step 6: 保存原始结果（带时间戳）
    raw_file = OUTPUT_DIR / f"coauthors_raw_{RUN_TS}.json"
    raw_file.write_text(
        json.dumps(list(all_coauthors.values()), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    log(f"\n💾 原始数据: {raw_file}")

    import_file = OUTPUT_DIR / f"coauthors_import_{RUN_TS}.json"
    import_file.write_text(
        json.dumps(import_records, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    log(f"💾 导入数据: {import_file}")

    # Top 20 预览
    top20 = sorted(
        import_records,
        key=lambda r: (
            {"S": 0, "A+": 1, "A": 2, "B": 3, "C": 4}.get(r["talent_tier"], 9),
            -(json.loads(r["structured_tags"]).get("h_index") or 0)
        )
    )[:20]

    log(f"\n🌟 Top 20 预览:")
    log(f"{'姓名':<30} {'机构':<35} {'级':<4} {'h':<6} {'工业界'}")
    log("-" * 90)
    for r in top20:
        tags = json.loads(r["structured_tags"])
        flag = "✅" if tags.get("has_industry_signal") else ""
        log(f"{r['name']:<30} {r['current_company']:<35} "
            f"{r['talent_tier']:<4} {tags.get('h_index',0):<6} {flag}")

    # Step 7: 写入 DB
    if import_records:
        log(f"\n🗃️  写入数据库…")
        inserted = import_to_db(import_records, db_path, dry_run=args.dry_run)
        log(f"\n✅ 全部完成！新增 {inserted} 名候选人")
        log(f"📁 输出目录: {OUTPUT_DIR}")
    else:
        log(f"\n⚠️  没有符合条件的候选人需要导入")


if __name__ == "__main__":
    main()
