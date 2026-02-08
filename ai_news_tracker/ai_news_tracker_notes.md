# AI 资讯追踪系统 - 研究笔记

## 📌 MediaCrawler 项目分析

### 核心优势
1. **配置驱动**: 所有行为通过 `config/base_config.py` 控制
2. **模块化设计**: 每个平台独立模块，易于扩展
3. **无需 JS 逆向**: 通过保存浏览器登录态获取签名
4. **多存储支持**: CSV/JSON/Excel/SQLite/MySQL
5. **WebUI 支持**: 可视化操作界面

### 可复用的设计模式
```python
# 配置模式
config = {
    'platform': 'xhs',
    'login_type': 'qrcode',
    'crawl_type': 'search'
}

# 爬虫模式
crawler = MediaCrawler(config)
crawler.start()

# 数据存储模式
storage = Storage(config)
storage.save(data)
```

### 适配我们的需求
```python
# AI 资讯爬虫配置
config = {
    'platforms': ['weibo', 'zhihu', 'xhs'],
    'keywords': ['AI', '大模型', 'GPT', 'ChatGPT'],
    'login_type': 'cookie',
    'storage': 'sqlite'
}
```

---

## 📌 小红书内容风格分析

### 成功案例特征

#### 1. 标题特征
- ✅ 使用数字："5个AI工具让你的效率翻倍"
- ✅ 制造悬念："这个AI功能太炸了！"
- ✅ 情绪化词汇："绝了"、"哭死"、"必冲"
- ✅ 热点关键词："GPT-5"、"OpenAI"、"AGI"

#### 2. 正文结构
```
【开头】吸引注意（3-5字）
    ↓
【核心内容】干货/观点（200-500字）
    ↓
【总结】行动号召（"快去试"、"关注我"）
    ↓
【标签】#AI #ChatGPT #黑科技
```

#### 3. 视觉元素
- 表情符号：😱🔥✨💡
- 空行分段：提高可读性
- 关键信息加粗：用【】突出
- 配图要求：首图吸睛 + 内容配图

---

## 📌 技术选型调研

### AI 服务对比

| 服务 | 优势 | 劣势 | 成本 | 推荐度 |
|------|------|------|------|--------|
| **GPT-4o** | 理解强、中文好 | 贵 | $5/1M tokens | ⭐⭐⭐⭐⭐ |
| **Claude 3.5** | 写作强、逻辑好 | 慢 | $3/1M tokens | ⭐⭐⭐⭐⭐ |
| **DeepSeek-V3** | 便宜、中文好 | 不稳定 | ¥1/1M tokens | ⭐⭐⭐⭐ |
| **文心一言** | 本土化 | 理解弱 | 按次计费 | ⭐⭐⭐ |

**推荐组合**：
- 资讯摘要：DeepSeek（便宜）
- 内容生成：Claude 3.5（质量）
- 标签生成：GPT-4o（准确）

### 前端框架对比

| 框架 | 优势 | 劣势 | 开发速度 | 推荐度 |
|------|------|------|----------|--------|
| **Streamlit** | 极快、纯Python | 定制受限 | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ |
| **Vue.js** | 灵活、美观 | 学习曲线 | ⚡⚡ | ⭐⭐⭐⭐ |
| **React** | 生态好 | 复杂 | ⚡⚡ | ⭐⭐⭐ |

**推荐**：MVP 用 Streamlit，后期重构为 Vue.js

---

## 📌 数据源调研

### 免费数据源
1. **微博**
   - AI 大V：量子位、机器之心、新智元
   - 官方账号：OpenAI、 Anthropic
   - 爬取难度：⭐⭐

2. **知乎**
   - AI 话题讨论
   - 专栏文章
   - 爬取难度：⭐⭐⭐

3. **36氪**
   - 科技新闻 RSS
   - AI 投融资
   - 爬取难度：⭐

4. **InfoQ**
   - 技术文章
   - RSS 订阅
   - 爬取难度：⭐

### 付费数据源（可选）
1. **虎嗅网** - VIP 内容
2. **晚点LatePost** - 深度报道
3. **AI研习社** - 专业社区

---

## 📌 竞品分析

### 1. 机器之心（jiqizhixin.com）
- **优势**: 内容专业、更新快
- **不足**: 无个性化推荐
- **可借鉴**: 分类体系、标签系统

