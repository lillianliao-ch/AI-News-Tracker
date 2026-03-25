#!/usr/bin/env python3
"""
Academic Contact Enricher — 学术人才联系方式增强 (v3)

两条路径并行补充联系方式:
  Method 1: Paper PDF Email Extraction (S2 API → ArXiv / OpenReview)
  Method 2: Google Scholar Homepage Lookup (scholarly)

用法:
  python3 academic_contact_enricher.py \
    --input all_conf_2025_full.json \
    --output data/academic/runs/.../outputs/

  # 只跑 PDF 提取（跳过 Scholar，更快）
  python3 academic_contact_enricher.py --input ... --output ... --pdf-only

  # 限制处理人数
  python3 academic_contact_enricher.py --input ... --output ... --max-users 20

特性:
  - 断点续传: 缓存文件自动保存/恢复进度
  - 定期落盘: 每 50 条自动保存缓存
  - 安全写入: 原子写（先写 .tmp 再 rename）+ .bak 备份
  - 时间戳输出: 输出文件名自动带时间戳
  - 优雅退出: Ctrl+C 保存缓存后退出
"""

import os
import re
import sys
import json
import time
import signal
import shutil
import argparse
import tempfile
import functools
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# 强制刷新输出
print = functools.partial(print, flush=True)

SCRIPT_DIR = Path(__file__).parent

# 全局：用于 Ctrl+C 保护
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
    """安全写入 JSON：先写 .tmp 再 rename，避免写半截。可选 .bak 备份。"""
    path = Path(path)
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, bak)
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.rename(path)


def save_json(data, path):
    """简单写入（兼容旧调用）"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
# Method 1: Paper PDF Email Extraction
# ============================================================

def find_pdf_url(author: dict) -> Optional[str]:
    """
    尝试为学者找到一篇论文的 PDF URL。
    v2: S2 API 优先（已有 s2_id，速度快），OpenReview 兜底。
    """
    papers = author.get("papers", [])
    name = author.get("name", "")

    # 策略 1: S2 API → ArXiv / Open Access PDF（优先，因为已有 s2_id）
    s2_id = author.get("s2_id")
    if s2_id:
        for attempt in range(3):  # 最多重试 3 次
            try:
                resp = requests.get(
                    f"https://api.semanticscholar.org/graph/v1/author/{s2_id}/papers",
                    params={"fields": "title,externalIds,openAccessPdf", "limit": 10},
                    timeout=15
                )
                if resp.status_code == 200:
                    s2_papers = resp.json().get("data", [])
                    for p in s2_papers:
                        # ArXiv PDF (最稳定)
                        ext = p.get("externalIds") or {}
                        arxiv_id = ext.get("ArXiv")
                        if arxiv_id:
                            return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                        # OpenAccess PDF
                        oa = p.get("openAccessPdf") or {}
                        if oa.get("url"):
                            return oa["url"]
                    break  # 成功但没找到 PDF，不重试
                elif resp.status_code == 429:
                    wait = 5 * (attempt + 1)
                    time.sleep(wait)
                else:
                    break
            except Exception:
                break

    # 策略 2: OpenReview 标题搜索（兜底）
    for paper_title in papers[:2]:  # 最多试 2 篇
        try:
            resp = requests.get(
                "https://api2.openreview.net/notes/search",
                params={"query": paper_title, "limit": 3},
                timeout=15
            )
            if resp.status_code == 200:
                notes = resp.json().get("notes", [])
                for note in notes:
                    content = note.get("content", {})
                    note_title = content.get("title", {})
                    if isinstance(note_title, dict):
                        note_title = note_title.get("value", "")
                    if note_title and _fuzzy_title_match(paper_title, note_title):
                        pdf_path = content.get("pdf", {})
                        if isinstance(pdf_path, dict):
                            pdf_path = pdf_path.get("value", "")
                        if pdf_path:
                            return f"https://openreview.net{pdf_path}"
                        forum_id = note.get("forum")
                        if forum_id:
                            return f"https://openreview.net/pdf?id={forum_id}"
        except Exception:
            pass
        time.sleep(0.3)

    return None


def _fuzzy_title_match(title1: str, title2: str) -> bool:
    """简单的标题模糊匹配"""
    def normalize(t):
        return re.sub(r'[^a-z0-9]', '', t.lower())
    n1, n2 = normalize(title1), normalize(title2)
    if not n1 or not n2:
        return False
    # 较短的标题被较长的包含 or 80% 重叠
    if n1 in n2 or n2 in n1:
        return True
    # Jaccard on character n-grams (quick dirty fuzzy)
    s1, s2 = set(n1[i:i+4] for i in range(len(n1)-3)), set(n2[i:i+4] for i in range(len(n2)-3))
    if not s1 or not s2:
        return False
    jaccard = len(s1 & s2) / len(s1 | s2)
    return jaccard > 0.5


def extract_emails_from_pdf(pdf_url: str, author_name: str) -> List[str]:
    """
    下载 PDF → 提取前两页文字 → regex 找邮箱 → 过滤
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        log("  ⚠️  PyMuPDF 未安装，跳过 PDF 提取")
        return []

    try:
        resp = requests.get(pdf_url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (academic research)"
        })
        if resp.status_code != 200:
            return []

        # 保存临时 PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        try:
            doc = fitz.open(tmp_path)
            # 只提取前 2 页（邮箱通常在第一页）
            text = ""
            for page_num in range(min(2, len(doc))):
                text += doc[page_num].get_text()
            doc.close()
        finally:
            os.unlink(tmp_path)

        if not text:
            return []

        # 提取邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        raw_emails = re.findall(email_pattern, text)

        # 过滤无效邮箱
        valid_emails = []
        for e in raw_emails:
            e = e.lower().strip()
            # 跳过明显无效的
            if any(x in e for x in ['noreply', 'example.com', 'domain.com',
                                     'review', 'editor', 'submission', 'openreview']):
                continue
            # 基本格式校验
            if re.match(r'^[^@]+@[^@]+\.[^@]+$', e):
                valid_emails.append(e)

        return list(set(valid_emails))

    except Exception as e:
        return []


