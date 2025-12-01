#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的候选人数据分析脚本
用于分析AIGC产品经理岗位的候选人匹配度
"""

import pandas as pd
import sys
import os

def check_senior_pm_requirement(row):
    """检查是否符合资深产品经理要求"""
    # 必须有产品经理经验
    senior_pm_keywords = ['产品经理', '产品总监', '产品负责人', '产品专家', 'PM', 'Product Manager', '产品副总裁']
    senior_indicators = ['高级', '资深', '首席', '总监', '专家', '负责人', 'Senior', 'Lead', 'Principal']
    
    has_pm_experience = False
    is_senior = False
    
    for i in range(1, 4):
        position_col = f'工作经历{i}职位'
        if pd.notna(row[position_col]):
            position = str(row[position_col])
            # 检查是否有产品经理经验
            if any(keyword in position for keyword in senior_pm_keywords):
                has_pm_experience = True
                # 检查是否资深
                if any(indicator in position for indicator in senior_indicators):
                    is_senior = True
    
    # 工作年限判断资深度
    work_years = row.get('工作年限', 0)
    if pd.notna(work_years) and work_years >= 5:
        is_senior = True
    
    return has_pm_experience, is_senior

def check_industry_match(row):
    """检查行业匹配度"""
    # 核心行业关键词
    ai_companies = ['字节跳动', '腾讯', '阿里', '百度', '美团', '快手', '小红书', '网易', 'B站', 'bilibili']
    music_companies = ['网易云音乐', 'QQ音乐', '酷狗', '酷我', '喜马拉雅', '荔枝', '全民K歌']
    content_companies = ['抖音', 'TikTok', '快手', '小红书', 'B站', 'bilibili', '爱奇艺', '优酷', '腾讯视频']
    
    # AI/技术职位关键词
    ai_positions = ['AI', 'AIGC', '人工智能', '机器学习', 'ML', '深度学习', '算法', '自然语言', 'NLP', 'CV', '计算机视觉']
    music_positions = ['音频', '音乐', '声音', '语音', '播客', 'K歌', '直播']
    content_positions = ['内容', '创作', '生成', '编辑', '短视频', '视频', '图像', '创意']
    
    industry_score = 0
    industry_match = []
    
    for i in range(1, 4):
        company_col = f'工作经历{i}公司'
        position_col = f'工作经历{i}职位'
        
        if pd.notna(row[company_col]):
            company = str(row[company_col])
            # AI互联网公司
            if any(comp in company for comp in ai_companies):
                industry_score += 30
                industry_match.append(f'AI互联网公司: {company}')
            # 音乐公司
            if any(comp in company for comp in music_companies):
                industry_score += 40
                industry_match.append(f'音乐行业: {company}')
            # 内容公司
            if any(comp in company for comp in content_companies):
                industry_score += 35
                industry_match.append(f'内容行业: {company}')
        
        if pd.notna(row[position_col]):
            position = str(row[position_col])
            # AI相关职位
            if any(keyword in position for keyword in ai_positions):
                industry_score += 25
                industry_match.append(f'AI相关职位: {position}')
            # 音乐相关职位
            if any(keyword in position for keyword in music_positions):
                industry_score += 30
                industry_match.append(f'音乐相关职位: {position}')
            # 内容相关职位
            if any(keyword in position for keyword in content_positions):
                industry_score += 25
                industry_match.append(f'内容相关职位: {position}')
    
    return min(industry_score, 100), industry_match

def get_relevant_experience_score(row):
    """计算相关经验评分"""
    # 首先检查基础要求
    has_pm, is_senior = check_senior_pm_requirement(row)
    if not has_pm:
        return 0, []  # 没有产品经理经验直接淘汰
    
    industry_score, industry_details = check_industry_match(row)
    if industry_score < 20:  # 行业匹配度太低
        return 0, []
    
    # 基础产品经理分数
    base_score = 40 if is_senior else 20
    
    # 工作年限加分
    work_years = row.get('工作年限', 0)
    if pd.notna(work_years):
        if work_years >= 8:
            base_score += 20
        elif work_years >= 5:
            base_score += 15
        elif work_years >= 3:
            base_score += 10
    
    total_score = base_score + industry_score
    return min(total_score, 100), industry_details

def get_education_score(row):
    """计算教育背景评分"""
    score = 0
    
    # 相关专业关键词
    relevant_majors = ['计算机', '人工智能', '软件', '信息', '设计', '交互', '数字媒体', '电子', '自动化']
    
    for i in range(1, 4):
        major_col = f'教育经历{i}专业'
        degree_col = f'教育经历{i}学历'
        school_col = f'教育经历{i}学校'
        
        if pd.notna(row[major_col]):
            major = str(row[major_col])
            if any(keyword in major for keyword in relevant_majors):
                score += 25
                
        if pd.notna(row[degree_col]):
            degree = str(row[degree_col])
            if '硕士' in degree or '研究生' in degree:
                score += 15
            elif '本科' in degree or '学士' in degree:
                score += 10
                
        if pd.notna(row[school_col]):
            school = str(row[school_col])
            # 985/211院校加分
            top_schools = ['清华', '北大', '复旦', '上交', '浙大', '中科大', '南大', '华科', '西交']
            if any(s in school for s in top_schools):
                score += 20
    
    return min(score, 60)  # 最高60分

def analyze_candidates():
    """分析候选人数据"""
    
    # 读取Excel文件
    file_path = '/Users/lillianliao/notion_rag/candidate 2025-09-26 13_28_27.xls'
    
    try:
        df = pd.read_excel(file_path)
        print('=' * 80)
        print('AIGC创意工具产品经理岗位候选人匹配分析')
        print('=' * 80)
        print(f'候选人总数: {len(df)}')
        
        # 计算匹配分数
        experience_results = df.apply(get_relevant_experience_score, axis=1)
        df['经验评分'] = [result[0] if isinstance(result, tuple) else result for result in experience_results]
        df['行业匹配详情'] = [result[1] if isinstance(result, tuple) else [] for result in experience_results]
        df['教育评分'] = df.apply(get_education_score, axis=1)
        df['总评分'] = df['经验评分'] + df['教育评分']
        
        # 首先筛选有产品经理经验且行业相关的候选人
        qualified_candidates = df[df['经验评分'] > 0].sort_values('总评分', ascending=False)
        
        print(f'\n符合基础要求候选人数量: {len(qualified_candidates)}')
        print(f'(必须有产品经理经验 + AI/音乐/内容生成行业背景)')
        
        if len(qualified_candidates) == 0:
            print('\n❌ 未找到符合要求的候选人')
            return df, qualified_candidates
        
        print('\n' + '=' * 80)
        print('🎯 精准匹配的AIGC创意工具产品经理候选人:')
        print('=' * 80)
        
        for idx, (_, candidate) in enumerate(qualified_candidates.head(15).iterrows(), 1):
            print(f'\n【TOP {idx}】{candidate["姓名"]} ⭐️ 匹配度: {candidate["总评分"]:.0f}分')
            print(f'📱 {candidate["手机"]} | 📧 {candidate["邮箱"]} | 📍 {candidate["所在城市"]}')
            print(f'💼 工作年限: {candidate["工作年限"]}年')
            
            # 显示行业匹配亮点
            if candidate['行业匹配详情']:
                print('🎯 行业匹配亮点:')
                for detail in candidate['行业匹配详情']:
                    print(f'   ✅ {detail}')
            
            # 显示工作经历
            work_exp = []
            for i in range(1, 4):
                company = candidate.get(f'工作经历{i}公司')
                position = candidate.get(f'工作经历{i}职位')
                if pd.notna(company) and pd.notna(position):
                    work_exp.append(f'{company} - {position}')
            
            if work_exp:
                print('💼 核心工作经历:')
                for exp in work_exp:
                    print(f'   • {exp}')
            
            # 显示教育经历
            edu_exp = []
            for i in range(1, 4):
                school = candidate.get(f'教育经历{i}学校')
                degree = candidate.get(f'教育经历{i}学历')
                major = candidate.get(f'教育经历{i}专业')
                if pd.notna(school):
                    edu_info = school
                    if pd.notna(degree):
                        edu_info += f' | {degree}'
                    if pd.notna(major):
                        edu_info += f' | {major}'
                    edu_exp.append(edu_info)
            
            if edu_exp:
                print('🎓 教育背景:')
                for edu in edu_exp:
                    print(f'   • {edu}')
            
            print(f'📊 评分: 行业经验 {candidate["经验评分"]:.0f}分 + 教育背景 {candidate["教育评分"]:.0f}分')
            print('-' * 60)
        
        return df, qualified_candidates
        
    except Exception as e:
        print(f'读取文件时出错: {e}')
        return None, None

if __name__ == '__main__':
    df = analyze_candidates()