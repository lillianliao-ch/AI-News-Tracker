#!/usr/bin/env python3
"""
GitHub 人才分级质量评估工具

评估方法：
1. 分层抽样 - 按Tier比例抽取样本
2. 多维度验证 - GitHub、LinkedIn、技能等
3. 生成人工审核样本
4. 计算准确率指标

用法:
    python evaluate_tier_quality.py --sample-size 620 --output-tier_sample.csv
"""

import sys
import os
import random
import argparse
import csv
from datetime import datetime
from collections import Counter

db_path = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
os.environ['DB_PATH'] = db_path

sys.path.insert(0, '/Users/lillianliao/notion_rag/personal-ai-headhunter')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Candidate

engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(bind=engine)


def stratified_sample(session, total_sample_size=620):
    """
    分层抽样：按Tier比例抽取样本
    """
    # 获取最近的GitHub导入
    candidates = session.query(Candidate).filter(
        Candidate.source == 'github',
        Candidate.created_at >= '2026-02-27'
    ).all()

    # 按Tier分组
    tier_groups = {}
    for c in candidates:
        tier = c.talent_tier or 'Unknown'
        if tier not in tier_groups:
            tier_groups[tier] = []
        tier_groups[tier].append(c)

    # 计算每层应该抽取的数量
    total = len(candidates)
    sample = []

    print(f"📊 分层抽样计划 (总计 {total_sample_size} 人):")
    print("-" * 60)

    for tier, group in sorted(tier_groups.items()):
        group_size = len(group)
        # 按比例抽样
        sample_size = max(1, int(group_size * total_sample_size / total))
        # 限制每层最多抽取数量（避免某个Tier样本过大）
        sample_size = min(sample_size, 200)

        # 随机抽取
        sampled = random.sample(group, min(sample_size, len(group)))
        sample.extend(sampled)

        print(f"   {tier}: {group_size:5} 人 → 抽取 {len(sampled):3} 人")

    print("-" * 60)
    print(f"   实际抽取: {len(sample)} 人\n")

    return sample


def evaluate_quality(sample):
    """
    评估样本质量
    """
    metrics = {
        'total': len(sample),
        'has_linkedin': 0,
        'has_email': 0,
        'has_github_stars': 0,
        'has_work_exp': 0,
        'has_skills': 0,
        'has_ai_summary': 0,
        'has_company': 0,
    }

    for c in sample:
        if c.linkedin_url:
            metrics['has_linkedin'] += 1
        if c.email:
            metrics['has_email'] += 1
        if c.github_url:
            metrics['has_github_stars'] += 1
        if c.work_experiences:
            metrics['has_work_exp'] += 1
        if c.skills:
            metrics['has_skills'] += 1
        if c.ai_summary:
            metrics['has_ai_summary'] += 1
        if c.current_company:
            metrics['has_company'] += 1

    return metrics


