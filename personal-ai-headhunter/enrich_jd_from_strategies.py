#!/usr/bin/env python3
"""
enrich_jd_from_strategies.py

从 sourcing_strategies.json 精准匹配字节 JD，更新 urgency/hr_contact/jd_link。
使用 title 子串匹配 + 部门锚定，避免误匹配。

用法:
  python3 enrich_jd_from_strategies.py          # dry-run 预览
  python3 enrich_jd_from_strategies.py --apply   # 实际写入
"""

import json
import sys
from collections import defaultdict

sys.path.insert(0, '.')
from database import SessionLocal, Job


def load_strategies(path='data/sourcing_strategies.json'):
    with open(path, 'r') as f:
        return json.load(f)


def _urgency_to_int(urgency_str):
    """将 sourcing 策略中的 urgency 转为整数 0-3"""
    if not urgency_str:
        return 0
    s = str(urgency_str)
    fire_count = s.count('🔥')
    if fire_count >= 6:
        return 3
    if fire_count >= 4:
        return 2
    if fire_count >= 2:
        return 1
    s_lower = s.lower()
    if 'p00' in s_lower:
        return 3
    if s_lower.startswith('p0') or s_lower == 'p0':
        return 2
    if 'p1' in s_lower:
        return 1
    return 0


def build_title_rules(strategies):
    """
    构建精准匹配规则：title 子串 → strategy 详情。
    只用 position title 自身的关键片段，不用泛化的 tech_keywords。
    """
    rules = []
    for domain in strategies.get('domains', []):
        domain_name = domain.get('name', '')
        domain_id = domain.get('id', '')

        # 获取 domain 级别的 target_teams
        domain_teams = domain.get('target_teams', [])
        teams_by_pos = domain.get('target_teams_by_position', {})

        for pos in domain.get('positions', []):
            title = pos.get('title', '')
            urgency = _urgency_to_int(pos.get('urgency', ''))
            hr = pos.get('hr_contact', '')
            if isinstance(hr, list):
                hr = ', '.join(hr)
            jd_link = pos.get('jd_link', '')

            # 从 title 提取精准匹配短语
            # 例如 "AIGC视频生成算法工程师-火山方舟" → 标题本身就是最好的匹配串
            match_phrases = [title]  # 完整标题优先

            # 去掉后缀再匹配
            # 如 "大语言模型算法工程师-豆包大模型" → "大语言模型算法工程师"
            if '-' in title:
                parts = title.split('-')
                match_phrases.append(parts[0].strip())

            # 找对应的 target_teams
            target_teams = domain_teams
            for key, teams in teams_by_pos.items():
                if key in title:
                    target_teams = teams
                    break

            rules.append({
                'match_phrases': match_phrases,
                'strategy_title': title,
                'domain_name': domain_name,
                'domain_id': domain_id,
                'urgency': urgency,
                'hr_contact': hr,
                'jd_link': jd_link,
                'target_teams': target_teams,
                'tech_keywords': pos.get('tech_keywords', []),
                'profile': pos.get('profile', ''),
            })

    return rules


def match_job(job, rules):
    """
    精准匹配：JD title 必须包含 strategy position 的核心短语。
    返回 (best_rule, score)。
    """
    jd_title = job.title or ''

    best = None
    best_score = 0

    for rule in rules:
        score = 0
        for phrase in rule['match_phrases']:
            # 完整短语匹配 — 高分
            if phrase in jd_title:
                score = max(score, 10 + len(phrase))
            # 去掉team后缀的前半匹配
            elif len(phrase) > 8 and phrase[:8] in jd_title:
                core = phrase[:8]
                if len(core) >= 6:
                    score = max(score, 5 + len(core))

        if score > best_score:
            best_score = score
            best = rule

    # 最低阈值：至少 10 分才算匹配（即至少一个完整短语命中）
    if best_score >= 10:
        return best, best_score
    return None, 0


