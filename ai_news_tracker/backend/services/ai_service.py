"""
AI 服务 - 分类、摘要、内容生成
"""
import json
from typing import Dict, List
from openai import OpenAI
from anthropic import Anthropic
from loguru import logger
from config.base_config import settings
from config.prompts import PROMPTS, is_ai_related

class AIService:
    """AI 服务"""

    def __init__(self):
        # 初始化 OpenAI 客户端（支持千问等兼容接口）
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
        else:
            self.openai_client = None

        # 初始化 Anthropic 客户端
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

    async def classify_news(self, news: Dict) -> Dict:
        """
        资讯分类

        Args:
            news: 资讯数据

        Returns:
            分类结果: {"category": "xxx", "confidence": 0.9, "tags": ["tag1", "tag2"]}
        """
        if not self.openai_client:
            return self._default_classify(news)

        prompt = f"""
请将以下 AI 资讯分类为以下类别之一：
- product: 新产品发布（工具、应用、平台）
- model: 新模型发布（开源、闭源、学术）
- investment: 投融资（融资、收购、IPO）
- view: 行业观点（评论、分析、观点）
- research: 学术论文（研究、实验、发布）
- application: AI应用（落地案例、应用场景）

标题：{news['title']}
摘要：{news['summary']}

返回JSON格式（不要其他文字）：
{{"category": "xxx", "confidence": 0.9, "tags": ["tag1", "tag2"], "reasoning": "分类原因"}}
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=settings.CLASSIFY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"分类成功: {news['title'][:30]}... -> {result['category']}")
            return result

        except Exception as e:
            logger.error(f"分类失败: {e}")
            return self._default_classify(news)

    def _default_classify(self, news: Dict) -> Dict:
        """默认分类（失败时的后备方案）"""
        title_lower = news['title'].lower()
        summary_lower = news['summary'].lower()

        # 基于关键词的简单分类
        if any(kw in title_lower for kw in ['融资', '投资', 'ipo', '收购', '亿美元', '亿人民币']):
            return {"category": "investment", "confidence": 0.6, "tags": [], "reasoning": "关键词匹配"}

        if any(kw in title_lower for kw in ['模型', 'gpt', 'llm', '开源', '发布']):
            return {"category": "model", "confidence": 0.6, "tags": [], "reasoning": "关键词匹配"}

        if any(kw in title_lower for kw in ['发布', '推出', '上线', '工具', '平台']):
            return {"category": "product", "confidence": 0.6, "tags": [], "reasoning": "关键词匹配"}

        return {"category": "view", "confidence": 0.4, "tags": [], "reasoning": "默认分类"}

    async def generate_summary(self, news: Dict) -> str:
        """
        生成摘要

        Args:
            news: 资讯数据

        Returns:
            摘要文本
        """
        if not self.anthropic_client:
            return news.get('summary', '')[:200]

        prompt = f"""
请用 100-200 字总结以下 AI 资讯的核心要点：

标题：{news['title']}
摘要：{news['summary'][:500]}

