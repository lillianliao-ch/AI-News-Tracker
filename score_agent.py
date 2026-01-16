#!/usr/bin/env python3
import pandas as pd
import re

INPUT = "/Users/lillianliao/notion_rag/Agent-脉脉搜索结果_2025-12-26T13-04-56.csv"
OUTPUT = "/Users/lillianliao/notion_rag/Agent-脉脉搜索结果_评分.csv"

EXCLUDE = ['运维', '测试', '前端', '商务', '销售', '产品经理', '产品']
TECH1 = ['LLM', '大模型', 'Agent', '智能体', 'GPT', 'RAG', 'embedding', 'prompt', 'RLHF', 'langchain', 'Mcp', 'MCP', 'GraphRAG', 'Multi-Agent']
TECH2 = ['NLP', '自然语言', '对话', '问答', '知识图谱', 'BERT', 'Transformer']
TECH3 = ['算法', '机器学习', '深度学习', '推荐', 'AI', 'PyTorch', 'CV', '多模态']
TECH4 = ['后端', '架构', 'Python', 'Golang', '工程师', 'Java']
COMP1 = ['Qwen', '通义', '百度', '字节', 'Seed', '阿里', '腾讯', '华为', 'OpenAI', 'Google', '文心', 'Meta', '光年之外', '京东']
COMP2 = ['智谱', '月之暗面', 'Moonshot', 'MiniMax', '百川', '商汤', '旷视', 'realme']
COMP3 = ['快手', '美团', '小红书', '网易', 'B站', '小米', 'OPPO', '滴滴']
SCHOOLS = ['清华', '北大', '交大', '复旦', '浙大', '中科大', '南京大学', '哈工大', '武大', '北航', '北邮', '东北大学']

df = pd.read_csv(INPUT, encoding='utf-8-sig')
print(f"原始: {len(df)}人")

results = []
for _, row in df.iterrows():
    all_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
    
    # 排除判断
    excluded = False
    for kw in EXCLUDE:
        if kw in all_text:
            excluded = True
            break
    years = row.get('工作年限')
    if pd.notna(years) and float(years) < 1:
        excluded = True
    if excluded:
        continue
    
    # 评分
    tech_s, tech_kw = 0, '-'
    for kw in TECH1:
        if kw.lower() in all_text.lower():
            tech_s, tech_kw = 40, kw
            break
    if tech_s == 0:
        for kw in TECH2:
            if kw.lower() in all_text.lower():
                tech_s, tech_kw = 30, kw
                break
    if tech_s == 0:
        for kw in TECH3:
            if kw.lower() in all_text.lower():
                tech_s, tech_kw = 20, kw
                break
    if tech_s == 0:
        for kw in TECH4:
            if kw.lower() in all_text.lower():
                tech_s, tech_kw = 10, kw
                break
    
    comp_s, comp_kw = 5, '-'
    for c in COMP1:
        if c in all_text:
            comp_s, comp_kw = 25, c
            break
    if comp_s == 5:
        for c in COMP2:
            if c in all_text:
                comp_s, comp_kw = 22, c
                break
    if comp_s == 5:
        for c in COMP3:
            if c in all_text:
                comp_s, comp_kw = 18, c
                break
    
    exp_s = 10
    if pd.notna(years):
        y = float(years)
        if 3 <= y <= 8: exp_s = 20
        elif 8 < y <= 12: exp_s = 15
        elif 1 <= y < 3: exp_s = 10
        else: exp_s = 5
    
    edu_s = 6
    is_top = any(s in all_text for s in SCHOOLS)
    has_master = '硕' in all_text
    if is_top and has_master: edu_s = 15
    elif is_top: edu_s = 12
    elif has_master: edu_s = 10
    
    total = tech_s + comp_s + exp_s + edu_s
    
    active = str(row.get('活跃状态', ''))
    is_active = '小时内' in active or '刚刚' in active
    is_recent = '天' in active
    
    if total >= 80 and is_active:
        priority = 'P0-今日联系'
    elif total >= 60 and (is_active or is_recent):
        priority = 'P1-本周联系'
    elif total >= 40:
        priority = 'P2-常规跟进'
    else:
        priority = 'P3-入库观察'
    
    results.append({
        '姓名': row['姓名'],
        '活跃状态': active,
        '总分': total,
        '技术关键词': tech_kw,
        '匹配公司': comp_kw,
        '优先级': priority
    })

result_df = pd.DataFrame(results).sort_values('总分', ascending=False)
print(f"通过: {len(result_df)}人")

for p in ['P0-今日联系', 'P1-本周联系', 'P2-常规跟进', 'P3-入库观察']:
    print(f"  {p}: {len(result_df[result_df['优先级'] == p])}人")

print("\nTop 15:")
for _, r in result_df.head(15).iterrows():
    print(f"  {r['姓名']:<12} | {r['活跃状态']:<10} | 分数:{r['总分']:>2} | {r['技术关键词']:<10} | {r['匹配公司']:<8} | {r['优先级']}")

result_df.to_csv(OUTPUT, index=False, encoding='utf-8-sig')
print(f"\n已保存: {OUTPUT}")
