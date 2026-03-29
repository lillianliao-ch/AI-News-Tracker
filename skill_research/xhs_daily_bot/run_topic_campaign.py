import os
import sys
import json
import subprocess
import urllib.request
import textwrap
import time
import argparse
from datetime import datetime

# =====================================================================
# 一站式 AI资讯自动发文矩阵 / Daily XHS Bot Campaign Orchestrator 
# 衍生版：指定话题网络联查爆款机 (Thematic Topic Campaign)
# =====================================================================

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")
TG_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
WORKSPACE_DIR = "/Users/lillianliao/notion_rag/skill_research/xhs_daily_bot"

os.makedirs(os.path.join(WORKSPACE_DIR, "drafts"), exist_ok=True)

PROMPT_A = """
# 角色设定
你是一位身居一线的「高端AI猎头」与「硬核行业观察者」，名为「Lilian的AI观察」。
受众群体：资深算法工程师、大厂技术高管。

# 当前新闻底料：
{news_text}

# 纪律约束 (CRITICAL)
1. 【绝对禁止废话】直接单刀直入。
2. 【仅限符号】排版只允许使用 👉 和 💡，禁止其他任何表情符号！
3. 【客观冷峻】提供极度冰冷、商业理性的高阶视角。

# 输出结构 (严格遵循，不带括号)
[精准但硬核的话题名，作为首行大标题，不带括号，不超过20字]

[第1段：极简概述该新闻的硬核真相或转折点]
[第2段：点出背后的技术突破点或大厂战略意图]

👉 [核心技术或商业洞察一]
[一两句话深度阐述]

👉 [核心技术或商业洞察二]
[一两句话深度阐述]

💡 对于顶尖从业者意味着什么？
→ [底层架构上哪些技术将暴涨，哪些将洗牌]
→ [高阶人才的一句话冷酷建议]

#Lilian的AI观察 #AI科技前沿 #算法工程师 #AI猎头
"""

PROMPT_B = """
# 角色设定
请你充当一位专注 AI 产业观察的小红书创作者，账号名「Lilian聊AI」。
风格：专业有洞察、轻松有温度、既聊技术也聊人。
目标读者：AI从业者、科技行业人士、对AI感兴趣的职场人。

# 核心要求
不做信息搬运工，要有独特洞察。根据我提供的主题，生成一篇高阅读量笔记，包括标题、正文和标签。

# 当前新闻底料：
{news_text}

# 输出要求
0️⃣ 【最重要】深度思考步骤（先在脑中完成，绝不输出）
这条新闻的表面是什么？本质在押注什么？
这不是XX，而是XX（找到更深层的真正意图）
这改变了什么游戏规则？

1️⃣ 标题格式（高点击+有观点）
🔥 + [品牌/关键词] + [动词] + [独特洞察]
示例：ElevenLabs估值110亿🔥AI不是在做语音，是在抢岗位

2️⃣ 正文结构
🚀 开头：一句话点题 + 反转洞察
先说事实，然后给出独特解读：「这不是XX，而是XX」
📊 数据支撑（若有）
用1-3条数据增强说服力
🎬 核心观点（2-3个，每个有小标题）
每个观点要有「一句亮点 + 支撑逻辑 + 一句结论」
可以用对比思维。
💡 职业视角段落
以「对从业者意味着什么？」开头
列出2-3条具体影响（用→符号），给读者行动方向感
⚡ 金句收尾
要有观点、可引用、有记忆点
💬 互动引导
提一个开放式问题，引发讨论

3️⃣ 文风要求
每段≤3行，短句为主，多用emoji。语气自信、有观点。

4️⃣ 标签（10-12个）
热点关键词 + 功能场景 + 职业相关
"""

