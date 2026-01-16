#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通义候选人筛选与评分脚本
针对 AI Agent 工程师岗位
"""

import pandas as pd
import re

# 文件路径
INPUT_FILE = "/Users/lillianliao/notion_rag/tongyi-talent-final-cleaned.xlsx"
OUTPUT_FILE = "/Users/lillianliao/notion_rag/tongyi-talent-评分.csv"

# ==================== 排除规则 ====================
EXCLUDE_TITLES = ["运维", "测试", "前端", "商务", "销售", "产品经理", "产品"]

# ==================== 评分规则配置 ====================

# 技术方向关键词（注意：文心/通义等是产品名，不是技术关键词）
TECH_KEYWORDS = {
    # 40分 - 直接相关 Agent/LLM 技术
    "tier1": [
        "LLM", "大模型", "Agent", "智能体", "GPT", "RAG", "Retrieval",
        "向量", "embedding", "prompt", "RLHF", "langchain", "LangChain",
        "CoT", "思维链", "多模态大模型", "对话系统", "对话机器人",
        "ChatBot", "copilot", "Copilot", "预训练", "Pre-training",
        "Hallucination", "幻觉"
    ],
    # 30分 - 强相关 NLP/AI
    "tier2": [
        "NLP", "自然语言", "语言模型", "对话", "问答", "知识图谱",
        "语义理解", "文本", "BERT", "Transformer", "意图识别",
        "实体识别", "情感分析", "机器翻译", "NLG", "NLU"
    ],
    # 20分 - 相关 ML/DL
    "tier3": [
        "算法", "机器学习", "深度学习", "推荐", "搜索", "研究员",
        "AI", "人工智能", "模型", "训练", "推理", "PyTorch",
        "TensorFlow", "CV", "计算机视觉", "多模态"
    ],
    # 10分 - 潜在相关
    "tier4": [
        "后端", "架构", "分布式", "Python", "Golang", "工程师", "DRL"
    ]
}

# 公司/产品背景分层（包含产品名）
COMPANY_TIERS = {
    # 25分 - 顶级 AI 团队/产品
    "tier1": [
        "Qwen", "通义", "百度", "字节", "Seed", "seed", "阿里", "达摩院",
        "腾讯", "混元", "华为", "盘古", "OpenAI", "Google", "DeepMind",
        "文心", "ERNIE", "Meta", "Anthropic"
    ],
    # 22分 - 六小龙 + AI 独角兽
    "tier2": [
        "智谱", "月之暗面", "Moonshot", "MiniMax", "百川", "零一万物", "阶跃星辰",
        "商汤", "旷视", "依图", "云从", "科大讯飞", "第四范式", "地平线", "寒武纪"
    ],
    # 18分 - 知名互联网 + AI 新锐
    "tier3": [
        "快手", "美团", "京东", "小红书", "拼多多", "网易", "B站", "哔哩哔哩",
        "小米", "OPPO", "vivo", "滴滴", "蚂蚁", "Kimi", "豆包",
        "Shanghai AI Laboratory", "上海人工智能实验室"
    ],
    # 12分 - 其他知名公司
    "tier4": [
        "微软", "亚马逊", "IBM", "英特尔", "英伟达", "NVIDIA",
        "携程", "新浪", "微博", "知乎", "爱奇艺"
    ]
}

# 名校列表
TOP_SCHOOLS = [
    "清华", "北大", "北京大学", "交大", "上海交通", "复旦", "浙大", "浙江大学",
    "中科大", "南京大学", "哈工大", "哈尔滨工业", "西安交通", "武汉大学",
    "华中科技", "中山大学", "北航", "同济", "南开", "天津大学",
    "北理工", "电子科技", "西电", "北邮", "香港科技", "香港大学", "香港中文",
    "Carnegie", "Stanford", "MIT", "Berkeley", "CMU", "Columbia",
    "Cornell", "Princeton", "Harvard", "Yale", "Oxford", "Cambridge"
]


def should_exclude(row):
    """检查是否应排除"""
    all_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
    
    # 规则1: 工作年限 < 1年
    exp = row.get('总工作经验', '')
    if pd.notna(exp):
        match = re.search(r'([\d.]+)', str(exp))
        if match and float(match.group(1)) < 1:
            return True, "工作年限不足1年"
    
    # 规则2: 排除职位
    title = str(row.get('职位', ''))
    for keyword in EXCLUDE_TITLES:
        if keyword in title:
            return True, f"职位含排除词: {keyword}"
    
    return False, None


def score_tech(text):
    """技术方向评分"""
    text = str(text)
    
    for keyword in TECH_KEYWORDS["tier1"]:
        if keyword.lower() in text.lower():
            return 40, keyword
    for keyword in TECH_KEYWORDS["tier2"]:
        if keyword.lower() in text.lower():
            return 30, keyword
    for keyword in TECH_KEYWORDS["tier3"]:
        if keyword.lower() in text.lower():
            return 20, keyword
    for keyword in TECH_KEYWORDS["tier4"]:
        if keyword.lower() in text.lower():
            return 10, keyword
    
    return 0, None


def score_company(text):
    """公司背景评分"""
    text = str(text)
    
    for company in COMPANY_TIERS["tier1"]:
        if company in text:
            return 25, company
    for company in COMPANY_TIERS["tier2"]:
        if company in text:
            return 22, company
    for company in COMPANY_TIERS["tier3"]:
        if company in text:
            return 18, company
    for company in COMPANY_TIERS["tier4"]:
        if company in text:
            return 12, company
    
    return 5, None


def score_experience(exp_str):
    """工作年限评分"""
    if pd.isna(exp_str):
        return 10, "未知"
    
    match = re.search(r'([\d.]+)', str(exp_str))
    if not match:
        return 10, "未知"
    
    years = float(match.group(1))
    
    if 3 <= years <= 8:
        return 20, f"{years}年(黄金期)"
    elif 8 < years <= 12:
        return 15, f"{years}年(资深)"
    elif 1 <= years < 3:
        return 10, f"{years}年(潜力股)"
    elif years > 12:
        return 5, f"{years}年(偏管理)"
    else:
        return 5, f"{years}年(不足)"


def score_education(row):
    """学历评分"""
    edu_text = ' '.join([str(row.get(c, '')) for c in ['研究生学校', '本科学校', '学历', '研究生专业'] if pd.notna(row.get(c))])
    
    is_top_school = any(school in edu_text for school in TOP_SCHOOLS)
    degree = str(row.get('学历', ''))
    has_phd = '博' in degree
    has_master = '硕' in degree
    
    if is_top_school and has_phd:
        return 15, "名校博士"
    elif is_top_school and has_master:
        return 14, "名校硕士"
    elif has_phd:
        return 13, "博士"
    elif is_top_school:
        return 12, "名校本科"
    elif has_master:
        return 10, "硕士"
    else:
        return 6, "本科"


def get_priority(total_score, status):
    """计算优先级"""
    status = str(status) if pd.notna(status) else ""
    
    is_active = "在职" in status and "不看" not in status
    is_looking = "看机会" in status or "离职" in status
    
    if total_score >= 80 and is_looking:
        return "P0-今日联系", "🔥"
    elif total_score >= 60 and (is_looking or is_active):
        return "P1-本周联系", "⭐"
    elif total_score >= 40:
        return "P2-常规跟进", "📋"
    else:
        return "P3-入库观察", "📦"


def score_candidate(row):
    """评分单个候选人"""
    all_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
    
    # 各维度评分
    tech_score, tech_match = score_tech(all_text)
    company_score, company_match = score_company(all_text)
    exp_score, exp_label = score_experience(row.get('总工作经验'))
    edu_score, edu_label = score_education(row)
    
    # 总分
    total_score = tech_score + company_score + exp_score + edu_score
    
    # 优先级
    priority, emoji = get_priority(total_score, row.get('状态'))
    
    return {
        '技术匹配分': tech_score,
        '技术关键词': tech_match or '-',
        '公司背景分': company_score,
        '匹配公司': company_match or '-',
        '年限评分': exp_score,
        '年限标签': exp_label,
        '学历评分': edu_score,
        '学历标签': edu_label,
        '总分': total_score,
        '优先级': priority,
        '标记': emoji
    }


def main():
    print("=" * 60)
    print("🎯 通义候选人筛选与评分")
    print("=" * 60)
    
    # 读取数据
    df = pd.read_excel(INPUT_FILE)
    print(f"\n📊 原始数据: {len(df)} 人")
    
    # Step 1: 排除筛选
    exclude_results = df.apply(should_exclude, axis=1)
    df['排除原因'] = [r[1] for r in exclude_results]
    df['是否排除'] = [r[0] for r in exclude_results]
    
    excluded = df[df['是否排除'] == True]
    passed = df[df['是否排除'] == False].copy()
    
    print(f"   ❌ 排除: {len(excluded)} 人")
    print(f"   ✅ 通过: {len(passed)} 人")
    
    # Step 2: 评分
    print("\n🔍 开始评分...")
    scores = []
    for idx, row in passed.iterrows():
        score_result = score_candidate(row)
        scores.append(score_result)
    
    score_df = pd.DataFrame(scores)
    
    # 合并结果
    key_cols = ['姓名', '职位', '公司', '状态', '总工作经验', '学历', '技术领域', '技术专长']
    key_cols = [c for c in key_cols if c in passed.columns]
    
    result_df = pd.concat([passed[key_cols].reset_index(drop=True), score_df], axis=1)
    result_df = result_df.sort_values('总分', ascending=False)
    
    # 统计
    print("\n📈 优先级分布:")
    for p in ['P0-今日联系', 'P1-本周联系', 'P2-常规跟进', 'P3-入库观察']:
        count = len(result_df[result_df['优先级'] == p])
        emoji = {'P0': '🔥', 'P1': '⭐', 'P2': '📋', 'P3': '📦'}[p[:2]]
        print(f"   {emoji} {p}: {count} 人")
    
    # Top 10
    print("\n🏆 Top 10 候选人:")
    print("-" * 100)
    top10 = result_df.head(10)[['标记', '姓名', '总分', '技术关键词', '匹配公司', '学历标签', '优先级']]
    for _, r in top10.iterrows():
        print(f"   {r['标记']} {str(r['姓名']):<15} | 分数:{r['总分']:>3} | 技术:{str(r['技术关键词']):<12} | 公司:{str(r['匹配公司']):<8} | {r['学历标签']:<6} | {r['优先级']}")
    
    # 保存
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n💾 结果已保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
