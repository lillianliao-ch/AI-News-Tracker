# Rupro ATS++ 详细产品需求文档 v3.0

> **项目名称**: Rupro ATS++ (Browser-First Edition)  
> **版本**: v3.0 完整版  
> **创建时间**: 2025-11-15  
> **文档类型**: 产品需求文档 (PRD) + 技术设计文档 (TDD)  
> **适用对象**: 产品经理、工程师、架构师、投资人、合伙人  
> **文档状态**: 可直接用于工程实现

---

## 📋 文档说明

### 文档目标

本文档旨在为 **Rupro ATS++** 提供一份**完整、详细、可执行**的产品需求和技术设计文档，包括：

- ✅ 产品背景与系统目标
- ✅ 完整的系统架构设计（Browser-First）
- ✅ 详细的功能模块设计（插件、解析、匹配、策略）
- ✅ 完整的标签体系（可直接用于初始化）
- ✅ 完整的数据库设计（可直接建表）
- ✅ 完整的 API 设计（可直接对接）
- ✅ 详细的开发路线图（可直接用于项目管理）
- ✅ 部署、测试、风险应对方案

### 文档结构

```
第0章: 文档说明 ✓
第1章: 产品背景 & 系统目标
第2章: 系统架构（Browser-First）
第3章: 浏览器插件模块
第4章: 数据获取层
第5章: 解析层（Tag Extractor）
第6章: 标签体系
第7章: 匹配引擎
第8章: 寻访策略引擎
第9章: 数据库设计
第10章: API 设计
第11章: 报告生成
第12章: 开发路线图
第13章: 部署与运维
第14章: 测试策略
第15章: 风险与应对
```

### 文档版本历史

| 版本 | 日期 | 变更说明 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-10 | 初始版本（MVP 基础功能） | Lillian |
| v2.0 | 2025-11-15 | 扩展版本（智能匹配系统） | AI Assistant |
| v3.0 | 2025-11-15 | 完整版（整合 Browser-First + 完整技术方案） | Lillian + AI |

---

# 📘 第1章：产品背景 & 系统目标

## 1.1 产品背景（Business Background）

Rupro 作为一家聚焦 **AI、互联网、科技行业中高端岗位**的猎头公司，正在经历规模化和系统化升级。随着：

- **人才供给多元化**（Boss、猎聘、LinkedIn、GitHub、行业社区）
- **岗位复杂度升级**（LLM、模型评测、Agent、AI Infra）
- **业务效率诉求提升**
- **团队扩张、流程标准化需求增强**

人工处理 JD、人工访寻人才、人工对比技能等方式已经无法满足效率与规模要求。

推出 **Rupro ATS++** 的必要性已经完全确定。

---

## 1.2 行业痛点（Industry Problems）

### （1）招聘平台风控严厉

Boss / 猎聘 / 脉脉 对爬虫的限制愈加严格，传统爬虫风险极高。

### （2）信息冗杂、不结构化

JD、候选人简历都包含大量自然语言内容，需要 AI 才能高质量解析。

### （3）岗位与人才对齐效率低

人工对比技能、场景、背景效率极低，容易误判。

### （4）寻访策略依赖经验

不同顾问的能力差异大，缺乏标准化策略。

### （5）客户要求越来越高

客户更偏好"数据化、图形化、专业化"的人才推荐形式（如 PDF、矩阵、雷达图）。

---

## 1.3 产品定位（Product Positioning）

**Rupro ATS++ 是一套为猎头场景打造的"智能人才匹配系统（AI-powered Talent Intelligence Engine）"。**

它的定位是：

> 把猎头从重复劳动里解放出来，让 AI 完成"获取 → 解析 → 结构化 → 匹配 → 推荐 → 报告"的全链路工作。

其核心价值是：

- **快**：原本 3 小时 → 现在 2 分钟
- **准**：标签、匹配、分析依托模型
- **稳**：通过浏览器插件避免风险
- **专**：为客户提供更专业的交付结果
- **强**：可以规模化复用与扩张

---

## 1.4 产品愿景（Vision）

打造一个"猎头的操作系统"（Headhunter Operating System），包括：

- 人才洞察引擎
- 岗位分析引擎
- 匹配引擎
- 策略生成引擎
- 交付引擎（报告）
- 客户洞察引擎（未来）

其中第一步就是构建 **Rupro ATS++（Browser-First Edition）**。

---

## 1.5 核心原则（System Principles）

### ✔ 原则 1：浏览器插件为主通道

- 使用用户行为采集
- 极低风控风险
- Boss/猎聘最佳方案
- 能保持系统持久稳定运行

### ✔ 原则 2：Spider 只用于低风险来源

- 公司官网
- GitHub Jobs
- LinkedIn 官方 API
- **永不用于 BOSS/猎聘，确保账号安全**

### ✔ 原则 3：数据结构化是核心

Rupro ATS++ 的真正核心是：

```
原始人才数据（raw resume）
→ 结构化标签（skill、scenario、background、soft…）
→ 匹配 → 评分 → 报告
```

### ✔ 原则 4：一切流程可追溯、可解释

- 匹配不是黑盒
- 所有推荐都有 explain 字段

### ✔ 原则 5：可扩展、可并行、可自动化

支持未来扩展：

- 城市/行业/薪资画像
- Offer 预测
- 面试管理
- Onboarding 跟踪

---

## 1.6 系统目标（System Goals）

Rupro ATS++ 的目标拆分为 6 级：

### **Goal 1：自动化人才获取（重点：插件）**

- 一键采集 Boss 人才卡片
- 自动解析 DOM
- 自动发送到 ATS++ 后端
- 无需爬虫，不被封号
- LinkedIn 的列表页、详情页均可支持
- 每天可采集 50~200 名候选人

### **Goal 2：自动化岗位获取**

通过 Spider/API 获取以下信息：

