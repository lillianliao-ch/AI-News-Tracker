#!/usr/bin/env python3
"""
脉脉候选人数据批量清洗与评分脚本
支持自动检测编码，统一输出格式
"""

import pandas as pd
import re
import os
from datetime import datetime

# ============ 待处理文件列表（已去重） ============
FILES_TO_PROCESS = [
    "baidu-算法-脉脉搜索结果_2025-12-23T09-27-01.csv",        # 3 (移除4)
    "minimax-算法-脉脉_2025-12-23(1).csv",                    # 5
    "minimax-负责人-脉脉_2025-1223.csv",                      # 6
    "华为-2012实验室-脉脉搜索结果_2025-12-23T10-25-44.csv",    # 7
    "华为-AI算法-脉脉搜索结果_2025-12-23T10-25-44.csv",        # 8
    "华为-算法-脉脉搜索结果_2025-12-23T10-25-44.csv",          # 9
    "小米-算法-脉脉搜索结果_2025-12-24T06-45-24.csv",          # 10
    "阶跃-算法-脉脉_2025-12-23.csv",                          # 11
    "阶跃-负责人-脉脉_2025-12-23.csv",                        # 12
    "智谱-算法-脉脉_2025-12-231.csv",                         # 13
    "智谱-负责人-脉脉_2025-12-232.csv",                       # 14
    "高德-脉脉搜索结果_2025-12-24T11-48-22.csv",              # 15 (移除16)
    "海康2-脉脉搜索结果_2025-12-26T01-36-45.csv",             # 17
    "第六镜-脉脉搜索结果_2025-12-25T13-57-04.csv",            # 18
    "美团算法-脉脉搜索结果_2025-12-23T12-33-43.csv",          # 19
    # 新增文件 2025-12-27/28
    "零一-脉脉搜索结果_2025-12-27T12-41-59.csv",              # 新增
    "百川-脉脉搜索结果_2025-12-28T07-26-54.csv",              # 新增
    "上海人工智能研究院-脉脉搜索结果_2025-12-28T06-04-10.csv", # 新增
    "奇虎-脉脉搜索结果_2025-12-27T13-25-20.csv",              # 新增
    "科大讯飞-脉脉搜索结果_2025-12-28T07-34-52.csv",          # 新增
    "旷世-脉脉搜索结果_2025-12-25T13-48-15.csv",              # 新增
]

BASE_DIR = "/Users/lillianliao/notion_rag"
OUTPUT_DIR = "/Users/lillianliao/notion_rag/cleaned_results"

# ============ 清洗配置 ============
INVALID_NAMES = ['脉脉助手', '?', '？', '']
SOCIAL_PATTERN = re.compile(r'(TA|他|她)有\d+个好友在此(公司|学校)')
SEPARATOR_PATTERN = re.compile(r'\n---\n|\n\n---\n\n')

ELITE_SCHOOLS = [
    '清华', '北大', '复旦', '交大', '浙大', '中科大', '南京大学', '哈工大', 
    '武大', '北航', '北邮', '东北大学', '同济', '华科', '中山', '西交',
    '华南理工', '电子科大', '北理工', '天津大学', '东南大学', '厦门大学',
    '吉林大学', '中国人民大学', '国防科技大学', '四川大学', '中南大学'
]

TECH1 = ['LLM', '大模型', 'Agent', '智能体', 'GPT', 'RAG', 'embedding', 'prompt', 'RLHF', 'langchain', 'Mcp', 'MCP', 'GraphRAG', 'Multi-Agent', '文心']
TECH2 = ['NLP', '自然语言', '对话', '问答', '知识图谱', 'BERT', 'Transformer']
TECH3 = ['算法', '机器学习', '深度学习', '推荐', 'AI', 'PyTorch', 'CV', '多模态']
TECH4 = ['后端', '架构', 'Python', 'Golang', '工程师', 'Java']
COMP1 = ['Qwen', '通义', '百度', '字节', 'Seed', '阿里', '腾讯', '华为', 'OpenAI', 'Google', '文心', 'Meta', '光年之外', '京东', '蚂蚁']
COMP2 = ['智谱', '月之暗面', 'Moonshot', 'MiniMax', '百川', '商汤', '旷视', '阶跃']
COMP3 = ['快手', '美团', '小红书', '网易', 'B站', '小米', 'OPPO', '滴滴', '携程', '高德', '海康']

