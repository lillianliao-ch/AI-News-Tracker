import sqlite3
import os
import glob
import subprocess
import json
import argparse
import sys

NLM_CLI = "/Users/lillianliao/Library/Python/3.12/bin/notebooklm"
DB_PATHS = [
    "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter.db",
    "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
]
BASE_RESEARCH_DIR = "/Users/lillianliao/notion_rag/skill_research"

def get_db():
    for path in DB_PATHS:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'")
                if cur.fetchone():
                    return path
            except:
                pass
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", help="Comma separated company keywords", required=True)
    parser.add_argument("--teams", help="Comma separated team/tech keywords", required=True)
    parser.add_argument("--prefix", help="Prefix for folder and files (e.g., Baidu)", required=True)
    parser.add_argument("--desc", help="Description of the company used in the prompt", required=True)
    parser.add_argument("--title", help="Title of NotebookLM notebook", required=True)
    args = parser.parse_args()

    companies = [c.strip() for c in args.companies.split(',')]
    teams = [t.strip() for t in args.teams.split(',')]

    cat_dir = os.path.join(BASE_RESEARCH_DIR, f"{args.prefix}_Org_Chart")
    os.makedirs(cat_dir, exist_ok=True)
    
    db_path = get_db()
    if not db_path:
        print("Database candidates table not found.")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    comp_queries = []
    for c in companies:
        comp_queries.append(f"current_company LIKE '%{c}%'")
        comp_queries.append(f"company_normalized LIKE '%{c}%'")
        comp_queries.append(f"work_experiences LIKE '%{c}%'")
        comp_queries.append(f"raw_resume_text LIKE '%{c}%'")
    comp_clause = " OR ".join(comp_queries)

    team_queries = []
    for t in teams:
        team_queries.append(f"work_experiences LIKE '%{t}%'")
        team_queries.append(f"project_experiences LIKE '%{t}%'")
        team_queries.append(f"current_title LIKE '%{t}%'")
        team_queries.append(f"raw_resume_text LIKE '%{t}%'")
    team_clause = " OR ".join(team_queries)

    query = f"SELECT id, name, current_company, current_title, work_experiences, project_experiences, raw_resume_text FROM candidates WHERE ({comp_clause}) AND ({team_clause})"
    
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    
    print(f"[{len(rows)}] Multi-faceted candidates mentioning {args.prefix} and target teams discovered.")
    if not rows:
        sys.exit(0)
        
    # Cap at 1000 candidates to keep chunks manageable (NotebookLM has a 50 file source limit)
    rows = rows[:1000]
    chunk_size = 20
    chunks_created = 0

    chunk_files = []
    for i in range(0, len(rows), chunk_size):
        chunk_rows = rows[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        filepath = os.path.join(cat_dir, f"MEGA_CHUNK_{chunk_num}.txt")
        
        with open(filepath, "w", encoding="utf-8") as outfile:
            outfile.write(f"# CANDIDATE BATCH {chunk_num}\n\n")
            for row in chunk_rows:
                cid, name, comp, title, work, proj, raw = row
                outfile.write("========================================\n")
                outfile.write(f"Candidate ID: {cid}\n")
                outfile.write(f"Name Mask: {'*'+str(name)[1:] if name and len(str(name))>1 else name or 'Unknown'}\n")
                outfile.write(f"Current Title/Company: {title} @ {comp}\n\n")
                if work:
                    outfile.write("=== WORK EXPERIENCES ===\n" + str(work) + "\n\n")
                if proj:
                    outfile.write("=== PROJECT EXPERIENCES ===\n" + str(proj) + "\n\n")
                if raw:
                    outfile.write("=== RAW RESUME EXTRACT ===\n" + str(raw)[:3500] + "\n\n")
                outfile.write("========================================\n\n")
        chunks_created += 1
    
    chunk_files = glob.glob(os.path.join(cat_dir, "MEGA_CHUNK_*.txt"))
    chunk_files = chunk_files[:50]
    print(f"Aggregated resumes into {len(chunk_files)} MEGA CHUNK files.")
    
    print("1. Creating Notebook...")
    result = subprocess.run([NLM_CLI, "create", args.title, "--json"], capture_output=True, text=True)
    try:
        nb_id = json.loads(result.stdout).get("notebook", {}).get("id")
    except Exception as e:
        print(f"Failed to parse notebook JSON. Output: {result.stdout}\nError: {e}")
        sys.exit(1)
        
    print(f"Notebook ID: {nb_id}")
    if not nb_id:
        print(f"Failed to create notebook. Output: {result.stdout}")
        sys.exit(1)
    
    print("2. Uploading chunks and waiting for processing...")
    source_ids = []
    for fpath in chunk_files:
        add_res = subprocess.run([NLM_CLI, "source", "add", fpath, "-n", nb_id, "--json"], capture_output=True, text=True)
        try:
            sid = json.loads(add_res.stdout).get("source", {}).get("id")
            if sid:
                source_ids.append(sid)
        except:
            print(f"Failed uploading {fpath}: {add_res.stdout}")
            pass
            
    print(f"Waiting for {len(source_ids)} chunked profiles to be indexed...")
    for sid in source_ids:
        subprocess.run([NLM_CLI, "source", "wait", sid, "-n", nb_id, "--timeout", "120"])
        
    print("3. Querying Final ORG CHART Report...")
    prompt = f"""请你化身世界顶级的科技猎头团队 Intelligence Researcher。
现在你收到了这批数百位来自“{args.desc}”的候选人真实履历记录。

请根据所有这些履历中提及的**工作经历、职责边界、负责的具体项目代号、交叉协作方、甚至是偶尔提及的汇报人 (Reporting Line) 等草蛇灰线**，帮我：
1. **完整逆向拼凑还原出 {args.desc}的核心AI及业务部门 的组织架构（Org Chart）**。
   用极具职业猎头直觉的方式，梳理出包含基础模型预训练、前沿AI探索、多模态、Infra基建、具体业务落地等可能存在的内部划分支线。
2. **【核心】呈现一张层级树状图矩阵**（请使用 Markdown list）。
   请把你能识别出来的**核心成员（列出ID或对应的Title特征，能拼凑出多少是多少）**放在这棵树的正确位置上。
3. **技术攻坚方向窥探**：通过这些人最近半年主要写的“项目经历”，分析出该阵列当下重点押注的技术高地是什么？
4. 如果数据不够拼全，请大胆根据你对通用大厂大模型架构的常识进行**合理推演补齐**，并在你不确定的地方打上 `(?)` 问号标识。

请输出极其专业、震撼的报告！"""
             
    report_path = os.path.join(cat_dir, f"{args.prefix}_Org_Chart_Mapping.md")
    with open(report_path, "w", encoding="utf-8") as out:
        subprocess.run([NLM_CLI, "ask", prompt, "-n", nb_id], stdout=out)
        
    print(f"DONE! Org Chart Mapping saved to {report_path}")

if __name__ == "__main__":
    main()
