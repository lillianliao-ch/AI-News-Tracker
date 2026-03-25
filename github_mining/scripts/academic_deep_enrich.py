#!/usr/bin/env python3
"""
Academic Deep Enricher — 学术人才深度富化 (Phase 6)

两种模式:
  Mode A (homepage): 对所有有主页的学者，爬取子页面提取联系方式 + 保存网页原文 (供 LLM 富化)
  Mode B (github-commit): 对已有 GitHub URL 但无邮箱的学者，从 commit history 提取 email

用法:
  # 主页深度爬取
  python3 academic_deep_enrich.py \
    --input all_conf_2025_full.json \
    --serper-cache _serper_cache.json \
    --output-dir ./outputs/ \
    --mode homepage

  # GitHub commit email
  python3 academic_deep_enrich.py \
    --input all_conf_2025_full.json \
    --serper-cache _serper_cache.json \
    --output-dir ./outputs/ \
    --mode github-commit

  # 两者都跑
  python3 academic_deep_enrich.py \
    --input all_conf_2025_full.json \
    --serper-cache _serper_cache.json \
    --output-dir ./outputs/ \
    --mode all

特性:
  - 断点续传: 缓存文件自动保存/恢复进度
  - 定期落盘: 每 20 条自动保存缓存
  - 安全写入: 先写 .tmp 再 rename + .bak 备份
  - 优雅退出: Ctrl+C 保存缓存
"""

import os
import re
import sys
import json
import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import argparse
import functools
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 强制刷新输出
print = functools.partial(print, flush=True)

SCRIPT_DIR = Path(__file__).parent

# 全局缓存引用 (Ctrl+C 保护)
_global_cache = None
_global_cache_path = None

# ============================================================
# 通用工具
# ============================================================

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def load_json(path) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def safe_save_json(data, path, backup=True):
    """安全写入 JSON：先写 .tmp 再 rename，避免写半截。"""
    path = Path(path)
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, bak)
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.rename(path)


def _graceful_exit(signum, frame):
    """Ctrl+C 优雅退出：保存缓存后退出"""
    global _global_cache, _global_cache_path
    log("\n⚠️  收到中断信号，正在保存缓存...")
    if _global_cache and _global_cache_path:
        safe_save_json(_global_cache, _global_cache_path, backup=True)
        log(f"  💾 缓存已保存: {_global_cache_path} ({len(_global_cache)} 条)")
    log("  下次运行将自动从断点继续")
    sys.exit(0)

signal.signal(signal.SIGINT, _graceful_exit)
signal.signal(signal.SIGTERM, _graceful_exit)


# ============================================================
# 联系方式提取 (复用 extract_paper_email.py)
# ============================================================
sys.path.append(str(SCRIPT_DIR))
try:
    from extract_paper_email import extract_academic_contacts
except ImportError:
    log("⚠️  extract_paper_email.py 未找到，主页提取功能受限")
    extract_academic_contacts = None


# ============================================================
# Mode A: 主页深度爬取
# ============================================================

# 常见子页面路径 (学术主页常见联系方式页面)
CONTACT_SUBPAGES = [
    "/contact", "/contact.html", "/contact/",
    "/about", "/about.html", "/about/",
    "/about-me", "/about-me.html",
    "/bio", "/bio.html",
    "/cv", "/cv.html",
]

