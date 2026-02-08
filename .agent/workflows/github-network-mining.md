---
description: 从AI猎头的GitHub Following网络中挖掘AI人才，包括采集、过滤、扩展、联系信息提取和自动Follow
---

# GitHub 社交网络挖掘 AI 人才 - 统一实施与验证方案

## 前提准备

1. **GitHub 登录**: 用户必须在浏览器中登录其 GitHub 账号（lillianliao），否则部分邮箱不可见
2. **GitHub Token**: 需要 Personal Access Token 用于 API 调用（Settings -> Developer settings -> Personal access tokens -> Tokens (classic)，勾选 `public_repo` 和 `read:user` 权限）
3. **脚本位置**: `/Users/lillianliao/notion_rag/github_network_miner.py`

---

## Phase 1: 种子采集（采集 Neal12332 的 Following 列表）

### 1.1 执行

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py phase1 --target Neal12332
```

**功能**: 
- 调用 GitHub API `GET /users/Neal12332/following?per_page=100` 分页采集全部 ~6,100 个 following 用户
- 采集基本信息: username, name, bio, company, location, email, followers, following, public_repos
- 保存到 `github_mining/phase1_seed_users.json` 和 `.csv`

### 1.2 验证 ✅ 检查点

运行验证脚本:
```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py verify1
```

验证项:
- [ ] **总数校验**: 采集数量 ≈ 6,100（与 GitHub 页面显示的 6.1k 一致，允许 ±50 误差）
- [ ] **去重校验**: username 无重复
- [ ] **字段完整率**: `username` 100%, `name` ≥ 80%, `bio` ≥ 40%
- [ ] **抽样比对**: 随机抽 10 人，用浏览器打开其 GitHub 页面，验证数据一致性

**🚦 通过标准**: 总数误差 < 2% 且抽样比对全部通过
**🚦 未通过**: 检查 API 分页逻辑或 Token 权限

---

## Phase 2: AI 相关性过滤

### 2.1 执行

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py phase2
```

**功能**:
- 从 Phase 1 结果中，通过 Bio/公司/仓库 关键词匹配过滤 AI 相关人才
- AI 关键词集: LLM, NLP, CV, transformer, diffusion, AIGC, agent, RAG, ML, DL, CUDA, GPU, 大模型, 多模态, 预训练, reinforcement learning...
- AI 公司集: ByteDance, Alibaba, Tencent, Baidu, ZhipuAI, Moonshot, Baichuan, MiniMax, SenseTime, Megvii, Huawei, OpenAI, DeepMind, Meta AI...
- AI 学校集: Tsinghua, PKU, NJU, SJTU, ZJU, USTC, Stanford, MIT, CMU, Berkeley...
- 输出分层: Tier A (强 AI 信号), Tier B (中 AI 信号), Tier C (弱/疑似 AI 信号)
- 保存到 `github_mining/phase2_ai_filtered.json` 和 `.csv`

### 2.2 验证 ✅ 检查点

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py verify2
```

验证项:
- [ ] **分布统计**: 打印公司 Top 20、地域 Top 10、关键词命中分布
- [ ] **精确率抽检**: 从 Tier A 随机抽 20 人，检查是否确实做 AI → 目标: ≥ 90%
- [ ] **精确率抽检**: 从 Tier B 随机抽 20 人 → 目标: ≥ 70%
- [ ] **召回率抽检**: 从被过滤掉的人中随机抽 20 人，检查是否有遗漏 → 目标: 漏判 ≤ 20%
- [ ] **直觉校验**: 公司分布 Top 10 应包含字节、阿里等主流 AI 公司

**🚦 通过标准**: Tier A 精确率 ≥ 90%, Tier B ≥ 70%
**🚦 未通过**: 调整关键词集重新执行 Phase 2

---

## Phase 3: 深度信息提取 + 浏览器验证（需要用户登录）

### 3.1 执行 — 批量 API 深度信息

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py phase3
```

**功能**:
- 对 Phase 2 的 Tier A + Tier B 用户进行深度信息提取
- 提取: 公开邮箱, commit 邮箱, Top 仓库详情, 编程语言, Star 数
- 评分排序(AI 相关度 30% + 影响力 25% + 活跃度 20% + 可联系性 15% + 地域 10%)
- 保存到 `github_mining/phase3_enriched.json` 和 `.csv`

### 3.2 执行 — 浏览器补充（需要用户手动登录 GitHub）

