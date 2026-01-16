# 新闻源问题分析与解决方案

## 📊 当前问题分析

### 1. 当前数据源

| 数据源 | RSS URL | 类型 | 覆盖范围 | AI相关性 |
|--------|---------|------|----------|----------|
| **36氪** | https://36kr.com/feed | 综合科技 | 创投、互联网、AI | ⭐⭐⭐ (30-50%) |
| **InfoQ** | https://www.infoq.cn/feed | 技术社区 | 编程、架构、AI | ⭐⭐⭐⭐ (70-80%) |
| **TechCrunch** | https://techcrunch.com/feed/ | 国际科技 | 创投、科技、AI | ⭐⭐⭐ (40-60%) |

### 2. 抓取逻辑

```python
# 当前实现（sources/base.py）
class RSSSource(BaseSource):
    async def get_data(self) -> List[Dict[str, Any]]:
        # 1. 解析 RSS Feed
        feed = feedparser.parse(self.rss_url)

        # 2. 获取前50条
        for entry in feed.entries[:50]:
            # 3. 标准化数据
            normalized = self.normalize({...})

        # 4. 返回所有数据（无过滤）
        return results
```

### 3. 为什么有这么多非AI新闻？

#### 原因1: **数据源本身就是综合性的**
- **36氪**: 覆盖所有创业和科技新闻，不限于AI
- - 科技创业公司融资
  - 互联网产品发布
  - 大厂动态（腾讯、阿里等）
  - 新能源、芯片等其他科技

- **TechCrunch**: 国际科技媒体，覆盖范围更广
  - App和产品发布
  - 创投新闻（不限于AI）
  - 科技政策和监管
  - 硬件和设备

#### 原因2: **RSS Feed是全量内容**
- RSS Feed返回该网站的所有新闻
- 没有分类筛选机制
- 即使是InfoQ这种偏技术的，也只有70-80%是AI相关

#### 原因3: **当前过滤只在入库时进行**
```python
# 当前过滤逻辑（tasks/crawler.py）
if not is_ai_related(item['title'], item.get('summary', '')):
    logger.info(f"跳过非AI资讯: {item['title'][:50]}...")
    continue  # 这里确实会过滤
```

但问题是：
1. **已经爬取了** - 浪费带宽和时间
2. **过滤太宽松** - 关键词列表可能不够全面
3. **没有分类过滤** - 没有利用RSS本身的分类信息

## 📈 实际数据测试

### 36氪最新30条内容分析
```
AI相关: ~10条 (33%)
- 智能座舱开始AI变革 ✅
- Agent创业 ✅
- 王小川：百川智能预计2027年启动IPO ✅

非AI: ~20条 (67%)
- 美防长称马斯克旗下AI聊天机器人... ❌ (政治/军事)
- 瑞银首席执行官据悉将于2027年4月卸任 ❌ (商业)
- xTool，下一个「影石」要IPO了？ ❌ (硬件)
- 外骨骼机器人画大饼还是真愿景？ ❌ (硬件/医疗)
```

### InfoQ最新20条内容分析
```
AI相关: ~16条 (80%)
- AI应用榜 ✅
- Claude Code创建者 ✅
- Anthropic深夜放出王炸 ✅
- DeepSeek突发新论文 ✅

非AI: ~4条 (20%)
- 亚马逊云科技推出VPC加密控制 ❌ (云安全)
- MongoBleed漏洞 ❌ (安全)
```

### TechCrunch最新20条内容分析
```
AI相关: ~10条 (50%)
- Deepgram raises $130M ✅ (AI语音)
- Slackbot is an AI agent now ✅
- Meta-backed Hupo finds growth after pivot to AI ✅

非AI: ~10条 (50%)
- Apple launches Creator Studio ❌ (产品)
- Superorganism raises $25M ❌ (生物科技)
- Brazil orders Meta to suspend policy ❌ (政策)
```

## 💡 解决方案

### 方案1: 添加专门的AI数据源 ⭐⭐⭐⭐⭐

#### 推荐数据源

**中文AI媒体**
```python
SOURCES_CONFIG = {
    # === 专门的AI媒体 ===
    "ai-china": {
        "id": "ai-china",
        "name": "新智元",
        "home_url": "https://www.newrank.cn",
        "rss_url": "https://www.newrank.cn/rss/aiNews",
        "enabled": True,
        "category": "AI新闻"
    },

    "quantum-bit": {
        "id": "quantum-bit",
        "name": "量子位",
        "home_url": "https://www.qbitai.com",
        "rss_url": "https://www.qbitai.com/feed",
        "enabled": True,
        "category": "AI新闻"
    },

    "machine-heart": {
        "id": "machine-heart",
        "name": "机器之心",
        "home_url": "https://www.jiqizhixin.com",
        "rss_url": "https://www.jiqizhixin.com/feed",
        "enabled": True,
        "category": "AI新闻"
    },

    "ai-era": {
        "id": "ai-era",
        "name": "AI新榜",
        "home_url": "https://www.ainaera.com",
        "rss_url": "https://www.ainaera.com/rss",
        "enabled": True,
        "category": "AI新闻"
    },
}
```