# HTTP 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _crawl_subpages(homepage: str, author_name: str) -> Dict:
    """
    爬取主页及其常见子页面，提取联系方式 + 保存网页原文。
    返回: {"emails": [...], "github": "...", "linkedin": "...", "twitter": "...",
           "homepage_text": "..."}
    """
    result = {"emails": [], "github": None, "linkedin": None, "twitter": None,
              "homepage_text": None}
    all_emails = set()
    all_texts = []  # 收集所有页面的文本
    
    # 解析基础 URL
    parsed = urllib.parse.urlparse(homepage)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # 构建要爬的 URL 列表: 首页 + 所有子页面
    urls_to_crawl = [homepage]
    for sub in CONTACT_SUBPAGES:
        urls_to_crawl.append(urllib.parse.urljoin(homepage.rstrip('/') + '/', sub.lstrip('/')))
    
    # 去重
    urls_to_crawl = list(dict.fromkeys(urls_to_crawl))
    
    for url in urls_to_crawl:
        try:
            resp = requests.get(url, timeout=8, verify=False, headers=HEADERS,
                              allow_redirects=True)
            if resp.status_code != 200:
                continue
            
            content_type = resp.headers.get('content-type', '')
            if 'html' not in content_type and 'text' not in content_type:
                continue
            
            # 提取联系方式
            if extract_academic_contacts:
                contacts = extract_academic_contacts(resp.text, url)
                if contacts.get("emails"):
                    all_emails.update(contacts["emails"])
                if contacts.get("github") and not result["github"]:
                    result["github"] = contacts["github"]
                if contacts.get("linkedin") and not result["linkedin"]:
                    result["linkedin"] = contacts["linkedin"]
                if contacts.get("twitter") and not result["twitter"]:
                    result["twitter"] = contacts["twitter"]
            else:
                text = resp.text
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                found = re.findall(email_pattern, text)
                for e in found:
                    e = e.lower().strip()
                    if not any(x in e for x in ['noreply', 'example.com', 'domain.com',
                                                 'review', 'editor', 'submission']):
                        all_emails.add(e)
            
            # 提取干净文本 (供 LLM 使用)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            page_text = soup.get_text(separator='\n', strip=True)
            if len(page_text) > 50:
                all_texts.append(page_text)
                        
        except Exception:
            continue
        
        time.sleep(0.3)  # 礼貌延迟
    
    result["emails"] = list(all_emails)
    
    # 合并所有页面文本
    if all_texts:
        combined = '\n\n---\n\n'.join(all_texts)
        if len(combined) > 15000:
            combined = combined[:15000] + '...[truncated]'
        result["homepage_text"] = combined
    
    return result


def _match_email_to_author_simple(emails: List[str], author_name: str) -> Optional[str]:
    """
    简单版名字匹配：从候选邮箱列表中找到最可能属于作者的那个。
    复用 academic_contact_enricher.py 的 v3 匹配逻辑的简化版。
    """
    if not emails or not author_name:
        return None
    
    name_parts = [p.lower() for p in author_name.split()]
    last_name = name_parts[-1] if name_parts else ""
    first_name = name_parts[0] if len(name_parts) > 1 else ""
    
    best_email = None
    best_score = 0
    
    for email in emails:
        local = email.split('@')[0].lower()
        local_flat = re.sub(r'[._\-\d]', '', local)
        score = 0
        
        # first + last both present
        if (last_name and len(last_name) >= 2 and last_name in local_flat and
                first_name and len(first_name) >= 2 and first_name in local_flat):
            score = 10
        # last name at start or end
        elif last_name and len(last_name) >= 3:
            if local_flat.startswith(last_name) or local_flat.endswith(last_name):
                score = 6
                if first_name and first_name[0] in local_flat:
                    score = 8
        # first name at start (3+ chars)
        elif first_name and len(first_name) >= 3 and local_flat.startswith(first_name):
            score = 5
        
        if score > best_score:
            best_score = score
            best_email = email
    
    return best_email if best_score >= 5 else None


