import json
import sqlite3
import os

def check_duplicates():
    # Load candidate JSON
    json_path = "/Users/lillianliao/notion_rag/github_mining/scripts/github_mining/phase5_expanded_latest.json"
    print(f"Loading {json_path}...")
    try:
        with open(json_path) as f:
            candidates = json.load(f)
        print(f"Total candidates in JSON: {len(candidates)}")
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return
    
    # Connect to database
    db_path = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
    print(f"Connecting to database {db_path}...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get all GitHub URLs from database
    c.execute("SELECT github_url FROM candidates WHERE github_url IS NOT NULL")
    db_github_urls = {row[0].lower().strip('/') for row in c.fetchall()}
    print(f"Total GitHub profiles in DB: {len(db_github_urls)}")
    
    # Compare
    duplicates = []
    new_candidates = []
    
    # Some candidates might be None or malformed
    for candidate in candidates:
        if not candidate or not isinstance(candidate, dict):
            continue
            
        github_url = candidate.get("github_url", "")
        if not github_url:
            new_candidates.append(candidate)
            continue
            
        github_url = github_url.lower().strip('/')
        if github_url in db_github_urls:
            duplicates.append(candidate)
        else:
            new_candidates.append(candidate)
            
    print(f"\n--- Results ---")
    print(f"Total valid candidates in Phase 5 JSON: {len(candidates)}")
    print(f"Already in DB (Duplicates): {len(duplicates)}")
    print(f"New Candidates to be added: {len(new_candidates)}")

if __name__ == "__main__":
    check_duplicates()
