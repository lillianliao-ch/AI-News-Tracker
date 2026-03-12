# MediaCrawler vs newsnow 深度对比分析

> 基于官方 README 和源码分析，为你打造最优 AI 资讯追踪系统

---

## 📊 项目概览对比

| 维度 | MediaCrawler | newsnow | 你的需求 |
|------|-------------|---------|---------|
| **核心功能** | 多平台爬虫 | 新闻聚合展示 | 爬虫 + 展示 + AI生成 |
| **技术栈** | Python + Playwright | Node.js + Astro | Python 后端 + 前端 |
| **主要用途** | 数据采集 | 用户阅读 | 自动化内容生产 |
| **数据源** | 7个自媒体平台 | 多个新闻源 | AI 相关资讯 |
| **UI风格** | 后台管理 | 优雅阅读界面 | 类 newsnow |
| **AI能力** | ❌ 无 | ❌ 无 | ✅ 核心 |

---

## 🏗️ MediaCrawler 架构深度分析

### 1. 核心设计理念

```python
# MediaCrawler 的核心思想
"无需JS逆向" + "浏览器自动化" + "配置驱动"

# 实现方式
1. Playwright 模拟真实浏览器
2. 保存登录态（Cookie/LocalStorage）
3. 通过 JS 表达式获取签名参数
4. 配置文件控制所有行为
```

### 2. 项目结构

```
MediaCrawler/
├── config/
│   ├── base_config.py          # ⭐ 配置中心
│   ├── config.py              # 多平台配置
│   └── media_config.py        # 媒体配置
├── core/
│   ├── exector.py             # 执行器
│   ├── initializer.py         # 初始化
│   └── handler.py             # 处理器
├── proxy/
│   └── ip_proxy.py           # IP代理池
├── store/
│   ├── sqlite_store.py       # SQLite存储
│   ├── mysql_store.py        # MySQL存储
│   └── csv_store.py          # CSV存储
├── tools/
│   └── utils.py              # 工具函数
├── main.py                    # ⭐ 入口文件
├── var/
│   └── cookies/              # Cookie存储
└── api/                       # WebUI
    └── main.py               # FastAPI服务
```

### 3. 配置驱动设计（核心优势）

```python
# config/base_config.py
class Config:
    # 平台配置
    platform = "xhs"  # xhs/dy/kuaishou/bilibili/weibo/tieba/zhihu

    # 登录方式
    login_type = "qrcode"  # qrcode/cookie/phone

    # 爬取类型
    crawl_type = "search"  # search/detail

    # 关键词
    keywords = "AI,大模型,GPT"

    # 数据存储
    storage_mode = "sqlite"  # csv/json/excel/sqlite/mysql

    # WebUI配置
    webui_port = 8080

    # 代理配置
    enable_proxy = False

    # 爬取间隔
    crawl_interval = 2  # 秒
```

### 4. 可复用的核心模块

#### A. 爬虫执行器
```python
# 核心流程
class MediaCrawler:
    def start(self):
        # 1. 初始化浏览器
        browser = self.init_browser()

        # 2. 登录
        self.login(browser)

        # 3. 爬取数据
        data = self.crawl_data(browser)

        # 4. 保存数据
        self.save_data(data)

        # 5. 关闭浏览器
        browser.close()
```

#### B. 多存储适配
```python
# 统一存储接口
class StorageFactory:
    @staticmethod
    def create_storage(mode):
        if mode == "sqlite":
            return SQLiteStore()
        elif mode == "mysql":
            return MySQLStore()
        elif mode == "csv":
            return CSVStore()
        # ...
```

#### C. WebUI (FastAPI)
```python
# api/main.py
from fastapi import FastAPI
app = FastAPI()

@app.post("/crawl/start")
async def start_crawl(config: CrawlConfig):
    """启动爬虫"""
    crawler = MediaCrawler(config)
    result = await crawler.start()
    return result

@app.get("/data/preview")
async def preview_data():
    """预览数据"""
    return get_latest_data()
```

### 5. 关键技术点

#### 登录态保存
```python
# 核心机制：保存浏览器上下文
browser_context.save_state()
# 下次启动时恢复
browser_context.load_state()
```

