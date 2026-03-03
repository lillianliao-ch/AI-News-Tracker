#!/usr/bin/env python3
"""
修复顶级公司分级错误

将顶级公司（DeepMind, OpenAI, Anthropic等）的A级人才升级为S级
"""

import sys
import os
import sqlite3
import json
from datetime import datetime

# 数据库路径
DB_PATH = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"

# 顶级公司关键词（不区分大小写）
TOP_COMPANY_KEYWORDS = [
    'deepmind',
    'openai',
    'anthropic',
    'meta ai',
    'fair',  # Facebook AI Research
    'google brain',
    'xaigroup',
    'xai',
    'microsoft research',
    'openai'
]

# 需要检查的公司（更宽松的匹配）
LOOSE_MATCH_COMPANIES = {
    'google': ['google research', 'google deepmind', 'googler'],
    'meta': ['meta ai', 'fair', 'facebook ai'],
    'microsoft': ['microsoft research']
}


def is_top_company(text: str) -> bool:
    """检查是否为顶级公司"""
    if not text:
        return False

    text_lower = text.lower()

    # 精确匹配顶级公司关键词
    for keyword in TOP_COMPANY_KEYWORDS:
        if keyword in text_lower:
            return True

    return False


def should_upgrade_to_s(row: dict) -> tuple:
    """
    判断是否应该升级为 S 级

    Returns:
        (should_upgrade, reason)
    """
    current_tier = row.get('talent_tier', '')
    current_company = row.get('current_company', '') or ''
    notes = row.get('notes', '') or ''
    name = row.get('name', '')

    # 已经是 S 级的跳过
    if current_tier == 'S':
        return False, "已经是 S 级"

    # D 级不升级（可能是组织账号）
    if current_tier == 'D':
        return False, "D 级，跳过"

    # 首先检查 current_company（当前公司）
    if current_company and is_top_company(current_company):
        return True, f"当前在顶级公司工作: {current_company}"

    # 如果没有 current_company，检查 notes 中的"当前"职位
    # 只检查明确标注为"当前"的顶级公司经历
    if notes and '【当前】' in notes:
        # 提取"当前"部分
        current_section = notes.split('【当前】')[1].split('【')[0] if '【' in notes.split('【当前】')[1] else notes.split('【当前】')[1]

        # 检查"当前"部分是否包含顶级公司
        if is_top_company(current_section):
            return True, f"当前在顶级公司工作 (从 notes 检测)"

    return False, None


def fix_top_company_tiers(dry_run=True):
    """修复顶级公司分级"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 查询所有非 D 级的候选人
        query = """
        SELECT id, name, current_company, talent_tier, notes
        FROM candidates
        WHERE talent_tier != 'D'
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        candidates = [dict(row) for row in rows]

        print(f"📊 总共 {len(candidates)} 个候选人（非D级）")
        print("=" * 70)

        # 找出需要升级的候选人
        to_upgrade = []
        to_s = []  # 升级到 S
        to_a_plus = []  # 升级到 A+

        for c in candidates:
            should_upgrade, reason = should_upgrade_to_s(c)

            if should_upgrade:
                current_tier = c.get('talent_tier', '')
                to_upgrade.append((c, reason))

                # A/A+ 级升级到 S
                if current_tier in ['A', 'A+', 'B', 'B+']:
                    to_s.append((c, reason))

        print(f"\n🔍 需要升级的候选人: {len(to_upgrade)} 个")
        print(f"   → S 级: {len(to_s)} 个")

        # 显示部分样本
        print("\n📋 将升级到 S 级的样本（前20个）:")
        for c, reason in to_s[:20]:
            old_tier = c.get('talent_tier', '')
            name = c.get('name', 'Unknown')
            company = c.get('current_company', '') or '(未知)'
            print(f"  • {name} ({company})")
            print(f"    ID: {c.get('id')}, {old_tier} → S")
            print(f"    原因: {reason}")

        if len(to_s) > 20:
            print(f"  ... 还有 {len(to_s) - 20} 个")

        if not dry_run:
            print(f"\n🔧 开始升级...")

            updated_count = 0
            upgrade_log = []

            for c, reason in to_s:
                old_tier = c.get('talent_tier')
                new_notes = (c.get('notes') or "") + f" [顶级公司自动升级: {reason}]"

                update_query = """
                UPDATE candidates
                SET talent_tier = 'S',
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
                upgrade_log.append({
                    "id": c.get('id'),
                    "name": c.get('name'),
                    "company": c.get('current_company') or '',
                    "old_tier": old_tier,
                    "new_tier": "S",
                    "reason": reason
                })

                if updated_count <= 10:
                    print(f"  ✓ {c.get('name')}: {old_tier} → S")

            conn.commit()
            print(f"\n✅ 已升级 {updated_count} 个候选人为 S 级")

            # 生成报告
            report = {
                "fix_date": datetime.now().isoformat(),
                "total_scanned": len(candidates),
                "to_upgrade": len(to_upgrade),
                "upgraded_to_s": updated_count,
                "upgrade_log": upgrade_log
            }

            with open('top_company_upgrade_report.json', 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"📄 详细报告已保存到: top_company_upgrade_report.json")

            # 统计
            print("\n📊 升级统计:")
            print(f"  从 A 升级到 S: {sum(1 for c in to_s if c[0].get('talent_tier') == 'A')}")
            print(f"  从 A+ 升级到 S: {sum(1 for c in to_s if c[0].get('talent_tier') == 'A+')}")
            print(f"  从 B 升级到 S: {sum(1 for c in to_s if c[0].get('talent_tier') == 'B')}")
            print(f"  从 B+ 升级到 S: {sum(1 for c in to_s if c[0].get('talent_tier') == 'B+')}")

        else:
            print(f"\n🔍 这是干运行模式，没有实际修改数据库")
            print(f"   如需实际执行，请使用: python3 fix_top_company_tiers.py --execute")

        conn.close()

    except Exception as e:
        conn.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="修复顶级公司分级")
    parser.add_argument('--execute', action='store_true', help='实际执行升级（默认为干运行）')

    args = parser.parse_args()

    print("=" * 70)
    print("🔧 顶级公司分级修复工具")
    print("=" * 70)

    dry_run = not args.execute
    fix_top_company_tiers(dry_run=dry_run)
