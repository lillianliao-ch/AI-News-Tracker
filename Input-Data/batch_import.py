#!/usr/bin/env python3
"""
候选人数据批量导入脚本 - 分批处理避免超时
"""

import pandas as pd
import json
import psycopg2
from psycopg2.extras import execute_values
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()
load_dotenv('/Users/lillianliao/notion_rag/headhunter-platform/backend/.env')

BATCH_SIZE = 500  # 每批处理500条记录

def clean_phone_number(phone):
    """清理手机号格式"""
    if pd.isna(phone):
        return None
    phone_str = str(phone).strip()
    phone_clean = ''.join(filter(str.isdigit, phone_str))
    if len(phone_clean) == 11 and phone_clean.startswith('1'):
        return phone_clean
    return None

def create_tags_from_row(row):
    """从Excel行创建tags JSON"""
    tags = {}
    
    # 工作经历
    work_exp = []
    for i in range(1, 4):
        company = row.get(f'工作经历{i}公司')
        position = row.get(f'工作经历{i}职位')
        if not pd.isna(company) or not pd.isna(position):
            exp = {}
            if not pd.isna(company):
                exp['company'] = str(company)
            if not pd.isna(position):
                exp['position'] = str(position)
            work_exp.append(exp)
    
    if work_exp:
        tags['work_experience'] = work_exp
    
    # 教育经历  
    education = []
    for i in range(1, 4):
        school = row.get(f'教育经历{i}学校')
        degree = row.get(f'教育经历{i}学历')
        major = row.get(f'教育经历{i}专业')
        if not pd.isna(school) or not pd.isna(degree) or not pd.isna(major):
            edu = {}
            if not pd.isna(school):
                edu['school'] = str(school)
            if not pd.isna(degree):
                edu['degree'] = str(degree)
            if not pd.isna(major):
                edu['major'] = str(major)
            education.append(edu)
    
    if education:
        tags['education'] = education
    
    # 其他信息
    if not pd.isna(row.get('所在城市')):
        tags['city'] = str(row['所在城市'])
    if not pd.isna(row.get('性别')):
        tags['gender'] = str(row['性别'])
    if not pd.isna(row.get('工作年限')):
        tags['work_years'] = float(row['工作年限'])
    if not pd.isna(row.get('状态')):
        tags['status'] = str(row['状态'])
    
    return json.dumps(tags, ensure_ascii=False) if tags else None

def batch_import():
    """分批导入所有候选人数据"""
    print("🚀 候选人数据批量导入")
    print("=" * 50)
    
    # 读取Excel数据
    print("📂 加载Excel文件...")
    df = pd.read_excel('/Users/lillianliao/notion_rag/candidate 2025-09-26 13_28_27.xls')
    total_records = len(df)
    print(f"✅ 总共 {total_records} 条记录")
    
    # 连接数据库
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 获取管理员ID作为默认维护人
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role = 'platform_admin' LIMIT 1")
    admin_user = cursor.fetchone()
    if not admin_user:
        print("❌ 找不到平台管理员")
        return
    
    admin_id = admin_user[0]
    print(f"👤 默认维护人: {admin_id}")
    
    # 统计信息
    total_imported = 0
    total_skipped = 0
    
    # 分批处理
    for batch_start in range(0, total_records, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_records)
        batch_df = df.iloc[batch_start:batch_end]
        
        print(f"\n📦 处理批次 {batch_start//BATCH_SIZE + 1}: 记录 {batch_start+1}-{batch_end}")
        
        candidates_to_insert = []
        batch_skipped = 0
        
        for index, row in batch_df.iterrows():
            # 验证必要字段
            name = str(row['姓名']).strip() if not pd.isna(row['姓名']) else None
            phone = clean_phone_number(row['手机'])
            
            if not name or not phone:
                batch_skipped += 1
                continue
            
            # 检查重复
            cursor.execute("SELECT id FROM candidates WHERE name = %s AND phone = %s", (name, phone))
            if cursor.fetchone():
                batch_skipped += 1
                continue
            
            # 准备数据
            email = str(row['邮箱']).strip() if not pd.isna(row['邮箱']) else None
            tags = create_tags_from_row(row)
            
            candidate_data = (
                str(uuid.uuid4()),
                name,
                phone,
                email,
                tags,
                admin_id,
                datetime.now(),
                datetime.now()
            )
            
            candidates_to_insert.append(candidate_data)
        
        # 批量插入当前批次
        if candidates_to_insert:
            try:
                insert_query = """
                    INSERT INTO candidates (id, name, phone, email, tags, maintainer_id, created_at, updated_at)
                    VALUES %s
                """
                execute_values(cursor, insert_query, candidates_to_insert)
                conn.commit()
                
                batch_imported = len(candidates_to_insert)
                total_imported += batch_imported
                total_skipped += batch_skipped
                
                print(f"  ✅ 导入: {batch_imported} 条, 跳过: {batch_skipped} 条")
                
            except Exception as e:
                conn.rollback()
                print(f"  ❌ 批次导入失败: {e}")
                break
        else:
            total_skipped += batch_skipped
            print(f"  ⚠️  本批次无有效数据, 跳过: {batch_skipped} 条")
        
        # 短暂暂停避免数据库压力
        if batch_start + BATCH_SIZE < total_records:
            time.sleep(0.1)
    
    # 最终统计
    cursor.execute("SELECT COUNT(*) FROM candidates")
    final_count = cursor.fetchone()[0]
    
    print(f"\n🎉 导入完成!")
    print(f"📊 总导入: {total_imported} 条")
    print(f"⚠️  总跳过: {total_skipped} 条")
    print(f"📈 数据库中候选人总数: {final_count}")
    
    cursor.close()
    conn.close()
    print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    print("⚠️  即将开始完整数据导入，预计需要几分钟时间")
    response = input("确认继续？(y/N): ")
    if response.lower() == 'y':
        batch_import()
    else:
        print("❌ 用户取消导入")