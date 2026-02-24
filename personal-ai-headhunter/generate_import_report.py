#!/usr/bin/env python3
"""
生成CV导入对比清单
对比导入前后的候选人数据变化
"""

import os
import sys
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)
os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")

from database import SessionLocal, Candidate

def generate_import_report():
    """生成导入对比报告"""
    db = SessionLocal()

    print("=" * 80)
    print("📊 CV批量导入对比报告")
    print("=" * 80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 总体统计
    print("【1. 总体统计】")
    total = db.query(Candidate).count()
    maimai_cv = db.query(Candidate).filter(Candidate.source.like('%脉脉CV%')).count()
    maimai_total = db.query(Candidate).filter(Candidate.source.like('%脉脉%')).count()

    print(f"   总候选人数: {total}")
    print(f"   脉脉CV来源: {maimai_cv}")
    print(f"   脉脉总计: {maimai_total}")
    print()

    # 2. 最近导入的候选人
    print("【2. 最近导入/更新的候选人】")
    print("-" * 80)

    recent = db.query(Candidate).filter(
        Candidate.source.like('%脉脉CV%')
    ).order_by(Candidate.updated_at.desc()).limit(20).all()

    for i, c in enumerate(recent, 1):
        print(f"\n{i}. {c.name} (ID: {c.id})")
        print(f"   公司: {c.current_company or '未知'}")
        print(f"   职位: {c.current_title or '未知'}")
        print(f"   邮箱: {c.email or '无'}")
        print(f"   电话: {c.phone or '无'}")
        print(f"   工作年限: {c.experience_years or 0}年")
        print(f"   学历: {c.education_level or '未知'}")
        print(f"   来源: {c.source}")
        print(f"   更新时间: {c.updated_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"   人才等级: {c.talent_tier or '未评级'}")

        # 统计工作经历和教育背景
        work_count = len(c.work_experiences) if c.work_experiences else 0
        edu_count = len(c.education_details) if c.education_details else 0
        skill_count = len(c.skills) if c.skills else 0

        print(f"   工作经历: {work_count}条 | 教育: {edu_count}条 | 技能: {skill_count}项")

    print()
    print("=" * 80)

    # 3. 按更新时间分类
    print("【3. 按操作类型分类】")
    print("-" * 80)

    today = datetime.now().date()
    today_updates = db.query(Candidate).filter(
        Candidate.source.like('%脉脉CV%'),
        db.func.date(Candidate.updated_at) == today
    ).all()

    created = [c for c in today_updates if db.func.date(c.created_at) == today]
    updated = [c for c in today_updates if db.func.date(c.created_at) < today]

    print(f"   新建: {len(created)} 人")
    for c in created[:10]:
        print(f"      - {c.name} (ID: {c.id})")

    print(f"\n   更新: {len(updated)} 人")
    for c in updated[:10]:
        print(f"      - {c.name} (ID: {c.id})")

    print()
    print("=" * 80)

    # 4. 导出完整清单到CSV
    import csv
    report_file = f"/tmp/cv_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(report_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', '姓名', '公司', '职位', '邮箱', '电话',
            '工作年限', '学历', '人才等级', '来源',
            '工作经历数', '教育数', '技能数', '更新时间'
        ])

        for c in today_updates:
            writer.writerow([
                c.id,
                c.name,
                c.current_company or '',
                c.current_title or '',
                c.email or '',
                c.phone or '',
                c.experience_years or 0,
                c.education_level or '',
                c.talent_tier or '',
                c.source,
                len(c.work_experiences) if c.work_experiences else 0,
                len(c.education_details) if c.education_details else 0,
                len(c.skills) if c.skills else 0,
                c.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

    print(f"\n✅ 完整清单已导出到: {report_file}")
    print()

    db.close()

if __name__ == "__main__":
    generate_import_report()
