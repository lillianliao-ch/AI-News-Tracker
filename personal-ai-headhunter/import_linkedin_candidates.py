#!/usr/bin/env python3
"""
LinkedIn 候选人数据导入脚本
从 LinkedIn 导出的 Excel 文件导入候选人到数据库
"""

import pandas as pd
import json
import re
import os
import sys
from datetime import datetime

# 添加项目路径
PROJECT_DIR = "/Users/lillianliao/notion_rag/personal-ai-headhunter"
sys.path.insert(0, PROJECT_DIR)

from database import init_db, SessionLocal, Candidate


def parse_work_experiences(work_text):
    """解析 LinkedIn 工作经历文本为 JSON 数组"""
    if pd.isna(work_text) or not work_text:
        return [], '', ''
    
    text = str(work_text).strip()
    experiences = []
    current_company = ''
    current_title = ''
    
    # LinkedIn 格式: "title @ company (date - date · duration); title2 @ company2 ..."
    # 或: "company @ duration; title @ company2 ..."
    entries = re.split(r';\s*', text)
    
    for i, entry in enumerate(entries):
        entry = entry.strip()
        if not entry:
            continue
        
        # 尝试解析 "title @ company (date - date · duration)" 格式
        match = re.match(r'^(.+?)\s*@\s*(.+?)(?:\s*\((.+?)\))?$', entry)
        if match:
            title_or_company = match.group(1).strip()
            company_or_details = match.group(2).strip()
            time_info = match.group(3).strip() if match.group(3) else ''
            
            # 提取时间信息
            time_match = re.search(r'(\d{4}年\d+月\s*-\s*(?:至今|\d{4}年\d+月)?)', company_or_details)
            if time_match:
                time_info = time_match.group(1)
                company_or_details = company_or_details.replace(time_match.group(0), '').strip()
            
            experiences.append({
                "company": company_or_details if company_or_details else title_or_company,
                "title": title_or_company,
                "time": time_info,
                "description": entry[:500]
            })
            
            # 第一条是当前工作
            if i == 0:
                current_company = company_or_details if company_or_details else title_or_company
                current_title = title_or_company
        else:
            # 无法解析的格式，整体作为描述
            experiences.append({
                "company": "",
                "title": "",
                "time": "",
                "description": entry[:500]
            })
    
    return experiences, current_company, current_title


def parse_education_details(edu_text):
    """解析 LinkedIn 教育经历文本为 JSON 数组"""
    if pd.isna(edu_text) or not edu_text:
        return [], '未知'
    
    text = str(edu_text).strip()
    details = []
    highest_level = '未知'
    
    # LinkedIn 格式: "degree，major @ school (year - year); ..."
    entries = re.split(r';\s*', text)
    
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        
        # 尝试解析 "degree，major @ school (year - year)" 格式
        match = re.match(r'^(.+?)\s*@\s*(.+?)(?:\s*\((.+?)\))?$', entry)
        if match:
            degree_major = match.group(1).strip()
            school = match.group(2).strip()
            year = match.group(3).strip() if match.group(3) else ''
            
            # 分离学位和专业
            degree = ''
            major = ''
            if '，' in degree_major:
                parts = degree_major.split('，', 1)
                degree = parts[0].strip()
                major = parts[1].strip() if len(parts) > 1 else ''
            else:
                major = degree_major
            
            details.append({
                "school": school,
                "degree": degree,
                "major": major,
                "year": year
            })
        else:
            details.append({
                "school": entry,
                "degree": "",
                "major": "",
                "year": ""
            })
    
    # 推断最高学历
    combined = text.lower()
    if 'ph.d' in combined or '博士' in combined or 'doctor' in combined:
        highest_level = '博士'
    elif 'master' in combined or '硕士' in combined or 'm.s' in combined or 'm.phil' in combined:
        highest_level = '硕士'
    elif 'bachelor' in combined or '本科' in combined or 'b.s' in combined or 'b.e' in combined:
        highest_level = '本科'
    
    return details, highest_level


def extract_email_from_notes(notes_text):
    """从备注中提取邮箱"""
    if pd.isna(notes_text) or not notes_text:
        return ''
    
    text = str(notes_text)
    # 匹配邮箱格式
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        return email_match.group(0)
    return ''


def extract_location(location_text):
    """提取期望地点"""
    if pd.isna(location_text) or not location_text:
        return ''
    return str(location_text).strip()


