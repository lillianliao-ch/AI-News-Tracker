#!/usr/bin/env python3
"""
使用修复后的 GitHub URL 重新提取邮箱
"""

import csv
import os
import time
from github_email_enricher import GitHubEmailExtractor


def main():
    """使用修复后的 URL 重新提取邮箱"""
    print("=" * 80)
    print("使用修复后的 GitHub URL 重新提取邮箱")
    print("=" * 80)
    print()

    # 读取修复后的候选人数据
    input_csv = 'lamda_candidates_urls_fixed.csv'
    output_csv = 'lamda_candidates_final_enriched.csv'

    candidates = []
    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        candidates = list(reader)

    print(f"📊 总候选人: {len(candidates)}")

    # 筛选有修复后 GitHub 的候选人
    with_github = [c for c in candidates if c.get('github_url_fixed') and c['github_url_fixed'].strip()]
    print(f"✓ 有 GitHub (修复后): {len(with_github)}")
    print()

    # 筛选之前没有邮箱的候选人
    need_extraction = [c for c in with_github
                       if not c.get('github_email') or not c['github_email'].strip()]
    print(f"📧 需要提取邮箱: {len(need_extraction)}")
    print(f"✓ 已有邮箱: {len(with_github) - len(need_extraction)}")
    print()

    # 获取 GitHub Token
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("⚠️ 未设置 GITHUB_TOKEN 环境变量")
        print("   继续执行（未认证模式，限流更严格）")
        print()

    # 创建提取器
    extractor = GitHubEmailExtractor(github_token=token)

    # 统计
    stats = {
        'total': len(need_extraction),
        'processed': 0,
        'emails_found': 0,
        'from_api': 0,
        'from_website': 0,
        'from_commits': 0,
        'from_readme': 0,
        'failed': 0
    }

    # 处理每个候选人
    print("开始提取邮箱...")
    print("=" * 80)
    print()

    for i, candidate in enumerate(need_extraction, 1):
        name = candidate['姓名']
        github_url = candidate['github_url_fixed']

        print(f"[{i}/{len(need_extraction)}] {name}")
        print(f"  GitHub: {github_url}")
        print(f"  原始: {candidate.get('github_url_original', 'N/A')}")

        try:
            # 提取邮箱
            emails = extractor.extract_all_emails(github_url)

            if emails['all']:
                # 找到邮箱
                candidate['github_email'] = emails['all'][0]
                candidate['email_source'] = '+'.join([
                    'API' if emails['api'] else '',
                    '网站' if emails['website'] else '',
                    'Commits' if emails['commits'] else '',
                    'README' if emails['readme'] else ''
                ]).strip('+')

                candidate['email_extraction_details'] = f"找到 {len(emails['all'])} 个邮箱: {emails['all']}"

                # 更新统计
                stats['emails_found'] += 1
                if emails['api']:
                    stats['from_api'] += 1
                if emails['website']:
                    stats['from_website'] += 1
                if emails['commits']:
                    stats['from_commits'] += 1
                if emails['readme']:
                    stats['from_readme'] += 1

                print(f"  ✓ 邮箱: {candidate['github_email']}")
                print(f"  来源: {candidate['email_source']}")

            else:
                # 未找到邮箱
                candidate['github_email'] = ''
                candidate['email_source'] = '未找到'
                candidate['email_extraction_details'] = '所有来源均未找到邮箱'

                print(f"  ✗ 未找到邮箱")

            stats['processed'] += 1

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            stats['failed'] += 1
            candidate['github_email'] = ''
            candidate['email_source'] = '错误'
            candidate['email_extraction_details'] = str(e)

        print()

        # 礼貌延迟（避免限流）
        if i < len(need_extraction):
            time.sleep(2)

    # 写入结果
    print("=" * 80)
    print("保存结果...")
    print()

    fieldnames = list(candidates[0].keys())
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)

    # 打印统计
    print("=" * 80)
    print("提取统计")
    print("=" * 80)
    print(f"总数: {stats['total']}")
    print(f"已处理: {stats['processed']}")
    print(f"找到邮箱: {stats['emails_found']} ({stats['emails_found']/stats['processed']*100:.1f}%)")
    print(f"失败: {stats['failed']}")
    print()
    print(f"来源分布:")
    print(f"  API: {stats['from_api']}")
    print(f"  网站: {stats['from_website']}")
    print(f"  Commits: {stats['from_commits']}")
    print(f"  README: {stats['from_readme']}")
    print()

    # 显示找到邮箱的候选人
    print("🏆 新找到邮箱的候选人:")
    found_email = [c for c in need_extraction if c.get('github_email') and c['github_email'].strip()]

    if found_email:
        for c in found_email:
            print(f"  • {c['姓名']:10s} | {c['github_email']:30s} | {c['email_source']}")
    else:
        print("  无")

    print()
    print(f"✓ 结果已保存到: {output_csv}")
    print(f"✓ 新找到 {len(found_email)} 个邮箱")
    print()


if __name__ == '__main__':
    main()
