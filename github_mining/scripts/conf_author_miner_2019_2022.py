#!/usr/bin/env python3
"""
2019-2022 顶会论文作者挖掘 — 找已就职 AI 人才
================================================
目标: 从 2019-2022 年顶级 AI 学术会议中挖掘作者，
    这批人到 2024 年已工作 3-5 年，大概率已就职。

数据源:
  - NeurIPS Proceedings: proceedings.neurips.cc (2019-2022)
  - ICML PMLR:  proceedings.mlr.press (v97/v119/v139/v162)
  - ICLR OpenReview: api2.openreview.net (2020-2022)
  - ACL Anthology: aclanthology.org (ACL/EMNLP/NAACL)
  - Semantic Scholar: fallback for any venue

目标会议 (2019-2022):
  NeurIPS, ICML, ICLR, CVPR, ICCV(2019,2021), ECCV(2020,2022)
  ACL, EMNLP, NAACL, AAAI

用法:
    # 测试运行（每会议仅取 30 篇，dry-run）
    S2_API_KEY=xxx python3 conf_author_miner_2019_2022.py --dry-run --max-papers 30

    # 正式运行全量
    S2_API_KEY=xxx python3 conf_author_miner_2019_2022.py

    # 只跑某几个会议+年份（分批运行）
    S2_API_KEY=xxx python3 conf_author_miner_2019_2022.py --conferences NeurIPS,ICML --years 2020,2021

    # 仅华人作者（减少 S2 ID 补全调用量）
    S2_API_KEY=xxx python3 conf_author_miner_2019_2022.py --chinese-only

输出目录结构 (遵循 CONVENTIONS.md):
    data/conf_2019_2022/runs/pipeline_2019_2022_YYYYMMDD_HHMMSS/
      outputs/
        authors_raw_2019_2022_YYYYMMDD_HHMMSS.json    所有作者原始数据
        authors_import_2019_2022_YYYYMMDD_HHMMSS.json 准备导入 DB 的记录
      logs/
        run_YYYYMMDD_HHMMSS.log                        运行日志
    data/conf_2019_2022/_cache/                        跨 run 共享缓存
      paper_cache_YEAR.json                            ← 年份隔离缓存（防交叉污染）
      s2_name_cache_YEAR.json

环境变量:
    S2_API_KEY    Semantic Scholar API Key（强烈推荐，否则严重限流）
    DB_PATH       数据库路径（默认自动推断，建议显式指定避免影子 DB）
"""

import os
import sys
import json
import time
import random
import argparse
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

# ============================================================
# 路径配置
# ============================================================
SCRIPT_DIR      = Path(__file__).parent
REPO_ROOT       = SCRIPT_DIR.parent.parent
# DB 路径：优先用环境变量，防止影子 DB（CONVENTIONS.md 规则）
DB_PATH_DEFAULT = Path(os.getenv(
    "DB_PATH",
    str(REPO_ROOT / "personal-ai-headhunter" / "data" / "headhunter_dev.db")
))

RUN_TS    = datetime.now().strftime("%Y%m%d_%H%M%S")
# 遵循 CONVENTIONS.md：runs/pipeline_YEARS_TS/ 独立目录
RUN_DIR   = (SCRIPT_DIR.parent / "data" / "conf_2019_2022" / "runs"
             / f"pipeline_2019_2022_{RUN_TS}")
