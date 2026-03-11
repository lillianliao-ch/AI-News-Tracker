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
| ~~Phase 2~~ | ~~AI 过滤 (Legacy)~~ | ⚠️ 已废弃 | ~~3,723~~ | 仅靠 bio 过滤，误杀 2358 人。已被 V3 替代 |
| **Phase 2 V3** | **全量轻富化** | ✅ 完成 | 6,081 | 对全部 6081 人做 Repo+网站探活+Scholar |
| **Phase 3 V3** | **统一 AI 判定** | ✅ 完成 | ~2,000 | 多维信号一次性筛选（bio+repo+scholar+语言） |
| Phase 3/3.5 | 深度富化 | ✅ 完成 | 3,723 人 | 仅对 AI 人才执行网站爬取+Scholar |
| **Phase 4** | **社交网络扩展** | ✅ 完成 | **892 人** | 262 种子(S/A+/A)共现分析，发现新 AI 人才 |
| **Phase 4 富化** | **Phase 3+3.5 补强** | ✅ 完成 | 892 人 | `run_phase4_enrichment.py` 无人值守执行完成 |
| **Phase 4.5** | **LLM 深度富化** | **✅ 新增** | **2,476 人** | **在导入前进行 LLM 智能提取（工作履历/教育/技能/谈话点）** |
| Phase 5 | 入库+统一评级打标 | ✅ 完成 | 4,043 人 | S/A/B/C + V2 标签，新增 `tier_updated_at` |
| **Phase 5 V2** | **多轮社交网络扩展** | **[/] 进行中** | **28,242 人** | **从高质量种子再次延展，无人值守端到端富化入库后台运行中** |
| Phase 6 | 分层触达 | ✅ 引擎就绪 | V2 Prompt | LinkedIn/邮件按标签智能选模板 |
| Phase 6.5 | 网站内容价值提取 | ✅ Phase 2 完成 | 5,193 人 | 从个人网站提取结构化数据 (工作履历/技能/教育) |
| Phase 7 | 持续跟进 | [/] 进行中 | — | CRM + Nurture (邮件触达 P1/P2 已开始) |

**Phase 6 入库执行记录**:
| 日期 | 批次 | 说明 |
|:---|:---|:---|
| 2/08 | Phase 3.5 Top500 首批 | 测试性导入 19 人 |
| 2/09 - 2/11 | Phase 3 全量 | 累计导入约 3,604 人 |
| 2/15 | Phase 3.5 大规模拓展 | 借助 Lamda Scraper 工具全量网站深挖，有效入库 3,167 人 |
| 2/24 | **Phase 4 全量入库** | **完成 892 人富化加分、入库及 Tier 分级，全量入库 4,043 人** |
| 2/27 - 2/28 | **Phase 4 大规模扩展** | **从 B 级种子(5,435) + 今日导入(2,094) 扩展，发现 15,645 人，入库 10,061 人，DB 增长 165% (6,076→16,137)** |

