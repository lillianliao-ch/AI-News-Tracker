# AI 资讯追踪与小红书内容生成系统 - 项目规划

## 🎯 项目目标

基于 MediaCrawler 爬虫项目，构建一个 AI 行业资讯追踪与小红书内容自动生成系统，实现：
1. 多平台 AI 资讯自动爬取与聚合
2. 资讯可视化展示（参考用户提供的界面样式）
3. AI 驱动的小红书内容生成（3个版本）
4. 用户偏好学习与内容管理

---

## 📋 核心功能需求

### 1. 资讯爬取模块
- **数据源**：
  - 小红书（AI相关笔记）
  - 微博（AI大V、官方账号）
  - 知乎（AI话题讨论）
  - 贴吧（AI相关帖子）
  - B站（AI UP主动态）
  - 即时新闻源（36氪、虎嗅、量子位等）

- **追踪内容**：
  - ✅ 新产品发布（模型、应用、工具）
  - ✅ 新模型发布（开源、闭源）
  - ✅ 投融资动态
  - ✅ 行业观点和讨论
  - ✅ 技术突破和论文
  - ✅ 公司动态

### 2. 资讯聚合与展示
- **界面设计**（参考用户提供的截图）：
  ```
  ┌─────────────────────────────────────────┐
  │  AI 资讯仪表板                            │
  ├─────────────────────────────────────────┤
  │  [筛选] 按时间/热度/来源/类型             │
  ├─────────────────────────────────────────┤
  │  ┌──────┐ ┌──────┐ ┌──────┐             │
  │  │资讯1  │ │资讯2  │ │资讯3  │  卡片式布局│
  │  │摘要   │ │摘要   │ │摘要   │             │
  │  │[查看] │ │[查看] │ │[查看] │             │
  │  └──────┘ └──────┘ └──────┘             │
  │  [加载更多]                              │
  └─────────────────────────────────────────┘
  ```

- **核心功能**：
  - 资讯卡片展示（标题、摘要、来源、时间、热度）
  - 多维度筛选（时间、热度、来源、类型）
  - 搜索功能（关键词搜索）
  - 跳转原文链接
  - 收藏/标记功能

### 3. 小红书内容生成
- **输入**：选中的3条资讯
- **输出**：每条资讯生成3个版本的小红书内容
- **版本差异**：
  - 版本A：硬核技术风（适合专业用户）
  - 版本B：轻松科普风（适合大众用户）
  - 版本C：热点观点风（适合讨论）

- **生成要素**：
  - 吸引眼球的标题
  - 简洁有力的正文
  - 相关标签（#）
  - 配图建议
  - SEO 优化关键词

### 4. 内容管理与反馈
- **Tab 1：内容生成**
  - 显示3条资讯 × 3个版本 = 9个内容卡片
  - 用户可预览、选择、编辑
  - 支持批量操作

- **Tab 2：已发布管理**
  - 已发布内容记录
  - 发布平台（小红书、朋友圈等）
  - 发布时间
  - 数据反馈（点赞、收藏、评论）

- **用户偏好学习**：
  - 记录用户选择的版本类型
  - 分析用户喜好（风格、长度、话题）
  - 自动优化后续生成

---

## 🏗️ 技术架构设计

### 系统分层架构
```
┌─────────────────────────────────────────┐
│  前端展示层 (Streamlit/WebUI)            │
├─────────────────────────────────────────┤
│  业务逻辑层                              │
│  - 资讯聚合与筛选                        │
│  - 内容生成调度                          │
│  - 用户偏好管理                          │
├─────────────────────────────────────────┤
│  AI 服务层                               │
│  - 资讯分类与摘要                        │
│  - 小红书内容生成                        │
│  - 用户偏好分析                          │
├─────────────────────────────────────────┤
│  数据层                                  │
│  - SQLite/PostgreSQL                    │
│  - 向量数据库 (ChromaDB)                 │
│  - 缓存 (Redis)                          │
├─────────────────────────────────────────┤
│  爬虫层 (基于 MediaCrawler)             │
│  - 多平台爬虫                            │
│  - 数据清洗与去重                        │
│  - 定时任务调度                          │
└─────────────────────────────────────────┘
```

