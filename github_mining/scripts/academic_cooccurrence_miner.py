#!/usr/bin/env python3
"""
Academic-GitHub 共现挖掘脚本
================================
以 academic 渠道有 github_url 的人为种子，爬取其 GitHub following，
统计被 ≥N 个种子共同 follow 的新用户。

用法:
    python3 academic_cooccurrence_miner.py --dry-run          # 预览种子，不爬取
    python3 academic_cooccurrence_miner.py                     # 正式运行（共现≥2）
    python3 academic_cooccurrence_miner.py --resume            # 断点续传
    python3 academic_cooccurrence_miner.py --min-cooccurrence 3

遵守 CONVENTIONS.md:
    - 输出文件带年份+时间戳
    - 字段名: github, linkedin, emails, homepage
    - 只 INSERT，不跨源 UPDATE
    - 每步输出处理摘要
"""

import argparse
import json
import os
import sys
import time
import random
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# 路径配置（严格使用绝对路径，避免影子 DB）
# ============================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
BASE_DIR = SCRIPT_DIR.parent.resolve()           # github_mining/
WRITE_DIR = SCRIPT_DIR / "github_mining"         # github_mining/scripts/github_mining/
HEADHUNTER_DIR = BASE_DIR.parent / "personal-ai-headhunter"

WRITE_DIR.mkdir(exist_ok=True)

# ============================================================
# Token 配置（从 github_hunter_config.py 读取）
# ============================================================
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from github_hunter_config import GITHUB_CONFIG
    _token_pool_str = GITHUB_CONFIG.get("token", "")
    TOKEN_POOL = [t.strip() for t in _token_pool_str.split(",") if t.strip()]
except ImportError:
    TOKEN_POOL = []

_token_idx = 0

def get_token() -> str:
    if not TOKEN_POOL:
        return ""
    return TOKEN_POOL[_token_idx % len(TOKEN_POOL)]

def rotate_token():
    global _token_idx
    _token_idx += 1

API_BASE = "https://api.github.com"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10

# ============================================================
# GitHub API 封装（带 token 轮换 + 限流处理）
# ============================================================

def _headers():
    token = get_token()
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h

def api_get(url: str, params: dict = None, retry: int = 0) -> dict | None:
    """单次 GET 请求，返回 JSON dict 或 None"""
    try:
        resp = requests.get(url, params=params, headers=_headers(),
                            timeout=REQUEST_TIMEOUT, verify=False)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 403:
            # Rate limit → 轮换 token 并等待
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            reset = resp.headers.get("X-RateLimit-Reset", "")
            print(f"  ⚠️ 限流 (remaining={remaining}), 轮换 token...")
            rotate_token()
            wait = 61 if not reset else max(0, int(reset) - int(time.time())) + 1
            if wait > 60:
                print(f"  ⏳ 等待 {wait}s 重置限流...")
                time.sleep(wait)
            return api_get(url, params, retry)
        elif resp.status_code == 404:
            return None
        elif resp.status_code >= 500 and retry < MAX_RETRIES:
            time.sleep(2 ** retry)
            return api_get(url, params, retry + 1)
        else:
            return None
    except (requests.Timeout, requests.ConnectionError) as e:
        if retry < MAX_RETRIES:
            time.sleep(2 + retry * 2)
            return api_get(url, params, retry + 1)
        return None

def api_list(url: str, params: dict = None, max_pages: int = 5) -> list:
    """分页 GET，合并所有页的结果"""
    params = params or {}
    params.setdefault("per_page", 100)
    results = []
    for page in range(1, max_pages + 1):
        params["page"] = page
        data = api_get(url, params.copy())
        if not data:
            break
        if isinstance(data, list):
            results.extend(data)
            if len(data) < params["per_page"]:
                break
        else:
            break
    return results

# ============================================================
# 工具函数
# ============================================================

def save_json(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path: Path) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def today_str() -> str:
    return datetime.now().strftime("%Y%m%d")

def now_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def is_org_account(username: str) -> bool:
    """简单过滤：包含常见组织账号特征"""
    org_keywords = [
        "-group", "-lab", "-team", "-org", "-hub", "-ai", "-ml",
        "DMIRLAB", "LaVi-Lab", "ucas-vg", "academicpages"
    ]
    u_lower = username.lower()
    for kw in org_keywords:
        if kw.lower() in u_lower:
            return True
    return False

