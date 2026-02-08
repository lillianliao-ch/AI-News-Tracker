#!/usr/bin/env python3
"""
南京大学校友数据导入脚本
将清洗后的南京大学校友 CSV 数据导入 personal-ai-headhunter 数据库

使用方法:
  python import_nju_alumni.py                    # 导入到开发库
  python import_nju_alumni.py --prod             # 导入到生产库
  python import_nju_alumni.py --dry-run          # 模拟运行
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

# 默认使用开发库
os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")


def extract_company_from_title(title_text):
    """从职位文本中提取公司名"""
    if pd.isna(title_text) or not title_text:
        return ''
    text = str(title_text)
    
    # 匹配模式: 职位名公司名时间
    patterns = [
        r'(?:工程师|经理|专家|负责人|研发|开发|算法|架构师|总监|实习生|Lead|infra)(.+?)(?:\d{4}\.|至今|\()',
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
    
    pos_match = re.match(
        r'^((?:AI|高级|资深|主任)?(?:算法|前端|后端|研发|开发|产品|架构|技术|数据|软件|硬件|视觉)?'
        r'(?:工程师|经理|专家|负责人|总监|实习生|科学家|分析师|Lead|infra|操作工)[^\d]{0,10})', 
        text
    )
    if pos_match:
        return pos_match.group(1).strip()
    return text[:30] if len(text) > 0 else ''


def infer_education_level(edu_text, degree_text):
    """推断最高学历"""
    text = f"{edu_text} {degree_text}"
    if '博士' in text:
        return '博士'
    elif '硕士' in text:
        return '硕士'
    elif '本科' in text or '学士' in text:
        return '本科'
    elif '专科' in text or '大专' in text:
        return '专科'
    return '未知'


def build_education_details_from_row(row, original_row):
    """从原始行构建教育经历 JSON"""
    edu_details = []
    
    # 南京大学信息
    if row.get('南大专业') or row.get('南大时间'):
        edu_details.append({
            "school": "南京大学",
            "degree": row.get('南大学历', ''),
            "major": row.get('南大专业', ''),
            "year": row.get('南大时间', '')
        })
    
    return edu_details


def build_work_experiences_from_text(work_text):
    """从工作经历文本构建工作经历 JSON"""
    work_exps = []
    if pd.isna(work_text) or not work_text:
        return work_exps
    
    # 尝试解析多段工作经历（以 | 分隔）
    parts = str(work_text).split('|')
    for part in parts[:3]:  # 最多取前3段
        part = part.strip()
        if not part:
            continue
        
        work_exps.append({
            "company": extract_company_from_title(part),
            "title": extract_position_from_title(part),
            "time": "",
            "description": part[:500]
        })
    
    return work_exps


def convert_nju_to_candidate(row, source_file):
    """将南京大学校友数据行转换为 Candidate 对象"""
    from database import Candidate
    
    name = str(row.get('姓名', '')).strip()
    if not name or name == 'nan':
        return None
    
    # 工作年限
    exp_years = row.get('工作年限', 0)
    try:
        exp_years = int(float(exp_years)) if pd.notna(exp_years) else 0
    except:
        exp_years = 0
    
    # 学历
    edu_level = row.get('南大学历', '')
    if not edu_level or pd.isna(edu_level):
        edu_level = infer_education_level(
            str(row.get('教育经历', '')), 
            str(row.get('南大学历', ''))
        )
    
    # 简历全文
    work_text = str(row.get('工作经历', '')) if pd.notna(row.get('工作经历')) else ''
    edu_text = str(row.get('教育经历', '')) if pd.notna(row.get('教育经历')) else ''
    raw_resume = f"【工作经历】\n{work_text}\n\n【教育经历】\n{edu_text}"
    
    # 当前公司和职位
    current_company = ''
    current_title = ''
    if work_text:
        current_company = extract_company_from_title(work_text)
        current_title = extract_position_from_title(work_text)
    
    # 技能标签
    skills = ['南京大学']
    if row.get('南大专业') and pd.notna(row.get('南大专业')):
        major = str(row['南大专业'])
        if '计算机' in major:
            skills.append('计算机')
        if '人工智能' in major:
            skills.append('人工智能')
    
    # 备注
    notes = f"南大{edu_level}, 专业:{row.get('南大专业', '-')}, 时间:{row.get('南大时间', '-')}"
    
    return Candidate(
        name=name,
        experience_years=exp_years,
        education_level=edu_level if edu_level else '未知',
        current_company=current_company,
        current_title=current_title,
        source_file=source_file,
        raw_resume_text=raw_resume,
        skills=skills,
        education_details=build_education_details_from_row(row, row),
        work_experiences=build_work_experiences_from_text(work_text),
        notes=notes
    )


def import_nju_alumni(csv_path, session, dry_run=False):
    """导入南京大学校友数据"""
    from database import Candidate
    
    filename = os.path.basename(csv_path)
    source_name = f"maimai_nju_{datetime.now().strftime('%Y%m%d')}"
    
    # 读取数据
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        return 0, 0, []
    
    print(f"  📊 共 {len(df)} 条数据")
    
    imported = 0
    skipped = 0
    imported_names = []
    
    for _, row in df.iterrows():
        name = str(row.get('姓名', '')).strip()
        
        # 跳过无效
        if not name or name == 'nan':
            skipped += 1
            continue
        
        # 检查是否已存在
        existing = session.query(Candidate).filter(Candidate.name == name).first()
        if existing:
            print(f"    ⏭️ 跳过 {name}（已存在）")
            skipped += 1
            continue
        
        # 转换并添加
        candidate = convert_nju_to_candidate(row, source_name)
        if candidate:
            if not dry_run:
                session.add(candidate)
            imported_names.append(name)
            imported += 1
        else:
            skipped += 1
    
    if not dry_run:
        session.commit()
    
    return imported, skipped, imported_names


def main():
    import argparse
    parser = argparse.ArgumentParser(description='导入南京大学校友数据到 Headhunter 数据库')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不实际写入')
    parser.add_argument('--prod', action='store_true', help='导入到生产库（默认开发库）')
    parser.add_argument('--csv', default='南京大学校友_清洗结果.csv', help='CSV 文件路径')
    args = parser.parse_args()
    
    # 切换到生产库
    if args.prod:
        os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter.db")
        db_type = "生产库"
    else:
        db_type = "开发库"
    
    print("=" * 60)
    print("🎓 南京大学校友数据导入工具")
    print("=" * 60)
    print(f"📁 数据库: {db_type}")
    print(f"📄 CSV 文件: {args.csv}")
    
    if args.dry_run:
        print("⚠️ 模拟模式，不会实际写入数据库")
    
    # 初始化数据库
    from database import init_db, SessionLocal
    init_db()
    session = SessionLocal()
    
    # 导入
    csv_path = args.csv
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        return
    
    print(f"\n📄 处理: {os.path.basename(csv_path)}")
    imported, skipped, imported_names = import_nju_alumni(csv_path, session, args.dry_run)
    
    session.close()
    
    # 汇总
    print("\n" + "=" * 60)
    print("📊 导入汇总")
    print("=" * 60)
    print(f"✅ 成功导入: {imported} 人")
    print(f"⏭️ 跳过（已存在/无效）: {skipped} 人")
    
    if imported_names:
        print(f"\n📝 已导入候选人:")
        for name in imported_names[:10]:
            print(f"   • {name}")
        if len(imported_names) > 10:
            print(f"   ... 还有 {len(imported_names) - 10} 人")
    
    if args.dry_run:
        print("\n⚠️ 这是模拟运行，未实际写入数据库")
        print("   移除 --dry-run 参数以实际导入")


if __name__ == "__main__":
    main()
