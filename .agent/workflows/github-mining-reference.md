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
| **🟡 A** | P7/P8 | 顶尖Lab | 在 Seed/通义/2012/MSRA 等顶尖Lab | 惠彬元(通义), 姜轶昆(PyTorch member) |
| **🔵 B+** | P6/P7 | 一线+名校 | 一线大厂 + 985高校 + (32岁以下参考) | Li Jiahao(字节/清华), doubleZ(阿里/北大) |
| **⚪ B** | P5/P6 | 大厂或名校 | 一线大厂(学校不明) OR 985+二线大厂 | PureWhiteWu(字节CloudWeGo) |
| **🟢 C** | Other | 方向不符/其他 | 非 AI 方向 OR 以上不满足 | 任玉刚(Android), 黄晓刚(前端) |

### 2.2 自动分级逻辑 (`batch_update_tiers.py`)

按以下**优先级顺序**判定：

1. **S级**: `Followers > 5000` OR `Total Stars > 5000` OR `H-index > 30`
2. **A+级**: 顶会论文 ≥ 3 篇（ICLR/NeurIPS/ICML/ACL/CVPR/ICCV 等）
3. **A级**: Bio/公司/仓库 匹配顶尖 Lab 关键词（即使没有论文）
4. **C级(方向)**: Bio 含移动端/前端关键词 且无 AI 关键词
5. **B+级**: 一线大厂 + 985 高校
6. **B级**: 一线大厂(学校不明) OR 985+二线大厂 OR 二线大厂
7. **C级(默认)**: 以上都不满足

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
| `linkedin_position` / `company` | `current_title` / `current_company` | 优先 LinkedIn 数据，否则从 Bio 提取 |
| `blog` | `personal_website` | 个人网站链接 |
| `twitter_url` | `twitter_url` | Twitter 链接 |
| `linkedin_career` | `work_experiences` | 转换为 `[{company, title, time, description}]` |
| `top_venues` / `linkedin_achievements` | `awards_achievements` | 合并顶会论文统计和 LinkedIn 奖项 |
| `final_score` | `structured_tags.github_score` | 存入 JSON 标签 |
| `followers` | `structured_tags.github_followers` | 存入 JSON 标签 |
| `github_url` | `github` | GitHub 链接 |
| — | `source` | 固定值 `"github"` |

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
| **最终分布** | **S:27 / A:76 / B+:239 / B:130 / C:14 (共 486 人)** |

---

## 8. 输出文件目录结构

```
github_mining/
├── phase1_seed_users.json          # Phase 1 原始数据
├── phase1_seed_users.csv
├── phase1_following_list.json      # 断点续传用
├── phase2_ai_filtered.json         # Phase 2 AI 过滤结果
├── phase2_ai_filtered.csv
├── phase3_enriched.json            # Phase 3 深度信息 + 评分 (3,723人)
├── phase3_enriched.csv
├── phase3_5_enriched.json          # Phase 3.5 个人主页增强 (当前70人)
├── phase3_5_enriched.csv
├── phase4_expanded.json            # Phase 4 网络扩展 (待执行)
└── screenshots/                    # 浏览器截图
```
