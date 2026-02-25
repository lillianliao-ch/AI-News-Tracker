"""
公司名标准化脚本 — 将 current_company 映射为 company_normalized

用法:
  python3 normalize_companies.py          # 标准化所有空 company_normalized 的候选人
  python3 normalize_companies.py --all    # 全量重跑
  python3 normalize_companies.py --stats  # 查看标准化统计
"""

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from database import SessionLocal, Candidate, engine
from sqlalchemy import text

# 确保字段存在
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE candidates ADD COLUMN company_normalized VARCHAR(200)"))
        print("🔧 已新增 company_normalized 字段")
except:
    pass  # 字段已存在

# 加载别名映射
ALIASES_PATH = os.path.join(os.path.dirname(__file__), 'data', 'company_aliases.json')
with open(ALIASES_PATH, 'r') as f:
    raw = json.load(f)

# 构建反向索引: 别名(小写) -> 标准名
ALIAS_MAP = {}
for canonical, aliases in raw.items():
    if canonical.startswith('_'):
        continue
    # 标准名本身也放进去
    ALIAS_MAP[canonical.lower()] = canonical
    for alias in aliases:
        ALIAS_MAP[alias.lower()] = canonical


def normalize_company(company_name: str) -> str:
    """将公司名标准化为统一名称"""
    if not company_name:
        return ''

    # 清理常见后缀 (LinkedIn 格式: "ByteDance · 正式", "Google · Full-time")
    cleaned = re.sub(r'\s*·\s*(正式|实习|全职|合同|兼职|Full-time|Part-time|Internship|Contract|Freelance).*$', '', company_name).strip()
    # 清理年限后缀 ("正式 · 4 年 10 个月")
    cleaned = re.sub(r'^\d+\s*年.*$', '', cleaned).strip()
    if not cleaned:
        cleaned = company_name.strip()

    # 精确匹配
    key = cleaned.lower()
    if key in ALIAS_MAP:
        return ALIAS_MAP[key]

    # 模糊匹配: 从长到短尝试别名子串
    for alias, canonical in sorted(ALIAS_MAP.items(), key=lambda x: -len(x[0])):
        # 英文用单词边界
        if re.match(r'^[a-z0-9\s\.\-]+$', alias):
            if re.search(r'\b' + re.escape(alias) + r'\b', key):
                return canonical
        else:
            if alias in key:
                return canonical

    # 未匹配，返回清理后的原名
    return cleaned


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else None

    session = SessionLocal()

    if mode == '--stats':
        total = session.query(Candidate).count()
        has_norm = session.query(Candidate).filter(Candidate.company_normalized != None, Candidate.company_normalized != '').count()
        print(f'📊 标准化统计: {has_norm}/{total} 已标准化')

        all_c = session.query(Candidate).filter(Candidate.company_normalized != None, Candidate.company_normalized != '').all()
        dist = Counter(c.company_normalized for c in all_c)
        print(f'\n🏢 标准化公司 Top 30:')
        for name, cnt in dist.most_common(30):
            print(f'  {cnt:5d}  {name}')
        session.close()
        sys.exit(0)

    if mode == '--all':
        candidates = session.query(Candidate).filter(Candidate.current_company != None).all()
        print(f'🔄 全量标准化: {len(candidates)} 人')
    else:
        candidates = session.query(Candidate).filter(
            Candidate.current_company != None,
            (Candidate.company_normalized == None) | (Candidate.company_normalized == '')
        ).all()
        print(f'🔄 增量标准化: {len(candidates)} 人 (company_normalized 为空)')

    updated = 0
    unmatched = Counter()
    for c in candidates:
        norm = normalize_company(c.current_company)
        if norm:
            c.company_normalized = norm
            updated += 1
            # 统计未命中别名的
            if norm == c.current_company.strip() or norm == re.sub(r'\s*·.*$', '', c.current_company).strip():
                unmatched[norm] += 1

    session.commit()
    print(f'✅ 已标准化 {updated} 人')

    # 显示标准化结果
    all_c = session.query(Candidate).filter(Candidate.company_normalized != None, Candidate.company_normalized != '').all()
    dist = Counter(c.company_normalized for c in all_c)
    print(f'\n🏢 标准化后公司 Top 20:')
    for name, cnt in dist.most_common(20):
        print(f'  {cnt:5d}  {name}')

    if unmatched:
        print(f'\n⚠️  未命中别名的公司 Top 15（保留原名）:')
        for name, cnt in unmatched.most_common(15):
            print(f'  {cnt:4d}  {name}')

    session.close()