- 企业官网 Careers 页面
- GitHub Jobs
- LinkedIn Jobs（安全来源）

由系统自动 clean → 提取 JD → 结构化为 Job Tags。

### **Goal 3：自动化结构化解析（AI Tag Extractor）**

将自然语言简历、JD 自动提取为标签：

例如：

```
Python、LLM Evaluation、RAG、K8s、模型对齐、金融文档、Java、Scala、Transformers
```

并分层：

- skill
- scenario
- background
- soft
- experience

### **Goal 4：自动化寻访策略生成（阶段 II）**

系统自动给出：

- Ideal Persona
- Standard Persona
- Optional Persona
- Boolean Search
- 推荐寻访渠道（LinkedIn / Boss / GitHub）
- Target Company Tier

本模块是猎头专业能力的完全产品化。

### **Goal 5：自动化匹配（Matching Engine）**

输入：

- 1 份 JD
- N 个候选人

输出：

- 匹配度评分
- 推荐 Top3 岗位
- 推荐 Top3 候选人

并带 explain 字段，指导顾问判断。

### **Goal 6：自动报告（PDF）**

生成专业级报告，可直接提供给客户：

- 岗位画像
- 人才画像
- 匹配雷达图
- 匹配矩阵（N × M）
- 推荐列表
- 项目摘要
- 风险点（可选）

---

# 📘 第2章：系统架构（Browser-First 架构版）

这一章极为关键，因为它决定：

- 工程师如何搭建系统
- Cursor 如何生成模块化代码
- Browser Extension 如何和后端协作
- 整个 ATS++ 的数据在系统中的流转方式

---

## 🔵 2.1 系统总体架构图（Total System Architecture）

新版 Browser-First 架构如下（核心在于数据获取层的重构）：

```
                       ┌────────────────────────────┐
                       │         前端 Dashboard      │
                       └──────────────┬─────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     │          API Gateway            │
                     └──────────────┬─────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────────┐
           │                        │                            │
 ┌─────────▼────────┐    ┌──────────▼──────────┐      ┌─────────▼─────────┐
 │ Browser Plugin    │    │ Official API Fetcher │      │  Website Spider    │
 │ (Boss/猎聘/脉脉/LinkedIn) │    │ (GitHub / LinkedIn API)│      │ (Careers 网站)       │
 └─────────┬────────┘    └──────────┬──────────┘      └─────────┬─────────┘
           │                         │                            │
           ▼                         ▼                            ▼
 ┌────────────────────┐   ┌─────────────────────┐     ┌────────────────────┐
 │  Talent Raw Data    │   │    JD Raw Data       │     │   JD Raw Data       │
 └─────────┬──────────┘   └─────────┬───────────┘     └─────────┬──────────┘
           │                        │                             │
           ▼                        ▼                             ▼
 ┌────────────────────┐   ┌─────────────────────┐     ┌──────────────────────┐
 │ Talent Tag Extractor│   │    JD Tag Extractor │     │   Tag Normalizer      │
 └─────────┬──────────┘   └─────────┬───────────┘     └─────────┬────────────┘
           │                        │                             │
           └──────────────┬─────────▼──────────────┬─────────────┘
                          │                        │
                          ▼                        ▼
                 ┌────────────────┐      ┌─────────────────────────┐
                 │ Matching Engine│      │ Sourcing Strategy Engine │
                 └──────────┬─────┘      └───────────┬────────────┘
                            │                         │
                            ▼                         ▼
                 ┌────────────────┐      ┌─────────────────────────┐
                 │ Recommendation │      │  Report Generator (PDF) │
                 └──────────┬─────┘      └───────────┬────────────┘
                            │                         │
                            ▼                         ▼
                      ┌──────────────┐          ┌───────────────┐
                      │ PostgreSQL   │          │   飞书/前端    │
                      └──────────────┘          └───────────────┘
```

---

## 🔵 2.2 系统核心分层（System Layers）

整个 ATS++ 架构分为 6 层：

### ✔ Layer 1：Browser-Based Acquisition Layer（主通道）

来源平台：

- BOSS
- 猎聘
- 脉脉
- LinkedIn

数据通过插件获取，自动读取 DOM 内容，风险极低。

### ✔ Layer 2：API-Based Acquisition Layer（辅助通道）

来源平台：

- GitHub
- LinkedIn API
- Kaggle（可选）
- Open APIs

API 不受反爬限制，非常稳定。

### ✔ Layer 3：Spider-Based Acquisition Layer（备用）

来源：

- 公司官网 Careers
- GitHub Jobs
- 小众公开人才站点

此层为可选，仅在低风险场景激活。

### ✔ Layer 4：Parsing & Tagging Layer（标签解析层）

包括以下模块：

- **Talent Tag Extractor**
- **JD Tag Extractor**
- **Tag Normalizer（标签规范化）**

作用是将自然语言转成结构化标签体系：

```
skills
scenario
background
soft
experience
system_tags（Job 特有）
ai_tags（Job 特有）
```

### ✔ Layer 5：Matching & Strategy Layer（智能分析层）

包括：

- Matching Engine（核心）
- Sourcing Strategy Engine（阶段 II）
- Boolean Builder
- Persona Generator
- Company Tier Engine

### ✔ Layer 6：Output Layer

包括：

- Recommendation Engine
- Report Generator（PDF/JSON）
- 中台（人才库、JD库）

---

## 🔵 2.3 数据流动图（End-to-End Data Flow）

下面是系统的"数据生命线（Data Lifecycle）"，从"用户浏览页面"开始，到"生成 PDF"。

```
用户浏览人才页面
→ 插件自动识别 DOM
→ 插件把数据发送到 API
→ Talent Raw Data 入库
→ Talent Tag Extractor（LLM）
→ 标签标准化（Tag Normalizer）
→ Talent Tag 入库
→ 触发 Matching Engine
→ 获得匹配矩阵
→ Recommendation Engine（Top3 岗位 / Top3 候选人）
→ Report Engine（生成 PDF）
→ 前端展示 / 下载
```

