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
   【AI/算法类】大模型/LLM, Agent/智能体, NLP, 多模态, 语音, CV, 推荐系统, 搜索, AI Infra, 具身智能, 垂直应用
   【工程类】客户端开发, 后端开发, 前端开发, 基础架构/Infra, 数据库/存储, 安全, 测试/QA, 音视频
   ⚠️ 必须从上述选项中选择，不要用"其他"。如果候选人是C++客户端/移动端/跨端开发，选"客户端开发"；如果是服务端/微服务，选"后端开发"。

2. ★★ core_specialty (核心专长/主线) - 多选，选择最能定义"做什么"的1-2个 ★★
   这是最重要的标签！指定此人/岗位的核心职业方向：
   【AI/算法专长】
   - 语音合成 (TTS)
   - 语音识别 (ASR)
   - 多模态理解
   - 多模态生成
   - 图像/视频生成 (AIGC/美颜/风格迁移等)
   - 图像/视频理解 (分析/标注/内容理解)
   - 视觉分类/检测 (目标检测/图像分类/分割)
   - 内容安全/风控 (审核/违规识别/风控)
   - OCR/文档识别
   - 推荐系统
   - 搜索排序
   - Agent/智能体开发
   - 对话系统 (聊天机器人/对话管理)
   - AI客服/智能客服 (客服机器人/工单系统/服务自动化)
   - 代码生成
   【工程专长】
   - IM/即时通讯 (消息系统/实时通信/消息通道)
   - 跨端框架 (跨平台C++/Flutter/React Native/多端统一)
   - 客户端基础架构 (SDK/客户端Infra/端侧框架)
   - 音视频引擎 (流媒体/编解码/RTC)
   - 网络通信 (网络协议/长连接/传输优化)
   - 微服务架构 (服务治理/中间件)
   - DevOps/CI-CD
   - 数据平台 (数据仓库/数据治理/ETL)
   ⚠️ 务必填写！如果候选人做C++客户端IM/消息系统，应选"IM/即时通讯"和"客户端基础架构"
   
3. tech_skills (技术技能/辅线) - 多选，选择1-3个通用技能
   这些是"怎么做"的方法，不定义职业方向：
   【AI技能】预训练, SFT微调, RLHF/对齐, 推理加速, 模型压缩/量化, 分布式训练, RAG/知识库, 算子优化, 框架开发
   【工程技能】跨端开发, 性能优化, 高并发, 架构设计, 组件化/模块化

4. role_type (岗位类型) - 单选:
   算法工程师, 算法专家, 算法研究员, 客户端工程师, 后端工程师, 前端工程师, 架构师, 解决方案架构师, 产品经理, 技术管理, 研究员, 运维/SRE, 数据工程师, 工程开发

5. role_orientation (角色定位) - 多选:
   Research型, Applied/落地型, Platform/Infra型, Tool/Agent Builder, Tech Lead, 纯IC

6. tech_stack (技术栈) - 多选:
   Python, C++, Java, Go, Rust, Kotlin, Swift, Objective-C, TypeScript, JavaScript,
   PyTorch, TensorFlow, LangChain, vLLM, Transformers, DeepSpeed, TensorRT, CUDA,
   QT, Flutter, React Native, Electron,
   K8s, Ray, Spark, FAISS, Redis, MySQL, PostgreSQL, MongoDB

7. industry_exp (行业背景) - 多选:
   互联网大厂, AI独角兽, 云厂商, 芯片/硬件, 外企, 学术背景, IM/通信厂商, 游戏

8. seniority (职级层次) - 单选:
   初级(0-3年), 中级(3-5年), 资深(5-10年), 专家(10年+), 管理层
   ⚠️ 根据工作年限判断：硕士毕业后工作4-5年 = 资深(5-10年)

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


