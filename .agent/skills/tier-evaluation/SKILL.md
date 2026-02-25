---
description: 批量评级候选人 Tier（S/A+/A/B+/B/C/D），支持按来源、时间段或全量重跑
---

# 候选人 Tier 评级

对 personal-ai-headhunter 系统中的候选人执行自动 Tier 分级。

## 评级标准

| Tier | 条件 | 说明 |
|------|------|------|
| S | AI领域 + Followers>5000 / Stars>5000 / H-index>30 | 行业领军 |
| A+ | 3+顶会论文 | 顶会多产作者 |
| A | 顶尖Lab 关键词匹配 | 核心实验室 |
| **A** | **tier1 + 985 Top20** | 一线大厂+顶尖名校 |
| D | 非AI方向（前端/移动端等）且无AI信号 | 方向不符（提前排除） |
| B+ | tier1 + 985（全部985） | 一线+名校 |
| B | tier1 or 985 | 一线大厂或名校 |
| B | tier2 | 二线大厂 |
| B | Followers > 500 | GitHub影响力 |
| C | 默认 | 无显著信号 |

> 评级优先级固定为：S > A+ > A > D > B+ > B > C

## 配置文件

- **公司/学校关键词**: `personal-ai-headhunter/data/company_tier_config.json`
  - `tier1_companies`: 一线大厂/AI公司
  - `tier2_companies`: 二线大厂
  - `top_labs`: 顶尖实验室（匹配即A）
  - `985_top20`: 985排名前20 + 海外顶尖（用于A级）
  - `985_universities`: 全部985 + 海外名校（用于B+/B级）

- **评级脚本**: `personal-ai-headhunter/batch_update_tiers.py`
- **人工覆盖**: 脚本内 `manual_overrides` 字典（最高优先级）

## 使用方法

### 1. 按来源重跑（推荐）

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

# GitHub 来源
python3 batch_update_tiers.py github

# 脉脉来源（需用内联代码）
python3 -c "
from database import SessionLocal, Candidate
from batch_update_tiers import auto_tier, _parse_tags, manual_overrides
from datetime import datetime
from collections import Counter

session = SessionLocal()
candidates = session.query(Candidate).filter(Candidate.source == '脉脉').all()
print(f'🔄 重新评级脉脉来源: {len(candidates)} 人')

for c in candidates:
    tags = _parse_tags(c.structured_tags)
    gh = tags.get('github_username', '')
    new_tier = manual_overrides[gh] if gh in manual_overrides else auto_tier(c)[0]
    c.talent_tier = new_tier
    c.tier_updated_at = datetime.now()

session.commit()
tier_dist = Counter(c.talent_tier for c in candidates)
for t in ['S','A+','A','B+','B','C','D']:
    if tier_dist.get(t,0) > 0: print(f'  {t}: {tier_dist[t]}')
print(f'  总计: {len(candidates)}')
session.close()
"
```

### 2. 全量重跑

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 batch_update_tiers.py all
```

### 3. 仅处理未分级

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 batch_update_tiers.py
```

### 4. 重跑昨日新增

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 batch_update_tiers.py yesterday
```

## 注意事项

1. **中文匹配**：985 列表已包含中文全称（如 `上海交通大学`）和简称（如 `上交大`），兼容 GitHub（英文）和脉脉（中文）两种数据源
2. **人工覆盖优先**：`manual_overrides` 中的评级不会被自动评级覆盖
3. **字段依赖**：评级依赖 `current_company`、`work_experiences`、`education_details`、`structured_tags`、`awards_achievements` 等字段的内容
4. **新增公司/学校**：编辑 `data/company_tier_config.json` 后重跑即可生效
