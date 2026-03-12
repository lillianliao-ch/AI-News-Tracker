import json
import sqlite3
import os

def prepare_filtered_input():
    # Load candidate JSON
    json_path = "/Users/lillianliao/notion_rag/github_mining/scripts/github_mining/phase5_expanded_latest.json"
    print(f"Loading {json_path}...")
    with open(json_path) as f:
        candidates = json.load(f)
    print(f"Total candidates in Phase 5 JSON: {len(candidates)}")
    
    # Connect to database
    db_path = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT github_url FROM candidates WHERE github_url IS NOT NULL")
    db_github_urls = {row[0].lower().strip('/') for row in c.fetchall()}
    
    # Filter
    new_candidates = []
    
    for candidate in candidates:
        if not candidate or not isinstance(candidate, dict): continue
        github_url = candidate.get("github_url", "")
        if not github_url:
            new_candidates.append(candidate)
            continue
        github_url = github_url.lower().strip('/')
        if github_url not in db_github_urls:
            new_candidates.append(candidate)
            
    # Save back
    output_path = "/Users/lillianliao/notion_rag/github_mining/scripts/phase5_filtered_input.json"
    with open(output_path, "w") as f:
        json.dump(new_candidates, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(new_candidates)} new candidates to {output_path}")

if __name__ == "__main__":
    prepare_filtered_input()
