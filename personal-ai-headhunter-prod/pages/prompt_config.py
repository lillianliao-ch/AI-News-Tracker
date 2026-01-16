import streamlit as st
import pandas as pd
from database import get_db, SystemPrompt
from sqlalchemy.orm import Session

def get_session():
    return next(get_db())

def render_prompt_config():
    st.title("⚙️ 提示词配置")
    st.info("在此配置 AI 分析简历和职位时使用的 Prompt。修改后可选择仅应用到未来数据，或重制历史数据。")
    
    db = get_session()
    
    # Fetch active prompts
    active_candidate_prompt = db.query(SystemPrompt).filter_by(prompt_type='candidate', is_active=True).order_by(SystemPrompt.created_at.desc()).first()
    active_job_prompt = db.query(SystemPrompt).filter_by(prompt_type='job', is_active=True).order_by(SystemPrompt.created_at.desc()).first()
    
    # Default contents
    cand_content = active_candidate_prompt.content if active_candidate_prompt else ""
    job_content = active_job_prompt.content if active_job_prompt else ""
    
    with st.form("prompt_form"):
        st.subheader("1. 候选人画像提示词 (Candidate Parsing)")
        new_cand_prompt = st.text_area("Candidate Prompt", value=cand_content, height=300)
        
        st.subheader("2. 职位画像提示词 (Job Parsing)")
        new_job_prompt = st.text_area("Job Prompt", value=job_content, height=300)
        
        col1, col2 = st.columns(2)
        with col1:
            apply_btn = st.form_submit_button("💾 仅保存并应用到新数据")
        with col2:
            reprocess_btn = st.form_submit_button("⚠️ 保存并重制所有历史数据")
    
    if apply_btn:
        _save_prompts(db, new_cand_prompt, new_job_prompt)
        st.success("配置已更新！新导入的数据将使用新 Prompt，历史数据保持不变。")
        
    if reprocess_btn:
        _save_prompts(db, new_cand_prompt, new_job_prompt)
        st.warning("正在重制所有历史数据，请勿关闭页面...")
        _reprocess_all_data(db)
        st.success("全量数据重制完成！")

def _save_prompts(db: Session, cand_prompt_text, job_prompt_text):
    # Deactivate old prompts
    db.query(SystemPrompt).filter(SystemPrompt.is_active == True).update({"is_active": False})
    
    # Insert new prompts
    p1 = SystemPrompt(prompt_type='candidate', prompt_name='Custom', content=cand_prompt_text, is_active=True)
    p2 = SystemPrompt(prompt_type='job', prompt_name='Custom', content=job_prompt_text, is_active=True)
    
    db.add(p1)
    db.add(p2)
    db.commit()

def _reprocess_all_data(db: Session):
    from ai_service import AIService
    from database import Candidate, Job
    
    # 1. Reprocess Candidates
    candidates = db.query(Candidate).all()
    if candidates:
        progress_bar = st.progress(0)
        st.write(f"正在重析 {len(candidates)} 位候选人...")
        
        for i, cand in enumerate(candidates):
            if cand.raw_resume_text:
                # Call AI
                parsed = AIService.parse_resume(cand.raw_resume_text)
                if parsed.get("name") != "Parse Error":
                    # Update fields
                    cand.name = parsed.get("name", cand.name)
                    cand.email = parsed.get("email")
                    cand.phone = parsed.get("phone")
                    cand.ai_summary = parsed.get("summary")
                    cand.skills = parsed.get("skills")
                    cand.experience_years = parsed.get("experience_years")
                    cand.education_level = parsed.get("education_level")
                    cand.education_details = parsed.get("education_details")
                    cand.work_experiences = parsed.get("work_experiences")
                    cand.project_experiences = parsed.get("project_experiences")
                    cand.current_company = parsed.get("current_company")
                    cand.current_title = parsed.get("current_title")
                    
                    # Update Vector DB (Metadata might change)
                    AIService.add_candidate_to_vector_db(
                        cand.id, 
                        cand.raw_resume_text, 
                        {"name": cand.name, "skills": cand.skills}
                    )
            progress_bar.progress((i + 1) / len(candidates))
        
        db.commit()
    
    # 2. Reprocess Jobs
    jobs = db.query(Job).all()
    if jobs:
        st.write(f"正在重析 {len(jobs)} 个职位...")
        progress_bar = st.progress(0)
        
        for i, job in enumerate(jobs):
            if job.raw_jd_text:
                parsed = AIService.parse_job(job.raw_jd_text)
                if parsed.get("title") != "Parse Error":
                    job.title = parsed.get("title", job.title) # Usually we keep original title, but here we can update
                    job.ai_analysis = parsed.get("analysis")
                    job.salary_range = parsed.get("salary_range")
                    job.location = parsed.get("location")
                    job.required_experience_years = parsed.get("required_experience_years")
                    
                    AIService.add_job_to_vector_db(
                        job.id,
                        job.raw_jd_text,
                        {"title": job.title, "company": job.company}
                    )
            progress_bar.progress((i + 1) / len(jobs))
            
        db.commit()