#### 反爬虫绕过
```python
# 1. User-Agent 轮换
user_agents = ["UA1", "UA2", "UA3"]

# 2. IP 代理池
proxies = ["proxy1", "proxy2", "proxy3"]

# 3. 随机延迟
time.sleep(random.uniform(1, 3))

# 4. 签名参数获取
signature = browser.evaluate("window.getSignature()")
```

---

## 🎨 newsnow 架构深度分析

### 1. 核心设计理念

```javascript
// newsnow 的核心思想
"优雅阅读" + "实时更新" + "数据同步" + "智能缓存"

// 实现方式
1. Astro SSG (静态生成)
2. 服务端 API (数据爬取)
3. 客户端轮询 (实时更新)
4. GitHub OAuth (用户同步)
5. 自适应缓存 (避免被封)
```

### 2. 项目结构

```
newsnow/
├── src/
│   ├── pages/                  # Astro 页面
│   │   └── index.astro         # ⭐ 主页
│   ├── components/             # 组件
│   │   ├── NewsCard.astro      # 新闻卡片
│   │   ├── NewsList.astro      # 新闻列表
│   │   └── RefreshButton.astro # 刷新按钮
│   ├── layouts/                # 布局
│   └── styles/                 # 样式
├── server/
│   ├── sources/                # ⭐ 数据源
│   │   ├── index.ts           # 数据源聚合
│   │   ├── 36kr.ts            # 36氪
│   │   ├── zhihu.ts           # 知乎
│   │   └── ...
│   └── api/                   # API路由
│       ├── index.ts           # 主API
│       ├── oauth.ts           # OAuth
│       └── refresh.ts         # 刷新接口
├── shared/
│   ├── sources/               # 共享数据源定义
│   └── types.ts               # 类型定义
├── public/                     # 静态资源
├── db/                         # 数据库
│   └── schema.sql             # 数据库Schema
└── astro.config.mjs            # Astro配置
```

### 3. 数据源架构（核心优势）

```typescript
// shared/sources/index.ts
export interface Source {
  id: string
  name: string
  homeUrl: string
  icon: string
  getData: () => Promise<NewsItem[]>
}

// server/sources/36kr.ts
export const kr36: Source = {
  id: '36kr',
  name: '36氪',
  homeUrl: 'https://36kr.com',
  icon: '/icons/36kr.png',

  async getData() {
    // 爬取逻辑
    const response = await fetch('https://36kr.com/api/news')
    const data = await response.json()

    return data.map(item => ({
      id: item.id,
      title: item.title,
      url: item.url,
      summary: item.summary,
      timestamp: Date.now()
    }))
  }
}
```

### 4. UI组件设计

#### NewsCard 组件
```astro
---
// src/components/NewsCard.astro
const { title, url, summary, source, timestamp } = Astro.props;

<div class="news-card">
  <div class="source">{source.name}</div>
  <h3 class="title">
    <a href={url}>{title}</a>
  </h3>
  <p class="summary">{summary}</p>
  <div class="meta">
    <time>{new Date(timestamp).toLocaleString()}</time>
  </div>
</div>

<style>
  .news-card {
    padding: 16px;
    border-radius: 8px;
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  .title a {
    color: #1a1a1a;
    text-decoration: none;
  }
  .title a:hover {
    color: #007bff;
  }
</style>
```

#### 主页布局
```astro
---
// src/pages/index.astro
import NewsList from '../components/NewsList.astro';
import RefreshButton from '../components/RefreshButton.astro';
const allNews = await fetch('http://localhost:8080/api/news').then(r => r.json());
---

<html>
  <head>
    <title>NewsNow - AI资讯</title>
  </head>
  <body>
    <header>
      <h1>🤖 AI News Now</h1>
      <RefreshButton client:load />
    </header>

    <main>
      <NewsList news={allNews} client:load />
    </main>
  </body>
</html>
```

### 5. 智能缓存机制

```typescript
// server/api/index.ts
export async function GET({ request }) {
  // 检查缓存
  const cached = await cache.get('all_news');
  if (cached && isWithinCacheTime(cached.timestamp, 30 * 60 * 1000)) {
    return new Response(JSON.stringify(cached.data));
  }

  // 缓存失效，爬取新数据
  const allNews = await Promise.all(
    sources.map(source => source.getData())
  );

  // 保存到缓存
  await cache.set('all_news', {
    data: allNews.flat(),
    timestamp: Date.now()
  });

  return new Response(JSON.stringify(allNews.flat()));
}
```

