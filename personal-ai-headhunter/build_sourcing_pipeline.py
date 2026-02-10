#!/usr/bin/env python3
"""
build_sourcing_pipeline.py

聚合所有紧急 JD 的 target_teams，生成按对标公司排序的全局 sourcing pipeline。

核心逻辑:
  1. 读取所有 urgency >= 1 的 JD
  2. 从 sourcing_strategies.json 提取每个域的 target_teams
  3. 从 JD.sourcing_notes 提取 HR 原始策略中提到的公司
  4. 聚合为 "对标公司 → 覆盖哪些紧急JD"
  5. 按覆盖度排序，生成 sourcing_pipeline.json

用法:
  python3 build_sourcing_pipeline.py
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, '.')
from database import SessionLocal, Job


def load_strategies(path='data/sourcing_strategies.json'):
    with open(path, 'r') as f:
        return json.load(f)


# === 公司名标准化映射 ===
COMPANY_ALIASES = {
    # 阿里系
    '阿里通义': '阿里-通义', '通义千问': '阿里-通义', '通义': '阿里-通义',
    '阿里云PAI': '阿里-PAI', '阿里云PAI-灵积百炼': '阿里-PAI/百炼', '阿里百炼': '阿里-百炼',
    '夸克': '阿里-夸克', '夸克基模': '阿里-夸克',
    '蚂蚁百灵': '蚂蚁-百灵',
    '美团龙猫': '美团', '美团longcat': '美团', '美团图灵机器学习平台': '美团',
    # 腾讯系
    '腾讯混元': '腾讯-混元', '腾讯云TI平台/太极ML平台': '腾讯-TI平台',
    '腾讯妙系列': '腾讯-妙系列',
    # 字节系 (排除自家)
    '字节Seed': '(自家)', '字节Seed/AML': '(自家)', '字节即创算法团队(袁泽寰)': '(自家)',
    '字节seed/data': '(自家)', '字节其他业务线data/抖音': '(自家)', '字节': '(自家)',
    # 创业公司
    '月之暗面': '月之暗面/Kimi', 'Kimi': '月之暗面/Kimi', 'KIMI': '月之暗面/Kimi',
    '阶跃': '阶跃星辰', '阶跃星辰': '阶跃星辰',
    '稀宇MiniMax': 'MiniMax', 'MiniMax': 'MiniMax',
    '百川': '百川智能',
    '智谱': '智谱AI', '智谱(清华+ai院)': '智谱AI',
    '智谱(研究院)': '智谱AI',
    # 其他
    'DeepSeek': 'DeepSeek', '深度求索': 'DeepSeek',
    '华为': '华为', '华为云ModelArts': '华为',
}


def _normalize_company(name):
    """标准化公司名"""
    return COMPANY_ALIASES.get(name, name)


def _extract_companies_from_notes(notes_text):
    """从 HR sourcing_notes 原文中提取公司名"""
    if not notes_text:
        return []
    
    companies = []
    # 提取已知公司关键词
    known = [
        '阿里', '通义', '腾讯', '混元', '百度', '文心', '华为',
        'DeepSeek', '月之暗面', 'Kimi', '智谱', '百川', '阶跃', 'MiniMax',
        '快手', '美团', '小红书', '商汤', '旷视', '地平线',
        'OpenAI', 'Anthropic', 'Google', 'Meta',
    ]
    for kw in known:
        if kw in notes_text:
            companies.append(kw)
    
    return companies


def build_pipeline():
    strategies = load_strategies()
    session = SessionLocal()

    # === 获取所有紧急 JD ===
    urgent_jobs = session.query(Job).filter(
        Job.urgency >= 1,
        Job.is_active == 1
    ).order_by(Job.urgency.desc()).all()

    print(f'📋 紧急 JD 总数: {len(urgent_jobs)}')
    for j in urgent_jobs:
        labels = {3: '🔴', 2: '🟠', 1: '🟡'}
        print(f'  {labels.get(j.urgency, "⚪")} [{j.job_code}] {j.title} ({j.company})')

    # === 构建 公司→JD 映射 ===
    company_to_jobs = defaultdict(lambda: {
        'job_codes': [],
        'job_titles': [],
        'max_urgency': 0,
        'domains': set(),
        'search_keywords': set(),
        'sources': set(),  # 'strategy' or 'hr_notes'
    })

    # 1) 从 sourcing_strategies.json 提取
    for domain in strategies.get('domains', []):
        domain_name = domain.get('name', '')

        # domain 级 target_teams
        for tg in domain.get('target_teams', []):
            for ex in tg.get('examples', []):
                norm = _normalize_company(ex)
                if norm == '(自家)' or '均可' in ex:
                    continue
                company_to_jobs[norm]['domains'].add(domain_name)
                company_to_jobs[norm]['sources'].add('strategy')

        # position 级 target_teams
        for key, teams in domain.get('target_teams_by_position', {}).items():
            for tg in teams:
                for ex in tg.get('examples', []):
                    norm = _normalize_company(ex)
                    if norm == '(自家)' or '均可' in ex:
                        continue
                    company_to_jobs[norm]['domains'].add(f'{domain_name}/{key}')
                    company_to_jobs[norm]['sources'].add('strategy')

    # 2) 匹配紧急 JD 到 target_companies
    # 用 sourcing_strategies.json 中的 enrich_jd_from_strategies.py 逻辑来关联
    for job in urgent_jobs:
        job_title = job.title or ''
        job_domain = ''

        # 从 sourcing_notes 提取
        if job.sourcing_notes and '[Sourcing]' in job.sourcing_notes:
            parts = job.sourcing_notes.replace('[Sourcing] ', '').split(' | ')
            if parts:
                job_domain = parts[0].replace('domain=', '')

        # 从 sourcing_notes 提取 HR 提到的公司
        companies_from_hr = _extract_companies_from_notes(job.sourcing_notes)
        for c in companies_from_hr:
            norm = _normalize_company(c)
            if norm == '(自家)':
                continue
            company_to_jobs[norm]['job_codes'].append(job.job_code)
            company_to_jobs[norm]['job_titles'].append(job.title)
            company_to_jobs[norm]['max_urgency'] = max(
                company_to_jobs[norm]['max_urgency'], job.urgency or 0
            )
            company_to_jobs[norm]['sources'].add('hr_notes')

        # 根据 domain 关联 target_companies
        for company, info in company_to_jobs.items():
            if job_domain and any(job_domain in d for d in info['domains']):
                if job.job_code not in info['job_codes']:
                    info['job_codes'].append(job.job_code)
                    info['job_titles'].append(job.title)
                    info['max_urgency'] = max(info['max_urgency'], job.urgency or 0)

    # === 生成搜索关键词 ===
    for company, info in company_to_jobs.items():
        # 使用简洁公司名 (去掉 "-通义" 等后缀中的前缀)
        short_name = company.split('-')[-1] if '-' in company else company
        # 如果 short_name 是 AI 结尾, 去掉避免 "智谱AI AI"
        base = short_name.rstrip('AI').strip() if short_name.endswith('AI') else short_name

        domains_str = ' '.join(info['domains'])
        if '算法' in domains_str or '模型' in domains_str:
            info['search_keywords'].update([
                f'{base} 大模型算法', f'{base} AI算法',
            ])
        if 'Infra' in domains_str or '平台' in domains_str:
            info['search_keywords'].update([
                f'{base} AI Infra', f'{base} 训练框架',
            ])
        if 'AIGC' in domains_str or '创意' in domains_str:
            info['search_keywords'].update([
                f'{base} AIGC', f'{base} 图像生成',
            ])
        if not info['search_keywords']:
            info['search_keywords'].add(f'{base} AI')

    # === 按优先级排序 ===
    pipeline = []
    for company, info in company_to_jobs.items():
        if not info['job_codes']:
            continue
        pipeline.append({
            'target_company': company,
            'priority_score': len(info['job_codes']) * 10 + info['max_urgency'] * 5,
            'covers_jobs_count': len(info['job_codes']),
            'max_urgency': info['max_urgency'],
            'covers_job_codes': info['job_codes'],
            'covers_job_titles': info['job_titles'],
            'domains': sorted(info['domains']),
            'search_keywords': {
                'maimai': sorted(info['search_keywords']),
            },
            'sources': sorted(info['sources']),
            'status': 'pending',
        })

    pipeline.sort(key=lambda x: -x['priority_score'])

    # === 输出报告 ===
    print(f'\n\n{"="*70}')
    print(f'📊 全局 SOURCING PIPELINE ({len(pipeline)} 个对标公司)')
    print(f'{"="*70}')

    for i, item in enumerate(pipeline, 1):
        urgency_icon = {3: '🔴', 2: '🟠', 1: '🟡'}.get(item['max_urgency'], '⚪')
        print(f'\n{i}. {urgency_icon} {item["target_company"]} '
              f'(覆盖 {item["covers_jobs_count"]} 个JD, score={item["priority_score"]})')
        print(f'   领域: {", ".join(item["domains"][:3])}')
        print(f'   覆盖JD: {", ".join(item["covers_job_codes"][:5])}')
        print(f'   脉脉搜索: {" | ".join(item["search_keywords"]["maimai"][:4])}')
        print(f'   来源: {", ".join(item["sources"])}')

    # === 保存 ===
    output = {
        '_description': '全局 Sourcing Pipeline — 按对标公司优先级排序',
        '_generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        '_total_urgent_jobs': len(urgent_jobs),
        '_total_target_companies': len(pipeline),
        'pipeline': pipeline,
    }

    with open('data/sourcing_pipeline.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n\n💾 已保存到 data/sourcing_pipeline.json')
    print(f'   {len(pipeline)} 个对标公司, 覆盖 {len(urgent_jobs)} 个紧急JD')

    session.close()


if __name__ == '__main__':
    build_pipeline()
