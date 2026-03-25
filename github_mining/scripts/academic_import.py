#!/usr/bin/env python3
"""
学术人才合并 & 导入脚本

合并多路数据源：
  1. all_conf_2025_full.json (基础数据: 姓名、h-index、论文、tier)
  2. _serper_cache.json (主页、邮箱、GitHub、LinkedIn)
  3. _enrichment_cache.json (v3 PDF提取的邮箱)
  4. _deep_cache.json (主页爬取: 邮箱、GitHub、homepage_text)
  5. _llm_enrichment_results.json (LLM提取: 工作/教育/技能/谈话点)

然后导入到猎头系统数据库。

用法:
  # 预览（不写入数据库）
  python3 academic_import.py --dry-run

  # 只导入 S/A+ 级
  python3 academic_import.py --tiers S,A+

  # 更新已有记录的 LLM 字段
  python3 academic_import.py --update --llm-results _llm_enrichment_results.json

  # 全部导入
  python3 academic_import.py
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 确保可以 import database
HEADHUNTER_DIR = Path(__file__).parent.parent.parent / "personal-ai-headhunter"
sys.path.insert(0, str(HEADHUNTER_DIR))


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def merge_data(full_path, serper_cache_path, pdf_cache_path,
               deep_cache_path=None, llm_results_path=None):
    """合并多路数据"""
    authors = load_json(full_path)
    serper_cache = load_json(serper_cache_path) if Path(serper_cache_path).exists() else {}
    pdf_cache = load_json(pdf_cache_path) if Path(pdf_cache_path).exists() else {}
    deep_cache = load_json(deep_cache_path) if deep_cache_path and Path(deep_cache_path).exists() else {}
    llm_results = load_json(llm_results_path) if llm_results_path and Path(llm_results_path).exists() else {}

    # Build lookup maps
    # 兼容两种 Serper cache key 格式:
    #   - "serper::Name" (2025/2023 标准格式)
    #   - "Name::"       (2024 contact_cache 格式)
    serper_map = {}
    for k, v in serper_cache.items():
        if k.startswith('serper::'):
            name = k.replace('serper::', '')
            serper_map[name] = v
        elif k.endswith('::'):
            name = k.rstrip(':')
            if name and name not in serper_map:  # serper:: 优先
                serper_map[name] = v

    pdf_map = {}
    for k, v in pdf_cache.items():
        if k.startswith('pdf::'):
            parts = k.split('::')
            name = parts[-1]
            pdf_map[name] = v

    deep_map = {}
    for k, v in deep_cache.items():
        if k.startswith('deep_homepage::'):
            name = k.split('::')[1]
            if name not in deep_map:
                deep_map[name] = v

    merged_count = 0
    llm_count = 0
    for author in authors:
        name = author.get('name', '')

        # Merge Serper data
        if name in serper_map:
            s = serper_map[name]
            if s.get('homepage') and not author.get('personal_website'):
                author['personal_website'] = s['homepage']
            if s.get('emails'):
                author['serper_emails'] = s['emails']
                if not author.get('email'):
                    author['email'] = s['emails'][0]
            if s.get('github') and not author.get('github_url'):
                author['github_url'] = s['github']
            if s.get('linkedin'):
                author['linkedin_url'] = s['linkedin']

        # Merge v3 PDF data
        if name in pdf_map:
            p = pdf_map[name]
            if p.get('matched_email'):
                author['pdf_email'] = p['matched_email']
                author['pdf_match_confidence'] = p.get('match_confidence', 'high')
                if not author.get('email'):
                    author['email'] = p['matched_email']

        # Merge deep cache data
        if name in deep_map:
            d = deep_map[name]
            if d.get('matched_email') and not author.get('email'):
                author['email'] = d['matched_email']
                author['deep_email_source'] = 'homepage_deep'
            if d.get('github') and not author.get('github_url'):
                author['github_url'] = d['github']
            if d.get('linkedin') and not author.get('linkedin_url'):
                author['linkedin_url'] = d['linkedin']

        # Merge LLM results
        if name in llm_results:
            lr = llm_results[name]
            if lr.get('llm_status') == 'done':
                author['_llm_extracted'] = lr.get('extracted', {})
                llm_count += 1

        # Track merged
        if author.get('email') or author.get('personal_website') or author.get('github_url'):
            merged_count += 1

    print(f"✅ 合并完成: {merged_count}/{len(authors)} 人有联系方式, {llm_count} 有LLM数据")
    return authors


def convert_to_import_format(author: dict) -> dict:
    """将学术记录转换为 import_github_candidates.py 兼容格式"""
    name = author.get('name', '')
    tier = author.get('_academic_tier', '?')
    h_index = author.get('h_index', 0) or 0
    citation = author.get('citation_count', 0) or 0
    nationality = author.get('_nationality', 'unknown')
    conferences = author.get('conferences', [])
    papers = author.get('papers', [])
    affiliation = author.get('affiliation', '') or ''

    # Build notes
    notes_lines = []
    notes_lines.append(f"【来源】Academic Mining 2025 | Tier: {tier} | h-index: {h_index} | Citations: {citation}")
    if affiliation:
        notes_lines.append(f"【机构】{affiliation}")
    if conferences:
        notes_lines.append(f"【顶会】{', '.join(conferences)}")
    if papers:
        notes_lines.append(f"【论文】共 {len(papers)} 篇:")
        for p in papers[:5]:
            if isinstance(p, dict):
                notes_lines.append(f"  · {p.get('title', '')} ({p.get('venue', '')})")
            else:
                notes_lines.append(f"  · {p}")
        if len(papers) > 5:
            notes_lines.append(f"  ... 另有 {len(papers)-5} 篇")

    # Multiple emails
    all_emails = set()
    if author.get('email'):
        all_emails.add(author['email'])
    if author.get('serper_emails'):
        all_emails.update(author['serper_emails'])
    if author.get('pdf_email'):
        all_emails.add(author['pdf_email'])
    emails = list(all_emails)

    primary_email = emails[0] if emails else None
    extra_emails = emails[1:] if len(emails) > 1 else []
    if extra_emails:
        notes_lines.append(f"【其他邮箱】{', '.join(extra_emails)}")

    # Skills from research topics + LLM
    skills = []
    llm_data = author.get('_llm_extracted', {})
    if llm_data.get('skills'):
        skills = llm_data['skills'][:20]
    else:
        for p in papers:
            if isinstance(p, dict):
                venue = p.get('venue', '')
                if venue and venue not in skills:
                    skills.append(venue)

    # structured_tags for academic-specific data
    tags = {
        'academic_tier': tier,
        'h_index': h_index,
        'citation_count': citation,
        'conferences': conferences,
        'paper_count': len(papers),
        'nationality_guess': nationality,
    }
    if author.get('s2_id'):
        tags['s2_id'] = author['s2_id']
    if author.get('pdf_email'):
        tags['pdf_email'] = author['pdf_email']
        tags['pdf_match_confidence'] = author.get('pdf_match_confidence', '')
    if llm_data.get('research_areas'):
        tags['research_areas'] = llm_data['research_areas']
    if llm_data.get('research_summary'):
        tags['research_summary'] = llm_data['research_summary']

    # Current title/company from LLM or affiliation
    current_title = 'Researcher'
    current_company = affiliation
    if llm_data.get('current_position'):
        pos = llm_data['current_position']
        if isinstance(pos, dict):
            if pos.get('title') and str(pos.get('title')) != 'None':
                current_title = pos['title']
            if pos.get('company') and str(pos.get('company')) != 'None':
                current_company = pos['company']
    elif h_index >= 50:
        current_title = 'Professor / Senior Researcher'
    elif h_index >= 20:
        current_title = 'Assistant/Associate Professor'

    # LLM work history → work_experiences format
    work_experiences = []
    if llm_data.get('work_history'):
        for w in llm_data['work_history']:
            if isinstance(w, dict):
                work_experiences.append({
                    'company': w.get('company', ''),
                    'title': w.get('role', ''),
                    'time': w.get('period', ''),
                    'description': '',
                })

    # LLM education → education_details format
    education_details = []
    if llm_data.get('education'):
        for e in llm_data['education']:
            if isinstance(e, dict):
                education_details.append({
                    'school': e.get('university', ''),
                    'degree': e.get('degree', ''),
                    'major': e.get('field', ''),
                    'time': e.get('year', ''),
                })

    # LLM talking points
    talking_pts = ''
    if llm_data.get('talking_points'):
        talking_pts = '\n'.join(f"• {tp}" for tp in llm_data['talking_points'])

    # LLM quality score
    quality_score = 0
    if isinstance(llm_data.get('quality_score'), (int, float)):
        quality_score = int(llm_data['quality_score'])

    return {
        'name': name,
        'username': name.lower().replace(' ', '-'),
        'email': primary_email,
        'extra_emails': extra_emails,
        'github_url': author.get('github_url', ''),
        'html_url': author.get('github_url', ''),
        'linkedin_url': author.get('linkedin_url', ''),
        'twitter_url': '',
        'personal_website': author.get('personal_website', ''),
        'blog': author.get('personal_website', ''),
        'company': current_company,
        'bio': f"Academic researcher | h-index: {h_index} | {'、'.join(conferences[:3])}",
        'current_title': current_title,
        'linkedin_position': current_title,
        'notes': '\n'.join(notes_lines),
        'source': 'academic',
        'nationality': nationality,
        'final_score_v2': h_index,
        'seniority_level': tier,
        'structured_tags': tags,
        'skills': skills[:20] if skills else None,
        'work_experiences': work_experiences if work_experiences else None,
        'education_details': education_details if education_details else None,
        'talking_points': talking_pts,
        'website_quality_score': quality_score,
        'linkedin_research_focus': skills[:20],
        'linkedin_career': work_experiences,
        'linkedin_education': education_details,
        'linkedin_achievements': [],
    }


def import_to_db(records, dry_run=False, update_mode=False):
    """导入到数据库
    
    ⚠️ 关键规则: 不同渠道的数据绝不互相更新！
    - 同源 (academic→academic): update_mode 下可补充空字段
    - 跨源 (academic→github/脉脉): 永远 INSERT 新记录 + 输出疑似重复清单
    
    Args:
        records: 待导入记录列表
        dry_run: 预览模式，不写入
        update_mode: 更新模式 — 仅对同源 academic 记录补充空字段
    """
    from database import SessionLocal, Candidate, init_db

    init_db()
    session = SessionLocal()

    imported = 0
    skipped = 0
    updated = 0
    duplicates = []  # 疑似重复清单 (跨源匹配)

    # 预建 s2_id 索引 (O(1) 查找，避免每条记录全表扫)
    print("  📇 构建 s2_id 索引...")
    s2_id_index = {}  # s2_id → Candidate
    for cand in session.query(Candidate).filter(Candidate.source == 'academic').all():
        cand_s2 = str((cand.structured_tags or {}).get('s2_id', ''))
        if cand_s2:
            s2_id_index[cand_s2] = cand
    print(f"  📇 索引完成: {len(s2_id_index)} 条 academic 记录有 s2_id")

    for i, rec in enumerate(records, 1):
        name = rec['name']
        email = rec.get('email', '')
        s2_id = str(rec.get('structured_tags', {}).get('s2_id', ''))

        # ===== 匹配策略 =====
        # 1) s2_id 精确匹配 (仅同源 academic, 最高优先级, O(1))
        # 2) email/name/github/linkedin/website 匹配 (跨源检测)
        
        existing = None
        match_type = None
        
        # Step 1: s2_id 匹配 — O(1) 字典查找
        if s2_id and s2_id in s2_id_index:
            existing = s2_id_index[s2_id]
            match_type = 's2_id'
        
        # Step 2: 跨源匹配检测 (如果 s2_id 没找到同源)
        if not existing:
            if email:
                existing = session.query(Candidate).filter(Candidate.email == email).first()
                if existing: match_type = 'email'
            if not existing and name:
                existing = session.query(Candidate).filter(Candidate.name == name).first()
                if existing: match_type = 'name'
            if not existing and rec.get('github_url'):
                existing = session.query(Candidate).filter(
                    Candidate.github_url == rec['github_url']).first()
                if existing: match_type = 'github'
            if not existing and rec.get('linkedin_url'):
                existing = session.query(Candidate).filter(
                    Candidate.linkedin_url == rec['linkedin_url']).first()
                if existing: match_type = 'linkedin'
            if not existing and rec.get('personal_website'):
                existing = session.query(Candidate).filter(
                    Candidate.personal_website == rec['personal_website']).first()
                if existing: match_type = 'website'

        if existing:
            is_same_source = (existing.source == 'academic')
            
            if not is_same_source:
                # ⛔ 跨源匹配 — 绝不更新！记录到重复清单，然后 INSERT 新记录
                duplicates.append({
                    'new_name': name,
                    'new_email': email or '',
                    'new_github': rec.get('github_url', ''),
                    'new_linkedin': rec.get('linkedin_url', ''),
                    'existing_id': existing.id,
                    'existing_name': existing.name,
                    'existing_source': existing.source,
                    'existing_email': existing.email or '',
                    'existing_github': existing.github_url or '',
                    'existing_linkedin': existing.linkedin_url or '',
                    'match_type': match_type,
                })
                # 继续走 INSERT 流程 (不 continue)
                existing = None  # 清除 match，强制 INSERT
                
            elif update_mode:
                # ✅ 同源 academic→academic: 可以补充空字段
                changes = []
                if not existing.email and rec.get('email'):
                    existing.email = rec['email']
                    changes.append(f"📧 {rec['email']}")
                if not existing.github_url and rec.get('github_url'):
                    existing.github_url = rec['github_url']
                    changes.append(f"🐙 github")
                if not existing.personal_website and rec.get('personal_website'):
                    existing.personal_website = rec['personal_website']
                    changes.append(f"🌐 website")
                if not existing.linkedin_url and rec.get('linkedin_url'):
                    existing.linkedin_url = rec['linkedin_url']
                    changes.append(f"🔗 linkedin")
                
                # LLM 字段 — 更新 current_title/company
                if rec.get('current_title') and rec['current_title'] != 'Researcher':
                    if not existing.current_title or existing.current_title in (
                        'Researcher', 'Professor / Senior Researcher',
                        'Assistant/Associate Professor'):
                        existing.current_title = rec['current_title']
                        existing.current_company = rec.get('company', '')
                        changes.append(f"👤 {rec['current_title'][:30]}")
                
                # LLM 字段 — work_experiences, education_details, skills
                if rec.get('work_experiences') and not existing.work_experiences:
                    existing.work_experiences = rec['work_experiences']
                    changes.append(f"💼 {len(rec['work_experiences'])} jobs")
                if rec.get('education_details') and not existing.education_details:
                    existing.education_details = rec['education_details']
                    changes.append(f"🎓 {len(rec['education_details'])} edu")
                if rec.get('skills') and not existing.skills:
                    existing.skills = rec['skills']
                    changes.append(f"🔧 {len(rec['skills'])} skills")
                if rec.get('talking_points') and not existing.talking_points:
                    existing.talking_points = rec['talking_points']
                    changes.append(f"💬 talking_pts")
                if rec.get('website_quality_score') and (not existing.website_quality_score or existing.website_quality_score == 0):
                    existing.website_quality_score = rec['website_quality_score']
                
                # 补充 structured_tags 中的深度数据
                if rec.get('structured_tags'):
                    old_tags = existing.structured_tags or {}
                    new_tags = rec['structured_tags']
                    for k in ['deep_email', 'deep_email_source', 'deep_github',
                              'deep_unmatched_emails', 'research_areas',
                              'research_summary']:
                        if new_tags.get(k) and not old_tags.get(k):
                            old_tags[k] = new_tags[k]
                    # 合并 conferences (关键: 跨年 update 时保留所有年份标签)
                    if new_tags.get('conferences'):
                        old_confs = set(old_tags.get('conferences', []))
                        new_confs = set(new_tags['conferences'])
                        merged = sorted(old_confs | new_confs)
                        if merged != sorted(old_confs):
                            old_tags['conferences'] = merged
                            changes.append(f"📅 +{len(new_confs - old_confs)} confs")
                    existing.structured_tags = old_tags
                
                if changes:
                    updated += 1
                    if updated <= 30 or updated % 50 == 0:
                        print(f"  🔄 {i:4d}. {name:30s} — 补充: {', '.join(changes)}")
                else:
                    skipped += 1
                continue
            else:
                skipped += 1
                if i <= 20 or i % 100 == 0:
                    print(f"  ⏭️  {i:4d}. {name:30s} — 已存在 (id={existing.id})")
                continue

        if dry_run:
            tier = rec.get('structured_tags', {}).get('academic_tier', '?')
            h = rec.get('structured_tags', {}).get('h_index', 0)
            print(f"  ✅ {i:4d}. [{tier:>2s}] h={h:>3d} {name:30s} | 📧 {email or 'N/A'}")
            imported += 1
            continue

        # Build candidate
        tags = rec.get('structured_tags', {})
        candidate = Candidate(
            name=name,
            email=email or None,
            current_title=rec.get('current_title', ''),
            current_company=rec.get('company', ''),
            linkedin_url=rec.get('linkedin_url', '') or None,
            github_url=rec.get('github_url', '') or None,
            personal_website=rec.get('personal_website', '') or None,
            notes=rec.get('notes', ''),
            source='academic',
            structured_tags=tags,
            pipeline_stage='new',
            nationality=rec.get('nationality', 'unknown'),
            skills=rec.get('skills'),
        )
        session.add(candidate)
        imported += 1

        if i <= 20 or i % 100 == 0:
            tier = tags.get('academic_tier', '?')
            h = tags.get('h_index', 0)
            print(f"  ✅ {i:4d}. [{tier:>2s}] h={h:>3d} {name:30s} | 📧 {email or 'N/A'}")

    if not dry_run:
        session.commit()
    session.close()

    print(f"\n{'='*60}")
    print(f"📊 导入结果:")
    print(f"   ✅ 新增: {imported}")
    print(f"   🔄 补充 (同源 academic): {updated}")
    print(f"   ⏭️  跳过 (已存在/无变化): {skipped}")
    print(f"   ⚠️  疑似跨源重复 (已新建，需人工核对): {len(duplicates)}")
    print(f"   📝 总处理: {imported + updated + skipped}")
    if dry_run:
        print(f"   ⚠️  DRY RUN — 未写入数据库")
    if update_mode:
        print(f"   📋 UPDATE 模式已启用 (仅同源)")

    # 输出疑似重复清单
    if duplicates:
        import csv
        report_path = str(Path(records[0].get('_source_dir', '.')) if records else '.') 
        report_path = str(Path(__file__).parent.parent / 'data' / 'academic' / 'duplicate_report.csv')
        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'match_type', 'new_name', 'new_email', 'new_github', 'new_linkedin',
                'existing_id', 'existing_name', 'existing_source', 
                'existing_email', 'existing_github', 'existing_linkedin',
            ])
            writer.writeheader()
            writer.writerows(duplicates)
        print(f"\n📋 疑似重复清单已保存: {report_path}")
        print(f"   请人工核对后决定是否合并")
        # 也打印前 10 条
        for d in duplicates[:10]:
            print(f"   ⚠️  [{d['match_type']:6s}] {d['new_name']:25s} ↔ id={d['existing_id']} {d['existing_name']:25s} (src={d['existing_source']})")
        if len(duplicates) > 10:
            print(f"   ... 还有 {len(duplicates) - 10} 条，详见 CSV")

    return imported, skipped


def main():
    parser = argparse.ArgumentParser(description="学术人才合并 & 导入")
    parser.add_argument('--input', required=True,
                       help='输入 full.json 路径 (必填)')
    parser.add_argument('--serper-cache', default=None,
                       help='Serper 缓存路径')
    parser.add_argument('--pdf-cache', default=None,
                       help='v3 PDF 缓存路径')
    parser.add_argument('--deep-cache', default=None,
                       help='Deep cache 路径 (_deep_cache.json)')
    parser.add_argument('--llm-results', default=None,
                       help='LLM 富化结果路径 (_llm_enrichment_results.json)')
    parser.add_argument('--tiers', default=None,
                       help='只导入指定 tier (逗号分隔)')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式')
    parser.add_argument('--update', action='store_true',
                        help='更新模式: 对已存在的记录补充空字段 (email/github/website)')
    parser.add_argument('--require-email', action='store_true',
                        help='只导入有邮箱的')
    args = parser.parse_args()

    # 默认路径: 从 --input 所在目录推导 cache 文件位置
    base = Path(args.input).parent
    full_path = args.input
    serper_path = args.serper_cache or str(base / "_serper_cache.json")
    pdf_path = args.pdf_cache or str(base / "_enrichment_cache.json")

    print(f"{'='*60}")
    print(f"📥 学术人才合并 & 导入")
    print(f"   基础数据: {full_path}")
    print(f"   Serper:   {serper_path}")
    print(f"   v3 PDF:   {pdf_path}")
    print(f"{'='*60}")

    # Step 1: 合并
    authors = merge_data(full_path, serper_path, pdf_path,
                         deep_cache_path=args.deep_cache or str(base / "_deep_cache.json"),
                         llm_results_path=args.llm_results or str(base / "_llm_enrichment_results.json"))

    # Step 2: 过滤
    if args.tiers:
        tiers = args.tiers.split(',')
        authors = [a for a in authors if a.get('_academic_tier') in tiers]
        print(f"   Tier 过滤: {args.tiers} → {len(authors)} 人")

    if args.require_email:
        authors = [a for a in authors if a.get('email')]
        print(f"   只含邮箱 → {len(authors)} 人")

    # Stats before import
    has_email = sum(1 for a in authors if a.get('email'))
    has_hp = sum(1 for a in authors if a.get('personal_website'))
    has_gh = sum(1 for a in authors if a.get('github_url'))
    has_li = sum(1 for a in authors if a.get('linkedin_url'))
    print(f"\n📊 合并后覆盖率 ({len(authors)} 人):")
    print(f"   📧 邮箱:    {has_email} ({has_email/len(authors)*100:.0f}%)")
    print(f"   🌐 主页:    {has_hp} ({has_hp/len(authors)*100:.0f}%)")
    print(f"   🐙 GitHub:  {has_gh} ({has_gh/len(authors)*100:.0f}%)")
    print(f"   🔗 LinkedIn:{has_li} ({has_li/len(authors)*100:.0f}%)")

    # Step 3: 转换格式
    records = [convert_to_import_format(a) for a in authors]

    # Step 4: 导入
    print(f"\n{'='*60}")
    import_to_db(records, dry_run=args.dry_run, update_mode=args.update)


if __name__ == '__main__':
    main()
