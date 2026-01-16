# AI News Tracker

智能资讯追踪与内容生成系统 - 自动聚合 AI 行业资讯，AI 驱动分类摘要，一键生成小红书内容。

## ✨ 核心特性

- **🤖 AI 驱动**: 自动分类、智能摘要、3种风格内容生成
- **📰 多源聚合**: 36氪、InfoQ、TechCrunch 等主流科技媒体 RSS 订阅
- **🎨 精美 UI**: 参考 newsnow 设计，优雅卡片式布局
- **⚡ 实时更新**: 定时爬取 + 手动刷新，2小时间隔
- **🔍 智能筛选**: 按分类、来源、标签快速筛选
- **📱 内容生成**: 一键生成 3 版本小红书内容（硬核/科普/观点）
- **💾 本地优先**: SQLite 本地数据库，完全掌控数据

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 (Astro)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  NewsGrid    │  │  NewsCard    │  │  GenerateBtn │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 API (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  GET /news   │  │ POST /crawl  │  │POST /generate│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  爬虫模块     │    │  AI 服务     │    │   数据库      │
│  RSS Source  │    │  Classify    │    │   SQLite     │
│  HTTP Source │    │  Summary     │    │  SQLAlchemy  │
│              │    │  Generate    │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 📦 项目结构

```
ai_news_tracker/
├── backend/                 # Python 后端
│   ├── config/             # 配置管理
│   │   └── base_config.py  # 基础配置 + 数据源配置
│   ├── sources/            # 数据源抽象层
│   │   └── base.py         # BaseSource, RSSSource
│   ├── services/           # 业务服务
│   │   └── ai_service.py   # AI 服务（分类/摘要/生成）
│   ├── models/             # 数据模型
│   │   ├── database.py     # SQLAlchemy 模型
│   │   └── init_db.py      # 数据库初始化
│   ├── tasks/              # 异步任务
│   │   └── crawler.py      # 爬虫任务
│   ├── main.py             # FastAPI 应用
│   ├── requirements.txt    # Python 依赖
│   └── .env.example        # 环境变量示例
│
├── frontend/               # Astro 前端
│   ├── src/
│   │   ├── pages/
│   │   │   └── index.astro  # 主页面
│   │   └── components/      # Astro 组件
│   │       ├── NewsGrid.astro
│   │       ├── NewsCard.astro
│   │       ├── Header.astro
│   │       ├── Sidebar.astro
│   │       └── RefreshButton.astro
│   ├── package.json
│   └── astro.config.mjs
│
└── README.md
```

## 🚀 快速开始

### 前置要求

- **Python**: 3.9+
- **Node.js**: 18+
- **API Keys**:
  - OpenAI API Key（用于分类）
  - Anthropic API Key（用于摘要和内容生成）

### 1️⃣ 克隆项目

```bash
cd ai_news_tracker
```

### 2️⃣ 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

**`.env` 配置示例:**

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

DATABASE_URL=sqlite+aiosqlite:///./data/ai_news.db

# 可选配置
CRAWL_INTERVAL=7200  # 爬取间隔（秒）
LOG_LEVEL=INFO
```

**初始化数据库:**

```bash
# 方式1：使用初始化脚本
python models/init_db.py

# 方式2：启动时自动初始化（main.py 中已配置）
# 数据库会在首次启动时自动创建
```

**启动后端服务:**

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 `http://localhost:8000` 启动

- API 文档: `http://localhost:8000/docs`
- Root 接口: `http://localhost:8000/`

### 3️⃣ 前端设置

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用 pnpm
pnpm install

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:4321` 启动

### 4️⃣ 首次爬取

访问 `http://localhost:4321`，点击右上角 **"刷新资讯"** 按钮，或直接调用 API:

```bash
curl -X POST http://localhost:8000/api/crawl
```

## 📖 API 文档

### 获取资讯列表

```bash
GET /api/news?category=model&limit=20
```

**参数:**
- `category`: 筛选分类（可选）
- `source`: 筛选来源（可选）
- `limit`: 数量限制（默认 50）
- `offset`: 分页偏移（默认 0）

**响应:**
```json
[
  {
    "id": 1,
    "news_id": "36kr_12345",
    "title": "GPT-5 即将发布",
    "url": "https://36kr.com/...",
    "summary": "OpenAI 宣布...",
    "source": "36氪",
    "category": "model",
    "tags": "GPT,LLM,OpenAI",
    "publish_time": "2025-01-13T10:00:00",
    "crawl_time": "2025-01-13T10:05:00"
  }
]
```

### 生成小红书内容

```bash
POST /api/generate
{
  "news_id": "36kr_12345",
  "versions": ["A", "B", "C"]
}
```

**响应:**
```json
[
  {
    "news_id": "36kr_12345",
    "version": "A",
    "title": "🔥 GPT-5 来了！这些技术突破你必须知道",
    "content": "OpenAI 正式宣布 GPT-5...",
    "hashtags": ["#AI", "#GPT5", "#黑科技"],
    "image_prompt": "GPT-5 技术突破配图，科技风格"
  }
]
```

### 手动触发爬虫

```bash
POST /api/crawl
```

**响应:**
```json
{
  "message": "爬虫任务已启动，正在后台运行",
  "status": "running"
}
```

### 获取统计信息

```bash
GET /api/stats
```

**响应:**
```json
{
  "total_news": 1250,
  "today_news": 45,
  "category_stats": {
    "product": 320,
    "model": 280,
    "investment": 150,
    "view": 500
  },
  "source_stats": {
    "36氪": 450,
    "InfoQ": 380,
    "TechCrunch": 420
  }
}
```

## 🎯 资讯分类体系

系统自动将资讯分类为以下 6 类：

| 分类 | 说明 | 示例 |
|------|------|------|
| `product` | 新产品发布 | 新工具、新应用、新平台 |
| `model` | 新模型发布 | 开源模型、学术模型 |
| `investment` | 投融资 | 融资、收购、IPO |
| `view` | 行业观点 | 评论、分析、观点 |
| `research` | 学术论文 | 研究成果、实验发布 |
| `application` | AI应用 | 落地案例、应用场景 |

## 🎨 小红书内容生成

系统为每条资讯生成 **3 种风格** 的小红书内容：

### 版本 A: 硬核技术风
- **目标受众**: 技术人员、开发者
- **风格特点**: 专业但不晦涩，用数据说话
- **标题**: 包含技术关键词
- **内容**: 技术原理 + 应用场景 + 竞品对比

### 版本 B: 轻松科普风
- **目标受众**: 大众用户、AI 初学者
- **风格特点**: 口语化，多用表情符号 😱🔥✨
- **标题**: 制造好奇心，用感叹号
- **内容**: 比喻解释 + 日常应用 + 关注理由

### 版本 C: 热点观点风
- **目标受众**: 行业从业者、关注趋势者
- **风格特点**: 有观点、有立场
- **标题**: 引发讨论或争议
- **内容**: 影响分析 + 行业冲击 + 个人看法

## 🛠️ 配置说明

### 添加新的数据源

编辑 `backend/config/base_config.py`:

```python
SOURCES_CONFIG = {
    "my_source": {
        "id": "my_source",
        "name": "我的数据源",
        "enabled": True,
        "type": "rss",  # 或 "http"
        "url": "https://example.com/feed",
        "icon": "https://example.com/icon.png"
    }
}
```

### AI 模型配置

在 `.env` 中配置不同的模型：

```bash
# 分类模型（推荐使用便宜快速的模型）
CLASSIFY_MODEL=gpt-4o-mini

# 摘要模型（推荐使用长文本模型）
SUMMARY_MODEL=claude-3-5-sonnet-20241022

# 生成模型
GENERATE_MODEL=claude-3-5-sonnet-20241022
```

## 📊 数据库 Schema

```sql
-- 资讯表
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    news_id VARCHAR UNIQUE,  -- 唯一标识
    title VARCHAR,           -- 标题
    url VARCHAR,             -- 链接
    summary TEXT,            -- 摘要
    content TEXT,            -- 内容
    source VARCHAR,          -- 来源
    source_url VARCHAR,      -- 来源链接
    icon VARCHAR,            -- 图标
    category VARCHAR,        -- 分类
    tags VARCHAR,            -- 标签（逗号分隔）
    sentiment VARCHAR,       -- 情感
    importance INTEGER,      -- 重要性
    publish_time DATETIME,   -- 发布时间
    crawl_time DATETIME      -- 爬取时间
);

-- 爬虫日志表
CREATE TABLE crawler_log (
    id INTEGER PRIMARY KEY,
    platform VARCHAR,        -- 平台
    start_time DATETIME,     -- 开始时间
    end_time DATETIME,       -- 结束时间
    status VARCHAR,          -- 状态
    items_crawled INTEGER,   -- 爬取数量
    error_message TEXT       -- 错误信息
);
```

## 🔧 开发指南

### 添加新的 AI 功能

编辑 `backend/services/ai_service.py`:

```python
class AIService:
    async def your_new_function(self, data: Dict) -> Dict:
        prompt = "你的 prompt"
        response = self.anthropic_client.messages.create(
            model=settings.GENERATE_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"result": response.content[0].text}
```

### 添加新的前端组件

创建 `frontend/src/components/YourComponent.astro`:

```astro
---
const { title, items } = Astro.props;
---

<div class="your-component">
  <h2>{title}</h2>
  {items.map(item => <p>{item}</p>)}
</div>

<style>
  .your-component {
    /* 样式 */
  }
</style>
```

## 🚀 部署

### 后端部署

```bash
# 使用 gunicorn + uvicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 前端部署

```bash
# 构建静态文件
npm run build

# 输出在 dist/ 目录，可部署到任何静态托管服务
# - Vercel
# - Netlify
# - GitHub Pages
# - Nginx
```

## 📝 待办事项

- [ ] 用户偏好学习系统
- [ ] 更多数据源支持（知乎、微博等）
- [ ] 内容质量评分
- [ ] 定时发布到小红书
- [ ] 数据分析仪表板
- [ ] 通知系统（Telegram/Email）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 联系

如有问题，请提交 Issue 或通过以下方式联系：

- Email: your-email@example.com
- GitHub Issues: [项目 Issues 页面]

---

**⚠️ 免责声明**: 本项目仅供学习研究使用，请遵守相关网站的使用条款和 robots.txt 规定。
