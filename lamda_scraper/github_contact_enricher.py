#!/usr/bin/env python3
"""
LAMDA 候选人联系信息深度挖掘工具
从 GitHub 和个人网站中提取邮箱和工作单位信息
"""

import requests
import json
import csv
import time
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import ssl

# 忽略 SSL 验证错误（某些个人网站证书有问题）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# GitHub API 配置
GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class GitHubContactEnricher:
    """GitHub 联系信息深度挖掘器"""

    def __init__(self, github_token: Optional[str] = None):
        """初始化"""
        self.token = github_token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'application/vnd.github.v3+json'
        })

        if self.token:
            self.session.headers.update({
                'Authorization': f'token {self.token}'
            })

        self.requests_made = 0
        self.rate_limit_remaining = 5000

    def scrape_github_profile_page(self, username: str) -> Dict:
        """
        爬取 GitHub 用户主页，提取网页上显示的联系方式

        这可以获取到 API 中不包含的信息：
        - 邮箱（可能只在网页上显示）
        - Twitter/X
        - LinkedIn
        - 个人网站链接
        """
        url = f"https://github.com/{username}"

        extra_info = {
            'webpage_email': '',
            'webpage_twitter': '',
            'webpage_linkedin': '',
            'webpage_website': '',
            'webpage_company': ''
        }

        try:
            resp = self.session.get(url, timeout=30)
            self.requests_made += 1

            if resp.status_code != 200:
                return extra_info

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 方法1: 查找用户信息区域的 itemprop 属性
            # 邮箱通常在 <li class="vcard-detail" itemprop="email">
            email_elem = soup.find('li', {'itemprop': 'email'})
            if email_elem:
                email_link = email_elem.find('a')
                if email_link:
                    email = email_link.get_text(strip=True)
                    extra_info['webpage_email'] = email

            # 方法2: 查找所有 vcard-detail 元素
            vcard_items = soup.find_all('li', class_='vcard-detail')
            for item in vcard_items:
                link = item.find('a')
                if link:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    # 检查是否是邮箱链接
                    if href.startswith('mailto:') or '@' in text:
                        if not extra_info['webpage_email']:
                            email = text if '@' in text else href.replace('mailto:', '')
                            extra_info['webpage_email'] = email

                    # 检查是否是 Twitter/X 链接
                    if 'twitter.com' in href or 'x.com' in href:
                        extra_info['webpage_twitter'] = text

                    # 检查是否是 LinkedIn 链接
                    if 'linkedin.com' in href:
                        extra_info['webpage_linkedin'] = href

                    # 检查是否是个人网站
                    if href.startswith('http') and 'github.com' not in href and 'twitter.com' not in href:
                        if not extra_info['webpage_website']:
                            extra_info['webpage_website'] = href

            # 方法3: 查找公司信息
            company_elem = soup.find('li', {'itemprop': 'worksFor'})
            if company_elem:
                company_link = company_elem.find('a')
                if company_link:
                    company = company_link.get_text(strip=True)
                    extra_info['webpage_company'] = company

            # 方法4: 正则匹配页面中的邮箱
            if not extra_info['webpage_email']:
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                profile_div = soup.find('div', class_='js-profile-editable-area')
                if profile_div:
                    text = profile_div.get_text()
                    emails = re.findall(email_pattern, text)
                    if emails:
                        # 过滤掉明显不是个人邮箱的
                        for email in emails:
                            if 'noreply' not in email and 'github' not in email:
                                extra_info['webpage_email'] = email
                                break

        except Exception as e:
            print(f"  ⚠️ GitHub 网页解析错误 ({username}): {e}")

        return extra_info

    def scrape_personal_website(self, website_url: str) -> Dict:
        """
        爬取个人网站，提取联系信息

        Args:
            website_url: 个人网站 URL

        Returns:
            包含邮箱、工作单位等信息的字典
        """
        result = {
            'personal_email': '',
            'personal_company': '',
            'personal_location': '',
            'personal_role': ''
        }

        if not website_url:
            return result

        try:
            # 避免重复爬取 GitHub
            if 'github.com' in website_url:
                return result

            headers = {
                'User-Agent': USER_AGENT
            }

            resp = requests.get(website_url, headers=headers, timeout=30, verify=False)
            self.requests_made += 1

            if resp.status_code != 200:
                return result

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 1. 提取邮箱
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, resp.text)

            # 过滤邮箱
            for email in emails:
                if 'noreply' not in email and 'github' not in email and 'example' not in email:
                    result['personal_email'] = email
                    break

            # 2. 提取工作单位/机构信息
            # 查找常见的 meta 标签
            meta_keywords = ['author', 'organization', 'company', 'affiliation', 'workplace']

            for meta_name in meta_keywords:
                meta_elem = soup.find('meta', {'name': meta_name}) or soup.find('meta', {'property': meta_name})
                if meta_elem:
                    content = meta_elem.get('content', '').strip()
                    if content and len(content) < 100:
                        result['personal_company'] = content
                        break

            # 3. 从页面文本中提取机构信息
            # 常见的机构标识
            org_patterns = [
                r'(?:Ph\.?D\.?(?:\s*Student|Candidate)?\s*(?:at|@)\s+([^\n,\.]{5,50}))',
                r'(?:Graduate Student|Researcher|Professor)\s+(?:at|@)\s+([^\n,\.]{5,50}))',
                r'(?:Working|Work)\s+(?:at|@)\s+([^\n,\.]{5,50}))',
            ]

            for pattern in org_patterns:
                matches = re.finditer(pattern, resp.text, re.IGNORECASE)
                for match in matches:
                    org = match.group(1).strip()
                    if org and len(org) < 100 and 'University' in org or 'Institute' in org:
                        result['personal_company'] = org
                        break

                if result['personal_company']:
                    break

            # 4. 从常见的简历网站结构中提取
            # Google Scholar, Academic 网站
            if 'scholar.google' in website_url or 'academic' in website_url:
                # Google Scholar 通常有机构信息
                org_elem = soup.find('div', class_='gsc_prf_in')
                if org_elem:
                    result['personal_company'] = org_elem.get_text(strip=True)

            # 5. 从常见的 About/Contact 部分提取
            for section_name in ['about', 'contact', 'bio', 'profile']:
                section = soup.find('div', id=section_name) or soup.find('section', id=section_name)
                if section:
                    # 在这个section中查找邮箱（如果之前没找到）
                    if not result['personal_email']:
                        section_emails = re.findall(email_pattern, section.get_text())
                        for email in section_emails:
                            if 'noreply' not in email and 'github' not in email:
                                result['personal_email'] = email
                                break

        except Exception as e:
            print(f"    ⚠️ 个人网站解析错误: {e}")

        return result

    def enrich_candidate_contacts(self, input_csv: str, output_csv: str, scrape_websites: bool = True):
        """
        增强候选人联系信息

        Args:
            input_csv: 输入 CSV 文件（GitHub 增强版）
            output_csv: 输出 CSV 文件
            scrape_websites: 是否爬取个人网站（较慢）
        """
        print("="*80)
        print("LAMDA 候选人联系信息深度挖掘")
        print("="*80)
        print(f"\n输入文件: {input_csv}")
        print(f"输出文件: {output_csv}")
        print(f"爬取个人网站: {'是' if scrape_websites else '否'}\n")

        # 读取候选人
        candidates = []
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            candidates = list(reader)

        print(f"📊 总候选人: {len(candidates)}")

        # 筛选有 GitHub 的候选人
        with_github = [c for c in candidates if c.get('github_username') and c['github_username'] != '']
        print(f"✓ 有 GitHub: {len(with_github)}\n")

        # 处理每个候选人
        enriched = []
        stats = {
            'total': len(with_github),
            'github_enhanced': 0,
            'website_scraped': 0,
            'email_found': 0,
            'company_found': 0
        }

        for i, candidate in enumerate(with_github, 1):
            name = candidate['姓名']
            username = candidate['github_username']

            print(f"\n[{i}/{len(with_github)}] {name} (@{username})")

            # 步骤1: 爬取 GitHub 页面获取更多信息
            github_webpage_info = self.scrape_github_profile_page(username)

            # 合并邮箱信息（GitHub API 的邮箱优先）
            api_email = candidate.get('github_email', '')
            webpage_email = github_webpage_info.get('webpage_email', '')
            final_email = api_email or webpage_email

            # 合并 Twitter
            api_twitter = candidate.get('github_twitter', '')
            webpage_twitter = github_webpage_info.get('webpage_twitter', '')
            final_twitter = api_twitter or webpage_twitter

            # 合并 LinkedIn
            linkedin = github_webpage_info.get('webpage_linkedin', '')

            # 合并个人网站
            personal_website = github_webpage_info.get('webpage_website', '') or candidate.get('github_blog', '')

            # 合并公司信息
            webpage_company = github_webpage_info.get('webpage_company', '')
            api_company = candidate.get('github_company', '')
            final_company = api_company or webpage_company

            # 更新候选人的 GitHub 字段
            candidate['github_email_enhanced'] = final_email
            candidate['github_twitter_enhanced'] = final_twitter
            candidate['github_linkedin'] = linkedin
            candidate['github_website_enhanced'] = personal_website
            candidate['github_company_enhanced'] = final_company

            # 记录增强统计
            if webpage_email or webpage_twitter or linkedin:
                stats['github_enhanced'] += 1
                print(f"  ✓ GitHub 网页增强成功")

            if final_email:
                stats['email_found'] += 1
                email_source = "API" if api_email else "网页"
                print(f"  ✓ 邮箱: {final_email} (来源: {email_source})")

            # 步骤2: 爬取个人网站
            personal_info = {}

            if scrape_websites and personal_website:
                print(f"  🔍 爬取个人网站: {personal_website[:60]}...")
                personal_info = self.scrape_personal_website(personal_website)
                stats['website_scraped'] += 1

                if personal_info.get('personal_email'):
                    # 如果个人网站找到邮箱，使用个人网站的邮箱
                    candidate['final_email'] = personal_info['personal_email']
                    print(f"  ✓ 个人网站邮箱: {personal_info['personal_email']}")

                if personal_info.get('personal_company'):
                    candidate['personal_company'] = personal_info['personal_company']
                    stats['company_found'] += 1
                    print(f"  ✓ 工作单位: {personal_info['personal_company']}")
            else:
                # 没有爬取个人网站，使用 GitHub 的信息
                candidate['final_email'] = final_email
                candidate['personal_company'] = ''

            # 添加到结果
            enriched.append(candidate)

            # 礼貌延迟
            time.sleep(2)

        # 添加没有 GitHub 的候选人
        without_github = [c for c in candidates if not c.get('github_username') or c['github_username'] == '']
        for candidate in without_github:
            candidate['github_email_enhanced'] = ''
            candidate['github_twitter_enhanced'] = ''
            candidate['github_linkedin'] = ''
            candidate['github_website_enhanced'] = ''
            candidate['github_company_enhanced'] = ''
            candidate['final_email'] = candidate.get('邮箱', '')
            candidate['personal_company'] = ''
            enriched.append(candidate)

        # 写入结果
        fieldnames = list(enriched[0].keys())
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched)

        # 打印统计
        print("\n" + "="*80)
        print("联系信息挖掘统计")
        print("="*80)
        print(f"总数: {stats['total']}")
        print(f"GitHub 网页增强: {stats['github_enhanced']}")
        print(f"个人网站爬取: {stats['website_scraped']}")
        print(f"找到邮箱: {stats['email_found']} ({stats['email_found']/stats['total']*100:.1f}%)")
        print(f"找到工作单位: {stats['company_found']}")

        # 对比原有邮箱
        original_emails = sum(1 for c in candidates if c.get('邮箱') and c['邮箱'] != '')
        new_emails = sum(1 for c in enriched if c.get('final_email') and c['final_email'] != '')
        print(f"\n邮箱对比:")
        print(f"  原有邮箱: {original_emails}")
        print(f"  现在邮箱: {new_emails}")
        print(f"  新增邮箱: {new_emails - original_emails}")

        print(f"\n✓ 结果已保存到: {output_csv}\n")


def main():
    """主函数"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description='LAMDA 联系信息深度挖掘工具')
    parser.add_argument('--input', type=str, default='lamda_candidates_github_enhanced.csv',
                       help='输入 CSV 文件')
    parser.add_argument('--output', type=str, default='lamda_candidates_with_contacts.csv',
                       help='输出 CSV 文件')
    parser.add_argument('--token', type=str, default=None,
                       help='GitHub Personal Access Token')
    parser.add_argument('--no-scrape-websites', action='store_true',
                       help='不爬取个人网站（更快，但信息更少）')

    args = parser.parse_args()

    # 获取 Token
    token = args.token
    if not token:
        token = os.environ.get('GITHUB_TOKEN')

    # 创建增强器
    enricher = GitHubContactEnricher(github_token=token)

    # 执行增强
    enricher.enrich_candidate_contacts(
        args.input,
        args.output,
        scrape_websites=not args.no_scrape_websites
    )


if __name__ == '__main__':
    main()