**英文AI媒体**
```python
# AI 专门媒体
"venturebeat-ai": {
    "id": "venturebeat-ai",
    "name": "VentureBeat AI",
    "home_url": "https://venturebeat.com/ai",
    "rss_url": "https://venturebeat.com/ai/feed/",
    "enabled": True,
    "category": "AI新闻"
},

"the-algorithm": {
    "id": "the-algorithm",
    "name": "The Algorithm",
    "home_url": "https://www.technologyreview.com",
    "rss_url": "https://www.technologyreview.com/feed/",
    "enabled": True,
    "category": "AI新闻"
},
```

**Reddit AI社区**
```python
# Reddit AI 子版块
"reddit-ai": {
    "id": "reddit-ai",
    "name": "Reddit AI",
    "home_url": "https://reddit.com/r/artificial",
    "rss_url": "https://www.reddit.com/r/artificial/.rss",
    "enabled": True,
    "category": "AI社区"
},

"reddit-machinelearning": {
    "id": "reddit-machinelearning",
    "name": "Reddit ML",
    "home_url": "https://reddit.com/r/MachineLearning",
    "rss_url": "https://www.reddit.com/r/MachineLearning/.rss",
    "enabled": True,
    "category": "ML社区"
},
```

### 方案2: 优化AI关键词过滤 ⭐⭐⭐⭐

#### 当前关键词问题
```python
# 当前 keywords (config/prompts.py)
AI_KEYWORDS = [
    'AI', 'GPT', 'ChatGPT', 'Claude', 'Llama',
    # ... 80+ 关键词
]
```

**问题**:
1. 缺少新兴AI术语（如 "Agent", "RAG", "Copilot"）
2. 缺少中文AI术语（如 "大模型", "智能体"）
3. 没有考虑上下文（"AI公司" vs "做AI的公司"）

#### 改进方案

```python
# 改进的关键词列表
AI_KEYWORDS = {
    # === 核心AI术语 ===
    'gpt', 'chatgpt', 'claude', 'llama', 'mistral', 'gemini', 'deepseek',
    'qwen', '文心一言', '通义千问', 'kimi', '豆包', '智谱',

    # === AI技术 ===
    'machine learning', '机器学习', 'deep learning', '深度学习',
    'neural network', '神经网络', 'transformer', 'attention', 'llm', '大语言模型',
    'diffusion model', 'stable diffusion', 'generative ai',

    # === AI应用 ===
    'ai agent', '智能体', 'copilot', 'rag', 'fine-tuning', 'prompt',
    'chatbot', 'conversational ai', 'computer vision', 'nlp',

    # === AI公司 ===
    'openai', 'anthropic', 'google deepmind', 'meta ai', 'microsoft ai',
    '百川智能', '月之暗面', '智谱ai', '零一万物',

    # === AI产品 ===
    'midjourney', 'dall-e', 'sora', 'runway', 'character.ai',
    'perplexity', 'huggingface',

    # === AI行业 ===
    'aigc', 'agi', 'generative', 'foundation model', '基础模型',
    'multimodal', '多模态', 'embodied ai', '具身智能',

    # === 中英文混合 ===
    '人工智能', 'ai模型', 'ai应用', 'ai芯片', 'ai创业',
    'ai公司', 'ai融资', 'ai行业', 'ai工具'
}

def is_ai_related(title: str, summary: str = "") -> bool:
    """
    改进的AI相关性判断

    Args:
        title: 新闻标题
        summary: 新闻摘要

    Returns:
        bool: 是否AI相关
    """
    import re
    from collections import Counter

    text = (title + " " + summary).lower()

    # 1. 精确匹配
    for keyword in AI_KEYWORDS:
        if keyword.lower() in text:
            return True

    # 2. 模式匹配（应对AI相关的模式）
    ai_patterns = [
        r'\bai\b.*\b(model|system|tool|app|startup|company)\b',
        r'\b(machine|deep) learning\b',
        r'\b(neural|transformer|diffusion)\s*(network|model)?\b',
        r'大.*?模型',
        r'智能.*?(体|助手|客服|系统)',
    ]

    for pattern in ai_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # 3. 上下文判断（避免误判）
    # 如果包含AI关键词但明显不是AI新闻，返回False
    negative_keywords = [
        '非ai', '不是ai', '除ai外',
        # 可以添加更多
    ]

    for neg_kw in negative_keywords:
        if neg_kw in text:
            return False

    return False
```

