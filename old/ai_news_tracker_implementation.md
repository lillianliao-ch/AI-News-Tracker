# AI 资讯追踪系统 - 技术实施文档

> 基于 MediaCrawler 的 AI 资讯追踪与小红书内容生成系统

---

## 🎯 MVP 范围定义（最小可行产品）

### ✅ 第一版本包含
- **数据源**: 微博 + 36氪（RSS）
- **爬取频率**: 每2小时一次
- **资讯量**: 每天 20-30 条
- **AI 功能**: 自动分类 + 摘要生成
- **内容生成**: 手动触发，单条生成
- **前端**: Streamlit 简单界面
- **存储**: SQLite

### ❌ 第一版本不包含
- 多平台爬虫（先用 2 个）
- 自动内容生成（手动触发）
- 用户偏好学习（手动记录）
- 实时推送（定时查看）
- 复杂推荐算法

---

## 🛠️ 技术栈确定

### 核心依赖
```bash
# requirements.txt
# 爬虫相关
playwright==1.40.0
requests==2.31.0
beautifulsoup4==4.12.2
feedparser==6.0.10

# 数据处理
pandas==2.1.3
openpyxl==3.1.2

# 数据库
sqlalchemy==2.0.23
chromadb==0.4.18

# AI 服务
openai==1.6.1
anthropic==0.7.8

# Web 框架
streamlit==1.29.0

# 任务调度
apscheduler==3.10.4
```

### 项目结构
```
ai_news_tracker/
├── config/
│   ├── __init__.py
│   ├── base_config.py          # 基础配置
│   └── prompts.py              # Prompt 模板
├── crawlers/
│   ├── __init__.py
│   ├── base_crawler.py         # 基础爬虫类
│   ├── weibo_crawler.py        # 微博爬虫
│   └── rss_crawler.py          # RSS 爬虫
├── services/
│   ├── __init__.py
│   ├── news_service.py         # 资讯业务逻辑
│   ├── ai_service.py           # AI 服务
│   └── content_service.py      # 内容生成服务
├── models/
│   ├── __init__.py
│   ├── database.py             # 数据库模型
│   └── schemas.py              # 数据结构
├── utils/
│   ├── __init__.py
│   ├── text_utils.py           # 文本处理工具
│   └── ai_utils.py             # AI 工具函数
├── web/
│   ├── app.py                  # Streamlit 应用
│   └── pages/
│       ├── 1_📰_资讯列表.py
│       ├── 2_✍️_内容生成.py
│       └── 3_📊_已发布.py
├── data/
│   ├── ai_news.db              # SQLite 数据库
│   └── cache/                  # 缓存目录
├── logs/                       # 日志目录
├── tests/                      # 测试代码
├── main.py                     # 程序入口
└── README.md
```

---

## 📊 数据库详细设计

### 表结构 SQL

```sql
-- 1. 资讯表
CREATE TABLE ai_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    source TEXT NOT NULL,        -- weibo/36kr
    source_url TEXT UNIQUE,      -- 原文链接（去重依据）
    author TEXT,
    publish_time TIMESTAMP,
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- AI 分析
    category TEXT,               -- product/model/investment/view
    tags TEXT,                   -- JSON: ["GPT-5", "OpenAI"]
    sentiment TEXT,              -- positive/neutral/negative
    importance INTEGER DEFAULT 3, -- 1-5

    -- 向量搜索
    vector_id TEXT,

    -- 统计
    view_count INTEGER DEFAULT 0,
    select_count INTEGER DEFAULT 0,

    -- 索引
    INDEX idx_publish_time (publish_time),
    INDEX idx_category (category),
    INDEX idx_importance (importance)
);

-- 2. 生成内容表
CREATE TABLE generated_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER NOT NULL,
    version TEXT NOT NULL,       -- A/B/C

    -- 小红书内容
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    hashtags TEXT,               -- JSON: ["#AI", "#黑科技"]
    image_prompt TEXT,

    -- 元数据
    model_used TEXT,
    prompt_template TEXT,
    generation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 用户反馈
    is_selected BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    published_platform TEXT,     -- xiaohongshu/friend_circle
    published_time TIMESTAMP,

    FOREIGN KEY (news_id) REFERENCES ai_news(id) ON DELETE CASCADE,
    INDEX idx_news_version (news_id, version)
);

-- 3. 用户偏好表
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'default',
    preference_type TEXT NOT NULL, -- style/length/topic
    preference_value TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_type, preference_value)
);

-- 4. 选择历史表
CREATE TABLE selection_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'default',
    news_id INTEGER,
    content_id INTEGER,
    version TEXT NOT NULL,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (news_id) REFERENCES ai_news(id),
    FOREIGN KEY (content_id) REFERENCES generated_content(id),
    INDEX idx_user_time (user_id, selected_at)
);

-- 5. 爬虫配置表
CREATE TABLE crawler_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    crawl_interval INTEGER DEFAULT 7200, -- 秒
    last_crawl_time TIMESTAMP,
    next_crawl_time TIMESTAMP,
    config_json TEXT,             -- JSON 配置
);

-- 6. 爬虫日志表
CREATE TABLE crawler_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT,                  -- success/error
    items_crawled INTEGER DEFAULT 0,
    error_message TEXT,
    log_details TEXT               -- JSON 详细日志
);
```

