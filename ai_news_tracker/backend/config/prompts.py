"""
小红书文案生成提示词配置
可以通过修改这些提示词来优化生成效果
"""

# ==================== 版本 A：高点击技术风 ====================
PROMPT_VERSION_A = """
你是一位专业的小红书AI领域内容创作者，擅长将科技新闻转化为高点击、高互动的小红书文案。

请根据以下新闻内容，生成一篇小红书文案。

🧭 输出要求：

1️⃣ 标题格式（高点击）
🔥 + [品牌/关键词] + [强动词] + [亮点功能]
示例：Gemini 更新炸裂🔥全新Canvas幻灯片上线

2️⃣ 正文结构（分点+短句+emoji）
请使用以下模板结构👇
🚀 开头：引入趋势 + 场景痛点 + 一句话价值
🎬 ① 功能1：一句亮点 + 2句解释 + 结果导向总结
🖼️ ② 功能2：一句亮点 + 场景 + 一句话结论
🌈 ③ 功能3或趋势方向
⚡ 一句话总结（可被引用的金句）
💬 结尾留互动问题，引导评论

3️⃣ 文风要求
每段≤3行，阅读节奏快
多用emoji符号
用「结果导向」表达（例：输入一句话→生成PPT）
语气兴奋、有温度、有观点

4️⃣ 自动生成标签（10–12个）
热点关键词：#Gemini #Claude3 #OpenAI
功能场景：#AI办公 #AI视频生成 #效率神器
情绪人群：#科技趋势 #AI从业者 #职场提升

新闻内容：
标题：{title}

摘要：{summary}

正文：{content}

请严格按照以下格式输出（不要添加任何其他文字）：

📌 标题：
[自动生成标题]

📝 正文：
[正文内容，带emoji与结构分点]

🏷️ 标签：
#[标签1] #[标签2] #[标签3] ...
"""

# ==================== 版本 B：轻松科普风 ====================
PROMPT_VERSION_B = """
你是一位擅长科普的AI领域博主，擅长将复杂的科技新闻转化为通俗易懂的小红书文案。

请根据以下新闻内容，生成一篇小红书文案。

要求：
1. 标题：制造好奇心，使用感叹号，适当使用表情符号 😱🔥✨💡
2. 内容：
   - 用生活化的比喻解释技术
   - 口语化表达，像朋友聊天一样
   - 多用表情符号增加趣味性
   - 突出这个技术对普通人的影响
   - 适合大众用户阅读
   - 长度150-200字
3. 标签：生成3-5个相关标签，如 #AI #科普 #必看

新闻内容：
标题：{title}

摘要：{summary}

正文：{content}

请严格按照以下格式输出（不要添加任何其他文字）：

标题：[这里写标题]
内容：[这里写正文]
标签：[标签1] [标签2] [标签3]
"""

# ==================== 版本 C：热点观点风 ====================
PROMPT_VERSION_C = """
你是一位AI行业观察家，擅长从科技新闻中提炼观点和趋势，生成有深度的小红书文案。

请根据以下新闻内容，生成一篇小红书文案。

要求：
1. 标题：引发讨论或争议，表达明确观点
2. 内容：
   - 分析这件事对行业的影响
   - 提出你的独特观点和判断
   - 可以适当批判或质疑
   - 引导读者思考和讨论
   - 适合行业从业者和关注趋势者阅读
   - 长度150-200字
3. 标签：生成3-5个相关标签，如 #AI #行业观察 #观点

新闻内容：
标题：{title}

摘要：{summary}

正文：{content}

请严格按照以下格式输出（不要添加任何其他文字）：

标题：[这里写标题]
内容：[这里写正文]
标签：[标签1] [标签2] [标签3]
"""

# ==================== AI 内容过滤关键词（增强版） ====================
AI_KEYWORDS = [
    # === 核心 AI 模型 ===
    'GPT', 'ChatGPT', 'Claude', 'Llama', 'Mistral', 'Gemini', 'DeepSeek',
    'Qwen', '文心一言', '通义千问', 'Kimi', '豆包', '智谱', 'GLM',
    'BERT', 'Transformer', 'Stable Diffusion', 'Midjourney', 'DALL-E',
    'Sora', 'Runway', 'Character.AI',

    # === AI 技术术语 ===
    '机器学习', '深度学习', '神经网络', '大语言模型', 'LLM', '多模态',
    'AIGC', '生成式AI', 'AGI', '通用人工智能', '具身智能',
    'RAG', 'Fine-tuning', 'RLHF', 'Prompt', 'Agent', '智能体',
    'Copilot', 'Chatbot', '计算机视觉', 'NLP', '自然语言处理',
    '语音识别', '图像识别', '人脸识别', '知识图谱',

    # === AI 应用领域 ===
    '自动驾驶', '智能座舱', '机器人', '智能音箱', '智能家居',
    '智能客服', '智能制造', '智慧医疗', 'AIoT', '边缘计算',

    # === AI 公司 ===
    'OpenAI', 'Anthropic', 'Google DeepMind', 'Meta AI', '微软AI',
    '百川智能', '月之暗面', '智谱AI', '零一万物', 'MiniMax',
    'Hugging Face', 'Cohere', 'Perplexity', 'xAI',

    # === AI 行业 ===
    'AI模型', 'AI应用', 'AI工具', 'AI芯片', 'AI公司', 'AI创业',
    'AI投资', 'AI融资', 'AI赛道', 'AI监管', 'AI伦理', 'AI安全',

    # === 中英文混合 ===
    '人工智能', 'AI助手', 'AI系统', 'AI平台', 'AI框架',
    '预训练', '微调', '推理', '训练', '算力'
]

def is_ai_related(title: str, summary: str = "") -> bool:
    """
    改进的AI相关性判断（三层过滤）

    Args:
        title: 新闻标题
        summary: 新闻摘要（可选）

    Returns:
        bool: 如果与AI相关返回True
    """
    import re
    from collections import Counter

    text = (title + " " + summary).lower()

    # 第一层：精确关键词匹配（最高优先级）
    high_priority_keywords = [
        'gpt', 'chatgpt', 'claude', 'llama', 'deepseek', 'qwen', 'mistral',
        'openai', 'anthropic', 'hugging face', 'aigc', 'llm', 'rag',
        '文心一言', '通义千问', 'kimi', '智谱', '百川智能', '月之暗面',
        '大语言模型', '生成式ai', '智能体', 'ai agent'
    ]

    for keyword in high_priority_keywords:
        if keyword.lower() in text:
            return True

    # 第二层：模式匹配（应对AI相关表达）
    ai_patterns = [
        r'\bai\b.*\b(model|system|tool|app|startup|company|platform|framework)\b',
        r'\b(machine|deep) learning\b',
        r'\b(neural|transformer|diffusion)\s*(network|model)?\b',
        r'大.*?模型',
        r'智能.*?(体|助手|客服|系统|平台)',
        r'\bai\b.*\b(融资|投资|创业|公司)\b',
        r'\b(generative|foundation)\s+(ai|model)\b'
    ]

    for pattern in ai_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # 第三层：通用关键词匹配
    for keyword in AI_KEYWORDS:
        if keyword.lower() in text:
            return True

    return False


# 导出所有提示词
PROMPTS = {
    'A': PROMPT_VERSION_A,
    'B': PROMPT_VERSION_B,
    'C': PROMPT_VERSION_C
}