### 技术栈选择

#### 后端
- **框架**: FastAPI / Flask
- **爬虫**: 基于 MediaCrawler（Playwright）
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **向量库**: ChromaDB (语义搜索)
- **任务调度**: APScheduler / Celery
- **AI 服务**: OpenAI API / DeepSeek / 本地模型

#### 前端
- **方案 A (快速)**: Streamlit
- **方案 B (专业)**: Vue.js + FastAPI
- **方案 C (复用)**: MediaCrawler WebUI

#### AI 能力
- **资讯处理**: GPT-4 / DeepSeek-V3
- **内容生成**: GPT-4o / Claude 3.5 Sonnet
- **摘要提炼**: BERT / T5
- **图片生成**: DALL-E 3 / Midjourney API

---

## 📊 数据流设计

### 1. 资讯采集流程
```
定时任务触发
    ↓
MediaCrawler 爬取各平台
    ↓
数据清洗与去重
    ↓
AI 分类打标签（产品/模型/融资/观点）
    ↓
AI 生成摘要
    ↓
存入数据库（结构化 + 向量化）
    ↓
推送到前端展示
```

### 2. 内容生成流程
```
用户选择3条资讯
    ↓
读取资讯全文
    ↓
调用 AI 生成小红书内容（3个版本）
    ↓
保存草稿到数据库
    ↓
前端展示供用户选择
    ↓
用户选择并确认
    ↓
记录用户偏好
    ↓
生成发布格式（Markdown/HTML）
    ↓
提供复制/发布接口
```

### 3. 偏好学习流程
```
用户选择版本A/B/C
    ↓
记录选择（资讯ID、版本、时间）
    ↓
累计选择历史
    ↓
定期分析偏好模式
    ↓
优化生成 Prompt
    ↓
下次生成更符合用户喜好
```

---

## 🗄️ 数据库设计

### 核心表结构

#### 1. 资讯表 (ai_news)
```sql
CREATE TABLE ai_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    source TEXT,              -- 来源平台
    source_url TEXT,          -- 原文链接
    author TEXT,              -- 作者
    publish_time TIMESTAMP,
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- AI 分析字段
    category TEXT,            -- 产品/模型/融资/观点
    tags TEXT,                -- JSON数组 ["GPT-5", "OpenAI"]
    sentiment TEXT,           -- 积极/中性/消极
    importance INTEGER,       -- 重要性评分 1-5

    -- 互动数据
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,

    -- 向量化
    embedding_id TEXT,

    -- 状态
    is_published BOOLEAN DEFAULT FALSE,
    is_selected BOOLEAN DEFAULT FALSE,
    selected_count INTEGER DEFAULT 0
);
```

#### 2. 内容生成表 (generated_content)
```sql
CREATE TABLE generated_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER,
    version TEXT,             -- A/B/C

    -- 小红书内容
    title TEXT,
    content TEXT,
    hashtags TEXT,            -- JSON数组
    image_prompt TEXT,

    -- 元数据
    model_used TEXT,
    prompt_used TEXT,
    generation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 用户反馈
    is_selected BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    published_to TEXT,        -- 小红书/朋友圈
    published_time TIMESTAMP,

    FOREIGN KEY (news_id) REFERENCES ai_news(id)
);
```