### 方案3: 利用RSS分类信息 ⭐⭐⭐

```python
class RSSSource(BaseSource):
    async def get_data(self) -> List[Dict[str, Any]]:
        feed = feedparser.parse(self.rss_url)

        for entry in feed.entries[:50]:
            # 检查RSS条目的分类标签
            tags = entry.get('tags', [])
            categories = [tag.term.lower() for tag in tags]

            # 如果有明确的非AI分类，跳过
            non_ai_categories = [
                'gaming', 'entertainment', 'politics', 'sports',
                'fashion', 'food', 'travel', 'music', 'movies'
            ]

            if any(cat in categories for cat in non_ai_categories):
                logger.debug(f"跳过非AI分类: {categories}")
                continue

            # 如果有明确的AI分类，优先保留
            ai_categories = [
                'artificial intelligence', 'machine learning', 'ai',
                'deep learning', 'nlp', 'computer vision'
            ]

            if any(cat in categories for cat in ai_categories):
                # 直接保留，不做关键词过滤
                normalized = self.normalize({...})
                results.append(normalized)
                continue

            # 其他情况，使用关键词过滤
            if is_ai_related(entry.get('title', ''), entry.get('summary', '')):
                normalized = self.normalize({...})
                results.append(normalized)
```

### 方案4: 分层过滤策略 ⭐⭐⭐⭐⭐

```python
# 三层过滤策略
def should_crawl_news(title: str, summary: str, categories: List[str]) -> bool:
    """
    三层过滤策略

    第一层: RSS分类过滤（最快）
    第二层: 精确关键词匹配（中等）
    第三层: 模式匹配 + 上下文判断（最慢但最准）
    """

    # 第一层: RSS分类
    if has_explicit_ai_category(categories):
        return True  # 明确AI分类，直接保留

    if has_explicit_non_ai_category(categories):
        return False  # 明确非AI分类，直接跳过

    # 第二层: 精确关键词
    if matches_exact_ai_keywords(title, summary):
        return True

    # 第三层: 模式匹配
    if matches_ai_patterns(title, summary):
        return True

    return False
```

### 方案5: 使用LLM进行智能分类 ⭐⭐⭐⭐⭐

```python
async def intelligent_ai_filter(title: str, summary: str) -> bool:
    """
    使用LLM判断是否AI相关
    成本低（因为调用qwen-turbo，单次<¥0.001）
    """

    prompt = f"""
判断这条新闻是否与AI（人工智能）相关。

标题: {title}
摘要: {summary}

只回答：是 或 否
"""

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )

    try:
        response = client.chat.completions.create(
            model="qwen-turbo",  # 使用最快的模型
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )

        result = response.choices[0].message.content.strip()
        return "是" in result

    except:
        # 失败时回退到关键词匹配
        return is_ai_related(title, summary)
```

## 🎯 推荐实施方案

### 短期（立即实施）
1. ✅ **添加专门的AI数据源**（方案1）
   - 量子位
   - 机器之心
   - Reddit AI
   - VentureBeat AI

2. ✅ **优化关键词过滤**（方案2）
   - 添加新兴AI术语
   - 添加中文AI术语
   - 改进匹配逻辑

### 中期（1周内）
3. ✅ **实现分层过滤**（方案4）
   - RSS分类优先
   - 关键词其次
   - 模式匹配兜底

4. ✅ **添加数据源配置**
   - 可配置每个数据源的权重
   - 可配置过滤策略

### 长期（可选）
5. ⚠️ **LLM智能分类**（方案5）
   - 使用qwen-turbo进行智能判断
   - 成本可控（<¥0.001/次）

## 📊 预期效果

### 实施前
- **36氪**: 33% AI相关
- **InfoQ**: 80% AI相关
- **TechCrunch**: 50% AI相关
- **总体**: ~54% AI相关

### 实施后（添加专门AI媒体）
- **量子位**: 95%+ AI相关 ✅
- **机器之心**: 95%+ AI相关 ✅
- **Reddit AI**: 90%+ AI相关 ✅
- **InfoQ**: 80% AI相关
- **36氪**: 33% AI相关（可选保留）

**新的总体AI相关性**: 85%+ ✅

## 🔧 立即行动

我可以帮你：
1. 添加专门的AI数据源配置
2. 优化关键词列表
3. 实现分层过滤逻辑
4. 运行测试验证效果

需要我立即实施哪个方案？
