#!/usr/bin/env python3
"""
标准化公司名称

解决同一公司有多种写法的问题：
- Google DeepMind / google-deepmind / DeepMind / google deepmind
- OpenAI / openai
- Anthropic / anthropics
- Microsoft / Microsoft Research / Microsoft Research Asia

统一为标准名称，提高数据一致性
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
from collections import Counter

# 数据库路径
DB_PATH = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"

# 公司名称标准化映射表
COMPANY_NORMALIZATION = {
    # Google 系
    'google deepmind': 'Google DeepMind',
    'google-deepmind': 'Google DeepMind',
    'google deepmind': 'Google DeepMind',
    'deepmind': 'Google DeepMind',
    'googlemind': 'Google DeepMind',
    'deep mind': 'Google DeepMind',
    'googlebrain': 'Google Brain',
    'google brain': 'Google Brain',
    'googleresearch': 'Google Research',
    'google research': 'Google Research',
    'google': 'Google',
    'alphabet': 'Google',
    'google inc': 'Google',

    # OpenAI 系
    'open ai': 'OpenAI',
    'openai': 'OpenAI',
    'openai, l.p.': 'OpenAI',
    'openai lp': 'OpenAI',

    # Anthropic 系
    'anthropics': 'Anthropic',
    'anthropic.': 'Anthropic',

    # Microsoft 系
    'microsoft research': 'Microsoft Research',
    'microsoft research asia': 'Microsoft Research Asia',
    'microsoft': 'Microsoft',
    'msft': 'Microsoft',
    'microsoft corporation': 'Microsoft',

    # Meta 系
    'meta': 'Meta',
    'meta platforms': 'Meta',
    'facebook': 'Meta',
    'meta (facebook)': 'Meta',
    'fair, meta ai': 'Meta AI (FAIR)',
    'fair': 'Meta AI (FAIR)',
    'fair, meta': 'Meta AI (FAIR)',
    'meta fair': 'Meta AI (FAIR)',
    'meta fair,': 'Meta AI (FAIR)',
    'meta ai (fair)': 'Meta AI (FAIR)',
    'meta ai': 'Meta AI (FAIR)',
    'fair @ meta': 'Meta AI (FAIR)',
    'fair labs, meta ai': 'Meta AI (FAIR)',
    'meta / fair': 'Meta AI (FAIR)',
    'facebook ai research (fair)': 'Meta AI (FAIR)',
    'meta fundamental ai research (fair)': 'Meta AI (FAIR)',
    'fair labs, meta ai': 'Meta AI (FAIR)',
    'fair, meta ai': 'Meta AI (FAIR)',

    # Amazon
    'amazon': 'Amazon',
    'amazon web services': 'Amazon',
    'aws': 'Amazon',

    # 其他顶级公司
    'nvidia': 'NVIDIA',
    'nvidia corporation': 'NVIDIA',
    'intel': 'Intel',

    'ibm': 'IBM',
    'ibm research': 'IBM Research',

    'apple': 'Apple',
    'apple inc': 'Apple',

    'salesforce': 'Salesforce',
    'salesforce research': 'Salesforce Research',

    'adobe': 'Adobe',
    'adobe research': 'Adobe Research',

    'baidu': 'Baidu',
    'baidu inc': 'Baidu',

    'alibaba': 'Alibaba',
    'alibaba group': 'Alibaba',
    'alibaba cloud': 'Alibaba',
    'alibaba damo academy': 'Alibaba DAMO Academy',

    'tencent': 'Tencent',
    'tencent ai lab': 'Tencent AI Lab',
    'tencent holdings': 'Tencent',

    'bytedance': 'ByteDance',
    'byte dance': 'ByteDance',
    'byte dancers': 'ByteDance',

    # 清理明显错误的公司名
    'null': None,
    'none': None,
    'n/a': None,
    '-': None,
    'unknown': None,
}


def normalize_company_name(company_name):
    """标准化公司名称"""
    if not company_name:
        return None

    # 去除前后空格
    company = company_name.strip()

    # 转换为小写进行匹配
    company_lower = company.lower()

    # 移除常见后缀
    company_lower = company_lower.replace(',', '').replace('.', '').replace(' inc', '').replace(' corp', '')

    # 查找映射
    for variant, standard in COMPANY_NORMALIZATION.items():
        if variant == company_lower:
            return standard

    # 如果没有映射，返回原名（但去除多余空格和标点）
    return company


def analyze_company_names():
    """分析当前公司名称分布"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 查询所有公司名称
    cursor.execute("""
        SELECT current_company, COUNT(*) as count
        FROM candidates
        WHERE current_company IS NOT NULL AND current_company != ''
        GROUP BY current_company
        ORDER BY count DESC
        LIMIT 50
    """)

    companies = cursor.fetchall()

    print("=" * 60)
    print("📊 公司名称分布分析 (Top 50)")
    print("=" * 60)

    for c in companies:
        company = c['current_company']
        count = c['count']
        normalized = normalize_company_name(company)

        if normalized != company:
            print(f"  {company} ({count}人)")
            print(f"    → 标准化为: {normalized}")

    conn.close()


