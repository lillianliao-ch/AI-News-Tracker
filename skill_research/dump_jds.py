import sqlite3
import pandas as pd
import json
from collections import defaultdict

DB_PATH = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT id, title, company, department, team_name, is_active, 
           raw_jd_text, ai_analysis, job_code, candidate_profile
    FROM jobs
    WHERE is_active = 1 OR is_active IS NULL
    ORDER BY company, title
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Fill NA for company to group properly
    df['company'] = df['company'].fillna('Unknown Company')
    
    company_counts = df['company'].value_counts()
    print("=== Active JD Counts by Company ===")
    print(company_counts)
    
    print("\n=== Detailed JD List ===")
    grouped = df.groupby('company')
    payload = defaultdict(list)
    for company, group in grouped:
        print(f"\n[{company}] - {len(group)} roles")
        for _, row in group.iterrows():
            print(f"  - {row['title']} (ID: {row['id']}, Dept: {row['department']}, Team: {row['team_name']})")
            payload[company].append({
                "id": row['id'],
                "title": row['title'],
                "department": row['department'],
                "team_name": row['team_name'],
                "job_code": row['job_code'],
                "raw_jd_text": str(row['raw_jd_text'])[:1000] if row['raw_jd_text'] else "",
                "ai_analysis": row['ai_analysis'],
                "candidate_profile": row['candidate_profile']
            })
            
    # Save payload to JSON for further LLM analysis
    out_file = "/Users/lillianliao/notion_rag/skill_research/active_jds.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nDumped {len(df)} mapped JDs to {out_file}")

if __name__ == "__main__":
    main()
