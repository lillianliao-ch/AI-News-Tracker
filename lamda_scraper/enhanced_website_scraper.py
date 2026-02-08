#!/usr/bin/env python3
"""
增强的个人网站联系信息挖掘工具
支持 HTTP、meta refresh 和 JavaScript 重定向
"""

import requests
import re
import csv
import time
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin
from redirect_utils import RedirectFollower


class EnhancedWebsiteScraper:
    """增强的个人网站联系信息提取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.redirect_follower = RedirectFollower(max_redirects=5)
        self.scraped_count = 0
        self.email_found = 0
        self.company_found = 0
        self.redirect_followed = 0

    def scrape_website(self, website_url: str) -> Dict:
        """
        爬取个人网站，提取联系信息（支持重定向）

        Args:
            website_url: 个人网站 URL

        Returns:
            包含邮箱、公司等信息的字典
        """
        result = {
            'website_email': '',
            'website_company': '',
            'website_position': '',
            'final_url': '',
            'redirect_count': 0,
            'redirect_types': []
        }

        if not website_url:
            return result

        # 确保URL完整
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url

        try:
            # 1. 跟随重定向
            redirect_result = self.redirect_follower.follow_redirects(website_url)
            final_url = redirect_result['final_url']
            redirect_count = redirect_result['redirect_count']
            redirect_types = redirect_result['redirect_types']

            result['final_url'] = final_url
            result['redirect_count'] = redirect_count
            result['redirect_types'] = redirect_types

            if redirect_count > 0:
                self.redirect_followed += 1
                print(f"  → 重定向 ({redirect_count}次, {', '.join(redirect_types)})")
                print(f"     {website_url[:50]}...")
                print(f"     → {final_url[:50]}...")

            # 2. 获取最终页面内容
            resp = self.session.get(final_url, timeout=30, verify=True)
            self.scraped_count += 1

            if resp.status_code != 200:
                return result

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 3. 提取邮箱
            result['website_email'] = self._extract_email(resp.text, soup)

            if result['website_email']:
                self.email_found += 1

            # 4. 提取公司信息
            result['website_company'] = self._extract_company(soup, resp.text)

            if result['website_company']:
                self.company_found += 1

        except requests.exceptions.SSLError as e:
            print(f"  ⚠️ SSL Error: {e}")

        except requests.exceptions.RequestException as e:
            print(f"  ⚠️ Request Error: {e}")

        except Exception as e:
            print(f"  ⚠️ Unexpected Error: {e}")

        return result

    def _extract_email(self, text: str, soup: BeautifulSoup) -> str:
        """提取邮箱"""
        # 1. 明文邮箱
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)

        # 过滤邮箱
        for email in emails:
            if ('noreply' not in email and
                'github' not in email and
                'example' not in email and
                'localhost' not in email and
                'test' not in email.lower() and
                'w3.org' not in email and
                '@2x' not in email):  # 过滤图片文件名
                return email

        # 2. Cloudflare 保护邮箱（需要解码）
        cloudflare_links = soup.find_all('a', href=lambda x: x and '/cdn-cgi/l/email-protection' in x)
        if cloudflare_links:
            # 可以调用 decode_cloudflare_email 函数
            pass

        return ''

    def _extract_company(self, soup: BeautifulSoup, text: str) -> str:
        """提取公司信息"""
        # 1. 从 meta 标签提取
        meta_keywords = ['author', 'organization', 'company', 'affiliation', 'workplace']

        for meta_name in meta_keywords:
            meta_elem = soup.find('meta', {'name': meta_name}) or soup.find('meta', {'property': meta_name})
            if meta_elem:
                content = meta_elem.get('content', '').strip()
                if content and len(content) < 100:
                    return content

        # 2. 从页面文本提取
        org_patterns = [
            r'(?:Ph\.?D\.?\s*(?:Student|Candidate)?\s*(?:at|@)\s+([^\n,\.]{5,80}))',
            r'(?:Graduate Student|Researcher|Professor|Faculty)\s+(?:at|@)\s+([^\n,\.]{5,80})',
        ]

        for pattern in org_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                org = match.group(1).strip()
                if org and len(org) < 100:
                    return org

        return ''


def main():
    """主函数 - 测试增强的网站爬虫"""
    print("="*80)
    print("增强的个人网站联系信息挖掘测试")
    print("="*80)
    print()

    scraper = EnhancedWebsiteScraper()

    # 测试案例
    test_cases = [
        {
            'name': '陈雄辉',
            'url': 'http://www.lamda.nju.edu.cn/chenxh/',
            'expected_email': 'xionghui.cxh@alibaba-inc.com',
            'expected_company': 'Alibaba'
        },
        {
            'name': '杨嘉祺',
            'url': 'https://academic.thyrixyang.com',
            'expected_email': 'thyrixyang@gmail.com',
            'expected_company': ''
        }
    ]

    for case in test_cases:
        print(f"测试: {case['name']}")
        print(f"URL: {case['url']}")
        print()

        result = scraper.scrape_website(case['url'])

        print(f"最终 URL: {result['final_url']}")
        print(f"重定向: {result['redirect_count']} 次 ({', '.join(result['redirect_types']) or '无'})")

        if result['website_email']:
            print(f"✓ 邮箱: {result['website_email']}")
            if case['expected_email'] and case['expected_email'] in result['website_email']:
                print(f"  ✅ 符合预期")
        else:
            print(f"✗ 未找到邮箱")

        if result['website_company']:
            print(f"✓ 公司: {result['website_company']}")
            if case['expected_company'] and case['expected_company'] in result['website_company']:
                print(f"  ✅ 符合预期")

        print()
        print("-"*80)
        print()

    # 统计
    print("="*80)
    print("统计")
    print("="*80)
    print(f"处理网站数: {scraper.scraped_count}")
    print(f"重定向跟随: {scraper.redirect_followed}")
    print(f"找到邮箱: {scraper.email_found}")
    print(f"找到公司: {scraper.company_found}")
    print()


if __name__ == '__main__':
    main()
