#!/usr/bin/env python3
"""
检查所有可能的数据库文件
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime

all_dbs = [
    ("personal-ai-headhunter/data/headhunter.db", "当前开发环境"),
    ("personal-ai-headhunter/data/headhunter_dev.db", "开发环境备份"),
    ("personal-ai-headhunter/data/headhunter_prod.db", "生产环境(只有职位)"),
    ("personal-ai-headhunter-prod/data/headhunter.db", "生产环境副本"),
    ("临时文件夹/instance/headhunter_alliance.db", "联盟数据库")
]

print("=" * 80)
print("🔍 检查所有数据库文件")
print("=" * 80)

for db_path_str, description in all_dbs:
    db_path = Path(db_path_str)

    if not db_path.exists():
        print(f"\n❌ {db_path_str}")
        print(f"   描述: {description}")
        print(f"   状态: 文件不存在")
        continue

    # 获取文件信息
    size_mb = db_path.stat().st_size / 1024 / 1024
    mtime = datetime.fromtimestamp(db_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')

    print(f"\n{'='*80}")
    print(f"📦 {db_path_str}")
    print(f"   描述: {description}")
    print(f"   大小: {size_mb:.2f} MB")
    print(f"   修改时间: {mtime}")

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        print(f"\n   📊 数据统计:")

        # 检查 candidates 表
        if 'candidates' in tables:
            cursor.execute("SELECT COUNT(*) FROM candidates")
            candidate_count = cursor.fetchone()[0]
            print(f"      ✅ 候选人: {candidate_count}")

            if candidate_count > 0:
                # 获取最新候选人
                cursor.execute("SELECT name, current_company, current_title FROM candidates ORDER BY created_at DESC LIMIT 1")
                latest = cursor.fetchone()
                if latest:
                    print(f"      最新: {latest[0]} - {latest[1]} ({latest[2]})")
        else:
            print(f"      ⚠️  候选人: 无此表")

        # 检查 jobs 表
        if 'jobs' in tables:
            cursor.execute("SELECT COUNT(*) FROM jobs")
            job_count = cursor.fetchone()[0]
            print(f"      职位: {job_count}")

        # 检查 match_records 表
        if 'match_records' in tables:
            cursor.execute("SELECT COUNT(*) FROM match_records")
            match_count = cursor.fetchone()[0]
            print(f"      匹配记录: {match_count}")

        conn.close()

    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")

print(f"\n{'='*80}")
print("\n📝 总结:")
print("=" * 80)

# 找出候选人最多的数据库
max_count = 0
recommended_db = None
recommended_path = None

for db_path_str, _ in all_dbs:
    db_path = Path(db_path_str)
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM candidates")
            count = cursor.fetchone()[0]
            conn.close()

            if count > max_count:
                max_count = count
                recommended_db = db_path_str
                recommended_path = db_path
        except:
            pass

if recommended_db:
    print(f"✅ 候选人最多的数据库: {recommended_db}")
    print(f"   包含 {max_count} 个候选人")
    print(f"\n💡 如需使用此数据库，请设置环境变量:")
    print(f"   export DB_PATH=$(pwd)/{recommended_db}")
    print(f"\n   或创建 .env 文件:")
    print(f"   echo 'DB_PATH={recommended_path}' > personal-ai-headhunter/.env")

print(f"\n{'='*80}\n")
