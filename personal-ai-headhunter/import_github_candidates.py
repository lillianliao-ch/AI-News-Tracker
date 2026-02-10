#!/usr/bin/env python3
"""
GitHub Mining 候选人导入猎头系统 v2

从 phase3_5_enriched.json 读取候选人数据，映射到 Candidate 模型字段，
组装 notes 备注文本，写入数据库。

改进点 (v2):
- source 设为 'github'
- 自动检测组织账号 (多重策略)
- 更好地从 bio/company 提取信息
- 中文名保留 (如有)
- personal_website、twitter_url 独立存储

Usage:
    python import_github_candidates.py --file ../github_mining/phase3_5_enriched.json
    python import_github_candidates.py --file ../github_mining/phase3_5_enriched.json --top 20
    python import_github_candidates.py --file ../github_mining/phase3_5_enriched.json --skip 20 --top 25
    python import_github_candidates.py --file ../github_mining/phase3_5_enriched.json --dry-run
"""

import argparse
import json
import os
import sys

# 确保可以 import database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Candidate, init_db


# 已知组织账号 (手动补充，避免遗漏)
KNOWN_ORGS = {
    'Tencent', 'baidu', 'didi', 'meituan', 'Meituan-Dianping',
    'thunlp', 'THUDM', 'alibaba', 'bytedance', 'huawei',
    'microsoft', 'google', 'meta', 'openai',
}


def is_organization(user: dict) -> bool:
    """多重策略检测组织账号"""
    # 1. 明确标记
    if user.get('type') == 'Organization':
        return True
    if user.get('is_organization'):
        return True
    # 2. 已知组织列表
    username = user.get('username', '')
    if username in KNOWN_ORGS:
        return True
    # 3. 启发式: 无 bio 且无 name 差异且 company=None 且 followers 很高
    name = user.get('name', '')
    if name and name == username and not user.get('bio') and not user.get('email'):
        return True
    return False


def build_notes(user: dict) -> str:
    """组装人可读的 notes 备注文本"""
    lines = []

    # 来源和评分
    score = user.get('final_score_v2', user.get('final_score', user.get('score', 0)))
    seniority = user.get('seniority_level', '')
    source_line = f"【来源】GitHub Mining | Score: {score}"
    if seniority:
        source_line += f" | 资历: {seniority}"
    if user.get('is_hiring'):
        source_line += " | 🔥正在招聘"
    lines.append(source_line)

    # Bio
    bio = user.get('bio', '')
    if bio:
        lines.append(f"【Bio】{bio}")

    # 当前职位
    pos = user.get('linkedin_position', user.get('current_title', ''))
    if pos:
        lines.append(f"【当前】{pos}")

    # 工作履历
    career = user.get('linkedin_career', [])
    if career:
        lines.append("【履历】")
        for c in career:
            company = c.get('company', '')
            title = c.get('title', '')
            period = c.get('period', '')
            note = c.get('note', '')
            entry = f"  · {company} — {title} ({period})"
            if note:
                entry += f" [{note}]"
            lines.append(entry)

    # 学历
    edu = user.get('linkedin_education', [])
    if edu:
        edu_parts = []
        for e in edu:
            if isinstance(e, dict):
                parts = [e.get('school', '')]
                if e.get('degree'):
                    parts.append(e['degree'])
                if e.get('field'):
                    parts.append(e['field'])
                if e.get('year') or e.get('period'):
                    parts.append(e.get('year', e.get('period', '')))
                edu_parts.append(' — '.join(p for p in parts if p))
        if edu_parts:
            lines.append(f"【学历】{'; '.join(edu_parts)}")

    # 成就
    achievements = user.get('linkedin_achievements', [])
    if achievements:
        lines.append(f"【成就】{'; '.join(achievements[:5])}")

    # 搜索备注 (原始摘要)
    note = user.get('search_note', '')
    if note:
        lines.append(f"【搜索备注】{note}")

    return '\n'.join(lines)


