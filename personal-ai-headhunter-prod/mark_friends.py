#!/usr/bin/env python3
"""
将最近从脉脉好友导入的候选人标记为已加好友
"""
import os
import sys
from datetime import datetime, timedelta

PROJECT_DIR = "/Users/lillianliao/notion_rag/personal-ai-headhunter"
sys.path.insert(0, PROJECT_DIR)

os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")

from database import SessionLocal, Candidate
from sqlalchemy import and_

def main():
    print("=" * 60)
    print("🏷️  标记脉脉好友")
    print("=" * 60)

    session = SessionLocal()

    # 获取最新导入的候选人（通过 source_file = 'maimai' 判断）
    new_candidates = session.query(Candidate).filter(
        and_(
            Candidate.source_file == 'maimai',
            Candidate.is_friend == 0
        )
    ).all()

    print(f"\n找到 {len(new_candidates)} 个今天导入的脉脉好友\n")

    if len(new_candidates) == 0:
        print("⚠️  没有找到需要标记的候选人")
        session.close()
        return

    # 标记为好友
    updated_count = 0
    for candidate in new_candidates:
        candidate.is_friend = 1
        candidate.friend_added_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        candidate.friend_channel = '脉脉'
        updated_count += 1

        print(f"✅ {candidate.name} - {candidate.current_company}")

    session.commit()

    print(f"\n{'='*60}")
    print(f"✅ 成功标记 {updated_count} 个好友")
    print(f"{'='*60}\n")

    # 验证结果
    total_friends = session.query(Candidate).filter(Candidate.is_friend == 1).count()
    print(f"📊 当前好友总数: {total_friends}")

    session.close()

if __name__ == "__main__":
    main()