def _match_email_to_author(emails: List[str], author_name: str) -> Tuple[Optional[str], str, List[str]]:
    """
    v3: 严格匹配邮箱与作者名，返回 (best_email, confidence, all_emails)
    confidence: 'high' (名字直接出现), 'medium' (缩写匹配), 'none' (无匹配)

    v3 fixes:
    - 短姓氏 (Yu/Ma/Li/Xu) 必须配合 first name 才算匹配
    - 姓氏必须是 local part 的独立子串（边界检查，避免 'long' 匹配 'wujialong'）
    """
    if not emails or not author_name:
        return None, "none", emails

    name_parts = [p.lower() for p in author_name.split()]
    last_name = name_parts[-1] if name_parts else ""
    first_name = name_parts[0] if len(name_parts) > 1 else ""
    # 首字母缩写: "Jong Chul Ye" → initials="jcy", first_last="jye"
    initials = "".join(p[0] for p in name_parts if p)
    first_last = f"{name_parts[0][0]}{last_name}" if len(name_parts) > 1 else ""

    def _is_boundary_match(haystack: str, needle: str) -> bool:
        """Check if needle appears as a 'boundary' substring in haystack.
        e.g., 'tang' in 'tangjili' → True (at start)
              'long' in 'wujialong' → False (middle, not boundary)
              'gao' in 'gaosh' → True (at start)
              'cao' in 'caoxiaochun' → True (at start)
        """
        idx = haystack.find(needle)
        if idx == -1:
            return False
        # At start or end of local part = boundary match
        if idx == 0 or idx + len(needle) == len(haystack):
            return True
        # Check if preceded/followed by common separators in original
        return False

    def score(email: str) -> Tuple[int, str]:
        local = email.split('@')[0].lower()
        local_clean = re.sub(r'\d+$', '', local)
        local_flat = re.sub(r'[._-]', '', local_clean)

        # === High confidence patterns ===

        # 1. Both first AND last name in local part (strongest)
        if (last_name and len(last_name) >= 2 and last_name in local_flat and
                first_name and len(first_name) >= 2 and first_name in local_flat):
            return (10, "high")

        # 2. Last name at boundary + first initial
        if last_name and len(last_name) >= 3 and _is_boundary_match(local_flat, last_name):
            if first_name and first_name[0] in local_flat:
                return (8, "high")
            return (6, "high")

        # 3. Short last name (2 chars: Yu, Ma, Li, Xu...) only matches
        #    if combined with first name evidence
        if last_name and len(last_name) == 2 and _is_boundary_match(local_flat, last_name):
            if first_name and (first_name in local_flat or first_name[:3] in local_flat):
                return (7, "high")
            # Short last name alone is NOT enough

        # 4. First name (3+ chars) at boundary
        if first_name and len(first_name) >= 3 and _is_boundary_match(local_flat, first_name):
            return (5, "high")

        # === Medium confidence patterns ===

        # 5. Abbreviated patterns: "jcye@" "jye@"
        if first_last and len(first_last) >= 3 and local_flat.startswith(first_last):
            return (4, "medium")
        if initials and len(initials) >= 2 and local_flat.startswith(initials):
            return (3, "medium")

        return (0, "none")

    scored = [(e, *score(e)) for e in emails]
    scored.sort(key=lambda x: x[1], reverse=True)

    best_email, best_score, best_conf = scored[0]
    if best_score >= 3:
        return best_email, best_conf, emails
    else:
        return None, "none", emails