### 6. 实时更新机制

```typescript
// 客户端轮询
<script>
  async function autoRefresh() {
    const interval = setInterval(async () => {
      const response = await fetch('/api/refresh');
      const news = await response.json();

      // 更新UI
      updateNewsList(news);
    }, 2 * 60 * 1000); // 2分钟刷新一次

    return () => clearInterval(interval);
  }

  autoRefresh();
</script>
```

---

## 🔥 融合方案设计

### 方案架构图

```
┌─────────────────────────────────────────┐
│  前端 (参考 newsnow UI)                 │
│  - Astro SSG + React 组件                │
│  - 优雅卡片式布局                        │
│  - 实时刷新按钮                          │
├─────────────────────────────────────────┤
│  API 服务层                              │
│  - /api/news (获取资讯)                  │
│  - /api/generate (生成小红书内容)        │
│  - /api/preference (用户偏好)            │
├─────────────────────────────────────────┤
│  业务逻辑层                              │
│  - 资讯聚合 (参考 newsnow)                │
│  - AI 处理 (分类、摘要、生成)             │
│  - 用户偏好学习                          │
├─────────────────────────────────────────┤
│  数据层                                  │
│  - SQLite (结构化数据)                   │
│  - ChromaDB (向量搜索)                   │
│  - Redis (缓存)                          │
├─────────────────────────────────────────┤
│  爬虫层 (参考 MediaCrawler)             │
│  - 基础爬虫基类                          │
│  - RSS 爬虫                              │
│  - 微博爬虫 (可选)                       │
└─────────────────────────────────────────┘
```

---

## 💡 核心代码实现

### 1. 数据源抽象（参考 newsnow）

```python
# shared/sources/base.py
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime

class BaseSource(ABC):
    """数据源基类"""

    def __init__(self):
        self.id = None
        self.name = None
        self.home_url = None
        self.icon = None

    @abstractmethod
    async def get_data(self) -> List[Dict]:
        """获取数据"""
        pass

    def normalize(self, raw_data: Dict) -> Dict:
        """标准化数据格式"""
        return {
            'id': f"{self.id}_{raw_data['id']}",
            'title': raw_data['title'],
            'url': raw_data['url'],
            'summary': raw_data.get('summary', ''),
            'content': raw_data.get('content', ''),
            'source': self.name,
            'source_url': self.home_url,
            'publish_time': self.parse_time(raw_data.get('time')),
            'crawl_time': datetime.now(),
            'extra': raw_data.get('extra', {})
        }
```

### 2. RSS 数据源实现

```python
# sources/rss_source.py
import feedparser
from shared.sources.base import BaseSource

class RSSSource(BaseSource):
    """RSS 数据源"""

    def __init__(self, config):
        super().__init__()
        self.id = config['id']
        self.name = config['name']
        self.home_url = config['home_url']
        self.rss_url = config['rss_url']

    async def get_data(self):
        """解析 RSS"""
        feed = feedparser.parse(self.rss_url)

        results = []
        for entry in feed.entries[:50]:  # 限制50条
            item = self.normalize({
                'id': entry.get('id', entry.get('link')),
                'title': entry.get('title'),
                'url': entry.get('link'),
                'summary': entry.get('summary', ''),
                'content': entry.get('content', [{}])[0].get('value', ''),
                'time': entry.get('published')
            })
            results.append(item)

        return results
```

### 3. 爬虫基类（参考 MediaCrawler）

```python
# crawlers/base_crawler.py
from playwright.async_api import async_playwright
from typing import List, Dict

class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, config: Dict):
        self.config = config
        self.browser = None
        self.context = None

    async def init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()

        # 读取已保存的浏览器状态
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=f"./var/browser/{self.config['platform']}",
            headless=False  # 可见模式，便于调试
        )

        self.browser = await self.context.new_page()

    async def close_browser(self):
        """关闭浏览器"""
        if self.context:
            await self.context.save_state()
        if self.playwright:
            await self.playwright.stop()

    @abstractmethod
    async def crawl(self) -> List[Dict]:
        """爬取数据"""
        pass
```

### 4. 前端组件（参考 newsnow）

