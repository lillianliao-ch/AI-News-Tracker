#!/usr/bin/env python3
"""
导出有联系方式的候选人
"""

import csv

# 读取最终数据
with open('lamda_candidates_final.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    candidates = list(reader)

# 筛选有邮箱或工作单位的
with_contact = []
for c in candidates:
    has_email = (c.get('contact_email') and c['contact_email'] != '') or \
                (c.get('website_email') and c['website_email'] != '')
    has_company = (c.get('contact_company') and c['contact_company'] != '') or \
                  (c.get('website_company') and c['website_company'] != '') or \
                  (c.get('github_company') and c['github_company'] != '')

    if has_email or has_company:
        # 合并邮箱和公司信息
        email = c.get('contact_email', '') or c.get('website_email', '')
        company = c.get('contact_company', '') or c.get('website_company', '') or c.get('github_company', '')
        blog = c.get('contact_blog', '')
        twitter = c.get('contact_twitter', '')
        score = float(c.get('github_score', 0))

        with_contact.append({
            '姓名': c['姓名'],
            'github_username': c.get('github_username', ''),
            'github_score': score,
            'github_stars': c.get('github_stars', 0),
            'github_repos': c.get('github_repos', 0),
            '邮箱': email,
            '工作单位': company,
            '个人网站': blog,
            'Twitter': twitter,
            '邮箱来源': 'GitHub API' if c.get('contact_email') else ('个人网站' if c.get('website_email') else ''),
        })

# 按分数排序
with_contact_sorted = sorted(with_contact, key=lambda x: x['github_score'], reverse=True)

# 导出完整 CSV
fieldnames = ['姓名', 'github_username', 'github_score', 'github_stars', 'github_repos',
              '邮箱', '工作单位', '个人网站', 'Twitter', '邮箱来源']

with open('candidates_with_contacts.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(with_contact_sorted)

print(f"✓ 已导出 {len(with_contact_sorted)} 位有联系方式的候选人")
print(f"  文件: candidates_with_contacts.csv")

# 导出有邮箱的候选人
with_email = [c for c in with_contact_sorted if c['邮箱']]

with open('candidates_with_email.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(with_email)

print(f"✓ 已导出 {len(with_email)} 位有邮箱的候选人")
print(f"  文件: candidates_with_email.csv")

# 导出高质量且有邮箱的候选人
high_quality_with_email = [c for c in with_email if c['github_score'] >= 70]

with open('high_quality_with_email.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(high_quality_with_email)

print(f"✓ 已导出 {len(high_quality_with_email)} 位高质量(≥70分)且有邮箱的候选人")
print(f"  文件: high_quality_with_email.csv")

# 打印高质量候选人名单
print("\n" + "="*80)
print("🎯 高质量且有邮箱的候选人 (立即可联系)")
print("="*80)

for c in high_quality_with_email:
    print(f"\n{c['姓名']} | {c['github_score']:.0f}分")
    print(f"  邮箱: {c['邮箱']}")
    print(f"  工作单位: {c['工作单位']}")
    print(f"  GitHub: https://github.com/{c['github_username']}")
    print(f"  Stars: {c['github_stars']} | Repos: {c['github_repos']}")

print("\n" + "="*80)
