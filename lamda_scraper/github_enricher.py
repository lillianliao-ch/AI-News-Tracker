#!/usr/bin/env python3
"""
LAMDA 候选人 GitHub 信息深度挖掘工具
从候选人的 GitHub 链接中提取额外信息，评估技术能力
"""

import requests
import json
import csv
import time
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

# GitHub API 配置
GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "LAMDA-Talent-Scanner/1.0"

# 技术栈关键词映射
TECH_STACK_KEYWORDS = {
    'python': ['python', '.py', 'django', 'flask', 'fastapi'],
    'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
    'machine_learning': ['tensorflow', 'pytorch', 'keras', 'scikit-learn', 'ml'],
    'deep_learning': ['neural', 'deep learning', ' cnn', 'rnn', 'transformer', 'bert'],
    'computer_vision': ['opencv', 'cv2', 'detection', 'segmentation', 'vision'],
    'nlp': ['nlp', 'text', 'tokenizer', 'language model', 'gpt', 'llm'],
    'reinforcement_learning': ['reinforcement', 'rl', 'agent', 'policy', 'q-learning'],
    'data_science': ['pandas', 'numpy', 'matplotlib', 'visualization', 'analytics'],
    'web': ['html', 'css', 'frontend', 'backend', 'fullstack'],
}


