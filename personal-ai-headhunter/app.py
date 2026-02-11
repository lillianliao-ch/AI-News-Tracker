import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
from sqlalchemy.orm import Session, defer
from sqlalchemy import String, cast
from database import engine, init_db, get_db, SessionLocal, Candidate, Job, MatchRecord, SystemPrompt
from ai_service import AIService
import json
import re
from job_search import match_candidate_to_jobs
import time as _time
import logging as _logging

# ⏱️ 性能计时 — 脚本开始执行
_PERF_SCRIPT_START = _time.time()
_perf_logger = _logging.getLogger('headhunter_perf')
if not _perf_logger.handlers:
    _fh = _logging.FileHandler('/tmp/headhunter_perf.log', mode='a')
    _fh.setFormatter(_logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
    _perf_logger.addHandler(_fh)
    _perf_logger.setLevel(_logging.DEBUG)
_perf_logger.debug(f"\n====== 脚本开始执行 ======")

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


@st.cache_data(ttl=30, show_spinner=False)
def get_jobs_page_cached(
    filter_job_code,
    filter_title,
    filter_company,
    filter_location,
    filter_level,
    filter_tags,
    filter_link,
    filter_urgency,
    page_num,
    page_size,
    cache_buster=0
):
    """
    职位列表缓存查询：
    - DB 侧过滤 + 分页
    - 返回轻量字典，避免在缓存里放 ORM 对象
    """
    db = SessionLocal()
    try:
        urgency_options = ["全部", "较急", "紧急", "非常紧急"]
        query = db.query(Job).filter(Job.is_active == 1)

        if filter_job_code:
            query = query.filter(Job.job_code.contains(filter_job_code))
        if filter_title:
            query = query.filter(Job.title.contains(filter_title))
        if filter_company:
            query = query.filter(Job.company.contains(filter_company))
        if filter_location:
            query = query.filter(Job.location.contains(filter_location))
        if filter_link:
            query = query.filter(Job.jd_link.contains(filter_link))
        if filter_urgency != "全部":
            urgency_value = urgency_options.index(filter_urgency)
            query = query.filter(Job.urgency >= urgency_value)
        if filter_level:
            query = query.filter(cast(Job.detail_fields, String).contains(filter_level))
        if filter_tags and filter_tags.strip():
            for tag in [t.strip() for t in filter_tags.split(",") if t.strip()]:
                query = query.filter(cast(Job.project_tags, String).contains(tag))

        total_jobs = query.count()
        start_idx = (page_num - 1) * page_size
        jobs = query.order_by(Job.created_at.desc()).offset(start_idx).limit(page_size).all()

        items = []
        for job in jobs:
            items.append({
                "id": job.id,
                "job_code": job.job_code,
                "title": job.title,
                "urgency": getattr(job, "urgency", 0) or 0,
                "company": job.company,
                "department": job.department,
                "seniority_level": job.seniority_level,
                "location": job.location,
                "detail_fields": job.detail_fields,
                "published_channels": job.published_channels,
            })

        return {"total": total_jobs, "items": items}
    finally:
        db.close()

def extract_candidate_tags(candidate):
    """
    为候选人提取结构化标签。
    Args:
        candidate: Candidate对象（需要已保存到数据库，有id）
    Returns:
        dict: 提取的标签，如果失败返回None
    """
    from openai import OpenAI
    
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 构建候选人信息文本
        resume_text = candidate.raw_resume_text or ""
        if candidate.work_experiences:
            work_exp = candidate.work_experiences if isinstance(candidate.work_experiences, list) else json.loads(candidate.work_experiences)
            for exp in work_exp[:3]:
                resume_text += f"\n工作: {exp.get('company','')} - {exp.get('title','')} - {exp.get('description','')}"
        if candidate.education_details:
            edu_details = candidate.education_details if isinstance(candidate.education_details, list) else json.loads(candidate.education_details)
            for edu in edu_details:
                resume_text += f"\n教育: {edu.get('school','')} - {edu.get('degree','')} - {edu.get('major','')}"
        
        tag_prompt = f"""请从以下候选人信息中提取结构化标签。

【候选人信息】
姓名: {candidate.name}
当前职位: {candidate.current_title or '未知'}
当前公司: {candidate.current_company or '未知'}
工作年限: {candidate.experience_years or 0}年
学历: {candidate.education_level or '未知'}
简历/画像: {resume_text[:2000]}

请从以下维度提取标签:
1. tech_domain (技术方向): 【AI】大模型/LLM, CV, NLP, 推荐系统, 搜索, 语音/音频, 多模态, AI Infra, 具身智能, 垂直应用 【工程】客户端开发, 后端开发, 前端开发, 基础架构/Infra, 音视频 (不要用"其他")
2. core_specialty (核心专长): 【AI】预训练, 对齐/RLHF, SFT微调, 推理优化, RAG/知识库, Agent开发, Prompt工程, 模型压缩/量化, 分布式训练, 框架开发 【工程】IM/即时通讯, 跨端框架, 客户端基础架构, 音视频引擎, 微服务架构, DevOps
3. tech_skills (技术技能): 具体技术点
4. role_type (岗位类型): 算法工程师, 算法专家, 算法研究员, 客户端工程师, 后端工程师, 前端工程师, 架构师, 工程开发, 产品经理, 技术管理, 研究员
5. seniority (职级层次): 初级(0-3年), 中级(3-5年), 资深(5-10年), 专家(10年+), 管理层
6. industry_exp (行业背景): 互联网大厂, AI独角兽, 云厂商, 芯片/硬件, 外企, 学术背景, IM/通信厂商

请输出JSON格式，只输出JSON，不要其他内容:
{{
  "tech_domain": ["技术方向1"],
  "core_specialty": ["核心专长1"],
  "tech_skills": ["技术技能1", "技术技能2"],
  "role_type": "岗位类型",
  "seniority": "职级层次",
  "industry_exp": ["行业背景"]
}}"""

        tag_response = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": tag_prompt}],
            temperature=0.1
        )
        
        tag_result = tag_response.choices[0].message.content.strip()
        if "```json" in tag_result:
            tag_result = tag_result.split("```json")[1].split("```")[0]
        elif "```" in tag_result:
            tag_result = tag_result.split("```")[1].split("```")[0]
        
        tags = json.loads(tag_result)
        return tags
        
    except Exception as e:
        print(f"标签提取失败: {e}")
        return None

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

