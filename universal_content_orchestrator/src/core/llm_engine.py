import os
import json
import urllib.request
from typing import List
from src.core.schemas import RawContentEvent

class QwenEngine:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv("/Users/lillianliao/notion_rag/.env")
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")

    def call_qwen(self, prompt: str) -> str:
        data = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        req = urllib.request.Request(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            data=json.dumps(data).encode('utf-8'),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"❌ LLM API 故障: {e}")
            return ""

    def select_top_articles(self, events: List[RawContentEvent], limit: int) -> List[RawContentEvent]:
        """
        AI-driven heuristic filter. Prompts the LLM to select the most relevant events.
        """
        if len(events) <= limit: return events
        
        print(f"🧠 [Brain: Selector] 正在对 {len(events)} 篇底料执行深度 AI 排序，提取 Top {limit}...")
        
        # Build catalogue
        catalogue = ""
        for i, e in enumerate(events):
            catalogue += f"[{i}] {e.title}\\n"
            
        prompt = f"""你是一个顶级的AI科技新闻主编。
这是今天从各种渠道获取的新闻池：
{catalogue}

请根据以下【优先级】帮我挑选出最有价值的 {limit} 篇文章以供发布：
1）硬核模型、产品更新
2）大牛专家讲话和观点
3）vibe coding相关的新的开发技能
4）新的github的项目、工具、技能
5）其他

【输出格式】
只输出逗号分隔的编号组合，绝对不要输出任何其他解释。例如: 0, 4, 7"""
        
        reply = self.call_qwen(prompt)
        
        # Parse logic
        selected_events = []
        try:
            indices = [int(x.strip()) for x in reply.replace('[', '').replace(']', '').split(',') if x.strip().isdigit()]
            for idx in indices[:limit]:
                if 0 <= idx < len(events):
                    selected_events.append(events[idx])
        except Exception as e:
            print("⚠️ 大模型编号解析失败，采用默认截流策略。")
        
        # Fallback if LLM failed to return enough
        if len(selected_events) < limit:
            for e in events:
                if e not in selected_events:
                    selected_events.append(e)
                if len(selected_events) == limit: break
                
        return selected_events

    def synthesize_single_article(self, event: RawContentEvent) -> str:
        print(f"🧠 [Brain: Writer] 正在为【{event.title[:15]}...】生成独立小红书文案...")
        prompt = f"""# 角色设定
请充当专注 AI 产业深度观察的小红书顶级创作者「Lilian聊AI」。

# 今日本条新闻底料：
- 标题：{event.title}
- 内容/链接：{event.content} ({event.url})

# 结构与纪律要求 (CRITICAL)
请为这条新闻写一篇独立的、高爆发力的小红书打卡图文。
1. 第一行必须纯输出标题（用【】符号包裹，反转体，制造悬念，不可超18字）。
2. 第二行必须用一句话点破这条新闻的奇点。
3. 第三行开始正文：
   - 👉 深度解读：用冷峻专业的语气，剖析其为什么在这个优先级类别里重要（它是个硬核产品、还是大牛的真知灼见、还是酷炫的Vibe Coding新技能？）
   - 💡 核心启示：别客套，给从业者一点硬核的危机感或行动建议。
4. 字数必须精简，排版多空行。"""
        
        res = self.call_qwen(prompt)
        if not res:
            return f"【{event.title[:15]}】\\n极客新情报送达。\\n\\n👉 解读:\\n底层通信异常，请阅读原文。\\n\\n💡 启示:\\n保持敏锐。 ({event.url})"
        return res