def enrich_via_pdf(authors: List[Dict], cache: dict, cache_path: Path = None) -> List[Dict]:
    """Method 1: 通过论文 PDF 提取邮箱（带定期落盘和进度 ETA）"""
    log(f"\n{'='*60}")
    log(f"📄 Method 1: Paper PDF Email Extraction")
    log(f"{'='*60}")

    found = 0
    errors = 0
    skipped = 0
    new_queries = 0
    start_time = time.time()

    for i, author in enumerate(authors):
        name = author.get("name", "")
        s2_id = author.get("s2_id", "")

        # 没有 s2_id 的跳过（无法查 S2 API，OpenReview 标题搜索太慢且不准）
        if not s2_id:
            skipped += 1
            continue

        # 使用 s2_id 作为 cache key（更唯一），name 作为 fallback
        cache_key = f"pdf::{s2_id}::{name}"

        if cache_key in cache:
            cached = cache[cache_key]
            if cached.get("matched_email"):
                author["pdf_matched_email"] = cached["matched_email"]
                author["pdf_match_confidence"] = cached.get("match_confidence", "high")
                author["pdf_emails"] = cached.get("pdf_emails", [])
                author["pdf_url"] = cached.get("pdf_url")
                found += 1
            elif cached.get("pdf_emails"):
                author["pdf_emails_unmatched"] = cached["pdf_emails"]
                author["pdf_url"] = cached.get("pdf_url")
            skipped += 1
            continue

        new_queries += 1

        # 进度 + ETA
        if new_queries % 10 == 0:
            elapsed = time.time() - start_time
            processed = i + 1
            remaining = len(authors) - processed
            speed = new_queries / max(elapsed, 1)
            eta_min = remaining / max(speed, 0.01) / 60
            log(f"  进度: {processed}/{len(authors)} (found: {found}, "
                f"speed: {speed:.1f}/s, ETA: {eta_min:.0f}min)")

        # 找 PDF URL
        pdf_url = find_pdf_url(author)
        if not pdf_url:
            cache[cache_key] = {"pdf_emails": [], "pdf_url": None,
                                "matched_email": None, "match_confidence": "none"}
            # 定期落盘（每 50 条新查询）
            if cache_path and new_queries % 50 == 0:
                safe_save_json(cache, cache_path, backup=False)
            continue

        # 提取邮箱
        raw_emails = extract_emails_from_pdf(pdf_url, name)
        matched_email, confidence, all_emails = _match_email_to_author(
            raw_emails, name)

        cache_entry = {
            "pdf_emails": all_emails,
            "pdf_url": pdf_url,
            "matched_email": matched_email,
            "match_confidence": confidence,
        }

        if matched_email:
            author["pdf_emails"] = all_emails
            author["pdf_matched_email"] = matched_email
            author["pdf_match_confidence"] = confidence
            author["pdf_url"] = pdf_url
            found += 1
        elif all_emails:
            # 有邮箱但匹配不上 — 仍保存 raw emails 供手动审核
            author["pdf_emails_unmatched"] = all_emails
            author["pdf_url"] = pdf_url

        cache[cache_key] = cache_entry

        # 定期落盘（每 50 条新查询）
        if cache_path and new_queries % 50 == 0:
            safe_save_json(cache, cache_path, backup=False)

        time.sleep(0.3)  # Rate limiting

    elapsed = time.time() - start_time
    log(f"  ✅ PDF 提取完成: {found}/{len(authors)} 人找到邮箱 "
        f"({skipped} cached, {new_queries} new, {elapsed/60:.1f}min)")
    return authors


# ============================================================
# Method 2: Serper Google Search → Homepage → Contact Extraction
# ============================================================

SERPER_API_URL = "https://google.serper.dev/search"


