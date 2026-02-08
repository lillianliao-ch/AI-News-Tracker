#!/usr/bin/env python3
"""
GitHub URL 标准化和修复工具

解决以下问题:
1. 仓库链接而非用户主页
2. 文件链接
3. 协议错误 (http://)
4. 非 GitHub 链接
"""

import re
import csv
from typing import Optional, Tuple


class GitHubURLFixer:
    """GitHub URL 标准化工具"""

    # GitHub URL 模式
    PATTERNS = {
        'user_profile': r'github\.com/([^/]+)/?$',
        'repo': r'github\.com/([^/]+)/([^/]+)',
        'repo_file': r'github\.com/([^/]+)/([^/]+)/blob/.*',
        'repo_tree': r'github\.com/([^/]+)/([^/]+)/tree/.*',
        'repo_issues': r'github\.com/([^/]+)/([^/]+)/issues',
        'gist': r'gist\.github\.com/([^/]+)/',
    }

    # 已知组织账号 (非个人)
    ORGANIZATIONS = {
        'lamda-bbo', 'LAMDA-Tabular', 'SkyworkAI',
        'FLAIR-THU', 'tencentopen'
    }

    def __init__(self):
        """初始化"""
        self.stats = {
            'total': 0,
            'already_valid': 0,
            'fixed': 0,
            'cannot_fix': 0,
            'not_github': 0
        }

    def fix_url(self, url: str) -> Tuple[str, str]:
        """
        修复 GitHub URL

        Args:
            url: 原始 URL

        Returns:
            (fixed_url, status_message)
        """
        self.stats['total'] += 1

        if not url or not url.strip():
            return ('', '空 URL')

        url = url.strip()

        # 1. 检查是否是 GitHub URL
        if 'github.com' not in url and 'gist.github.com' not in url:
            self.stats['not_github'] += 1
            return (url, '非 GitHub URL')

        # 2. 修复协议
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        elif not url.startswith('https://'):
            url = 'https://' + url

        # 3. 移除尾部斜号
        url = url.rstrip('/')

        # 4. 检查是否已经是用户主页
        user_match = re.search(self.PATTERNS['user_profile'], url)
        if user_match:
            self.stats['already_valid'] += 1
            return (url, '已是用户主页')

        # 5. 尝试从各种格式中提取用户名
        for pattern_name, pattern in self.PATTERNS.items():
            if pattern_name == 'user_profile':
                continue

            match = re.search(pattern, url)
            if match:
                username = match.group(1)

                # 跳过组织账号 (保留原 URL)
                if username in self.ORGANIZATIONS or username.lower().startswith('lamda'):
                    self.stats['cannot_fix'] += 1
                    return (url, f'组织账号: {username}')

                # 构建用户主页 URL
                fixed_url = f'https://github.com/{username}'
                self.stats['fixed'] += 1
                return (fixed_url, f'从 {pattern_name} 提取')

        # 6. 无法处理的格式
        self.stats['cannot_fix'] += 1
        return (url, '无法识别格式')

    def batch_fix_urls(self, candidates: list) -> list:
        """
        批量修复候选人 GitHub URL

        Args:
            candidates: 候选人列表

        Returns:
            更新后的候选人列表
        """
        for candidate in candidates:
            if not candidate.get('GitHub'):
                continue

            original_url = candidate['GitHub']
            fixed_url, message = self.fix_url(original_url)

            # 添加修复信息字段
            candidate['github_url_original'] = original_url
            candidate['github_url_fixed'] = fixed_url
            candidate['github_url_fix_status'] = message

            # 更新 GitHub 字段
            if fixed_url and fixed_url != original_url:
                candidate['GitHub'] = fixed_url

        return candidates

    def print_stats(self):
        """打印统计信息"""
        print("=" * 80)
        print("GitHub URL 修复统计")
        print("=" * 80)
        print(f"总数: {self.stats['total']}")
        print(f"✓ 已是用户主页: {self.stats['already_valid']}")
        print(f"✓ 已修复: {self.stats['fixed']}")
        print(f"✗ 无法修复: {self.stats['cannot_fix']}")
        print(f"✗ 非 GitHub URL: {self.stats['not_github']}")
        print()


def main():
    """主函数"""
    print("=" * 80)
    print("GitHub URL 标准化和修复")
    print("=" * 80)
    print()

    # 读取候选人数据
    input_csv = 'lamda_candidates_with_emails.csv'
    output_csv = 'lamda_candidates_urls_fixed.csv'

    candidates = []
    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        candidates = list(reader)

    print(f"📊 总候选人: {len(candidates)}")

    # 筛选有 GitHub 的候选人
    with_github = [c for c in candidates if c.get('GitHub') and c['GitHub'].strip()]
    print(f"✓ 有 GitHub: {len(with_github)}")
    print()

    # 创建修复器
    fixer = GitHubURLFixer()

    # 展示修复示例
    print("修复示例:")
    print("-" * 80)

    examples = [
        'https://github.com/ThyrixYang',
        'https://github.com/yixiaoshenghua/Multi-Temporal-Training-Based-Remote-Sensing-Images-Information-Extraction',
        'http://github.com/njuyxw',
        'https://github.com/Hao-Yuan-He/resume_typst/blob/main/main.pdf',
        'https://github.com/lamda-bbo/NSS/blob/main/CITATION.bib',
    ]

    for url in examples:
        fixed_url, message = fixer.fix_url(url)
        print(f"原始: {url}")
        print(f"修复: {fixed_url}")
        print(f"状态: {message}")
        print()

    # 批量修复
    print("=" * 80)
    print("开始批量修复...")
    print("=" * 80)
    print()

    candidates = fixer.batch_fix_urls(candidates)

    # 显示修复统计
    fixer.print_stats()

    # 显示已修复的 URL
    fixed_candidates = [c for c in candidates
                        if c.get('github_url_fix_status') and
                        c['github_url_fix_status'] not in ['已是用户主页', '空 URL', '非 GitHub URL']]

    print(f"🔧 已修复的 URL ({len(fixed_candidates)} 个):")
    print("-" * 80)

    for c in fixed_candidates[:20]:  # 显示前20个
        print(f"{c['姓名']:15s}")
        print(f"  原始: {c['github_url_original']}")
        print(f"  修复: {c['github_url_fixed']}")
        print(f"  状态: {c['github_url_fix_status']}")
        print()

    if len(fixed_candidates) > 20:
        print(f"... 还有 {len(fixed_candidates) - 20} 个")
        print()

    # 保存结果
    print("=" * 80)
    print("保存结果...")
    print()

    fieldnames = list(candidates[0].keys())
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)

    print(f"✓ 已保存到: {output_csv}")
    print()
    print("=" * 80)
    print("下一步:")
    print("  1. 检查修复后的 URL 是否正确")
    print("  2. 使用修复后的 URL 重新提取邮箱")
    print("  python3 batch_extract_emails.py lamda_candidates_urls_fixed.csv")
    print("=" * 80)


if __name__ == '__main__':
    main()
