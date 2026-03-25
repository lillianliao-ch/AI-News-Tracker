#!/usr/bin/env python3
"""
竞赛获奖者人才挖掘工具 — Competition Miner
从 Kaggle / Codeforces / NOI / ICPC 采集高水平竞赛选手

用法:
    # Codeforces 国际大师级以上（无需 API Key）
    python3 competition_miner.py --competition codeforces --min-rating 2200 --max-users 500

    # Kaggle 指定比赛 Top 200（需 KAGGLE_USERNAME + KAGGLE_KEY 环境变量）
    python3 competition_miner.py --competition kaggle --slug imagenet-object-localization-challenge --top-n 200

    # NOI 金牌名单（2020-2024）
    python3 competition_miner.py --competition noi --year 2020,2021,2022,2023,2024

    # ICPC Asia 区域赛 金奖
    python3 competition_miner.py --competition icpc --year 2023,2024

    # 批量运行所有渠道
    python3 competition_miner.py --competition all --output-dir /path/to/dir
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
# 路径配置（与 academic_miner.py 保持一致）
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

# 输出目录
OUTPUT_DIR = GITHUB_MINING_DIR / "data" / "competition"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Serper API Key
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")


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


def load_cache(cache_file: Path) -> Dict:
    if cache_file and cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cache = json.load(f)
            log(f"  📦 读取缓存 {len(cache)} 条（断点续传）")
            return cache
        except Exception as e:
            log(f"  ⚠️ 读取缓存失败: {e}")
    return {}


def save_cache(cache: Dict, cache_file: Path):
    if cache_file:
        with open(cache_file, "w") as f:
            json.dump(cache, f, ensure_ascii=False)


def http_get(url: str, params: Dict = None, headers: Dict = None,
             retries: int = 3, timeout: int = 15) -> Optional[requests.Response]:
    _headers = {"User-Agent": "CompetitionMiner/1.0 (talent-sourcing-tool)"}
    if headers:
        _headers.update(headers)
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=_headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 30)) + random.uniform(1, 5)
                log(f"  ⏳ 限流，等待 {wait:.0f}s...")
                time.sleep(wait)
            elif resp.status_code == 404:
                return None
            else:
                log(f"  ⚠️ HTTP {resp.status_code}: {url}")
                time.sleep(2)
        except Exception as e:
            log(f"  ❌ 请求异常 (尝试 {attempt+1}/{retries}): {e}")
            time.sleep(3 * (attempt + 1))
    return None


# ============================================================
# Phase A1: Kaggle 竞赛 Leaderboard
# ============================================================

# 预设一批 AI/CV/NLP 相关比赛（可扩展）
KAGGLE_AI_COMPETITIONS = [
    # 计算机视觉
    "imagenet-object-localization-challenge",
    "coco-detection",
    "open-images-2019-object-detection",
    "google-landmarks-2021",
    "google-universal-image-embedding",
    # NLP / LLM
    "lmsys-chatbot-arena-leaderboard",
    "feedback-prize-english-language-learning",
    "commonlit-evaluate-student-summaries",
    # 多模态 / 视频
    "google-research-identify-contrails-reduce-global-warming",
    "rsna-2024-lumbar-spine-degenerative-classification",
    # 推荐系统
    "recsys-challenge-2023",
]


def collect_kaggle_winners(slug: str, top_n: int = 100,
                           out_dir: Path = None, prefix: str = "") -> List[Dict]:
    """
    采集 Kaggle 竞赛排行榜 Top-N 选手
    需要环境变量: KAGGLE_USERNAME + KAGGLE_KEY
    """
    log(f"\n{'='*60}")
    log(f"🏆 采集 Kaggle 竞赛: {slug}  (Top {top_n})")
    log(f"{'='*60}")

    username = os.getenv("KAGGLE_USERNAME")
    api_key = os.getenv("KAGGLE_KEY")

    if not username or not api_key:
        log("  ⚠️ 未设置 KAGGLE_USERNAME / KAGGLE_KEY，尝试以游客方式爬取公开页面")
        return _collect_kaggle_public(slug, top_n)

    # 使用 Kaggle 官方 REST API
    auth = (username, api_key)
    lb_url = f"https://www.kaggle.com/api/v1/competitions/{slug}/leaderboard/view"
    resp = http_get(lb_url, headers={"Authorization": f"Basic {_basic_auth(username, api_key)}"})

    if not resp:
        log(f"  ⚠️ Kaggle API 失败，降级到公开页面爬取")
        return _collect_kaggle_public(slug, top_n)

    try:
        data = resp.json()
    except Exception:
        log("  ❌ Kaggle API 返回非 JSON")
        return _collect_kaggle_public(slug, top_n)

    submissions = data.get("submissions", [])[:top_n]
    winners = []
    for item in submissions:
        team_name = item.get("teamName", "") or item.get("userName", "")
        score = item.get("score")
        rank = item.get("rank")
        winners.append({
            "name": team_name,
            "competition": slug,
            "rank": rank,
            "score": score,
            "source": "kaggle",
            "email": None,
            "github_url": None,
            "affiliation": None,
            "personal_website": f"https://www.kaggle.com/{team_name}",
        })

    log(f"✅ Kaggle {slug}: 获取 {len(winners)} 名选手")
    # 进一步抓取每位选手 Profile 补充 github / website
    winners = _enrich_kaggle_profiles(winners, out_dir=out_dir, prefix=prefix)
    return winners


def _basic_auth(username: str, api_key: str) -> str:
    import base64
    credentials = f"{username}:{api_key}".encode()
    return base64.b64encode(credentials).decode()


def _collect_kaggle_public(slug: str, top_n: int) -> List[Dict]:
    """无 API Key 时，爬取 Kaggle 公开排行榜页面"""
    url = f"https://www.kaggle.com/competitions/{slug}/leaderboard"
    resp = http_get(url)
    if not resp:
        log(f"  ❌ 无法访问 Kaggle 公开页面")
        return []

    # Kaggle 用 Redux state 注入数据（JSON embeds in <script>）
    match = re.search(r'"leaderboard":\{"pageData":(.*?),"totalTeams"', resp.text, re.DOTALL)
    winners = []
    if match:
        try:
            teams = json.loads(match.group(1))
            for item in (teams if isinstance(teams, list) else [])[:top_n]:
                team_name = item.get("teamName") or item.get("name") or ""
                winners.append({
                    "name": team_name,
                    "competition": slug,
                    "rank": item.get("rank"),
                    "score": item.get("score"),
                    "source": "kaggle",
                    "email": None,
                    "github_url": None,
                    "affiliation": None,
                    "personal_website": f"https://www.kaggle.com/{team_name}",
                })
        except Exception as e:
            log(f"  ⚠️ Kaggle 页面解析失败: {e}")

    log(f"  📊 公开页面获取 {len(winners)} 名")
    return winners


def _enrich_kaggle_profiles(winners: List[Dict],
                             out_dir: Optional[Path] = None,
                             prefix: str = "") -> List[Dict]:
    """抓取 Kaggle 用户 Profile 补充 GitHub / 简介"""
    cache_file = out_dir / f"{prefix}_kaggle_profile_cache.json" if out_dir else None
    cache = load_cache(cache_file) if cache_file else {}

    enriched = []
    new_crawls = 0
    for i, w in enumerate(winners):
        team_name = w.get("name", "")
        if not team_name:
            enriched.append(w)
            continue

        cache_key = f"kaggle_profile::{team_name}"
        if cache_key in cache:
            enriched.append({**w, **cache[cache_key]})
            continue

        # 请求 Kaggle 用户 API
        profile_url = f"https://www.kaggle.com/api/v1/users/{team_name}"
        resp = http_get(profile_url)
        if resp:
            try:
                profile = resp.json()
                updates = {
                    "affiliation": profile.get("occupation") or profile.get("organization"),
                    "personal_website": profile.get("websiteUrl") or w["personal_website"],
                    "github_url": _extract_github(profile.get("websiteUrl", "")),
                    "email": None,  # Kaggle Profile 不公开邮箱
                }
                cache[cache_key] = updates
                w.update({k: v for k, v in updates.items() if v})
            except Exception:
                pass

        enriched.append(w)
        new_crawls += 1

        if new_crawls % 20 == 0 and cache_file:
            save_cache(cache, cache_file)

        time.sleep(0.5)

    if cache_file and new_crawls > 0:
        save_cache(cache, cache_file)

    return enriched


def collect_kaggle_all_ai(top_n: int = 100, out_dir: Path = None,
                           prefix: str = "") -> List[Dict]:
    """批量采集所有预设 AI 比赛的 Top-N"""
    all_winners = []
    for slug in KAGGLE_AI_COMPETITIONS:
        winners = collect_kaggle_winners(slug, top_n, out_dir=out_dir, prefix=prefix)
        all_winners.extend(winners)
        time.sleep(1)
    return all_winners


# ============================================================
# Phase A2: Codeforces Top 用户
# ============================================================

def collect_codeforces_top(min_rating: int = 2200,
                            max_users: int = 500,
                            country: str = "China",
                            out_dir: Path = None,
                            prefix: str = "") -> List[Dict]:
    """
    从 Codeforces API 采集高 Rating 用户
    无需 API Key，公开接口
    rating >= 2200 = International Master 及以上
    rating >= 2500 = Grandmaster 及以上
    """
    log(f"\n{'='*60}")
    log(f"🖥️  采集 Codeforces Top 用户 (rating>={min_rating}, country={country})")
    log(f"{'='*60}")

    # 获取排行榜（指定国家）
    url = "https://codeforces.com/api/user.list"
    params = {"activeOnly": "false", "includeRetired": "true"}

    # CF API 不支持按国家/rating 过滤，需拉全量再筛选
    # 先从排行榜页面获取 Top 用户（更高效）
    users = _collect_cf_from_ratings_page(min_rating, max_users, country)

    if not users:
        log("  ⚠️ 排行榜页面解析失败，尝试 API 全量获取")
        users = _collect_cf_via_api(min_rating, max_users, country)

    log(f"✅ Codeforces: 获取 {len(users)} 名 rating≥{min_rating} 用户")

    # 补充 Profile 信息（个人网站等）
    users = _enrich_cf_profiles(users, out_dir=out_dir, prefix=prefix)
    return users


def _collect_cf_from_ratings_page(min_rating: int, max_users: int,
                                   country: str) -> List[Dict]:
    """
    爬取 Codeforces 国家排行榜页面
    URL: https://codeforces.com/ratings/country/{country}?page={n}
    每页 200 人，按 rating 降序，拿到 rating >= min_rating 的人为止
    """
    users = []
    page = 1
    country_url_encoded = country.replace(" ", "%20")

    while len(users) < max_users:
        url = f"https://codeforces.com/ratings/country/{country_url_encoded}"
        resp = http_get(url, params={"page": page}, timeout=20)
        if not resp:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table.ratingsDatatable tbody tr")
        if not rows:
            # 尝试另一种选择器
            rows = soup.select("table tr")

        if not rows:
            log(f"  ⚠️ 第 {page} 页没有找到数据行")
            break

        page_added = 0
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            # 典型列: rank | handle | name | rating | max_rating | ...
            handle_tag = row.select_one(".userhandle") or row.select_one("a[href*='/profile/']") 
            handle = ""
            if handle_tag:
                href = handle_tag.get("href", "")
                handle = href.split("/profile/")[-1].strip() if "/profile/" in href else handle_tag.get_text(strip=True)

            # 提取 rating（找含数字的最后几列）
            rating = 0
            for col in reversed(cols):
                text = col.get_text(strip=True)
                if text.isdigit() and int(text) > 1000:
                    rating = int(text)
                    break

            if rating < min_rating:
                # CF 排行榜按 rating 降序，一旦低于门槛可以停
                return users[:max_users]

            if not handle:
                continue

            # 提取显示名
            name_cols = [c.get_text(strip=True) for c in cols]
            full_name = next((t for t in name_cols if t and t != handle and not t.isdigit()), handle)

            users.append({
                "name": full_name,
                "cf_handle": handle,
                "rating": rating,
                "rank": "",
                "affiliation": "",
                "country": country,
                "personal_website": f"https://codeforces.com/profile/{handle}",
                "competition": f"Codeforces (rating≥{min_rating})",
                "source": "codeforces",
                "email": None,
                "github_url": None,
            })
            page_added += 1

        if page_added == 0:
            break

        page += 1
        time.sleep(1)

    # 再通过 CF API 批量补充 rank/organization（每次最多 500 handles）
    if users:
        handles = ",".join(u["cf_handle"] for u in users[:500])
        resp = http_get("https://codeforces.com/api/user.info",
                        params={"handles": handles}, timeout=20)
        if resp:
            try:
                info_map = {u["handle"]: u for u in resp.json().get("result", [])}
                for u in users:
                    info = info_map.get(u["cf_handle"], {})
                    if info:
                        u["rank"] = info.get("rank", "")
                        u["affiliation"] = info.get("organization", "") or ""
                        u["max_rating"] = info.get("maxRating", 0)
                        first = info.get("firstName", "") or ""
                        last = info.get("lastName", "") or ""
                        if first or last:
                            u["name"] = f"{first} {last}".strip()
            except Exception as e:
                log(f"  ⚠️ API user.info 补充失败: {e}")

    return users[:max_users]


def _collect_cf_via_api(min_rating: int, max_users: int,
                         country: str) -> List[Dict]:
    """
    备用: 从 Codeforces Div.1 比赛成绩收集选手 handles，
    再批量用 user.info 过滤国家 + rating
    """
    # 获取近期 Div 1 比赛（多取几场，确保覆盖足够人数）
    resp = http_get("https://codeforces.com/api/contest.list?gym=false")
    if not resp:
        return []
    try:
        data = resp.json()
        contests = data.get("result", [])
        # 取近期 Div.1 比赛（含 Div.1+2 联合赛）
        div1_contests = [
            c for c in contests
            if c.get("phase") == "FINISHED"
            and ("Div. 1" in (c.get("name") or "") or "Global" in (c.get("name") or ""))
        ][:5]
    except Exception:
        return []

    handles = set()
    for contest in div1_contests:
        cid = contest["id"]
        standings_resp = http_get(
            "https://codeforces.com/api/contest.standings",
            params={"contestId": cid, "from": 1, "count": 200, "showUnofficial": False}
        )
        if not standings_resp:
            continue
        try:
            sdata = standings_resp.json().get("result", {})
            for row in sdata.get("rows", []):
                for member in row.get("party", {}).get("members", []):
                    h = member.get("handle", "")
                    if h:
                        handles.add(h)
        except Exception:
            pass
        time.sleep(1)

    if not handles:
        return []

    # 批量查 user.info（每次最多 500 handles）
    all_users = []
    handle_list = list(handles)
    BATCH = 500
    for i in range(0, len(handle_list), BATCH):
        batch = handle_list[i:i+BATCH]
        info_resp = http_get(
            "https://codeforces.com/api/user.info",
            params={"handles": ";".join(batch)}, timeout=20
        )
        if not info_resp:
            continue
        try:
            info_data = info_resp.json()
            if info_data.get("status") == "OK":
                all_users.extend(info_data.get("result", []))
        except Exception:
            pass
        time.sleep(0.5)

    # 按国家 + rating 过滤
    country_lower = country.strip().lower()
    filtered = [
        u for u in all_users
        if (u.get("rating", 0) or 0) >= min_rating
        and (u.get("country", "") or "").strip().lower() == country_lower
    ]
    filtered.sort(key=lambda u: u.get("rating", 0), reverse=True)

    results = []
    for u in filtered[:max_users]:
        handle = u.get("handle", "")
        first = u.get("firstName", "") or ""
        last = u.get("lastName", "") or ""
        full_name = f"{first} {last}".strip() or handle
        results.append({
            "name": full_name,
            "cf_handle": handle,
            "rating": u.get("rating", 0),
            "max_rating": u.get("maxRating", 0),
            "rank": u.get("rank", ""),
            "affiliation": u.get("organization", "") or "",
            "country": u.get("country", ""),
            "personal_website": f"https://codeforces.com/profile/{handle}",
            "competition": f"Codeforces Div.1 (rating≥{min_rating})",
            "source": "codeforces",
            "email": None,
            "github_url": None,
        })

    return results


def _enrich_cf_profiles(users: List[Dict], out_dir: Optional[Path] = None,
                         prefix: str = "") -> List[Dict]:
    """
    CF Profile 直接爬取被 403 拦截，改用 Serper 搜索 GitHub/个人主页
    对于有 affiliation 的用户，用 '{handle} codeforces github' 搜索
    """
    if not SERPER_API_KEY:
        log("  ℹ️ 未设置 SERPER_API_KEY，跳过 CF profile 联系方式补充")
        return users

    cache_file = out_dir / f"{prefix}_cf_profile_cache.json" if out_dir else None
    cache = load_cache(cache_file) if cache_file else {}

    enriched = []
    new_queries = 0

    for u in users:
        handle = u.get("cf_handle") or u.get("name", "")
        cache_key = f"cf_serper::{handle}"

        if cache_key in cache:
            enriched.append({**u, **cache[cache_key]})
            continue

        # Serper 搜索: handle + codeforces + github
        query = f"{handle} codeforces site:github.com"
        results = _serper_search(query, num=3)
        updates = {}
        for r in results:
            url = r.get("link", "")
            github = _extract_github(url)
            if github:
                updates["github_url"] = github
                break

        cache[cache_key] = updates
        if updates:
            u.update({k: v for k, v in updates.items() if v})

        enriched.append(u)
        new_queries += 1

        if new_queries % 30 == 0 and cache_file:
            save_cache(cache, cache_file)

        time.sleep(0.4)

    if cache_file and new_queries > 0:
        save_cache(cache, cache_file)

    return enriched


# ============================================================
# Phase A3: NOI 金牌名单
# ============================================================

# NOI 历年数据（年份 → 结果页面 URL 模式）
NOI_URLS = {
    2024: "https://www.noi.cn/gynoi/jsjds/2024-07-31/849.shtml",  # 2024 金牌
    2023: "https://www.noi.cn/gynoi/jsjds/2023-08-01/849.shtml",
    2022: "https://www.noi.cn/gynoi/jsjds/2022-08-01/849.shtml",
    2021: "https://www.noi.cn/gynoi/jsjds/2021-09-01/849.shtml",
    2020: "https://www.noi.cn/gynoi/jsjds/2020-09-01/849.shtml",
    2019: "https://www.noi.cn/gynoi/jsjds/2019-08-01/849.shtml",
}

# NOI 结果备用源：CCPC/NOI 成绩公示
NOI_FALLBACK_URLS = {
    year: f"https://www.noi.cn/page/noi-results.shtml"
    for year in range(2015, 2025)
}


def collect_noi_winners(years: List[int], out_dir: Path = None,
                         prefix: str = "") -> List[Dict]:
    """
    爬取 NOI 金牌获奖者名单
    来源: noi.cn 历年金牌公示页面
    """
    log(f"\n{'='*60}")
    log(f"🇨🇳 采集 NOI 金牌名单: {years}")
    log(f"{'='*60}")

    all_winners = []
    for year in years:
        winners = _collect_noi_year(year)
        if not winners:
            log(f"  ⚠️ NOI {year}: 未能采集，尝试备用搜索")
            winners = _collect_noi_via_serper(year)
        all_winners.extend(winners)
        log(f"  ✅ NOI {year}: {len(winners)} 名金牌得主")
        time.sleep(1)

    log(f"✅ NOI 总计: {len(all_winners)} 名")
    return all_winners


def _collect_noi_year(year: int) -> List[Dict]:
    """解析 NOI 官网当年金牌公示页"""
    # 先试固定 URL，再试通用结果页
    urls_to_try = [
        NOI_URLS.get(year),
        f"https://www.noi.cn/gynoi/jsjds/{year}-08-01/849.shtml",
        f"https://www.noi.cn/gynoi/jsjds/{year}-07-31/849.shtml",
        f"https://www.noi.cn/gynoi/jsjds/{year}-09-01/849.shtml",
    ]
    urls_to_try = [u for u in urls_to_try if u]

    for url in urls_to_try:
        resp = http_get(url, timeout=15)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        winners = _parse_noi_table(soup, year)
        if winners:
            return winners

    return []


def _parse_noi_table(soup: BeautifulSoup, year: int) -> List[Dict]:
    """从 NOI 页面 HTML 中提取名单表格"""
    winners = []
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        headers = []
        for i, row in enumerate(rows):
            cells = [td.get_text(strip=True) for td in row.find_all(["th", "td"])]
            if i == 0:
                headers = [c.lower() for c in cells]
                continue

            # 跳过空行
            if not any(cells):
                continue

            # 尝试根据表头解析
            record = {}
            for j, cell in enumerate(cells):
                if j < len(headers):
                    record[headers[j]] = cell

            # 提取姓名（兼容不同表头格式）
            name = (
                record.get("姓名") or record.get("name") or
                record.get("选手") or record.get("参赛者")
                or (cells[1] if len(cells) > 1 else "")
            )
            school = (
                record.get("学校") or record.get("来自学校") or
                record.get("省份") or record.get("学校/省份")
                or (cells[2] if len(cells) > 2 else "")
            )

            if name and len(name) >= 2 and not name.isdigit():
                winners.append({
                    "name": name.strip(),
                    "affiliation": school.strip() if school else "",
                    "competition": f"NOI {year} 金牌",
                    "rank": None,
                    "score": None,
                    "source": "noi",
                    "email": None,
                    "github_url": None,
                    "personal_website": None,
                    "country": "China",
                    "_nationality": "chinese",
                    "_nat_confidence": "high",
                })

    return winners


def _collect_noi_via_serper(year: int) -> List[Dict]:
    """通过 Serper 搜索 NOI 获奖名单（备用方案）"""
    if not SERPER_API_KEY:
        return []

    query = f"NOI {year} 全国信息学奥林匹克 金牌 名单 获奖"
    results = _serper_search(query)
    log(f"  🔍 Serper 搜索 NOI {year} → {len(results)} 条结果")

    # 结果里没有结构化名单，主要用于找到官方页面后手动确认
    return []


# ============================================================
# Phase A4: ICPC Asia 区域赛 & 全球赛
# ============================================================

def collect_icpc_winners(years: List[int], region: str = "Asia",
                          out_dir: Path = None, prefix: str = "") -> List[Dict]:
    """
    从 icpc.global 爬取 ICPC 亚洲区域赛金奖名单
    """
    log(f"\n{'='*60}")
    log(f"🌏 采集 ICPC {region} 区域赛: {years}")
    log(f"{'='*60}")

    all_winners = []
    for year in years:
        winners = _collect_icpc_year(year, region)
        all_winners.extend(winners)
        log(f"  ✅ ICPC {year}: {len(winners)} 支金奖队伍")
        time.sleep(2)

    log(f"✅ ICPC 总计: {len(all_winners)} 支队伍")
    return all_winners


def _collect_icpc_year(year: int, region: str) -> List[Dict]:
    """从 ICPC 官方 API 或网页获取区域赛成绩"""
    # ICPC.global 提供了区域赛结果 JSON API
    api_url = f"https://icpc.global/api/v1/team/regionals/{year}"
    resp = http_get(api_url, timeout=15)

    if resp:
        try:
            data = resp.json()
            return _parse_icpc_api(data, year, region)
        except Exception:
            pass

    # 备用：爬 icpc.global 网页
    page_url = f"https://icpc.global/regionals/results?year={year}"
    resp = http_get(page_url, timeout=15)
    if not resp:
        return []

    return _parse_icpc_page(resp.text, year, region)


def _parse_icpc_api(data, year: int, region: str) -> List[Dict]:
    """解析 ICPC API 返回的队伍数据"""
    winners = []
    teams = data if isinstance(data, list) else data.get("teams", [])

    for team in teams:
        region_name = team.get("regionName", "") or ""
        if region.lower() not in region_name.lower():
            continue

        award = team.get("award", "") or ""
        if "gold" not in award.lower() and "first" not in award.lower():
            continue

        institution = team.get("institution", {})
        school = institution.get("name", "") if isinstance(institution, dict) else ""

        winners.append({
            "name": team.get("name", "") or team.get("teamName", ""),
            "affiliation": school,
            "competition": f"ICPC {region} Regional {year} 金奖",
            "rank": team.get("rank"),
            "score": None,
            "source": "icpc",
            "email": None,
            "github_url": None,
            "personal_website": None,
            "country": "China",
            "_nationality": "chinese",
            "_nat_confidence": "medium",
        })

    return winners


def _parse_icpc_page(html: str, year: int, region: str) -> List[Dict]:
    """备用：解析 ICPC 页面"""
    soup = BeautifulSoup(html, "html.parser")
    winners = []

    for tr in soup.select("table tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) < 3:
            continue

        # 粗略判断：包含金奖关键词
        row_text = " ".join(cells).lower()
        if "gold" in row_text or "金奖" in row_text or "第一" in row_text:
            winners.append({
                "name": cells[1] if len(cells) > 1 else cells[0],
                "affiliation": cells[2] if len(cells) > 2 else "",
                "competition": f"ICPC {region} Regional {year}",
                "rank": None,
                "score": None,
                "source": "icpc",
                "email": None,
                "github_url": None,
                "personal_website": None,
                "country": "China",
                "_nationality": "chinese",
                "_nat_confidence": "medium",
            })

    return winners


# ============================================================
# Phase B: 去重 + 华人过滤
# ============================================================

def deduplicate(records: List[Dict]) -> List[Dict]:
    """按姓名去重（竞赛记录不合并，保留每条赛事）"""
    log(f"\n📊 去重: {len(records)} 条原始记录")
    seen = set()
    result = []
    for r in records:
        # 以 name+competition 为 key（同一人不同赛事都保留）
        key = f"{r.get('name','').strip().lower()}::{r.get('competition','')}"
        if key and key not in seen:
            seen.add(key)
            result.append(r)

    log(f"✅ 去重后: {len(result)} 条")
    return result


def filter_nationality(records: List[Dict]) -> Tuple[List[Dict], int]:
    """过滤非华人（NOI/ICPC 全是华人，Kaggle/CF 需检测）"""
    log(f"\n🌏 国籍过滤: {len(records)} 人")
    keep, skip = [], 0

    for r in records:
        # NOI/ICPC 来源默认华人
        if r.get("source") in ("noi", "icpc"):
            if "_nationality" not in r:
                r["_nationality"] = "chinese"
            keep.append(r)
            continue

        # 已有 nationality 标注
        if r.get("_nationality") in ("chinese", "unknown"):
            keep.append(r)
            continue

        name = r.get("name", "")
        affil = r.get("affiliation", "") or ""

        if NATIONALITY_AVAILABLE:
            nat, conf = detect_nationality(name, affil)
        else:
            nat, conf = "unknown", "low"

        r["_nationality"] = nat
        r["_nat_confidence"] = conf

        if nat in ("chinese", "unknown"):
            keep.append(r)
        else:
            skip += 1

    log(f"  保留: {len(keep)} 人 | 过滤外国人: {skip} 人")
    return keep, skip


# ============================================================
# Phase C: Serper 搜索补充 GitHub / 邮箱
# ============================================================

def _serper_search(query: str, num: int = 5) -> List[Dict]:
    """调用 Serper API 搜索"""
    if not SERPER_API_KEY:
        return []
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=10,
        )
        return resp.json().get("organic", [])
    except Exception:
        return []


def enrich_with_serper(records: List[Dict], out_dir: Path = None,
                        prefix: str = "") -> List[Dict]:
    """
    对 GitHub URL / 邮箱缺失的记录，用 Serper 搜索补充
    策略: "{name} {affiliation} github.com"
    """
    if not SERPER_API_KEY:
        log("\n⚠️  未设置 SERPER_API_KEY，跳过 Serper 搜索")
        return records

    log(f"\n🔍 Serper 搜索补充联系方式: {len(records)} 人")

    cache_file = out_dir / f"{prefix}_serper_cache.json" if out_dir else None
    cache = load_cache(cache_file) if cache_file else {}

    need_enrich = [r for r in records if not r.get("github_url") and not r.get("email")]
    log(f"  需要 Serper 搜索的记录: {len(need_enrich)} 条")

    new_queries = 0
    for i, r in enumerate(need_enrich):
        name = r.get("name", "")
        affil = r.get("affiliation", "") or ""
        source = r.get("source", "")
        cache_key = f"serper::{name}::{affil}"

        if cache_key in cache:
            r.update({k: v for k, v in cache[cache_key].items() if v})
            continue

        # 构造搜索 query
        if source == "codeforces":
            handle = r.get("cf_handle") or name
            query = f"{handle} site:github.com OR \"{name}\" {affil} github"
        elif source in ("noi", "icpc"):
            query = f"\"{name}\" {affil} github.com OR linkedin.com"
        else:
            query = f"\"{name}\" {affil} site:github.com"

        results = _serper_search(query)
        updates = {}

        for result in results:
            url = result.get("link", "")
            if "github.com/" in url and not updates.get("github_url"):
                github = _extract_github(url)
                if github:
                    updates["github_url"] = github
            if not updates.get("email"):
                snippet = result.get("snippet", "")
                email_match = re.search(r"[\w.+%-]+@[\w-]+\.\w+", snippet)
                if email_match:
                    updates["email"] = email_match.group(0)

        cache[cache_key] = updates
        if updates:
            r.update({k: v for k, v in updates.items() if v})

        new_queries += 1
        if new_queries % 30 == 0 and cache_file:
            save_cache(cache, cache_file)

        time.sleep(0.5)

    if cache_file and new_queries > 0:
        save_cache(cache, cache_file)

    github_count = sum(1 for r in records if r.get("github_url"))
    email_count = sum(1 for r in records if r.get("email"))
    log(f"✅ Serper 完成: {github_count} 人有 GitHub, {email_count} 人有邮箱")
    return records


# ============================================================
# Phase D: 输出（与 academic_miner.py 格式兼容）
# ============================================================

def export_results(records: List[Dict], prefix: str, out_dir: Path):
    """
    导出三个文件（与 academic_miner.py 格式兼容）:
    1. *_full.json    — 所有字段完整版
    2. *_direct_import.json — 可直接导入 headhunter 系统的格式
    3. *_github_pipeline.json — 有 GitHub URL 的子集（送 github_network_miner 流程）
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = out_dir / f"comp_{ts}"

    # 1. Full
    save_json(records, Path(f"{base}_full.json"))

    # 2. Direct import（字段映射到候选人库格式）
    import_records = []
    for r in records:
        import_records.append({
            "name": r.get("name", ""),
            "current_company": r.get("affiliation", "") or "",
            "current_title": _infer_title(r),
            "email": r.get("email") or "",
            "github_url": r.get("github_url") or "",
            "linkedin_url": r.get("linkedin_url") or "",
            "source": f"competition_{r.get('source', 'unknown')}",
            "talent_tier": _infer_tier(r),
            "raw_resume_text": _build_resume_text(r),
            "structured_tags": _build_tags(r),
            "_meta": {
                "competition": r.get("competition"),
                "rank": r.get("rank"),
                "score": r.get("score"),
                "cf_handle": r.get("cf_handle"),
                "cf_rating": r.get("rating"),
                "_nationality": r.get("_nationality"),
            }
        })
    save_json(import_records, Path(f"{base}_direct_import.json"))

    # 3. GitHub Pipeline（有 GitHub URL 的子集）
    github_records = [r for r in records if r.get("github_url")]
    save_json(github_records, Path(f"{base}_github_pipeline.json"))

    log(f"\n📦 导出完成:")
    log(f"  完整版:     comp_{ts}_full.json ({len(records)} 条)")
    log(f"  导入格式:   comp_{ts}_direct_import.json ({len(import_records)} 条)")
    log(f"  GitHub流:   comp_{ts}_github_pipeline.json ({len(github_records)} 条)")


