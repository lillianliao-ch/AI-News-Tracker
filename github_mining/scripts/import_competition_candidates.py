#!/usr/bin/env python3
"""
竞赛人才专用导入脚本
source='competition'，notes 显示 CF rating/竞赛背景
用法: python3 import_competition_candidates.py [--dry-run]
"""

import sys, os, json, argparse
from pathlib import Path

# 正确指向猎头系统
HEADHUNTER_DIR = Path("/Users/lillianliao/notion_rag/personal-ai-headhunter")
sys.path.insert(0, str(HEADHUNTER_DIR))

def cf_tier(rating: int) -> str:
    if rating >= 3000: return "S"
    if rating >= 2700: return "A+"
    if rating >= 2500: return "A"
    if rating >= 2300: return "B+"
    return "B"

def build_notes(u: dict) -> str:
    lines = []
    rating = u.get("rating", 0)
    max_rating = u.get("max_rating", rating)
    rank = u.get("rank", "")
    handle = u.get("cf_handle", "")
    comp = u.get("competition", "")
    org = u.get("affiliation", "") or ""

    lines.append(f"【来源】竞赛人才挖掘 | {comp}")
    lines.append(f"【CF】handle: {handle} | Rating: {rating} (最高: {max_rating}) | {rank}")
    if org:
        lines.append(f"【机构】{org}")
    if u.get("google_scholar_url"):
        lines.append(f"【Scholar】{u['google_scholar_url']}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/Users/lillianliao/notion_rag/github_mining/data/competition/runs/run_20260320_155247/comp_enriched_full.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"🏆 竞赛人才导入 → 猎头系统")
    print(f"   DB: {HEADHUNTER_DIR}/data/headhunter_dev.db")
    print(f"   模式: {'DRY RUN' if args.dry_run else '实际写入'}")
    print(f"{'='*60}")

    with open(args.input) as f:
        data = json.load(f)

    # 按 rating 排序
    data.sort(key=lambda x: x.get("rating", 0), reverse=True)

    from database import SessionLocal, Candidate, init_db
    init_db()
    session = SessionLocal()

    imported = skipped = 0
    skip_names = []

    for i, u in enumerate(data, 1):
        name = u.get("name", "").strip()
        handle = u.get("cf_handle", "")
        rating = u.get("rating", 0)
        tier = cf_tier(rating)

        if not name or name == handle:
            # 用 handle 作为 name（没有真实姓名）
            name = handle

        github = u.get("github_url") or None
        linkedin = u.get("linkedin_url") or None
        org = u.get("affiliation", "") or ""
        website = u.get("personal_website") or None

        # 去重检查: name + github + linkedin
        existing = None
        match_type = None
        if name:
            existing = session.query(Candidate).filter(Candidate.name == name).first()
            if existing: match_type = "name"
        if not existing and github:
            existing = session.query(Candidate).filter(Candidate.github_url == github).first()
            if existing: match_type = "github"
        if not existing and linkedin:
            existing = session.query(Candidate).filter(Candidate.linkedin_url == linkedin).first()
            if existing: match_type = "linkedin"

        if existing:
            skipped += 1
            skip_names.append(f"{name}(已存在 id={existing.id} match={match_type})")
            if i <= 20:
                print(f"  ⏭️  {i:3d}. {name:30s} ← 已存在 [{match_type}]")
            continue

        notes = build_notes(u)
        structured_tags = {
            "competition_tier": tier,
            "cf_rating": rating,
            "cf_max_rating": u.get("max_rating", rating),
            "cf_rank": u.get("rank", ""),
            "cf_handle": handle,
            "competition": u.get("competition", ""),
            "google_scholar_url": u.get("google_scholar_url", ""),
        }

        profile_parts = [f"Codeforces {u.get('rank','').title()} Rating {rating}"]
        if org:
            profile_parts.append(org)
        bio = " | ".join(profile_parts)

        if args.dry_run:
            gh_flag = "🐙" if github else "  "
            sc_flag = "📚" if u.get("google_scholar_url") else "  "
            li_flag = "🔗" if linkedin else "  "
            print(f"  ✅ {i:3d}. [{tier}] rating={rating} {gh_flag}{sc_flag}{li_flag} {name:28s} | {org[:30]}")
            imported += 1
        else:
            cand = Candidate(
                name=name,
                email=None,
                current_title=f"Codeforces {u.get('rank','').title()}",
                current_company=org,
                linkedin_url=linkedin,
                github_url=github,
                personal_website=website,
                notes=notes,
                source="competition",
                structured_tags=structured_tags,
                pipeline_stage="new",
                nationality="chinese",
                skills=["算法", "竞赛编程", "数据结构"],
                talent_tier=tier,
            )
            session.add(cand)
            imported += 1
            if i <= 20 or i % 20 == 0:
                gh_flag = "🐙" if github else "  "
                print(f"  ✅ {i:3d}. [{tier}] rating={rating} {gh_flag} {name:28s}")

    if not args.dry_run:
        session.commit()
        print(f"\n✅ 已提交到数据库！")

    session.close()

    print(f"\n{'='*60}")
    print(f"📊 导入结果:")
    print(f"   ✅ 新增: {imported}")
    print(f"   ⏭️  跳过 (已存在): {skipped}")
    if not args.dry_run:
        print(f"   source='competition' 标记完成")
    if args.dry_run:
        print(f"   ⚠️  DRY RUN — 未写入数据库")

if __name__ == "__main__":
    main()
