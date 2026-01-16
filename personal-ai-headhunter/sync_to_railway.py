#!/usr/bin/env python3
"""
增量数据同步脚本：只添加新记录，不删除现有数据
使用方法：DATABASE_URL="postgresql://..." python3 sync_to_railway.py
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

def get_existing_ids(table_name):
    """获取 Railway 数据库中已存在的 ID"""
    with pg_engine.connect() as conn:
        result = conn.execute(text(f"SELECT id FROM {table_name}"))
        return set(row[0] for row in result)

def sync_table(table_name, mode='insert_only'):
    """
    增量同步表
    mode: 
        'insert_only' - 只插入新记录（默认，最安全）
        'upsert' - 插入新记录，更新已存在的记录
    """
    print(f"\n🔄 正在同步 {table_name} (模式: {mode})...")
    
    pg_columns = get_pg_columns(table_name)
    if not pg_columns:
        print(f"   ⚠️ PostgreSQL 中不存在表 {table_name}")
        return
    
    # 获取已存在的 ID
    existing_ids = get_existing_ids(table_name)
    print(f"   Railway 现有记录: {len(existing_ids)}")
    
    sqlite_cur.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cur.fetchall()
    local_columns = [desc[0] for desc in sqlite_cur.description]
    print(f"   本地总记录: {len(rows)}")
    
    common_columns = [c for c in local_columns if c in pg_columns]
    
    new_count = 0
    update_count = 0
    skip_count = 0
    error_count = 0
    
    with pg_engine.connect() as conn:
        for row in rows:
            row_dict = dict(row)
            row_id = row_dict.get('id')
            
            # 检查是否已存在
            if row_id in existing_ids:
                if mode == 'insert_only':
                    skip_count += 1
                    continue
                # upsert 模式：更新现有记录
                # (这里可以扩展实现 UPDATE 逻辑)
            
            # 准备数据
            filtered_dict = {}
            for key in common_columns:
                value = row_dict.get(key)
                if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                    filtered_dict[key] = value
                elif isinstance(value, (dict, list)):
                    filtered_dict[key] = json.dumps(value, ensure_ascii=False)
                else:
                    filtered_dict[key] = value
            
            col_names = ', '.join(filtered_dict.keys())
            placeholders = ', '.join([f':{k}' for k in filtered_dict.keys()])
            insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
            
            try:
                conn.execute(text(insert_sql), filtered_dict)
                new_count += 1
                if new_count % 50 == 0:
                    conn.commit()
                    print(f"   进度: 新增 {new_count}...")
            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    print(f"   ❌ ID {row_id}: {str(e)[:80]}")
        
        conn.commit()
    
    print(f"   ✅ 新增: {new_count}, 跳过: {skip_count}, 错误: {error_count}")
    
    # 重置序列
    if new_count > 0:
        try:
            with pg_engine.connect() as conn:
                result = conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                max_id = result.scalar() or 0
                conn.execute(text(f"SELECT setval('{table_name}_id_seq', {max_id + 1}, false)"))
                conn.commit()
        except:
            pass

print("=" * 50)
print("🚀 开始增量同步（只添加新记录，不删除已有数据）")
print("=" * 50)

sync_table('candidates', mode='insert_only')
sync_table('jobs', mode='insert_only')

print("\n" + "=" * 50)
print("✅ 增量同步完成!")
print("=" * 50)

with pg_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM candidates"))
    print(f"📊 Railway 候选人总数: {result.scalar()}")
    result = conn.execute(text("SELECT COUNT(*) FROM jobs"))
    print(f"📊 Railway 职位总数: {result.scalar()}")

sqlite_conn.close()
