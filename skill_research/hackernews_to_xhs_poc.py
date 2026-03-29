import os
import subprocess
import json
import re
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

DASHSCOPE_API_KEY = "sk-4e2bb9108e1541f9b7dd88855922c7a3"

def get_hackernews_top():
    print("🌍 正在拦截 HackerNews 硅谷实时前沿热点...")
    cmd = ["npx", "--yes", "@jackwener/opencli", "hackernews", "top", "--limit", "4", "-f", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def summarize_with_qwen(news_list):
    print("🧠 正在唤醒 Qwen-Plus 将海外热点重写为小红书硬核大字报文案...")
    
    client = OpenAI(
        api_key=DASHSCOPE_API_KEY, 
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    news_text = "\n".join([f"- {n['title']} (HN Score: {n['score']}) - {n['url']}" for n in news_list])
    prompt = f"""你是一个顶级的硅谷极客/AI资深猎头(Lilian聊AI)。
这里是目前 HackerNews 上排名前列的技术热推：
{news_text}

请帮我把它们提炼合并为一篇小红书硬核干货图文。
要求：
1. 第一行生成一个霸气、有深度的标题（控制在18个字以内，供主画面排版，必须带【】框起）。
2. 第二行生成一句高对比度的副标题（20个字内，说明这个趋势或合集的意义）。
3. 接下来是正文，用👉和💡等emoji增加可读性，分享这几个事件背后的硬核逻辑以及对“打工人/AI开发者”的启示。
直接输出，不要废话。"""

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.choices[0].message.content

def measure_wrap(text, font, max_width):
    lines = []
    tokens = re.findall(r'[a-zA-Z0-9]+|.', text)
    current_line = ''
    for token in tokens:
        test_line = current_line + token
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = token
            while font.getlength(current_line) > max_width:
                if max_width < 10: break 
                for i in range(1, len(current_line)):
                    if font.getlength(current_line[:i]) > max_width:
                        lines.append(current_line[:i-1])
                        current_line = current_line[i-1:]
                        break
                else: break
    if current_line: lines.append(current_line)
    return lines

font_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"
if not os.path.exists(font_path): font_path = "/System/Library/Fonts/STHeiti Medium.ttc"

def robust_draw_xhs(title, subtitle, badge_text, output_path):
    W, H = 1080, 1440
    img = Image.new('RGB', (W, H), color=(252, 252, 252))
    draw = ImageDraw.Draw(img)
    clean_title = re.sub(r'[^\w\s，。！：|!a-zA-Z0-9-]', '', title).strip()
    clean_sub = re.sub(r'[^\w\s，。！：.,|!a-zA-Z0-9%-]', '', subtitle).strip()
    PAD_X = 80
    MAX_W = W - PAD_X * 2

    try: badge_font = ImageFont.truetype(font_path, 50, index=0)
    except: badge_font = ImageFont.load_default()
    box_w = len(badge_text) * 50 + 60
    draw.rounded_rectangle([PAD_X, 150, PAD_X+box_w, 230], radius=15, fill=(227, 35, 34))
    draw.text((PAD_X + 30, 165), badge_text, fill=(255, 255, 255), font=badge_font)

    title_start_y = 300
    title_font_size = 180
    while title_font_size > 50:
        try: title_font = ImageFont.truetype(font_path, title_font_size, index=0)
        except: title_font = ImageFont.load_default()
        lines = measure_wrap(clean_title, title_font, MAX_W)
        if len(lines) * (title_font_size + 40) + title_start_y < 1000: break
        title_font_size -= 5

    wrapped_title = "\n".join(lines)
    draw.multiline_text((PAD_X, title_start_y), wrapped_title, fill=(24, 24, 24), font=title_font, spacing=40, stroke_width=3, stroke_fill=(24, 24, 24))

    sub_font_size = 80
    while sub_font_size > 30:
        try: sub_font = ImageFont.truetype(font_path, sub_font_size, index=0)
        except: sub_font = ImageFont.load_default()
        sub_lines = measure_wrap(clean_sub, sub_font, MAX_W)
        if len(sub_lines) <= 4: break
        sub_font_size -= 5
        
    sub_start_y = title_start_y + len(lines) * (title_font_size + 40) + 80
    wrapped_sub = "\n".join(sub_lines)
    draw.multiline_text((PAD_X, sub_start_y), wrapped_sub, fill=(50, 50, 50), font=sub_font, spacing=25, stroke_width=1, stroke_fill=(50, 50, 50))
    img.save(output_path)

def main():
    news = get_hackernews_top()
    draft_content = summarize_with_qwen(news)
    
    print("\n--- LLM Content Generated ---")
    print(draft_content)
    print("-----------------------------\n")

    lines = draft_content.strip().split('\n')
    raw_title = lines[0].strip()
    title = raw_title.replace('【', '').replace('】', '') if '【' in raw_title else raw_title
    
    # Extract subtitle
    subtitle = ""
    for line in lines[1:]:
        if line.strip():
            subtitle = line.strip()
            break
    
    if len(title) > 25: title = title[:25]
    if len(subtitle) > 40: subtitle = subtitle[:40]

    img_path = "/tmp/hn_auto_poster.jpg"
    print("🎨 正在生成纯色像素级硬核大字报...")
    robust_draw_xhs(title, subtitle, "极客快讯", img_path)

    api_title = title[:20]  # Respect XHS 20-char API limit
    print(f"🚀 将排版结果挂载至 OpenCLI，静默推送至小红书草稿箱 [标题: {api_title}]...")
    cmd = [
        "npx", "--yes", "@jackwener/opencli", "xiaohongshu", "publish",
        draft_content,
        "--title", api_title,
        "--images", img_path,
        "--draft", "true"
    ]
    try:
        subprocess.run(cmd, check=True)  # let's not hide output to see if there is error.
        print("✅ 闭环达成！您在 HackerNews 上抓取的硅谷热推，现在已是一篇小红书无损画质草稿！")
    except Exception as e:
        print("❌ 推送失败:", e)

if __name__ == "__main__":
    main()