### 2. 量子位（QbitAI）
- **优势**: 科研导向、深度报道
- **不足**: 界面传统
- **可借鉴**: 快讯模式

### 3. 新智元
- **优势**: 覆盖全面、翻译快
- **不足**: 内容质量不稳定
- **可借鉴**: 热点追踪

---

## 📌 Prompt 工程模板

### 小红书内容生成 Prompt（版本A - 硬核技术）

```markdown
你是一位专业的 AI 领域内容创作者，擅长将复杂的 AI 技术转化为通俗易懂的小红书笔记。

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
```text
【标题】

【正文】

【标签】
```
```

### 小红书内容生成 Prompt（版本B - 轻松科普）

```markdown
你是一位擅长科普的 AI 内容创作者，目标受众是对 AI 感兴趣的大众用户。

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
- 多用表情符号
- 亲切如朋友聊天

## 输出格式
```text
【标题】

【正文】

【标签】
```
```

### 小红书内容生成 Prompt（版本C - 热点观点）

```markdown
你是一位 AI 行业观察者，擅长捕捉热点并输出观点。

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
```text
【标题】

【正文】

【标签】
```
```

---

## 📌 用户偏好学习策略

### 冷启动策略
1. **默认偏好**：首次使用提供 3 种风格均衡混合
2. **引导选择**：主动询问用户偏好
3. **快速反馈**：每次选择后立即确认

### 偏好维度
1. **内容风格**：技术/科普/观点
2. **内容长度**：短(200字)/中(500字)/长(800字)
3. **话题偏好**：模型/应用/融资/技术
4. **发布时间**：早晨/中午/晚上/周末

### 学习算法
```python
def calculate_preference_score(user_history, content_features):
    """
    计算内容与用户偏好的匹配度

    Args:
        user_history: 用户历史选择
        content_features: 内容特征向量

    Returns:
        float: 匹配分数 0-1
    """
    # 1. 风格匹配（权重 0.4）
    style_score = match_style(user_history.style, content_features.style)

    # 2. 话题匹配（权重 0.3）
    topic_score = match_topic(user_history.topics, content_features.topic)

    # 3. 时效性匹配（权重 0.2）
    time_score = match_time(user_history.active_hours, content_features.publish_time)

    # 4. 新鲜度匹配（权重 0.1）
    novelty_score = calculate_novelty(user_history.viewed_topics, content_features.topic)

    return 0.4*style_score + 0.3*topic_score + 0.2*time_score + 0.1*novelty_score
```

---

## 📌 技术难点记录

### 难点 1: 资讯去重
**问题**: 同一新闻在不同平台重复
**解决方案**:
```python
def is_duplicate(news1, news2):
    # 1. 标题相似度
    title_sim = calculate_tfidf_similarity(news1.title, news2.title)

    # 2. 发布时间接近（24小时内）
    time_close = abs(news1.time - news2.time) < 86400

    # 3. URL 相似度（域名）
    url_sim = extract_domain(news1.url) == extract_domain(news2.url)

    return title_sim > 0.8 and time_close
```

### 难点 2: 内容生成质量控制
**问题**: AI 生成内容质量不稳定
**解决方案**:
- Prompt 优化：Few-shot learning
- 人工审核：草稿需确认
- 用户反馈：记录并优化
- A/B 测试：对比不同 Prompt 效果

### 难点 3: 实时性 vs 成本
**问题**: 实时爬取和 AI 生成都需要成本
**解决方案**:
- 定时任务：每小时爬取一次
- 增量更新：只爬取新内容
- 缓存策略：热门内容缓存
- 批量处理：降低 API 调用次数

---

## 📌 开发资源

### 学习资源
1. **MediaCrawler 源码**: https://github.com/NanmiCoder/MediaCrawler
2. **Prompt 工程**: https://www.promptingguide.ai/
3. **Streamlit 文档**: https://docs.streamlit.io/
4. **ChromaDB 文档**: https://docs.trychroma.com/

### 开源项目参考
1. **FastGPT**: 低代码 LLM 应用开发平台
2. **Dify**: LLMOps 平台
3. **Langchain**: LLM 应用框架

---

**更新时间**: 2025-01-12
**维护者**: lillianliao
