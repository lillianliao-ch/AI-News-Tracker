#!/usr/bin/env python3
"""
查询紧急程度高的职位
使用方法: python query_urgent_jobs.py [min_urgency]
示例: python query_urgent_jobs.py 1  # 查询紧急度>=1的职位
"""

import sys
from sqlalchemy import create_engine, text
from datetime import datetime

def query_urgent_jobs(min_urgency=1):
    """查询紧急程度 >= min_urgency 的职位"""

    # 连接数据库
    engine = create_engine('sqlite:///data/headhunter.db')

    with engine.connect() as conn:
        # 查询紧急职位
        query = text("""
            SELECT
                id,
                title,
                company,
                department,
                urgency,
                salary_range,
                location,
                required_experience_years,
                hr_contact,
                headcount,
                notes,
                sourcing_notes,
                created_at
            FROM jobs
            WHERE urgency >= :min_urgency
            ORDER BY urgency DESC, created_at DESC
        """)

        result = conn.execute(query, {"min_urgency": min_urgency})
        jobs = result.fetchall()

        if not jobs:
            print(f"❌ 没有找到紧急度 >= {min_urgency} 的职位")

            # 显示所有职位的紧急程度
            all_jobs = conn.execute(text("""
                SELECT id, title, company, urgency
                FROM jobs
                ORDER BY urgency DESC, id DESC
                LIMIT 20
            """)).fetchall()

            if all_jobs:
                print(f"\n📋 现有职位的紧急程度分布:")
                urgency_map = {0: "普通", 1: "较急", 2: "紧急", 3: "非常紧急"}
                for job in all_jobs:
                    text = urgency_map.get(job.urgency, f"未知({job.urgency})")
                    print(f"  ID {job.id}: {job.title} - {job.company} ({text})")
        else:
            urgency_map = {0: "普通", 1: "较急", 2: "紧急", 3: "非常紧急"}
            emoji_map = {1: "🟢", 2: "🟡", 3: "🔴"}

            print(f"✅ 找到 {len(jobs)} 个紧急职位")
            print("=" * 100)
            print()

            for job in jobs:
                emoji = emoji_map.get(job.urgency, "")
                urgency_text = urgency_map.get(job.urgency, str(job.urgency))

                print(f"{emoji} 【{urgency_text}】{job.title}")
                print(f"   公司: {job.company or '未指定'}")
                if job.department:
                    print(f"   部门: {job.department}")
                if job.salary_range:
                    print(f"   薪资: {job.salary_range}")
                if job.location:
                    print(f"   地点: {job.location}")
                if job.headcount:
                    print(f"   HC: {job.headcount} 人")
                if job.required_experience_years:
                    print(f"   经验要求: {job.required_experience_years} 年+")
                if job.hr_contact:
                    print(f"   HR 联系人: {job.hr_contact}")
                if job.sourcing_notes:
                    preview = job.sourcing_notes[:100] + "..." if len(job.sourcing_notes) > 100 else job.sourcing_notes
                    print(f"   Sourcing 策略: {preview}")
                if job.notes:
                    preview = job.notes[:100] + "..." if len(job.notes) > 100 else job.notes
                    print(f"   备注: {preview}")
                print(f"   ID: {job.id} | 创建于: {job.created_at}")
                print("-" * 100)
                print()

        # 统计紧急程度分布
        stats = conn.execute(text("""
            SELECT urgency, COUNT(*) as count
            FROM jobs
            GROUP BY urgency
            ORDER BY urgency DESC
        """)).fetchall()

        if stats:
            print("📊 紧急程度统计:")
            print("-" * 50)
            total = 0
            for row in stats:
                text = urgency_map.get(row.urgency, str(row.urgency))
                emoji = emoji_map.get(row.urgency, "")
                print(f"{emoji} {text}: {row.count} 个")
                total += row.count
            print(f"\n总计: {total} 个职位")

if __name__ == "__main__":
    min_urgency = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"🔍 查询紧急度 >= {min_urgency} 的职位\n")
    query_urgent_jobs(min_urgency)
