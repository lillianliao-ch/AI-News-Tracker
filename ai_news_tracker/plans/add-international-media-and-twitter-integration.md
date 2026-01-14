# 🚀 国际AI媒体和Twitter集成优化方案

## 📋 需求概述

### 当前状态
- **数据源数量**: 6个（中文AI媒体为主）
- **语言支持**: 仅中文
- **内容类型**: RSS feeds（AI新闻网站）
- **平均AI相关率**: ~70%

### 用户需求
1. **增加国际优秀AI网站支持**
   - 获取国际前沿AI资讯
   - 覆盖英文媒体、研究机构、公司博客
   - 提升内容质量和多样性

2. **实现Twitter数据获取**
   - 监控关注的AI专家账号
   - 获取第一手资讯和观点
   - 实时跟踪AI领域动态

---

## 📊 现状分析

### 当前架构分析

**数据源配置** ([`backend/config/base_config.py`](../backend/config/base_config.py:55-181)):
```python
SOURCES_CONFIG = {
    "qbitai": {"enabled": True, "limit": 10, "ai_related_rate": 0.95},
    "leiphone": {"enabled": True, "limit": 20, "ai相关率": 0.85},
    "tmtpost": {"enabled": True, "limit": 17, "ai相关率": 1.00},
    "infoq": {"enabled": True, "limit": 20, "ai相关率": 0.80},
    "reddit-ai": {"enabled": True, "limit": 25, "ai相关率": 0.68},
    "36kr-ai": {"enabled": True, "limit": 10, "ai相关率": 0.30}
}
```

**核心组件**:
- **RSSSource类**: [`backend/sources/base.py:84-180`](../backend/sources/base.py:84-180) - RSS feed解析
- **爬虫任务**: [`backend/tasks/crawler.py:24-110`](../backend/tasks/crawler.py:24-110) - 定时爬取
- **数据模型**: [`backend/models/database.py:22-65`](../backend/models/database.py:22-65) - News表结构
- **AI服务**: [`backend/services/ai_service.py`](../backend/services/ai_service.py) - 内容分类和生成

### 当前限制

1. **语言支持**: 仅支持中文内容
2. **数据源类型**: 仅RSS feeds，无社交媒体
3. **国际内容**: 缺少英文AI媒体
4. **实时性**: RSS更新频率有限

---

## 🌍 Part 1: 国际AI媒体支持

### ✅ 推荐添加的媒体源

#### 高质量源（AI相关率100%）

**1. AI News** ⭐⭐⭐⭐⭐
```python
"ai-news": {
    "id": "ai-news",
    "name": "AI News",
    "home_url": "https://artificialintelligence-news.com",
    "rss_url": "https://artificialintelligence-news.com/feed/",
    "enabled": True,
    "category": "国际AI新闻",
    "priority": 10,
    "limit": 12,
    "ai_related_rate": 1.00,  # 100% AI相关！
    "language": "en",
    "note": "专业AI新闻媒体，AI相关率极高"
}
```

**特点**:
- ✅ 100% AI相关内容
- ✅ 12条/次
- ✅ 覆盖研究、应用、政策

#### 高质量源（AI相关率67%）

**2. TechCrunch AI** ⭐⭐⭐⭐
```python
"techcrunch-ai": {
    "id": "techcrunch-ai",
    "name": "TechCrunch AI",
    "home_url": "https://techcrunch.com",
    "rss_url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "enabled": True,
    "category": "AI创投",
    "priority": 8,
    "limit": 20,
    "ai_related_rate": 0.67,
    "language": "en",
    "note": "专注AI初创公司和投资"
}
```

**3. Ars Technica** ⭐⭐⭐⭐
```python
"arstechnica": {
    "id": "arstechnica",
    "name": "Ars Technica",
    "home_url": "https://arstechnica.com",
    "rss_url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "enabled": True,
    "category": "AI技术",
    "priority": 8,
    "limit": 20,
    "ai_related_rate": 0.67,
    "language": "en",
    "note": "深度技术报道"
}
```

