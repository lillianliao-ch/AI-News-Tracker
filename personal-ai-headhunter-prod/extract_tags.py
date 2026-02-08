#!/usr/bin/env python3
"""
JD和候选人标签提取脚本
使用通义千问批量提取结构化标签
"""

import sqlite3
import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量 - 与 ai_service.py 保持一致
env_path = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    local_env = os.path.join(os.path.dirname(__file__), '.env.local')
    if os.path.exists(local_env):
        load_dotenv(local_env, override=True)
    else:
        load_dotenv()

# 配置
DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 标签体系定义
TAG_SCHEMA = """
## 标签体系说明

1. tech_domain (技术方向) - 多选:
   大模型/LLM, Agent/智能体, NLP, 多模态, 语音, CV, 推荐系统, 搜索, AI Infra, 具身智能, 垂直应用

2. ★★ core_specialty (核心专长/主线) - 多选，选择最能定义"做什么"的1-2个 ★★
   这是最重要的标签！指定此人/岗位的核心职业方向：
   - 语音合成 (TTS)
   - 语音识别 (ASR)
   - 多模态理解
   - 多模态生成
   - 图像/视频生成
   - 推荐系统
   - 搜索排序
   - Agent/智能体开发
   - 对话系统
   - 代码生成
   
3. tech_skills (技术技能/辅线) - 多选，选择1-3个通用技能
   这些是"怎么做"的方法，不定义职业方向：
   - 预训练
   - SFT微调
   - RLHF/对齐
   - 推理加速
   - 模型压缩/量化
   - 分布式训练
   - RAG/知识库
   - 算子优化
   - 框架开发

4. role_type (岗位类型) - 单选:
   算法工程师, 算法专家, 算法研究员, 工程开发, 解决方案架构师, 产品经理, 技术管理, 研究员, 运维/SRE, 数据工程师

5. role_orientation (角色定位) - 多选:
   Research型, Applied/落地型, Platform/Infra型, Tool/Agent Builder, Tech Lead, 纯IC

6. tech_stack (技术栈) - 多选:
   Python, C++, Java, Go, PyTorch, TensorFlow, LangChain, vLLM, Transformers, DeepSpeed, TensorRT, CUDA, K8s, Ray, Spark, FAISS

7. industry_exp (行业背景) - 多选:
   互联网大厂, AI独角兽, 云厂商, 芯片/硬件, 外企, 学术背景

8. seniority (职级层次) - 单选:
   初级(0-3年), 中级(3-5年), 高级(5-8年), 专家(8年+), 管理层

9. education (教育背景):
   - degree: 博士/硕士/本科
   - school_tier: 顶级名校/985/211/海外Top100/普通本科
"""

JD_PROMPT = """请从以下JD中提取结构化标签。

{schema}

【JD信息】
职位: {title}
公司: {company}
描述: {description}

⚠️ 重要：请仔细区分 core_specialty（核心专长，定义"做什么"）和 tech_skills（技术技能，定义"怎么做"）

请输出JSON格式，只输出JSON，不要其他内容:
{{
  "tech_domain": ["技术方向1", "技术方向2"],
  "core_specialty": ["核心专长1"],
  "tech_skills": ["技术技能1", "技术技能2"],
  "role_type": "岗位类型",
  "role_orientation": ["角色定位1"],
  "tech_stack": ["技术栈1", "技术栈2"],
  "preferred_industry": ["优先行业背景"],
  "seniority": "职级要求",
  "education_requirement": "学历要求"
}}"""

CANDIDATE_PROMPT = """请从以下候选人信息中提取结构化标签。

{schema}

【候选人信息】
姓名: {name}
当前职位: {title}
当前公司: {company}
工作年限: {years}年
学历: {education}
简历/画像: {resume}

⚠️ 重要：请仔细区分 core_specialty（核心专长，定义此人"做什么"职业方向）和 tech_skills（技术技能，定义"怎么做"的方法）
例如：语音合成工程师的 core_specialty 是 ["语音合成"]，tech_skills 可能是 ["SFT微调", "预训练"]

请输出JSON格式，只输出JSON，不要其他内容:
{{
  "tech_domain": ["技术方向1", "技术方向2"],
  "core_specialty": ["核心专长1"],
  "tech_skills": ["技术技能1", "技术技能2"],
  "role_type": "岗位类型",
  "role_orientation": ["角色定位1"],
  "tech_stack": ["技术栈1", "技术栈2"],
  "industry_exp": ["行业背景"],
  "seniority": "职级层次",
  "education": {{
    "degree": "学历",
    "school_tier": "学校层次"
  }}
}}"""


