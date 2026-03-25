# GitHub Mining 批次执行历史

**最后更新**: 2026-03-25

---

## 🔴 [INCIDENT] 2026-03-24 Academic-GitHub 共现批次 — 数据质量事故

### 事故摘要

| 项目 | 说明 |
|------|------|
| **发现时间** | 2026-03-25 08:00 |
| **影响** | 173 条外国人记录错误入库；4,314 人未入库 |
| **严重程度** | 中（DB 可修复，无不可逆数据丢失） |
| **根因** | `run_academic_cooc_pipeline.sh` 未调用 `batch_runner.py`，自行实现了阉割版流程 |

### 问题清单

| # | 缺失内容 | 实际影响 |
|---|---------|---------|
| 1 | **prefilter 完全缺失** | 306条入库中有 173 条外国人（56.5%）；4,814人未过滤跑了 Phase 3（浪费 API） |
| 2 | **Phase 4.5 LLM 富化缺失** | 所有入库记录无工作履历/技能/谈话点字段 |
| 3 | **Phase 3.5 只跑 Top 500** | 仅 500 人有主页富化，4,314 人未做 |
| 4 | **入库对象错误** | 只从 Phase 3.5 的 500 人入库，而非 Phase 3 的全量 4,814 人 |

### 数据量化

```
总共现挖掘: 4,814 人
prefilter 应过滤:
  - 机构账号:   5 人
  - 外国人:  1,381 人
  → 应保留:  3,428 人（chinese + unknown）

实际入库:      306 人（来自 Top 500，无过滤）
  - 外国人:    173 人 ← 错误入库
  - chinese/unknown: 133 人 ← 正确
未入库:      4,514 人（4,814 - 306 + 6 重复）
```

### 根因分析

- **直接原因**：设计 `run_academic_cooc_pipeline.sh` 时，没有使用已有的 `batch_runner.py`（7步标准流程），自行写了一个独立的5步 shell 脚本，漏掉了 prefilter / phase4_5，并将 phase3_5 限制在 Top 500
- **间接原因**：文档（`00-START-HERE.md`）虽然要求读工作流文档，但没有明确规定「入库必须走 `batch_runner.py`」，AI 在设计新 pipeline 时没有意识到需要复用

### 补救行动（2026-03-25）

| 步骤 | 状态 | 说明 |
|------|------|------|
| 删除 173 条外国人记录 | ✅ 完成 08:15 | 剩余 133 条均为 chinese/unknown |
| 启动补救批次（batch_runner）| 🔄 运行中 | 对 4,814 人跑 prefilter→db_dedup→phase3_5→phase4_5→db_import→tier_update |
| 重构 `run_academic_cooc_pipeline.sh` | ✅ 完成 | Steps 2-8 全部委托给 `batch_runner.py` |
| 更新约束文档 | ✅ 完成 | `batch_runner.py` 头部加「给 AI 的强制规范」, `00-START-HERE.md` 加 Pipeline 约束章节 |
| 添加 `ops-checklist.md` workflow | ✅ 完成 | git操作/DB操作/pipeline 三类高危操作前置检查 |

**补救批次**：`scripts/runs/20260325_081555_academic_cooc_remediation_20260325/`
- prefilter: 4,814 → 3,428（过滤 1,381 外国人 + 5 机构）
- db_dedup: 3,428 → 3,296（过滤 132 已在库）
- 预计入库约 1,000-2,000 人新候选人

### 预防改进

1. **`batch_runner.py` 强制规范注释**（第 25-57 行）：代码即文档，永不过时
2. **`00-START-HERE.md` 约束章节**：明确禁止另写独立 pipeline 替代 batch_runner.py 的步骤
3. **`run_academic_cooc_pipeline.sh` 重构为薄包装**：结构上不可能绕开 batch_runner.py
4. **`ops-checklist.md`**：强制前置检查——git仓库确认、DB路径确认、pipeline 标准步骤确认

---

## 🔗 2026-03-24 Academic-GitHub 共现挖掘批次