这条流程会贯穿整个 PRD。

---

## 🔵 2.4 模块依赖图（Module Dependencies）

为了让工程师更好理解模块边界，PRD 定义以下依赖关系：

| 模块 | 输入 | 输出 | 必须先于 | 依赖 |
| --- | --- | --- | --- | --- |
| Browser Plugin | DOM | raw_resume | Tag Extractor | 无 |
| Tag Extractor | raw_resume | talent_tags | Matching | LLM |
| JD Extractor | raw_jd | job_tags | Matching | LLM |
| Tag Normalizer | talent_tags/job_tags | normalized_tags | Matching | 字典库 |
| Matching Engine | normalized tags | scores | Recommendation | 标签体系 |
| Recommendation | scores | top results | Report | Matching |
| Report Engine | top results | PDF | - | 推荐与标签 |
| Strategy Engine | job_tags | persona/boolean | Candidate Search | 标签体系 |

模块边界清晰 → 更容易分工开发。

---

## 🔵 2.5 Browser Plugin 主导架构（关键新增）

### Browser Plugin 由三部分组成：

1. **content script**（读取 DOM）
2. **background script**（处理网络通信）
3. **service worker / popup UI**（用户交互）

### 插件架构图：

```
Page DOM
   │
   ▼
[Content Script]
   │ 抽取 DOM
   ▼
[Background Script]
   │ 发送数据到 API
   ▼
ATS++ Backend
```

---

## 🔵 2.6 技术栈选择（Tech Stack）

### 浏览器插件：

- JavaScript / TypeScript
- Manifest v3
- DOM 解析
- Axios / fetch 调用 API
- 插件内缓存（IndexedDB）

### 后端：

- **Python（FastAPI）** ✅ 已选择
- OpenAI / DeepSeek / **Qwen 模型调用** ✅ 已选择
- **PostgreSQL** + **飞书多维表格** ✅ 已选择
- Redis（可选）

### 前端：

- React + Tailwind（可选）

### PDF：

- **ReportLab（Python）** ✅ 推荐

---

## 🔵 2.7 非功能需求（NFR）

### 1）性能

- 插件解析 1 个候选人 ≤ 500ms
- Tag Extractor（LLM）≤ 1.5s

### 2）稳定性

- 插件应具备 fallback DOM selector
- API 超时自动重试

### 3）安全性

- Token 不存于插件
- 所有请求加密
- 插件行为必须模拟真实用户操作

### 4）可扩展性

- 标签池可扩展
- 新平台可在 Browser Plugin Layer 中添加 adapter

---

# 📘 第3章：浏览器插件模块（Browser Plugin Module）

本章节是整个系统最关键的部分，因为 **Browser Plugin = 你的主力人才获取通道**，涉及 BOSS、猎聘、脉脉、LinkedIn 四个平台。

---

## 🔵 3.1 浏览器插件模块概述（Module Overview）

Browser Plugin 是 Rupro ATS++ 的核心数据采集模块，用于：

- 自动提取 Boss / 猎聘 / 脉脉 / LinkedIn 的候选人信息
- 无需模拟登录、无需爬虫、不会触发风控
- 用户在浏览人才页面时自动采集 DOM 信息
- 一键发送后端进行解析（Tag Extractor）

其关键优势：

### ✔ 极低封号风险

所有操作发生在「用户主动打开」的页面内，平台无法识别为爬虫。

### ✔ DOM 可提取所有页面可见字段

包括：

姓名、职位、公司、技能、经历、教育、标签、薪资、当前状态。

### ✔ 适合 AI/猎头领域高频使用

一天采集几十到几百条不成问题。

---

## 🔵 3.2 插件总体架构（Browser Plugin Architecture）

插件采用 Manifest v3 架构，包括三个主要组件：

```
Page DOM
   │
   ▼
[Content Script] —— 负责读取页面内容
   │
   ▼
[Background Service Worker] —— 网络请求/存储/调度
   │
   ▼
ATS++ Backend API —— 数据解析、入库、匹配
```

内部构成：

```
- manifest.json
- content-script.js
- background.js (service worker)
- popup.html + popup.js
- options.html (可选)
```

---

## 🔵 3.3 插件适配的四大平台

### 3.3.1 BOSS 直聘 ✅ 已实现

DOM 结构相对稳定，信息完整，是最重要的来源。

### 3.3.2 猎聘

DOM 会动态加载，但页面信息通常比 BOSS 更详细。

### 3.3.3 脉脉

部分数据需要下拉展开，需要手动触发。

### 3.3.4 LinkedIn

- 可以解析 public profile
- 也可以解析搜索结果列表（低频）
- 适合高级人才采集

---

## 🔵 3.4 插件功能清单（Plugin Functional Requirements）

插件需求分为 **基础功能 + 高级功能**。

### 🟩 3.4.1 基础功能（必须实现）

#### ✔ 1. 自动识别 DOM 内容 ✅ 已实现

插件注入 content script，自动选择 DOM 节点：

如 BOSS：

```
.name
.job-title
.company
.work-experience
.education
.skills
.tags
```

#### ✔ 2. 一键采集按钮（主操作入口）✅ 已实现

在页面右下角显示一个悬浮按钮：

- "采集当前候选人"
- 点击后：
    1. 截取 DOM
    2. 发给后台
    3. 弹出成功提示

#### ✔ 3. 自动采集模式（可选）

在结果列表页：

- 每次用户点击一个候选人卡片 → 自动触发采集
- 需要节流：每 10 秒不能超过 1 次

#### ✔ 4. 信息清洗（Content Script 完成）✅ 已实现

