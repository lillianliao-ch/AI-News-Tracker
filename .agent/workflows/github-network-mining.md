---
description: 从AI猎头的GitHub Following网络中挖掘AI人才，包括采集、过滤、扩展、联系信息提取和自动Follow
---

# GitHub 社交网络挖掘 AI 人才

> ⚠️ **文档治理规则**
>
> GitHub Mining 项目**有且仅有**以下 2 个文档：
> 1. **本文件**: `github-network-mining.md` — 路线图 + Runbooks（做什么）
> 2. **参考文件**: `github-mining-reference.md` — 执行细节（怎么做）
>
> **规则**：
> - 🚫 **不得新建**其他 GitHub Mining 相关文档
> - ✅ 新信息必须**更新到这两个文件中**对应章节
> - 📍 分级标准**唯一以 reference 文档为准**

> 📄 **详细执行参考**: [github-mining-reference.md](file:///Users/lillianliao/notion_rag/.agent/workflows/github-mining-reference.md)
> 包含：爬取细节、分级标准、字段映射、评分公式、验证方法等

---

## 📍 路线图 (Roadmap)

| 阶段 | 名称 | 状态 | 结果 | 说明 |
|:---|:---|:---|:---|:---|
| Phase 1 | 种子采集 | ✅ 完成 | 6,081 人 | Neal12332 的 Following 列表 |
| Phase 2 | AI 相关性过滤 | ✅ 完成 | 3,723 AI 人才 | Tier A 1,027 / Tier B 2,508 |
| Phase 3 | 深度信息提取 + 评分 | ✅ 完成 | 3,723 人，邮箱 61.6% | commit邮箱、Top仓库、语言 |
| Phase 3.5 | 个人网站 + Scholar 深挖 | ✅ Top500 完成 | **500/1,027** (48.7%) | LinkedIn 42, Scholar 67, Twitter 136 |
| Phase 4 | 社交网络扩展 | ❌ 未开始 | — | 种子用户的Following交叉挖掘 |
| Phase 5 | 脉脉交叉匹配 | ❌ 未开始 | — | 补全手机号/微信 |
| Phase 6 | 入库猎头系统 | ✅ Top500 完成 | **486 人已入库** | 全部已分级(S27/A76/B+239/B130/C14) |
| Phase 7 | 个性化邮件触达 | ❌ 未开始 | — | 分层邮件模板 |
| Phase 8 | 持续跟进 + 关系维护 | ❌ 未开始 | — | GitHub Follow/脉脉/微信 |
| Phase 9 | 长期人才运营 | ❌ 未开始 | — | CRM Pipeline + 智能匹配 |

**当前重点**: Top 500 全流程完成 (Phase 3.5 → 导入 → 分级)，下一步可扩展至 Top 1000 或启动 Phase 7 邮件触达

> **💡 快速入库路径**: 可跳过 Phase 3.5 直接从 phase3_enriched.json 导入（基础字段完整度 70-100%），
> 后续用 `phase3_5 --resume` 批量补充数据，再用 DB 增强脚本更新到数据库。

---

## 前提准备

1. **GitHub Token**: Personal Access Token（Settings → Developer settings → Tokens (classic)，勾选 `public_repo` 和 `read:user`）
2. **脚本位置**: `/Users/lillianliao/notion_rag/github_network_miner.py`
3. **猎头系统**: `/Users/lillianliao/notion_rag/personal-ai-headhunter/`

---

## Runbook 1: 增量处理 N 个候选人 ⭐ 最常用

> 用户说「继续处理 20 个人」「再跑一批」时执行此流程
> **必须完整执行所有 5 个步骤，缺一不可**

### 步骤 1/5: 检查当前进度

```bash
cd /Users/lillianliao/notion_rag
python3 -c "
import json
d = json.load(open('github_mining/phase3_5_enriched.json'))
scraped = sum(1 for u in d if u.get('homepage_scraped'))
print(f'Phase 3.5 已处理: {len(d)} 人 (成功爬取: {scraped})')
"
```

记下当前人数 N。

### 步骤 2/5: Phase 3.5 爬取个人主页

```bash
cd /Users/lillianliao/notion_rag
python3 github_network_miner.py phase3_5 --top $((N + 20)) --resume
```

- `--top`: 设为 N + 新增数量（如已有 70 人，想加 20 人，则 --top 90）
- `--resume`: 跳过已处理的用户
- 耗时约 10-30 分钟（取决于网络和网站可达性）

### 步骤 3/5: 导入到猎头系统

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 import_github_candidates.py --file ../github_mining/phase3_5_enriched.json
```

- 自动去重（基于 GitHub username），已导入的会跳过
- 组织账号自动过滤

### 步骤 4/5: 自动分级

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 batch_update_tiers.py
```

- 分级标准详见 [reference 文档的「分级标准」章节](file:///Users/lillianliao/notion_rag/.agent/workflows/github-mining-reference.md)
- S/A/B/C 四级，对齐大厂 P 级体系

### 步骤 5/5: 验证结果

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 -c "
from database import SessionLocal, Candidate
from collections import Counter
session = SessionLocal()
all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
tier_dist = Counter(c.talent_tier for c in all_gh)
untiered = tier_dist.get(None, 0)
print(f'GitHub 候选人总数: {len(all_gh)}')
for tier in ['S', 'A', 'B', 'C']:
    print(f'  {tier}: {tier_dist.get(tier, 0)} 人')
if untiered > 0:
    print(f'  ⚠️ 未分级: {untiered} 人（需要重新运行步骤 4）')
else:
    print('✅ 全部已分级')
session.close()
"
```

**验证检查清单**:
- [ ] 新增候选人数是否正确
- [ ] 未分级人数为 0
- [ ] 无报错信息

### 最后: 更新路线图

完成后，更新本文件中「路线图」的 Phase 3.5 和 Phase 6 的数据。

---

## Runbook 2: 首次全量执行（Phase 1 → 3）

> 从零开始采集新的种子用户网络

### 步骤 1: 种子采集 (Phase 1)

```bash
cd /Users/lillianliao/notion_rag
python github_network_miner.py phase1 --target <GitHub用户名>
```

- 采集指定用户的全部 Following 列表
- 断点续传: `python github_network_miner.py phase1_resume`
- 产出: `github_mining/phase1_seed_users.json`

**验证**:
```bash
python github_network_miner.py verify1
```
- ✅ 总数与 GitHub 页面一致（±2%）
- ✅ username 无重复
- ✅ `name` 覆盖率 ≥ 80%

### 步骤 2: AI 相关性过滤 (Phase 2)

```bash
python github_network_miner.py phase2
```

- 通过 Bio/公司/仓库关键词过滤 AI 相关人才
- 输出分层: Tier A（强信号）、Tier B（中信号）
- 产出: `github_mining/phase2_ai_filtered.json`

**验证**:
```bash
python github_network_miner.py verify2
```
- ✅ Tier A 精确率 ≥ 90%
- ✅ Tier B 精确率 ≥ 70%

### 步骤 3: 深度信息提取 + 评分 (Phase 3)

```bash
python github_network_miner.py phase3
```

- 提取: 公开邮箱、commit 邮箱、Top 仓库、编程语言、Star 数
- 评分: AI 相关度 30% + 影响力 25% + 活跃度 20% + 可联系性 15% + 地域 10%
- 产出: `github_mining/phase3_enriched.json`

**验证**:
```bash
python github_network_miner.py verify3
```
- ✅ 邮箱覆盖率 ≥ 50%（排除 noreply）
- ✅ Top 20 人工审核通过率 ≥ 80%

### 步骤 4-6: 继续 Phase 3.5 → 导入 → 分级

完成 Phase 3 后，按 **Runbook 1** 执行增量处理流程。

---

## Runbook 3: 社交网络扩展 (Phase 4)

> 通过种子用户的 Following 交叉挖掘新人才

```bash
cd /Users/lillianliao/notion_rag
python github_network_miner.py phase4 --seed-top 300 --min-cooccurrence 3
```

- 采集 Top 300 种子用户的 Following 列表
- 被 ≥ 3 个种子用户共同 Follow 的新用户进入候选池
- 对新用户执行 AI 过滤 + 去重
- 产出: `github_mining/phase4_expanded.json`

**验证**:
```bash
python github_network_miner.py verify4
```
- ✅ 新发现 AI 人才 ≥ 2,000
- ✅ AI 精确率 ≥ 70%
- ✅ 共现 ≥ 5 的人应为业内知名人士

---

## Runbook 4: 脉脉交叉匹配 (Phase 5)

> 用脉脉补全手机号、微信、详细工作经历

**前置条件**: 浏览器登录脉脉 + 安装脉脉助手 Chrome 插件

**匹配策略（优先级）**:
1. 真名 + 公司名搜索（精确匹配率最高）
2. 邮箱前缀辅助验证
3. GitHub 用户名搜索

**补充字段**: 手机号、微信号、详细工作经历、教育背景、脉脉 ID

**验证**: Top 200 匹配率 ≥ 40%

---

## Runbook 5: 邮件触达 (Phase 7)

> 个性化邮件建立联系，核心目标：加微信

**邮件模板分层**:

| 层级 | 对象 | 个性化程度 | 关键策略 |
|:---|:---|:---|:---|
| Tier A | Top 200 | 完全个性化 | 提到具体项目名、Star 数、技术方向 |
| Tier B | 200-500 | 半模板化 | 提到公司和方向，邀请加入社群 |
| Tier C | 500+ | 标准模板 | 简短邀请 |

**发送策略**:
- 工作日上午 10:00-11:00 发送
- 先发 20 人测试 → 观察回复率 → 调整 → 全量
- 间隔 30-60 秒/封，3天无回复发 1 次 Follow-up
- **目标回复率**: Tier A ≥ 20%, Tier B ≥ 10%

**价值前置**: 不直接说"我是猎头"，提供行业报告/薪资数据/社群邀请作为交换

---

## Runbook 6: 长期运营 (Phase 8-9)

> 持续跟进和关系维护

**多渠道触达节奏**:

| 天数 | 动作 | 渠道 |
|:---|:---|:---|
| Day 0 | GitHub Follow + Star 热门项目 | GitHub |
| Day 1 | 第一封个性化邮件 | Email |
| Day 2 | 脉脉加好友 | 脉脉 |
| Day 4 | Follow-up 邮件（换角度） | Email |
| Day 7 | 脉脉打招呼（最后一次主动） | 脉脉 |
| 每月 | 行业资讯推送 | Email/微信 |

**候选人生命周期**:
```
未触达 → 已Follow → 已发邮件 → 已回复 → 已加微信 → 有岗位匹配 → 推荐中 → 成交
```

**系统未来需建设**:
- Pipeline Dashboard（各阶段候选人看板）
- 智能匹配通知（新 JD 自动匹配候选人）
- 邮件模板引擎（自动填充个性化变量）
- 候选人动态监控（GitHub 活动变化 → 触达时机）

---

## 关键注意事项

1. **Token 限流**: API 5,000 次/小时，限流时自动暂停等待重置
2. **多 Token 轮换**: 限流时用 `phase1_resume` 断点续传并切换 Token
3. **中间保存**: 脚本每 200 人自动保存，中断可恢复
4. **Follow 策略**: 只 Follow 评分 Top 30% 的 AI 人才，需 Classic Token
5. **数据安全**: 所有数据仅用于合法招聘目的
