#!/usr/bin/env python3
"""
脉脉候选人数据清洗脚本
功能：
1. 结构修复：处理CSV多行字段
2. 去重：按姓名+学校+职位去重，保留活跃度最高的
3. 噪音清理：移除社交关系文案
4. 字段标准化：新增当前公司、职位、学历等字段
"""

import pandas as pd
import re
from datetime import datetime

INPUT = "/Users/lillianliao/notion_rag/Agent-脉脉搜索结果_2025-12-26T13-04-56.csv"
OUTPUT_CLEAN = "/Users/lillianliao/notion_rag/Agent-脉脉搜索结果_清洗版.csv"
OUTPUT_SCORE = "/Users/lillianliao/notion_rag/Agent-脉脉搜索结果_评分版.csv"

# ============ 清洗配置 ============
INVALID_NAMES = ['脉脉助手', '?', '？', '']
SOCIAL_PATTERN = re.compile(r'(TA|他|她)有\d+个好友在此(公司|学校)')
SEPARATOR_PATTERN = re.compile(r'\n---\n|\n\n---\n\n')

# 985/211 学校名单（简化版）
ELITE_SCHOOLS = [
    '清华', '北大', '复旦', '交大', '浙大', '中科大', '南京大学', '哈工大', 
    '武大', '北航', '北邮', '东北大学', '同济', '华科', '中山', '西交',
    '华南理工', '电子科大', '北理工', '天津大学', '东南大学', '厦门大学',
    '吉林大学', '中国人民大学', '国防科技大学', '四川大学', '中南大学'
]

# 评分配置（与 score_agent.py 保持一致）
EXCLUDE_ROLES = ['运维', '测试', '销售', '商务']  # 移除"产品经理"和"产品"，保留AI产品相关候选人
TECH1 = ['LLM', '大模型', 'Agent', '智能体', 'GPT', 'RAG', 'embedding', 'prompt', 'RLHF', 'langchain', 'Mcp', 'MCP', 'GraphRAG', 'Multi-Agent']
TECH2 = ['NLP', '自然语言', '对话', '问答', '知识图谱', 'BERT', 'Transformer']
TECH3 = ['算法', '机器学习', '深度学习', '推荐', 'AI', 'PyTorch', 'CV', '多模态']
TECH4 = ['后端', '架构', 'Python', 'Golang', '工程师', 'Java']
COMP1 = ['Qwen', '通义', '百度', '字节', 'Seed', '阿里', '腾讯', '华为', 'OpenAI', 'Google', '文心', 'Meta', '光年之外', '京东', '蚂蚁']
COMP2 = ['智谱', '月之暗面', 'Moonshot', 'MiniMax', '百川', '商汤', '旷视', '阶跃']
COMP3 = ['快手', '美团', '小红书', '网易', 'B站', '小米', 'OPPO', '滴滴', '携程']

def clean_social_noise(text):
    """移除社交关系噪音"""
    if pd.isna(text):
        return text
    return SOCIAL_PATTERN.sub('', str(text)).strip()

def clean_separators(text):
    """清理分隔符，合并多行内容"""
    if pd.isna(text):
        return text
    text = SEPARATOR_PATTERN.sub(' | ', str(text))
    text = re.sub(r'\n+', ' ', text)
    return text.strip()

def get_activity_score(activity_str):
    """计算活跃度分数（用于去重时选择最活跃的记录）"""
    if pd.isna(activity_str):
        return 0
    s = str(activity_str)
    if '分钟内' in s or '刚刚' in s:
        return 100
    if '小时内' in s:
        match = re.search(r'(\d+)小时', s)
        return 90 - int(match.group(1)) if match else 85
    if '天' in s:
        match = re.search(r'(\d+)天', s)
        return 50 - int(match.group(1)) if match else 45
    return 10

def infer_work_years(row):
    """从工作经历推断工作年限"""
    if pd.notna(row.get('工作年限')):
        return row['工作年限']
    
    time_range = str(row.get('工作1-time_range', ''))
    if '至今' in time_range:
        match = re.search(r'(\d{4})\.?\d*-至今', time_range)
        if match:
            start_year = int(match.group(1))
            return datetime.now().year - start_year
    return None

