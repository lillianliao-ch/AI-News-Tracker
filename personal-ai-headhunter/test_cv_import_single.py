#!/usr/bin/env python3
"""
测试单个CV文件导入

用于验证导入流程是否正常工作
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# 设置数据库路径
os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")

from database import init_db, SessionLocal, Candidate
from ai_service import AIService

# ============================================================
# 配置
# ============================================================

# 测试文件
TEST_FILE = "/Users/lillianliao/notion_rag/数据输入/0224cv/zora_cv_2025_10.pdf"

# ============================================================
# PDF解析
# ============================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF中提取文本"""
    text = ""

    # 方法1: PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        if len(text.strip()) > 500:
            print(f"  ✅ PyPDF2解析成功: {len(text)}字符")
            return text
    except Exception as e:
        print(f"  ⚠️ PyPDF2解析失败: {e}")

    # 方法2: PyMuPDF
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if len(text.strip()) > 500:
            print(f"  ✅ PyMuPDF解析成功: {len(text)}字符")
            return text
    except Exception as e:
        print(f"  ⚠️ PyMuPDF解析失败: {e}")

    return text


def extract_name_from_filename(filename: str) -> str:
    """从文件名提取姓名"""
    name = os.path.splitext(filename)[0]
    # 移除常见后缀
    import re
    patterns = [
        r'_cv_\d+_\d+',
        r'-\d{8}',
        r'_cv',
    ]
    for pattern in patterns:
        name = re.sub(pattern, '', name)
    return name.strip()


# ============================================================
# 候选人识别
# ============================================================

def get_name_key(name: str) -> str:
    """提取姓名关键标识：首名 + 姓氏首字母"""
    if not name:
        return ''
    import re
    name = name.lower()
    name = re.sub(r'\([^)]*\)', '', name)  # 移除括号
    name = re.sub(r'[^a-z\s]', '', name)
    parts = name.split()
    if len(parts) >= 2:
        # 首名 + 姓氏首字母
        return f'{parts[0]} {parts[1][0]}'
    elif parts:
        return parts[0]
    return ''

def identify_candidate(parsed_data: dict, session):
    """通过多种方式识别候选人"""
    name = parsed_data.get('name', '').strip()
    email = parsed_data.get('email', '').strip()
    current_company = parsed_data.get('current_company', '').strip()

    # 方法1: 邮箱匹配（最准确）
    if email:
        candidate = session.query(Candidate).filter(
            Candidate.email == email
        ).first()
        if candidate:
            return candidate, 'email'

    if not name:
        return None, None

    # 提取姓名key
    name_key = get_name_key(name)

    # 方法2: 姓名 + 公司（精确匹配）
    if current_company:
        candidate = session.query(Candidate).filter(
            Candidate.name == name,
            Candidate.current_company == current_company
        ).first()
        if candidate:
            return candidate, 'name+company_exact'

    # 方法3: 姓名key + 公司（模糊匹配，用于Zora Wang vs ZORA W ANG）
    if current_company and name_key:
        all_candidates = session.query(Candidate).filter(
            Candidate.current_company == current_company
        ).all()
        for candidate in all_candidates:
            if get_name_key(candidate.name) == name_key:
                return candidate, 'name_key+company'

    # 方法4: 姓名key全局模糊匹配
    if name_key:
        all_candidates = session.query(Candidate).all()
        matches = []
        for candidate in all_candidates:
            if get_name_key(candidate.name) == name_key:
                matches.append(candidate)
        if len(matches) == 1:
            return matches[0], 'name_key_unique'

    # 方法5: 姓名精确匹配
    candidates = session.query(Candidate).filter(
        Candidate.name == name
    ).all()
    if len(candidates) == 1:
        return candidates[0], 'name_exact'

    return None, None


# ============================================================
# 数据合并
# ============================================================

