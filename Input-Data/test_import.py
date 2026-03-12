#!/usr/bin/env python3
"""
候选人数据导入测试脚本 - 仅导入前10条记录
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

def test_import():
    """测试导入前10条记录"""
    print("🧪 候选人数据导入测试")
    print("=" * 40)
    
    # 读取Excel前10条
    df = pd.read_excel('/Users/lillianliao/notion_rag/candidate 2025-09-26 13_28_27.xls')
    test_df = df.head(10)
    print(f"📂 加载测试数据: {len(test_df)} 条记录")
    
    # 连接数据库
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 获取默认维护人
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role = 'platform_admin' LIMIT 1")
    admin_user = cursor.fetchone()
    if not admin_user:
        print("❌ 找不到平台管理员")
        return
    
    admin_id = admin_user[0]
    print(f"👤 使用默认维护人: {admin_id}")
    
    # 准备测试数据
    candidates_to_insert = []
    for index, row in test_df.iterrows():
        name = str(row['姓名']).strip() if not pd.isna(row['姓名']) else None
        phone_raw = row['手机']
        
        if not name:
            print(f"⚠️  跳过第{index+1}行: 姓名为空")
            continue
            
        if pd.isna(phone_raw):
            print(f"⚠️  跳过第{index+1}行: 手机号为空")
            continue
            
        # 清理手机号
        phone = ''.join(filter(str.isdigit, str(phone_raw)))
        if len(phone) != 11 or not phone.startswith('1'):
            print(f"⚠️  跳过第{index+1}行: 手机号格式错误 ({phone_raw})")
            continue
        
        # 检查重复
        cursor.execute("SELECT id FROM candidates WHERE name = %s AND phone = %s", (name, phone))
        if cursor.fetchone():
            print(f"⚠️  跳过第{index+1}行: 候选人已存在 ({name})")
            continue
        
        # 准备数据
        email = str(row['邮箱']).strip() if not pd.isna(row['邮箱']) else None
        
        # 创建tags
        tags = {}
        if not pd.isna(row.get('工作经历1公司')):
            tags['work_company'] = str(row['工作经历1公司'])
        if not pd.isna(row.get('工作经历1职位')):
            tags['work_position'] = str(row['工作经历1职位'])
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
        print(f"✅ 准备导入: {name} ({phone})")
    
    # 执行导入
    if candidates_to_insert:
        try:
            insert_query = """
                INSERT INTO candidates (id, name, phone, email, tags, maintainer_id, created_at, updated_at)
                VALUES %s
            """
            execute_values(cursor, insert_query, candidates_to_insert)
            conn.commit()
            print(f"\n🎉 成功导入 {len(candidates_to_insert)} 条记录!")
            
            # 验证导入结果
            cursor.execute("SELECT COUNT(*) FROM candidates")
            total_count = cursor.fetchone()[0]
            print(f"📊 数据库中现有候选人总数: {total_count}")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 导入失败: {e}")
    else:
        print("❌ 没有有效数据可导入")
    
    cursor.close()
    conn.close()
    print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    test_import()