### 基本信息
- **脚本**: `github_mining/scripts/academic_cooccurrence_miner.py`
- **端到端流水线**: `github_mining/scripts/run_academic_cooc_pipeline.sh`
- **种子来源**: DB 中 academic 渠道有 `github_url` 的候选人
- **种子数量**: 3,849 个有效 GitHub username（过滤了 215 个组织账号）
- **共现阈值**: ≥2（被至少 2 个学术种子共同 follow）
- **Token 池**: 3 个，总速率 15,000次/小时

### 文件路径（CONVENTIONS.md 合规：带年份+日期）
| 文件 | 路径 |
|------|------|
| 种子列表 | `github_mining/academic_github_seeds_20260324.json` |
| 进度快照 | `scripts/github_mining/academic_cooc_progress_20260324.json` |
| 共现产出 | `scripts/github_mining/academic_cooc_expanded_20260324.json` |
| Phase 3 | `scripts/github_mining/academic_cooc_phase3_20260324.json` |
| Phase 3.5 | `scripts/github_mining/academic_cooc_phase35_20260324.json` |
| 流水线日志 | `github_mining/academic_cooc_pipeline_20260324.log` |

### 正式运行状态（更新：2026-03-24 16:12）
| 步骤 | 状态 | 说明 |
|------|------|------|
| 种子导出 | ✅ 完成 | 3,849 人，已保存，全部已在 DB |
| academic_cooccurrence_miner | ✅ **13:49 完成** | 共现挖掘成功 |
| academic_cooc_pipeline（共现网络扩展）| 🔄 **86%（4,150/4,814）** | 仍在运行，预计今晚完成 |
| Phase 3 富化产出 | 🔄 进行中 | 产出 `academic_cooc_phase3_20260324.json`（3,900人，带 final_score） |
| 入库 | 📋 待运行 | Phase 3 完成后执行 |
| 分级 | 📋 待运行 | — |

### 种子数据说明
> 3,849 人（`academic_github_seeds_20260324.json`）**已经是 DB 已有用户**（db_id 与 SQLite id 匹配），
> 不需要重新导入。真正的新产出是 `academic_cooc_phase3_20260324.json`（3,900人），待流水线完成后入库。

---

## 🎓 2026-03-24 顶会作者挖掘 (2019-2022届)

### 基本信息
- **脚本**: `github_mining/scripts/conf_author_miner_2019_2022.py`
- **目标会议**: NeurIPS, ICML, ICLR, CVPR, ICCV, ECCV, ACL, EMNLP, NAACL, AAAI
- **目标年份**: 2019-2022（预计已就职 3-5 年的 AI 人才）
- **数据源**: NeurIPS proceedings / ICML PMLR / ICLR OpenReview / ACL Anthology / S2 fallback
- **输出目录**: `data/conf_2019_2022/runs/pipeline_2019_2022_TIMESTAMP/`

### Dry-run 验证结果 (2026-03-24 08:13)
- 测试范围: NeurIPS 2021 + ICML 2021 + ACL 2021 (max 30篇/会议)
- NeurIPS 2021: 缓存命中 ✅
- ICML 2021 (PMLR v139): 正确解析 119 条 / 30 篇 ✅
- ACL 2021: ACL Anthology 解析（待验证正式运行）
- **DB 去重**: 103 新增 / 11 已存在 ✅
- **输出目录**: `runs/pipeline_2019_2022_20260324_081311/outputs/` ✅

### 已导入（2026-03-24 16:00）
- **小批次测试**（`authors_import_20260324_082406.json`，99人）→ **成功导入 96 人，3 人超时失败**
  - 格式：name / current_title / talent_tier / source:academic / notes（含会议+代表论文）
  - 数据富化状态：**未富化**（github_url/linkedin_url/email 多为 null，h-index=0）
  - 待后续跑 Semantic Scholar 富化 + LinkedIn/GitHub 查找

### 正式运行状态（更新：2026-03-24 16:12）
| 批次 | 会议 | 状态 |
|------|------|------|
| **batch_A_ai（S2 ID 补全）** | NeurIPS+ICML+ICLR+AAAI | 🔄 **71%（21,352/29,870）** 限流慢，预计明早完成 |
| 批次 B | CVPR+ICCV+ECCV | 📋 待运行 |
| 批次 C | ACL+EMNLP+NAACL | 📋 待运行 |