def build_candidate_resume_text(candidate_obj=None, *, skills=None, work_experiences=None, 
                                  education_details=None, project_experiences=None,
                                  current_title=None, current_company=None):
    """
    从结构化数据合成简历文本（用于无 raw_resume_text 的脉脉候选人）。
    可接收 ORM 对象或独立字段。
    """
    parts = []
    
    # 如果传入 ORM 对象，从中提取数据
    if candidate_obj is not None:
        skills = skills or candidate_obj.skills
        work_experiences = work_experiences or candidate_obj.work_experiences
        education_details = education_details or candidate_obj.education_details
        project_experiences = project_experiences or candidate_obj.project_experiences
        current_title = current_title or candidate_obj.current_title
        current_company = current_company or candidate_obj.current_company
    
    # 当前职位
    if current_title or current_company:
        parts.append(f"当前: {current_title or ''} @ {current_company or ''}")
    
    # 技能标签
    if skills:
        skill_list = skills if isinstance(skills, list) else json.loads(skills) if isinstance(skills, str) else []
        if skill_list:
            parts.append(f"技能: {', '.join(skill_list)}")
    
    # 工作经历
    if work_experiences:
        exp_list = work_experiences if isinstance(work_experiences, list) else json.loads(work_experiences) if isinstance(work_experiences, str) else []
        if exp_list:
            parts.append("工作经历:")
            for exp in exp_list[:6]:
                if isinstance(exp, dict):
                    line = f"  - {exp.get('company', '')} {exp.get('position', exp.get('title', ''))} ({exp.get('start_date', exp.get('time', ''))}~{exp.get('end_date', '')})"
                    desc = exp.get('description', '')
                    if desc:
                        line += f" {desc[:150]}"
                    parts.append(line)
    
    # 教育经历
    if education_details:
        edu_list = education_details if isinstance(education_details, list) else json.loads(education_details) if isinstance(education_details, str) else []
        if edu_list:
            parts.append("教育经历:")
            for edu in edu_list[:4]:
                if isinstance(edu, dict):
                    parts.append(f"  - {edu.get('school', '')} {edu.get('degree', '')} {edu.get('major', '')} ({edu.get('start_year', '')}~{edu.get('end_year', '')})")
    
    # 项目经历
    if project_experiences:
        proj_list = project_experiences if isinstance(project_experiences, list) else json.loads(project_experiences) if isinstance(project_experiences, str) else []
        if proj_list:
            parts.append("项目经历:")
            for proj in proj_list[:4]:
                if isinstance(proj, dict):
                    desc = proj.get('description', '')[:150]
                    parts.append(f"  - {proj.get('name', '')} {desc}")
    
    return "\n".join(parts)


def extract_tags_for_candidate_by_id(candidate_id: int) -> dict:
    """
    为单个候选人提取结构化标签（供导入时调用）。
    支持无 raw_resume_text 的脉脉候选人——自动从结构化字段合成简历。
    Returns: 提取的标签 dict，失败返回 None
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, current_title, current_company, experience_years, 
               education_level, raw_resume_text, ai_summary,
               skills, work_experiences, education_details, project_experiences
        FROM candidates WHERE id = ?
    """, (candidate_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        print(f"❌ 候选人 ID={candidate_id} 不存在")
        return None
    
    cid, name, title, company, years, edu, resume, summary, skills_json, work_json, edu_json, proj_json = row
    
    # 构建简历文本：优先 ai_summary → raw_resume_text → 合成简历
    resume_text = summary or resume or ''
    if not resume_text.strip():
        # 从结构化数据合成
        skills = json.loads(skills_json) if isinstance(skills_json, str) and skills_json else skills_json
        work_exp = json.loads(work_json) if isinstance(work_json, str) and work_json else work_json
        edu_det = json.loads(edu_json) if isinstance(edu_json, str) and edu_json else edu_json
        proj_exp = json.loads(proj_json) if isinstance(proj_json, str) and proj_json else proj_json
        
        resume_text = build_candidate_resume_text(
            skills=skills, work_experiences=work_exp,
            education_details=edu_det, project_experiences=proj_exp,
            current_title=title, current_company=company
        )
        print(f"  📝 合成简历文本 ({len(resume_text)} 字)")
    
    if not resume_text.strip():
        conn.close()
        print(f"❌ {name} 无任何可用信息，跳过")
        return None
    
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
        print(f"✅ {name} 标签提取成功: {list(tags.keys())}")
    else:
        print(f"❌ {name} 标签提取失败")
    
    conn.close()
    return tags


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
                   education_level, raw_resume_text, ai_summary,
                   skills, work_experiences, education_details, project_experiences
            FROM candidates
        """)
    else:
        cursor.execute("""
            SELECT id, name, current_title, current_company, experience_years, 
                   education_level, raw_resume_text, ai_summary,
                   skills, work_experiences, education_details, project_experiences
            FROM candidates 
            WHERE structured_tags IS NULL OR structured_tags = 'null'
        """)
    candidates = cursor.fetchall()
    print(f"\n=== 开始处理 {len(candidates)} 个候选人 {'(强制更新)' if force else ''} ===")
    
    for i, (cid, name, title, company, years, edu, resume, summary, skills_json, work_json, edu_json, proj_json) in enumerate(candidates):
        # 优先使用ai_summary，其次使用raw_resume_text，最后合成
        resume_text = summary or resume or ''
        if not resume_text.strip():
            skills = json.loads(skills_json) if isinstance(skills_json, str) and skills_json else skills_json
            work_exp = json.loads(work_json) if isinstance(work_json, str) and work_json else work_json
            edu_det = json.loads(edu_json) if isinstance(edu_json, str) and edu_json else edu_json
            proj_exp = json.loads(proj_json) if isinstance(proj_json, str) and proj_json else proj_json
            resume_text = build_candidate_resume_text(
                skills=skills, work_experiences=work_exp,
                education_details=edu_det, project_experiences=proj_exp,
                current_title=title, current_company=company
            )
        
        if not resume_text.strip():
            print(f"[{i+1}/{len(candidates)}] ⏭️ {name} - 无任何数据，跳过")
            continue
        
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
