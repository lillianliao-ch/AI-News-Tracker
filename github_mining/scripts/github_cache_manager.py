#!/usr/bin/env python3
"""
GitHub 爬虫缓存管理器

用于避免在一定时间内重复爬取已存储的用户数据

功能：
1. 检查用户是否在缓存期内（基于 created_at）
2. 从数据库读取缓存的用户数据
3. 记录爬取统计和缓存命中情况

Usage:
    from github_cache_manager import GitHubCacheManager

    cache = GitHubCacheManager(cache_days=30)

    # 检查是否需要爬取
    username = "torvalds"
    if cache.is_cached(username):
        data = cache.get_cached_data(username)
        print(f"从缓存读取: {data}")
    else:
        # 执行爬取...
        # 爬取完成后更新缓存
        cache.mark_as_crawled(username, scraped_data)
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json

# 添加 headhunter 目录到路径
headhunter_dir = Path(__file__).parent.parent.parent / "personal-ai-headhunter"
sys.path.insert(0, str(headhunter_dir))

try:
    from database import SessionLocal, Candidate
    from sqlalchemy import or_
except ImportError:
    print("❌ 无法导入数据库模块")
    Candidate = None
    SessionLocal = None


class GitHubCacheManager:
    """GitHub 爬虫缓存管理器"""

    def __init__(self, cache_days: int = 30, verbose: bool = True):
        """
        Args:
            cache_days: 缓存天数（默认30天）
            verbose: 是否打印详细日志
        """
        self.cache_days = cache_days
        self.verbose = verbose
        self.stats = {
            "cache_hits": 0,        # 缓存命中
            "cache_misses": 0,      # 缓存未命中
            "skipped_users": [],    # 跳过的用户列表
            "crawled_users": [],    # 爬取的用户列表
        }

        if Candidate is None:
            print("⚠️  警告: 数据库模块未加载，缓存功能将被禁用")
            self.enabled = False
        else:
            self.enabled = True

    def _log(self, message: str):
        """打印日志"""
        if self.verbose:
            print(message)

    def _get_cutoff_date(self) -> datetime:
        """获取缓存截止日期"""
        return datetime.now() - timedelta(days=self.cache_days)

    def _find_candidate_by_username(self, session, username: str) -> Optional[Candidate]:
        """通过 username 查找候选人（支持多种 GitHub URL 格式）"""
        if not session:
            return None

        # 构造可能的 GitHub URL 格式
        possible_urls = [
            f"https://github.com/{username}",
            f"https://github.com/{username}/",
            f"http://github.com/{username}",
            f"http://github.com/{username}/",
        ]

        # 尝试精确匹配 github_url
        candidate = session.query(Candidate).filter(
            Candidate.github_url.in_(possible_urls)
        ).first()

        # 如果没找到，尝试模糊匹配（处理末尾斜杠等问题）
        if not candidate:
            candidate = session.query(Candidate).filter(
                Candidate.github_url.isnot(None),
                or_(
                    Candidate.github_url.contains(f"github.com/{username}"),
                    Candidate.github_url.contains(f"github.com/{username}/"),
                )
            ).first()

        return candidate

    def is_cached(self, username: str) -> bool:
        """
        检查用户是否在缓存期内

        Args:
            username: GitHub 用户名

        Returns:
            True 如果在缓存期内（不需要重新爬取）
            False 如果不在缓存期内或不存在（需要爬取）
        """
        if not self.enabled:
            self.stats["cache_misses"] += 1
            return False

        session = SessionLocal()
        try:
            candidate = self._find_candidate_by_username(session, username)

            if not candidate:
                self.stats["cache_misses"] += 1
                self._log(f"🔍 缓存未命中: @{username} (数据库中不存在)")
                return False

            # 检查 created_at 是否在缓存期内
            if not candidate.created_at:
                self.stats["cache_misses"] += 1
                self._log(f"🔍 缓存未命中: @{username} (没有 created_at)")
                return False

            cutoff_date = self._get_cutoff_date()
            if candidate.created_at >= cutoff_date:
                # 计算剩余缓存天数
                remaining_days = (candidate.created_at + timedelta(days=self.cache_days) - datetime.now()).days
                self.stats["cache_hits"] += 1
                self.stats["skipped_users"].append(username)
                self._log(f"✅ 缓存命中: @{username} (创建于 {candidate.created_at.strftime('%Y-%m-%d')}, 剩余 {remaining_days} 天)")
                return True
            else:
                # 数据过期
                days_old = (datetime.now() - candidate.created_at).days
                self.stats["cache_misses"] += 1
                self._log(f"⏰ 缓存过期: @{username} (创建于 {candidate.created_at.strftime('%Y-%m-%d')}, 已过 {days_old} 天)")
                return False

        finally:
            session.close()

    def get_cached_data(self, username: str) -> Optional[Dict]:
        """
        从数据库获取缓存的用户数据

        Args:
            username: GitHub 用户名

        Returns:
            用户数据字典，如果不存在则返回 None
        """
        if not self.enabled:
            return None

        session = SessionLocal()
        try:
            candidate = self._find_candidate_by_username(session, username)
            if not candidate:
                return None

            # 返回完整的候选人数据
            return {
                "name": candidate.name,
                "email": candidate.email,
                "phone": candidate.phone,
                "github_url": candidate.github_url,
                "linkedin_url": candidate.linkedin_url,
                "twitter_url": candidate.twitter_url,
                "personal_website": candidate.personal_website,
                "current_company": candidate.current_company,
                "current_title": candidate.current_title,
                "bio": candidate.ai_summary,
                "skills": candidate.skills,
                "talent_tier": candidate.talent_tier,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
                # 可以根据需要添加更多字段
            }
        finally:
            session.close()

    def mark_as_crawled(self, username: str, data: Optional[Dict] = None):
        """
        标记用户已爬取（用于统计）

        Args:
            username: GitHub 用户名
            data: 爬取到的数据（可选）
        """
        self.stats["crawled_users"].append(username)
        self._log(f"🔄 爬取完成: @{username}")

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total * 100 if total > 0 else 0

        return {
            **self.stats,
            "total_requests": total,
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "cache_days": self.cache_days,
        }

    def print_stats(self):
        """打印缓存统计报告"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("📊 缓存统计报告")
        print("=" * 60)
        print(f"  总请求数:     {stats['total_requests']}")
        print(f"  缓存命中:     {stats['cache_hits']} ({stats['cache_hit_rate']})")
        print(f"  缓存未命中:   {stats['cache_misses']}")
        print(f"  跳过用户:     {len(stats['skipped_users'])}")
        print(f"  爬取用户:     {len(stats['crawled_users'])}")
        print(f"  缓存期:       {stats['cache_days']} 天")
        print("=" * 60 + "\n")

    def save_stats(self, filepath: str):
        """保存统计信息到文件"""
        stats = self.get_stats()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
        print(f"📄 统计信息已保存到: {filepath}")

    @staticmethod
    def batch_check_cache(usernames: List[str], cache_days: int = 30) -> Dict[str, bool]:
        """
        批量检查用户是否在缓存期内

        Args:
            usernames: GitHub 用户名列表
            cache_days: 缓存天数

        Returns:
            字典 {username: is_cached}
        """
        cache = GitHubCacheManager(cache_days=cache_days, verbose=False)
        results = {}

        for username in usernames:
            results[username] = cache.is_cached(username)

        return results


