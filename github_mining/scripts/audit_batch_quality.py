#!/usr/bin/env python3
"""
3/11 批次质量审计脚本
输出: github_mining/docs/BATCH_QUALITY_REPORT_20260311.md
"""
import sqlite3
import json
import re
import random
from datetime import datetime
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "personal-ai-headhunter" / "data" / "headhunter_dev.db"
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "BATCH_QUALITY_REPORT_20260311.md"

BATCH_WHERE = "source='github' AND created_at >= '2026-03-11' AND created_at < '2026-03-13'"
OLD_WHERE = "source='github' AND created_at < '2026-03-11'"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def section_field_coverage(conn):
    """字段覆盖率 + 与旧批次对比"""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM candidates WHERE {BATCH_WHERE}")
    total = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM candidates WHERE {OLD_WHERE}")
    old_total = cur.fetchone()[0]

    fields = [
        ('name', '姓名'),
        ('email', '邮箱'),
        ('linkedin_url', 'LinkedIn'),
        ('twitter_url', 'Twitter'),
        ('personal_website', '个人网站'),
        ('current_company', '当前公司'),
        ('current_title', '当前职位'),
        ('github_url', 'GitHub'),
        ('structured_tags', '结构化标签'),
        ('talent_labels', '人才标签'),
        ('ai_summary', 'AI摘要'),
        ('skills', '技能'),
        ('work_experiences', '工作经历'),
        ('education_details', '教育背景'),
    ]

    lines = ["## 一、字段覆盖率\n"]
    lines.append("| 字段 | 新批次 | 覆盖率 | 旧批次覆盖率 | 差异 |")
    lines.append("|------|--------|--------|------------|------|")

    for col, label in fields:
        # 新批次
        try:
            cur.execute(f"SELECT COUNT(*) FROM candidates WHERE {BATCH_WHERE} AND {col} IS NOT NULL AND {col} != '' AND {col} != '[]' AND {col} != '{{}}'")
            new_n = cur.fetchone()[0]
        except:
            new_n = -1
        # 旧批次
        try:
            cur.execute(f"SELECT COUNT(*) FROM candidates WHERE {OLD_WHERE} AND {col} IS NOT NULL AND {col} != '' AND {col} != '[]' AND {col} != '{{}}'")
            old_n = cur.fetchone()[0]
        except:
            old_n = -1

        if new_n >= 0 and old_n >= 0 and old_total > 0:
            new_pct = new_n * 100 / total
            old_pct = old_n * 100 / old_total
            diff = new_pct - old_pct
            flag = "🔴" if diff < -10 else ("🟡" if diff < -3 else "🟢")
            lines.append(f"| {label} | {new_n:,} | {new_pct:.1f}% | {old_pct:.1f}% | {flag} {diff:+.1f}% |")
        elif new_n >= 0:
            new_pct = new_n * 100 / total
            lines.append(f"| {label} | {new_n:,} | {new_pct:.1f}% | N/A | — |")
        else:
            lines.append(f"| {label} | N/A | N/A | N/A | — |")

    lines.append(f"\n> 新批次: {total:,} 人 | 旧批次: {old_total:,} 人\n")
    return "\n".join(lines)


def section_tier_distribution(conn):
    """评级分布"""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM candidates WHERE {BATCH_WHERE}")
    total = cur.fetchone()[0]

    cur.execute(f"SELECT talent_tier, COUNT(*) FROM candidates WHERE {BATCH_WHERE} GROUP BY talent_tier ORDER BY CASE talent_tier WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B+' THEN 3 WHEN 'B' THEN 4 WHEN 'C' THEN 5 WHEN 'D' THEN 6 ELSE 7 END")
    rows = cur.fetchall()

    # 旧批次
    cur.execute(f"SELECT COUNT(*) FROM candidates WHERE {OLD_WHERE}")
    old_total = cur.fetchone()[0]
    cur.execute(f"SELECT talent_tier, COUNT(*) FROM candidates WHERE {OLD_WHERE} GROUP BY talent_tier")
    old_tiers = {r[0]: r[1] for r in cur.fetchall()}

    lines = ["## 二、评级分布\n"]
    lines.append("| 评级 | 新批次 | 占比 | 旧批次占比 |")
    lines.append("|------|--------|------|----------|")
    for tier, cnt in rows:
        pct = cnt * 100 / total
        old_pct = old_tiers.get(tier, 0) * 100 / old_total if old_total > 0 else 0
        lines.append(f"| {tier or 'None'} | {cnt:,} | {pct:.1f}% | {old_pct:.1f}% |")

    high = sum(c for t, c in rows if t in ('S', 'A', 'B+'))
    lines.append(f"\n**优质候选人 (S/A/B+)**: {high} 人 ({high*100/total:.1f}%)\n")
    return "\n".join(lines)