def enrich_via_homepage(authors: List[Dict], serper_cache: Dict,
                         deep_cache: Dict, cache_path: Path,
                         max_workers: int = 10) -> List[Dict]:
    """
    Mode A: 主页深度爬取 (并发版)
    对所有有主页的学者，并发爬取子页面:
      1. 提取联系方式 (email, GitHub, LinkedIn)
      2. 保存网页原文 (homepage_text) 供后续 LLM 富化
    """
    log(f"\n{'='*60}")
    log(f"🌐 Mode A: 主页深度爬取 (并发={max_workers} workers)")
    log(f"{'='*60}")
    
    # 构建 serper 映射 (主页 + 邮箱)
    homepage_map = {}
    serper_emails = {}
    for k, v in serper_cache.items():
        if k.startswith('serper::'):
            name = k.replace('serper::', '')
            if v.get('homepage'):
                homepage_map[name] = v['homepage']
            if v.get('emails'):
                serper_emails[name] = v['emails']
    
    # 筛选目标
    skip_domains = ['researchgate.net', 'dl.acm.org', 'scholar.google',
                   'arxiv.org', 'semanticscholar.org', 'dblp.org',
                   'openreview.net', 'linkedin.com', 'twitter.com', 'x.com']
    targets = []
    skipped_cache = 0
    found_email = 0
    found_github = 0
    saved_text = 0
    
    for a in authors:
        name = a.get("name", "")
        homepage = (a.get("personal_website") or 
                   a.get("serper_homepage") or
                   homepage_map.get(name))
        
        if homepage and 'github.com' not in homepage:
            if any(d in homepage for d in skip_domains):
                continue
            has_email = bool(a.get("email") or a.get("pdf_matched_email") or 
                            a.get("enriched_email") or name in serper_emails)
            cache_key = f"deep_homepage::{name}::{homepage}"
            
            # 缓存命中 — 直接跳过
            if cache_key in deep_cache:
                cached = deep_cache[cache_key]
                if cached.get("matched_email") and not has_email:
                    a["deep_email"] = cached["matched_email"]
                    a["deep_email_source"] = "homepage_deep"
                    found_email += 1
                if cached.get("github"):
                    a["deep_github"] = cached["github"]
                    found_github += 1
                if cached.get("homepage_text"):
                    saved_text += 1
                skipped_cache += 1
                continue
            
            targets.append((a, name, homepage, has_email, cache_key))
    
    log(f"  目标: {len(targets)} 人待爬取, {skipped_cache} 缓存命中")
    need_email = sum(1 for _, _, _, has, _ in targets if not has)
    log(f"  其中需要邮箱: {need_email} 人")
    
    if not targets:
        log("  ✅ 所有目标已完成")
        return authors
    
    # 并发爬取
    start_time = time.time()
    new_queries = 0
    lock = threading.Lock()
    
    def _process_one(item):
        """线程安全的单人处理"""
        author, name, homepage, already_has_email, cache_key = item
        contacts = _crawl_subpages(homepage, name)
        
        cache_entry = {
            "homepage": homepage,
            "all_emails": contacts["emails"],
            "matched_email": None,
            "github": contacts.get("github"),
            "linkedin": contacts.get("linkedin"),
            "homepage_text": contacts.get("homepage_text"),
        }
        
        if contacts["emails"] and not already_has_email:
            matched = _match_email_to_author_simple(contacts["emails"], name)
            if matched:
                cache_entry["matched_email"] = matched
        
        return name, cache_key, cache_entry, author, already_has_email
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_one, item): item for item in targets}
        
        for future in as_completed(futures):
            try:
                name, cache_key, cache_entry, author, already_has_email = future.result()
                
                with lock:
                    new_queries += 1
                    deep_cache[cache_key] = cache_entry
                    
                    if cache_entry.get("homepage_text"):
                        saved_text += 1
                    if cache_entry.get("matched_email") and not already_has_email:
                        author["deep_email"] = cache_entry["matched_email"]
                        author["deep_email_source"] = "homepage_deep"
                        found_email += 1
                    if cache_entry.get("github") and not author.get("github_url"):
                        author["deep_github"] = cache_entry["github"]
                        found_github += 1
                    
                    # 进度 + 定期落盘
                    if new_queries % 50 == 0:
                        elapsed = time.time() - start_time
                        speed = new_queries / max(elapsed, 1)
                        remaining = len(targets) - new_queries
                        eta_min = remaining / max(speed, 0.01) / 60
                        log(f"  进度: {new_queries}/{len(targets)} "
                            f"(email: {found_email}, text: {saved_text}, "
                            f"speed: {speed:.1f}/s, ETA: {eta_min:.0f}min)")
                        if cache_path:
                            safe_save_json(deep_cache, cache_path, backup=False)
                            
            except Exception as e:
                log(f"  ❌ 爬取异常: {e}")
    
    # 最终保存
    if cache_path:
        safe_save_json(deep_cache, cache_path, backup=False)
    
    elapsed = (time.time() - start_time) / 60
    log(f"  ✅ 完成: {found_email} 新邮箱, {found_github} GitHub, "
        f"{saved_text} 有网页文本 ({new_queries} new, {elapsed:.1f}min)")
    
    return authors