def _serper_find_homepage(name: str, affiliation: str, api_key: str) -> Optional[str]:
    """用 Serper Google Search 找学者个人主页"""
    query = f"{name} {affiliation} homepage" if affiliation else f"{name} researcher homepage"
    try:
        resp = requests.post(
            SERPER_API_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 5},
            timeout=10
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        results = data.get("organic", [])

        # 从结果中找最可能是个人主页的链接
        # 优先级: 个人域名 > 大学 faculty 页 > Google Scholar
        homepage = None
        scholar_url = None
        for r in results:
            url = r.get("link", "")
            title = r.get("title", "").lower()
            # 跳过论文/搜索引擎/社交媒体
            if any(x in url for x in ["arxiv.org", "semanticscholar.org",
                                       "linkedin.com", "twitter.com", "x.com",
                                       "dblp.org", "openreview.net"]):
                continue
            # Google Scholar 页面单独记录
            if "scholar.google" in url:
                scholar_url = url
                continue
            # 找到个人主页
            if not homepage:
                homepage = url

        return homepage or scholar_url  # 优先个人主页，其次 Scholar

    except Exception:
        return None


def enrich_via_serper(authors: List[Dict], cache: dict, api_key: str,
                      cache_path: Path = None, tiers: List[str] = None) -> List[Dict]:
    """Method 2: 通过 Serper Google Search 找个人主页，再爬取联系方式"""
    log(f"\n{'='*60}")
    log(f"🔍 Method 2: Serper Google Search → Homepage → Contacts")
    log(f"{'='*60}")

    # 导入已有的联系方式提取器
    sys.path.append(str(SCRIPT_DIR))
    try:
        from extract_paper_email import extract_academic_contacts
    except ImportError:
        log("  ⚠️  extract_paper_email 未找到，仅提取 homepage URL")
        extract_academic_contacts = None

    found_homepage = 0
    found_email = 0
    found_github = 0
    skipped_cache = 0
    skipped_tier = 0
    new_queries = 0
    start_time = time.time()

    for i, author in enumerate(authors):
        name = author.get("name", "")
        tier = author.get("_academic_tier", "?")

        # Tier 过滤（只跑指定 tier）
        if tiers and tier not in tiers:
            skipped_tier += 1
            continue

        cache_key = f"serper::{name}"
        if cache_key in cache:
            cached = cache[cache_key]
            if cached.get("homepage"):
                author["serper_homepage"] = cached["homepage"]
                found_homepage += 1
            if cached.get("emails"):
                author["serper_emails"] = cached["emails"]
                found_email += 1
            if cached.get("github"):
                author["serper_github"] = cached["github"]
                found_github += 1
            skipped_cache += 1
            continue

        new_queries += 1

        # 进度 + ETA
        if new_queries % 10 == 0:
            elapsed = time.time() - start_time
            speed = new_queries / max(elapsed, 1)
            total_target = sum(1 for a in authors
                              if (not tiers or a.get('_academic_tier','?') in tiers))
            remaining = total_target - skipped_cache - new_queries
            eta_min = remaining / max(speed, 0.01) / 60
            log(f"  进度: {new_queries} queries (homepage: {found_homepage}, "
                f"email: {found_email}, ETA: {eta_min:.0f}min)")

        affiliation = author.get("affiliation", "") or ""
        result = {"homepage": None, "emails": [], "github": None, "linkedin": None}

        # Step A: Serper 搜索主页
        homepage = _serper_find_homepage(name, affiliation, api_key)
        if homepage:
            result["homepage"] = homepage
            author["serper_homepage"] = homepage
            found_homepage += 1

            # Step B: 爬主页提取联系方式 + 保存网页原文
            if extract_academic_contacts:
                try:
                    resp = requests.get(homepage, timeout=10, verify=False,
                                       headers={"User-Agent": "Mozilla/5.0 (Macintosh)"})
                    if resp.status_code == 200:
                        contacts = extract_academic_contacts(resp.text, homepage)
                        if contacts.get("emails"):
                            result["emails"] = contacts["emails"]
                            author["serper_emails"] = contacts["emails"]
                            found_email += 1
                        if contacts.get("github"):
                            result["github"] = contacts["github"]
                            author["serper_github"] = contacts["github"]
                            found_github += 1
                        if contacts.get("linkedin"):
                            result["linkedin"] = contacts["linkedin"]
                            author["serper_linkedin"] = contacts["linkedin"]
                        
                        # 保存网页原文 (供后续 LLM 富化使用)
                        from bs4 import BeautifulSoup as _BS
                        soup = _BS(resp.text, 'html.parser')
                        for tag in soup(['script', 'style', 'nav', 'footer']):
                            tag.decompose()
                        text_content = soup.get_text(separator='\n', strip=True)
                        if len(text_content) > 50:
                            if len(text_content) > 10000:
                                text_content = text_content[:10000] + '...[truncated]'
                            result["homepage_text"] = text_content
                except Exception:
                    pass

        cache[cache_key] = result

        # 定期落盘（每 50 条）
        if cache_path and new_queries % 50 == 0:
            safe_save_json(cache, cache_path, backup=False)

        time.sleep(0.5)  # Serper rate: 保守一点

    elapsed = time.time() - start_time
    log(f"  ✅ Serper 查询完成: "
        f"homepage={found_homepage}, email={found_email}, "
        f"github={found_github} / {new_queries} queries "
        f"({skipped_cache} cached, {skipped_tier} tier-skipped, "
        f"{elapsed/60:.1f}min)")
    return authors


