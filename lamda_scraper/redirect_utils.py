#!/usr/bin/env python3
"""
增强的重定向处理工具
支持 HTTP 重定向、meta refresh 和 JavaScript 重定向
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from urllib.parse import urljoin


class RedirectFollower:
    """增强的重定向跟随器"""

    def __init__(self, max_redirects=5, timeout=30):
        """
        初始化重定向跟随器

        Args:
            max_redirects: 最大重定向次数
            timeout: 请求超时时间
        """
        self.max_redirects = max_redirects
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def follow_redirects(self, url: str) -> Dict:
        """
        跟随所有类型的重定向

        Args:
            url: 起始 URL

        Returns:
            {
                'final_url': 最终 URL,
                'redirect_chain': 重定向链,
                'redirect_count': 重定向次数,
                'redirect_types': 重定向类型列表
            }
        """
        result = {
            'final_url': url,
            'redirect_chain': [],
            'redirect_count': 0,
            'redirect_types': []
        }

        current_url = url

        for i in range(self.max_redirects):
            # 1. HTTP 重定向
            try:
                resp = self.session.get(
                    current_url,
                    timeout=self.timeout,
                    verify=True,
                    allow_redirects=True
                )

                # 检查 HTTP 重定向
                if resp.url != current_url:
                    redirect_type = 'HTTP'
                    result['redirect_chain'].append({
                        'from': current_url,
                        'to': resp.url,
                        'type': redirect_type,
                        'status_code': resp.status_code
                    })
                    result['redirect_types'].append(redirect_type)
                    current_url = resp.url
                    result['final_url'] = current_url
                    result['redirect_count'] += 1
                    continue

                # 2. 检查 meta refresh
                meta_redirect = self._extract_meta_refresh(resp.text, current_url)
                if meta_redirect:
                    result['redirect_chain'].append({
                        'from': current_url,
                        'to': meta_redirect,
                        'type': 'meta-refresh',
                        'status_code': resp.status_code
                    })
                    result['redirect_types'].append('meta-refresh')
                    current_url = meta_redirect
                    result['final_url'] = current_url
                    result['redirect_count'] += 1
                    continue

                # 3. 检查 JavaScript 重定向
                js_redirect = self._extract_js_redirect(resp.text, current_url)
                if js_redirect:
                    result['redirect_chain'].append({
                        'from': current_url,
                        'to': js_redirect,
                        'type': 'javascript',
                        'status_code': resp.status_code
                    })
                    result['redirect_types'].append('javascript')
                    current_url = js_redirect
                    result['final_url'] = current_url
                    result['redirect_count'] += 1
                    continue

                # 没有更多重定向
                break

            except Exception as e:
                # 错误，停止跟随
                result['error'] = str(e)
                break

        return result

    def _extract_meta_refresh(self, html: str, base_url: str) -> Optional[str]:
        """
        提取 meta refresh 重定向

        Args:
            html: HTML 内容
            base_url: 基础 URL

        Returns:
            重定向 URL 或 None
        """
        soup = BeautifulSoup(html, 'html.parser')
        meta_refresh = soup.find('meta', {'http-equiv': 'refresh'})

        if meta_refresh:
            content = meta_refresh.get('content', '')
            # 格式: "0;url=https://example.com" 或 "5;url=https://example.com"
            match = re.search(r'url\s*=\s*([^\s]+)', content, re.IGNORECASE)
            if match:
                redirect_url = match.group(1)
                # 处理相对 URL
                return urljoin(base_url, redirect_url)

        return None

    def _extract_js_redirect(self, html: str, base_url: str) -> Optional[str]:
        """
        提取 JavaScript 重定向

        Args:
            html: HTML 内容
            base_url: 基础 URL

        Returns:
            重定向 URL 或 None
        """
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')

        for script in scripts:
            if not script.string:
                continue

            code = script.string

            # 匹配常见的 JavaScript 重定向模式
            patterns = [
                r'window\.location\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                r'location\.href\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)',
            ]

            for pattern in patterns:
                match = re.search(pattern, code)
                if match:
                    redirect_url = match.group(1)
                    # 处理相对 URL
                    return urljoin(base_url, redirect_url)

        return None


def test_redirect_follower():
    """测试重定向跟随器"""
    print("="*80)
    print("增强重定向跟随器测试")
    print("="*80)
    print()

    follower = RedirectFollower(max_redirects=5)

    test_cases = [
        {
            'name': '陈雄辉 - LAMDA 主页 (meta refresh)',
            'url': 'http://www.lamda.nju.edu.cn/chenxh/',
            'expected': 'https://xionghuichen.github.io/'
        },
        {
            'name': 'HTTP 重定向',
            'url': 'http://github.com/',
            'expected': 'https://github.com/'
        },
        {
            'name': '无重定向',
            'url': 'https://github.com/xionghuichen',
            'expected': 'https://github.com/xionghuichen'
        }
    ]

    for case in test_cases:
        print(f"测试: {case['name']}")
        print(f"URL: {case['url']}")
        print()

        result = follower.follow_redirects(case['url'])

        print(f"  最终 URL: {result['final_url']}")
        print(f"  重定向次数: {result['redirect_count']}")
        print(f"  重定向类型: {', '.join(result['redirect_types']) or '无'}")

        if result['redirect_chain']:
            print(f"  重定向链:")
            for i, redirect in enumerate(result['redirect_chain'], 1):
                print(f"    {i}. {redirect['type']}: {redirect['from'][:60]}")
                print(f"       → {redirect['to'][:60]}")

        # 检查是否符合预期
        if result['final_url'] == case['expected']:
            print(f"  状态: ✅ 符合预期")
        elif case['expected'] in result['final_url']:
            print(f"  状态: ✅ 部分符合预期")
        else:
            print(f"  状态: ⚠️ 不符合预期")
            print(f"  预期: {case['expected']}")

        print()
        print("-"*80)
        print()


if __name__ == '__main__':
    test_redirect_follower()
