# 学术流水线执行清单 (跨会话持久化)

> 📅 最后更新: 2026-03-24 08:13
> 📂 批次目录: `data/academic/runs/conference_full_20260311_131547/`
> 🎯 最终目标: 为每位候选人建立完整猎头档案 (工作/教育/技能/联系方式/谈话点)

---

## ⚠️ 重要教训与规则

### 跨源隔离规则 (2026-03-14 确立)

> **不同渠道的数据绝不互相更新！Academic、GitHub、脉脉各自独立。**

- ❌ 禁止: academic 数据更新 github/脉脉 记录
- ❌ 禁止: 仅凭名字判断是否同一人
- ✅ 允许: 同源 academic→academic 更新 (用 s2_id 匹配)
- ✅ 允许: 跨源匹配到时 → INSERT 新记录 + 输出重复清单

### DB 路径陷阱

> `academic_import.py` 必须指定 `DB_PATH` 环境变量！

```bash
# ✅ 正确
DB_PATH=/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db \
  python3 scripts/academic_import.py --update

# ❌ 错误 — 会写到 github_mining/data/ 下的影子 DB
python3 scripts/academic_import.py --update
```

### 同源匹配改进 ✅ (2026-03-14 已完成)

已改为 **s2_id** 匹配，不再仅靠 name。

### TODO: 综合评级 (h-index + 职位/公司)

> 当前评级**纯粹基于 h-index**，但 LLM 富化已提取到 title/company。
> 业界转型者 (如前蚂蚁副总裁戚远 h=10) 会被严重低估。

建议规则：
1. h-index 基础分级（保持不变）
2. 如果 LLM 提取到高管职位 (VP/CTO/Chief/Director/Head of AI 等) → 至少 A+ 级
3. 如果在顶级 AI 公司 (OpenAI/Google DeepMind/Meta FAIR 等) → 至少 A 级
4. 取 h-index 分级和职位分级中的**较高者**

### TODO: 同名碰撞三层解决方案 (优先级 P1)

> 中文名英文拼写重复率极高 ("Wei Zhang", "Jun Chen" 等可能对应几十人)。
> 当前缓存用 `name` 做 key，同名人的数据互相覆盖。
> 案例: "Yuan Qi" (s2_id=2026836818, 实为 Yuanyuan Qi) → Serper 搜到齐逸岩 → 数据张冠李戴

**第 1 层: 缓存 key 改为 s2_id (防覆盖)** — ⭐⭐⭐ 最先做
```python
# ❌ 当前: 10 个 "Jun Chen" 互相覆盖
cache["Jun Chen"] = {...}
# ✅ 改进
cache["Jun Chen::2026836818"] = {...}
```

**第 2 层: Serper 搜索加机构消歧** — ⭐⭐ 改 1 行
```python
# ❌ 当前
query = "Yuan Qi homepage"
# ✅ 改进: 加入机构
query = "Yuan Qi MIT homepage"
```

**第 3 层: LLM 后置验证 (兜底)** — ⭐⭐
- LLM 提取的姓名 vs 论文作者姓名 → 不一致标记 `confidence=low`
- 邮箱域名 vs S2 机构域名 → 不匹配则排除
- 不入库或留待人工审核

---

## 当前 DB 状态 (19:18 快照)

| 渠道 | 记录数 |
|------|:---:|
| 全库 | **51,300** |
| GitHub | 25,468 |
| Academic | **12,643** (原 4,397 + 新 8,246) |
| 其他 | 13,189 |

### 跨源重复

- `data/academic/duplicate_report.csv` — 2,409 条
- 高置信度 (email/github/linkedin/website): **944 人**
- 仅名字: 1,465 人
- **决定: 暂不合并** — 等全部富化完成后一次性处理

---

## 🚨 Task 19: 补齐 CV/NLP 历史领域欠债 (最高优先级)

> 📅 2026-03-25 分析发现：2019-2025 所有挖掘批次均**严重缺失** NLP（完全未跑）和一半的 CV（完全漏掉 ICCV/ECCV）。大模型时代的 Vision 和 NLP 专家供给被严重切断。

### 优先级 P0 (已完成)
- [x] **2019-2022 批次大盘收尾**: 已在此前完成自动纠正，执行 `academic_import.py --update` 将 3,305 人的 LLM 深度提取数据安全注入主库。

### 优先级 P1 (已完成)
- [x] **跑通 2019-2022 的 Batch B (CV) 和 Batch C (NLP)**
  - **Batch B**: CVPR, ICCV, ECCV (2019-2022)
  - **Batch C**: ACL, EMNLP, NAACL (2019-2022)
  - *战报*：端到端（S2+Serper+LLM+入库）全自动拉通，成功新增 1,096 名野生大牛，补充完善了 1,276 人的详细履历。