# ============================================================
# Mode B: GitHub Commit Email
# ============================================================

def _extract_commit_email(github_url: str) -> Optional[str]:
    """
    从 GitHub Events API 或 commit patch 中提取 commit 邮箱。
    策略:
      1. GitHub Events API (不需要 token, 但有限流)
      2. 最近 commit 的 .patch URL (公开访问)
    """
    # 解析 GitHub 用户名
    parsed = urllib.parse.urlparse(github_url)
    path_parts = [p for p in parsed.path.split('/') if p]
    if not path_parts:
        return None
    username = path_parts[0]
    
    # 跳过组织账号和特殊页面
    if username.lower() in ('orgs', 'topics', 'collections', 'sponsors',
                             'about', 'pricing', 'features', 'login', 'join'):
        return None
    
    # 策略 1: Events API — 免费,无需 token, 但限流严格
    try:
        resp = requests.get(
            f"https://api.github.com/users/{username}/events/public",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AcademicDeepEnrich/1.0"
            },
            timeout=10
        )
        
        if resp.status_code == 200:
            events = resp.json()
            for event in events:
                if event.get("type") == "PushEvent":
                    commits = event.get("payload", {}).get("commits", [])
                    for commit in commits:
                        author_info = commit.get("author", {})
                        email = author_info.get("email", "")
                        if (email and "@" in email and 
                            "noreply" not in email and
                            "users.noreply.github.com" not in email):
                            return email
        elif resp.status_code == 403:
            # Rate limited, try strategy 2
            pass
    except Exception:
        pass
    
    # 策略 2: 直接访问用户 repos, 找最近 commit 的 .patch
    try:
        resp = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={"sort": "updated", "per_page": 3},
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AcademicDeepEnrich/1.0"
            },
            timeout=10
        )
        
        if resp.status_code == 200:
            repos = resp.json()
            for repo in repos:
                if repo.get("fork"):
                    continue
                repo_name = repo.get("full_name", "")
                if not repo_name:
                    continue
                
                # 获取最新 commit
                try:
                    commit_resp = requests.get(
                        f"https://api.github.com/repos/{repo_name}/commits",
                        params={"per_page": 3},
                        headers={
                            "Accept": "application/vnd.github.v3+json",
                            "User-Agent": "AcademicDeepEnrich/1.0"
                        },
                        timeout=10
                    )
                    if commit_resp.status_code == 200:
                        commits = commit_resp.json()
                        for c in commits:
                            author_data = c.get("commit", {}).get("author", {})
                            email = author_data.get("email", "")
                            if (email and "@" in email and
                                "noreply" not in email and
                                "users.noreply.github.com" not in email):
                                return email
                except Exception:
                    continue
                    
                time.sleep(0.5)  # Rate limiting
    except Exception:
        pass
    
    return None


