#!/usr/bin/env python3
"""
GitHub 邮箱深度挖掘工具
从 GitHub 用户的个人网站、commits、README 等多处提取邮箱
"""

import requests
import re
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin


class GitHubEmailExtractor:
    """GitHub 邮箱提取器"""

    def __init__(self, github_token: Optional[str] = None):
        """
        初始化

        Args:
            github_token: GitHub Personal Access Token (可选)
        """
        self.token = github_token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        if github_token:
            self.api_session = requests.Session()
            self.api_session.headers.update({
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        else:
            self.api_session = self.session

    def extract_all_emails(self, github_url: str, username: str = None) -> Dict[str, List[str]]:
        """
        从 GitHub 用户提取所有可能的邮箱

        Args:
            github_url: GitHub URL
            username: GitHub 用户名 (可选)

        Returns:
            邮箱字典: {
                'api': [],           # 从 API 直接获取
                'website': [],       # 从个人网站提取
                'commits': [],       # 从 commits 提取
                'readme': [],        # 从 README 提取
                'all': []            # 所有邮箱（去重）
            }
        """
        emails = {
            'api': [],
            'website': [],
            'commits': [],
            'readme': [],
            'all': []
        }

        # 提取用户名
        if not username:
            username = self._extract_username_from_url(github_url)

        if not username:
            return emails

        print(f"  📧 为 {username} 提取邮箱...")

        # 1. 从 GitHub API 获取
        api_email = self._get_email_from_api(username)
        if api_email:
            emails['api'].append(api_email)

        # 2. 获取用户 profile
        profile = self._get_user_profile(username)
        if profile:
            # 3. 从个人网站提取
            blog_url = profile.get('blog')
            if blog_url:
                website_emails = self._extract_emails_from_website(blog_url)
                emails['website'].extend(website_emails)

            # 4. 从 commits 提取
            commit_emails = self._get_emails_from_commits(username)
            emails['commits'].extend(commit_emails)

            # 5. 从 README 提取
            readme_emails = self._get_emails_from_readme(username)
            emails['readme'].extend(readme_emails)

        # 去重合并
        all_emails = []
        for source in ['api', 'website', 'commits', 'readme']:
            for email in emails[source]:
                if email and email not in all_emails:
                    all_emails.append(email)

        emails['all'] = all_emails

        # 打印结果
        if all_emails:
            print(f"  ✓ 找到 {len(all_emails)} 个邮箱:")
            for email in all_emails:
                source = self._get_email_source(email, emails)
                print(f"    - {email} (来源: {source})")
        else:
            print(f"  ✗ 未找到邮箱")

        return emails

    def _extract_username_from_url(self, github_url: str) -> Optional[str]:
        """从 URL 提取用户名"""
        if not github_url:
            return None

        match = re.search(r'github\.com/([^/]+)', github_url)
        if match:
            return match.group(1)
        return None

    def _get_email_from_api(self, username: str) -> Optional[str]:
        """从 GitHub API 获取邮箱"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = self.api_session.get(url, timeout=10)

            if response.status_code == 200:
                profile = response.json()
                email = profile.get('email')
                if email:
                    print(f"    API 直接返回: {email}")
                    return email
        except Exception as e:
            print(f"    API 请求失败: {e}")

        return None

    def _get_user_profile(self, username: str) -> Optional[Dict]:
        """获取用户完整 profile"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = self.api_session.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"    获取 profile 失败: {e}")

        return None

    def _extract_emails_from_website(self, website_url: str) -> List[str]:
        """
        从个人网站提取邮箱

        Args:
            website_url: 网站 URL

        Returns:
            邮箱列表
        """
        emails = []

        try:
            print(f"    抓取网站: {website_url}")

            # 请求网站
            response = self.session.get(website_url, timeout=15, verify=True)
            response.raise_for_status()

            # 1. 直接提取邮箱
            found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                               response.text)

            # 2. 提取 Cloudflare 邮件保护
            cloudflare_emails = self._decode_cloudflare_emails(response.text)
            found.extend(cloudflare_emails)

            # 3. 提取 mailto: 链接
            mailto_emails = re.findall(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                                      response.text)
            found.extend(mailto_emails)

            # 过滤常见假阳性
            fake_emails = ['example@', 'test@', 'your@', 'username@', 'email@',
                          'localhost', 'example.com', 'test.com']
            found = [e for e in found if not any(fake in e for fake in fake_emails)]

            # 去重
            found = list(set(found))

            if found:
                print(f"    网站找到 {len(found)} 个邮箱: {found}")
                emails.extend(found)

        except Exception as e:
            print(f"    网站抓取失败: {e}")

        return emails

    def _decode_cloudflare_emails(self, html: str) -> List[str]:
        """
        解码 Cloudflare 邮件保护的邮箱

        Cloudflare 邮件保护格式: /cdn-cgi/l/email-protection#hex_string
        解码算法: https://usamaejaz.com/cloudflare-email-decoding/

        Args:
            html: HTML 内容

        Returns:
            解码后的邮箱列表
        """
        emails = []

        # 查找所有 Cloudflare 邮件保护链接
        pattern = r'/cdn-cgi/l/email-protection#([a-zA-Z0-9]+)'
        matches = re.findall(pattern, html)

        for encoded in matches:
            try:
                email = self._decode_cloudflare_email(encoded)
                if email:
                    emails.append(email)
            except Exception:
                continue

        return emails

    def _decode_cloudflare_email(self, encoded: str) -> Optional[str]:
        """
        解码单个 Cloudflare 邮件

        Cloudflare 使用简单的 XOR 算法:
        1. 将 hex 字符串转换为字节数组
        2. 第一个字节是 key (r)
        3. 对每个后续字节进行 XOR: byte ^ r

        Args:
            encoded: 编码的 hex 字符串

        Returns:
            解码后的邮箱
        """
        try:
            # 将 hex 转换为字节
            data = bytes.fromhex(encoded)

            if len(data) < 2:
                return None

            # 第一个字节是 key
            key = data[0]

            # 简单 XOR 解密 (key 直接对每个字节 XOR)
            decoded = ''.join(chr(b ^ key) for b in data[1:])

            # 验证是否是有效的邮箱
            if '@' in decoded and '.' in decoded.split('@')[1]:
                return decoded

            # 如果简单 XOR 不行，尝试标准的 >>2 算法
            decoded_alt = ''.join(chr(b ^ (key >> 2)) for b in data[1:])
            if '@' in decoded_alt and '.' in decoded_alt.split('@')[1]:
                return decoded_alt

        except Exception as e:
            pass  # 静默失败

        return None

    def _get_emails_from_commits(self, username: str) -> List[str]:
        """
        从用户的公开 commits 提取邮箱

        Args:
            username: GitHub 用户名

        Returns:
            邮箱列表
        """
        emails = []

        try:
            # 获取最近的公开事件
            url = f"https://api.github.com/users/{username}/events/public?per_page=30"
            response = self.api_session.get(url, timeout=10)

            if response.status_code == 200:
                events = response.json()

                for event in events:
                    if event.get('payload'):
                        payload = event['payload']

                        # 从 PushEvent 提取
                        if 'commits' in payload:
                            for commit in payload['commits']:
                                if 'author' in commit:
                                    author_email = commit['author'].get('email')
                                    if author_email and '@' in author_email:
                                        emails.append(author_email)

                        # 从其他事件类型提取
                        if 'commits' in event.get('payload', {}):
                            for commit in event['payload']['commits']:
                                if 'author' in commit:
                                    commit_email = commit['author'].get('email')
                                    if commit_email and '@' in commit_email:
                                        emails.append(commit_email)

                    # 限制数量
                    if len(emails) >= 5:
                        break

                if emails:
                    print(f"    Commits 找到 {len(set(emails))} 个邮箱")

        except Exception as e:
            print(f"    Commits 提取失败: {e}")

        return list(set(emails))

    def _get_emails_from_readme(self, username: str) -> List[str]:
        """
        从用户仓库的 README 提取邮箱

        Args:
            username: GitHub 用户名

        Returns:
            邮箱列表
        """
        emails = []

        try:
            # 获取用户的仓库
            url = f"https://api.github.com/users/{username}/repos?per_page=10&sort=updated"
            response = self.api_session.get(url, timeout=10)

            if response.status_code == 200:
                repos = response.json()

                for repo in repos[:5]:  # 只检查前5个
                    repo_name = repo['full_name']
                    print(f"    检查 README: {repo_name}")

                    # 尝试获取 README
                    readme_url = f"https://api.github.com/repos/{repo_name}/readme"
                    readme_response = self.api_session.get(readme_url, timeout=10)

                    if readme_response.status_code == 200:
                        readme_data = readme_response.json()

                        # README 内容是 base64 编码的
                        import base64
                        content = base64.b64decode(readme_data['content']).decode('utf-8')

                        # 提取邮箱
                        found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                                           content)

                        if found:
                            print(f"    README 找到 {len(found)} 个邮箱")
                            emails.extend(found)

                    time.sleep(0.5)  # 礼貌延迟

        except Exception as e:
            print(f"    README 提取失败: {e}")

        return list(set(emails))

    def _get_email_source(self, email: str, emails: Dict) -> str:
        """获取邮箱的来源"""
        sources = []
        if email in emails['api']:
            sources.append('API')
        if email in emails['website']:
            sources.append('网站')
        if email in emails['commits']:
            sources.append('Commits')
        if email in emails['readme']:
            sources.append('README')
        return '+'.join(sources)


def main():
    """测试主函数"""
    import os

    # 获取 token
    token = os.environ.get('GITHUB_TOKEN')

    # 创建提取器
    extractor = GitHubEmailExtractor(github_token=token)

    # 测试案例
    test_cases = [
        'https://github.com/ThyrixYang',  # 杨嘉祺
    ]

    for github_url in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {github_url}")
        print('='*60)

        emails = extractor.extract_all_emails(github_url)

        print(f"\n总结:")
        print(f"  总邮箱数: {len(emails['all'])}")
        print(f"  来源分布:")
        print(f"    API: {len(emails['api'])}")
        print(f"    网站: {len(emails['website'])}")
        print(f"    Commits: {len(emails['commits'])}")
        print(f"    README: {len(emails['readme'])}")


if __name__ == '__main__':
    main()