def convert_career_to_work_experiences(user: dict) -> list:
    """将 linkedin_career 或 bio/company 转换为 work_experiences 格式"""
    result = []
    
    # 优先使用 linkedin_career
    for c in user.get('linkedin_career', []):
        result.append({
            'company': c.get('company', ''),
            'title': c.get('title', ''),
            'time': c.get('period', ''),
            'description': c.get('note', ''),
        })
    
    # 如果没有 linkedin_career，从 bio/company 推断
    if not result:
        company = user.get('company', '')
        if company and company.startswith('@'):
            company = company[1:]
        bio = user.get('bio', '') or ''
        
        if company:
            # 尝试从 bio 提取职位
            title = ''
            for keyword in ['Engineer', 'Researcher', 'Developer', 'Professor',
                          'Architect', 'Scientist', 'Student', 'Ph.D', 'PhD',
                          '工程师', '研究员', '架构师', '教授', '博士']:
                if keyword.lower() in bio.lower():
                    # 取 bio 的前一部分作为 title
                    title = bio.split('.')[0].split(',')[0].split('|')[0].strip()
                    if len(title) > 80:
                        title = title[:80]
                    break
            
            if not title and bio:
                title = bio.split('.')[0].split(',')[0].split('|')[0].strip()
                if len(title) > 80:
                    title = title[:80]
            
            result.append({
                'company': company,
                'title': title or 'Unknown',
                'time': 'Current',
                'description': '',
            })
    
    return result


def convert_education(edu: list) -> list:
    """将 linkedin_education 转换为 education_details 格式"""
    result = []
    for e in edu:
        if isinstance(e, dict):
            result.append({
                'school': e.get('school', ''),
                'degree': e.get('degree', ''),
                'major': e.get('field', ''),
                'year': str(e.get('year', e.get('period', ''))),
            })
    return result


def convert_achievements(user: dict) -> list:
    """合并论文统计和成就为 awards_achievements"""
    result = []

    # LinkedIn 成就
    for a in user.get('linkedin_achievements', []):
        result.append({'type': 'achievement', 'title': a})

    # 顶会论文统计
    venues = user.get('top_venues', {})
    if isinstance(venues, dict) and venues:
        venue_str = ', '.join(f"{k}: {v}" for k, v in venues.items())
        result.append({'type': 'publications', 'title': f"顶会论文: {venue_str}"})

    return result


def build_skills(user: dict) -> list:
    """合并研究方向为 skills 列表"""
    skills = set()
    for topic in user.get('linkedin_research_focus', []):
        skills.add(topic)
    for topic in user.get('research_topics', []):
        skills.add(topic)
    return list(skills) if skills else None


def build_structured_tags(user: dict) -> dict:
    """将 GitHub 专属数据存入 structured_tags"""
    tags = {}
    tags['github_username'] = user.get('username', '')
    tags['github_score'] = user.get('final_score_v2', user.get('final_score', user.get('score', 0)))
    if user.get('seniority_level'):
        tags['seniority_level'] = user['seniority_level']
    if user.get('is_hiring'):
        tags['is_hiring'] = True
    if user.get('scholar_url'):
        tags['google_scholar'] = user['scholar_url']
    if user.get('linkedin_search_url'):
        tags['linkedin_search_url'] = user['linkedin_search_url']
    # 保留 GitHub 原始数据的关键指标
    if user.get('followers'):
        tags['github_followers'] = user['followers']
    if user.get('public_repos'):
        tags['github_repos'] = user['public_repos']
    if user.get('total_stars'):
        tags['github_total_stars'] = user['total_stars']
    return tags


def extract_name(user: dict) -> str:
    """提取候选人姓名，保留中文名"""
    name = user.get('name', '') or user.get('username', '')
    username = user.get('username', '')
    
    # 如果 name 就是 username (没有真名)，直接返回 username
    if name == username:
        return username
    
    return name


def extract_current_info(user: dict) -> tuple:
    """提取当前职位和公司"""
    # 优先用 linkedin_position
    current_title = user.get('linkedin_position', user.get('current_title', ''))
    
    # 公司
    current_company = user.get('company', '')
    if current_company and current_company.startswith('@'):
        current_company = current_company[1:]
    
    # 如果没有 title，从 bio 提取
    if not current_title:
        bio = user.get('bio', '') or ''
        if bio:
            # 取第一句作为title
            first_line = bio.split('\n')[0].split('.')[0].split('|')[0].strip()
            if len(first_line) <= 80:
                current_title = first_line
    
    return current_title, current_company


