import os
import sys
import json
import subprocess
import urllib.request
import textwrap

# 1. 配置阿里云 DashScope Key (从知识库得知您使用这个模型)
API_KEY = os.environ.get("DASHSCOPE_API_KEY")

def get_latest_news():
    print("=> 🌐 [Stage 1/4] 使用 OpenCLI 抓取 HackerNews 首页最新科技/AI动向...")
    try:
        # 直接使用 OpenCLI 的 hackernews 适配器无头提取 JSON
        res = subprocess.check_output(
            ['npx', '--yes', '@jackwener/opencli', 'hackernews', 'top', '--limit', '20', '--format', 'json']
        )
        items = json.loads(res.decode('utf-8'))
        # 简单过滤出含 AI / LLM / Model 等关键字的头条新闻
        ai_news = [item for item in items if any(k in item['title'].upper() for k in ['AI', 'LLM', 'MODEL', 'GPT', 'OPENAI', 'CLAUDE'])]
        if not ai_news:
            ai_news = items[:3]
        return ai_news[:2] # 选取最热的两条作为底料
    except Exception as e:
        print(f"抓取失败: {e}，将使用备用 Mock 新闻底料。")
        return [{"title": "Major AI Lab Announces Breakthrough in Long-Context Reasoning", "url": "https://example.com"}]

def generate_post(news_items):
    print("=> 🧠 [Stage 2/4] 调用 Qwen大模型 并施加结构化封印约束...")
    
    news_text = json.dumps(news_items, indent=2, ensure_ascii=False)
    
    # 【核心：完美复刻 Lilian的AI观察 的严苛提示词设计】
    prompt = textwrap.dedent(f"""
    # 角色设定
    你是一位身居一线的「高端AI猎头」与「硬核行业观察者」，账号叫「Lilian的AI观察」。
    你的受众是资深算法工程师、技术高管。

    # 最新鲜的行业资讯（底料）：
    {news_text}

    # 纪律约束 (CRITICAL)
    1. 【绝对禁止废话】不要有任何“大家好”、“今天给大家分享”等口语化废话。
    2. 【禁止泛滥表情】全文排版只允许使用 👉 和 💡 两个符号！绝对禁止使用 🔥🚀🌟 等带廉价感的符号！
    3. 【客观冷峻风格】用词必须精准干练。描述事实，提炼商业或技术的底层本质。

    # 输出结构 (必须100%遵照，不可加任何其他段落)
    [一个引人注目的短标题，切忌标题党，不超过20字，不要带括号]

    [第1段：1句话极简概述上述新闻事实的核心]
    [第2段：点出这个事件背后的核心技术拐点或商业卡位逻辑]

    👉 [核心洞察论点一]
    [一两句话深度拆解该论点的支撑细节]

    👉 [核心洞察论点二]
    [一两句话深度拆解核心逻辑]

    💡对从业者意味着什么？
    → [行业洗牌或岗位面临的威胁]
    → [未来真正稀缺的能力模型]
    → [给顶尖AI人才的一句硬核建议]

    #AI猎头 #大模型前沿 #Lilian的AI观察 #AI动态
    """)

    if not API_KEY:
        print("⚠️ 未检测到 DASHSCOPE_API_KEY 环境变量，本次将输出硬编码的 Mock 文案进行跑通测试...")
        return "大厂重塑Agent底层架构\n\n昨日顶级实验室相继宣布了长文本推理的突破性进展。\n这标志着大模型正在从“文本补全”正式向“自主推理机器”跨越。\n\n👉 算力下沉至推理期的重大拐点\n模型真正开始具备 Test-Time Compute 能力，慢思考正在取代快问快答。\n\n👉 平台型入口的重新洗牌\n所有原本依赖“组装套壳API”的中间层项目，生命线将受到毁灭性打击。\n\n💡对从业者意味着什么？\n→ 简单做提示词工程的岗位很快会被淘汰。\n→ 具备极强底层工程改造能力、能把模型真正嵌入异构系统的工程师被天价争夺。\n→ 别盯着调参看了，去搞懂强化学习和内核架构！\n\n#AI猎头 #大模型前沿 #Lilian的AI观察 #AI动态"
    
    # 标准的兼容 OpenAI 接口形式的请求
    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "You are Lilian, a senior AI industry headhunter and observer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4 # 低温抑制无用的发散
    }
    
    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {API_KEY}", 
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
            return resp_data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ 大模型接口调用失败: {e}")
        return "生成失败"

def main():
    news = get_latest_news()
    content = generate_post(news)
    
    # 提取生成的首行作为指令的 title (并去掉各类MD符号)
    lines = content.strip().split('\\n')
    title = lines[0].replace('[', '').replace(']', '').replace('#', '').strip()[:20]
    
    # 写入文件供 OpenCLI 发布指令读取
    draft_path = "/tmp/xhs_daily_draft.md"
    with open(draft_path, "w") as f:
        f.write(content)
        
    print("=> 🏞️  [Stage 3/4] 模拟生成当日优质封面配图...")
    img_path = "/tmp/xhs_daily_cover.jpg"
    urllib.request.urlretrieve("https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80", img_path)
    
    print(f"=> 🚀 [Stage 4/4] 触发 OpenCLI 小红书自动化推流引擎 (Draft Mode)...")
    cmd = [
        "npx", "--yes", "@jackwener/opencli", "xiaohongshu", "publish",
        content,
        "--title", title,
        "--images", img_path,
        "--draft", "true"
    ]
    try:
        subprocess.run(cmd, check=True)
        print("✅ 全自动化发文生命周期执行完毕！(请检查您的浏览器小红书草稿箱)")
    except subprocess.CalledProcessError as e:
        print(f"❌ OpenCLI 发布过程中断: {e}")

if __name__ == "__main__":
    print("-" * 50)
    print("🤖 启动 Lilian的AI观察 自动化每日发帖机器人")
    print("-" * 50)
    main()