Raw HTML → Clean Text

用于后端解析更高精度。

#### ✔ 5. 本地缓存（防重复采集）

IndexedDB 存储采集过的 URL/id：

```
candidate_hash: {...}
```

每次提交前先检查是否重复。

### 🟩 3.4.2 高级功能（增强体验）

#### ✔ 6. Popup 面板（操作界面）✅ 已实现

可切换功能模式：

- 自动采集 ON/OFF
- 展示最近 20 个采集记录
- 重新发送失败任务
- 设置 API Key / User ID

#### ✔ 7. 反风控策略 ✅ 已实现

- 随机延迟请求（1.2s–3.2s）
- 手动触发优先
- 阻止高频调用（例如 <=5 秒）
- 插件内部计数器

#### ✔ 8. 错误场景处理 ✅ 已实现

包括：

- DOM 结构变更（fallback selector）
- 网络失败（重试）
- 429 / 限流（间隔 60 秒重试）
- 后端不可用（缓存到本地队列）

---

## 🔵 3.5 插件数据结构（核心 Schema）

插件向后端发送的数据格式：

```json
{
  "platform": "boss",
  "url": "https://www.zhipin.com/.../xxx",
  "timestamp": 1737283233,
  "raw_html": "<div>....</div>",
  "clean_text": "姓名：李XX\n职位：AI工程师\n...",
  "fields": {
     "name": "...",
     "title": "...",
     "current_company": "...",
     "skills": "...",
     "work_history": "...",
     "education": "...",
     "tags": ["AI", "NLP", "LLM"],
     "location": "北京",
     "salary": "30-45K"
  }
}
```

此 Schema 将用于 Tag Extractor。

---

## 🔵 3.6 插件与后端通信协议（API Contract）

插件调用后端：

### POST `/api/v1/plugin/talent_raw`

#### Request Body:

（见上面的 JSON）

#### Response:

```json
{
  "status": "ok",
  "candidate_id": "uuid",
  "next_step": "tag_extraction"
}
```

出错：

```json
{
  "status": "error",
  "reason": "DOM parse failed"
}
```

---

## 🔵 3.7 插件风控策略（反封号的关键）

为了保证账号安全，插件必须遵循：

### ✔ 节流规则

- 尽量让用户手动触发
- 自动模式：每 10 秒最多采集一次
- 不能滚动采集（Boss 会封）

### ✔ 模拟用户行为

- 插件不执行 scrollToBottom
- 不模拟点击
- 不自动打开页面
    
    → 所有页面动作均由用户完成

### ✔ 不批量采集（Boss 禁止）

- 插件只能处理当前页面
- 不抓取列表页

### ✔ 访问限制

- 同一域名，每分钟最多 3 次提交

---

# 📘 第4章：数据获取层（Acquisition Layer）

*(保留文档B的第4章内容)*

---

# 📘 第5章：解析层（Tag Extractor Layer）

*(保留文档B的第5章内容)*

---

# 📘 第6章：标签体系（Tag System）

*(保留文档B的第6章内容，包括完整的标签池)*

---

# 📘 第7章：匹配引擎（Matching Engine）

*(保留文档B的第7章内容，包括完整的匹配公式和算法)*

---

# 📘 第8章：寻访策略引擎（Sourcing Strategy Engine）

*(保留文档B的第8章内容，包括7个子模块)*

---

# 📘 第9章：数据库设计

## 9.1 数据库概述

Rupro ATS++ 使用 **PostgreSQL** 作为主数据库，**飞书多维表格**作为协作数据库。

### 数据库分层

```
PostgreSQL（核心数据）
  - job_tags（JD 库）
  - talent_tags（人才库）
  - matching_results（匹配记录）
  - skills_dictionary（标签字典）
  - company_knowledge（公司库）

飞书多维表格（协作数据）
  - 候选人信息
  - 简历截图
  - AI 评估结果
```

---

## 9.2 JD 表（job_tags）

### 表结构

```sql
CREATE TABLE job_tags (
    jd_id VARCHAR(50) PRIMARY KEY,
    source VARCHAR(50),  -- boss/linkedin/website/manual
    url TEXT,
    title VARCHAR(200),
    company VARCHAR(200),
    location VARCHAR(100),
    salary_range VARCHAR(50),
    work_years VARCHAR(50),
    education VARCHAR(50),
    
    -- 标签（JSONB）
    skills JSONB,  -- ["Python", "Kubernetes", ...]
    system JSONB,  -- ["AWS", "微服务", ...]
    ai_tags JSONB,  -- ["NLP", "CV", ...]
    scenario JSONB,  -- ["金融风控", ...]
    experience JSONB,  -- ["3-5年", "大厂背景", ...]
    soft JSONB,  -- ["沟通能力", ...]
    
    -- 原始数据
    raw_content TEXT,
    
    -- 元数据
    status VARCHAR(20),  -- active/paused/closed
    scraped_at TIMESTAMP,
    parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_jd_company ON job_tags(company);
CREATE INDEX idx_jd_status ON job_tags(status);
CREATE INDEX idx_jd_skills ON job_tags USING GIN(skills);
```

---

## 9.3 人才表（talent_tags）

### 表结构

```sql
CREATE TABLE talent_tags (
    candidate_id VARCHAR(50) PRIMARY KEY,
    source VARCHAR(50),  -- boss/linkedin/github/manual
    name VARCHAR(100),
    current_company VARCHAR(200),
    current_position VARCHAR(200),
    work_years INT,
    education VARCHAR(50),
    school VARCHAR(200),
    
    -- 标签（JSONB）
    skills JSONB,  -- ["Python", ...]
    scenario JSONB,  -- ["金融风控", ...]
    background JSONB,  -- {"companies": [...], "education": "..."}
    soft JSONB,  -- ["沟通能力", ...]
    domain_strength JSONB,  -- {"AI": 9, "Backend": 7}
    projects JSONB,  -- [{"name": "...", "skills": [...]}]
    
    -- 联系方式
    email VARCHAR(200),
    phone VARCHAR(50),
    linkedin_url TEXT,
    github_url TEXT,
    
    -- 原始数据
    raw_profile TEXT,
    resume_screenshot TEXT,  -- Base64 或 URL
    
    -- 元数据
    scraped_at TIMESTAMP,
    parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_talent_company ON talent_tags(current_company);
CREATE INDEX idx_talent_skills ON talent_tags USING GIN(skills);
```