def section_data_anomalies(conn):
    """数据异常检测"""
    cur = conn.cursor()
    lines = ["## 三、数据异常检测\n"]

    # 1. 重复 GitHub URL
    cur.execute(f"SELECT github_url, COUNT(*) as cnt FROM candidates WHERE {BATCH_WHERE} AND github_url IS NOT NULL GROUP BY github_url HAVING cnt > 1")
    dups = cur.fetchall()
    lines.append(f"### 3.1 重复记录: **{len(dups)}** 个重复 GitHub URL")
    if dups:
        for d in dups[:10]:
            lines.append(f"- `{d[0]}` (×{d[1]})")
    lines.append("")

    # 2. LinkedIn 格式
    cur.execute(f"SELECT linkedin_url FROM candidates WHERE {BATCH_WHERE} AND linkedin_url IS NOT NULL AND linkedin_url != ''")
    li_urls = [r[0] for r in cur.fetchall()]
    bad_li = [u for u in li_urls if 'linkedin.com' not in u.lower()]
    lines.append(f"### 3.2 LinkedIn 格式: **{len(bad_li)}** 个异常格式 (共 {len(li_urls)})")
    for u in bad_li[:5]:
        lines.append(f"- `{u}`")
    lines.append("")

    # 3. Email 格式
    cur.execute(f"SELECT email FROM candidates WHERE {BATCH_WHERE} AND email IS NOT NULL AND email != ''")
    emails = [r[0] for r in cur.fetchall()]
    email_re = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    bad_email = [e for e in emails if not email_re.match(e)]
    lines.append(f"### 3.3 Email 格式: **{len(bad_email)}** 个异常 (共 {len(emails)})")
    for e in bad_email[:5]:
        lines.append(f"- `{e}`")
    lines.append("")

    # 4. 空姓名
    cur.execute(f"SELECT COUNT(*) FROM candidates WHERE {BATCH_WHERE} AND (name IS NULL OR name = '')")
    no_name = cur.fetchone()[0]
    lines.append(f"### 3.4 缺失姓名: **{no_name}** 人\n")

    # 5. S/A 但无联系方式
    cur.execute(f"SELECT name, github_url FROM candidates WHERE {BATCH_WHERE} AND talent_tier IN ('S','A') AND (email IS NULL OR email = '') AND (linkedin_url IS NULL OR linkedin_url = '')")
    no_contact = cur.fetchall()
    lines.append(f"### 3.5 S/A 级无联系方式: **{len(no_contact)}** 人")
    for r in no_contact[:10]:
        lines.append(f"- {r[0]} | {r[1]}")
    lines.append("")

    return "\n".join(lines)


def section_top_candidates(conn):
    """Top 50 S/A 级候选人"""
    cur = conn.cursor()
    cur.execute(f"""SELECT name, current_company, current_title, talent_tier, email, linkedin_url, github_url 
        FROM candidates WHERE {BATCH_WHERE} AND talent_tier IN ('S','A') 
        ORDER BY CASE talent_tier WHEN 'S' THEN 1 WHEN 'A' THEN 2 END, name
        LIMIT 50""")
    rows = cur.fetchall()

    lines = ["## 四、Top 50 高级候选人 (S/A)\n"]
    lines.append("| # | 姓名 | 评级 | 公司 | 职位 | 联系方式 |")
    lines.append("|---|------|------|------|------|---------|")
    for i, r in enumerate(rows, 1):
        name = r[0] or ''
        company = (r[1] or '')[:20]
        title = (r[2] or '')[:25]
        tier = r[3]
        contact = []
        if r[4]: contact.append('📧')
        if r[5]: contact.append('🔗')
        contact_str = ' '.join(contact) if contact else '❌'
        lines.append(f"| {i} | {name[:15]} | {tier} | {company} | {title} | {contact_str} |")

    lines.append("")
    return "\n".join(lines)


def section_random_sample(conn):
    """30 人随机抽检列表"""
    cur = conn.cursor()
    cur.execute(f"SELECT id, name, current_company, current_title, talent_tier, github_url, email FROM candidates WHERE {BATCH_WHERE} ORDER BY RANDOM() LIMIT 30")
    rows = cur.fetchall()

    lines = ["## 五、30 人随机抽检样本\n"]
    lines.append("以下候选人需人工逐个打开 GitHub 主页核实信息准确性：\n")
    lines.append("| # | 姓名 | 评级 | 公司 | GitHub | 核实结果 |")
    lines.append("|---|------|------|------|--------|---------|")
    for i, r in enumerate(rows, 1):
        name = (r[1] or '')[:15]
        company = (r[2] or '')[:15]
        tier = r[4] or '?'
        gh = r[5] or ''
        gh_short = gh.replace('https://github.com/', '').replace('https://api.github.com/users/', '')[:20]
        lines.append(f"| {i} | {name} | {tier} | {company} | [{gh_short}]({gh}) | ⬜ 待验证 |")

    lines.append("\n> 核实要点: 姓名、公司、职位是否与 GitHub/个人网站一致；评级是否合理\n")
    return "\n".join(lines)


def main():
    print("🔍 开始审计 3/11 批次...", flush=True)
    conn = get_conn()

    report = []
    report.append("# 3/11 批次人才质量审计报告\n")
    report.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    print("  📊 字段覆盖率...", flush=True)
    report.append(section_field_coverage(conn))

    print("  📊 评级分布...", flush=True)
    report.append(section_tier_distribution(conn))

    print("  🔍 数据异常...", flush=True)
    report.append(section_data_anomalies(conn))

    print("  🌟 Top 50...", flush=True)
    report.append(section_top_candidates(conn))

    print("  🎲 随机抽检...", flush=True)
    report.append(section_random_sample(conn))

    # 写入文件
    content = "\n".join(report)
    OUTPUT_PATH.write_text(content, encoding='utf-8')
    print(f"\n✅ 报告已生成: {OUTPUT_PATH}", flush=True)

    conn.close()


if __name__ == '__main__':
    main()