def extract_company(title_field):
    """从工作1-title提取公司名"""
    if pd.isna(title_field):
        return ''
    text = str(title_field)
    # 常见格式: "职位公司名时间" 或 "职位公司名 ? 部门时间"
    patterns = [
        r'(?:工程师|经理|专家|负责人|研发|开发|算法|架构师|总监|Lead)(.+?)(?:\d{4}\.|至今|\?)',
        r'^.+?([^\d]+?)(?:\d{4}\.|\d{4}-)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            company = match.group(1).strip()
            # 清理部门标记
            company = re.sub(r'\s*\?\s*.+$', '', company)
            if len(company) > 1 and len(company) < 30:
                return company
    return ''

def extract_position(title_field):
    """从工作1-title提取职位"""
    if pd.isna(title_field):
        return ''
    text = str(title_field)
    # 职位通常在最前面
    match = re.match(r'^([^0-9]+?)(?:[A-Za-z\u4e00-\u9fa5]{2,}公司|字节|腾讯|阿里|百度|华为|美团|快手|小红书)', text)
    if match:
        return match.group(1).strip()[:30]
    # 尝试匹配常见职位
    pos_match = re.match(r'^((?:AI|高级|资深)?(?:算法|研发|开发|产品|架构|技术)?(?:工程师|经理|专家|负责人|总监|Lead)[^\d]{0,10})', text)
    if pos_match:
        return pos_match.group(1).strip()
    return ''

def get_education_level(edu_text):
    """推断最高学历"""
    if pd.isna(edu_text):
        return '未知'
    text = str(edu_text)
    if '博士' in text:
        return '博士'
    if '硕士' in text or '硕' in text:
        return '硕士'
    if '本科' in text:
        return '本科'
    if '专科' in text:
        return '专科'
    return '未知'

def is_elite_school(edu_text):
    """判断是否985/211"""
    if pd.isna(edu_text):
        return '否'
    text = str(edu_text)
    return '是' if any(school in text for school in ELITE_SCHOOLS) else '否'

def calculate_score(row, all_text):
    """计算候选人评分"""
    # 技术方向分数
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
    
    # 公司背景分数
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
    
    # 经验分数
    years = row.get('工作年限_推断')
    exp_s = 10
    if pd.notna(years):
        y = float(years)
        if 3 <= y <= 8: exp_s = 20
        elif 8 < y <= 12: exp_s = 15
        elif 1 <= y < 3: exp_s = 10
        else: exp_s = 5
    
    # 学历分数
    edu_text = str(row.get('教育经历', ''))
    is_top = row.get('是否985/211') == '是'
    has_master = row.get('最高学历') in ['硕士', '博士']
    if is_top and has_master: edu_s = 15
    elif is_top: edu_s = 12
    elif has_master: edu_s = 10
    else: edu_s = 6
    
    return tech_s + comp_s + exp_s + edu_s, tech_kw, comp_kw

def get_priority(total_score, activity_str):
    """根据分数和活跃度确定优先级"""
    is_active = '小时内' in str(activity_str) or '刚刚' in str(activity_str) or '分钟内' in str(activity_str)
    is_recent = '天' in str(activity_str)
    
    if total_score >= 80 and is_active:
        return 'P0-今日联系'
    elif total_score >= 60 and (is_active or is_recent):
        return 'P1-本周联系'
    elif total_score >= 40:
        return 'P2-常规跟进'
    else:
        return 'P3-入库观察'

def get_role_type(title_field, all_text):
    """判断角色类型：技术 / 产品经理"""
    title = str(title_field) if pd.notna(title_field) else ''
    
    # 产品经理关键词
    pm_keywords = ['产品经理', '产品专家', '产品负责人', '产品运营', '产品总监', 'PM']
    for kw in pm_keywords:
        if kw in title or kw in all_text:
            return '产品经理'
    
    # 技术关键词（更广泛）
    tech_keywords = ['工程师', '开发', '算法', '架构', '研发', '技术', 'Engineer', 'Developer', 
                     'Researcher', '研究员', 'Lead', '总监', '专家', 'Intern', '实习']
    for kw in tech_keywords:
        if kw in title:
            return '技术'
    
    # 默认根据内容判断
    if any(kw in all_text for kw in ['开发', '算法', '工程', '研发', '架构', '代码', 'Python', 'Java', 'Golang']):
        return '技术'
    
    return '其他'

def main():
    print("=" * 50)
    print("脉脉候选人数据清洗与评分")
    print("=" * 50)
    
    # 1. 读取数据
    df = pd.read_csv(INPUT, encoding='utf-8-sig')
    print(f"\n📥 原始数据: {len(df)} 行")
    
    # 2. 过滤无效记录
    df = df[df['姓名'].notna()]
    df = df[~df['姓名'].astype(str).str.strip().isin(INVALID_NAMES)]
    df = df[~df['姓名'].astype(str).str.contains(r'^[?\s]+$', regex=True, na=False)]
    print(f"📋 过滤无效记录后: {len(df)} 行")
    
    # 3. 清洗噪音文本
    text_columns = df.select_dtypes(include=['object']).columns
    for col in text_columns:
        df[col] = df[col].apply(clean_social_noise)
        if col in ['工作经历', '教育经历']:
            df[col] = df[col].apply(clean_separators)
    print("🧹 噪音文本已清理")
    
    # 4. 计算活跃度分数
    df['_活跃度分数'] = df['活跃状态'].apply(get_activity_score)
    
    # 5. 去重（保留活跃度最高的）
    df = df.sort_values('_活跃度分数', ascending=False)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['姓名', '教育1-school'], keep='first')
    print(f"🔄 去重: {before_dedup} → {len(df)} 行 (移除 {before_dedup - len(df)} 条重复)")
    
    # 6. 推断工作年限
    df['工作年限_推断'] = df.apply(infer_work_years, axis=1)
    
    # 7. 新增标准化字段
    df['当前公司'] = df['工作1-title'].apply(extract_company)
    df['当前职位'] = df['工作1-title'].apply(extract_position)
    df['最高学历'] = df['教育经历'].apply(get_education_level)
    df['是否985/211'] = df['教育经历'].apply(is_elite_school)
    
    # 8. 删除临时列
    df = df.drop(columns=['_活跃度分数'])
    
    # 9. 保存清洗版
    df.to_csv(OUTPUT_CLEAN, index=False, encoding='utf-8-sig')
    print(f"\n✅ 清洗版已保存: {OUTPUT_CLEAN}")
    
    # ============ 评分阶段 ============
    print("\n" + "=" * 50)
    print("开始评分...")
    print("=" * 50)
    
    results = []
    
    for _, row in df.iterrows():
        all_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
        
        # 评分（不再排除任何人）
        total_score, tech_kw, comp_kw = calculate_score(row, all_text)
        priority = get_priority(total_score, row.get('活跃状态', ''))
        role_type = get_role_type(row.get('工作1-title'), all_text)
        
        results.append({
            '姓名': row['姓名'],
            '活跃状态': row.get('活跃状态', ''),
            '角色类型': role_type,
            '当前公司': row.get('当前公司', ''),
            '当前职位': row.get('当前职位', ''),
            '工作年限': row.get('工作年限_推断', ''),
            '最高学历': row.get('最高学历', ''),
            '是否985/211': row.get('是否985/211', ''),
            '总分': total_score,
            '技术关键词': tech_kw,
            '匹配公司': comp_kw,
            '优先级': priority
        })
    
    # 排序：先按角色类型（技术优先），再按总分降序，再按活跃度
    result_df = pd.DataFrame(results)
    result_df['_活跃度分数'] = result_df['活跃状态'].apply(get_activity_score)
    result_df = result_df.sort_values(
        by=['角色类型', '总分', '_活跃度分数'], 
        ascending=[True, False, False]  # 技术 < 产品经理 < 其他（字母序），分数降序
    )
    result_df = result_df.drop(columns=['_活跃度分数'])
    
    print(f"\n📊 评分统计:")
    print(f"  - 总人数: {len(result_df)} 人")
    
    print(f"\n👤 角色类型分布:")
    for role in ['技术', '产品经理', '其他']:
        count = len(result_df[result_df['角色类型'] == role])
        if count > 0:
            print(f"  {role}: {count} 人")
    
    print(f"\n📈 优先级分布:")
    for p in ['P0-今日联系', 'P1-本周联系', 'P2-常规跟进', 'P3-入库观察']:
        count = len(result_df[result_df['优先级'] == p])
        print(f"  {p}: {count} 人")
    
    print(f"\n🌟 技术类 Top 15:")
    tech_df = result_df[result_df['角色类型'] == '技术']
    for _, r in tech_df.head(15).iterrows():
        print(f"  {r['姓名']:<12} | {str(r['活跃状态']):<10} | 分数:{r['总分']:>2} | {r['技术关键词']:<10} | {r['匹配公司']:<8} | {r['优先级']}")
    
    pm_df = result_df[result_df['角色类型'] == '产品经理']
    if len(pm_df) > 0:
        print(f"\n📋 产品经理类 Top 10:")
        for _, r in pm_df.head(10).iterrows():
            print(f"  {r['姓名']:<12} | {str(r['活跃状态']):<10} | 分数:{r['总分']:>2} | {r['技术关键词']:<10} | {r['匹配公司']:<8} | {r['优先级']}")
    
    result_df.to_csv(OUTPUT_SCORE, index=False, encoding='utf-8-sig')
    print(f"\n✅ 评分版已保存: {OUTPUT_SCORE}")
    
    print("\n" + "=" * 50)
    print("处理完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
