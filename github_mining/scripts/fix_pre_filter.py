import json
import sys
import re

# Insert path to import detect_nationality
sys.path.insert(0, '/Users/lillianliao/notion_rag/personal-ai-headhunter/scripts/extract')
from add_nationality_tags import detect_nationality

# Import KNOWN_ORG_BLACKLIST from github_network_miner
sys.path.insert(0, '/Users/lillianliao/notion_rag/github_mining/scripts')
from github_network_miner import KNOWN_ORG_BLACKLIST

def is_organization_account_fixed(user: dict) -> bool:
    username = user.get('username', '').lower()
    name = (user.get('name') or '').lower()
    bio = (user.get('bio') or '').lower()
    user_type = user.get('type', '')

    # 1: check type if available
    if user_type == 'Organization':
        return True

    # 2: KNOWN_ORG_BLACKLIST
    if username in KNOWN_ORG_BLACKLIST:
        return True

    # 3: suspicious org features
    if name and name == username:
        if not bio or len(bio) < 20:
            official_keywords = ['official', 'repo', 'repository', 'project', 'team', 'org', 'organization']
            if any(kw in bio for kw in official_keywords):
                return True

    return False

def fix_pre_filter():
    input_file = '/Users/lillianliao/notion_rag/github_mining/scripts/phase5_filtered_input.json'
    with open(input_file, 'r') as f:
        candidates = json.load(f)
        
    print(f"Total pure-new candidates before true pre-filtering: {len(candidates)}")
    
    kept_candidates = []
    org_count = 0
    foreign_count = 0
    
    for c in candidates:
        # Check org using the precise original logic
        if is_organization_account_fixed(c):
            org_count += 1
            continue
            
        # Check nationality using the exact logic from add_nationality_tags.py
        name = c.get('name', '')
        company = c.get('company', '')
        
        # company might literally have '@' from scraping, the original script does this strip:
        if company and company.startswith('@'):
            company = company[1:]
            
        nationality, confidence = detect_nationality(name, company)
        
        if nationality == 'foreign':
            foreign_count += 1
            continue
            
        # Keep 'chinese' and 'unknown' for the LLM to process
        kept_candidates.append(c)
        
    print(f"Filtered out {org_count} Org/Bot accounts based on official rules.")
    print(f"Filtered out {foreign_count} explicitly Foreign accounts (NAME-based, ignoring location).")
    print(f"Kept {len(kept_candidates)} candidates for API processing (Chinese + Unknown).")
    
    output_file = '/Users/lillianliao/notion_rag/github_mining/scripts/phase5_pre_filtered_input.json'
    with open(output_file, 'w') as f:
        json.dump(kept_candidates, f, ensure_ascii=False, indent=2)
    print(f"Saved strictly corrected optimized input to {output_file}")

if __name__ == "__main__":
    fix_pre_filter()