def convert_to_candidate(row, source_file):
    """将 Excel 行转换为 Candidate 对象"""
    
    # 姓名（必须有）
    name = str(row.get('姓名', '')).strip()
    if not name or name == 'nan' or name == '':
        return None
    
    # 解析工作经历
    work_text = row.get('工作经历', '')
    work_exps, current_company, current_title = parse_work_experiences(work_text)
    
    # 如果工作经历没解析出公司/职位，尝试从 '职位' 列获取
    position_col = str(row.get('职位', '')).strip() if pd.notna(row.get('职位')) else ''
    if position_col and (not current_title or not current_company):
        # 格式: "Company - title" 或只有 title
        if ' - ' in position_col:
            parts = position_col.split(' - ', 1)
            if not current_company:
                current_company = parts[0].strip()
            if not current_title and len(parts) > 1:
                current_title = parts[1].strip()
        else:
            if not current_title:
                current_title = position_col
    
    # 解析教育经历
    edu_text = row.get('教育经历', '')
    edu_details, education_level = parse_education_details(edu_text)
    
    # 提取邮箱
    notes_text = row.get('备注', '')
    email = extract_email_from_notes(notes_text)
    
    # 地点
    location = extract_location(row.get('位置', ''))
    
    # LinkedIn 链接
    linkedin_url = str(row.get('个人链接', '')).strip() if pd.notna(row.get('个人链接')) else ''
    
    # 简历原文
    raw_resume = f"【职位】{position_col}\n【位置】{location}\n\n【工作经历】\n{work_text}\n\n【教育经历】\n{edu_text}\n\n【备注】\n{notes_text}"
    
    # 备注 (含原始备注)
    notes = f"来源: LinkedIn\n提取时间: {row.get('提取时间', '')}"
    if notes_text:
        notes += f"\n原始备注: {notes_text}"
    
    return Candidate(
        name=name,
        email=email,
        education_level=education_level,
        current_company=current_company,
        current_title=current_title,
        expect_location=location,
        linkedin_url=linkedin_url,
        source_file=source_file,
        raw_resume_text=raw_resume,
        skills=[],  # 将在后续通过AI提取
        education_details=edu_details,
        work_experiences=work_exps,
        notes=notes
    )


def import_linkedin_excel(excel_path, session, dry_run=False):
    """导入 LinkedIn Excel 文件"""
    filename = os.path.basename(excel_path)
    
    print(f"📄 读取文件: {filename}")
    
    df = pd.read_excel(excel_path)
    
    # 过滤掉空列
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
    
    print(f"   共 {len(df)} 行数据")
    print(f"   列: {list(df.columns)}")
    
    imported = 0
    skipped = 0
    duplicates = 0
    
    for idx, row in df.iterrows():
        name = str(row.get('姓名', '')).strip()
        
        # 跳过无效行
        if not name or name == 'nan' or name == '':
            skipped += 1
            continue
        
        # 检查是否已存在（通过姓名查重）
        existing = session.query(Candidate).filter(Candidate.name == name).first()
        if existing:
            duplicates += 1
            print(f"   ⏭️ 跳过重复: {name}")
            continue
        
        # 转换并添加
        candidate = convert_to_candidate(row, filename)
        if candidate:
            if not dry_run:
                session.add(candidate)
            imported += 1
            print(f"   ✅ 导入: {name} - {candidate.current_title} @ {candidate.current_company}")
            
            # 每50条提交一次
            if imported % 50 == 0 and not dry_run:
                session.commit()
                print(f"   ... 已提交 {imported} 条")
        else:
            skipped += 1
    
    if not dry_run:
        session.commit()
    
    return imported, skipped, duplicates


def main():
    import argparse
    parser = argparse.ArgumentParser(description='导入 LinkedIn 候选人数据到数据库')
    parser.add_argument('excel_file', nargs='?', help='要导入的 Excel 文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不实际写入')
    parser.add_argument('--dev', action='store_true', help='使用开发数据库')
    args = parser.parse_args()
    
    # 默认 Excel 文件
    default_excel = '/Users/lillianliao/notion_rag/LinkedIn_2026-01-17-30.xlsx'
    excel_file = args.excel_file if args.excel_file else default_excel
    
    if not os.path.exists(excel_file):
        print(f"❌ 文件不存在: {excel_file}")
        return
    
    # 数据库配置
    if args.dev:
        os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")
        print("⚠️ 使用开发数据库")
    else:
        os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter.db")
        print("📦 使用生产数据库")
    
    print("=" * 60)
    print("🚀 LinkedIn 候选人导入工具")
    print("=" * 60)
    
    if args.dry_run:
        print("⚠️ 模拟模式，不会实际写入数据库")
    
    print(f"\n📂 Excel 文件: {excel_file}")
    
    # 初始化数据库
    init_db()
    session = SessionLocal()
    
    # 导入
    imported, skipped, duplicates = import_linkedin_excel(excel_file, session, args.dry_run)
    
    session.close()
    
    # 汇总
    print("\n" + "=" * 60)
    print("📊 导入汇总")
    print("=" * 60)
    print(f"✅ 成功导入: {imported} 人")
    print(f"⏭️ 跳过（无效数据）: {skipped} 人")
    print(f"🔄 跳过（已存在）: {duplicates} 人")
    
    if args.dry_run:
        print("\n⚠️ 这是模拟运行，未实际写入数据库")
        print("   移除 --dry-run 参数以实际导入")


if __name__ == "__main__":
    main()