def merge_work_experiences(existing, new_exps):
    """合并工作经历"""
    if not existing:
        return new_exps if new_exps else []
    if not new_exps:
        return existing if isinstance(existing, list) else []

    if isinstance(existing, str):
        try:
            existing = json.loads(existing)
        except:
            existing = []
    if isinstance(new_exps, str):
        try:
            new_exps = json.loads(new_exps)
        except:
            new_exps = []

    seen = set()
    merged = []

    for exp in existing:
        if not isinstance(exp, dict):
            continue
        key = (exp.get('company', ''), exp.get('title', ''), exp.get('time', ''))
        seen.add(key)
        merged.append(exp)

    for exp in new_exps:
        if not isinstance(exp, dict):
            continue
        key = (exp.get('company', ''), exp.get('title', ''), exp.get('time', ''))
        if key not in seen:
            seen.add(key)
            merged.append(exp)

    return merged


def merge_education_details(existing, new_edu):
    """合并教育背景"""
    if not existing:
        return new_edu if new_edu else []
    if not new_edu:
        return existing if isinstance(existing, list) else []

    if isinstance(existing, str):
        try:
            existing = json.loads(existing)
        except:
            existing = []
    if isinstance(new_edu, str):
        try:
            new_edu = json.loads(new_edu)
        except:
            new_edu = []

    seen = set()
    merged = []

    for edu in existing:
        if not isinstance(edu, dict):
            continue
        key = (edu.get('school', ''), edu.get('degree', ''), edu.get('major', ''))
        seen.add(key)
        merged.append(edu)

    for edu in new_edu:
        if not isinstance(edu, dict):
            continue
        key = (edu.get('school', ''), edu.get('degree', ''), edu.get('major', ''))
        if key not in seen:
            seen.add(key)
            merged.append(edu)

    return merged


def merge_candidate_data(existing, new_data):
    """智能合并候选人数据"""
    merged = {}

    # 基础信息 - 新数据优先
    merged['name'] = new_data.get('name') or existing.name
    merged['email'] = new_data.get('email') or existing.email
    merged['phone'] = new_data.get('phone') or existing.phone
    merged['age'] = new_data.get('age') or existing.age
    merged['experience_years'] = new_data.get('experience_years') or existing.experience_years
    merged['education_level'] = new_data.get('education_level') or existing.education_level
    merged['current_company'] = new_data.get('current_company') or existing.current_company
    merged['current_title'] = new_data.get('current_title') or existing.current_title

    # 工作经历 - 合并去重
    existing_work = existing.work_experiences if existing.work_experiences else []
    new_work = new_data.get('work_experiences', [])
    merged['work_experiences'] = merge_work_experiences(existing_work, new_work)

    # 教育背景 - 合并去重
    existing_edu = existing.education_details if existing.education_details else []
    new_edu = new_data.get('education_details', [])
    merged['education_details'] = merge_education_details(existing_edu, new_edu)

    # 技能 - 合并去重
    existing_skills = existing.skills or []
    new_skills = new_data.get('skills', [])
    all_skills = (existing_skills if isinstance(existing_skills, list) else [existing_skills]) + \
                 (new_skills if isinstance(new_skills, list) else [new_skills])
    merged['skills'] = list(set(all_skills))

    # AI摘要 - 新的优先
    merged['ai_summary'] = new_data.get('ai_summary') or existing.ai_summary

    # 原始简历 - 拼接
    old_resume = existing.raw_resume_text or ''
    new_resume = new_data.get('raw_resume_text', '')
    if old_resume and new_resume:
        merged['raw_resume_text'] = f"{old_resume}\n\n{'='*60}\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n来源: 脉脉CV更新\n{new_resume}"
    else:
        merged['raw_resume_text'] = new_resume or old_resume

    # 来源
    old_source = existing.source or ''
    merged['source'] = f"{old_source} -> 脉脉CV更新" if old_source else "脉脉CV"

    # 保留notes
    merged['notes'] = existing.notes

    return merged