#### 3. 用户偏好表 (user_preferences)
```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preference_type TEXT,     -- style/length/topic
    preference_value TEXT,    -- technical/casual/hot
    weight REAL DEFAULT 1.0,  -- 权重
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. 选择历史表 (selection_history)
```sql
CREATE TABLE selection_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER,
    content_id INTEGER,
    version TEXT,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (news_id) REFERENCES ai_news(id),
    FOREIGN KEY (content_id) REFERENCES generated_content(id)
);
```

---

## 🚀 实施计划

### Phase 1: 基础爬虫 (1-2周)
- [ ] 选择 2-3 个平台进行爬虫开发
- [ ] 基于 MediaCrawler 实现数据采集
- [ ] 实现数据清洗与去重
- [ ] 数据库设计与实现
- [ ] 基础数据展示（Streamlit）

### Phase 2: AI 增强 (2-3周)
- [ ] 接入 AI API（分类、摘要）
- [ ] 实现资讯自动打标签
- [ ] 开发摘要生成功能
- [ ] 实现相似资讯去重（向量搜索）
- [ ] 优化数据展示界面

### Phase 3: 内容生成 (2-3周)
- [ ] 设计小红书内容 Prompt
- [ ] 实现 3 版本内容生成
- [ ] 开发内容预览界面
- [ ] 实现用户选择功能
- [ ] 添加编辑与调整功能

### Phase 4: 偏好学习 (1-2周)
- [ ] 记录用户选择历史
- [ ] 实现偏好分析算法
- [ ] 优化生成 Prompt
- [ ] A/B 测试不同风格

### Phase 5: 完善与优化 (持续)
- [ ] 添加更多数据源
- [ ] 优化界面体验
- [ ] 性能优化
- [ ] 数据统计分析

---

## 💡 关键技术难点

### 1. 资讯去重
**挑战**: 同一新闻在不同平台重复出现
**解决方案**:
- 文本相似度计算（TF-IDF + Cosine）
- 向量化语义搜索（ChromaDB）
- 标题 + 摘要 + 时间联合去重

### 2. 内容生成质量控制
**挑战**: AI 生成内容可能不准确或不符合小红书风格
**解决方案**:
- 精心设计的 Prompt 模板
- Few-shot learning（提供优质示例）
- 人工审核 + 用户反馈闭环
- 定期更新 Prompt

### 3. 用户偏好学习
**挑战**: 如何从少量选择数据中学习偏好
**解决方案**:
- 冷启动：提供默认偏好设置
- 显式反馈：用户主动选择
- 隐式反馈：停留时间、点击率
- 协同过滤：找相似用户

### 4. 实时性 vs 成本
**挑战**: 实时爬取和 AI 生成都需要成本
**解决方案**:
- 定时任务 + 增量更新
- 缓存热门内容
- 批量处理降低 API 调用
- 免费数据源 + 付费 API 结合

---

## 📈 成功指标

### 短期目标（1个月）
- ✅ 成功爬取 3+ 平台资讯
- ✅ 每天 50+ 条 AI 相关资讯
- ✅ 生成内容可用率 > 60%

### 中期目标（3个月）
- ✅ 覆盖 5+ 数据源
- ✅ 每天 100+ 条资讯
- ✅ 用户选择生成内容 > 80% 满意度

### 长期目标（6个月）
- ✅ 自动化运行，人工干预 < 10%
- ✅ 内容生成质量 > 90%
- ✅ 用户增长 + 活跃度提升

---

## 🎁 额外价值

通过这个项目，你将获得：
1. **多平台爬虫经验**: MediaCrawler 实战应用
2. **AI 应用开发**: LLM 集成与 Prompt 工程
3. **产品思维**: 从 0 到 1 构建完整产品
4. **数据分析**: 用户行为分析与优化
5. **小红书运营**: 内容生产与流量获取

---

## 📝 下一步行动

### 立即可做
1. 确定 MVP 范围（最小可行产品）
2. 选择第一个爬取平台（建议：微博 + 36氪）
3. 设计数据库 Schema
4. 搭建基础开发环境

### 本周完成
1. 实现第一个爬虫
2. 数据库设计与创建
3. 基础 WebUI 搭建
4. AI API 接入测试

### 本月完成
1. 完成 MVP 版本
2. 内测与反馈
3. 优化迭代

---

**项目代号**: AI News Tracker
**预计工期**: 8-12 周
**优先级**: 🔥 高
**风险等级**: 中等