# ==================== 命令行接口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub 爬虫缓存管理器")
    parser.add_argument("action", choices=["check", "stats", "batch"], help="操作类型")
    parser.add_argument("--username", help="GitHub 用户名")
    parser.add_argument("--cache-days", type=int, default=30, help="缓存天数（默认30天）")
    parser.add_argument("--file", help="包含用户名的 JSON 文件")
    parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    cache = GitHubCacheManager(cache_days=args.cache_days)

    if args.action == "check":
        if not args.username:
            print("❌ 请提供 --username 参数")
            sys.exit(1)

        is_cached = cache.is_cached(args.username)
        if is_cached:
            data = cache.get_cached_data(args.username)
            print(f"\n✅ 用户 @{args.username} 在缓存期内")
            print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False, default=str)}")
        else:
            print(f"\n❌ 用户 @{args.username} 不在缓存期内，需要重新爬取")

    elif args.action == "batch":
        if not args.file:
            print("❌ 请提供 --file 参数")
            sys.exit(1)

        with open(args.file) as f:
            usernames = json.load(f)

        print(f"🔍 批量检查 {len(usernames)} 个用户...")
        results = cache.batch_check_cache(usernames, args.cache_days)

        cached_count = sum(1 for v in results.values() if v)
        print(f"\n✅ 在缓存期内: {cached_count} 人")
        print(f"❌ 需要重新爬取: {len(usernames) - cached_count} 人")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📄 结果已保存到: {args.output}")

    cache.print_stats()