def extract_tags(prompt: str, max_retries=3) -> dict:
    """调用LLM提取标签"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="qwen-plus",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            # 清理可能的markdown标记
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except Exception as e:
            print(f"  重试 {attempt+1}/{max_retries}: {e}")
            time.sleep(1)
    return None


def process_jobs(force=False):
    """处理所有JD
    Args:
        force: 如果为 True，重新处理所有记录（包括已有标签的）
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if force:
        cursor.execute("SELECT id, title, company, raw_jd_text FROM jobs")
    else:
        cursor.execute("SELECT id, title, company, raw_jd_text FROM jobs WHERE structured_tags IS NULL OR structured_tags = 'null'")
    jobs = cursor.fetchall()
    print(f"\n=== 开始处理 {len(jobs)} 个JD {'(强制更新)' if force else ''} ===")
    
    for i, (jid, title, company, jd_text) in enumerate(jobs):
        prompt = JD_PROMPT.format(
            schema=TAG_SCHEMA,
            title=title or '',
            company=company or '',
            description=(jd_text or '')[:2000]
        )
        
        tags = extract_tags(prompt)
        if tags:
            cursor.execute(
                "UPDATE jobs SET structured_tags = ? WHERE id = ?",
                (json.dumps(tags, ensure_ascii=False), jid)
            )
            conn.commit()
            print(f"[{i+1}/{len(jobs)}] ✅ {title[:30]}")
        else:
            print(f"[{i+1}/{len(jobs)}] ❌ {title[:30]} - 提取失败")
        
        time.sleep(0.5)  # 限速
    
    conn.close()
    print("JD处理完成！")


def process_candidates(force=False):
    """处理所有候选人
    Args:
        force: 如果为 True，重新处理所有记录（包括已有标签的）
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if force:
        cursor.execute("""
            SELECT id, name, current_title, current_company, experience_years, 
                   education_level, raw_resume_text, ai_summary 
            FROM candidates
        """)
    else:
        cursor.execute("""
            SELECT id, name, current_title, current_company, experience_years, 
                   education_level, raw_resume_text, ai_summary 
            FROM candidates 
            WHERE structured_tags IS NULL OR structured_tags = 'null'
        """)
    candidates = cursor.fetchall()
    print(f"\n=== 开始处理 {len(candidates)} 个候选人 {'(强制更新)' if force else ''} ===")
    
    for i, (cid, name, title, company, years, edu, resume, summary) in enumerate(candidates):
        # 优先使用ai_summary，其次使用raw_resume_text
        resume_text = summary or resume or ''
        
        prompt = CANDIDATE_PROMPT.format(
            schema=TAG_SCHEMA,
            name=name or '',
            title=title or '',
            company=company or '',
            years=years or 0,
            education=edu or '',
            resume=resume_text[:2000]
        )
        
        tags = extract_tags(prompt)
        if tags:
            cursor.execute(
                "UPDATE candidates SET structured_tags = ? WHERE id = ?",
                (json.dumps(tags, ensure_ascii=False), cid)
            )
            conn.commit()
            print(f"[{i+1}/{len(candidates)}] ✅ {name}")
        else:
            print(f"[{i+1}/{len(candidates)}] ❌ {name} - 提取失败")
        
        time.sleep(0.5)  # 限速
    
    conn.close()
    print("候选人处理完成！")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python extract_tags.py [jobs|candidates|all] [--force]")
        print("  --force: 强制更新所有记录（包括已有标签的）")
        sys.exit(1)
    
    target = sys.argv[1]
    force = '--force' in sys.argv
    
    if force:
        print("⚠️ 强制更新模式：将重新处理所有记录")
    
    if target == "jobs":
        process_jobs(force=force)
    elif target == "candidates":
        process_candidates(force=force)
    elif target == "all":
        process_jobs(force=force)
        process_candidates(force=force)
    else:
        print(f"未知目标: {target}")
