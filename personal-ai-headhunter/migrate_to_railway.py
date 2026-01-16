#!/usr/bin/env python3
"""
数据迁移脚本：从本地 SQLite 迁移到 Railway PostgreSQL (修复版 v4)
保持整数字段为整数，不转换为 boolean
"""

import os
import sys
import sqlite3
import json

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ 请设置 DATABASE_URL 环境变量")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"📦 目标数据库: {DATABASE_URL[:50]}...")

from sqlalchemy import create_engine, text
import psycopg2

LOCAL_DB_PATH = "data/headhunter.db"
sqlite_conn = sqlite3.connect(LOCAL_DB_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cur = sqlite_conn.cursor()

pg_engine = create_engine(DATABASE_URL)

def get_pg_columns(table_name):
    with pg_engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{table_name}'
        """))
        return [row[0] for row in result]

def migrate_table(table_name):
    print(f"\n🔄 正在迁移 {table_name}...")
    
    pg_columns = get_pg_columns(table_name)
    if not pg_columns:
        print(f"   ⚠️ PostgreSQL 中不存在表 {table_name}")
        return
    
    sqlite_cur.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cur.fetchall()
    local_columns = [desc[0] for desc in sqlite_cur.description]
    print(f"   本地记录数: {len(rows)}")
    
    if len(rows) == 0:
        print(f"   ⏭️ 跳过空表")
        return
    
    common_columns = [c for c in local_columns if c in pg_columns]
    print(f"   共同列数: {len(common_columns)}")
    
    success_count = 0
    error_count = 0
    
    with pg_engine.connect() as conn:
        # 清空目标表
        conn.execute(text(f"DELETE FROM {table_name}"))
        conn.commit()
        
        for row in rows:
            row_dict = dict(row)
            filtered_dict = {}
            
            for key in common_columns:
                value = row_dict.get(key)
                
                # 保持原始类型，不做 boolean 转换
                # JSON 字段保持字符串
                if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                    filtered_dict[key] = value  # 保持 JSON 字符串
                elif isinstance(value, (dict, list)):
                    filtered_dict[key] = json.dumps(value, ensure_ascii=False)
                else:
                    # 保持原始值（包括整数 0/1）
                    filtered_dict[key] = value
            
            col_names = ', '.join(filtered_dict.keys())
            placeholders = ', '.join([f':{k}' for k in filtered_dict.keys()])
            insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
            
            try:
                conn.execute(text(insert_sql), filtered_dict)
                success_count += 1
                if success_count % 100 == 0:
                    conn.commit()
                    print(f"   进度: {success_count}/{len(rows)}")
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"   ❌ ID {row_dict.get('id')}: {str(e)[:100]}")
        
        conn.commit()
        print(f"   ✅ 成功: {success_count}, 失败: {error_count}")
        
        # 重置序列
        if 'id' in pg_columns and success_count > 0:
            try:
                result = conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                max_id = result.scalar() or 0
                conn.execute(text(f"SELECT setval('{table_name}_id_seq', {max_id + 1}, false)"))
                conn.commit()
            except:
                pass

print("=" * 50)
print("🚀 开始数据迁移（仅候选人）")
print("=" * 50)

migrate_table('candidates')

print("\n" + "=" * 50)
print("✅ 数据迁移完成!")
print("=" * 50)

with pg_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM candidates"))
    print(f"📊 PostgreSQL 候选人数: {result.scalar()}")
    result = conn.execute(text("SELECT COUNT(*) FROM jobs"))
    print(f"📊 PostgreSQL 职位数: {result.scalar()}")

sqlite_conn.close()
