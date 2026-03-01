#!/usr/bin/env python3
"""
清理 GitHub 数据库中的组织账号

识别并标记那些被误认为是个人账号的组织账号（如 tensorflow, kubernetes 等）
"""

import sys
import os
import sqlite3
import json
from datetime import datetime

# 数据库路径
DB_PATH = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"

# 已知组织黑名单
KNOWN_ORGS = [
    'tensorflow', 'keras', 'pytorch', 'kubernetes', 'cursor',
    'meta-pytorch', 'google-research-datasets', 'huggingface',
    'microsoft', 'google', 'facebook', 'amazonaws', 'alibaba',
    'apache', 'elastic', 'nv-tlabs', 'tensorflow', 'pytorch',
    'open-mmlab', 'rust-lang', 'golang', 'nodejs', 'vuejs',
    'react', 'angular', 'facebookincubator', 'uber', 'netflix',
    'airbnb', 'spotify', 'twitter', 'instagram', 'linkedin'
]

# 可疑特征（无空格、全小写、品牌词）
SUSPICIOUS_PATTERNS = [
    'tensor', 'kuber', 'pytorch', 'meta', 'facebook',
    'google', 'microsoft', 'amazon', 'alibaba', 'tencent',
    'apache', 'elastic', 'nvidia', 'intel', 'amd'
]


def is_suspicious_account(row):
    """检查是否为可疑组织账号"""
    github_url = row.get('github_url')
    if not github_url:
        return False, "无 GitHub 链接"

    username = github_url.rstrip('/').split('/')[-1].strip().lower()
    name = row.get('name', '') or ''
    bio = row.get('bio', '') or ''  # bio 可能在 notes 中
    email = row.get('email', '') or ''
    notes = row.get('notes', '') or ''

    # 检查1: 在已知黑名单中
    if username in KNOWN_ORGS:
        return True, f"匹配黑名单: {username}"

    # 检查2: GitHub URL 包含组织关键词
    if any(org in username for org in SUSPICIOUS_PATTERNS):
        # 进一步验证特征
        # 特征A: name 等于 username
        if name and name.lower() == username:
            # 特征B: 无 bio 或 bio 很短
            if not notes or (notes and len(notes) < 20):
                # 特征C: 无邮箱
                if not email:
                    return True, f"可疑组织特征: name=username, 无notes, 无email"

        # 特征D: 包含官方词汇
        official_keywords = ['official', 'repo', 'repository', 'project', 'team', 'org']
        if notes and any(kw in notes.lower() for kw in official_keywords):
            return True, f"Notes包含官方词汇: {notes[:50]}"

    return False, None


def identify_org_accounts(dry_run=True):
    """识别并标记组织账号"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 查询所有 GitHub 来源的候选人
        query = """
        SELECT id, name, email, github_url, talent_tier, notes, source
        FROM candidates
        WHERE source LIKE '%github%' AND github_url IS NOT NULL
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        candidates = [dict(row) for row in rows]

        print(f"📊 总共 {len(candidates)} 个 GitHub 候选人")
        print("=" * 60)

        org_accounts = []
        suspicious_accounts = []

        for c in candidates:
            is_org, reason = is_suspicious_account(c)

            if is_org:
                org_accounts.append((c, reason))
            elif reason and ("可疑" in reason or "黑名单" in reason):
                suspicious_accounts.append((c, reason))

        # 输出结果
        print(f"\n🔴 确认的组织账号: {len(org_accounts)} 个")
        for c, reason in org_accounts[:20]:  # 只显示前20个
            print(f"  • {c.get('name')} ({c.get('github_url')})")
            print(f"    ID: {c.get('id')}, 当前Tier: {c.get('talent_tier')}")
            print(f"    原因: {reason}")

        if len(org_accounts) > 20:
            print(f"  ... 还有 {len(org_accounts) - 20} 个")

        print(f"\n⚠️  可疑账号: {len(suspicious_accounts)} 个")
        for c, reason in suspicious_accounts[:10]:
            print(f"  • {c.get('name')} ({c.get('github_url')})")
            print(f"    原因: {reason}")

        if not dry_run:
            # 执行标记
            print(f"\n🔧 开始标记组织账号为 D 级...")

            updated_count = 0
            for c, reason in org_accounts:
                old_tier = c.get('talent_tier')
                if old_tier != 'D':
                    # 更新数据库
                    new_notes = (c.get('notes') or "") + f" [标记为组织账号: {reason}]"

                    update_query = """
                    UPDATE candidates
                    SET talent_tier = 'D',
                        notes = ?,
                        updated_at = ?
                    WHERE id = ?
                    """

                    cursor.execute(update_query, (
                        new_notes,
                        datetime.now().isoformat(),
                        c.get('id')
                    ))

                    updated_count += 1
                    print(f"  ✓ {c.get('name')}: {old_tier} → D")

            conn.commit()
            print(f"\n✅ 已标记 {updated_count} 个账号为 D 级")

            # 生成报告
            report = {
                "scan_date": datetime.now().isoformat(),
                "total_scanned": len(candidates),
                "org_accounts_found": len(org_accounts),
                "suspicious_accounts": len(suspicious_accounts),
                "accounts_marked": updated_count,
                "org_list": [
                    {
                        "id": c.get('id'),
                        "name": c.get('name'),
                        "github_url": c.get('github_url'),
                        "old_tier": c.get('talent_tier'),
                        "reason": reason
                    }
                    for c, reason in org_accounts
                ]
            }

            with open('org_accounts_report.json', 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"📄 详细报告已保存到: org_accounts_report.json")

        else:
            print(f"\n🔍 这是干运行模式，没有实际修改数据库")
            print(f"   如需实际执行，请使用: python3 clean_org_accounts.py --execute")

        conn.close()

    except Exception as e:
        conn.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="清理 GitHub 组织账号")
    parser.add_argument('--execute', action='store_true', help='实际执行标记（默认为干运行）')
    parser.add_argument('--tier', help='只检查指定 Tier 的候选人')

    args = parser.parse_args()

    print("=" * 60)
    print("🧹 GitHub 组织账号清理工具")
    print("=" * 60)

    dry_run = not args.execute
    identify_org_accounts(dry_run=dry_run)
