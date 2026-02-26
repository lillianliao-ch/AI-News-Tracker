# GitHub 网络挖掘 AI 人才完整工作流

## 🎯 项目目标
通过社交网络共现分析，发现、验证、丰富AI人才信息，最终建立可触达的人才库。

---

## 📊 完整 Pipeline 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                        第一轮：种子挖掘                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────────────┐
                    │   Phase 1     │
                    │  采集种子用户   │
                    │   (Neal12332)  │
                    └───────────────┘
                            ↓
                    ┌───────────────┐
                    │   Phase 2     │
                    │   AI相关性过滤   │
                    │ (Tier A/B/C)  │
                    └───────────────┘
                            ↓
                    ┌───────────────┐
                    │   Phase 3     │
                    │   Repos深度信息  │
                    │ (languages等)  │
                    └───────────────┘
                            ↓
                    ┌───────────────┐
                    │   Phase 3.5   │
                    │  个人主页爬取   │
                    │ (LinkedIn等)   │
                    └───────────────┘
                            ↓
                    ┌───────────────┐
                    │  入库 & 打标签  │
                    │   (Tier S/A+)  │
                    └───────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   第二轮：社交网络扩展                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
              ┌────────────────────────────────┐
              │          Phase 4               │
              │  社交网络扩展 (发现新人才)        │
              │                                 │
              │  输入: 262个种子(Tier S/A+/A)   │
              │  操作: 采集following列表        │
              │  分析: 共现频率统计            │
              │  输出: 892个新发现的AI人才       │
              │                                 │
              │  ✅ 已完成:                   │
              │     - GitHub基础信息          │
              │     - AI评分                  │
              │     - AI信号                  │
              │                                 │
              │  ⚠️  缺失:                   │
              │     - Repos深度信息 (Phase 3)  │
              │     - LinkedIn (Phase 3.5)     │
              │     - 职业经历 (Phase 3.5)     │
              │     - 学术信息 (Phase 3.5)     │
              └────────────────────────────────┘
                            ↓
              ┌────────────────────────────────┐
              │      Phase 3 (补强)            │
              │   获取Repos深度信息             │
              │  (languages, stars, repos)     │
              └────────────────────────────────┘
                            ↓
              ┌────────────────────────────────┐
              │     Phase 3.5 (补强)           │
              │   爬取个人主页深度信息          │
              │  (LinkedIn, 经历, 论文)        │
              └────────────────────────────────┘
                            ↓
              ┌────────────────────────────────┐
              │   入库 & 打标签 & 评级           │
              │    (Tier S/A+/A/B/B+)          │
              └────────────────────────────────┘
```

---

## 🔍 关键问题解答

### Q1: Phase 4 和 Phase 1 的区别？

| 维度 | Phase 1 | Phase 4 |
|------|---------|---------|
| **目标** | 单个用户（Neal12332） | 262个种子用户 |
| **操作** | 采集following | 采集following |
| **数据源** | GitHub API | GitHub API |
| **筛选** | 无筛选 | 共现频率筛选 |

**核心区别：Phase 4 = Phase 1 + 共现分析**

- Phase 1：单点采样
- Phase 4：多点采样 + 统计分析

### Q2: Phase 4 是否包含了 Phase 2/Phase 3？

| Phase | Phase 4是否包含 | 说明 |
|-------|----------------|------|
| Phase 1（GitHub基础信息） | ✅ 完全包含 | username, name, email, bio等17个字段 |
| Phase 2（AI评分） | ✅ 部分包含 | 有ai_score和ai_signals，但没有tier分类 |
| Phase 3（Repos深度信息） | ❌ 完全缺失 | 缺少languages, total_stars, top_repos等 |
| Phase 3.5（个人主页深度信息） | ❌ 完全缺失 | 缺少LinkedIn, 工作经历, 教育背景, 论文等 |

**Phase 4 = Phase 1 + Phase 2(部分)**

### Q3: Phase 4 完成后需要做什么？

```
Phase 4输出 (892人)
    ↓
❌ 缺少repos信息 → 需要运行 Phase 3 (补强)
    ↓
❌ 缺少LinkedIn → 需要运行 Phase 3.5 (补强)
    ↓
❌ 缺少深度职业信息 → 需要运行 Phase 3.5 (补强)
    ↓
