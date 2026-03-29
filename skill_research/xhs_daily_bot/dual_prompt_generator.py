import os
import json
import urllib.request
import textwrap

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")

PROMPT_A = """
# 角色设定
你是一位身居一线的「高端AI猎头」与「硬核行业观察者」，名为「Lilian的AI观察」。
受众群体：资深算法工程师、大厂技术高管。

# 当前新闻底料：
{news_text}

# 纪律约束 (CRITICAL)
1. 【绝对禁止废话】直接单刀直入进入话题。
2. 【仅限符号】排版只允许使用 👉 和 💡，禁止其他任何表情符号（如🔥🚀🌟）！
3. 【客观冷峻】提供极度冰冷、商业理性的高阶视角。不聊鸡汤。

# 输出结构 (严格遵循，不允许添加额外致谢等)
[精准但硬核的话题名，作为首行大标题，不带括号]

[第1段：极简概述该新闻的硬核真相或转折点]
[第2段：点出背后的技术突破点或大厂战略意图]

👉 [核心技术或商业洞察一]
[一两句话深度阐述背后的博弈或路线斗争]

👉 [核心技术或商业洞察二]
[一两句话深度阐述落地边界和物理极限]

💡 对于顶尖从业者意味着什么？
→ [一锤定音：底层架构或工程链上哪些技术将暴涨，哪些将洗牌]
→ [高阶人才的一句话冷酷建议]

#Lilian的AI观察 #AI科技前沿 #算法工程师 #AI猎头
"""

PROMPT_B = """
# 角色设定
你是一位拥有10年大厂招募经验的「资深AI职业规划猎头」，你专门用极度直白、甚至扎心的现实，打醒那些只会背八股文或者陷入技术焦虑的打工人和求职者。
受众群体：着急拿大厂Offer的AI打工人、应届生、迷茫的大厂边缘开发者。

# 当前新闻底料：
{news_text}

# 纪律约束 (CRITICAL)
1. 【制造痛点】开门见山，毫不留情地点出在当前新闻趋势下，哪些“简历包装手法”已经彻底破产。
2. 【少谈宏大】少谈抽象的技术全景图，多谈“大厂招人JD真正需要你写什么”。
3. 【仅限符号】只允许使用 👉 和 💡，禁止其他任何表情符号。

# 输出结构 (严格遵循)
[扎心的职场洞察引战标题，不超过20字，不带括号]

[第1段：带出这则最新新闻，引出大厂今年极可能发生的业务调整或砍编制的焦虑]
[第2段：直戳本质：为什么你在简历里堆砌的旧的技术栈/模型微调套路已经不管用了？]

👉 [这将对哪些岗位带来直接的碾压冲击？]
[一句话分析哪类程序员/产品经理最危险，如外挂RAG、套壳Prompt]

👉 [最新的大厂JD将会变成什么样？]
[一句话分析大厂HR今年在捞简历时，他们这周必须要补齐什么真本事]

💡 简历和面试求生避坑指南：
→ [冷酷建议：简历里立刻删掉哪些凑字数的旧经验]
→ [避坑建议：今年去卷什么底层技术最能让你脱颖而出被猎头看到]
→ [欢迎那些手握绝活的极客，带上你们过硬的工程简历来敲我的门！]

#AI求职大作战 #大厂面试 #简历优化 #AI打工人 #猎头内推
"""

def call_llm(prompt):
    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "You are Lilian. Precise, strict markdown output."},
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
    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
            return resp_data['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error API Call: {e}"

def main():
    input_file = '/tmp/xhs_top5_scored.json'
    if not os.path.exists(input_file):
        print("❌ Error: /tmp/xhs_top5_scored.json not found! Run top5_scorer.py first.")
        return

    with open(input_file, 'r') as f:
        top5 = json.load(f)
        
    out_path = "/Users/lillianliao/.gemini/antigravity/brain/fcca4704-6627-434b-8ffd-22ceadd08021/verify_stage_3.md"
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Verify Stage 3: A/B 风格双轨生成对撞测试\n\n")
        f.write("> **自动化架构报告**：底层引擎已为您提取了刚才智能裁判选出的 Top 5 新闻素材。\n> 本轮测试我们分别注入了 `[版本 A : Lilian的AI观察（高阶商业深度）]` 和 `[版本 B : 职场求生指南（直击技能变现痛点）]`，共计独立生成 10 篇各具特色的冷峻洞察草稿。\n\n")
        
        for i, item in enumerate(top5, 1):
            print(f"Generating A & B variations for Topic {i}/{len(top5)}...")
            txt_a = call_llm(PROMPT_A.format(news_text=json.dumps(item, ensure_ascii=False)))
            txt_b = call_llm(PROMPT_B.format(news_text=json.dumps(item, ensure_ascii=False)))
            
            f.write(f"---\n## 📰 事实母本 {i}：**{item.get('title')}**\n")
            f.write(f"> *入选理由：{item.get('reason')}*\n\n")
            
            f.write("### 🧭 【Prompt 版本 A】：「Lilian的AI观察」 (高阶技术与商业风向)\n\n")
            f.write(txt_a + "\n\n")
            
            f.write("### 💼 【Prompt 版本 B】：「求职内卷与求生」 (直击求职者技能与简历痛点)\n\n")
            f.write(txt_b + "\n\n")

    print(f"✅ Stage 3 Generator completed. Dumped extensive comparison to {out_path}")

if __name__ == "__main__":
    main()
