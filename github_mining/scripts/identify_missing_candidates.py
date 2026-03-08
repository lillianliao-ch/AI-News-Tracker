#!/usr/bin/env python3
"""
识别需要 LLM 富化的候选人（不在数据库或未富化）
"""

import json
import sqlite3
from pathlib import Path

def main():
    # 读取新输入文件
    input_file = Path(__file__).parent / "github_mining" / "phase4_final_enriched.json"
    output_file = Path(__file__).parent / "github_mining" / "phase45_missing_1105.json"
    
    print(f"📖 读取输入文件: {input_file}")
    with open(input_file) as f:
        new_input = json.load(f)
    
    print(f"✅ 加载 {len(new_input)} 个候选人")
    
    # 提取有网站内容的候选人
    with_websites = [c for c in new_input if c.get('homepage_scraped')]
    print(f"🌐 有个人网站的候选人: {len(with_websites)} 人")
    
    # 连接数据库
    db_path = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
    print(f"🔗 连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 找出需要富化的人
    to_enrich = []
    not_in_db = 0
    not_enriched = 0
    
    for i, person in enumerate(with_websites):
        github = person.get('github_url', '')
        if github and 'github.com/' in github:
            username = github.split('github.com/')[-1].split('/')[0]
            
            # 查询数据库
            cursor.execute('''
                SELECT extracted_work_history
                FROM candidates
                WHERE github_url LIKE ?
            ''', (f'%{username}%',))
            
            result = cursor.fetchone()
            
            # 不在数据库中或未富化
            if not result:
                not_in_db += 1
                to_enrich.append(person)
            elif not result[0] or result[0] == '' or result[0] == '[]':
                not_enriched += 1
                to_enrich.append(person)
        
        # 每1000人显示进度
        if (i + 1) % 1000 == 0:
            print(f"  进度: {i+1}/{len(with_websites)} ...")
    
    conn.close()
    
    # 保存到文件
    print(f"\n💾 保存需要富化的候选人到: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(to_enrich, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 统计结果:")
    print(f"   总计: {len(to_enrich)} 人")
    print(f"   - 不在数据库: {not_in_db} 人")
    print(f"   - 未富化: {not_enriched} 人")
    print(f"\n✅ 完成!")

if __name__ == "__main__":
    main()
