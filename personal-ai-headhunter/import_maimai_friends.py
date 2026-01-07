#!/usr/bin/env python3
"""
脉脉好友候选人数据导入脚本
从脉脉好友导出的CSV文件(Friends-脉脉_*.csv)导入候选人到数据库
该格式与清洗版CSV不同，直接从脉脉好友列表导出
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

# 设置数据库路径 - 默认使用开发数据库
os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")

from database import init_db, SessionLocal, Candidate


def extract_company_from_work(work_title):
    """从工作经历文本中提取公司名"""
    if pd.isna(work_title) or not work_title:
        return ''
    text = str(work_title).strip()
    
    # 常见格式: "职位公司名 • 部门时间范围"
    patterns = [
        # 匹配 "职位公司名2024.1-至今" 格式
        r'(?:AI|高级|资深|首席|主任|见习)?(?:算法|研发|开发|产品|架构|技术|数据|运营|市场|销售)?(?:工程师|经理|专家|负责人|总监|Lead|Director|Manager|Intern|实习生)?[\s]*(.+?)(?:\s*•|\s*\d{4}\.|至今|$)',
        # 匹配中间有 • 的格式: 职位公司 • 部门
        r'^[^\•]+([^\d•]+?)(?:\s*•|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # 过滤掉太短或太长的结果
            if 1 < len(company) < 40:
                # 清理公司名末尾的时间信息
                company = re.sub(r'\d{4}.*$', '', company).strip()
                return company
    
    return ''


def extract_position_from_work(work_title):
    """从工作经历文本中提取职位名"""
    if pd.isna(work_title) or not work_title:
        return ''
    text = str(work_title).strip()
    
    # 常见的职位模式
    pos_patterns = [
        r'^((?:AI|高级|资深|首席|主任|见习)?(?:算法|研发|开发|前端|后端|产品|架构|技术|数据|运营|市场|销售|GPU优化|计算机视觉|机器学习|深度学习|NLP|风控|Android|iOS)?(?:工程师|算法|经理|专家|负责人|总监|科学家|Lead|Director|Manager|Researcher|研究员|实习生|CTO|CEO|VP|Staff|Intern))',
    ]
    
    for pattern in pos_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # 如果没匹配到，返回前20个字符
    return text[:20] if len(text) > 0 else ''


def build_work_experiences(row):
    """构建工作经历 JSON 数组"""
    work_exps = []
    
    for i in range(1, 14):  # 最多13个工作经历
        title_col = f'工作{i}-title'
        time_col = f'工作{i}-time_range'
        pos_col = f'工作{i}-position'
        proj_col = f'工作{i}-project_name'
        
        if title_col not in row.index:
            break
            
        title = row.get(title_col, '')
        time_range = row.get(time_col, '')
        position = row.get(pos_col, '')
        
        if pd.notna(title) and str(title).strip():
            title_str = str(title).strip()
            work_exps.append({
                "company": extract_company_from_work(title_str),
                "title": position if pd.notna(position) and position else extract_position_from_work(title_str),
                "time": str(time_range) if pd.notna(time_range) else '',
                "description": title_str[:500]
            })
    
    return work_exps


def build_education_details(row):
    """构建教育经历 JSON 数组"""
    edu_details = []
    
    for i in range(1, 4):  # 最多3个教育经历
        school_col = f'教育{i}-school'
        major_col = f'教育{i}-major'
        time_col = f'教育{i}-time_range'
        
        if school_col not in row.index:
            break
            
        school = row.get(school_col, '')
        major = row.get(major_col, '')
        time_range = row.get(time_col, '')
        
        if pd.notna(school) and str(school).strip():
            edu_details.append({
                "school": str(school).strip(),
                "degree": "",  # CSV中没有单独的学位字段
                "major": str(major).strip() if pd.notna(major) else '',
                "year": str(time_range).strip() if pd.notna(time_range) else ''
            })
    
    return edu_details


def infer_education_level(edu_details, edu_text):
    """从教育经历推断最高学历"""
    combined = str(edu_text) if edu_text else ""
    for edu in edu_details:
        combined += str(edu.get('school', '')) + str(edu.get('major', ''))
    
    if '博士' in combined:
        return '博士'
    elif '硕士' in combined or 'Master' in combined:
        return '硕士'
    elif '本科' in combined or 'Bachelor' in combined:
        return '本科'
    elif '专科' in combined or '大专' in combined:
        return '专科'
    return '未知'


def convert_to_candidate(row, source_file):
    """将CSV行转换为 Candidate 对象"""
    
    # 姓名（必须有）
    name = str(row.get('姓名', '')).strip()
    if not name or name == 'nan' or name == '':
        return None
    
    # 工作年限
    exp_years = row.get('工作年限', 0)
    try:
        exp_years = int(float(exp_years)) if pd.notna(exp_years) and exp_years != '' else 0
    except:
        exp_years = 0
    
    # 活跃状态
    activity = str(row.get('活跃状态', '')) if pd.notna(row.get('活跃状态')) else ''
    
    # 构建工作经历和教育经历
    work_exps = build_work_experiences(row)
    edu_details = build_education_details(row)
    
    # 获取当前公司和职位（从第一份工作经历）
    current_company = ''
    current_title = ''
    if work_exps:
        current_company = work_exps[0].get('company', '')
        current_title = work_exps[0].get('title', '')
    
    # 简历原文
    work_text = str(row.get('工作经历', '')) if pd.notna(row.get('工作经历')) else ''
    edu_text = str(row.get('教育经历', '')) if pd.notna(row.get('教育经历')) else ''
    raw_resume = f"【工作经历】\n{work_text}\n\n【教育经历】\n{edu_text}"
    
    # 推断学历
    education_level = infer_education_level(edu_details, edu_text)
    
    # 简历链接
    resume_link = str(row.get('简历链接', '')) if pd.notna(row.get('简历链接')) else ''
    
    # 来源
    source = str(row.get('简历来源', 'maimai')) if pd.notna(row.get('简历来源')) else 'maimai'
    
    # 备注
    notes = f"活跃状态: {activity}"
    if resume_link:
        notes += f"\n脉脉链接: {resume_link}"
    
    return Candidate(
        name=name,
        experience_years=exp_years,
        education_level=education_level,
        current_company=current_company,
        current_title=current_title,
        source_file=source,
        raw_resume_text=raw_resume,
        skills=[],  # 将在后续通过AI提取
        education_details=edu_details,
        work_experiences=work_exps,
        notes=notes
    )


def import_friends_csv(csv_path, session, dry_run=False):
    """导入好友CSV文件"""
    filename = os.path.basename(csv_path)
    
    print(f"📄 读取文件: {filename}")
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_path, encoding='gbk')
    
    print(f"   共 {len(df)} 行数据")
    
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
            continue
        
        # 转换并添加
        candidate = convert_to_candidate(row, filename)
        if candidate:
            if not dry_run:
                session.add(candidate)
            imported += 1
            
            # 每50条提交一次，避免内存过大
            if imported % 50 == 0 and not dry_run:
                session.commit()
                print(f"   ... 已导入 {imported} 条")
        else:
            skipped += 1
    
    if not dry_run:
        session.commit()
    
    return imported, skipped, duplicates


def main():
    import argparse
    parser = argparse.ArgumentParser(description='导入脉脉好友候选人数据到数据库')
    parser.add_argument('csv_file', nargs='?', help='要导入的CSV文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不实际写入')
    parser.add_argument('--dev', action='store_true', help='使用开发数据库')
    args = parser.parse_args()
    
    # 默认CSV文件
    default_csv = '/Users/lillianliao/notion_rag/Friends-脉脉_2026-01-05.csv'
    csv_file = args.csv_file if args.csv_file else default_csv
    
    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在: {csv_file}")
        return
    
    # 如果指定开发模式，使用开发数据库
    if args.dev:
        os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")
        print("⚠️ 使用开发数据库")
    
    print("=" * 60)
    print("🚀 脉脉好友候选人导入工具")
    print("=" * 60)
    
    if args.dry_run:
        print("⚠️ 模拟模式，不会实际写入数据库")
    
    print(f"\n📂 CSV文件: {csv_file}")
    
    # 初始化数据库
    init_db()
    session = SessionLocal()
    
    # 导入
    imported, skipped, duplicates = import_friends_csv(csv_file, session, args.dry_run)
    
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