# ============ 侧边栏导航（更窄的样式）============
# 添加CSS使侧边栏更窄
st.markdown("""
<style>
    /* ===== 蓝色主题 ===== */
    :root {
        --primary-color: #2563eb;
        --primary-hover: #1d4ed8;
        --primary-light: #dbeafe;
        --secondary-color: #64748b;
        --text-dark: #1e293b;
        --text-muted: #64748b;
        --bg-light: #f8fafc;
        --border-color: #e2e8f0;
    }
    
    /* 主按钮改为蓝色 */
    .stButton > button[kind="primary"],
    .stButton > button[data-baseweb="button"] {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-baseweb="button"]:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    
    /* 次要按钮 */
    .stButton > button[kind="secondary"] {
        background-color: #f1f5f9 !important;
        border-color: #e2e8f0 !important;
        color: #475569 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #e2e8f0 !important;
    }
    
    /* 下载按钮蓝色 */
    .stDownloadButton > button {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: white !important;
    }
    .stDownloadButton > button:hover {
        background-color: #1d4ed8 !important;
    }
    
    /* 侧边栏背景 */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
    }
    
    /* Radio按钮选中状态改为蓝色 */
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
        background-color: #dbeafe !important;
    }
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"]::before {
        background-color: #2563eb !important;
    }
    
    /* 复选框蓝色 */
    .stCheckbox > label > div[data-checked="true"] {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
    }
    
    /* Tab选项卡蓝色 */
    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        border-bottom-color: #2563eb !important;
    }
    
    /* 输入框聚焦边框蓝色 */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div:focus-within {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 1px #2563eb !important;
    }
    
    /* 链接蓝色 */
    a {
        color: #2563eb !important;
    }
    a:hover {
        color: #1d4ed8 !important;
    }
    
    /* Metric指标标签颜色 */
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
    }
    
    /* 进度条蓝色 */
    .stProgress > div > div > div {
        background-color: #2563eb !important;
    }
    
    /* ===== 原有侧边栏样式 ===== */
    /* 隐藏Streamlit多页面导航（app, prompt config文字）*/
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* 侧边栏宽度调整 */
    [data-testid="stSidebar"] {
        min-width: 140px !important;
        max-width: 140px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 140px !important;
    }
    
    /* 侧边栏内边距减小 */
    [data-testid="stSidebar"] .block-container {
        padding: 0.5rem 0.3rem !important;
    }
    
    /* 侧边栏标题字体 */
    [data-testid="stSidebar"] h1 {
        font-size: 1.1rem !important;
        white-space: nowrap !important;
        margin-bottom: 1rem !important;
    }
    
    /* Radio按钮文字不换行，增加间隔 */
    [data-testid="stSidebar"] .stRadio label {
        white-space: nowrap !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        white-space: nowrap !important;
        padding: 0.5rem 0 !important;
        margin-bottom: 0.3rem !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 0.5rem !important;
    }
    
    /* 主内容区顶部空白减少 */
    .main .block-container {
        padding-top: 1rem !important;
    }
    
    /* 标题上方间距减少 */
    .main h1:first-of-type {
        margin-top: 0 !important;
    }
    
    /* 隐藏tab下方的灰色分割线 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0.5rem !important;
    }
    
    /* 筛选区域更紧凑 */
    .stExpander {
        border: none !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("🕵️ AI猎头")

# 支持从其他页面跳转
nav_options = ["每日工作台", "沟通跟进", "人才库管理", "职位库管理", "智能匹配", "数据分析", "批处理", "提示词配置"]

# 获取当前应该显示的页面（优先使用session_state中的nav_page）
current_page = st.session_state.get('nav_page', '每日工作台')
if current_page not in nav_options:
    current_page = '每日工作台'
default_idx = nav_options.index(current_page)

# 使用key来追踪radio的选择
page = st.sidebar.radio("导航", nav_options, index=default_idx, key="nav_radio")

# 只有当用户通过radio改变页面时才更新nav_page
# 如果page与nav_page不同，说明用户点击了radio
if page != st.session_state.get('nav_page'):
    st.session_state.nav_page = page
    # 重置view_mode，因为用户主动切换了页面
    if 'view_mode' in st.session_state:
        st.session_state.view_mode = 'list'
else:
    # 保持当前的nav_page不变
    page = st.session_state.get('nav_page', page)

# ---------------- 每日工作台 ----------------
if page == "每日工作台":
    st.title("📋 每日工作台")
    st.caption("🧠 Agent-Lite — 基于数据库实时状态的智能行动建议")

    from daily_planner import collect_daily_context, generate_plan_with_llm
    import glob

    # 数据采集（缓存1小时）
    @st.cache_data(ttl=3600, show_spinner="正在采集数据库状态...")
    def get_daily_context():
        return collect_daily_context()

    context = get_daily_context()
    stats = context["stats"]

    # ── 核心指标 ──
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("👥 候选人", stats["total_candidates"])
    m2.metric("🤝 好友", stats["total_friends"])
    m3.metric("📋 活跃JD", stats["total_active_jds"])
    m4.metric("🔥 紧急JD", stats["urgent_jds_count"])
    m5.metric("📭 空管道JD", stats["jds_no_pipeline_count"])

    m6, m7, m8, m9, m10 = st.columns(5)
    m6.metric("🏷 有标签", stats["candidates_with_tags"])
    m7.metric("🙈 好友未沟通", stats["friends_no_comm_count"])
    m8.metric("📥 本周新候选人", stats["recent_candidates_count"])
    m9.metric("📥 本周新JD", stats["recent_jds_count"])
    m10.metric("📅 今日预约", len(context["scheduled_today"]))

    st.divider()

    # ── 告警区域 ──
    alert_col1, alert_col2 = st.columns(2)

    with alert_col1:
        # 今日预约
        if context["scheduled_today"]:
            st.markdown("### 📞 今日预约联系")
            for c in context["scheduled_today"]:
                st.markdown(f"- **{c['name']}** — {c.get('company') or ''} {c.get('title') or ''}")

        # 过期预约
        if context["overdue_scheduled"]:
            st.markdown("### ⚠️ 过期未联系")
            for c in context["overdue_scheduled"]:
                st.warning(f"**{c['name']}** — 预约{c['scheduled_date']}，已过期", icon="⚠️")

    with alert_col2:
        # 紧急JD
        if context["urgent_jds"]:
            st.markdown("### 🔥 紧急JD")
            for j in context["urgent_jds"]:
                urgency_text = "🔴" * min(j.get("urgency", 1), 3)
                hc = f" HC:{j['headcount']}" if j.get("headcount") else ""
                code = f" [{j['job_code']}]" if j.get("job_code") else ""
                st.markdown(f"{urgency_text} **{j['title']}** — {j['company']}{code}{hc}")

        # 超期未跟进
        if context["stale_candidates"]:
            st.markdown("### 💤 超期未跟进")
            for c in context["stale_candidates"][:5]:
                st.markdown(f"- **{c['name']}** — {c.get('company') or ''} — 上次沟通: {c.get('last_comm', '-')}")

    st.divider()

    # ── LLM行动计划 ──
    st.markdown("## 🧠 AI行动建议")

    # 检查是否有今日已缓存的报告
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_report = os.path.join(reports_dir, f"daily_plan_{today_str}.md")

    # 用session_state缓存LLM结果
    if "daily_plan" not in st.session_state:
        st.session_state.daily_plan = None

    col_gen, col_info = st.columns([1, 3])
    with col_gen:
        generate_btn = st.button("🧠 生成/刷新行动计划", type="primary")
    with col_info:
        if os.path.exists(today_report):
            mod_time = datetime.fromtimestamp(os.path.getmtime(today_report))
            st.caption(f"📄 今日报告已缓存（{mod_time.strftime('%H:%M')} 生成）")

    if generate_btn:
        with st.spinner("🧠 正在调用 AI 分析生成行动计划..."):
            plan = generate_plan_with_llm(context)
            if plan:
                st.session_state.daily_plan = plan
                # 保存报告
                from daily_planner import save_daily_report
                save_daily_report(context, plan)
                st.success("✅ 行动计划已生成并保存")
            else:
                st.error("❌ AI 分析失败，请稍后重试")

    # 显示行动计划
    plan = st.session_state.daily_plan

    # 如果session没有但有文件缓存，从文件读取显示
    if not plan and os.path.exists(today_report):
        with open(today_report, "r", encoding="utf-8") as f:
            report_content = f.read()
        # 只显示LLM部分（---分隔符之后）
        if "---" in report_content:
            llm_part = report_content.split("---", 1)[1]
            st.markdown(llm_part)
        else:
            st.info("💡 今日报告中暂无AI建议，点击上方按钮生成")
    elif plan:
        if plan.get("greeting"):
            st.info(f"💬 {plan['greeting']}")

        plan_col1, plan_col2 = st.columns(2)

        with plan_col1:
            high = plan.get("high_priority", [])
            if high:
                st.markdown("### 🔴 今日必做")
                for i, item in enumerate(high, 1):
                    if not isinstance(item, dict) or not item:
                        continue
                    action = item.get('action', item.get('title', ''))
                    reason = item.get('reason', '')
                    how = item.get('how', '')
                    st.markdown(f"**{i}. {action}**")
                    if reason:
                        st.caption(f"原因: {reason}")
                    if how:
                        st.caption(f"方法: {how}")
                    st.markdown("---")

        with plan_col2:
            suggested = plan.get("suggested", [])
            if suggested:
                st.markdown("### 🟡 建议做")
                for i, item in enumerate(suggested, 1):
                    if not isinstance(item, dict) or not item:
                        continue
                    action = item.get('action', item.get('title', ''))
                    reason = item.get('reason', '')
                    st.markdown(f"**{i}. {action}**")
                    if reason:
                        st.caption(f"原因: {reason}")
                    st.markdown("---")

        if plan.get("pipeline_health"):
            st.markdown(f"**📈 管道健康度:** {plan['pipeline_health']}")
        if plan.get("weekly_insight"):
            st.markdown(f"**💡 本周洞察:** {plan['weekly_insight']}")
    else:
        st.info("💡 点击上方「生成/刷新行动计划」按钮，获取AI智能分析")

    # ── Sourcing 进度 ──
    sp = context.get("sourcing_progress")
    if sp:
        st.divider()
        st.markdown("### 📈 Sourcing 进度")
        totals = sp['totals']
        targets = sp['targets']

        # 渠道进度条
        s_col1, s_col2, s_col3 = st.columns(3)

        def _progress_metric(col, label, key, icon):
            done = totals.get(key, 0)
            goal = targets.get(key, 0)
            pct = done / goal if goal > 0 else 0
            with col:
                st.markdown(f"**{icon} {label}**")
                st.progress(min(pct, 1.0))
                st.caption(f"{done} / {goal} ({pct*100:.0f}%)")

        _progress_metric(s_col1, "脉脉打招呼", "maimai_greeting", "💬")
        _progress_metric(s_col2, "脉脉加好友", "maimai_friend", "🤝")
        _progress_metric(s_col3, "LinkedIn", "linkedin_request", "🔗")

        s_col4, s_col5, s_col6 = st.columns(3)
        _progress_metric(s_col4, "Email", "email", "📧")
        _progress_metric(s_col5, "全渠道回复", "replies", "💬")
        _progress_metric(s_col6, "推荐提交", "referrals", "🎯")

        today_target = sp.get('today_target')
        if today_target:
            st.info(f"🎯 **今日目标公司**: {today_target['target_company']}")

    # ── 今日跟进提醒 ──
    st.divider()
    st.markdown("### 🔔 今日跟进提醒")
    db = get_session()
    from datetime import date as _date_type
    _today_date = _date_type.today()
    _today_str = _today_date.strftime("%Y-%m-%d")

    # 策略跟进 (follow_up_date)
    fu_candidates = db.query(Candidate).filter(
        Candidate.pipeline_stage.notin_(['closed', 'new']),
        Candidate.follow_up_date.isnot(None),
        Candidate.follow_up_date <= _today_str
    ).order_by(Candidate.follow_up_date.asc()).all()

    # 手动预约 (scheduled_contact_date)
    sched_candidates = db.query(Candidate).filter(
        Candidate.scheduled_contact_date.isnot(None),
        Candidate.scheduled_contact_date != '',
        Candidate.scheduled_contact_date <= _today_str
    ).order_by(Candidate.scheduled_contact_date.asc()).all()

    # 去重（同一人可能同时出现在两套系统中）
    seen_ids = set()
    followup_merged = []
    for c in fu_candidates + sched_candidates:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            followup_merged.append(c)

    if followup_merged:
        fu_col1, fu_col2 = st.columns([1, 5])
        with fu_col1:
            st.metric("待跟进", len(followup_merged))
        with fu_col2:
            for c in followup_merged[:5]:
                stage_icons = {"contacted": "📤", "following_up": "🔄", "replied": "💬", "wechat_connected": "💚", "in_pipeline": "🎯"}
                icon = stage_icons.get(c.pipeline_stage, "○")
                st.markdown(f"{icon} **{c.name}** — {c.current_company or ''} · {c.current_title or ''}")
            if len(followup_merged) > 5:
                st.caption(f"... 还有 {len(followup_merged) - 5} 人，前往「沟通跟进」查看")
        if st.button("📋 前往沟通跟进", key="goto_followup"):
            st.session_state.nav_page = '沟通跟进'
            st.rerun()
    else:
        st.success("✅ 今天没有需要跟进的候选人")

    # ── 历史报告 ──
    with st.expander("📂 历史报告"):
        if os.path.isdir(reports_dir):
            report_files = sorted(glob.glob(os.path.join(reports_dir, "daily_plan_*.md")), reverse=True)
            if report_files:
                for rf in report_files[:10]:
                    fname = os.path.basename(rf)
                    date_str = fname.replace("daily_plan_", "").replace(".md", "")
                    with open(rf, "r", encoding="utf-8") as f:
                        content = f.read()
                    st.markdown(f"**📅 {date_str}**")
                    st.markdown(content[:500] + ("..." if len(content) > 500 else ""))
                    st.divider()
            else:
                st.info("暂无历史报告")
        else:
            st.info("暂无历史报告")

# ---------------- 批处理 ----------------
elif page == "批处理":
    st.title("⚙️ 批处理任务")
    
    db = get_session()
    from database import ResumeTask
    from datetime import timedelta
    
    # 统计
    pending_count = db.query(ResumeTask).filter(ResumeTask.status == 'pending').count()
    processing_count = db.query(ResumeTask).filter(ResumeTask.status == 'processing').count()
    done_count = db.query(ResumeTask).filter(ResumeTask.status == 'done').count()
    failed_count = db.query(ResumeTask).filter(ResumeTask.status == 'failed').count()
    
    # 状态卡片
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.metric("⏳ 待处理", pending_count)
    with col2:
        st.metric("🔄 处理中", processing_count)
    with col3:
        st.metric("✅ 已完成", done_count)
    with col4:
        st.metric("❌ 失败", failed_count)
    with col5:
        if st.button("🔄 刷新", key="refresh_batch"):
            st.rerun()
    
    st.divider()
    
    # === 批量导入简历 ===
    st.subheader("📤 批量导入简历")
    st.caption("输入包含简历文件的文件夹路径，系统将自动完成：导入 → AI解析 → 提取标签 → 复制附件")
    
    folder_path = st.text_input(
        "文件夹路径", 
        placeholder="例如: /Users/lillianliao/notion_rag/数据输入/0131CV",
        key="batch_folder_path"
    )
    
    # 显示文件夹内容预览
    if folder_path and os.path.isdir(folder_path):
        import glob
        supported_ext = ['*.pdf', '*.txt', '*.jpg', '*.jpeg', '*.png', '*.webp']
        files = []
        for ext in supported_ext:
            files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        # 过滤非简历文件
        excluded = ['论文', 'paper', 'arxiv', '1908.', '1909.', '2020.', '2021.']
        resume_files = [f for f in files if not any(kw.lower() in os.path.basename(f).lower() for kw in excluded)]
        
        st.info(f"📂 发现 **{len(resume_files)}** 个简历文件")
        
        if resume_files:
            with st.expander("查看文件列表", expanded=False):
                for f in resume_files[:20]:
                    st.write(f"• {os.path.basename(f)}")
                if len(resume_files) > 20:
                    st.write(f"... 还有 {len(resume_files) - 20} 个文件")
            
            if st.button("🚀 开始导入", type="primary", key="start_batch_import"):
                import shutil
                import uuid
                
                UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                added = 0
                skipped = 0
                
                # 检查已存在的任务
                existing = set(t.file_name for t in db.query(ResumeTask).all() if t.file_name)
                
                for i, filepath in enumerate(resume_files):
                    filename = os.path.basename(filepath)
                    progress_bar.progress((i + 1) / len(resume_files))
                    status_text.text(f"正在处理 {i+1}/{len(resume_files)}: {filename}")
                    
                    if filename in existing:
                        skipped += 1
                        continue
                    
                    # 复制到uploads目录
                    ext = os.path.splitext(filename)[1].lower().strip('.')
                    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
                    dest_path = os.path.join(UPLOAD_DIR, unique_name)
                    
                    try:
                        shutil.copy2(filepath, dest_path)
                        
                        # 创建任务
                        task = ResumeTask(
                            file_path=dest_path,
                            file_name=filename,
                            file_type=ext,
                            status='pending'
                        )
                        db.add(task)
                        added += 1
                    except Exception as e:
                        st.warning(f"复制失败: {filename} - {e}")
                
                db.commit()
                progress_bar.empty()
                status_text.empty()
                
                st.success(f"✅ 已添加 {added} 个任务到队列，跳过 {skipped} 个已存在文件")
                st.info("💡 后台Worker正在自动处理，完成后会自动提取标签和复制附件")
                st.rerun()
    elif folder_path:
        st.error("❌ 文件夹路径不存在")
    
    st.divider()
    
    # === 最近任务 ===
    st.subheader("📋 最近任务")
    
    # 筛选器
    filter_col1, filter_col2 = st.columns([1, 4])
    with filter_col1:
        status_filter = st.selectbox("状态", ["全部", "pending", "processing", "done", "failed"], key="task_status_filter")
    
    if status_filter == "全部":
        recent_tasks = db.query(ResumeTask).order_by(ResumeTask.id.desc()).limit(30).all()
    else:
        recent_tasks = db.query(ResumeTask).filter(ResumeTask.status == status_filter).order_by(ResumeTask.id.desc()).limit(30).all()
    
    if recent_tasks:
        for task in recent_tasks:
            status_icon = {"pending": "⏳", "processing": "🔄", "done": "✅", "failed": "❌"}.get(task.status, "❓")
            
            with st.container():
                cols = st.columns([0.5, 3, 1, 2])
                with cols[0]:
                    st.write(status_icon)
                with cols[1]:
                    st.write(f"**{task.file_name}**")
                with cols[2]:
                    st.write(task.status)
                with cols[3]:
                    if task.status == 'done' and task.candidate_id:
                        cand = db.query(Candidate).filter(Candidate.id == task.candidate_id).first()
                        if cand:
                            st.write(f"→ {cand.name}")
                    elif task.status == 'failed' and task.error_message:
                        st.write(f"❌ {task.error_message[:40]}...")
    else:
        st.info("暂无任务记录")
    
    st.divider()
    
    # === 操作区 ===
    st.subheader("🛠️ 后续操作")
    
    op_col1, op_col2, op_col3 = st.columns(3)
    
    with op_col1:
        # 提取标签
        new_cands_no_tags = db.query(Candidate).filter(
            Candidate.source.like('%后台解析%'),
            Candidate.structured_tags == None
        ).count()
        
        if st.button(f"🏷️ 提取标签 ({new_cands_no_tags}人)", disabled=new_cands_no_tags == 0):
            st.info("正在后台提取标签，请稍候...")
            os.system(f"cd {os.path.dirname(os.path.abspath(__file__))} && python3 extract_tags.py candidates &")
            st.success("已在后台启动标签提取")
    
    with op_col2:
        # 复制附件
        if st.button("📄 复制简历附件"):
            import shutil
            RESUMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "resumes")
            os.makedirs(RESUMES_DIR, exist_ok=True)
            
            copied = 0
            for task in db.query(ResumeTask).filter(ResumeTask.status == 'done').all():
                if not task.candidate_id:
                    continue
                cand = db.query(Candidate).filter(Candidate.id == task.candidate_id).first()
                if not cand or not os.path.exists(task.file_path):
                    continue
                dest = os.path.join(RESUMES_DIR, f"{cand.id}_{task.file_name}")
                if not os.path.exists(dest):
                    shutil.copy2(task.file_path, dest)
                    copied += 1
            
            st.success(f"✅ 已复制 {copied} 个简历附件")
    
    with op_col3:
        if failed_count > 0:
            if st.button(f"🔁 重试失败 ({failed_count})", type="secondary"):
                for task in db.query(ResumeTask).filter(ResumeTask.status == 'failed').all():
                    task.status = 'pending'
                    task.error_message = None
                    task.started_at = None
                db.commit()
                st.success(f"已重置 {failed_count} 个失败任务")
                st.rerun()
    
    # 清理按钮
    if done_count > 0:
        if st.button("🗑️ 清理已完成记录"):
            db.query(ResumeTask).filter(ResumeTask.status == 'done').delete()
            db.commit()
            st.success("已清理完成记录")
            st.rerun()

# ---------------- PROMPT CONFIG ----------------
elif page == "提示词配置":
    from prompt_config_module import render_prompt_config
    render_prompt_config()

# ---------------- DASHBOARD ----------------
elif page == "数据分析":
    title_col, refresh_col = st.columns([6, 1])
    with title_col:
        st.title("📊 数据分析")
    with refresh_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 刷新", key="dashboard_refresh", use_container_width=True):
            st.rerun()
    
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
    
    # --- 大学分布 & 历史公司分布 ---
    st.divider()
    univ_col, hist_company_col = st.columns(2)
    
    with univ_col:
        st.markdown("### 🎓 大学分布 (Top 20)")
        
        # 从 education_details 提取学校
        all_candidates = db.query(Candidate).filter(
            Candidate.education_details != None
        ).all()
        
        school_counter = {}
        for cand in all_candidates:
            if cand.education_details and isinstance(cand.education_details, list):
                for edu in cand.education_details:
                    school = edu.get('school', '') or ''
                    school = school.strip()
                    # 清理特殊字符
                    if school and school[0] in '·、-':
                        school = school[1:].strip()
                    if school and len(school) >= 2:
                        school_counter[school] = school_counter.get(school, 0) + 1
        
        # 排序取前20
        top_schools = sorted(school_counter.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if top_schools:
            df_school = pd.DataFrame(top_schools, columns=['学校', '人数'])
            df_school = df_school.sort_values('人数', ascending=True)
            
            fig_school = px.bar(df_school, x='人数', y='学校', orientation='h', text='人数',
                               color_discrete_sequence=['#4CAF50'])  # 绿色
            fig_school.update_layout(height=500, yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            fig_school.update_traces(textposition='outside')
            st.plotly_chart(fig_school, use_container_width=True)
        else:
            st.info("暂无教育数据")
    
    with hist_company_col:
        st.markdown("### 🏢 历史公司分布 (Top 20)")
        
        # 从 work_experiences 提取所有历史公司
        hist_company_counter = {}
        for cand in all_candidates:
            if cand.work_experiences and isinstance(cand.work_experiences, list):
                for work in cand.work_experiences:
                    company = work.get('company', '') or ''
                    company = company.strip()
                    if company and len(company) >= 2:
                        hist_company_counter[company] = hist_company_counter.get(company, 0) + 1
        
        # 排序取前20
        top_hist_companies = sorted(hist_company_counter.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if top_hist_companies:
            df_hist = pd.DataFrame(top_hist_companies, columns=['公司', '人数'])
            df_hist = df_hist.sort_values('人数', ascending=True)
            
            fig_hist = px.bar(df_hist, x='人数', y='公司', orientation='h', text='人数',
                             color_discrete_sequence=['#9C27B0'])  # 紫色
            fig_hist.update_layout(height=500, yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            fig_hist.update_traces(textposition='outside')
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("暂无工作经历数据")
    
    # --- 📡 渠道分析 ---
    st.divider()
    st.markdown("## 📡 渠道分析")
    
    # 查询所有候选人的 source 和联系方式字段
    channel_data = db.query(
        Candidate.source,
        Candidate.phone,
        Candidate.email,
        Candidate.linkedin_url,
        Candidate.github_url,
        Candidate.personal_website,
        Candidate.is_friend
    ).all()
    
    # 统计各渠道人数和联系方式覆盖
    from collections import defaultdict
    channel_stats = defaultdict(lambda: {'total': 0, 'phone': 0, 'email': 0, 'linkedin': 0, 'github': 0, 'website': 0, 'friend': 0, 'any_contact': 0})
    
    for src, phone, email, linkedin, github, website, is_friend in channel_data:
        ch = src if src else '未知'
        channel_stats[ch]['total'] += 1
        has_any = False
        if phone:
            channel_stats[ch]['phone'] += 1
            has_any = True
        if email:
            channel_stats[ch]['email'] += 1
            has_any = True
        if linkedin:
            channel_stats[ch]['linkedin'] += 1
            has_any = True
        if github:
            channel_stats[ch]['github'] += 1
            has_any = True
        if website:
            channel_stats[ch]['website'] += 1
            has_any = True
        if is_friend == 1:
            channel_stats[ch]['friend'] += 1
        if has_any:
            channel_stats[ch]['any_contact'] += 1
    
    # 按人数排序
    sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]['total'], reverse=True)
    
    ch_col1, ch_col2 = st.columns(2)
    
    with ch_col1:
        st.markdown("### 🎯 渠道来源分布")
        ch_names = [ch for ch, _ in sorted_channels]
        ch_counts = [s['total'] for _, s in sorted_channels]
        color_map = {'脉脉': '#1E6FFF', 'github': '#24292e', 'Boss': '#FF6A00', 'linkedin': '#0A66C2'}
        ch_colors = [color_map.get(ch, '#999999') for ch in ch_names]
        
        fig_ch = px.pie(
            names=ch_names, values=ch_counts,
            hole=0.45,
            color_discrete_sequence=ch_colors
        )
        fig_ch.update_traces(textinfo='label+value+percent', textposition='outside')
        fig_ch.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_ch, use_container_width=True)
    
    with ch_col2:
        st.markdown("### 📱 联系方式完备度")
        
        # 构建分组柱状图数据
        bar_data = []
        for ch, stats_d in sorted_channels:
            total = stats_d['total']
            if total > 0:
                bar_data.append({'渠道': ch, '类型': '📱 手机', '覆盖率': round(stats_d['phone'] / total * 100, 1)})
                bar_data.append({'渠道': ch, '类型': '📧 邮箱', '覆盖率': round(stats_d['email'] / total * 100, 1)})
                bar_data.append({'渠道': ch, '类型': '🔗 LinkedIn', '覆盖率': round(stats_d['linkedin'] / total * 100, 1)})
                bar_data.append({'渠道': ch, '类型': '💻 GitHub', '覆盖率': round(stats_d['github'] / total * 100, 1)})
                bar_data.append({'渠道': ch, '类型': '🌐 个人网站', '覆盖率': round(stats_d['website'] / total * 100, 1)})
                bar_data.append({'渠道': ch, '类型': '🤝 加好友', '覆盖率': round(stats_d['friend'] / total * 100, 1)})
        
        if bar_data:
            df_bar = pd.DataFrame(bar_data)
            fig_bar = px.bar(
                df_bar, x='渠道', y='覆盖率', color='类型',
                barmode='group', text='覆盖率',
                color_discrete_map={
                    '📱 手机': '#4CAF50', '📧 邮箱': '#2196F3',
                    '🔗 LinkedIn': '#0A66C2', '💻 GitHub': '#24292e',
                    '🌐 个人网站': '#FF9800', '🤝 加好友': '#E91E63'
                }
            )
            fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_bar.update_layout(
                height=400, yaxis_title='覆盖率 (%)',
                yaxis=dict(range=[0, 105]),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # 明细表格
    table_data = []
    for ch, stats_d in sorted_channels:
        total = stats_d['total']
        completeness = round(stats_d['any_contact'] / total * 100, 1) if total > 0 else 0
        table_data.append({
            '渠道': ch,
            '总人数': total,
            '📱 有手机': stats_d['phone'],
            '📧 有邮箱': stats_d['email'],
            '🔗 有LinkedIn': stats_d['linkedin'],
            '💻 有GitHub': stats_d['github'],
            '🌐 有网站': stats_d['website'],
            '🤝 加好友': stats_d['friend'],
            '✅ 完备率': f"{completeness}%"
        })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    
    # --- 🏅 人才评级分析 ---
    st.divider()
    st.markdown("## 🏅 人才评级分析")
    
    # 查询所有候选人的 source 和 talent_tier
    tier_data = db.query(
        Candidate.source,
        Candidate.talent_tier
    ).all()
    
    # 定义评级顺序和颜色
    TIER_ORDER = ['S', 'A', 'B+', 'B', 'C']
    TIER_COLORS = {'S': '#FFD700', 'A': '#FF4D4F', 'B+': '#FF8C00', 'B': '#1890FF', 'C': '#BFBFBF'}
    TIER_LABELS = {'S': '🏆 S 顶尖', 'A': '⭐ A 优秀', 'B+': '📈 B+ 良好', 'B': '📋 B 一般', 'C': '📎 C 关注'}
    
    # 统计总体分布
    overall_tier = {}
    channel_tier = {}  # {channel: {tier: count}}
    
    for src, tier in tier_data:
        ch = src if src else '未知'
        t = tier if tier and tier in TIER_ORDER else '未评级'
        overall_tier[t] = overall_tier.get(t, 0) + 1
        if ch not in channel_tier:
            channel_tier[ch] = {}
        channel_tier[ch][t] = channel_tier[ch].get(t, 0) + 1
    
    tier_col1, tier_col2 = st.columns(2)
    
    with tier_col1:
        st.markdown("### 📊 总体评级分布")
        
        # 按固定顺序排列
        pie_labels = []
        pie_values = []
        pie_colors = []
        for t in TIER_ORDER:
            if t in overall_tier:
                pie_labels.append(TIER_LABELS.get(t, t))
                pie_values.append(overall_tier[t])
                pie_colors.append(TIER_COLORS.get(t, '#999'))
        if '未评级' in overall_tier:
            pie_labels.append('❓ 未评级')
            pie_values.append(overall_tier['未评级'])
            pie_colors.append('#E0E0E0')
        
        if pie_values:
            fig_tier = px.pie(
                names=pie_labels, values=pie_values,
                hole=0.45,
                color_discrete_sequence=pie_colors
            )
            fig_tier.update_traces(textinfo='label+value+percent', textposition='outside')
            fig_tier.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_tier, use_container_width=True)
    
    with tier_col2:
        st.markdown("### 📡 各渠道人才质量")
        
        # 构建堆叠柱状图
        stack_data = []
        sorted_ch = sorted(channel_tier.items(), key=lambda x: sum(x[1].values()), reverse=True)
        
        for ch, tiers in sorted_ch:
            ch_total = sum(tiers.values())
            for t in TIER_ORDER:
                cnt = tiers.get(t, 0)
                stack_data.append({
                    '渠道': ch,
                    '评级': t,
                    '人数': cnt,
                    '占比': round(cnt / ch_total * 100, 1) if ch_total > 0 else 0
                })
        
        if stack_data:
            df_stack = pd.DataFrame(stack_data)
            fig_stack = px.bar(
                df_stack, x='渠道', y='人数', color='评级',
                barmode='stack', text='人数',
                color_discrete_map=TIER_COLORS,
                category_orders={'评级': TIER_ORDER}
            )
            fig_stack.update_traces(textposition='inside', textfont_size=10)
            fig_stack.update_layout(
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
            )
            st.plotly_chart(fig_stack, use_container_width=True)
    
    # 评级明细表格
    tier_table = []
    for ch, tiers in sorted_ch:
        ch_total = sum(tiers.values())
        row = {'渠道': ch, '总人数': ch_total}
        for t in TIER_ORDER:
            row[t] = tiers.get(t, 0)
        # 计算 S+A 率
        sa_count = tiers.get('S', 0) + tiers.get('A', 0)
        row['S+A率'] = f"{round(sa_count / ch_total * 100, 1)}%" if ch_total > 0 else '0%'
        # 计算 B+以上率
        above_b_plus = sa_count + tiers.get('B+', 0)
        row['B+以上率'] = f"{round(above_b_plus / ch_total * 100, 1)}%" if ch_total > 0 else '0%'
        tier_table.append(row)
    
    if tier_table:
        df_tier_table = pd.DataFrame(tier_table)
        st.dataframe(df_tier_table, use_container_width=True, hide_index=True)
    
    # --- JD 分析 ---
    st.divider()
    st.markdown("## 📋 JD 分析")
    
    # 获取所有JD
    all_jobs = db.query(Job).filter(Job.is_active == 1).all()
    
    # 右侧饼图视觉上偏小，适当增加右列宽度
    jd_col1, jd_col2 = st.columns([1.25, 1.15])
    
    with jd_col1:
        st.markdown("### 🏢 JD发布公司")
        
        # 阿里系公司关键词（用于分组）
        ALIBABA_KEYWORDS = [
            '阿里云', '阿里集团', '阿里健康', '淘天集团', '云智能集团',
            '高德', '钉钉', '平头哥', '通义', '优酷', '虎鲸文娱',
            '阿里控股', '智能互联', '阿里妈妈'
        ]
        
        job_company_counter = {}
        alibaba_sub_counter = {}  # 阿里系子公司统计
        
        for job in all_jobs:
            company = job.company or "未知"
            
            # 检查是否是阿里系公司
            is_alibaba = any(kw in company for kw in ALIBABA_KEYWORDS)
            
            if is_alibaba:
                # 统计阿里系总数
                job_company_counter["🏛️ 阿里集团+阿里云"] = job_company_counter.get("🏛️ 阿里集团+阿里云", 0) + 1
                # 统计子公司
                alibaba_sub_counter[company] = alibaba_sub_counter.get(company, 0) + 1
            else:
                job_company_counter[company] = job_company_counter.get(company, 0) + 1
        
        # 显示所有公司，按数量排序
        all_job_companies = sorted(job_company_counter.items(), key=lambda x: x[1], reverse=True)
        
        if all_job_companies:
            df_jc = pd.DataFrame(all_job_companies, columns=['公司', 'JD数'])
            df_jc = df_jc.sort_values('JD数', ascending=True)
            # 动态调整高度：每个公司约25px，最小350px，最大800px
            chart_height = max(350, min(800, len(all_job_companies) * 25))
            fig_jc = px.bar(df_jc, x='JD数', y='公司', orientation='h', text='JD数',
                           color_discrete_sequence=['#1565C0'])  # 深蓝色
            fig_jc.update_layout(
                height=chart_height, 
                yaxis={'categoryorder': 'total ascending', 'tickfont': {'size': 12}},
                showlegend=False
            )
            fig_jc.update_traces(textposition='outside', textfont_size=12)
            st.plotly_chart(fig_jc, use_container_width=True)
            
            # 阿里系子公司明细 - 始终展开，浅蓝色
            if alibaba_sub_counter:
                st.markdown(f"##### 📊 阿里集团+阿里云 子公司明细 ({sum(alibaba_sub_counter.values())} 个职位)")
                alibaba_subs = sorted(alibaba_sub_counter.items(), key=lambda x: x[1], reverse=True)[:8]
                df_sub = pd.DataFrame(alibaba_subs, columns=['子公司', '职位数'])
                df_sub = df_sub.sort_values('职位数', ascending=True)
                
                # 创建 mini 条形图 - 浅蓝色
                fig_sub = px.bar(df_sub, x='职位数', y='子公司', orientation='h', text='职位数',
                                color_discrete_sequence=['#64B5F6'])  # 浅蓝色
                fig_sub.update_layout(
                    height=min(280, len(alibaba_subs) * 32 + 40),
                    margin=dict(l=0, r=0, t=5, b=5),
                    yaxis={'categoryorder': 'total ascending', 'tickfont': {'size': 12}},
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title=None
                )
                fig_sub.update_traces(textposition='outside', textfont_size=12)  # 统一12px
                st.plotly_chart(fig_sub, use_container_width=True)
                
                # 如果还有更多子公司，显示提示
                if len(alibaba_sub_counter) > 8:
                    st.caption(f"还有 {len(alibaba_sub_counter) - 8} 个其他子公司...")
        else:
            st.info("暂无JD数据")
    
    with jd_col2:
        st.markdown("### 👤 职位大类分布")
        
        # role_type 合并规则
        ROLE_MERGE = {
            "算法工程师": "🔬 算法岗",
            "算法专家": "🔬 算法岗",
            "算法研究员": "🔬 算法岗",
            "研究员": "🔬 算法岗",
            "工程开发": "💻 工程岗",
            "运维/SRE": "💻 工程岗",
            "数据工程师": "💻 工程岗",
            "产品经理": "🎯 产品岗",
            "解决方案架构师": "🏗️ 架构岗",
            "系统架构师": "🏗️ 架构岗",
            "架构师": "🏗️ 架构岗",
            "技术管理": "👔 管理岗",
            "技术专家": "🔬 算法岗"
        }
        
        role_counter = {}
        for job in all_jobs:
            if job.structured_tags:
                import json
                try:
                    tags = json.loads(job.structured_tags) if isinstance(job.structured_tags, str) else job.structured_tags
                    role = tags.get("role_type", "其他")
                    merged_role = ROLE_MERGE.get(role, "❓ 其他")
                    role_counter[merged_role] = role_counter.get(merged_role, 0) + 1
                except:
                    pass
        
        if role_counter:
            df_role = pd.DataFrame(list(role_counter.items()), columns=['职位类型', '数量'])
            fig_role = px.pie(df_role, values='数量', names='职位类型', hole=0.4)
            fig_role.update_layout(
                height=560,
                showlegend=True,
                margin=dict(l=10, r=10, t=10, b=70),
                legend=dict(
                    orientation='h',
                    yanchor='top',
                    y=-0.08,
                    xanchor='center',
                    x=0.5
                ),
                uniformtext_minsize=11,
                uniformtext_mode='hide'
            )
            fig_role.update_traces(
                textinfo='value+percent',
                textposition='inside',
                textfont_size=13,
                insidetextorientation='auto'
            )
            st.plotly_chart(fig_role, use_container_width=True)
        else:
            st.info("暂无职位类型数据")
    
    # 技术方向分布
    st.markdown("### 🧠 技术方向分布")
    tech_domain_counter = {}
    for job in all_jobs:
        if job.structured_tags:
            import json
            try:
                tags = json.loads(job.structured_tags) if isinstance(job.structured_tags, str) else job.structured_tags
                domains = tags.get("tech_domain", [])
                if isinstance(domains, list):
                    for domain in domains:
                        tech_domain_counter[domain] = tech_domain_counter.get(domain, 0) + 1
            except:
                pass
    
    if tech_domain_counter:
        top_domains = sorted(tech_domain_counter.items(), key=lambda x: x[1], reverse=True)[:12]
        df_domain = pd.DataFrame(top_domains, columns=['技术方向', 'JD数'])
        
        fig_domain = px.bar(df_domain, x='技术方向', y='JD数', text='JD数',
                           color='JD数', color_continuous_scale='Viridis')
        fig_domain.update_layout(height=300, showlegend=False, coloraxis_showscale=False)
        fig_domain.update_traces(textposition='outside')
        st.plotly_chart(fig_domain, use_container_width=True)
    else:
        st.info("暂无技术方向数据")
    
    # --- 门户转化漏斗 ---
    st.divider()
    st.markdown("## 🔗 门户转化漏斗")
    
    try:
        import hashlib, requests
        PORTAL_BASE = "https://jobs.rupro-consulting.com"
        token = hashlib.sha256('ruproAI'.encode()).hexdigest()
        stats_resp = requests.get(f"{PORTAL_BASE}/api/portal/stats",
                                  cookies={'auth_token': token}, timeout=10)
        
        if stats_resp.status_code == 200 and stats_resp.json().get('success'):
            stats = stats_resp.json()
            funnel = stats['funnel']
            recent = stats['recent_7d']
            top_viewed = stats.get('top_viewed', [])
            
            # 漏斗指标卡片
            fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
            fc1.metric("🏠 门户总数", funnel['total_portals'])
            fc2.metric("📨 已推JD", funnel['portals_with_recs'])
            fc3.metric("👁️ 已打开", funnel['viewed_portals'])
            fc4.metric("💬 有反馈", funnel['total_feedback'])
            fc5.metric("✅ 感兴趣", funnel['interested'])
            fc6.metric("🎯 进面试", funnel['advanced_pipeline'])
            
            # 漏斗图 + 近7天
            funnel_col, recent_col = st.columns([2, 1])
            
            with funnel_col:
                import plotly.graph_objects as go
                
                funnel_stages = ["门户总数", "已推送JD", "已打开", "有反馈", "感兴趣", "进入面试"]
                funnel_values = [
                    funnel['total_portals'],
                    funnel['portals_with_recs'],
                    funnel['viewed_portals'],
                    funnel['total_feedback'],
                    funnel['interested'],
                    funnel['advanced_pipeline'],
                ]
                
                fig_funnel = go.Figure(go.Funnel(
                    y=funnel_stages,
                    x=funnel_values,
                    textinfo="value+percent initial",
                    marker=dict(color=["#3b82f6", "#8b5cf6", "#d4af55", "#f59e0b", "#10b981", "#ef4444"]),
                ))
                fig_funnel.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_funnel, use_container_width=True)
            
            with recent_col:
                st.markdown("#### 📅 近 7 天")
                st.metric("反馈数", recent['feedback'])
                st.metric("感兴趣", recent['interested'])
                st.markdown("---")
                st.markdown("#### 📊 总量")
                st.metric("总访问次数", funnel['total_views'])
                st.metric("不感兴趣", funnel['not_interested'])
            
            # Top 10 最活跃门户
            if top_viewed:
                with st.expander(f"🏆 最活跃门户 Top {len(top_viewed)}", expanded=False):
                    tv_data = []
                    for p in top_viewed:
                        last_visit = p.get('last_visited_at', '')
                        if last_visit:
                            try:
                                from datetime import datetime as dt
                                lv = dt.fromisoformat(last_visit)
                                last_visit = lv.strftime("%m/%d %H:%M")
                            except:
                                pass
                        tv_data.append({
                            "候选人": p['candidate_name'],
                            "访问次数": p['visit_count'],
                            "最后访问": last_visit,
                        })
                    st.dataframe(pd.DataFrame(tv_data), use_container_width=True, hide_index=True)
        else:
            st.warning("门户统计接口返回异常")
    except Exception as e:
        st.caption(f"⚠️ 门户统计加载失败: {e}")

# ---------------- 沟通跟进 ----------------
elif page == "沟通跟进":
    # 标题 + 刷新按钮
    title_col, refresh_col = st.columns([6, 1])
    with title_col:
        st.title("📋 沟通跟进")
    with refresh_col:
        st.markdown("")  # 垂直居中对齐
        if st.button("🔄 刷新", key="followup_refresh", use_container_width=True):
            st.rerun()
    
    db = get_session()
    from datetime import date, timedelta
    
    # ===== 管道概览 =====
    st.markdown("#### 📊 管道概览")
    
    STAGE_LABELS_LOCAL = {
        "new": "🆕 新发现",
        "contacted": "📤 已打招呼",
        "following_up": "🔄 跟进中",
        "replied": "💬 已回复",
        "wechat_connected": "💚 已加微信",
        "in_pipeline": "🎯 面试中",
        "closed": "⏸️ 关闭",
    }
    
    # 统计各阶段人数
    stage_cols = st.columns(7)
    for i, (stage, label) in enumerate(STAGE_LABELS_LOCAL.items()):
        count = db.query(Candidate).filter(Candidate.pipeline_stage == stage).count()
        with stage_cols[i]:
            stage_name = label.split(" ", 1)[1] if " " in label else label
            st.markdown(f"<div style='text-align:center'><span style='font-size:20px;font-weight:600;color:#333'>{count}</span><br><span style='font-size:12px;color:#888'>{stage_name}</span></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # ===== 今日需跟进 =====
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    followup_candidates = db.query(Candidate).filter(
        Candidate.pipeline_stage.notin_(['closed', 'new']),
        Candidate.follow_up_date.isnot(None),
        Candidate.follow_up_date <= today_str
    ).order_by(Candidate.follow_up_date.asc()).all()
    
    st.markdown(f"#### 🔔 策略跟进 ({len(followup_candidates)}人)")
    
    if followup_candidates:
        for cand in followup_candidates:
            days_overdue = 0
            if cand.follow_up_date:
                try:
                    fu_date = datetime.strptime(cand.follow_up_date, "%Y-%m-%d").date()
                    days_overdue = (today - fu_date).days
                except:
                    pass
            
            overdue_badge = f"🔴 逾期{days_overdue}天" if days_overdue > 0 else "🟢 今天"
            stage_label = STAGE_LABELS_LOCAL.get(cand.pipeline_stage, cand.pipeline_stage)
            
            # 获取沟通次数
            logs = cand.communication_logs or []
            if isinstance(logs, str):
                try:
                    logs = json.loads(logs)
                except:
                    logs = []
            outbound_count = sum(1 for l in logs if isinstance(l, dict) and l.get('direction') == 'outbound')
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                with col1:
                    st.markdown(f"**{cand.name}** {overdue_badge}")
                    st.caption(f"{cand.current_company or ''} · {cand.current_title or ''}")
                with col2:
                    st.markdown(f"{stage_label}")
                    st.caption(f"已联系 {outbound_count} 次")
                with col3:
                    if cand.wechat_id:
                        st.markdown(f"💚 微信: {cand.wechat_id}")
                    if cand.phone:
                        st.markdown(f"📱 {cand.phone}")
                with col4:
                    # 阶段流转按钮
                    btn_cols = st.columns(4)
                    with btn_cols[0]:
                        if st.button("💬 已回复", key=f"stage_replied_{cand.id}", use_container_width=True):
                            cand.pipeline_stage = 'replied'
                            cand.follow_up_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                            db.commit()
                            st.rerun()
                    with btn_cols[1]:
                        if st.button("🔄 再跟进", key=f"stage_followup_{cand.id}", use_container_width=True):
                            cand.pipeline_stage = 'following_up'
                            cand.follow_up_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                            db.commit()
                            st.rerun()
                    with btn_cols[2]:
                        if st.button("💚 加微信", key=f"stage_wechat_{cand.id}", use_container_width=True):
                            cand.pipeline_stage = 'wechat_connected'
                            cand.follow_up_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                            db.commit()
                            st.rerun()
                    with btn_cols[3]:
                        if st.button("⏸️ 关闭", key=f"stage_close_{cand.id}", use_container_width=True):
                            cand.pipeline_stage = 'closed'
                            cand.follow_up_date = None
                            db.commit()
                            st.rerun()
    else:
        st.info("今天没有需要策略跟进的候选人")
    
    st.divider()
    st.markdown("#### 📅 预约跟进（手动排期）")
    
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    week_end = today + timedelta(days=7)
    week_end_str = week_end.strftime("%Y-%m-%d")
    
    # 获取所有有预约的候选人
    scheduled_candidates = db.query(Candidate).filter(
        Candidate.scheduled_contact_date != None,
        Candidate.scheduled_contact_date != ""
    ).all()
    
    # 计算时间范围
    next_week_start = today + timedelta(days=8)  # 本周之后
    next_week_end = today + timedelta(days=14)   # 下周结束
    quarter_end = today + timedelta(days=90)     # 3个月
    
    # 分类统计
    today_pending = []
    tomorrow_pending = []
    week_pending = []
    next_week_pending = []  # 新增：下周
    quarter_pending = []     # 新增：下季度
    overdue_pending = []
    recent_completed = []
    
    for cand in scheduled_candidates:
        sched_date_str = cand.scheduled_contact_date
        try:
            sched_date = datetime.strptime(sched_date_str, "%Y-%m-%d").date()
        except:
            continue
        
        # 判断是否已完成：预约日期当天或之后有沟通记录
        is_completed = False
        if cand.last_communication_at:
            last_comm_date = cand.last_communication_at.date() if hasattr(cand.last_communication_at, 'date') else cand.last_communication_at
            if last_comm_date >= sched_date:
                is_completed = True
        
        if is_completed:
            # 最近7天完成的
            if sched_date >= today - timedelta(days=7):
                recent_completed.append((cand, sched_date))
        else:
            # 未完成的分类
            if sched_date < today:
                overdue_pending.append((cand, sched_date))
            elif sched_date == today:
                today_pending.append((cand, sched_date))
            elif sched_date == tomorrow:
                tomorrow_pending.append((cand, sched_date))
            elif sched_date <= week_end:
                week_pending.append((cand, sched_date))
            elif sched_date <= next_week_end:
                next_week_pending.append((cand, sched_date))
            elif sched_date <= quarter_end:
                quarter_pending.append((cand, sched_date))
    
    # 日期筛选 Tab
    tab_labels = [
        f"🔴 今天 ({len(today_pending)})",
        f"📅 明天 ({len(tomorrow_pending)})",
        f"📆 本周 ({len(week_pending)})",
        f"📆 下周 ({len(next_week_pending)})",
        f"🗓️ 下季度 ({len(quarter_pending)})",
        f"⚠️ 逾期 ({len(overdue_pending)})",
        f"✅ 已完成 ({len(recent_completed)})"
    ]
    tabs = st.tabs(tab_labels)
    
    def render_followup_list(items, show_date=True, is_completed=False):
        """渲染跟进列表"""
        from datetime import date, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        if not items:
            st.caption("暂无记录")
            return
        
        for cand, sched_date in items:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    # 状态图标 + 候选人信息
                    status_icon = "✅" if is_completed else "○"
                    company = cand.current_company or "-"
                    title = (cand.current_title or "-")[:15]
                    st.markdown(f"{status_icon} **{cand.name}** · {company} · {title}")
                    
                    # 日期信息（无日历符号）
                    if show_date:
                        if sched_date == today:
                            date_label = ""  # 今天tab不需要显示
                        elif sched_date == tomorrow:
                            date_label = ""  # 明天tab不需要显示
                        elif sched_date < today:
                            days_ago = (today - sched_date).days
                            date_label = f"⚠️ 逾期{days_ago}天"
                        else:
                            date_label = f"{sched_date.month}/{sched_date.day}"
                        
                        if is_completed and cand.last_communication_at:
                            comm_time = cand.last_communication_at.strftime("%m/%d %H:%M")
                            st.caption(f"完成于 {comm_time}")
                        elif date_label:
                            st.caption(f"{date_label}")
                with col2:
                    # 显示最新2条沟通记录（按时间倒序）
                    if cand.communication_logs and len(cand.communication_logs) > 0:
                        # 按时间倒序排序
                        sorted_logs = sorted(cand.communication_logs, key=lambda x: x.get('time', ''), reverse=True)
                        # 取最新2条
                        for log in sorted_logs[:2]:
                            log_content = log.get('content', '')[:40]
                            if len(log.get('content', '')) > 40:
                                log_content += '...'
                            log_time = log.get('time', '')[:10]  # 只显示日期部分
                            st.caption(f"💬 {log_time}: {log_content}")
                    else:
                        st.caption("暂无沟通记录")
                
                with col3:
                    # 操作按钮
                    if not is_completed:
                        bc1, bc2, bc3, bc4 = st.columns(4)
                        if bc1.button("📄", key=f"fu_view_{cand.id}_{sched_date}", help="查看详情"):
                            st.session_state.selected_candidate_id = cand.id
                            st.session_state.view_mode = 'detail'
                            st.session_state.from_followup = True  # 标记来源
                            st.session_state.nav_page = '人才库管理'
                            st.rerun()
                        
                        # 完成按钮 - 使用popover支持"仅完成"或"完成并预约下次"
                        with bc2.popover("✅", help="标记完成"):
                            from datetime import datetime as dt_module
                            st.caption("完成本次跟进")
                            
                            # 仅完成
                            if st.button("✅ 仅标记完成", key=f"fu_done_only_{cand.id}", use_container_width=True):
                                now_str = dt_module.now().strftime("%Y-%m-%d %H:%M")
                                new_log = {"time": now_str, "content": "已完成跟进"}
                                if cand.communication_logs:
                                    cand.communication_logs = cand.communication_logs + [new_log]
                                else:
                                    cand.communication_logs = [new_log]
                                cand.last_communication_at = dt_module.now()
                                db.commit()
                                st.toast(f"✅ 已标记 {cand.name} 完成")
                                st.rerun()
                            
                            st.divider()
                            st.caption("完成并预约下次沟通")
                            
                            # 快捷预约选项
                            from datetime import date, timedelta
                            today_date = date.today()
                            next_week = today_date + timedelta(days=7)
                            next_month = today_date + timedelta(days=30)
                            next_quarter = today_date + timedelta(days=90)
                            
                            qc1, qc2 = st.columns(2)
                            if qc1.button("📅 下周", key=f"fu_done_week_{cand.id}", use_container_width=True):
                                now_str = dt_module.now().strftime("%Y-%m-%d %H:%M")
                                new_log = {"time": now_str, "content": "已完成跟进，预约下周继续"}
                                if cand.communication_logs:
                                    cand.communication_logs = cand.communication_logs + [new_log]
                                else:
                                    cand.communication_logs = [new_log]
                                cand.last_communication_at = dt_module.now()
                                cand.scheduled_contact_date = next_week.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"✅ 已完成 {cand.name}，预约下周跟进")
                                st.rerun()
                            if qc2.button("📅 下月", key=f"fu_done_month_{cand.id}", use_container_width=True):
                                now_str = dt_module.now().strftime("%Y-%m-%d %H:%M")
                                new_log = {"time": now_str, "content": "已完成跟进，预约下月继续"}
                                if cand.communication_logs:
                                    cand.communication_logs = cand.communication_logs + [new_log]
                                else:
                                    cand.communication_logs = [new_log]
                                cand.last_communication_at = dt_module.now()
                                cand.scheduled_contact_date = next_month.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"✅ 已完成 {cand.name}，预约下月跟进")
                                st.rerun()
                            
                            if st.button("🗓️ 下季度", key=f"fu_done_quarter_{cand.id}", use_container_width=True):
                                now_str = dt_module.now().strftime("%Y-%m-%d %H:%M")
                                new_log = {"time": now_str, "content": "已完成跟进，预约下季度继续"}
                                if cand.communication_logs:
                                    cand.communication_logs = cand.communication_logs + [new_log]
                                else:
                                    cand.communication_logs = [new_log]
                                cand.last_communication_at = dt_module.now()
                                cand.scheduled_contact_date = next_quarter.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"✅ 已完成 {cand.name}，预约3个月后跟进")
                                st.rerun()
                            
                            # 自定义日期
                            max_date = today_date + timedelta(days=365)
                            dc1, dc2 = st.columns([2, 1])
                            sel_next_date = dc1.date_input("下次日期", value=next_month, min_value=today_date, max_value=max_date, key=f"fu_done_date_{cand.id}", label_visibility="collapsed")
                            if dc2.button("✓", key=f"fu_done_conf_{cand.id}", type="primary"):
                                now_str = dt_module.now().strftime("%Y-%m-%d %H:%M")
                                new_log = {"time": now_str, "content": f"已完成跟进，预约{sel_next_date}继续"}
                                if cand.communication_logs:
                                    cand.communication_logs = cand.communication_logs + [new_log]
                                else:
                                    cand.communication_logs = [new_log]
                                cand.last_communication_at = dt_module.now()
                                cand.scheduled_contact_date = sel_next_date.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"✅ 已完成 {cand.name}，预约{sel_next_date}跟进")
                                st.rerun()
                        
                        # 延期按钮 - 不标记完成，只修改预约日期
                        with bc3.popover("⏰", help="延期"):
                            from datetime import date, timedelta
                            today_date = date.today()
                            tomorrow = today_date + timedelta(days=1)
                            day_after = today_date + timedelta(days=2)
                            days_until_monday = (7 - today_date.weekday()) % 7
                            if days_until_monday == 0:
                                days_until_monday = 7
                            next_monday = today_date + timedelta(days=days_until_monday)
                            
                            st.caption("延期跟进（不标记完成）")
                            
                            dc1, dc2, dc3 = st.columns(3)
                            if dc1.button("明天", key=f"fu_delay_tom_{cand.id}", use_container_width=True):
                                cand.scheduled_contact_date = tomorrow.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"⏰ {cand.name} 已延期到明天")
                                st.rerun()
                            if dc2.button("后天", key=f"fu_delay_da_{cand.id}", use_container_width=True):
                                cand.scheduled_contact_date = day_after.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"⏰ {cand.name} 已延期到后天")
                                st.rerun()
                            if dc3.button("周一", key=f"fu_delay_mon_{cand.id}", use_container_width=True):
                                cand.scheduled_contact_date = next_monday.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"⏰ {cand.name} 已延期到周一")
                                st.rerun()
                        
                        # 取消预约
                        if bc4.button("✕", key=f"fu_clr_{cand.id}_{sched_date}", help="取消预约"):
                            cand.scheduled_contact_date = None
                            db.commit()
                            st.rerun()
                    else:
                        # 已完成的显示查看详情 + 继续沟通
                        bc1, bc2 = st.columns(2)
                        if bc1.button("📄", key=f"fu_view_{cand.id}_{sched_date}", help="查看详情"):
                            st.session_state.selected_candidate_id = cand.id
                            st.session_state.view_mode = 'detail'
                            st.session_state.from_followup = True
                            st.session_state.nav_page = '人才库管理'
                            st.rerun()
                        # 继续沟通 - popover 方式设置新预约时间
                        with bc2.popover("📅", help="继续沟通"):
                            from datetime import date, timedelta
                            today = date.today()
                            tomorrow = today + timedelta(days=1)
                            day_after = today + timedelta(days=2)
                            days_until_monday = (7 - today.weekday()) % 7
                            if days_until_monday == 0:
                                days_until_monday = 7
                            next_monday = today + timedelta(days=days_until_monday)
                            
                            st.caption("设置下次沟通时间")
                            
                            # 紧凑三列快捷按钮
                            c1, c2, c3 = st.columns(3)
                            if c1.button("明天", key=f"fu_pop_tom_{cand.id}"):
                                cand.scheduled_contact_date = tomorrow.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"📅 已预约 {cand.name} 明天跟进")
                                st.rerun()
                            if c2.button("后天", key=f"fu_pop_da_{cand.id}"):
                                cand.scheduled_contact_date = day_after.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"📅 已预约 {cand.name} 后天跟进")
                                st.rerun()
                            if c3.button("周一", key=f"fu_pop_mon_{cand.id}"):
                                cand.scheduled_contact_date = next_monday.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"📅 已预约 {cand.name} 下周一跟进")
                                st.rerun()
                            
                            # 自定义日期
                            max_date = today + timedelta(days=90)
                            dc1, dc2 = st.columns([2, 1])
                            sel_date = dc1.date_input("预约日期", value=tomorrow, min_value=today, max_value=max_date, key=f"fu_pop_date_{cand.id}", label_visibility="collapsed")
                            if dc2.button("✓", key=f"fu_pop_conf_{cand.id}", type="primary"):
                                cand.scheduled_contact_date = sel_date.strftime("%Y-%m-%d")
                                db.commit()
                                st.toast(f"📅 已预约 {cand.name} {sel_date} 跟进")
                                st.rerun()
    
    # Tab 1: 今天
    with tabs[0]:
        render_followup_list(sorted(today_pending, key=lambda x: x[0].name))
    
    # Tab 2: 明天
    with tabs[1]:
        render_followup_list(sorted(tomorrow_pending, key=lambda x: x[0].name))
    
    # Tab 3: 本周
    with tabs[2]:
        render_followup_list(sorted(week_pending, key=lambda x: x[1]))
    
    # Tab 4: 下周
    with tabs[3]:
        render_followup_list(sorted(next_week_pending, key=lambda x: x[1]))
    
    # Tab 5: 下季度
    with tabs[4]:
        if quarter_pending:
            st.caption(f"未来3个月内预约的跟进（{len(quarter_pending)}人）")
        render_followup_list(sorted(quarter_pending, key=lambda x: x[1]))
    
    # Tab 6: 逾期
    with tabs[5]:
        if overdue_pending:
            st.warning(f"有 {len(overdue_pending)} 个候选人预约已过期但未联系")
            # 批量清除按钮
            if st.button("🗑️ 清除所有逾期预约", type="secondary"):
                for cand, _ in overdue_pending:
                    cand.scheduled_contact_date = None
                db.commit()
                st.toast(f"已清除 {len(overdue_pending)} 个逾期预约")
                st.rerun()
        render_followup_list(sorted(overdue_pending, key=lambda x: x[1]))
    
    # Tab 7: 已完成
    with tabs[6]:
        st.caption("最近7天完成的跟进")
        render_followup_list(sorted(recent_completed, key=lambda x: x[1], reverse=True), is_completed=True)

# ---------------- CANDIDATES ----------------
elif page == "人才库管理":
    
    _perf_page_enter = _time.time()
    _perf_logger.debug(f"进入人才库管理页 — 距脚本启动 {_perf_page_enter - _PERF_SCRIPT_START:.3f}s")
    
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
            # === 第一行：返回按钮 ===
            if st.session_state.get('from_followup'):
                bc1, bc2 = st.columns([1, 4])
                if bc1.button("← 返回跟进清单", key="back_to_followup_btn"):
                    st.session_state.from_followup = False
                    st.session_state.view_mode = 'list'
                    st.session_state.nav_page = '沟通跟进'
                    st.rerun()
                if bc2.button("← 返回人才列表", key="back_to_talent_list_btn"):
                    st.session_state.from_followup = False
                    back_to_list()
            else:
                if st.button("← 返回列表", key="back_to_list_btn"):
                    back_to_list()
            
            # === 第二行：姓名（左）+ 状态徽章（右）===
            name_col, status_col = st.columns([5, 3])
            
            with name_col:
                # 显示预约徽章
                schedule_badge = ""
                if cand.scheduled_contact_date:
                    from datetime import date
                    try:
                        sched_date = datetime.strptime(cand.scheduled_contact_date, "%Y-%m-%d").date()
                        today = date.today()
                        if sched_date == today:
                            schedule_badge = "🔴今天"
                        elif sched_date < today:
                            schedule_badge = f"⚪{sched_date.month}/{sched_date.day}"
                        else:
                            schedule_badge = f"📅{sched_date.month}/{sched_date.day}"
                    except:
                        pass
                # 人才分级徽章
                tier_badge_map = {
                    'S': '🔴S', 'A+': '🟠A+', 'A': '🟠A', 'B+': '🟡B+', 'B': '🟡B', 'C': '🟢C'
                }
                tier_badge = tier_badge_map.get(cand.talent_tier, '') if cand.talent_tier else ''
                st.markdown(f"## {tier_badge} {cand.name} {schedule_badge}")
            
            with status_col:
                # 管道阶段徽章
                stage_badge_map = {
                    "new": "", 
                    "contacted": "📤已打招呼", 
                    "following_up": "🔄跟进中", 
                    "replied": "💬已回复",
                    "wechat_connected": "💚已加微信", 
                    "in_pipeline": "🎯面试中", 
                    "closed": "⏸️关闭",
                }
                pipeline_badge = stage_badge_map.get(cand.pipeline_stage or 'new', '')
                
                # 跟进日期提示
                followup_badge = ""
                if cand.follow_up_date:
                    try:
                        fu_date = datetime.strptime(cand.follow_up_date, "%Y-%m-%d").date()
                        from datetime import date as date_cls
                        today_d = date_cls.today()
                        if fu_date < today_d:
                            days_late = (today_d - fu_date).days
                            followup_badge = f"🔴逾期{days_late}天"
                        elif fu_date == today_d:
                            followup_badge = "🟡今天跟进"
                        else:
                            followup_badge = f"📅{fu_date.month}/{fu_date.day}跟进"
                    except:
                        pass
                
                st.markdown(f"<div style='text-align:right;margin-top:16px'><span style='font-size:13px'>{pipeline_badge}</span> <span style='font-size:12px;color:#e74c3c'>{followup_badge}</span></div>", unsafe_allow_html=True)
            
            # === 第三行：公司·职位·基本信息（左）+ 操作按钮（右）===
            info_col, btn_col = st.columns([5, 3])
            
            with info_col:
                company_str = cand.current_company or "-"
                title_str = cand.current_title[:30] if cand.current_title else "-"
                loc_str = cand.expect_location or "-"
                edu_str = cand.education_level or "-"
                exp_str = f"{cand.experience_years}年" if cand.experience_years else "-"
                age_str = f"{cand.age}岁" if cand.age else "-"
                st.markdown(f"🏢 **{company_str}** · {title_str} │ 📍 {loc_str} │ 🎓 {edu_str} │ ⏳ {exp_str} │ {age_str}")
            
            with btn_col:
                # 好友星星 + 预约 + 标签更新
                is_friend = cand.is_friend == 1
                star_icon = "⭐" if is_friend else "☆"
                star_label = "已关注" if is_friend else "关注"
                
                ac1, ac2, ac3, ac4, ac5 = st.columns(5)
                if ac5.button("🔄", key="refresh_detail", help="刷新"):
                    st.cache_data.clear()
                    st.rerun()
                if ac1.button(f"{star_icon} {star_label}", key="toggle_friend_star"):
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
                
                # 预约沟通
                with ac2.popover("📅", help="预约沟通"):
                    from datetime import date, timedelta
                    today = date.today()
                    tomorrow = today + timedelta(days=1)
                    day_after = today + timedelta(days=2)
                    days_until_monday = (7 - today.weekday()) % 7
                    if days_until_monday == 0:
                        days_until_monday = 7
                    next_monday = today + timedelta(days=days_until_monday)
                    
                    # 显示当前预约状态
                    if cand.scheduled_contact_date:
                        st.caption(f"⚡ 已预约: {cand.scheduled_contact_date}")
                    
                    # 紧凑三列快捷按钮
                    c1, c2, c3 = st.columns(3)
                    if c1.button("明天", key="d_pop_tom"):
                        cand.scheduled_contact_date = tomorrow.strftime("%Y-%m-%d")
                        db.commit()
                        st.rerun()
                    if c2.button("后天", key="d_pop_da"):
                        cand.scheduled_contact_date = day_after.strftime("%Y-%m-%d")
                        db.commit()
                        st.rerun()
                    if c3.button("周一", key="d_pop_mon"):
                        cand.scheduled_contact_date = next_monday.strftime("%Y-%m-%d")
                        db.commit()
                        st.rerun()
                    
                    # 自定义日期 - 紧凑版
                    max_date = today + timedelta(days=90)
                    dc1, dc2 = st.columns([2, 1])
                    sel_date = dc1.date_input("预约日期", value=tomorrow, min_value=today, max_value=max_date, key="d_pop_date", label_visibility="collapsed")
                    if dc2.button("✓", key="d_pop_conf", type="primary"):
                        cand.scheduled_contact_date = sel_date.strftime("%Y-%m-%d")
                        db.commit()
                        st.rerun()
                    
                    # 清除预约
                    if cand.scheduled_contact_date:
                        if st.button("🗑️ 清除", key="d_pop_clr", use_container_width=True):
                            cand.scheduled_contact_date = None
                            db.commit()
                            st.rerun()
                
                # 重新评级按钮
                with ac4.popover("🏅", help="重新评级"):
                    st.markdown("**🔄 重新评级**")
                    st.caption("根据当前数据（工作经历、学校、GitHub、论文等）重新计算分级")
                    
                    tier_map = {'S': '🔴 S', 'A+': '🟠 A+', 'A': '🟠 A', 'B+': '🟡 B+', 'B': '🟡 B', 'C': '🟢 C'}
                    current_tier = cand.talent_tier or '未分级'
                    st.markdown(f"**当前评级：** {tier_map.get(current_tier, current_tier)}")
                    
                    st.divider()
                    
                    if st.button("🚀 开始评级", key="re_tier_btn", type="primary", use_container_width=True):
                        with st.spinner("评级中..."):
                            try:
                                import requests as req
                                resp = req.post(f"http://localhost:8502/api/candidate/{cand.id}/re-tier", timeout=10)
                                result = resp.json()
                                if result.get('success'):
                                    st.success(f"✅ {result['message']}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result.get('detail', '评级失败')}")
                            except Exception as e:
                                st.error(f"❌ 评级失败: {e}")
                
                # 更新标签按钮
                with ac3.popover("🏷️", help="更新标签"):
                    st.markdown("**🔄 更新结构化标签**")
                    st.caption("根据当前简历和工作经历，使用AI重新提取标签")
                    
                    # 显示当前标签摘要
                    if cand.structured_tags:
                        try:
                            current_tags = json.loads(cand.structured_tags) if isinstance(cand.structured_tags, str) else cand.structured_tags
                            st.markdown("**当前标签：**")
                            if current_tags.get("tech_domain"):
                                st.caption(f"📂 技术方向: {', '.join(current_tags.get('tech_domain', []))}")
                            if current_tags.get("core_specialty"):
                                st.caption(f"⭐ 核心专长: {', '.join(current_tags.get('core_specialty', []))}")
                            if current_tags.get("role_type"):
                                st.caption(f"👤 岗位类型: {current_tags.get('role_type', '')}")
                        except:
                            st.caption("当前标签解析失败")
                    else:
                        st.caption("⚠️ 暂无标签")
                    
                    st.divider()
                    
                    if st.button("🚀 开始更新标签", key="update_cand_tags_btn", type="primary", use_container_width=True):
                        with st.spinner("AI 正在分析..."):
                            try:
                                # 使用extract_tags模块的逻辑
                                from openai import OpenAI
                                import os
                                from dotenv import load_dotenv
                                
                                env_path = os.path.join(os.path.dirname(__file__), 'config.env')
                                if os.path.exists(env_path):
                                    load_dotenv(env_path, override=True)
                                
                                API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('OPENAI_API_KEY')
                                llm_client = OpenAI(
                                    api_key=API_KEY,
                                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                                )
                                
                                # 构建候选人信息
                                resume_text = cand.ai_summary or cand.raw_resume_text or ''
                                work_exp_text = ""
                                if cand.work_experiences:
                                    for w in cand.work_experiences[:3]:
                                        work_exp_text += f"\n{w.get('company', '')} - {w.get('title', '')}: {w.get('description', '')[:200]}"
                                
                                TAG_SCHEMA = """
## 标签体系说明
1. tech_domain (技术方向) - 多选，非技术岗可为空: 【AI】大模型/LLM, Agent/智能体, NLP, 多模态, 语音, CV, 推荐系统, 搜索, AI Infra, 具身智能, 垂直应用 【工程】客户端开发, 后端开发, 前端开发, 基础架构/Infra, 音视频 (不要用"其他")
2. core_specialty (核心专长) - 多选1-2个，非技术岗可为空: 【AI】语音合成, 语音识别, 多模态理解, 多模态生成, 图像视频生成, 推荐系统, 搜索排序, Agent开发, 对话系统, AI客服, 代码生成 【工程】IM/即时通讯, 跨端框架, 客户端基础架构, 音视频引擎, 微服务架构, DevOps
3. tech_skills (技术技能) - 多选1-3个，非技术岗可为空: 【AI】预训练, SFT微调, RLHF/对齐, 推理加速, 模型压缩/量化, 分布式训练, RAG/知识库, 算子优化, 框架开发 【工程】跨端开发, 性能优化, 高并发, 架构设计
4. role_type (岗位类型) - 单选: 算法工程师, 算法专家, 算法研究员, 客户端工程师, 后端工程师, 前端工程师, 架构师, 工程开发, 解决方案架构师, 产品经理, 技术管理, 研究员, 运营管理, 项目管理, 商务/销售, 人力资源, 其他非技术
5. role_orientation (角色定位) - 多选: Research型, Applied/落地型, Platform/Infra型, Tool/Agent Builder, Tech Lead, 纯IC, 团队管理
6. tech_stack (技术栈) - 多选，非技术岗可为空: Python, C++, Java, Go, Rust, Swift, Kotlin, TypeScript, PyTorch, TensorFlow, QT, Flutter, K8s, CUDA
7. industry_exp (行业背景) - 多选: 互联网大厂, AI独角兽, 云厂商, 芯片/硬件, 外企, 学术背景, 教育培训, 物流/电商, IM/通信厂商
8. seniority (职级层次) - 单选: 初级(0-3年), 中级(3-5年), 资深(5-10年), 专家(10年+), 管理层
"""
                                
                                prompt = f"""请从以下候选人信息中提取结构化标签。

{TAG_SCHEMA}

【候选人信息】
姓名: {cand.name or ''}
当前职位: {cand.current_title or ''}
当前公司: {cand.current_company or ''}
工作年限: {cand.experience_years or 0}年
学历: {cand.education_level or ''}
简历/画像: {resume_text[:1500]}
工作经历: {work_exp_text[:500]}

⚠️ 注意：如果候选人是非技术岗位（如运营、项目管理、商务等），tech_domain/core_specialty/tech_skills/tech_stack可以为空数组。

请输出JSON格式，只输出JSON:
{{
  "tech_domain": ["技术方向"],
  "core_specialty": ["核心专长"],
  "tech_skills": ["技术技能"],
  "role_type": "岗位类型",
  "role_orientation": ["角色定位"],
  "tech_stack": ["技术栈"],
  "industry_exp": ["行业背景"],
  "seniority": "职级层次"
}}"""
                                
                                response = llm_client.chat.completions.create(
                                    model="qwen-plus",
                                    messages=[{"role": "user", "content": prompt}],
                                    temperature=0.1
                                )
                                content = response.choices[0].message.content.strip()
                                
                                # 清理markdown标记
                                if content.startswith("```"):
                                    content = content.split("```")[1]
                                    if content.startswith("json"):
                                        content = content[4:]
                                
                                new_tags = json.loads(content)
                                cand.structured_tags = json.dumps(new_tags, ensure_ascii=False)
                                db.commit()
                                
                                # 保存新标签到session_state用于显示
                                st.session_state['updated_tags'] = new_tags
                                st.session_state['tags_updated'] = True
                                st.success("✅ 标签已更新！")
                                st.json(new_tags)
                            except Exception as e:
                                st.error(f"更新失败: {e}")
            
            
            # === 第四行：技能标签（仅显示，编辑在"编辑基础信息"中）===
            current_skills = cand.skills if cand.skills and isinstance(cand.skills, list) else []
            
            if current_skills:
                tags_html = " ".join([f"`{s}`" for s in current_skills[:12]])
                if len(current_skills) > 12:
                    tags_html += f" `+{len(current_skills) - 12}更多`"
                st.markdown(f"🏷️ {tags_html}")
            else:
                st.caption("🏷️ 暂无标签（展开编辑基础信息添加）")
            
            # === 第五行：核心专长标签（来自structured_tags）===
            if cand.structured_tags:
                try:
                    struct_tags = cand.structured_tags if isinstance(cand.structured_tags, dict) else json.loads(cand.structured_tags)
                    core_specs = struct_tags.get("core_specialty", [])
                    tech_domains = struct_tags.get("tech_domain", [])
                    
                    spec_parts = []
                    if core_specs:
                        spec_parts.append(f"**核心专长**: {', '.join(core_specs)}")
                    if tech_domains:
                        spec_parts.append(f"**技术方向**: {', '.join(tech_domains)}")
                    
                    if spec_parts:
                        st.markdown(f"🎯 {' │ '.join(spec_parts)}")
                except:
                    pass
            
            # 联系方式（有内容才显示）
            contact_parts = []
            if cand.phone:
                contact_parts.append(f"📱 {cand.phone}")
            if cand.email:
                contact_parts.append(f"📧 [{cand.email}](mailto:{cand.email})")
            if cand.linkedin_url:
                contact_parts.append(f"[🔗 LinkedIn]({cand.linkedin_url})")
            if cand.github_url:
                contact_parts.append(f"[💻 GitHub]({cand.github_url})")
            if hasattr(cand, 'personal_website') and cand.personal_website:
                contact_parts.append(f"[🌐 主页]({cand.personal_website if cand.personal_website.startswith('http') else 'https://' + cand.personal_website})")
            if hasattr(cand, 'twitter_url') and cand.twitter_url:
                contact_parts.append(f"[🐦 Twitter]({cand.twitter_url})")
            
            if contact_parts:
                st.markdown(" │ ".join(contact_parts))
            
            # 进入渠道（来源）
            if cand.source:
                source_icons = {
                    'maimai': '🟦 脉脉', 'github': '💻 GitHub', 'linkedin': '🔗 LinkedIn',
                    'boss': '🟧 Boss', '图片OCR': '📷 图片OCR', 'PDF解析': '📄 PDF解析',
                    '文档解析': '📝 文档解析', '后台解析': '⚙️ 后台解析'
                }
                sources = [s.strip() for s in cand.source.replace(',', ' ').split() if s.strip()]
                source_display = []
                for s in sources:
                    matched = False
                    for key, label in source_icons.items():
                        if key.lower() in s.lower():
                            if label not in source_display:
                                source_display.append(label)
                            matched = True
                            break
                    if not matched and s not in source_display:
                        source_display.append(s)
                if source_display:
                    st.markdown(f"📂 **进入渠道**: {' │ '.join(source_display)}")
            
            # 左右布局：左侧主要经历，右侧备注和沟通记录
            main_col, side_col = st.columns([3, 2])

            
            with main_col:
                # === Tab切换：履历 vs 匹配职位 ===
                detail_tab, match_tab = st.tabs(["📋 履历", "🎯 匹配职位"])
                
                with detail_tab:
                    work_header_col, work_edit_col = st.columns([5, 1])
                    with work_header_col:
                        st.subheader("💼 工作经历")
                    with work_edit_col:
                        edit_work_mode = st.toggle("✏️", key="edit_work_toggle", help="编辑工作经历")
                
                    if cand.work_experiences and isinstance(cand.work_experiences, list):
                        if edit_work_mode:
                            # 编辑模式
                            st.info("📝 编辑模式：修改公司、职位、时间、具体内容")
                            
                            # 新增工作经历按钮
                            if st.button("➕ 新增工作经历", key="add_new_work_exp"):
                                # 在列表开头添加空的工作经历
                                new_exp = {'company': '', 'title': '', 'time': '', 'description': ''}
                                cand.work_experiences = [new_exp] + list(cand.work_experiences)
                                db.commit()
                                st.rerun()
                            
                            updated_work = []
                            delete_indices = []
                            
                            for i, work in enumerate(cand.work_experiences):
                                with st.container(border=True):
                                    header_col, del_col = st.columns([6, 1])
                                    with header_col:
                                        st.markdown(f"**工作经历 #{i+1}**")
                                    with del_col:
                                        if st.button("🗑️", key=f"del_work_{i}", help="删除此工作经历"):
                                            delete_indices.append(i)
                                    
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
                                        height=350  # 约10行
                                    )
                                
                                    if i not in delete_indices:
                                        updated_work.append({
                                            'company': new_company,
                                            'title': new_title,
                                            'time': new_time,
                                            'description': new_desc
                                        })
                            
                            # 处理删除操作
                            if delete_indices:
                                remaining_work = [w for i, w in enumerate(cand.work_experiences) if i not in delete_indices]
                                cand.work_experiences = remaining_work
                                if remaining_work:
                                    cand.current_company = remaining_work[0].get('company', '')
                                    cand.current_title = remaining_work[0].get('title', '')
                                db.commit()
                                st.toast(f"🗑️ 已删除 {len(delete_indices)} 条工作经历")
                                st.rerun()
                        
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
                                    # 兼容多种时间格式
                                    time_str = work.get('time') or work.get('time_range', '')
                                    if not time_str:
                                        start = work.get('start_date', '')
                                        end = work.get('end_date', '')
                                        duration = work.get('duration', '')
                                        if start and end:
                                            time_str = f"{start} - {end}"
                                            if duration:
                                                time_str += f" ({duration})"
                                        elif duration:
                                            time_str = duration
                                    st.caption(f"📅 {time_str or 'N/A'}")
                                
                                    # 清洗描述文本，兼容content和description
                                    desc = work.get('description') or work.get('content', '')
                                    desc = re.sub(r'^(内容|工作内容|职责|工作职责|项目描述)[:：]\s*', '', desc, flags=re.IGNORECASE).strip()
                                    # 优化换行显示
                                    desc = desc.replace("\n", "  \n") 
                                
                                    if desc:
                                        st.markdown(desc)
                                
                                    # 显示详细工作内容（details数组）
                                    details = work.get('details', [])
                                    if details and isinstance(details, list):
                                        st.markdown("**工作内容：**")
                                        for i, detail in enumerate(details, 1):
                                            st.markdown(f"{i}. {detail}")
                                
                                    st.markdown("---")
                    else:
                        # 没有工作经历时显示新增按钮
                        if edit_work_mode:
                            st.info("📝 暂无工作经历，点击下方按钮添加")
                            if st.button("➕ 新增工作经历", key="add_first_work_exp"):
                                new_exp = {'company': '', 'title': '', 'time': '', 'description': ''}
                                cand.work_experiences = [new_exp]
                                db.commit()
                                st.rerun()
                        else:
                            st.info("暂无详细工作经历（开启编辑模式可新增）")
                
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
                                    new_desc = st.text_input("描述(GPA/研究方向/导师)", value=edu.get('description', ''), key=f"edit_edu_desc_{i}")
                                
                                    updated_edu.append({
                                        'school': new_school,
                                        'major': new_major,
                                        'time': new_time,
                                        'degree': edu.get('degree', ''),
                                        'description': new_desc,
                                        'tags': edu.get('tags', [])
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
                                description = edu.get('description', '')
                                tags = edu.get('tags', [])
                            
                                # 构建显示文本
                                display_text = f"- **{school}** | {major}"
                                if degree:
                                    display_text += f" | {degree}"
                                if time_range and time_range != 'nan':
                                    display_text += f" ({time_range})"
                                if tags:
                                    display_text += f" `{'` `'.join(tags)}`"
                            
                                st.markdown(display_text)
                                if description:
                                    st.caption(f"  {description}")
                    else:
                        st.info("暂无详细教育经历")

                    # --- 荣誉与科研成果 ---
                    st.subheader("🏆 荣誉与科研成果")
                
                    awards = cand.awards_achievements or []
                    if isinstance(awards, str):
                        import json as json_lib
                        try:
                            awards = json_lib.loads(awards)
                        except:
                            awards = []
                
                    # 编辑模式开关
                    edit_awards_mode = st.toggle("✏️", key="edit_awards_toggle", help="编辑荣誉与科研成果")
                
                    if edit_awards_mode:
                        # 编辑模式
                        if not awards:
                            awards = [{"type": "", "title": "", "time": "", "description": ""}]
                    
                        edited_awards = []
                        for i, award in enumerate(awards):
                            with st.container(border=True):
                                st.markdown(f"**成果 #{i+1}**")
                                ac1, ac2 = st.columns([1, 2])
                                with ac1:
                                    award_type = st.selectbox(
                                        "类型", 
                                        ["", "论文", "专利", "奖学金", "竞赛获奖", "荣誉称号", "其他"],
                                        index=["", "论文", "专利", "奖学金", "竞赛获奖", "荣誉称号", "其他"].index(award.get("type", "")) if award.get("type", "") in ["", "论文", "专利", "奖学金", "竞赛获奖", "荣誉称号", "其他"] else 0,
                                        key=f"award_type_{i}"
                                    )
                                    award_time = st.text_input("时间", value=award.get("time", ""), key=f"award_time_{i}")
                                with ac2:
                                    award_title = st.text_input("名称", value=award.get("title", ""), key=f"award_title_{i}")
                                    award_desc = st.text_input("描述", value=award.get("description", ""), key=f"award_desc_{i}")
                            
                                edited_awards.append({
                                    "type": award_type,
                                    "title": award_title,
                                    "time": award_time,
                                    "description": award_desc
                                })
                    
                        # 添加更多按钮
                        add_cols = st.columns([1, 3])
                        if add_cols[0].button("➕ 添加成果", key="add_award"):
                            edited_awards.append({"type": "", "title": "", "time": "", "description": ""})
                            from sqlalchemy.orm.attributes import flag_modified
                            cand.awards_achievements = edited_awards
                            flag_modified(cand, "awards_achievements")
                            db.commit()
                            st.rerun()
                    
                        # 保存按钮
                        if st.button("💾 保存荣誉与成果", type="primary", key="save_awards"):
                            # 过滤掉空项
                            valid_awards = [a for a in edited_awards if a.get("title")]
                            from sqlalchemy.orm.attributes import flag_modified
                            cand.awards_achievements = valid_awards
                            flag_modified(cand, "awards_achievements")
                            db.commit()
                            st.success("✅ 荣誉与科研成果已保存！")
                            st.rerun()
                    else:
                        # 展示模式
                        if awards:
                            for award in awards:
                                award_type = award.get("type", "")
                                title = award.get("title", "")
                                time_str = award.get("time", "")
                                desc = award.get("description", "")
                            
                                if not title:
                                    continue
                            
                                # 类型图标
                                type_icons = {
                                    "论文": "📝",
                                    "专利": "💡", 
                                    "奖学金": "🎓",
                                    "竞赛获奖": "🥇",
                                    "荣誉称号": "🏅",
                                    "其他": "✨"
                                }
                                icon = type_icons.get(award_type, "🏆")
                            
                                display = f"{icon} **{title}**"
                                if award_type:
                                    display += f" ({award_type})"
                                if time_str:
                                    display += f" - {time_str}"
                                st.markdown(display)
                                if desc:
                                    st.caption(f"  {desc}")
                        else:
                            st.info("暂无荣誉与科研成果，点击 ✏️ 添加")

                    # --- GitHub 概览 ---
                    if cand.github_url:
                        st.subheader("🐙 GitHub 概览")
                        
                        # 从 structured_tags 获取缓存的 GitHub 数据
                        gh_tags = cand.structured_tags or {}
                        if isinstance(gh_tags, str):
                            try:
                                gh_tags = json.loads(gh_tags)
                            except:
                                gh_tags = {}
                        
                        gh_followers = gh_tags.get('github_followers', 0)
                        gh_stars = gh_tags.get('github_total_stars', 0)
                        gh_repos = gh_tags.get('github_repos', 0)
                        gh_score = gh_tags.get('github_score', 0)
                        gh_username = gh_tags.get('github_username', '')
                        gh_refreshed = gh_tags.get('github_refreshed_at', '')
                        
                        # 指标展示
                        gc1, gc2, gc3, gc4 = st.columns(4)
                        gc1.metric("⭐ Stars", f"{gh_stars:,}" if gh_stars else "-")
                        gc2.metric("👥 Followers", f"{gh_followers:,}" if gh_followers else "-")
                        gc3.metric("📦 Repos", gh_repos if gh_repos else "-")
                        gc4.metric("📊 Score", f"{gh_score:.1f}" if gh_score else "-")
                        
                        # GitHub 链接 + 刷新按钮
                        ghc1, ghc2 = st.columns([3, 1])
                        ghc1.markdown(f"🔗 [{gh_username or cand.github_url}]({cand.github_url})")
                        if gh_refreshed:
                            ghc1.caption(f"上次更新: {gh_refreshed[:10]}")
                        
                        if ghc2.button("🔄 更新", key="refresh_github_btn", use_container_width=True):
                            with st.spinner("查询 GitHub API..."):
                                try:
                                    import requests as req
                                    resp = req.post(f"http://localhost:8502/api/candidate/{cand.id}/refresh-github", timeout=30)
                                    result = resp.json()
                                    if result.get('success'):
                                        st.success(f"✅ {result['message']}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {result.get('detail', '刷新失败')}")
                                except Exception as e:
                                    st.error(f"❌ GitHub 数据刷新失败: {e}")
                        
                        st.divider()
                    
                    # --- 学术数据查询 ---
                    with st.expander("🔍 查询学术数据 (Semantic Scholar)"):
                        sc_tags = cand.structured_tags or {}
                        if isinstance(sc_tags, str):
                            try:
                                sc_tags = json.loads(sc_tags)
                            except:
                                sc_tags = {}
                        
                        # 展示已有学术数据
                        if sc_tags.get('scholar_h_index'):
                            st.markdown(f"**已缓存学术数据：** H-index: {sc_tags.get('scholar_h_index', 0)} | 引用: {sc_tags.get('scholar_citations', 0):,} | 论文: {sc_tags.get('scholar_papers', 0)}")
                            if sc_tags.get('scholar_top_venues'):
                                venues = sc_tags['scholar_top_venues']
                                venue_str = ' | '.join(f"{k}: {v}" for k, v in sorted(venues.items(), key=lambda x: -x[1]))
                                st.caption(f"📄 顶会: {venue_str}")
                            if sc_tags.get('scholar_refreshed_at'):
                                st.caption(f"上次更新: {sc_tags['scholar_refreshed_at'][:10]}")
                            st.divider()
                        
                        # 搜索作者
                        search_name = st.text_input("搜索作者姓名", value=cand.name, key="scholar_search_name")
                        if st.button("🔍 搜索", key="search_scholar_btn"):
                            with st.spinner("查询 Semantic Scholar..."):
                                try:
                                    import requests as req
                                    resp = req.get(f"http://localhost:8502/api/candidate/{cand.id}/search-scholar", params={"query": search_name}, timeout=20)
                                    result = resp.json()
                                    if result.get('success'):
                                        authors = result.get('authors', [])
                                        if authors:
                                            st.session_state['scholar_authors'] = authors
                                        else:
                                            st.warning("未找到匹配的作者")
                                except Exception as e:
                                    st.error(f"❌ 搜索失败: {e}")
                        
                        # 显示搜索结果
                        if 'scholar_authors' in st.session_state:
                            for idx, author in enumerate(st.session_state['scholar_authors']):
                                aff_str = ', '.join(author.get('affiliations', [])) if author.get('affiliations') else ''
                                st.markdown(f"**{author['name']}** — 论文: {author['paperCount']} | 引用: {author['citationCount']:,} | H-index: {author['hIndex']} {('| ' + aff_str) if aff_str else ''}")
                                if st.button(f"✅ 选择此人", key=f"select_scholar_{idx}"):
                                    with st.spinner("获取学术数据..."):
                                        try:
                                            import requests as req
                                            resp = req.post(
                                                f"http://localhost:8502/api/candidate/{cand.id}/fetch-scholar",
                                                json={"authorId": author['authorId']},
                                                timeout=30
                                            )
                                            result = resp.json()
                                            if result.get('success'):
                                                st.success(f"✅ {result['message']}")
                                                del st.session_state['scholar_authors']
                                                st.rerun()
                                            else:
                                                st.error(f"❌ {result.get('detail', '获取失败')}")
                                        except Exception as e:
                                            st.error(f"❌ 获取学术数据失败: {e}")

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
                
                    # --- 编辑基础信息 (移到左侧底部) ---
                    with st.expander("✏️ 编辑基础信息"):
                        # 第一行：姓名、年龄、年限、学历
                        r1c1, r1c2, r1c3, r1c4 = st.columns([1.5, 1, 1, 1])
                        with r1c1:
                            new_name = st.text_input("姓名", value=cand.name or "", key="edit_name")
                        with r1c2:
                            new_age = st.number_input("年龄", value=int(cand.age or 0), min_value=0, max_value=100, key="edit_age")
                        with r1c3:
                            new_exp = st.number_input("年限", value=int(cand.experience_years or 0), min_value=0, max_value=50, key="edit_exp")
                        with r1c4:
                            edu_options = ["未知", "大专", "本科", "硕士", "博士", "其他"]
                            current_edu_idx = edu_options.index(cand.education_level) if cand.education_level in edu_options else 0
                            new_edu = st.selectbox("学历", edu_options, index=current_edu_idx, key="edit_edu")
                    
                        # 第二行：公司、职位、地点
                        r2c1, r2c2, r2c3 = st.columns([2, 2, 1])
                        with r2c1:
                            new_company = st.text_input("公司", value=cand.current_company or "", key="edit_company")
                        with r2c2:
                            new_title = st.text_input("职位", value=cand.current_title or "", key="edit_title")
                        with r2c3:
                            new_location = st.text_input("地点", value=cand.expect_location or "", key="edit_location")
                    
                        # 第三行：联系方式
                        r3c1, r3c2, r3c3, r3c4 = st.columns(4)
                        with r3c1:
                            new_phone = st.text_input("📱 电话", value=cand.phone or "", key="edit_phone_basic")
                        with r3c2:
                            new_email = st.text_input("📧 邮箱", value=cand.email or "", key="edit_email_basic")
                        with r3c3:
                            new_linkedin = st.text_input("🔗 LinkedIn", value=cand.linkedin_url or "", key="edit_linkedin_basic")
                        with r3c4:
                            new_github = st.text_input("💻 GitHub", value=cand.github_url or "", key="edit_github_basic")
                    
                        # 第三行半前：个人网站 + Twitter
                        r3b1, r3b2 = st.columns(2)
                        with r3b1:
                            new_website = st.text_input("🌐 个人网站", value=cand.personal_website or "", key="edit_website_basic")
                        with r3b2:
                            new_twitter = st.text_input("🐦 Twitter", value=cand.twitter_url or "", key="edit_twitter_basic")
                    
                        # 第三行半：管道阶段 + 微信号 + 人才分级
                        r35c1, r35c2, r35c3, r35c4 = st.columns([1.5, 1.5, 1, 1])
                        with r35c1:
                            stage_options = ["new", "contacted", "following_up", "replied", "wechat_connected", "in_pipeline", "closed"]
                            stage_labels = ["🆕 新发现", "📤 已打招呼", "🔄 跟进中", "💬 已回复", "💚 已加微信", "🎯 面试中", "⏸️ 关闭"]
                            current_stage = cand.pipeline_stage or 'new'
                            current_idx = stage_options.index(current_stage) if current_stage in stage_options else 0
                            new_stage = st.selectbox("📊 管道阶段", stage_labels, index=current_idx, key="edit_pipeline_stage")
                        with r35c2:
                            new_wechat_id = st.text_input("💚 微信号", value=cand.wechat_id or "", key="edit_wechat_id")
                        with r35c3:
                            new_follow_up = st.date_input("📅 下次跟进", value=datetime.strptime(cand.follow_up_date, "%Y-%m-%d").date() if cand.follow_up_date else None, key="edit_follow_up_date", format="YYYY-MM-DD")
                        with r35c4:
                            tier_options = ["", "S", "A+", "A", "B+", "B", "C"]
                            tier_labels = ["未分级", "🔴 S-顶尖大牛", "🟠 A+-卓越", "🟠 A-优秀", "🟡 B+-良好", "🟡 B-不错", "🟢 C-一般"]
                            current_tier = cand.talent_tier or ''
                            current_tier_idx = tier_options.index(current_tier) if current_tier in tier_options else 0
                            new_tier = st.selectbox("🏅 人才分级", tier_labels, index=current_tier_idx, key="edit_talent_tier")
                    
                        # 第四行：技能标签编辑
                        st.markdown("##### 🏷️ 技能标签")
                        current_skills = cand.skills if cand.skills and isinstance(cand.skills, list) else []
                        
                        # multiselect 支持删除标签
                        updated_skills = st.multiselect(
                            "技能标签",
                            options=current_skills,
                            default=current_skills,
                            key=f"edit_skills_{cand.id}",
                            label_visibility="collapsed"
                        )
                        
                        # 添加新标签
                        tag_col1, tag_col2 = st.columns([3, 1])
                        with tag_col1:
                            new_tags_input = st.text_input(
                                "添加新标签",
                                placeholder="输入新标签，多个用逗号分隔",
                                key=f"new_tags_input_{cand.id}",
                                label_visibility="collapsed"
                            )
                        with tag_col2:
                            if st.button("➕ 添加", key=f"add_tags_btn_{cand.id}"):
                                if new_tags_input and new_tags_input.strip():
                                    from sqlalchemy.orm.attributes import flag_modified
                                    new_skills = list(current_skills)
                                    added_tags = []
                                    for tag in new_tags_input.split(","):
                                        tag = tag.strip()
                                        if tag and tag not in new_skills:
                                            new_skills.append(tag)
                                            added_tags.append(tag)
                                    if added_tags:
                                        cand.skills = new_skills
                                        flag_modified(cand, "skills")
                                        db.commit()
                                        st.toast(f"✅ 已添加: {', '.join(added_tags)}")
                                        st.rerun()
                                    else:
                                        st.toast("⚠️ 标签已存在")
                                else:
                                    st.toast("⚠️ 请输入标签")
                    
                        # 简历上传
                        st.markdown("##### 📄 上传简历")
                    
                        # 显示已有简历附件
                        if cand.source_file:
                            st.info(f"📎 **已有简历**: {cand.source_file}")
                    
                        uploaded_resume = st.file_uploader("上传简历文件 (PDF/Word/TXT)", type=["pdf", "docx", "txt"], key="upload_resume")
                    
                        if uploaded_resume:
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
                    
                        if st.button("💾 保存修改", type="primary", key="save_basic_info"):
                            print(f"📌 开始保存候选人信息: {new_name}")
                            from sqlalchemy.orm.attributes import flag_modified
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
                            cand.personal_website = new_website if new_website else None
                            cand.twitter_url = new_twitter if new_twitter else None
                            # 保存技能标签
                            cand.skills = updated_skills
                            flag_modified(cand, "skills")
                            # 保存管道阶段、微信号、跟进日期、人才分级
                            selected_stage_idx = stage_labels.index(new_stage)
                            cand.pipeline_stage = stage_options[selected_stage_idx]
                            cand.wechat_id = new_wechat_id if new_wechat_id else None
                            cand.follow_up_date = new_follow_up.strftime("%Y-%m-%d") if new_follow_up else None
                            # 保存人才分级
                            selected_tier_idx = tier_labels.index(new_tier)
                            cand.talent_tier = tier_options[selected_tier_idx] if tier_options[selected_tier_idx] else None
                        
                            if uploaded_resume:
                                print(f"📄 处理上传的简历: {uploaded_resume.name}")
                                if uploaded_resume.name.endswith('.txt'):
                                    uploaded_resume.seek(0)
                                    resume_content = uploaded_resume.read().decode('utf-8')
                                elif uploaded_resume.name.endswith('.pdf'):
                                    try:
                                        import PyPDF2
                                        uploaded_resume.seek(0)
                                        pdf_reader = PyPDF2.PdfReader(uploaded_resume)
                                        resume_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                                        print(f"✅ PDF解析成功，内容长度: {len(resume_content)}")
                                    except Exception as pdf_err:
                                        print(f"❌ PDF解析失败: {pdf_err}")
                                        resume_content = None
                                else:
                                    resume_content = None
                            
                                if resume_content:
                                    cand.raw_resume_text = resume_content
                                    cand.source_file = uploaded_resume.name
                                    print(f"✅ 简历内容已更新")
                                
                                    # 保存原始文件以支持下载
                                    try:
                                        resume_dir = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/resumes"
                                        os.makedirs(resume_dir, exist_ok=True)
                                        uploaded_resume.seek(0)
                                        file_path = f"{resume_dir}/{cand.id}_{uploaded_resume.name}"
                                        with open(file_path, "wb") as f:
                                            f.write(uploaded_resume.read())
                                        print(f"✅ 简历文件已保存: {file_path}")
                                    except Exception as save_err:
                                        print(f"⚠️ 文件保存失败: {save_err}")
                        
                            db.commit()
                            print(f"✅ 保存成功")
                            st.success("✅ 已保存！")
                            st.rerun()
                
                # === 🎯 匹配职位 Tab ===
                with match_tab:
                    st.subheader(f"🎯 为 {cand.name} 匹配职位")
                    
                    # 检查是否有结构化标签
                    if not cand.structured_tags:
                        st.warning("⚠️ 该候选人暂无结构化标签，无法进行匹配。")
                        st.info("请先在【批处理】页面提取标签，或手动添加技能标签。")
                    else:
                        # 显示候选人标签
                        with st.expander("🏷️ 当前标签（用于匹配）", expanded=False):
                            st.json(cand.structured_tags)
                        
                        # 匹配按钮
                        col_btn, col_slider = st.columns([1, 2])
                        with col_slider:
                            match_top_k = st.slider("显示结果数量", 5, 30, 15, key=f"match_topk_{cand.id}")
                        
                        cache_key = f"detail_match_results_{cand.id}"
                        
                        with col_btn:
                            if st.button("🚀 开始匹配", type="primary", key=f"match_btn_{cand.id}"):
                                try:
                                    from job_search import match_candidate_to_jobs
                                    with st.spinner("正在匹配职位..."):
                                        results = match_candidate_to_jobs(cand.id, top_k=match_top_k)
                                    st.session_state[cache_key] = results
                                    # 确保页面状态不变
                                    st.session_state.view_mode = 'detail'
                                    st.session_state.selected_candidate_id = cand.id
                                    st.session_state.nav_page = '人才库管理'
                                except Exception as e:
                                    st.error(f"匹配失败: {e}")
                                    st.session_state[cache_key] = []
                        
                        # 显示缓存的匹配结果
                        if cache_key in st.session_state and st.session_state[cache_key]:
                            results = st.session_state[cache_key]
                            
                            st.success(f"✅ 找到 {len(results)} 个匹配职位")
                            
                            if st.button("🔄 清除结果", key=f"clear_match_{cand.id}"):
                                del st.session_state[cache_key]
                                st.rerun()
                            
                            st.divider()
                            
                            # 显示匹配结果列表
                            import sqlite3
                            DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            
                            for i, r in enumerate(results, 1):
                                with st.container(border=True):
                                    job_id = r.get('job_id')
                                    score = r.get('score', 0)
                                    job_code = r.get('job_code', '')
                                    job_title = r.get('title', '未知职位')
                                    company = r.get('company', '')
                                    location = r.get('location', '')
                                    seniority = r.get('seniority', '')
                                    
                                    # 标题行：checkbox + 职位信息 + 分数
                                    chk_col, info_col, score_col = st.columns([0.5, 4, 1])
                                    with chk_col:
                                        selected = st.checkbox("选", key=f"rec_chk_{cand.id}_{job_id}", label_visibility="collapsed")
                                    with info_col:
                                        st.markdown(f"### {i}. [{job_code}] {job_title}")
                                        st.caption(f"🏢 {company} · 📍 {location}")
                                    with score_col:
                                        if score >= 80:
                                            st.success(f"**{score:.1f}分**")
                                        elif score >= 60:
                                            st.warning(f"{score:.1f}分")
                                        else:
                                            st.error(f"{score:.1f}分")
                                    
                                    # 匹配原因
                                    reasons = r.get('match_reasons', [])
                                    if reasons:
                                        st.markdown(f"✅ **匹配原因**: {', '.join(reasons[:3])}")
                                    
                                    # 风险提示
                                    risks = r.get('risk_flags', [])
                                    if risks:
                                        st.markdown(f"⚠️ **风险**: {', '.join(risks)}")
                                    
                                    # 使用 expander 显示职位详情
                                    with st.expander("📄 查看职位详情", expanded=False):
                                        cursor.execute("""
                                            SELECT raw_jd_text, structured_tags, salary_range, 
                                                   required_experience_years, original_link
                                            FROM jobs WHERE id = ?
                                        """, (job_id,))
                                        job_detail = cursor.fetchone()
                                        
                                        if job_detail:
                                            jd_text, struct_tags, salary, exp_years, orig_link = job_detail
                                            
                                            # 基本信息行
                                            info_col1, info_col2, info_col3 = st.columns(3)
                                            with info_col1:
                                                st.markdown(f"**💰 薪资**: {salary or '面议'}")
                                            with info_col2:
                                                st.markdown(f"**📅 经验**: {exp_years or '-'}年+")
                                            with info_col3:
                                                if orig_link:
                                                    st.markdown(f"[🔗 原始链接]({orig_link})")
                                            
                                            st.divider()
                                            
                                            # 结构化标签
                                            if struct_tags:
                                                try:
                                                    tags_data = json.loads(struct_tags) if isinstance(struct_tags, str) else struct_tags
                                                    tag_col1, tag_col2 = st.columns(2)
                                                    with tag_col1:
                                                        st.markdown(f"• 技术方向: {', '.join(tags_data.get('tech_domain', []))}")
                                                        st.markdown(f"• 核心专长: {', '.join(tags_data.get('core_specialty', []))}")
                                                    with tag_col2:
                                                        st.markdown(f"• 岗位类型: {tags_data.get('role_type', '-')}")
                                                        st.markdown(f"• 职级要求: {tags_data.get('seniority', '-')}")
                                                    st.divider()
                                                except:
                                                    pass
                                            
                                            # JD全文
                                            if jd_text:
                                                display_text = jd_text[:2000] + ("..." if len(jd_text) > 2000 else "")
                                                st.markdown(display_text)
                                            else:
                                                st.info("暂无JD内容")
                                        else:
                                            st.warning("无法加载职位详情")
                            
                            conn.close()
                            
                            # =============================================
                            # 📤 推荐给候选人 — 从匹配列表中勾选 + 手动补充
                            # =============================================
                            st.divider()
                            st.subheader("📤 推荐给候选人")
                            
                            # 收集已勾选的 JD
                            selected_jobs = []
                            for r in results:
                                jid = r.get('job_id')
                                if st.session_state.get(f"rec_chk_{cand.id}_{jid}"):
                                    selected_jobs.append({
                                        'job_id': jid,
                                        'job_code': r.get('job_code', ''),
                                        'job_title': r.get('title', ''),
                                        'job_company': r.get('company', ''),
                                        'job_location': r.get('location', ''),
                                        'job_seniority': r.get('seniority', ''),
                                    })
                            
                            # 手动补充 JD Code
                            with st.expander("🔍 按 JD Code 补充推荐", expanded=False):
                                extra_code = st.text_input("输入 JD Code（如 BT090）", key=f"extra_jd_code_{cand.id}")
                                if extra_code and st.button("➕ 查找并添加", key=f"add_extra_jd_{cand.id}"):
                                    from database import Job, SessionLocal as _DbSession
                                    db_sess = _DbSession()
                                    found_job = db_sess.query(Job).filter(Job.job_code == extra_code.strip()).first()
                                    if found_job:
                                        # 避免重复
                                        existing_ids = [j['job_id'] for j in selected_jobs]
                                        if found_job.id not in existing_ids:
                                            extra_key = f"extra_jobs_{cand.id}"
                                            if extra_key not in st.session_state:
                                                st.session_state[extra_key] = []
                                            st.session_state[extra_key].append({
                                                'job_id': found_job.id,
                                                'job_code': found_job.job_code or '',
                                                'job_title': found_job.title or '',
                                                'job_company': found_job.company or '',
                                                'job_location': found_job.location or '',
                                                'job_seniority': found_job.seniority_level or '',
                                            })
                                            st.success(f"✅ 已添加: [{found_job.job_code}] {found_job.title} · {found_job.company}")
                                        else:
                                            st.warning("该职位已在推荐列表中")
                                    else:
                                        st.error(f"❌ 未找到 JD Code: {extra_code}")
                                    db_sess.close()
                            
                            # 合并手动添加的 JD
                            extra_key = f"extra_jobs_{cand.id}"
                            if extra_key in st.session_state:
                                for ej in st.session_state[extra_key]:
                                    existing_ids = [j['job_id'] for j in selected_jobs]
                                    if ej['job_id'] not in existing_ids:
                                        selected_jobs.append(ej)
                            
                            # 显示已选汇总
                            if selected_jobs:
                                st.info(f"📋 已选 **{len(selected_jobs)}** 个职位：" + 
                                        "、".join([f"[{j['job_code']}]{j['job_title']}" for j in selected_jobs]))
                            else:
                                st.caption("💡 请在上方匹配结果中勾选要推荐的职位")
                            
                            # 推荐按钮
                            if selected_jobs:
                                if st.button(f"🚀 一键推荐 {len(selected_jobs)} 个职位", type="primary", key=f"push_rec_{cand.id}"):
                                    import hashlib, requests
                                    PORTAL_BASE = "https://jobs.rupro-consulting.com"
                                    token = hashlib.sha256('ruproAI'.encode()).hexdigest()
                                    cookies = {'auth_token': token}
                                    
                                    with st.spinner("正在推荐..."):
                                        # 1. 创建/获取门户
                                        portal_resp = requests.post(f"{PORTAL_BASE}/api/portal/create", json={
                                            'candidate_id': cand.id,
                                            'candidate_name': cand.name,
                                        }, cookies=cookies, timeout=15)
                                        
                                        if portal_resp.status_code != 200:
                                            st.error(f"创建门户失败 (HTTP {portal_resp.status_code}): {portal_resp.text[:200]}")
                                        else:
                                            portal_data = portal_resp.json()
                                            
                                            if portal_data.get('success'):
                                                portal_code = portal_data['portal_code']
                                                
                                                # 2. 逐个推荐 JD
                                                success_count = 0
                                                from database import Job, SessionLocal as _DbSession
                                                for j in selected_jobs:
                                                    try:
                                                        db_s = _DbSession()
                                                        job_obj = db_s.query(Job).filter(Job.id == j['job_id']).first()
                                                        jd_text = ""
                                                        if job_obj and job_obj.raw_jd_text:
                                                            jd_text = job_obj.raw_jd_text[:3000]
                                                        db_s.close()
                                                        
                                                        rec_resp = requests.post(f"{PORTAL_BASE}/api/portal/recommend", json={
                                                            'portal_code': portal_code,
                                                            'local_job_id': j['job_id'],
                                                            'job_code': j.get('job_code', ''),
                                                            'job_title': j.get('job_title', ''),
                                                            'job_company': j.get('job_company', ''),
                                                            'job_location': j.get('job_location', ''),
                                                            'job_seniority': j.get('job_seniority', ''),
                                                            'job_description': jd_text,
                                                        }, cookies=cookies, timeout=15)
                                                        
                                                        if rec_resp.status_code == 200 and rec_resp.json().get('success'):
                                                            success_count += 1
                                                        else:
                                                            st.warning(f"推荐 {j.get('job_code', '')} 失败: {rec_resp.text[:100]}")
                                                    except Exception as e:
                                                        st.warning(f"推荐 {j.get('job_code', '')} 失败: {e}")
                                                
                                                # 3. 显示结果和链接
                                                st.success(f"🎉 成功推荐 {success_count}/{len(selected_jobs)} 个职位！")
                                                
                                                portal_url = f"{PORTAL_BASE}/p/{portal_code}"
                                                friend_url = f"{portal_url}?f=1"
                                                
                                                st.session_state[f"portal_urls_{cand.id}"] = {
                                                    'portal_url': portal_url,
                                                    'friend_url': friend_url,
                                                    'portal_code': portal_code,
                                                }
                                            else:
                                                st.error(f"创建门户失败: {portal_data}")
                            


            with side_col:
                # === 📱 VIP 服务通道名片卡（最顶部，方便截图） ===
                try:
                    import hashlib, requests
                    PORTAL_BASE = "https://jobs.rupro-consulting.com"
                    token = hashlib.sha256('ruproAI'.encode()).hexdigest()
                    
                    # 获取或创建门户
                    portal_resp = requests.post(f"{PORTAL_BASE}/api/portal/create", json={
                        'candidate_id': cand.id,
                        'candidate_name': cand.name,
                    }, cookies={'auth_token': token}, timeout=10)
                    
                    if portal_resp.status_code == 200 and portal_resp.json().get('success'):
                        portal_code = portal_resp.json()['portal_code']
                        portal_url = f"{PORTAL_BASE}/p/{portal_code}"
                        friend_url = f"{portal_url}?f=1"
                        
                        with st.expander("📱 VIP 服务通道", expanded=False):
                            # 生成名片卡
                            from portal_card import generate_portal_card_base64
                            card_b64 = generate_portal_card_base64(cand.name, portal_code)
                            
                            st.markdown(
                                f'<img src="data:image/png;base64,{card_b64}" '
                                f'style="width:100%;border-radius:10px;">',
                                unsafe_allow_html=True
                            )
                            st.caption("👆 截图发给候选人即可")
                            
                            lc1, lc2 = st.columns(2)
                            with lc1:
                                st.code(portal_url, language=None)
                                st.caption("📨 普通链接")
                            with lc2:
                                st.code(friend_url, language=None)
                                st.caption("💚 微信好友链接")
                except Exception as e:
                    st.caption(f"⚠️ 门户加载失败: {e}")
                
                # --- 简历附件（紧凑布局）---
                if cand.source_file:
                    resume_path = f"/Users/lillianliao/notion_rag/personal-ai-headhunter/data/resumes/{cand.id}_{cand.source_file}"
                    col_label, col_btn = st.columns([1, 1])
                    with col_label:
                        st.caption(f"📄 **简历**: {cand.source_file[:30]}..." if len(cand.source_file) > 30 else f"📄 **简历**: {cand.source_file}")
                    with col_btn:
                        if os.path.exists(resume_path):
                            with open(resume_path, "rb") as f:
                                st.download_button(
                                    label="📥 下载",
                                    data=f.read(),
                                    file_name=cand.source_file,
                                    mime="application/octet-stream",
                                    key="download_resume_btn"
                                )
                        elif cand.raw_resume_text:
                            st.download_button(
                                label="📥 下载(.txt)",
                                data=cand.raw_resume_text.encode('utf-8'),
                                file_name=f"{cand.name}_简历.txt",
                                mime="text/plain",
                                key="download_resume_txt_btn"
                            )
                
                # --- 备注 ---
                st.markdown("##### 📝 备注")
                
                # 使用唯一key避免冲突
                notes_key = f"notes_{cand.id}"
                new_notes = st.text_area(
                    "备注", 
                    value=cand.notes or "",
                    key=notes_key, 
                    height=250,
                    placeholder="输入备注信息...",
                    label_visibility="collapsed"
                )
                
                # 保存按钮
                if st.button("💾 保存备注", key=f"save_notes_{cand.id}", use_container_width=True):
                    import sqlite3
                    conn = sqlite3.connect('/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE candidates SET notes = ? WHERE id = ?", (new_notes, cand.id))
                    conn.commit()
                    conn.close()
                    st.toast("✅ 备注已保存")
                    st.rerun()
                
                # --- 沟通记录 (倒序，最近3条展开) ---
                st.markdown("### 💬 沟通记录")
                
                # 添加新记录
                log_input_col, channel_col = st.columns([4, 1])
                with log_input_col:
                    new_log_content = st.text_area(
                        "新沟通记录", 
                        key="new_comm_log", 
                        placeholder="输入沟通内容...",
                        height=80,
                        label_visibility="collapsed"
                    )
                with channel_col:
                    channel_options = ["微信", "脉脉", "LinkedIn", "邮件", "电话"]
                    channel_values = ["wechat", "maimai", "linkedin", "email", "phone"]
                    selected_channel_label = st.selectbox("渠道", channel_options, key="comm_channel_select")
                    selected_channel = channel_values[channel_options.index(selected_channel_label)]
                    
                    direction_options = ["📤 我发的", "📥 对方发的"]
                    direction_values = ["outbound", "inbound"]
                    selected_dir_label = st.selectbox("方向", direction_options, key="comm_direction_select")
                    selected_direction = direction_values[direction_options.index(selected_dir_label)]
                
                if st.button("➕ 添加记录", key="add_comm_log", type="primary"):
                    if new_log_content:
                        from datetime import datetime
                        from sqlalchemy.orm.attributes import flag_modified
                        logs = list(cand.communication_logs) if cand.communication_logs else []
                        new_entry = {
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "channel": selected_channel,
                            "action": "manual_log",
                            "content": new_log_content,
                            "direction": selected_direction,
                        }
                        logs.insert(0, new_entry)
                        cand.communication_logs = logs
                        cand.last_communication_at = datetime.now()
                        flag_modified(cand, "communication_logs")
                        
                        # 如果对方回复了，自动更新阶段
                        if selected_direction == 'inbound' and cand.pipeline_stage in ('contacted', 'following_up'):
                            cand.pipeline_stage = 'replied'
                            cand.follow_up_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                        
                        db.commit()
                        st.toast("✅ 沟通记录已添加")
                        st.rerun()
                
                st.divider()
                
                # 显示历史记录 (倒序，最近3条默认展开)
                logs = cand.communication_logs or []
                if logs:
                    for i, log in enumerate(logs):
                        # 最近3条默认展开
                        is_recent = i < 3
                        
                        channel_icons = {"wechat": "💚微信", "maimai": "🟠脉脉", "linkedin": "🔵LinkedIn", "email": "📧邮件", "phone": "📞电话", "maimai_direct": "🟠脉脉", "system": "⚙️系统"}
                        dir_icons = {"outbound": "📤", "inbound": "📥", "system": "⚙️"}
                        ch = channel_icons.get(log.get('channel', ''), log.get('channel', ''))
                        d = dir_icons.get(log.get('direction', ''), '')
                        
                        with st.expander(f"🕐 {log.get('time', '')}  {ch} {d}", expanded=is_recent):
                            # 检查是否在编辑模式
                            edit_key = f"edit_log_{cand.id}_{i}"
                            is_editing = st.session_state.get(edit_key, False)
                            
                            edit_col, del_col = st.columns([1, 1])
                            with edit_col:
                                if st.button("✏️ 编辑", key=f"edit_btn_{cand.id}_{i}"):
                                    st.session_state[edit_key] = not is_editing
                                    st.rerun()
                            with del_col:
                                if st.button("🗑️ 删除", key=f"del_log_{cand.id}_{i}"):
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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["人才列表", "导入导出", "好友标记", "批量画像", "搜索人才", "➕ 添加人才"])
        
        with tab1:
            # --- Search Filters (用 st.form 包裹，防止每次按键触发 rerun) ---
            with st.form("candidate_filter_form", border=False):
                with st.expander("🔍 筛选条件", expanded=True):
                    # 第一行：主要筛选条件
                    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.5, 1.5, 1.5, 0.6, 0.6])
                    with col1:
                        filter_name = st.text_input("姓名/关键词", value=st.session_state.get('filter_name', ''), key="filter_name_input", label_visibility="collapsed", placeholder="姓名/关键词")
                    with col2:
                        filter_company = st.text_input("公司", value=st.session_state.get('filter_company', ''), key="filter_company_input", label_visibility="collapsed", placeholder="公司")
                    with col3:
                        filter_school = st.text_input("名校/学历", value=st.session_state.get('filter_school', ''), key="filter_school_input", label_visibility="collapsed", placeholder="名校/学历")
                    with col4:
                        filter_location = st.text_input("期望地点", value=st.session_state.get('filter_location', ''), key="filter_location_input", label_visibility="collapsed", placeholder="期望地点")
                    with col5:
                        # 年龄改为数字输入
                        saved_age = st.session_state.get('filter_age', (20, 45))
                        age_min = st.number_input("年龄", min_value=18, max_value=60, value=saved_age[0], key="filter_age_min", label_visibility="collapsed", placeholder="最小")
                    with col6:
                        age_max = st.number_input("至", min_value=18, max_value=60, value=saved_age[1], key="filter_age_max", label_visibility="collapsed", placeholder="最大")
                    
                    col7, col8, col8b, col11 = st.columns([1, 1, 1, 0.6])
                    with col7:
                        friend_options = ["全部", "✅ 仅好友", "❌ 非好友"]
                        saved_friend_idx = friend_options.index(st.session_state.get('filter_friend', '全部')) if st.session_state.get('filter_friend') in friend_options else 0
                        filter_friend = st.selectbox("好友状态", friend_options, index=saved_friend_idx, key="filter_friend_input", label_visibility="collapsed")
                    with col8:
                        tier_filter_options = ["全部", "🔴 S-顶尖", "🟠 A+-卓越", "🟠 A-优秀", "🟡 B+-良好", "🟡 B-不错", "🟢 C-一般", "❓ 未分级"]
                        saved_tier_filter_idx = tier_filter_options.index(st.session_state.get('filter_tier', '全部')) if st.session_state.get('filter_tier') in tier_filter_options else 0
                        filter_tier = st.selectbox("人才分级", tier_filter_options, index=saved_tier_filter_idx, key="filter_tier_input", label_visibility="collapsed")
                    with col8b:
                        source_filter_options = ["全部", "🟦 脉脉", "💻 GitHub", "🔗 LinkedIn", "🟧 Boss", "❓ 其他"]
                        saved_source_idx = source_filter_options.index(st.session_state.get('filter_source', '全部')) if st.session_state.get('filter_source') in source_filter_options else 0
                        filter_source = st.selectbox("渠道", source_filter_options, index=saved_source_idx, key="filter_source_input", label_visibility="collapsed")
                    with col11:
                        st.form_submit_button("🔍 搜索", use_container_width=True)
                    
                    # 第三行：联系方式筛选
                    st.caption("📞 联系方式筛选")
                    cc1, cc2, cc3, cc4, cc5, cc6 = st.columns(6)
                    with cc1:
                        f_has_phone = st.checkbox("📱 有电话", value=st.session_state.get('_persist_has_phone', False), key="filter_has_phone")
                    with cc2:
                        f_has_email = st.checkbox("📧 有邮件", value=st.session_state.get('_persist_has_email', False), key="filter_has_email")
                    with cc3:
                        f_has_linkedin = st.checkbox("🔗 有LinkedIn", value=st.session_state.get('_persist_has_linkedin', False), key="filter_has_linkedin")
                    with cc4:
                        f_has_github = st.checkbox("💻 有GitHub", value=st.session_state.get('_persist_has_github', False), key="filter_has_github")
                    with cc5:
                        f_has_website = st.checkbox("🌐 有网站", value=st.session_state.get('_persist_has_website', False), key="filter_has_website")
                    with cc6:
                        f_has_friend = st.checkbox("🤝 加好友", value=st.session_state.get('_persist_has_friend', False), key="filter_has_friend")
            
            # Form 提交后更新 session_state（在 form 外部）
            st.session_state.filter_name = filter_name
            st.session_state.filter_company = filter_company
            st.session_state.filter_school = filter_school
            st.session_state.filter_location = filter_location
            st.session_state.filter_age = (age_min, age_max)
            st.session_state.filter_friend = filter_friend
            st.session_state.filter_tier = filter_tier
            st.session_state.filter_source = filter_source
            st.session_state._persist_has_phone = f_has_phone
            st.session_state._persist_has_email = f_has_email
            st.session_state._persist_has_linkedin = f_has_linkedin
            st.session_state._persist_has_github = f_has_github
            st.session_state._persist_has_website = f_has_website
            st.session_state._persist_has_friend = f_has_friend
            
            # 操作按钮（表单外部）
            _btn_col1, _btn_col2, _btn_spacer = st.columns([0.5, 0.5, 5])
            with _btn_col1:
                if st.button("🔄 刷新", help="重新加载候选人列表"):
                    st.rerun()
            with _btn_col2:
                def _do_clear_filters():
                    """Callback: 在 rerun 之前清空所有筛选条件"""
                    for _wk in ['filter_name_input','filter_company_input','filter_school_input','filter_location_input',
                                'filter_age_min','filter_age_max',
                                'filter_friend_input','filter_tier_input','filter_source_input',
                                'filter_has_phone','filter_has_email','filter_has_linkedin','filter_has_github','filter_has_website','filter_has_friend']:
                        st.session_state.pop(_wk, None)
                    st.session_state.filter_name = ''
                    st.session_state.filter_company = ''
                    st.session_state.filter_school = ''
                    st.session_state.filter_location = ''
                    st.session_state.filter_age = (20, 45)
                    st.session_state.filter_friend = '全部'
                    st.session_state.filter_tier = '全部'
                    st.session_state.filter_source = '全部'
                    for _ck in ['_persist_has_phone','_persist_has_email','_persist_has_linkedin','_persist_has_github','_persist_has_website','_persist_has_friend']:
                        st.session_state[_ck] = False
                st.button("🧹 清空", help="清空所有筛选条件", on_click=_do_clear_filters)
            
            # --- Query Data ---
            _perf_query_start = _time.time()
            _perf_logger.debug(f"开始构建查询 — 距脚本启动 {_perf_query_start - _PERF_SCRIPT_START:.3f}s, 距进入页面 {_perf_query_start - _perf_page_enter:.3f}s")
            query = db.query(Candidate).options(
                defer(Candidate.raw_resume_text),
                defer(Candidate.ai_summary),
                defer(Candidate.project_experiences),
                defer(Candidate.structured_tags),
                defer(Candidate.communication_logs),
                defer(Candidate.awards_achievements),
            ).filter(Candidate.name != "Parse Error")
            
            if filter_name:
                import re as _re
                # 智能搜索：纯中文名(2-4字)只搜name字段，避免扫描skills JSON
                _is_chinese_name = bool(_re.match(r'^[\u4e00-\u9fff]{2,4}$', filter_name.strip()))
                _perf_logger.debug(f"搜索关键词='{filter_name}', 中文名={_is_chinese_name}")
                if _is_chinese_name:
                    query = query.filter(Candidate.name.contains(filter_name))
                else:
                    query = query.filter(Candidate.name.contains(filter_name) | Candidate.skills.cast(String).contains(filter_name))
            
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
            
            # 人才分级筛选
            tier_filter_map = {"🔴 S-顶尖": "S", "🟠 A+-卓越": "A+", "🟠 A-优秀": "A", "🟡 B+-良好": "B+", "🟡 B-不错": "B", "🟢 C-一般": "C"}
            if filter_tier in tier_filter_map:
                query = query.filter(Candidate.talent_tier == tier_filter_map[filter_tier])
            elif filter_tier == "❓ 未分级":
                from sqlalchemy import or_
                query = query.filter(or_(Candidate.talent_tier == None, Candidate.talent_tier == ''))
            
            # 渠道筛选
            source_filter_map = {"🟦 脉脉": "脉脉", "💻 GitHub": "github", "🔗 LinkedIn": "linkedin", "🟧 Boss": "Boss", "📷 图片OCR": "图片OCR", "📄 PDF解析": "PDF解析"}
            if filter_source in source_filter_map:
                query = query.filter(Candidate.source.contains(source_filter_map[filter_source]))
            elif filter_source == "❓ 其他":
                from sqlalchemy import or_, and_, not_
                known_sources = ['maimai', 'github', 'linkedin', 'boss', '图片OCR', 'PDF解析']
                conditions = [not_(Candidate.source.contains(s)) for s in known_sources]
                query = query.filter(and_(Candidate.source != None, *conditions))
            
            # 联系方式筛选
            if f_has_phone:
                query = query.filter(Candidate.phone != None, Candidate.phone != '')
            if f_has_email:
                query = query.filter(Candidate.email != None, Candidate.email != '')
            if f_has_linkedin:
                query = query.filter(Candidate.linkedin_url != None, Candidate.linkedin_url != '')
            if f_has_github:
                query = query.filter(Candidate.github_url != None, Candidate.github_url != '')
            if f_has_website:
                query = query.filter(Candidate.personal_website != None, Candidate.personal_website != '')
            if f_has_friend:
                query = query.filter(Candidate.is_friend == 1)
            
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

            # --- 分页设置（在查询前设置）---
            # 表头：只显示总数和每页选择
            header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
            
            with header_col2:
                page_size = st.selectbox("每页显示", [20, 50], key="page_size", label_visibility="collapsed")
            
            with header_col3:
                sort_option = st.selectbox("排序", ["最新导入", "最近沟通", "姓名 A-Z", "姓名 Z-A"], label_visibility="collapsed")
            
            # 使用SQL排序
            if sort_option == "姓名 A-Z":
                query = query.order_by(Candidate.name.asc())
            elif sort_option == "姓名 Z-A":
                query = query.order_by(Candidate.name.desc())
            elif sort_option == "最近沟通":
                # 使用 case 表达式实现 NULLS LAST（SQLite 兼容）
                from sqlalchemy import case
                query = query.order_by(
                    case((Candidate.last_communication_at == None, 1), else_=0),
                    Candidate.last_communication_at.desc()
                )
            else:  # 最新导入
                query = query.order_by(Candidate.created_at.desc())
            
            # 显示加载状态
            with st.spinner("🔍 正在筛选候选人..."):
                # 先获取总数（高效的count查询 — 用 func.count 避免构造ORM对象）
                from sqlalchemy import func as _func
                _perf_count_start = _time.time()
                total_count = query.with_entities(_func.count(Candidate.id)).scalar()
                _perf_count_end = _time.time()
                _perf_logger.debug(f"COUNT完成 = {total_count}条 — 耗时 {_perf_count_end - _perf_count_start:.3f}s, 距脚本启动 {_perf_count_end - _PERF_SCRIPT_START:.3f}s")
            
            with header_col1:
                st.markdown(f"共 **{total_count}** 人")
            
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
            
            # 使用SQL分页（高效）
            offset = (st.session_state.current_page - 1) * page_size
            _perf_page_start = _time.time()
            candidates_page = query.offset(offset).limit(page_size).all()
            _perf_page_end = _time.time()
            _perf_logger.debug(f"分页查询完成 — 取{len(candidates_page)}条, 耗时 {_perf_page_end - _perf_page_start:.3f}s, 距脚本启动 {_perf_page_end - _PERF_SCRIPT_START:.3f}s")

            # --- 卡片式列表 (参考脉脉UI) ---
            if candidates_page:
                _perf_render_start = _time.time()
                for _cand_idx, cand in enumerate(candidates_page):
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
                            
                            # 电话号码（过滤无效值）
                            valid_phone = cand.phone and len(cand.phone) >= 6 and '未' not in cand.phone and '无' not in cand.phone
                            phone_badge = f"📞 {cand.phone}" if valid_phone else ""
                            
                            # 预约日期徽章
                            schedule_badge = ""
                            if cand.scheduled_contact_date:
                                from datetime import date
                                try:
                                    sched_date = datetime.strptime(cand.scheduled_contact_date, "%Y-%m-%d").date()
                                    today = date.today()
                                    if sched_date == today:
                                        schedule_badge = "🔴今天"
                                    elif sched_date < today:
                                        schedule_badge = f"⚪{sched_date.month}/{sched_date.day}"  # 已过期
                                    else:
                                        schedule_badge = f"📅{sched_date.month}/{sched_date.day}"
                                except:
                                    pass
                            
                            # 人才分级徽章
                            tier_map = {'S': '🔴S', 'A+': '🟠A+', 'A': '🟠A', 'B+': '🟡B+', 'B': '🟡B', 'C': '🟢C'}
                            tier_str = tier_map.get(cand.talent_tier, '') if cand.talent_tier else ''
                            
                            st.markdown(f"### {tier_str} {cand.name} {friend_badge} {phone_badge}")
                        
                        with top_right:
                            btn1, btn3, btn4 = st.columns([2, 1, 1])
                            if btn1.button("📄 详情", key=f"view_{cand.id}", use_container_width=True):
                                st.session_state.selected_candidate_id = cand.id
                                st.session_state.view_mode = 'detail'
                                st.rerun()
                            # 预约沟通 - 使用 popover 弹出面板
                            with btn3.popover("📅", help="预约沟通"):
                                from datetime import date, timedelta
                                today = date.today()
                                tomorrow = today + timedelta(days=1)
                                day_after = today + timedelta(days=2)
                                days_until_monday = (7 - today.weekday()) % 7
                                if days_until_monday == 0:
                                    days_until_monday = 7
                                next_monday = today + timedelta(days=days_until_monday)
                                
                                # 显示当前预约状态
                                if cand.scheduled_contact_date:
                                    st.caption(f"⚡ 已预约: {cand.scheduled_contact_date}")
                                
                                # 紧凑三列快捷按钮
                                c1, c2, c3 = st.columns(3)
                                if c1.button("今天", key=f"pop_today_{cand.id}"):
                                    cand.scheduled_contact_date = today.strftime("%Y-%m-%d")
                                    db.commit()
                                    st.rerun()
                                if c2.button("明天", key=f"pop_tom_{cand.id}"):
                                    cand.scheduled_contact_date = tomorrow.strftime("%Y-%m-%d")
                                    db.commit()
                                    st.rerun()
                                if c3.button("后天", key=f"pop_da_{cand.id}"):
                                    cand.scheduled_contact_date = day_after.strftime("%Y-%m-%d")
                                    db.commit()
                                    st.rerun()
                                
                                # 自定义日期 - 紧凑版
                                max_date = today + timedelta(days=90)
                                dc1, dc2 = st.columns([2, 1])
                                sel_date = dc1.date_input("预约日期", value=tomorrow, min_value=today, max_value=max_date, key=f"pop_date_{cand.id}", label_visibility="collapsed")
                                if dc2.button("✓", key=f"pop_conf_{cand.id}", type="primary"):
                                    cand.scheduled_contact_date = sel_date.strftime("%Y-%m-%d")
                                    db.commit()
                                    st.rerun()
                                
                                # 清除预约
                                if cand.scheduled_contact_date:
                                    if st.button("🗑️ 清除", key=f"pop_clr_{cand.id}", use_container_width=True):
                                        cand.scheduled_contact_date = None
                                        db.commit()
                                        st.rerun()
                            if btn4.button("🗑️", key=f"del_{cand.id}", help="删除"):
                                delete_candidate(cand.id)
                                st.rerun()
                        
                        # 主体：左侧基础信息 + 中间时间线
                        left_col, mid_col = st.columns([1.2, 2])
                        
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
                            
                            # 联系方式
                            _contacts = []
                            if cand.phone:
                                _contacts.append(f"📱 {cand.phone}")
                            if cand.email:
                                _contacts.append(f"📧 {cand.email}")
                            if cand.linkedin_url:
                                _contacts.append(f"[🔗 LI]({cand.linkedin_url})")
                            if cand.github_url:
                                _contacts.append(f"[💻 GH]({cand.github_url})")
                            if _contacts:
                                st.markdown(" │ ".join(_contacts))
                            
                            # 技能标签
                            if cand.skills and isinstance(cand.skills, list):
                                tags = " ".join([f"`{s}`" for s in cand.skills[:5]])
                                st.markdown(f"🏷️ {tags}")
                            
                            # 进入渠道
                            if cand.source:
                                _src_map = {'maimai': '🟦脉脉', 'github': '💻GitHub', 'linkedin': '🔗LinkedIn', 'boss': '🟧Boss'}
                                _src_parts = []
                                for _k, _v in _src_map.items():
                                    if _k in (cand.source or '').lower() and _v not in _src_parts:
                                        _src_parts.append(_v)
                                if not _src_parts:
                                    _src_parts = [cand.source[:20]]
                                st.caption(f"📂 {' '.join(_src_parts)}")
                            
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
                                    # 兼容多种时间格式
                                    time_str = w.get('time', '') or w.get('time_range', '')
                                    if not time_str:
                                        start = w.get('start_date', '')
                                        end = w.get('end_date', '')
                                        if start and end:
                                            time_str = f"{start}-{end}"
                                        elif w.get('duration'):
                                            time_str = w.get('duration')
                                    company = w.get('company', '') or ''
                                    title = w.get('position') or w.get('title', '') or ''
                                    
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
                        
                        st.markdown("")  # 卡片底部间距
                
                _perf_render_end = _time.time()
                _perf_logger.debug(f"渲染{len(candidates_page)}张卡片完成 — 耗时 {_perf_render_end - _perf_render_start:.3f}s, 距脚本启动 {_perf_render_end - _PERF_SCRIPT_START:.3f}s")
                _perf_logger.debug(f"====== 总耗时 {_perf_render_end - _PERF_SCRIPT_START:.3f}s ======\n")
                
                # --- 底部分页控件 ---
                st.divider()
                prev_col, info_col, next_col, jump_col = st.columns([1, 1, 1, 1.5])
                with prev_col:
                    if st.button("◀ 上一页", disabled=st.session_state.current_page <= 1, use_container_width=True, key="prev_page"):
                        st.session_state.current_page -= 1
                        st.rerun()
                with info_col:
                    st.markdown(f"<div style='text-align:center;padding-top:8px;font-size:16px;'><b>{st.session_state.current_page}</b> / {total_pages} 页</div>", unsafe_allow_html=True)
                with next_col:
                    if st.button("下一页 ▶", disabled=st.session_state.current_page >= total_pages, use_container_width=True, key="next_page"):
                        st.session_state.current_page += 1
                        st.rerun()
                with jump_col:
                    jump_page = st.number_input("跳转", min_value=1, max_value=max(total_pages, 1), value=st.session_state.current_page, step=1, key="page_jump", label_visibility="collapsed")
                    if jump_page != st.session_state.current_page:
                        st.session_state.current_page = jump_page
                        st.rerun()
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

        with tab6:
            st.subheader("➕ 添加人才")

            # 三种录入模式选择
            mode = st.radio(
                "选择录入方式",
                ["⚡ 快速录入", "📝 标准录入", "🤖 简历解析"],
                index=2,  # 默认选择"简历解析"
                horizontal=True,
                label_visibility="collapsed"
            )

            if mode == "⚡ 快速录入":
                st.info("💡 快速录入适用于简单记录人才联系方式，30秒内完成")

                with st.form("quick_add_form"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        name = st.text_input("✅ 姓名*", placeholder="张三")
                    with col2:
                        company = st.text_input("✅ 公司*", placeholder="阿里巴巴")
                    with col3:
                        title = st.text_input("✅ 职位*", placeholder="算法工程师")

                    col4, col5, col6 = st.columns(3)
                    with col4:
                        phone = st.text_input("📱 电话", placeholder="13800138000")
                    with col5:
                        email = st.text_input("📧 邮箱", placeholder="zhangsan@example.com")
                    with col6:
                        quick_tags = st.text_input("🏷️ 快速标签", placeholder="Python, NLP, 5年经验")

                    # 提交按钮
                    submitted = st.form_submit_button("➕ 快速添加", type="primary")
                    if submitted:
                        if not name or not company or not title:
                            st.error("❌ 姓名公司职位为必填项")
                        else:
                            # 解析快速标签到技能列表
                            skills = [t.strip() for t in quick_tags.split(",") if t.strip()] if quick_tags else []

                            # 创建候选人
                            new_candidate = Candidate(
                                name=name,
                                current_company=company,
                                current_title=title,
                                phone=phone or None,
                                email=email or None,
                                skills=skills,
                                source_file='manual_quick',
                                created_at=datetime.now()
                            )

                            # 生成简单的 AI 总结
                            if skills:
                                new_candidate.ai_summary = f"**技能标签**: {', '.join(skills)}\n\n快速录入记录，待完善详细信息。"
                            else:
                                new_candidate.ai_summary = "快速录入记录，待完善详细信息。"

                            db.add(new_candidate)
                            db.commit()

                            # 自动提取标签
                            try:
                                with st.spinner("🏷️ 正在为候选人生成标签..."):
                                    print(f"📌 [快速录入] 开始为 {new_candidate.name} 提取标签...")
                                    tags = extract_candidate_tags(new_candidate)
                                    if tags:
                                        # 使用直接SQL更新
                                        import sqlite3
                                        conn = sqlite3.connect('/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db')
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "UPDATE candidates SET structured_tags = ? WHERE id = ?",
                                            (json.dumps(tags, ensure_ascii=False), new_candidate.id)
                                        )
                                        conn.commit()
                                        conn.close()
                                        print(f"✅ 标签提取成功并保存到数据库: {tags}")
                                        st.info("🏷️ 已生成结构化标签")
                                    else:
                                        print(f"⚠️ 标签提取返回空")
                            except Exception as tag_error:
                                print(f"❌ [快速录入] 标签提取异常: {tag_error}")

                            st.success(f"✅ 成功添加人才: {name}")
                            st.balloons()
                            st.rerun()

            elif mode == "📝 标准录入":
                st.info("💡 标准录入适用于完整的人才信息录入，工作/教育经历可直接粘贴，系统会自动解析")

                with st.form("standard_add_form"):
                    st.markdown("### 基本信息")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        std_name = st.text_input("✅ 姓名*", placeholder="张三")
                    with col2:
                        std_age = st.number_input("年龄", min_value=0, max_value=100, value=0, step=1)
                    with col3:
                        std_exp_years = st.number_input("工作年限", min_value=0, max_value=50, value=0, step=1)
                    with col4:
                        edu_options = ["未知", "大专", "本科", "硕士", "博士", "其他"]
                        std_edu_level = st.selectbox("学历", edu_options)

                    std_location = st.text_input("📍 期望工作地点", placeholder="北京/上海/杭州/深圳")

                    st.markdown("### 职位信息")
                    col5, col6 = st.columns(2)
                    with col5:
                        std_company = st.text_input("✅ 当前公司*", placeholder="阿里巴巴")
                    with col6:
                        std_title = st.text_input("✅ 当前职位*", placeholder="算法工程师")

                    st.markdown("### 联系方式")
                    col7, col8 = st.columns(2)
                    with col7:
                        std_phone = st.text_input("📱 电话", placeholder="13800138000")
                    with col8:
                        std_email = st.text_input("📧 邮箱", placeholder="zhangsan@example.com")

                    col9, col10, col11 = st.columns(3)
                    with col9:
                        std_linkedin = st.text_input("🔗 LinkedIn", placeholder="https://linkedin.com/in/...")
                    with col10:
                        std_github = st.text_input("💻 GitHub", placeholder="https://github.com/...")
                    with col11:
                        std_twitter = st.text_input("🐦 Twitter", placeholder="https://twitter.com/...")

                    selected_skills = []  # 保留变量以兼容后续代码

                    st.markdown("### 工作经历")
                    st.caption("💡 直接粘贴简历中的工作经历，系统会自动解析时间、公司、职位、工作内容")
                    work_exp_text = st.text_area(
                        "工作经历", 
                        height=200,
                        placeholder="""示例格式（支持多种格式）:

2022.03 - 至今 | 字节跳动 | 高级算法工程师
负责大模型训练和推理优化，主导了RAG系统的架构设计

2020.07 - 2022.02 | 阿里巴巴 | 算法工程师
参与推荐算法优化，提升CTR 15%""",
                        label_visibility="collapsed"
                    )

                    st.markdown("### 教育经历")
                    st.caption("💡 直接粘贴教育经历，系统会自动解析学校、专业、学历、时间")
                    edu_exp_text = st.text_area(
                        "教育经历",
                        height=120,
                        placeholder="""示例格式:

2016-2020 | 清华大学 | 计算机科学与技术 | 本科
2020-2023 | 北京大学 | 人工智能 | 硕士""",
                        label_visibility="collapsed"
                    )

                    st.markdown("### 备注")
                    std_notes = st.text_area("📝 备注", height=100, placeholder="候选人的其他信息...")

                    # 提交按钮
                    submitted = st.form_submit_button("➕ 标准添加", type="primary")
                    if submitted:
                        if not std_name or not std_company or not std_title:
                            st.error("❌ 姓名、公司、职位为必填项")
                        else:
                            # 使用LLM解析工作经历和教育经历
                            work_experiences = []
                            education_details = []
                            
                            if work_exp_text.strip() or edu_exp_text.strip():
                                with st.spinner("🤖 AI正在解析经历信息..."):
                                    try:
                                        from openai import OpenAI
                                        client = OpenAI(
                                            api_key=os.getenv('DASHSCOPE_API_KEY'),
                                            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                                        )
                                        
                                        parse_prompt = f"""请解析以下工作经历和教育经历文本，返回JSON格式。

工作经历文本：
{work_exp_text if work_exp_text.strip() else "(无)"}

教育经历文本：
{edu_exp_text if edu_exp_text.strip() else "(无)"}

请返回如下JSON格式（不要有其他内容）：
{{
  "work_experiences": [
    {{"time": "2022.03-至今", "company": "字节跳动", "title": "高级算法工程师", "description": "工作内容..."}}
  ],
  "education_details": [
    {{"year": "2020-2023", "school": "北京大学", "major": "人工智能", "degree": "硕士"}}
  ]
}}

注意：
- 如果某个字段无法识别，设为空字符串
- 保持原文中的时间格式
- 如果没有对应经历，返回空数组[]"""

                                        response = client.chat.completions.create(
                                            model="qwen-plus",
                                            messages=[{"role": "user", "content": parse_prompt}],
                                            temperature=0.1
                                        )
                                        
                                        result_text = response.choices[0].message.content.strip()
                                        # 提取JSON部分
                                        if "```json" in result_text:
                                            result_text = result_text.split("```json")[1].split("```")[0]
                                        elif "```" in result_text:
                                            result_text = result_text.split("```")[1].split("```")[0]
                                        
                                        import json
                                        parsed = json.loads(result_text)
                                        work_experiences = parsed.get("work_experiences", [])
                                        education_details = parsed.get("education_details", [])
                                        
                                    except Exception as e:
                                        st.warning(f"⚠️ AI解析失败，将保存原始文本: {e}")
                                        # 失败时保存原始文本
                                        if work_exp_text.strip():
                                            work_experiences = [{"raw_text": work_exp_text}]
                                        if edu_exp_text.strip():
                                            education_details = [{"raw_text": edu_exp_text}]
                            
                            # 创建候选人
                            new_candidate = Candidate(
                                name=std_name,
                                age=std_age if std_age > 0 else None,
                                experience_years=std_exp_years if std_exp_years > 0 else None,
                                education_level=std_edu_level if std_edu_level != "未知" else None,
                                expect_location=std_location or None,
                                current_company=std_company,
                                current_title=std_title,
                                phone=std_phone or None,
                                email=std_email or None,
                                linkedin_url=std_linkedin or None,
                                github_url=std_github or None,
                                twitter_url=std_twitter or None,
                                skills=selected_skills if selected_skills else None,
                                work_experiences=work_experiences if work_experiences else None,
                                education_details=education_details if education_details else None,
                                notes=std_notes or None,
                                source_file='manual_standard',
                                created_at=datetime.now()
                            )

                            # 生成结构化标签（不是AI画像）
                            with st.spinner("🏷️ 正在生成人才标签..."):
                                try:
                                    # 构建候选人信息文本
                                    resume_text_parts = []
                                    if work_experiences:
                                        for exp in work_experiences:
                                            if exp.get('company'):
                                                resume_text_parts.append(f"{exp.get('time','')} {exp.get('company','')} {exp.get('title','')} {exp.get('description','')}")
                                    if education_details:
                                        for edu in education_details:
                                            if edu.get('school'):
                                                resume_text_parts.append(f"{edu.get('year','')} {edu.get('school','')} {edu.get('major','')} {edu.get('degree','')}")
                                    
                                    resume_summary = "\n".join(resume_text_parts) if resume_text_parts else ""
                                    
                                    tag_prompt = f"""请从以下候选人信息中提取结构化标签。

## 标签体系说明

1. tech_domain (技术方向) - 多选:
   【AI】大模型/LLM, Agent/智能体, NLP, 多模态, 语音, CV, 推荐系统, 搜索, AI Infra, 具身智能, 垂直应用
   【工程】客户端开发, 后端开发, 前端开发, 基础架构/Infra, 音视频 (不要用"其他")

2. core_specialty (核心专长) - 多选1-2个:
   【AI】语音合成, 语音识别, 多模态理解, 多模态生成, 图像/视频生成, 推荐系统, 搜索排序, Agent/智能体开发, 对话系统, 代码生成
   【工程】IM/即时通讯, 跨端框架, 客户端基础架构, 音视频引擎, 微服务架构, DevOps

3. tech_skills (技术技能) - 多选1-3个:
   【AI】预训练, SFT微调, RLHF/对齐, 推理加速, 模型压缩/量化, 分布式训练, RAG/知识库, 算子优化, 框架开发
   【工程】跨端开发, 性能优化, 高并发, 架构设计

4. role_type (岗位类型) - 单选:
   算法工程师, 算法专家, 算法研究员, 客户端工程师, 后端工程师, 前端工程师, 架构师, 工程开发, 解决方案架构师, 产品经理, 技术管理, 研究员

5. seniority (职级层次) - 单选:
   初级(0-3年), 中级(3-5年), 资深(5-10年), 专家(10年+), 管理层

6. industry_exp (行业背景) - 多选:
   互联网大厂, AI独角兽, 云厂商, 芯片/硬件, 外企, 学术背景

【候选人信息】
姓名: {std_name}
当前职位: {std_title}
当前公司: {std_company}
工作年限: {std_exp_years if std_exp_years > 0 else '未知'}年
学历: {std_edu_level}
经历: {resume_summary[:1500]}

请输出JSON格式，只输出JSON:
{{
  "tech_domain": ["技术方向"],
  "core_specialty": ["核心专长"],
  "tech_skills": ["技术技能"],
  "role_type": "岗位类型",
  "seniority": "职级层次",
  "industry_exp": ["行业背景"]
}}"""

                                    tag_response = client.chat.completions.create(
                                        model="qwen-plus",
                                        messages=[{"role": "user", "content": tag_prompt}],
                                        temperature=0.1
                                    )
                                    
                                    tag_result = tag_response.choices[0].message.content.strip()
                                    if "```json" in tag_result:
                                        tag_result = tag_result.split("```json")[1].split("```")[0]
                                    elif "```" in tag_result:
                                        tag_result = tag_result.split("```")[1].split("```")[0]
                                    
                                    structured_tags = json.loads(tag_result)
                                    new_candidate.structured_tags = structured_tags
                                    
                                except Exception as e:
                                    st.warning(f"⚠️ 标签生成失败: {e}")

                            # 简单的AI总结
                            summary_parts = []
                            if work_experiences:
                                companies = [exp.get('company', '') for exp in work_experiences if exp.get('company')]
                                if companies:
                                    summary_parts.append(f"**工作经历**: {', '.join(companies[:3])}")
                            if education_details:
                                schools = [edu.get('school', '') for edu in education_details if edu.get('school')]
                                if schools:
                                    summary_parts.append(f"**教育背景**: {', '.join(schools[:2])}")

                            new_candidate.ai_summary = "\n\n".join(summary_parts) if summary_parts else "标准录入记录。"

                            db.add(new_candidate)
                            db.commit()

                            # 自动提取标签
                            try:
                                with st.spinner("🏷️ 正在为候选人生成标签..."):
                                    print(f"📌 [标准录入] 开始为 {new_candidate.name} 提取标签...")
                                    tags = extract_candidate_tags(new_candidate)
                                    if tags:
                                        # 使用直接SQL更新
                                        import sqlite3
                                        conn = sqlite3.connect('/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db')
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "UPDATE candidates SET structured_tags = ? WHERE id = ?",
                                            (json.dumps(tags, ensure_ascii=False), new_candidate.id)
                                        )
                                        conn.commit()
                                        conn.close()
                                        print(f"✅ 标签提取成功并保存到数据库: {tags}")
                                    else:
                                        print(f"⚠️ 标签提取返回空")
                            except Exception as tag_error:
                                print(f"❌ [标准录入] 标签提取异常: {tag_error}")

                            st.success(f"✅ 成功添加人才: {std_name}")
                            if work_experiences:
                                st.info(f"📋 解析到 {len(work_experiences)} 段工作经历")
                            if education_details:
                                st.info(f"🎓 解析到 {len(education_details)} 段教育经历")
                            if hasattr(new_candidate, 'structured_tags') and new_candidate.structured_tags:
                                st.info(f"🏷️ 已生成结构化标签")
                            st.balloons()
                            st.rerun()

            elif mode == "🤖 简历解析":
                st.markdown("### 上传简历")
                
                # 解析模式选择
                parse_mode_col1, parse_mode_col2 = st.columns(2)
                with parse_mode_col1:
                    parse_mode = st.radio(
                        "解析模式", 
                        ["⚡ 立即解析", "🕐 后台解析"],
                        horizontal=True,
                        help="后台解析：上传后自动加入处理队列，完成后会在页面顶部通知"
                    )
                
                # 检测是否是图片类型的上传（用于多选）
                upload_type = st.radio("选择上传类型", ["📄 文档 (PDF/TXT/DOCX)", "🖼️ 图片 (可多选)"], horizontal=True, label_visibility="collapsed")
                
                # === 后台解析模式 ===
                if parse_mode == "🕐 后台解析":
                    from database import ResumeTask
                    import os
                    import uuid
                    
                    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    
                    if upload_type == "📄 文档 (PDF/TXT/DOCX)":
                        uploaded_files_bg = st.file_uploader(
                            "支持格式: PDF, TXT, DOCX（可多选）",
                            type=['pdf', 'txt', 'docx'],
                            accept_multiple_files=True,
                            key="bg_doc_upload"
                        )
                        
                        if uploaded_files_bg:
                            st.info(f"已选择 {len(uploaded_files_bg)} 个文件")
                            
                            if st.button("📤 加入处理队列", type="primary", key="queue_docs"):
                                added = 0
                                for uf in uploaded_files_bg:
                                    # 保存文件
                                    ext = uf.name.split('.')[-1].lower()
                                    unique_name = f"{uuid.uuid4().hex[:8]}_{uf.name}"
                                    file_path = os.path.join(UPLOAD_DIR, unique_name)
                                    
                                    with open(file_path, 'wb') as f:
                                        f.write(uf.read())
                                    
                                    # 创建任务
                                    task = ResumeTask(
                                        file_path=file_path,
                                        file_name=uf.name,
                                        file_type=ext,
                                        status='pending'
                                    )
                                    db.add(task)
                                    added += 1
                                
                                db.commit()
                                st.success(f"✅ 已添加 {added} 个文件到处理队列！")
                                st.info("💡 后台Worker会自动处理，完成后刷新页面可在顶部看到结果")
                                st.rerun()
                    
                    else:  # 图片上传
                        uploaded_files_bg = st.file_uploader(
                            "支持格式: PNG, JPG, JPEG（可多选）",
                            type=['png', 'jpg', 'jpeg'],
                            accept_multiple_files=True,
                            key="bg_img_upload"
                        )
                        
                        if uploaded_files_bg:
                            st.info(f"已选择 {len(uploaded_files_bg)} 张图片")
                            
                            # 预览
                            cols = st.columns(min(len(uploaded_files_bg), 4))
                            for idx, f in enumerate(uploaded_files_bg):
                                with cols[idx % 4]:
                                    st.image(f, caption=f.name, use_container_width=True)
                            
                            if st.button("📤 加入处理队列", type="primary", key="queue_imgs"):
                                added = 0
                                for uf in uploaded_files_bg:
                                    ext = uf.name.split('.')[-1].lower()
                                    unique_name = f"{uuid.uuid4().hex[:8]}_{uf.name}"
                                    file_path = os.path.join(UPLOAD_DIR, unique_name)
                                    
                                    with open(file_path, 'wb') as f:
                                        f.write(uf.read())
                                    
                                    task = ResumeTask(
                                        file_path=file_path,
                                        file_name=uf.name,
                                        file_type=ext,
                                        status='pending'
                                    )
                                    db.add(task)
                                    added += 1
                                
                                db.commit()
                                st.success(f"✅ 已添加 {added} 张图片到处理队列！")
                                st.info("💡 后台Worker会自动处理，完成后刷新页面可在顶部看到结果")
                                st.rerun()
                
                # === 立即解析模式（原有逻辑）===
                elif upload_type == "📄 文档 (PDF/TXT/DOCX)":
                    uploaded_file = st.file_uploader(
                        "支持格式: PDF, TXT, DOCX",
                        type=['pdf', 'txt', 'docx'],
                        help="上传候选人的简历文件"
                    )
                    
                    if uploaded_file:
                        st.success(f"✅ 已上传文件: {uploaded_file.name}")

                        # 读取文件内容
                        if uploaded_file.name.endswith('.txt'):
                            resume_content = uploaded_file.read().decode('utf-8')
                            st.text_area("简历内容预览", value=resume_content[:500] + "...", height=200, disabled=True)

                            if st.button("🚀 开始 AI 解析", type="primary"):
                                with st.spinner("正在解析简历..."):
                                    parsed_data = AIService.parse_resume(resume_content)

                                    if parsed_data and parsed_data.get("name") != "Parse Error":
                                        st.success("✅ 解析成功！")
                                        st.json(parsed_data)
                                        st.session_state['txt_parsed_data'] = parsed_data
                                        st.session_state['txt_resume_content'] = resume_content
                                        st.session_state['txt_source_file'] = uploaded_file.name
                                    else:
                                        st.error("❌ 解析失败，请检查简历格式或重试")
                            
                            # 确认保存
                            if 'txt_parsed_data' in st.session_state and st.session_state.get('txt_source_file') == uploaded_file.name:
                                parsed_data = st.session_state['txt_parsed_data']
                                if st.button("💾 确认保存到人才库", type="primary", key="save_txt_resume"):
                                    new_candidate = Candidate(
                                        name=parsed_data.get("name", "未知"),
                                        email=parsed_data.get("email"),
                                        phone=parsed_data.get("phone"),
                                        age=parsed_data.get("age"),
                                        experience_years=parsed_data.get("experience_years"),
                                        expect_location=parsed_data.get("expect_location"),
                                        education_level=parsed_data.get("education_level"),
                                        current_company=parsed_data.get("current_company"),
                                        current_title=parsed_data.get("current_title"),
                                        skills=parsed_data.get("skills"),
                                        education_details=parsed_data.get("education_details"),
                                        work_experiences=parsed_data.get("work_experiences"),
                                        project_experiences=parsed_data.get("project_experiences"),
                                        ai_summary=parsed_data.get("summary"),
                                        raw_resume_text=st.session_state.get('txt_resume_content', ''),
                                        source_file=uploaded_file.name,
                                        source='文档解析',
                                        created_at=datetime.now()
                                    )
                                    db.add(new_candidate)
                                    db.commit()
                                    
                                    # 自动提取标签
                                    with st.spinner("🏷️ 正在为候选人生成标签..."):
                                        tags = extract_candidate_tags(new_candidate)
                                        if tags:
                                            # 使用直接SQL更新
                                            import sqlite3
                                            conn = sqlite3.connect('/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db')
                                            cursor = conn.cursor()
                                            cursor.execute(
                                                "UPDATE candidates SET structured_tags = ? WHERE id = ?",
                                                (json.dumps(tags, ensure_ascii=False), new_candidate.id)
                                            )
                                            conn.commit()
                                            conn.close()
                                            print(f"✅ 标签提取成功并保存到数据库: {tags}")
                                            st.info("🏷️ 已生成结构化标签")
                                    
                                    st.success(f"✅ 成功添加人才: {parsed_data.get('name')}")
                                    st.balloons()
                                    del st.session_state['txt_parsed_data']
                                    
                        elif uploaded_file.name.endswith('.pdf'):
                            try:
                                import PyPDF2
                                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                                resume_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                                st.text_area("简历内容预览", value=resume_content[:500] + "...", height=200, disabled=True)

                                if st.button("🚀 开始 AI 解析", type="primary"):
                                    with st.spinner("正在解析简历..."):
                                        print(f"📄 PDF简历内容长度: {len(resume_content)} 字符")
                                        parsed_data = AIService.parse_resume(resume_content)
                                        print(f"📊 解析结果: {json.dumps(parsed_data, ensure_ascii=False, indent=2)[:2000]}")
                                        if parsed_data and parsed_data.get("name") != "Parse Error":
                                            st.success("✅ 解析成功！")
                                            st.json(parsed_data)
                                            st.session_state['pdf_parsed_data'] = parsed_data
                                            st.session_state['pdf_resume_content'] = resume_content
                                            st.session_state['pdf_source_file'] = uploaded_file.name
                                        else:
                                            st.error("❌ 解析失败，请检查简历格式或重试")
                                
                                if 'pdf_parsed_data' in st.session_state and st.session_state.get('pdf_source_file') == uploaded_file.name:
                                    parsed_data = st.session_state['pdf_parsed_data']
                                    if st.button("💾 确认保存到人才库", type="primary", key="save_pdf_resume"):
                                        new_candidate = Candidate(
                                            name=parsed_data.get("name", "未知"),
                                            email=parsed_data.get("email"),
                                            phone=parsed_data.get("phone"),
                                            age=parsed_data.get("age"),
                                            experience_years=parsed_data.get("experience_years"),
                                            expect_location=parsed_data.get("expect_location"),
                                            education_level=parsed_data.get("education_level"),
                                            current_company=parsed_data.get("current_company"),
                                            current_title=parsed_data.get("current_title"),
                                            skills=parsed_data.get("skills"),
                                            education_details=parsed_data.get("education_details"),
                                            work_experiences=parsed_data.get("work_experiences"),
                                            project_experiences=parsed_data.get("project_experiences"),
                                            ai_summary=parsed_data.get("summary"),
                                            raw_resume_text=st.session_state.get('pdf_resume_content', ''),
                                            source_file=uploaded_file.name,
                                            source='PDF解析',
                                            created_at=datetime.now()
                                        )
                                        db.add(new_candidate)
                                        db.commit()
                                        
                                        # 保存原始PDF文件以支持下载
                                        try:
                                            resume_dir = "/Users/lillianliao/notion_rag/personal-ai-headhunter/data/resumes"
                                            os.makedirs(resume_dir, exist_ok=True)
                                            uploaded_file.seek(0)
                                            file_path = f"{resume_dir}/{new_candidate.id}_{uploaded_file.name}"
                                            with open(file_path, "wb") as f:
                                                f.write(uploaded_file.read())
                                            print(f"✅ 原始PDF文件已保存: {file_path}")
                                        except Exception as save_err:
                                            print(f"⚠️ PDF文件保存失败: {save_err}")
                                        
                                        # 自动提取标签
                                        try:
                                            with st.spinner("🏷️ 正在为候选人生成标签..."):
                                                print(f"📌 开始为 {new_candidate.name} 提取标签...")
                                                tags = extract_candidate_tags(new_candidate)
                                                if tags:
                                                    # 使用直接SQL更新，避免SQLAlchemy JSON字段检测问题
                                                    import sqlite3
                                                    conn = sqlite3.connect('/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db')
                                                    cursor = conn.cursor()
                                                    cursor.execute(
                                                        "UPDATE candidates SET structured_tags = ? WHERE id = ?",
                                                        (json.dumps(tags, ensure_ascii=False), new_candidate.id)
                                                    )
                                                    conn.commit()
                                                    conn.close()
                                                    print(f"✅ 标签提取成功并保存到数据库: {tags}")
                                                    st.info("🏷️ 已生成结构化标签")
                                                else:
                                                    print(f"⚠️ 标签提取返回空")
                                                    st.warning("⚠️ 标签生成失败，可稍后手动添加")
                                        except Exception as tag_error:
                                            print(f"❌ 标签提取异常: {tag_error}")
                                            st.warning(f"⚠️ 标签生成异常: {tag_error}")
                                        
                                        st.success(f"✅ 成功添加人才: {parsed_data.get('name')}")
                                        st.balloons()
                                        del st.session_state['pdf_parsed_data']
                            except ImportError:
                                st.error("❌ 缺少 PyPDF2 库，请运行: `pip install PyPDF2`")
                        else:
                            st.warning("⚠️ 暂不支持此格式")
                
                elif parse_mode == "⚡ 立即解析" and upload_type == "🖼️ 图片 (可多选)":  # 图片上传（支持多选）
                    uploaded_files = st.file_uploader(
                        "支持格式: PNG, JPG, JPEG（可多选）",
                        type=['png', 'jpg', 'jpeg'],
                        accept_multiple_files=True,
                        help="上传候选人的简历截图，支持多页简历"
                    )
                    
                    if uploaded_files:
                        st.success(f"✅ 已上传 {len(uploaded_files)} 张图片")
                        
                        # 显示所有图片预览
                        cols = st.columns(min(len(uploaded_files), 3))
                        for idx, f in enumerate(uploaded_files):
                            with cols[idx % 3]:
                                st.image(f, caption=f"第{idx+1}页: {f.name}", use_container_width=True)
                        
                        if st.button("🚀 开始 AI OCR 解析", type="primary"):
                            import base64
                            from io import BytesIO
                            
                            with st.spinner("正在处理图片..."):
                                # 如果是多张图片，先拼接成一张大图
                                if len(uploaded_files) > 1:
                                    try:
                                        from PIL import Image
                                        
                                        st.info(f"📐 正在拼接 {len(uploaded_files)} 张图片...")
                                        
                                        # 加载所有图片
                                        images = []
                                        for f in uploaded_files:
                                            img = Image.open(f)
                                            # 转换为RGB模式（处理RGBA或其他模式）
                                            if img.mode != 'RGB':
                                                img = img.convert('RGB')
                                            images.append(img)
                                        
                                        # 计算拼接后的尺寸（垂直拼接）
                                        max_width = max(img.width for img in images)
                                        total_height = sum(img.height for img in images)
                                        
                                        # 创建新图片并拼接
                                        combined = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                                        y_offset = 0
                                        for img in images:
                                            # 如果宽度不一致，居中放置
                                            x_offset = (max_width - img.width) // 2
                                            combined.paste(img, (x_offset, y_offset))
                                            y_offset += img.height
                                        
                                        # 如果图片太大，按比例缩放（最大高度4000像素）
                                        MAX_HEIGHT = 4000
                                        if total_height > MAX_HEIGHT:
                                            scale = MAX_HEIGHT / total_height
                                            new_width = int(max_width * scale)
                                            combined = combined.resize((new_width, MAX_HEIGHT), Image.Resampling.LANCZOS)
                                            st.info(f"📏 图片已缩放: {max_width}x{total_height} → {new_width}x{MAX_HEIGHT}")
                                        
                                        # 转为base64
                                        buffer = BytesIO()
                                        combined.save(buffer, format='JPEG', quality=90)
                                        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                                        
                                        st.success(f"✅ 图片拼接完成: {combined.width}x{combined.height}")
                                        
                                    except ImportError:
                                        st.error("❌ 需要安装 Pillow 库: `pip install Pillow`")
                                        st.stop()
                                else:
                                    # 单张图片直接转base64
                                    image_bytes = uploaded_files[0].getvalue()
                                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                                
                                st.info("🤖 正在识别简历内容...")
                                
                                # 一次性调用OCR
                                parsed_data = AIService.ocr_resume_image(image_base64)
                                
                                if parsed_data and parsed_data.get("name") != "OCR识别失败":
                                    st.success("✅ OCR 识别成功！")
                                    st.json(parsed_data)
                                    
                                    # 保存到 session state
                                    st.session_state['ocr_parsed_data'] = parsed_data
                                    st.session_state['ocr_source_files'] = [f.name for f in uploaded_files]
                                    st.session_state['ocr_raw_text'] = parsed_data.get('raw_text', '')
                                else:
                                    st.error("❌ OCR 识别失败，请尝试更清晰的图片")
                        
                        # 确认保存按钮
                        if 'ocr_parsed_data' in st.session_state:
                            parsed_data = st.session_state['ocr_parsed_data']
                            
                            if st.button("💾 确认保存到人才库", type="primary", key="save_ocr_resume"):
                                source_files = st.session_state.get('ocr_source_files', [])
                                new_candidate = Candidate(
                                    name=parsed_data.get("name", "未知"),
                                    email=parsed_data.get("email"),
                                    phone=parsed_data.get("phone"),
                                    age=parsed_data.get("age"),
                                    experience_years=parsed_data.get("experience_years"),
                                    expect_location=parsed_data.get("expect_location"),
                                    education_level=parsed_data.get("education_level"),
                                    current_company=parsed_data.get("current_company"),
                                    current_title=parsed_data.get("current_title"),
                                    skills=parsed_data.get("skills"),
                                    education_details=parsed_data.get("education_details"),
                                    work_experiences=parsed_data.get("work_experiences"),
                                    project_experiences=parsed_data.get("project_experiences"),
                                    awards_achievements=parsed_data.get("awards_achievements"),
                                    ai_summary=parsed_data.get("summary"),
                                    notes=parsed_data.get("notes"),
                                    raw_resume_text=st.session_state.get('ocr_raw_text', ''),
                                    source_file=f'ocr_upload_{"_".join(source_files[:3])}',
                                    source='图片OCR',
                                    created_at=datetime.now()
                                )

                                db.add(new_candidate)
                                db.commit()
                                
                                # 自动提取标签
                                try:
                                    with st.spinner("🏷️ 正在为候选人生成标签..."):
                                        print(f"📌 开始为 {new_candidate.name} 提取标签...")
                                        tags = extract_candidate_tags(new_candidate)
                                        if tags:
                                            # 使用直接SQL更新
                                            import sqlite3
                                            conn = sqlite3.connect('/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db')
                                            cursor = conn.cursor()
                                            cursor.execute(
                                                "UPDATE candidates SET structured_tags = ? WHERE id = ?",
                                                (json.dumps(tags, ensure_ascii=False), new_candidate.id)
                                            )
                                            conn.commit()
                                            conn.close()
                                            print(f"✅ 标签提取成功并保存到数据库: {tags}")
                                            st.info("🏷️ 已生成结构化标签")
                                        else:
                                            print(f"⚠️ 标签提取返回空")
                                            st.warning("⚠️ 标签生成失败，可稍后手动添加")
                                except Exception as tag_error:
                                    print(f"❌ 标签提取异常: {tag_error}")
                                    st.warning(f"⚠️ 标签生成异常: {tag_error}")

                                st.success(f"✅ 成功添加人才: {parsed_data.get('name')}")
                                st.balloons()
                                
                                # 清理 session state
                                del st.session_state['ocr_parsed_data']
                                if 'ocr_source_files' in st.session_state:
                                    del st.session_state['ocr_source_files']
                                if 'ocr_raw_text' in st.session_state:
                                    del st.session_state['ocr_raw_text']
                                
                                # 强制刷新页面，防止重复保存
                                st.rerun()
                    else:
                        st.info("👆 请先上传简历图片（可多选）")

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
            
            # --- 简洁Header（适合截图）---
            st.markdown(f"""
            <p style='color: #666; margin: 0 0 5px 0; font-size: 14px;'>编号: {job.job_code or '-'}</p>
            <h2 style='margin: 0 0 5px 0; font-weight: 700;'>{job.title}</h2>
            <p style='color: #666; margin: 0; font-size: 14px;'>
                {job.location or '地点不限'} | {job.required_experience_years or '经验不限'}年
            </p>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 提取字段
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
            
            dept = job.department if hasattr(job, 'department') and job.department else get_field(["部门", "department"], "")
            hr = job.hr_contact if hasattr(job, 'hr_contact') and job.hr_contact else get_field(["HR", "责任人", "recruiter"], "")
            jd_link = job.jd_link if hasattr(job, 'jd_link') and job.jd_link else get_field(["JD链接", "jd_link"], "")
            seniority = job.seniority_level if hasattr(job, 'seniority_level') and job.seniority_level else get_field(["职级", "level", "seniority"], "")
            
            # Content Layout - 左右两栏（左侧1，右侧1）
            main_col, right_col = st.columns([1, 1])
            
            with main_col:
                # --- 职位展示（蓝色竖线样式，适合截图）---
                jd_text = job.raw_jd_text or ""
                
                # 智能分段：用蓝色竖线区分"职位描述"和"职位要求"
                def format_jd_for_display(text):
                    lines = text.split('\n')
                    html_parts = []
                    current_section = None
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 检测分段标题（开启新的蓝色竖线区块）
                        is_desc_title = any(kw in line for kw in ['职位描述', '岗位描述', '工作职责', '职责描述'])
                        is_req_title = any(kw in line for kw in ['职位要求', '岗位要求', '任职要求', '任职资格'])
                        
                        if is_desc_title or is_req_title:
                            if current_section:
                                html_parts.append("</div>")
                            html_parts.append(f"<div style='border-left: 4px solid #4A90D9; padding-left: 15px; margin: 10px 0;'>")
                            # 标题行作为加粗文字显示
                            html_parts.append(f"<p style='margin: 0 0 8px 0; font-weight: bold; font-size: 16px;'>{line}</p>")
                            current_section = 'desc' if is_desc_title else 'req'
                        else:
                            # 普通内容
                            if not current_section:
                                html_parts.append(f"<div style='border-left: 4px solid #4A90D9; padding-left: 15px; margin: 10px 0;'>")
                                current_section = 'auto'
                            html_parts.append(f"<p style='margin: 3px 0; line-height: 1.5;'>{line}</p>")
                    
                    if current_section:
                        html_parts.append("</div>")
                    
                    return "\n".join(html_parts)
                
                # 渲染职位内容
                st.markdown(format_jd_for_display(jd_text), unsafe_allow_html=True)
                
                # ===== 编辑模式（放在左侧职位详情下方）=====
                if 'job_edit_mode' not in st.session_state:
                    st.session_state.job_edit_mode = False
                
                edit_mode = st.toggle("✏️ 编辑职位信息", value=st.session_state.job_edit_mode, key="job_edit_toggle")
                st.session_state.job_edit_mode = edit_mode
                
                if edit_mode:
                    # 编辑模式 - 显示所有可编辑字段
                    edit_c1, edit_c2 = st.columns(2)
                    with edit_c1:
                        new_seniority = st.text_input("职级", value=seniority or "", key="edit_seniority")
                        new_dept = st.text_input("部门", value=dept or "", key="edit_dept")
                        new_location = st.text_input("地点", value=job.location or "", key="edit_location")
                    with edit_c2:
                        new_exp = st.text_input("年限", value=str(job.required_experience_years or ""), key="edit_exp")
                        new_salary = st.text_input("薪资", value=job.salary_range or "", key="edit_salary")
                        new_hr = st.text_input("HR", value=hr or "", key="edit_hr")
                    new_link = st.text_input("JD链接", value=jd_link or "", key="edit_link")
                    
                    if st.button("💾 保存修改", key="save_job_info"):
                        job.seniority_level = new_seniority
                        job.department = new_dept
                        job.location = new_location
                        try:
                            job.required_experience_years = int(new_exp) if new_exp else None
                        except:
                            pass
                        job.salary_range = new_salary
                        job.hr_contact = new_hr
                        job.jd_link = new_link
                        db.commit()
                        st.success("已保存")
                        st.rerun()
                    
                    # 编辑JD内容
                    with st.expander("✏️ 编辑JD内容", expanded=False):
                        current_jd = job.raw_jd_text or ""
                        new_jd = st.text_area("", value=current_jd, height=300, key="edit_job_jd", label_visibility="collapsed")
                        if new_jd != current_jd:
                            job.raw_jd_text = new_jd
                            db.commit()
                            st.toast("JD已更新")
                            st.rerun()
            
            with right_col:
                # ===== 紧急程度设置（便捷按钮样式）=====
                st.markdown("<div style='margin-bottom:10px'><b>🚨 紧急程度</b></div>", unsafe_allow_html=True)
                urgency_options = ["普通", "较急", "紧急", "非常紧急"]
                urgency_colors = ["#e0e0e0", "#ffe082", "#ffb74d", "#ef5350"]
                current_urgency = getattr(job, 'urgency', 0) or 0
                
                # 使用4列按钮实现快速选择
                urg_cols = st.columns(4)
                for idx, (label, color) in enumerate(zip(urgency_options, urgency_colors)):
                    with urg_cols[idx]:
                        # 选中状态高亮
                        is_selected = current_urgency == idx
                        btn_style = f"background-color: {color}; border: 2px solid {'#333' if is_selected else 'transparent'}; border-radius: 4px; font-weight: {'bold' if is_selected else 'normal'};"
                        if st.button(f"{'✓ ' if is_selected else ''}{label}", key=f"urg_{idx}_{job.id}", use_container_width=True):
                            if current_urgency != idx:
                                job.urgency = idx
                                db.commit()
                                st.toast(f"已设置为: {label}")
                                st.rerun()
                
                # ===== 发布渠道 =====
                published = job.published_channels or []
                if isinstance(published, str):
                    try:
                        published = json.loads(published)
                    except:
                        published = []
                if published:
                    channel_map = {"MM": "🟠 脉脉", "LI": "🔵 LinkedIn", "BOSS": "🟢 Boss"}
                    ch_parts = []
                    for ch in published:
                        ch_name = channel_map.get(ch.get("channel"), ch.get("channel", ""))
                        ch_time = ch.get("published_at", "")[:10]  # 只取日期部分
                        ch_parts.append(f"{ch_name} ({ch_time})")
                    st.markdown(f"**📢 已发布**: {' / '.join(ch_parts)}")
                
                st.markdown("<hr style='margin: 10px 0; border-color: #eee;'>", unsafe_allow_html=True)
                
                # ===== 职级、部门、HR、链接并列第一排 =====
                info_parts = []
                if seniority:
                    info_parts.append(f"**职级**: {seniority}")
                if dept:
                    info_parts.append(f"**部门**: {dept}")
                if hr:
                    info_parts.append(f"**HR**: {hr}")
                if jd_link:
                    info_parts.append(f"[🔗原始JD]({jd_link})")
                if info_parts:
                    st.markdown(" | ".join(info_parts))
                
                # ===== 标签 =====
                st.markdown("<div style='margin-top:10px'><b>🏷️ 标签</b></div>", unsafe_allow_html=True)
                
                # 显示AI结构化标签
                if job.structured_tags:
                    try:
                        tags_data = json.loads(job.structured_tags) if isinstance(job.structured_tags, str) else job.structured_tags
                        tag_display = []
                        if tags_data.get('role_type'):
                            tag_display.append(f"🎯{tags_data['role_type']}")
                        if tags_data.get('seniority'):
                            tag_display.append(f"📊{tags_data['seniority']}")
                        if tags_data.get('tech_domain'):
                            domains = tags_data['tech_domain'] if isinstance(tags_data['tech_domain'], list) else [tags_data['tech_domain']]
                            tag_display.append(f"💻{', '.join(domains[:2])}")
                        if tag_display:
                            st.markdown(" | ".join(tag_display))
                    except:
                        pass
                
                # 自定义标签
                current_tags = ", ".join(job.project_tags) if job.project_tags else ""
                new_tags_str = st.text_input("自定义标签", value=current_tags, key="job_tags_input", placeholder="逗号分隔", label_visibility="collapsed")
                if new_tags_str != current_tags:
                    job.project_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
                    db.commit()
                    st.toast("标签已保存")
                
                # ===== 职位备注（标题和保存按钮同行）=====
                notes_label_col, notes_btn_col = st.columns([2, 1])
                with notes_label_col:
                    st.markdown("<div style='margin-top:10px'><b>📝 备注</b></div>", unsafe_allow_html=True)
                with notes_btn_col:
                    save_notes_clicked = st.button("💾 保存", key=f"save_job_notes_{job.id}")
                
                # 使用CSS缩小备注框字体
                st.markdown("""
                <style>
                    div[data-testid="stTextArea"] textarea {
                        font-size: 13px !important;
                        line-height: 1.4 !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                job_notes_key = f"job_notes_{job.id}"
                new_notes = st.text_area("", value=job.notes or "", key=job_notes_key, height=400, placeholder="面试安排、HR反馈...", label_visibility="collapsed")
                
                if save_notes_clicked:
                    import sqlite3
                    conn = sqlite3.connect('/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE jobs SET notes = ? WHERE id = ?", (new_notes, job.id))
                    conn.commit()
                    conn.close()
                    st.toast("✅ 备注已保存")
                    st.rerun()





        else:
            st.error("未找到该职位")
            if st.button("返回"):
                back_to_job_list()

    else:
        # --- 职位列表视图 ---
        st.title("💼 职位库管理")
        
        tab1, tab2, tab3, tab4 = st.tabs(["职位列表", "发布职位(手动)", "导入导出职位", "批量画像"])
        
        with tab1:
            if "job_list_cache_buster" not in st.session_state:
                st.session_state.job_list_cache_buster = 0

            # --- Search Filters (紧凑单行布局) ---
            with st.expander("🔍 筛选条件", expanded=True):
                # 所有筛选项在一行
                cols = st.columns([1, 1.5, 1, 0.8, 0.8, 1, 1.2, 0.6, 0.6])
                with cols[0]:
                    filter_job_code = st.text_input("职位ID", value=st.session_state.get('filter_job_code', ''), key="filter_job_code_input", label_visibility="collapsed", placeholder="职位ID")
                    st.session_state.filter_job_code = filter_job_code
                with cols[1]:
                    filter_title = st.text_input("关键词", value=st.session_state.get('filter_title', ''), key="filter_title_input", label_visibility="collapsed", placeholder="职位名称/关键词")
                    st.session_state.filter_title = filter_title
                with cols[2]:
                    filter_company = st.text_input("公司", value=st.session_state.get('filter_job_company', ''), key="filter_job_company_input", label_visibility="collapsed", placeholder="公司")
                    st.session_state.filter_job_company = filter_company
                with cols[3]:
                    filter_location = st.text_input("地点", value=st.session_state.get('filter_job_location', ''), key="filter_job_location_input", label_visibility="collapsed", placeholder="地点")
                    st.session_state.filter_job_location = filter_location
                with cols[4]:
                    filter_level = st.text_input("职级", value=st.session_state.get('filter_job_level', ''), key="filter_job_level_input", label_visibility="collapsed", placeholder="职级")
                    st.session_state.filter_job_level = filter_level
                with cols[5]:
                    urgency_options = ["全部", "较急", "紧急", "非常紧急"]
                    filter_urgency = st.selectbox("紧急度", urgency_options, index=st.session_state.get('filter_job_urgency_idx', 0), key="filter_job_urgency_input", label_visibility="collapsed")
                    st.session_state.filter_job_urgency_idx = urgency_options.index(filter_urgency)
                filter_tags = ''  # 标签搜索已隐藏，传空值保持后端兼容
                with cols[6]:
                    filter_link = st.text_input("链接", value=st.session_state.get('filter_job_link', ''), key="filter_job_link_input", label_visibility="collapsed", placeholder="链接/职位ID")
                    st.session_state.filter_job_link = filter_link
                with cols[7]:
                    if st.button("清空", key="clear_job_filters", use_container_width=True):
                        st.session_state.filter_job_code = ''
                        st.session_state.filter_title = ''
                        st.session_state.filter_job_company = ''
                        st.session_state.filter_job_location = ''
                        st.session_state.filter_job_level = ''
                        st.session_state.filter_job_link = ''
                        st.session_state.filter_job_urgency_idx = 0
                        st.session_state.job_list_cache_buster += 1
                        st.rerun()
                with cols[8]:
                    if st.button("🔄", key="refresh_job_list", use_container_width=True, help="刷新"):
                        st.session_state.job_list_cache_buster += 1
                        st.rerun()
            
            # Pagination
            list_container = st.container()
            pagination_container = st.container()
            
            with pagination_container:
                st.divider()
                cp1, cp2, cp3 = st.columns([4, 2, 2])
                with cp2:
                    page_size = st.selectbox("每页显示", [20, 50, 100], key="job_page_size", label_visibility="collapsed")
                with cp3:
                    page_num = st.number_input(
                        "页码",
                        min_value=1,
                        value=st.session_state.get("job_page_num", 1),
                        key="job_page_num"
                    )

            # 缓存查询（DB侧过滤 + 分页）
            result = get_jobs_page_cached(
                filter_job_code=filter_job_code,
                filter_title=filter_title,
                filter_company=filter_company,
                filter_location=filter_location,
                filter_level=filter_level,
                filter_tags=filter_tags,
                filter_link=filter_link,
                filter_urgency=filter_urgency,
                page_num=int(page_num),
                page_size=int(page_size),
                cache_buster=int(st.session_state.job_list_cache_buster),
            )
            total_jobs = result["total"]
            total_pages = max(1, (total_jobs - 1) // page_size + 1)

            if page_num > total_pages:
                st.session_state.job_page_num = total_pages
                st.rerun()

            st.markdown(f"共 **{total_jobs}** 个职位")
            page_jobs = result["items"]
            
            with list_container:
                # Header - 包含紧急程度列和发布渠道列
                # ID, Title, Urgency, Comp, Dept, Level, Loc, Channel, PubDate, Action
                h0, h1, h1u, h2, h3, h4, h5, h5c, h6, h7 = st.columns([0.8, 2, 0.9, 1.3, 1, 0.6, 0.8, 0.8, 0.9, 0.9])
                h0.markdown("**职位ID**")
                h1.markdown("**职位名称**")
                h1u.markdown("**紧急程度**")
                h2.markdown("**公司**")
                h3.markdown("**部门**")
                h4.markdown("**职级**")
                h5.markdown("**地点**")
                h5c.markdown("**发布渠道**")
                h6.markdown("**发布日期**")
                h7.markdown("**操作**")
                st.divider()
                
                if page_jobs:
                    for job in page_jobs:
                        c0, c1, c1u, c2, c3, c4, c5, c5c, c6, c7 = st.columns([0.8, 2, 0.9, 1.3, 1, 0.6, 0.8, 0.8, 0.9, 0.9])
                        
                        # Extract Fields - 优先从独立字段读取
                        dept = job.get("department") or "-"
                        level = job.get("seniority_level") or "-"
                        pub_date = "-"
                        
                        # 如果独立字段为空，尝试从 detail_fields 补充
                        if job.get("detail_fields") and (dept == "-" or level == "-"):
                            try:
                                if isinstance(job.get("detail_fields"), str):
                                    d = json.loads(job.get("detail_fields"))
                                else:
                                    d = job.get("detail_fields")
                                # Fuzzy key match
                                for k in d:
                                    k_str = str(k).lower()
                                    if dept == "-" and ("部门" in k_str or "department" in k_str): dept = str(d[k])
                                    if level == "-" and ("层级" in k_str or "level" in k_str or "rank" in k_str or "p级" in k_str or "职级" in k_str): level = str(d[k])
                                    if "发布" in k_str or "publish" in k_str: pub_date = str(d[k])
                            except:
                                pass

                        with c0: st.write(job.get("job_code") or "-")

                        with c1:
                            title_md = f"**{job.get('title')}**"
                            if "急" in (job.get("title") or "") or "Urgent" in (job.get("title") or ""):
                                title_md += " 🔥"
                            st.markdown(title_md)
                        
                        # 紧急程度列 - 带颜色标签
                        with c1u:
                            urgency = job.get("urgency", 0) or 0
                            urgency_labels = ["普通", "较急", "紧急", "非常紧急"]
                            urgency_colors = ["#9e9e9e", "#ffc107", "#ff9800", "#f44336"]
                            urgency_icons = ["", "⚡", "🔥", "🚨"]
                            if urgency > 0:
                                st.markdown(f"<span style='background-color:{urgency_colors[urgency]}; color:white; padding:2px 8px; border-radius:12px; font-size:12px;'>{urgency_icons[urgency]} {urgency_labels[urgency]}</span>", unsafe_allow_html=True)
                            else:
                                st.write("-")
                        
                        with c2: st.write(job.get("company"))
                        with c3: st.write(dept)
                        with c4: st.write(level)
                        with c5: st.write(job.get("location") or "-")
                        
                        # 发布渠道列
                        with c5c:
                            channels = job.get("published_channels") or []
                            if isinstance(channels, str):
                                try:
                                    channels = json.loads(channels)
                                except:
                                    channels = []
                            if channels:
                                channel_styles = {
                                    "MM": ("🟠", "#ff9800", "脉脉"),
                                    "LI": ("🔵", "#0077b5", "LinkedIn"),
                                    "BOSS": ("🟢", "#00c853", "Boss")
                                }
                                badges = []
                                for c in channels:
                                    ch = c.get("channel", "")
                                    t = c.get("published_at", "")[:10]
                                    icon, color, name = channel_styles.get(ch, ("⚪", "#999", ch))
                                    badges.append(f"<span title='{name} {t}' style='background:{color};color:#fff;padding:1px 6px;border-radius:10px;font-size:11px;margin-right:2px;cursor:default;'>{ch}</span>")
                                st.markdown("".join(badges), unsafe_allow_html=True)
                            else:
                                st.write("-")
                        
                        with c6: st.write(format_date(pub_date))
                            
                        with c7:
                            cb1, cb2 = st.columns(2)
                            if cb1.button("📄", key=f"view_job_{job.get('id')}", help="查看详情"):
                                st.session_state.selected_job_id = job.get("id")
                                st.session_state.job_view_mode = 'detail'
                                st.rerun()
                            
                            if cb2.button("🗑️", key=f"del_job_{job.get('id')}", help="删除"):
                                delete_job(job.get("id"))
                                st.session_state.job_list_cache_buster += 1
                                st.rerun()
                        
                        st.markdown("---")
                else:
                    st.info("暂无职位数据")

        with tab2:
            # ★★★ 图片OCR识别功能（紧凑布局）★★★
            uploaded_image = st.file_uploader(
                "📷 上传JD截图识别（可选）", 
                type=["png", "jpg", "jpeg", "webp"],
                help="支持粘贴或上传JD截图，AI将自动识别并填充下方表单",
                key="jd_image_uploader"
            )
            
            # 初始化session state
            if 'ocr_title' not in st.session_state:
                st.session_state.ocr_title = ""
            if 'ocr_company' not in st.session_state:
                st.session_state.ocr_company = ""
            if 'ocr_jd_text' not in st.session_state:
                st.session_state.ocr_jd_text = ""
            
            if uploaded_image is not None:
                # 显示上传的图片预览
                col_img, col_btn = st.columns([3, 1])
                with col_img:
                    st.image(uploaded_image, caption="JD截图预览", use_container_width=True)
                with col_btn:
                    if st.button("🔍 AI识别图片", type="primary", key="ocr_btn"):
                        with st.spinner("AI 正在识别图片内容..."):
                            import base64
                            # 读取图片并转base64
                            image_bytes = uploaded_image.read()
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            
                            # 调用OCR
                            ocr_result = AIService.ocr_job_image(image_base64)
                            
                            if ocr_result.get('title') or ocr_result.get('jd_text'):
                                # 保存到session state
                                st.session_state.ocr_title = ocr_result.get('title', '')
                                st.session_state.ocr_company = ocr_result.get('company', '')
                                st.session_state.ocr_jd_text = ocr_result.get('jd_text', '')
                                st.session_state.ocr_location = ocr_result.get('location', '')
                                st.success(f"✅ 识别成功！职位：{ocr_result.get('title', 'N/A')} | 地点：{ocr_result.get('location', 'N/A')}")
                                st.rerun()
                            else:
                                st.error("❌ 图片识别失败，请手动输入")
            
            # 初始化OCR结果的session state
            if 'ocr_location' not in st.session_state:
                st.session_state.ocr_location = ""
            
            # 表单输入（使用OCR结果作为默认值）
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("职位名称 *", value=st.session_state.ocr_title, key="job_title_input")
            with col2:
                company = st.text_input("公司名称 *", value=st.session_state.ocr_company, key="job_company_input")
            
            # 第二行：部门、地点
            col3, col4 = st.columns(2)
            with col3:
                department = st.text_input("部门", placeholder="如：通义实验室、AI Coding团队", key="job_dept_input")
            with col4:
                location = st.text_input("地点", value=st.session_state.ocr_location, placeholder="如：北京、上海", key="job_location_input")
            
            # 第三行：职级、薪资
            col5, col6 = st.columns(2)
            with col5:
                seniority_level = st.text_input("职级", placeholder="如：P7、高级专家、Tech Lead", key="job_seniority_input")
            with col6:
                salary = st.text_input("薪资范围", placeholder="如：30-50K、面议", key="job_salary_input")
            
            # 第四行：年限、HR
            col7, col8 = st.columns(2)
            with col7:
                exp_years = st.text_input("年限要求", placeholder="如：3、5+（从JD自动匹配）", key="job_exp_input")
            with col8:
                hr_contact = st.text_input("HR", placeholder="如：张三（微信xxx）", key="job_hr_input")
            
            # 第五行：JD链接
            jd_link = st.text_input("JD链接", placeholder="原始职位链接（可选）", key="job_link_input")
            
            # 职位描述和备注（左右布局）
            jd_col, notes_col = st.columns([2, 1])
            with jd_col:
                jd_text = st.text_area(
                    "职位描述 (JD) *", 
                    value=st.session_state.ocr_jd_text,
                    height=350, 
                    placeholder="请粘贴完整的 JD 内容，或上传图片自动识别...",
                    key="job_jd_input"
                )
            with notes_col:
                job_notes = st.text_area(
                    "📝 备注",
                    height=350,
                    placeholder="HR信息、面试安排、薪资信息等...",
                    key="job_notes_new_input"
                )

            if st.button("💾 保存并生成标签", type="primary"):
                if not title or not jd_text:
                    st.error("请填写职位名称和 JD 内容")
                else:
                    with st.spinner("正在保存职位并生成AI标签..."):
                        # 0. ★★★ 自动生成JD编号 ★★★
                        def generate_job_code(company_name):
                            """根据公司名称生成JD编号，使用JSON文件存储映射"""
                            import json
                            import re
                            import pinyin
                            
                            if not company_name:
                                return None
                            
                            # 映射文件路径
                            map_file = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/company_prefix_map.json'
                            
                            # 加载现有映射
                            try:
                                with open(map_file, 'r', encoding='utf-8') as f:
                                    prefix_map = json.load(f)
                            except:
                                prefix_map = {}
                            
                            # 查找匹配的前缀
                            prefix = None
                            matched_key = None
                            for key, val in prefix_map.items():
                                if key.lower() in company_name.lower() or company_name.lower() in key.lower():
                                    prefix = val
                                    matched_key = key
                                    break
                            
                            # 如果没有匹配，生成新的前缀
                            if not prefix:
                                # 生成3字母缩写
                                company_clean = company_name.strip()
                                
                                # 尝试提取英文首字母
                                english_words = re.findall(r'[A-Za-z]+', company_clean)
                                if english_words:
                                    # 英文公司：取各单词首字母或前3个字母
                                    if len(english_words) >= 3:
                                        prefix = ''.join([w[0].upper() for w in english_words[:3]])
                                    elif len(english_words) == 2:
                                        prefix = (english_words[0][0] + english_words[1][:2]).upper()
                                    else:
                                        prefix = english_words[0][:3].upper()
                                else:
                                    # 中文公司：取拼音首字母
                                    try:
                                        py = pinyin.get(company_clean, format="strip", delimiter="")
                                        # 取前3个字的拼音首字母
                                        prefix = ''.join([c[0].upper() for c in py.split() if c][:3])
                                        if len(prefix) < 2:
                                            prefix = py[:3].upper()
                                    except:
                                        # 拼音失败，用默认
                                        prefix = "OTH"
                                
                                # 确保前缀至少2个字符
                                if len(prefix) < 2:
                                    prefix = "OTH"
                                
                                # 保存新的映射
                                prefix_map[company_name] = prefix
                                try:
                                    with open(map_file, 'w', encoding='utf-8') as f:
                                        json.dump(prefix_map, f, ensure_ascii=False, indent=4)
                                    print(f"✅ 新增公司前缀映射: {company_name} -> {prefix}")
                                except Exception as e:
                                    print(f"⚠️ 保存前缀映射失败: {e}")
                            
                            # 查询该前缀下最大序号（使用原生SQL支持大小写不敏感）
                            from sqlalchemy import text
                            # 同时匹配大写和小写前缀，以及可能的下划线格式
                            prefix_variants = [prefix.upper(), prefix.lower(), f"{prefix.lower()}_"]
                            max_num = 0
                            for pv in prefix_variants:
                                result = db.execute(text(f"SELECT job_code FROM jobs WHERE job_code LIKE '{pv}%' ORDER BY job_code DESC LIMIT 1")).first()
                                if result and result[0]:
                                    match = re.search(r'(\d+)$', result[0])
                                    if match:
                                        num = int(match.group(1))
                                        if num > max_num:
                                            max_num = num
                            
                            next_num = max_num + 1
                            
                            # 生成编号（统一3位数格式，使用大写前缀）
                            return f"{prefix.upper()}{next_num:03d}"
                        
                        job_code = generate_job_code(company)
                        
                        # 1. AI 解析基础信息（不使用模版）
                        parsed_job = AIService.parse_job(jd_text, user_prompt_template=None)
                        
                        # 自动从JD匹配年限（如果用户未填写）
                        def extract_exp_years_from_jd(text):
                            """从JD文本中提取年限要求"""
                            import re
                            patterns = [
                                r'(\d+)\s*年[及以]?[上以]?[工作]?经[验历]',  # 3年以上经验
                                r'(\d+)[+＋]?\s*年[的]?[相关]?[工作]?经[验历]',  # 3+年经验
                                r'[要求]?\s*(\d+)\s*[-~至到]\s*\d+\s*年',  # 3-5年
                            ]
                            for pattern in patterns:
                                match = re.search(pattern, text)
                                if match:
                                    return match.group(1)
                            return None
                        
                        # 年限：优先用户输入，其次JD匹配，最后AI解析
                        final_exp_years = None
                        if exp_years and exp_years.strip():
                            # 提取数字
                            import re
                            num_match = re.search(r'(\d+)', exp_years)
                            if num_match:
                                final_exp_years = int(num_match.group(1))
                        if not final_exp_years:
                            jd_exp = extract_exp_years_from_jd(jd_text)
                            if jd_exp:
                                final_exp_years = int(jd_exp)
                        if not final_exp_years:
                            final_exp_years = parsed_job.get("required_experience_years")
                        
                        # 2. 存入 DB（保存所有表单字段）
                        new_job = Job(
                            title=title,
                            company=company,
                            job_code=job_code,
                            department=department if department else None,
                            location=location if location else "",
                            seniority_level=seniority_level if seniority_level else None,
                            salary_range=salary if salary else parsed_job.get("salary_range"),
                            hr_contact=hr_contact if hr_contact else None,
                            jd_link=jd_link if jd_link else None,
                            required_experience_years=final_exp_years,
                            raw_jd_text=jd_text,
                            ai_analysis=parsed_job.get("analysis"),
                            notes=job_notes if job_notes else None,
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
                        
                        # 4. ★★★ 生成结构化标签 ★★★
                        try:
                            from extract_tags import extract_tags, JD_PROMPT, TAG_SCHEMA
                            tag_prompt = JD_PROMPT.format(
                                schema=TAG_SCHEMA,
                                title=title or '',
                                company=company or '',
                                description=(jd_text or '')[:2000]
                            )
                            tags = extract_tags(tag_prompt)
                            
                            if tags:
                                import json
                                new_job.structured_tags = json.dumps(tags, ensure_ascii=False)
                                db.commit()
                                st.success(f"✅ 职位保存成功！编号: {job_code} | 标签: {tags.get('role_type', 'N/A')} / {tags.get('seniority', 'N/A')}")
                            else:
                                st.warning("⚠️ 职位已保存，但标签生成失败，可稍后在批量画像中重试")
                        except Exception as e:
                            st.warning(f"⚠️ 职位已保存，标签生成异常: {e}")
                        
                        # 清空所有表单缓存
                        st.session_state.ocr_title = ""
                        st.session_state.ocr_company = ""
                        st.session_state.ocr_jd_text = ""
                        st.session_state.ocr_location = ""
                        # 清空其他表单字段（通过删除key）
                        for key in ['job_title_input', 'job_company_input', 'job_dept_input', 
                                    'job_location_input', 'job_seniority_input', 'job_salary_input',
                                    'job_exp_input', 'job_hr_input', 'job_link_input', 
                                    'job_jd_input', 'job_notes_new_input']:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        # 刷新列表
                        st.rerun()

        with tab3:
            st.subheader("从 Excel/CSV 批量导入职位")
            
            # 导入 JobImportTask
            from database import JobImportTask
            
            # 任务状态统计
            pending_count = db.query(JobImportTask).filter(JobImportTask.status == 'pending').count()
            processing_count = db.query(JobImportTask).filter(JobImportTask.status == 'processing').count()
            done_count = db.query(JobImportTask).filter(JobImportTask.status == 'done').count()
            failed_count = db.query(JobImportTask).filter(JobImportTask.status == 'failed').count()
            
            # 状态卡片
            stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns([1, 1, 1, 1, 1])
            with stat_col1:
                st.metric("⏳ 待处理", pending_count)
            with stat_col2:
                st.metric("🔄 处理中", processing_count)
            with stat_col3:
                st.metric("✅ 已完成", done_count)
            with stat_col4:
                st.metric("❌ 失败", failed_count)
            with stat_col5:
                if st.button("🔄 刷新", key="refresh_job_import"):
                    st.rerun()
            
            st.divider()
            
            # 多文件上传
            st.markdown("##### 📤 上传职位文件")
            uploaded_files = st.file_uploader(
                "支持多选，拖拽上传", 
                type=["xlsx", "csv"], 
                accept_multiple_files=True,
                key="job_import_files"
            )
            
            if uploaded_files:
                st.info(f"已选择 **{len(uploaded_files)}** 个文件")
                
                # 显示文件列表
                for f in uploaded_files:
                    st.caption(f"📄 {f.name}")
                
                if st.button("🚀 添加到导入队列", type="primary"):
                    import uuid
                    import shutil
                    
                    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "jobs")
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    
                    added = 0
                    for uploaded_file in uploaded_files:
                        # 检查是否已存在相同文件名的任务
                        existing = db.query(JobImportTask).filter(
                            JobImportTask.file_name == uploaded_file.name
                        ).first()
                        
                        if existing:
                            st.warning(f"⏭️ 跳过 (已存在): {uploaded_file.name}")
                            continue
                        
                        # 生成唯一文件名保存
                        ext = uploaded_file.name.split('.')[-1].lower()
                        unique_name = f"{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
                        dest_path = os.path.join(UPLOAD_DIR, unique_name)
                        
                        # 保存文件
                        with open(dest_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 创建任务
                        task = JobImportTask(
                            file_path=dest_path,
                            file_name=uploaded_file.name,
                            file_type=ext,
                            status='pending'
                        )
                        db.add(task)
                        added += 1
                    
                    db.commit()
                    
                    if added > 0:
                        st.success(f"✅ 已添加 {added} 个文件到导入队列")
                        st.info("💡 后台 Worker 将自动处理导入并提取标签")
                        st.rerun()
            
            st.divider()
            
            # 最近任务
            st.markdown("##### 📋 最近导入任务")
            recent_tasks = db.query(JobImportTask).order_by(JobImportTask.created_at.desc()).limit(10).all()
            
            if recent_tasks:
                for task in recent_tasks:
                    status_icon = {"pending": "⏳", "processing": "🔄", "done": "✅", "failed": "❌"}.get(task.status, "❓")
                    
                    with st.container(border=True):
                        cols = st.columns([0.5, 3, 1.5, 1])
                        with cols[0]:
                            st.write(status_icon)
                        with cols[1]:
                            st.write(f"**{task.file_name}**")
                        with cols[2]:
                            if task.status == 'done':
                                st.caption(f"导入{task.jobs_imported} / 跳过{task.jobs_skipped} / 标签{task.tags_extracted}")
                            elif task.status == 'failed':
                                st.caption(f"❌ {(task.error_message or '')[:30]}...")
                            elif task.status == 'processing':
                                st.caption("处理中...")
                            else:
                                st.caption("等待处理")
                        with cols[3]:
                            if task.status == 'failed':
                                if st.button("🔁", key=f"retry_job_{task.id}", help="重试"):
                                    task.status = 'pending'
                                    task.error_message = None
                                    task.started_at = None
                                    db.commit()
                                    st.rerun()
            else:
                st.info("暂无导入任务")
            
            # Worker 状态提示
            st.divider()
            st.markdown("##### ⚙️ 后台 Worker")
            st.caption("职位导入由后台 Worker 自动处理，包括：导入数据库、去重检查、生成编号、提取标签")
            st.code("启动命令: nohup python job_import_worker.py &", language="bash")

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
    match_type = st.radio("匹配模式", ["为职位找人 (Job -> Candidates)", "为人才找职位 (Candidate -> Jobs)", "🔍 AI语义搜索职位", "🔍 AI语义搜索人才"])
    
    # 导入匹配引擎
    import sqlite3
    DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
    
    if match_type == "为职位找人 (Job -> Candidates)":
        # 获取有标签的职位
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, job_code, title, company, structured_tags 
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
            "🔍 搜索职位（Code/名称/公司）",
            placeholder="输入关键词，如 BT020...",
            key='job_search_keyword'
        )

        job_search = st.session_state.job_search_keyword

        # 根据搜索词筛选 (id, job_code, title, company, structured_tags)
        if job_search:
            filtered_jobs = [j for j in jobs_data if 
                            (job_search.upper() in (j[1] or '').upper()) or  # job_code
                            (job_search.lower() in (j[2] or '').lower()) or  # 职位名称
                            (job_search.lower() in (j[3] or '').lower())]  # 公司
        else:
            filtered_jobs = jobs_data[:50]  # 默认显示前50个
        
        # 显示格式: job_code: title - company
        job_options = {f"{j[1] or j[0]}: {j[2]} - {j[3]}": j[0] for j in filtered_jobs}
        
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
                
                # 获取有structured_tags的候选人
                cursor.execute("""
                    SELECT c.id, c.name, c.current_company, c.current_title, 
                           c.structured_tags, c.is_friend, c.skills
                    FROM candidates c
                    WHERE c.structured_tags IS NOT NULL AND c.structured_tags != 'null'
                """)
                candidates = cursor.fetchall()
                
                # 导入同义词匹配（复用job_search.py的逻辑）
                import re
                def clean_tag(s):
                    s = s.split(": ")[-1] if ": " in s else s
                    s = re.sub(r'\s*[\(（][^)）]*[\)）]', '', s)
                    return s.lower().strip()
                
                # 职级映射
                SENIORITY_LEVELS = {
                    "初级": 1, "初级(0-3年)": 1,
                    "中级": 2, "中级(3-5年)": 2,
                    "高级": 3, "高级(5-8年)": 3,
                    "专家": 4, "专家(8年+)": 4,
                    "管理层": 5
                }
                
                # 学历映射
                EDU_LEVELS = {"专科": 1, "大专": 1, "本科": 2, "硕士": 3, "博士": 4}
                
                # 角色池定义
                ROLE_POOLS = {
                    "技术": ["算法工程师", "算法专家", "算法研究员", "高级算法工程师"],
                    "管理": ["技术管理"],
                    "产品": ["产品经理", "AI产品专家", "AI产品经理", "运营"],
                    "工程": ["工程开发", "运维/SRE", "数据工程师"],
                    "销售": ["销售专家", "AI销售专家", "解决方案架构师"]
                }
                
                def get_role_pool(role):
                    for pool, roles in ROLE_POOLS.items():
                        if role in roles:
                            return pool
                    return None
                
                # 提取职位标签
                job_domains = set(job_tags.get("tech_domain", []))
                job_core_specs = {clean_tag(s) for s in job_tags.get("core_specialty", [])}
                job_tech_skills = {clean_tag(s) for s in job_tags.get("tech_skills", [])}
                job_role = job_tags.get("role_type", "")
                job_seniority = job_tags.get("seniority", "")
                job_edu = job_tags.get("education", {})
                job_edu_degree = job_edu.get("degree", "") if isinstance(job_edu, dict) else ""
                
                job_level = SENIORITY_LEVELS.get(job_seniority, 0)
                job_edu_level = EDU_LEVELS.get(job_edu_degree, 0)
                job_pool = get_role_pool(job_role)
                
                # 计算匹配分数
                results = []
                for cid, name, company, title, tags_str, is_friend, skills_str in candidates:
                    try:
                        cand_tags = json.loads(tags_str) if tags_str else {}
                        
                        # 提取候选人标签
                        cand_domains = set(cand_tags.get("tech_domain", []))
                        cand_core_specs = {clean_tag(s) for s in cand_tags.get("core_specialty", [])}
                        cand_tech_skills = {clean_tag(s) for s in cand_tags.get("tech_skills", [])}
                        cand_role = cand_tags.get("role_type", "")
                        cand_seniority = cand_tags.get("seniority", "")
                        cand_edu = cand_tags.get("education", {})
                        cand_edu_degree = cand_edu.get("degree", "") if isinstance(cand_edu, dict) else ""
                        
                        cand_level = SENIORITY_LEVELS.get(cand_seniority, 0)
                        cand_edu_level = EDU_LEVELS.get(cand_edu_degree, 0)
                        cand_pool = get_role_pool(cand_role)
                        
                        # === 6维度匹配评分（按知识库权重）===
                        match_reasons = []
                        risk_flags = []
                        
                        # 1. tech_domain (25%)
                        domain_overlap = cand_domains & job_domains
                        tech_score = len(domain_overlap) / max(len(job_domains), 1) * 100 if job_domains else 50
                        if domain_overlap:
                            match_reasons.append(f"技术方向: {', '.join(list(domain_overlap)[:2])}")
                        
                        # 2. core_specialty (30%) - 核心！
                        core_overlap = cand_core_specs & job_core_specs
                        specialty_score = len(core_overlap) / max(len(job_core_specs), 1) * 100 if job_core_specs else 50
                        if core_overlap:
                            match_reasons.insert(0, f"🎯 核心专长: {', '.join(list(core_overlap)[:2])}")
                        
                        # 3. tech_skills (15%)
                        skill_overlap = cand_tech_skills & job_tech_skills
                        skill_score = len(skill_overlap) / max(len(job_tech_skills), 1) * 100 if job_tech_skills else 50
                        if skill_overlap and not core_overlap:
                            match_reasons.append(f"技能: {', '.join(list(skill_overlap)[:2])}")
                        
                        # 4. role_type (15%)
                        if cand_role == job_role and cand_role:
                            role_score = 100
                            match_reasons.append(f"岗位匹配: {job_role}")
                        elif cand_pool == job_pool and cand_pool:
                            role_score = 70
                        elif cand_pool and job_pool:
                            # 跨池惩罚
                            role_score = 30
                            risk_flags.append(f"跨池({cand_pool}→{job_pool})")
                        else:
                            role_score = 50
                        
                        # 5. seniority (10%)
                        if cand_level > 0 and job_level > 0:
                            level_gap = cand_level - job_level
                            if level_gap == 0:
                                seniority_score = 100
                            elif level_gap == 1:  # 略过高
                                seniority_score = 85
                                risk_flags.append("资历略过高(+1级)")
                            elif level_gap >= 2:  # 过高（严重风险）
                                seniority_score = 40
                                risk_flags.append(f"资历过高(+{level_gap}级)")
                            elif level_gap == -1:  # 略不足（可接受，不影响分层）
                                seniority_score = 85
                                risk_flags.append("💡资历略不足(-1级)")
                            elif level_gap == -2:  # 不足（严重风险）
                                seniority_score = 40
                                risk_flags.append(f"⚠️资历不足({level_gap}级)")
                            elif level_gap <= -3:  # 严重不足
                                seniority_score = 20
                                risk_flags.append(f"⛔资历不足({level_gap}级)")
                            else:
                                seniority_score = 50
                        else:
                            seniority_score = 50
                        
                        # 6. education (5%)
                        if cand_edu_level > 0 and job_edu_level > 0:
                            edu_gap = cand_edu_level - job_edu_level
                            if edu_gap >= 0:
                                edu_score = 100
                            else:
                                edu_score = max(50 + edu_gap * 20, 0)
                        else:
                            edu_score = 50
                        
                        # === 加权总分 ===
                        total = (
                            tech_score * 0.25 +
                            specialty_score * 0.30 +
                            skill_score * 0.15 +
                            role_score * 0.15 +
                            seniority_score * 0.10 +
                            edu_score * 0.05
                        )
                        
                        # 风险上限（只有严重风险才触发）
                        # 严重风险：资历过高+2级、资历不足-2级、跨池
                        has_severe_risk = any("⚠️" in f or "⛔" in f or "过高" in f or "跨池" in f for f in risk_flags)
                        # 轻微风险：资历略过高+1级（不包含资历略不足-1级）
                        has_minor_risk = any("资历略过高" in f for f in risk_flags)
                        
                        if has_severe_risk:
                            total = min(total, 85)
                        elif has_minor_risk:
                            total = min(total, 92)
                        # 资历略不足(-1级)不触发任何上限，只显示提示
                        
                        # 匹配分层（放宽强匹配条件：资历略不足-1级可以进入强匹配）
                        if total >= 90 and not has_severe_risk and not has_minor_risk:
                            match_tier = "强匹配"
                        elif total >= 75:
                            match_tier = "可转型"
                        else:
                            match_tier = "泛化拓展"
                        
                        results.append({
                            "id": cid, "name": name, "company": company, "title": title,
                            "score": round(total, 1), 
                            "reasons": match_reasons, 
                            "risk_flags": risk_flags,
                            "match_tier": match_tier,
                            "is_friend": is_friend,
                            # 分项分数（用于进度条显示）
                            "tech": tech_score,
                            "role": role_score,
                            "stack": skill_score
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
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            # 分层颜色
                            tier = r.get("match_tier", "")
                            if tier == "强匹配":
                                score_color = "🟢"
                            elif tier == "可转型":
                                score_color = "🟡"
                            else:
                                score_color = "🔴"
                            
                            friend_badge = "⭐" if r["is_friend"] else ""
                            st.markdown(f"### {i}. {r['name']} {friend_badge} {score_color} **{r['score']}分**")
                            st.caption(f"🏢 {r['company']} · {r['title']} · 🏷️ {tier}")
                            
                            if r["reasons"]:
                                st.markdown(f"✅ {', '.join(r['reasons'])}")
                            
                            if r.get("risk_flags"):
                                st.markdown(f"⚠️ 风险: {', '.join(r['risk_flags'])}")
                        
                        with col2:
                            st.caption("技术/岗位/技能")
                            st.progress(int(min(r.get("tech", 0), 100)) / 100)
                            st.progress(int(min(r.get("role", 0), 100)) / 100)
                            st.progress(int(min(r.get("stack", 0), 100)) / 100)
                        
                        # 使用 expander 显示候选人详情
                        with st.expander("👀 查看候选人详情", expanded=False):
                            # 获取候选人详细信息
                            cursor.execute("""
                                SELECT current_company, current_title, expect_location, age, 
                                       experience_years, education_level, education_details,
                                       work_experiences, structured_tags,
                                       skills, phone, email, linkedin_url, source
                                FROM candidates WHERE id = ?
                            """, (r['id'],))
                            cand_detail = cursor.fetchone()
                            
                            if cand_detail:
                                (company, title, location, age, years_exp, edu_level, edu_details,
                                 work_exp, struct_tags, skills, phone, email, 
                                 linkedin, source) = cand_detail
                                
                                # 从education_details提取学校名
                                school = None
                                if edu_details:
                                    try:
                                        edu_list = json.loads(edu_details) if isinstance(edu_details, str) else edu_details
                                        if edu_list and len(edu_list) > 0:
                                            school = edu_list[0].get('school') or edu_list[0].get('school_name')
                                    except:
                                        pass
                                
                                # 左右分栏布局（借鉴详情页风格）
                                left_col, right_col = st.columns([2, 3])
                                
                                with left_col:
                                    # 基本信息
                                    st.markdown(f"**-** · **{years_exp or '-'}年** · **{edu_level or '-'}**")
                                    st.markdown(f"🏢 {company or '-'}")
                                    st.markdown(f"{title or '-'}")
                                    
                                    # 技能标签
                                    if skills:
                                        try:
                                            skill_list = json.loads(skills) if isinstance(skills, str) else skills
                                            if skill_list:
                                                tags_html = " ".join([f"`{s}`" for s in skill_list[:6]])
                                                st.markdown(f"🏷️ {tags_html}")
                                        except:
                                            pass
                                    
                                    # 来源
                                    if source:
                                        st.caption(f"📁 来源: {source}")
                                
                                with right_col:
                                    # 工作经历
                                    if work_exp:
                                        try:
                                            work_list = json.loads(work_exp) if isinstance(work_exp, str) else work_exp
                                            if work_list:
                                                st.markdown("**💼 工作经历**")
                                                for exp in work_list[:3]:  # 最多显示3条
                                                    exp_company = exp.get('company') or exp.get('company_name') or '-'
                                                    exp_title = exp.get('title') or exp.get('position') or '-'
                                                    exp_time = exp.get('time_range') or exp.get('duration') or ''
                                                    exp_duration = exp.get('duration_text') or ''
                                                    
                                                    time_display = f"`{exp_time}`" if exp_time else ""
                                                    st.markdown(f"{time_display} **{exp_company}** · {exp_title} {exp_duration}")
                                        except:
                                            pass
                                    
                                    # 教育经历
                                    if edu_details:
                                        try:
                                            edu_list = json.loads(edu_details) if isinstance(edu_details, str) else edu_details
                                            if edu_list:
                                                st.markdown("**🎓 教育经历**")
                                                for edu in edu_list[:2]:  # 最多显示2条
                                                    edu_school = edu.get('school') or edu.get('school_name') or '-'
                                                    edu_major = edu.get('major') or edu.get('field') or ''
                                                    edu_time = edu.get('time_range') or edu.get('graduation_year') or ''
                                                    edu_degree = edu.get('degree') or ''
                                                    
                                                    time_display = f"({edu_time})" if edu_time else ""
                                                    st.markdown(f"🏫 **{edu_school}** {time_display} · {edu_major} {edu_degree}")
                                        except:
                                            pass
                                
                                st.divider()
                                
                                # 跳转到详情页按钮
                                if st.button("📄 查看完整简历", key=f"view_full_{r['id']}"):
                                    st.session_state.selected_candidate_id = r["id"]
                                    st.session_state.view_mode = 'detail'
                                    st.session_state.nav_page = "人才库管理"
                                    st.rerun()
        
        conn.close()

    elif match_type == "为人才找职位 (Candidate -> Jobs)":
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
                
                # 使用 job_search 模块的匹配函数
                with st.spinner("正在匹配职位..."):
                    results = match_candidate_to_jobs(cand_id, top_k=20)
                
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
                        # 显示职位ID和标题
                        st.markdown(f"### {i}. [#{r.get('id', '')}] {r['title']}")
                        st.caption(f"🏢 {r.get('company', '')} · 📍 {r.get('location') or '未知'} · 🏷️ {r.get('match_tier', '')}")
                        
                        # 显示匹配原因
                        match_reasons = r.get('match_reasons', [])
                        if match_reasons:
                            reasons_str = ", ".join(match_reasons)
                            st.markdown(f"✅ **匹配原因**: {reasons_str}")
                        
                        # 显示风险标签
                        risk_flags = r.get('risk_flags', [])
                        if risk_flags:
                            st.markdown(f"⚠️ **风险**: {', '.join(risk_flags)}")
                            
                    with col2:
                        # 根据分层显示颜色
                        match_tier = r.get('match_tier', '')
                        if match_tier == "强匹配" or r["score"] >= 90:
                            st.success(f"**{r['score']}分**")
                        elif match_tier == "可转型" or r["score"] >= 75:
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
    
    # AI 语义搜索职位
    elif match_type == "🔍 AI语义搜索职位":
        st.subheader("🧠 用自然语言搜索职位")
        st.caption("输入任意描述，AI 会帮你找到最相关的职位。例如：'语音相关的AIGC算法工作' 或 '机器学习推荐系统专家'")
        
        # 导入搜索模块
        try:
            from job_search import search_jobs, get_index_stats
            
            # 显示索引状态
            stats = get_index_stats()
            if stats["status"] == "ready":
                st.success(f"✅ 向量索引就绪，共 {stats['count']} 条职位")
            else:
                st.warning("⚠️ 向量索引未构建，请先运行: python job_search.py build")
            
            # 搜索输入
            search_query = st.text_input(
                "搜索职位",
                placeholder="例如：找语音相关的AIGC算法工作、机器学习专家、大模型训练...",
                label_visibility="collapsed"
            )
            
            col_btn, col_k = st.columns([2, 1])
            with col_btn:
                search_clicked = st.button("🚀 智能搜索", type="primary", use_container_width=True)
            with col_k:
                top_k = st.selectbox("结果数", [10, 20, 30, 50], index=1, label_visibility="collapsed")
            
            if search_query and search_clicked:
                with st.spinner("AI 正在搜索..."):
                    results = search_jobs(search_query, top_k=top_k)
                
                if results:
                    st.success(f"✅ 找到 {len(results)} 个匹配职位")
                    
                    for i, r in enumerate(results, 1):
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.markdown(f"### {i}. [#{r.get('id', '')}] {r['title']}")
                                st.caption(f"🏢 {r.get('company', '')} · 📍 {r.get('location', '未知')}")
                                
                                # 匹配原因
                                if r.get("match_reasons"):
                                    st.markdown(f"✅ **匹配原因**: {', '.join(r['match_reasons'])}")
                                
                                # 标签展示
                                tags = r.get("tags", {})
                                if tags:
                                    tag_items = []
                                    if tags.get("tech_domain"):
                                        tag_items.append(f"📂 {', '.join(tags['tech_domain'][:3])}")
                                    if tags.get("role_type"):
                                        tag_items.append(f"👤 {tags['role_type']}")
                                    if tags.get("seniority"):
                                        tag_items.append(f"📊 {tags['seniority']}")
                                    if tag_items:
                                        st.caption(" | ".join(tag_items))
                            
                            with col2:
                                st.metric("匹配度", f"{r['score']}分")
                            
                            # 使用 expander 显示职位详情（参考"为人才找职位"的设计）
                            with st.expander("📄 查看职位详情", expanded=False):
                                import sqlite3
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                
                                cursor.execute("""
                                    SELECT raw_jd_text, ai_analysis, structured_tags, salary_range, 
                                           required_experience_years, original_link
                                    FROM jobs WHERE id = ?
                                """, (r['id'],))
                                job_detail = cursor.fetchone()
                                
                                if job_detail:
                                    jd_text, ai_analysis, struct_tags, salary, exp_years, orig_link = job_detail
                                    
                                    # 使用 tabs 组织内容
                                    detail_tabs = st.tabs(["📝 JD全文", "🏷️ 标签信息", "🤖 AI分析"])
                                    
                                    # Tab 1: JD全文
                                    with detail_tabs[0]:
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
                                        
                                        if jd_text:
                                            display_text = jd_text[:3000] + ("..." if len(jd_text) > 3000 else "")
                                            st.markdown(display_text)
                                        else:
                                            st.info("暂无JD内容")
                                    
                                    # Tab 2: 标签信息
                                    with detail_tabs[1]:
                                        if struct_tags:
                                            try:
                                                tags_data = json.loads(struct_tags) if isinstance(struct_tags, str) else struct_tags
                                                tag_col1, tag_col2 = st.columns(2)
                                                with tag_col1:
                                                    st.markdown(f"• **技术方向**: {', '.join(tags_data.get('tech_domain', []))}")
                                                    st.markdown(f"• **细分专长**: {', '.join(tags_data.get('specialty', []))}")
                                                    st.markdown(f"• **岗位类型**: {tags_data.get('role_type', '-')}")
                                                with tag_col2:
                                                    st.markdown(f"• **角色定位**: {', '.join(tags_data.get('role_orientation', []))}")
                                                    st.markdown(f"• **技术栈**: {', '.join(tags_data.get('tech_stack', []))}")
                                                    st.markdown(f"• **职级要求**: {tags_data.get('seniority', '-')}")
                                            except:
                                                st.info("标签解析失败")
                                        else:
                                            st.info("暂无标签信息")
                                    
                                    # Tab 3: AI分析
                                    with detail_tabs[2]:
                                        if ai_analysis:
                                            if isinstance(ai_analysis, str):
                                                try:
                                                    ai_data = json.loads(ai_analysis)
                                                    st.json(ai_data)
                                                except:
                                                    st.markdown(ai_analysis)
                                            else:
                                                st.json(ai_analysis)
                                        else:
                                            st.info("暂无AI分析")
                                
                                conn.close()
                else:
                    st.info("未找到匹配的职位，请尝试其他关键词")
        except Exception as e:
            st.error(f"加载搜索模块失败: {e}")
    
    # AI 语义搜索人才
    elif match_type == "🔍 AI语义搜索人才":
        st.subheader("🧠 用自然语言搜索人才")
        st.caption("输入任意描述，AI 会帮你找到最相关的候选人。例如：'找有广告行业AIGC经验的人才' 或 '在字节做过推荐算法的专家'")
        
        # 导入搜索模块
        try:
            from job_search import search_candidates, get_candidate_index_stats
            
            # 显示索引状态
            stats = get_candidate_index_stats()
            if stats["status"] == "ready":
                st.success(f"✅ 候选人向量索引就绪，共 {stats['count']} 人")
            else:
                st.warning("⚠️ 候选人向量索引未构建，请先运行: python job_search.py build-cand")
            
            # 搜索输入
            search_query = st.text_input(
                "搜索人才",
                placeholder="例如：找有广告行业AIGC经验的人才、在字节做过推荐算法、语音合成专家...",
                label_visibility="collapsed"
            )
            
            col_btn, col_k = st.columns([2, 1])
            with col_btn:
                search_clicked = st.button("🚀 智能搜索", type="primary", use_container_width=True, key="search_cand_btn")
            with col_k:
                top_k = st.selectbox("结果数", [10, 20, 30, 50], index=1, label_visibility="collapsed", key="search_cand_k")
            
            if search_query and search_clicked:
                with st.spinner("AI 正在搜索人才..."):
                    results = search_candidates(search_query, top_k=top_k)
                
                if results:
                    st.success(f"✅ 找到 {len(results)} 个匹配候选人")
                    
                    for i, r in enumerate(results, 1):
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.markdown(f"### {i}. {r['name']}")
                                st.caption(f"🏢 {r.get('company', '未知')} · 👤 {r.get('title', '未知')}")
                                
                                # 匹配原因
                                if r.get("match_reasons"):
                                    st.markdown(f"✅ **匹配原因**: {', '.join(r['match_reasons'])}")
                                
                                # 标签展示
                                tags = r.get("tags", {})
                                if tags:
                                    tag_items = []
                                    if tags.get("tech_domain"):
                                        tag_items.append(f"📂 {', '.join(tags['tech_domain'][:3])}")
                                    if tags.get("role_type"):
                                        tag_items.append(f"👤 {tags['role_type']}")
                                    if tags.get("seniority"):
                                        tag_items.append(f"📊 {tags['seniority']}")
                                    if tag_items:
                                        st.caption(" | ".join(tag_items))
                            
                            with col2:
                                st.metric("匹配度", f"{r['score']}分")
                                if st.button("👀 详情", key=f"search_cand_view_{r['id']}"):
                                    st.session_state.selected_candidate_id = r["id"]
                                    st.session_state.candidate_view_mode = 'detail'
                                    st.session_state.nav_page = "人才库"
                                    st.rerun()
                else:
                    st.info("未找到匹配的候选人，请尝试其他关键词")
        except Exception as e:
            st.error(f"加载搜索模块失败: {e}")
