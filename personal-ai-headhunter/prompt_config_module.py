import streamlit as st
import pandas as pd
from database import get_db, SystemPrompt, Candidate, Job
from sqlalchemy.orm import Session
from ai_service import AIService
from datetime import datetime

def get_session():
    return next(get_db())

def render_prompt_config():
    st.title("⚙️ 提示词配置")
    st.info("在此配置 AI 分析简历和职位时使用的 Prompt。修改后可选择仅应用到未来数据，或重制历史数据。")
    
    db = get_session()
    
    # Fetch prompts
    # System Prompts (Active)
    active_sys_cand = db.query(SystemPrompt).filter_by(prompt_type='candidate', prompt_role='system', is_active=True).first()
    active_sys_job = db.query(SystemPrompt).filter_by(prompt_type='job', prompt_role='system', is_active=True).first()
    
    # User Prompts (List)
    user_cand_prompts = db.query(SystemPrompt).filter_by(prompt_type='candidate', prompt_role='user').all()
    
    tab1, tab2 = st.tabs(["候选人提示词 (Candidate)", "职位提示词 (Job)"])
    
    with tab1:
        st.subheader("1. System Prompt (核心指令)")
        sys_content = active_sys_cand.content if active_sys_cand else ""
        new_sys_cand = st.text_area("System Prompt", value=sys_content, height=300, key="sys_cand")
        
        if st.button("💾 更新 System Prompt", key="btn_sys_cand"):
            _update_system_prompt(db, 'candidate', new_sys_cand)
            st.success("System Prompt 已更新")
            st.rerun()
            
        st.divider()
        st.subheader("2. User Prompts (分析模版)")
        
        # List existing user prompts
        for p in user_cand_prompts:
            with st.expander(f"模版: {p.prompt_name}"):
                st.text_area("Content", value=p.content, height=150, key=f"user_p_{p.id}", disabled=True)
                # Edit/Delete logic could go here (simplified for MVP)
        
        with st.expander("➕ 新增模版"):
            new_name = st.text_input("模版名称", key="new_cand_p_name")
            new_content = st.text_area("模版内容 ({raw_text} 为占位符)", height=150, key="new_cand_p_content")
            if st.button("保存模版", key="save_new_cand_p"):
                _add_user_prompt(db, 'candidate', new_name, new_content)
                st.success("模版已添加")
                st.rerun()

    with tab2:
        st.subheader("1. System Prompt (核心指令)")
        sys_content_job = active_sys_job.content if active_sys_job else ""
        new_sys_job = st.text_area("System Prompt", value=sys_content_job, height=300, key="sys_job")
        
        if st.button("💾 更新 System Prompt", key="btn_sys_job"):
            _update_system_prompt(db, 'job', new_sys_job)
            st.success("System Prompt 已更新")
            st.rerun()

def _update_system_prompt(db, p_type, content):
    # Deactivate old
    db.query(SystemPrompt).filter_by(prompt_type=p_type, prompt_role='system', is_active=True).update({"is_active": False})
    # Add new
    p = SystemPrompt(prompt_type=p_type, prompt_role='system', prompt_name=f'Custom {datetime.now()}', content=content, is_active=True)
    db.add(p)
    db.commit()

def _add_user_prompt(db, p_type, name, content):
    p = SystemPrompt(prompt_type=p_type, prompt_role='user', prompt_name=name, content=content, is_active=True)
    db.add(p)
    db.commit()

def _reprocess_all_data(db: Session):
    # 1. Reprocess Candidates
    candidates = db.query(Candidate).all()
    if candidates:
        progress_text = "正在重析候选人..."
        my_bar = st.progress(0, text=progress_text)
        
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
                    cand.age = parsed.get("age")
                    cand.expect_location = parsed.get("expect_location")
                    cand.education_level = parsed.get("education_level")
                    cand.education_details = parsed.get("education_details")
                    cand.work_experiences = parsed.get("work_experiences")
                    cand.project_experiences = parsed.get("project_experiences")
                    cand.current_company = parsed.get("current_company")
                    cand.current_title = parsed.get("current_title")
                    
                    # Update Vector DB
                    AIService.add_candidate_to_vector_db(
                        cand.id, 
                        cand.raw_resume_text, 
                        {"name": cand.name, "skills": cand.skills}
                    )
            my_bar.progress((i + 1) / len(candidates), text=f"正在重析候选人 {i+1}/{len(candidates)}")
        
        db.commit()
        my_bar.empty()
    
    # 2. Reprocess Jobs
    jobs = db.query(Job).all()
    if jobs:
        progress_text = "正在重析职位..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, job in enumerate(jobs):
            if job.raw_jd_text:
                parsed = AIService.parse_job(job.raw_jd_text)
                if parsed.get("title") != "Parse Error":
                    job.title = parsed.get("title", job.title)
                    job.ai_analysis = parsed.get("analysis")
                    job.salary_range = parsed.get("salary_range")
                    job.location = parsed.get("location")
                    job.required_experience_years = parsed.get("required_experience_years")
                    
                    AIService.add_job_to_vector_db(
                        job.id,
                        job.raw_jd_text,
                        {"title": job.title, "company": job.company}
                    )
            my_bar.progress((i + 1) / len(jobs), text=f"正在重析职位 {i+1}/{len(jobs)}")
            
        db.commit()
        my_bar.empty()

