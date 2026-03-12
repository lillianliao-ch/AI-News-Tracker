#!/usr/bin/env python3
"""
学术渠道人才挖掘工具 - Academic Miner
从顶级 AI 会议（ICLR/NeurIPS/ICML/ACL/CVPR）作者列表中挖掘华人 AI 人才

用法:
    # ICLR 2024 完整采集
    python3 academic_miner.py --conference iclr --year 2024 --max-authors 200

    # 多会议批量
    python3 academic_miner.py --conference iclr,acl --year 2023,2024

    # 只跑过滤+打分（已有原始数据）
    python3 academic_miner.py --input academics_raw.json --score-only
"""

import os
import sys
import json
import time
import re
import argparse
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# ============================================================
# 路径配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent
GITHUB_MINING_DIR = SCRIPT_DIR.parent
PERSONAL_AI_DIR = GITHUB_MINING_DIR.parent / "personal-ai-headhunter"

# 复用国籍检测模块
sys.path.insert(0, str(PERSONAL_AI_DIR / "scripts" / "extract"))
try:
    from add_nationality_tags import detect_nationality
    NATIONALITY_AVAILABLE = True
except ImportError:
    NATIONALITY_AVAILABLE = False
    print("⚠️  无法导入国籍检测模块，将保留所有 unknown 国籍")

# 输出目录
OUTPUT_DIR = GITHUB_MINING_DIR / "data" / "academic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Semantic Scholar API
# ============================================================
S2_API_BASE = "https://api.semanticscholar.org/graph/v1"
S2_AUTHOR_FIELDS = "name,affiliations,hIndex,citationCount,paperCount,externalIds,homepage,papers.year,papers.venue,papers.citationCount"

# ============================================================
# 顶会识别（用于 Semantic Scholar 论文筛选）
# ============================================================
TOP_VENUES = {
    "NeurIPS", "ICML", "ICLR", "CVPR", "ECCV", "ICCV",
    "ACL", "EMNLP", "NAACL", "AAAI", "IJCAI",
    "KDD", "WWW", "SIGIR", "CIKM", "RecSys",
    "OSDI", "SOSP", "NSDI", "MLSys", "ASPLOS",
}

# ============================================================
# 工具函数
# ============================================================
def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def save_json(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"💾 保存 {len(data)} 条 → {path.name}")


