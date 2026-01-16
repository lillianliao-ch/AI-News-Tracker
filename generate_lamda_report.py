#!/usr/bin/env python3
"""
LAMDA 实验室综合分析报告
生成最终的人才分析报告
"""

import pandas as pd
from datetime import datetime

def generate_lamda_report():
    """生成 LAMDA 综合分析报告"""

    print("="*80)
    print("LAMDA 实验室顶级人才分析报告")
    print("="*80)
    print(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 加载数据
    df_original = pd.read_excel('LAMDA.xlsx')
    df_scraped = pd.read_excel('LAMDA_profiles_zh_first_20260105_112233.xlsx')

    print("\n" + "="*80)
    print("一、实验室概况")
    print("="*80)

    total_students = len(df_original)
    professors = df_original[['Professor', 'Professor_URL']].drop_duplicates()
    num_professors = len(professors)

    print(f"\n教授总数: {num_professors}")
    print(f"学生总数: {total_students}")

    # 学生类型分布
    print(f"\n学生类型分布:")
    type_dist = df_original['Student_Type'].value_counts()
    for stype, count in type_dist.items():
        pct = count / total_students * 100
        print(f"  - {stype}: {count} 人 ({pct:.1f}%)")

    print("\n" + "="*80)
    print("二、教授团队分析（按学生数量排名）")
    print("="*80)

    prof_student_count = df_original.groupby('Professor').size().sort_values(ascending=False)

    print(f"\n{'排名':<5}{'教授':<15}{'学生数':<10}{'说明'}")
    print("-" * 80)

    for i, (prof, count) in enumerate(prof_student_count.head(10).items(), 1):
        # 获取该教授的URL
        prof_url = professors[professors['Professor'] == prof]['Professor_URL'].values
        url_info = prof_url[0] if len(prof_url) > 0 else 'N/A'

        # 判断是否是核心教授
        note = "⭐ 核心导师" if count >= 20 else ""

        print(f"{i:<5}{prof:<15}{count:<10}{note}")

    print("\n" + "="*80)
    print("三、联系方式统计")
    print("="*80)

    # 统计有联系方式的学生
    students_with_email = df_scraped[(df_scraped['type'] == 'student') & (df_scraped['email'] != '')]
    print(f"\n有邮箱的学生: {len(students_with_email)} 人")
    print(f"邮箱获取率: {len(students_with_email) / total_students * 100:.1f}%")

    # 展示部分邮箱
    print(f"\n邮箱示例 (前10个):")
    for idx, row in students_with_email.head(10).iterrows():
        print(f"  {row['name']}: {row['email']}")

    print("\n" + "="*80)
    print("四、推荐关注的顶级学生")
    print("="*80)

    # 策略：找出核心导师（学生数>=20）的博士生
    core_professors = prof_student_count[prof_student_count >= 20].index.tolist()

    print(f"\n核心导师名单: {', '.join(core_professors)}")

    # 找出这些导师的 PhD 学生
    phd_students = df_original[
        (df_original['Professor'].isin(core_professors)) &
        (df_original['Student_Type'] == 'PhD')
    ][['Student_Name', 'Professor', 'Start_Year', 'Student_URL']]

    print(f"\n核心导师的博士生总数: {len(phd_students)}")

    # 按入学年份排序，找出最近的学生
    recent_phd = phd_students[phd_students['Start_Year'] >= 2020].copy()

    print(f"\n🎓 近5年入学的博士生 ({len(recent_phd)}人):")

    # 按导师分组
    for prof in core_professors:
        prof_phds = recent_phd[recent_phd['Professor'] == prof]
        if len(prof_phds) > 0:
            print(f"\n【{prof}】的博士生 ({len(prof_phds)}人):")
            for _, row in prof_phds.iterrows():
                # 查找是否有邮箱
                student_info = df_scraped[df_scraped['name'] == row['Student_Name']]
                email = student_info['email'].values[0] if len(student_info) > 0 and student_info['email'].values[0] else '无邮箱信息'
                print(f"  - {row['Student_Name']} ({row['Start_Year']}年入学) | {email}")

    print("\n" + "="*80)
    print("五、重点关注建议")
    print("="*80)

    print("\n📌 基于以上分析，建议重点关注以下学生：\n")

    print("1️⃣ 俞扬教授团队的博士生（规模最大，34名学生）")
    print("   - 研究方向：强化学习、演化计算")

    print("\n2️⃣ 詹德川教授团队的博士生（32名学生）")
    print("   - 研究方向：机器学习理论、弱监督学习")

    print("\n3️⃣ 李宇峰教授团队的博士生（26名学生）")
    print("   - 研究方向：机器学习、度量学习")

    print("\n4️⃣ 周志华教授团队的博士生（16名学生）")
    print("   - 研究方向：机器学习理论、集成学习")
    print("   - 备注：周老师是 LAMDA 创始人，学生质量普遍很高")

    print("\n" + "="*80)
    print("六、数据文件说明")
    print("="*80)

    print("\n已生成的分析文件：")
    print("  1. LAMDA_profiles_zh_first_*.xlsx - 完整成员信息")
    print("  2. LAMDA_contacts_only_*.xlsx - 联系方式专用")
    print("  3. LAMDA_biographies_zh_*.xlsx - 个人简介")
    print("  4. LAMDA_professors_students_analysis_*.xlsx - 教授学生分析")

    print("\n" + "="*80)
    print("报告生成完成")
    print("="*80 + "\n")

    # 保存报告到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'LAMDA_analysis_report_{timestamp}.txt'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("LAMDA 实验室顶级人才分析报告\n")
        f.write("="*80 + "\n")
        f.write(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 写入核心信息
        f.write(f"\n【核心导师】(学生数>=20):\n")
        for prof in core_professors:
            count = prof_student_count[prof]
            f.write(f"  - {prof}: {count} 名学生\n")

        f.write(f"\n【博士生列表】(核心导师，2020年后入学):\n")
        for _, row in recent_phd.iterrows():
            f.write(f"  {row['Student_Name']} | {row['Professor']} | {row['Start_Year']}年入学\n")

    print(f"✓ 报告已保存到: {report_file}\n")

if __name__ == '__main__':
    generate_lamda_report()