def generate_review_csv(sample, output_file):
    """
    生成人工审核CSV
    包含关键信息用于人工验证
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Name', 'Tier', 'GitHub', 'LinkedIn',
            'Email', 'Company', 'Title',
            'Skills', 'AI_Summary',
            'Verification_Link',  # 人工审核用
            'Notes',  # 人工审核笔记
            'Is_Correct'  # 人工判断: Y/N
        ])

        for c in sample:
            # 构造验证链接
            github = c.github_url or ''
            linkedin = c.linkedin_url or ''

            # 优先显示可验证的链接
            if github:
                verify_link = github
            elif linkedin:
                verify_link = linkedin
            else:
                verify_link = 'N/A'

            # 技能列表
            skills = '; '.join(c.skills) if c.skills else ''

            writer.writerow([
                c.id,
                c.name or 'N/A',
                c.talent_tier or 'Unknown',
                github,
                linkedin,
                c.email or '',
                c.current_company or '',
                c.current_title or '',
                skills,
                (c.ai_summary or '')[:200],  # 限制长度
                verify_link,
                '',  # Notes - 待人工填写
                ''   # Is_Correct - 待人工填写
            ])

    print(f"✅ 已生成人工审核样本: {output_file}")
    print(f"   包含 {len(sample)} 条记录\n")


def cross_validation_check(sample):
    """
    交叉验证：通过多源数据验证Tier准确性
    """
    print("🔍 交叉验证分析:")
    print("-" * 60)

    # S级应该有：高stars、顶级公司/学校、知名项目
    s_tier = [c for c in sample if c.talent_tier == 'S']
    if s_tier:
        has_strong_signals = 0
        for c in s_tier:
            # 强信号：顶级公司、知名学校、高followers等
            strong = False
            if c.current_company:
                company_lower = c.current_company.lower()
                top_companies = ['google', 'meta', 'openai', 'deepmind', 'microsoft', 'anthropic']
                if any(tc in company_lower for tc in top_companies):
                    strong = True
            if c.ai_summary and ('phd' in c.ai_summary.lower() or 'professor' in c.ai_summary.lower()):
                strong = True
            if strong:
                has_strong_signals += 1

        print(f"   S级样本: {len(s_tier)} 人")
        print(f"   有强信号: {has_strong_signals} 人 ({has_strong_signals*100//max(len(s_tier),1)}%)")

    # D级应该有：信号弱、信息少
    d_tier = [c for c in sample if c.talent_tier == 'D']
    if d_tier:
        weak_signals = 0
        for c in d_tier:
            # 弱信号：缺少关键信息
            if not c.linkedin_url and not c.email and not c.work_experiences:
                weak_signals += 1

        print(f"   D级样本: {len(d_tier)} 人")
        print(f"   缺少关键信息: {weak_signals} 人 ({weak_signals*100//max(len(d_tier),1)}%)")

    print("-" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='评估GitHub人才分级质量')
    parser.add_argument('--sample-size', type=int, default=620, help='样本大小')
    parser.add_argument('--output', default='tier_review_sample.csv', help='输出CSV文件')
    parser.add_argument('--seed', type=int, help='随机种子（可复现）')

    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)
        print(f"🎲 随机种子: {args.seed}\n")

    session = SessionLocal()

    # 1. 分层抽样
    print("=" * 60)
    print("🎯 GitHub 人才分级质量评估")
    print("=" * 60 + "\n")
    sample = stratified_sample(session, args.sample_size)

    # 2. 质量指标
    metrics = evaluate_quality(sample)
    print("📊 样本质量指标:")
    print("-" * 60)
    for key, value in metrics.items():
        if key != 'total':
            pct = value * 100 // metrics['total']
            print(f"   {key}: {value}/{metrics['total']} ({pct}%)")
    print("-" * 60 + "\n")

    # 3. 交叉验证
    cross_validation_check(sample)

    # 4. Tier分布
    tier_dist = Counter(c.talent_tier for c in sample if c.talent_tier)
    print("📈 样本Tier分布:")
    print("-" * 60)
    for tier, count in sorted(tier_dist.items()):
        pct = count * 100 // len(sample)
        print(f"   {tier}: {count:3} 人 ({pct}%)")
    print("-" * 60 + "\n")

    # 5. 生成人工审核CSV
    output_path = f"/Users/lillianliao/notion_rag/github_mining/scripts/github_mining/{args.output}"
    generate_review_csv(sample, output_path)

    # 6. 使用说明
    print("📝 人工审核步骤:")
    print("-" * 60)
    print("1. 打开生成的CSV文件")
    print("2. 逐一检查 Verification_Link 列的URL")
    print("3. 对比实际水平与 Tier 分级")
    print("4. 在 Is_Correct 列填写:")
    print("   Y - 分级正确")
    print("   N - 分级错误")
    print("   ? - 不确定")
    print("5. 在 Notes 列记录具体问题")
    print("-" * 60)
    print("\n✅ 评估完成！")

    session.close()


if __name__ == '__main__':
    main()
