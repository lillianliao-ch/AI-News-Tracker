import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import String
from database import engine, init_db, get_db, Candidate, Job, MatchRecord, SystemPrompt
from ai_service import AIService
import json
import re

# 初始化页面配置
st.set_page_config(
    page_title="AI Headhunter Personal",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 Session State
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'list'
if 'selected_candidate_id' not in st.session_state:
    st.session_state.selected_candidate_id = None
if 'selected_job_id' not in st.session_state:
    st.session_state.selected_job_id = None
if 'job_view_mode' not in st.session_state:
    st.session_state.job_view_mode = 'list'

# 初始化数据库
if not os.path.exists("personal-ai-headhunter/data/headhunter.db"):
    init_db()

# Helper Functions
def get_session():
    return next(get_db())

def save_uploaded_file(uploaded_file):
    if not os.path.exists("personal-ai-headhunter/data/uploads"):
        os.makedirs("personal-ai-headhunter/data/uploads", exist_ok=True)
    file_path = os.path.join("personal-ai-headhunter/data/uploads", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def back_to_list():
    st.session_state.view_mode = 'list'
    st.session_state.selected_candidate_id = None
    # 保持查询条件不变，不清空
    st.rerun()

def format_date(val):
    if not val or str(val) == "None": return "-"
    try:
        val_float = float(val)
        if val_float > 30000000000: 
             val_float /= 1000
        return datetime.fromtimestamp(val_float).strftime('%Y-%m-%d')
    except:
        return str(val)

def delete_candidate(cand_id):
    db = get_session()
    cand = db.query(Candidate).filter(Candidate.id == cand_id).first()
    if cand:
        db.delete(cand)
        db.commit()
        st.toast(f"已删除候选人: {cand.name}")
        # Also delete from ChromaDB if possible (not implemented in AIService yet but good practice)
        return True
    return False

def delete_job(job_id):
    db = get_session()
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        db.delete(job)
        db.commit()
        st.toast(f"已删除职位: {job.title}")
        return True
    return False

# Sidebar Navigation
st.sidebar.title("🕵️‍♂️ AI Headhunter")

# 支持从其他页面跳转
nav_options = ["Dashboard", "人才库管理", "职位库管理", "智能匹配", "提示词配置"]
default_idx = nav_options.index(st.session_state.get('nav_page', 'Dashboard')) if st.session_state.get('nav_page') in nav_options else 0
page = st.sidebar.radio("导航", nav_options, index=default_idx)
st.session_state.nav_page = page  # 同步状态

# ---------------- PROMPT CONFIG ----------------
if page == "提示词配置":
    from prompt_config_module import render_prompt_config
    render_prompt_config()

# ---------------- DASHBOARD ----------------
elif page == "Dashboard":
    st.title("📊 概览")
    
    db = get_session()
    cand_count = db.query(Candidate).count()
    friend_count = db.query(Candidate).filter(Candidate.is_friend == 1).count()
    job_count = db.query(Job).count()
    match_count = db.query(MatchRecord).count()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("人才总数", cand_count)
    col2.metric("好友总数", friend_count)
    col3.metric("在招职位", job_count)
    col4.metric("匹配记录", match_count)
    
    st.divider()
    
    # --- 按公司统计人数 - 两图并列 ---
    from sqlalchemy import func
    import pandas as pd
    import plotly.express as px
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### 🏢 人才公司分布 (Top 20)")
        
        # 查询全部公司统计
        company_stats = db.query(
            Candidate.current_company, 
            func.count(Candidate.id).label('count')
        ).filter(
            Candidate.current_company != None,
            Candidate.current_company != ''
        ).group_by(
            Candidate.current_company
        ).order_by(
            func.count(Candidate.id).desc()
        ).all()
        
        top_20 = company_stats[:20]
        
        if top_20:
            df_company = pd.DataFrame(top_20, columns=['公司', '人数'])
            df_company = df_company.sort_values('人数', ascending=True)
            
            fig = px.bar(df_company, x='人数', y='公司', orientation='h', text='人数')
            fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无公司数据")
    
    with chart_col2:
        st.markdown("### ⭐ 好友公司分布 (Top 20)")
        
        # 查询好友公司统计
        friend_company_stats = db.query(
            Candidate.current_company, 
            func.count(Candidate.id).label('count')
        ).filter(
            Candidate.current_company != None,
            Candidate.current_company != '',
            Candidate.is_friend == 1
        ).group_by(
            Candidate.current_company
        ).order_by(
            func.count(Candidate.id).desc()
        ).all()
        
        friend_top_20 = friend_company_stats[:20]
        
        if friend_top_20:
            df_friend = pd.DataFrame(friend_top_20, columns=['公司', '人数'])
            df_friend = df_friend.sort_values('人数', ascending=True)
            
            fig2 = px.bar(df_friend, x='人数', y='公司', orientation='h', text='人数',
                         color_discrete_sequence=['#FFD700'])  # 金色
            fig2.update_layout(height=500, yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            fig2.update_traces(textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("暂无好友数据")
    
    # 详细数据
    with st.expander("📋 查看详细数据"):
        data_col1, data_col2 = st.columns(2)
        with data_col1:
            if top_20:
                st.markdown("**全部人才**")
                st.dataframe(pd.DataFrame(top_20, columns=['公司', '人数']), use_container_width=True)
        with data_col2:
            if friend_top_20:
                st.markdown("**好友**")
                st.dataframe(pd.DataFrame(friend_top_20, columns=['公司', '人数']), use_container_width=True)
    
    st.divider()
    
    # --- 最近一周沟通记录 ---
    st.markdown("### 💬 最近一周沟通记录")
    
    from datetime import datetime, timedelta
    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_ago_str = one_week_ago.strftime("%Y-%m-%d")
    
    # 查询有沟通记录的候选人
    candidates_with_logs = db.query(Candidate).filter(
        Candidate.communication_logs != None
    ).all()
    
    # 筛选最近一周有更新的沟通记录
    recent_logs = []
    for cand in candidates_with_logs:
        if cand.communication_logs:
            for log in cand.communication_logs:
                log_time = log.get('time', '')
                if log_time >= one_week_ago_str:
                    recent_logs.append({
                        'id': cand.id,
                        'name': cand.name,
                        'company': cand.current_company or '-',
                        'time': log_time,
                        'content': log.get('content', '')[:100] + ('...' if len(log.get('content', '')) > 100 else '')
                    })
    
    # 按时间倒序排序
    recent_logs.sort(key=lambda x: x['time'], reverse=True)
    
    if recent_logs:
        # 创建表格
        for log in recent_logs[:20]:  # 最多显示20条
            col_name, col_company, col_content, col_time = st.columns([1, 1.5, 4, 1])
            with col_name:
                if st.button(f"👤 {log['name']}", key=f"log_nav_{log['id']}_{log['time']}"):
                    st.session_state.selected_candidate_id = log['id']
                    st.session_state.view_mode = 'detail'
                    st.session_state.nav_page = '人才库管理'  # 切换页面
                    st.rerun()
            with col_company:
                st.caption(log['company'])
            with col_content:
                st.markdown(log['content'])
            with col_time:
                st.caption(log['time'])
            st.divider()
    else:
        st.info("最近一周暂无沟通记录")
    
    st.divider()
    
    st.markdown("### 👋 欢迎回来")
    st.info("请从左侧菜单开始操作。首先请在【人才库管理】或【职位库管理】中导入数据。")

# ---------------- CANDIDATES ----------------
elif page == "人才库管理":
    
    db = get_session()

    if st.session_state.view_mode == 'detail' and st.session_state.selected_candidate_id:
        # --- 详情视图 ---
        cand_id = st.session_state.selected_candidate_id
        cand = db.query(Candidate).filter(Candidate.id == cand_id).first()
        
        # 初始化编辑状态（避免跨候选人保留状态）
        if 'last_viewed_cand_id' not in st.session_state or st.session_state.last_viewed_cand_id != cand_id:
            st.session_state.last_viewed_cand_id = cand_id
            st.session_state.show_skill_editor = False
        
        if cand:
            # === 第一行：导航 + 操作按钮 ===
            col_nav, col_spacer, col_update = st.columns([1, 3, 1])
            with col_nav:
                if st.button("← 返回列表"):
                    back_to_list()
            with col_update:
                if st.button("🔄 更新画像", type="primary", use_container_width=True):
                    with st.spinner("正在更新 AI 画像..."):
                        active_p = db.query(SystemPrompt).filter_by(prompt_type='candidate', prompt_role='user', is_active=True).first()
                        template_c = active_p.content if active_p else None
                        
                        parsed = AIService.parse_resume(cand.raw_resume_text, user_prompt_template=template_c)
                        if parsed.get("name") != "Parse Error":
                            cand.name = parsed.get("name") or cand.name
                            cand.email = parsed.get("email") or cand.email
                            cand.phone = parsed.get("phone") or cand.phone
                            summary = parsed.get("summary")
                            if not summary:
                                if "evaluation" in parsed: summary = str(parsed.get("evaluation"))
                                elif "analysis" in parsed: summary = str(parsed.get("analysis"))
                                else: summary = "AI未提供评价"
                            cand.ai_summary = summary
                            cand.skills = parsed.get("skills")
                            cand.experience_years = parsed.get("experience_years")
                            cand.age = parsed.get("age")
                            cand.expect_location = parsed.get("expect_location")
                            cand.education_level = parsed.get("education_level")
                            cand.education_details = parsed.get("education_details")
                            cand.work_experiences = parsed.get("work_experiences")
                            cand.project_experiences = parsed.get("project_experiences")
                            cand.current_company = parsed.get("current_company") or cand.current_company
                            cand.current_title = parsed.get("current_title") or cand.current_title
                            
                            AIService.add_candidate_to_vector_db(cand.id, cand.raw_resume_text, {"name": cand.name, "skills": cand.skills})
                            db.commit()
                            db.refresh(cand)
                            st.success("画像已更新")
                            st.rerun()
                        else:
                            st.error("更新失败")
            
            # === 第二行：姓名 + 好友标记 + 状态标签 + 编辑开关 ===
            name_col, star_col, badge_col, edit_basic_col = st.columns([2.5, 0.5, 2, 1])
            
            activity_badge = ""
            priority_badge = ""
            if cand.notes:
                notes_str = str(cand.notes)
                if "P0" in notes_str:
                    activity_badge = "🟢 活跃"
                    priority_badge = "`P0-今日联系`"
                elif "P1" in notes_str:
                    activity_badge = "🔵 近期"
                    priority_badge = "`P1-本周联系`"
                elif "P2" in notes_str:
                    activity_badge = "⚪"
                    priority_badge = "`P2-常规`"
            
            with name_col:
                st.markdown(f"## {cand.name} {activity_badge} {priority_badge}")
            
            with star_col:
                # 好友星星标记
                is_friend = cand.is_friend == 1
                star_icon = "⭐" if is_friend else "☆"
                star_label = "已关注" if is_friend else "关注"
                if st.button(f"{star_icon}", key="toggle_friend_star", help=star_label):
                    from datetime import datetime
                    if is_friend:
                        cand.is_friend = 0
                        cand.friend_added_at = None
                        cand.friend_channel = None
                        st.toast("已取消关注")
                    else:
                        cand.is_friend = 1
                        cand.friend_added_at = datetime.now().strftime("%Y-%m-%d")
                        st.toast("⭐ 已关注")
                    db.commit()
                    st.rerun()
                
                # 显示渠道信息
                if is_friend:
                    channel = cand.friend_channel or "未设置"
                    st.caption(f"📱 {channel}")
            
            with badge_col:
                # 好友渠道选择（仅在已关注时显示）
                if cand.is_friend == 1:
                    channel_options = ["脉脉", "微信", "LinkedIn", "钉钉", "邮件", "电话", "其他"]
                    current_channel = cand.friend_channel or "脉脉"
                    current_idx = channel_options.index(current_channel) if current_channel in channel_options else 0
                    new_channel = st.selectbox(
                        "沟通渠道", 
                        channel_options, 
                        index=current_idx,
                        key="friend_channel_select",
                        label_visibility="collapsed"
                    )
                    if new_channel != cand.friend_channel:
                        cand.friend_channel = new_channel
                        db.commit()
                        st.toast(f"渠道已更新: {new_channel}")
                        st.rerun()
                else:
                    # 显示活跃度标签
                    if activity_badge:
                        st.markdown(f"{activity_badge} {priority_badge}")
            
            with edit_basic_col:
                edit_basic_mode = st.toggle("✏️ 编辑基础信息", key="edit_basic_toggle")
            
            if edit_basic_mode:
                # 编辑模式
                with st.container(border=True):
                    # 第一行：姓名、年龄、年限、学历、公司、职位、地点
                    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6, r1c7 = st.columns([1.2, 0.8, 0.8, 0.8, 1.5, 1.5, 1])
                    with r1c1:
                        new_name = st.text_input("姓名", value=cand.name or "", key="edit_name")
                    with r1c2:
                        new_age = st.number_input("年龄", value=cand.age or 0, min_value=0, max_value=100, key="edit_age")
                    with r1c3:
                        new_exp = st.number_input("年限", value=cand.experience_years or 0, min_value=0, max_value=50, key="edit_exp")
                    with r1c4:
                        edu_options = ["未知", "大专", "本科", "硕士", "博士", "其他"]
                        current_edu_idx = edu_options.index(cand.education_level) if cand.education_level in edu_options else 0
                        new_edu = st.selectbox("学历", edu_options, index=current_edu_idx, key="edit_edu")
                    with r1c5:
                        new_company = st.text_input("公司", value=cand.current_company or "", key="edit_company")
                    with r1c6:
                        new_title = st.text_input("职位", value=cand.current_title or "", key="edit_title")
                    with r1c7:
                        new_location = st.text_input("地点", value=cand.expect_location or "", key="edit_location")
                    
                    # 第二行：联系方式
                    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
                    with r2c1:
                        new_phone = st.text_input("📱 电话", value=cand.phone or "", key="edit_phone_basic")
                    with r2c2:
                        new_email = st.text_input("📧 邮箱", value=cand.email or "", key="edit_email_basic")
                    with r2c3:
                        new_linkedin = st.text_input("🔗 LinkedIn", value=cand.linkedin_url or "", key="edit_linkedin_basic")
                    with r2c4:
                        new_github = st.text_input("💻 GitHub", value=cand.github_url or "", key="edit_github_basic")
                    
                    # 简历上传
                    st.markdown("##### 📄 上传简历")
                    uploaded_resume = st.file_uploader("上传简历文件 (PDF/Word/TXT)", type=["pdf", "docx", "txt"], key="upload_resume")
                    
                    if uploaded_resume:
                        # 读取文件内容
                        if uploaded_resume.name.endswith('.txt'):
                            resume_content = uploaded_resume.read().decode('utf-8')
                        elif uploaded_resume.name.endswith('.pdf'):
                            try:
                                import PyPDF2
                                pdf_reader = PyPDF2.PdfReader(uploaded_resume)
                                resume_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                            except:
                                resume_content = "[PDF读取失败，请安装PyPDF2]"
                        else:
                            resume_content = "[暂不支持此格式，请使用TXT或PDF]"
                        
                        st.text_area("简历内容预览", value=resume_content[:500] + "...", height=100, disabled=True)
                    
                    if st.button("💾 保存", type="primary"):
                        cand.name = new_name
                        cand.age = new_age if new_age > 0 else None
                        cand.experience_years = new_exp if new_exp > 0 else None
                        cand.education_level = new_edu
                        cand.current_company = new_company
                        cand.current_title = new_title
                        cand.expect_location = new_location
                        cand.phone = new_phone
                        cand.email = new_email
                        cand.linkedin_url = new_linkedin
                        cand.github_url = new_github
                        
                        if uploaded_resume:
                            if uploaded_resume.name.endswith('.txt'):
                                resume_content = uploaded_resume.read().decode('utf-8')
                            elif uploaded_resume.name.endswith('.pdf'):
                                try:
                                    import PyPDF2
                                    uploaded_resume.seek(0)
                                    pdf_reader = PyPDF2.PdfReader(uploaded_resume)
                                    resume_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                                except:
                                    resume_content = None
                            else:
                                resume_content = None
                            
                            if resume_content:
                                cand.raw_resume_text = resume_content
                                cand.source_file = uploaded_resume.name
                        
                        db.commit()
                        st.success("✅ 已保存！")
            else:
                # 展示模式
                # === 第三行：基础信息（紧凑一行）===
                age_str = f"{cand.age}岁" if cand.age else "-"
                exp_str = f"{cand.experience_years}年" if cand.experience_years else "-"
                edu_str = cand.education_level or "未知"
                loc_str = cand.expect_location or "-"
                
                st.markdown(f"📍 **{loc_str}** │ **{exp_str}** │ **{edu_str}** │ **{age_str}**")
                
                if cand.current_company or cand.current_title:
                    company_str = cand.current_company or ""
                    title_str = cand.current_title[:50] if cand.current_title else ""
                    st.markdown(f"🏢 **{company_str}** · {title_str}")
            
            # 技能标签（可编辑）
            skill_col, edit_col = st.columns([5, 1])
            with skill_col:
                current_skills = cand.skills if cand.skills and isinstance(cand.skills, list) else []
                if current_skills:
                    tags = " ".join([f"`{s}`" for s in current_skills[:8]])
                    st.markdown(f"🏷️ {tags}")
                else:
                    st.caption("🏷️ 暂无技能标签")
            with edit_col:
                if st.button("✏️ 编辑", key="edit_skills_btn", help="编辑技能标签"):
                    st.session_state.show_skill_editor = not st.session_state.get('show_skill_editor', False)
            
            # 技能标签编辑器（展开时显示）
            if st.session_state.get('show_skill_editor', False):
                skills_str = ", ".join(current_skills) if current_skills else ""
                new_skills_str = st.text_input(
                    "编辑技能（逗号分隔）", 
                    value=skills_str, 
                    key="edit_skills_input",
                    placeholder="例如: Python, LLM, Agent, 大模型"
                )
                if new_skills_str != skills_str:
                    # 解析并保存
                    new_skills = [s.strip() for s in new_skills_str.split(",") if s.strip()]
                    cand.skills = new_skills
                    db.commit()
                    st.toast("技能标签已更新")
                    st.session_state.show_skill_editor = False
                    st.rerun()
            
            # === 第四行：联系方式（有内容才显示）===
            contact_info = []
            if cand.phone:
                contact_info.append(f"📱 {cand.phone}")
            if cand.email:
                contact_info.append(f"📧 {cand.email}")
            if cand.linkedin_url:
                contact_info.append(f"🔗 LinkedIn")
            if cand.github_url:
                contact_info.append(f"💻 GitHub")
            
            if contact_info:
                st.caption(" │ ".join(contact_info))
            
            # 左右布局：左侧主要经历，右侧 AI 画像
            main_col, side_col = st.columns([3, 2])
            
            with main_col:

                # --- 工作经历 ---
                work_header_col, work_edit_col = st.columns([5, 1])
                with work_header_col:
                    st.subheader("💼 工作经历")
                with work_edit_col:
                    edit_work_mode = st.toggle("✏️", key="edit_work_toggle", help="编辑工作经历")
                
                if cand.work_experiences and isinstance(cand.work_experiences, list):
                    if edit_work_mode:
                        # 编辑模式
                        st.info("📝 编辑模式：修改公司、职位、时间、具体内容")
                        updated_work = []
                        for i, work in enumerate(cand.work_experiences):
                            with st.container(border=True):
                                st.markdown(f"**工作经历 #{i+1}**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    new_company = st.text_input(
                                        "公司", 
                                        value=work.get('company', ''), 
                                        key=f"edit_work_company_{i}"
                                    )
                                with col2:
                                    new_title = st.text_input(
                                        "职位", 
                                        value=work.get('title', ''), 
                                        key=f"edit_work_title_{i}"
                                    )
                                
                                new_time = st.text_input(
                                    "时间", 
                                    value=work.get('time', ''), 
                                    key=f"edit_work_time_{i}"
                                )
                                
                                new_desc = st.text_area(
                                    "具体内容", 
                                    value=work.get('description', ''), 
                                    key=f"edit_work_desc_{i}",
                                    height=80
                                )
                                
                                updated_work.append({
                                    'company': new_company,
                                    'title': new_title,
                                    'time': new_time,
                                    'description': new_desc
                                })
                        
                        if st.button("💾 保存工作经历", type="primary"):
                            cand.work_experiences = updated_work
                            # 更新当前公司为第一份工作
                            if updated_work:
                                cand.current_company = updated_work[0]['company']
                                cand.current_title = updated_work[0]['title']
                            db.commit()
                            st.success("✅ 工作经历已保存！")
                            st.rerun()
                    else:
                        # 展示模式
                        for work in cand.work_experiences:
                            with st.container():
                                # 兼容Boss和脉脉两种数据格式
                                # Boss: title=公司, subtitle=职位, content=描述
                                # 脉脉: company=公司, title=职位, description=描述
                                company = work.get('company') or work.get('title', 'Unknown')
                                title = work.get('subtitle') or work.get('position') or work.get('title', '')
                                # 如果company和title相同，说明是Boss格式，title实际是公司名
                                if company == title:
                                    title = work.get('subtitle', work.get('role', ''))
                                
                                # 优化显示
                                if title and title != company:
                                    header = f"**{company}** | {title}"
                                else:
                                    header = f"**{company}**"
                                    
                                st.markdown(header)
                                st.caption(f"📅 {work.get('time', work.get('time_range', 'N/A'))}")
                                
                                # 清洗描述文本，兼容content和description
                                desc = work.get('description') or work.get('content', '')
                                desc = re.sub(r'^(内容|工作内容|职责|工作职责|项目描述)[:：]\s*', '', desc, flags=re.IGNORECASE).strip()
                                # 优化换行显示
                                desc = desc.replace("\n", "  \n") 
                                
                                st.markdown(desc)
                                st.markdown("---")
                else:
                    st.info("暂无详细工作经历")
                
                # --- 项目经历 ---
                st.subheader("🚀 项目经历")
                if cand.project_experiences and isinstance(cand.project_experiences, list):
                    for proj in cand.project_experiences:
                        with st.container():
                            name = proj.get('name', 'Unknown Project')
                            role = proj.get('role', 'Unknown')
                            if role == name: 
                                header = f"**{name}**"
                            else:
                                header = f"**{name}** | {role}"
                                
                            st.markdown(header)
                            st.caption(f"📅 {proj.get('time', 'N/A')}")
                            
                            desc = proj.get('description', '')
                            desc = re.sub(r'^(内容|项目内容|描述|项目描述)[:：]\s*', '', desc, flags=re.IGNORECASE).strip()
                            desc = desc.replace("\n", "  \n")
                            
                            st.markdown(desc)
                            st.markdown("---")
                else:
                    st.info("暂无详细项目经历")

                # --- 教育经历 ---
                edu_header_col, edu_edit_col = st.columns([5, 1])
                with edu_header_col:
                    st.subheader("🎓 教育经历")
                with edu_edit_col:
                    edit_edu_mode = st.toggle("✏️", key="edit_edu_toggle", help="编辑教育经历")
                
                if cand.education_details and isinstance(cand.education_details, list):
                    if edit_edu_mode:
                        # 编辑模式
                        st.info("📝 编辑模式：修改学校、专业、时间")
                        updated_edu = []
                        for i, edu in enumerate(cand.education_details):
                            with st.container(border=True):
                                st.markdown(f"**教育经历 #{i+1}**")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    new_school = st.text_input("学校", value=edu.get('school', ''), key=f"edit_edu_school_{i}")
                                with col2:
                                    new_major = st.text_input("专业", value=edu.get('major', ''), key=f"edit_edu_major_{i}")
                                with col3:
                                    new_time = st.text_input("时间", value=edu.get('time', ''), key=f"edit_edu_time_{i}")
                                
                                updated_edu.append({
                                    'school': new_school,
                                    'major': new_major,
                                    'time': new_time,
                                    'degree': edu.get('degree', '')
                                })
                        
                        if st.button("💾 保存教育经历", type="primary", key="save_edu"):
                            cand.education_details = updated_edu
                            db.commit()
                            st.success("✅ 教育经历已保存！")
                            st.rerun()
                    else:
                        # 展示模式
                        for edu in cand.education_details:
                            school = edu.get('school', 'Unknown School')
                            major = edu.get('major', 'N/A')
                            # 兼容time, time_range, year字段
                            time_range = edu.get('time_range') or edu.get('time', '') or edu.get('year', '')
                            degree = edu.get('degree', '')
                            
                            # 构建显示文本
                            display_text = f"- **{school}** | {major}"
                            if degree:
                                display_text += f" | {degree}"
                            if time_range and time_range != 'nan':
                                display_text += f" ({time_range})"
                            
                            st.markdown(display_text)
                else:
                    st.info("暂无详细教育经历")

                # --- 原始简历 ---
                with st.expander("📄 查看原始简历全文"):
                    # 构建完整简历文本
                    full_resume = cand.raw_resume_text or ""
                    
                    # 添加工作经历
                    if cand.work_experiences and isinstance(cand.work_experiences, list):
                        full_resume += "\n\n====== 工作经历 ======\n"
                        for work in cand.work_experiences:
                            company = work.get('company') or work.get('title', '')
                            title = work.get('subtitle') or work.get('position') or work.get('title', '')
                            if company == title:
                                title = work.get('subtitle', work.get('role', ''))
                            time = work.get('time', work.get('time_range', ''))
                            desc = work.get('description') or work.get('content', '')
                            full_resume += f"\n【{company}】{title} ({time})\n{desc}\n"
                    
                    # 添加教育经历
                    if cand.education_details and isinstance(cand.education_details, list):
                        full_resume += "\n\n====== 教育经历 ======\n"
                        for edu in cand.education_details:
                            school = edu.get('school', '')
                            major = edu.get('major', '')
                            time_range = edu.get('time_range') or edu.get('time', '')
                            degree = edu.get('degree', '')
                            full_resume += f"\n【{school}】{major} {degree} ({time_range})\n"
                    
                    st.text_area("原始内容", full_resume, height=400, label_visibility="collapsed")
                
                # --- 原始 JSON ---
                with st.expander("🔍 查看 JSON 数据"):
                    st.json(cand.to_dict())

            with side_col:
                # --- AI 画像 ---
                st.markdown("### 🤖 AI 画像")
                
                st.write("**核心评价**:")
                
                # Editable AI Analysis
                current_ai_text = cand.ai_summary or ""
                new_ai_text = st.text_area("AI 评价 (可编辑)", value=current_ai_text, height=300, key="cand_ai_edit")
                
                if new_ai_text != current_ai_text:
                    cand.ai_summary = new_ai_text
                    db.commit()
                    st.toast("AI 评价已更新")
                
                # --- 备注 ---
                with st.expander("📝 备注", expanded=bool(cand.notes)):
                    new_notes = st.text_area(
                        "备注", 
                        value=cand.notes or "", 
                        key="cand_notes_input", 
                        height=120,
                        placeholder="输入备注信息...",
                        label_visibility="collapsed"
                    )
                    if new_notes != (cand.notes or ""):
                        cand.notes = new_notes
                        db.commit()
                        st.toast("备注已保存")
                
                # --- 沟通记录 ---
                with st.expander("💬 沟通记录", expanded=False):
                    # 添加新记录
                    new_log_content = st.text_area(
                        "新沟通记录", 
                        key="new_comm_log", 
                        placeholder="输入沟通内容...",
                        height=100,
                        label_visibility="collapsed"
                    )
                    if st.button("➕ 添加记录", key="add_comm_log", type="primary"):
                        if new_log_content:
                            from datetime import datetime
                            from sqlalchemy.orm.attributes import flag_modified
                            logs = list(cand.communication_logs) if cand.communication_logs else []
                            new_entry = {
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "content": new_log_content
                            }
                            logs.insert(0, new_entry)
                            cand.communication_logs = logs
                            flag_modified(cand, "communication_logs")
                            db.commit()
                            st.toast("✅ 沟通记录已添加")
                            st.rerun()
                    
                    st.divider()
                    
                    # 显示历史记录
                    logs = cand.communication_logs or []
                    if logs:
                        for i, log in enumerate(logs):
                            with st.container(border=True):
                                # 检查是否在编辑模式
                                edit_key = f"edit_log_{cand.id}_{i}"
                                is_editing = st.session_state.get(edit_key, False)
                                
                                time_col, edit_col, del_col = st.columns([4, 0.5, 0.5])
                                with time_col:
                                    st.caption(f"🕐 {log.get('time', '')}")
                                with edit_col:
                                    if st.button("✏️", key=f"edit_btn_{cand.id}_{i}", help="编辑"):
                                        st.session_state[edit_key] = not is_editing
                                        st.rerun()
                                with del_col:
                                    if st.button("🗑️", key=f"del_log_{cand.id}_{i}", help="删除"):
                                        from sqlalchemy.orm.attributes import flag_modified
                                        new_logs = [l for j, l in enumerate(logs) if j != i]
                                        cand.communication_logs = new_logs
                                        flag_modified(cand, "communication_logs")
                                        db.commit()
                                        st.rerun()
                                
                                if is_editing:
                                    # 编辑模式
                                    edited_content = st.text_area(
                                        "编辑内容",
                                        value=log.get('content', ''),
                                        key=f"edit_content_{cand.id}_{i}",
                                        height=100,
                                        label_visibility="collapsed"
                                    )
                                    if st.button("💾 保存修改", key=f"save_edit_{cand.id}_{i}"):
                                        from sqlalchemy.orm.attributes import flag_modified
                                        new_logs = list(logs)
                                        new_logs[i] = {**log, "content": edited_content}
                                        cand.communication_logs = new_logs
                                        flag_modified(cand, "communication_logs")
                                        db.commit()
                                        st.session_state[edit_key] = False
                                        st.toast("✅ 已保存")
                                        st.rerun()
                                else:
                                    # 显示模式
                                    st.markdown(log.get('content', ''))
                    else:
                        st.caption("暂无沟通记录")
        else:
            st.error("未找到该候选人")
            if st.button("返回列表"):
                back_to_list()

    else:
        # --- 列表视图 ---
        st.title("👥 人才库管理")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["人才列表", "导入导出", "好友标记", "批量画像", "搜索人才"])
        
        with tab1:
            # --- Search Filters ---
            with st.expander("🔍 筛选条件", expanded=True):
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    filter_name = st.text_input("姓名/关键词", value=st.session_state.get('filter_name', ''), key="filter_name_input")
                    st.session_state.filter_name = filter_name
                with col2:
                    filter_company = st.text_input("公司", value=st.session_state.get('filter_company', ''), key="filter_company_input")
                    st.session_state.filter_company = filter_company
                with col3:
                    filter_school = st.text_input("名校/学历", value=st.session_state.get('filter_school', ''), key="filter_school_input")
                    st.session_state.filter_school = filter_school
                with col4:
                    filter_location = st.text_input("期望地点", value=st.session_state.get('filter_location', ''), key="filter_location_input")
                    st.session_state.filter_location = filter_location
                with col5:
                    # Age range, handling min/max
                    saved_age = st.session_state.get('filter_age', (20, 45))
                    age_min, age_max = st.slider("年龄区间", 18, 60, saved_age, key="filter_age_input")
                    st.session_state.filter_age = (age_min, age_max)
                
                # 第二行筛选条件
                col6, col7, col8 = st.columns([1, 2, 2])
                with col6:
                    friend_options = ["全部", "✅ 仅好友", "❌ 非好友"]
                    saved_friend_idx = friend_options.index(st.session_state.get('filter_friend', '全部')) if st.session_state.get('filter_friend') in friend_options else 0
                    filter_friend = st.selectbox("好友状态", friend_options, index=saved_friend_idx, key="filter_friend_input")
                    st.session_state.filter_friend = filter_friend
                with col7:
                    filter_tags = st.text_input("技能标签 (多个用逗号分隔)", value=st.session_state.get('filter_tags', ''), placeholder="Python, 机器学习, LLM", key="filter_tags_input")
                    st.session_state.filter_tags = filter_tags
                with col8:
                    if st.button("🔄 清空筛选"):
                        st.session_state.filter_name = ''
                        st.session_state.filter_company = ''
                        st.session_state.filter_school = ''
                        st.session_state.filter_location = ''
                        st.session_state.filter_age = (20, 45)
                        st.session_state.filter_friend = '全部'
                        st.session_state.filter_tags = ''
                        st.rerun()
            
            # --- Query Data ---
            query = db.query(Candidate).filter(Candidate.name != "Parse Error")
            
            if filter_name:
                query = query.filter(Candidate.name.contains(filter_name) | Candidate.skills.contains(filter_name))
            
            if filter_company:
                # Search in current company OR historical work experiences (JSON)
                query = query.filter(Candidate.current_company.contains(filter_company) | Candidate.work_experiences.cast(String).contains(filter_company))
            
            if filter_location:
                # 模糊匹配 expect_location 或者 raw text
                query = query.filter(Candidate.expect_location.contains(filter_location) | Candidate.raw_resume_text.contains(filter_location))
            
            # 好友筛选
            if filter_friend == "✅ 仅好友":
                query = query.filter(Candidate.is_friend == 1)
            elif filter_friend == "❌ 非好友":
                from sqlalchemy import or_
                query = query.filter(or_(Candidate.is_friend == 0, Candidate.is_friend == None))
            
            # 标签筛选
            if filter_tags:
                tags = [t.strip() for t in filter_tags.split(",") if t.strip()]
                for tag in tags:
                    query = query.filter(Candidate.skills.contains(tag) | Candidate.raw_resume_text.contains(tag))
            
            # Age Filtering (Logic: if age is 0 or null, we might include or exclude. Here we filter strict range if age > 0)
            # 仅对已解析出年龄的做筛选，未解析出的暂且保留或放后面? 
            # 这里简单处理：如果筛选了，只显示符合条件的。
            # query = query.filter(Candidate.age >= age_min, Candidate.age <= age_max) 
            # 考虑到很多数据 age 可能是 0，这样会把它们都过滤掉。
            # 优化：仅当 age > 0 时生效，或者用户意图是强制筛选。
            # 修复：允许 age 为 None 的候选人通过筛选
            if age_min > 18 or age_max < 60:
                from sqlalchemy import or_
                query = query.filter(or_(
                    Candidate.age == None,  # 允许无年龄数据的候选人
                    (Candidate.age >= age_min) & (Candidate.age <= age_max)
                ))

            # School Filtering (In-memory mostly for JSON list)
            # SQL LIKE on JSON text is a bit hacky but works for simple cases in SQLite
            if filter_school:
                query = query.filter(Candidate.education_details.contains(filter_school) | Candidate.raw_resume_text.contains(filter_school))

            # Sorting
            c_sort1, c_sort2 = st.columns([5, 1])
            with c_sort2:
                sort_option = st.selectbox("排序方式", ["最新导入", "姓名 A-Z", "姓名 Z-A"], label_visibility="collapsed")
            
            if sort_option == "姓名 A-Z":
                query = query.order_by(Candidate.name.asc())
            elif sort_option == "姓名 Z-A":
                query = query.order_by(Candidate.name.desc())
            else:
                query = query.order_by(Candidate.created_at.desc())

            candidates = query.all()
            
            # --- 分页设置 ---
            total_count = len(candidates)
            
            # 分页控制行
            pag_col1, pag_col2, pag_col3, pag_col4 = st.columns([2, 1, 1, 1])
            
            with pag_col1:
                st.markdown(f"共 **{total_count}** 人")
            
            with pag_col2:
                page_size = st.selectbox("每页显示", [20, 50], key="page_size", label_visibility="collapsed")
            
            # 计算总页数
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
            
            # 初始化当前页
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            
            # 确保页码有效
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = total_pages
            if st.session_state.current_page < 1:
                st.session_state.current_page = 1
            
            with pag_col3:
                # 上一页/下一页按钮
                prev_btn, next_btn = st.columns(2)
                with prev_btn:
                    if st.button("◀", disabled=st.session_state.current_page <= 1, use_container_width=True):
                        st.session_state.current_page -= 1
                        st.rerun()
                with next_btn:
                    if st.button("▶", disabled=st.session_state.current_page >= total_pages, use_container_width=True):
                        st.session_state.current_page += 1
                        st.rerun()
            
            with pag_col4:
                st.markdown(f"**{st.session_state.current_page}** / {total_pages} 页")
            
            # 分页切片
            start_idx = (st.session_state.current_page - 1) * page_size
            end_idx = start_idx + page_size
            candidates_page = candidates[start_idx:end_idx]
            
            st.divider()

            # --- 卡片式列表 (参考脉脉UI) ---
            if candidates_page:
                for cand in candidates_page:
                    with st.container(border=True):
                        # 顶部：姓名 + 活跃状态 + 操作按钮
                        top_left, top_right = st.columns([3, 1])
                        
                        with top_left:
                            # 解析活跃状态（从 notes 字段）
                            activity_badge = ""
                            if cand.notes:
                                notes_str = str(cand.notes)
                                if "P0" in notes_str or "今日" in notes_str:
                                    activity_badge = "🟢 活跃"
                                elif "P1" in notes_str or "本周" in notes_str:
                                    activity_badge = "🔵 近期活跃"
                                elif "P2" in notes_str:
                                    activity_badge = "⚪ 一般"
                            
                            # 好友标记
                            friend_badge = "✅好友" if cand.is_friend else ""
                            
                            st.markdown(f"### {cand.name} {activity_badge} {friend_badge}")
                        
                        with top_right:
                            btn1, btn2 = st.columns(2)
                            if btn1.button("📄 详情", key=f"view_{cand.id}", use_container_width=True):
                                st.session_state.selected_candidate_id = cand.id
                                st.session_state.view_mode = 'detail'
                                st.rerun()
                            if btn2.button("🗑️", key=f"del_{cand.id}", help="删除"):
                                delete_candidate(cand.id)
                                st.rerun()
                        
                        # 主体：左侧基础信息 + 中间时间线 + 右侧快速记录
                        left_col, mid_col, right_col = st.columns([1.2, 2, 1.2])
                        
                        with left_col:
                            # 基础信息
                            age_str = f"{cand.age}岁" if cand.age else "-"
                            exp_str = f"{cand.experience_years}年" if cand.experience_years else "-"
                            edu_str = cand.education_level or "未知"
                            
                            st.markdown(f"**{age_str}** · **{exp_str}** · **{edu_str}**")
                            
                            # 当前公司/职位
                            if cand.current_company:
                                st.write(f"🏢 {cand.current_company}")
                            if cand.current_title:
                                st.caption(f"{cand.current_title[:40]}")
                            
                            # 期望地点
                            if cand.expect_location:
                                st.write(f"📍 期望: {cand.expect_location}")
                            
                            # 技能标签
                            if cand.skills and isinstance(cand.skills, list):
                                tags = " ".join([f"`{s}`" for s in cand.skills[:5]])
                                st.markdown(f"🏷️ {tags}")
                            
                            # 评分信息（从 notes 解析）
                            if cand.notes:
                                import re
                                score_match = re.search(r'总分:(\d+)', str(cand.notes))
                                if score_match:
                                    st.metric("评分", score_match.group(1), label_visibility="collapsed")
                            
                            # 简历来源
                            if cand.source_file:
                                st.caption(f"📄 来源: {cand.source_file}")
                        
                        with mid_col:
                            # 工作经历时间线
                            st.markdown("**💼 工作经历**")
                            if cand.work_experiences and isinstance(cand.work_experiences, list):
                                for i, w in enumerate(cand.work_experiences[:3]):
                                    time_str = w.get('time', '') or ''
                                    company = w.get('company', '') or ''
                                    title = w.get('title', '') or ''
                                    
                                    if company or title:
                                        st.markdown(f"📅 `{time_str}` **{company}** · {title[:30]}")
                            else:
                                st.caption("暂无工作经历")
                            
                            st.markdown("")  # 间距
                            
                            # 教育经历时间线
                            st.markdown("**🎓 教育经历**")
                            if cand.education_details and isinstance(cand.education_details, list):
                                for e in cand.education_details[:2]:
                                    time_str = e.get('time', '') or e.get('year', '') or ''
                                    school = (e.get('school', '') or '').strip()
                                    # 清理学校名前的特殊字符
                                    if school and school[0] in '·、-':
                                        school = school[1:].strip()
                                    major = e.get('major', '') or ''
                                    
                                    if school:
                                        display = f"🏫 **{school}**"
                                        if time_str:
                                            display += f" ({time_str})"
                                        if major:
                                            display += f" · {major}"
                                        st.markdown(display)
                            else:
                                st.caption("暂无教育经历")
                        
                        with right_col:
                            # 快速沟通记录
                            st.markdown("**💬 快速记录**")
                            quick_note = st.text_area(
                                "沟通记录",
                                key=f"quick_log_{cand.id}",
                                placeholder="输入沟通内容...",
                                height=100,
                                label_visibility="collapsed"
                            )
                            if st.button("💾 保存", key=f"save_quick_{cand.id}", type="primary", use_container_width=True):
                                if quick_note:
                                    from datetime import datetime
                                    from sqlalchemy.orm.attributes import flag_modified
                                    logs = list(cand.communication_logs) if cand.communication_logs else []
                                    logs.insert(0, {
                                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "content": quick_note
                                    })
                                    cand.communication_logs = logs
                                    flag_modified(cand, "communication_logs")
                                    db.commit()
                                    st.toast(f"✅ 已保存 {cand.name} 的沟通记录")
                                    st.rerun()
                        
                        st.markdown("")  # 卡片底部间距
            else:
                st.info("没有找到符合条件的候选人")

        with tab2:
            st.subheader("从 Excel/CSV 批量导入")
            uploaded_file = st.file_uploader("上传文件", type=["xlsx", "csv"])
            
            if uploaded_file and st.button("开始导入 (仅数据)"):
                status_text = st.empty()
                progress_bar = st.progress(0)
                
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.write(f"读取到 {len(df)} 条数据，开始导入数据库...")
                    
                    count = 0
                    for index, row in df.iterrows():
                        count += 1
                        status_text.text(f"正在处理第 {index + 1}/{len(df)} 条...")
                        
                        # 智能字段映射
                        row_dict = {str(k).strip().lower(): v for k, v in row.items()}
                        def get_val(keys, default=""):
                            for k in keys:
                                for row_k in row_dict:
                                    if k in row_k:
                                        val = row_dict[row_k]
                                        return str(val) if pd.notna(val) else default
                            return default

                        # 提取基础字段 (无 AI)
                        name = get_val(["name", "姓名", "candidate"], "Unknown")
                        if name == "Unknown": 
                            # 尝试从第一列获取，如果没找到名字列
                            first_val = row.iloc[0] if not row.empty else "Unknown"
                            if pd.notna(first_val): name = str(first_val)

                        # 简单校验
                        if not name or name.lower() == "nan":
                            continue

                        # 拼接全文
                        raw_text = " ".join([f"{k}: {v}" for k, v in row.items() if pd.notna(v)])
                        
                        # 提取关键字段
                        current_company = get_val(["company", "公司", "企业"], "Unknown")
                        current_title = get_val(["title", "职位", "岗位"], "Unknown")
                        education_level = get_val(["education", "degree", "学历"], "Unknown")

                        # 辅助解析函数: 尝试解析 JSON 格式的复杂字段
                        def try_parse_json(content):
                            if not content or not isinstance(content, str):
                                return None
                            content = content.strip()
                            # 简单判断是否像 JSON 列表
                            if not (content.startswith('[') and content.endswith(']')):
                                return None
                            try:
                                return json.loads(content)
                            except:
                                try:
                                    import ast
                                    # 处理单引号的 Python List 字符串
                                    return ast.literal_eval(content)
                                except:
                                    return None

                        # --- 工作经历 (智能解析) ---
                        work_exp_val = get_val(["work_experience", "工作经历", "经历"])
                        work_parsed = try_parse_json(work_exp_val)
                        work_experiences = []
                        if work_parsed and isinstance(work_parsed, list):
                            for item in work_parsed:
                                if isinstance(item, dict):
                                    # 映射字段
                                    work_experiences.append({
                                        "company": item.get("company") or item.get("company_name") or "Unknown",
                                        "title": item.get("title") or item.get("position") or "Unknown",
                                        "time": item.get("time") or item.get("time_range") or item.get("duration") or "",
                                        "description": item.get("content") or item.get("work_desc") or item.get("description") or ""
                                    })
                        elif work_exp_val:
                            # 兜底：纯文本
                            work_experiences = [{"description": work_exp_val, "company": current_company, "title": current_title, "time": "-"}]

                        # --- 项目经历 (智能解析) ---
                        proj_exp_val = get_val(["project_experience", "项目经历", "项目"])
                        proj_parsed = try_parse_json(proj_exp_val)
                        project_experiences = []
                        if proj_parsed and isinstance(proj_parsed, list):
                            for item in proj_parsed:
                                if isinstance(item, dict):
                                    project_experiences.append({
                                        "name": item.get("project_name") or item.get("name") or "Unknown",
                                        "role": item.get("role") or item.get("my_role") or "Unknown",
                                        "time": item.get("time") or item.get("time_range") or "",
                                        "description": item.get("content") or item.get("project_desc") or item.get("description") or ""
                                    })
                        elif proj_exp_val:
                            project_experiences = [{"description": proj_exp_val, "name": "Project", "role": current_title, "time": "-"}]

                        # --- 教育经历 (智能解析) ---
                        edu_val = get_val(["education_details", "教育经历", "教育"])
                        edu_parsed = try_parse_json(edu_val)
                        education_details = []
                        if edu_parsed and isinstance(edu_parsed, list):
                            for item in edu_parsed:
                                if isinstance(item, dict):
                                    education_details.append({
                                        "school": item.get("school") or item.get("school_name") or "Unknown",
                                        "major": item.get("major") or item.get("specialty") or "",
                                        "degree": item.get("degree") or item.get("education_level") or "",
                                        "year": item.get("time") or item.get("time_range") or item.get("year") or ""
                                    })
                        elif edu_val:
                            education_details = [{"major": edu_val, "school": "-", "degree": education_level, "year": "-"}]

                        new_cand = Candidate(
                            name=name,
                            email=get_val(["email", "邮箱", "mail"]),
                            phone=get_val(["phone", "电话", "手机", "mobile"]),
                            current_company=current_company,
                            current_title=current_title,
                            education_level=education_level,
                            experience_years=int(float(get_val(["experience", "work_years", "工龄", "经验"], "0"))),
                            age=int(float(get_val(["age", "年龄"], "0"))),
                            expect_location=get_val(["location", "city", "地点", "城市"]),
                            raw_resume_text=raw_text,
                            source_file=uploaded_file.name,
                            work_experiences=work_experiences,
                            project_experiences=project_experiences,
                            education_details=education_details
                        )
                        db.add(new_cand)
                    
                    db.commit()
                    progress_bar.progress(1.0)
                    st.success(f"导入完成！共 {count} 条数据已存入数据库 (待画像)。请前往“批量画像”标签页生成 AI 简历。")
                    
                except Exception as e:
                    st.error(f"导入失败: {str(e)}")

            st.divider()
            
            st.subheader("📤 导出数据")
            
            # Export Options
            export_mode = st.radio("导出范围", ["全量导出", "按公司导出"], horizontal=True)
            
            query_export = db.query(Candidate)
            
            if export_mode == "按公司导出":
                # Get unique companies
                companies = [r[0] for r in db.query(Candidate.current_company).distinct().all() if r[0]]
                selected_companies = st.multiselect("选择公司", companies)
                if selected_companies:
                    query_export = query_export.filter(Candidate.current_company.in_(selected_companies))
                else:
                    query_export = None # Don't export anything if no company selected
            
            if st.button("生成导出文件"):
                if query_export:
                    candidates_export = query_export.all()
                    if candidates_export:
                        # Prepare DataFrame
                        export_data = []
                        for c in candidates_export:
                            # Flatten JSON fields back to string
                            work_str = json.dumps(c.work_experiences, ensure_ascii=False) if c.work_experiences else ""
                            proj_str = json.dumps(c.project_experiences, ensure_ascii=False) if c.project_experiences else ""
                            edu_str = json.dumps(c.education_details, ensure_ascii=False) if c.education_details else ""
                            
                            export_data.append({
                                "姓名": c.name,
                                "邮箱": c.email,
                                "电话": c.phone,
                                "公司": c.current_company,
                                "职位": c.current_title,
                                "学历": c.education_level,
                                "工作年限": c.experience_years,
                                "年龄": c.age,
                                "期望地点": c.expect_location,
                                "工作经历": work_str,
                                "项目经历": proj_str,
                                "教育经历": edu_str,
                                "AI评价": c.ai_summary,
                                "技能标签": json.dumps(c.skills, ensure_ascii=False) if c.skills else ""
                            })
                        
                        df_export = pd.DataFrame(export_data)
                        
                        # Convert to Excel buffer
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_export.to_excel(writer, index=False)
                        
                        st.download_button(
                            label="📥 点击下载 Excel 文件",
                            data=buffer.getvalue(),
                            file_name=f"candidates_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success(f"已生成 {len(export_data)} 条数据的导出文件")
                    else:
                        st.warning("没有符合条件的数据")
                else:
                    st.warning("请至少选择一个公司")

        with tab3:
            # === 好友标记功能 ===
            st.subheader("🤝 批量标记好友")
            st.info("上传Excel文件，批量标记已添加为好友的候选人。")
            
            # 下载模板
            template_col, upload_col = st.columns([1, 2])
            with template_col:
                import pandas as pd
                template_df = pd.DataFrame({
                    "姓名": ["张三", "李四"],
                    "公司": ["快手", "阿里巴巴"],
                    "加好友时间": ["2024-12-25", "2024-12-26"],
                    "渠道": ["脉脉", "微信"]
                })
                csv_template = template_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 下载模板",
                    csv_template,
                    "好友标记模板.csv",
                    "text/csv",
                    key="download_friend_template"
                )
            
            with upload_col:
                uploaded_file = st.file_uploader("上传好友名单 (CSV/Excel)", type=["csv", "xlsx"], key="friend_upload")
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.write(f"📊 读取到 **{len(df)}** 条记录")
                    st.dataframe(df.head(5))
                    
                    if st.button("🚀 开始匹配并标记", type="primary"):
                        matched = 0
                        already_friend = 0
                        not_found = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for idx, row in df.iterrows():
                            name = str(row.get('姓名', '')).strip()
                            company = str(row.get('公司', '')).strip()
                            added_at = str(row.get('加好友时间', '')).strip()
                            channel = str(row.get('渠道', '')).strip()
                            
                            if not name:
                                continue
                            
                            # 在数据库中匹配
                            query = db.query(Candidate).filter(Candidate.name == name)
                            if company and company != 'nan':
                                query = query.filter(Candidate.current_company.contains(company))
                            
                            candidates = query.all()
                            
                            if candidates:
                                for cand in candidates:
                                    if not cand.is_friend:
                                        cand.is_friend = 1
                                        cand.friend_added_at = added_at if added_at != 'nan' else None
                                        cand.friend_channel = channel if channel != 'nan' else None
                                        matched += 1
                                    else:
                                        already_friend += 1
                            else:
                                not_found.append({"姓名": name, "公司": company})
                            
                            progress_bar.progress((idx + 1) / len(df))
                            status_text.text(f"处理中: {idx + 1}/{len(df)}")
                        
                        db.commit()
                        progress_bar.empty()
                        status_text.empty()
                        
                        # 显示结果
                        st.success(f"✅ 成功标记: **{matched}** 人")
                        if already_friend > 0:
                            st.info(f"⏭️ 已是好友: **{already_friend}** 人")
                        
                        if not_found:
                            st.warning(f"❌ 未匹配: **{len(not_found)}** 人")
                            not_found_df = pd.DataFrame(not_found)
                            csv_not_found = not_found_df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                "📥 下载未匹配名单",
                                csv_not_found,
                                "未匹配好友名单.csv",
                                "text/csv",
                                key="download_not_found"
                            )
                            with st.expander("查看未匹配名单"):
                                st.dataframe(not_found_df)
                
                except Exception as e:
                    st.error(f"处理失败: {e}")
            
            st.divider()
            
            # 显示当前好友统计
            friend_count = db.query(Candidate).filter(Candidate.is_friend == 1).count()
            total_count = db.query(Candidate).count()
            st.metric("已标记好友", f"{friend_count} / {total_count}")

        with tab4:
            st.subheader("批量生成简历画像")
            
            # Filter options
            c_filter, c_action = st.columns([2, 2])
            with c_filter:
                filter_option = st.radio("筛选范围", ["所有未画像候选人", "所有候选人"], horizontal=True)
            
            # User Prompt Selection
            user_prompts = db.query(SystemPrompt).filter_by(prompt_type='candidate', prompt_role='user', is_active=True).all()
            prompt_options = {p.prompt_name: p.content for p in user_prompts}
            selected_template = None
            if user_prompts:
                selected_prompt_name = st.selectbox("选择分析模版 (User Prompt)", options=list(prompt_options.keys()))
                selected_template = prompt_options[selected_prompt_name]
            
            # Name Filter
            name_search = st.text_input("🔍 按姓名搜索候选人", key="batch_name_search")
            
            query = db.query(Candidate)
            if filter_option == "所有未画像候选人":
                query = query.filter((Candidate.ai_summary == None) | (Candidate.ai_summary == ""))
            
            if name_search:
                query = query.filter(Candidate.name.contains(name_search))
            
            batch_candidates = query.order_by(Candidate.created_at.desc()).all()
            
            if batch_candidates:
                st.write(f"待处理候选人: {len(batch_candidates)} 位")
                
                with c_action:
                    st.write("") # Spacer
                    st.write("")
                    if st.button("🚀 生成/重制选中的画像", type="primary"):
                        # Collect selected IDs from session state
                        selected_ids = []
                        for cand in batch_candidates:
                            if st.session_state.get(f"batch_chk_{cand.id}", False):
                                selected_ids.append(cand.id)
                        
                        if selected_ids:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for idx, cand_id in enumerate(selected_ids):
                                cand = db.query(Candidate).get(int(cand_id))
                                if cand and cand.raw_resume_text:
                                    status_text.text(f"正在分析: {cand.name} ({idx+1}/{len(selected_ids)})")
                                    
                                    # Call AI with selected template
                                    parsed = AIService.parse_resume(cand.raw_resume_text, user_prompt_template=selected_template)
                                    if parsed.get("name") != "Parse Error":
                                        cand.name = parsed.get("name") or cand.name
                                        cand.email = parsed.get("email") or cand.email
                                        cand.phone = parsed.get("phone") or cand.phone
                                        
                                        # Robust Summary
                                        summary = parsed.get("summary")
                                        if not summary:
                                            if "evaluation" in parsed: summary = str(parsed.get("evaluation"))
                                            elif "analysis" in parsed: summary = str(parsed.get("analysis"))
                                            else: summary = "AI未提供评价"
                                        cand.ai_summary = summary
                                        
                                        cand.skills = parsed.get("skills")
                                        cand.experience_years = parsed.get("experience_years")
                                        cand.age = parsed.get("age")
                                        cand.expect_location = parsed.get("expect_location")
                                        cand.education_level = parsed.get("education_level")
                                        cand.education_details = parsed.get("education_details")
                                        cand.work_experiences = parsed.get("work_experiences")
                                        cand.project_experiences = parsed.get("project_experiences")
                                        cand.current_company = parsed.get("current_company") or cand.current_company
                                        cand.current_title = parsed.get("current_title") or cand.current_title
                                        
                                        AIService.add_candidate_to_vector_db(cand.id, cand.raw_resume_text, {"name": cand.name, "skills": cand.skills})
                                        db.commit()
                                        db.refresh(cand)
                                    else:
                                        st.error(f"解析失败 ({cand.name}): {parsed.get('summary')}")
                                
                                progress_bar.progress((idx + 1) / len(selected_ids))
                            
                            st.success("批量处理完成！")
                            st.rerun()
                        else:
                            st.warning("请先勾选候选人")

                st.divider()
                
                # Custom List Header
                h1, h2, h3, h4, h5, h6 = st.columns([0.5, 0.5, 1.5, 2, 1.5, 1])
                h1.markdown("✅")
                h2.markdown("**ID**")
                h3.markdown("**姓名**")
                h4.markdown("**公司**")
                h5.markdown("**AI状态**")
                h6.markdown("**操作**")
                
                for cand in batch_candidates:
                    c1, c2, c3, c4, c5, c6 = st.columns([0.5, 0.5, 1.5, 2, 1.5, 1])
                    with c1:
                        st.checkbox("Select", key=f"batch_chk_{cand.id}", label_visibility="collapsed")
                    with c2:
                        st.write(str(cand.id))
                    with c3:
                        st.write(cand.name)
                    with c4:
                        st.write(cand.current_company or "-")
                    with c5:
                        if cand.ai_summary:
                            st.success("已生成")
                        else:
                            st.caption("未生成")
                    with c6:
                        if cand.ai_summary:
                            if st.button("查看", key=f"btn_view_batch_{cand.id}"):
                                st.session_state.selected_candidate_id = cand.id
                                st.session_state.view_mode = 'detail'
                                st.rerun()
                    st.markdown("---")
            else:
                st.info("没有符合条件的候选人。")

        with tab5:
            st.subheader("AI 搜索人才")
            query = st.text_input("输入搜索关键词 (自然语言，如: '找一个懂Python和机器学习的资深工程师')")
            if query and st.button("AI 搜索"):
                results = AIService.search_candidates(query)
                
                if results and results['ids'][0]:
                    st.subheader("搜索结果")
                    for i, vector_id in enumerate(results['ids'][0]):
                        cand_id = int(vector_id.split('_')[1])
                        cand = db.query(Candidate).filter(Candidate.id == cand_id).first()
                        if cand:
                            with st.expander(f"{cand.name} - {cand.current_title} ({cand.current_company})"):
                                st.write(f"**AI 评价**: {cand.ai_summary}")
                                st.write(f"**匹配片段**: {results['documents'][0][i][:200]}...")
                                
                                # 搜索结果也可以点进去看详情
                                if st.button(f"查看详情", key=f"search_cand_{cand.id}"):
                                     st.session_state.selected_candidate_id = cand.id
                                     st.session_state.view_mode = 'detail'
                                     st.rerun()
                else:
                    st.warning("未找到相关候选人")

# ---------------- JOBS ----------------
elif page == "职位库管理":

    db = get_session()

    # 初始化 Job 相关的 Session State
    if 'selected_job_id' not in st.session_state:
        st.session_state.selected_job_id = None
    if 'job_view_mode' not in st.session_state:
        st.session_state.job_view_mode = 'list'

    if st.session_state.job_view_mode == 'detail' and st.session_state.selected_job_id:
        # --- 职位详情视图 ---
        job_id = st.session_state.selected_job_id
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if job:
            def back_to_job_list():
                st.session_state.job_view_mode = 'list'
                st.session_state.selected_job_id = None
                st.rerun()

            if st.button("← 返回职位列表"):
                back_to_job_list()
            
            # --- Header Section (Original Static Display) ---
            # 职位标题和紧急标签 - 更紧凑布局
            col_title, col_tags = st.columns([4, 1])
            with col_title:
                st.markdown(f"<h3 style='margin: 0;'>{job.title}</h3>", unsafe_allow_html=True)
            
            # Highlight Company and Tags
            tags = []
            # Simple logic to detect urgency
            if "急" in job.title or "Urgent" in job.title:
                tags.append("🔥 紧急")
            
            with col_tags:
                if tags:
                    for tag in tags:
                        st.markdown(f'<span style="background-color: #ff6b6b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{tag}</span>', unsafe_allow_html=True)
            
            # 公司信息展示 - 更紧凑
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{job.company}** · 📍 {job.location or '地点不限'} · ⏰ {job.required_experience_years or '经验不限'}")
            
            with col2:
                st.markdown(f"💰 {job.salary_range or '薪资面议'}")
            
            st.markdown("<br>", unsafe_allow_html=True)  # 最小间距
            
            # --- Restored & Enhanced Info Grid ---
            # Helper to extract extended fields
            def get_field(keys, default="-"):
                if not job.detail_fields: return default
                data = job.detail_fields if isinstance(job.detail_fields, dict) else {}
                if isinstance(job.detail_fields, str):
                    try: data = json.loads(job.detail_fields)
                    except: data = {}
                
                for k in keys:
                    for field_key in data:
                        if k in str(field_key):
                            return str(data[field_key]) if data[field_key] else default
                return default

            def update_detail_field(job_obj, keys, new_value):
                data = dict(job_obj.detail_fields) if job_obj.detail_fields else {}
                if isinstance(job.detail_fields, str):
                    try: data = json.loads(job.detail_fields)
                    except: data = {}
                
                found_key = None
                for k in keys:
                    for field_key in data:
                        if k in str(field_key):
                            found_key = field_key
                            break
                    if found_key: break
                
                target_key = found_key if found_key else keys[0]
                data[target_key] = new_value
                job_obj.detail_fields = data
                db.commit()

            # Extract Fields
            dept = get_field(["部门", "department"], "")
            edu = get_field(["学历", "education", "degree"], "不限")
            level = get_field(["层级", "level", "rank"], "")
            count = get_field(["人数", "count", "headcount"], "1")
            hr = get_field(["HR", "责任人", "recruiter"], "-")
            publish_date = get_field(["发布日期", "publish_date"], "-")
            
            # Custom Metric Helper
            def small_metric(col, label, value):
                col.markdown(f"""
                <div style="line-height: 1.2;">
                    <span style="color: #666; font-size: 13px;">{label}</span><br>
                    <span style="color: #222; font-size: 16px; font-weight: 600;">{value}</span>
                </div>
                """, unsafe_allow_html=True)

            # 扩展信息网格 - 更紧凑布局
            st.markdown("<br>", unsafe_allow_html=True)  # 最小间距
            
            # 合并成一行显示所有扩展信息
            info_text = f"🏢 {dept or '-'} | 📚 {edu} | 📊 {level or '-'} | 👥 {count or '-'} | 📅 {publish_date} | 👤 {hr}"
            st.markdown(f"<div style='background-color: #f8f9fa; padding: 8px; border-radius: 5px; font-size: 14px;'>{info_text}</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)  # 最小间距
            
            # Content Layout
            main_col, ai_col = st.columns([1, 1])
            
            with main_col:
                st.subheader("📋 职位详情")
                
                # 原职位链接（放在标题下方更明显）
                if job.detail_fields:
                    import json
                    details = job.detail_fields if isinstance(job.detail_fields, dict) else json.loads(job.detail_fields)
                    job_link = details.get('职位链接', '')
                    if job_link:
                        st.markdown(f"🔗 [点击查看原职位链接]({job_link})")
                
                # 职位详情编辑
                current_jd = job.raw_jd_text or ""
                new_jd = st.text_area("职位描述内容 (可编辑)", value=current_jd, height=350, key="edit_job_jd")
                if new_jd != current_jd:
                    job.raw_jd_text = new_jd
                    db.commit()
                    st.toast("职位描述已更新")
                
                st.divider()
                
                # --- Project Tags & Notes ---
                st.markdown("**🏷️ 项目标签**")
                # Simple text input for tags (comma separated) for MVP
                current_tags = ", ".join(job.project_tags) if job.project_tags else ""
                new_tags_str = st.text_input("输入标签 (逗号分隔)", value=current_tags, key="job_tags_input")
                if new_tags_str != current_tags:
                    job.project_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
                    db.commit()
                    st.toast("标签已保存")
                
                st.markdown("**📝 职位备注**")
                new_notes = st.text_area("输入备注信息", value=job.notes or "", key="job_notes_input", height=200)
                if new_notes != (job.notes or ""):
                    job.notes = new_notes
                    db.commit()
                    st.toast("备注已保存")

            with ai_col:
                # --- Update Controls ---
                user_job_prompts_s = db.query(SystemPrompt).filter_by(prompt_type='job', prompt_role='user', is_active=True).all()
                job_prompt_options_s = {p.prompt_name: p.content for p in user_job_prompts_s}
                selected_job_template_s = None
                
                if user_job_prompts_s:
                    selected_job_prompt_name_s = st.selectbox("选择分析模版", options=list(job_prompt_options_s.keys()), key="single_job_prompt_sel")
                    selected_job_template_s = job_prompt_options_s[selected_job_prompt_name_s]
                
                if st.button("🔄 更新画像", key="btn_update_job_single", type="primary"):
                    with st.spinner("正在更新 AI 画像..."):
                        parsed = AIService.parse_job(job.raw_jd_text, user_prompt_template=selected_job_template_s)
                        if parsed.get("title") != "Parse Error":
                            job.title = parsed.get("title") or job.title
                            job.company = parsed.get("company") or job.company
                            
                            # Robust AI Analysis Extraction
                            analysis_data = parsed.get("analysis")
                            if not analysis_data:
                                if any(k in parsed for k in ["must_have", "summary", "evaluation", "job_summary"]):
                                    analysis_data = parsed
                                else:
                                    analysis_data = parsed
                            job.ai_analysis = analysis_data
                            
                            job.salary_range = parsed.get("salary_range")
                            job.location = parsed.get("location")
                            job.required_experience_years = parsed.get("required_experience_years")
                            
                            AIService.add_job_to_vector_db(job.id, job.raw_jd_text, {"title": job.title, "company": job.company})
                            db.commit()
                            db.refresh(job)
                            st.success("画像已更新")
                            st.rerun()
                        else:
                            st.error("更新失败")

                st.subheader("🤖 AI 画像")
                # Editable AI Analysis
                current_ai_text = ""
                if job.ai_analysis:
                    if isinstance(job.ai_analysis, str):
                        current_ai_text = job.ai_analysis
                    elif isinstance(job.ai_analysis, dict):
                        # Convert dict to formatted string for editing
                        lines = []
                        
                        # Check for standard keys
                        std_keys = ["must_have", "nice_to_have", "soft_skills", "selling_points", "summary", "evaluation", "job_summary"]
                        has_std = any(k in job.ai_analysis for k in std_keys)
                        
                        if has_std:
                            if job.ai_analysis.get("summary"):
                                lines.append("**📋 职位总结**")
                                lines.append(job.ai_analysis.get("summary", ""))
                            if job.ai_analysis.get("evaluation"):
                                lines.append("\n**💼 职位评价**")
                                lines.append(job.ai_analysis.get("evaluation", ""))
                            if job.ai_analysis.get("must_have"):
                                lines.append("\n**🎯 核心硬性要求**")
                                lines.extend([f"- {i}" for i in job.ai_analysis.get("must_have", [])])
                            if job.ai_analysis.get("nice_to_have"):
                                lines.append("\n**✨ 加分项**")
                                lines.extend([f"- {i}" for i in job.ai_analysis.get("nice_to_have", [])])
                            if job.ai_analysis.get("soft_skills"):
                                lines.append("\n**💡 软技能**")
                                lines.append(", ".join(job.ai_analysis.get("soft_skills", [])))
                            if job.ai_analysis.get("selling_points"):
                                lines.append("\n**🔥 职位亮点**")
                                lines.append(", ".join(job.ai_analysis.get("selling_points", [])))
                        else:
                            # Fallback for custom prompts: Dump all keys
                            for k, v in job.ai_analysis.items():
                                if k in ["title", "company", "location", "salary_range", "required_experience_years"]: 
                                    continue  # Skip base fields
                                if isinstance(v, (list, dict)):
                                    lines.append(f"\n**{k}**")
                                    if isinstance(v, dict):
                                        lines.append(json.dumps(v, ensure_ascii=False, indent=2))
                                    else:
                                        lines.extend([f"- {item}" for item in v])
                                else:
                                    lines.append(f"**{k}**: {v}")
                        
                        current_ai_text = "\n".join(lines)
                    
                    # Debug: Show what we got
                    if not current_ai_text.strip():
                        st.info("AI 分析数据为空，请点击更新画像生成分析内容")
                        current_ai_text = ""
                else:
                    st.info("暂无 AI 分析内容，请点击更新画像生成")
                
                new_ai_text = st.text_area("AI 分析内容 (可编辑)", value=current_ai_text, height=600, key="job_ai_edit")
                
                if new_ai_text != current_ai_text:
                    # Save as string to preserve edits
                    job.ai_analysis = new_ai_text
                    db.commit()
                    st.toast("AI 画像已更新")


        else:
            st.error("未找到该职位")
            if st.button("返回"):
                back_to_job_list()

    else:
        # --- 职位列表视图 ---
        st.title("💼 职位库管理")
        
        tab1, tab2, tab3, tab4 = st.tabs(["职位列表", "发布职位(手动)", "导入导出职位", "批量画像"])
        
        with tab1:
            # --- Search Filters ---
            with st.expander("🔍 筛选条件", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    filter_job_code = st.text_input("职位ID", value=st.session_state.get('filter_job_code', ''), key="filter_job_code_input")
                    st.session_state.filter_job_code = filter_job_code
                with c2:
                    filter_title = st.text_input("职位名称/关键词", value=st.session_state.get('filter_title', ''), key="filter_title_input")
                    st.session_state.filter_title = filter_title
                with c3:
                    filter_company = st.text_input("公司", value=st.session_state.get('filter_job_company', ''), key="filter_job_company_input")
                    st.session_state.filter_job_company = filter_company
                with c4:
                    filter_dept = st.text_input("部门", value=st.session_state.get('filter_dept', ''), key="filter_dept_input")
                    st.session_state.filter_dept = filter_dept

                c5, c6, c7, c8 = st.columns(4)
                with c5:
                    filter_location = st.text_input("地点", value=st.session_state.get('filter_job_location', ''), key="filter_job_location_input")
                    st.session_state.filter_job_location = filter_location
                with c6:
                    filter_level = st.text_input("职级", value=st.session_state.get('filter_job_level', ''), key="filter_job_level_input")
                    st.session_state.filter_job_level = filter_level
                with c7:
                    filter_tags = st.text_input("标签", value=st.session_state.get('filter_job_tags', ''), key="filter_job_tags_input")
                    st.session_state.filter_job_tags = filter_tags
                with c8:
                    filter_urgent = st.checkbox("只看紧急职位", value=st.session_state.get('filter_job_urgent', False), key="filter_job_urgent_input")
                    st.session_state.filter_job_urgent = filter_urgent

                # 清空筛选按钮
                if st.button("🔄 清空筛选", key="clear_job_filters"):
                    st.session_state.filter_job_code = ''
                    st.session_state.filter_title = ''
                    st.session_state.filter_job_company = ''
                    st.session_state.filter_dept = ''
                    st.session_state.filter_job_location = ''
                    st.session_state.filter_job_level = ''
                    st.session_state.filter_job_tags = ''
                    st.session_state.filter_job_urgent = False
                    st.rerun()
            
            query = db.query(Job).filter(Job.is_active == 1)
            
            if filter_job_code:
                query = query.filter(Job.job_code.contains(filter_job_code))
            if filter_title:
                query = query.filter(Job.title.contains(filter_title))
            if filter_company:
                query = query.filter(Job.company.contains(filter_company))
            if filter_location:
                query = query.filter(Job.location.contains(filter_location))
            if filter_urgent:
                query = query.filter(Job.title.contains("急") | Job.title.contains("Urgent"))
                
            jobs = query.order_by(Job.created_at.desc()).all()
            
            # Python-side filtering for JSON fields
            if filter_dept:
                jobs = [j for j in jobs if j.detail_fields and filter_dept in str(j.detail_fields)]
            if filter_level:
                jobs = [j for j in jobs if j.detail_fields and filter_level in str(j.detail_fields)]
            
            # Filter by project tags (AND logic)
            if filter_tags.strip():
                # Split tags by comma and create list
                tag_list = [tag.strip() for tag in filter_tags.split(",") if tag.strip()]
                if tag_list:
                    # AND logic: must match all input tags
                    def matches_all_tags(job_tags):
                        if not job_tags:
                            return False
                        job_tags_str = [str(tag).lower() for tag in job_tags]
                        return all(any(tag_filter.lower() in job_tag 
                                      for job_tag in job_tags_str) 
                                  for tag_filter in tag_list)
                    
                    jobs = [j for j in jobs if j.project_tags and matches_all_tags(j.project_tags)]
            
            st.markdown(f"共 **{len(jobs)}** 个职位")
            
            # Pagination
            list_container = st.container()
            pagination_container = st.container()
            
            with pagination_container:
                st.divider()
                cp1, cp2, cp3 = st.columns([4, 2, 2])
                with cp2:
                    page_size = st.selectbox("每页显示", [20, 50, 100], key="job_page_size", label_visibility="collapsed")
                with cp3:
                    total_pages = max(1, (len(jobs) - 1) // page_size + 1)
                    page_num = st.number_input(f"页码 (共{total_pages}页)", min_value=1, max_value=total_pages, value=1, key="job_page_num")
            
            # Slicing
            start_idx = (page_num - 1) * page_size
            end_idx = start_idx + page_size
            page_jobs = jobs[start_idx:end_idx]
            
            with list_container:
                # Header
                # ID, Title, Comp, Dept, Level, Tags, Loc, PubDate, UpdDate, Action
                h0, h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([1, 2, 1.5, 1, 0.8, 1, 1, 1, 1, 1])
                h0.markdown("**职位ID**")
                h1.markdown("**职位名称**")
                h2.markdown("**公司**")
                h3.markdown("**部门**")
                h4.markdown("**职级**")
                h5.markdown("**标签**")
                h6.markdown("**地点**")
                h7.markdown("**发布日期**")
                h8.markdown("**更新日期**")
                h9.markdown("**操作**")
                st.divider()
                
                if page_jobs:
                    for job in page_jobs:
                        c0, c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([1, 2, 1.5, 1, 0.8, 1, 1, 1, 1, 1])
                        
                        # Extract Fields from JSON
                        dept = "-"
                        level = "-"
                        pub_date = "-"
                        upd_date = "-"
                        
                        if job.detail_fields:
                            try:
                                if isinstance(job.detail_fields, str):
                                    d = json.loads(job.detail_fields)
                                else:
                                    d = job.detail_fields
                                # Fuzzy key match
                                for k in d:
                                    k_str = str(k).lower()
                                    if "部门" in k_str or "department" in k_str: dept = str(d[k])
                                    if "层级" in k_str or "level" in k_str or "rank" in k_str or "p级" in k_str: level = str(d[k])
                                    if "发布" in k_str or "publish" in k_str: pub_date = str(d[k])
                                    if "更新" in k_str or "update" in k_str: upd_date = str(d[k])
                            except:
                                pass

                        with c0: st.write(job.job_code or "-")

                        with c1:
                            title_md = f"**{job.title}**"
                            if "急" in job.title or "Urgent" in job.title:
                                title_md += " 🔥"
                            st.markdown(title_md)
                        
                        with c2: st.write(job.company)
                        with c3: st.write(dept)
                        with c4: st.write(level)
                        
                        # 显示项目标签
                        with c5: 
                            if job.project_tags:
                                tags_text = ", ".join(job.project_tags) if isinstance(job.project_tags, list) else str(job.project_tags)
                                st.write(tags_text)
                            else:
                                st.write("-")
                        
                        with c6: st.write(job.location or "-")
                        with c7: st.write(format_date(pub_date))
                        with c8: st.write(format_date(upd_date))
                            
                        with c9:
                            cb1, cb2 = st.columns(2)
                            if cb1.button("📄", key=f"view_job_{job.id}", help="查看详情"):
                                st.session_state.selected_job_id = job.id
                                st.session_state.job_view_mode = 'detail'
                                st.rerun()
                            
                            if cb2.button("🗑️", key=f"del_job_{job.id}", help="删除"):
                                delete_job(job.id)
                                st.rerun()
                        
                        st.markdown("---")
                else:
                    st.info("暂无职位数据")

        with tab2:
            st.subheader("录入新职位")
            # 简单的手动录入 + AI 辅助完善
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("职位名称")
                company = st.text_input("公司名称")
            
            jd_text = st.text_area("职位描述 (JD)", height=300, placeholder="请粘贴完整的 JD 内容...")
            
            # User Prompt Selection for Job
            user_job_prompts = db.query(SystemPrompt).filter_by(prompt_type='job', prompt_role='user', is_active=True).all()
            job_prompt_options = {p.prompt_name: p.content for p in user_job_prompts}
            selected_job_template = None
            if user_job_prompts:
                selected_job_prompt_name = st.selectbox("选择分析模版 (User Prompt)", options=list(job_prompt_options.keys()))
                selected_job_template = job_prompt_options[selected_job_prompt_name]

            if st.button("生成画像并保存"):
                if not title or not jd_text:
                    st.error("请填写职位名称和 JD 内容")
                else:
                    with st.spinner("AI 正在分析 JD..."):
                        # 1. AI 解析
                        parsed_job = AIService.parse_job(jd_text, user_prompt_template=selected_job_template)
                        
                        # 2. 存入 DB
                        new_job = Job(
                            title=title,
                            company=company,
                            raw_jd_text=jd_text,
                            ai_analysis=parsed_job.get("analysis"),
                            salary_range=parsed_job.get("salary_range"),
                            location=parsed_job.get("location"),
                            required_experience_years=parsed_job.get("required_experience_years")
                        )
                        db.add(new_job)
                        db.commit()
                        db.refresh(new_job)
                        
                        # 3. 存入 Vector DB
                        vector_id = AIService.add_job_to_vector_db(
                            new_job.id,
                            jd_text,
                            {"title": title, "company": company}
                        )
                        new_job.vector_id = vector_id
                        db.commit()
                        
                        st.success("职位发布成功！AI 画像已生成。")
                        # 刷新列表
                        st.rerun()

        with tab3:
            st.subheader("从 Excel/CSV 批量导入职位")
            uploaded_file = st.file_uploader("上传职位文件", type=["xlsx", "csv"])
            
            if uploaded_file and st.button("开始导入职位"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.write(f"读取到 {len(df)} 条职位数据...")
                    
                    count = 0
                    for index, row in df.iterrows():
                        status_text.text(f"正在处理第 {index + 1}/{len(df)} 条...")
                        
                        # 智能字段映射
                        row_dict = {str(k).strip().lower(): v for k, v in row.items()}
                        
                        def get_val(keys, default=""):
                            for k in keys:
                                for row_k in row_dict:
                                    if k in row_k:
                                        val = row_dict[row_k]
                                        return str(val) if pd.notna(val) else default
                            return default

                        # 1. 提取关键字段 (优先匹配用户指定的 Excel 表头)
                        job_code_val = get_val(["职位ID", "job_code", "id", "编码", "编号"])
                        title = get_val(["职位名称", "职位", "岗位", "title"], "Unknown Title")
                        company = get_val(["公司名称", "公司", "company"], "Unknown Company")
                        location = get_val(["工作地点", "地点", "location", "city"])
                        salary = get_val(["薪资范围", "薪资", "salary", "pay"])
                        experience = get_val(["工作年限", "经验", "experience"])
                        
                        # 2. 数据校验
                        if title == "Unknown Title" and company == "Unknown Company":
                            # 跳过无效行
                            continue

                        # 3. 构建高质量 JD 文本 (合并描述与要求)
                        desc = get_val(["岗位描述", "职位描述", "description"])
                        req = get_val(["岗位要求", "任职要求", "requirement"])
                        
                        jd_parts = []
                        if desc: jd_parts.append(f"【岗位描述】:\n{desc}")
                        if req: jd_parts.append(f"【岗位要求】:\n{req}")
                        
                        # 如果没有专门的描述列，则使用全行拼接
                        if jd_parts:
                            raw_text = "\n\n".join(jd_parts)
                        else:
                            raw_text = " ".join([f"{k}: {v}" for k, v in row.items() if pd.notna(v)])
                        
                        # 4. 提取年限数字
                        req_exp = 0
                        if experience:
                            import re
                            match = re.search(r'(\d+)', str(experience))
                            if match:
                                req_exp = int(match.group(1))
                        
                        # 5. 存入数据库
                        detail_fields = json.loads(row.to_json())
                        
                        new_job = Job(
                            job_code=job_code_val,
                            title=title,
                            company=company,
                            raw_jd_text=raw_text, 
                            salary_range=salary,
                            location=location,
                            required_experience_years=req_exp,
                            detail_fields=detail_fields,
                            ai_analysis=None
                        )
                        
                        db.add(new_job)
                        count += 1
                    
                    db.commit()
                    progress_bar.progress(1.0)
                    
                    st.success(f"职位导入完成！成功导入 {count} 条数据。")
                    
                except Exception as e:
                    st.error(f"导入失败: {str(e)}")

            st.divider()
            
            st.subheader("📤 导出职位数据")
            
            export_j_mode = st.radio("导出范围", ["全量导出", "按公司导出"], horizontal=True, key="export_job_mode")
            query_j_export = db.query(Job)
            
            if export_j_mode == "按公司导出":
                companies = [r[0] for r in db.query(Job.company).distinct().all() if r[0]]
                sel_j_companies = st.multiselect("选择公司", companies, key="export_job_comp_sel")
                if sel_j_companies:
                    query_j_export = query_j_export.filter(Job.company.in_(sel_j_companies))
                else:
                    query_j_export = None
            
            if st.button("生成职位导出文件", key="btn_export_job"):
                if query_j_export:
                    jobs_export = query_j_export.all()
                    if jobs_export:
                        export_list = []
                        for j in jobs_export:
                            # Base info
                            row_data = {
                                "职位名称": j.title,
                                "公司": j.company,
                                "薪资范围": j.salary_range,
                                "工作地点": j.location,
                                "经验要求": j.required_experience_years,
                                "JD全文": j.raw_jd_text,
                                "AI画像": j.ai_analysis,
                                "项目标签": ", ".join(j.project_tags) if j.project_tags else "",
                                "备注": j.notes
                            }
                            # Merge detail fields (flatten)
                            if j.detail_fields:
                                d_fields = j.detail_fields
                                if isinstance(d_fields, str):
                                    try: d_fields = json.loads(d_fields)
                                    except: pass
                                if isinstance(d_fields, dict):
                                    # Avoid overwriting base fields if keys conflict, or allow?
                                    # Prefixing might be safer but user wants original format.
                                    # We'll just merge, giving priority to base fields if collision (unlikely).
                                    row_data.update(d_fields)
                            
                            export_list.append(row_data)
                        
                        df_j_export = pd.DataFrame(export_list)
                        
                        buffer_j = io.BytesIO()
                        with pd.ExcelWriter(buffer_j, engine='openpyxl') as writer:
                            df_j_export.to_excel(writer, index=False)
                        
                        st.download_button(
                            label="📥 点击下载职位 Excel",
                            data=buffer_j.getvalue(),
                            file_name=f"jobs_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success(f"已生成 {len(export_list)} 条职位数据")
                    else:
                        st.warning("没有符合条件的数据")
                else:
                    st.warning("请至少选择一个公司")

        with tab4:
            st.subheader("批量生成职位画像")
            
            c_filter_j, c_action_j = st.columns([2, 2])
            with c_filter_j:
                job_filter_option = st.radio("筛选范围", ["所有未画像职位", "所有职位"], horizontal=True, key="job_filter_rad")
            
            # User Prompt Selection for Job
            user_job_prompts = db.query(SystemPrompt).filter_by(prompt_type='job', prompt_role='user', is_active=True).all()
            job_prompt_options = {p.prompt_name: p.content for p in user_job_prompts}
            selected_job_template = None
            if user_job_prompts:
                selected_job_prompt_name = st.selectbox("选择分析模版 (User Prompt)", options=list(job_prompt_options.keys()), key="batch_job_prompt_sel")
                selected_job_template = job_prompt_options[selected_job_prompt_name]

            query_j = db.query(Job)
            if job_filter_option == "所有未画像职位":
                query_j = query_j.filter((Job.ai_analysis == None) | (Job.ai_analysis == ""))
            
            batch_jobs = query_j.order_by(Job.created_at.desc()).all()
            
            if batch_jobs:
                st.write(f"待处理职位: {len(batch_jobs)} 个")
                
                with c_action_j:
                    st.write("")
                    st.write("")
                    if st.button("🚀 生成/重制选中的画像", type="primary", key="btn_batch_job_start"):
                        selected_job_ids = []
                        for job in batch_jobs:
                            if st.session_state.get(f"batch_job_chk_{job.id}", False):
                                selected_job_ids.append(job.id)
                        
                        if selected_job_ids:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for idx, job_id in enumerate(selected_job_ids):
                                job = db.query(Job).get(int(job_id))
                                if job and job.raw_jd_text:
                                    status_text.text(f"正在分析: {job.title}...")
                                    
                                    # Call AI
                                    parsed = AIService.parse_job(job.raw_jd_text, user_prompt_template=selected_job_template)
                                    
                                    if parsed.get("title") != "Parse Error":
                                        # Update fields
                                        job.title = parsed.get("title") or job.title
                                        job.company = parsed.get("company") or job.company
                                        
                                        # Robust AI Analysis Extraction
                                        analysis_data = parsed.get("analysis")
                                        if not analysis_data:
                                            # If 'analysis' key is missing, check if root contains content
                                            if any(k in parsed for k in ["must_have", "summary", "evaluation", "job_summary"]):
                                                analysis_data = parsed
                                            else:
                                                analysis_data = parsed
                                        job.ai_analysis = analysis_data
                                        
                                        job.salary_range = parsed.get("salary_range")
                                        job.location = parsed.get("location")
                                        job.required_experience_years = parsed.get("required_experience_years")
                                        
                                        AIService.add_job_to_vector_db(job.id, job.raw_jd_text, {"title": job.title, "company": job.company})
                                        db.commit()
                                        db.refresh(job)
                                    else:
                                        st.error(f"解析失败 ({job.title}): {parsed.get('analysis')}")
                                
                                progress_bar.progress((idx + 1) / len(selected_job_ids))
                            
                            st.success("批量处理完成！")
                            st.rerun()
                        else:
                            st.warning("请先勾选职位")

                st.divider()
                
                # Header
                h1, h2, h3, h4, h5, h6 = st.columns([0.5, 0.5, 2, 2, 1.5, 1])
                h1.markdown("✅")
                h2.markdown("**ID**")
                h3.markdown("**职位**")
                h4.markdown("**公司**")
                h5.markdown("**AI状态**")
                h6.markdown("**操作**")
                
                for job in batch_jobs:
                    c1, c2, c3, c4, c5, c6 = st.columns([0.5, 0.5, 2, 2, 1.5, 1])
                    with c1:
                        st.checkbox("Select", key=f"batch_job_chk_{job.id}", label_visibility="collapsed")
                    with c2:
                        st.write(str(job.id))
                    with c3:
                        st.write(job.title)
                    with c4:
                        st.write(job.company)
                    with c5:
                        if job.ai_analysis:
                            st.success("已生成")
                        else:
                            st.caption("未生成")
                    with c6:
                        if job.ai_analysis:
                            if st.button("查看", key=f"btn_view_batch_job_{job.id}"):
                                st.session_state.selected_job_id = job.id
                                st.session_state.job_view_mode = 'detail'
                                st.rerun()
                    st.markdown("---")
            else:
                st.info("没有符合条件的职位")

# ---------------- MATCH ----------------
elif page == "智能匹配":
    st.title("🎯 智能匹配中心")
    
    db = get_session()
    match_type = st.radio("匹配模式", ["为职位找人 (Job -> Candidates)", "为人才找职位 (Candidate -> Jobs)"])
    
    # 导入匹配引擎
    import sqlite3
    DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
    
    if match_type == "为职位找人 (Job -> Candidates)":
        # 获取有标签的职位
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, company, structured_tags 
            FROM jobs 
            WHERE structured_tags IS NOT NULL AND structured_tags != 'null' AND is_active = 1
            ORDER BY id
        """)
        jobs_data = cursor.fetchall()

        # 初始化搜索状态
        if 'job_search_keyword' not in st.session_state:
            st.session_state.job_search_keyword = ''

        # 搜索框 - 直接使用 key，Streamlit 会自动保存到 session_state
        st.text_input(
            "🔍 搜索职位（ID/名称/公司）",
            placeholder="输入关键词...",
            key='job_search_keyword'
        )

        job_search = st.session_state.job_search_keyword

        # 根据搜索词筛选
        if job_search:
            filtered_jobs = [j for j in jobs_data if 
                            (job_search.lower() in str(j[0])) or  # ID
                            (job_search.lower() in (j[1] or '').lower()) or  # 职位名称
                            (job_search.lower() in (j[2] or '').lower())]  # 公司
        else:
            filtered_jobs = jobs_data[:50]  # 默认显示前50个
        
        job_options = {f"{j[0]}: {j[1]} - {j[2]}": j[0] for j in filtered_jobs}
        
        st.caption(f"找到 {len(filtered_jobs)} 个职位")
        selected_job_label = st.selectbox("选择职位", options=list(job_options.keys()), label_visibility="collapsed")
        top_k = st.slider("显示结果数量", min_value=5, max_value=50, value=20)
        
        if selected_job_label and st.button("🚀 开始匹配", type="primary"):
            job_id = job_options[selected_job_label]
            
            # 获取职位标签
            cursor.execute("SELECT title, company, structured_tags FROM jobs WHERE id = ?", (job_id,))
            job_row = cursor.fetchone()
            if not job_row or not job_row[2]:
                st.error("该职位没有结构化标签，无法匹配")
            else:
                job_title, job_company, job_tags_str = job_row
                job_tags = json.loads(job_tags_str)
                
                st.subheader(f"📋 {job_title} @ {job_company}")
                
                # 显示职位标签
                with st.expander("🏷️ 职位要求标签", expanded=False):
                    st.json(job_tags)
                
                st.divider()
                
                # 获取候选人并匹配
                cursor.execute("""
                    SELECT c.id, c.name, c.current_company, c.current_title, c.skills, c.is_friend
                    FROM candidates c
                    WHERE c.skills IS NOT NULL AND c.skills != 'null' AND c.skills != '[]'
                """)
                candidates = cursor.fetchall()
                
                # 计算匹配分数
                results = []
                for cid, name, company, title, skills_str, is_friend in candidates:
                    try:
                        # skills 是一个简单的字符串数组，如 ["Python", "Django", "React"]
                        cand_skills = set(json.loads(skills_str)) if skills_str else set()

                        # 从职位标签中提取所有相关关键词
                        job_keywords = set()
                        for key in ["tech_domain", "tech_stack", "required_stack", "preferred_industry"]:
                            job_keywords.update(job_tags.get(key, []))

                        # 简单的技能匹配分数：候选人技能与职位关键词的重叠度
                        if job_keywords and cand_skills:
                            matched_skills = job_keywords & cand_skills
                            skill_score = len(matched_skills) / max(len(job_keywords), 1) * 100

                            # 生成匹配理由（显示匹配的技能）
                            reasons = [f"技能匹配: {', '.join(list(matched_skills)[:3])}"] if matched_skills else ["技能部分匹配"]
                        else:
                            skill_score = 50
                            reasons = ["需要进一步评估"]

                        # 公司匹配加分（如果候选人在目标公司）
                        company_score = 0
                        if company and job_company:
                            if any(kw in company.lower() for kw in str(job_company).lower().split()):
                                company_score = 20
                                reasons.append("目标公司背景")

                        # 基础分 + 技能匹配分 + 公司加分
                        total = 50 + skill_score * 0.3 + company_score

                        results.append({
                            "id": cid, "name": name, "company": company, "title": title,
                            "score": round(total, 1), "reasons": reasons, "is_friend": is_friend,
                            "matched_count": len(job_keywords & cand_skills) if job_keywords else 0
                        })
                    except Exception as e:
                        pass
                
                # 排序
                results.sort(key=lambda x: x["score"], reverse=True)
                results = results[:top_k]
                
                st.success(f"✅ 匹配完成！从 {len(candidates)} 位候选人中找到 Top {len(results)} 匹配")
                
                # 显示结果
                for i, r in enumerate(results, 1):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1.5, 1])
                        
                        with col1:
                            score_color = "🟢" if r["score"] >= 75 else ("🟡" if r["score"] >= 55 else "🔴")
                            friend_badge = "⭐" if r["is_friend"] else ""
                            st.markdown(f"### {i}. {r['name']} {friend_badge} {score_color} **{r['score']}分**")
                            st.caption(f"🏢 {r['company']} · {r['title']}")
                            if r["reasons"]:
                                st.markdown(f"✅ {', '.join(r['reasons'])}")
                        
                        with col2:
                            st.caption("技术/岗位/技术栈")
                            st.progress(int(r["tech"]) if r["tech"] <= 100 else 100)
                            st.progress(int(r["role"]) if r["role"] <= 100 else 100)
                            st.progress(int(r["stack"]) if r["stack"] <= 100 else 100)
                        
                        with col3:
                            if st.button("👀 详情", key=f"match_view_{r['id']}"):
                                st.session_state.selected_candidate_id = r["id"]
                                st.session_state.view_mode = 'detail'
                                st.session_state.nav_page = "人才库管理"
                                st.rerun()
        
        conn.close()

    else:  # Candidate -> Jobs
        # 获取有标签的候选人
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, current_company, current_title, structured_tags 
            FROM candidates 
            WHERE structured_tags IS NOT NULL AND structured_tags != 'null'
            ORDER BY name
        """)
        candidates_data = cursor.fetchall()

        # 初始化搜索状态
        if 'candidate_search_keyword' not in st.session_state:
            st.session_state.candidate_search_keyword = ''

        # 搜索框 - 直接使用 key，Streamlit 会自动保存到 session_state
        st.text_input(
            "🔍 搜索候选人（姓名/公司/职位）",
            placeholder="输入关键词...",
            key='candidate_search_keyword'
        )

        search_keyword = st.session_state.candidate_search_keyword

        # 根据搜索词筛选
        if search_keyword:
            filtered_data = [c for c in candidates_data if 
                            (search_keyword.lower() in (c[1] or '').lower()) or 
                            (search_keyword.lower() in (c[2] or '').lower()) or
                            (search_keyword.lower() in (c[3] or '').lower())]
        else:
            filtered_data = candidates_data[:100]  # 默认显示前100个
        
        cand_options = {f"{c[0]}: {c[1]} - {c[3] or '无职位'} @{c[2] or ''}": c[0] for c in filtered_data}
        
        st.caption(f"找到 {len(filtered_data)} 位候选人")
        selected_cand_label = st.selectbox("选择人才", options=list(cand_options.keys()), label_visibility="collapsed")
        
        if selected_cand_label and st.button("🚀 开始匹配", type="primary"):
            cand_id = cand_options[selected_cand_label]
            
            # 获取候选人标签
            cursor.execute("SELECT name, structured_tags FROM candidates WHERE id = ?", (cand_id,))
            cand_row = cursor.fetchone()
            if not cand_row or not cand_row[1]:
                st.error("该候选人没有结构化标签，无法匹配")
            else:
                cand_name, cand_tags_str = cand_row
                cand_tags = json.loads(cand_tags_str)
                
                
                # 获取职位并匹配（过滤空JD）
                cursor.execute("""
                    SELECT id, title, company, location, structured_tags 
                    FROM jobs 
                    WHERE structured_tags IS NOT NULL AND structured_tags != 'null' 
                    AND is_active = 1
                    AND raw_jd_text IS NOT NULL AND LENGTH(raw_jd_text) > 50
                """)
                jobs = cursor.fetchall()
                
                results = []
                for jid, title, company, location, tags_str in jobs:
                    try:
                        job_tags = json.loads(tags_str)
                        
                        # === 硬过滤规则 ===
                        cand_role = cand_tags.get("role_type", "")
                        job_role = job_tags.get("role_type", "")
                        cand_seniority = cand_tags.get("seniority", "")
                        job_seniority = job_tags.get("seniority", "")
                        
                        # 1. 管理层不匹配纯IC岗位
                        is_manager = cand_seniority == "管理层" or "Tech Lead" in cand_tags.get("role_orientation", [])
                        job_is_ic = job_seniority in ["初级(0-3年)", "中级(3-5年)"]
                        if is_manager and job_is_ic:
                            continue  # 跳过
                        
                        # 2. 岗位类型匹配 - 细分组
                        role_penalty = 1.0
                        role_match_groups = {
                            "算法": ["算法工程师", "算法专家", "算法研究员", "高级算法工程师"],  # 扩展算法组
                            "非技术研究": ["研究员"],  # 非技术类研究(法律/政策)
                            "工程": ["工程开发", "运维/SRE", "数据工程师"],
                            "管理": ["技术管理"],
                            "产品": ["产品经理", "解决方案架构师"]
                        }
                        cand_group = None
                        job_group = None
                        for group, roles in role_match_groups.items():
                            if cand_role in roles:
                                cand_group = group
                            if job_role in roles:
                                job_group = group
                        
                        # 3. 不同组严重惩罚
                        if cand_group and job_group and cand_group != job_group:
                            if cand_group == "算法开发" and job_group == "研究":
                                role_penalty = 0.3  # 算法开发不太适合研究岗
                            elif cand_group == "算法开发" and job_group == "工程":
                                role_penalty = 0.5
                            elif cand_group == "管理" and job_group != "管理":
                                role_penalty = 0.6
                            else:
                                role_penalty = 0.4
                        
                        # === 评分逻辑 ===
                        # 技术方向匹配 (30%) - 增加相关领域相似度
                        job_domains = set(job_tags.get("tech_domain", []))
                        cand_domains = set(cand_tags.get("tech_domain", []))
                        
                        # 相关领域映射（可获得额外加分）
                        domain_similarity = {
                            "语音": ["多模态", "NLP", "大模型/LLM"],  # 语音与多模态、NLP相关
                            "多模态": ["语音", "CV", "大模型/LLM"],  # 多模态涵盖音视频
                            "CV": ["多模态"],
                            "NLP": ["大模型/LLM", "语音", "Agent/智能体"],
                            "大模型/LLM": ["NLP", "Agent/智能体", "语音", "多模态"],
                            "AI Infra": ["大模型/LLM"],  # AI Infra支持大模型
                        }
                        
                        # 计算直接匹配
                        direct_match = len(job_domains & cand_domains)
                        
                        # 计算间接匹配（相关领域）
                        indirect_match = 0
                        for jd in job_domains:
                            if jd not in cand_domains:  # 没有直接匹配
                                related = domain_similarity.get(jd, [])
                                if any(cd in related for cd in cand_domains):
                                    indirect_match += 0.5  # 相关领域算半分
                        
                        total_match = direct_match + indirect_match
                        tech_score = total_match / max(len(job_domains), 1) * 100 if job_domains else 50
                        tech_score = min(tech_score, 100)  # 上限100
                        
                        # 细分专长匹配 (15%) - 新增
                        job_specialty = set(job_tags.get("specialty", []))
                        cand_specialty = set(cand_tags.get("specialty", []))
                        if job_specialty:
                            # 简化标签比较（去除前缀）
                            job_spec_clean = set()
                            for s in job_specialty:
                                if ": " in s:
                                    job_spec_clean.add(s.split(": ")[1])
                                else:
                                    job_spec_clean.add(s)
                            cand_spec_clean = set()
                            for s in cand_specialty:
                                if ": " in s:
                                    cand_spec_clean.add(s.split(": ")[1])
                                else:
                                    cand_spec_clean.add(s)
                            specialty_score = len(job_spec_clean & cand_spec_clean) / len(job_spec_clean) * 100
                        else:
                            specialty_score = 50  # 无要求时给中等分
                        
                        # 技术栈匹配 (20%)
                        job_stack = set(job_tags.get("tech_stack", []))
                        cand_stack = set(cand_tags.get("tech_stack", []))
                        stack_score = len(job_stack & cand_stack) / max(len(job_stack), 1) * 100 if job_stack else 50
                        
                        # 岗位类型匹配 (20%) - 改进：考虑升级匹配
                        # 升级路径：算法工程师 → 算法专家 → 高级算法工程师/算法研究员
                        role_upgrade_paths = {
                            ("算法工程师", "算法专家"): 95,  # 工程师升专家，良好匹配
                            ("算法工程师", "高级算法工程师"): 95,
                            ("算法专家", "算法研究员"): 90,
                        }
                        
                        if cand_role == job_role:
                            role_score = 100
                        elif (cand_role, job_role) in role_upgrade_paths:
                            role_score = role_upgrade_paths[(cand_role, job_role)]
                        elif cand_group == job_group:
                            role_score = 90  # 同组匹配提高到90分
                        else:
                            role_score = 20
                        
                        # 职级匹配 (15%) - 改进高配逻辑
                        seniority_order = ["初级(0-3年)", "中级(3-5年)", "高级(5-8年)", "专家(8年+)", "管理层"]
                        seniority_score = 50
                        if cand_seniority in seniority_order and job_seniority in seniority_order:
                            gap = seniority_order.index(cand_seniority) - seniority_order.index(job_seniority)
                            if gap == 0:
                                seniority_score = 100
                            elif gap == 1:
                                seniority_score = 90  # 候选人稍高，很好的匹配（提高）
                            elif gap == 2:
                                seniority_score = 75  # 候选人高2级，仍可接受
                            elif gap == -1:
                                seniority_score = 70
                            elif gap > 2:
                                seniority_score = 60  # 高配较多
                            else:
                                seniority_score = 40  # 低配
                        
                        # 加权总分 + 角色惩罚 (新权重: 30+15+20+20+15=100)
                        total = (tech_score * 0.30 + specialty_score * 0.15 + stack_score * 0.20 + 
                                 role_score * 0.20 + seniority_score * 0.15) * role_penalty
                        
                        results.append({
                            "id": jid, "title": title, "company": company, 
                            "location": location, "score": round(total, 1)
                        })
                    except:
                        pass
                
                results.sort(key=lambda x: x["score"], reverse=True)
                results = results[:20]
                
                # 缓存匹配结果到 session_state
                st.session_state['cand_match_results'] = results
                st.session_state['cand_match_cand_id'] = cand_id
                st.session_state['cand_match_cand_name'] = cand_name
                st.session_state['cand_match_cand_tags'] = cand_tags
        
        # 显示缓存的匹配结果（如果有）
        if 'cand_match_results' in st.session_state and st.session_state.get('cand_match_results'):
            results = st.session_state['cand_match_results']
            cand_name = st.session_state.get('cand_match_cand_name', '')
            cand_tags = st.session_state.get('cand_match_cand_tags', {})
            
            st.subheader(f"🧑‍💻 为 {cand_name} 匹配的职位")
            
            # 显示候选人标签
            with st.expander("🏷️ 候选人标签", expanded=False):
                st.json(cand_tags)
            
            st.success(f"✅ 找到 {len(results)} 个匹配职位")
            
            # 清除结果按钮
            if st.button("🔄 重新匹配", key="clear_cand_match"):
                del st.session_state['cand_match_results']
                st.rerun()
            
            st.divider()
            
            for i, r in enumerate(results, 1):
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"### {i}. {r['title']}")
                        st.caption(f"🏢 {r['company']} · 📍 {r['location'] or '未知'}")
                    with col2:
                        if r["score"] >= 70:
                            st.success(f"{r['score']}分")
                        elif r["score"] >= 50:
                            st.warning(f"{r['score']}分")
                        else:
                            st.error(f"{r['score']}分")
                    
                    # 使用 expander 显示职位详情（不需要 rerun）
                    with st.expander("📄 查看职位详情", expanded=False):
                        # 获取职位详细信息
                        cursor.execute("""
                            SELECT raw_jd_text, ai_analysis, structured_tags, salary_range, 
                                   required_experience_years, original_link
                            FROM jobs WHERE id = ?
                        """, (r['id'],))
                        job_detail = cursor.fetchone()
                        
                        if job_detail:
                            jd_text, ai_analysis, struct_tags, salary, exp_years, orig_link = job_detail
                            
                            # 基本信息行
                            info_col1, info_col2, info_col3 = st.columns(3)
                            with info_col1:
                                st.markdown(f"**💰 薪资**: {salary or '面议'}")
                            with info_col2:
                                st.markdown(f"**📅 经验要求**: {exp_years or '-'}年+")
                            with info_col3:
                                if orig_link:
                                    st.markdown(f"[🔗 原始链接]({orig_link})")
                            
                            st.divider()
                            
                            # 结构化标签
                            if struct_tags:
                                try:
                                    tags_data = json.loads(struct_tags) if isinstance(struct_tags, str) else struct_tags
                                    st.markdown("**🏷️ 职位标签**")
                                    tag_col1, tag_col2 = st.columns(2)
                                    with tag_col1:
                                        st.markdown(f"• 技术方向: {', '.join(tags_data.get('tech_domain', []))}")
                                        st.markdown(f"• 细分专长: {', '.join(tags_data.get('specialty', []))}")
                                        st.markdown(f"• 岗位类型: {tags_data.get('role_type', '-')}")
                                    with tag_col2:
                                        st.markdown(f"• 角色定位: {', '.join(tags_data.get('role_orientation', []))}")
                                        st.markdown(f"• 技术栈: {', '.join(tags_data.get('tech_stack', []))}")
                                        st.markdown(f"• 职级要求: {tags_data.get('seniority', '-')}")
                                    st.divider()
                                except:
                                    pass
                            
                            # JD全文
                            st.markdown("**📝 职位描述 (JD)**")
                            if jd_text:
                                # 限制显示长度，太长会影响阅读
                                display_text = jd_text[:3000] + ("..." if len(jd_text) > 3000 else "")
                                st.markdown(display_text)
                            else:
                                st.info("暂无JD内容")
                            
                            # AI分析（如果有）
                            if ai_analysis:
                                st.divider()
                                st.markdown("**🤖 AI画像分析**")
                                if isinstance(ai_analysis, str):
                                    try:
                                        ai_data = json.loads(ai_analysis)
                                        st.json(ai_data)
                                    except:
                                        st.markdown(ai_analysis)
                                else:
                                    st.json(ai_analysis)
        
        conn.close()