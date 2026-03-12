import sqlite3
from collections import Counter

conn = sqlite3.connect("/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db")
c = conn.cursor()

# Check nationality column
try:
    c.execute("SELECT nationality FROM candidates WHERE nationality IS NOT NULL")
    nationalities = [row[0] for row in c.fetchall()]
    counts = Counter(nationalities)
    print("Nationality Distribution in DB:")
    for k, v in counts.items():
        print(f"  {k}: {v} ({v/len(nationalities)*100:.1f}%)")
except Exception as e:
    print(f"Error querying nationality: {e}")

# Check company for institutions
c.execute("SELECT company FROM candidates WHERE company IS NOT NULL")
companies = [row[0] for row in c.fetchall()]
org_keywords = ['university', 'institute', 'lab', 'research', 'foundation', 'inc', 'llc', 'corporation']
org_count = sum(1 for c in companies if any(kw in c.lower() for kw in org_keywords))
print(f"\nPotential Orgs based on company name: {org_count} out of {len(companies)} ({org_count/len(companies)*100:.1f}%)")
