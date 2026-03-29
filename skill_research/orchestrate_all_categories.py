import sqlite3
import os
import glob
import subprocess
import json
import time

NLM_CLI = "/Users/lillianliao/Library/Python/3.12/bin/notebooklm"
DB_PATH = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"
BASE_RESEARCH_DIR = "/Users/lillianliao/notion_rag/skill_research"

CATEGORIES = [
    {
        "name": "Agent",
        "sql_condition": "title LIKE '%Agent%' OR title LIKE '%智能体%' OR raw_jd_text LIKE '%Agent%'",
        "prompt_topic": "Agent 智能体"
    },
    {
        "name": "LLM",
        "sql_condition": "title LIKE '%LLM%' OR title LIKE '%大语言模型%' OR title LIKE '%基础模型%'",
        "prompt_topic": "LLM 大语言基础模型"
    },
    {
        "name": "具身智能",
        "sql_condition": "title LIKE '%具身智能%' OR title LIKE '%机器人%' OR title LIKE '%Robotics%' OR title LIKE '%Embodied%'",
        "prompt_topic": "具身智能 (Embodied AI)"
    },
    {
        "name": "AI Infra",
        "sql_condition": "title LIKE '%Infra%' OR title LIKE '%高性能计算%' OR title LIKE '%HPC%' OR title LIKE '%算子%' OR title LIKE '%系统架构%'",
        "prompt_topic": "AI Infra (AI 基础设施与算力集群)"
    },
    {
        "name": "AI产品经理",
        "sql_condition": "title LIKE '%产品%' AND (title LIKE '%AI%' OR title LIKE '%大模型%' OR title LIKE '%AIGC%')",
        "prompt_topic": "AI / 大模型产品经理 (AI PM)"
    }
]

def extract_and_chunk(category):
    cat_dir = os.path.join(BASE_RESEARCH_DIR, f"{category['name']}_jds")
    os.makedirs(cat_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT id, title, company, raw_jd_text FROM jobs WHERE {category['sql_condition']}")
    rows = cur.fetchall()
    conn.close()
    
    print(f"[{category['name']}] Found {len(rows)} matching JDs.")
    if not rows:
        return 0, cat_dir
        
    chunk_size = 15
    chunks_created = 0
    for i in range(0, len(rows), chunk_size):
        chunk_rows = rows[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        filepath = os.path.join(cat_dir, f"MEGA_CHUNK_{chunk_num}.txt")
        
        with open(filepath, "w", encoding="utf-8") as outfile:
            outfile.write(f"# JD BATCH {chunk_num}\n\n")
            for row in chunk_rows:
                jid, title, comp, desc = row
                outfile.write("========================================\n")
                outfile.write(f"Company: {comp or 'Unknown'}\nTitle: {title}\nID: {jid}\n\n")
                outfile.write(desc if desc else "")
                outfile.write("\n========================================\n\n")
        chunks_created += 1
        
    print(f"[{category['name']}] Aggregated into {chunks_created} MEGA CHUNK files.")
    return chunks_created, cat_dir

def run_notebooklm_pipeline(category, cat_dir):
    chunk_files = glob.glob(os.path.join(cat_dir, "MEGA_CHUNK_*.txt"))
    if not chunk_files:
        print(f"[{category['name']}] Skipping notebook creation (no chunks).")
        return
        
    print(f"[{category['name']}] 1. Creating Notebook...")
    title = f"{category['name']} 岗位深度对标分析"
    result = subprocess.run([NLM_CLI, "create", title, "--json"], capture_output=True, text=True)
    try:
        nb_id = json.loads(result.stdout).get("notebook", {}).get("id")
    except:
        print(f"Failed to create notebook. Output: {result.stdout}")
        return
    
    print(f"[{category['name']}] Notebook ID: {nb_id}")
    
    print(f"[{category['name']}] 2. Uploading chunks and waiting for processing...")
    source_ids = []
    for fpath in chunk_files:
        # source add
        add_res = subprocess.run([NLM_CLI, "source", "add", fpath, "-n", nb_id, "--json"], capture_output=True, text=True)
        try:
            sid = json.loads(add_res.stdout).get("source", {}).get("id")
            if sid:
                source_ids.append(sid)
        except:
            print(f"Failed to extract source_id for {fpath}")
            
    print(f"[{category['name']}] Waiting for {len(source_ids)} sources to be ready...")
    for sid in source_ids:
        # source wait
        subprocess.run([NLM_CLI, "source", "wait", sid, "-n", nb_id, "--timeout", "120"])
        
    print(f"[{category['name']}] 3. Querying Final Report...")
    prompt = f"请系统地分析目前你收到的所有有关『{category['prompt_topic']}』的真实招聘需求 JD。\n" + \
             "请输出一份详尽的【招聘风向洞察报告】，包含以下核心：\n" + \
             "1. 【核心技能栈与工具】目前各家最统一要求的底层技术或框架工具是什么？（按提及频率排序）\n" + \
             "2. 【主流业务落地区域】挑出具有代表性的 3 家不同公司，详细对比他们在该领域使用场景上的侧重点差异。\n" + \
             "3. 【人才画像分级】该岗位不同职级（如初级 vs 架构师/专家）的核心分水岭要求是什么？\n" + \
             "4. 【隐性要求与排雷点】有哪些经验是这些 JD 普遍明确排斥，或者看似亮眼实际不加分的？\n" + \
             "请使用极为专业、结构清晰的 Markdown 格式输出分析结果。"
             
    report_path = os.path.join(cat_dir, "final_report.md")
    with open(report_path, "w", encoding="utf-8") as out:
        subprocess.run([NLM_CLI, "ask", prompt, "-n", nb_id], stdout=out)
        
    print(f"[{category['name']}] DONE! Report saved to {report_path}")

def main():
    print("Starting Multi-Category JD Analysis Pipeline...")
    for cat in CATEGORIES:
        print(f"\n{'='*50}\nProcessing Category: {cat['name']}\n{'='*50}")
        chunks_count, cat_dir = extract_and_chunk(cat)
        if chunks_count > 0:
            run_notebooklm_pipeline(cat, cat_dir)
            
    print("\nAll pipeline tasks finished successfully!")

if __name__ == "__main__":
    main()
