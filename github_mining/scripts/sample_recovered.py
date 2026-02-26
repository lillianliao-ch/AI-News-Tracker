import json
import random

with open('/Users/lillianliao/notion_rag/github_mining/scripts/github_mining/phase3_5_enriched.json', 'r') as f:
    data = json.load(f)

valid_users = [u for u in data if not u.get('is_organization') and u.get('type') != 'Organization']
random.seed(42) # fixed seed for reproducibility in this test
sample = random.sample(valid_users, 6)

for u in sample:
    name = u.get('name') or u.get('username')
    username = u.get('username')
    print(f"👤 {name} ({username})")
    print(f"📝 Bio: {u.get('bio')}")
    print(f"🏫 Co: {u.get('company')} | 🌐 Scholar: {u.get('scholar_url')}")
    print(f"🧠 V3 AI Score: {u.get('ai_score_v3')}")
    
    print(f"📦 Top Repositories:")
    repos = u.get('repos', [])
    for r in repos[:5]:
        desc = (r.get('description') or '')[:80]
        print(f"   - {r.get('name')} (⭐{r.get('stargazers_count')} | Lang: {r.get('language')}): {desc}")
    print("-" * 60)