# ============================================================
# Step 1: 从 DB 导出 academic 种子
# ============================================================

def export_academic_seeds(output_path: Path) -> list[dict]:
    """从数据库导出 academic 渠道有 github_url 的候选人作为种子"""
    print(f"\n{'='*60}")
    print(f"📡 Step 1: 导出 Academic-GitHub 种子")
    print(f"{'='*60}\n")

    # 必须显式指定 DB_PATH（CONVENTIONS.md 规定）
    os.environ["DB_PATH"] = str(HEADHUNTER_DIR / "data" / "headhunter_dev.db")
    sys.path.insert(0, str(HEADHUNTER_DIR))

    orig_dir = Path.cwd()
    os.chdir(HEADHUNTER_DIR)

    try:
        from database import SessionLocal, Candidate
        session = SessionLocal()

        academic = session.query(Candidate).filter(
            Candidate.source == "academic",
            Candidate.github_url.isnot(None),
        ).all()

        session.close()
    finally:
        os.chdir(orig_dir)

    print(f"  DB 中 academic 有 github_url: {len(academic)} 人")

    seeds = []
    skipped_org = 0
    skipped_invalid = 0

    for c in academic:
        url = (c.github_url or "").strip().rstrip("/")
        if not url or "github.com" not in url:
            skipped_invalid += 1
            continue

        # 提取 username
        username = url.split("/")[-1].strip()
        if not username or "/" in username:
            skipped_invalid += 1
            continue

        # 过滤组织账号（粗过滤，后续 API 层再验证）
        if is_org_account(username):
            skipped_org += 1
            continue

        seeds.append({
            "username": username,
            "github_url": url,
            "name": c.name or "",
            "db_id": c.id,
        })

    # 去重（同一 username 可能来自多个候选人）
    seen = {}
    deduped = []
    for s in seeds:
        if s["username"] not in seen:
            seen[s["username"]] = True
            deduped.append(s)

    print(f"  有效种子: {len(deduped)} 人")
    print(f"  跳过组织账号: {skipped_org}")
    print(f"  跳过 URL 无效: {skipped_invalid}")

    save_json(deduped, output_path)
    print(f"  💾 种子列表保存: {output_path}")

    return deduped

# ============================================================
# Step 2: 共现分析
# ============================================================