def _infer_title(r: Dict) -> str:
    source = r.get("source", "")
    rating = r.get("rating", 0) or 0
    if source == "kaggle":
        rank = r.get("rank") or 99
        return f"Kaggle 竞赛选手 (#{rank})" if rank else "Kaggle 算法竞赛选手"
    elif source == "codeforces":
        cf_rank = r.get("rank", "")
        return f"Codeforces {cf_rank} (Rating {rating})" if cf_rank else f"Codeforces Rating {rating}"
    elif source == "noi":
        return "NOI 金牌得主 | 竞技编程"
    elif source == "icpc":
        return "ICPC 金奖选手 | 竞技编程"
    return "算法竞赛选手"


def _infer_tier(r: Dict) -> str:
    source = r.get("source", "")
    rating = r.get("rating", 0) or 0
    rank = r.get("rank") or 999

    if source == "codeforces":
        if rating >= 3000: return "S"
        if rating >= 2600: return "A+"
        if rating >= 2400: return "A"
        if rating >= 2200: return "B+"
        return "B"
    elif source == "kaggle":
        if rank <= 3: return "A+"
        if rank <= 10: return "A"
        if rank <= 50: return "B+"
        return "B"
    elif source in ("noi", "icpc"):
        return "A"  # 国内顶级竞赛金牌默认 A
    return "B"