# ============================================================
# 结果合并 & 统计
# ============================================================

def merge_and_report(authors: List[Dict]) -> dict:
    """合并两路结果，生成统计报告"""
    log(f"\n{'='*60}")
    log(f"📊 Enrichment Results")
    log(f"{'='*60}")

    stats = {
        "total": len(authors),
        "has_email_before": 0,
        "has_email_after": 0,
        "email_from_pdf": 0,
        "email_from_scholar": 0,
        "has_homepage_after": 0,
        "has_github_after": 0,
        "by_tier": {},
    }

    for author in authors:
        tier = author.get("_academic_tier", "?")
        if tier not in stats["by_tier"]:
            stats["by_tier"][tier] = {
                "total": 0, "email": 0, "homepage": 0, "github": 0
            }
        stats["by_tier"][tier]["total"] += 1

        # 合并逻辑：PDF matched email 优先
        best_email = None
        email_source = None
        email_confidence = None

        if author.get("email"):
            stats["has_email_before"] += 1
            best_email = author["email"]
            email_source = "original"
            email_confidence = "high"
        elif author.get("pdf_matched_email"):
            best_email = author["pdf_matched_email"]
            email_source = "pdf"
            email_confidence = author.get("pdf_match_confidence", "high")
            stats["email_from_pdf"] += 1
        elif author.get("scholar_emails"):
            best_email = author["scholar_emails"][0]
            email_source = "scholar"
            email_confidence = "medium"
            stats["email_from_scholar"] += 1

        if best_email:
            author["enriched_email"] = best_email
            author["email_source"] = email_source
            author["email_confidence"] = email_confidence
            stats["has_email_after"] += 1
            stats["by_tier"][tier]["email"] += 1

        # Track unmatched (have PDF emails but couldn't match to author)
        if not best_email and author.get("pdf_emails_unmatched"):
            stats.setdefault("has_unmatched_emails", 0)
            stats["has_unmatched_emails"] += 1

        # Homepage (原有 > Serper)
        homepage = (author.get("personal_website") or
                   author.get("serper_homepage"))
        if homepage:
            author["enriched_homepage"] = homepage
            stats["has_homepage_after"] += 1
            stats["by_tier"][tier]["homepage"] += 1

        # GitHub (原有 > Serper)
        github = (author.get("github_url") or
                 author.get("serper_github"))
        if github:
            author["enriched_github"] = github
            stats["has_github_after"] += 1
            stats["by_tier"][tier]["github"] += 1

    # 打印报告
    total = stats["total"]
    log(f"\n  总人数: {total}")
    log(f"  ───────────────────────────────────")
    log(f"  📧 Email 覆盖:")
    log(f"     之前: {stats['has_email_before']} ({stats['has_email_before']/total*100:.1f}%)")
    log(f"     之后: {stats['has_email_after']} ({stats['has_email_after']/total*100:.1f}%)")
    log(f"       └ PDF 来源:     {stats['email_from_pdf']}")
    log(f"       └ Scholar 来源: {stats['email_from_scholar']}")
    log(f"  🌐 Homepage: {stats['has_homepage_after']} ({stats['has_homepage_after']/total*100:.1f}%)")
    log(f"  🔗 GitHub:   {stats['has_github_after']} ({stats['has_github_after']/total*100:.1f}%)")
    log(f"  ───────────────────────────────────")
    log(f"  按 Tier 分布:")
    for tier in ["S", "A+", "A", "B", "C"]:
        if tier in stats["by_tier"]:
            t = stats["by_tier"][tier]
            log(f"    {tier:3s}: {t['total']:4d} | "
                f"email: {t['email']:3d} ({t['email']/t['total']*100:.0f}%) | "
                f"homepage: {t['homepage']:3d} | github: {t['github']:3d}")

    return stats