> ⚠️ **提醒用户**: 请先在浏览器中登录你的 GitHub 账号

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py phase3_browser --top 200
```

**功能**:
- 用浏览器逐一打开 Top 200 人的 GitHub 页面
- 采集仅登录可见的邮箱
- 对评分 ≥ 阈值的人才，自动点击 "Follow" 按钮
- 截图保存到 `github_mining/screenshots/`

### 3.3 验证 ✅ 检查点

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py verify3
```

验证项:
- [ ] **邮箱恢复率**: ≥ 50%（排除 `noreply@github.com`）
- [ ] **邮箱格式校验**: 无 noreply 邮箱混入
- [ ] **Follow 执行率**: 已 Follow 的人数统计
- [ ] **Tier A Top 20 人工审核**: 用户审核评分排名前 20 的人，确认质量

**🚦 通过标准**: 邮箱恢复率 ≥ 50%, Top 20 人工审核通过率 ≥ 80%

---

## Phase 4: 社交网络扩展

### 4.1 执行

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py phase4 --seed-top 300 --min-cooccurrence 3
```

**功能**:
- 从 Phase 3 评分 Top 300 的种子用户出发
- 采集他们各自的 following 列表
- 统计共现频率: 被 ≥ 3 个种子用户共同 follow 的新用户
- 对新发现的用户执行 Phase 2 同样的 AI 过滤
- 全局去重（与已有人才库对比）
- 保存到 `github_mining/phase4_expanded.json`

### 4.2 验证 ✅ 检查点

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py verify4
```

验证项:
- [ ] **去重率**: 新发现用户中与 Phase 1-3 的重复率统计
- [ ] **AI 精确率**: 随机抽 30 个新发现用户，AI 相关率 ≥ 70%
- [ ] **共现分布**: 共现频率 Top 50 人名单是否合理
- [ ] **高共现人才质量**: 共现 ≥ 5 的人应该是业内知名人士

**🚦 通过标准**: 新发现 AI 人才 ≥ 2,000 且精确率 ≥ 70%

---

## Phase 5: 入库 & 触达

### 5.1 入库到猎头系统

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py phase5_import
```

**功能**:
- 将最终人才清单导入 `personal-ai-headhunter` 数据库
- 字段映射: name → candidate.name, company → work_experience, email → contact
- 标记来源为 "GitHub Network Mining"

### 5.2 浏览器 Follow + 触达

> ⚠️ **提醒用户**: 请确保浏览器中已登录 GitHub 账号

```bash
cd /Users/lillianliao/notion_rag && python github_network_miner.py phase5_follow --tier A
```

**功能**:
- 批量 Follow Phase 4 新发现的优质人才
- 生成个性化邮件模板（引用其 GitHub 项目）

### 5.3 最终验证 ✅

- [ ] **交叉验证**: 抽 20 人在脉脉/LinkedIn 搜索，比对信息一致性
- [ ] **试触达**: 挑 5-10 人发邮件，观察回复率
- [ ] **总产出统计**: 总人才数、有邮箱人数、已 Follow 人数、已触达人数

---

## 输出文件目录结构

```
github_mining/
├── phase1_seed_users.json          # Phase 1 原始数据
├── phase1_seed_users.csv
├── phase2_ai_filtered.json         # Phase 2 AI 过滤结果
├── phase2_ai_filtered.csv
├── phase2_rejected.json            # Phase 2 被过滤掉的（用于召回率验证）
├── phase3_enriched.json            # Phase 3 深度信息
├── phase3_enriched.csv
├── phase3_follow_log.json          # Phase 3 Follow 记录
├── phase4_expanded.json            # Phase 4 扩展结果
├── phase4_expanded.csv
├── verification/                   # 验证报告
│   ├── verify1_report.txt
│   ├── verify2_report.txt
│   ├── verify3_report.txt
│   └── verify4_report.txt
├── screenshots/                    # 浏览器截图
└── final_candidates.xlsx           # 最终候选人清单
```

---

## 关键注意事项

1. **必须使用已登录的 GitHub 账号**: API 使用 Token，浏览器操作需要手动登录
2. **Token 权限**: 需要 `public_repo` + `read:user`，Follow 操作需要 `user:follow`
3. **速率控制**: API 有 Token 时 5,000次/小时，无 Token 仅 60次/小时
4. **Follow 策略**: 只 Follow 评分 ≥ 阈值（默认 Top 30%）的 AI 人才
5. **数据安全**: 所有数据仅用于合法招聘目的，不外泄
