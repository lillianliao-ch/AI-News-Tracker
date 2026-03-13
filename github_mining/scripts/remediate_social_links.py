#!/usr/bin/env python3
"""
补救脚本 v2：为已导入的候选人补充提取社交链接 (LinkedIn/Scholar/Twitter)
修复 v1 的问题：单线程、SQLite 兼容、强制 unbuffered
"""
import sys, os, re, requests, urllib3
from pathlib import Path
from bs4 import BeautifulSoup

# 强制 unbuffered 输出
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

urllib3.disable_warnings()
print('🚀 补救脚本 v2 启动')

HEADHUNTER_DIR = Path(__file__).parent.parent.parent / "personal-ai-headhunter"
sys.path.insert(0, str(HEADHUNTER_DIR))
os.chdir(HEADHUNTER_DIR)

from database import SessionLocal, Candidate


def extract_social_links(url: str) -> dict:
    """从网页 HTML 中提取社交链接"""
    if not url or not url.strip():
        return {}
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    url_lower = url.lower()

    # 如果 blog 就是 LinkedIn URL，直接提取
    if 'linkedin.com/' in url_lower:
        return {'linkedin_url': url}

    # 跳过纯社交平台
    skip = ['twitter.com/', 'x.com/', 'weibo.com/', 'bilibili.com/',
            'youtube.com/', 'facebook.com/', 'instagram.com/']
    if any(d in url_lower for d in skip):
        return {}

    # github.com profile 跳过, 但 github.io 保留
    if 'github.com/' in url_lower and '.github.io' not in url_lower:
        return {}

    try:
        resp = requests.get(url, timeout=10, verify=False, allow_redirects=True,
                           headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
        if resp.status_code != 200:
            return {}

        soup = BeautifulSoup(resp.text, 'html.parser')
        all_links = [a.get('href', '') for a in soup.find_all('a', href=True)]

        result = {}
        li = [l for l in all_links if 'linkedin.com/in/' in l]
        if li:
            result['linkedin_url'] = li[0]

        tw = [l for l in all_links if 'twitter.com/' in l or 'x.com/' in l]
        if tw:
            result['twitter_url'] = tw[0]

        sc = [l for l in all_links if 'scholar.google' in l]
        if sc:
            result['scholar_url'] = sc[0]

        return result
    except Exception as e:
        return {}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    session = SessionLocal()
    candidates = session.query(Candidate.id, Candidate.personal_website).filter(
        Candidate.source == 'github',
        Candidate.personal_website.isnot(None),
        Candidate.personal_website != '',
        (Candidate.linkedin_url.is_(None) | (Candidate.linkedin_url == ''))
    ).all()

    print(f"📊 找到 {len(candidates)} 个候选人", flush=True)
    if args.limit:
        candidates = candidates[:args.limit]

    linkedin_found = 0
    updated = 0
    errors = 0
    skipped = 0

    print(f'🔄 开始处理 {len(candidates)} 个候选人...')
    # 单线程顺序处理（避免 SQLite 并发问题）
    for i, (cid, website) in enumerate(candidates, 1):
        links = extract_social_links(website)

        if not links:
            skipped += 1
        else:
            if 'linkedin_url' in links:
                linkedin_found += 1

            if not args.dry_run:
                try:
                    c = session.get(Candidate, cid)
                    if c and links.get('linkedin_url') and not c.linkedin_url:
                        c.linkedin_url = links['linkedin_url']
                        updated += 1
                except Exception as e:
                    errors += 1
                    print(f"  DB error: {e}", flush=True)

        if i % 200 == 0:
            if not args.dry_run:
                session.commit()
            print(f"  进度: {i}/{len(candidates)} | LinkedIn: +{linkedin_found} | updated: {updated} | errors: {errors}", flush=True)

    if not args.dry_run:
        session.commit()

    print(f"\n{'='*60}", flush=True)
    print(f"📊 结果: 处理 {len(candidates)} | LinkedIn找到: {linkedin_found} | DB更新: {updated} | 跳过: {skipped} | 错误: {errors}", flush=True)
    if args.dry_run:
        print(f"⚠️ DRY-RUN 模式", flush=True)

    session.close()


if __name__ == '__main__':
    main()
