---
description: GitHub Mining 执行细节参考文档，包含爬取方法、分级标准、字段映射、验证方法
---

# GitHub Mining 执行参考文档

> ⚠️ **文档治理规则**
> 
> GitHub Mining 项目**有且仅有**以下 2 个文档：
> 1. **主文件**: [github-network-mining.md](file:///Users/lillianliao/notion_rag/.agent/workflows/github-network-mining.md) — 路线图 + Runbooks（做什么）
> 2. **本文件**: `github-mining-reference.md` — 执行细节参考（怎么做）
>
> **规则**：
> - 🚫 **不得新建**其他 GitHub Mining 相关文档或 markdown 文件
> - ✅ 新信息必须**更新到这两个文件中**对应的章节
> - ✅ 执行过程中发现的新知识（如新的爬取技巧、bug 修复）也更新到本文件
> - 📍 分级标准**唯一以本文件为准**，不参考其他来源

---

## 1. Phase 3.5 爬取细节

### 1.1 个人主页分析方法

Phase 3.5 对 Tier A 候选人的个人网站进行爬取，提取结构化信息。

**数据来源**:
- Phase 1 `blog` 字段中的个人网站 URL（GitHub Pages ~820 人，个人域名 ~199 人）
- Bio 中的 URL 链接（~65 人）
- Phase 1 `blog` 字段中的 `scholar.google.com` 链接（~60 人）

**必须提取的字段**:

| 字段 | 提取方式 | 重要性 |
|:---|:---|:---|
| **LinkedIn URL** | 页面中 `linkedin.com/in/` 链接 | ⭐⭐⭐ 核心 |
| **个人主页 URL** | GitHub `blog` 字段 | ⭐⭐⭐ 核心 |
| **Google Scholar URL** | `scholar.google.com` 链接 | ⭐⭐⭐ 核心 |
| 额外邮箱 | `mailto:` 链接、页面文本中的邮箱 | ⭐⭐ |
| Twitter/微博链接 | `twitter.com` / `weibo.com` 链接 | ⭐⭐ |
| 当前职位 | 页面结构化信息 | ⭐⭐ |
| 工作经历 | LinkedIn 数据或页面提取 | ⭐⭐ |
| 教育背景 | 页面提取 | ⭐⭐ |
| 发表论文/顶会 | Scholar 或页面提取 | ⭐⭐ |
| 研究方向 | 页面提取 | ⭐ |
| 是否在招聘 | "hiring"/"招聘" 关键词 | ⭐ |

**技术实现**:
- 使用 `requests` + `BeautifulSoup` 爬取
- SSL 验证跳过（`verify=False`）处理证书问题
- GitHub Pages 个人主页优先处理（格式相对统一）
- 限制并发和频率，避免被封

### 1.2 Google Scholar 数据提取

**提取字段**: 论文总数、总引用数、h-index、近 5 年引用数、Top 论文、研究方向

**实现方案**（已选择方案C）:
- 直接 HTTP 请求 + BeautifulSoup 解析
- 备选: `scholarly` Python 库（免费但可能被反爬）
- 备选: SerpAPI（付费但稳定）

### 1.3 LinkedIn 信息获取

**获取方式**: 从个人主页中提取 LinkedIn URL 后：
- Phase 3.5 目前仅记录 LinkedIn URL（不主动爬取 LinkedIn 页面）
- LinkedIn URL 保存到 `linkedin_url` 字段
- 导入系统时映射到候选人的 `linkedin` 字段

**LinkedIn 数据（如已有）**:
- `linkedin_position`: 当前职位
- `linkedin_career`: 工作经历列表 `[{company, title, time, description}]`
- `linkedin_achievements`: 奖项/成就

---

## 2. 分级标准 (Talent Tier Standards)

> 📍 **这是分级标准的唯一真相源**
> 📊 **配置文件**: `personal-ai-headhunter/data/company_tier_config.json`

基于业务需求与大厂职级体系（P级）对齐的 **6 级**标准。

### 2.1 标准定义

| 等级 | 对应职级 | 核心画像 | 关键判定条件 | 典型示例 |
|:---|:---|:---|:---|:---|
| **🔴 S** | P10/P11+ | 行业领军 | Followers>5k OR Stars>5k OR H-index>30 | 王晋东(教授), 稚晖(华为), Yang Yu(南大) |
| **🟠 A+** | P8/P9 | 学术/技术强者 | 3+ 顶会论文可查 | 王思为(42篇), 方佳瑞(ColossalAI CTO) |
| **🟡 A** | P7/P8 | 顶尖Lab | 在 Seed/通义/MSRA 等顶尖Lab | 惠彬元(通义), 姜轶昆(PyTorch) |
| **🔵 B+** | P6/P7 | 一线+名校 | 一线大厂 + 985高校 | Li Jiahao(字节/清华), doubleZ(阿里/北大) |
| **⚪ B** | P5/P6 | 大厂或名校 | 一线大厂(学校不明) OR 985+二线大厂 OR 500+Followers | PureWhiteWu(字节), HarrisonXi(网易) |
| **🟢 C** | 观察池 | 普通 AI 开发者 | AI方向但无大厂/硕博光环 (沉默的大多数) | 绝大部分长尾 AI 算法开发工程师 |
| **⚫ D** | 隔离区 | 明确非 AI | Bio 包含前端/移动端/测试等无关关键词 | 任玉刚(Android), 黄晓刚(前端) |

### 2.2 自动分级逻辑 (`batch_update_tiers.py`)

按以下**优先级顺序**判定：

100. **S级**: `Followers > 5000` OR `Total Stars > 5000` OR `H-index > 30`
101. **A+级**: 顶会论文 ≥ 3 篇（ICLR/NeurIPS/ICML/ACL/CVPR/ICCV 等）
102. **A级**: Bio/公司/仓库 匹配顶尖 Lab 关键词（即使没有论文）
103. **学术标记**: `structured_tags.google_scholar` 存在（用于 Email Prompt 路由判定）
104. **D级**(隔离区): Bio 包含明确非 AI 的关键词 (Android, iOS, Frontend, Vue 等)
105. **B+级**: 一线大厂 + 985 高校
106. **B级**: 一线大厂(学校不明) OR 985+二线大厂 OR 纯二线大厂 OR Followers > 500
107. **C级**(兜底): 以上都不满足（正常 AI 标签开发者）

> ⚠️ **匹配机制警告**: 为了防止像 `thu` 这样极短的学校缩写意外击中 `github` 这样的无关长单词，代码层面已强制启用了**Regex英语单词边界匹配 (`\b`)**。仅当关键词独立成词时才会得分。

### 2.3 配置文件 (`data/company_tier_config.json`)

| 分类 | 说明 | 示例 |
|:---|:---|:---|
| `tier1_companies` | 一线大厂 | 阿里、字节、腾讯、华为、百度、DeepSeek、MiniMax、智谱、Moonshot |
| `tier2_companies` | 二线大厂 | 京东、美团、小红书、快手、网易、B站、商汤、旷视、讯飞 |
| `top_labs` | 顶尖实验室 | Seed、通义/DAMO、2012/Noah、MSRA、FAIR、Google Brain |
| `985_universities` | 985+海外名校 | 清北浙复交南、中科大哈工大、Stanford/MIT/CMU |

**维护方式**: 直接编辑 JSON 文件新增关键词，无需修改代码。

### 2.4 人工覆盖

`batch_update_tiers.py` 中的 `manual_overrides` 字典优先级高于自动判定。


---

## 3. 数据字段映射

### 3.1 GitHub → 系统映射

从 `phase3_5_enriched.json` 导入到 `personal-ai-headhunter` 的字段映射：

| GitHub 源字段 | 目标字段 (Candidate) | 处理逻辑 |
|:---|:---|:---|
| `username` / `name` | `name` | 优先用 `name`，若无则用 `username`；自动保留中文名 |
| `email` | `email` | 优先主邮箱，无则取 `extra_emails[0]` |
138. | `linkedin_position` / `company` | `current_title` / `current_company` | 优先 LinkedIn 数据，否则从 Bio 提取 |
139. | `blog` | `personal_website` | 个人网站链接 |
140. | `twitter_url` | `twitter_url` | Twitter 链接 |
141. | `linkedin_career` | `work_experiences` | 转换为 `[{company, title, time, description}]` |
142. | `top_venues` / `linkedin_achievements` | `awards_achievements` | 合并顶会论文统计和 LinkedIn 奖项 |
143. | `final_score` | `structured_tags.github_score` | 存入 JSON 标签 |
144. | `top_repos` | `structured_tags.top_repos` | **重要**：回填开源项目亮点 (用于 Email Prompt) |
145. | `homepage_text` | `website_content` | **重要**：个人主页抓取摘要 (用于 Email Prompt) |
146. | `followers` | `structured_tags.github_followers` | 存入 JSON 标签 |
147. | `github_url` | `github` | GitHub 链接 |
148. | — | `source` | 固定值 `"github"` |

### 3.2 去重策略

导入时按以下顺序检查是否已存在：
1. **GitHub URL**（唯一性最高）
2. **Email**
3. **Name**（仅在 Name ≠ Username 时检查）

任何命中的记录都会被跳过。

---

## 4. 评分公式

### 4.1 Phase 3 基础评分 (`final_score`)

| 维度 | 权重 | 说明 |
|:---|:---|:---|
| AI 相关度 | 30% | Bio/仓库中 AI 关键词密度 |
| 影响力 | 25% | Followers、Star 总数 |
| 活跃度 | 20% | 近期 commit 频率、仓库更新 |
| 可联系性 | 15% | 有邮箱 +10，有个人网站 +5 |
| 地域 | 10% | 中国/北美 +10，其他按比例 |

### 4.2 Phase 3.5 加分 (`enrichment_bonus`)

爬取个人主页后的额外加分：
- 有顶会论文统计: +5~15
- 有 Google Scholar 且 H-index > 10: +5~10
- 有额外邮箱: +2
- 有 LinkedIn: +2
- 有教育背景: +1
- 在招聘 (hiring): +1

新评分: `final_score_v2 = final_score + enrichment_bonus`

---

## 5. 验证方法

### 5.1 Phase 1 验证 (`verify1`)
- 总数与 GitHub 页面 Following 数一致（±2%）
- Username 无重复
- `name` 覆盖率 ≥ 80%，`bio` 覆盖率 ≥ 40%

### 5.2 Phase 2 验证 (`verify2`)
- Tier A 随机抽 20 人，AI 精确率 ≥ 90%
- Tier B 随机抽 20 人，AI 精确率 ≥ 70%
- 公司分布 Top 10 包含字节、阿里等

### 5.3 Phase 3 验证 (`verify3`)
- 邮箱覆盖率 ≥ 50%（排除 noreply）
- Top 20 人工审核通过率 ≥ 80%

### 5.4 增量处理验证（每次执行 Runbook 1 后）
- 新增候选人数与预期一致
- 数据库中未分级人数为 0
- 无报错信息

---

## 6. Token 轮换策略

- Token 1 (lillianliao-ch): 用于 Phase 1 前 2,250 人
- Token 2 (备用账号): 用于 Phase 1 剩余 3,881 人 + Phase 3
- 每个 Token 5,000 次/小时
- 限流时自动等待或手动切换
- Fine-grained Token 可用于 API 读取，Classic Token 才支持 Follow

---

## 7. 执行记录

### 2026-02-08 ~ 02-09

| 操作 | 结果 |
|:---|:---|
| Phase 1 | 6,081 人，2 个 Token，~50 分钟 |
| Phase 2 | 3,723 AI 人才 (Tier A 1,027 / Tier B 2,508) |
| Phase 3 | 3,723 人全量，邮箱 61.6% |
| Phase 3.5 (批次1) | Top 50，成功爬取 14 人 |
| Phase 3.5 (批次2) | Top 70 --resume，新增处理 21 人(成功14/失败7) |
| 导入系统 (首批) | 63 人入库（44 新增 + 19 已存在跳过 + 7 组织跳过） |
| 自动分级 (首批) | 63 人全部完成 (S:7 / A:31 / B:19 / C:6) |
| 批量导入 Top 500 | 424 人新增（66 去重跳过 + 10 组织跳过） |
| Phase 3.5 (批次3) | Top 500 --resume，200 成功 / 40 失败 |
| DB 增强更新 | 253 人补充数据（LinkedIn 42, Scholar 67, Twitter 136, Awards 77） |
| 重新分级 | 8 人升级（含 Chenfei Wu A→S, Xingkai Yu B+→S）|
| 基本盘分布 | S:27 / A:76 / B+:239 / B:130 / C:14 (共 486 人) |

### 2026-02-15 (Phase 3.5 全量深挖)

| 操作 | 结果 |
|:---|:---|
| Phase 3.5 全量深挖 | 利用 Lamda Scraper 工具链与网络爬虫，对所有候选人外部主页和简历进行交叉检索 |
| 数据入库 | 导入系统，大幅提升邮箱和履历覆盖率 |
| **最终 DB 指标** | **共 3,167 人**入库。**邮箱覆盖 66.9%** (2,120人)，**经历覆盖 86.5%** (2,738人) |---

## 8. 文件与脚本索引

### 8.1 数据文件 (`github_mining/`)

```
github_mining/
├── phase1_seed_users.json          # Phase 1 原始数据 (6,081人)
├── phase1_following_list.json      # 断点续传用
├── phase2_ai_filtered.json         # Phase 2 AI 过滤结果 (3,723人)
├── phase2_tier_a/b.json            # Phase 2 分层
├── phase3_enriched.json            # Phase 3 深度信息 + 评分 (3,723人)
├── phase3_5_enriched.json          # Phase 3.5 主页增强 (旧流程产出)
├── linkedin_career_data.json       # LinkedIn 工作经历缓存
├── verification/                   # 验证报告
├── screenshots/                    # 浏览器截图
└── scripts/github_mining/          # V3/Phase 4 流程数据（新）
    ├── phase2_v3_enriched.json     # Phase 2 V3 全量轻富化
    ├── phase3_v3_ai_candidates.json # Phase 3 V3 AI 判定通过
    ├── phase3_v3_rejected.json     # Phase 3 V3 非 AI
    ├── phase4_expanded.json        # Phase 4 社交网络扩展 (892人)
    ├── phase3_from_phase4.json     # Phase 4 候选人 Phase 3 补强
    ├── phase4_final_enriched.json  # Phase 4 最终富化输出
    └── pipeline_state.json         # 流水线断点状态
```

### 8.2 采集脚本 (`github_mining/scripts/`)

| 脚本 | 用途 |
|:---|:---|
| `github_network_miner.py` | 核心采集 Phase 1-4 |
| `github_hunter_config.py` | GitHub Token 及配置文件 |
| `auto_restart_wrapper.py` | 崩溃自动重启包装器 |
| `run_phase4_enrichment.py` | Phase 4 全自动流水线（富化→入库→分级） |
| `run_pipeline_v3.py` | V3 入库+过滤+打标流水线 |

### 8.3 猎头系统脚本 (`personal-ai-headhunter/`)

> 这些脚本依赖猎头系统的 `database.py`，留在原位

| 脚本 | 用途 |
|:---|:---|
| `import_github_candidates.py` | Phase 6: 导入系统 |
| `scripts/label_github_candidates.py` | Phase 6.5: Priority 标签 |
| `scripts/fetch_github_bios.py` | Phase 6.5: Bio 二次筛选 |
| `data/github_bios.json` | Bio 缓存（2,088条） |

### 8.4 文档 (`github_mining/docs/`)

| 文档 | 内容 |
|:---|:---|
| `GITHUB_HUNTER_GUIDE.md` | Hunter 工具使用指南 |
| `GMAIL_GITHUB_SCRAPER_ANALYSIS.md` | Gmail+GitHub 联合分析 |

---

## 9. 触达策略 (Outreach Strategy)

> 基于 Priority 分级（Phase 6.5 完成后）制定的触达决策树

### 9.1 总体决策树

```
所有 GitHub 候选人
├── AI 相关? (bio/网站/仓库验证)
│   ├── 否 → Skip 删除
│   └── 是 → 按 Tier + 渠道分流
│       ├── S / A+ → [§9.2] VIP 精细化触达
│       ├── A / B+，有 LinkedIn → [§9.3] LinkedIn 优先
│       ├── 有网站+邮箱，无 LinkedIn → [§9.4] 邮件触达
│       ├── 仅 GitHub+邮箱 → [§9.5] 条件触达
│       └── 无邮箱 → 保留 P3，暂不触达
```

### 9.2 S/A+ 级 — VIP 精细化触达

**原则**: 人工核准 + 个性化内容 + 最佳渠道

| 步骤 | 说明 |
|:---|:---|
| 研究候选人 | 整合 GitHub 贡献、LinkedIn 经历、个人网站/博客、论文 |
| AI 生成草稿 | 引用具体贡献（如 "看到您在 vLLM 的 inference 优化 PR"） |
| 人工审核 | Lilian 逐条核准，调整措辞和匹配职位 |
| 渠道选择 | LinkedIn InMail / Email / 双渠道组合 |
| 跟踪 | 7 天未回复换渠道 Follow-up |

**邮件风格**: 行业洞察切入（非直接猎头），提及"Lilian聊AI"小红书建立信任。

### 9.3 A/B+，有 LinkedIn — LinkedIn 优先触达

1. 数据融合: LinkedIn Profile + GitHub 数据 + 网站内容
2. AI 生成 LinkedIn 连接请求消息（`generateLinkedInMessage` API）
3. 连接成功后发送职位信息
4. 未连接 7 天 → 转邮件触达

### 9.4 有网站+邮箱（无 LinkedIn）— 邮件触达

- 网站内容已通过 `label_github_candidates.py` 验证 AI 相关性
- 参考其网站/博客文章生成个性化开头
- 匹配相关职位推荐（`generateEmailDraft` API）

### 9.5 仅 GitHub+邮箱 — 条件触达

**准入条件**（满足之一）:
- `github_score ≥ 30` 且 bio 含 AI 关键词
- S/A/A+ 级
- `followers ≥ 100` 或 `total_stars ≥ 500`

---

## 10. 常用命令速查

```bash
# === 采集阶段 ===
cd /Users/lillianliao/notion_rag

# Phase 1: 采集 Following 网络
python3 github_mining/scripts/github_network_miner.py phase1 --target USERNAME

# Phase 2: AI 过滤
python3 github_mining/scripts/github_network_miner.py phase2

# Phase 3: 深度富化
GITHUB_TOKEN=xxx python3 github_mining/scripts/github_network_miner.py phase3

# Phase 3.5: 网站爬取（增量）
python3 github_mining/scripts/github_network_miner.py phase3_5 --top 100 --resume

# Phase 4: 网络扩展（标准模式）
python3 github_mining/scripts/github_network_miner.py phase4 --seed-top 300

# Phase 4: 网络扩展（自动重启模式，推荐）
python3 github_mining/scripts/auto_restart_wrapper.py -- \
  python3 github_mining/scripts/github_network_miner.py phase4 --seed-top 300

# === 系统操作 ===
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

# Phase 6: 导入系统
python3 import_github_candidates.py --file ../github_mining/scripts/github_mining/phase3_5_enriched.json --dry-run
python3 import_github_candidates.py --file ../github_mining/scripts/github_mining/phase3_5_enriched.json

# Phase 6.5: 打 Priority 标签
python3 scripts/label_github_candidates.py --dry-run
python3 scripts/label_github_candidates.py

# Phase 6.5: Bio 二次筛选
GITHUB_TOKENS='t1,t2,t3' python3 scripts/fetch_github_bios.py --dry-run
GITHUB_TOKENS='t1,t2,t3' python3 scripts/fetch_github_bios.py
# 从缓存重跑（不需要 API）
python3 scripts/fetch_github_bios.py --from-cache
```

---

## 11. 自动重启包装器（Auto Restart Wrapper）

### 11.1 为什么需要？

长时间任务（如 Phase 4 的 2-6 小时）面临的风险：

| 风险 | 场景 | 后果 |
|:---|:---|:---|
| **网络闪断** | 家里 WiFi 突然断开 3 分钟 | 脚本崩溃，需人工重启 |
| **API 异常** | GitHub 返回 502 Bad Gateway | 脚本退出，进度丢失 |
| **临时故障** | 系统资源不足、DNS 解析失败 | 任务中断，无法恢复 |

**结果**: 你晚上 11 点启动任务，半夜 2 点网络闪断，第二天早上 9 点醒来发现只跑到 2 点。

### 11.2 解决方案

**自动重启包装器** = 一个"自动按回车键的监工"

- 捕获所有异常和崩溃
- 等待指定时间（默认 30 秒）
- 自动重启任务（配合 `--resume` 参数实现断点续传）
- 真正的"睡眠自由"

### 11.3 使用方法

#### 基础用法

```bash
cd /Users/lillianliao/notion_rag

# 前台运行（可以看到实时输出）
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
```

#### 自定义参数

```bash
# 自定义最大重启次数和延迟
python3 github_mining/scripts/auto_restart_wrapper.py \
  --max-restarts 50 \
  --delay 60 \
  -- \
  python3 github_mining/scripts/github_network_miner.py phase4
```

#### 查看日志

```bash
# 实时查看自动重启日志
tail -f github_mining/auto_restart.log

# 日志示例
# [2026-02-23 22:00:00] 🚀 自动重启包装器启动
# [2026-02-23 22:00:00] 📝 执行命令: python3 github_network_miner.py phase4
# [2026-02-23 22:00:00] 🔄 启动任务（第 1 次尝试）
# ...
# [2026-02-24 02:13:45] ⚠️  任务异常退出（返回码: 1）
# [2026-02-24 02:13:45] 🔁 30 秒后自动重启（第 1/100 次）...
# [2026-02-24 02:14:15] 🔄 继续执行（将自动从断点恢复）
# ...
# [2026-02-24 08:30:22] ✅ 任务成功完成！
```

### 11.4 参数说明

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--max-restarts` | 100 | 最大重启次数 |
| `--delay` | 30 | 重启延迟（秒） |

### 11.5 工作原理

```
┌─────────────────────────────────────────────────────┐
│           Auto Restart Wrapper (外层)               │
│  - 监控内层命令的退出码                              │
│  - 捕获所有异常                                      │
│  - 失败后等待并自动重启                              │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │ github_network_     │
         │ miner.py phase4     │
         │ (内层任务)          │
         │ - 执行实际逻辑      │
         │ - 保存断点状态      │
         └─────────────────────┘
```

**配合断点续传**:
1. `github_network_miner.py` 保存进度到 JSON 文件
2. 崩溃后，自动重启包装器重新启动命令
3. `github_network_miner.py` 从 JSON 文件恢复进度
4. 继续处理，不会重复

### 11.6 适用场景

| 场景 | 是否需要 | 原因 |
|:---|:---:|:---|
| Phase 1（采集 Following） | ✅ | 1-2 小时，API 限流风险 |
| Phase 2 V3（轻富化） | ✅ | 2-4 小时，网络请求多 |
| Phase 3 V3（AI 判定） | ❌ | 本地计算，5-10 分钟 |
| **Phase 4（社交扩展）** | ✅✅✅ | **2-6 小时，最高风险** |
| Phase 3.5（网站爬取） | ✅ | 1-3 小时，网络爬虫 |

### 11.7 注意事项

1. **日志文件**: 所有重启记录保存在 `github_mining/auto_restart.log`
2. **手动中断**: Ctrl+C 可以正常退出，不会自动重启
3. **最大重启次数**: 默认 100 次，对于大多数任务足够
4. **重启延迟**: 默认 30 秒，给 GitHub API 恢复时间
5. **不保证成功率**: 如果是代码逻辑错误，自动重启也会失败