class GitHubEnricher:
    """GitHub 信息增强器"""

    def __init__(self, github_token: Optional[str] = None):
        """
        初始化 GitHub API 客户端

        Args:
            github_token: GitHub Personal Access Token (可选，但强烈推荐)
        """
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

        # 请求统计
        self.requests_made = 0
        self.rate_limit_remaining = 5000

    def _make_request(self, url: str) -> Optional[Dict]:
        """
        发送 GitHub API 请求

        Args:
            url: API 端点 URL

        Returns:
            响应 JSON 或 None
        """
        try:
            response = self.session.get(url, timeout=30)
            self.requests_made += 1

            # 更新剩余配额
            self.rate_limit_remaining = int(
                response.headers.get('X-RateLimit-Remaining', 0)
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # API 限流
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = reset_time - int(time.time()) + 1
                print(f"⚠️ API 限流，需等待 {wait_time} 秒")
                time.sleep(max(wait_time, 60))
                return self._make_request(url)  # 重试
            elif response.status_code == 404:
                return None
            else:
                print(f"❌ API 错误: {response.status_code} - {url}")
                return None

        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None

    def extract_username(self, github_url: str) -> Optional[str]:
        """
        从 GitHub URL 提取用户名

        Args:
            github_url: GitHub URL

        Returns:
            GitHub 用户名或 None
        """
        if not github_url:
            return None

        # 处理各种 GitHub URL 格式
        patterns = [
            r'github\.com/([^/]+)/?$',
            r'github\.com/([^/]+)',
            r'github\.io/([^/.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, github_url)
            if match:
                username = match.group(1)
                # 排除组织/项目页面
                if username and username not in ['pages', 'about', 'repo', 'gist', 'blog']:
                    return username

        return None

    def get_user_profile(self, username: str) -> Optional[Dict]:
        """
        获取用户完整档案

        Args:
            username: GitHub 用户名

        Returns:
            用户信息字典或 None
        """
        if not username:
            return None

        print(f"  🔍 获取用户: {username}")

        # 基础用户信息
        url = f"{GITHUB_API_BASE}/users/{username}"
        profile = self._make_request(url)

        if not profile:
            return None

        # 提取关键信息
        result = {
            'username': username,
            'name': profile.get('name') or '',
            'bio': profile.get('bio') or '',
            'location': profile.get('location') or '',
            'company': profile.get('company') or '',
            'blog': profile.get('blog') or '',
            'email': profile.get('email') or '',
            'twitter': profile.get('twitter_username') or '',
            'public_repos': profile.get('public_repos', 0),
            'followers': profile.get('followers', 0),
            'following': profile.get('following', 0),
            'account_created': profile.get('created_at', ''),
            'updated_at': profile.get('updated_at', ''),
            'hireable': profile.get('hireable', False),
            'avatar_url': profile.get('avatar_url', ''),
            'html_url': profile.get('html_url', ''),
        }

        # 计算账号年限
        if result['account_created']:
            created = datetime.fromisoformat(result['account_created'].replace('Z', '+00:00'))
            years_active = (datetime.now(created.tzinfo) - created).days / 365.25
            result['years_active'] = round(years_active, 1)

        # 获取语言统计
        repos_url = f"{GITHUB_API_BASE}/users/{username}/repos?per_page=100&sort=updated"
        repos = self._make_request(repos_url)

        if repos:
            result['top_repos'] = self._analyze_repos(repos[:10])  # 分析前10个仓库
            result['language_stats'] = self._calculate_language_stats(repos)
            result['total_stars'] = sum(r.get('stargazers_count', 0) for r in repos)
            result['total_forks'] = sum(r.get('forks_count', 0) for r in repos)

        return result

    def _analyze_repos(self, repos: List[Dict]) -> List[Dict]:
        """
        分析仓库列表

        Args:
            repos: 仓库列表

        Returns:
            关键仓库信息
        """
        top_repos = []

        for repo in repos[:10]:
            repo_info = {
                'name': repo.get('full_name'),
                'description': repo.get('description', ''),
                'language': repo.get('language', ''),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'updated_at': repo.get('updated_at', ''),
                'topics': repo.get('topics', []),
                'url': repo.get('html_url', ''),
            }
            top_repos.append(repo_info)

        return top_repos

    def _calculate_language_stats(self, repos: List[Dict]) -> Dict[str, int]:
        """
        计算编程语言统计

        Args:
            repos: 仓库列表

        Returns:
            语言使用次数
        """
        languages = {}

        for repo in repos:
            lang = repo.get('language')
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        return languages

    def detect_tech_stack(self, profile: Dict) -> List[str]:
        """
        检测候选人的技术栈

        Args:
            profile: GitHub 档案

        Returns:
            技术栈列表
        """
        tech_stacks = set()

        # 从 Bio 中检测
        bio = profile.get('bio', '').lower()
        for stack, keywords in TECH_STACK_KEYWORDS.items():
            if any(kw in bio for kw in keywords):
                tech_stacks.add(stack)

        # 从仓库名和描述中检测
        for repo in profile.get('top_repos', [])[:5]:
            repo_text = f"{repo['name']} {repo.get('description', '')}".lower()
            for stack, keywords in TECH_STACK_KEYWORDS.items():
                if any(kw in repo_text for kw in keywords):
                    tech_stacks.add(stack)

        # 从编程语言统计推断
        languages = profile.get('language_stats', {})
        if languages.get('Python', 0) >= 3:
            tech_stacks.add('python')
        if languages.get('JavaScript', 0) >= 3:
            tech_stacks.add('javascript')

        return sorted(list(tech_stacks))

    def calculate_github_score(self, profile: Dict) -> Dict:
        """
        计算 GitHub 活跃度评分

        Args:
            profile: GitHub 档案

        Returns:
            评分详情
        """
        scores = {
            'activity_score': 0,      # 活跃度 (0-40)
            'influence_score': 0,      # 影响力 (0-30)
            'quality_score': 0,        # 质量分 (0-30)
            'total_score': 0,          # 总分 (0-100)
        }

        # 1. 活跃度评分 (40分)
        # 公开仓库数
        repos = profile.get('public_repos', 0)
        scores['activity_score'] += min(repos * 2, 20)

        # 账号年限
        years = profile.get('years_active', 0)
        scores['activity_score'] += min(years * 3, 10)

        # 最近更新
        if profile.get('top_repos'):
            latest_update = profile['top_repos'][0].get('updated_at', '')
            if latest_update:
                try:
                    # 处理时区
                    if latest_update.endswith('Z'):
                        latest_update = latest_update.replace('Z', '+00:00')
                    update_time = datetime.fromisoformat(latest_update)
                    if update_time.tzinfo is None:
                        update_time = update_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
                    days_since_update = (datetime.now(update_time.tzinfo) - update_time).days
                    if days_since_update <= 30:
                        scores['activity_score'] += 10
                    elif days_since_update <= 90:
                        scores['activity_score'] += 5
                except:
                    pass  # 忽略时间解析错误

        # 2. 影响力评分 (30分)
        # Followers
        followers = profile.get('followers', 0)
        scores['influence_score'] += min(followers / 10, 15)

        # Stars
        stars = profile.get('total_stars', 0)
        scores['influence_score'] += min(stars / 5, 10)

        # Forks
        forks = profile.get('total_forks', 0)
        scores['influence_score'] += min(forks / 10, 5)

        # 3. 质量分 (30分)
        # 有 Bio
        if profile.get('bio'):
            scores['quality_score'] += 5

        # 有公司信息
        if profile.get('company'):
            scores['quality_score'] += 5

        # hireable
        if profile.get('hireable'):
            scores['quality_score'] += 10

        # 有邮箱
        if profile.get('email'):
            scores['quality_score'] += 5

        # 仓库质量 (平均 stars > 10)
        if profile.get('top_repos'):
            avg_stars = sum(r['stars'] for r in profile['top_repos'][:5]) / 5
            if avg_stars >= 10:
                scores['quality_score'] += 5

        # 总分
        scores['total_score'] = (
            scores['activity_score'] +
            scores['influence_score'] +
            scores['quality_score']
        )

        return scores

    def enrich_candidates(self, input_csv: str, output_csv: str):
        """
        增强候选人 CSV 文件

        Args:
            input_csv: 输入 CSV 文件
            output_csv: 输出 CSV 文件
        """
        print("="*80)
        print("LAMDA 候选人 GitHub 信息深度挖掘")
        print("="*80)
        print(f"\n输入文件: {input_csv}")
        print(f"输出文件: {output_csv}\n")

        # 读取候选人
        candidates = []
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            candidates = list(reader)

        print(f"📊 总候选人: {len(candidates)}")

        # 筛选有 GitHub 的候选人
        with_github = [c for c in candidates if c.get('GitHub') and c['GitHub'] != '']
        print(f"✓ 有 GitHub: {len(with_github)}")
        print(f"✗ 无 GitHub: {len(candidates) - len(with_github)}\n")

        # 处理每个候选人
        enriched = []
        github_stats = {
            'total': len(with_github),
            'success': 0,
            'failed': 0,
            'high_quality': 0,  # 总分 >= 60
        }

        for i, candidate in enumerate(with_github, 1):
            name = candidate['姓名']
            github_url = candidate['GitHub']

            print(f"\n[{i}/{len(with_github)}] {name}")

            # 提取用户名
            username = self.extract_username(github_url)

            if not username:
                print(f"  ⚠️ 无法提取用户名: {github_url}")
                candidate['github_username'] = ''
                candidate['github_profile'] = '{}'
                candidate['github_score'] = 0
                enriched.append(candidate)
                github_stats['failed'] += 1
                continue

            # 获取 GitHub 信息
            profile = self.get_user_profile(username)

            if not profile:
                print(f"  ❌ 获取失败: {username}")
                candidate['github_username'] = username
                candidate['github_profile'] = '{}'
                candidate['github_score'] = 0
                enriched.append(candidate)
                github_stats['failed'] += 1
                continue

            # 计算评分
            scores = self.calculate_github_score(profile)
            tech_stack = self.detect_tech_stack(profile)

            # 保存信息
            candidate['github_username'] = username
            candidate['github_profile'] = json.dumps(profile, ensure_ascii=False)
            candidate['github_score'] = scores['total_score']
            candidate['github_activity'] = scores['activity_score']
            candidate['github_influence'] = scores['influence_score']
            candidate['github_quality'] = scores['quality_score']
            candidate['github_repos'] = profile.get('public_repos', 0)
            candidate['github_stars'] = profile.get('total_stars', 0)
            candidate['github_followers'] = profile.get('followers', 0)
            candidate['github_bio'] = profile.get('bio', '')
            candidate['github_company'] = profile.get('company', '')
            candidate['github_location'] = profile.get('location', '')
            candidate['github_tech_stack'] = '; '.join(tech_stack)
            candidate['github_languages'] = '; '.join(
                f"{k}×{v}" for k, v in profile.get('language_stats', {}).items()
            )
            candidate['github_top_repos'] = json.dumps(profile.get('top_repos', []), ensure_ascii=False)

            # 统计
            github_stats['success'] += 1
            if scores['total_score'] >= 60:
                github_stats['high_quality'] += 1

            print(f"  ✓ 总分: {scores['total_score']:.0f}/100")
            print(f"    活跃度: {scores['activity_score']:.0f}/40")
            print(f"    影响力: {scores['influence_score']:.0f}/30")
            print(f"    质量: {scores['quality_score']:.0f}/30")
            print(f"    公开仓库: {profile.get('public_repos', 0)}")
            print(f"    总 Stars: {profile.get('total_stars', 0)}")

            # 添加到结果
            enriched.append(candidate)

            # 礼貌延迟
            if i < len(with_github):
                time.sleep(1)

        # 添加没有 GitHub 的候选人
        without_github = [c for c in candidates if not c.get('GitHub') or c['GitHub'] == '']
        for candidate in without_github:
            candidate['github_username'] = ''
            candidate['github_profile'] = '{}'
            candidate['github_score'] = 0
            candidate['github_activity'] = 0
            candidate['github_influence'] = 0
            candidate['github_quality'] = 0
            candidate['github_repos'] = 0
            candidate['github_stars'] = 0
            candidate['github_followers'] = 0
            candidate['github_bio'] = ''
            candidate['github_company'] = ''
            candidate['github_location'] = ''
            candidate['github_tech_stack'] = ''
            candidate['github_languages'] = ''
            candidate['github_top_repos'] = '[]'
            enriched.append(candidate)

        # 写入结果
        fieldnames = list(enriched[0].keys())
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched)

        # 打印统计
        print("\n" + "="*80)
        print("GitHub 信息挖掘统计")
        print("="*80)
        print(f"总数: {github_stats['total']}")
        print(f"成功: {github_stats['success']}")
        print(f"失败: {github_stats['failed']}")
        print(f"高质量 (≥60分): {github_stats['high_quality']}")
        print(f"API 请求次数: {self.requests_made}")
        print(f"剩余配额: {self.rate_limit_remaining}")

        # Top 10 GitHub 用户
        print("\n🏆 Top 10 GitHub 活跃用户:")
        top_github = sorted(enriched, key=lambda x: x.get('github_score', 0), reverse=True)[:10]
        for i, c in enumerate(top_github, 1):
            if c['github_score'] > 0:
                print(f"{i:2}. {c['姓名']:10s} | {c['github_username']:20s} | "
                      f"Score:{c['github_score']:3.0f} | "
                      f"Repos:{c['github_repos']:2} | "
                      f"Stars:{c['github_stars']:3} | "
                      f"Tech:{c['github_tech_stack']}")

        print(f"\n✓ 结果已保存到: {output_csv}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='LAMDA GitHub 信息挖掘工具')
    parser.add_argument('--input', type=str, default='lamda_candidates_full.csv',
                       help='输入 CSV 文件')
    parser.add_argument('--output', type=str, default='lamda_candidates_github_enhanced.csv',
                       help='输出 CSV 文件')
    parser.add_argument('--token', type=str, default=None,
                       help='GitHub Personal Access Token (推荐设置 GITHUB_TOKEN 环境变量)')

    args = parser.parse_args()

    # 获取 Token
    token = args.token
    if not token:
        import os
        token = os.environ.get('GITHUB_TOKEN')

    if not token:
        print("⚠️ 警告: 未提供 GitHub Token")
        print("   请求限制: 60次/小时 (未认证)")
        print("   推荐设置: export GITHUB_TOKEN=your_token_here")
        print()
        print("继续执行（使用未认证模式）")

    # 创建增强器
    enricher = GitHubEnricher(github_token=token)

    # 执行增强
    enricher.enrich_candidates(args.input, args.output)


if __name__ == '__main__':
    main()