def _build_resume_text(r: Dict) -> str:
    parts = [f"竞赛选手: {r.get('name', '')}"]
    if r.get("competition"):
        parts.append(f"竞赛: {r['competition']}")
    if r.get("rank"):
        parts.append(f"排名: 第 {r['rank']} 名")
    if r.get("rating"):
        parts.append(f"Codeforces Rating: {r['rating']} ({r.get('rank', '')})")
    if r.get("affiliation"):
        parts.append(f"所属机构/学校: {r['affiliation']}")
    if r.get("cf_handle"):
        parts.append(f"CF Handle: {r['cf_handle']}")
    return "\n".join(parts)


def _build_tags(r: Dict) -> Dict:
    source = r.get("source", "")
    tags: Dict = {
        "tech_domain": ["AI/算法类"],
        "core_specialty": [],
        "role_type": "算法工程师",
        "role_orientation": ["Applied/落地型"],
    }

    if source in ("kaggle",):
        tags["core_specialty"].append("机器学习竞赛")
        if "image" in (r.get("competition") or "").lower():
            tags["tech_domain"].append("CV")
            tags["core_specialty"].append("计算机视觉/CV")
        if "nlp" in (r.get("competition") or "").lower() or "language" in (r.get("competition") or "").lower():
            tags["tech_domain"].append("NLP")
    elif source in ("codeforces", "noi", "icpc"):
        tags["core_specialty"].append("竞技编程/算法")
        tags["role_orientation"].append("AI Infra/系统优化型")
    return tags