def run_enrichment(dry_run=True):
    strategies = load_strategies()
    rules = build_title_rules(strategies)

    session = SessionLocal()
    bt_jobs = session.query(Job).filter(Job.company == '字节跳动').all()

    print(f'📋 字节 JD 总数: {len(bt_jobs)}')
    print(f'📚 匹配规则数: {len(rules)}')
    print()

    matched = []
    unmatched = []

    for job in bt_jobs:
        rule, score = match_job(job, rules)
        if rule:
            matched.append((job, rule, score))
        else:
            unmatched.append(job)

    # === 按 domain 分组展示匹配结果 ===
    print(f'✅ 精准匹配: {len(matched)} / {len(bt_jobs)}')
    print(f'❌ 未匹配:   {len(unmatched)} / {len(bt_jobs)}')

    by_domain = defaultdict(list)
    for job, rule, score in matched:
        by_domain[rule['domain_name']].append((job, rule, score))

    for domain_name, items in sorted(by_domain.items()):
        print(f'\n=== {domain_name} ({len(items)} 个) ===')
        for job, rule, score in items:
            updates = []
            if rule['urgency'] > 0 and (not job.urgency or job.urgency == 0):
                updates.append(f'urgency: 0→{rule["urgency"]}')
            if rule['hr_contact'] and not job.hr_contact:
                updates.append(f'hr→{rule["hr_contact"]}')
            if rule['jd_link'] and not job.jd_link:
                updates.append(f'link→...')
            update_str = ' | '.join(updates) if updates else '(已有数据)'
            print(f'  [{job.job_code}] {job.title}')
            print(f'    ← {rule["strategy_title"]} (score={score}) → {update_str}')

    # === 执行更新 ===
    updated_count = 0
    if not dry_run:
        for job, rule, score in matched:
            changed = False

            if rule['urgency'] > 0 and (not job.urgency or job.urgency == 0):
                job.urgency = rule['urgency']
                changed = True

            if rule['hr_contact'] and not job.hr_contact:
                job.hr_contact = rule['hr_contact']
                changed = True

            if rule['jd_link'] and not job.jd_link:
                job.jd_link = rule['jd_link']
                changed = True

            # 关联 sourcing 领域到 notes
            if not job.notes:
                job.notes = f'[Sourcing] {rule["domain_name"]} | {rule["strategy_title"]}'
                changed = True

            if changed:
                updated_count += 1

        session.commit()
        print(f'\n💾 已更新 {updated_count} 个 JD')
    else:
        print(f'\n⚠️  DRY RUN — 加 --apply 执行更新')

    # === 未匹配列表（分部门） ===
    print(f'\n\n📝 未匹配的 JD ({len(unmatched)} 个):')
    by_dept = defaultdict(list)
    for j in unmatched:
        by_dept[j.department or '未设置'].append(j)

    for dept, jobs_list in sorted(by_dept.items()):
        print(f'\n  [{dept}] ({len(jobs_list)})')
        for j in jobs_list:
            print(f'    [{j.job_code}] {j.title} | hr={j.hr_contact or "无"}')

    # === Sourcing 优先级计划 ===
    print('\n\n' + '='*70)
    print('📊 SOURCING 优先级清单 (urgency ≥ 2)')
    print('='*70)

    all_urgent = []

    # 字节匹配到的
    for job, rule, score in matched:
        urg = rule['urgency']
        if job.urgency and job.urgency > urg:
            urg = job.urgency
        if urg >= 2:
            all_urgent.append({
                'company': '字节跳动',
                'job_code': job.job_code,
                'title': job.title,
                'dept': job.department or '',
                'urgency': urg,
                'hr': rule['hr_contact'] or job.hr_contact or '',
                'target_teams': rule['target_teams'],
                'tech_keywords': rule['tech_keywords'],
                'profile': rule['profile'],
            })

    # 字节未匹配但本身有urgency的
    for job in unmatched:
        if job.urgency and job.urgency >= 2:
            all_urgent.append({
                'company': '字节跳动',
                'job_code': job.job_code,
                'title': job.title,
                'dept': job.department or '',
                'urgency': job.urgency,
                'hr': job.hr_contact or '',
                'target_teams': [],
                'tech_keywords': [],
                'profile': '',
            })

    # MiniMax
    mmx = session.query(Job).filter(Job.company == 'MiniMax', Job.urgency >= 2).all()
    for j in mmx:
        all_urgent.append({
            'company': 'MiniMax',
            'job_code': j.job_code,
            'title': j.title,
            'dept': j.department or '',
            'urgency': j.urgency,
            'hr': j.hr_contact or '',
            'target_teams': [],
            'tech_keywords': [],
            'profile': '',
        })

    all_urgent.sort(key=lambda x: (-x['urgency'], x['company']))

    labels = {3: '🔴 非常紧急', 2: '🟠 紧急', 1: '🟡 较急', 0: '⚪ 普通'}
    print(f'\n共 {len(all_urgent)} 个紧急职位:\n')

    for item in all_urgent:
        label = labels.get(item['urgency'], '⚪')
        print(f'{label} [{item["job_code"]}] {item["title"]} ({item["company"]})')
        if item['hr']:
            print(f'   HR: {item["hr"]}')
        if item['target_teams']:
            for tg in item['target_teams'][:3]:
                examples = tg.get('examples', [])
                p = tg.get('priority', '?')
                print(f'   P{p} 对标: {", ".join(examples[:5])}')
        if item['tech_keywords']:
            print(f'   搜索词: {", ".join(item["tech_keywords"][:8])}')
        print()

    session.close()


if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    run_enrichment(dry_run=dry_run)