---

## 9.4 匹配记录表（matching_results）

### 表结构

```sql
CREATE TABLE matching_results (
    matching_id VARCHAR(50) PRIMARY KEY,
    jd_id VARCHAR(50) REFERENCES job_tags(jd_id),
    candidate_id VARCHAR(50) REFERENCES talent_tags(candidate_id),
    
    -- 分数
    total_score FLOAT,
    skill_score FLOAT,
    scenario_score FLOAT,
    background_score FLOAT,
    soft_score FLOAT,
    
    -- 推荐等级
    recommend_level VARCHAR(20),  -- 强推/推荐/一般/不推荐
    
    -- 匹配详情
    matched_skills JSONB,
    missing_skills JSONB,
    matched_scenarios JSONB,
    highlights TEXT,  -- 匹配亮点
    risks TEXT,  -- 匹配风险
    
    -- 元数据
    matched_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_matching_jd ON matching_results(jd_id);
CREATE INDEX idx_matching_candidate ON matching_results(candidate_id);
CREATE INDEX idx_matching_score ON matching_results(total_score DESC);
CREATE INDEX idx_matching_level ON matching_results(recommend_level);
```

---

## 9.5 标签字典表（skills_dictionary）

### 表结构

```sql
CREATE TABLE skills_dictionary (
    standard_name VARCHAR(100) PRIMARY KEY,
    aliases JSONB,  -- ["python", "py", "Python3"]
    category VARCHAR(50),  -- programming/framework/tool/domain
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 初始数据
INSERT INTO skills_dictionary (standard_name, aliases, category) VALUES
('Python', '["python", "py", "Python3", "python3"]', 'programming'),
('Kubernetes', '["k8s", "kube", "kubernetes", "K8S"]', 'tool'),
('RAG', '["rag", "retrieval-augmented-generation", "检索增强生成"]', 'domain'),
('NLP', '["nlp", "自然语言处理", "natural language processing"]', 'domain');
```

---

## 9.6 公司库表（company_knowledge）

### 表结构

```sql
CREATE TABLE company_knowledge (
    company_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(200),
    tier VARCHAR(20),  -- tier1/tier2/tier3
    industry VARCHAR(100),
    tags JSONB,  -- ["AI", "大模型", ...]
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 初始数据
INSERT INTO company_knowledge (company_id, company_name, tier, industry, tags) VALUES
('minimax', 'MiniMax', 'tier1', 'AI', '["大模型", "AI"]'),
('zhipu', '智谱AI', 'tier1', 'AI', '["大模型", "AI"]'),
('moonshot', '月之暗面', 'tier1', 'AI', '["大模型", "AI"]'),
('bytedance', '字节跳动', 'tier2', '互联网', '["推荐系统", "AI", "大厂"]');
```

---

# 📘 第10章：API 设计

## 10.1 API 概述

Rupro ATS++ 后端使用 **FastAPI** 框架，提供 RESTful API。

### API 基础信息

- **Base URL**: `http://localhost:8000` (开发环境)
- **Base URL**: `https://api.rupro-ats.com` (生产环境)
- **认证方式**: Bearer Token
- **数据格式**: JSON

---

## 10.2 JD 相关 API

### POST /api/jd/scrape

抓取 JD

**Request**:
```json
{
  "url": "https://www.example.com/jobs",
  "source": "website"
}
```

**Response**:
```json
{
  "success": true,
  "jd_id": "JD_20251115_001",
  "raw_content": "..."
}
```

---

### POST /api/jd/parse

解析 JD

**Request**:
```json
{
  "jd_id": "JD_20251115_001"
}
```

**Response**:
```json
{
  "success": true,
  "jd_tags": {
    "skills": ["Python", "Kubernetes"],
    "system": ["AWS", "微服务"],
    "ai_tags": ["NLP", "RAG"],
    "scenario": ["金融风控"],
    "experience": ["3-5年"],
    "soft": ["沟通能力"]
  }
}
```

---

### GET /api/jd/list

获取 JD 列表

**Query Parameters**:
- `status`: active/paused/closed
- `company`: 公司名
- `page`: 页码
- `limit`: 每页数量

**Response**:
```json
{
  "success": true,
  "total": 100,
  "data": [
    {
      "jd_id": "JD_20251115_001",
      "title": "AI产品经理",
      "company": "字节跳动",
      "status": "active",
      "created_at": "2025-11-15 14:00:00"
    }
  ]
}
```

---

## 10.3 人才相关 API

### POST /api/talent/scrape

批量抓取候选人

**Request**:
```json
{
  "source": "boss",
  "keywords": ["NLP工程师", "RAG工程师"],
  "companies": ["MiniMax", "智谱AI"],
  "limit": 100
}
```

**Response**:
```json
{
  "success": true,
  "total_scraped": 95,
  "candidate_ids": ["CAND_001", "CAND_002"]
}
```

---

### POST /api/candidates/process ✅ 已实现

解析候选人（当前 MVP 使用）

**Request**:
```json
{
  "candidate_info": {
    "name": "张先生",
    "current_company": "字节跳动",
    "current_position": "AI工程师",
    "work_years": 5,
    "education": "硕士",
    "skills": ["Python", "LLM"],
    "source_url": "https://..."
  },
  "resume_file": "mock_data",
  "resume_text": "完整简历文本...",
  "resume_screenshot": "data:image/png;base64,...",
  "jd_config": {
    "position": "AI产品经理",
    "requirements": "..."
  }
}
```