#### 中等质量源

**4. MIT Technology Review** ⭐⭐⭐
```python
"mit-tech-review": {
    "id": "mit-tech-review",
    "name": "MIT Tech Review",
    "home_url": "https://www.technologyreview.com",
    "rss_url": "https://www.technologyreview.com/feed/",
    "enabled": True,
    "category": "AI研究",
    "priority": 7,
    "limit": 10,
    "ai_related_rate": 0.33,
    "language": "en",
    "note": "MIT出品，涵盖技术趋势"
}
```

**5. The Verge AI** ⭐⭐⭐
```python
"the-verge-ai": {
    "id": "the-verge-ai",
    "name": "The Verge AI",
    "home_url": "https://www.theverge.com",
    "rss_url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "enabled": True,
    "category": "AI产品",
    "priority": 7,
    "limit": 10,
    "ai_related_rate": 0.33,
    "language": "en",
    "note": "消费科技和AI产品"
}
```

### 📊 预期效果

添加后，数据源分布：

| 类型 | 当前 | 新增后 | 改善 |
|------|------|--------|------|
| 中文AI媒体 | 3个 | 3个 | - |
| 国际AI媒体 | 0个 | 5个 | +5 |
| 社区 | 1个 | 1个 | - |
| **总计** | 4个 | **9个** | +125% |

**AI相关率**:
- 当前平均: ~70%
- 新增后平均: ~75%（国际媒体质量较高）

### 🔧 技术实现

#### 1. 添加语言检测

**文件**: [`backend/sources/base.py`](../backend/sources/base.py)

在 `RSSSource.normalize()` 方法中添加语言检测：

```python
def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """标准化RSS数据，添加语言检测"""
    base_data = super().normalize(raw_data)

    # 添加语言检测
    title = base_data.get('title', '')
    lang_info = self._detect_language(title)

    base_data['language'] = lang_info['lang']
    base_data['lang_confidence'] = lang_info['confidence']

    return base_data

def _detect_language(self, text: str) -> Dict[str, Any]:
    """检测文本语言"""
    if not text:
        return {'lang': 'unknown', 'confidence': 0.0}

    # 快速检测中文字符
    import re
    if re.search(r'[\u4e00-\u9fff]', text):
        return {'lang': 'zh', 'confidence': 0.8}

    # 默认英文
    return {'lang': 'en', 'confidence': 0.7}
```

#### 2. 更新数据模型

**文件**: [`backend/models/database.py`](../backend/models/database.py:22-65)

添加语言字段：

```python
class News(Base):
    __tablename__ = "news"

    # 现有字段...
    language = Column(String(10), default='zh', comment='语言: zh/en')
    lang_confidence = Column(Float, default=0.0, comment='语言检测置信度')
```

#### 3. 更新AI关键词

**文件**: [`backend/config/prompts.py`](../backend/config/prompts.py)

添加英文AI关键词：

```python
AI_KEYWORDS_EN = [
    'GPT', 'ChatGPT', 'Claude', 'Anthropic', 'OpenAI',
    'LLM', 'RAG', 'Fine-tuning', 'Transformer',
    'Stable Diffusion', 'Midjourney', 'DALL-E',
    'DeepMind', 'Google DeepMind', 'Meta AI',
    'artificial intelligence', 'machine learning',
    'deep learning', 'neural network'
]

def is_ai_related_international(title: str, summary: str = "",
                               language: str = "en") -> bool:
    """国际AI相关性检测"""
    text = (title + " " + summary).lower()

    if language == 'zh':
        keywords = AI_KEYWORDS_ZH  # 现有中文关键词
    else:  # language == 'en'
        keywords = AI_KEYWORDS_EN

    return any(kw.lower() in text for kw in keywords)
```

