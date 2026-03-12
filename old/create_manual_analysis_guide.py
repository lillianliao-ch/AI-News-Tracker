#!/usr/bin/env python3
"""
LAMDA 顶级人才 - 手动分析辅助工具
基于已有的学生数据，生成便于手动验证和分析的格式
"""

import pandas as pd
from datetime import datetime

def create_manual_analysis_guide():
    """创建手动分析指南"""

    # 读取数据
    df_original = pd.read_excel('LAMDA.xlsx')
    df_scraped = pd.read_excel('LAMDA_profiles_zh_first_20260105_112233.xlsx')

    print("="*80)
    print("LAMDA 顶级人才分析 - 手动验证指南")
    print("="*80)

    # 1. 识别核心导师的博士生
    prof_student_count = df_original.groupby('Professor').size()
    core_professors = prof_student_count[prof_student_count >= 20].index.tolist()

    print(f"\n核心导师（学生数≥20）: {', '.join(core_professors)}\n")

    # 2. 获取这些导师的博士生（近5年入学）
    current_year = datetime.now().year

    # 确保 Start_Year 是数值类型
    df_original['Start_Year'] = pd.to_numeric(df_original['Start_Year'], errors='coerce')

    recent_phd = df_original[
        (df_original['Professor'].isin(core_professors)) &
        (df_original['Student_Type'] == 'PhD') &
        (df_original['Start_Year'] >= (current_year - 5))
    ].copy()

    print(f"核心导师的近5年博士生: {len(recent_phd)} 人\n")

    # 3. 为每个学生创建分析记录
    analysis_records = []

    for _, student in recent_phd.iterrows():
        student_name = student['Student_Name']
        professor = student['Professor']
        start_year = student['Start_Year']
        student_url = student['Student_URL']

        # 从爬取的数据中查找邮箱
        scraped_info = df_scraped[df_scraped['name'] == student_name]
        email = scraped_info['email'].values[0] if len(scraped_info) > 0 else ''
        biography = scraped_info['biography'].values[0] if len(scraped_info) > 0 else ''

        # 转换为字符串
        if pd.isna(biography):
            biography = ''
        biography = str(biography)

        # 计算毕业时间（PhD 通常 4-6 年）
        expected_graduation = start_year + 5

        analysis_records.append({
            '学生姓名': student_name,
            '导师': professor,
            '入学年份': start_year,
            '预计毕业': expected_graduation,
            '邮箱': email,
            '个人页面': student_url,
            '简介': biography[:200] if biography else '',
            'Google Scholar 搜索': f'=HYPERLINK("https://scholar.google.com/scholar?q={student_name}+{professor}";"搜索 {student_name}")',
            'Semantic Scholar': f'=HYPERLINK("https://www.semanticscholar.org/search?q={student_name}%20Nanjing";"搜索 {student_name}")',
            '顶级论文数': '',  # 待手动填写
            '总引用数': '',    # 待手动填写
            '备注': '',        # 待手动填写
            '推荐程度': ''     # 高/中/低
        })

    # 4. 保存为 Excel
    df_analysis = pd.DataFrame(analysis_records)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'LAMDA_manual_analysis_template_{timestamp}.xlsx'

    df_analysis.to_excel(output_file, index=False, engine='openpyxl')
    print(f"✓ 分析模板已保存到: {output_file}")

    # 5. 生成分析指南
    print(f"\n{'='*80}")
    print("手动分析指南")
    print(f"{'='*80}\n")

    print("步骤1：打开生成的 Excel 文件")
    print(f"  文件名: {output_file}")

    print("\n步骤2：对每个学生进行论文分析")
    print("  方法A - 使用 Google Scholar:")
    print("    1. 点击 'Google Scholar 搜索' 链接")
    print("    2. 查看该学生的论文列表")
    print("    3. 统计近5年在顶级会议的论文数")
    print("    4. 查看总引用数")

    print("\n  方法B - 使用 Semantic Scholar:")
    print("    1. 点击 'Semantic Scholar' 链接")
    print("    2. 找到正确的学生（看 affiliation 是 Nanjing University）")
    print("    3. 查看该作者的论文和引用统计")

    print("\n步骤3：填写以下列")
    print("  - 顶级论文数：近5年在 NeurIPS/ICML/ICLR/AAAI/IJCAI 等的论文数")
    print("  - 总引用数：所有论文的总引用数")
    print("  - 推荐程度：高（≥3篇顶级论文）、中（1-2篇）、低（0篇）")

    print("\n步骤4：按 '顶级论文数' 排序，找出最优秀的学生")

    print(f"\n{'='*80}")
    print("重点关注的导师团队")
    print(f"{'='*80}\n")

    for prof in core_professors:
        prof_students = recent_phd[recent_phd['Professor'] == prof]
        print(f"\n【{prof}】")
        print(f"  博士生数: {len(prof_students)}")
        print(f"  学生名单:")

        for _, student in prof_students.iterrows():
            has_email = '✓' if student['Student_Name'] in df_scraped['name'].values else '✗'
            print(f"    - {student['Student_Name']} ({student['Start_Year']}) | 邮箱: {has_email}")

    print(f"\n{'='*80}")
    print("分析完成")
    print(f"{'='*80}\n")

    return output_file

if __name__ == '__main__':
    create_manual_analysis_guide()