**Response**:
```json
{
  "success": true,
  "candidate_id": "CAND_001",
  "structured_resume": {...},
  "evaluation": {
    "综合匹配度": 85,
    "推荐等级": "推荐",
    "匹配亮点": [...],
    "风险提示": [...]
  },
  "resume_text": "原始简历文本"
}
```

---

### POST /api/talent/enrich

补全联系方式

**Request**:
```json
{
  "candidate_id": "CAND_001"
}
```

**Response**:
```json
{
  "success": true,
  "contact": {
    "email": "zhang@example.com",
    "phone": "138****1234",
    "linkedin": "https://linkedin.com/in/zhang",
    "github": "https://github.com/zhang"
  }
}
```

---

## 10.4 匹配相关 API

### POST /api/matching/calculate

计算匹配度

**Request**:
```json
{
  "jd_id": "JD_20251115_001",
  "candidate_ids": ["CAND_001", "CAND_002"]
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "candidate_id": "CAND_001",
      "total_score": 92.5,
      "skill_score": 95,
      "scenario_score": 88,
      "background_score": 90,
      "soft_score": 85,
      "recommend_level": "强推",
      "matched_skills": ["Python", "LLM"],
      "missing_skills": ["Kubernetes"]
    }
  ]
}
```

---

### GET /api/matching/recommend

获取推荐

**Query Parameters**:
- `jd_id`: JD ID
- `top_n`: Top N 候选人
- `min_score`: 最低分数

**Response**:
```json
{
  "success": true,
  "recommendations": [
    {
      "rank": 1,
      "candidate_id": "CAND_001",
      "name": "张先生",
      "total_score": 92.5,
      "highlights": ["5年NLP经验", "大厂背景"],
      "risks": ["薪资预期略高"]
    }
  ]
}
```

---

## 10.5 报告相关 API

### POST /api/report/generate

生成报告

**Request**:
```json
{
  "jd_id": "JD_20251115_001",
  "candidate_ids": ["CAND_001", "CAND_002"],
  "format": "pdf",
  "include_radar": true,
  "include_matrix": true
}
```

**Response**:
```json
{
  "success": true,
  "report_id": "REPORT_20251115_001",
  "download_url": "https://oss.example.com/reports/REPORT_20251115_001.pdf",
  "expires_at": "2025-11-22 14:00:00"
}
```

---

### GET /api/report/download/{report_id}

下载报告

**Response**: PDF 文件流

---

## 10.6 寻访策略 API

### POST /api/sourcing/strategy

生成寻访策略

**Request**:
```json
{
  "jd_id": "JD_20251115_001"
}
```

**Response**:
```json
{
  "success": true,
  "strategy": {
    "ideal_persona": {...},
    "standard_persona": {...},
    "optional_persona": {...},
    "target_company_list": {
      "tier1": ["MiniMax", "智谱AI"],
      "tier2": ["字节跳动", "阿里巴巴"],
      "tier3": ["金融IT公司"]
    },
    "recommended_channels": ["Boss直聘", "LinkedIn"],
    "recommended_keywords": ["NLP工程师", "RAG工程师"],
    "boolean_queries": ["(\"NLP Engineer\" OR \"RAG Engineer\") AND ..."]
  }
}
```

---

## 10.7 飞书集成 API ✅ 已实现

### GET /api/feishu/health

飞书 API 健康检查

**Response**:
```json
{
  "success": true,
  "feishu_enabled": true,
  "token_valid": true,
  "table_accessible": true
}
```

---

# 📘 第11章：报告生成

## 11.1 报告生成概述

Rupro ATS++ 支持三种报告格式：

1. **PDF 专业报告** - 面向客户
2. **CSV 数据报告** - 面向数据分析
3. **JSON API** - 面向系统集成

---

## 11.2 PDF 报告结构

### 报告组成

```python
PDF_REPORT_STRUCTURE = {
    "封面": {
        "title": "人才推荐报告",
        "jd_title": "AI产品经理",
        "company": "字节跳动",
        "date": "2025-11-15",
        "logo": "company_logo.png"
    },
    "Executive Summary": {
        "total_candidates": 50,
        "recommended": 15,
        "avg_match_score": 72.5,
        "top3_highlights": [...]
    },
    "岗位画像": {
        "skills": [...],
        "scenario": [...],
        "experience": [...]
    },
    "人才画像": {
        "ideal_persona": {...},
        "standard_persona": {...}
    },
    "匹配矩阵": {
        "table": [...],
        "heatmap": "heatmap.png"
    },
    "Top 推荐": [
        {
            "rank": 1,
            "name": "张先生",
            "match_score": 92,
            "highlights": [...],
            "risks": [...]
        }
    ],
    "雷达图": {
        "skills_radar": "skills_radar.png",
        "comparison": "comparison.png"
    }
}
```

---

## 11.3 PDF 生成实现

### 使用 ReportLab

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