#### 4. 更新API接口

**文件**: [`backend/main.py`](../backend/main.py:133-167)

添加语言筛选：

```python
@app.get("/api/news", response_model=List[NewsItem])
async def get_news(
    category: Optional[str] = None,
    source: Optional[str] = None,
    language: Optional[str] = None,  # 新增：语言筛选
    limit: int = 50,
    offset: int = 0
):
    """获取资讯列表（支持语言筛选）"""
    db = SessionLocal()
    try:
        query = db.query(News)

        # 现有筛选
        if category:
            query = query.filter(News.category == category)
        if source:
            query = query.filter(News.source == source)

        # 新增：语言筛选
        if language:
            query = query.filter(News.language == language)

        # 排序和分页
        query = query.order_by(News.publish_time.desc())
        query = query.offset(offset).limit(limit)

        return query.all()
    finally:
        db.close()
```

### 📝 实施步骤

**阶段1: 配置更新** (30分钟)
1. ✅ 更新 `backend/config/base_config.py` - 添加5个国际媒体源
2. ✅ 更新 `backend/models/database.py` - 添加language字段
3. ✅ 更新 `backend/sources/base.py` - 添加语言检测
4. ✅ 更新 `backend/config/prompts.py` - 添加英文AI关键词
5. ✅ 更新 `backend/main.py` - 添加语言筛选API

**阶段2: 测试验证** (30分钟)
1. ✅ 运行爬虫: `python -m backend.tasks.crawler`
2. ✅ 检查数据: 验证language字段正确
3. ✅ 测试API: `curl "http://localhost:8000/api/news?language=en"`
4. ✅ 调整limit和优先级

**阶段3: 部署上线** (10分钟)
1. ✅ 提交代码: `git add . && git commit -m "feat: Add international AI media sources"`
2. ✅ 推送GitHub: `git push`
3. ✅ Railway自动重新部署

---

## 🐦 Part 2: Twitter数据获取方案

### 方案对比

#### 方案A: RSSHub（推荐个人使用）⭐⭐⭐⭐⭐

**优点**:
- ✅ 完全免费
- ✅ 无需Twitter API
- ✅ 开源，可自建
- ✅ 支持多种路由

**缺点**:
- ⚠️ 需要部署RSSHub实例
- ⚠️ 更新频率限制（通常15分钟）
- ⚠️ 认证token需要定期更新

**实施步骤**:

**1. 部署RSSHub实例**

使用Railway一键部署：

```bash
# 方法1: 使用Railway部署（推荐）
npm install -g @railway/cli
railway login
railway init
# 选择 Docker 镜像: DIYgod/RSSHub
railway up
```