def enrich_via_github_commit(authors: List[Dict], serper_cache: Dict,
                              deep_cache: Dict, cache_path: Path) -> List[Dict]:
    """
    Mode B: GitHub Commit Email 提取
    对有 GitHub URL 但无邮箱的学者，从 commit history 提取 email。
    """
    log(f"\n{'='*60}")
    log(f"🐙 Mode B: GitHub Commit Email Extraction")
    log(f"{'='*60}")
    
    # 构建 serper GitHub 映射
    github_map = {}
    for k, v in serper_cache.items():
        if k.startswith('serper::') and v.get('github'):
            name = k.replace('serper::', '')
            github_map[name] = v['github']
    
    # 筛选目标: 有 GitHub 但无邮箱
    targets = []
    for a in authors:
        name = a.get("name", "")
        github = (a.get("github_url") or 
                 a.get("serper_github") or 
                 a.get("deep_github") or
                 github_map.get(name))
        has_email = bool(a.get("email") or a.get("pdf_matched_email") or 
                        a.get("enriched_email") or a.get("deep_email"))
        
        if github and not has_email:
            targets.append((a, github))
    
    log(f"  目标: {len(targets)} 人 (有 GitHub 无邮箱)")
    
    found_email = 0
    new_queries = 0
    rate_limited = 0
    start_time = time.time()
    
    for i, (author, github_url) in enumerate(targets):
        name = author.get("name", "")
        cache_key = f"deep_github::{name}::{github_url}"
        
        # 缓存命中
        if cache_key in deep_cache:
            cached = deep_cache[cache_key]
            if cached.get("commit_email"):
                author["deep_email"] = cached["commit_email"]
                author["deep_email_source"] = "github_commit"
                found_email += 1
            continue
        
        new_queries += 1
        
        # 进度 + ETA
        if new_queries % 20 == 0:
            elapsed = time.time() - start_time
            speed = new_queries / max(elapsed, 1)
            remaining = len(targets) - i
            eta_min = remaining / max(speed, 0.01) / 60
            log(f"  进度: {i+1}/{len(targets)} (email: {found_email}, "
                f"rate_limited: {rate_limited}, speed: {speed:.1f}/s, ETA: {eta_min:.0f}min)")
        
        # 提取 commit email
        email = _extract_commit_email(github_url)
        
        cache_entry = {
            "github_url": github_url,
            "commit_email": email,
        }
        
        if email:
            author["deep_email"] = email
            author["deep_email_source"] = "github_commit"
            found_email += 1
        
        deep_cache[cache_key] = cache_entry
        
        # 定期落盘
        if cache_path and new_queries % 20 == 0:
            safe_save_json(deep_cache, cache_path, backup=False)
        
        # GitHub API rate limiting: 60 req/hour unauthenticated
        # 每分钟约 1 个请求，保守一些
        time.sleep(1.5)
    
    elapsed = (time.time() - start_time) / 60
    log(f"  ✅ GitHub commit email 提取完成: {found_email}/{len(targets)} 人找到邮箱 "
        f"({new_queries} new, {elapsed:.1f}min)")
    
    return authors


# ============================================================
# 统计报告
# ============================================================

def generate_report(authors: List[Dict]) -> Dict:
    """生成深度补充统计报告"""
    stats = {
        "total": len(authors),
        "deep_email_homepage": 0,
        "deep_email_github": 0,
        "deep_github_new": 0,
        "by_tier": {},
    }
    
    for a in authors:
        tier = a.get("_academic_tier", "?")
        if tier not in stats["by_tier"]:
            stats["by_tier"][tier] = {"total": 0, "deep_email": 0, "deep_github": 0}
        stats["by_tier"][tier]["total"] += 1
        
        source = a.get("deep_email_source", "")
        if source == "homepage_deep":
            stats["deep_email_homepage"] += 1
            stats["by_tier"][tier]["deep_email"] += 1
        elif source == "github_commit":
            stats["deep_email_github"] += 1
            stats["by_tier"][tier]["deep_email"] += 1
        
        if a.get("deep_github"):
            stats["deep_github_new"] += 1
            stats["by_tier"][tier]["deep_github"] += 1
    
    log(f"\n{'='*60}")
    log(f"📊 Deep Enrichment Results")
    log(f"{'='*60}")
    log(f"  总人数: {stats['total']}")
    log(f"  ─────────────────────────")
    log(f"  📧 深度邮箱:")
    log(f"     主页爬取: {stats['deep_email_homepage']}")
    log(f"     GitHub commit: {stats['deep_email_github']}")
    log(f"     合计: {stats['deep_email_homepage'] + stats['deep_email_github']}")
    log(f"  🐙 新增 GitHub: {stats['deep_github_new']}")
    log(f"  ─────────────────────────")
    log(f"  按 Tier 分布:")
    for tier in ["S", "A+", "A", "B", "C"]:
        if tier in stats["by_tier"]:
            t = stats["by_tier"][tier]
            log(f"    {tier:3s}: {t['total']:4d} | deep_email: {t['deep_email']:3d} | "
                f"deep_github: {t['deep_github']:3d}")
    
    return stats