> `batch_A_ai` = 给 29,870 名 2019-2022 顶会论文作者补全 Semantic Scholar ID（用于后续拉 h-index、引用数）。
> S2 API 限流严重（每次等 30-38 秒），按当前速度预计明早 08:00 前完成。

> 详细执行步骤见: `docs/TASK_19_conf_2019_2022.md`

---



## 🔬 2026-03-24 S2 共作者扩散批次

### 基本信息
- **脚本**: `github_mining/scripts/s2_coauthor_expansion.py`
- **种子来源**: DB 中已有的 18,263 个学术人才（有 s2_id）
- **扩散年份**: 2021-2022 年论文
- **策略**: 每批约 3,200 种子，分批运行+导入

### 设计决策
> S2 共作者扩散**天然覆盖 2019-2022 届已就职人才**：
> 库里的 2023-2025 届种子，2021-2022 年发论文时的共作者，大量是比他们早 2-4 年毕业的人。
> 这批人到 2024 年工作 3-5 年，功能上等价于顶会作者挖掘（且依赖已有关系网更精准）。

### 批次记录

| 批次 | 种子范围 | 状态 | 共作者数 | 导入数 | PID |
|------|----------|------|----------|--------|-----|
| 批次1（停） | 1-3,200 | ✅ 扩散完成，富化被中断 | 86,055 | — | 5028（已停）|
| **批次2** | 1-6,400 | 🔄 **运行中** (08:19 启动) | 86,055+新增中 | 待完成 | 18952 |

### 监控命令
```bash
tail -f /Users/lillianliao/notion_rag/github_mining/data/s2_coauthor_expansion/batch2_6400.log
ps aux | grep s2_coauthor | grep -v grep
```

### 下次批次
- 批次3: `--max-seeds 9600`（9601-6400 从缓存，以此类推）
- 最终目标: 全量 18,263 个种子 ≈ 6 批次

---

## 🎓 2026-03-24 顶会作者挖掘 (2019-2022届) — ⏸️ 已暂停待修复

### 暂停原因
| 问题 | 说明 |
|------|------|
| NeurIPS S2 venue 名错误 | S2 存的是 `"Neural Information Processing Systems"`，不是 `"NeurIPS"` |
| OpenReview API 403 | `content.venue` 参数格式不被新版 API 接受 |

### NeurIPS 只有 2021 正常
- 2021 用缓存（上次 tencent miner 跑过），2019/2020/2022 返回 0
- ICML PMLR 网页解析正常 ✅

### 待修复后恢复
详细步骤见: `docs/TASK_19_conf_2019_2022.md`

---


## 📋 说明

本文档记录每次批次的详细信息、效果评估和优化建议。

**记录格式**:
- 基本信息（输入、输出、阶段）
- 过滤统计（Pre-filter、DB Dedup）
- 最终结果（新增人数、评级分布）
- 效果评估（优点、问题、优化点）
- 策略建议（下次改进）

---

## 🎓 2026-03-14 学术流水线 (Academic Sourcing Pipeline)

### 基本信息
- **批次目录**: `data/academic/runs/conference_full_20260311_131547/`
- **目标会议**: ICLR, ACL, NeurIPS, ICML, CVPR (2025 + 2024)
- **最终目标**: 为每位候选人建立完整猎头档案 (工作/教育/技能/联系方式/谈话点)

### 2025 年度

| 阶段 | 人数/状态 | 说明 |
|------|----------|------|
| Phase A-C 采集+S2 | 12,460 unique | ✅ |
| Phase D Serper (B+) | 5,067 | ✅ |
| Phase D Serper (C) | 7,393 | 🔄 PID 65120, Key 1, 34% |
| Phase E-F2 PDF+爬取+GitHub | — | ✅ |
| Phase F3 LLM (R1+R2) | 3,587 | ✅ 100% 完成 |
| Phase G 入库 | 8,246 新增 | ✅ (跨源隔离模式) |

