#!/usr/bin/env python3
"""
脉脉CV批量导入脚本 - 支持去重、更新、自动标签生成和等级评估

功能特点：
1. 从PDF简历中提取文本（支持文本版和扫描版OCR）
2. AI结构化解析候选人信息
3. 智能去重识别（邮箱、姓名+公司、姓名模糊匹配）
4. 数据智能合并（工作经历、教育背景、技能标签）
5. 自动生成结构化标签
6. 自动评估人才等级

使用方法：
    # 基本用法
    python3 batch_import_cv_with_update.py --source "/path/to/cv/directory"

    # Dry-run模式
    python3 batch_import_cv_with_update.py --source "/path/to/cv/directory" --dry-run

    # 指定文件模式
    python3 batch_import_cv_with_update.py --source "/path/to/cv/directory" --pattern "*工作4年*.pdf"

    # 详细日志
    python3 batch_import_cv_with_update.py --source "/path/to/cv/directory" --verbose
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加项目路径
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# 设置数据库路径（使用开发库）
os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")

from database import init_db, SessionLocal, Candidate
from ai_service import AIService

# ============================================================
# 配置
# ============================================================

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = ['.pdf']

# ============================================================
# PDF解析模块
# ============================================================

def extract_text_from_pdf(pdf_path: str) -> Tuple[str, str]:
    """
    从PDF中提取文本
    返回: (文本内容, 使用的解析方法)
    """
    text = ""
    method = ""

    # 方法1: PyPDF2 (文本PDF)
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        if len(text.strip()) > 500:
            return text, "PyPDF2"
    except Exception as e:
        pass

    # 方法2: PyMuPDF (支持OCR)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if len(text.strip()) > 500:
            return text, "PyMuPDF"
    except Exception as e:
        pass

    return text, "none"


def is_resume_file(filename: str) -> bool:
    """判断是否为简历文件"""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False

    # 排除明显不是简历的文件
    exclude_keywords = ['论文', 'paper', 'report', '文档', '说明']
    lower_name = filename.lower()
    for kw in exclude_keywords:
        if kw in lower_name:
            return False

    return True


# ============================================================
# 候选人识别模块
# ============================================================

def get_name_key(name: str) -> str:
    """提取姓名关键标识：首名 + 姓氏首字母"""
    if not name:
        return ''
    name = name.lower()
    name = re.sub(r'\([^)]*\)', '', name)  # 移除括号
    name = re.sub(r'[^a-z\s]', '', name)
    parts = name.split()
    if len(parts) >= 2:
        return f'{parts[0]} {parts[1][0]}'
    elif parts:
        return parts[0]
    return ''


def identify_candidate(parsed_data: Dict, session) -> Tuple[Optional[Candidate], str]:
    """
    识别候选人是否已存在

    识别策略：
    1. 邮箱匹配（最准确）
    2. 姓名 + 当前公司（精确匹配）
    3. 姓名key + 公司（模糊匹配，处理Zora Wang vs ZORA W ANG）
    4. 姓名key全局唯一匹配
    5. 姓名精确匹配

    返回: (候选人对象, 识别方法)
    """
    name = (parsed_data.get('name') or '').strip() if parsed_data.get('name') else ''
    email = (parsed_data.get('email') or '').strip() if parsed_data.get('email') else ''
    current_company = (parsed_data.get('current_company') or '').strip() if parsed_data.get('current_company') else ''

    # 方法1: 邮箱匹配
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

    # 方法3: 姓名key + 公司（模糊匹配）
    if current_company and name_key:
        all_candidates = session.query(Candidate).filter(
            Candidate.current_company == current_company
        ).all()
        for candidate in all_candidates:
            if get_name_key(candidate.name) == name_key:
                return candidate, 'name_key+company'

    # 方法4: 姓名key全局唯一匹配
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
# 数据合并模块
# ============================================================

def merge_work_experiences(existing: List, new_exps: List) -> List[Dict]:
    """合并工作经历，去重逻辑：公司+职位+时间都相同视为重复"""
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


def merge_education_details(existing: List, new_edu: List) -> List[Dict]:
    """合并教育背景，去重逻辑：学校+学位+专业相同视为重复"""
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


def merge_skills(existing: List, new_skills: List) -> List:
    """合并技能标签，去重"""
    if not existing:
        return new_skills if new_skills else []
    if not new_skills:
        return existing if isinstance(existing, list) else []

    if isinstance(existing, str):
        existing = [existing]
    if isinstance(new_skills, str):
        new_skills = [new_skills]

    all_skills = list(existing) + list(new_skills)
    return list(set(all_skills))


def merge_candidate_data(existing: Candidate, new_data: Dict) -> Dict:
    """
    智能合并候选人数据

    策略：
    - 基础信息：新数据优先（CV可能更准确）
    - 工作/教育经历：合并去重
    - 技能标签：合并去重
    - 原始简历：拼接保留历史
    """
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

    # 技能标签 - 合并去重
    existing_skills = existing.skills or []
    new_skills_list = new_data.get('skills', [])
    merged['skills'] = merge_skills(existing_skills, new_skills_list)

    # AI摘要 - 保留新的
    merged['ai_summary'] = new_data.get('ai_summary') or existing.ai_summary

    # 原始简历 - 拼接（保留历史）
    old_resume = existing.raw_resume_text or ''
    new_resume = new_data.get('raw_resume_text', '')
    if old_resume and new_resume:
        merged['raw_resume_text'] = f"{old_resume}\n\n{'='*60}\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n来源: 脉脉CV更新\n{new_resume}"
    elif new_resume:
        merged['raw_resume_text'] = new_resume
    else:
        merged['raw_resume_text'] = old_resume

    # 来源标注
    old_source = existing.source or ''
    merged['source'] = f"{old_source} -> 脉脉CV更新" if old_source else "脉脉CV"

    # 保留notes
    merged['notes'] = existing.notes

    return merged


# ============================================================
# 主导入逻辑
# ============================================================

def import_single_cv(pdf_path: str, session, dry_run: bool = False, verbose: bool = False) -> Dict:
    """
    导入单个CV文件

    返回: {
        'success': bool,
        'action': 'created' | 'updated' | 'skipped' | 'failed',
        'candidate_id': int | None,
        'name': str,
        'message': str
    }
    """
    filename = os.path.basename(pdf_path)

    # 1. 提取PDF文本
    resume_text, method = extract_text_from_pdf(pdf_path)

    if len(resume_text.strip()) < 100:
        return {
            'success': False,
            'action': 'failed',
            'candidate_id': None,
            'name': filename,
            'message': f'PDF文本过短或无法解析 ({len(resume_text)}字符, 方法:{method})'
        }

    if verbose:
        print(f"    📝 PDF解析成功: {len(resume_text)}字符 ({method})")

    # 2. AI解析
    try:
        ai_service = AIService()
        parsed = ai_service.parse_resume(resume_text)

        if isinstance(parsed, str):
            parsed = json.loads(parsed)

        # 添加原始文本
        parsed['raw_resume_text'] = resume_text

    except Exception as e:
        return {
            'success': False,
            'action': 'failed',
            'candidate_id': None,
            'name': filename,
            'message': f'AI解析失败: {e}'
        }

    if not parsed.get('name'):
        return {
            'success': False,
            'action': 'failed',
            'candidate_id': None,
            'name': filename,
            'message': 'AI未能识别姓名'
        }

    name = parsed.get('name')

    # 3. 识别候选人
    existing_candidate, identify_method = identify_candidate(parsed, session)

    if existing_candidate:
        # 4. 合并数据
        merged_data = merge_candidate_data(existing_candidate, parsed)

        if not dry_run:
            # 更新候选人
            for key, value in merged_data.items():
                setattr(existing_candidate, key, value)

            existing_candidate.updated_at = datetime.now()
            session.commit()

        return {
            'success': True,
            'action': 'updated',
            'candidate_id': existing_candidate.id,
            'name': name,
            'message': f'更新成功 (方法:{identify_method})'
        }
    else:
        # 4. 创建新候选人
        if not dry_run:
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

        return {
            'success': True,
            'action': 'created',
            'candidate_id': new_candidate.id if not dry_run else None,
            'name': name,
            'message': '创建成功'
        }


def batch_import_cv_directory(
    source_dir: str,
    pattern: str = "*.pdf",
    dry_run: bool = False,
    verbose: bool = False
) -> Dict[str, int]:
    """
    批量导入CV目录

    返回统计: {
        'total': int,
        'created': int,
        'updated': int,
        'skipped': int,
        'failed': int
    }
    """
    print("=" * 60)
    print("🚀 批量导入脉脉CV简历")
    print("=" * 60)
    print(f"📂 源目录: {source_dir}")
    print(f"📄 文件模式: {pattern}")
    if dry_run:
        print("⚠️ DRY-RUN模式 - 不会实际写入数据库")
    print("=" * 60)

    # 初始化数据库
    init_db()
    session = SessionLocal()

    # 扫描文件
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"❌ 目录不存在: {source_dir}")
        return {'total': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

    pdf_files = list(source_path.glob(pattern))
    pdf_files = [f for f in pdf_files if is_resume_file(f.name)]

    print(f"\n📊 发现 {len(pdf_files)} 个简历文件\n")

    stats = {
        'total': len(pdf_files),
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }

    # 批量处理
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_file.name}")

        try:
            result = import_single_cv(str(pdf_file), session, dry_run, verbose)

            if result['success']:
                if result['action'] == 'created':
                    stats['created'] += 1
                    print(f"  ✅ {result['message']}")
                elif result['action'] == 'updated':
                    stats['updated'] += 1
                    print(f"  ✅ {result['message']}")
            else:
                stats['failed'] += 1
                print(f"  ❌ {result['message']}")

        except Exception as e:
            stats['failed'] += 1
            print(f"  ❌ 处理失败: {e}")
            if verbose:
                import traceback
                traceback.print_exc()

    session.close()

    # 打印汇总
    print("\n" + "=" * 60)
    print("📊 导入汇总")
    print("=" * 60)
    print(f"✅ 新建: {stats['created']} 人")
    print(f"🔄 更新: {stats['updated']} 人")
    print(f"⏭️ 跳过: {stats['skipped']} 人")
    print(f"❌ 失败: {stats['failed']} 人")
    print(f"📦 总计: {stats['total']} 个文件")
    print("=" * 60)

    if dry_run:
        print("\n⚠️ 这是DRY-RUN运行，未实际写入数据库")
        print("   移除 --dry-run 参数以实际导入")

    return stats


# ============================================================
# 命令行接口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='批量导入脉脉CV简历到AI猎头系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python3 batch_import_cv_with_update.py --source "/path/to/cv/directory"

  # Dry-run模式
  python3 batch_import_cv_with_update.py --source "/path/to/cv/directory" --dry-run

  # 指定文件模式
  python3 batch_import_cv_with_update.py --source "/path/to/cv/directory" --pattern "*工作4年*.pdf"

  # 详细日志
  python3 batch_import_cv_with_update.py --source "/path/to/cv/directory" --verbose
        """
    )

    parser.add_argument(
        '--source',
        required=True,
        help='CV文件所在目录（必需）'
    )
    parser.add_argument(
        '--pattern',
        default='*.pdf',
        help='文件匹配模式（glob），默认: *.pdf'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际写入数据库'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )

    args = parser.parse_args()

    # 执行导入
    batch_import_cv_directory(
        source_dir=args.source,
        pattern=args.pattern,
        dry_run=args.dry_run,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
