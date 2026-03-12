#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脉脉候选人匹配度评分脚本
针对 AI Agent 工程师岗位
"""

import pandas as pd
import re

# 文件路径
INPUT_FILE = "/Users/lillianliao/notion_rag/文心-脉脉搜索结果_通过.csv"
OUTPUT_FILE = "/Users/lillianliao/notion_rag/文心-脉脉搜索结果_评分.csv"

# ==================== 评分规则配置 ====================

# 技术方向关键词（权重从高到低）
TECH_KEYWORDS = {
    # 40分 - 直接相关
    "tier1": [
        "文心", "LLM", "大模型", "Agent", "智能体", "GPT", "ERNIE",
        "RAG", "Retrieval", "向量", "embedding", "prompt", "RLHF",
        "langchain", "LangChain", "CoT", "思维链", "多模态大模型",
        "对话系统", "对话机器人", "ChatBot", "copilot", "Copilot"
    ],
    # 30分 - 强相关
    "tier2": [
        "NLP", "自然语言", "语言模型", "对话", "问答", "知识图谱",
        "搜索算法", "语义理解", "文本", "BERT", "Transformer",
        "意图识别", "实体识别", "情感分析", "机器翻译"
    ],
    # 20分 - 相关
    "tier3": [
        "算法", "机器学习", "深度学习", "推荐", "搜索", "研究员",
        "AI", "人工智能", "模型", "训练", "推理", "PyTorch", "TensorFlow"
    ],
    # 10分 - 潜在相关
    "tier4": [
        "后端", "架构", "分布式", "Python", "Golang", "工程师"
    ]
}

# 公司背景分层
COMPANY_TIERS = {
    # 25分 - 顶级 AI Lab
    "tier1": [
        "百度", "文心", "字节", "Seed", "seed", "阿里", "达摩院",
        "腾讯", "混元", "华为", "盘古", "OpenAI", "Google", "DeepMind"
    ],
    # 22分 - 六小龙 + 顶级 AI 独角兽
    "tier2": [
        "智谱", "月之暗面", "MiniMax", "百川", "零一万物", "阶跃星辰",  # 六小龙
        "商汤", "旷视", "依图", "云从",  # AI 四小龙
        "科大讯飞", "第四范式", "地平线", "寒武纪"
    ],
    # 18分 - 知名互联网 + AI 新锐
    "tier3": [
        "快手", "美团", "京东", "小红书", "拼多多", "网易", "B站", "哔哩哔哩",
        "小米", "OPPO", "vivo", "滴滴", "蚂蚁", "蚂蚁金服",
        "Kimi", "通义", "文小言", "豆包"
    ],
    # 12分 - 其他知名公司
    "tier4": [
        "微软", "亚马逊", "IBM", "英特尔", "英伟达", "NVIDIA",
        "携程", "新浪", "微博", "知乎", "爱奇艺", "优酷"
    ]
}

# 活跃度权重
ACTIVE_PRIORITY = {
    "刚刚活跃": 3,
    "今日活跃": 3,
    "近1周活跃": 2,
    "近1月活跃": 1
}


def score_tech_direction(text):
    """技术方向评分（满分40分）"""
    text = str(text).lower()
    
    for keyword in TECH_KEYWORDS["tier1"]:
        if keyword.lower() in text:
            return 40, keyword
    
    for keyword in TECH_KEYWORDS["tier2"]:
        if keyword.lower() in text:
            return 30, keyword
    
    for keyword in TECH_KEYWORDS["tier3"]:
        if keyword.lower() in text:
            return 20, keyword
    
    for keyword in TECH_KEYWORDS["tier4"]:
        if keyword.lower() in text:
            return 10, keyword
    
    return 0, None


def score_company(text):
    """公司背景评分（满分25分）"""
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


def score_experience(years_str):
    """工作年限评分（满分20分）"""
    if pd.isna(years_str):
        return 10, "未知"
    
    try:
        years = float(years_str)
    except:
        match = re.search(r'(\d+)', str(years_str))
        years = int(match.group(1)) if match else 0
    
    if 3 <= years <= 8:
        return 20, f"{years}年(黄金期)"
    elif 8 < years <= 12:
        return 15, f"{years}年(资深)"
    elif 1 <= years < 3:
        return 10, f"{years}年(潜力股)"
    elif years > 12:
        return 5, f"{years}年(偏管理)"
    else:
        return 5, "经验不足"


def score_education(edu_text):
    """学历评分（满分15分）"""
    text = str(edu_text)
    
    # 985/211 院校列表（部分）
    top_schools = [
        "清华", "北大", "北京大学", "交大", "上海交通", "复旦", "浙大", "浙江大学",
        "中科大", "南京大学", "哈工大", "哈尔滨工业", "西安交通", "武汉大学",
        "华中科技", "中山大学", "北航", "北京航空", "同济", "南开", "天津大学",
        "北理工", "北京理工", "电子科技", "成电", "西电", "北邮", "北京邮电",
        "Carnegie", "Stanford", "MIT", "Berkeley", "CMU"
    ]
    
    is_top_school = any(school in text for school in top_schools)
    has_master_phd = "硕" in text or "博" in text or "研究生" in text
    
    if is_top_school and has_master_phd:
        return 15, "985硕博"
    elif is_top_school:
        return 12, "985本科"
    elif has_master_phd:
        return 10, "硕博"
    else:
        return 6, "本科"


def get_priority(total_score, active_status):
    """计算优先级"""
    active_weight = ACTIVE_PRIORITY.get(active_status, 0)
    
    if total_score >= 80 and active_weight >= 3:
        return "P0-今日联系", "🔥"
    elif total_score >= 60 and active_weight >= 2:
        return "P1-本周联系", "⭐"
    elif total_score >= 40:
        return "P2-常规跟进", "📋"
    else:
        return "P3-入库观察", "📦"


def score_candidate(row):
    """对单个候选人评分"""
    # 合并所有文本用于匹配
    all_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
    
    # 各维度评分
    tech_score, tech_match = score_tech_direction(all_text)
    company_score, company_match = score_company(all_text)
    exp_score, exp_label = score_experience(row.get('工作年限'))
    
    # 学历评分（查找教育相关列）
    edu_text = ""
    for col in row.index:
        if '学校' in col or 'school' in col.lower() or '教育' in col:
            edu_text += str(row.get(col, '')) + " "
    edu_score, edu_label = score_education(edu_text if edu_text else all_text)
    
    # 总分
    total_score = tech_score + company_score + exp_score + edu_score
    
    # 优先级
    active_status = str(row.get('活跃状态', ''))
    priority, emoji = get_priority(total_score, active_status)
    
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
    print("🎯 AI Agent 工程师候选人匹配评分")
    print("=" * 60)
    
    # 读取数据
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"\n📊 待评分人数: {len(df)}")
    
    # 评分
    print("\n🔍 开始评分...")
    scores = []
    for idx, row in df.iterrows():
        score_result = score_candidate(row)
        scores.append(score_result)
    
    # 合并结果
    score_df = pd.DataFrame(scores)
    result_df = pd.concat([df[['姓名', '活跃状态', '工作年限']], score_df], axis=1)
    
    # 按总分排序
    result_df = result_df.sort_values('总分', ascending=False)
    
    # 统计结果
    print("\n📈 评分结果统计:")
    print(f"   🔥 P0-今日联系: {len(result_df[result_df['优先级'] == 'P0-今日联系'])} 人")
    print(f"   ⭐ P1-本周联系: {len(result_df[result_df['优先级'] == 'P1-本周联系'])} 人")
    print(f"   📋 P2-常规跟进: {len(result_df[result_df['优先级'] == 'P2-常规跟进'])} 人")
    print(f"   📦 P3-入库观察: {len(result_df[result_df['优先级'] == 'P3-入库观察'])} 人")
    
    # 显示 Top 10
    print("\n🏆 Top 10 候选人:")
    print("-" * 80)
    top10 = result_df.head(10)[['标记', '姓名', '总分', '技术关键词', '匹配公司', '优先级']]
    for idx, row in top10.iterrows():
        print(f"   {row['标记']} {row['姓名']:<10} | 总分:{row['总分']:>3} | 技术:{row['技术关键词']:<8} | 公司:{row['匹配公司']:<8} | {row['优先级']}")
    
    # 保存结果
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n💾 详细结果已保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
