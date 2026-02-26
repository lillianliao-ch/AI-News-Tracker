#!/usr/bin/env python3
"""
GitHub 候选人信息提取工具
基于 MediaCrawler 设计理念，简化版实现
"""

import requests
import pandas as pd
import time
from typing import List, Dict
import json

class GitHubHunter:
    """GitHub 候选人挖掘器 - MVP 版本"""

    def __init__(self, token: str = None):
        """
        初始化
        :param token: GitHub Personal Access Token (可选，提升速率限制)
        """
        self.api_base = "https://api.github.com"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"

    def extract_username(self, url: str) -> str:
        """从 GitHub URL 提取 username"""
        if not url:
            return None
        # 支持多种 URL 格式
        # https://github.com/username
        # https://github.com/username/repo
        # github.com/username
        parts = url.strip().strip('/').split('/')
        if 'github.com' in parts:
            idx = parts.index('github.com')
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return None

    def get_user_profile(self, username: str) -> Dict:
        """
        获取用户基本信息
        :param username: GitHub username
        :return: 用户信息字典
        """
        url = f"{self.api_base}/users/{username}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            return {
                'github_url': f"https://github.com/{username}",
                'username': username,
                'name': data.get('name'),
                'email': data.get('email'),  # 主邮箱
                'bio': data.get('bio'),
                'location': data.get('location'),
                'company': data.get('company'),
                'blog': data.get('blog'),
                'public_repos': data.get('public_repos', 0),
                'followers': data.get('followers', 0),
                'following': data.get('following', 0),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
                'hireable': data.get('hireable', False),
            }
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取 {username} 失败: {e}")
            return None

    def get_user_repos(self, username: str, limit: int = 10) -> List[Dict]:
        """
        获取用户的公开仓库（按 star 数排序）
        :param username: GitHub username
        :param limit: 返回数量限制
        :return: 仓库列表
        """
        url = f"{self.api_base}/users/{username}/repos"
        params = {
            'sort': 'updated',
            'direction': 'desc',
            'per_page': min(limit, 100)
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            repos = response.json()

            return [{
                'repo_name': repo.get('name'),
                'full_name': repo.get('full_name'),
                'description': repo.get('description'),
                'language': repo.get('language'),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'is_fork': repo.get('fork', False),
                'created_at': repo.get('created_at'),
                'updated_at': repo.get('updated_at'),
                'url': repo.get('html_url'),
            } for repo in repos[:limit]]
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取 {username} 仓库失败: {e}")
            return []

    def get_user_languages(self, repos: List[Dict]) -> Dict[str, int]:
        """
        统计用户的主要编程语言
        :param repos: 仓库列表
        :return: 语言统计字典
        """
        languages = {}
        for repo in repos:
            lang = repo.get('language')
            if lang and not repo.get('is_fork'):
                languages[lang] = languages.get(lang, 0) + 1
        return dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))

    def get_user_emails(self, username: str) -> List[str]:
        """
        尝试从多个来源获取用户邮箱
        :param username: GitHub username
        :return: 邮箱列表（去重）
        """
        emails = set()

        # 1. 主邮箱（如果公开）
        profile = self.get_user_profile(username)
        if profile and profile.get('email'):
            emails.add(profile['email'])

        # 2. 从最近的 commits 提取邮箱
        try:
            url = f"{self.api_base}/users/{username}/events/public"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            events = response.json()

            for event in events[:20]:  # 只看最近20个事件
                if event.get('type') == 'PushEvent':
                    for commit in event.get('payload', {}).get('commits', []):
                        email = commit.get('author', {}).get('email')
                        if email and '@' in email:
                            emails.add(email)
        except:
            pass

        return list(emails) if emails else []

    def analyze_candidate(self, url: str) -> Dict:
        """
        完整分析一个候选人
        :param url: GitHub URL
        :return: 完整的候选人信息
        """
        username = self.extract_username(url)
        if not username:
            return None

        print(f"🔍 分析候选人: {username}")

        # 获取基本信息
        profile = self.get_user_profile(username)
        if not profile:
            return None

        # 获取仓库信息
        repos = self.get_user_repos(username, limit=20)

        # 统计语言
        languages = self.get_user_languages(repos)

        # 获取邮箱
        emails = self.get_user_emails(username)

        # 组合结果
        result = {
            **profile,
            'emails': ', '.join(emails) if emails else '',
            'primary_languages': ', '.join(list(languages.keys())[:5]),
            'language_count': len(languages),
            'top_repos': [
                f"{repo['repo_name']} ({repo['stars']}★)" for repo in repos[:5]
            ],
            'total_stars': sum(repo['stars'] for repo in repos),
            'original_repos': sum(1 for repo in repos if not repo['is_fork']),
            'fork_repos': sum(1 for repo in repos if repo['is_fork']),
        }

        # 移除不需要的字段
        result.pop('blog', None)

        return result

    def batch_analyze(self, urls: List[str], delay: float = 1.0) -> List[Dict]:
        """
        批量分析候选人
        :param urls: GitHub URL 列表
        :param delay: 请求间隔（秒）
        :return: 候选人信息列表
        """
        results = []

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 处理: {url}")

            candidate = self.analyze_candidate(url)
            if candidate:
                results.append(candidate)
                print(f"✅ 成功: {candidate['username']} - {candidate['name']}")
            else:
                print(f"❌ 失败: {url}")

            # 速率限制
            if i < len(urls):
                time.sleep(delay)

        return results

    def save_to_excel(self, results: List[Dict], filename: str = 'github_candidates.xlsx'):
        """
        保存到 Excel
        :param results: 候选人列表
        :param filename: 输出文件名
        """
        df = pd.DataFrame(results)

        # 调整列顺序
        columns_order = [
            'github_url', 'username', 'name', 'emails', 'company', 'location',
            'bio', 'primary_languages', 'total_stars', 'public_repos',
            'original_repos', 'fork_repos', 'followers', 'created_at'
        ]

        # 只保留存在的列
        columns = [col for col in columns_order if col in df.columns]
        df = df[columns]

        # 保存
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✅ 已保存到: {filename}")
        print(f"📊 总计: {len(results)} 个候选人")

    def save_to_json(self, results: List[Dict], filename: str = 'github_candidates.json'):
        """
        保存到 JSON
        :param results: 候选人列表
        :param filename: 输出文件名
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 已保存到: {filename}")


# ===== 使用示例 =====
if __name__ == "__main__":
    # 初始化（建议添加 GitHub Token 以提升速率限制）
    hunter = GitHubHunter(token=None)  # 或 hunter = GitHubHunter(token="your_token_here")

    # 方式 1: 从 Excel 读取
    # df = pd.read_excel('github_urls.xlsx')
    # urls = df['github_url'].tolist()

    # 方式 2: 直接提供列表
    urls = [
        'https://github.com/torvalds',
        'https://github.com/NanmiCoder',
        'https://github.com/python/cpython',  # 仓库会自动提取 owner
    ]

    # 批量分析
    results = hunter.batch_analyze(urls, delay=1)

    # 保存结果
    hunter.save_to_excel(results)
    hunter.save_to_json(results)

    print("\n✨ 完成！")