def send_telegram_msg(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("⚠️ Telegram Config Missing. Skipping TG Notification.")
        return
    
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def draw_xhs_text_poster(title, subtitle, badge_text, output_path):
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        import re
        import os
    except ImportError:
        print("     ⚠️ Pillow未安装，跳过文字渲染")
        return False
        
    print(f"   🎨 正在本地拉起大字报强视觉引擎渲染【{title}】...")
    W, H = 1080, 1440
    # 纯净的极白底色（符合最新截图大字报质感）
    img = Image.new('RGB', (W, H), color=(252, 252, 252))
    draw = ImageDraw.Draw(img)

    font_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/STHeiti Medium.ttc"

    # 清除容易干扰字体的emoji和特异符号
    clean_title = re.sub(r'[^\w\s，。！：|!a-zA-Z0-9-]', '', title).strip()
    clean_sub = re.sub(r'[^\w\s，。！：.,|!a-zA-Z0-9%-]', '', subtitle).strip()

    PAD_X = 80
    MAX_W = W - PAD_X * 2

    # 1. 绘制红色的标签徽章 (Badge)
    try:
        badge_font = ImageFont.truetype(font_path, 50, index=0)
    except:
        badge_font = ImageFont.load_default()
        
    box_w = len(badge_text) * 50 + 60
    box_h = 80
    badge_y = 150
    draw.rounded_rectangle([PAD_X, badge_y, PAD_X+box_w, badge_y+box_h], radius=15, fill=(227, 35, 34))
    draw.text((PAD_X + 30, badge_y + 15), badge_text, fill=(255, 255, 255), font=badge_font)

    # 智能像素测量与自动换行算子 (防御超框爆出)
    def measure_wrap(text, font, max_width):
        lines = []
        tokens = re.findall(r'[a-zA-Z0-9]+|.', text)
        current_line = ""
        for token in tokens:
            test_line = current_line + token
            if font.getlength(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line: 
                    lines.append(current_line)
                current_line = token
                # 极端长单词被逼到绝角的情况
                while font.getlength(current_line) > max_width:
                    for i in range(1, len(current_line)):
                        if font.getlength(current_line[:i]) > max_width:
                            lines.append(current_line[:i-1])
                            current_line = current_line[i-1:]
                            break
        if current_line:
            lines.append(current_line)
        return lines

    # 2. 动态调节大字报主标题字号
    title_start_y = 300
    title_font_size = 180
    while title_font_size > 60:
        try:
            title_font = ImageFont.truetype(font_path, title_font_size, index=0)
        except:
            title_font = ImageFont.load_default()
            
        lines = measure_wrap(clean_title, title_font, MAX_W)
        total_height = len(lines) * (title_font_size + 40)
        
        # 必须留出至少空间给副标题
        if total_height + title_start_y < 1000:
            break
        title_font_size -= 10

    wrapped_title = "\n".join(lines)
    # 极强的高频 stroke 模拟最重黑体
    draw.multiline_text((PAD_X, title_start_y), wrapped_title, fill=(24, 24, 24), font=title_font, spacing=40, stroke_width=3, stroke_fill=(24, 24, 24))

    # 3. 动态调节副标题字号
    sub_font_size = 80
    while sub_font_size > 40:
        try:
            sub_font = ImageFont.truetype(font_path, sub_font_size, index=0)
        except:
            sub_font = ImageFont.load_default()
        sub_lines = measure_wrap(clean_sub, sub_font, MAX_W)
        if len(sub_lines) <= 4:  # 副标不要霸占太多行
            break
        sub_font_size -= 5
        
    title_total_h = len(lines) * (title_font_size + 40)
    sub_start_y = title_start_y + title_total_h + 80
    
    wrapped_sub = "\n".join(sub_lines)
    draw.multiline_text((PAD_X, sub_start_y), wrapped_sub, fill=(50, 50, 50), font=sub_font, spacing=25, stroke_width=1, stroke_fill=(50, 50, 50))

    img.save(output_path)
    return True

def call_llm(prompt):
    import time
    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "You are Lilian. Expert markdown generation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }
    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(data).encode('utf-8'),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))['choices'][0]['message']['content'].strip()
        except Exception as e:
            if attempt == 2:
                raise e
            print(f"     ⚠️ LLM API connection dropped ({e}), retrying in 3 seconds...")
            time.sleep(3)

def fetch_topic_research(topic):
    prompt = f"""请利用你的全网搜索能力，深度检索关于【{topic}】的最新高质量文章、行业观点和技术演进。
从中综合、提炼出 5 个不同视角的、信息密度极高且具有小红书爆款潜力的子话题/新闻点。
要求：仅返回纯JSON数组，绝对不要返回任何其他格式或说明文字！
格式如下：
[
    {{"title": "子话题或新闻标题（少于20字）", "content": "100字左右的深度概要、新闻事实或技术细节"}}
]
"""
    data = {
        "model": "qwen-plus",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "enable_search": True
    }
    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(data).encode('utf-8'),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        raw = json.loads(resp.read().decode('utf-8'))['choices'][0]['message']['content'].strip()
        if raw.startswith("```json"): raw = raw[7:-3].strip()
        elif raw.startswith("```"): raw = raw[3:-3].strip()
        
        items = json.loads(raw)
        # 为流水线对齐结构
        return [{"id": i, "title": it.get("title", ""), "url": "AI Web Search Agent", "content": it.get("content", "")} for i, it in enumerate(items, 1)]