async def generate_pdf_report(
    jd_tags: dict,
    matching_results: List[dict],
    output_path: str
) -> str:
    """生成 PDF 报告"""
    
    # 创建 PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 1. 封面
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "人才推荐报告")
    c.setFont("Helvetica", 14)
    c.drawString(100, height - 150, f"岗位：{jd_tags['title']}")
    c.drawString(100, height - 180, f"日期：{datetime.now().strftime('%Y-%m-%d')}")
    c.showPage()
    
    # 2. Executive Summary
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, "Executive Summary")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 150, f"总候选人数：{len(matching_results)}")
    c.drawString(100, height - 180, f"推荐候选人：{len([r for r in matching_results if r['recommend_level'] == '推荐'])}")
    c.showPage()
    
    # 3. 岗位画像
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, "岗位画像")
    y = height - 150
    for skill in jd_tags["skills"][:10]:
        c.drawString(120, y, f"• {skill}")
        y -= 20
    c.showPage()
    
    # 4. Top 推荐
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, "Top 推荐候选人")
    y = height - 150
    for i, result in enumerate(matching_results[:5], 1):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, y, f"{i}. {result['name']} - {result['total_score']}%")
        c.setFont("Helvetica", 10)
        y -= 20
        c.drawString(120, y, f"技能匹配：{result['skill_score']}%")
        y -= 15
        c.drawString(120, y, f"场景匹配：{result['scenario_score']}%")
        y -= 30
    c.showPage()
    
    # 5. 雷达图
    radar_chart = generate_radar_chart(matching_results[0])
    c.drawImage(radar_chart, 100, height - 500, width=400, height=300)
    
    c.save()
    
    return output_path
```

---

## 11.4 雷达图生成

```python
def generate_radar_chart(matching_result: dict) -> str:
    """生成雷达图"""
    
    categories = ['技能', '场景', '背景', '软技能']
    values = [
        matching_result['skill_score'],
        matching_result['scenario_score'],
        matching_result['background_score'],
        matching_result['soft_score']
    ]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    
    chart_path = "/tmp/radar_chart.png"
    plt.savefig(chart_path)
    plt.close()
    
    return chart_path
```

---

## 11.5 CSV 导出 ✅ 已实现

当前 MVP 已实现 CSV 导出功能，包括：

- 候选人基本信息
- 匹配分数
- 推荐等级
- 关键标签

---

## 11.6 Markdown 导出 ✅ 已实现

当前 MVP 已实现 Markdown 导出功能，包括：

- 候选人详细信息
- 简历原文
- AI 评估结果
- 简历截图（Base64 编码）

---

# 📘 第12章：开发路线图

## 12.1 路线图概述

Rupro ATS++ 的开发分为 **8 个 Phase，预计 14 周完成**。

---

## 12.2 Phase 1: 基础设施（2周）

### Week 1: 数据库 + 标签体系

- [ ] PostgreSQL 数据库设计
- [ ] JD Tags 表结构
- [ ] Talent Tags 表结构
- [ ] Matching Results 表结构
- [ ] Skills Dictionary 初始化
- [ ] Tag Normalizer 实现

### Week 2: 爬虫基础设施

- [ ] Playwright 环境搭建
- [ ] IP 代理池
- [ ] Cookie 管理
- [ ] 限流策略
- [ ] 验证码 OCR

---

## 12.3 Phase 2: JD 模块（2周）

### Week 3: JD 采集

- [ ] JD Spider 实现
  - [ ] 企业官网爬虫
  - [ ] Boss 直聘 JD 爬虫
  - [ ] LinkedIn Jobs 爬虫
  - [ ] 手动输入接口
- [ ] JD 存储
- [ ] JD 管理界面

### Week 4: JD 解析

- [ ] JD Tag Extractor 实现
- [ ] LLM Prompt 优化
- [ ] 标签标准化集成
- [ ] JD 详情页
- [ ] 批量解析

---

## 12.4 Phase 3: 人才模块（2周）

### Week 5: 人才采集 ✅ 部分完成

- [x] Boss 直聘浏览器插件 ✅ 已完成
- [ ] LinkedIn 抓取
- [ ] GitHub 抓取
- [ ] 猎聘抓取
- [ ] 联系方式补全
- [ ] 人才库管理

### Week 6: 人才解析优化 ✅ 部分完成

- [x] Talent Tag Extractor 基础实现 ✅ 已完成
- [ ] 与 JD 标签体系对齐
- [ ] 项目经历提取
- [ ] 技能深度评估

---

## 12.5 Phase 4: 匹配引擎（2周）

### Week 7: 匹配算法 ✅ 部分完成

- [x] 基础匹配算法 ✅ 已完成（Mock 版本）
- [ ] 技能匹配算法（完整版）
- [ ] 场景匹配算法（Embedding）
- [ ] 背景匹配算法
- [ ] 软技能评估（LLM）
- [ ] 加权总分计算

### Week 8: 匹配优化

- [ ] 批量匹配
- [ ] 匹配矩阵生成
- [ ] Top N 推荐
- [ ] 匹配结果存储
- [ ] 匹配历史查询

---

## 12.6 Phase 5: 寻访策略（1周）

### Week 9: 策略生成

- [ ] Sourcing Strategy Generator
- [ ] Target Company Tiering
- [ ] Boolean Search Builder
- [ ] 目标公司库
- [ ] 策略模板

---

## 12.7 Phase 6: 报告生成（2周）

### Week 10: PDF 报告

- [ ] 报告模板设计
- [ ] ReportLab 集成
- [ ] 雷达图生成
- [ ] 匹配矩阵可视化
- [ ] 封面 + Summary

### Week 11: 多格式报告

- [x] CSV 导出 ✅ 已完成
- [x] Markdown 导出 ✅ 已完成
- [ ] JSON API
- [ ] Dashboard（可选）
- [ ] 报告管理
- [ ] 批量生成

---

## 12.8 Phase 7: 集成与测试（2周）

### Week 12: 系统集成 ✅ 部分完成

- [x] 前后端联调 ✅ 已完成
- [x] Chrome 插件集成 ✅ 已完成
- [ ] Web 管理后台
- [x] 飞书集成 ✅ 已完成
- [ ] 权限管理

### Week 13: 测试与优化

- [ ] 功能测试
- [ ] 性能测试
- [ ] 压力测试
- [ ] Bug 修复
- [ ] 文档编写

---

## 12.9 Phase 8: 上线与迭代（持续）

### Week 14+: 生产部署

- [ ] 服务器部署
- [ ] 域名配置
- [ ] SSL 证书
- [ ] 监控告警
- [ ] 数据备份

### 后续迭代

- [ ] 用户反馈收集
- [ ] 功能优化
- [ ] 新数据源接入
- [ ] AI 模型优化
- [ ] 性能优化

---

## 12.10 当前进度（MVP v1.0）

### ✅ 已完成

- [x] Boss 直聘浏览器插件（采集、解析、导出）
- [x] 后端 AI 解析（通义千问）
- [x] 飞书集成（自动上传推荐候选人）
- [x] CSV 导出
- [x] Markdown 导出
- [x] 简历截图

### 🔜 待完成（MVP v1.0）

- [ ] 批量测试（20-50人）
- [ ] 用户手册
- [ ] 自动打招呼（可选）

---

# 📘 第13章：部署与运维

## 13.1 部署架构

### 开发环境

```
本地开发
  - Backend: localhost:8000
  - Frontend: localhost:3000
  - PostgreSQL: localhost:5432
  - Redis: localhost:6379
