import json
import os
import subprocess

NLM_CLI = "/Users/lillianliao/Library/Python/3.12/bin/notebooklm"

def main():
    try:
        with open("/Users/lillianliao/notion_rag/skill_research/active_jds.json", "r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        print("Run Python dump_jds.py first.")
        return
        
    out_dir = "/Users/lillianliao/notion_rag/skill_research/JD_Analytics"
    os.makedirs(out_dir, exist_ok=True)
    
    target_files = []
    
    # We aggregate text files by company.
    for comp, jds in payload.items():
        # filter out empty companies and companies with few JDs
        if len(jds) < 3:
            continue
            
        chunk_size = 100 # Put up to 100 JDs per file to prevent file explosion
        for i in range(0, len(jds), chunk_size):
            chunk = jds[i:i+chunk_size]
            filename = os.path.join(out_dir, f"{comp.replace('/', '_')}_JDs_Batch_{i//chunk_size + 1}.txt")
            with open(filename, "w", encoding="utf-8") as outfile:
                outfile.write(f"=== {comp} 职位描述数据集 (第 {i//chunk_size + 1} 批) ===\n\n")
                for jd in chunk:
                    outfile.write(f"【职位编号】: {jd.get('job_code')}\n")
                    outfile.write(f"【职位名称】: {jd.get('title')}\n")
                    outfile.write(f"【所在部门】: {jd.get('department')}\n")
                    outfile.write(f"【所在团队】: {jd.get('team_name')}\n")
                    if jd.get('ai_analysis'):
                        outfile.write(f"【AI猎头分析】: {jd.get('ai_analysis')}\n")
                    if jd.get('candidate_profile'):
                        outfile.write(f"【理想候选人画像】: {jd.get('candidate_profile')}\n")
                    outfile.write(f"【原始JD文本】:\n{jd.get('raw_jd_text', '')}\n")
                    outfile.write("\n" + "="*80 + "\n\n")
            target_files.append(filename)
            
    print(f"Generated {len(target_files)} JD Chunk Files representing multiple companies.")
    
    # NotebookLM limits us to 50 sources max per notebook
    if len(target_files) > 50:
        print("Capping at 50 max files to comply with NotebookLM limitations.")
        target_files = target_files[:50]
    
    notebook_title = "大厂核心AI职位(JD)分析资产库"
    print(f"1. Creating Notebook: {notebook_title} ...")
    res = subprocess.run([NLM_CLI, "create", notebook_title, "--json"], capture_output=True, text=True)
    try:
        nb_id = json.loads(res.stdout).get("notebook", {}).get("id")
    except Exception as e:
        print(f"Failed to parse notebook JSON. Output: {res.stdout}\nError: {e}")
        return
        
    print(f"Notebook ID: {nb_id}")
    if not nb_id:
        return
    
    print("2. Uploading JD chunk files...")
    source_ids = []
    for f in target_files:
        add_res = subprocess.run([NLM_CLI, "source", "add", f, "-n", nb_id, "--json"], capture_output=True, text=True)
        try:
            sid = json.loads(add_res.stdout).get("source", {}).get("id")
            if sid:
                source_ids.append(sid)
        except:
            pass
            
    print(f"Waiting for {len(source_ids)} files to be indexed by NotebookLM.")
    for sid in source_ids:
        subprocess.run([NLM_CLI, "source", "wait", sid, "-n", nb_id, "--timeout", "120"])
        
    print("DONE! Notebook is ready for querying.")

if __name__ == "__main__":
    main()
