# 🚀 AI News Tracker 优化方案

## 📋 需求概述

1. **增加国外优秀AI网站支持**
   - 目标：获取国际前沿AI资讯
   - 覆盖：英文媒体、研究机构、公司博客

2. **Twitter数据获取**
   - 目标：监控关注的AI专家账号
   - 获取第一手资讯和观点

---

## 🌍 Part 1: 国外AI媒体支持

### ✅ 推荐添加的媒体源

根据测试结果，推荐以下媒体：

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

#### 其他备选源

**6. VentureBeat AI**（RSS可能需要修复）
```python
"venturebeat-ai": {
    "id": "venturebeat-ai",
    "name": "VentureBeat AI",
    "home_url": "https://venturebeat.com/ai",
    "rss_url": "https://venturebeat.com/ai/feed/",
    "enabled": False,  # RSS暂时无数据
    "disabled_reason": "RSS解析失败，需要修复URL或使用爬虫",
    "priority": 6,
    "limit": 20,
    "ai_related_rate": 0.85,
    "language": "en"
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

**实施步骤**:

1. **部署RSSHub实例**

```bash
# 方法1: 使用Railway部署
git clone https://github.com/DIYgod/RSSHub.git
cd RSSHub
railway init
railway up

# 方法2: 使用Vercel部署
vercel
```

2. **使用Twitter路由**

获取关注列表的RSS：
```
https://your-rsshub-instance.com/twitter/user/following/:userId
```

获取用户时间线的RSS：
```
https://your-rsshub-instance.com/twitter/user/:userId
```

**3. 集成到项目**

```python
"twitter-rsshub": {
    "id": "twitter-rsshub",
    "name": "Twitter (RSSHub)",
    "home_url": "https://twitter.com",
    "rss_url": "https://your-rsshub-instance.com/twitter/user/following/YOUR_TWITTER_ID",
    "enabled": False,  # 需要配置RSSHub实例
    "disabled_reason": "需要先部署RSSHub实例",
    "category": "社交媒体",
    "priority": 5,
    "limit": 20,
    "ai_related_rate": 0.80,
    "note": "通过RSSHub获取Twitter关注列表"
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
- ⚠️ 需要申请开发者账号
- ⚠️ 有配额限制

**实施步骤**:

1. **申请Twitter开发者账号**
   - 访问 https://developer.twitter.com/
   - 创建应用
   - 获取API Key和Bearer Token

2. **集成Twitter API**

```python
# backend/sources/twitter.py
import tweepy
from typing import List, Dict
from loguru import logger

class TwitterSource:
    """Twitter数据源（使用官方API）"""

    def __init__(self, config: Dict):
        self.bearer_token = config.get('bearer_token')
        self.client = tweepy.Client(bearer_token=self.bearer_token)

    async def get_timeline(self, user_id: str, count: int = 20) -> List[Dict]:
        """获取用户时间线"""
        try:
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=count,
                tweet_fields=['created_at', 'public_metrics', 'text']
            )

            results = []
            for tweet in tweets.data:
                results.append({
                    'title': tweet.text[:100] + '...',
                    'content': tweet.text,
                    'url': f"https://twitter.com/i/web/status/{tweet.id}",
                    'summary': tweet.text[:200],
                    'source': 'Twitter',
                    'publish_time': tweet.created_at,
                    'author': user_id
                })

            return results
        except Exception as e:
            logger.error(f"获取Twitter数据失败: {e}")
            return []

    async def get_following_tweets(self, user_id: str, count: int = 50) -> List[Dict]:
        """获取关注用户的推文（需要Premium API）"""
        # Free Tier不支持此功能
        logger.warning("Free Tier不支持获取关注列表，需要升级到Basic/Premium")
        return []
```

**配置**:

```python
# backend/config/base_config.py
TWITTER_CONFIG = {
    "bearer_token": os.environ.get("TWITTER_BEARER_TOKEN"),
    "user_id": os.environ.get("TWITTER_USER_ID"),  # 你的Twitter用户ID
}
```

**环境变量**:

```env
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_USER_ID=your_numeric_user_id
```

**成本**:
- Free Tier: 免费（500条推文/月）
- Basic Tier: $100/月（10,000条推文/月）

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
            url = f"{instance}/{username}"
            # 使用feedparser解析RSS
            feed = feedparser.parse(f"{url}/rss")
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
1. 更新 `backend/config/base_config.py`
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
2. 配置Twitter路由
3. 获取RSS URL
4. 集成到项目

**预期时间**: 2-3小时

### 阶段3: Twitter - API方案（可选）⭐⭐⭐

**优先级**: ⭐⭐⭐

**原因**:
- 需要申请开发者账号
- Free Tier有配额限制
- 数据质量最高

**实施步骤**:
1. 申请Twitter开发者账号
2. 创建应用获取API Key
3. 实现Twitter API客户端
4. 集成到爬虫

**预期时间**: 4-6小时

---

## 📝 配置文件示例

### 完整的数据源配置

```python
# backend/config/base_config.py

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
        "note": "通过RSSHub获取Twitter关注列表"
    }
}
```

---

## 🎬 实施计划

### 第1周：国际媒体

- [ ] 添加5个国际AI媒体源
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
- [ ] 集成到项目

**预期成果**:
- 可以获取Twitter关注列表
- 实时获取AI专家推文
- 每天更新20-50条

### 第3周：优化和监控

- [ ] 添加数据源监控
- [ ] 实现智能过滤
- [ ] 优化AI相关性判断
- [ ] 性能优化

---

## 💡 技术要点

### 多语言支持

需要修改数据模型支持语言字段：

```python
# backend/models/database.py
class News(Base):
    __tablename__ = "news"

    # ... 现有字段 ...

    language = Column(String(10), default="zh", comment="语言: zh/en")
```

### 翻译功能（可选）

```python
# 可以使用千问API翻译英文新闻
async def translate_to_chinese(content: str) -> str:
    """将英文内容翻译成中文"""
    prompt = f"请将以下英文新闻翻译成中文：\n\n{content}"
    # 调用千问API
    return translated_content
```

### 内容过滤优化

针对Twitter和英文内容，需要更新AI关键词：

```python
# backend/config/prompts.py
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

## ✅ 下一步行动

### 立即可做（今天就完成）

1. **添加国际AI媒体**
   ```bash
   # 编辑配置
   vim backend/config/base_config.py

   # 添加5个国际媒体源

   # 测试
   python -m tasks.crawler

   # 提交
   git add .
   git commit -m "feat: Add international AI media sources"
   git push
   ```

2. **监控效果**
   - 查看数据分布
   - 检查AI相关率
   - 调整limit和优先级

### 本周完成（Twitter）

1. **部署RSSHub**
2. **测试Twitter路由**
3. **集成到项目**

---

**创建时间**: 2026-01-14 17:30
**状态**: ✅ 规划完成，等待实施
**优先级**:
1. 国际媒体（高）⭐⭐⭐⭐⭐
2. Twitter RSSHub（中）⭐⭐⭐⭐
3. Twitter API（低）⭐⭐⭐

**预期工作量**:
- 国际媒体：1小时
- Twitter RSSHub：3-4小时
- Twitter API：4-6小时