### 优先级 P2 (算力空闲时补充预备役)
- [ ] **补齐 2024-2025 梯队缺漏的 CV & NLP 顶会**
  - **补充目标**: ICCV, ECCV, ACL, EMNLP, NAACL (2024 & 2025)
  - *依据*：充实 0-2 年的高潜力天才少年/应届生池子，为后续 Sourcing 和 Nurture 提供充足的冷启动种子池。

---

## Task 1-6: 基础设施 — ✅ 全部完成

(详见 BATCH_HISTORY.md)

---

## Task 7: 2024 S2 — ✅ 完成

- ✅ 17,923/17,923 (2026-03-14 17:40 完成)
- 产出: `all_conf_2024_20260314_174059_full.json` (13.9MB, 17,923 人)
- Tier: S=768, A+=773, A=2,317, B=3,418, C=10,647 → B+=7,276

---

## Task 8: Serper 搜索 — ✅ 完成

| 任务 | 状态 |
|------|:---:|
| 2025 B+ | ✅ |
| 2025 C | ✅ |
| 2024 B+ | ✅ |
| 2024 C | ✅ (03-15 07:17) |

---

## Task 9: Deep + LLM + 入库 (2025) — ✅ 完成

- ✅ Deep 04:56 完成 (6h, 9,442 条缓存)
- ✅ LLM 07:05 完成 (5,769 条)
- ✅ 入库 07:05 完成
- ⚠️ `quality_check` 有 `NameError: step_name` 小 bug，不影响数据

---

## Task 10: Deep + LLM + 入库 (2024) — ✅ 完成

> 📅 2026-03-16 06:30 完成重新入库
> Bug 修复: `academic_import.py` 之前默认用 2025 full.json，现在 `--input` 为必填参数

### 最终入库结果:
- 处理: **17,923** 人
- 新增: **11,833** | 补充: 143 | 跳过: 5,947
- 验证: 2024-only 抽样 20/20 ✅, 覆盖率 98.7%
- ⚠️ **联系方式覆盖率低** — B+ 可触达率仅 21%，见 Task 17

---

## Task 11: 2023 Pipeline — ✅ 完成

> 📅 2026-03-16 07:05 C-tier Chain 全部完成

### 数据准备:
- ✅ 手动合并 3 个 full.json → `all_conf_2023_20260315_merged_full.json` (8,458 人, 去重后)
- ✅ 补全 tier 字段 (S=455, A+=402, A=1,158, B=1,566, C=4,877)