要求：
1. 提炼核心信息（50字）
2. 简洁明了
3. 突出亮点
4. 保持客观
"""

        try:
            response = self.anthropic_client.messages.create(
                model=settings.SUMMARY_MODEL,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text
            logger.info(f"摘要生成成功: {news['title'][:30]}...")
            return summary

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return news.get('summary', '')[:200]

    async def generate_xiaohongshu_content(self, news: Dict, version: str) -> Dict:
        """
        生成小红书内容

        Args:
            news: 资讯数据
            version: 版本 (A/B/C)

        Returns:
            生成内容: {title, content, hashtags, image_prompt}
        """
        prompt = self._get_prompt_template(version, news)

        try:
            # 优先使用 OpenAI 兼容接口（包括千问）
            if self.openai_client:
                content = await self._generate_with_openai(prompt)
            elif self.anthropic_client:
                content = await self._generate_with_anthropic(prompt)
            else:
                raise Exception("未配置任何 AI 服务")

            # 调试：记录原始返回
            logger.debug(f"LLM返回内容:\n{content[:500]}...")

            # 解析生成的内容
            result = self._parse_generated_content(content)
            result['version'] = version
            result['model_used'] = settings.GENERATE_MODEL

            logger.info(f"小红书内容生成成功: {version} - 标题:{result['title'][:30]}...")
            return result

        except Exception as e:
            logger.error(f"小红书内容生成失败: {e}")
            return self._fallback_content(news, version)

    def _get_prompt_template(self, version: str, news: Dict) -> str:
        """获取 Prompt 模板（从配置文件读取）"""
        # 从 config/prompts.py 获取对应版本的提示词
        base_prompt = PROMPTS.get(version, PROMPTS['A'])

        # 将新闻内容填充到提示词中
        prompt = base_prompt.format(
            title=news['title'],
            summary=news['summary'],
            content=news.get('content', news['summary'])[:1000]
        )

        return prompt

    async def _generate_with_openai(self, prompt: str) -> str:
        """使用 OpenAI 生成"""
        response = self.openai_client.chat.completions.create(
            model=settings.GENERATE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1000
        )
        return response.choices[0].message.content

    async def _generate_with_anthropic(self, prompt: str) -> str:
        """使用 Anthropic 生成"""
        response = self.anthropic_client.messages.create(
            model=settings.GENERATE_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _parse_generated_content(self, content: str) -> Dict:
        """解析生成的内容（支持多种格式）"""
        lines = content.split('\n')

        title = ''
        body = []
        hashtags = []

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 支持多种格式：📌 标题：、标题：、标题:、【标题】
            if ('📌 标题：' in line or '📌标题：' in line or
                '标题：' in line or '标题:' in line or
                line.startswith('【标题】')):
                current_section = 'title'
                # 如果是 "标题：xxx" 格式，直接提取
                if any(x in line for x in ['📌 标题：', '📌标题：', '标题：', '标题:']):
                    # 移除emoji前缀
                    clean_line = line.replace('📌 ', '').replace('📌', '')
                    parts = clean_line.split('：' if '：' in clean_line else ':', 1)
                    if len(parts) > 1:
                        title = parts[1].strip()
            elif ('📝 正文：' in line or '📝正文：' in line or
                  '📝 内容：' in line or '📝内容：' in line or
                  '内容：' in line or '内容:' in line or
                  line.startswith('【正文】') or line.startswith('【内容】')):
                current_section = 'body'
                # 如果是 "内容：xxx" 格式，直接提取
                if any(x in line for x in ['📝 正文：', '📝正文：', '📝 内容：', '📝内容：',
                                            '内容：', '内容:']):
                    # 移除emoji前缀
                    clean_line = line.replace('📝 ', '').replace('📝', '')
                    parts = clean_line.split('：' if '：' in clean_line else ':', 1)
                    if len(parts) > 1:
                        body.append(parts[1].strip())
            elif ('🏷️ 标签：' in line or '🏷️标签：' in line or
                  '标签：' in line or '标签:' in line or
                  line.startswith('【标签】')):
                current_section = 'hashtags'
                # 如果是 "标签：xxx" 格式，直接提取
                if any(x in line for x in ['🏷️ 标签：', '🏷️标签：', '标签：', '标签:']):
                    # 移除emoji前缀
                    clean_line = line.replace('🏷️ ', '').replace('🏷️', '')
                    parts = clean_line.split('：' if '：' in clean_line else ':', 1)
                    if len(parts) > 1:
                        tags = parts[1].replace('#', ' ').split()
                        hashtags.extend([f"#{tag}" for tag in tags if tag])
            elif line.startswith('【'):
                # 【xxx】标记本身不处理，但需要跳过
                if line == '【标题】':
                    current_section = 'title'
                elif line == '【正文】' or line == '【内容】':
                    current_section = 'body'
                elif line == '【标签】':
                    current_section = 'hashtags'
                continue
            else:
                if current_section == 'title' and not title:
                    title = line
                elif current_section == 'body':
                    body.append(line)
                elif current_section == 'hashtags':
                    tags = line.replace('#', ' ').split()
                    hashtags.extend([f"#{tag}" for tag in tags if tag])

        return {
            'title': title or '未命名',
            'content': '\n'.join(body) or '内容生成中...',
            'hashtags': hashtags or ['#AI', '#黑科技'],
            'image_prompt': f"{title} 的配图，科技风格"
        }

    def _fallback_content(self, news: Dict, version: str) -> Dict:
        """后备内容生成"""
        return {
            'title': news['title'],
            'content': news.get('summary', '')[:500],
            'hashtags': ['#AI', '#黑科技'],
            'image_prompt': f"{news['title']} 配图",
            'version': version
        }


# 导出
__all__ = ['AIService']
