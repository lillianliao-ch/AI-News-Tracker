#!/usr/bin/env python3
"""
标记职位为紧急
使用方法:
  python mark_jobs_urgent.py --list              # 列出所有职位
  python mark_jobs_urgent.py --mark <id> <level> # 标记单个职位
  python mark_jobs_urgent.py --auto              # 自动标记最近的职位
  python mark_jobs_urgent.py --reset             # 重置所有紧急度

紧急程度:
  0 = 普通
  1 = 较急
  2 = 紧急
  3 = 非常紧急
"""

import sys
import argparse
from sqlalchemy import create_engine, text

DB_PATH = 'data/headhunter.db'

def list_jobs(limit=20):
    """列出职位"""
    engine = create_engine(f'sqlite:///{DB_PATH}')

    with engine.connect() as conn:
        jobs = conn.execute(text("""
            SELECT id, title, company, urgency, salary_range,
                   created_at
            FROM jobs
            ORDER BY urgency DESC, id DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()

        if not jobs:
            print("❌ 没有找到职位")
            return

        print(f"📋 职位列表 (最近 {len(jobs)} 个):")
        print("=" * 100)

        for job in jobs:
            urgency_map = {0: "", 1: "🟢", 2: "🟡", 3: "🔴"}
            emoji = urgency_map.get(job.urgency, "")
            urgency_text = f" [紧急度: {job.urgency}]" if job.urgency > 0 else ""

            print(f"ID {job.id}: {emoji} {job.title} - {job.company}{urgency_text}")
            if job.salary_range:
                print(f"        薪资: {job.salary_range}")
            print(f"        创建于: {job.created_at}")
            print()

def mark_job(job_id, urgency):
    """标记单个职位"""
    if not 0 <= urgency <= 3:
        print(f"❌ 紧急度必须在 0-3 之间")
        return False

    engine = create_engine(f'sqlite:///{DB_PATH}')

    with engine.connect() as conn:
        # 检查职位是否存在
        job = conn.execute(text("""
            SELECT id, title, company, urgency
            FROM jobs
            WHERE id = :job_id
        """), {"job_id": job_id}).fetchone()

        if not job:
            print(f"❌ 职位 ID {job_id} 不存在")
            return False

        # 更新紧急度
        conn.execute(text("""
            UPDATE jobs
            SET urgency = :urgency
            WHERE id = :job_id
        """), {"urgency": urgency, "job_id": job_id})

        conn.commit()

        urgency_map = {0: "普通", 1: "较急", 2: "紧急", 3: "非常紧急"}
        urgency_text = urgency_map.get(urgency, str(urgency))

        print(f"✅ 职位已更新:")
        print(f"   ID: {job.id}")
        print(f"   职位: {job.title} - {job.company}")
        print(f"   紧急度: {job.urgency} → {urgency_text} ({urgency})")

    return True

def mark_recent_jobs(count=5, urgency=2):
    """自动标记最近的职位为紧急"""
    engine = create_engine(f'sqlite:///{DB_PATH}')

    with engine.connect() as conn:
        # 获取最近的非紧急职位
        jobs = conn.execute(text("""
            SELECT id, title, company
            FROM jobs
            WHERE urgency = 0
            ORDER BY id DESC
            LIMIT :count
        """), {"count": count}).fetchall()

        if not jobs:
            print(f"❌ 没有找到可标记的职位")
            return False

        urgency_map = {0: "普通", 1: "较急", 2: "紧急", 3: "非常紧急"}
        urgency_text = urgency_map.get(urgency, str(urgency))

        print(f"🔄 标记最近的 {len(jobs)} 个职位为「{urgency_text}」:")
        print()

        for job in jobs:
            conn.execute(text("""
                UPDATE jobs
                SET urgency = :urgency
                WHERE id = :job_id
            """), {"urgency": urgency, "job_id": job.id})

            print(f"  ✅ ID {job.id}: {job.title} - {job.company}")

        conn.commit()

        print()
        print(f"✅ 已标记 {len(jobs)} 个职位为紧急")
        return True

def reset_all_urgency():
    """重置所有紧急度为0"""
    engine = create_engine(f'sqlite:///{DB_PATH}')

    with engine.connect() as conn:
        result = conn.execute(text("""
            UPDATE jobs
            SET urgency = 0
        """))
        conn.commit()

        print(f"✅ 已重置 {result.rowcount} 个职位的紧急度为 0")

def show_urgency_stats():
    """显示紧急度统计"""
    engine = create_engine(f'sqlite:///{DB_PATH}')

    with engine.connect() as conn:
        stats = conn.execute(text("""
            SELECT urgency, COUNT(*) as count
            FROM jobs
            GROUP BY urgency
            ORDER BY urgency DESC
        """)).fetchall()

        print("📊 紧急程度统计:")
        print("-" * 40)

        urgency_map = {0: "普通", 1: "较急", 2: "紧急", 3: "非常紧急"}
        total = 0

        for row in stats:
            urgency_label = urgency_map.get(row.urgency, str(row.urgency))
            emoji = {1: "🟢", 2: "🟡", 3: "🔴"}.get(row.urgency, "")
            print(f"{emoji} {urgency_label}: {row.count} 个")
            total += row.count

        print(f"\n总计: {total} 个职位")

def main():
    parser = argparse.ArgumentParser(description='标记职位紧急程度')
    parser.add_argument('--list', action='store_true', help='列出所有职位')
    parser.add_argument('--mark', nargs=2, metavar=('ID', 'LEVEL'), help='标记单个职位')
    parser.add_argument('--auto', nargs='?', const=5, type=int, metavar='COUNT', help='自动标记最近的职位')
    parser.add_argument('--reset', action='store_true', help='重置所有紧急度为0')
    parser.add_argument('--stats', action='store_true', help='显示紧急度统计')

    args = parser.parse_args()

    if args.list:
        list_jobs()
    elif args.mark:
        job_id = int(args.mark[0])
        urgency = int(args.mark[1])
        mark_job(job_id, urgency)
    elif args.auto is not None:
        count = args.auto
        mark_recent_jobs(count)
        print()
        show_urgency_stats()
    elif args.reset:
        reset_all_urgency()
    elif args.stats:
        show_urgency_stats()
    else:
        # 默认显示统计和列表
        show_urgency_stats()
        print()
        list_jobs(limit=10)

if __name__ == "__main__":
    main()
