#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脉脉候选人筛选脚本
筛除规则：
1. 工作年限 < 1年（应届生）
2. Title含："运维"、"测试"、"前端"、"商务"、"销售"、"产品经理"
3. 教育/工作时间全是未来（如2025–2026），且无当前工作
"""

import pandas as pd
import re
import os
from datetime import datetime

# 文件路径
INPUT_FILE = "/Users/lillianliao/notion_rag/文心-脉脉搜索结果_2025-12-26T08-19-04.csv"
OUTPUT_FILE = "/Users/lillianliao/notion_rag/文心-脉脉搜索结果_筛选后.csv"

# 需要排除的 Title 关键词
EXCLUDE_TITLES = ["运维", "测试", "前端", "商务", "销售", "产品经理", "产品"]

def detect_encoding(file_path):
    """尝试多种编码读取文件"""
    encodings = ['utf-8-sig', 'utf-8', 'gb18030', 'gbk', 'utf-16', 'utf-16-le', 'utf-16-be']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc, nrows=5)
            print(f"✅ 成功使用编码: {enc}")
            return enc
        except Exception as e:
            continue
    return None

def parse_years(years_str):
    """解析工作年限，返回数字"""
    if pd.isna(years_str) or not years_str:
        return 0
    match = re.search(r'(\d+)', str(years_str))
    if match:
        return int(match.group(1))
    return 0

def has_exclude_title(row):
    """检查是否包含需要排除的 Title"""
    # 检查所有可能包含职位的列
    title_columns = [col for col in row.index if 'title' in col.lower() or 'position' in col.lower() or '职位' in col]
    
    for col in title_columns:
        val = str(row.get(col, ''))
        for keyword in EXCLUDE_TITLES:
            if keyword in val:
                return True, keyword
    
    # 同时检查所有列的内容
    for col in row.index:
        val = str(row.get(col, ''))
        for keyword in EXCLUDE_TITLES:
            if keyword in val:
                return True, keyword
    
    return False, None

def has_only_future_dates(row):
    """检查是否只有未来日期（2025及以后）且无当前工作"""
    current_year = datetime.now().year
    all_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
    
    # 检查是否有"至今"（表示当前工作）
    if '至今' in all_text:
        return False
    
    # 提取所有年份
    years = re.findall(r'20\d{2}', all_text)
    if not years:
        return False  # 没有年份信息，不排除
    
    years = [int(y) for y in years]
    
    # 如果所有年份都是今年或未来，则标记排除
    if all(y >= current_year for y in years):
        return True
    
    return False

def filter_candidates(df):
    """应用筛选规则"""
    results = []
    
    for idx, row in df.iterrows():
        exclude_reason = None
        
        # 规则1: 工作年限 < 1年
        years_col = None
        for col in df.columns:
            if '年限' in col or 'years' in col.lower() or col == '工作年限':
                years_col = col
                break
        
        if years_col:
            years = parse_years(row.get(years_col))
            if years < 1:
                exclude_reason = f"工作年限不足1年 ({years}年)"
        
        # 规则2: Title 包含排除关键词
        if not exclude_reason:
            has_exclude, keyword = has_exclude_title(row)
            if has_exclude:
                exclude_reason = f"Title含排除词: {keyword}"
        
        # 规则3: 只有未来日期
        if not exclude_reason:
            if has_only_future_dates(row):
                exclude_reason = "只有未来日期且无当前工作"
        
        # 添加筛选结果
        row_dict = row.to_dict()
        row_dict['筛选标签'] = exclude_reason if exclude_reason else '通过'
        row_dict['是否排除'] = '是' if exclude_reason else '否'
        results.append(row_dict)
    
    return pd.DataFrame(results)

def main():
    print("=" * 50)
    print("脉脉候选人筛选工具")
    print("=" * 50)
    
    # 检测编码
    print(f"\n📂 读取文件: {INPUT_FILE}")
    encoding = detect_encoding(INPUT_FILE)
    
    if not encoding:
        print("❌ 无法检测文件编码")
        return
    
    # 读取数据
    df = pd.read_csv(INPUT_FILE, encoding=encoding)
    print(f"📊 总行数: {len(df)}")
    print(f"📋 列名: {list(df.columns)[:10]}...")  # 只显示前10个列名
    
    # 应用筛选
    print("\n🔍 应用筛选规则...")
    result_df = filter_candidates(df)
    
    # 统计结果
    passed = len(result_df[result_df['是否排除'] == '否'])
    excluded = len(result_df[result_df['是否排除'] == '是'])
    
    print(f"\n📈 筛选结果:")
    print(f"   ✅ 通过: {passed} 人")
    print(f"   ❌ 排除: {excluded} 人")
    
    # 显示排除原因分布
    if excluded > 0:
        print("\n📊 排除原因分布:")
        excluded_df = result_df[result_df['是否排除'] == '是']
        reason_counts = excluded_df['筛选标签'].value_counts()
        for reason, count in reason_counts.items():
            print(f"   - {reason}: {count} 人")
    
    # 保存结果
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n💾 结果已保存至: {OUTPUT_FILE}")
    
    # 同时保存通过的候选人
    passed_file = OUTPUT_FILE.replace('_筛选后.csv', '_通过.csv')
    passed_df = result_df[result_df['是否排除'] == '否']
    passed_df.to_csv(passed_file, index=False, encoding='utf-8-sig')
    print(f"💾 通过名单已保存至: {passed_file}")

if __name__ == "__main__":
    main()