### 2024 年度

| 阶段 | 人数/状态 | 说明 |
|------|----------|------|
| Phase A 论文采集 | 33,925 unique | ✅ |
| Phase C S2 富化 | 17,923 | ✅ 3/14 17:40 完成 |
| Phase D Serper (B+) | 7,276 | 🔄 PID 80649, Key 2, 22% |
| Phase D Serper (C) | 10,647 | 🔄 PID 84700, Key 4, 10% |
| Phase E-G | 待 Serper 完成 | |

### ⚠️ 事件记录 (2026-03-14)

1. **跨源污染事件**: `--update` 模式通过名字匹配，将 academic 数据写入了 242 条 github 记录
   - 已修复: 清除污染数据 + 重写 `import_to_db()` 逻辑
   - 规则确立: **不同渠道绝不互相更新**，只能各自 INSERT
2. **DB 路径陷阱**: CWD 不对导致写入影子 DB → 修复: 必须显式指定 `DB_PATH`
3. **匹配改进**: 同源匹配从 `name` 改为 `s2_id` ✅ (2026-03-14 完成)
4. **⚠️ 缓存字段名不统一** (2026-03-15 发现) — 导致分析代码查错字段、得出完全相反的结论
   - Serper cache: `homepage`, `emails`, `github`, `linkedin`
   - Deep cache: `homepage_text`, `all_emails`, `matched_email`, `github`, `linkedin`
   - Deep cache key: `deep_homepage::Name::URL` (有前缀，需 split 提取 name)
   - **TODO**: 2024/2025 跑完后统一 schema，所有缓存使用相同字段名

### 联系方式来源分析 (2026-03-15, 2025 年度)

> ⚠️ 此分析用于评估各步骤的投入产出比，指导后续年度的流程优化。

#### 邮箱覆盖 (按来源)

| Tier | 总数 | Serper 邮箱 | Deep 邮箱 | 仅Serper | 仅Deep | 重叠 | 无邮箱 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| S | 271 | 174 (64%) | 108 (39%) | 79 | 13 | 95 | 84 |
| A+ | 738 | 464 (62%) | 219 (29%) | 263 | 18 | 201 | 256 |
| A | 1,453 | 855 (58%) | 324 (22%) | 552 | 21 | 303 | 577 |
| B | 2,277 | 1,269 (55%) | 443 (19%) | 869 | 43 | 400 | 965 |
| C | 7,721 | 1,734 (22%) | 636 (8%) | 1,150 | 52 | 584 | 5,935 |
| **ALL** | **12,460** | **4,496 (36%)** | **1,730 (13%)** | **2,913** | **147** | **1,583** | **7,817** |

#### 主页/GitHub/LinkedIn 覆盖

| Tier | Serper 主页 | Serper GitHub | Serper LinkedIn | Deep GitHub | Deep LinkedIn |
|------|:---:|:---:|:---:|:---:|:---:|
| S | 270 (99%) | 89 (32%) | 54 (19%) | 7 | 14 |
| A+ | 736 (99%) | 310 (42%) | 157 (21%) | 22 | 36 |
| A | 1,294 (89%) | 654 (45%) | 323 (22%) | 50 | 72 |
| B | 2,245 (98%) | 1,019 (44%) | 502 (22%) | 40 | 79 |
| C | 2,818 (36%) | 1,307 (16%) | 680 (8%) | 15 | 93 |

#### 关键结论

1. **Serper 不可跳过** — 是最大邮箱来源 (4,496, 36%)，也是主页/GitHub/LinkedIn 的主要发现者
2. **Deep 是有效补充** — 在 Serper 没找到邮箱的人中，额外找到 147 个独占邮箱
3. **Serper → Deep 链条**: Serper 找到 7,363 个主页 → Deep 爬取这些主页 → 提取邮箱/LinkedIn
4. **B+ 级 Serper 邮箱 55-64%**，C 级仅 22% — C 级 presence 少，Serper 效果有限
5. **Deep 对 LinkedIn 的补充**: Serper LinkedIn 已较高 (19-22%)，Deep 额外补充 3-5%

