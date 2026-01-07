#!/usr/bin/env python3
"""
验证数据库配置
模拟应用启动时的数据库连接
"""
import os
from dotenv import load_dotenv

# 加载 .env（这是应用启动时做的第一步）
load_dotenv()

print("=" * 60)
print("🔍 数据库配置验证")
print("=" * 60)

# 检查环境变量
db_path_env = os.getenv("DB_PATH")
print(f"\n📝 .env 文件中的 DB_PATH: {db_path_env}")

# 导入 database 模块
from database import db_path, DATABASE_URL, SessionLocal, Candidate

print(f"\n📦 实际使用的数据库路径:")
print(f"   {db_path}")

# 验证文件存在
import os.path
if os.path.exists(db_path):
    size_mb = os.path.getsize(db_path) / 1024 / 1024
    print(f"\n✅ 数据库文件存在")
    print(f"   大小: {size_mb:.2f} MB")
else:
    print(f"\n❌ 数据库文件不存在！")

# 连接并查询数据
session = SessionLocal()
candidate_count = session.query(Candidate).count()
session.close()

print(f"\n📊 数据统计:")
print(f"   候选人数: {candidate_count}")

# 确认应该连接哪个数据库
if 'headhunter_dev.db' in db_path:
    expected_count = 994  # 导入后的数量
    if candidate_count == expected_count:
        print(f"\n✅ 配置正确！")
        print(f"   正在使用 headhunter_dev.db")
        print(f"   候选人数量符合预期 ({expected_count})")
    else:
        print(f"\n⚠️  候选人数量不符")
        print(f"   期望: {expected_count}")
        print(f"   实际: {candidate_count}")
else:
    print(f"\n❌ 配置错误！")
    print(f"   应该使用 headhunter_dev.db")
    print(f"   实际使用: {db_path}")

print(f"\n{'='*60}\n")
