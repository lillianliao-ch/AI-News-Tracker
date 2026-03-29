import os
import json
import subprocess
import urllib.request
import re

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")

def fetch_hackernews_top30():
    print("=> 🌐 Fetching Top 30 HackerNews items via OpenCLI...")
    try:
        res = subprocess.check_output(
            ['npx', '--yes', '@jackwener/opencli', 'hackernews', 'top', '--limit', '30', '--format', 'json']
        )
        items = json.loads(res.decode('utf-8'))
        # 只保留 id, title 和 url 减少 Token 开销
        clean_items = [{"id": i, "title": item.get("title", ""), "url": item.get("url", "")} for i, item in enumerate(items)]
        return clean_items
    except Exception as e:
        print(f"Fetch failed: {e}")
        return []

def llm_score_and_filter(news_items):
    print("=> 🧠 Calling Qwen-Plus to act as LLM Scorer...")
    
    prompt = f"""
    作为资深AI科技媒体主编与AI猎头，你的任务是从以下 30 条当天的全球科技新闻中，挑选出最适合发在小红书上引发程序员受众深度讨论的 5 条新闻。
    挑选评估标准（满分10分）：
    1. 话题必须与 AI/大模型、前沿编程开发、或者大厂动向有关。（+4分）
    2. 能够引发从业者的饭碗焦虑 或 提供硬核技术价值（+3分）
    3. 具有现象级商业变现潜力 或 反共识特质（+3分）
    
    候选新闻列表（JSON格式）：
    {json.dumps(news_items, ensure_ascii=False)}
    
    【核心要求】必须严格以纯 JSON 数组格式返回总分最高的前 5 条新闻，结构如下，不要输出任何额外的思考过程文字，也不要带 ```json Markdown标记：
    [
      {{ "id": "匹配原始id", "title": "原始英文标题", "reason": "一句中文说明为什么选中它以及潜在的职场洞察方向", "score": "综合得分(1-10)" }}
    ]
    """
    
    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "You are a precise JSON-only output bot. Produce raw JSON arrays cleanly."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
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
            raw_content = resp_data['choices'][0]['message']['content'].strip()
            
            # 清理可能的 markdown 包裹
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:-3].strip()
            elif raw_content.startswith("```"):
                raw_content = raw_content[3:-3].strip()
                
            selected = json.loads(raw_content)
            return selected
    except Exception as e:
        print(f"LLM API Error: {e}")
        return []

def main():
    items = fetch_hackernews_top30()
    if not items:
        return
    
    top5 = llm_score_and_filter(items)
    
    verify_output = "/Users/lillianliao/.gemini/antigravity/brain/fcca4704-6627-434b-8ffd-22ceadd08021/verify_stage_2.md"
    with open(verify_output, "w", encoding="utf-8") as f:
        f.write("# Verify Stage 1 & 2: 大模型智能挑选器结果\n\n")
        f.write("裁判模型 (Qwen-Plus) 严格按照**“AI属性”、“职场焦虑度”和“商业卡位”**三个维度对 HackerNews 的实时 Top 30 进行了脱水评估。以下是被它高分选中的 Top 5：\n\n")
        for i, item in enumerate(top5, 1):
            f.write(f"### {i}. {item.get('title')} (得分: **{item.get('score')}/10**)\n")
            f.write(f"💡 **AI主编推荐语**: {item.get('reason')}\n\n")
            
        f.write("---\n*请您核实：大模型挑选出来的话题是否有爆款图文潜质？如果有，回复同意，我们将进入下一环节。*")
        
    with open('/tmp/xhs_top5_scored.json', 'w', encoding='utf-8') as jf:
        json.dump(top5, jf, indent=2, ensure_ascii=False)
        
    print(f"✅ Analysis complete! Verification saved to {verify_output}")

if __name__ == "__main__":
    main()