def main():
    parser = argparse.ArgumentParser(description="定向火力全开：根据关键词直接引爆生成10篇爆款图文！")
    parser.add_argument("--topic", type=str, required=True, help="指定的主题方向 (如 'Vibe Coding')")
    args = parser.parse_args()

    print(f"🚀 [1/4] Web Research Agent 启动，正在全网深掘主题：【{args.topic}】...")
    try:
        top5 = fetch_topic_research(args.topic)
        print(f"   ✓ 找到了 5 个强力子话题爆点！")
    except Exception as e:
        print(f"❌ 检索资料失败: {e}")
        send_telegram_msg(f"🚨 <b>XHS Topic Bot Error</b>\\nSearch phase failed: {e}")
        return

    print(f"🧠 [2/4] Generating 10 Drafts (A/B Styles) for 【{args.topic}】...")
    drafts = []
    for i, item in enumerate(top5[:5], 1):
        for style, P in [("A", PROMPT_A), ("B", PROMPT_B)]:
            # 传过去的是 JSON 字典包含 title 和 content
            content = call_llm(P.format(news_text=json.dumps(item, ensure_ascii=False)))
            
            # 强大的标题提取过滤机制，抛弃带有 "📌 标题：" 的前置行废话
            clean_lines = [l.strip() for l in content.split('\n') if l.strip()]
            raw_title = clean_lines[0]
            if ("标题" in raw_title or "Title" in raw_title) and len(raw_title) <= 10 and len(clean_lines) > 1:
                raw_title = clean_lines[1]
                
            title = raw_title.replace('[', '').replace(']', '').replace('#', '').replace('*', '').strip()
            while sum(2 if ord(c) > 0xFFFF else 1 for c in title) > 20:
                title = title[:-1]
            
            filepath = os.path.join(WORKSPACE_DIR, "drafts", f"topic_{args.topic}_{i}_{style}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            drafts.append({
                "title": title,
                "filepath": filepath,
                "news_title": item.get('title')
            })
            print(f"   ✓ Draft Subtopic {i} Style {style} ready.")

    print("📝 [3/4 & 4/4] Executing OpenCLI 小红书 Publish 引擎 (带动态配图)...")
    
    success_count = 0
    for idx, d in enumerate(drafts, 1):
        print(f"   ► Pushing {idx}/10: {d['title']}")
        img_path = os.path.join(WORKSPACE_DIR, "drafts", f"cover_{args.topic}_{idx}.jpg")
        
        # 1. 彻底弃用大模型视觉，直接调用 Python 大字报海报渲染引擎
        badge_text = "行业洞察" if d['filepath'].endswith("_A.md") else "求职突围"
        sub_text = "行业增速400%，下一个百万从业者风口来了" if d['filepath'].endswith("_A.md") else "别再只刷LeetCode了，立刻切入这个方向"
        draw_xhs_text_poster(d['title'], sub_text, badge_text, img_path)

        # 2. XHS 创作者中心 DOM Bug 热修复 (强制将标题注入正文顶部)
        with open(d['filepath'], 'r', encoding='utf-8') as f:
            raw_content = f.read()
        full_content = f"【{d['title']}】\n\n{raw_content}"
            
        cmd = [
            "npx", "--yes", "@jackwener/opencli", "xiaohongshu", "publish",
            full_content,
            "--title", d['title'],
            "--images", img_path,
            "--draft", "true"
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
            success_count += 1
            time.sleep(3) 
        except subprocess.CalledProcessError as e:
            print(f"     ❌ Subprocess failed for draft {idx}")

    # Finishing and notifying
    result_text = (
        "🤖 <b>专题追踪雷达：任务结束</b>\\n\\n"
        f"🎯 <b>指令主题</b>: 【{args.topic}】\\n"
        f"✅ <b>全网检索与提炼完成</b> (严抓 5 个重磅素材)\\n"
        f"✅ <b>撰稿与AI制图完成</b> (10篇覆盖职场/洞察两端)\\n"
        f"✅ <b>入库成功</b> ({success_count}/10 篇草稿待发)\\n\\n"
        "🔗 <i>小红书热点抢占成功，请打开手机端分发！</i>"
    )
    send_telegram_msg(result_text)
    print("🎉 Topic Campaign Fully Executed!")

if __name__ == "__main__":
    main()