OUTPUT_DIR = RUN_DIR / "outputs"
LOG_DIR    = RUN_DIR / "logs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 跨 run 共享缓存（年份隔离，防交叉污染）
CACHE_DIR = SCRIPT_DIR.parent / "data" / "conf_2019_2022" / "_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 目标会议配置
# ============================================================
# 格式: (会议名, 年份列表, 采集方法)
TARGET_CONFERENCES = [
    # --- 综合 AI ---
    ("NeurIPS", [2019, 2020, 2021, 2022], "neurips"),
    ("ICML",   [2019, 2020, 2021, 2022], "icml_pmlr"),
    ("ICLR",   [2020, 2021, 2022],       "openreview"),  # 2019 ICLR 较小跳过
    ("AAAI",   [2020, 2021, 2022],       "s2_venue"),
    # --- 计算机视觉 ---
    ("CVPR",   [2019, 2020, 2021, 2022], "s2_venue"),
    ("ICCV",   [2019, 2021],             "s2_venue"),    # 隔年举办
    ("ECCV",   [2020, 2022],             "s2_venue"),    # 隔年举办
    # --- NLP ---
    ("ACL",    [2019, 2020, 2021, 2022], "acl_anthology"),
    ("EMNLP",  [2019, 2020, 2021, 2022], "acl_anthology"),
    ("NAACL",  [2019, 2021],             "acl_anthology"),  # 隔年举办
]

# PMLR 卷号映射
ICML_PMLR_MAP = {
    2024: "v235", 2023: "v202", 2022: "v162",
    2021: "v139", 2020: "v119", 2019: "v97",
}

# S2 venue 字段真实名称（与显示名/缩写不同）
# 通过查询已知论文的 venue 字段确认
S2_VENUE_ALIASES = {
    "NeurIPS": "Neural Information Processing Systems",
    "NIPS":    "Neural Information Processing Systems",
    "ICLR":   "International Conference on Learning Representations",
    "ICML":   "International Conference on Machine Learning",
    "CVPR":   "Computer Vision and Pattern Recognition",
    "ICCV":   "International Conference on Computer Vision",
    "ECCV":   "European Conference on Computer Vision",
    "ACL":    "Annual Meeting of the Association for Computational Linguistics",
    "EMNLP":  "Empirical Methods in Natural Language Processing",
    "NAACL":  "North American Chapter of the Association for Computational Linguistics",
    "AAAI":   "AAAI Conference on Artificial Intelligence",
}

# 顶级会议集（用于评级）
TOP_VENUES = {
    "NeurIPS", "ICML", "ICLR", "CVPR", "ECCV", "ICCV",
    "ACL", "EMNLP", "NAACL", "AAAI", "IJCAI",
    "INTERSPEECH", "ICASSP", "KDD", "WWW",
}

# 华人识别信号
CHINESE_NAME_PATTERN = re.compile(
    r'[\u4e00-\u9fff]|'  # CJK 汉字
    r'\b(?:zhang|wang|li|liu|chen|yang|huang|zhao|wu|sun|'
    r'zhou|xu|lin|ma|he|zhu|gao|luo|zheng|xiao|'
    r'tang|han|hu|wei|xie|qian|feng|dong|peng|'
    r'shi|shen|jiang|liang|cai|cao|ye|deng|cheng|'
    r'bai|ding|lu|zeng|fu|yao|pan|yu|hong|fan)\b',
    re.IGNORECASE
)

# ============================================================
# 工具函数
# ============================================================
def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def rate_sleep(has_key: bool = None):
    if has_key is None:
        has_key = bool(os.getenv("S2_API_KEY", ""))
    if has_key:
        time.sleep(random.uniform(0.12, 0.25))
    else:
        time.sleep(random.uniform(1.0, 1.5))


def http_get(url: str, params: Dict = None, headers: Dict = None,
             retries: int = 3, timeout: int = 20) -> Optional[requests.Response]:
    _headers = {"User-Agent": "ConfAuthorMiner/1.0 (academic-talent-sourcing)"}
    if headers:
        _headers.update(headers)
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=_headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 30)) + random.uniform(2, 8)
                log(f"  ⏳ 限流，等待 {wait:.0f}s…")
                time.sleep(wait)
            elif resp.status_code == 404:
                return None
            else:
                log(f"  ⚠️ HTTP {resp.status_code}: {url[:80]}")
                time.sleep(3)
        except Exception as e:
            log(f"  ❌ 请求异常: {e}")
            time.sleep(3 * (attempt + 1))
    return None


