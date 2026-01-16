#!/usr/bin/env python3
"""
LAMDA 候选人个人网站联系信息挖掘工具
从个人网站中批量提取邮箱和工作单位信息
"""

import requests
import re
import csv
import time
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin

# 忽略 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PersonalWebsiteScraper:
    """个人网站联系信息提取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.scraped_count = 0
        self.email_found = 0
        self.company_found = 0

    def scrape_website(self, website_url: str) -> Dict:
        """
        爬取个人网站，提取联系信息

        Args:
            website_url: 个人网站 URL

        Returns:
            包含邮箱、公司等信息的字典
        """
        result = {
            'website_email': '',
            'website_company': '',
            'website_position': ''
        }

        if not website_url:
            return result

        # 确保URL完整
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url

        try:
            resp = self.session.get(website_url, timeout=30, verify=False)
            self.scraped_count += 1

            if resp.status_code != 200:
                return result

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 1. 提取邮箱
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, resp.text)

            # 过滤邮箱
            for email in emails:
                if ('noreply' not in email and
                    'github' not in email and
                    'example' not in email and
                    'localhost' not in email and
                    'test' not in email.lower()):
                    result['website_email'] = email
                    self.email_found += 1
                    break

            # 2. 提取机构信息 - 查找 meta 标签
            meta_keywords = ['author', 'organization', 'company', 'affiliation', 'workplace']

            for meta_name in meta_keywords:
                meta_elem = soup.find('meta', {'name': meta_name}) or soup.find('meta', {'property': meta_name})
                if meta_elem:
                    content = meta_elem.get('content', '').strip()
                    if content and len(content) < 100:
                        result['website_company'] = content
                        self.company_found += 1
                        break

            # 3. 从页面文本中提取机构
            if not result['website_company']:
                org_patterns = [
                    r'(?:Ph\.?D\.?\s*(?:Student|Candidate)?\s*(?:at|@)\s+([^\n,\.]{5,80}))',
                    r'(?:Graduate Student|Researcher|Professor|Faculty)\s+(?:at|@)\s+([^\n,\.]{5,80}))',
                ]

                for pattern in org_patterns:
                    matches = re.finditer(pattern, resp.text, re.IGNORECASE)
                    for match in matches:
                        org = match.group(1).strip()
                        if org and len(org) < 100:
                            result['website_company'] = org
                            self.company_found += 1
                            break

                    if result['website_company']:
                        break

            # 4. 特定网站类型的处理
            # GitHub Pages
            if 'github.io' in website_url:
                # 尝试从 About 部分提取
                about_section = soup.find('div', id='about') or soup.find('section', id='about')
                if about_section:
                    about_emails = re.findall(email_pattern, about_section.get_text())
                    for email in about_emails:
                        if 'noreply' not in email and 'github' not in email:
                            result['website_email'] = email
                            break

        except Exception as e:
            pass

        return result

    def process_candidates(self, input_csv: str, output_csv: str, limit: int = None):
        """
        处理候选人 CSV，从个人网站提取联系信息

        Args:
            input_csv: 输入 CSV 文件（已有 contact_blog 字段）
            output_csv: 输出 CSV 文件
            limit: 限制处理数量（用于测试）
        """
        print("="*80)
        print("LAMDA 候选人个人网站联系信息挖掘")
        print("="*80)
        print(f"\n输入文件: {input_csv}")
        print(f"输出文件: {output_csv}\n")

        # 读取候选人
        candidates = []
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            candidates = list(reader)

        # 筛选有个人网站的候选人
        with_website = [c for c in candidates if c.get('contact_blog') and c['contact_blog'] != '']

        if limit:
            with_website = with_website[:limit]

        print(f"📊 总候选人: {len(candidates)}")
        print(f"✓ 有个人网站: {len(with_website)}\n")

        # 处理每个有个人网站的候选人
        enriched = []

        for i, candidate in enumerate(with_website, 1):
            name = candidate['姓名']
            website = candidate['contact_blog']
            score = candidate.get('github_score', 0)

            print(f"[{i}/{len(with_website)}] {name} | {score}分")
            print(f"  网站: {website[:60]}...")

            # 爬取网站
            website_info = self.scrape_website(website)

            # 添加到候选人记录
            candidate['website_email'] = website_info['website_email']
            candidate['website_company'] = website_info['website_company']
            candidate['website_position'] = website_info['website_position']

            # 显示结果
            if website_info['website_email']:
                print(f"  ✓ 邮箱: {website_info['website_email']}")

            if website_info['website_company']:
                print(f"  ✓ 机构: {website_info['website_company'][:60]}")

            if not website_info['website_email'] and not website_info['website_company']:
                print(f"  ⚠️ 未找到联系信息")

            print()

            enriched.append(candidate)

            # 礼貌延迟
            time.sleep(2)

        # 更新所有候选人
        # 1. 已处理的候选人（添加网站信息）
        processed_usernames = {c['github_username'] for c in enriched}
        for c in candidates:
            if c.get('github_username') in processed_usernames:
                # 找到对应的增强记录
                enhanced_record = next(
                    (e for e in enriched if e['github_username'] == c['github_username']),
                    None
                )
                if enhanced_record:
                    c.update({
                        'website_email': enhanced_record.get('website_email', ''),
                        'website_company': enhanced_record.get('website_company', ''),
                        'website_position': enhanced_record.get('website_position', '')
                    })
            else:
                # 没有个人网站的候选人，添加空字段
                c['website_email'] = ''
                c['website_company'] = ''
                c['website_position'] = ''

        # 保存结果
        fieldnames = list(candidates[0].keys())
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)

        # 统计
        print("="*80)
        print("个人网站挖掘统计")
        print("="*80)
        print(f"处理网站数: {self.scraped_count}")
        print(f"找到邮箱: {self.email_found} ({self.email_found/self.scraped_count*100:.1f}%)")
        print(f"找到机构: {self.company_found} ({self.company_found/self.scraped_count*100:.1f}%)")

        # 对比邮箱数量
        original_emails = sum(1 for c in candidates if c.get('contact_email') and c['contact_email'] != '')
        website_emails = sum(1 for c in candidates if c.get('website_email') and c['website_email'] != '')
        total_emails = sum(1 for c in candidates if
                          (c.get('contact_email') and c['contact_email'] != '') or
                          (c.get('website_email') and c['website_email'] != ''))

        print(f"\n邮箱统计:")
        print(f"  GitHub API 邮箱: {original_emails}")
        print(f"  个人网站邮箱: {website_emails}")
        print(f"  总邮箱数: {total_emails}")
        print(f"  新增邮箱: {website_emails}")

        # 显示找到的联系方式
        print(f"\n📊 从个人网站找到的联系信息:")
        print("-"*80)

        found_contacts = [c for c in candidates if c.get('website_email') or c.get('website_company')]
        found_contacts_sorted = sorted(found_contacts, key=lambda x: float(x.get('github_score', 0)), reverse=True)[:15]

        for c in found_contacts_sorted:
            email = c.get('website_email', '')
            company = c.get('website_company', '')
            print(f"{c['姓名']:10s} | 邮箱: {email:30s} | 机构: {company[:40]}")

        print(f"\n✓ 结果已保存到: {output_csv}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='LAMDA 个人网站联系信息挖掘工具')
    parser.add_argument('--input', type=str, default='lamda_candidates_contact_enhanced.csv',
                       help='输入 CSV 文件')
    parser.add_argument('--output', type=str, default='lamda_candidates_final.csv',
                       help='输出 CSV 文件')
    parser.add_argument('--limit', type=int, default=None,
                       help='限制处理数量（用于测试）')

    args = parser.parse_args()

    scraper = PersonalWebsiteScraper()
    scraper.process_candidates(args.input, args.output, args.limit)


if __name__ == '__main__':
    main()
