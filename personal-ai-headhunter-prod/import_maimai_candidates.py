#!/usr/bin/env python3
"""
脉脉候选人数据导入脚本
将清洗后的脉脉CSV数据导入 personal-ai-headhunter 数据库
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

# 设置数据库路径（使用开发库，避免影响生产数据）
os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")

from database import init_db, SessionLocal, Candidate


def extract_company_from_title(title_text):
    """从职位文本中提取公司名"""
    if pd.isna(title_text) or not title_text:
        return ''
    text = str(title_text)
    # 匹配模式: 职位名公司名时间
    patterns = [
        r'(?:工程师|经理|专家|负责人|研发|开发|算法|架构师|总监|Lead)(.+?)(?:\d{4}\.|至今)',
        r'^.+?([^\d]+?)(?:\d{4}\.|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            company = match.group(1).strip()
            company = re.sub(r'\s*\?\s*.+$', '', company)
            if 1 < len(company) < 30:
                return company
    return ''


def extract_position_from_title(title_text):
    """从职位文本中提取职位名"""
    if pd.isna(title_text) or not title_text:
        return ''
    text = str(title_text)
    pos_match = re.match(r'^((?:AI|高级|资深)?(?:算法|研发|开发|产品|架构|技术)?(?:工程师|经理|专家|负责人|总监|Lead)[^\d]{0,10})', text)
    if pos_match:
        return pos_match.group(1).strip()
    return text[:30] if len(text) > 0 else ''


def build_work_experiences(row):
    """构建工作经历 JSON 数组"""
    work_exps = []
    for i in range(1, 7):
        title_col = f'工作{i}-title'
        time_col = f'工作{i}-time_range'
        
        if title_col in row.index:
            title = row.get(title_col, '')
            time_range = row.get(time_col, '')
            
            if title and pd.notna(title) and str(title).strip():
                work_exps.append({
                    "company": extract_company_from_title(title),
                    "title": extract_position_from_title(title),
                    "time": str(time_range) if pd.notna(time_range) else '',
                    "description": str(title)[:500]
                })
    return work_exps


def build_education_details(row):
    """构建教育经历 JSON 数组"""
    edu_details = []
    for i in range(1, 4):
        school_col = f'教育{i}-school'
        major_col = f'教育{i}-major'
        time_col = f'教育{i}-time_range'
        
        if school_col in row.index:
            school = row.get(school_col, '')
            major = row.get(major_col, '')
            time_range = row.get(time_col, '')
            
            if school and pd.notna(school) and str(school).strip():
                edu_details.append({
                    "school": str(school),
                    "degree": row.get('最高学历', '') if '最高学历' in row.index else '',
                    "major": str(major) if pd.notna(major) else '',
                    "year": str(time_range) if pd.notna(time_range) else ''
                })
    return edu_details


def convert_maimai_to_candidate(row, source_file):
    """将脉脉清洗数据行转换为 Candidate 对象"""
    
    # 基础字段
    name = str(row.get('姓名', '')).strip()
    if not name or name == 'nan':
        return None
    
    # 工作年限
    exp_years = row.get('工作年限_推断', row.get('工作年限', 0))
    try:
        exp_years = int(float(exp_years)) if pd.notna(exp_years) else 0
    except:
        exp_years = 0
    
    # 简历全文
    work_text = str(row.get('工作经历', '')) if pd.notna(row.get('工作经历')) else ''
    edu_text = str(row.get('教育经历', '')) if pd.notna(row.get('教育经历')) else ''
    raw_resume = f"【工作经历】\n{work_text}\n\n【教育经历】\n{edu_text}"
    
    # 技能列表
    tech_kw = row.get('技术关键词', '-')
    skills = [str(tech_kw)] if pd.notna(tech_kw) and tech_kw != '-' else []
    
    # 评分备注
    total_score = row.get('总分', 0)
    priority = row.get('优先级', '')
    match_company = row.get('匹配公司', '')
    notes = f"总分:{total_score}, 优先级:{priority}, 匹配公司:{match_company}"
    
    return Candidate(
        name=name,
        experience_years=exp_years,
        education_level=str(row.get('最高学历', '未知')) if pd.notna(row.get('最高学历')) else '未知',
        current_company=str(row.get('当前公司', '')) if pd.notna(row.get('当前公司')) else '',
        current_title=str(row.get('当前职位', '')) if pd.notna(row.get('当前职位')) else '',
        source_file=source_file,
        raw_resume_text=raw_resume,
        skills=skills,
        education_details=build_education_details(row),
        work_experiences=build_work_experiences(row),
        notes=notes
    )


def import_csv_file(csv_path, session, dry_run=False):
    """导入单个 CSV 文件"""
    filename = os.path.basename(csv_path)
    source_name = filename.replace('_清洗版.csv', '').replace('_评分版.csv', '')
    
    # 优先读取清洗版（包含完整信息）
    clean_path = csv_path.replace('_评分版.csv', '_清洗版.csv')
    score_path = csv_path.replace('_清洗版.csv', '_评分版.csv')
    
    # 读取数据
    try:
        if os.path.exists(clean_path):
            clean_df = pd.read_csv(clean_path, encoding='utf-8-sig')
        else:
            clean_df = pd.DataFrame()
        
        if os.path.exists(score_path):
            score_df = pd.read_csv(score_path, encoding='utf-8-sig')
        else:
            score_df = pd.DataFrame()
    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        return 0, 0
    
    # 合并数据（以姓名为键）
    if len(clean_df) > 0 and len(score_df) > 0:
        merged = pd.merge(clean_df, score_df[['姓名', '总分', '技术关键词', '优先级', '匹配公司']], 
                          on='姓名', how='left', suffixes=('', '_score'))
    elif len(clean_df) > 0:
        merged = clean_df
    elif len(score_df) > 0:
        merged = score_df
    else:
        return 0, 0
    
    imported = 0
    skipped = 0
    
    for _, row in merged.iterrows():
        name = str(row.get('姓名', '')).strip()
        
        # 跳过无效或已存在
        if not name or name == 'nan':
            skipped += 1
            continue
        
        # 检查是否已存在
        existing = session.query(Candidate).filter(Candidate.name == name).first()
        if existing:
            skipped += 1
            continue
        
        # 转换并添加
        candidate = convert_maimai_to_candidate(row, source_name)
        if candidate:
            if not dry_run:
                session.add(candidate)
            imported += 1
        else:
            skipped += 1
    
    if not dry_run:
        session.commit()
    
    return imported, skipped


def main():
    import argparse
    parser = argparse.ArgumentParser(description='导入脉脉候选人数据到数据库')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不实际写入')
    parser.add_argument('--dir', default='/Users/lillianliao/notion_rag/cleaned_results', help='清洗数据目录')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 脉脉候选人数据导入工具")
    print("=" * 60)
    
    if args.dry_run:
        print("⚠️ 模拟模式，不会实际写入数据库")
    
    # 初始化数据库
    init_db()
    session = SessionLocal()
    
    # 获取所有清洗版 CSV
    csv_files = []
    for f in os.listdir(args.dir):
        if f.endswith('_清洗版.csv'):
            csv_files.append(os.path.join(args.dir, f))
    
    print(f"\n📂 发现 {len(csv_files)} 个清洗版文件")
    
    total_imported = 0
    total_skipped = 0
    
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        print(f"\n📄 处理: {filename}")
        
        imported, skipped = import_csv_file(csv_path, session, args.dry_run)
        total_imported += imported
        total_skipped += skipped
        
        print(f"   ✅ 导入: {imported}  ⏭️ 跳过: {skipped}")
    
    session.close()
    
    # 汇总
    print("\n" + "=" * 60)
    print("📊 导入汇总")
    print("=" * 60)
    print(f"✅ 成功导入: {total_imported} 人")
    print(f"⏭️ 跳过（已存在/无效）: {total_skipped} 人")
    
    if args.dry_run:
        print("\n⚠️ 这是模拟运行，未实际写入数据库")
        print("   移除 --dry-run 参数以实际导入")


if __name__ == "__main__":
    main()
