# GitHub Mining 批次执行历史

**最后更新**: 2026-03-11

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