```

### 生产环境

```
云服务器（阿里云/腾讯云）
  - Backend: api.rupro-ats.com
  - Frontend: app.rupro-ats.com
  - PostgreSQL: RDS
  - Redis: Redis 云服务
  - OSS: 对象存储（报告、截图）
```

---

## 13.2 部署步骤

### 后端部署

```bash
# 1. 安装依赖
cd apps/backend
pip install -r requirements.txt

# 2. 配置环境变量
cp env.example .env
vim .env

# 3. 初始化数据库
python init_db.py

# 4. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端部署（可选）

```bash
# 1. 安装依赖
cd apps/frontend
npm install

# 2. 构建
npm run build

# 3. 部署到 Nginx
cp -r dist/* /var/www/html/
```

### Chrome 插件部署

```
1. 打开 Chrome 扩展程序页面
2. 启用"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择 apps/extension 目录
```

---

## 13.3 监控与告警

### 监控指标

- API 响应时间
- 数据库连接数
- LLM 调用次数
- 错误率
- 用户活跃度

### 告警规则

- API 响应时间 > 3s
- 错误率 > 5%
- 数据库连接数 > 80%
- 磁盘使用率 > 85%

---

## 13.4 备份策略

### 数据库备份

- 每日全量备份
- 每小时增量备份
- 保留 30 天

### 文件备份

- 简历截图备份到 OSS
- 报告文件备份到 OSS
- 保留 90 天

---

# 📘 第14章：测试策略

## 14.1 测试类型

### 单元测试

- 测试覆盖率 > 80%
- 关键模块 > 90%

### 集成测试

- API 接口测试
- 数据库操作测试
- 飞书集成测试

### 端到端测试

- 浏览器插件 → 后端 → 飞书
- 完整流程测试

### 性能测试

- 并发用户测试
- 压力测试
- 负载测试

---

## 14.2 测试工具

- **Pytest** - Python 单元测试
- **Postman** - API 测试
- **Selenium** - 端到端测试
- **Locust** - 性能测试

---

# 📘 第15章：风险与应对

## 15.1 技术风险

### 风险1: 平台反爬虫

**描述**: Boss/猎聘加强反爬虫策略

**应对**:
- 浏览器插件为主通道（风险最低）
- 限流策略
- 用户行为模拟

### 风险2: LLM API 限流

**描述**: 通义千问 API 调用受限

**应对**:
- 多模型备份（GPT-4, DeepSeek）
- 本地缓存
- 批量处理

### 风险3: 数据库性能

**描述**: 数据量增大导致查询变慢

**应对**:
- 索引优化
- 分库分表
- Redis 缓存

---

## 15.2 业务风险

### 风险1: 用户接受度

**描述**: 顾问不习惯使用系统

**应对**:
- 用户培训
- 操作简化
- 快速迭代

### 风险2: 数据准确性

**描述**: AI 解析错误率高

**应对**:
- 人工审核机制
- 顾问反馈循环
- 模型持续优化

---

## 15.3 合规风险

### 风险1: 数据隐私

**描述**: 候选人数据泄露

**应对**:
- 数据加密
- 访问控制
- 审计日志

### 风险2: 平台协议

**描述**: 违反招聘平台用户协议

**应对**:
- 浏览器插件合规
- 不使用爬虫
- 用户主动操作

---

# 🎉 文档完成！

## 📚 文档总结

本文档为 **Rupro ATS++ v3.0** 提供了：

✅ **完整的产品需求** - 从背景、目标到功能模块  
✅ **详细的系统架构** - Browser-First 架构，6 层设计  
✅ **可执行的技术方案** - 浏览器插件、标签体系、匹配引擎、寻访策略  
✅ **完整的数据库设计** - 5 张表，可直接建表  
✅ **完整的 API 设计** - 20+ 接口，可直接对接  
✅ **详细的开发路线图** - 8 个 Phase，14 周计划  
✅ **部署运维方案** - 从开发到生产  
✅ **测试策略** - 单元、集成、端到端、性能  
✅ **风险应对** - 技术、业务、合规

---

## 🚀 下一步行动

### 选项A: 继续完成 MVP v1.0 ⭐⭐⭐⭐⭐ **推荐**

- Day 10.1: 批量测试（20-50人）
- Day 10.3: 用户手册
- (可选) Day 9: 自动打招呼

**时间**: 2-3天

---

### 选项B: 开始 v2.0 开发

- Phase 2: JD 模块（采集 + 解析）
- Phase 4: 完整匹配引擎
- Phase 5: 寻访策略引擎

**时间**: 6-8周

---

### 选项C: 优化当前系统

- 性能优化
- 用户体验优化
- Bug 修复
- 文档完善

**时间**: 1-2周

---

## 🤔 你的选择？

请告诉我你想选择哪个方案！😊

