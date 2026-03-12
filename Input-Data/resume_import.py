#!/usr/bin/env python3
"""
续导未完成的候选人数据
"""

import pandas as pd
import json
import psycopg2
from psycopg2.extras import execute_values
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
load_dotenv('/Users/lillianliao/notion_rag/headhunter-platform/backend/.env')

def resume_import():
    """继续导入剩余数据，改进重复检查逻辑"""
    print("🔄 继续导入剩余候选人数据")
    print("=" * 40)
    
    # 连接数据库
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 获取已存在的候选人组合
    cursor = conn.cursor()
    cursor.execute("SELECT name, phone FROM candidates")
    existing_candidates = set(cursor.fetchall())
    print(f"📊 已存在候选人: {len(existing_candidates)} 个")
    
    # 读取Excel数据
    df = pd.read_excel('/Users/lillianliao/notion_rag/candidate 2025-09-26 13_28_27.xls')
    print(f"📂 Excel总记录: {len(df)} 条")
    
    # 获取管理员ID
    cursor.execute("SELECT id FROM users WHERE role = 'platform_admin' LIMIT 1")
    admin_id = cursor.fetchone()[0]
    
    # 从第6000条开始继续处理
    start_index = 6000
    candidates_to_insert = []
    skipped = 0
    
    for index, row in df.iloc[start_index:].iterrows():
        name = str(row['姓名']).strip() if not pd.isna(row['姓名']) else None
        phone_raw = row['手机']
        
        if not name or pd.isna(phone_raw):
            skipped += 1
            continue
        
        # 清理手机号
        phone = ''.join(filter(str.isdigit, str(phone_raw)))
        if len(phone) != 11 or not phone.startswith('1'):
            skipped += 1
            continue
        
        # 检查是否已存在
        if (name, phone) in existing_candidates:
            skipped += 1
            continue
        
        # 准备数据
        email = str(row['邮箱']).strip() if not pd.isna(row['邮箱']) else None
        
        # 创建简化的tags
        tags = {}
        if not pd.isna(row.get('工作经历1公司')):
            tags['company'] = str(row['工作经历1公司'])
        if not pd.isna(row.get('工作经历1职位')):
            tags['position'] = str(row['工作经历1职位'])
        if not pd.isna(row.get('所在城市')):
            tags['city'] = str(row['所在城市'])
        
        tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
        
        candidate_data = (
            str(uuid.uuid4()),
            name,
            phone,
            email,
            tags_json,
            admin_id,
            datetime.now(),
            datetime.now()
        )
        
        candidates_to_insert.append(candidate_data)
        existing_candidates.add((name, phone))  # 添加到已存在集合
        
        # 每1000条批量插入一次
        if len(candidates_to_insert) >= 1000:
            try:
                insert_query = """
                    INSERT INTO candidates (id, name, phone, email, tags, maintainer_id, created_at, updated_at)
                    VALUES %s
                """
                execute_values(cursor, insert_query, candidates_to_insert)
                conn.commit()
                print(f"✅ 已导入: {len(candidates_to_insert)} 条")
                candidates_to_insert = []
            except Exception as e:
                print(f"❌ 导入错误: {e}")
                conn.rollback()
                break
    
    # 导入剩余记录
    if candidates_to_insert:
        try:
            insert_query = """
                INSERT INTO candidates (id, name, phone, email, tags, maintainer_id, created_at, updated_at)
                VALUES %s
            """
            execute_values(cursor, insert_query, candidates_to_insert)
            conn.commit()
            print(f"✅ 最后导入: {len(candidates_to_insert)} 条")
        except Exception as e:
            print(f"❌ 最后批次错误: {e}")
            conn.rollback()
    
    # 最终统计
    cursor.execute("SELECT COUNT(*) FROM candidates")
    final_count = cursor.fetchone()[0]
    
    print(f"\n🎉 续导完成!")
    print(f"📈 数据库候选人总数: {final_count}")
    print(f"⚠️  跳过记录: {skipped}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    resume_import()