def normalize_company_names(dry_run=True):
    """执行公司名称标准化"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 查询所有需要标准化的记录
        query = """
        SELECT id, name, current_company, talent_tier
        FROM candidates
        WHERE current_company IS NOT NULL AND current_company != ''
        """

        cursor.execute(query)
        candidates = cursor.fetchall()

        print(f"📊 总共 {len(candidates)} 个有公司信息的候选人")
        print("=" * 60)

        # 统计需要修改的记录
        changes = []
        company_mapping = {}  # 记录 old -> new 的映射

        for c in candidates:
            old_company = c['current_company']
            new_company = normalize_company_name(old_company)

            if new_company and new_company != old_company:
                changes.append({
                    'id': c['id'],
                    'name': c['name'],
                    'old_company': old_company,
                    'new_company': new_company,
                    'tier': c['talent_tier']
                })

                # 记录映射
                if old_company not in company_mapping:
                    company_mapping[old_company] = new_company

        print(f"\n🔍 发现 {len(changes)} 条需要标准化的记录\n")

        # 按原公司分组显示
        old_companies = {}
        for change in changes:
            old = change['old_company']
            if old not in old_companies:
                old_companies[old] = []
            old_companies[old].append(change)

        # 显示前 20 个
        count = 0
        for old_company, company_list in old_companies.items():
            new_company = company_list[0]['new_company']
            print(f"  {old_company} ({len(company_list)}人)")
            print(f"    → {new_company}")
            for c in company_list[:3]:
                print(f"      - {c['name']} (Tier: {c['tier']})")
            if len(company_list) > 3:
                print(f"      ... 还有 {len(company_list) - 3} 个")

            count += 1
            if count >= 20:
                print(f"  ... 还有 {len(old_companies) - count} 个公司")
                break

        if not dry_run:
            # 执行标准化
            print(f"\n🔧 开始执行公司名称标准化...")

            update_query = """
            UPDATE candidates
            SET current_company = ?,
                updated_at = ?
            WHERE id = ?
            """

            updated_count = 0
            for change in changes:
                cursor.execute(update_query, (
                    change['new_company'],
                    datetime.now().isoformat(),
                    change['id']
                ))
                updated_count += 1

            conn.commit()
            print(f"\n✅ 已标准化 {updated_count} 条记录")

            # 生成报告
            report = {
                "scan_date": datetime.now().isoformat(),
                "total_analyzed": len(candidates),
                "records_changed": updated_count,
                "company_mapping": company_mapping,
                "affected_candidates": [
                    {
                        "id": c['id'],
                        "name": c['name'],
                        "old_company": c['old_company'],
                        "new_company": c['new_company'],
                        "tier": c['tier']
                    }
                    for c in changes
                ]
            }

            with open('company_normalization_report.json', 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"📄 详细报告已保存到: company_normalization_report.json")

        else:
            print(f"\n🔍 这是干运行模式，没有实际修改数据库")
            print(f"   如需实际执行，请使用: python3 normalize_company_names.py --execute")

        conn.close()

    except Exception as e:
        conn.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        conn.close()


def find_duplicate_candidates_by_github():
    """通过 GitHub URL 查找重复候选人"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 查找有重复 GitHub URL 的候选人
        query = """
        SELECT github_url, COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM candidates
        WHERE github_url IS NOT NULL AND github_url != ''
        GROUP BY github_url
        HAVING count > 1
        ORDER BY count DESC
        """

        cursor.execute(query)
        duplicates = cursor.fetchall()

        print("\n" + "=" * 60)
        print("🔍 GitHub URL 重复检查")
        print("=" * 60)

        if not duplicates:
            print("✅ 未发现重复的 GitHub URL")
        else:
            print(f"⚠️  发现 {len(duplicates)} 个重复的 GitHub URL\n")

            for dup in duplicates[:20]:  # 只显示前 20 个
                github_url = dup['github_url']
                count = dup['count']
                ids = dup['ids'].split(',')

                # 查询这些候选人的详细信息
                placeholders = ','.join(['?' for _ in ids])
                detail_query = f"""
                SELECT id, name, current_company, talent_tier
                FROM candidates
                WHERE id IN ({placeholders})
                """

                cursor.execute(detail_query, ids)
                candidates = cursor.fetchall()

                print(f"  {github_url} ({count} 个重复)")
                for c in candidates:
                    print(f"    ID: {c['id']}, 姓名: {c['name']}, 公司: {c['current_company']}, Tier: {c['talent_tier']}")

            if len(duplicates) > 20:
                print(f"  ... 还有 {len(duplicates) - 20} 个重复")

        conn.close()

    except Exception as e:
        print(f"❌ 错误: {e}")
        raise
    finally:
        conn.close()


