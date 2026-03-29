import sqlite3
import os

db_paths = [
    "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter.db",
    "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
]

out_dir = "/Users/lillianliao/notion_rag/skill_research/multimodal_jds/"
os.makedirs(out_dir, exist_ok=True)

total_extracted = 0

for path in db_paths:
    if not os.path.exists(path):
        continue
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if cur.fetchone():
            print(f"Found 'jobs' table in {path}")
            
            cur.execute("PRAGMA table_info(jobs)")
            cols = [col[1] for col in cur.fetchall()]
            
            content_col = "raw_jd_text" if "raw_jd_text" in cols else ("description" if "description" in cols else None)
            
            if content_col:
                query = f"SELECT id, title, company, {content_col} FROM jobs WHERE title LIKE '%多模态%' OR title LIKE '%大模型%' OR {content_col} LIKE '%多模态%'"
                cur.execute(query)
                rows = cur.fetchall()
                print(f"  -> Found {len(rows)} matching JDs.")
                for row in rows:
                    jid, title, comp, desc = row
                    safe_title = "".join(x for x in (title or "untitled") if x.isalnum() or x in " ")[:20].strip()
                    comp = comp or "Unknown"
                    safe_comp = "".join(x for x in comp if x.isalnum())[:10]
                    filename = f"JD_{jid}_{safe_comp}_{safe_title.replace(' ', '_')}.txt"
                    
                    filepath = os.path.join(out_dir, filename)
                    # Deduplicate by avoiding overwrite
                    if not os.path.exists(filepath):
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(f"Company: {comp}\nTitle: {title}\n\n{desc}")
                        total_extracted += 1
    except Exception as e:
        print(f"Error on {path}: {e}")

print(f"Total Unique JDs extracted: {total_extracted}")