def s2_get(endpoint: str, params: Dict = None) -> Optional[Dict]:
    url = f"https://api.semanticscholar.org/graph/v1/{endpoint}"
    headers = {"User-Agent": "ConfAuthorMiner/1.0"}
    api_key = os.getenv("S2_API_KEY", "")
    if api_key:
        headers["x-api-key"] = api_key
    resp = http_get(url, params=params, headers=headers)
    if resp:
        try:
            return resp.json()
        except Exception:
            pass
    return None


def load_cache(path: Path) -> Dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(cache: Dict, path: Path):
    path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def is_likely_chinese(name: str, affiliation: str = "") -> bool:
    """粗略判断是否华人"""
    combined = f"{name} {affiliation}".lower()
    if CHINESE_NAME_PATTERN.search(name):
        return True
    # 中国大学/机构
    cn_orgs = ["tsinghua", "peking", "zhejiang", "fudan", "ustc", "sjtu",
               "nju", "ict", "cas", "cuhk", "hkust", "ntu", "nus",
               "bytedance", "alibaba", "tencent", "baidu", "huawei",
               "sensetime", "megvii", "kuaishou", "meituan",
               "清华", "北大", "浙大", "复旦", "科大", "交大"]
    for org in cn_orgs:
        if org in combined:
            return True
    return False


# ============================================================
# 采集方法 1: Semantic Scholar venue 搜索
# ============================================================
def collect_via_s2_venue(conf_name: str, year: int, max_papers: int,
                          cache: Dict) -> List[Dict]:
    """
    通过 S2 Paper Search 按 venue+year 获取论文。
    使用 S2_VENUE_ALIASES 映射真实 venue 字段名。
    """
    cache_key = f"s2_venue::{conf_name}::{year}"
    if cache_key in cache:
        log(f"  📦 缓存命中: {conf_name} {year} ({len(cache[cache_key])} 篇)")
        return cache[cache_key]

    # 真实 venue 名（S2 数据库中存的格式）
    s2_venue = S2_VENUE_ALIASES.get(conf_name, conf_name)
    log(f"  🔍 S2 venue 搜索: {conf_name} {year} (venue={s2_venue!r})")
    authors = []
    offset = 0
    limit = 100
    has_key = bool(os.getenv("S2_API_KEY", ""))

    while True:
        result = s2_get("paper/search", {
            "query": s2_venue,
            "fields": "title,year,venue,authors",
            "year": f"{year}-{year}",
            "venue": s2_venue,
            "limit": limit,
            "offset": offset,
        })
        rate_sleep(has_key)

        if not result:
            break

        papers = result.get("data", [])
        if not papers:
            break

        for paper in papers:
            if paper.get("year") != year:
                continue
            # venue 字段匹配（用别名或简称任一）
            venue = paper.get("venue", "").lower()
            if not (s2_venue.lower() in venue or conf_name.lower() in venue):
                continue
            for author in paper.get("authors", []):
                aid = author.get("authorId")
                name = author.get("name", "")
                if aid and name:
                    authors.append({
                        "s2_id": aid,
                        "name": name,
                        "conference": f"{conf_name} {year}",
                        "paper_title": paper.get("title", ""),
                    })

        if max_papers and len(authors) >= max_papers:
            authors = authors[:max_papers]
            break

        offset += limit
        total = result.get("total", 0)
        if offset >= total or offset >= 10000:
            break

    log(f"  ✅ {conf_name} {year}: {len(authors)} 条作者记录")
    cache[cache_key] = authors
    return authors