**Phase 4.5 LLM 深度富化执行记录**:
| 日期 | 阶段 | 说明 |
|:---|:---|:---|
| 3/02 | **小规模测试** | **20 样本：LLM更优 80%，平均提升 +18.6 分** |
| 3/02 - 3/03 | **批量处理** | **2,476 人：成功率 99.9%，提升率 95.3%，平均质量分 95.1** |
| 3/03 | **流程集成** | **集成到 Phase 4 富化流程，在导入前执行** |
| 3/08 | **0308 批次** | **1,105 人富化：成功 1,033 (93.5%)，高质量 208 (20.1%)，新增 10 人**。详见 [参考文档 Section 7](file:///Users/lillianliao/notion_rag/.agent/workflows/github-mining-reference.md#2026-03-08-phase-45--1105-人-llm-富化--数据库导入) |

**Phase 6.5 网站内容价值提取执行记录**:
| 日期 | 阶段 | 说明 |
|:---|:---|:---|
| 3/01 | **Option A: 验证完成** | **100 样本分析：45% 网站有价值，技能提取 55%，工作履历 34%** |
| 3/02 | **Option B: Phase 1** | **增强版提取脚本：技能库 100+，中文支持，教育/项目提取** |
| 3/02 | **Option B: Phase 2 ✅** | **批量处理 8,434 人：5,193 个有价值网站 (61.6%)，工作履历 94%，技能 78%，平均 4分13秒** |
| 3/02 | **Option B: Phase 3 ✅** | **数据库集成完成：6 个新字段，8,434 条记录成功导入，平均质量分 39.4** |

**Phase 5 V2 多轮社交网络扩展执行记录**:
| 日期 | 批次 | 说明 |
|:---|:---|:---|
| 3/10 | **端到端流程** | **对 28,242 人进行端到端全量处理 (`run_phase5_end_to_end.sh`)。目前正在执行第一个环节（Phase 3 富化）。执行结束后将自动爬取网站并LLM富化后导入数据库。** |

**种子批次备份记录**:
| 日期 | 备份文件 | 原始种子 | 说明 |
|:---|:---|:---|:---|
| 2/24 | `github_mining/phase1_seed_users_backup_20260224.json` | Neal12332 Following | 启动新 seed 批次前备份，共 6,081 人 |

> 📌 **规则**：每次启动新 seed 批次（Runbook 2）前，必须先备份当前 `phase1_seed_users.json`，命名格式为 `phase1_seed_users_backup_YYYYMMDD.json`，并在上表中记录。

**当前重点**: 
1. **全量触达** — 针对 4000+ 带 Draft 的候选人启动批量发送。
2. **Phase 4 常驻化** — 利用 `run_phase4_followup_daemon.sh` 在后台持续自动发现并富化新人才。

> **Phase 2 淘汰的人员**: 未满足 AI 相关性的人员已排除，不再处理。

> **Phase 2 淘汰的 2,358 人**: 这些是 Neal 的 Following 中**非AI相关**的用户（前端/后端/运维/学生等），已在 Phase 2 通过 AI 关键词过滤排除，不建议再处理。

---

## 前提准备

### 1. GitHub Token 配置（重要）

> ⚠️ **所有需要调用 GitHub API 的脚本都依赖 Token。Token 缺失会导致脚本反复报错退出。**

Token 加载优先级（脚本按此顺序查找，找到即停）：

| 优先级 | 来源 | 说明 |
|:---|:---|:---|
| 1 | 环境变量 `GITHUB_TOKEN` | 临时生效，终端关闭即失效 |
| 2 | 配置文件 `github_hunter_config.py` | **推荐**，永久生效，所有脚本共享 |
| 3 | 命令行 `--token` 参数 | 仅对单次命令生效 |

**推荐方式：写入配置文件（一次配置，永久生效）**

配置文件路径：`/Users/lillianliao/notion_rag/github_mining/scripts/github_hunter_config.py`

```python
GITHUB_CONFIG = {
    # 多 token 用逗号分隔，支持自动轮换（每个 token 5000次/小时）
    "token": "ghp_token1,ghp_token2,ghp_token3",
    ...
}
```

**验证 Token 是否可用**：

```bash
cd /Users/lillianliao/notion_rag/github_mining/scripts
python3 -c "
from github_hunter_config import GITHUB_CONFIG
token = GITHUB_CONFIG.get('token', '')
if not token:
    print('❌ Token 未配置！请编辑 github_hunter_config.py')
else:
    tokens = [t.strip() for t in token.split(',') if t.strip()]
    print(f'✅ Token pool: {len(tokens)} 个')
    for i, t in enumerate(tokens):
        print(f'  Token {i+1}: {t[:15]}...{t[-4:]}')
"
```

**Token 获取方式**：GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens，勾选 `public_repo` 和 `read:user`

**当前配置**：3 个 token 轮换，总速率 15,000 次/小时

### 2. 其他依赖

- **采集脚本位置**: `/Users/lillianliao/notion_rag/github_mining/scripts/github_network_miner.py`
- **猎头系统**: `/Users/lillianliao/notion_rag/personal-ai-headhunter/`
- **系统操作脚本**: `personal-ai-headhunter/import_github_candidates.py`, `scripts/label_github_candidates.py`, `scripts/fetch_github_bios.py`

---

## Runbook 1: 增量处理 N 个候选人 ⭐ 最常用

> 用户说「继续处理 20 个人」「再跑一批」时执行此流程
> **必须完整执行所有 5 个步骤，缺一不可**

### 步骤 1/5: 检查当前进度

```bash
cd /Users/lillianliao/notion_rag
python3 -c "
import json
d = json.load(open('github_mining/scripts/github_mining/phase3_5_enriched.json'))
scraped = sum(1 for u in d if u.get('homepage_scraped'))
print(f'Phase 3.5 已处理: {len(d)} 人 (成功爬取: {scraped})')
"
```

同时检查 Priority 标签分布：
```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 -c "
from database import SessionLocal, Candidate
from collections import Counter
session = SessionLocal()
all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
label_dist = Counter()
for c in all_gh:
    labels = (c.talent_labels or '').split(',')
    for l in labels:
        l = l.strip()
        if l.startswith('github-p'): label_dist[l] += 1
for k, v in sorted(label_dist.items()): print(f'  {k}: {v}')
print(f'  总计: {len(all_gh)} 人')
session.close()
"
```

记下当前人数 N。

### 步骤 2/5: Phase 3.5 爬取个人主页

```bash
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase3_5 --top $((N + 20)) --resume
```

- `--top`: 设为 N + 新增数量（如已有 70 人，想加 20 人，则 --top 90）
- `--resume`: 跳过已处理的用户
- 耗时约 10-30 分钟（取决于网络和网站可达性）

### 步骤 3/5: 导入到猎头系统

> ⚠️ **致命警告**：**必须** `cd` 进入 `personal-ai-headhunter` 目录下执行后续脚本！因为 `.env` 里的 `DB_PATH=data/headhunter_dev.db` 是相对路径，如果在根目录跑，系统会在根目录凭空造出一个影子数据库并把数据倒进去！

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 import_github_candidates.py --file ../github_mining/scripts/github_mining/phase3_5_enriched.json
```

- 自动去重（基于 GitHub username），已导入的会跳过
- 组织账号自动过滤

### 步骤 4/5: 自动分级

> 脚本 `batch_update_tiers.py` 现已**纯净化**，只会对数据库中已存在的人员进行打分，不会再越俎代庖去偷偷读取 json 文件执行暗箱导入（为防混入旧垃圾数据）。

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 batch_update_tiers.py
```

- 分级标准详见 [reference 文档的「分级标准」章节](file:///Users/lillianliao/notion_rag/.agent/workflows/github-mining-reference.md)
- S/A+/A/B+/B/D 六级，对齐大厂 P 级体系，非 AI 者强制打入 D 级。

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

## Runbook 1.5: V3 Simplified Routing Architecture (代替旧 Phase 6.5)

> 核心思想：摒弃复杂的 `github-p1/p2/p3` 标签，回归数据库字段本身。Tier 决定质量，字段决定触达渠道。

### 1. 字段级路由法则

| 触达方式 | 核心触达群 | 路由条件 (api_server.py 判定) |
|:---|:---|:---|
| **LinkedIn 推岗** | 最优质双栖人才 | `linkedin_url` 存在 && Tier ∈ (S, A+, A, B+) |
| **LinkedIn 交友** | 潜力双栖人才 | `linkedin_url` 存在 && Tier ∈ (B, C, D) |
| **学术套瓷邮件** | 顶刊/高校学者 | `personal_website` 包含 `scholar.google` / `.edu` |
| **硬核切磋邮件** | 开源大佬 | `structured_tags.github_score` ≥ 50 |
| **深度定制邮件** | 有个人主页者 | 兜底逻辑：调用大模型总结 `website_content` |
| **基础调研邮件** | 纯 GitHub+Gmail | 啥都没有，拿 bio 硬聊 |

### 2. 特殊标签

`talent_labels` 仅保留极其特殊的标记，不再用于路由：
- `google-scholar`：自动打标，用于前端快速筛选学者
- 人工标签例如 "重点关注", "暂不联系" 等

### 步骤 1.5: P3 盲盒队列抢救 (Repo Screening)

针对学历/厂牌背景极佳 (A, A+, B, B+) 但被初始标记为 `github-p3-observe` 的人才：

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

# 先预览
python3 scripts/scrub_p3_repos.py --dry-run

# 确认无误后执行 (会自动调 GitHub API 抓取 Top 3 仓库)
python3 scripts/scrub_p3_repos.py
```

**运行结果**:
- 命中 AI/Python 特征的会被打上 `github-p2-repo-active` 标签，捞回触达池。
- 未命中特征的将导出为 `p3_review_sample.csv`，抽查 10% 确认无误后在 DB 中全盘标记 `Skip`。

### 步骤 2: Bio 二次筛选（需要 GitHub Token）

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

# 用多 Token 加速（3 tokens × 5,000 = 15,000 requests/hr）
GITHUB_TOKENS='token1,token2,token3' python3 scripts/fetch_github_bios.py --dry-run
GITHUB_TOKENS='token1,token2,token3' python3 scripts/fetch_github_bios.py

# 后续可从缓存重跑（调整关键词后不需要再调 API）
python3 scripts/fetch_github_bios.py --from-cache --dry-run
python3 scripts/fetch_github_bios.py --from-cache
```

**Bio 分类逻辑**:
- Bio 含 AI 关键词 → 升级 P2
- Bio 明确非 AI（前端/Android/DevOps 等）→ 标记 Skip 删除
- 无 Bio → 保留 P3

**数据缓存**: Bio 数据保存在 `data/github_bios.json`，支持离线重分类。

### 步骤 3: 验证

```bash
python3 -c "
from database import SessionLocal, Candidate
from collections import Counter
session = SessionLocal()
all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
label_dist = Counter()
for c in all_gh:
    for l in (c.talent_labels or '').split(','):
        l = l.strip()
        if l.startswith('github-p'): label_dist[l] += 1
for k, v in sorted(label_dist.items()): print(f'  {k}: {v}')
print(f'总计: {len(all_gh)} 人')
session.close()
"
```

- ✅ P1 + P2 + P3 = 总数
- ✅ 无未标签的 GitHub 候选人

---

## 📖 完整流程图解

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Mining 完整流程                        │
└─────────────────────────────────────────────────────────────────┘

方案 A: 旧流程 (Phase 1 → 2 → 3 → 3.5)  ⚠️ 不推荐
┌────────┐   ┌────────┐   ┌────────┐   ┌──────────┐
│Phase 1 │──▶│Phase 2 │──▶│Phase 3 │──▶│Phase 3.5 │
│种子采集 │   │AI过滤  │   │深度富化│   │主页爬取  │
│~6100人 │   │~3700人 │   │~3700人 │   │300人    │
│1-2小时 │   │1分钟   │   │2-3小时│   │1-2小时  │
└────────┘   └────────┘   └────────┘   └──────────┘
              ❌ 误杀多  ❌ 慢     ✅ 准确

方案 B: V3 流程 (Phase 1 → 2V3 → 3V3 → 3.5)  ⭐ 推荐
┌────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Phase 1 │──▶│Phase 2V3 │──▶│Phase 3V3 │──▶│Phase 3.5 │
│种子采集 │   │全量轻富化│   │统一AI判定│   │主页爬取  │
│~6100人 │   │~6100人   │   │~1500人  │   │300人    │
│1-2小时 │   │1-2小时  │   │<1分钟  │   │1-2小时  │
└────────┘   └──────────┘   └──────────┘   └──────────┘
              ✅ 全覆盖  ✅ 快     ✅ 准确

总计耗时: 3-5 小时 (vs 旧流程 6-8 小时)
预期产出: 300 人高质量 AI 人才，邮箱覆盖率 60-80%
```

**关键区别**:
1. **Phase 2 V3** 对全部 6,100 人轻富化，而不是先过滤再富化
2. **多维信号**: Bio + Repo + Scholar + 语言，减少误杀
3. **更快**: API 请求减少 60%，总耗时缩短 40%

---

## Runbook 2: 首次全量执行（推荐 V3 快速流程）⭐

> 从零开始采集新的种子用户网络
>
> **重要**: V3 流程比旧流程更快、更准确，强烈推荐使用！

### 方案对比

| 方案 | 流程 | 耗时 | 准确率 | 推荐度 |
|:---|:---|:---|:---|:---|
| **方案 A（旧流程）** | Phase 1 → Phase 2 → Phase 3 → Phase 3.5 | 4-6 小时 | 70% | ⚠️ 不推荐 |
| **方案 B（V3 流程）** | Phase 1 → Phase 2 V3 → Phase 3 V3 → Phase 3.5（手动串联） | 2-3 小时 | 85% | ✅ 可用 |
| **方案 C（全自动）** | Phase 1 → `run_new_seed_pipeline.sh`（自动完成后续所有步骤） | 2-3 小时 | 85% | ⭐ **强烈推荐** |

**方案 C 优势（相比 B）**:
- ✅ **全程无人值守**: Phase 1 跑完后一键接管，无需手动串联各步骤
- ✅ **内建断点续传**: 通过 `pipeline_new_seed_state.json` 记录各步完成状态，崩溃后重启自动跳过已完成步骤
- ✅ **每步自动重试**: 最多 5 次重试，30s 间隔，网络闪断自动恢复
- ✅ **支持跳步重跑**: `START_FROM=phase3_5` 可从任意步骤重新开始

---

### 方案 C: 全自动无人值守流水线 ⭐ **强烈推荐**

> 🗂️ 脚本路径: `github_mining/scripts/run_new_seed_pipeline.sh`

#### 前置: Phase 1 种子采集（仍需手动触发）

```bash
# ⚠️ 每次启动新 seed 批次前，必须先备份并记录！
cp github_mining/phase1_seed_users.json \
   github_mining/phase1_seed_users_backup_$(date +%Y%m%d).json

cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase1 --target <GitHub用户名>
```

Phase 1 中断续传:
```bash
python3 github_mining/scripts/github_network_miner.py phase1_resume
```

#### Phase 1 完成后: 一键启动全自动流水线

```bash
cd /Users/lillianliao/notion_rag

# 后台无人值守（推荐，睡前启动，醒来看结果）
nohup bash github_mining/scripts/run_new_seed_pipeline.sh \
  > github_mining/scripts/github_mining/pipeline_seed.log 2>&1 &

# 实时监控进度
tail -f github_mining/scripts/github_mining/pipeline_seed.log
```

**高级参数**:
```bash
# 调整 Phase 3.5 爬取数量（默认 Top 500）
PHASE35_TOP=300 bash github_mining/scripts/run_new_seed_pipeline.sh

# 从指定步骤重新运行（断点恢复）
START_FROM=phase3_5 bash github_mining/scripts/run_new_seed_pipeline.sh
# 可选值: phase2_v3 | phase3_v3 | phase3_5 | import | tier

# Phase 1 已跑完，直接从 Phase 2 开始（跳过 Phase 1 检查）
SKIP_PHASE1=1 bash github_mining/scripts/run_new_seed_pipeline.sh
```

**流水线各步骤**:

| 步骤 | 内容 | 断点续传 | 自动重试 |
|:---|:---|:---|:---|
| Phase 2 V3 | 全量轻富化（邮箱/Scholar/AI仓库） | ✅ `--resume` | ✅ 5次 |
| Phase 3 V3 | 多维 AI 相关性判定 | - | ✅ 5次 |
| Phase 3.5 | 个人主页深度爬取 | ✅ `--resume` | ✅ 5次 |
| 入库 | 导入猎头数据库（自动去重） | ✅ 幂等 | ✅ 5次 |
| 分级 | Tier S/A/B/C 评分 | ✅ 幂等 | ✅ 5次 |

**状态文件**: `github_mining/scripts/github_mining/pipeline_new_seed_state.json`

---

### 方案 B: V3 手动流程（仅供参考）

#### 步骤 1: Phase 1 种子采集

```bash
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase1 --target <GitHub用户名>
```

- 采集指定用户的全部 Following 列表
- 建议：选择 AI 领域知名开发者（如 OpenAI、Anthropic、Hugging Face 核心开发者）
- 预期产出: ~6,100 人基础资料
- 耗时: 1-2 小时
- 产出: `github_mining/phase1_seed_users.json`

**验证**:
```bash
python3 github_mining/scripts/github_network_miner.py verify1
```
- ✅ 总数与 GitHub 页面一致（±2%）
- ✅ username 无重复
- ✅ `name` 覆盖率 ≥ 80%

#### 步骤 2: Phase 2 V3 全量轻富化

```bash
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase2_v3
```

- 对全部 6,100 人进行轻量级富化：
  - 从 GitHub events 提取邮箱
  - 检测主语言（是否 Python）
  - 网站探活（是否可访问）
  - 检测 Google Scholar
  - 统计 AI 相关仓库数量
- 支持断点续传: `python3 github_mining/scripts/github_network_miner.py phase2_v3 --resume`
- 预期产出: ~6,100 人富化数据
- 耗时: 1-2 小时
- 产出: `github_mining/scripts/github_mining/phase2_v3_enriched.json`

**验证**:
```bash
# 检查输出统计
python3 -c "
import json
d = json.load(open('github_mining/scripts/github_mining/phase2_v3_enriched.json'))
print(f'总人数: {len(d)}')
print(f'有邮箱: {sum(1 for u in d if u.get(\"all_emails\"))}')
print(f'有 Scholar: {sum(1 for u in d if u.get(\"has_scholar\"))}')
print(f'有活跃网站: {sum(1 for u in d if u.get(\"website_status\") == \"active\")}')
"
```

#### 步骤 3: Phase 3 V3 统一 AI 判定

```bash
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase3_v3
```

- 基于多维信号重新判定 AI 相关性：
  - **Bio 信号** (1.5 分): AI 关键词、AI 公司、顶尖学校
  - **Repo 信号** (2.0 分): AI 仓库数量、主语言是否 Python
  - **Scholar 信号** (3.0 分): 有 Google Scholar
  - **语言信号** (1.0 分): 主要语言为 Python
  - **影响力** (0.3-1.0 分): followers ≥ 100
- 判定阈值: score ≥ 1.5 → AI 候选人
- 预期产出: ~1,000-2,000 人 AI 人才
- 耗时: <1 分钟
- 产出: `github_mining/scripts/github_mining/phase3_v3_ai_candidates.json`

**验证**:
```bash
# 检查筛选结果
python3 -c "
import json
ai = json.load(open('github_mining/scripts/github_mining/phase3_v3_ai_candidates.json'))
rej = json.load(open('github_mining/scripts/github_mining/phase3_v3_rejected.json'))
print(f'AI 相关: {len(ai)} 人 ({len(ai)*100//(len(ai)+len(rej))}%)')
print(f'非 AI:   {len(rej)} 人')
"
```

#### 步骤 4: Phase 3.5 深度爬取个人主页

```bash
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase3_5 --top 300 --input phase3_v3_ai_candidates.json --resume
```

- 只对 Top 300 AI 候选人爬取个人主页
- 提取: 当前职位、工作经历、教育背景、额外邮箱、LinkedIn、顶会论文数量
- 支持断点续传: 中断后重新运行相同命令即可继续
- 预期产出: 300 人深度数据（邮箱覆盖率可达 60-80%）
- 耗时: 30-60 分钟
- 产出: `github_mining/scripts/github_mining/phase3_5_enriched.json`

**验证**:
```bash
# 检查 Phase 3.5 结果
python3 -c "
import json
d = json.load(open('github_mining/scripts/github_mining/phase3_5_enriched.json'))
scraped = sum(1 for u in d if u.get('homepage_scraped'))
has_linkedin = sum(1 for u in d if u.get('linkedin_url'))
has_title = sum(1 for u in d if u.get('current_title'))
print(f'Phase 3.5 总人数: {len(d)}')
print(f'成功爬取主页: {scraped} 人')
print(f'有 LinkedIn: {has_linkedin} 人')
print(f'有职位信息: {has_title} 人')
"
```

#### 步骤 5-7: 导入 → 分级 → 标签

完成 Phase 3.5 后，按 **Runbook 1** 执行增量处理，再按 **Runbook 1.5** 打标签。

---

### 方案 A: 旧流程（不推荐，仅供参考）

> ⚠️ 已被 V3 流程替代，仅保留作为参考

### 步骤 1: 种子采集 (Phase 1)

```bash
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase1 --target <GitHub用户名>
```

- 采集指定用户的全部 Following 列表
- 断点续传: `python3 github_mining/scripts/github_network_miner.py phase1_resume`
- 产出: `github_mining/phase1_seed_users.json`

**验证**:
```bash
python3 github_mining/scripts/github_network_miner.py verify1
```
- ✅ 总数与 GitHub 页面一致（±2%）
- ✅ username 无重复
- ✅ `name` 覆盖率 ≥ 80%

### 步骤 2: AI 相关性过滤 (Phase 2)

```bash
python3 github_mining/scripts/github_network_miner.py phase2
```

- 通过 Bio/公司/仓库关键词过滤 AI 相关人才
- 输出分层: Tier A（强信号）、Tier B（中信号）
- 产出: `github_mining/phase2_ai_filtered.json`

**验证**:
```bash
python3 github_mining/scripts/github_network_miner.py verify2
```
- ✅ Tier A 精确率 ≥ 90%
- ✅ Tier B 精确率 ≥ 70%

### 步骤 3: 深度信息提取 + 评分 (Phase 3)

```bash
python3 github_mining/scripts/github_network_miner.py phase3
```

- 提取: 公开邮箱、commit 邮箱、Top 仓库、编程语言、Star 数
- 评分: AI 相关度 30% + 影响力 25% + 活跃度 20% + 可联系性 15% + 地域 10%
- 产出: `github_mining/phase3_enriched.json`

**验证**:
```bash
python3 github_mining/scripts/github_network_miner.py verify3
```
- ✅ 邮箱覆盖率 ≥ 50%（排除 noreply）
- ✅ Top 20 人工审核通过率 ≥ 80%

### 步骤 4-6: 继续 Phase 3.5 → 导入 → 分级 → 标签

完成 Phase 3 后，按 **Runbook 1** 执行增量处理，再按 **Runbook 1.5** 打标签。

---

## Runbook 3: 社交网络扩展 (Phase 4)

> 通过高质量种子的 Following 交叉挖掘新人才
>
> **核心理念**：从已验证的高质量候选人（S/A+/A tier）出发，挖掘他们社交网络中的隐藏人才
> **前置条件**：✅ 已完成 Phase 5（入库+分级），数据库中有 tier 标签

---

### 步骤 1/5: 选择种子用户

**种子选择标准**（质量优先）:

| 优先级 | Tier | 描述 | 预期数量 |
|:---|:---|:---|:---|
| 1 | S | 行业领军（Followers>5k 或 Stars>5k） | ~30-50 人 |
| 2 | A+ | 学术/技术强者（3+顶会论文） | ~100-200 人 |
| 3 | A | 顶尖Lab（通义/MSRA/Seed等） | ~500-1000 人 |
| 4 | B+ | 一线+名校（可选，用于快速扩展） | ~2000+ 人 |

**从数据库导出种子**:

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 -c "
from database import SessionLocal, Candidate
import json

session = SessionLocal()

# 选择 S/A+/A tier 的候选人
seeds = session.query(Candidate).filter(
    Candidate.source == 'github',
    Candidate.talent_tier.in_(['S', 'A+', 'A']),
    Candidate.github.isnot(None)
).all()

# 提取 GitHub username（从 github URL 中解析）
seed_usernames = []
for s in seeds:
    if s.github:
        # 从 https://github.com/username 提取 username
        username = s.github.strip('/').split('/')[-1]
        seed_usernames.append(username)

# 保存到文件
with open('../github_mining/phase4_seeds.json', 'w') as f:
    json.dump(seed_usernames, f, indent=2)

print(f'✅ 导出种子: {len(seed_usernames)} 人')
print(f'   S/A+/A 分布: S={sum(1 for s in seeds if s.talent_tier==\"S\")}, A+={sum(1 for s in seeds if s.talent_tier==\"A+\")}, A={sum(1 for s in seeds if s.talent_tier==\"A\")}')
session.close()
"
```

**预期输出**:
```
✅ 导出种子: 264 人
   S/A+/A 分布: S=37, A+=5, A=222
```

---

### 步骤 2/5: 执行社交网络扩展

> ⚠️ **重要**: Phase 4 是长时间任务（2-6 小时），建议使用自动重启包装器实现"无人值守"

#### 选项 A: 标准模式（适合白天监控）

```bash
cd /Users/lillianliao/notion_rag

# 标准模式（使用导出的种子文件）
python3 github_mining/scripts/github_network_miner.py phase4 \
  --seeds-file github_mining/phase4_seeds.json \
  --min-cooccurrence 3

# 或使用简化版（从数据库自动选择 Top N）
python3 github_mining/scripts/github_network_miner.py phase4 \
  --seed-tier S,A+,A \
  --seed-top 264 \
  --min-cooccurrence 3
```

**缺点**: 如果网络闪断或 API 异常，脚本会崩溃，需要人工手动重启

#### 选项 B: 自动重启模式（推荐，适合夜间运行）⭐

```bash
cd /Users/lillianliao/notion_rag

# 前台运行（自动重启）
python3 github_mining/scripts/auto_restart_wrapper.py -- \
  python3 github_mining/scripts/github_network_miner.py phase4 \
  --seed-tier S,A+,A \
  --seed-top 264 \
  --min-cooccurrence 3

# 后台运行（真正的无人值守）
nohup python3 github_mining/scripts/auto_restart_wrapper.py -- \
  python3 github_mining/scripts/github_network_miner.py phase4 \
  --seed-tier S,A+,A \
  --seed-top 264 \
  --min-cooccurrence 3 > /dev/null 2>&1 &

# 查看自动重启日志
tail -f github_mining/auto_restart.log
```

**自动重启包装器的优势**:
- ✅ 网络闪断自动恢复
- ✅ API 502 错误自动重试
- ✅ 临时故障自动重启
- ✅ 真正的"睡眠自由" - 睡前启动，醒来查看结果
- ✅ 配合断点续传机制，不会重复处理

**自动重启日志示例**:
```
[2026-02-23 22:00:00] 🚀 自动重启包装器启动
[2026-02-23 22:00:00] 📝 执行命令: python3 github_network_miner.py phase4 --seed-top 264
[2026-02-23 22:00:00] 🔄 启动任务（第 1 次尝试）
...
[2026-02-24 02:13:45] ⚠️  任务异常退出（返回码: 1）
[2026-02-24 02:13:45] 🔁 30 秒后自动重启（第 1/100 次）...
[2026-02-24 02:14:15] 🔄 继续执行（将自动从断点恢复）
[2026-02-24 02:14:15] 🔄 启动任务（第 2 次尝试）
...
[2026-02-24 08:30:22] ✅ 任务成功完成！
```

---

**参数说明**:

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--seeds-file` | - | 种子用户列表文件（JSON array） |
| `--seed-tier` | S,A+,A | 按 tier 选择种子（逗号分隔） |
| `--seed-top` | 300 | 限制种子数量 |
| `--min-cooccurrence` | 3 | 最小共现次数（越高越精准） |

**共现次数建议**:

| 共现次数 | 预期质量 | 适用场景 | 预期产出 |
|:---|:---|:---|:---|
| 2+ | 宽松 | 快速扩大人才池 | 种子数的 20-30 倍 |
| **3+** | **平衡** | **推荐**，质量与数量平衡 | **种子数的 10-20 倍** |
| 5+ | 严格 | 挖掘业内领袖级人物 | 种子数的 3-5 倍 |

**执行过程**:
1. 采集每个种子的 Following 列表
2. 统计被多个种子共同 Follow 的新用户
3. 自动去重（排除已存在的用户）
4. 对新用户执行 AI 过滤
5. 产出: `github_mining/scripts/github_mining/phase4_expanded.json`

**预期耗时**: 2-6 小时（取决于种子数量和网速）

---

### 步骤 3/5: 验证结果

```bash
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py verify4
```

**验收标准**:

| 指标 | 目标 | 说明 |
|:---|:---|:---|
| 新发现 AI 人才 | ≥ 2,000 | 或种子的 5 倍以上 |
| AI 精确率 | ≥ 70% | 人工抽检 50 人验证 |
| 高共现人物质量 | Top级 | 共现 ≥ 5 的人应为业内知名 |

**查看结果分布**:

```bash
cd /Users/lillianliao/notion_rag
python3 -c "
import json
from collections import Counter

with open('github_mining/scripts/github_mining/phase4_expanded.json') as f:
    data = json.load(f)

print(f'📊 Phase 4 结果统计')
print(f'=' * 50)
print(f'总发现: {len(data)} 人')

# 共现分布
co = Counter(u.get('cooccurrence', 0) for u in data)
print(f'\n共现分布:')
for count in sorted(co.keys(), reverse=True):
    print(f'  {count}+ 人共同关注: {co[count]} 人')

# Tier 分布（如果有）
if any('tier' in u for u in data):
    tiers = Counter(u.get('tier', 'Unknown') for u in data)
    print(f'\n预估 Tier 分布:')
    for tier in ['S', 'A+', 'A', 'B+', 'B', 'C']:
        if tier in tiers:
            print(f'  {tier}: {tiers[tier]} 人')
"
```

---

### 步骤 4/5: Phase 3 + 3.5 深度富化（无人值守 + 断点续传 + 自动验证）

> Phase 4 产出的 892 人只有基础 GitHub 信息，必须经过 Phase 3（仓库）和 Phase 3.5（主页/LinkedIn/论文）补强才能使用。

#### 脚本: `run_phase4_enrichment.py`

**崩溃恢复机制**:
- `pipeline_state.json` 记录每步完成状态，崩溃重启后跳过已完成步骤
- Phase 3/3.5 均传 `resume=True`，每 50 人自动保存，崩溃后从断点继续
- 每步完成后自动验证数据质量（人数、字段覆盖率），不合格则 exit(1) 触发重试

**自动验证标准**:

| 阶段 | 验证项 | 阈值 |
|:---|:---|:---|
| Phase 3 | 人数 ≥ 预期 90% | 必须 |
| Phase 3 | Stars 覆盖率 | ≥ 90% |
| Phase 3.5 | 人数 ≥ 预期 90% | 必须 |
| Phase 3.5 | homepage_scraped 标记 | ≥ 50% |
| 入库 | 导入猎头系统数据库 | 自动去重 |
| 分级 | Tier 标签覆盖 | 未分级人数 = 0 |

**启动命令（无人值守）**:

```bash
cd /Users/lillianliao/notion_rag

# ✅ 推荐：全链路端到端（Phase 4 爬取 + 富化 + 入库 + 分级，真正一键无人值守）
nohup bash github_mining/scripts/run_phase4_full_pipeline.sh \
  > /tmp/phase4_pipeline.log 2>&1 &
tail -f /tmp/phase4_pipeline.log

# 可选参数（环境变量形式）：
# SEED_TOP=300        种子数量（默认 300）
# MIN_CO=3            最小共现次数（默认 3）
# SEED_TIER=S,A       按 Tier 选种子（空=从文件取）
# SKIP_PHASE4=1       跳过爬取，直接用已有 phase4_expanded.json

# 旧方式（仅富化后半段，Phase 4 爬取需手动完成）：
cd /Users/lillianliao/notion_rag/github_mining/scripts
bash run_phase4_followup_daemon.sh
```

**各脚本对比**:

| 脚本 | 覆盖范围 | 断点续传 | 自动重启 |
|:---|:---|:---|:---|
| `run_phase4_full_pipeline.sh` | **Phase4爬取 + 富化 + 入库 + 分级（全链路）** | ✅ | ✅ |
| `run_phase4_followup_daemon.sh` | 富化 + 入库 + 分级（Phase4后半段，需手动先跑爬取） | ✅ | ✅ |

**查看进度**:

```bash
# 全链路日志
tail -f /tmp/phase4_pipeline.log

# 流水线状态
cat github_mining/scripts/github_mining/pipeline_state_phase4.json
cat github_mining/scripts/github_mining/pipeline_state.json
```


**产出文件**:

| 文件 | 说明 |
|:---|:---|
| `phase3_from_phase4.json` | Phase 3 补强输出（repos/stars/languages/emails） |
| `phase4_final_enriched.json` | 最终完整数据（repos + LinkedIn + 经历 + 论文） |
| `pipeline_state.json` | enrichment 流水线状态（断点续传用） |
| `pipeline_state_phase4.json` | 全链路流水线状态（包含 Phase 4 爬取步骤） |
| `batch_report_phase4_{timestamp}.json` | **批次报告**（每阶段关键指标，用于数据源质量比对） |

> ✅ **入库+分级已集成到流水线中**，`run_phase4_enrichment.py` 会在 Phase 3.5 验证通过后自动执行入库（`import_github_candidates.py`）和分级（`batch_update_tiers.py`），无需手动操作。

#### 批次报告（Batch Report）

每次 Pipeline 运行完成后，会自动生成一份 JSON 格式的批次报告，记录每个阶段的关键数据指标。

**文件位置**：
- 新 Seed Pipeline: `batches/{batch_name}/batch_report.json`
- Phase 4 Pipeline: `batch_report_phase4_{timestamp}.json`

**报告字段**：

| 字段 | 说明 |
|:---|:---|
| `batch_id` | 批次标识 |
| `started_at` / `completed_at` | 运行时间窗口 |
| `source` | 数据来源（`new_seed_pipeline` / `phase4_social_expansion`） |
| `phases.phase1` | 种子采集人数 |
| `phases.phase2_v3` | 富化数据（邮箱、Python、Scholar、主页覆盖率） |
| `phases.phase3_v3` | AI 判定结果（通过率、排除人数） |
| `phases.phase3_5` | 深度爬取结果（主页成功数、LinkedIn 数） |
| `phases.tier` | 各 Tier 级别人数分布 |
| `db_snapshot` | 入库后数据库全局快照 |

> 📌 **用途**：未来可将这些报告导入 personal-ai-headhunter 系统，用于不同数据源（GitHub / 脉脉 / LinkedIn）的质量比对分析。

#### 状态隔离规则

> [!WARNING]
> `run_phase4_enrichment.py` 使用全局共享的 `pipeline_state.json` 记录富化进度。
> **每次新批次数据到来时，必须重置该文件**，否则旧批次的 "all done" 状态会导致新数据被跳过。

**自动防护机制**（已内置于 `run_phase4_full_pipeline.sh`）：
1. Phase 4 爬取完成后，自动备份并重置 `pipeline_state.json`
2. 同时清理旧的中间产出文件（`phase3_from_phase4.json` 等）
3. 旧状态和文件备份为 `*.bak_{timestamp}`，可追溯

**手动重置方法**（如需单独重跑 enrichment）：
```bash
rm github_mining/scripts/github_mining/pipeline_state.json
```

#### 批次数据入库 (batch_runs 表)

Pipeline 完成后自动将**本批次维度**的统计数据写入 `batch_runs` 表，用于不同数据源质量比对。

**自动入库（Pipeline 内置）**：
- `run_phase4_full_pipeline.sh`：完成后自动统计本批次入库人数的评级分布+可联系信息，写入 DB

**手动入库**：
```bash
cd personal-ai-headhunter

# 按来源生成快照
python3 import_batch_report.py --source github --batch-id "github_20260225"
python3 import_batch_report.py --source 脉脉 --batch-id "maimai_20260225"

# 导入 JSON 报告
python3 import_batch_report.py path/to/batch_report.json

# 查看所有批次
python3 import_batch_report.py --list
```

**记录字段**：评级分布(S/A+/A/B+/B/C/D)、可联系信息(Email/LinkedIn/GitHub/Phone/Website)、DB全局快照

#### 评级逻辑 (2026-02-25 更新)

| Tier | 条件 |
|------|------|
| S | AI领域 + Followers>5000/Stars>5000/H-index>30 |
| A+ | 3+顶会论文 |
| A | 顶尖Lab / **tier1 + 985 Top20** |
| B+ | tier1 + 985(全部) |
| B | tier1 or 985 / tier2 / Followers>500 |
| C | 默认 |

配置文件: `personal-ai-headhunter/data/company_tier_config.json`
评级 Skill: `.agent/skills/tier-evaluation/SKILL.md`

---

### 步骤 5/5: （可选）迭代扩展

如果 Phase 4 发掘了新的 S/A+/A 级人才，可以用他们作为新种子继续扩展：

```bash
# 重新导出种子（包含新发现的高质量人才）
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 -c "
from database import SessionLocal, Candidate
import json

session = SessionLocal()
seeds = session.query(Candidate).filter(
    Candidate.source == 'github',
    Candidate.talent_tier.in_(['S', 'A+', 'A']),
    Candidate.github.isnot(None)
).all()

seed_usernames = [s.github.strip('/').split('/')[-1] for s in seeds if s.github]

with open('../github_mining/phase4_seeds_v2.json', 'w') as f:
    json.dump(seed_usernames, f)

print(f'✅ 种子 v2: {len(seed_usernames)} 人（包含上一轮发现的新人才）')
session.close()
"

# 再次执行 Phase 4
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase4 \
  --seeds-file github_mining/phase4_seeds_v2.json \
  --min-cooccurrence 3
```

---

### 变体：从单个用户启动完整流程

如果你想从**任意用户**（如新的目标用户）开始完整挖掘：

```bash
# 1. Phase 1: 采集 Following
cd /Users/lillianliao/notion_rag
python3 github_mining/scripts/github_network_miner.py phase1 --target USERNAME

# 2. Phase 2 V3: 全量轻富化
python3 github_mining/scripts/github_network_miner.py phase2_v3

# 3. Phase 3 V3: 统一 AI 判定
python3 github_mining/scripts/github_network_miner.py phase3_v3

# 4. Phase 4.5: LLM 深度富化（NEW ⭐）

> **在导入数据库前对候选人进行智能信息提取**
>
> **目标**：从个人网站内容中提取结构化信息，提升候选人数据质量
>
> **核心优势**：在入库前完成数据富化，避免导入后的额外处理

---

## 📍 流程位置

```
Phase 4 (社交扩展)
    ↓
Phase 3 (Repos补强)
    ↓
Phase 3.5 (主页爬取)
    ↓
Phase 4.5 (LLM深度富化) ⭐ NEW!
    ├─ 工作履历提取
    ├─ 教育背景提取
    ├─ 技能列表提取
    └─ 谈话点生成
    ↓
入库 (数据库导入)
    ↓
分级 (Tier 标签)
```

---

## 🎯 Phase 4.5 功能

### 提取内容

| 字段 | 类型 | 说明 | 示例 |
|:---|:---|:---|:---|
| `extracted_work_history` | JSON | 工作履历（公司、职位、是否当前） | `[{"company": "Google", "role": "ML Engineer", "current": true}]` |
| `extracted_education` | JSON | 教育背景（学位、专业、学校） | `[{"degree": "PhD", "field": "CS", "university": "Stanford"}]` |
| `extracted_skills` | TEXT | 技能列表（逗号分隔） | `Python, Machine Learning, PyTorch, NLP` |
| `talking_points` | TEXT | 外联谈话点（换行分隔） | `看到你在Google做过ML工程师...` |
| `website_quality_score` | INTEGER | 质量分数（0-100） | `95` |

### 质量评分标准

- 有工作履历: +25分
- 有教育背景: +20分
- 每个技能: +2分
- 有项目: +15分
- 有论文: +20分

---

## 🚀 执行方法

### 选项1：集成到完整流程（推荐）

```bash
cd github_mining/scripts

# 运行完整流程（包含 Phase 4.5）
python3 run_phase4_enrichment.py
```

流程会自动执行：
1. Phase 3: Repos深度信息补强
2. Phase 3.5: 个人主页爬取
3. **Phase 4.5: LLM深度富化** ⭐
4. 入库
5. 分级

### 选项2：单独运行 Phase 4.5

```bash
cd github_mining/scripts

# 只运行 LLM 富化
python3 run_phase4_5_llm_enrichment.py
```

---

## 📊 性能指标

### 测试结果（20样本）

- ✅ 成功率: 100% (20/20)
- 📈 提升率: 80% (16/20)
- 📊 平均提升: +18.6 分

### 批量处理结果（2,476人）

| 指标 | 数值 | 比例 |
|:---|:---|:---|
| **成功处理** | 2,473 人 | 99.9% |
| **质量提升** | 2,360 人 | 95.3% ✨ |
| 质量下降 | 111 人 | 4.5% |
| **平均质量分** | 95.1 分 | - |
| 处理速度 | 4.5 人/分钟 | - |
| 总耗时 | 9小时3分钟 | - |

### 质量改善效果

- 从 **50-69分段** → **90-100分段**
- 技能数量: 4-6个 → 15-25个
- 工作履历: 经常缺失 → 完整结构化
- 教育背景: 经常缺失 → 完整结构化

---

## 🔧 技术实现

### 文件位置

- 主脚本: `github_mining/scripts/run_phase4_5_llm_enrichment.py`
- 流程集成: `github_mining/scripts/run_phase4_enrichment.py`

### API 依赖

- API 服务器: `http://localhost:8502`
- API 端点: `/api/generate-website-based-message`
- 认证: Bearer Token

### 数据流向

```
Phase 3.5 输出 (phase3_5_enriched.json)
    ↓
筛选有个人网站的候选人
    ↓
批量调用 LLM API
    ↓
提取 + 质量评分
    ↓
Phase 4.5 输出 (phase4_5_llm_enriched.json)
    ↓
用于数据库导入
```

---

## 💡 核心优势

### 对比：规则提取 vs LLM 提取

| 维度 | 规则提取 | LLM提取 |
|:---|:---|:---|
| 工作履历 | ❌ 经常缺失 | ✅ 完整结构化 |
| 教育背景 | ❌ 经常缺失 | ✅ 完整结构化 |
| 技能数量 | 4-6个 | 15-25个 |
| 准确度 | 关键词匹配 | 上下文理解 |
| 外联谈话点 | ❌ 无 | ✅ 个性化生成 |

### 流程优化

- ✅ 在导入数据库**前**完成数据富化
- ✅ 避免导入后额外处理的冗余步骤
- ✅ 数据在入库前就已经完整富化
- ✅ 支持断点续传和崩溃恢复

---

## 📝 使用示例

### 输入数据结构

```json
{
  "id": 12345,
  "name": "张三",
  "personal_website": "https://zhangsan.com",
  "homepage_text": "完整的网站HTML内容...",
  "other_fields": "..."
}
```

### 输出数据结构

```json
{
  "id": 12345,
  "name": "张三",
  "personal_website": "https://zhangsan.com",
  "homepage_text": "完整的网站HTML内容...",
  "extracted_work_history": "[{\"company\": \"Google\", \"role\": \"ML Engineer\", \"current\": true}]",
  "extracted_education": "[{\"degree\": \"PhD\", \"field\": \"CS\", \"university\": \"Stanford\"}]",
  "extracted_skills": "Python, Machine Learning, PyTorch, NLP",
  "talking_points": "看到你在Google做过ML工程师...",
  "website_quality_score": 95,
  "other_fields": "..."
}
```

---

# 5. Phase 5: 入库+分级（参考 Runbook 1 步骤 3-5）
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 import_github_candidates.py --file ../github_mining/scripts/github_mining/phase3_v3_ai_candidates.json
python3 batch_update_tiers.py

# 5. （可选）Phase 4: 用新发现的 S/A+/A 用户作为种子继续扩展
python3 github_mining/scripts/github_network_miner.py phase4 --seed-tier S,A+,A
```

这个变体适用于：
- 🆕 新增目标用户（如某技术大牛）
- 🔄 重新执行全流程（如算法更新后）
- 📊 批量处理多个种子用户

---

## Runbook 4.5: 网站内容价值提取 (Phase 6.5)

> 从个人网站提取结构化数据，生成增强候选人画像和个性化谈话点
>
> **目标**: 提取工作履历、技术技能、教育背景、项目经验，用于精准画像和个性化外联
>
> **前置条件**: ✅ 有 `website_content` 字段的候选人（8,434 人，41%）

### 核心价值

| 数据类型 | 提取成功率 | 业务价值 |
|:---|:---|:---|
| **技能关键词** | 55% | 精准技能匹配 |
| **工作履历** | 34% | 公司/职位验证 |
| **教育背景** | 待测 | 学历/院校验证 |
| **项目经验** | 待测 | 开源项目亮点 |
| **谈话点** | 1.1 个/人 | 个性化外联 |

### 执行阶段

#### **Option A: 快速验证** ✅ 已完成（3/01）

**目标**: 验证提取可行性

**执行**:
```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 scripts/analyze_website_content_value.py --sample-size 100
```

**结果**:
- ✅ 45/100 (45%) 网站有提取价值
- ✅ 技能提取成功率 55%
- ✅ 工作履历提取成功率 34%
- ✅ 平均谈话点 1.1 个/人
- ✅ 生成 4 种个性化外联模板示例

**报告**: `personal-ai-headhunter/docs/OPTION_A_VALIDATION_REPORT.md`

---

#### **Option B: MVP 实施** 🔄 进行中

**目标**: 批量处理 8,434 个候选人，生成增强画像

**时间**: 2-3 周

---

##### **Phase 1: 数据提取增强** ✅ 已完成（3/02）

**完成项**:
- ✅ 技能关键词库扩展（20 → 100+）
- ✅ 工作履历提取规则优化（支持中英文）
- ✅ 教育背景提取（中英文）
- ✅ 项目经验提取（GitHub 项目等）
- ✅ 中文内容支持

**脚本**: `personal-ai-headhunter/scripts/extract_website_data_enhanced.py`

**测试**:
```bash
python3 scripts/extract_website_data_enhanced.py
```

**输出示例**:
```json
{
  "has_value": true,
  "quality_score": 52,
  "extracted": {
    "work_history": [
      {"company": "ByteDance", "role": "ML Engineer", "current": true}
    ],
    "education": [
      {"degree": "PhD", "university": "Tsinghua University"}
    ],
    "skills": ["PyTorch", "TensorFlow", "JAX", "Python", "Deep Learning"],
    "projects": [
      {"name": "awesome-project", "platform": "GitHub"}
    ],
    "publications": []
  },
  "talking_points": [
    "Currently ML Engineer at ByteDance",
    "PhD from Tsinghua University",
    "Expertise in PyTorch, TensorFlow, JAX"
  ]
}
```

---

##### **Phase 2: 全量数据处理** ⏳ 预计 3-4 天

**目标**: 批量处理 8,434 个候选人

**待创建脚本**:
```bash
# 批量提取
python3 scripts/batch_extract_website_data.py \
    --limit 8434 \
    --output data/website_extracted_batch1.json

# 数据验证
python3 scripts/validate_extracted_data.py \
    --input data/website_extracted_batch1.json
```

**预期产出**:
- ~3,800 个增强候选人画像（45% × 8,434）
- ~4,600 个技能标签（55% × 8,434）
- ~9,200 个个性化谈话点（1.1 个/人 × 8,434）

---

##### **Phase 3: 系统集成** ⏳ 预计 2-3 天

**数据库 Schema 扩展**:
```sql
ALTER TABLE candidates ADD COLUMN website_extracted_data JSON;
ALTER TABLE candidates ADD COLUMN extracted_skills TEXT;
ALTER TABLE candidates ADD COLUMN extracted_work_history JSON;
ALTER TABLE candidates ADD COLUMN extracted_education JSON;
ALTER TABLE candidates ADD COLUMN talking_points TEXT;
ALTER TABLE candidates ADD COLUMN website_quality_score INTEGER;
```

**导入脚本**:
```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 scripts/import_website_extracted_data.py \
    --input data/website_extracted_batch1.json
```

**前端更新**:
- 候选人详情页面展示增强信息
- 技能搜索/筛选功能
- 谈话点预览

---

##### **Phase 4: 外联优化** ⏳ 预计 1-2 天

**个性化消息生成**:
```bash
# 基于提取数据生成个性化消息
python3 scripts/generate_personalized_outreach.py \
    --tier "S,A+,A" \
    --use-website-data
```

**消息模板扩展**:
- 学术型人才（引用教育背景、论文）
- 工程型人才（引用技术栈、项目）
- 研究员（引用研究方向、学术成就）
- 复合型人才（综合引用）

**A/B 测试框架**:
```bash
python3 scripts/outreach_ab_test.py \
    --template website-based \
    --control-template generic \
    --sample-size 100
```

---

### 预期成果

| 指标 | 当前 | 目标 | 提升 |
|:---|:---|:---|:---|
| **增强候选人画像** | 0 | ~3,800 | +100% |
| **技能标签覆盖率** | - | 55% | 新增 |
| **个性化谈话点** | 0 | ~9,200 | +100% |
| **外联成功率** | 基线 | - | +30-50% |

---

### 相关文档

- **Option A 验证报告**: [docs/OPTION_A_VALIDATION_REPORT.md](file:///Users/lillianliao/notion_rag/personal-ai-headhunter/docs/OPTION_A_VALIDATION_REPORT.md)
- **网站有效性研究**: [docs/WEBSITE_VALIDITY_RESEARCH.md](file:///Users/lillianliao/notion_rag/personal-ai-headhunter/docs/WEBSITE_VALIDITY_RESEARCH.md)
- **执行细节参考**: [github-mining-reference.md §13](file:///Users/lillianliao/notion_rag/.agent/workflows/github-mining-reference.md#13-网站内容提取细节)

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

## Runbook 5: 邮件/社交触达 (Phase 7 - V4 LinkedIn优先策略)

> 个性化触达建立联系，核心目标：加微信/同频技术交流
>
> **核心原则**：LinkedIn 优先于邮件 - 有LinkedIn的候选人，先从LinkedIn添加，2周无回复再考虑邮件

---

## 一、数据资产盘点 (4,127人)

### 整体数据分布

| 维度 | 人数 | 占比 | 核心价值 |
|:---|:---|:---|:---|
| **总人才池** | 4,127 | 100% | - |
| **待触达 (new)** | 4,083 | 99% | 核心触达池 |
| **已触达** | 44 | 1% | 需跟进 |
| **有邮箱** | 2,566 | 62% | 主触达渠道 |
| **有 LinkedIn** | 269 | 6.5% | **优先触达渠道** |
| **有 Scholar** | 213 | 5.2% | 学者群体 |
| **高质量 (Score≥20)** | 3,122 | 76% | 核心目标 |
| **S/A+/A级** | 273 | 6.6% | 顶级人才 |

### 核心挑战与机遇

| 挑战 | 数据 | 应对策略 |
|:---|:---|:---|
| LinkedIn 覆盖率低 | 6.5% (269人) | **LinkedIn 优先，精准触达** |
| 待触达池巨大 | 4,083人 | 分批触达，3周完成首轮 |
| 邮箱覆盖率中等 | 62% | 无LinkedIn者走邮件 |
| 质量分布两极 | S级37人 vs B级2238人 | 分级差异化策略 |

---

## 二、触达优先级矩阵

### 🔴 P0 - 顶级人才 (273人，S/A+/A级)

**特征**：行业领袖、技术权威、稀缺人才

| Tier | 总数 | 有LinkedIn | 有邮箱 | 有Scholar | 触达策略 |
|:---|:---|:---|:---|:---|:---|
| **S** | 37 | 4 (11%) | 24 (65%) | 4 (11%) | **LinkedIn优先** → 手工定制 |
| **A+** | 5 | 2 (40%) | 4 (80%) | 3 (60%) | **LinkedIn优先** → 学术套瓷 |
| **A** | 231 | 35 (15%) | 140 (61%) | 62 (27%) | **LinkedIn优先** → 深度定制 |

**核心规则**：
- ✅ 有LinkedIn者：**第1天LinkedIn Connect**，不接受再发邮件
- ✅ 无LinkedIn者：直接发送深度定制邮件/学术套瓷邮件

---

### 🟠 P1 - 高质量工程师 (2,352人，B+/B级)

**特征**：技术扎实、活跃、可触达

| Tier | 总数 | 有LinkedIn | 有邮箱 | 有Scholar | 触达策略 |
|:---|:---|:---|:---|:---|:---|
| **B+** | 114 | 32 (28%) | 75 (66%) | 24 (21%) | **LinkedIn优先** → 硬核切磋 |
| **B** | 2,238 | 144 (6%) | 1,491 (67%) | 74 (3%) | **LinkedIn优先** → 批量定制 |

**核心规则**：
- ✅ 有LinkedIn者：**第1天LinkedIn Connect**，2周无回复发邮件
- ✅ 无LinkedIn者：分批轮换邮件

---

### 🟡 P2 - 潜力候选人 (1,416人，C级)

**特征**：有AI信号但证据不足，需验证

| Tier | 总数 | 有LinkedIn | 有邮箱 | 触达策略 |
|:---|:---|:---|:---|:---|
| **C** | 1,416 | 51 (4%) | 776 (55%) | **LinkedIn优先** → 低成本试触 |

**核心规则**：
- ✅ 有LinkedIn者：轻度LinkedIn互动，暂不推岗
- ✅ 无LinkedIn者：基础调研邮件，分批低频

---

### ⚫ P3 - 排除 (86人，D级)

**特征**：非AI人才，暂不触达

**行动**：
- 打标签 `D-tier-exclude`
- 定期复查 (季度)

---

## 三、触达渠道优先级 (LinkedIn优先版)

### 渠道执行顺序

```
LinkedIn (优先) → 邮件 (2周后备用) → GitHub 社交 (辅助)
```

### 渠道分层逻辑

| 优先级 | 触达方式 | 核心触达群 | 路由条件 | 执行时机 |
|:---|:---|:---|:---|:---|
| **P0** | **LinkedIn 推岗** | S/A+/A级有LinkedIn | `linkedin_url` 存在 && Tier ∈ (S, A+, A, B+) | **第1天立即执行** |
| **P1** | **LinkedIn 交友** | B+/B/C/D级有LinkedIn | `linkedin_url` 存在 && Tier ∈ (B, C, D) | **第1天立即执行** |
| P2 | 学术套瓷邮件 | 顶刊/高校学者 | `personal_website` 包含 `scholar.google` / `.edu` | LinkedIn 2周无回复 |
| P3 | 硬核切磋邮件 | 开源大佬 | `structured_tags.github_score` ≥ 50 | 无LinkedIn，直接邮件 |
| P4 | 深度定制邮件 | 有个人主页者 | 有 `personal_website` 但无 Scholar | 无LinkedIn，直接邮件 |
| P5 | 基础调研邮件 | 纯 GitHub+Gmail | 啥都没有 | 无LinkedIn，直接邮件 |
| P6 | GitHub 社交 | 无任何联系方式 | 仅 GitHub | Follow + Star，等待反向 |

---

## 四、全量触达执行路线图 (4,127人)

### 📅 第1周：LinkedIn 优先触达期 (269人)

**目标**：对所有有LinkedIn的候选人完成首次触达

| 批次 | 人群 | 人数 | 触达方式 | 消息类型 |
|:---|:---|:---|:---|:---|
| 1.1 | S/A+/A级有LinkedIn | 41 | LinkedIn Connect | 推岗消息 (模板1) |
| 1.2 | B+/B级有LinkedIn | 176 | LinkedIn Connect | 交友消息 (模板2) |
| 1.3 | C/D级有LinkedIn | 52 | LinkedIn Connect | 轻度互动 (模板3) |

**执行节奏**：
- 每天不超过 50 个 LinkedIn 请求
- 上午 10:00-11:00 发送
- 记录所有发送状态，2周后复盘

---

### 📅 第2-3周：规模化并行触达期 (3,858人)

**目标**：LinkedIn无回复 + 无LinkedIn候选人，同时触达

**每周计划** (每周约1,286人)：

| 人群 | 人数 | LinkedIn策略 | 邮件策略 | GitHub策略 |
|:---|:---|:---|:---|:---|
| S/A+/A级 (无LinkedIn) | 232 | - | 深度定制+学术套瓷 | Follow+Star |
| B+/B级 (无LinkedIn) | 2,176 | - | 硬核切磋+深度定制 | Follow+Star |
| C级 (无LinkedIn) | 1,364 | - | 基础调研邮件 | Follow |
| D级 | 86 | - | 暂不触达 | - |

**执行节奏**：
- **LinkedIn跟进**：每天检查新接受，立即回复
- **邮件发送**：每天100封，分3个时段 (10点/14点/17点)
- **GitHub社交**：每天Follow 100人，Star 20个项目

---

### 📅 第4周及以后：持续跟进期

**LinkedIn 策略**：
- 每2周对未接受的候选人重试1次
- 对已接受的候选人，每周互动1次 (点赞/评论)

**邮件策略**：
- LinkedIn 2周无回复 → 发送第一封邮件
- 邮件发送3天无回复 → 发送 Follow-up
- 每月发送1次 Newsletter 给未回复的候选人

**GitHub策略**：
- 持续 Follow 活跃候选人
- 对高质量项目 Star + Watch
- 偶尔提交小 PR 建立联系

---

## 五、LinkedIn 消息模板体系 (新增)

### 模板1：推岗消息 (S/A+/A级，41人)

```
Hi {姓名},

看到你在{公司}做{职位}，对你在{技术领域}的工作印象深刻。

我也是AI领域的从业者，目前在关注{相关方向}的机会。如果你或你认识的朋友在看新机会，很期待能和你聊聊。

我在LinkedIn上也会分享一些行业动态，期待能保持联系！

{你的名字}
```

### 模板2：交友消息 (B+/B级，176人)

```
Hi {姓名},

看到你的GitHub项目{项目名}，用{技术栈}解决{问题}很有意思！

我也是做{相关技术}的，想认识一下同行。如果你对技术交流感兴趣，欢迎通过我的请求。

Best,
{你的名字}
```

### 模板3：轻度互动 (C/D级，52人)

```
Hi {姓名},

看到你关注AI领域，想加个LinkedIn保持联系。我也会分享一些技术资讯和机会。

{你的名字}
```

---

## 六、邮件模板体系 (针对无LinkedIn或LinkedIn 2周无回复的候选人)

### 模板1：学术套瓷邮件 (213位Scholar)

**适用人群**：有 Google Scholar 的顶刊/高校学者

**触发条件**：LinkedIn 2周无回复 OR 无LinkedIn + 有Scholar

```
Subject: [学术交流] 关于你在{研究方向}的研究

{姓名}老师/博士好，

我是{你的名字}，一直关注你在{研究方向}领域的工作，特别是你关于{具体论文/项目}的研究给我留下了深刻印象。

我目前在运营一个AI研究社区，主要聚焦于：
- {相关方向1}，定期组织论文讨论会
- {相关方向2}，已有{X}位来自{顶尖院校}的成员

我们社区正在讨论{近期热点话题}，如果你有兴趣，我很期待能邀请你参与。

另外，如果你或你的团队在找工作，我这边也有一些{公司类型/实验室}的优质线索可以分享。

祝研究顺利！

{你的名字}
{个人网站/GitHub}
```

---

### 模板2：深度定制邮件 (880人有个人网站)

**适用人群**：有个人网站/博客的工程师

**触发条件**：LinkedIn 2周无回复 OR 无LinkedIn + 有网站

```
Subject: 看了你的{个人网站/博客/项目} - 关于{具体技术}

{候选人姓名}你好，

刚刚浏览了你的个人网站，看到了你在{具体项目}上的工作，非常认同你关于{技术观点/理念}的思考。

我注意到你：
- {亮点1：从网站提取的具体成就/项目}
- {亮点2：技术栈/开源贡献}
- {亮点3：职业经历/研究方向}

我是{简短背景介绍}，最近在{你的领域}活跃。目前在构建一个AI人才社区，已经有{X}位从业者，主要来自{公司/院校背景}。

我们近期在讨论：
- {话题1：如LLM推理优化}
- {话题2：如多模态学习进展}

如果你对技术交流或职业机会感兴趣，欢迎回复这封邮件。即使暂时没有需求，我也很期待能认识一位志同道合的工程师。

Best,
{你的名字}
{GitHub}: {你的GitHub链接}
```

---

### 模板3：硬核切磋邮件 (B级工程师，有活跃项目)

**适用人群**：github_score ≥ 50，有活跃项目的工程师

**触发条件**：LinkedIn 2周无回复 OR 无LinkedIn + 高Score

```
Subject: GitHub上看到你的{项目} - 技术交流

{候选人姓名}你好，

在 GitHub 上发现了你的{项目名称}项目，看到你使用{技术栈}来解决{问题}，印象深刻！

我注意到你：
- GitHub有{star数}关注，最近活跃在{领域}
- 主要技术栈：{语言/框架}
- 最近在维护：{1-2个活跃项目}

我是{简短介绍}，最近也在探索{相关技术}。正在组建一个小范围的AI工程交流群（目前约{群规模}人），成员主要是{成员背景}。

我们在讨论：
- {技术话题1}
- {技术话题2}

如果你对技术交流感兴趣，欢迎回复。纯技术向，非推销。

另外，如果你在看新机会，我这边也有一些{公司类型/阶段/方向}的线索可以分享。

祝好，
{你的名字}
```

---

### 模板4：基础调研邮件 (C级，AI信号较弱)

**适用人群**：仅GitHub+邮箱，AI信号不强的候选人

**触发条件**：LinkedIn 2周无回复 OR 无LinkedIn + 仅邮箱

```
Subject: AI领域技术交流 - 来自{GitHub/公司}

Hi {候选人姓名},

我是{你的名字}，通过 GitHub 找到了你。看到你关注{AI领域}方向，想简单打个招呼。

我目前在运营一个AI人才社区，主要成员来自{公司/院校}。我们日常会：
- 分享最新的 AI 论文和技术进展
- 组织线上技术交流
- 偶尔内推一些优质职位（近期有{公司类型}的机会）

如果你对技术交流或职业发展感兴趣，欢迎回复。即使暂时没有需求，也很期待能认识你。

如果你有LinkedIn，也欢迎加一下：{你的LinkedIn链接}

Best,
{你的名字}
```

---

## 七、触达执行命令

```bash
# ===== LinkedIn 优先触达 =====

# 1. 生成 LinkedIn 消息草稿 (全部有LinkedIn的候选人)
python3 personal-ai-headhunter/batch_linkedin_outreach.py --priority linkedin-first --tier "S,A+,A,B+,B,C,D"

# 2. 按 Tier 分批生成 LinkedIn 消息
python3 personal-ai-headhunter/batch_linkedin_outreach.py --tier "S,A+,A" --template job-offer
python3 personal-ai-headhunter/batch_linkedin_outreach.py --tier "B+,B" --template networking
python3 personal-ai-headhunter/batch_linkedin_outreach.py --tier "C,D" --template light

# 3. 查看有LinkedIn的候选人分布
python3 -c "
from database import SessionLocal, Candidate
session = SessionLocal()
gh = session.query(Candidate).filter(Candidate.source.ilike('%github%'), Candidate.linkedin_url != None).all()
from collections import Counter
tiers = Counter(c.talent_tier for c in gh)
for t, c in tiers.items(): print(f'{t}: {c}人')
"

# ===== 邮件触达 (无LinkedIn 或 LinkedIn 2周无回复) =====

# 4. 生成邮件草稿 (仅无LinkedIn候选人)
python3 personal-ai-headhunter/batch_email_outreach.py --filter-no-linkedin

# 5. 生成学术套瓷邮件 (有Scholar的候选人)
python3 personal-ai-headhunter/batch_email_outreach.py --filter-scholar --template academic

# 6. 生成深度定制邮件 (有个人网站的候选人)
python3 personal-ai-headhunter/batch_email_outreach.py --filter-website --template deep-dive

# ===== GitHub 社交辅助 =====

# 7. GitHub 批量 Follow (全员)
python3 personal-ai-headhunter/batch_github_follow.py --limit 100 --tier "S,A+,A,B+,B,C"

# 8. GitHub 批量 Star (高质量项目)
python3 personal-ai-headhunter/batch_github_star.py --limit 20 --min-score 30
```

---

## 八、发送策略与节奏控制

### 发送策略更新

**LinkedIn**：
- 每天不超过 50 个请求
- 上午 10:00-11:00 发送
- 2周无回应删除，1个月后可重试

**邮件**：
- 仅对 LinkedIn 无回复 或 无LinkedIn 的候选人发送
- LinkedIn 接受2周后仍无深度沟通 → 发邮件
- 工作日上午 10:00-11:00 发送
- 间隔 30-60 秒/封

**GitHub**：
- 全员 Follow (无论是否有其他联系方式)
- 每天Follow 100人
- Star 高质量项目

---

## Runbook 6: 长期运营 (Phase 8-9)

> 持续跟进和关系维护

**多渠道触达节奏 (LinkedIn优先版)**:

| 天数 | 动作 | 渠道 | 条件 |
|:---|:---|:---|:---|
| **Day 0** | **LinkedIn Connect** | **LinkedIn** | **有LinkedIn，立即执行** |
| Day 0 | GitHub Follow + Star 热门项目 | GitHub | 全员执行 |
| Day 1 | LinkedIn 消息跟进 (如接受) | LinkedIn | 对方接受后 |
| Day 14 | LinkedIn 未接受 → 第一封邮件 | Email | LinkedIn 2周无回复 |
| Day 17 | Follow-up 邮件（换角度） | Email | 邮件3天无回复 |
| Day 30 | 删除 LinkedIn 请求 | LinkedIn | 仍无回应 |
| 每月 | 行业资讯推送 | Email/微信 | 已建立联系 |

**有 LinkedIn vs 无 LinkedIn 候选人的触达路径**：

```
【有LinkedIn候选人】 (269人)
  ├─ Day 0: LinkedIn Connect
  ├─ Day 1: 对方接受 → 深度对话 → 邀请加微信
  ├─ Day 14: 未接受 → 发送邮件
  ├─ Day 17: 邮件无回复 → Follow-up
  └─ Day 30: 删除请求，标记为"冷接触"

【无LinkedIn候选人】 (3,858人)
  ├─ Day 0: GitHub Follow + Star
  ├─ Day 0-1: 发送第一封邮件 (分批)
  ├─ Day 3-4: 邮件无回复 → Follow-up
  ├─ Day 7: 尝试通过姓名搜索LinkedIn
  ├─ Day 14: 第二次Follow-up (换角度)
  └─ 每月: GitHub社交 (持续)
```

**候选人生命周期 (LinkedIn优先版)**:
```
未触达
  ↓
[有LinkedIn?]
  ├─ Yes → LinkedIn已发送
  │         ↓
  │       [接受?]
  │         ├─ Yes → LinkedIn已接受 → 深度对话 → 已加微信 → 有岗位匹配 → 推荐中 → 成交
  │         └─ No → 等待14天
  │                   ↓
  │                 发送邮件 → [回复?]
  │                            ├─ Yes → 已回复 → 已加微信 → ...
  │                            └─ No → 标记"冷接触" → 归入观察池
  │
  └─ No → GitHub已Follow → 发送邮件 → [回复?]
                                ├─ Yes → 已回复 → ...
                                └─ No → 标记"低活跃" → 定期GitHub社交
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
3. **中间保存**: 脚本每 50 人自动保存，中断可恢复
4. **无人值守**: `auto_restart_wrapper.py` + `run_phase4_enrichment.py` 实现崩溃自动重启 + 断点续传 + 自动验证
5. **Follow 策略**: 只 Follow 评分 Top 30% 的 AI 人才，需 Classic Token
6. **数据安全**: 所有数据仅用于合法招聘目的
