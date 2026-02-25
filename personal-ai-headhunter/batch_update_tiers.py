"""
GitHub 候选人自动分级脚本
分级标准详见: .agent/workflows/github-mining-reference.md

6级体系: S → A+ → A → B+ → B → C
公司/Lab/学校配置: data/company_tier_config.json
"""

import json
import re
import os
from datetime import datetime
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
UNI_985_TOP20_KEYWORDS = [k.lower() for k in CONFIG['985_top20']['keywords']]


def _match_any(text: str, keywords: list) -> bool:
    """检查文本是否包含任意关键词 (带英文单词边界保护)"""
    if not text:
        return False
    text_lower = text.lower()
    for kw in keywords:
        kw = kw.lower()
        # 如果关键词全由英文字母/数字/常见符号组成，使用单词边界匹配，防止 thu 匹配到 github
        if re.match(r'^[a-z0-9\s\.\-]+$', kw):
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return True
        else:
            # 包含中文等字符，使用普通子串匹配
            if kw in text_lower:
                return True
    return False


def _parse_tags(tags) -> dict:
    """安全解析 structured_tags，处理字符串或字典格式"""
    if tags is None:
        return {}
    if isinstance(tags, dict):
        return tags
    if isinstance(tags, str):
        try:
            return json.loads(tags)
        except:
            return {}
    return {}


def _get_searchable_text(candidate) -> str:
    """合并候选人所有可搜索的文本字段"""
    parts = [
        candidate.notes or '',
        candidate.current_company or '',
        candidate.current_title or '',
    ]
    # structured_tags 里的信息
    tags = _parse_tags(candidate.structured_tags)
    parts.append(tags.get('github_bio') or '')
    parts.append(tags.get('github_company') or '')
    # 工作经历
    if candidate.work_experiences:
        if isinstance(candidate.work_experiences, list):
            for exp in candidate.work_experiences:
                if isinstance(exp, dict):
                    parts.append(exp.get('company') or '')
                    parts.append(exp.get('title') or '')
        elif isinstance(candidate.work_experiences, str):
            parts.append(candidate.work_experiences)
    return ' '.join(str(p) for p in parts if p)


def _get_education_text(candidate) -> str:
    """提取教育背景文本"""
    parts = []
    if candidate.education_details:
        if isinstance(candidate.education_details, list):
            for edu in candidate.education_details:
                if isinstance(edu, dict):
                    parts.append(edu.get('school') or '')
                    parts.append(edu.get('degree') or '')
                elif isinstance(edu, str):
                    parts.append(edu)
        elif isinstance(candidate.education_details, str):
            parts.append(candidate.education_details)
    # education_level 也可能有学校信息
    if candidate.education_level:
        parts.append(str(candidate.education_level))
    # bio 里也可能提到学校
    parts.append(candidate.notes or '')
    return ' '.join(str(p) for p in parts if p)


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
    tags = _parse_tags(candidate.structured_tags)
    followers = tags.get('github_followers', 0)
    total_stars = tags.get('github_total_stars', 0)
    score = tags.get('github_score', 0)

    achievements = candidate.awards_achievements or ''
    top_venues = _count_top_venues(achievements)
    h_index = _get_h_index(achievements)

    searchable = _get_searchable_text(candidate)
    edu_text = _get_education_text(candidate)

    # AI方向检查 (用于S级判断)
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
                    'nlp', 'natural language', 'cv', 'computer vision', 'llm', 'large language model',
                    'neural', 'reinforcement learning', 'transformer', 'pytorch', 'tensorflow',
                    'chatgpt', 'gpt', 'bert', 'diffusion', 'stable diffusion', 'openai']
    is_ai_related = any(kw in searchable.lower() for kw in ai_keywords)

    # === S级: AI领域行业领军 ===
    # 必须是AI相关 + 满足影响力条件之一
    if not is_ai_related:
        pass  # 不符合S级，继续检查其他级别
    elif followers > 5000:
        return 'S', f'AI领域, Followers={followers}'
    elif total_stars > 5000:
        return 'S', f'AI领域, Stars={total_stars}'
    elif h_index > 30:
        return 'S', f'AI领域, H-index={h_index}'

    # === A+级: 有3+顶会论文 ===
    if top_venues >= 3:
        return 'A+', f'顶会={top_venues}'

    # === A级: 顶尖Lab (即使没论文) ===
    if _match_any(searchable, TOP_LAB_KEYWORDS):
        return 'A', '顶尖Lab'

    # === A级: 一线大厂 + 985 Top20 ===
    is_tier1 = _match_any(searchable, TIER1_KEYWORDS)
    is_985_top20 = _match_any(edu_text, UNI_985_TOP20_KEYWORDS)
    is_985 = _match_any(edu_text, UNI_985_KEYWORDS)

    if is_tier1 and is_985_top20:
        return 'A', '一线+985Top20'

    # === D级: 非AI方向 (提前判断，避免被 B+/B 吸收) ===
    bio_lower = (candidate.notes or '').lower()
    non_ai_keywords = ['android', 'ios开发', 'ios app', 'frontend', 'react', 'vue', 'angular',
                       'swift developer', 'kotlin android', '前端', '移动端']
    if any(kw in bio_lower for kw in non_ai_keywords):
        # 但如果在大厂做 AI 相关的移动端工作，不降级
        if not _match_any(searchable, ['ai', 'ml', 'deep learning', 'nlp', 'cv', 'llm']):
            return 'D', '非AI方向'

    # === B+级: 一线大厂 + 985高校(全部985) ===
    if is_tier1 and is_985:
        return 'B+', '一线+985'

    # === B级: 一线大厂 or 985高校 ===
    is_tier2 = _match_any(searchable, TIER2_KEYWORDS)

    if is_tier1:
        return 'B', '一线大厂'
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
import sys
from datetime import timedelta, datetime