---

## 🚀 核心模块实现

### 1. 基础爬虫类 (crawlers/base_crawler.py)

```python
from abc import ABC, abstractmethod
from typing import List, Dict
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, config: Dict):
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def crawl(self) -> List[Dict]:
        """爬取数据，返回资讯列表"""
        pass

    @abstractmethod
    def parse_item(self, raw_data: Dict) -> Dict:
        """解析单条数据"""
        pass

    def save_log(self, status: str, items: int, error: str = None):
        """保存爬虫日志"""
        # 实现日志记录
        pass

    def validate_item(self, item: Dict) -> bool:
        """验证数据有效性"""
        required_fields = ['title', 'source_url', 'publish_time']
        return all(field in item and item[field] for field in required_fields)
```

### 2. RSS 爬虫实现 (crawlers/rss_crawler.py)

```python
import feedparser
from crawlers.base_crawler import BaseCrawler
from typing import List, Dict
from datetime import datetime

class RSSCrawler(BaseCrawler):
    """RSS 订阅爬虫"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.rss_url = config.get('rss_url')

    def crawl(self) -> List[Dict]:
        """爬取 RSS 订阅"""
        logger.info(f"开始爬取 RSS: {self.rss_url}")

        feed = feedparser.parse(self.rss_url)
        items = []

        for entry in feed.entries[:50]:  # 限制 50 条
            try:
                item = self.parse_item(entry)
                if self.validate_item(item):
                    items.append(item)
            except Exception as e:
                logger.error(f"解析 RSS 条目失败: {e}")

        logger.info(f"RSS 爬取完成，共 {len(items)} 条")
        return items

    def parse_item(self, raw_data: Dict) -> Dict:
        """解析 RSS 条目"""
        return {
            'title': raw_data.get('title'),
            'summary': raw_data.get('summary', ''),
            'content': raw_data.get('content', [{}])[0].get('value', ''),
            'source_url': raw_data.get('link'),
            'author': raw_data.get('author', ''),
            'publish_time': self._parse_time(raw_data.get('published')),
            'source': self.config.get('source_name', 'rss')
        }

    def _parse_time(self, time_str: str) -> datetime:
        """解析时间字符串"""
        if not time_str:
            return datetime.now()
        try:
            return datetime.strptime(time_str, '%a, %d %b %Y %H:%M:%S %z')
        except:
            return datetime.now()
```

### 3. AI 服务 (services/ai_service.py)