def load_json(path: Path) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def s2_request(url: str, params: Dict = None, retries: int = 3) -> Optional[Dict]:
    """Semantic Scholar API 请求（带重试 + 限流控制）"""
    headers = {"User-Agent": "AcademicMiner/1.0 (talent-sourcing-tool)"}
    
    # 支持注入官方 API Key 突破 1 QPS 限流
    api_key = os.getenv("S2_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
        
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:  # Rate limit
                # 优先使用服务器告知的精确等待时间
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    wait = float(retry_after) + random.uniform(1, 3)
                else:
                    wait = 30 + random.uniform(0, 10)
                log(f"  ⏳ 限流，等待 {wait:.0f}s...")
                time.sleep(wait)
            elif resp.status_code == 404:
                return None
            else:
                log(f"  ⚠️  HTTP {resp.status_code}: {url}")
                time.sleep(2)
        except Exception as e:
            log(f"  ❌ 请求异常: {e}")
            time.sleep(5)
    return None


# ============================================================
# Phase A1: ICLR 作者采集（OpenReview API）
# ============================================================
def collect_iclr_authors(year: int, max_papers: int = None) -> List[Dict]:
    """从 ICLR OpenReview API v2 采集所有论文作者"""
    log(f"\n{'='*60}")
    log(f"📚 采集 ICLR {year} 论文作者")
    log(f"{'='*60}")

    # OpenReview 已切换至 api2，使用 venue 字段查询
    base_url = "https://api2.openreview.net/notes"
    venue_name = f"ICLR {year}"

    authors = []
    offset = 0
    per_page = 1000
    total_papers = 0

    while True:
        params = {
            "content.venue": venue_name,
            "limit": per_page,
            "offset": offset,
        }
        try:
            resp = requests.get(base_url, params=params, timeout=20)
            if resp.status_code != 200:
                log(f"  ❌ OpenReview API 错误: {resp.status_code} — {resp.text[:200]}")
                break
            data = resp.json()
        except Exception as e:
            log(f"  ❌ 请求失败: {e}")
            break

        notes = data.get("notes", [])
        if not notes:
            break

        for note in notes:
            content = note.get("content", {})
            # API v2: 每个字段是 {"value": ...} 格式
            title = (content.get("title") or {}).get("value", "")
            paper_authors = (content.get("authors") or {}).get("value", [])
            author_emails = (content.get("authorids") or {}).get("value", [])

            for i, author_name in enumerate(paper_authors):
                if not author_name or not author_name.strip():
                    continue

                email = None
                if i < len(author_emails):
                    raw_id = author_emails[i]
                    if raw_id and "@" in raw_id and "." in raw_id:
                        email = raw_id

                authors.append({
                    "name": author_name.strip(),
                    "email": email,
                    "affiliation": None,
                    "paper_title": title,
                    "conference": f"ICLR {year}",
                    "source": "openreview_v2",
                })

            total_papers += 1
            if max_papers and total_papers >= max_papers:
                break

        log(f"  📄 已获取 {total_papers} 篇论文（累计作者记录: {len(authors)}）")

        if max_papers and total_papers >= max_papers:
            break
        if len(notes) < per_page:
            break

        offset += per_page
        time.sleep(0.5)

    log(f"✅ ICLR {year}: {total_papers} 篇论文, {len(authors)} 条作者记录")
    return authors




# ============================================================
# Phase A2: ACL Anthology 作者采集
# ============================================================
def collect_acl_authors(year: int, max_papers: int = None) -> List[Dict]:
    """从 ACL Anthology API 采集作者"""
    log(f"\n{'='*60}")
    log(f"📚 采集 ACL Anthology {year} 作者")
    log(f"{'='*60}")

    # ACL Anthology 有一个 JSON API
    url = f"https://aclanthology.org/anthology+abstracts.json.gz"
    # 更简单的方式：直接用年份过滤
    search_url = f"https://aclanthology.org/search/?q=&filter=year%3A{year}&filter=venue%3AACL&format=json"

    try:
        # 使用 ACL Anthology 的非官方 search API
        resp = requests.get(
            "https://aclanthology.org/api/papers",
            params={"q": "", "year": year, "venue": "ACL", "limit": 1000},
            timeout=20
        )
        if resp.status_code == 404:
            # 降级：直接爬 HTML 页面
            log("  ⚠️  ACL API 返回 404，使用备用方案")
            return _collect_acl_fallback(year, max_papers)
        data = resp.json()
    except Exception as e:
        log(f"  ⚠️  ACL API 请求失败: {e}，使用备用方案")
        return _collect_acl_fallback(year, max_papers)

    authors = []
    papers = data if isinstance(data, list) else data.get("results", [])
    for paper in papers[:max_papers] if max_papers else papers:
        title = paper.get("title", "")
        for author in paper.get("authors", []):
            authors.append({
                "name": author.get("name", "").strip(),
                "email": None,
                "affiliation": None,
                "paper_title": title,
                "conference": f"ACL {year}",
                "source": "acl_anthology",
            })

    log(f"✅ ACL {year}: {len(papers)} 篇论文, {len(authors)} 条作者记录")
    return authors


def _collect_acl_fallback(year: int, max_papers: int = None) -> List[Dict]:
    """ACL Anthology 备用采集方案（直接爬 EMNLP/ACL proceedings 页面中的 JSON）"""
    # ACL Anthology 提供了完整的论文数据，可通过 GitHub 的 data repo 获取
    # https://github.com/acl-org/acl-anthology/tree/master/data/json
    acl_data_url = f"https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/json/anthology+abstracts.json"
    log(f"  🔄 尝试从 ACL Anthology GitHub 数据仓库获取...")

    try:
        resp = requests.get(acl_data_url, timeout=30)
        if resp.status_code != 200:
            log(f"  ❌ 无法获取 ACL 数据: {resp.status_code}")
            return []
        data = resp.json()
    except Exception as e:
        log(f"  ❌ 请求失败: {e}")
        return []

    authors = []
    count = 0
    for paper_id, paper in data.items():
        if str(year) not in paper_id:
            continue
        title = paper.get("title", "")
        for author in paper.get("authors", []):
            name = f"{author.get('first', '')} {author.get('last', '')}".strip()
            if name:
                authors.append({
                    "name": name,
                    "email": None,
                    "affiliation": None,
                    "paper_title": title,
                    "conference": f"ACL/EMNLP {year}",
                    "source": "acl_anthology_github",
                })
        count += 1
        if max_papers and count >= max_papers:
            break

    log(f"✅ ACL/EMNLP {year}: {count} 篇论文, {len(authors)} 条作者记录")
    return authors


# ============================================================
# Phase A3: NeurIPS / ICML / CVPR 网页爬虫 (BeautifulSoup)
# ============================================================

def collect_neurips_authors(year: int, max_papers: int = None) -> List[Dict]:
    """从 NeurIPS Proceedings 页面抓取作者 (2022-2024可用)"""
    log(f"\n{'='*60}")
    log(f"📚 采集 NeurIPS {year} 作者")
    log(f"{'='*60}")

    url = f"https://proceedings.neurips.cc/paper_files/paper/{year}"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            log(f"  ❌ NeurIPS 页面错误: {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        log(f"  ❌ 请求失败: {e}")
        return []

    authors = []
    papers = soup.select('ul.paper-list li')
    count = 0

    for paper in papers:
        title_tag = paper.find('a')
        if not title_tag:
            continue
        title = title_tag.text.strip()
        
        authors_tag = paper.select_one('.paper-authors')
        if authors_tag:
            author_names = [a.strip() for a in authors_tag.text.split(',')]
            for name in author_names:
                if name:
                    authors.append({
                        "name": name,
                        "email": None,
                        "affiliation": None,
                        "paper_title": title,
                        "conference": f"NeurIPS {year}",
                        "source": "neurips_proceedings",
                    })
            count += 1
            if max_papers and count >= max_papers:
                break

    log(f"✅ NeurIPS {year}: {count} 篇论文, {len(authors)} 条作者记录")
    return authors


def collect_icml_authors(year: int, max_papers: int = None) -> List[Dict]:
    """从 ICML PMLR 页面抓取作者"""
    log(f"\n{'='*60}")
    log(f"📚 采集 ICML {year} 作者")
    log(f"{'='*60}")

    # PMLR volume 映射 (需要根据年份手动维护一下)
    pmlr_map = {
        2024: "v235", 2023: "v202", 2022: "v162"
    }
    vol = pmlr_map.get(year)
    if not vol:
        log(f"  ⚠️  未知 ICML 年份对应 PMLR volume: {year}，需要手动添加映射")
        return []

    url = f"https://proceedings.mlr.press/{vol}/"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            log(f"  ❌ ICML (PMLR {vol}) 页面错误: {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        log(f"  ❌ 请求失败: {e}")
        return []

    authors = []
    papers = soup.select('.paper')
    count = 0

    for paper in papers:
        title_tag = paper.select_one('.title')
        authors_tag = paper.select_one('.authors')
        
        if title_tag and authors_tag:
            title = title_tag.text.strip()
            # PMLR authors 常见带有不间断空格 (\xa0) 和逗号
            author_text = authors_tag.text.replace('\xa0', ' ').strip()
            author_names = [a.strip() for a in author_text.split(',')]
            
            for name in author_names:
                if name:
                    authors.append({
                        "name": name,
                        "email": None,
                        "affiliation": None,
                        "paper_title": title,
                        "conference": f"ICML {year}",
                        "source": "icml_pmlr",
                    })
            count += 1
            if max_papers and count >= max_papers:
                break

    log(f"✅ ICML {year}: {count} 篇论文, {len(authors)} 条作者记录")
    return authors


def collect_cvpr_authors(year: int, max_papers: int = None) -> List[Dict]:
    """从 CVPR OpenAccess 页面抓取作者"""
    log(f"\n{'='*60}")
    log(f"📚 采集 CVPR {year} 作者")
    log(f"{'='*60}")

    url = f"https://openaccess.thecvf.com/CVPR{year}?day=all"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            log(f"  ❌ CVPR 页面错误: {resp.status_code} (可能需要按日期抓取或年份尚未在 OpenAccess)")
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        log(f"  ❌ 请求失败: {e}")
        return []

    authors = []
    paper_tags = soup.select('dt.ptitle')
    count = 0

    for dt in paper_tags:
        title = dt.text.strip()
        # CVPR 的作者在紧跟着的 dd 标签里，里面有多个包含作者信息的 form
        dd = dt.find_next_sibling('dd')
        if dd:
            author_forms = dd.select('form')
            for form in author_forms:
                name = form.text.strip().strip(',')
                if name:
                    authors.append({
                        "name": name,
                        "email": None,
                        "affiliation": None,
                        "paper_title": title,
                        "conference": f"CVPR {year}",
                        "source": "cvpr_openaccess",
                    })
            count += 1
            if max_papers and count >= max_papers:
                break

    log(f"✅ CVPR {year}: {count} 篇论文, {len(authors)} 条作者记录")
    return authors


# ============================================================
# Phase B: 去重 + 华人过滤 + 质量评分
# ============================================================
def deduplicate_authors(authors: List[Dict]) -> List[Dict]:
    """按姓名去重，保留所有论文信息合并"""
    log(f"\n📊 去重处理: {len(authors)} 条原始记录")
    merged = {}

    for a in authors:
        key = a["name"].strip().lower()
        if not key or len(key) < 2:
            continue

        if key not in merged:
            merged[key] = {
                **a,
                "papers": [a["paper_title"]],
                "conferences": [a["conference"]],
            }
        else:
            # 合并论文记录
            existing = merged[key]
            if a["paper_title"] not in existing["papers"]:
                existing["papers"].append(a["paper_title"])
            if a["conference"] not in existing["conferences"]:
                existing["conferences"].append(a["conference"])
            # 优先保留找到的邮箱
            if not existing.get("email") and a.get("email"):
                existing["email"] = a["email"]

    result = list(merged.values())
    log(f"✅ 去重后: {len(result)} 个独立作者（合并了 {len(authors) - len(result)} 条重复）")
    return result


def filter_chinese_researchers(authors: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """过滤华人学者"""
    log(f"\n🌏 国籍过滤: {len(authors)} 人")

    chinese, unknown, foreign = [], [], []

    for author in authors:
        name = author.get("name", "")
        company = author.get("affiliation", "") or ""

        if NATIONALITY_AVAILABLE:
            nationality, confidence = detect_nationality(name, company)
        else:
            nationality = "unknown"
            confidence = "low"

        author["_nationality"] = nationality
        author["_nat_confidence"] = confidence

        if nationality == "chinese":
            chinese.append(author)
        elif nationality == "unknown":
            unknown.append(author)
        else:
            foreign.append(author)

    log(f"  华人: {len(chinese)} 人")
    log(f"  Unknown: {len(unknown)} 人（全部保留）")
    log(f"  外国人: {len(foreign)} 人（过滤）")

    # 保留华人 + unknown（与现有管道策略一致）
    return chinese + unknown, chinese, foreign


# ============================================================
# Phase C: Semantic Scholar 查询（h-index/引用数/主页/GitHub）
# ============================================================
def enrich_with_semantic_scholar(authors: List[Dict], out_dir: Path = None, prefix: str = "") -> List[Dict]:
    """用 Semantic Scholar API 补充学术信息，带本地实时断点缓存"""
    log(f"\n🔬 Semantic Scholar 查询: {len(authors)} 人")

    cache_file = out_dir / f"{prefix}_s2_cache.json" if out_dir else None
    cache = {}
    if cache_file and cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cache = json.load(f)
            log(f"  > 📦 发现 S2 历史进度缓存，已恢复 {len(cache)} 名学者的查询记录 (断点续传生效)!")
        except Exception as e:
            log(f"  > ⚠️ 读取 S2 缓存失败: {e}")

    enriched = []
    failed = 0
    new_queries = 0

    for i, author in enumerate(authors):
        name = author.get("name", "")
        affiliation = author.get("affiliation", "") or ""

        # 检查是否已包含在缓存中
        cache_key = f"{name}::{affiliation}"
        if cache_key in cache:
            enriched.append(cache[cache_key])
            continue

        if new_queries % 20 == 0 and new_queries > 0:
            log(f"  进度: {i}/{len(authors)}...")

        # 搜索作者
        result = s2_request(
            f"{S2_API_BASE}/author/search",
            params={"query": name, "fields": S2_AUTHOR_FIELDS, "limit": 3}
        )

        new_queries += 1

        if not result or not result.get("data"):
            author["s2_found"] = False
            enriched.append(author)
            cache[cache_key] = author
            failed += 1
            
            # 定期落盘保护数据
            if cache_file and new_queries % 50 == 0:
                 with open(cache_file, "w") as f:
                     json.dump(cache, f, ensure_ascii=False)
                     
            time.sleep(0.3)
            continue

        # 消歧：取最匹配的（优先match affiliation）
        candidates = result["data"]
        best = _disambiguate_author(name, affiliation, candidates)

        if best:
            author["s2_id"] = best.get("authorId")
            author["s2_found"] = True
            author["h_index"] = best.get("hIndex", 0)
            author["citation_count"] = best.get("citationCount", 0)
            author["paper_count"] = best.get("paperCount", 0)
            author["personal_website"] = best.get("homepage") or author.get("personal_website")
            author["affiliation"] = (
                best.get("affiliations", [None])[0] if best.get("affiliations") else affiliation
            )

            # 统计顶会论文数
            papers = best.get("papers", [])
            top_venue_papers = [
                p for p in papers
                if any(v in (p.get("venue") or "") for v in TOP_VENUES)
            ]
            author["top_venue_paper_count"] = len(top_venue_papers)
            author["recent_top_papers"] = len([
                p for p in top_venue_papers if (p.get("year") or 0) >= 2021
            ])

            # 检查 externalIds 里是否有 GitHub 线索
            ext_ids = best.get("externalIds", {})
            author["dblp_id"] = ext_ids.get("DBLP")
            author["orcid"] = ext_ids.get("ORCiD")
        else:
            author["s2_found"] = False
            failed += 1

        enriched.append(author)
        cache[cache_key] = author
        
        # 增量落盘保护缓存
        if cache_file and new_queries % 20 == 0:
             with open(cache_file, "w") as f:
                 json.dump(cache, f, ensure_ascii=False)
                 
        time.sleep(0.5)  # 避免触发限流

    # 循环全部跑完，做最终的落盘
    if cache_file and new_queries > 0:
         with open(cache_file, "w") as f:
             json.dump(cache, f, ensure_ascii=False)

    log(f"✅ Semantic Scholar 查询完成: 命中 {len(enriched) - failed}/{len(enriched)} 人")
    return enriched


def _disambiguate_author(name: str, affiliation: str, candidates: List[Dict]) -> Optional[Dict]:
    """从多个候选者中选出最匹配的（名称 + 单位 消歧）"""
    if not candidates:
        return None

    name_lower = name.lower().strip()
    affil_lower = affiliation.lower().strip() if affiliation else ""

    def score_candidate(c: Dict) -> float:
        score = 0.0
        c_name = (c.get("name") or "").lower()

        # 名字完全匹配
        if c_name == name_lower:
            score += 3.0
        elif name_lower in c_name or c_name in name_lower:
            score += 1.0

        # 单位匹配
        if affil_lower:
            c_affils = " ".join(c.get("affiliations") or []).lower()
            if affil_lower and any(w in c_affils for w in affil_lower.split() if len(w) > 3):
                score += 2.0

        # 高影响力优先
        score += min(c.get("hIndex", 0) / 50, 1.0)

        return score

    scored = sorted(candidates, key=score_candidate, reverse=True)
    best = scored[0]

    # 最低质量门槛：名字要有一定相似度
    if score_candidate(best) < 0.5:
        return None

    return best


# ============================================================
# 学术质量打分
# ============================================================
def score_academic_quality(author: Dict) -> str:
    """根据 h-index、引用数、顶会论文评级"""
    h = author.get("h_index", 0) or 0
    cites = author.get("citation_count", 0) or 0
    top_papers = author.get("top_venue_paper_count", 0) or 0

    if h >= 30 or cites >= 10000 or top_papers >= 10:
        return "S"
    elif h >= 20 or cites >= 5000 or top_papers >= 5:
        return "A+"
    elif h >= 10 or cites >= 1000 or top_papers >= 2:
        return "A"
    elif h >= 5 or cites >= 200 or top_papers >= 1:
        return "B"
    else:
        return "C"


# ============================================================
# GitHub / Contact 关联
# ============================================================
def link_github_from_homepage(authors: List[Dict], out_dir: Path = None, prefix: str = "") -> List[Dict]:
    """从个人主页中提取 GitHub URL 和备用 Email，支持断点缓存"""
    log(f"\n🔗 联系方式挖掘: 个人主页解析")

    # 引入我们刚刚写的提取器
    import sys
    sys.path.append(str(SCRIPT_DIR))
    try:
        from extract_paper_email import extract_academic_contacts
    except ImportError:
        log("  ⚠️  未加载 extract_paper_email，跳过深度提取")
        return authors

    cache_file = out_dir / f"{prefix}_contact_cache.json" if out_dir else None
    cache = {}
    if cache_file and cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cache = json.load(f)
            log(f"  > 📦 发现邮箱网页解析进度缓存，恢复了 {len(cache)} 人的数据 (断点续传生效)!")
        except Exception:
            pass

    linked_github = 0
    found_email = 0
    new_crawls = 0

    for i, author in enumerate(authors):
        name = author.get("name", "")
        homepage = author.get("personal_website") or ""

        # 读取缓存
        cache_key = f"{name}::{homepage}"
        if cache_key in cache:
            # 用缓存的数据更新当前 author，还原之前挖出的字段
            cached_author = cache[cache_key]
            author.update(cached_author)
            if author.get("github_url"): linked_github += 1
            if author.get("email"): found_email += 1
            continue

        if not homepage:
            cache[cache_key] = author
            continue

        if new_crawls % 10 == 0 and new_crawls > 0:
            log(f"  进度: {i}/{len(authors)}...")

        new_crawls += 1

        # 直接是 GitHub 主页
        if "github.com" in homepage:
            import urllib.parse
            parsed = urllib.parse.urlparse(homepage)
            path_parts = [p for p in parsed.path.split('/') if p]
            if path_parts:
                username = path_parts[0]
                if username.lower() not in ("orgs", "topics", "collections", "sponsors"):
                    author["github_url"] = f"https://github.com/{username}"
                    linked_github += 1
                    cache[cache_key] = author
            continue

        # 爬个人主页找信息
        try:
            resp = requests.get(homepage, timeout=10, verify=False, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            if resp.status_code == 200:
                contacts = extract_academic_contacts(resp.text, homepage)
                
                # 提取 GitHub
                if contacts.get("github") and not author.get("github_url"):
                    author["github_url"] = contacts["github"]
                    linked_github += 1
                
                # 提取备用邮箱 (如果原始论文没有邮箱，尝试使用主页上的)
                if contacts.get("emails"):
                    # 不覆盖已有的有效邮箱，而是加到 extra_emails，如果本身为空则设置为首选
                    if not author.get("email"):
                        author["email"] = contacts["emails"][0]
                        found_email += 1
                    author["extra_emails"] = contacts["emails"]
                
                # 其他社交媒体保留
                author["linkedin_url"] = contacts.get("linkedin")
                author["twitter_url"] = contacts.get("twitter")
                
        except Exception:
            pass

        cache[cache_key] = author
        if cache_file and new_crawls % 20 == 0:
             with open(cache_file, "w") as f:
                 json.dump(cache, f, ensure_ascii=False)

        time.sleep(0.5)

    if cache_file and new_crawls > 0:
         with open(cache_file, "w") as f:
             json.dump(cache, f, ensure_ascii=False)

    log(f"✅ 联系方式挖掘: {linked_github} 人找到 GitHub URL，{found_email} 人通过主页补充了邮箱。")
    return authors


# ============================================================
# 分流输出
# ============================================================
def split_and_export(authors: List[Dict], output_prefix: str, out_dir: Path):
    """分离有/无 GitHub URL 的候选人，分别输出"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with_github = [a for a in authors if a.get("github_url")]
    without_github = [a for a in authors if not a.get("github_url")]

    # 有 GitHub URL → 格式化为 batch_runner 可以直接吃的格式
    pipeline_ready = []
    for a in with_github:
        pipeline_ready.append({
            "username": a["github_url"].split("/")[-1],
            "name": a.get("name", ""),
            "github_url": a.get("github_url", ""),
            "email": a.get("email"),
            "bio": None,
            "company": a.get("affiliation"),
            "location": None,
            "blog": a.get("personal_website"),
            "twitter_username": None,
            "public_repos": 0,
            "followers": 0,
            "following": 0,
            "created_at": None,
            "updated_at": None,
            "cooccurrence": 0,
            "ai_score": 1.0,
            "ai_signals": [f"scholar:{a.get('_academic_tier', 'B')}"],
            # 学术专有字段
            "_source": "scholar",
            "_h_index": a.get("h_index", 0),
            "_citation_count": a.get("citation_count", 0),
            "_conference": a.get("conferences", []),
        })

    # 直接入库（无 GitHub 但有邮箱）
    direct_import = []
    for a in without_github:
        if a.get("email"):
            direct_import.append({
                "name": a.get("name", ""),
                "email": a.get("email"),
                "github_url": None,
                "personal_website": a.get("personal_website"),
                "source": "scholar",
                "current_company": a.get("affiliation"),
                "notes": f"学术来源: {', '.join(a.get('conferences', []))}; h-index={a.get('h_index', 'N/A')}",
                "_h_index": a.get("h_index", 0),
                "_academic_tier": a.get("_academic_tier", "C"),
            })

    # 保存
    out_pipeline = out_dir / f"{output_prefix}_{timestamp}_github_pipeline.json"
    out_direct = out_dir / f"{output_prefix}_{timestamp}_direct_import.json"
    out_full = out_dir / f"{output_prefix}_{timestamp}_full.json"

    save_json(pipeline_ready, out_pipeline)
    save_json(direct_import, out_direct)
    save_json(authors, out_full)

    log(f"\n{'='*60}")
    log(f"📊 输出统计")
    log(f"{'='*60}")
    log(f"  总学者数:           {len(authors)}")
    log(f"  → 有 GitHub URL:    {len(with_github)} 人 → batch_runner 管道")
    log(f"  → 无 GitHub 有邮箱: {len(direct_import)} 人 → 直接入库")

    tier_counts = {}
    for a in authors:
        t = a.get("_academic_tier", "C")
        tier_counts[t] = tier_counts.get(t, 0) + 1

    log(f"\n  Tier 分布:")
    for t in ["S", "A+", "A", "B", "C"]:
        if t in tier_counts:
            log(f"    {t}: {tier_counts[t]} 人")

    log(f"\n  Pipeline 输出: {out_pipeline.name}")
    log(f"  直接入库输出:  {out_direct.name}")
    log(f"  完整数据:      {out_full.name}")

    return out_pipeline, out_direct


# ============================================================
# 主函数
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="学术渠道人才挖掘工具")
    parser.add_argument("--conference", type=str, default="iclr",
                       help="会议列表，逗号分隔: iclr,acl,neurips,icml,cvpr (默认: iclr)")
    parser.add_argument("--year", type=str, default="2024",
                       help="年份列表，逗号分隔: 2023,2024 (默认: 2024)")
    parser.add_argument("--max-papers", type=int, default=None,
                       help="每个会议最多采集论文数（测试用）")
    parser.add_argument("--input", type=str, default=None,
                       help="直接输入已有 JSON 文件，跳过采集阶段")
    parser.add_argument("--score-only", action="store_true",
                       help="只跑过滤+打分，不查 Semantic Scholar")
    parser.add_argument("--output-prefix", type=str, default="academic",
                       help="输出文件名前缀")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="目标输出目录 (如果提供，将覆盖默认目录)")
    parser.add_argument("--skip-github-link", action="store_true",
                       help="跳过 GitHub 关联（节省时间）")

    args = parser.parse_args()

    # 确定输出目录
    run_output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    run_output_dir.mkdir(parents=True, exist_ok=True)


    log("=" * 60)
    log("🎓 Academic Miner — 学术渠道人才挖掘")
    log(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)

    # 阶段 A：采集
    if args.input:
        log(f"\n📂 从文件加载: {args.input}")
        all_authors = load_json(Path(args.input))
        log(f"  已加载 {len(all_authors)} 条记录")
    else:
        conferences = [c.strip() for c in args.conference.split(",")]
        years = [int(y.strip()) for y in args.year.split(",")]

        all_authors = []
        for conf in conferences:
            for year in years:
                if conf.lower() == "iclr":
                    authors = collect_iclr_authors(year, args.max_papers)
                elif conf.lower() in ("acl", "emnlp", "naacl"):
                    authors = collect_acl_authors(year, args.max_papers)
                elif conf.lower() == "neurips":
                    authors = collect_neurips_authors(year, args.max_papers)
                elif conf.lower() == "icml":
                    authors = collect_icml_authors(year, args.max_papers)
                elif conf.lower() == "cvpr":
                    authors = collect_cvpr_authors(year, args.max_papers)
                else:
                    log(f"⚠️  暂不支持会议: {conf}，跳过")
                    continue
                all_authors.extend(authors)

        # 保存原始采集结果
        raw_path = run_output_dir / f"{args.output_prefix}_raw_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        save_json(all_authors, raw_path)

    # 阶段 B：去重 + 过滤 + 评分
    authors = deduplicate_authors(all_authors)
    filtered, chinese, foreign = filter_chinese_researchers(authors)

    if not args.score_only:
        # 阶段 C：Semantic Scholar 查询
        filtered = enrich_with_semantic_scholar(filtered, run_output_dir, args.output_prefix)

    # 打学术评级
    for a in filtered:
        a["_academic_tier"] = score_academic_quality(a)

    # 阶段 D：GitHub 关联
    if not args.skip_github_link:
        filtered = link_github_from_homepage(filtered, run_output_dir, args.output_prefix)

    # 输出
    split_and_export(filtered, args.output_prefix, run_output_dir)

    log(f"\n✅ 全流程完成！")


if __name__ == "__main__":
    main()
