#!/usr/bin/env python3
"""
检查所有数据库文件的候选人数量
"""
import os
import sqlite3
from pathlib import Path

data_dir = Path("personal-ai-headhunter/data")

print("=" * 80)
print("🔍 检查所有数据库文件")
print("=" * 80)

dbs = [
    ("headhunter.db", "默认数据库 (当前连接)"),
    ("headhunter_dev.db", "开发数据库"),
    ("headhunter_prod.db", "生产数据库")
]

for db_file, description in dbs:
    db_path = data_dir / db_file

    if not db_path.exists():
        print(f"\n❌ {db_file} 不存在")
        continue

    # 获取文件信息
    size_mb = db_path.stat().st_size / 1024 / 1024
    mtime = db_path.stat().st_mtime

    print(f"\n{'='*80}")
    print(f"📦 {db_file}")
    print(f"   描述: {description}")
    print(f"   大小: {size_mb:.2f} MB")
    print(f"   修改时间: {mtime}")

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"\n   📊 数据统计:")

        # 检查 candidates 表
        if ('candidates',) in tables:
            cursor.execute("SELECT COUNT(*) FROM candidates")
            candidate_count = cursor.fetchone()[0]
            print(f"      候选人: {candidate_count}")

            # 获取最新候选人
            cursor.execute("SELECT name, current_company, current_title FROM candidates ORDER BY created_at DESC LIMIT 1")
            latest = cursor.fetchone()
            if latest:
                print(f"      最新: {latest[0]} - {latest[1]} ({latest[2]})")
        else:
            print(f"      候选人: 无此表")

        # 检查 jobs 表
        if ('jobs',) in tables:
            cursor.execute("SELECT COUNT(*) FROM jobs")
            job_count = cursor.fetchone()[0]
            print(f"      职位: {job_count}")
        else:
            print(f"      职位: 无此表")

        # 检查 match_records 表
        if ('match_records',) in tables:
            cursor.execute("SELECT COUNT(*) FROM match_records")
            match_count = cursor.fetchone()[0]
            print(f"      匹配记录: {match_count}")
        else:
            print(f"      匹配记录: 无此表")

        conn.close()

    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")

print(f"\n{'='*80}")
print("\n📝 建议:")
print("=" * 80)

# 找出候选人最多的数据库
max_count = 0
recommended_db = None

for db_file, _ in dbs:
    db_path = data_dir / db_file
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM candidates")
            count = cursor.fetchone()[0]
            conn.close()

            if count > max_count:
                max_count = count
                recommended_db = db_file
        except:
            pass

if recommended_db:
    print(f"✅ 推荐使用: {recommended_db} (包含 {max_count} 个候选人)")
    print(f"\n如需切换数据库，可以设置环境变量:")
    print(f"   export DB_PATH=personal-ai-headhunter/data/{recommended_db}")

print(f"\n{'='*80}\n")