```python
import openai
import anthropic
from typing import List, Dict
from config.prompts import PROMPT_TEMPLATES

class AIService:
    """AI 服务：分类、摘要、内容生成"""

    def __init__(self, config: Dict):
        self.openai_client = openai.OpenAI(api_key=config.get('openai_key'))
        self.anthropic_client = anthropic.Anthropic(api_key=config.get('anthropic_key'))
        self.model_config = config.get('models', {})

    def classify_news(self, news: Dict) -> Dict:
        """资讯分类"""
        prompt = f"""
        请将以下资讯分类为以下类别之一：
        - product: 新产品发布
        - model: 新模型发布
        - investment: 投融资
        - view: 行业观点

        标题：{news['title']}
        摘要：{news['summary']}

        返回格式：{{"category": "xxx", "confidence": 0.9}}
        """

        response = self.openai_client.chat.completions.create(
            model=self.model_config.get('classify', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result

    def generate_summary(self, news: Dict) -> str:
        """生成摘要"""
        prompt = f"""
        请用 100-200 字总结以下 AI 资讯的核心要点：

        标题：{news['title']}
        内容：{news['content'][:1000]}

        要求：
        1. 提炼核心信息
        2. 简洁明了
        3. 突出亮点
        """

        response = self.anthropic_client.messages.create(
            model=self.model_config.get('summary', 'claude-3-5-sonnet-20241022'),
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def generate_xiaohongshu_content(self, news: Dict, version: str) -> Dict:
        """生成小红书内容"""
        prompt_template = PROMPT_TEMPLATES[version]
        prompt = prompt_template.format(
            title=news['title'],
            summary=news['summary'],
            content=news['content'][:1000]
        )

        model = self.model_config.get('generate', 'claude-3-5-sonnet-20241022')
        if model.startswith('gpt'):
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=1000
            )
            content = response.choices[0].message.content
        else:
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text

        # 解析生成的结构化内容
        return self._parse_generated_content(content)

    def _parse_generated_content(self, content: str) -> Dict:
        """解析生成的内容"""
        lines = content.split('\n')

        title = ''
        body = []
        hashtags = []

        current_section = 'title'
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('【标题】'):
                current_section = 'title'
            elif line.startswith('【正文】'):
                current_section = 'body'
            elif line.startswith('【标签】'):
                current_section = 'hashtags'
            else:
                if current_section == 'title':
                    title = line
                elif current_section == 'body':
                    body.append(line)
                elif current_section == 'hashtags':
                    hashtags.extend(line.split())

        return {
            'title': title,
            'content': '\n'.join(body),
            'hashtags': hashtags
        }
```

### 4. Prompt 模板 (config/prompts.py)

```python
PROMPT_TEMPLATES = {
    'A': """你是一位专业的 AI 领域内容创作者，擅长将复杂的 AI 技术转化为通俗易懂的小红书笔记。

## 任务
基于以下 AI 资讯，生成一篇小红书笔记（硬核技术版）。

## 输入资讯
标题：{title}
摘要：{summary}
核心内容：{content}

## 要求
1. **标题**：包含技术关键词，吸引技术人员
2. **开头**：直接切入技术亮点（3-5字）
3. **正文**：
   - 技术原理简单解释（100字）
   - 应用场景（2-3个）
   - 与竞品对比（如有）
4. **结尾**：技术展望 + 互动提问
5. **标签**：#AI #[技术名] #黑科技

## 风格
- 专业但不晦涩
- 用数据说话
- 适当使用技术术语

## 输出格式
【标题】

【正文】

【标签】
""",

    'B': """你是一位擅长科普的 AI 内容创作者，目标受众是对 AI 感兴趣的大众用户。

## 任务
基于以下 AI 资讯，生成一篇轻松有趣的小红书科普笔记。

## 输入资讯
标题：{title}
摘要：{summary}
核心内容：{content}

## 要求
1. **标题**：制造好奇心，用感叹号
2. **开头**：情绪化表达（哇、绝了）
3. **正文**：
   - 用比喻解释技术（50字）
   - 日常生活应用（2-3个）
   - 为什么值得关注（50字）
4. **结尾**：行动号召（"快去试试"）
5. **标签**：#AI神器 #黑科技 #宝藏发现

## 风格
- 口语化
- 多用表情符号 😱🔥✨💡
- 亲切如朋友聊天

## 输出格式
【标题】

【正文】

【标签】
""",

    'C': """你是一位 AI 行业观察者，擅长捕捉热点并输出观点。

## 任务
基于以下 AI 资讯，生成一篇带观点的小红书笔记。

## 输入资讯
标题：{title}
摘要：{summary}
核心内容：{content}

## 要求
1. **标题**：引发讨论或争议
2. **开头**：抛出观点或问题
3. **正文**：
   - 这件事意味着什么（100字）
   - 对行业的冲击（50字）
   - 我的看法（50字）
4. **结尾**：引导评论（"你怎么看"）
5. **标签**：#AI观察 #[热点] #行业观点

## 风格
- 有观点、有立场
- 引发思考和讨论
- 数据 + 观点结合

## 输出格式
【标题】

【正文】

【标签】
"""
}
```