session = SessionLocal()

# 支持命令行参数：指定重新评级的时间段
# 例如：python batch_update_tiers.py yesterday 重新评级昨日的候选人
#      python batch_update_tiers.py all 重新评级所有候选人
rerun_mode = len(sys.argv) > 1
target_period = sys.argv[1] if rerun_mode else None

# 确定筛选条件
if target_period == 'yesterday':
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    candidates = session.query(Candidate).filter(
        Candidate.created_at >= yesterday,
        Candidate.created_at < today
    ).all()
    print(f"🔄 重新评级昨日新增候选人 ({yesterday})...")
elif target_period == 'all':
    candidates = session.query(Candidate).all()
    print("🔄 重新评级所有候选人...")
elif target_period == 'github':
    candidates = session.query(Candidate).filter(Candidate.source == 'github').all()
    print("🔄 重新评级GitHub来源候选人...")
else:
    # 默认：只处理GitHub来源未分级的候选人
    candidates = session.query(Candidate).filter(
        Candidate.source == 'github',
        Candidate.talent_tier == None
    ).all()
    print("🤖 自动分级GitHub未分级候选人...")

# 步骤 1: 应用人工审核
manual_count = 0
for c in candidates:
    tags = _parse_tags(c.structured_tags)
    gh = tags.get('github_username', '')
    if gh in manual_overrides:
        c.talent_tier = manual_overrides[gh]
        c.tier_updated_at = datetime.now()
        manual_count += 1
        print(f"  ✅ {c.name} ({gh}) -> {manual_overrides[gh]}")

session.commit()
if manual_count > 0:
    print(f"✨ 人工审核 {manual_count} 人\n")

# 步骤 2: 自动分级
print("\n🤖 自动分级...")
auto_count = 0

for c in candidates:
    # 跳过已有人工审核的
    tags = _parse_tags(c.structured_tags)
    gh = tags.get('github_username', '')
    if gh in manual_overrides:
        continue

    # 如果不是rerun模式，跳过已分级的
    if not rerun_mode and c.talent_tier is not None:
        continue

    tier, reason = auto_tier(c)
    c.talent_tier = tier
    c.tier_updated_at = datetime.now()
    auto_count += 1
    print(f"  🤖 {c.name}: {reason} -> {tier}")

session.commit()
print(f"\n✨ 自动分级 {auto_count} 人")

# 步骤 3: 打印统计
print("\n📊 最终分级分布:")
from collections import Counter
tier_dist = Counter(c.talent_tier for c in candidates)
for tier in ['S', 'A+', 'A', 'B+', 'B', 'C', 'D', None]:
    count = tier_dist.get(tier, 0)
    if count > 0:
        label = tier if tier else '未分级'
        print(f"  {label}: {count} 人")
print(f"  总计: {len(candidates)} 人")

session.close()
