#!/usr/bin/env python3
"""
同义词配置验证工具
用法: python scripts/validate_synonyms.py
"""

import yaml
import sys
import os
from collections import Counter

SYNONYMS_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'synonyms.yaml')


def validate_synonyms(file_path: str = SYNONYMS_FILE):
    """验证同义词配置文件"""
    
    print(f"📂 验证配置文件: {file_path}")
    print("-" * 50)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    
    # 加载配置
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ YAML 解析错误: {e}")
        sys.exit(1)
    
    all_terms = []
    issues = []
    stats = {}
    
    # 处理各分类
    for category in ['specialties', 'tech_skills', 'tech_domains']:
        groups = config.get(category, [])
        stats[category] = {
            'groups': len(groups),
            'terms': 0
        }
        
        for i, group in enumerate(groups):
            # 检查必需字段
            if 'canonical' not in group:
                issues.append(f"⚠️ {category}[{i}] 缺少 canonical 字段")
                continue
            
            canonical = group['canonical'].lower().strip()
            all_terms.append(canonical)
            stats[category]['terms'] += 1
            
            for alias in group.get('aliases', []):
                alias_lower = alias.lower().strip()
                all_terms.append(alias_lower)
                stats[category]['terms'] += 1
                
                # 检查空别名
                if not alias_lower:
                    issues.append(f"⚠️ {category}/{canonical} 包含空别名")
    
    # 检查重复
    term_counts = Counter(all_terms)
    duplicates = [(term, count) for term, count in term_counts.items() if count > 1]
    
    if duplicates:
        for term, count in duplicates:
            issues.append(f"⚠️ 重复词汇 '{term}' 出现 {count} 次")
    
    # 输出统计
    print("\n📊 统计信息:")
    print(f"   版本: {config.get('version', 'N/A')}")
    print(f"   更新时间: {config.get('last_updated', 'N/A')}")
    print(f"   维护者: {config.get('maintainer', 'N/A')}")
    print()
    
    for category, stat in stats.items():
        category_names = {
            'specialties': '专业方向',
            'tech_skills': '技术技能',
            'tech_domains': '技术方向'
        }
        print(f"   {category_names.get(category, category)}: {stat['groups']} 组, {stat['terms']} 条映射")
    
    print(f"\n   总映射数: {len(all_terms)}")
    print(f"   唯一词汇: {len(set(all_terms))}")
    
    # 输出问题
    if issues:
        print("\n❌ 发现问题:")
        for issue in issues:
            print(f"   {issue}")
        print(f"\n共 {len(issues)} 个问题需要修复")
        sys.exit(1)
    else:
        print("\n✅ 配置验证通过，无问题！")
    
    return True


def show_mappings(file_path: str = SYNONYMS_FILE):
    """显示所有同义词映射"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("\n📋 同义词映射列表:")
    print("=" * 60)
    
    for category in ['specialties', 'tech_skills', 'tech_domains']:
        category_names = {
            'specialties': '🎯 专业方向',
            'tech_skills': '🔧 技术技能',
            'tech_domains': '📂 技术方向'
        }
        print(f"\n{category_names.get(category, category)}")
        print("-" * 40)
        
        for group in config.get(category, []):
            canonical = group['canonical']
            aliases = group.get('aliases', [])
            print(f"  {canonical}")
            if aliases:
                print(f"    └─ {', '.join(aliases[:5])}")
                if len(aliases) > 5:
                    print(f"    └─ ... (+{len(aliases)-5} more)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="同义词配置验证工具")
    parser.add_argument('--show', action='store_true', help='显示所有映射')
    parser.add_argument('--file', default=SYNONYMS_FILE, help='配置文件路径')
    
    args = parser.parse_args()
    
    if args.show:
        show_mappings(args.file)
    else:
        validate_synonyms(args.file)