或访问 [RSSHub on Railway](https://railway.app/new/template/DIYgod/RSSHub)

**2. 使用Twitter路由**

获取用户时间线的RSS：

```
https://your-rsshub-instance.com/twitter/user/:username
```

示例：
```
https://your-rsshub.railway.app/twitter/user/elonmusk?readable=1&includeReplies=0&count=50
```

**3. 集成到项目**

创建新的Twitter源类：

**文件**: `backend/sources/twitter_rsshub.py`

```python
import feedparser
import requests
from typing import List, Dict, Any
from loguru import logger

class TwitterRSSHubSource:
    """Twitter数据源（通过RSSHub）"""

    def __init__(self, config: Dict):
        self.username = config.get('username')
        self.rsshub_url = config.get('rsshub_url',
                                    'https://rsshub.app')
        self.enabled = config.get('enabled', False)
        self.name = f"Twitter (@{self.username})"

    async def get_data(self) -> List[Dict[str, Any]]:
        """获取Twitter用户时间线"""
        if not self.enabled:
            logger.warning(f"Twitter source {self.name} is disabled")
            return []

        url = f"{self.rsshub_url}/twitter/user/{self.username}"
        params = {
            'readable': '1',
            'includeReplies': '0',
            'count': '50'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            results = []
            for entry in feed.entries:
                # 标准化为统一格式
                results.append({
                    'title': entry.get('title', '')[:100],
                    'summary': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'source': self.name,
                    'source_url': f"https://twitter.com/{self.username}",
                    'category': '社交媒体',
                    'icon': '/icons/twitter.png',
                    'publish_time': entry.get('published_parsed'),
                    'language': 'en'
                })

            logger.info(f"Twitter ({self.name}): 获取到 {len(results)} 条推文")
            return results

        except Exception as e:
            logger.error(f"获取Twitter数据失败 ({self.name}): {e}")
            return []
```

**4. 配置Twitter源**

**文件**: `backend/config/base_config.py`

```python
"twitter-rsshub": {
    "id": "twitter-rsshub",
    "name": "Twitter",
    "home_url": "https://twitter.com",
    "rss_url": "",  # Twitter使用特殊处理
    "enabled": False,  # 需要先部署RSSHub
    "disabled_reason": "需要先部署RSSHub实例",
    "category": "社交媒体",
    "priority": 5,
    "limit": 20,
    "ai_related_rate": 0.80,
    "language": "en",
    "note": "通过RSSHub获取Twitter关注列表",
    "type": "twitter_rsshub",  # 新类型
    "username": "elonmusk",  # 示例用户名
    "rsshub_url": os.environ.get("TWITTER_RSSHUB_URL", "https://rsshub.app")
}
```

**成本**:
- Railway/Vercel免费额度足够
- 或自己的服务器：$5/月

#### 方案B: Twitter API Free Tier（推荐测试）⭐⭐⭐⭐

**优点**:
- ✅ 官方支持
- ✅ 数据完整
- ✅ 免费额度：每月500条推文

**缺点**:
- ⚠️ **Free Tier仅支持写操作，无读权限**
- ⚠️ 需要申请开发者账号
- ⚠️ Basic Tier: $100/月才有读权限

**实施步骤**:

**1. 申请Twitter开发者账号**

- 访问 https://developer.twitter.com/
- 创建应用
- 获取API Key和Bearer Token

**2. 安装Tweepy**

```bash
pip install tweepy
```

**3. 集成Twitter API**

**文件**: `backend/sources/twitter_api.py`

```python
import tweepy
from typing import List, Dict
from loguru import logger

class TwitterAPISource:
    """Twitter数据源（使用官方API）"""

    def __init__(self, config: Dict):
        self.bearer_token = config.get('bearer_token')
        self.username = config.get('username')
        self.client = tweepy.Client(bearer_token=self.bearer_token)

    async def get_timeline(self, count: int = 20) -> List[Dict]:
        """获取用户时间线"""
        try:
            # 获取用户ID
            user = self.client.get_user(username=self.username)
            if not user.data:
                logger.error(f"Twitter用户 {self.username} 不存在")
                return []

            user_id = user.data.id

            # 获取推文
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=count,
                tweet_fields=['created_at', 'public_metrics', 'text'],
                exclude=['retweets', 'replies']
            )

            results = []
            for tweet in tweets.data or []:
                results.append({
                    'title': tweet.text[:100] + '...',
                    'summary': tweet.text,
                    'content': tweet.text,
                    'url': f"https://twitter.com/{self.username}/status/{tweet.id}",
                    'source': f"Twitter (@{self.username})",
                    'source_url': f"https://twitter.com/{self.username}",
                    'category': '社交媒体',
                    'publish_time': tweet.created_at,
                    'language': 'en',
                    'metrics': {
                        'retweets': tweet.public_metrics['retweet_count'],
                        'likes': tweet.public_metrics['like_count']
                    }
                })

            return results

        except tweepy.Errors.TooManyRequests:
            logger.error("Twitter API rate limit exceeded")
            return []
        except Exception as e:
            logger.error(f"获取Twitter数据失败: {e}")
            return []
```

**配置**:

```python
# backend/config/base_config.py
TWITTER_CONFIG = {
    "bearer_token": os.environ.get("TWITTER_BEARER_TOKEN"),
    "username": os.environ.get("TWITTER_USERNAME", "elonmusk")
}
```

**环境变量**:

```env
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_USERNAME=elonmusk
```

**成本**:
- Free Tier: 免费（仅写操作）
- Basic Tier: $100/月（10,000条推文/月，读操作）
- Pro Tier: $5,000/月（1,000,000条推文/月）

#### 方案C: Nitter公共实例（最简单）⭐⭐⭐

**优点**:
- ✅ 完全免费
- ✅ 无需申请
- ✅ 简单快速

**缺点**:
- ⚠️ 公共实例不稳定
- ⚠️ 容易被封
- ⚠️ 数据可能不完整

**实施**:

```python
# 使用Nitter公共实例
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net"
]

async def fetch_nitter_timeline(username: str) -> List[Dict]:
    """从Nitter实例获取用户时间线"""
    for instance in NITTER_INSTANCES:
        try:
            url = f"{instance}/{username}/rss"
            # 使用feedparser解析RSS
            feed = feedparser.parse(url)
            if feed.entries:
                return parse_nitter_entries(feed.entries)
        except:
            continue
    return []
```

**成本**: 完全免费

---

## 🎯 推荐实施方案

### 阶段1: 国际媒体（优先，立即可做）✅

**优先级**: ⭐⭐⭐⭐⭐

**原因**:
- 简单直接，只需添加RSS配置
- 无需额外服务
- 立即生效

**实施步骤**:
1. 更新 [`backend/config/base_config.py`](../backend/config/base_config.py)
2. 添加5个国际媒体源
3. 测试爬取
4. 重新部署

**预期时间**: 30分钟

### 阶段2: Twitter - RSSHub方案（推荐）⭐⭐⭐⭐

**优先级**: ⭐⭐⭐⭐

**原因**:
- 免费、稳定、可靠
- 可自建，无第三方依赖
- 社区支持好

**实施步骤**:
1. 在Railway部署RSSHub
2. 测试Twitter路由
3. 获取RSS URL
4. 集成到项目

**预期时间**: 2-3小时

### 阶段3: Twitter - API方案（可选）⭐⭐⭐

**优先级**: ⭐⭐⭐

**原因**:
- 需要申请开发者账号
- Free Tier有配额限制
- Basic Tier成本较高（$100/月）
- 数据质量最高

**实施步骤**:
1. 申请Twitter开发者账号
2. 创建应用获取API Key
3. 实现Twitter API客户端
4. 集成到爬虫

**预期时间**: 4-6小时

---

## 📝 完整配置示例

### 数据源配置

**文件**: `backend/config/base_config.py`

```python
SOURCES_CONFIG = {
    # === 中文AI媒体 ===
    "qbitai": {
        "id": "qbitai",
        "name": "量子位",
        "home_url": "https://www.qbitai.com",
        "rss_url": "https://www.qbitai.com/feed",
        "enabled": True,
        "category": "AI新闻",
        "priority": 10,
        "limit": 10,
        "ai_related_rate": 0.95,
        "language": "zh"
    },

    "leiphone": {
        "id": "leiphone",
        "name": "雷锋网",
        "home_url": "https://www.leiphone.com",
        "rss_url": "https://www.leiphone.com/feed",
        "enabled": True,
        "category": "AI技术",
        "priority": 9,
        "limit": 20,
        "ai_related_rate": 0.85,
        "language": "zh"
    },

    "tmtpost": {
        "id": "tmtpost",
        "name": "钛媒体",
        "home_url": "https://www.tmtpost.com",
        "rss_url": "https://www.tmtpost.com/rss",
        "enabled": True,
        "category": "AI商业",
        "priority": 8,
        "limit": 17,
        "ai_related_rate": 1.00,
        "language": "zh"
    },

    # === 国际AI媒体 ===
    "ai-news": {
        "id": "ai-news",
        "name": "AI News",
        "home_url": "https://artificialintelligence-news.com",
        "rss_url": "https://artificialintelligence-news.com/feed/",
        "enabled": True,
        "category": "国际AI新闻",
        "priority": 10,
        "limit": 12,
        "ai_related_rate": 1.00,
        "language": "en",
        "note": "专业AI新闻媒体"
    },

    "techcrunch-ai": {
        "id": "techcrunch-ai",
        "name": "TechCrunch AI",
        "home_url": "https://techcrunch.com",
        "rss_url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "enabled": True,
        "category": "AI创投",
        "priority": 8,
        "limit": 20,
        "ai_related_rate": 0.67,
        "language": "en"
    },

    "arstechnica": {
        "id": "arstechnica",
        "name": "Ars Technica",
        "home_url": "https://arstechnica.com",
        "rss_url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "enabled": True,
        "category": "AI技术",
        "priority": 8,
        "limit": 20,
        "ai_related_rate": 0.67,
        "language": "en"
    },

    "mit-tech-review": {
        "id": "mit-tech-review",
        "name": "MIT Tech Review",
        "home_url": "https://www.technologyreview.com",
        "rss_url": "https://www.technologyreview.com/feed/",
        "enabled": True,
        "category": "AI研究",
        "priority": 7,
        "limit": 10,
        "ai_related_rate": 0.33,
        "language": "en"
    },

    "the-verge-ai": {
        "id": "the-verge-ai",
        "name": "The Verge AI",
        "home_url": "https://www.theverge.com",
        "rss_url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "enabled": True,
        "category": "AI产品",
        "priority": 7,
        "limit": 10,
        "ai_related_rate": 0.33,
        "language": "en"
    },

    # === 社区 ===
    "reddit-ai": {
        "id": "reddit-ai",
        "name": "Reddit AI",
        "home_url": "https://reddit.com/r/artificial",
        "rss_url": "https://www.reddit.com/r/artificial/.rss",
        "enabled": True,
        "category": "AI社区",
        "priority": 6,
        "limit": 25,
        "ai_related_rate": 0.68,
        "language": "en"
    },

    # === Twitter（可选） ===
    "twitter-rsshub": {
        "id": "twitter-rsshub",
        "name": "Twitter",
        "home_url": "https://twitter.com",
        "rss_url": os.environ.get("TWITTER_RSSHUB_URL", ""),
        "enabled": False,  # 需要配置RSSHub实例
        "disabled_reason": "需要先部署RSSHub并配置环境变量",
        "category": "社交媒体",
        "priority": 5,
        "limit": 20,
        "ai_related_rate": 0.80,
        "language": "en",
        "note": "通过RSSHub获取Twitter关注列表",
        "type": "twitter_rsshub"
    }
}
```

---

## 💡 技术要点

### 多语言支持

需要修改数据模型支持语言字段：

**文件**: `backend/models/database.py`

```python
class News(Base):
    __tablename__ = "news"

    # ... 现有字段 ...

    language = Column(String(10), default="zh", comment="语言: zh/en")
    lang_confidence = Column(Float, default=0.0, comment="语言检测置信度")
```

### 翻译功能（可选）

可以添加按需翻译功能：

```python
# backend/services/translation_service.py
async def translate_to_chinese(content: str) -> str:
    """将英文内容翻译成中文（按需）"""
    prompt = f"请将以下英文新闻翻译成中文：\n\n{content}"

    # 调用千问API
    from services.ai_service import AIService
    ai_service = AIService()

    response = await ai_service.client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

### 内容过滤优化

针对Twitter和英文内容，需要更新AI关键词：

**文件**: `backend/config/prompts.py`

```python
AI_KEYWORDS_EN = [
    'GPT', 'ChatGPT', 'Claude', 'Anthropic', 'OpenAI',
    'LLM', 'RAG', 'Fine-tuning', 'Transformer',
    'Stable Diffusion', 'Midjourney', 'DALL-E',
    'DeepMind', 'Google DeepMind', 'Meta AI',
    # ... 更多英文关键词
]
```

---

## 📊 预期效果

### 数据源分布（优化后）

```
中文AI媒体:     ████████████ 33% (3个)
国际AI媒体:     ████████████ 33% (5个)
社区:           ████████░░░ 22% (2个)
Twitter:       ████░░░░░░░░ 11% (1个，可选)
```

### 内容质量

| 指标 | 当前 | 优化后 | 改善 |
|------|------|--------|------|
| 数据源数量 | 4个 | 9-10个 | +125% |
| AI相关率 | ~70% | ~80% | +10% |
| 国际内容占比 | 0% | 30-40% | +30% |
| 更新频率 | 2小时 | 1小时 | 2倍 |

---

## ✅ 实施计划

### 第1周：国际媒体

- [ ] 添加5个国际AI媒体源
- [ ] 实现语言检测功能
- [ ] 更新数据模型添加language字段
- [ ] 测试爬取效果
- [ ] 调整limit和优先级
- [ ] 部署到生产环境

**预期成果**:
- 数据源从4个增加到9个
- 国际资讯占比提升到30%+
- AI相关率提升到75%+

### 第2周：Twitter（RSSHub）

- [ ] 部署RSSHub到Railway
- [ ] 测试Twitter路由
- [ ] 获取RSS URL
- [ ] 实现TwitterRSSHubSource类
- [ ] 集成到爬虫任务
- [ ] 测试和监控

**预期成果**:
- 可以获取Twitter关注列表
- 实时获取AI专家推文
- 每天更新20-50条

### 第3周：优化和监控

- [ ] 添加数据源监控
- [ ] 实现智能过滤
- [ ] 优化AI相关性判断
- [ ] 性能优化
- [ ] 文档更新

---

## 🔧 配置文件更新

### 环境变量

**文件**: `.env.railway.example`

```env
# ==================== Twitter RSSHub配置 ====================
# 可选：如果部署了RSSHub实例
TWITTER_RSSHUB_URL=https://your-rsshub-instance.railway.app
TWITTER_USERNAME=your_twitter_username

# ==================== Twitter API配置（可选）====================
# 如果使用官方Twitter API（Basic Tier: $100/月）
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

---

## 📚 参考资料

### 国际AI媒体列表
- [AI News](https://artificialintelligence-news.com/)
- [TechCrunch AI](https://techcrunch.com/category/artificial-intelligence/)
- [Ars Technica](https://arstechnica.com/)
- [MIT Technology Review](https://www.technologyreview.com/)
- [The Verge AI](https://www.theverge.com/ai-artificial-intelligence)

### RSSHub相关
- [RSSHub GitHub](https://github.com/DIYgod/RSSHub)
- [RSSHub on Railway](https://railway.app/new/template/DIYgod/RSSHub)
- [Twitter路由文档](https://docs.rsshub.app/routes/social-media)

### Twitter API相关
- [Twitter API v2文档](https://developer.twitter.com/en/docs/twitter-api)
- [Tweepy文档](https://docs.tweepy.org/)
- [Rate Limits](https://developer.twitter.com/en/docs/twitter-api/rate-limits)

---

**创建时间**: 2026-01-14 20:05
**状态**: ✅ 规划完成，等待实施
**优先级**:
1. 国际媒体（高）⭐⭐⭐⭐⭐
2. Twitter RSSHub（中）⭐⭐⭐⭐
3. Twitter API（低）⭐⭐⭐

**预期工作量**:
- 国际媒体：1小时
- Twitter RSSHub：3-4小时
- Twitter API：4-6小时
