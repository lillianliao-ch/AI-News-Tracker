import json
import sqlite3
import os

def analyze():
    # Load candidate JSON
    json_path = "/Users/lillianliao/notion_rag/github_mining/scripts/github_mining/phase5_expanded_latest.json"
    print(f"Loading {json_path}...")
    try:
        with open(json_path) as f:
            candidates = json.load(f)
        print(f"Total candidates in Phase 5 JSON: {len(candidates)}")
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return
        
    print(f"\n--- Results ---")
    org_keywords = ['org', 'organization', 'team', 'bot', 'ci', 'build', 'release', 'lab', 'university', 'research']
    
    org_count = 0
    foreign_count = 0
    chinese_count = 0
    unknown_country_count = 0
    
    china_kw = ["china", "beijing", "shanghai", "shenzhen", "hangzhou", "chengdu", "guangzhou", "nanjing", "taiwan", "hong kong", "中国", "北京", "上海", "深圳", "杭州", "成都", "广州", "南京", "台湾", "香港", "tsinghua", "peking", "fudan", "zhejiang", "sjtu", "ustc", "tencent", "alibaba", "bytedance", "baidu"]
    
    for candidate in candidates:
        if not candidate or not isinstance(candidate, dict):
            continue
            
        username_lower = (candidate.get("username") or "").lower()
        name_lower = (candidate.get("name") or "").lower()
        company_lower = (candidate.get("company") or "").lower()
        location_lower = (candidate.get("location") or "").lower()
        bio_lower = (candidate.get("bio") or "").lower()
        
        is_org = any(kw in username_lower or kw in name_lower for kw in org_keywords)
        if is_org:
            org_count += 1
            
        all_text = f"{location_lower} {company_lower} {bio_lower} {name_lower}"
        
        is_china = any(kw in all_text for kw in china_kw) or any('\u4e00' <= c <= '\u9fff' for c in all_text)
        
        if is_china:
            chinese_count += 1
        elif location_lower: # Has location but didn't match China keywords
            foreign_count += 1
        else:
            unknown_country_count += 1
            
    # Calculate percentages
    total = len(candidates)
    
    print(f"Total candidates: {total}")
    print(f"Potential Organization Accounts: {org_count} ({org_count/total*100:.1f}%)")
    print(f"Chinese/Domestic: {chinese_count} ({chinese_count/total*100:.1f}%)")
    print(f"Explicitly Foreign: {foreign_count} ({foreign_count/total*100:.1f}%)")
    print(f"Unknown Location: {unknown_country_count} ({unknown_country_count/total*100:.1f}%)")

if __name__ == "__main__":
    analyze()
