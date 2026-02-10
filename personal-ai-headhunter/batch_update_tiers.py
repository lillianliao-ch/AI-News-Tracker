"""
GitHub 候选人自动分级脚本
分级标准详见: .agent/workflows/github-mining-reference.md

6级体系: S → A+ → A → B+ → B → C
公司/Lab/学校配置: data/company_tier_config.json
"""

import json
import re
import os
from database import SessionLocal, Candidate
from import_github_candidates import import_candidates

# ============================================================
# 加载公司/Lab/学校分级配置
# ============================================================
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'company_tier_config.json')
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)

TIER1_KEYWORDS = [k.lower() for k in CONFIG['tier1_companies']['keywords']]
TIER2_KEYWORDS = [k.lower() for k in CONFIG['tier2_companies']['keywords']]
TOP_LAB_KEYWORDS = [k.lower() for k in CONFIG['top_labs']['keywords']]
UNI_985_KEYWORDS = [k.lower() for k in CONFIG['985_universities']['keywords']]


def _match_any(text: str, keywords: list) -> bool:
    """检查文本是否包含任意关键词"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _get_searchable_text(candidate) -> str:
    """合并候选人所有可搜索的文本字段"""
    parts = [
        candidate.notes or '',
        candidate.current_company or '',
        candidate.current_title or '',
    ]
    # structured_tags 里的信息
    tags = candidate.structured_tags or {}
    parts.append(tags.get('github_bio', ''))
    parts.append(tags.get('github_company', ''))
    # 工作经历
    if candidate.work_experiences:
        if isinstance(candidate.work_experiences, list):
            for exp in candidate.work_experiences:
                if isinstance(exp, dict):
                    parts.append(exp.get('company', ''))
                    parts.append(exp.get('title', ''))
        elif isinstance(candidate.work_experiences, str):
            parts.append(candidate.work_experiences)
    return ' '.join(parts)


def _get_education_text(candidate) -> str:
    """提取教育背景文本"""
    parts = []
    if candidate.education_details:
        if isinstance(candidate.education_details, list):
            for edu in candidate.education_details:
                if isinstance(edu, dict):
                    parts.append(edu.get('school', ''))
                    parts.append(edu.get('degree', ''))
                elif isinstance(edu, str):
                    parts.append(edu)
        elif isinstance(candidate.education_details, str):
            parts.append(candidate.education_details)
    # education_level 也可能有学校信息
    if candidate.education_level:
        parts.append(candidate.education_level)
    # bio 里也可能提到学校
    parts.append(candidate.notes or '')
    return ' '.join(parts)


def _normalize_achievements(achievements) -> str:
    """将 awards_achievements 统一为字符串"""
    if not achievements:
        return ''
    if isinstance(achievements, list):
        return ' '.join(str(a) for a in achievements)
    return str(achievements)


def _count_top_venues(achievements) -> int:
    """从 awards_achievements 中计算顶会论文总数"""
    text = _normalize_achievements(achievements)
    if not text:
        return 0
    venue_matches = re.findall(
        r'(ICLR|NeurIPS|ICML|ACL|EMNLP|NAACL|CVPR|ICCV|ECCV|AAAI|IJCAI|ICASSP):(\d+)',
        text
    )
    return sum(int(count) for _, count in venue_matches) if venue_matches else 0


def _get_h_index(achievements) -> int:
    """从 awards_achievements 中提取 h-index"""
    text = _normalize_achievements(achievements)
    if not text:
        return 0
    match = re.search(r'h-index[:\s]+(\d+)', text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def auto_tier(candidate) -> tuple:
    """
    计算候选人分级，返回 (tier, reason)

    优先级: S > A+ > A > C(方向不符) > B+ > B > C(默认)
    """
    tags = candidate.structured_tags or {}
    followers = tags.get('github_followers', 0)
    total_stars = tags.get('github_total_stars', 0)
    score = tags.get('github_score', 0)

    achievements = candidate.awards_achievements or ''
    top_venues = _count_top_venues(achievements)
    h_index = _get_h_index(achievements)

    searchable = _get_searchable_text(candidate)
    edu_text = _get_education_text(candidate)

    # === S级: 行业领军 ===
    if followers > 5000:
        return 'S', f'Followers={followers}'
    if total_stars > 5000:
        return 'S', f'Stars={total_stars}'
    if h_index > 30:
        return 'S', f'H-index={h_index}'

    # === A+级: 有3+顶会论文 ===
    if top_venues >= 3:
        return 'A+', f'顶会={top_venues}'

    # === A级: 顶尖Lab (即使没论文) ===
    if _match_any(searchable, TOP_LAB_KEYWORDS):
        return 'A', '顶尖Lab'

    # === C级: 方向不符 (提前判断，避免被 B+/B 吸收) ===
    bio_lower = (candidate.notes or '').lower()
    non_ai_keywords = ['android', 'ios开发', 'ios app', 'frontend', 'react', 'vue', 'angular',
                       'swift developer', 'kotlin android', '前端', '移动端']
    if any(kw in bio_lower for kw in non_ai_keywords):
        # 但如果在大厂做 AI 相关的移动端工作，不降级
        if not _match_any(searchable, ['ai', 'ml', 'deep learning', 'nlp', 'cv', 'llm']):
            return 'C', '方向不符'

    # === B+级: 一线大厂 + 985高校 ===
    is_tier1 = _match_any(searchable, TIER1_KEYWORDS)
    is_985 = _match_any(edu_text, UNI_985_KEYWORDS)

    if is_tier1 and is_985:
        return 'B+', '一线+985'

    # === B级: 一线大厂(学校不明), 或 985+二线大厂 ===
    is_tier2 = _match_any(searchable, TIER2_KEYWORDS)

    if is_tier1:
        return 'B', '一线大厂'
    if is_985 and is_tier2:
        return 'B', '985+二线'
    if is_985:
        return 'B', '985高校'
    if is_tier2:
        return 'B', '二线大厂'
    if followers > 500:
        return 'B', f'Followers={followers}'

    # === C级: 默认 ===
    return 'C', '默认'


# ============================================================
# 1. 人工审核覆盖（优先级最高）
# ============================================================
manual_overrides = {
    # 🔴 S - 领军/教授/顶级项目创始人
    'jindongwang': 'S',      # 助理教授, 23k citations
    'eyounx': 'S',           # 南大教授 LAMDA PI
    'xinntao': 'S',          # Real-ESRGAN (30k+ stars) 作者

    # 🟠 A+ - 顶会论文多/核心主力
    'wangsiwei2010': 'A+',   # 42篇顶会
    'feifeibear': 'A+',      # ColossalAI CTO
    'ZubinGou': 'A+',        # DeepSeek-R1 核心

    # 🟡 A - 顶尖Lab
    'Yikun': 'A',            # PyTorch member, OpenStack core
    'lafmdp': 'A',           # 华为TopMinds, 6 NeurIPS
    'wyhsirius': 'A',        # 视频生成核心作者
    'huybery': 'A',          # 阿里通义专家
    'li-plus': 'A',          # chatglm.cpp 作者 (工程强)
    'huangshiyu13': 'A',     # 小鹏VLM, 10年经验

    # 🟢 B+ - 大厂+名校
    'AtmaHou': 'B+',         # 哈工大 PhD
    'doubleZ0108': 'B+',     # 阿里/北大

    # 🔵 B - 大厂或名校
    'PureWhiteWu': 'B',      # 字节 CloudWeGo
    'sighingnow': 'B',       # 阿里/北航

    # ⚪ C - 方向不符
    'singwhatiwanna': 'C',   # Android
    'slashhuang': 'C',       # 前端
    'Nightonke': 'C',        # iOS/Android
}

# ============================================================
# 执行
# ============================================================
session = SessionLocal()
candidates = session.query(Candidate).filter(Candidate.source == 'github').all()

# 步骤 1: 应用人工审核
print("🔄 应用人工审核分级...")
manual_count = 0
for c in candidates:
    tags = c.structured_tags or {}
    gh = tags.get('github_username', '')
    if gh in manual_overrides:
        c.talent_tier = manual_overrides[gh]
        manual_count += 1
        print(f"  ✅ {c.name} ({gh}) -> {manual_overrides[gh]}")

session.commit()
print(f"✨ 人工审核 {manual_count} 人\n")

# 步骤 2: 导入新候选人
print("📦 导入新候选人...")
file_path = '../github_mining/phase3_5_enriched.json'
if os.path.exists(file_path):
    import_candidates(file_path, dry_run=False)
else:
    print(f"  ⚠️ {file_path} 不存在，跳过导入")

# 步骤 3: 自动分级（仅对未分级的候选人）
print("\n🤖 自动分级未分级候选人...")
new_candidates = session.query(Candidate).filter(
    Candidate.source == 'github',
    Candidate.talent_tier == None
).all()
auto_count = 0

for c in new_candidates:
    tier, reason = auto_tier(c)
    c.talent_tier = tier
    auto_count += 1
    print(f"  🤖 {c.name}: {reason} -> {tier}")

session.commit()

# 步骤 4: 打印统计
print(f"\n✨ 自动分级 {auto_count} 人")
print("\n📊 最终分级分布:")
from collections import Counter
all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
tier_dist = Counter(c.talent_tier for c in all_gh)
for tier in ['S', 'A+', 'A', 'B+', 'B', 'C', None]:
    count = tier_dist.get(tier, 0)
    if count > 0:
        label = tier if tier else '未分级'
        print(f"  {label}: {count} 人")
print(f"  总计: {len(all_gh)} 人")

session.close()
