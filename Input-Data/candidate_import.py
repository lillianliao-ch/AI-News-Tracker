#!/usr/bin/env python3
"""
候选人数据导入脚本
一次性将Excel候选人数据导入猎头协作平台
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

def load_excel_data(file_path):
    """加载Excel数据"""
    print(f"📂 加载Excel文件: {file_path}")
    df = pd.read_excel(file_path)
    print(f"✅ 成功加载 {len(df)} 条记录")
    return df

def clean_phone_number(phone):
    """清理手机号格式"""
    if pd.isna(phone):
        return None
    phone_str = str(phone).strip()
    # 移除非数字字符
    phone_clean = ''.join(filter(str.isdigit, phone_str))
    # 验证手机号长度
    if len(phone_clean) == 11 and phone_clean.startswith('1'):
        return phone_clean
    return None

def get_maintainer_id(db_conn, owner_name):
    """根据拥有者姓名获取maintainer_id"""
    if pd.isna(owner_name):
        return None
    
    cursor = db_conn.cursor()
    # 简单匹配用户名
    cursor.execute("""
        SELECT id FROM users 
        WHERE username ILIKE %s 
        LIMIT 1
    """, (f"%{owner_name}%",))
    
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return result[0]
    else:
        # 如果找不到，返回默认的admin用户ID
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT id FROM users 
            WHERE role = 'platform_admin' 
            LIMIT 1
        """)
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

def create_tags_from_excel_row(row):
    """从Excel行数据创建tags JSON"""
    tags = {}
    
    # 工作经历
    work_experience = []
    for i in range(1, 4):
        company_col = f'工作经历{i}公司'
        position_col = f'工作经历{i}职位'
        if not pd.isna(row.get(company_col)) or not pd.isna(row.get(position_col)):
            work_exp = {}
            if not pd.isna(row.get(company_col)):
                work_exp['company'] = str(row[company_col])
            if not pd.isna(row.get(position_col)):
                work_exp['position'] = str(row[position_col])
            work_experience.append(work_exp)
    
    if work_experience:
        tags['work_experience'] = work_experience
    
    # 教育经历
    education = []
    for i in range(1, 4):
        school_col = f'教育经历{i}学校'
        degree_col = f'教育经历{i}学历'
        major_col = f'教育经历{i}专业'
        if not pd.isna(row.get(school_col)) or not pd.isna(row.get(degree_col)) or not pd.isna(row.get(major_col)):
            edu = {}
            if not pd.isna(row.get(school_col)):
                edu['school'] = str(row[school_col])
            if not pd.isna(row.get(degree_col)):
                edu['degree'] = str(row[degree_col])
            if not pd.isna(row.get(major_col)):
                edu['major'] = str(row[major_col])
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
    if not pd.isna(row.get('备注')) and str(row['备注']).strip():
        tags['notes'] = str(row['备注'])
    
    return json.dumps(tags, ensure_ascii=False) if tags else None

def connect_to_database():
    """连接数据库"""
    try:
        # 使用平台的数据库连接配置
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:headhunter_pass@localhost:5432/headhunter_platform')
        conn = psycopg2.connect(database_url)
        print("✅ 数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def import_candidates(df, db_conn):
    """导入候选人数据"""
    print("🚀 开始导入候选人数据...")
    
    # 数据清洗和准备
    candidates_to_insert = []
    skipped_records = []
    
    for index, row in df.iterrows():
        # 验证必要字段
        name = str(row['姓名']).strip() if not pd.isna(row['姓名']) else None
        phone = clean_phone_number(row['手机'])
        
        if not name:
            skipped_records.append(f"第{index+1}行: 姓名为空")
            continue
        
        if not phone:
            skipped_records.append(f"第{index+1}行: 手机号无效 ({row['手机']})")
            continue
        
        # 检查是否已存在
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT id FROM candidates 
            WHERE name = %s AND phone = %s
        """, (name, phone))
        
        if cursor.fetchone():
            skipped_records.append(f"第{index+1}行: 候选人已存在 ({name}, {phone})")
            cursor.close()
            continue
        cursor.close()
        
        # 获取maintainer_id
        maintainer_id = get_maintainer_id(db_conn, row.get('拥有者'))
        if not maintainer_id:
            skipped_records.append(f"第{index+1}行: 无法确定维护人")
            continue
        
        # 准备数据
        email = str(row['邮箱']).strip() if not pd.isna(row['邮箱']) else None
        tags = create_tags_from_excel_row(row)
        
        candidate_data = (
            str(uuid.uuid4()),  # id
            name,               # name
            phone,              # phone
            email,              # email
            tags,               # tags (JSON)
            maintainer_id,      # maintainer_id
            datetime.now(),     # created_at
            datetime.now()      # updated_at
        )
        
        candidates_to_insert.append(candidate_data)
    
    # 批量插入
    if candidates_to_insert:
        cursor = db_conn.cursor()
        insert_query = """
            INSERT INTO candidates (id, name, phone, email, tags, maintainer_id, created_at, updated_at)
            VALUES %s
        """
        
        try:
            execute_values(cursor, insert_query, candidates_to_insert)
            db_conn.commit()
            print(f"✅ 成功导入 {len(candidates_to_insert)} 条候选人记录")
        except Exception as e:
            db_conn.rollback()
            print(f"❌ 批量插入失败: {e}")
            return False
        finally:
            cursor.close()
    
    # 输出跳过的记录
    if skipped_records:
        print(f"\n⚠️  跳过 {len(skipped_records)} 条记录:")
        for record in skipped_records[:10]:  # 只显示前10条
            print(f"  - {record}")
        if len(skipped_records) > 10:
            print(f"  ... 还有 {len(skipped_records) - 10} 条")
    
    return True

def main():
    """主函数"""
    excel_file = '/Users/lillianliao/notion_rag/candidate 2025-09-26 13_28_27.xls'
    
    print("🎯 候选人数据导入工具")
    print("=" * 50)
    
    # 加载数据
    df = load_excel_data(excel_file)
    
    # 连接数据库
    db_conn = connect_to_database()
    if not db_conn:
        return
    
    try:
        # 导入数据
        success = import_candidates(df, db_conn)
        
        if success:
            print("\n🎉 数据导入完成!")
        else:
            print("\n💥 数据导入失败!")
            
    finally:
        db_conn.close()
        print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    main()