def run_cooccurrence(
    seeds: list[dict],
    progress_path: Path,
    output_path: Path,
    min_cooccurrence: int = 2,
    max_following: int = 2000,
    existing_usernames: set = None,
):
    """核心共现分析：统计被 ≥min_cooccurrence 个种子共同 follow 的用户"""
    print(f"\n{'='*60}")
    print(f"🌐 Step 2: 共现分析 (min_cooccurrence={min_cooccurrence})")
    print(f"{'='*60}\n")

    existing_usernames = existing_usernames or set()

    # 断点续传：从 progress 文件恢复
    cooccurrence = Counter()
    new_user_info = {}
    processed_seeds = set()

    if progress_path.exists():
        progress = load_json(progress_path)
        processed_seeds = set(progress.get("processed_seeds", []))
        cooccurrence = Counter(progress.get("cooccurrence", {}))
        new_user_info = progress.get("new_user_info", {})
        print(f"  ⏩ 断点续传：已处理 {len(processed_seeds)} 个种子，"
              f"已发现 {len(cooccurrence)} 个新用户")

    total = len(seeds)
    skipped_following_too_many = 0
    api_errors = 0

    for i, seed in enumerate(seeds):
        username = seed["username"]

        if username in processed_seeds:
            continue

        if (i + 1) % 10 == 0:
            done = len(processed_seeds) + 1
            high_co = len([v for v in cooccurrence.values() if v >= min_cooccurrence])
            print(f"  进度: {done}/{total} | 新用户: {len(cooccurrence)} | "
                  f"共现≥{min_cooccurrence}: {high_co}")

        # 检查 following 数量（避免爬取 following 超大的人）
        # 注意：种子数据里可能没有 following 数，直接爬 API
        profile = api_get(f"{API_BASE}/users/{username}")
        if profile is None:
            api_errors += 1
            processed_seeds.add(username)
            continue

        following_count = profile.get("following", 0)
        if following_count > max_following:
            print(f"  ⏭️ 跳过 {username} (following={following_count} > {max_following})")
            skipped_following_too_many += 1
            processed_seeds.add(username)
            continue

        # 如果是组织账号（type='Organization'），跳过
        if profile.get("type") == "Organization":
            processed_seeds.add(username)
            continue

        # 获取 following 列表（最多 5 页 = 500 人）
        following = api_list(
            f"{API_BASE}/users/{username}/following",
            {"per_page": 100},
            max_pages=5
        )

        for f_user in following:
            f_username = f_user.get("login", "")
            if f_username and f_username.lower() not in existing_usernames:
                cooccurrence[f_username] += 1
                if f_username not in new_user_info:
                    new_user_info[f_username] = {
                        "username": f_username,
                        "github": f_user.get("html_url", f"https://github.com/{f_username}"),
                    }

        processed_seeds.add(username)
        time.sleep(0.5 + random.uniform(0, 0.3))

        # 每 50 个种子保存一次进度
        if len(processed_seeds) % 50 == 0:
            _save_progress(progress_path, processed_seeds, cooccurrence, new_user_info)

    # 最终保存进度
    _save_progress(progress_path, processed_seeds, cooccurrence, new_user_info)

    # 过滤高共现用户
    high_co = {u: c for u, c in cooccurrence.items() if c >= min_cooccurrence}
    print(f"\n{'='*40}")
    print(f"📊 共现统计:")
    print(f"  种子处理: {len(processed_seeds)} / {total}")
    print(f"  发现新用户总数: {len(cooccurrence)}")
    print(f"  共现 ≥{min_cooccurrence}: {len(high_co)}")
    print(f"  跳过 following 过多: {skipped_following_too_many}")
    print(f"  API 错误/不存在: {api_errors}")

    # 富化高共现用户信息
    print(f"\n📡 获取 {len(high_co)} 个高共现用户的完整 Profile...")
    expanded = []
    for j, (username, co_count) in enumerate(
        sorted(high_co.items(), key=lambda x: x[1], reverse=True)
    ):
        if j % 50 == 0 and j > 0:
            print(f"  进度: {j}/{len(high_co)}")

        profile = api_get(f"{API_BASE}/users/{username}")
        if profile:
            # 跳过组织账号
            if profile.get("type") == "Organization":
                continue

            user = {
                # CONVENTIONS.md 标准字段名
                "username": profile.get("login", username),
                "name": profile.get("name", ""),
                "github": profile.get("html_url", f"https://github.com/{username}"),
                "emails": profile.get("email", ""),           # 注意统一用 emails
                "blog": profile.get("blog", ""),              # ✅ 与 github_network_miner.py 一致，Phase 3.5 依赖此字段名
                "bio": profile.get("bio", ""),
                "company": profile.get("company", ""),
                "location": profile.get("location", ""),
                "twitter_username": profile.get("twitter_username", ""),
                "public_repos": profile.get("public_repos", 0),
                "followers": profile.get("followers", 0),
                "following": profile.get("following", 0),
                "created_at": profile.get("created_at", ""),
                "updated_at": profile.get("updated_at", ""),
                "cooccurrence": co_count,
                "source_channel": "academic_cooc",  # 追踪来源
            }
            expanded.append(user)

        time.sleep(0.3 + random.uniform(0, 0.2))

        # 每 100 个中间保存一次
        if (j + 1) % 100 == 0:
            save_json(expanded, output_path)

    expanded.sort(key=lambda x: x["cooccurrence"], reverse=True)
    save_json(expanded, output_path)

    # 打印 Top 20
    print(f"\n🏆 共现 Top 20 新发现用户:")
    for k, c in enumerate(expanded[:20], 1):
        print(f"  {k:2d}. {c['username']:25s} | co={c['cooccurrence']:3d} | "
              f"{str(c.get('company','') or '')[:25]} | {str(c.get('bio','') or '')[:40]}")

    print(f"\n✅ 共现分析完成！新发现高共现用户: {len(expanded)} 人")
    print(f"   💾 输出: {output_path}")

    return expanded

def _save_progress(path: Path, processed_seeds: set, cooccurrence: Counter, new_user_info: dict):
    progress = {
        "processed_seeds": list(processed_seeds),
        "cooccurrence": dict(cooccurrence),
        "new_user_info": new_user_info,
        "updated_at": datetime.now().isoformat(),
    }
    save_json(progress, path)