def read_csv_auto_encoding(filepath):
    """自动检测编码读取CSV"""
    encodings = ['utf-8-sig', 'utf-8', 'gb18030', 'gbk', 'utf-16']
    for enc in encodings:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            if '姓名' in df.columns:
                return df
        except:
            continue
    raise ValueError(f"无法读取文件: {filepath}")

def clean_social_noise(text):
    if pd.isna(text):
        return text
    return SOCIAL_PATTERN.sub('', str(text)).strip()

def clean_separators(text):
    if pd.isna(text):
        return text
    text = SEPARATOR_PATTERN.sub(' | ', str(text))
    text = re.sub(r'\n+', ' ', text)
    return text.strip()

def get_activity_score(activity_str):
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
    if pd.isna(title_field):
        return ''
    text = str(title_field)
    patterns = [
        r'(?:工程师|经理|专家|负责人|研发|开发|算法|架构师|总监|Lead)(.+?)(?:\d{4}\.|至今|\?)',
        r'^.+?([^\d]+?)(?:\d{4}\.|\d{4}-)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            company = match.group(1).strip()
            company = re.sub(r'\s*\?\s*.+$', '', company)
            if len(company) > 1 and len(company) < 30:
                return company
    return ''

def extract_position(title_field):
    if pd.isna(title_field):
        return ''
    text = str(title_field)
    pos_match = re.match(r'^((?:AI|高级|资深)?(?:算法|研发|开发|产品|架构|技术)?(?:工程师|经理|专家|负责人|总监|Lead)[^\d]{0,10})', text)
    if pos_match:
        return pos_match.group(1).strip()
    return text[:30] if len(text) > 0 else ''

def get_education_level(edu_text):
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
    if pd.isna(edu_text):
        return '否'
    text = str(edu_text)
    return '是' if any(school in text for school in ELITE_SCHOOLS) else '否'

def calculate_score(row, all_text):
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
    
    years = row.get('工作年限_推断')
    exp_s = 10
    if pd.notna(years):
        y = float(years)
        if 3 <= y <= 8: exp_s = 20
        elif 8 < y <= 12: exp_s = 15
        elif 1 <= y < 3: exp_s = 10
        else: exp_s = 5
    
    is_top = row.get('是否985/211') == '是'
    has_master = row.get('最高学历') in ['硕士', '博士']
    if is_top and has_master: edu_s = 15
    elif is_top: edu_s = 12
    elif has_master: edu_s = 10
    else: edu_s = 6
    
    return tech_s + comp_s + exp_s + edu_s, tech_kw, comp_kw

def get_priority(total_score, activity_str):
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
    title = str(title_field) if pd.notna(title_field) else ''
    
    pm_keywords = ['产品经理', '产品专家', '产品负责人', '产品运营', '产品总监', 'PM']
    for kw in pm_keywords:
        if kw in title or kw in all_text:
            return '产品经理'
    
    tech_keywords = ['工程师', '开发', '算法', '架构', '研发', '技术', 'Engineer', 'Developer', 
                     'Researcher', '研究员', 'Lead', '总监', '专家', 'Intern', '实习', 'SRE', '运维']
    for kw in tech_keywords:
        if kw in title:
            return '技术'
    
    if any(kw in all_text for kw in ['开发', '算法', '工程', '研发', '架构', '代码', 'Python', 'Java', 'Golang']):
        return '技术'
    
    return '其他'

def process_file(input_file, output_clean, output_score):
    """处理单个文件"""
    print(f"\n{'='*60}")
    print(f"📁 处理: {os.path.basename(input_file)}")
    print(f"{'='*60}")
    
    try:
        df = read_csv_auto_encoding(input_file)
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None
    
    print(f"📥 原始数据: {len(df)} 行")
    
    # 过滤无效记录
    df = df[df['姓名'].notna()]
    df = df[~df['姓名'].astype(str).str.strip().isin(INVALID_NAMES)]
    df = df[~df['姓名'].astype(str).str.contains(r'^[?\s]+$', regex=True, na=False)]
    
    # 清洗噪音文本
    text_columns = df.select_dtypes(include=['object']).columns
    for col in text_columns:
        df[col] = df[col].apply(clean_social_noise)
        if col in ['工作经历', '教育经历']:
            df[col] = df[col].apply(clean_separators)
    
    # 计算活跃度分数并去重
    if '活跃状态' not in df.columns:
        df['活跃状态'] = ''
    df['_活跃度分数'] = df['活跃状态'].apply(get_activity_score)
    df = df.sort_values('_活跃度分数', ascending=False)
    before_dedup = len(df)
    
    # 去重键
    dedup_cols = ['姓名']
    if '教育1-school' in df.columns:
        dedup_cols.append('教育1-school')
    df = df.drop_duplicates(subset=dedup_cols, keep='first')
    print(f"🔄 去重: {before_dedup} → {len(df)} 行")
    
    # 推断工作年限
    df['工作年限_推断'] = df.apply(infer_work_years, axis=1)
    
    # 新增标准化字段
    if '工作1-title' in df.columns:
        df['当前公司'] = df['工作1-title'].apply(extract_company)
        df['当前职位'] = df['工作1-title'].apply(extract_position)
    else:
        df['当前公司'] = ''
        df['当前职位'] = ''
    
    if '教育经历' in df.columns:
        df['最高学历'] = df['教育经历'].apply(get_education_level)
        df['是否985/211'] = df['教育经历'].apply(is_elite_school)
    else:
        df['最高学历'] = '未知'
        df['是否985/211'] = '否'
    
    df = df.drop(columns=['_活跃度分数'], errors='ignore')
    
    # 保存清洗版
    df.to_csv(output_clean, index=False, encoding='utf-8-sig')
    
    # 评分
    results = []
    for _, row in df.iterrows():
        all_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
        total_score, tech_kw, comp_kw = calculate_score(row, all_text)
        priority = get_priority(total_score, row.get('活跃状态', ''))
        title_field = row.get('工作1-title', '')
        role_type = get_role_type(title_field, all_text)
        
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
    
    result_df = pd.DataFrame(results)
    result_df['_活跃度分数'] = result_df['活跃状态'].apply(get_activity_score)
    result_df = result_df.sort_values(
        by=['角色类型', '总分', '_活跃度分数'], 
        ascending=[True, False, False]
    )
    result_df = result_df.drop(columns=['_活跃度分数'])
    
    # 统计
    tech_count = len(result_df[result_df['角色类型'] == '技术'])
    pm_count = len(result_df[result_df['角色类型'] == '产品经理'])
    p0_count = len(result_df[result_df['优先级'] == 'P0-今日联系'])
    p1_count = len(result_df[result_df['优先级'] == 'P1-本周联系'])
    
    print(f"📊 结果: {len(result_df)}人 (技术:{tech_count}, 产品经理:{pm_count})")
    print(f"📈 优先级: P0={p0_count}, P1={p1_count}")
    
    # Top 3
    tech_df = result_df[result_df['角色类型'] == '技术']
    if len(tech_df) > 0:
        print(f"🌟 技术Top3: {', '.join(tech_df.head(3)['姓名'].tolist())}")
    
    result_df.to_csv(output_score, index=False, encoding='utf-8-sig')
    
    return {
        'file': os.path.basename(input_file),
        'total': len(result_df),
        'tech': tech_count,
        'pm': pm_count,
        'p0': p0_count,
        'p1': p1_count
    }

def main():
    print("=" * 60)
    print("🚀 脉脉候选人数据批量清洗与评分")
    print("=" * 60)
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_stats = []
    
    for filename in FILES_TO_PROCESS:
        input_path = os.path.join(BASE_DIR, filename)
        
        if not os.path.exists(input_path):
            print(f"\n⚠️ 跳过不存在的文件: {filename}")
            continue
        
        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(filename))[0]
        output_clean = os.path.join(OUTPUT_DIR, f"{base_name}_清洗版.csv")
        output_score = os.path.join(OUTPUT_DIR, f"{base_name}_评分版.csv")
        
        stats = process_file(input_path, output_clean, output_score)
        if stats:
            all_stats.append(stats)
    
    # 汇总统计
    print("\n" + "=" * 60)
    print("📊 批处理汇总")
    print("=" * 60)
    
    total_people = sum(s['total'] for s in all_stats)
    total_tech = sum(s['tech'] for s in all_stats)
    total_pm = sum(s['pm'] for s in all_stats)
    total_p0 = sum(s['p0'] for s in all_stats)
    total_p1 = sum(s['p1'] for s in all_stats)
    
    print(f"✅ 处理文件: {len(all_stats)} 个")
    print(f"👥 总人数: {total_people} 人")
    print(f"💻 技术: {total_tech} 人")
    print(f"📋 产品经理: {total_pm} 人")
    print(f"🔥 P0-今日联系: {total_p0} 人")
    print(f"📅 P1-本周联系: {total_p1} 人")
    print(f"\n📁 输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
