#!/usr/bin/env python3
"""
LAMDA人才分析工具
对采集的候选人数据进行评分、分层和优先级排序
"""

import json
import csv
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import re


@dataclass
class CandidateScore:
    """候选人评分结果"""
    name: str
    source_type: str
    total_score: float
    academic_score: float  # 学术能力分
    career_score: float    # 职业潜力分
    reach_score: float     # 可触达性分
    timing_score: float    # 时机分
    tier: str              # A/B/C tier
    priority: str          # Hot/Warm/Pool
    summary: str           # 一句话评估
    recommendation: str    # 建议操作


# 顶会顶刊权重
VENUE_WEIGHTS = {
    # 顶会
    'ICML': 5, 'NeurIPS': 5, 'ICLR': 4, 
    'CVPR': 5, 'ICCV': 4, 'ECCV': 4,
    'ACL': 5, 'EMNLP': 4, 'NAACL': 3,
    'AAAI': 3, 'IJCAI': 3,
    'KDD': 4, 'WWW': 4, 'SIGIR': 4,
    # 顶刊
    'TPAMI': 6, 'JMLR': 5, 'TIP': 4, 'TKDE': 4,
}

# 导师权重 (周志华院士的直系弟子加分)
TOP_SUPERVISORS = {
    '周志华': 20, 'Zhi-Hua Zhou': 20, 'Zhou Zhihua': 20,
    '俞扬': 15, 'Yang Yu': 15,
    '张利军': 12, 'Lijun Zhang': 12,
    '姜远': 12, 'Yuan Jiang': 12,
    '黎铭': 10, 'Ming Li': 10,
    '吴建鑫': 10, 'Jianxin Wu': 10,
}

# 高价值公司
TOP_COMPANIES = {
    # 科技巨头
    '字节跳动': 15, 'ByteDance': 15, '抖音': 15,
    '阿里': 15, 'Alibaba': 15, '阿里巴巴': 15, 'DAMO': 15,
    '腾讯': 15, 'Tencent': 15,
    '华为': 12, 'Huawei': 12,
    'Google': 20, 'Microsoft': 18, 'Meta': 18, 'OpenAI': 25,
    'DeepMind': 25, 'Apple': 18, 'Amazon': 15,
    # AI独角兽
    '商汤': 12, 'SenseTime': 12,
    '旷视': 12, 'Megvii': 12,
    '智谱': 15, 'Zhipu': 15,
    '月之暗面': 18, 'Moonshot': 18,
    '百川': 15, 'Baichuan': 15,
    # 高校
    '教授': 10, 'Professor': 10, 'Assistant Professor': 8,
    '副教授': 8, 'Associate Professor': 8,
    '研究员': 8, 'Researcher': 8,
}


def parse_venues(venues_input) -> int:
    """解析顶会顶刊并计算分数"""
    if not venues_input:
        return 0
    
    # 处理list或string输入
    if isinstance(venues_input, list):
        venues_str = '; '.join(venues_input)
    else:
        venues_str = str(venues_input)
    
    score = 0
    # 格式: "ICML×4; NeurIPS×5"
    for item in venues_str.replace('; ', ';').split(';'):
        match = re.match(r'(\w+)×(\d+)', item.strip())
        if match:
            venue, count = match.groups()
            weight = VENUE_WEIGHTS.get(venue.upper(), 1)
            score += weight * int(count)
    return score


def get_supervisor_bonus(supervisor: str) -> int:
    """获取导师加分"""
    if not supervisor:
        return 0
    for name, bonus in TOP_SUPERVISORS.items():
        if name.lower() in supervisor.lower():
            return bonus
    return 0


def get_company_score(position: str, company: str = None) -> int:
    """获取公司/职位分数"""
    text = f"{position or ''} {company or ''}"
    if not text.strip():
        return 0
    
    for company_name, score in TOP_COMPANIES.items():
        if company_name.lower() in text.lower():
            return score
    return 5  # 其他公司基础分


def calculate_timing_score(work_start: str, phd_year: int = None, source_type: str = 'alumni') -> tuple:
    """计算时机分和优先级"""
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 在读学生
    if source_type in ['phd', 'msc']:
        if phd_year and current_year >= phd_year:
            return 15, 'Hot', '即将/刚毕业，求职窗口期'
        return 5, 'Pool', '在读学生，长期追踪'
    
    # 已毕业校友
    if work_start:
        try:
            parts = work_start.replace('.', '-').split('-')
            start_year = int(parts[0])
            start_month = int(parts[1]) if len(parts) > 1 else 1
            
            months_in_job = (current_year - start_year) * 12 + (current_month - start_month)
            
            if months_in_job < 6:
                return 3, 'Pool', '刚入职，暂不适合联系'
            elif months_in_job <= 18:
                return 8, 'Warm', '入职1年内，可建立联系'
            elif months_in_job <= 36:
                return 15, 'Hot', '在职2-3年，高跳槽意愿期'
            elif months_in_job <= 48:
                return 10, 'Warm', '在职3-4年，可能考虑机会'
            else:
                return 5, 'Pool', '在职超过4年，较稳定'
        except:
            pass
    
    # 毕业年份判断
    if phd_year:
        years_since_grad = current_year - phd_year
        if years_since_grad <= 0:
            return 15, 'Hot', '即将/刚毕业'
        elif years_since_grad <= 2:
            return 12, 'Hot', '毕业1-2年'
        elif years_since_grad <= 4:
            return 8, 'Warm', '毕业3-4年'
        else:
            return 5, 'Pool', '资深候选人'
    
    return 5, 'Warm', '时间信息不完整'


