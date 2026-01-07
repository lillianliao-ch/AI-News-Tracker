#!/usr/bin/env python3
"""
检查数据库连接和数据统计
"""
import os
import sys
from sqlalchemy import inspect, text

# 导入数据库配置
from database import engine, db_path, DATABASE_URL, SessionLocal, Candidate, Job, MatchRecord

print("=" * 60)
print("📦 数据库连接信息")
print("=" * 60)
print(f"数据库路径: {db_path}")
print(f"数据库 URL: {DATABASE_URL}")
print(f"文件大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
print(f"最后修改: {os.path.getmtime(db_path)}")

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"\n❌ 数据库文件不存在！")
    sys.exit(1)

# 连接数据库
session = SessionLocal()

try:
    # 检查表结构
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📊 数据表: {', '.join(tables)}")

    # 统计数据
    print(f"\n{'='*60}")
    print("📊 数据统计")
    print(f"{'='*60}")

    candidate_count = session.query(Candidate).count()
    job_count = session.query(Job).count()
    match_count = session.query(MatchRecord).count()

    print(f"候选人数量: {candidate_count}")
    print(f"职位数量: {job_count}")
    print(f"匹配记录: {match_count}")

    # 检查最新数据
    if candidate_count > 0:
        latest_candidate = session.query(Candidate).order_by(Candidate.created_at.desc()).first()
        print(f"\n最新候选人:")
        print(f"  - 姓名: {latest_candidate.name}")
        print(f"  - 公司: {latest_candidate.current_company}")
        print(f"  - 职位: {latest_candidate.current_title}")
        print(f"  - 创建时间: {latest_candidate.created_at}")

    if job_count > 0:
        latest_job = session.query(Job).order_by(Job.created_at.desc()).first()
        print(f"\n最新职位:")
        print(f"  - 标题: {latest_job.title}")
        print(f"  - 公司: {latest_job.company}")
        print(f"  - 创建时间: {latest_job.created_at}")

    # 检查其他数据库文件
    print(f"\n{'='*60}")
    print("🗂️  其他数据库文件")
    print(f"{'='*60}")

    data_dir = os.path.dirname(db_path)
    for file in os.listdir(data_dir):
        if file.endswith('.db') or file.endswith('.sqlite'):
            file_path = os.path.join(data_dir, file)
            size = os.path.getsize(file_path) / 1024 / 1024
            is_current = " ← 当前连接" if file_path == db_path else ""
            print(f"  {file}: {size:.2f} MB{is_current}")

except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
finally:
    session.close()

print(f"\n{'='*60}\n")
