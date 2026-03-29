import os
import json
import subprocess
import urllib.request
import textwrap

API_KEY = os.environ.get("DASHSCOPE_API_KEY")

def get_news():
    print("=> 🌐 Fetching 20 HackerNews items...")
    res = subprocess.check_output(
        ['npx', '--yes', '@jackwener/opencli', 'hackernews', 'top', '--limit', '30', '--format', 'json']
    )
    items = json.loads(res.decode('utf-8'))
    # Filter tech/AI items
    keywords = ['AI', 'LLM', 'MODEL', 'GPT', 'OPENAI', 'CLAUDE', 'AGENT', 'STARTUP', 'FUND', 'APPLE', 'GOOGLE', 'NVIDIA', 'GPU']
    ai_news = [item for item in items if any(k in item['title'].upper() for k in keywords)]
    
    # Ensure we have at least 5
    if len(ai_news) < 5:
        for it in items:
            if it not in ai_news:
                ai_news.append(it)
            if len(ai_news) == 5: break
            
    return ai_news[:5]

def generate_one(news_item, index):
    news_text = json.dumps(news_item, indent=2, ensure_ascii=False)
    
    prompt = textwrap.dedent(f"""
    # 角色设定
    你是一位身居一线的「高端AI猎头」与「行业观察者」，账号叫「Lilian的AI观察」。受众是资深算法工程师与技术高管。

    # 当前新闻素材：
    {news_text}

    # 纪律约束 (CRITICAL)
    1. 【绝对禁止废话】不要打招呼。
    2. 【仅限符号】只允许使用 👉 和 💡，禁止其他所有表情符号！
    3. 【客观冷峻】用词精准，洞察深刻，不吹捧不随波逐流。结合求职、创业或技术落地趋势分析。

    # 输出结构 (严格遵守)
    [标题，不超过20字，吸睛但克制，无括号]

    [第1段：1句话精简客观描述该新闻事实]
    [第2段：点出背后的技术/商业真正卡位逻辑]

    👉 [核心洞察一]
    [一两段精简深度拆解细节]

    👉 [核心洞察二]
    [一两段精简深度拆解逻辑]

    💡对从业者意味着什么？
    → [行业洗牌或岗位面临的威胁/机遇]
    → [未来真正稀缺的能力模型]
    → [给顶尖AI人才的硬核建议]

    #AI猎头 #大模型前沿 #Lilian的AI观察 #AI动态
    """)

    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "You are Lilian, a senior AI industry headhunter."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }
    
    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {API_KEY}", 
            "Content-Type": "application/json"
        }
    )
    
    print(f"=> 🧠 Generating post {index}/5 based on: {news_item['title']} ...")
    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
            return resp_data['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    news = get_news()
    results = []
    
    for i, item in enumerate(news, 1):
        content = generate_one(item, i)
        results.append(content)
        
    out_path = "/Users/lillianliao/.gemini/antigravity/brain/fcca4704-6627-434b-8ffd-22ceadd08021/5_auto_posts.md"
    
    with open(out_path, "w") as f:
        f.write("# 批量生成测试 (5篇)\n\n")
        for i, res in enumerate(results, 1):
            f.write(f"## 待发布草案 {i} (基于真实全球最新资讯)\n\n")
            f.write(res + "\n\n---\n\n")
            
    print(f"✅ Success! Wrote 5 massive posts to {out_path}")

if __name__ == "__main__":
    main()