### 执行结果:
- ✅ B+ Serper + Deep + LLM + 入库 (03-15 23:00 完成, 111 min)
- ✅ C-tier Serper (03-16 07:04, Key #1 即完成) + Chain Deep+LLM+入库 (07:05)
- 处理: **8,458** 人 | B+ 新增: 3,384 | C 新增: 484
- ⚠️ **联系方式覆盖率低** — B+ 可触达率仅 4%，见 Task 17

### 监控:
```bash
ps aux | grep 60894 | grep -v grep
tail -10 data/academic/runs/pipeline_2023_20260315_070407/logs/serper_c_rerun.log
tail -5 data/academic/runs/pipeline_2023_20260315_070407/logs/serper_c_chain.log
```

## Task 17: 修复 import 联系方式丢失 + 重新入库 — 🔄 进行中

> 📅 2026-03-16 08:16 开始
> 📊 详细分析: `docs/academic_data_analysis_20260316.md`

### 问题诊断 (2026-03-16 发现)

2024 B+ 可触达率 21%, 2023 B+ 仅 4%, 远低于 2025 的 65%。

| # | 根因 | 影响 |
|---|------|------|
| 1 | **Serper 缓存 key 格式不一致** — 2024 用 `Name::` 格式，import 只认 `serper::` | 2024 的 35,846 条 Serper 数据(含 3,231 邮箱)未入库 |
| 2 | **2024 无独立 Deep 缓存** — 共用 2025 的 `_deep_cache.json` | 2024-only 9,862 人完全未被 Deep 处理 |
| 3 | **2023 C-tier Chain 太快** — Deep+LLM 全是缓存命中(0 min) | C-tier 4,877 人几乎无联系方式 |

### 修复计划 (可并行执行)

**Step 1: 修复 merge_data()** ✅ 完成
- [x] `academic_import.py` merge_data() 兼容 `Name::` key 格式

**Step 2: 重新入库 2024 + 2023** ✅ 完成 (08:21)
- [x] 2024: 1,936 更新 + 841 新增 (可触达 912→919)
- [x] 2023: 390 更新 + 481 新增 (可触达 44→53)

**Step 3: Deep 富化** ✅ 完成 (10:32)
- [x] Both ran — 缓存命中率高 (2024: 4,388/5,004, 2023: 类似)
- [x] re-import 已执行

**Step 4: conferences 合并修复** ✅ 完成 (10:32)
- [x] fix: `--update` 时合并 `structured_tags.conferences`
- [x] 直接 DB 修复: **14,927 条** conferences 标签合并
- [x] 修正后: 2024 B+ 可触达 42%, 2023 B+ 43% (之前报告 21%/5% 是统计口径问题)

### 监控: 健康检查 (PID 47868, 每 30 分钟 Telegram)

---

## Task 18: Serper 命中率提升 — 🔄 进行中

> 📅 2026-03-16 13:01 开始
> 📊 详细分析: `docs/academic_data_analysis_20260316.md`

### 问题
同 tier 同 h-index 的学者，2024-only Serper homepage 命中率 (27%) 远低于 2025 (63%)。
- 搜索词一致 (`"{Name} researcher homepage"`), affiliation 仅 2% 覆盖
- 根因: (1) 2024-only 人群在线 presence 低 (~20pp); (2) 搜索词缺 affiliation 消歧

### 执行计划

**Step 1: S2 API 补全 affiliation** [~30 min]
- [ ] 对 2024-only B+ 级 (4,391 人) 通过 S2 API 补全 affiliation
- [ ] 对 2023-only B+ 级 (1,129 人) 同样补全

**Step 2: 重跑 Serper (仅空条目)** [消耗 Serper credits]
- [ ] 清除无结果的 serper 缓存条目，用补全的 affiliation 重搜
- [ ] 只对 B+ 级、原来搜索无结果的人重搜

**Step 3: 重新入库**
- [ ] import --update

---

## Task 12: 同名碰撞清理 — 📋 待处理

- 校验报告: `data/academic/name_collision_report.csv` (290 条)
- S/A+ 级 34 条需人工核验 (~5 分钟)
- 对确认错配的记录，清除错误的联系方式

---

## Task 13: 综合评级 — 📋 待开发

- 当前: 纯 h-index 评级
- 目标: h-index + LLM 提取的 title/company 综合评级
- 规则: VP/CTO/Chief → 至少 A+; 顶级 AI 公司 → 至少 A
- 详见 TASK.md 上方 TODO 章节

---

## Task 14: 同名碰撞三层修复 — 📋 待开发

1. 缓存 key 改为 `name::s2_id` (防覆盖)
2. Serper 搜索 query 加入 affiliation (消歧)
3. LLM 后置验证 (兜底)
- 详见 TASK.md 上方 TODO 章节

---

## Task 15: 缓存字段统一 — 📋 待开发

- Serper cache: `homepage`, `emails`
- Deep cache: `homepage_text`, `all_emails`
- 统一为标准字段名，详见 `docs/CONVENTIONS.md`

---

## Task 16: s2_id 匹配改进 — ✅ 已完成 (2026-03-14)

---

## Task 12: 2025 C 级富化 — 📋 等 Serper 完成

**前置条件**: Task 8 (2025 Serper C) 完成

1. [ ] Deep 爬取 (homepage_text)
2. [ ] LLM 富化
3. [ ] import --update (同源, 用 s2_id)

---

## Task 13: 2024 全流程 — 📋 等 Serper 完成

**前置条件**: Task 8 (2024 Serper) 完成

1. [ ] PDF 邮箱提取
2. [ ] Deep 爬取
3. [ ] LLM 富化
4. [ ] import (insert only)

---

## Task 14: 2023 全流程 — 📋 等 2024 完成后启动

**前置条件**: Task 13 (2024) 完成

1. [ ] Phase A 论文采集 (同样 5 个会议: ICLR, ACL, NeurIPS, ICML, CVPR 2023)
2. [ ] Phase C S2 富化
3. [ ] Phase D Serper
4. [ ] Phase E-F PDF + Deep 爬取 + LLM 富化
5. [ ] import (insert only, 跨源隔离)

---

## Task 15: 跨源重复合并 — 📋 最后执行

**前置条件**: 所有年份 (2025/2024/2023) 富化完成

1. [ ] 制作合并工具 (按 email/github/linkedin/website 自动匹配)
2. [ ] 合并方案: 补充 structured_tags (h_index, conferences) 到已有记录
3. [ ] 仅名字匹配的不自动合并
4. [ ] 合并后删除 academic 重复记录

---

## Serper API Keys (共 10 个, ~25,000 credits)

| # | Key | 分配 |
|---|-----|------|
| 1 | `633165fa15b2f68d512ccee4a7c5128eea03da68` | 2025 C 级 🔄 |
| 2 | `8cf7569e266a49026e8bc401e40286b5019bdc27` | 2024 B+ 🔄 |
| 3 | `291e00a3bda2a2266a54f28a0e4fbc30b422fff9` | 接力备用 |
| 4 | `07710687e4a725a1d5334e1fd0c85dec1dc7e73d` | 2024 C 级 🔄 |
| 5 | `71f44084beb2971b691ceba38f5935b5190971d9` | 接力备用 |
| 6 | `47f22063c60923cafbf7b634e42fdb9ae339130c` | 接力备用 |
| 7 | `ac3140b8332761219fd8d1788ad0535ecd7d34f6` | 接力备用 |
| 8 | `e915d3a6aaca5c7892b77235bae616525d99892f` | 接力备用 |
| 9 | `73b4e0a39126533a602c3bdae2e2b4e7e8415871` | 接力备用 |
| 10 | `dc03c4fc92e7f788c667fce356f0b457e36ed6c9` | 接力备用 |

> Key 用完后接力: `SERPER_API_KEY=<key> python3 scripts/academic_contact_enricher.py ...`（缓存自动跳过已完成）

---

## 🔔 Telegram 通知规范 (单行实战秘籍)

> 在执行长时间运行的任务（特别是跨越数小时的 API 抓取或 LLM 富化）时，必须挂载后台监听器，任务结束后自动推送到关联的 Telegram 账号。底层模块已配置好 Token，无需重新造轮子。

**底层引擎直接调用 (Python 核心):**
```python
import sys
sys.path.insert(0, '/Users/lillianliao/notion_rag/personal-ai-headhunter')
from telegram_notifier import notify
notify('🎉 任务已完成！')
```

**终端实战用法 (结合 PID 等待 — 推荐复制使用):**
假设你在后台刚跑了一个长任务，得到了它的 PID（例如 `10280`）。直接在终端执行以下挂载脚本，它会静默监控该进程直到消失，再发 Telegram 提醒你：

```bash
nohup bash -c '
TARGET_PID=10280
while kill -0 $TARGET_PID 2>/dev/null; do sleep 60; done
python3 -c "import sys; sys.path.insert(0, \"/Users/lillianliao/notion_rag/personal-ai-headhunter\"); from telegram_notifier import notify; notify(f\"🎉 报告老板，长期任务(PID {TARGET_PID}) 已顺利执行完毕！\")"
' >/dev/null 2>&1 &
```

---

## 监控命令

```bash
# 所有进程
ps aux | grep -E 'academic|run_all' | grep -v grep

# 2025 Serper C 级
tail -5 data/academic/runs/conference_full_20260311_131547/logs/serper_c_tier.log

# 2024 Serper B+
tail -5 data/academic/runs/conference_full_20260311_131547/logs/serper_2024_bplus.log

# 2024 Serper C 级
tail -5 data/academic/runs/conference_full_20260311_131547/logs/serper_2024_c_tier.log
```

## 故障恢复

```bash
# Serper 自动重试 (推荐! 自动轮换 Key)
nohup ./scripts/serper_auto_retry.sh \
  --input .../_full.json \
  --cache .../<cache_file>.json \
  --output .../outputs/ \
  --tiers "C" \
  --start-key 4 \
  --log .../logs/serper_auto.log &

# Serper 手动重启 (单个 Key)
SERPER_API_KEY=<next_key> python3 scripts/academic_contact_enricher.py \
  --input .../_full.json --output .../outputs/ \
  --cache .../<cache_file>.json --serper-only --serper-tiers <tiers>

# LLM 富化挂了 (缓存自动续传)
nohup python3 scripts/academic_llm_enrich.py \
  --deep-cache .../_deep_cache.json \
  --serper-cache .../_serper_cache.json \
  --input .../_full.json \
  --output .../_llm_enrichment_results.json \
  --workers 5 &

# 入库 (必须指定 DB_PATH!)
DB_PATH=/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db \
  python3 scripts/academic_import.py --update
```

## 关键缓存文件 (禁止删除)

| 文件 | 内容 |
|------|------|
| `_serper_cache.json` | 2025 Serper 结果 (增长中) |
| `all_conf_2024_contact_cache.json` | 2024 Serper 结果 (增长中) |
| `_deep_cache.json` | 3,997 主页爬取结果 |
| `_deep_github_cache.json` | 2,107 GitHub commit |
| `_llm_enrichment_results.json` | 3,587 LLM 结果 (R1+R2) |
| `_enrichment_cache.json` | 12,460 PDF 邮箱 |
| `all_conf_2025_*_full.json` | 12,460 人 S2 数据 |
| `all_conf_2024_*_full.json` | 17,923 人 S2 数据 |
| `duplicate_report.csv` | 2,409 跨源重复清单 |