# ============================================================
# 主测试函数
# ============================================================

def test_single_import(pdf_path: str, dry_run: bool = False):
    """测试单个CV导入"""
    filename = os.path.basename(pdf_path)

    print("=" * 60)
    print("🧪 测试单个CV导入")
    print("=" * 60)
    print(f"📄 文件: {filename}")
    print("=" * 60)

    # 初始化数据库
    init_db()
    session = SessionLocal()

    # 步骤1: 提取PDF文本
    print("\n[步骤1] 提取PDF文本")
    resume_text = extract_text_from_pdf(pdf_path)

    if len(resume_text.strip()) < 100:
        print(f"❌ PDF文本过短: {len(resume_text)}字符")
        session.close()
        return

    print(f"✅ 提取成功: {len(resume_text)}字符")

    # 步骤2: AI解析
    print("\n[步骤2] AI解析简历")
    ai_service = AIService()

    try:
        parsed = ai_service.parse_resume(resume_text)

        if isinstance(parsed, str):
            parsed = json.loads(parsed)

        print(f"✅ AI解析成功")
        print(f"   姓名: {parsed.get('name')}")
        print(f"   公司: {parsed.get('current_company')}")
        print(f"   职位: {parsed.get('current_title')}")
        print(f"   工作年限: {parsed.get('experience_years')}")
        print(f"   学历: {parsed.get('education_level')}")

        # 添加原始文本
        parsed['raw_resume_text'] = resume_text

    except Exception as e:
        print(f"❌ AI解析失败: {e}")
        session.close()
        return

    # 步骤3: 识别候选人
    print("\n[步骤3] 识别候选人")
    existing_candidate, method = identify_candidate(parsed, session)

    if existing_candidate:
        print(f"✅ 找到已存在候选人")
        print(f"   ID: {existing_candidate.id}")
        print(f"   姓名: {existing_candidate.name}")
        print(f"   公司: {existing_candidate.current_company}")
        print(f"   识别方法: {method}")

        # 步骤4: 合并数据
        print("\n[步骤4] 合并数据")

        merged_data = merge_candidate_data(existing_candidate, parsed)

        print(f"   工作经历: {len(merged_data.get('work_experiences', []))}条")
        print(f"   教育背景: {len(merged_data.get('education_details', []))}条")
        print(f"   技能: {len(merged_data.get('skills', []))}项")

        if not dry_run:
            # 更新候选人
            for key, value in merged_data.items():
                setattr(existing_candidate, key, value)

            existing_candidate.updated_at = datetime.now()
            session.commit()

            print("✅ 数据库更新成功")
        else:
            print("⚠️ DRY-RUN模式 - 跳过实际更新")

    else:
        print(f"🆕 新候选人")

        if not dry_run:
            # 创建新候选人
            new_candidate = Candidate(
                name=parsed.get('name'),
                email=parsed.get('email'),
                phone=parsed.get('phone'),
                age=parsed.get('age'),
                experience_years=parsed.get('experience_years'),
                education_level=parsed.get('education_level'),
                current_company=parsed.get('current_company'),
                current_title=parsed.get('current_title'),
                raw_resume_text=parsed.get('raw_resume_text'),
                work_experiences=parsed.get('work_experiences', []),
                education_details=parsed.get('education_details', []),
                skills=parsed.get('skills', []),
                ai_summary=parsed.get('summary'),
                source="脉脉CV",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            session.add(new_candidate)
            session.commit()
            session.refresh(new_candidate)

            print(f"✅ 创建成功 (ID: {new_candidate.id})")
        else:
            print("⚠️ DRY-RUN模式 - 跳过实际创建")

    session.close()

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='测试单个CV导入')
    parser.add_argument('--file', default=TEST_FILE, help='CV文件路径')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行')

    args = parser.parse_args()

    test_single_import(args.file, args.dry_run)