def clean_invalid_company_names(dry_run=True):
    """清理无效的公司名称"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 查找所有公司名称
        cursor.execute("""
            SELECT id, name, current_company, talent_tier
            FROM candidates
            WHERE current_company IS NOT NULL AND current_company != ''
        """)

        candidates = cursor.fetchall()

        print("=" * 60)
        print("🧹 清理无效公司名称")
        print("=" * 60)

        # 无效公司名称的模式
        invalid_patterns = [
            lambda x: len(x) < 3,  # 太短
            lambda x: any(c in x for c in ['🍞', 'ʕ', '•', '͡', 'ʔ', '͓']),  # 包含 emoji
            lambda x: x.startswith('@'),  # 以 @ 开头（可能是邮箱）
            lambda x: x.count('@') > 1,  # 多个 @
            lambda x: x in ['null', 'none', 'n/a', '-', 'unknown', '待定', ' TBD'],  # 明确无效
        ]

        invalid_candidates = []

        for c in candidates:
            company = c['current_company']
            is_invalid = any(pattern(company) for pattern in invalid_patterns)

            if is_invalid:
                invalid_candidates.append(c)

        print(f"\n🔍 发现 {len(invalid_candidates)} 个无效公司名称\n")

        # 按类型分组
        by_pattern = {}
        for c in invalid_candidates[:30]:  # 只显示前 30 个
            company = c['current_company']

            # 分类
            if len(company) < 3:
                category = "太短"
            elif any(c in company for c in ['🍞', 'ʕ', '•', '͡', 'ʔ', '͓']):
                category = "包含特殊字符"
            elif company.startswith('@'):
                category = "以@开头"
            else:
                category = "其他"

            if category not in by_pattern:
                by_pattern[category] = []
            by_pattern[category].append(c)

        # 显示
        for category, candidates_list in by_pattern.items():
            print(f"\n  {category} ({len(candidates_list)} 个):")
            for c in candidates_list[:5]:
                print(f"    - {c['current_company']} (ID: {c['id']}, 姓名: {c['name']}, Tier: {c['talent_tier']})")
            if len(candidates_list) > 5:
                print(f"    ... 还有 {len(candidates_list) - 5} 个")

        if not dry_run:
            # 执行清理（将无效公司名设为 NULL）
            print(f"\n🔧 开始清理无效公司名称...")

            update_query = """
            UPDATE candidates
            SET current_company = NULL,
                notes = ?,
                updated_at = ?
            WHERE id = ?
            """

            cleaned_count = 0
            for c in invalid_candidates:
                old_notes = (c['notes'] or "")
                new_notes = f"[清理无效公司名: '{c['current_company']}'] {old_notes}"

                cursor.execute(update_query, (
                    new_notes.strip(),
                    datetime.now().isoformat(),
                    c['id']
                ))
                cleaned_count += 1

            conn.commit()
            print(f"\n✅ 已清理 {cleaned_count} 条记录")

            # 生成报告
            invalid_types = {}
            for c in invalid_candidates:
                company = c['current_company']

                if len(company) < 3:
                    category = "too_short"
                elif any(c in company for c in ['🍞', 'ʕ', '•', '͡', 'ʔ', '͓']):
                    category = "special_chars"
                elif company.startswith('@'):
                    category = "starts_with_at"
                else:
                    category = "other"

                if category not in invalid_types:
                    invalid_types[category] = 0
                invalid_types[category] += 1

            report = {
                "scan_date": datetime.now().isoformat(),
                "total_analyzed": len(candidates),
                "invalid_found": len(invalid_candidates),
                "records_cleaned": cleaned_count,
                "invalid_by_type": invalid_types,
                "cleaned_candidates": [
                    {
                        "id": c['id'],
                        "name": c['name'],
                        "invalid_company": c['current_company'],
                        "tier": c['talent_tier']
                    }
                    for c in invalid_candidates
                ]
            }

            with open('invalid_company_cleaning_report.json', 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"📄 详细报告已保存到: invalid_company_cleaning_report.json")

        else:
            print(f"\n🔍 这是干运行模式，没有实际修改数据库")
            print(f"   如需实际执行，请使用: python3 normalize_company_names.py --execute --clean")

        conn.close()

    except Exception as e:
        conn.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub 人才库数据质量优化")
    parser.add_argument('--execute', action='store_true', help='实际执行修改（默认为干运行）')
    parser.add_argument('--analyze', action='store_true', help='仅分析，不执行任何操作')
    parser.add_argument('--normalize', action='store_true', help='执行公司名称标准化')
    parser.add_argument('--dedup', action='store_true', help='查找重复候选人（基于GitHub URL）')
    parser.add_argument('--clean', action='store_true', help='清理无效公司名称')

    args = parser.parse_args()

    # 如果没有指定任何操作，默认执行全部
    if not (args.analyze or args.normalize or args.dedup or args.clean):
        args.analyze = True
        args.normalize = True
        args.dedup = True
        args.clean = True

    print("=" * 60)
    print("🔧 GitHub 人才库数据质量优化工具")
    print("=" * 60)

    # 1. 分析
    if args.analyze:
        analyze_company_names()

    # 2. 标准化
    if args.normalize:
        normalize_company_names(dry_run=not args.execute)

    # 3. 去重检查
    if args.dedup:
        find_duplicate_candidates_by_github()

    # 4. 清理无效名称
    if args.clean:
        clean_invalid_company_names(dry_run=not args.execute)

    print("\n" + "=" * 60)
    print("✅ 完成！")
    if not args.execute:
        print("💡 提示: 这是干运行模式，使用 --execute 参数实际执行修改")