```astro
---
// src/components/NewsCard.astro
const { news } = Astro.props;

<article class="news-card">
  <div class="card-header">
    <img src={news.icon} alt={news.source} class="source-icon" />
    <span class="source-name">{news.source}</span>
    <span class="publish-time">
      {new Date(news.publish_time).toLocaleString('zh-CN')}
    </span>
  </div>

  <h2 class="news-title">
    <a href={news.url} target="_blank">{news.title}</a>
  </h2>

  <p class="news-summary">{news.summary}</p>

  <div class="card-footer">
    <span class="category">{news.category}</span>
    <button class="generate-btn" data-news-id={news.id}>
      ✍️ 生成小红书内容
    </button>
  </div>
</article>

<style>
  .news-card {
    padding: 20px;
    border-radius: 12px;
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .news-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  }

  .news-title a {
    color: #1a1a1a;
    font-size: 1.25rem;
    font-weight: 600;
    text-decoration: none;
  }

  .news-title a:hover {
    color: #007bff;
  }

  .generate-btn {
    padding: 8px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
  }

  .generate-btn:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  }
</style>
```

### 5. 主页布局（完全参考 newsnow）

```astro
---
// src/pages/index.astro
import NewsGrid from '../components/NewsGrid.astro';
import Header from '../components/Header.astro';
import Sidebar from '../components/Sidebar.astro';

// 获取所有资讯
const response = await fetch('http://localhost:8080/api/news');
const allNews = await response.json();

// 分类
const categories = ['全部', '产品', '模型', '融资', '观点'];
---

<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>AI News Now - 优雅的AI资讯阅读</title>
  </head>
  <body>
    <div class="container">
      <!-- 侧边栏 -->
      <Sidebar client:load />

      <!-- 主内容区 -->
      <main class="main-content">
        <Header client:load />

        <!-- 分类筛选 -->
        <div class="categories">
          {categories.map(cat => (
            <button class="category-btn">{cat}</button>
          ))}
        </div>

        <!-- 资讯网格 -->
        <NewsGrid news={allNews} client:load />
      </main>
    </div>
  </body>
</html>

<style is:global>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f7fa;
    color: #1a1a1a;
  }

  .container {
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 24px;
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px;
  }

  .main-content {
    min-width: 0;
  }

  .categories {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    }

  .category-btn {
    padding: 8px 16px;
    border: 1px solid #e0e0e0;
    background: white;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .category-btn:hover,
  .category-btn.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
  }
</style>
```

---

## 📋 最终推荐技术栈

### 后端 (Python)
```python
# 框架
FastAPI == 0.104.1

# 爬虫
playwright == 1.40.0
feedparser == 6.0.10
beautifulsoup4 == 4.12.2

# 数据处理
pandas == 2.1.3

# 数据库
sqlalchemy == 2.0.23
chromadb == 0.4.18
aiosqlite == 0.19.0

# AI 服务
openai == 1.6.1
anthropic == 0.7.8

# 任务调度
apscheduler == 3.10.4
```

### 前端 (Node.js)
```json
{
  "dependencies": {
    "astro": "^4.0.0",
    "react": "^18.2.0",
    "tailwindcss": "^3.4.0",
    "@astrojs/react": "^3.0.0"
  }
}
```

### 项目结构
```
ai_news_tracker/
├── backend/                    # Python 后端
│   ├── crawlers/              # 爬虫 (参考 MediaCrawler)
│   ├── sources/               # 数据源 (参考 newsnow)
│   ├── services/              # AI 服务
│   ├── api/                   # FastAPI
│   └── config/                # 配置
├── frontend/                   # Astro 前端 (参考 newsnow)
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── layouts/
│   └── public/
└── shared/                    # 共享类型定义
```

---

## ✅ 下一步行动

### 立即可做
1. **不需要下载项目** - 在线阅读代码即可
2. **创建融合项目** - 结合两者优势
3. **MVP 开发** - 先做 RSS + newsnow UI

### 学习重点
1. **MediaCrawler**: 配置驱动设计
2. **newsnow**: 数据源抽象 + UI组件
3. **两者结合**: 取长补短

---

**分析完成时间**: 2025-01-12
**状态**: ✅ 已完成对比分析
**建议**: 采用 newsnow UI + MediaCrawler 爬虫架构