### 关键数据
- **数据库 (2026-03-15 15:15)**: Academic **14,022** (原 4,397 + 2025 新增 8,246 + 2024 新增 1,379)，全库 **53,109**
- **跨源重复**: 2,409 条 (`duplicate_report.csv`)，暂不合并
- **同名碰撞**: 290 条疑似错配 (`name_collision_report.csv`)，S/A+ 34 条需优先处理
- **Serper Keys**: 共 10 个，已耗尽，2023 年需补充新 key

### 2024+2025 联系方式合并统计 (去重后 23,848 人)

| Tier | 总数 | 有邮箱 | LinkedIn | GitHub | 可触达(邮箱或LI) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| S | 461 | 231 (50%) | 67 (14%) | 107 (23%) | 239 (51%) |
| A+ | 1,329 | 617 (46%) | 202 (15%) | 390 (29%) | 650 (48%) |
| A | 2,745 | 1,148 (41%) | 442 (16%) | 856 (31%) | 1,200 (43%) |
| B | 4,439 | 1,691 (38%) | 659 (14%) | 1,329 (29%) | 1,783 (40%) |
| C | 14,868 | 2,714 (18%) | 999 (6%) | 1,867 (12%) | 2,858 (19%) |
| **B+合计** | **8,974** | **3,687 (41%)** | — | — | **3,872 (43%)** |

### ⚠️ 事件记录 (2026-03-15)

5. **2024 Deep 用错缓存** — `find_cache serper` 找到 `_serper_cache.json` (2025的)，2024 独有 11,378 人完全未被 Deep 处理
   - 修复: 合并两个 Serper 缓存 → `_serper_cache_merged.json` (41,765 条)，重跑 2024 Deep
   - 根因: 多年份共用 run 目录 + 缓存文件无年份标识 (详见 CONVENTIONS.md)
6. **2023 Pipeline 空跑** — Step 1 合并脚本搜 `*2023*_full.json`，但文件名是 `academic_20260315_*_full.json`，匹配到 0 个文件
   - 采集数据仍在: ICLR 1,307 + NeurIPS 6,192 + ICML 2,852 = ~10,351 人
   - 需要修复合并逻辑后重跑 Step 2-7
7. **同名碰撞** — Serper 搜 "Yuan Qi" 找到了错误的人 (齐逸岩 而非论文作者)
   - 已生成校验报告: `data/academic/name_collision_report.csv` (290 条)
   - 解决方案: 缓存 key 改 s2_id + Serper 搜索加机构消歧 + LLM 后验证

### 评级体系对照

| 等级 | Academic (h-index) | GitHub (综合) |
|:---:|------|------|
| S | h ≥ 40 | Followers >5k / Stars >5k |
| A+ | h ≥ 20 | 3+ 顶会论文 |
| A | h ≥ 10 | 顶尖 Lab |
| B | h ≥ 5 | 一线大厂 + 985 |
| C | h < 5 | 其他 |

> ⚠️ Academic 纯靠 h-index，会低估业界转型者（如前蚂蚁副总裁）。TODO: 综合评级。

---

## 2026-03-11 批次（进行中）

### 基本信息
- **批次 ID**: 20260311_104622_phase5_full_production_final
- **输入文件**: phase5_expanded_latest.json (28,242 人)
- **执行阶段**: prefilter → db_dedup → phase3 → phase3_5 → phase4_5 → db_import → tier_update
- **开始时间**: 10:46:22
- **Phase 3 完成**: 17:03 (✅)
- **Phase 3.5 完成**: ~00:11 3/12 (✅)
- **Phase 4.5 重启**: 06:55 3/12 (修复后重新执行)

### 过滤统计
- **Pre-filter**: 28,242 → 15,472 人
  - 机构过滤: 22 人
  - 外国人过滤: 12,748 人（45%）
  - 中文: 7,982 人
  - Unknown: 7,490 人

- **DB Dedup**: 15,472 → 10,497 人
  - 已在库: 4,975 人（32%）
  - 需处理: 10,497 人