# ============================================================
# CLI 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Academic Deep Enricher — 学术人才深度联系方式补充")
    parser.add_argument("--input", required=True,
                       help="输入 full.json 文件路径")
    parser.add_argument("--serper-cache", required=True,
                       help="Serper 缓存文件路径 (_serper_cache.json)")
    parser.add_argument("--output-dir", required=True,
                       help="输出目录")
    parser.add_argument("--cache", default=None,
                       help="深度补充缓存路径 (默认: output-dir/_deep_cache.json)")
    parser.add_argument("--mode", choices=["homepage", "github-commit", "all"],
                       default="all", help="运行模式 (默认: all)")
    parser.add_argument("--max-users", type=int, default=None,
                       help="限制处理人数 (测试用)")
    parser.add_argument("--workers", type=int, default=10,
                       help="并发 worker 数 (默认: 10)")
    args = parser.parse_args()
    
    global _global_cache, _global_cache_path
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        sys.exit(1)
    
    serper_path = Path(args.serper_cache)
    if not serper_path.exists():
        print(f"❌ Serper 缓存不存在: {serper_path}")
        sys.exit(1)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    log(f"{'='*60}")
    log(f"🔬 Academic Deep Enricher")
    log(f"   输入: {input_path.name}")
    log(f"   Serper 缓存: {serper_path.name}")
    log(f"   模式: {args.mode}")
    log(f"{'='*60}")
    
    authors = load_json(input_path)
    if args.max_users:
        authors = authors[:args.max_users]
    log(f"  📥 加载 {len(authors)} 人")
    
    serper_cache = {}
    try:
        serper_cache = load_json(serper_path)
        log(f"  📦 Serper 缓存: {len(serper_cache)} 条")
    except Exception as e:
        log(f"  ⚠️  Serper 缓存加载失败: {e}")
    
    # 加载深度缓存
    cache_path = Path(args.cache) if args.cache else (output_dir / "_deep_cache.json")
    deep_cache = {}
    if cache_path.exists():
        try:
            deep_cache = load_json(cache_path)
            if isinstance(deep_cache, list):
                deep_cache = {}
            log(f"  📦 恢复深度缓存: {len(deep_cache)} 条 (断点续传生效)")
        except Exception:
            bak = cache_path.with_suffix('.json.bak')
            if bak.exists():
                try:
                    deep_cache = load_json(bak)
                    if isinstance(deep_cache, list):
                        deep_cache = {}
                    log(f"  📦 从备份恢复缓存: {len(deep_cache)} 条")
                except Exception:
                    pass
    
    # 注册全局缓存引用
    _global_cache = deep_cache
    _global_cache_path = cache_path
    
    # Mode A: 主页深度爬取
    if args.mode in ("homepage", "all"):
        authors = enrich_via_homepage(authors, serper_cache, deep_cache, cache_path,
                                       max_workers=args.workers)
        safe_save_json(deep_cache, cache_path)
    
    # Mode B: GitHub commit email
    if args.mode in ("github-commit", "all"):
        authors = enrich_via_github_commit(authors, serper_cache, deep_cache, cache_path)
        safe_save_json(deep_cache, cache_path)
    
    # 报告
    stats = generate_report(authors)
    
    # 保存结果
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem.replace('_full', '')
    output_path = output_dir / f"{stem}_deep_{args.mode}_{ts}.json"
    safe_save_json(authors, output_path, backup=False)
    log(f"\n💾 结果已保存: {output_path}")
    
    stats_path = output_dir / f"{stem}_deep_{args.mode}_{ts}_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    log(f"📊 统计已保存: {stats_path}")
    log(f"📦 缓存: {cache_path} ({len(deep_cache)} 条, 下次可断点续传)")


if __name__ == "__main__":
    main()