# ============================================================
# Step 3: 从 DB 获取排除名单（已入库的 github username）
# ============================================================

def get_existing_github_usernames() -> set:
    """获取数据库中已有的 GitHub username，用于共现分析时排除"""
    os.environ["DB_PATH"] = str(HEADHUNTER_DIR / "data" / "headhunter_dev.db")
    sys.path.insert(0, str(HEADHUNTER_DIR))

    orig_dir = Path.cwd()
    os.chdir(HEADHUNTER_DIR)

    try:
        from database import SessionLocal, Candidate
        session = SessionLocal()
        github_candidates = session.query(Candidate.github_url).filter(
            Candidate.github_url.isnot(None)
        ).all()
        session.close()
    finally:
        os.chdir(orig_dir)

    usernames = set()
    for (url,) in github_candidates:
        if url:
            username = url.strip().rstrip("/").split("/")[-1].lower()
            if username:
                usernames.add(username)

    print(f"  DB 已有 GitHub 用户数 (排除名单): {len(usernames)}")
    return usernames

# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Academic-GitHub 共现挖掘：以 academic 渠道有 GitHub 的人为种子"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览种子，不实际爬取 GitHub API")
    parser.add_argument("--resume", action="store_true",
                        help="从断点续传（默认开启）")
    parser.add_argument("--min-cooccurrence", type=int, default=2,
                        help="最小共现次数（默认=2）")
    parser.add_argument("--max-following", type=int, default=2000,
                        help="跳过 following 超过此数的种子（默认=2000）")
    parser.add_argument("--date", type=str, default=today_str(),
                        help="覆盖输出文件的日期后缀（默认=今日 YYYYMMDD）")
    args = parser.parse_args()

    DATE = args.date
    TS = now_str()

    # 文件路径（遵守 CONVENTIONS.md：带年份+时间戳）
    seeds_path = BASE_DIR / f"academic_github_seeds_{DATE}.json"
    progress_path = WRITE_DIR / f"academic_cooc_progress_{DATE}.json"
    output_path = WRITE_DIR / f"academic_cooc_expanded_{DATE}.json"

    print(f"\n{'='*60}")
    print(f"🚀 Academic-GitHub 共现挖掘")
    print(f"   日期标签: {DATE}")
    print(f"   共现阈值: ≥{args.min_cooccurrence}")
    print(f"   Token 池: {len(TOKEN_POOL)} 个")
    print(f"{'='*60}")

    # ── Step 1: 导出种子 ──────────────────────────────────────
    if seeds_path.exists() and args.resume:
        seeds = load_json(seeds_path)
        print(f"\n  ⏩ 加载已有种子文件: {seeds_path} ({len(seeds)} 人)")
    else:
        seeds = export_academic_seeds(seeds_path)

    if args.dry_run:
        print(f"\n✅ [DRY RUN] 种子数量: {len(seeds)}")
        print(f"   种子文件: {seeds_path}")
        print(f"   将要输出: {output_path}")
        print(f"   共现阈值: ≥{args.min_cooccurrence}")
        print("\n前 10 个种子示例:")
        for s in seeds[:10]:
            print(f"  {s['username']:30s} | {s.get('name','')}")
        return

    # ── Step 2: 获取排除名单 ─────────────────────────────────
    print(f"\n{'='*60}")
    print(f"📋 获取数据库排除名单...")
    existing_usernames = get_existing_github_usernames()

    # ── Step 3: 共现分析 ──────────────────────────────────────
    expanded = run_cooccurrence(
        seeds=seeds,
        progress_path=progress_path,
        output_path=output_path,
        min_cooccurrence=args.min_cooccurrence,
        max_following=args.max_following,
        existing_usernames=existing_usernames,
    )

    # ── 最终摘要 ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"✅ 全部完成！处理摘要")
    print(f"{'='*60}")
    print(f"  种子数量        : {len(seeds)}")
    print(f"  新发现用户      : {len(expanded)}")
    print(f"  共现阈值        : ≥{args.min_cooccurrence}")
    print(f"  输出文件        : {output_path}")
    print(f"  下一步          : 运行 run_academic_cooc_pipeline.sh 完成富化入库")


if __name__ == "__main__":
    main()