### Phase 4.5 Bug 报告 🐛

**现象**: Phase 4.5 运行 10+ 小时，`check_progress.sh` 始终显示 67.8%/waiting

**根因 (3个)**:
1. **进度追踪 Bug**: `phase4_5_progress.json` 中 2,406 个 completed username 与 target_candidates (1,282人) **零重叠**。原因是进度文件残留了旧批次数据，导致断点续传完全失效，每次重启都从头跑
2. **filter_with_websites 过于严格**: 只选 `homepage_scraped=True` 的人 (1,282)，忽略了 5,137 个有 blog URL 但未爬取的候选人
3. **串行执行**: 单线程逐人处理 (~4人/min)，没有并发

**修复 (2026-03-12 06:55)**:
1. ✅ 扩展 `filter_with_websites` → 1,282 → **6,419 人** (含所有 blog URL)
2. ✅ 优化 `scrape_website_content` skip_domains — 保留 github.io/CSDN/博客园等
3. ✅ 修复进度追踪 — 自动清理不在 target 中的过期 completed IDs
4. ✅ 加 `ThreadPoolExecutor(max_workers=5)` → **22人/min** (5.3x 提速)

### 最终结果
- **新增候选人**: 9,315 人
- **评级分布**: S:108 | A:136 | B+:240 | B:3,264 | C:5,462 | D:105
- **优质候选人 (S/A/B+)**: **484 人 (5.2%)**
- **跳过**: 936 已存在 + 246 组织账号
- **Phase 4.5 LLM 富化**: 6,419 目标 → 4,941 成功 (77%) / 1,478 失败
- **完成时间**: 2026-03-12 13:05 (db_import + tier_update)

### 数据质量报告

| 字段 | 人数 | 覆盖率 | 备注 |
|------|------|--------|------|
| 邮箱 | 5,521 | 52.6% | 正常 |
| LinkedIn | 467 | **4.4%** | ⚠️ 异常低（旧批次 24.4%） |
| Twitter/X | 2,340 | 22.3% | GitHub API 原生字段 |
| Google Scholar | 433 | 4.1% | |
| LLM提取-工作履历 | 2,516 | 24.0% | Phase 4.5 新增 |
| LLM提取-教育背景 | 1,949 | 18.6% | Phase 4.5 新增 |
| LLM提取-技能列表 | 4,319 | 41.1% | Phase 4.5 新增 |

### 效果评估
- ✅ **优点**:
  - Pre-filter 有效过滤外国人（12,748 人，节省大量 API）
  - DB Dedup 有效去重（4,975 人）
  - Phase 4.5 并发优化效果显著（22人/min，6,419人约 4.5h 完成）
  - 批次隔离系统工作正常

- ⚠️ **问题**:
  - 🐛 **LinkedIn 覆盖率异常低 (4.4% vs 旧批次 24.4%)** — **根因: Phase 3.5 断点续传 Bug**。batch_runner 中断后重启时，Phase 3.5 用 INPUT 数据覆盖了 OUTPUT 数据，导致第一轮成功爬取的 3,591 个用户的 LinkedIn/Scholar 等社交链接全部丢失。只剩第二轮的 1,282 个结果。详见「Phase 3.5 Resume Bug 报告」。
  - Phase 4.5 进度追踪 Bug（已修复）
  - filter_with_websites 漏掉 5,137 人（已修复）
  - check_progress.sh 不识别 Phase 4.5 进度（已修复）
  - batch_runner.py 父进程在 kill Phase 4.5 后状态不一致（需手动执行后续阶段）

- 💡 **优化点**:
  - ✅ 已加并发处理
  - ✅ check_progress.sh 已适配 Phase 4.5 进度文件
  - ✅ Phase 3.5 resume Bug 已修复（合并 OUTPUT 数据回 INPUT）
  - ✅ Phase 4.5 `scrape_website_content` 已增加社交链接提取
  - ✅ 数据补救脚本 `remediate_social_links.py` 已运行
  - 🔧 batch_runner.py 需要支持从指定阶段恢复