✅ 最终可用的完整候选人数据
```

---

## 🚀 端到端完整执行指南

### 方案一：完整执行整个 Pipeline（推荐）

```bash
# 1. 第一轮：种子挖掘 (可选，如果已经有数据可跳过)
cd /Users/lillianliao/notion_rag/github_mining/scripts
python3 github_network_miner.py phase1 --target Neal12332
python3 github_network_miner.py phase2
python3 github_network_miner.py phase3
python3 github_network_miner.py phase3_5

# 2. 第二轮：社交网络扩展 (Phase 4)
# 从数据库加载Tier S/A+/A的种子
python3 github_network_miner.py phase4 --seed-tier S,A+,A --min-cooccurrence 3

# 3. 对Phase 4输出进行补强处理
# 3.1 Phase 3 补强: 获取repos信息
python3 github_network_miner.py phase3 --input phase4_expanded.json

# 3.2 Phase 3.5 补强: 爬取个人主页
python3 github_network_miner.py phase3_5 --input phase3_5_enriched.json

# 4. 入库和评级
python3 run_pipeline_v3.py --file phase3_5_enriched.json
```

### 方案二：针对Phase 4输出的完整处理

```bash
# 1. 确认Phase 4已完成
ls -lh github_mining/scripts/github_mining/phase4_expanded.json

# 2. 运行Phase 3补强脚本 (专门为Phase 4设计)
python3 github_network_miner.py phase3 --input phase4_expanded.json

# 3. 运行Phase 3.5补强
python3 github_network_miner.py phase3_5 --input phase3_5_enriched.json

# 4. 入库和评级
python3 run_pipeline_v3.py --file phase3_5_enriched.json
```

---

## 📋 各Phase详细说明

### Phase 1: 种子采集
- **输入**: 单个GitHub用户名
- **输出**: phase1_seed_users.json
- **数据**: GitHub基础信息（17个字段）

### Phase 2: AI过滤
- **输入**: phase1_seed_users.json
- **输出**: phase2_ai_filtered.json
- **数据**: AI评分 + tier分类

### Phase 3: Repos深度信息
- **输入**: phase2_ai_filtered.json
- **输出**: phase3_enriched.json
- **数据**: 增加repos相关字段（languages, total_stars, top_repos等）

### Phase 3.5: 个人主页爬取
- **输入**: phase3_enriched.json
- **输出**: phase3_5_enriched.json
- **数据**: 增加LinkedIn, 工作经历, 教育背景, 论文等

### Phase 4: 社交网络扩展
- **输入**: 262个种子用户（Tier S/A+/A）
- **输出**: phase4_expanded.json
- **数据**: GitHub基础信息 + AI评分 + 共现次数
- **状态**: ✅ Phase 1 ✅ Phase 2(部分) ❌ Phase 3 ❌ Phase 3.5

---

## ⚠️ 重要注意事项

1. **Phase 4输出不完整**
   - 只有GitHub基础信息和AI评分
   - 缺少repos、LinkedIn、经历等深度信息
   - 必须经过Phase 3和Phase 3.5补强才能使用

2. **共现分析的价值**
   - 不是简单采集，而是"被多个AI人才共同关注的人"
   - 优先级更高，相关性更强

3. **端到端执行**
   - 不要只跑Phase 4就结束
   - 必须完整跑完Phase 3和Phase 3.5
   - 最终数据才能用于outreach

4. **数据完整性检查**
   ```python
   # 检查数据完整性
   - LinkedIn: 应该有30-50%覆盖率
   - 邮箱: 应该有80%+覆盖率
   - 工作经历: 应该有60-70%覆盖率
   - 教育背景: 应该有40-50%覆盖率
   ```

---

## 🎯 总结

**Phase 4定位：发现新人才**
- ✅ 完成社交网络扩展
- ✅ 发现892个新AI人才
- ⚠️ 数据不完整（只有Phase 1+Phase 2(部分)）

**完整流程：Phase 4 → Phase 3 → Phase 3.5 → 入库**
- Phase 4: 发现
- Phase 3: Repos深度信息
- Phase 3.5: 个人主页深度信息
- 最终: 完整可用的候选人数据

**关键：必须端到端执行，不能半途而废！**