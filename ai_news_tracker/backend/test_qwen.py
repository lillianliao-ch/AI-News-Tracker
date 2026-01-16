"""
测试千问 API 集成
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

def test_qwen_connection():
    """测试千问连接"""
    print("=" * 60)
    print("测试千问 API 连接")
    print("=" * 60)

    # 读取配置
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("GENERATE_MODEL", "qwen-max")

    print(f"\n📋 配置信息:")
    print(f"  API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")

    # 初始化客户端
    client = OpenAI(api_key=api_key, base_url=base_url)

    # 测试简单对话
    print("\n🤖 测试简单对话...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个AI助手"},
                {"role": "user", "content": "用一句话介绍你自己"}
            ],
            temperature=0.7
        )

        result = response.choices[0].message.content
        print(f"✅ 对话成功!")
        print(f"   回复: {result}")

        # 显示 token 使用情况
        if hasattr(response, 'usage') and response.usage:
            print(f"\n📊 Token 使用:")
            print(f"   输入: {response.usage.prompt_tokens} tokens")
            print(f"   输出: {response.usage.completion_tokens} tokens")
            print(f"   总计: {response.usage.total_tokens} tokens")

    except Exception as e:
        print(f"❌ 对话失败: {e}")
        return False

    # 测试小红书文案生成
    print("\n📱 测试小红书文案生成...")
    test_news = {
        "title": "阿里云发布通义千问2.5，性能提升300%",
        "summary": "阿里云今日发布通义千问2.5版本，在推理性能上相比上一代提升300%，成本降低50%，支持更长的上下文窗口。",
        "content": "通义千问2.5采用全新架构，支持200K上下文窗口，在多项基准测试中超越GPT-4。"
    }

    prompt = f"""你是一位擅长科普的AI领域博主，擅长将复杂的AI新闻转化为通俗易懂的小红书文案。

请根据以下新闻内容，生成一篇小红书文案：

**要求：**
1. 标题：制造好奇心，使用感叹号，适当使用表情符号 😱🔥✨💡
2. 内容：
   - 用生活化的比喻解释技术
   - 口语化表达，像朋友聊天一样
   - 多用表情符号增加趣味性
   - 突出这个技术对普通人的影响
   - 适合大众用户阅读
3. 风格：轻松、有趣、接地气
4. 长度：150-200字
5. 标签：生成3-5个相关标签，如 #AI #科普 #必看

**新闻内容：**
{test_news['title']}

{test_news['summary']}

{test_news['content']}

**请直接输出生成的文案，格式如下：**
标题：[你的标题]
内容：[你的内容]
标签：[标签1] [标签2] [标签3]"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )

        result = response.choices[0].message.content
        print(f"✅ 文案生成成功!")
        print(f"\n{'='*60}")
        print(result)
        print(f"{'='*60}")

        # 显示 token 使用情况
        if hasattr(response, 'usage') and response.usage:
            print(f"\n📊 Token 使用:")
            print(f"   输入: {response.usage.prompt_tokens} tokens")
            print(f"   输出: {response.usage.completion_tokens} tokens")
            print(f"   总计: {response.usage.total_tokens} tokens")

            # 估算成本
            # qwen-max: ¥0.02/1K input tokens, ¥0.06/1K output tokens
            input_cost = (response.usage.prompt_tokens / 1000) * 0.02
            output_cost = (response.usage.completion_tokens / 1000) * 0.06
            total_cost = input_cost + output_cost
            print(f"\n💰 成本估算:")
            print(f"   输入: ¥{input_cost:.4f}")
            print(f"   输出: ¥{output_cost:.4f}")
            print(f"   总计: ¥{total_cost:.4f}")

    except Exception as e:
        print(f"❌ 文案生成失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！千问 API 集成成功！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_qwen_connection()
    sys.exit(0 if success else 1)
