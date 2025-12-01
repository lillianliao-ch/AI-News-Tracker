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
page = st.sidebar.radio("导航", ["Dashboard", "人才库管理", "职位库管理", "智能匹配", "提示词配置"])

# ---------------- PROMPT CONFIG ----------------
if page == "提示词配置":
    from prompt_config_module import render_prompt_config
    render_prompt_config()

# ---------------- DASHBOARD ----------------
elif page == "Dashboard":
    st.title("📊 概览")
    
    db = get_session()
    cand_count = db.query(Candidate).count()
    job_count = db.query(Job).count()
    match_count = db.query(MatchRecord).count()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("人才总数", cand_count)
    col2.metric("在招职位", job_count)
    col3.metric("匹配记录", match_count)
    
    st.markdown("### 👋 欢迎回来")
    st.info("请从左侧菜单开始操作。首先请在【人才库管理】或【职位库管理】中导入数据。")

# ---------------- CANDIDATES ----------------
elif page == "人才库管理":
    
    db = get_session()

    if st.session_state.view_mode == 'detail' and st.session_state.selected_candidate_id:
        # --- 详情视图 ---
        cand_id = st.session_state.selected_candidate_id
        cand = db.query(Candidate).filter(Candidate.id == cand_id).first()
        
        if cand:
            col_nav, col_update = st.columns([4, 1])
            with col_nav:
                if st.button("← 返回列表"):
                    back_to_list()
            with col_update:
                if st.button("🔄 更新画像", type="primary"):
                    with st.spinner("正在更新 AI 画像..."):
                        # Try to get selected template from session state if available, else default
                        # Here we pick the first active user prompt as default for single update
                        active_p = db.query(SystemPrompt).filter_by(prompt_type='candidate', prompt_role='user', is_active=True).first()
                        template_c = active_p.content if active_p else None
                        
                        parsed = AIService.parse_resume(cand.raw_resume_text, user_prompt_template=template_c)
                        if parsed.get("name") != "Parse Error":
                            cand.name = parsed.get("name") or cand.name
                            cand.email = parsed.get("email") or cand.email
                            cand.phone = parsed.get("phone") or cand.phone
                            # Robust Summary Extraction
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
            
            st.title(f"{cand.name}")
            
            # 展示基本信息
            st.markdown(f"### 👤 基础信息")
            col1, col2, col3 = st.columns(3)
            with col1:
                 st.write(f"**姓名**: {cand.name}")
                 st.write(f"**当前公司**: {cand.current_company}")
                 st.write(f"**当前职位**: {cand.current_title}")
                 
                 # Editable Social Links
                 new_linkedin = st.text_input("LinkedIn", value=cand.linkedin_url or "", key="edit_linkedin")
                 if new_linkedin != (cand.linkedin_url or ""):
                     cand.linkedin_url = new_linkedin
                     db.commit()
                     st.toast("LinkedIn 已更新")

            with col2:
                 st.write(f"**工作年限**: {cand.experience_years} 年")
                 st.write(f"**年龄/出生**: {cand.age if cand.age else '未知'}")
                 st.write(f"**最高学历**: {cand.education_level}")
                 
                 new_github = st.text_input("GitHub", value=cand.github_url or "", key="edit_github")
                 if new_github != (cand.github_url or ""):
                     cand.github_url = new_github
                     db.commit()
                     st.toast("GitHub 已更新")

            with col3:
                 st.write(f"**期望地点**: {cand.expect_location if cand.expect_location else '未知'}")
                 st.write(f"**电话**: {cand.phone}")
                 st.write(f"**邮箱**: {cand.email}")
                 
                 new_twitter = st.text_input("Twitter", value=cand.twitter_url or "", key="edit_twitter")
                 if new_twitter != (cand.twitter_url or ""):
                     cand.twitter_url = new_twitter
                     db.commit()
                     st.toast("Twitter 已更新")
            
            st.divider()

            # 左右布局：左侧主要经历，右侧 AI 画像
            main_col, side_col = st.columns([3, 2])
            
            with main_col:
                # --- 备注 (New) ---
                st.markdown("**📝 候选人备注**")
                new_notes = st.text_area("输入备注信息...", value=cand.notes or "", key="cand_notes_input", height=100)
                if new_notes != (cand.notes or ""):
                    cand.notes = new_notes
                    db.commit()
                    st.toast("备注已保存")
                
                st.divider()

                # --- 工作经历 ---
                st.subheader("💼 工作经历")
                if cand.work_experiences and isinstance(cand.work_experiences, list):
                    for work in cand.work_experiences:
                        with st.container():
                            company = work.get('company', 'Unknown')
                            title = work.get('title', 'Unknown')
                            
                            # 优化显示：如果职位和公司名一样（数据源常见问题），则不重复显示
                            if title == company:
                                header = f"**{company}**"
                            else:
                                header = f"**{company}** | {title}"
                                
                            st.markdown(header)
                            st.caption(f"📅 {work.get('time', 'N/A')}")
                            
                            # 清洗描述文本，去除冗余前缀
                            desc = work.get('description', '')
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
                st.subheader("🎓 教育经历")
                if cand.education_details and isinstance(cand.education_details, list):
                    for edu in cand.education_details:
                        st.markdown(f"- **{edu.get('school', 'Unknown School')}** | {edu.get('major', 'N/A')} | {edu.get('degree', '')} ({edu.get('year', '')})")
                else:
                    st.info("暂无详细教育经历")

                # --- 原始简历 ---
                with st.expander("📄 查看原始简历全文"):
                    st.text_area("原始内容", cand.raw_resume_text, height=300)

            with side_col:
                # --- AI 画像 ---
                st.markdown("### 🤖 AI 画像")
                
                st.write("**核心评价**:")
                
                # Editable AI Analysis
                current_ai_text = cand.ai_summary or ""
                new_ai_text = st.text_area("AI 评价 (可编辑)", value=current_ai_text, height=600, key="cand_ai_edit")
                
                if new_ai_text != current_ai_text:
                    cand.ai_summary = new_ai_text
                    db.commit()
                    st.toast("AI 评价已更新")
                
                with st.container(border=True):
                    st.write("**技能标签**:")
                    if cand.skills:
                        st.markdown(" ".join([f"`{s}`" for s in cand.skills]))
                
                # --- 原始 JSON ---
                with st.expander("查看 JSON 数据"):
                    st.json(cand.to_dict())
        else:
            st.error("未找到该候选人")
            if st.button("返回列表"):
                back_to_list()

    else:
        # --- 列表视图 ---
        st.title("👥 人才库管理")
        tab1, tab2, tab3, tab4 = st.tabs(["人才列表", "导入导出", "批量画像", "搜索人才"])
        
        with tab1:
            # --- Search Filters ---
            with st.expander("🔍 筛选条件", expanded=True):
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    filter_name = st.text_input("姓名/关键词")
                with col2:
                    filter_company = st.text_input("公司")
                with col3:
                    filter_school = st.text_input("名校/学历")
                with col4:
                    filter_location = st.text_input("期望地点")
                with col5:
                    # Age range, handling min/max
                    age_min, age_max = st.slider("年龄区间", 18, 60, (20, 45))
            
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
            
            # Age Filtering (Logic: if age is 0 or null, we might include or exclude. Here we filter strict range if age > 0)
            # 仅对已解析出年龄的做筛选，未解析出的暂且保留或放后面? 
            # 这里简单处理：如果筛选了，只显示符合条件的。
            # query = query.filter(Candidate.age >= age_min, Candidate.age <= age_max) 
            # 考虑到很多数据 age 可能是 0，这样会把它们都过滤掉。
            # 优化：仅当 age > 0 时生效，或者用户意图是强制筛选。
            # Let's do strict filtering for now as requested.
            if age_min > 18 or age_max < 60:
                 query = query.filter(Candidate.age >= age_min, Candidate.age <= age_max)

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
            
            st.markdown(f"共 **{len(candidates)}** 人")
            
            st.divider()

            # --- Custom List View ---
            # Header
            h1, h2, h3, h4, h5, h6 = st.columns([1.5, 0.8, 1.5, 1.5, 1, 1.5])
            h1.markdown("**姓名**")
            h2.markdown("**年龄**")
            h3.markdown("**学历/学校**")
            h4.markdown("**公司**")
            h5.markdown("**地点**")
            h6.markdown("**操作**")
            st.divider()

            if candidates:
                for cand in candidates:
                        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 0.8, 1.5, 1.5, 1, 1.5])
                        
                        # Name & Title
                        with c1:
                            st.markdown(f"**{cand.name}**")
                        
                        # Age
                        with c2:
                            st.write(f"{cand.age if cand.age else '-'}")
                        
                        # Education
                        with c3:
                            edu_text = cand.education_level or "未知"
                            if cand.education_details and isinstance(cand.education_details, list) and len(cand.education_details) > 0:
                                school = cand.education_details[0].get('school', '')
                                if school:
                                    edu_text += f"\n{school}"
                            st.write(edu_text)
                            
                        # Company
                        with c4:
                            st.write(f"{cand.current_company or '-'}")
                            
                        # Location
                        with c5:
                            st.write(f"{cand.expect_location or '-'}")
                            
                        # Actions
                        with c6:
                            col_btn1, col_btn2 = st.columns(2)
                            if col_btn1.button("📄", key=f"view_{cand.id}", help="查看详情"):
                                st.session_state.selected_candidate_id = cand.id
                                st.session_state.view_mode = 'detail'
                                st.rerun()
                            
                            if col_btn2.button("🗑️", key=f"del_{cand.id}", help="删除"):
                                delete_candidate(cand.id)
                                st.rerun()
                        
                        st.markdown("---")
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

        with tab4:
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

            col_nav, col_update = st.columns([4, 1])
            with col_nav:
                if st.button("← 返回职位列表"):
                    back_to_job_list()
            with col_update:
                if st.button("🔄 更新画像", key="btn_update_job_single", type="primary"):
                    with st.spinner("正在更新 AI 画像..."):
                        active_p = db.query(SystemPrompt).filter_by(prompt_type='job', prompt_role='user', is_active=True).first()
                        template_c = active_p.content if active_p else None
                        
                        parsed = AIService.parse_job(job.raw_jd_text, user_prompt_template=template_c)
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
            
            # --- Header Section ---
            st.title(f"{job.title}")
            
            # Highlight Company and Tags
            tags = []
            # Simple logic to detect urgency
            if "急" in job.title or "Urgent" in job.title:
                tags.append("🔥 紧急")
            
            company_md = f"**{job.company}**"
            salary_md = f"💰 {job.salary_range or '面议'}"
            
            # Display larger Company/Tags info
            st.markdown(f"### {company_md} &nbsp;&nbsp; | &nbsp;&nbsp; {salary_md} &nbsp;&nbsp; {' '.join(tags)}")
            
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

            # Render Grid (No Border)
            st.write("")
            r1c1, r1c2, r1c3, r1c4 = st.columns(4)
            with r1c1:
                new_dept = st.text_input("部门", value=dept, key="edit_job_dept")
                if new_dept != dept:
                    update_detail_field(job, ["部门", "department"], new_dept)
                    st.rerun()
            with r1c2:
                small_metric(st, "学历要求", edu)
            with r1c3:
                new_level = st.text_input("岗位层级", value=level, key="edit_job_level")
                if new_level != level:
                    update_detail_field(job, ["层级", "level", "rank"], new_level)
                    st.rerun()
            with r1c4:
                small_metric(st, "招聘人数", count)
            
            st.write("")
            r2c1, r2c2, r2c3, r2c4 = st.columns(4)
            with r2c1: small_metric(st, "工作地点", job.location or "-")
            with r2c2: small_metric(st, "经验要求", f"{job.required_experience_years}年" if job.required_experience_years else "不限")
            with r2c3: small_metric(st, "发布日期", publish_date)
            with r2c4: small_metric(st, "HR / 负责人", hr)

            st.divider()
            
            # Content Layout
            main_col, ai_col = st.columns([3, 2])
            
            with main_col:
                st.subheader("📋 职位详情")
                st.markdown(job.raw_jd_text or "暂无详细描述")
                
                st.divider()
                
                # --- Project Tags & Notes ---
                c_tags, c_notes = st.columns([1, 1])
                with c_tags:
                    st.markdown("**🏷️ 项目标签**")
                    # Simple text input for tags (comma separated) for MVP
                    current_tags = ", ".join(job.project_tags) if job.project_tags else ""
                    new_tags_str = st.text_input("输入标签 (逗号分隔)", value=current_tags, key="job_tags_input")
                    if new_tags_str != current_tags:
                        job.project_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
                        db.commit()
                        st.toast("标签已保存")
                        
                with c_notes:
                    st.markdown("**📝 职位备注**")
                    new_notes = st.text_area("输入备注信息", value=job.notes or "", key="job_notes_input", height=100)
                    if new_notes != (job.notes or ""):
                        job.notes = new_notes
                        db.commit()
                        st.toast("备注已保存")

            with ai_col:
                st.subheader("🤖 AI 画像")
                # Increased height for better readability
                # Editable AI Analysis
                current_ai_text = ""
                if job.ai_analysis:
                    if isinstance(job.ai_analysis, str):
                        current_ai_text = job.ai_analysis
                    elif isinstance(job.ai_analysis, dict):
                        # Convert dict to formatted string for editing
                        lines = []
                        
                        # Check for standard keys
                        std_keys = ["must_have", "nice_to_have", "soft_skills", "selling_points"]
                        has_std = any(k in job.ai_analysis for k in std_keys)
                        
                        if has_std:
                            if job.ai_analysis.get("must_have"):
                                lines.append("**🎯 核心硬性要求**")
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
                                if k in ["title", "company", "location", "salary_range", "required_experience_years"]: continue # Skip base fields
                                if isinstance(v, (list, dict)):
                                    lines.append(f"\n**{k}**")
                                    lines.append(json.dumps(v, ensure_ascii=False, indent=2))
                                else:
                                    lines.append(f"**{k}**: {v}")
                                    
                        current_ai_text = "\n".join(lines)
                
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
                    filter_title = st.text_input("职位名称/关键词")
                with c2:
                    filter_company = st.text_input("公司")
                with c3:
                    filter_dept = st.text_input("部门")
                with c4:
                    filter_location = st.text_input("地点")
                
                c5, c6, c7, c8 = st.columns(4)
                with c5:
                    filter_level = st.text_input("职级")
                with c6:
                    filter_status = st.text_input("状态")
                with c7:
                    filter_urgent = st.checkbox("只看紧急职位")
            
            query = db.query(Job).filter(Job.is_active == 1)
            
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
            if filter_status:
                jobs = [j for j in jobs if j.detail_fields and filter_status in str(j.detail_fields)]
            
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
                # Title, Comp, Dept, Level, Loc, PubDate, UpdDate, Action
                h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2, 1.5, 1, 0.8, 1, 1, 1, 1])
                h1.markdown("**职位名称**")
                h2.markdown("**公司**")
                h3.markdown("**部门**")
                h4.markdown("**职级**")
                h5.markdown("**地点**")
                h6.markdown("**发布日期**")
                h7.markdown("**更新日期**")
                h8.markdown("**操作**")
                st.divider()
                
                if page_jobs:
                    for job in page_jobs:
                        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 1.5, 1, 0.8, 1, 1, 1, 1])
                        
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

                        with c1:
                            title_md = f"**{job.title}**"
                            if "急" in job.title or "Urgent" in job.title:
                                title_md += " 🔥"
                            st.markdown(title_md)
                        
                        with c2: st.write(job.company)
                        with c3: st.write(dept)
                        with c4: st.write(level)
                        with c5: st.write(job.location or "-")
                        with c6: st.write(format_date(pub_date))
                        with c7: st.write(format_date(upd_date))
                            
                        with c8:
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
    
    if match_type == "为职位找人 (Job -> Candidates)":
        jobs = db.query(Job).filter(Job.is_active == 1).all()
        job_options = {f"{j.id}: {j.title} - {j.company}": j.id for j in jobs}
        
        selected_job_label = st.selectbox("选择职位", options=list(job_options.keys()))
        
        if selected_job_label and st.button("开始匹配"):
            job_id = job_options[selected_job_label]
            job = db.query(Job).get(job_id)
            
            st.subheader(f"正在为 [{job.title}] 寻找匹配人才...")
            
            # 核心逻辑：用 Job 的 AI 画像 + Raw Text 去搜 Candidate
            # 优化 Query 构建策略：
            # 1. 职位名称权重最高 (重复 3 次以增加 Attention)
            # 2. 核心技能 (Must Have) 其次
            # 3. 原始 JD 作为补充语义
            
            search_keywords = [job.title] * 3
            
            if job.ai_analysis:
                # 尝试解析 JSON
                analysis = job.ai_analysis
                if isinstance(analysis, str):
                    try:
                        analysis = json.loads(analysis)
                    except:
                        pass
                
                if isinstance(analysis, dict):
                    must_haves = analysis.get('must_have', [])
                    if must_haves:
                        search_keywords.extend(must_haves)
            
            # 构建混合 Query
            query_text = " ".join(search_keywords) + " " + job.raw_jd_text[:500] # 限制 JD 长度防止噪声
            
            st.caption(f"🔍 搜索关键词: {', '.join(search_keywords[:5])} ...")
            
            results = AIService.search_candidates(query_text, n_results=10)
            
            if results and results['ids'][0]:
                for i, vector_id in enumerate(results['ids'][0]):
                    cand_id = int(vector_id.split('_')[1])
                    cand = db.query(Candidate).get(cand_id)
                    
                    if cand:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"### {cand.name} | {cand.current_title}")
                            st.caption(f"相关度: {1 - results['distances'][0][i]:.2f}") # Distance 越小越好，这里简单反转展示
                            st.write(f"**AI Summary**: {cand.ai_summary}")
                            st.write(f"**Skills**: {', '.join(cand.skills) if cand.skills else 'N/A'}")
                        with col2:
                            # 匹配结果也可以跳进详情页
                            col2_1, col2_2 = st.columns(2)
                            with col2_1:
                                if st.button("👀 详情", key=f"match_view_{cand.id}"):
                                    st.session_state.selected_candidate_id = cand.id
                                    st.session_state.view_mode = 'detail'
                                    # Switch to candidates page context logically? No, just set state and maybe redirect
                                    # 但因为我们在"智能匹配"页，这里直接弹窗或跳转比较复杂
                                    # 简单处理：在当前页展示详情 (Overlay) 或者需要用户手动切Tab
                                    # 为了体验，我们这里用 expander 展示详情，或者 Dialog
                                    st.text_area("简历预览", cand.raw_resume_text, height=200)
                            
                            with col2_2:
                                if st.button("🤖 深度评估", key=f"match_assess_{cand.id}"):
                                    with st.spinner("AI 招聘专家正在深度分析 (Expert Mode)..."):
                                        # 准备数据
                                        job_data = {
                                            "title": job.title,
                                            "company": job.company,
                                            "requirements": job.ai_analysis,
                                            "jd_text": job.raw_jd_text[:1000]
                                        }
                                        cand_data = {
                                            "name": cand.name,
                                            "skills": cand.skills,
                                            "experience": cand.experience_years,
                                            "summary": cand.ai_summary,
                                            "resume_text": cand.raw_resume_text[:1000]
                                        }
                                        
                                        assessment = AIService.assess_match(job_data, cand_data)
                                        
                                        # 使用 Dialog 展示结果
                                        @st.dialog("AI 深度评估报告")
                                        def show_assessment(data):
                                            score = data.get('match_score', 0)
                                            if score >= 80:
                                                st.success(f"匹配度: {score}分 - 高度匹配")
                                            elif score >= 60:
                                                st.warning(f"匹配度: {score}分 - 一般匹配")
                                            else:
                                                st.error(f"匹配度: {score}分 - 不匹配")
                                            
                                            st.write(f"**综合评价**: {data.get('reason')}")
                                            
                                            c1, c2 = st.columns(2)
                                            with c1:
                                                st.write("✅ **优势**")
                                                for p in data.get('pros', []):
                                                    st.write(f"- {p}")
                                            with c2:
                                                st.write("⚠️ **劣势/风险**")
                                                for c in data.get('cons', []):
                                                    st.write(f"- {c}")
                                                    
                                            st.info(f"💡 **面试建议**: {data.get('suggestions', '无')}")
                                        
                                        show_assessment(assessment)
                        st.divider()
            else:
                st.info("没有找到匹配度足够高的人选。建议优化职位描述或扩充人才库。")

    else: # Candidate -> Jobs
        candidates = db.query(Candidate).all()
        cand_options = {f"{c.id}: {c.name} - {c.current_title}": c.id for c in candidates}
        
        selected_cand_label = st.selectbox("选择人才", options=list(cand_options.keys()))
        
        if selected_cand_label and st.button("开始匹配"):
            cand_id = cand_options[selected_cand_label]
            cand = db.query(Candidate).get(cand_id)
            
            st.subheader(f"正在为 [{cand.name}] 寻找合适职位...")
            
            query_text = f"{cand.current_title} {cand.raw_resume_text}"
            if cand.skills:
                query_text += " " + " ".join(cand.skills)
                
            results = AIService.search_jobs(query_text, n_results=10)
            
            if results and results['ids'][0]:
                for i, vector_id in enumerate(results['ids'][0]):
                    job_id = int(vector_id.split('_')[1])
                    job = db.query(Job).get(job_id)
                    
                    if job:
                        st.markdown(f"### {job.title} | {job.company}")
                        st.write(f"**薪资**: {job.salary_range}")
                        st.write(f"**地点**: {job.location}")
                        with st.expander("查看 JD"):
                            st.write(job.raw_jd_text)
                        st.divider()