import os
import subprocess
import time

ARTIFACTS_DIR = "/Users/lillianliao/.gemini/antigravity/brain/cd293d26-d80b-4708-a7c9-e271554cf68e"
EXTRACTOR = "/Users/lillianliao/notion_rag/skill_research/generic_extract_org_chart.py"
WORKSPACE = "/Users/lillianliao/notion_rag/skill_research"

UNICORNS = [
    {
        "companies": "DeepSeek,深度求索,幻方",
        "teams": "大模型,算法,Infra,MoE,训练,算力,强化学习,RL,推理",
        "prefix": "DeepSeek",
        "desc": "DeepSeek(深度求索)底层架构及核心算法团队",
        "title": "DeepSeek 核心算法与Infra团队架构还原图谱"
    },
    {
        "companies": "月之暗面,Moonshot,Kimi",
        "teams": "大模型,长文本,推荐,后端,算法, Infra,商业化",
        "prefix": "Moonshot",
        "desc": "月之暗面(Kimi)底层架构及核心应用研发团队",
        "title": "Moonshot_AI(月之暗面)核心大模型团队架构还原图谱"
    },
    {
        "companies": "智谱,Zhipu,GLM,清华",
        "teams": "大模型,商业化,生态,基座,多模态,算法,对齐",
        "prefix": "Zhipu",
        "desc": "智谱AI(GLM)基座大模型与商业化解决团队",
        "title": "智谱AI(Zhipu) 核心大模型团队架构还原图谱"
    },
    {
        "companies": "百川智能,Baichuan",
        "teams": "大模型,预训练,对齐,商业化,算法,医疗,搜索",
        "prefix": "Baichuan",
        "desc": "百川智能底层架构及核心研发团队",
        "title": "Baichuan(百川智能)核心大模型团队架构还原图谱"
    },
    {
        "companies": "零一万物,01.AI,01AI",
        "teams": "大模型,预训练,多模态,Infra,算法,开源",
        "prefix": "01AI",
        "desc": "零一万物(01.AI)底层架构及核心研发团队",
        "title": "零一万物(01.AI) 核心研发团队架构还原图谱"
    },
    {
        "companies": "阶跃星辰,StepFun",
        "teams": "大模型,多模态,预训练,Infra,算法,强化学习",
        "prefix": "StepFun",
        "desc": "阶跃星辰(StepFun)多模态大模型及核心研发团队",
        "title": "阶跃星辰(StepFun) 核心大模型团队架构还原图谱"
    }
]

def main():
    print("🚀 [BATCH ENGINE] Starting sequential Org Chart generation for 6 Domestic AI Unicorns...")
    success_count = 0
    
    for i, target in enumerate(UNICORNS, 1):
        print(f"\n[{i}/6] Processing {target['prefix']}...")
        cmd = [
            "python3", EXTRACTOR,
            "--companies", target["companies"],
            "--teams", target["teams"],
            "--prefix", target["prefix"],
            "--desc", target["desc"],
            "--title", target["title"]
        ]
        
        try:
            # 1. Execute the NotebookLM pipeline (takes several minutes)
            subprocess.run(cmd, cwd=WORKSPACE, check=True)
            
            # 2. Move file directly to artifacts dir for User review
            source_md = os.path.join(WORKSPACE, f"{target['prefix']}_Org_Chart", f"{target['prefix']}_Org_Chart_Mapping.md")
            dest_md = os.path.join(ARTIFACTS_DIR, f"{target['prefix']}_Org_Chart_Mapping.md")
            
            if os.path.exists(source_md):
                os.system(f"cp '{source_md}' '{dest_md}'")
                print(f"✅ {target['prefix']} successful! Copied to artifacts.")
                success_count += 1
            else:
                print(f"⚠️ {target['prefix']} pipeline finished, but output file missing: {source_md}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to process {target['prefix']}. Error: {e}")
            
        time.sleep(2) # brief pause between big tasks
        
    print(f"\n🎉 Batch processing complete! {success_count}/6 artifacts generated.")

if __name__ == "__main__":
    main()