# ============================================================
# 工具函数
# ============================================================

def _extract_github(url: str) -> Optional[str]:
    """从 URL 中提取 GitHub 个人主页"""
    if not url or "github.com" not in url:
        return None
    match = re.search(r"github\.com/([^/\s?#]+)", url)
    if match:
        username = match.group(1)
        # 排除非用户页面
        if username.lower() in ("topics", "collections", "organizations", "sponsors",
                                 "orgs", "login", "join", "features", "pricing"):
            return None
        return f"https://github.com/{username}"
    return None


# ============================================================
# CLI 入口
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(description="竞赛获奖者人才挖掘工具")
    parser.add_argument("--competition", "-c",
                        default="all",
                        help="采集来源: all | kaggle | codeforces | noi | icpc (逗号分隔)")
    parser.add_argument("--year", "-y",
                        default="2022,2023,2024",
                        help="年份范围 (逗号分隔), 用于 NOI/ICPC")
    parser.add_argument("--slug",
                        default=None,
                        help="Kaggle 比赛 slug (仅当 --competition kaggle 时)")
    parser.add_argument("--top-n", type=int, default=100,
                        help="Kaggle 取 Top N 名 (默认 100)")
    parser.add_argument("--min-rating", type=int, default=2200,
                        help="Codeforces 最低 Rating 门槛 (默认 2200)")
    parser.add_argument("--max-users", type=int, default=500,
                        help="Codeforces 最多采集 N 人 (默认 500)")
    parser.add_argument("--cf-country", default="China",
                        help="Codeforces 国家过滤 (默认 China)")
    parser.add_argument("--icpc-region", default="Asia",
                        help="ICPC 大区 (默认 Asia)")
    parser.add_argument("--output-dir", "-o",
                        default=str(OUTPUT_DIR),
                        help="输出目录")
    parser.add_argument("--no-serper", action="store_true",
                        help="跳过 Serper 联系方式搜索")
    parser.add_argument("--dry-run", action="store_true",
                        help="只采集不导出")
    return parser.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    competitions = [c.strip().lower() for c in args.competition.split(",")]
    years = [int(y.strip()) for y in args.year.split(",") if y.strip().isdigit()]
    prefix = f"comp_{datetime.now().strftime('%Y%m%d_%H%M')}"

    log(f"🚀 竞赛挖掘启动")
    log(f"   来源: {competitions}")
    log(f"   输出: {out_dir}")

    all_records: List[Dict] = []

    # ── Phase A: 采集 ──
    if "all" in competitions or "kaggle" in competitions:
        if args.slug:
            records = collect_kaggle_winners(args.slug, args.top_n,
                                             out_dir=out_dir, prefix=prefix)
        else:
            records = collect_kaggle_all_ai(args.top_n, out_dir=out_dir, prefix=prefix)
        all_records.extend(records)
        log(f"📊 Kaggle 小计: {len(records)} 条")

    if "all" in competitions or "codeforces" in competitions:
        records = collect_codeforces_top(
            min_rating=args.min_rating,
            max_users=args.max_users,
            country=args.cf_country,
            out_dir=out_dir, prefix=prefix,
        )
        all_records.extend(records)
        log(f"📊 Codeforces 小计: {len(records)} 条")

    if "all" in competitions or "noi" in competitions:
        records = collect_noi_winners(years, out_dir=out_dir, prefix=prefix)
        all_records.extend(records)
        log(f"📊 NOI 小计: {len(records)} 条")

    if "all" in competitions or "icpc" in competitions:
        records = collect_icpc_winners(years, region=args.icpc_region,
                                        out_dir=out_dir, prefix=prefix)
        all_records.extend(records)
        log(f"📊 ICPC 小计: {len(records)} 条")

    log(f"\n📊 总计采集: {len(all_records)} 条")

    # ── Phase B: 去重 + 国籍过滤 ──
    all_records = deduplicate(all_records)
    all_records, _ = filter_nationality(all_records)

    # ── Phase C: Serper 联系方式 ──
    if not args.no_serper:
        all_records = enrich_with_serper(all_records, out_dir=out_dir, prefix=prefix)

    # ── Phase D: 导出 ──
    if not args.dry_run:
        export_results(all_records, prefix=prefix, out_dir=out_dir)

    # 统计
    with_github = sum(1 for r in all_records if r.get("github_url"))
    with_email = sum(1 for r in all_records if r.get("email"))
    log(f"\n{'='*60}")
    log(f"🎉 竞赛挖掘完成!")
    log(f"   总人数:    {len(all_records)}")
    log(f"   有 GitHub: {with_github} ({with_github*100//max(len(all_records),1)}%)")
    log(f"   有邮箱:    {with_email} ({with_email*100//max(len(all_records),1)}%)")
    log(f"{'='*60}")

    return all_records


if __name__ == "__main__":
    main()