### Phase 3.5 Resume Bug 报告 🐛

**现象**: Phase 3.5 断点续传时，第一轮成功爬取的 3,591 个网站的社交链接数据全部丢失

**根因**: `phase3_5_enrich` 的 resume 逻辑从 INPUT 文件重新加载数据作为基础，仅用 OUTPUT 文件获取已完成用户名列表（用于跳过），但未将 OUTPUT 中已富化的数据合并回 INPUT 用户。保存时用 INPUT 空白数据覆盖了 OUTPUT。

**对比**: Phase 3 的 resume 逻辑正确（`enriched = existing`），Phase 3.5 缺少这一步。

**影响**: 约 3,591 个网站的 LinkedIn/Scholar/Twitter 链接丢失，导致 LinkedIn 覆盖率从预期 ~15% 降到 4.4%

**修复 (2026-03-12 22:05)**:
1. ✅ `github_network_miner.py` Phase 3.5 resume 逻辑修复 — 现在合并 OUTPUT enriched 数据回 INPUT
2. ✅ `run_phase4_5_llm_enrichment.py` `scrape_website_content` 增加社交链接提取
3. ✅ `remediate_social_links.py` 补救脚本运行，重新爬取 12,212 个有网站但无 LinkedIn 的候选人

### 策略建议
- ✅ 下次继续使用 Pre-filter（效果显著）
- ✅ 下次继续使用 DB Dedup（避免重复）
- 🔧 下次跑批前确认 progress 文件干净（或直接删除旧 progress）

---

## 2026-03-11 测试批次

### 基本信息
- **批次 ID**: 20260311_100022_test_tail_10
- **输入文件**: test_input_tail_50.json (50 人)
- **执行阶段**: prefilter → db_dedup → phase3 → phase3_5 → phase4_5 → db_import → tier_update
- **开始时间**: 10:00:22
- **完成时间**: 10:03:50
- **耗时**: 3 分 28 秒

### 过滤统计
- **Pre-filter**: 50 → 30 人
  - 外国人过滤: 20 人

- **DB Dedup**: 30 → 24 人
  - 已在库: 6 人

### 最终结果
- **新增候选人**: 23 人（1 个机构账号跳过）
- **评级分布**:
  - B: 6 人
  - C: 16 人
  - D: 1 人
- **数据质量**:
  - 邮箱覆盖: 17/24 (71%)
  - LinkedIn: 1/24 (4%)
  - 个人网站: 16/24 (67%)
  - 高质量简历: 1/24 (4%)
  - 含破冰话题: 10/24 (42%)

### 效果评估
- ✅ **优点**:
  - 端到端流程验证通过
  - 所有阶段正常工作
  - 批次隔离和自动备份有效

- ⚠️ **问题**:
  - 无

- 💡 **优化点**:
  - 测试成功，可以跑大批次

### 策略建议
- ✅ 流程已验证，可以跑全量数据

---

## 2026-03-11 早期测试批次

### 基本信息
- **批次 ID**: 20260311_091913_final_validation_20
- **输入文件**: test_input_50.json (50 人)
- **执行阶段**: prefilter → db_dedup → phase3 → phase3_5 → phase4_5 → db_import
- **完成时间**: 09:24:46

### 过滤统计
- **Pre-filter**: 50 → 30 人
- **DB Dedup**: 30 → 19 人

### 最终结果
- **新增候选人**: 7 人
- **评级分布**:
  - S: 2 人
  - B: 4 人
  - C: 1 人

### 效果评估
- ✅ **优点**: 测试成功
- ⚠️ **问题**: 缺少 tier_update 阶段
- 💡 **优化点**: 增加 tier_update 阶段

---

## 历史批次统计

### 总体数据
- **总批次数**: 7 个
- **成功批次**: 6 个
- **失败批次**: 1 个
- **总处理人数**: ~100 人（测试）
- **总新增人数**: ~40 人

### 效果最好的批次
- **批次**: 20260311_100022_test_tail_10
- **原因**: 完整流程，所有阶段正常

