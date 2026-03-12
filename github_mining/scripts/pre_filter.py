import json
import re

def pre_filter_foreigners():
    input_file = '/Users/lillianliao/notion_rag/github_mining/scripts/phase5_filtered_input.json'
    with open(input_file, 'r') as f:
        candidates = json.load(f)
        
    print(f"Total pure-new candidates before pre-filtering: {len(candidates)}")
    
    # 1. Organization filtering logic (from check_orgs_foreigners.py)
    org_keywords = [
        'official', 'community', 'organization', 'foundation', 'group', 'team',
        'project', 'lab', 'laboratory', 'institute', 'developer', 'developers',
        'bot', 'robot', 'auto', 'generator', 'cli', 'api', 'sdk'
    ]
    
    # 2. Foreigner filtering logic (from check_orgs_foreigners.py)
    chinese_chars = re.compile(r'[\u4e00-\u9fff]')
    domestic_regions = [
        'china', 'beijing', 'shanghai', 'shenzhen', 'guangzhou', 'hangzhou', 'chengdu',
        'taiwan', 'taipei', 'hong kong', 'hongkong', 'hk', 'macau', 'singapore', 'sg'
    ]
    
    kept_candidates = []
    org_count = 0
    foreign_count = 0
    
    for c in candidates:
        name = (c.get('name') or '').lower()
        company = (c.get('company') or '').lower()
        bio = (c.get('bio') or '').lower()
        location = (c.get('location') or '').lower()
        
        # Check Org
        is_org = False
        for field in [name, company, bio]:
            if any(kw in field for kw in org_keywords):
                is_org = True
                break
        if is_org:
            org_count += 1
            continue
            
        # Check Nationality
        # First check if clearly domestic
        is_domestic = False
        if chinese_chars.search(name) or chinese_chars.search(company) or chinese_chars.search(bio) or chinese_chars.search(location):
            is_domestic = True
        elif any(region in location for region in domestic_regions):
            is_domestic = True
            
        # If not clearly domestic, check if clearly foreign
        if not is_domestic and location:
            # If it has a location but didn't match domestic regions, it's highly likely foreign
            foreign_count += 1
            continue
            
        # If no location and no Chinese chars, we keep them as 'unknown' for LLM to decide
        kept_candidates.append(c)
        
    print(f"Filtered out {org_count} potential Orgs/Bots.")
    print(f"Filtered out {foreign_count} explicitly Foreign candidates based on location.")
    print(f"Kept {len(kept_candidates)} candidates (Domestic + Unknown) for API processing.")
    
    output_file = '/Users/lillianliao/notion_rag/github_mining/scripts/phase5_pre_filtered_input.json'
    with open(output_file, 'w') as f:
        json.dump(kept_candidates, f, ensure_ascii=False, indent=2)
    print(f"Saved optimized input to {output_file}")

if __name__ == "__main__":
    pre_filter_foreigners()