# ============================================================
# CLI 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Academic Contact Enricher — 学术人才联系方式增强 (v3)")
    parser.add_argument("--input", required=True, help="输入 JSON 文件")
    parser.add_argument("--output", required=True,
                       help="输出路径（目录则自动带时间戳，文件则原样使用）")
    parser.add_argument("--cache", default=None,
                       help="缓存文件路径（默认: 输出目录下 _enrichment_cache.json）")
    parser.add_argument("--pdf-only", action="store_true",
                       help="只跑 PDF 提取，跳过 Serper")
    parser.add_argument("--serper-only", action="store_true",
                       help="只跑 Serper，跳过 PDF")
    parser.add_argument("--serper-key", default=None,
                       help="Serper API Key (也可设环境变量 SERPER_API_KEY)")
    parser.add_argument("--serper-tiers", default=None,
                       help="Serper 只跑指定 tier，逗号分隔 (如 S,A+)")
    parser.add_argument("--max-users", type=int, default=None,
                       help="限制处理人数")
    args = parser.parse_args()

    global _global_cache, _global_cache_path

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        sys.exit(1)

    # 输出路径处理：支持目录（自动时间戳）或直接指定文件
    output_arg = Path(args.output)
    if output_arg.is_dir() or not output_arg.suffix:
        # 目录模式：自动生成带时间戳的文件名
        output_dir = output_arg
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = input_path.stem.replace('_full', '')
        output_path = output_dir / f"{stem}_contacts_{ts}.json"
    else:
        output_path = output_arg
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # 加载数据
    authors = load_json(input_path)
    total_loaded = len(authors)
    if args.max_users:
        authors = authors[:args.max_users]

    log(f"{'='*60}")
    log(f"🔬 Academic Contact Enricher v3")
    log(f"   输入: {input_path.name} ({total_loaded} 人, 使用 {len(authors)})")
    log(f"   输出: {output_path}")
    mode = 'PDF only' if args.pdf_only else 'Serper only' if args.serper_only else 'PDF + Serper'
    serper_key = args.serper_key or os.environ.get('SERPER_API_KEY', '')
    log(f"   模式: {mode}")
    if serper_key and not args.pdf_only:
        tiers = args.serper_tiers.split(',') if args.serper_tiers else None
        log(f"   Serper: key=***{serper_key[-6:]}, tiers={tiers or 'all'}")
    log(f"{'='*60}")

    # 加载缓存（断点续传核心）
    cache_path = Path(args.cache) if args.cache else (
        output_path.parent / "_enrichment_cache.json")
    cache = {}
    if cache_path.exists():
        try:
            cache = json.load(open(cache_path))
            log(f"  📦 恢复缓存: {len(cache)} 条 (断点续传生效)")
        except Exception:
            # 尝试 .bak
            bak = cache_path.with_suffix('.json.bak')
            if bak.exists():
                try:
                    cache = json.load(open(bak))
                    log(f"  📦 从备份恢复缓存: {len(cache)} 条")
                except Exception:
                    pass

    # 注册全局缓存引用（Ctrl+C 保护）
    _global_cache = cache
    _global_cache_path = cache_path

    # Method 1: PDF
    if not args.serper_only:
        authors = enrich_via_pdf(authors, cache, cache_path)
        safe_save_json(cache, cache_path)  # 落盘

    # Method 2: Serper Google Search
    if not args.pdf_only and serper_key:
        tiers = args.serper_tiers.split(',') if args.serper_tiers else None
        authors = enrich_via_serper(authors, cache, serper_key, cache_path, tiers)
        safe_save_json(cache, cache_path)  # 落盘
    elif not args.pdf_only and not serper_key:
        log("\n⚠️  未提供 Serper API Key，跳过 Method 2")
        log("   用法: --serper-key YOUR_KEY 或设环境变量 SERPER_API_KEY")

    # 合并 & 报告
    stats = merge_and_report(authors)

    # 保存结果（安全写入 + 备份）
    safe_save_json(authors, output_path)
    log(f"\n💾 结果已保存: {output_path}")

    # 也保存简洁统计
    stats_path = output_path.parent / f"{output_path.stem}_stats.json"
    save_json(stats, stats_path)
    log(f"📊 统计已保存: {stats_path}")
    log(f"📦 缓存文件: {cache_path} ({len(cache)} 条, 下次可断点续传)")


if __name__ == "__main__":
    main()