def import_candidates(file_path: str, top: int = None, skip: int = 0, dry_run: bool = False):
    """主导入函数"""
    # 读取数据
    with open(file_path, 'r', encoding='utf-8') as f:
        users = json.load(f)

    # 跳过前 skip 条，取 top 条
    if skip:
        users = users[skip:]
    if top:
        users = users[:top]

    print(f"📂 加载 {len(users)} 个候选人 from {file_path}")
    if skip:
        print(f"   ⏩ 跳过前 {skip} 条")

    if dry_run:
        print("🔍 DRY RUN 模式 — 不会写入数据库\n")

    # 初始化数据库
    init_db()
    session = SessionLocal()

    imported = 0
    skipped = 0
    skipped_org = 0

    for i, user in enumerate(users, 1):
        username = user.get('username', '')
        name = extract_name(user)

        # 跳过组织账号
        if is_organization(user):
            skipped_org += 1
            print(f"  🏢 {i:3d}. {username:25s} — 组织账号，跳过")
            continue

        # 选择最佳邮箱
        email = user.get('email', '')
        extra = user.get('extra_emails', [])
        if not email and extra:
            email = extra[0]

        # 去重检查 (by email or by GitHub URL)
        github_url = user.get('html_url', f"https://github.com/{username}")
        existing = None
        if email:
            existing = session.query(Candidate).filter(Candidate.email == email).first()
        if not existing:
            existing = session.query(Candidate).filter(Candidate.github_url == github_url).first()
        if not existing and name != username:
            existing = session.query(Candidate).filter(Candidate.name == name).first()

        if existing:
            skipped += 1
            if not dry_run:
                print(f"  ⏭️  {i:3d}. {name:25s} — 已存在 (id={existing.id})")
            continue

        # 构建字段
        current_title, current_company = extract_current_info(user)
        work_experiences = convert_career_to_work_experiences(user)
        education_details = convert_education(user.get('linkedin_education', []))
        awards = convert_achievements(user)
        skills = build_skills(user)
        notes = build_notes(user)
        tags = build_structured_tags(user)
        linkedin_url = user.get('linkedin_url', '')
        twitter_url = user.get('twitter_url', '')
        personal_website = user.get('blog', '')

        # 打印预览
        print(f"  ✅ {i:3d}. {name:25s} | {(current_title or '-')[:40]:40s} | 📧 {email or 'N/A'}")
        if work_experiences:
            print(f"        💼 工作: {len(work_experiences)} 条 | 🎓 学历: {len(education_details)} 条 | 🏷️ 技能: {len(skills or [])} 项")
        if linkedin_url:
            print(f"        🔗 LinkedIn: {linkedin_url}")
        if personal_website:
            print(f"        🌐 网站: {personal_website}")

        if dry_run:
            imported += 1
            continue

        # 创建 Candidate
        candidate = Candidate(
            name=name,
            email=email or None,
            current_title=current_title or None,
            current_company=current_company or None,
            linkedin_url=linkedin_url or None,
            github_url=github_url,
            twitter_url=twitter_url or None,
            personal_website=personal_website or None,
            work_experiences=work_experiences if work_experiences else None,
            education_details=education_details if education_details else None,
            awards_achievements=awards if awards else None,
            skills=skills,
            notes=notes,
            source='github',
            structured_tags=tags,
            pipeline_stage='new',
        )
        session.add(candidate)
        imported += 1

    if not dry_run:
        session.commit()

    session.close()

    print(f"\n{'='*60}")
    print(f"📊 导入结果:")
    print(f"   ✅ 新增: {imported}")
    print(f"   ⏭️  跳过 (已存在): {skipped}")
    print(f"   🏢 跳过 (组织账号): {skipped_org}")
    print(f"   📝 总处理: {imported + skipped + skipped_org}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="导入 GitHub Mining 候选人到猎头系统 v2")
    parser.add_argument('--file', required=True, help='phase3_5_enriched.json 文件路径')
    parser.add_argument('--top', type=int, default=None, help='只导入 Top N (在 skip 之后)')
    parser.add_argument('--skip', type=int, default=0, help='跳过前 N 条')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不写入数据库')
    args = parser.parse_args()

    import_candidates(args.file, top=args.top, skip=args.skip, dry_run=args.dry_run)