def calculate_reach_score(email: str, linkedin: str, github: str, scholar: str) -> int:
    """计算可触达性分数"""
    score = 0
    if email:
        # 区分公司邮箱和学校邮箱
        if any(domain in email for domain in ['alibaba', 'bytedance', 'tencent', 'huawei', 'google', 'microsoft']):
            score += 15  # 公司邮箱更有价值
        else:
            score += 10
    if linkedin:
        score += 8
    if github:
        score += 3
    if scholar:
        score += 2
    return min(score, 20)  # 上限20分


def analyze_candidate(candidate: dict) -> CandidateScore:
    """分析单个候选人"""
    
    # 1. 学术能力分 (40分满分)
    venue_score = min(parse_venues(candidate.get('top_venues', '') or 
                                   '; '.join(candidate.get('top_venues', []) if isinstance(candidate.get('top_venues'), list) else [])), 30)
    supervisor_bonus = get_supervisor_bonus(candidate.get('supervisor', ''))
    academic_score = min(venue_score + supervisor_bonus, 40)
    
    # 2. 职业潜力分 (30分满分)
    career_score = min(get_company_score(candidate.get('current_position', ''), 
                                         candidate.get('current_company', '')), 30)
    
    # 3. 可触达性分 (20分满分)
    reach_score = calculate_reach_score(
        candidate.get('email', ''),
        candidate.get('linkedin', ''),
        candidate.get('github', ''),
        candidate.get('google_scholar', '')
    )
    
    # 4. 时机分 (10分满分)
    phd_year = candidate.get('phd_year_end')
    timing_score, priority, timing_note = calculate_timing_score(
        candidate.get('work_start_date', ''),
        phd_year,
        candidate.get('source_type', 'alumni')
    )
    timing_score = min(timing_score, 10)
    
    # 总分
    total_score = academic_score + career_score + reach_score + timing_score
    
    # 分层
    if total_score >= 70:
        tier = 'A'
    elif total_score >= 45:
        tier = 'B'
    else:
        tier = 'C'
    
    # 生成摘要
    summary_parts = []
    if candidate.get('supervisor'):
        summary_parts.append(f"导师:{candidate['supervisor']}")
    if candidate.get('top_venues'):
        venues = candidate['top_venues'] if isinstance(candidate['top_venues'], str) else '; '.join(candidate['top_venues'][:3])
        summary_parts.append(venues)
    if candidate.get('current_position'):
        summary_parts.append(candidate['current_position'][:30])
    summary = ' | '.join(summary_parts) if summary_parts else '信息有限'
    
    # 生成建议
    if priority == 'Hot' and tier in ['A', 'B']:
        recommendation = '立即联系 - 发送个性化消息'
    elif priority == 'Hot':
        recommendation = '近期联系 - 建立初步认识'
    elif priority == 'Warm':
        recommendation = '建立联系 - 加好友/关注动态'
    else:
        recommendation = '长期追踪 - 加入人才库监控'
    
    return CandidateScore(
        name=candidate.get('name_cn', ''),
        source_type=candidate.get('source_type', ''),
        total_score=total_score,
        academic_score=academic_score,
        career_score=career_score,
        reach_score=reach_score,
        timing_score=timing_score,
        tier=tier,
        priority=priority,
        summary=summary,
        recommendation=recommendation
    )


def analyze_all(input_file: str, output_file: str = None) -> List[CandidateScore]:
    """分析所有候选人"""
    
    # 读取数据
    with open(input_file, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    
    print(f"Analyzing {len(candidates)} candidates...")
    
    # 分析每个候选人
    results = []
    for c in candidates:
        score = analyze_candidate(c)
        results.append(score)
    
    # 按总分排序
    results.sort(key=lambda x: x.total_score, reverse=True)
    
    # 统计
    tier_counts = {'A': 0, 'B': 0, 'C': 0}
    priority_counts = {'Hot': 0, 'Warm': 0, 'Pool': 0}
    for r in results:
        tier_counts[r.tier] += 1
        priority_counts[r.priority] += 1
    
    print("\n===== Analysis Summary =====")
    print(f"Total: {len(results)}")
    print(f"Tier A (顶级): {tier_counts['A']}")
    print(f"Tier B (优质): {tier_counts['B']}")
    print(f"Tier C (普通): {tier_counts['C']}")
    print(f"\nHot (立即联系): {priority_counts['Hot']}")
    print(f"Warm (建立联系): {priority_counts['Warm']}")
    print(f"Pool (长期追踪): {priority_counts['Pool']}")
    
    # 输出Top 20
    print("\n===== Top 20 Candidates =====")
    for i, r in enumerate(results[:20], 1):
        print(f"{i:2}. [{r.tier}] {r.name} (Score:{r.total_score:.0f}, {r.priority}) - {r.summary[:50]}")
    
    # 输出需要立即联系的
    hot_candidates = [r for r in results if r.priority == 'Hot' and r.tier in ['A', 'B']]
    if hot_candidates:
        print(f"\n===== 🔥 Priority Contacts ({len(hot_candidates)}) =====")
        for r in hot_candidates[:10]:
            print(f"• {r.name} [{r.tier}] - {r.recommendation}")
    
    # 导出结果
    if output_file:
        rows = []
        for r in results:
            rows.append({
                '姓名': r.name,
                '类型': r.source_type,
                '总分': r.total_score,
                '学术分': r.academic_score,
                '职业分': r.career_score,
                '触达分': r.reach_score,
                '时机分': r.timing_score,
                'Tier': r.tier,
                '优先级': r.priority,
                '摘要': r.summary,
                '建议': r.recommendation,
            })
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"\nExported analysis to {output_file}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LAMDA Talent Analyzer')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file from scraper')
    parser.add_argument('--output', type=str, default='lamda_analysis.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    analyze_all(args.input, args.output)


if __name__ == '__main__':
    main()