---

## 🖥️ Streamlit 界面实现

### 主应用 (web/app.py)

```python
import streamlit as st
from services.news_service import NewsService
from services.content_service import ContentService

st.set_page_config(
    page_title="AI 资讯追踪与内容生成",
    page_icon="🤖",
    layout="wide"
)

# 初始化服务
@st.cache_resource
def init_services():
    return {
        'news': NewsService(),
        'content': ContentService()
    }

services = init_services()

# 侧边栏
with st.sidebar:
    st.title("🤖 AI 资讯追踪")
    st.markdown("---")

    # 筛选器
    st.subheader("筛选")
    category = st.selectbox("分类", ["全部", "产品", "模型", "融资", "观点"])
    time_range = st.selectbox("时间", ["全部", "今天", "本周", "本月"])

    # 统计
    st.markdown("---")
    st.subheader("统计")
    stats = services['news'].get_stats()
    st.metric("总资讯", stats['total'])
    st.metric("今日新增", stats['today'])

# 主界面
tab1, tab2, tab3 = st.tabs(["📰 资讯列表", "✍️ 内容生成", "📊 已发布"])

with tab1:
    st.header("AI 资讯列表")

    # 获取资讯
    news_list = services['news'].get_news_list(category=category, time_range=time_range)

    # 展示
    for news in news_list:
        with st.expander(f"**{news['title']}** - {news['source']}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**摘要**: {news['summary']}")
                st.markdown(f"**分类**: {news['category']} | **重要性**: {news['importance']}⭐")
                st.markdown(f"**时间**: {news['publish_time']}")

            with col2:
                if st.button("生成内容", key=f"gen_{news['id']}"):
                    st.session_state['selected_news'] = news
                    st.switch_page("pages/2_✍️_内容生成.py")

                st.markdown(f"[查看原文]({news['source_url']})")

with tab2:
    st.header("小红书内容生成")

    # 检查是否选择了资讯
    if 'selected_news' not in st.session_state:
        st.info("请先在资讯列表中选择要生成内容的资讯")
    else:
        news = st.session_state['selected_news']

        st.subheader(f"基于: {news['title']}")

        # 生成按钮
        if st.button("🚀 生成 3 个版本"):
            with st.spinner("正在生成..."):
                versions = services['content'].generate_three_versions(news)
                st.session_state['generated_versions'] = versions

        # 展示生成的版本
        if 'generated_versions' in st.session_state:
            versions = st.session_state['generated_versions']

            for version_id, version_data in versions.items():
                with st.expander(f"版本 {version_id}: {version_data['title']}", expanded=True):
                    st.markdown(f"**{version_data['title']}**")
                    st.markdown(version_data['content'])
                    st.markdown(f"**标签**: {' '.join(version_data['hashtags'])}")

                    if st.button(f"选择版本 {version_id}", key=f"select_{version_id}"):
                        services['content'].save_selection(news['id'], version_id, version_data)
                        st.success(f"已选择版本 {version_id}!")

with tab3:
    st.header("已发布内容")

    # 获取已发布内容
    published = services['content'].get_published_content()

    for item in published:
        with st.expander(f"**{item['title']}** - {item['published_time']}"):
            st.markdown(item['content'])
            st.markdown(f"**平台**: {item['published_platform']}")
```

---

## 📅 开发时间表

### Week 1-2: 基础搭建
- [x] 项目规划
- [ ] 数据库设计
- [ ] 基础爬虫（RSS）
- [ ] Streamlit 界面原型

### Week 3-4: AI 集成
- [ ] AI 服务集成
- [ ] 分类与摘要功能
- [ ] 小红书内容生成
- [ ] 测试与优化

### Week 5-6: 完善功能
- [ ] 微博爬虫
- [ ] 用户偏好记录
- [ ] 内容管理功能
- [ ] 性能优化

### Week 7-8: 上线准备
- [ ] 部署准备
- [ ] 监控与日志
- [ ] 文档完善
- [ ] 内测与反馈

---

**文档版本**: v1.0
**最后更新**: 2025-01-12
**负责人**: lillianliao