### 遇到的主要问题
1. 数据覆盖（已解决 - 批次隔离）
2. 日志文件为空（已知问题 - 设计限制）
3. 外国人混入（已解决 - Pre-filter）

---

## 📊 批次效果对比

| 批次 | 输入 | 输出 | Pre-filter 效果 | DB Dedup 效果 | 评级分布 |
|------|------|------|----------------|--------------|---------|
| 2026-03-11 生产 | 28,242 | 10,497 | 45% 过滤 | 32% 去重 | 待完成 |
| 2026-03-11 测试 | 50 | 24 | 40% 过滤 | 20% 去重 | B:6, C:16, D:1 |

---

## 💡 经验总结

### 有效的策略
1. ✅ **Pre-filter 必须执行**（可过滤 40-45% 外国人）
2. ✅ **DB Dedup 必须执行**（可去重 20-32%）
3. ✅ **批次隔离系统**（零数据丢失）
4. ✅ **自动备份机制**（防止覆盖）
5. ✅ **并发 LLM 处理**（5.3x 提速, 22人/min vs 4人/min）

### 无效的策略
1. ❌ **跳过 Pre-filter**（会处理大量外国人）
2. ❌ **使用固定文件名**（会覆盖数据）
3. ❌ **filter_with_websites 只看 homepage_scraped**（会漏掉 80% 有 blog URL 的人）

### ⚠️ 已踩的坑 (必看)
1. 🐛 **进度文件 (progress.json) 里的 ID 必须与 target 匹配** — 如果 input 数据变了但 progress 没清，断点续传会完全失效
2. 🐛 **blog URL ≠ homepage_scraped** — 有 blog 字段不代表已爬取。必须区分「有 URL」和「URL 已成功爬取」
3. 🐛 **check_progress.sh 显示的百分比可能误导** — 分母必须用对应阶段的实际目标数，而不是 pre_filter 总数
4. 🐛 **kill 子进程后父进程 (batch_runner.py) 状态不一致** — 需要手动执行后续阶段
5. 🐛 **LinkedIn 覆盖率低于预期** — Phase 3.5 网站爬取范围太窄，导致 LinkedIn URL 提取从 24.4% 降到 4.4%。Phase 4.5 LLM 提取未回写 `linkedin_url` 字段

### 待验证的策略
1. ⏳ **实时日志输出**（待实现）
2. ⏳ **进度通知**（待实现）
3. ⏳ **数据质量自动检查**（待实现）
4. ⏳ **batch_runner 支持从中间阶段恢复**（待实现）

---

## 📝 更新指南

**每次跑批后，请更新本文档**：

1. 复制模板：
```markdown
## YYYY-MM-DD 批次

### 基本信息
- 批次 ID:
- 输入文件:
- 执行阶段:

### 过滤统计
- Pre-filter:
- DB Dedup:

### 最终结果
- 新增候选人:
- 评级分布:

### 效果评估
- ✅ 优点:
- ⚠️ 问题:
- 💡 优化点:

### 策略建议
-
```

2. 填写实际数据

3. 更新"历史批次统计"

---

**维护者**: GitHub Mining Team
**最后更新**: 2026-03-12

---

## 🔜 待跟进事项 (2026-03-12)

### ✅ 已完成
- [x] Phase 4.5 完成后，手动执行 `db_import` 和 `tier_update`
- [x] 更新本文档的「最终结果」部分
- [x] 更新 `check_progress.sh` — 正确读取 Phase 4.5 进度 + 修复分母
- [x] 修复 Phase 3.5 resume 数据覆盖 Bug（`github_network_miner.py`）
- [x] Phase 4.5 `scrape_website_content` 增加社交链接提取
- [x] 运行 `remediate_social_links.py` 补救丢失的 LinkedIn 数据

### 近期优化
- [ ] `batch_runner.py` 增加「从指定阶段恢复」功能
- [ ] 每次跑批前自动清理或验证 progress 文件

### 长期改进
- [ ] 实时日志输出（替代 subprocess.run 的 capture_output）
- [ ] 进度通知（钉钉/微信）
- [ ] 数据质量自动检查报告
