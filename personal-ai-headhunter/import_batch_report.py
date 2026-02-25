"""
批次报告入库脚本 — 将 Pipeline 生成的 batch_report JSON 导入 batch_runs 表
支持直接导入 JSON 文件或从当前数据库实时统计生成

用法:
  # 导入已有的 batch_report JSON
  python3 import_batch_report.py path/to/batch_report.json

  # 从数据库实时统计生成（按来源）
  python3 import_batch_report.py --source github --batch-id "github_20260225"
  python3 import_batch_report.py --source 脉脉 --batch-id "maimai_20260225"

  # 列出所有已入库的批次
  python3 import_batch_report.py --list
"""

import json
import sys
import os
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from database import SessionLocal, Candidate, BatchRun, Base, engine

# 确保表存在
Base.metadata.create_all(bind=engine)


def import_from_json(json_path: str):
    """从 batch_report JSON 文件导入"""
    with open(json_path) as f:
        report = json.load(f)

    session = SessionLocal()

    batch_id = report.get('batch_id', os.path.basename(json_path).replace('.json', ''))

    # 检查是否已存在
    existing = session.query(BatchRun).filter(BatchRun.batch_id == batch_id).first()
    if existing:
        print(f'⚠️  批次 {batch_id} 已存在(id={existing.id})，跳过')
        session.close()
        return

    phases = report.get('phases', {})
    tier_data = phases.get('tier', {})
    db_snap = report.get('db_snapshot', {})

    # 从 phase 数据提取人数
    p4 = phases.get('phase4_crawl', {})
    p35 = phases.get('phase3_5_scrape', phases.get('phase3_5', {}))
    import_phase = phases.get('import', {})

    run = BatchRun(
        batch_id=batch_id,
        source=report.get('source', 'unknown'),
        started_at=_parse_dt(report.get('started_at')),
        completed_at=_parse_dt(report.get('completed_at')),
        seed_config=report.get('seed_config'),
        phase_data=phases,
        total_input=p4.get('total') or p35.get('total') or phases.get('phase1', {}).get('total'),
        total_imported=import_phase.get('new_added'),
        duplicates_skipped=import_phase.get('duplicates_skipped'),
        tier_s=tier_data.get('S', 0),
        tier_a_plus=tier_data.get('A+', 0),
        tier_a=tier_data.get('A', 0),
        tier_b_plus=tier_data.get('B+', 0),
        tier_b=tier_data.get('B', 0),
        tier_c=tier_data.get('C', 0),
        tier_d=tier_data.get('D', 0),
        has_email=p35.get('has_email', 0),
        has_linkedin=p35.get('linkedin_found', 0),
        has_github=0,  # GitHub source 默认全部有
        has_phone=0,
        has_website=0,
        db_total_candidates=db_snap.get('total_candidates'),
        db_total_github=db_snap.get('total_github'),
        db_total_linkedin=db_snap.get('total_linkedin'),
    )

    session.add(run)
    session.commit()
    print(f'✅ 已导入批次: {batch_id} (id={run.id})')
    session.close()


def generate_from_db(source: str, batch_id: str):
    """从数据库实时统计生成批次记录"""
    session = SessionLocal()

    existing = session.query(BatchRun).filter(BatchRun.batch_id == batch_id).first()
    if existing:
        print(f'⚠️  批次 {batch_id} 已存在(id={existing.id})，跳过')
        session.close()
        return

    candidates = session.query(Candidate).filter(Candidate.source == source).all()
    if not candidates:
        print(f'❌ 没有找到来源为 "{source}" 的候选人')
        session.close()
        return

    tier_dist = Counter(c.talent_tier for c in candidates)
    has_email = sum(1 for c in candidates if c.email)
    has_linkedin = sum(1 for c in candidates if c.linkedin_url)
    has_github = sum(1 for c in candidates if c.github_url)
    has_phone = sum(1 for c in candidates if c.phone)
    has_website = sum(1 for c in candidates if c.personal_website)

    # 全局快照
    all_cands = session.query(Candidate).count()
    all_gh = session.query(Candidate).filter(Candidate.source == 'github').count()
    all_li = session.query(Candidate).filter(Candidate.linkedin_url != None).count()

    run = BatchRun(
        batch_id=batch_id,
        source=source,
        completed_at=datetime.now(),
        phase_data={"note": f"Generated from DB snapshot for source={source}"},
        total_input=len(candidates),
        total_imported=len(candidates),
        tier_s=tier_dist.get('S', 0),
        tier_a_plus=tier_dist.get('A+', 0),
        tier_a=tier_dist.get('A', 0),
        tier_b_plus=tier_dist.get('B+', 0),
        tier_b=tier_dist.get('B', 0),
        tier_c=tier_dist.get('C', 0),
        tier_d=tier_dist.get('D', 0),
        has_email=has_email,
        has_linkedin=has_linkedin,
        has_github=has_github,
        has_phone=has_phone,
        has_website=has_website,
        db_total_candidates=all_cands,
        db_total_github=all_gh,
        db_total_linkedin=all_li,
    )

    session.add(run)
    session.commit()

    print(f'✅ 已生成批次记录: {batch_id}')
    print(f'   来源: {source}, 总人数: {len(candidates)}')
    print(f'   评级: S={tier_dist.get("S",0)} A+={tier_dist.get("A+",0)} A={tier_dist.get("A",0)} '
          f'B+={tier_dist.get("B+",0)} B={tier_dist.get("B",0)} C={tier_dist.get("C",0)} D={tier_dist.get("D",0)}')
    print(f'   可联系: Email={has_email} LinkedIn={has_linkedin} GitHub={has_github} Phone={has_phone} Website={has_website}')

    session.close()


def list_batch_runs():
    """列出所有已入库的批次"""
    session = SessionLocal()
    runs = session.query(BatchRun).order_by(BatchRun.created_at.desc()).all()
    if not runs:
        print('📭 暂无批次记录')
        session.close()
        return

    print(f'📊 共 {len(runs)} 个批次记录:\n')
    print(f'{"ID":>4} | {"批次标识":30s} | {"来源":20s} | {"人数":>6} | {"S":>3} {"A+":>3} {"A":>4} {"B+":>3} {"B":>5} {"C":>4} | {"Email":>5} {"LI":>4} {"Phone":>5}')
    print('-' * 120)
    for r in runs:
        print(f'{r.id:4d} | {r.batch_id:30s} | {r.source:20s} | {r.total_input or 0:6d} | '
              f'{r.tier_s:3d} {r.tier_a_plus:3d} {r.tier_a:4d} {r.tier_b_plus:3d} {r.tier_b:5d} {r.tier_c:4d} | '
              f'{r.has_email:5d} {r.has_linkedin:4d} {r.has_phone:5d}')
    session.close()


def _parse_dt(s):
    if not s or s == 'unknown':
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except:
        return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_batch_runs()
    elif sys.argv[1] == '--source':
        if len(sys.argv) < 5 or sys.argv[3] != '--batch-id':
            print('Usage: python3 import_batch_report.py --source <source> --batch-id <id>')
            sys.exit(1)
        generate_from_db(sys.argv[2], sys.argv[4])
    else:
        import_from_json(sys.argv[1])
