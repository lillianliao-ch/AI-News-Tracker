#!/usr/bin/env python3
"""
Import JD (Job Descriptions) from CSV/Excel files into the headhunter database.
Deduplication: Skip jobs where title already exists in database.
Supports: Ali, Feishu, and other platform job files.
"""

import csv
import sqlite3
import json
import os
import re
from datetime import datetime

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("⚠️ pandas not installed, Excel files will be skipped")

# Configuration
DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
DATA_DIR = '/Users/lillianliao/notion_rag/数据输入'

# Files to import (新的3个文件)
FILES_TO_IMPORT = [
    'job_ali_2026-02-04_112043.xlsx',
    'job_feishu_2026-02-04_104144.csv',
    'job_feishu_2026-02-04_103644.csv',
]

def parse_experience_years(exp_str):
    """Extract numeric experience years from string like '五年以上', '三年以上', '3-5年'"""
    if not exp_str:
        return None
    
    exp_str = str(exp_str).strip()
    if exp_str in ['--', '-', '不限', '无要求', '']:
        return None
    
    chinese_num = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
    }
    
    for cn, num in chinese_num.items():
        if cn in exp_str:
            return num
    
    # Try to extract digits (e.g., "3-5年" -> 3)
    match = re.search(r'(\d+)', exp_str)
    if match:
        return int(match.group(1))
    
    return None

def determine_job_code_prefix(filename):
    """Determine job code prefix based on filename"""
    filename_lower = filename.lower()
    if 'ali' in filename_lower or 'aliyun' in filename_lower:
        return 'A'  # Alibaba/Aliyun
    elif 'feishu' in filename_lower or 'bytedance' in filename_lower:
        return 'F'  # Feishu/ByteDance
    elif 'xiaohongshu' in filename_lower:
        return 'X'  # Xiaohongshu
    else:
        return 'J'  # Generic Job

def read_file(filepath):
    """Read CSV or Excel file and return list of dicts"""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.xlsx' or ext == '.xls':
        if not HAS_PANDAS:
            print(f"  ⚠️ 跳过Excel文件 (需要pandas): {filepath}")
            return []
        df = pd.read_excel(filepath)
        # Convert NaN to empty string
        df = df.fillna('')
        return df.to_dict('records')
    elif ext == '.csv':
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        print(f"  ⚠️ 不支持的文件类型: {ext}")
        return []

def import_jobs():
    """Main import function"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing job titles for deduplication
    cursor.execute("SELECT title FROM jobs")
    existing_titles = set(row[0] for row in cursor.fetchall())
    print(f"📊 现有职位数: {len(existing_titles)}")
    
    total_processed = 0
    total_skipped = 0
    total_imported = 0
    
    for filename in FILES_TO_IMPORT:
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"⚠️ 文件不存在: {filepath}")
            continue
        
        print(f"\n📂 处理文件: {filename}")
        
        rows = read_file(filepath)
        if not rows:
            continue
        
        prefix = determine_job_code_prefix(filename)
        
        for row in rows:
            title = str(row.get('职位名称', '')).strip()
            if not title:
                continue
            
            total_processed += 1
            
            # Deduplication check
            if title in existing_titles:
                print(f"  ⏭️ 跳过 (已存在): {title[:40]}...")
                total_skipped += 1
                continue
            
            # Parse fields
            company = str(row.get('公司', '') or row.get('部门', '')).strip()
            department = str(row.get('部门', '')).strip()
            location = str(row.get('工作地点', '')).strip()
            exp_years = parse_experience_years(row.get('工作年限', ''))
            
            # Combine JD text
            jd_desc = str(row.get('岗位描述', '')).strip()
            jd_req = str(row.get('岗位要求', '')).strip()
            raw_jd_text = f"【岗位职责】\n{jd_desc}\n\n【岗位要求】\n{jd_req}" if jd_desc or jd_req else None
            
            # Store additional fields in detail_fields
            detail_fields = {
                '公司': company,
                '部门': department,
                '学历要求': str(row.get('学历要求', '')).strip(),
                '岗位层级': str(row.get('岗位层级', '')).strip(),
                '招聘人数': str(row.get('招聘人数', '')).strip(),
                'HR': str(row.get('HR', '')).strip(),
                '发布日期': str(row.get('发布日期', '')).strip(),
                '更新日期': str(row.get('更新日期', '')).strip(),
                '有效日期': str(row.get('有效日期', '')).strip(),
                '职位状态': str(row.get('职位状态', '')).strip(),
                '职位链接': str(row.get('职位链接', '')).strip(),
            }
            
            # Remove empty fields
            detail_fields = {k: v for k, v in detail_fields.items() if v and v != '--'}
            
            # Generate job_code
            cursor.execute(f"SELECT MAX(CAST(SUBSTR(job_code, 2) AS INTEGER)) FROM jobs WHERE job_code LIKE '{prefix}%'")
            max_code = cursor.fetchone()[0] or 0
            job_code = f"{prefix}{max_code + 1}"
            
            # Insert new job
            cursor.execute("""
                INSERT INTO jobs (
                    title, company, location, raw_jd_text, 
                    required_experience_years, detail_fields, job_code,
                    created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                title,
                company or department,
                location,
                raw_jd_text,
                exp_years,
                json.dumps(detail_fields, ensure_ascii=False),
                job_code,
                datetime.now().isoformat()
            ))
            
            existing_titles.add(title)  # Add to set to prevent duplicates within same run
            total_imported += 1
            print(f"  ✅ 导入: [{job_code}] {title[:50]}...")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"📊 导入统计:")
    print(f"   处理总数: {total_processed}")
    print(f"   跳过 (已存在): {total_skipped}")
    print(f"   新增导入: {total_imported}")
    print(f"{'='*50}")

if __name__ == '__main__':
    import_jobs()
