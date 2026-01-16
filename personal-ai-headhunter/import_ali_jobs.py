#!/usr/bin/env python3
"""
Import Ali/Aliyun jobs from CSV files into the headhunter database.
Deduplication: Skip jobs where title already exists in database.
"""

import csv
import sqlite3
import json
import os
import re
from datetime import datetime

# Configuration
DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
CSV_FILES = [
    '/Users/lillianliao/notion_rag/job_aliyun_2026-01-12_102955.csv',
    '/Users/lillianliao/notion_rag/job_ali_2026-01-12_102257.csv',
    '/Users/lillianliao/notion_rag/job_ali_2026-01-12_101346.csv',
]

def parse_experience_years(exp_str):
    """Extract numeric experience years from string like '五年以上', '三年以上'"""
    if not exp_str:
        return None
    
    chinese_num = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
    }
    
    for cn, num in chinese_num.items():
        if cn in exp_str:
            return num
    
    # Try to extract digits
    match = re.search(r'(\d+)', exp_str)
    if match:
        return int(match.group(1))
    
    return None

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
    
    for csv_file in CSV_FILES:
        if not os.path.exists(csv_file):
            print(f"⚠️ 文件不存在: {csv_file}")
            continue
        
        print(f"\n📂 处理文件: {os.path.basename(csv_file)}")
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                title = row.get('职位名称', '').strip()
                if not title:
                    continue
                
                total_processed += 1
                
                # Deduplication check
                if title in existing_titles:
                    print(f"  ⏭️ 跳过 (已存在): {title[:40]}...")
                    total_skipped += 1
                    continue
                
                # Parse fields
                company = row.get('部门', '').strip()
                location = row.get('工作地点', '').strip()
                exp_years = parse_experience_years(row.get('工作年限', ''))
                
                # Combine JD text
                jd_desc = row.get('岗位描述', '').strip()
                jd_req = row.get('岗位要求', '').strip()
                raw_jd_text = f"【岗位职责】\n{jd_desc}\n\n【岗位要求】\n{jd_req}" if jd_desc or jd_req else None
                
                # Store additional fields in detail_fields
                detail_fields = {
                    '学历要求': row.get('学历要求', '').strip(),
                    '岗位层级': row.get('岗位层级', '').strip(),
                    '招聘人数': row.get('招聘人数', '').strip(),
                    'HR': row.get('HR', '').strip(),
                    '发布日期': row.get('发布日期', '').strip(),
                    '有效日期': row.get('有效日期', '').strip(),
                    '职位状态': row.get('职位状态', '').strip(),
                    '职位链接': row.get('职位链接', '').strip(),
                }
                
                # Generate job_code
                cursor.execute("SELECT MAX(CAST(SUBSTR(job_code, 2) AS INTEGER)) FROM jobs WHERE job_code LIKE 'A%'")
                max_code = cursor.fetchone()[0] or 0
                job_code = f"A{max_code + 1}"
                
                # Insert new job
                cursor.execute("""
                    INSERT INTO jobs (
                        title, company, location, raw_jd_text, 
                        required_experience_years, detail_fields, job_code,
                        created_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    title,
                    company,
                    location,
                    raw_jd_text,
                    exp_years,
                    json.dumps(detail_fields, ensure_ascii=False),
                    job_code,
                    datetime.now().isoformat()
                ))
                
                existing_titles.add(title)  # Add to set to prevent duplicates within same run
                total_imported += 1
                print(f"  ✅ 导入: [{job_code}] {title[:40]}...")
    
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