# ============================================================
# 采集方法 2: NeurIPS Proceedings
# ============================================================
def collect_neurips(year: int, max_papers: int, cache: Dict) -> List[Dict]:
    cache_key = f"neurips::{year}"
    if cache_key in cache:
        log(f"  📦 缓存命中: NeurIPS {year} ({len(cache[cache_key])} 条)")
        return cache[cache_key]

    log(f"  🔍 爬取 NeurIPS {year}")
    url = f"https://proceedings.neurips.cc/paper_files/paper/{year}"
    resp = http_get(url)
    if not resp:
        log(f"  ❌ NeurIPS {year} 页面不可访问")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    authors = []
    count = 0

    # 真实 HTML 结构: ul.paper-list > li > div.paper-content
    for paper_li in soup.select("ul.paper-list li"):
        if max_papers and count >= max_papers:
            break
        content_div = paper_li.select_one("div.paper-content")
        if not content_div:
            continue
        # 标题
        title_tag = content_div.select_one("a")
        title = title_tag.get_text(strip=True) if title_tag else ""
        # 作者 —— 通常在 title 下方的 <i> 或 <p> 标签
        author_tag = content_div.select_one("i") or content_div.select_one(".author")
        if author_tag:
            author_text = author_tag.get_text(strip=True)
            for name in re.split(r",\s*", author_text):
                name = name.strip()
                if name and 2 < len(name) < 60:
                    authors.append({
                        "s2_id": None,
                        "name": name,
                        "conference": f"NeurIPS {year}",
                        "paper_title": title,
                    })
        count += 1

    # 如果网页解析未拿到作者（仅拿到标题链接），fallback 到 S2
    if not authors or len(authors) < 50:
        log(f"  ⚠️ NeurIPS {year} 网页解析不到作者，改用 S2 venue 搜索")
        s2_authors = collect_via_s2_venue("NeurIPS", year, max_papers, cache)
        if s2_authors:
            cache[cache_key] = s2_authors
            return s2_authors

    log(f"  ✅ NeurIPS {year}: {len(authors)} 条记录")
    cache[cache_key] = authors
    return authors


# ============================================================
# 采集方法 3: ICML PMLR
# ============================================================
def collect_icml_pmlr(year: int, max_papers: int, cache: Dict) -> List[Dict]:
    cache_key = f"icml_pmlr::{year}"
    if cache_key in cache:
        log(f"  📦 缓存命中: ICML {year} ({len(cache[cache_key])} 条)")
        return cache[cache_key]

    vol = ICML_PMLR_MAP.get(year)
    if not vol:
        log(f"  ⚠️ ICML {year} 无对应 PMLR 卷号")
        return []

    log(f"  🔍 爬取 ICML {year} (PMLR {vol})")
    url = f"https://proceedings.mlr.press/{vol}/"
    resp = http_get(url)
    if not resp:
        log(f"  ❌ PMLR {vol} 页面不可访问")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    authors = []
    count = 0

    for paper_div in soup.select("div.paper"):
        if max_papers and count >= max_papers:
            break
        title_tag = paper_div.select_one(".paper-title") or paper_div.select_one("p.title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        author_tag = paper_div.select_one(".authors") or paper_div.select_one("p.details")
        if author_tag:
            author_text = author_tag.get_text(strip=True)
            for name in re.split(r",\s*|\band\b", author_text):
                name = name.strip().rstrip(".")
                if name and 2 < len(name) < 50:
                    authors.append({
                        "s2_id": None,
                        "name": name,
                        "conference": f"ICML {year}",
                        "paper_title": title,
                    })
        count += 1

    log(f"  ✅ ICML {year}: {len(authors)} 条记录 (来自 {count} 篇论文)")
    cache[cache_key] = authors
    return authors


# ============================================================
# 采集方法 4: ICLR OpenReview
# ============================================================
OPENREVIEW_VENUES = {
    2022: "ICLR.cc/2022/Conference",
    2021: "ICLR.cc/2021/Conference",
    2020: "ICLR.cc/2020/Conference",
    2019: "ICLR.cc/2019/Conference",
}

def collect_iclr_openreview(year: int, max_papers: int, cache: Dict) -> List[Dict]:
    """
    ICLR: 直接用 S2 venue 搜索（OpenReview API v2 不稳定，历史年份需认证）。
    ICLR 在 S2 中的 venue 字段为 'International Conference on Learning Representations'。
    """
    cache_key = f"iclr_or::{year}"
    if cache_key in cache:
        log(f"  📦 缓存命中: ICLR {year} ({len(cache[cache_key])} 条)")
        return cache[cache_key]

    log(f"  🔍 ICLR {year} (via S2 venue 搜索)")
    # 直接走 S2 venue 搜索，已知 venue 名
    authors = collect_via_s2_venue("ICLR", year, max_papers, cache)
    # 写入独立缓存 key 以便下次命中
    cache[cache_key] = authors
    log(f"  ✅ ICLR {year}: {len(authors)} 条记录")
    return authors


# ============================================================
# 采集方法 5: ACL Anthology
# ============================================================
def collect_acl_anthology(conf_name: str, year: int, max_papers: int,
                           cache: Dict) -> List[Dict]:
    cache_key = f"acl_anthology::{conf_name}::{year}"
    if cache_key in cache:
        log(f"  📦 缓存命中: {conf_name} {year} ({len(cache[cache_key])} 条)")
        return cache[cache_key]

    log(f"  🔍 ACL Anthology: {conf_name} {year}")
    conf_map = {
        "ACL": "acl", "EMNLP": "emnlp", "NAACL": "naacl-hlt",
        "COLING": "coling", "EACL": "eacl",
    }
    conf_short = conf_map.get(conf_name.upper(), conf_name.lower())

    authors = []
    # ACL Anthology 事件页面 URL
    # 例如: https://aclanthology.org/events/acl-2021/
    volume_url = f"https://aclanthology.org/events/{conf_short}-{year}/"
    resp = http_get(volume_url)
    if resp and resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        count = 0
        # 正确的 HTML 结构: div.card > div.card-body > p 包含 strong (标题) 和 a (作者)
        for paper_card in soup.select("div.card-body > p"):
            if max_papers and count >= max_papers:
                break
            title_tag = paper_card.select_one("strong a") or paper_card.select_one("a")
            title = title_tag.get_text(strip=True) if title_tag else ""
            # 作者链接 href 包含 /people/
            for a_tag in paper_card.select("a[href*='/people/']"):
                name = a_tag.get_text(strip=True)
                if name and 2 < len(name) < 60:
                    authors.append({
                        "s2_id": None,
                        "name": name,
                        "conference": f"{conf_name} {year}",
                        "paper_title": title,
                    })
            count += 1

    # fallback: S2 venue 搜索
    if not authors:
        log(f"  ⚠️ ACL Anthology 解析失败 ({volume_url})，fallback 至 S2")
        authors = collect_via_s2_venue(conf_name, year, max_papers, cache)

    log(f"  ✅ {conf_name} {year}: {len(authors)} 条记录")
    cache[cache_key] = authors
    return authors


# ============================================================
# S2 作者 ID 补全 & 富化
# ============================================================
def resolve_s2_ids(authors: List[Dict], s2_cache: Dict) -> List[Dict]:
    """
    对没有 s2_id 的作者，通过 S2 Author Search 补全。
    带缓存避免重复查询。
    """
    has_key = bool(os.getenv("S2_API_KEY", ""))
    enriched = []
    batch_new = 0

    for i, author in enumerate(authors):
        if author.get("s2_id"):
            enriched.append(author)
            continue

        name = author.get("name", "").strip()
        if not name:
            continue

        cache_key = f"name_to_s2::{name.lower()}"
        if cache_key in s2_cache:
            author["s2_id"] = s2_cache[cache_key]
            enriched.append(author)
            continue

        # 搜索 S2
        result = s2_get("author/search", {
            "query": name,
            "fields": "name,affiliations,hIndex,homepage,externalIds",
            "limit": 3,
        })
        rate_sleep(has_key)

        s2_id = None
        if result and result.get("data"):
            # 取名字最匹配的第一个
            for candidate in result["data"]:
                cname = candidate.get("name", "").lower()
                if name.lower() in cname or cname in name.lower():
                    s2_id = candidate.get("authorId")
                    # 顺带补充机构
                    if not author.get("affiliation"):
                        affils = candidate.get("affiliations") or []
                        if affils:
                            author["affiliation"] = affils[0]
                    break
            if not s2_id:
                s2_id = result["data"][0].get("authorId")

        s2_cache[cache_key] = s2_id
        author["s2_id"] = s2_id
        enriched.append(author)
        batch_new += 1

        if batch_new % 200 == 0:
            log(f"  S2 ID 补全进度: {i}/{len(authors)}")

    return enriched


# ============================================================
# 聚合 & 去重 & 评分
# ============================================================
def aggregate_authors(all_records: List[Dict]) -> List[Dict]:
    """
    按 s2_id 或 name 去重，合并出现的会议列表。
    """
    by_s2id: Dict[str, Dict] = {}
    by_name: Dict[str, Dict] = {}

    for r in all_records:
        s2_id = r.get("s2_id")
        name = r.get("name", "").strip()
        conf = r.get("conference", "")

        if s2_id:
            if s2_id not in by_s2id:
                by_s2id[s2_id] = {**r, "conferences": [conf], "paper_count": 1}
            else:
                if conf not in by_s2id[s2_id]["conferences"]:
                    by_s2id[s2_id]["conferences"].append(conf)
                by_s2id[s2_id]["paper_count"] = by_s2id[s2_id].get("paper_count", 1) + 1
        elif name:
            key = name.lower()
            if key not in by_name:
                by_name[key] = {**r, "conferences": [conf], "paper_count": 1}
            else:
                if conf not in by_name[key]["conferences"]:
                    by_name[key]["conferences"].append(conf)
                by_name[key]["paper_count"] = by_name[key].get("paper_count", 1) + 1

    result = list(by_s2id.values()) + list(by_name.values())
    log(f"  📊 聚合后: {len(result)} 位不重复作者 (S2ID: {len(by_s2id)}, 仅姓名: {len(by_name)})")
    return result


def score_tier(author: Dict) -> str:
    h = author.get("h_index", 0) or 0
    cites = author.get("citation_count", 0) or 0
    confs = author.get("conferences", [])
    top_conf_count = sum(1 for c in confs if any(v in c for v in TOP_VENUES))
    if h >= 20 or cites >= 5000 or top_conf_count >= 3:
        return "S"
    elif h >= 10 or cites >= 1000 or top_conf_count >= 2:
        return "A+"
    elif h >= 5 or cites >= 200 or top_conf_count >= 1:
        return "A"
    elif h >= 2 or cites >= 50:
        return "B"
    else:
        return "C"


# ============================================================
# DB 去重 & 导入
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
    return existing_names, existing_s2_ids


def build_import_record(author: Dict) -> Dict:
    tier = score_tier(author)
    confs = author.get("conferences", [])
    affil = author.get("affiliation", "") or ""
    homepage = author.get("homepage", "") or ""

    github_url = None
    if homepage and "github.com" in homepage:
        github_url = homepage

    structured_tags = {
        "academic_tier": tier,
        "h_index": author.get("h_index", 0),
        "citation_count": author.get("citation_count", 0),
        "s2_id": author.get("s2_id"),
        "conferences": confs,
        "paper_count": author.get("paper_count", 1),
        "source_method": "conf_paper_author_2019_2022",
        "run_ts": RUN_TS,
        "likely_chinese": is_likely_chinese(author.get("name", ""), affil),
        "graduation_range": "2019-2022",
    }

    notes = (
        f"【来源】2019-2022届顶会论文作者\n"
        f"【会议】{', '.join(confs)}\n"
        f"【机构】{affil}\n"
        f"【代表论文】{author.get('paper_title', '')[:100]}"
    )

    return {
        "name": author.get("name", ""),
        "current_company": affil,
        "current_title": "Researcher / Engineer",
        "talent_tier": tier,
        "pipeline_stage": "new",
        "source": "academic",
        "source_file": f"conf_2019_2022_{RUN_TS}",
        "personal_website": homepage or None,
        "github_url": github_url,
        "linkedin_url": None,
        "email": None,
        "structured_tags": json.dumps(structured_tags, ensure_ascii=False),
        "ai_summary": None,
        "notes": notes,
    }


def import_to_db(records: List[Dict], db_path: Path, dry_run: bool) -> int:
    existing_names, existing_s2_ids = load_existing_keys(db_path)
    new_records = []
    skipped = 0

    for r in records:
        name_lower = r["name"].strip().lower()
        tags = json.loads(r["structured_tags"])
        s2_id = str(tags.get("s2_id", "") or "")

        if not r["name"].strip():
            skipped += 1
            continue
        if name_lower in existing_names:
            skipped += 1
            continue
        if s2_id and s2_id in existing_s2_ids:
            skipped += 1
            continue
        new_records.append(r)

    log(f"  📊 去重: {len(new_records)} 新增，{skipped} 已在库中跳过")

    if dry_run:
        log("  🔍 Dry-run 模式，不写入数据库")
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
            log(f"  ⚠️ 插入失败 {r['name']}: {e}")
    conn.commit()
    conn.close()
    log(f"  ✅ 成功写入 {inserted} 条")
    return inserted


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="2019-2022 顶会作者挖掘")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-papers", type=int, default=None,
                        help="每个会议最多采集论文数（测试用）")
    parser.add_argument("--conferences", type=str, default=None,
                        help="逗号分隔的会议名，如 NeurIPS,ICML，默认全部")
    parser.add_argument("--years", type=str, default=None,
                        help="逗号分隔的年份，如 2020,2021，默认全部")
    parser.add_argument("--chinese-only", action="store_true",
                        help="只保留疑似华人作者")
    parser.add_argument("--min-tier", type=str, default="C",
                        choices=["S", "A+", "A", "B", "C"])
    parser.add_argument("--db-path", type=str, default=str(DB_PATH_DEFAULT))
    parser.add_argument("--skip-s2-resolve", action="store_true",
                        help="跳过 S2 ID 补全（快速模式，直接以姓名导入）")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    has_key = bool(os.getenv("S2_API_KEY", ""))
    tier_order = {"S": 0, "A+": 1, "A": 2, "B": 3, "C": 4}

    # 过滤会议 & 年份
    conf_filter = set(args.conferences.split(",")) if args.conferences else None
    year_filter = set(int(y) for y in args.years.split(",")) if args.years else None

    targets = [
        (conf, years, method) for conf, years, method in TARGET_CONFERENCES
        if (conf_filter is None or conf in conf_filter)
    ]
    if year_filter:
        targets = [(c, [y for y in ys if y in year_filter], m) for c, ys, m in targets]
        targets = [(c, ys, m) for c, ys, m in targets if ys]

    log(f"🚀 2019-2022 顶会作者挖掘开始")
    log(f"   目标: {', '.join(f'{c}({min(ys)}-{max(ys)})' for c,ys,m in targets)}")
    log(f"   S2 API Key: {'有' if has_key else '无'}")
    log(f"   每会议上限: {args.max_papers or '不限'}")
    log(f"   仅华人: {args.chinese_only}")
    log(f"   写入 DB: {'否 (dry-run)' if args.dry_run else '是'}")
    log(f"   输出目录: {OUTPUT_DIR}")

    # 加载缓存
    paper_cache_file = CACHE_DIR / "paper_cache.json"
    s2_cache_file = CACHE_DIR / "s2_name_cache.json"
    paper_cache = load_cache(paper_cache_file)
    s2_cache = load_cache(s2_cache_file)

    log(f"\n📦 缓存: 论文={len(paper_cache)} 条, S2名字={len(s2_cache)} 条")

    # ── 采集阶段 ──
    all_raw: List[Dict] = []
    for conf_name, years, method in targets:
        log(f"\n{'='*55}")
        log(f"📚 {conf_name}  ({', '.join(str(y) for y in years)})")
        for year in sorted(years):
            if method == "neurips":
                records = collect_neurips(year, args.max_papers, paper_cache)
            elif method == "icml_pmlr":
                records = collect_icml_pmlr(year, args.max_papers, paper_cache)
            elif method == "openreview":
                records = collect_iclr_openreview(year, args.max_papers, paper_cache)
            elif method == "acl_anthology":
                records = collect_acl_anthology(conf_name, year, args.max_papers, paper_cache)
            else:  # s2_venue
                records = collect_via_s2_venue(conf_name, year, args.max_papers, paper_cache)

            all_raw.extend(records)
            # 定期保存缓存
            save_cache(paper_cache, paper_cache_file)

    log(f"\n📊 采集完成: {len(all_raw)} 条原始记录")

    # ── 华人过滤 ──
    if args.chinese_only:
        pre_filter = len(all_raw)
        all_raw = [r for r in all_raw if is_likely_chinese(r.get("name", ""), r.get("affiliation", ""))]
        log(f"   华人过滤: {len(all_raw)}/{pre_filter}")

    # ── S2 ID 补全 ──
    if not args.skip_s2_resolve:
        log(f"\n🔗 补全 S2 Author ID ({len(all_raw)} 条)…")
        all_raw = resolve_s2_ids(all_raw, s2_cache)
        save_cache(s2_cache, s2_cache_file)
    else:
        log("  ⚡ 跳过 S2 ID 补全")

    # ── 聚合去重 ──
    log(f"\n🔀 聚合作者记录…")
    aggregated = aggregate_authors(all_raw)

    # 保存原始聚合结果
    raw_file = OUTPUT_DIR / f"authors_raw_{RUN_TS}.json"
    raw_file.write_text(json.dumps(aggregated, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"💾 原始结果: {raw_file.name}")

    # ── 评级 & 过滤 ──
    tier_stats = {"S": 0, "A+": 0, "A": 0, "B": 0, "C": 0}
    import_records = []
    min_tier_val = tier_order[args.min_tier]

    for author in aggregated:
        tier = score_tier(author)
        tier_stats[tier] = tier_stats.get(tier, 0) + 1
        if tier_order.get(tier, 99) <= min_tier_val:
            import_records.append(build_import_record(author))

    log(f"\n🏆 评级分布:")
    for t, cnt in tier_stats.items():
        log(f"   {t}: {cnt} 人")
    log(f"   → 准备导入 ({args.min_tier}+): {len(import_records)} 人")

    # 保存导入文件
    import_file = OUTPUT_DIR / f"authors_import_{RUN_TS}.json"
    import_file.write_text(json.dumps(import_records, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"💾 导入数据: {import_file.name}")

    # Top 20 预览
    top20 = sorted(
        import_records,
        key=lambda r: (
            {"S": 0, "A+": 1, "A": 2, "B": 3, "C": 4}.get(r["talent_tier"], 9),
            -(json.loads(r["structured_tags"]).get("h_index") or 0)
        )
    )[:20]
    log(f"\n🌟 Top 20 预览:")
    log(f"{'姓名':<30} {'机构':<35} {'级':<4} {'会议'}")
    log("-" * 90)
    for r in top20:
        tags = json.loads(r["structured_tags"])
        confs = ", ".join(tags.get("conferences", [])[:3])
        log(f"{r['name']:<30} {r['current_company']:<35} {r['talent_tier']:<4} {confs}")

    # ── 写入 DB ──
    if import_records:
        log(f"\n🗃️  写入数据库…")
        inserted = import_to_db(import_records, db_path, dry_run=args.dry_run)
        log(f"\n✅ 完成! 新增 {inserted} 名候选人")
    else:
        log(f"\n⚠️  没有符合条件的候选人")

    log(f"📁 输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
