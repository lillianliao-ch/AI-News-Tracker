import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float, Boolean
from sqlalchemy import inspect
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import text
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

Base = declarative_base()

class SystemPrompt(Base):
    __tablename__ = 'system_prompts'
    
    id = Column(Integer, primary_key=True)
    prompt_type = Column(String(50), nullable=False) # 'candidate', 'job'
    prompt_role = Column(String(50), default='system') # 'system', 'user'
    prompt_name = Column(String(100)) # e.g. 'Default V1'
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)  # 使用本地时间

class Candidate(Base):
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(50))
    
    # 原始数据
    raw_resume_text = Column(Text)  # 简历全文
    source_file = Column(String(200)) # 来源文件名 (Excel/PDF)
    
    # AI 分析数据
    ai_summary = Column(Text) # AI 简短评价
    skills = Column(JSON) # 技能列表 ["Python", "Django"]
    experience_years = Column(Integer)
    age = Column(Integer) # 年龄/出生年份推算
    expect_location = Column(String(100)) # 期望工作地点
    education_level = Column(String(50))
    education_details = Column(JSON) # 存储详细教育经历 [{school, degree, major, time}, ...]
    work_experiences = Column(JSON) # 存储详细工作经历 [{company, title, time, description}, ...]
    project_experiences = Column(JSON) # 存储详细项目经历 [{name, role, time, description}, ...]
    current_company = Column(String(200))
    current_title = Column(String(200))
    
    # 社交链接与备注
    linkedin_url = Column(String(500))
    github_url = Column(String(500))
    twitter_url = Column(String(500))
    personal_website = Column(String(500))  # 个人主页/博客
    website_content = Column(Text) # 个人网站爬取得内容
    greeting_drafts = Column(JSON)  # {"linkedin": "...", "maimai": "...", "email": "..."} 按渠道存储打招呼草稿
    notes = Column(Text)
    
    # 好友标记
    is_friend = Column(Integer, default=0)  # 0=未加好友, 1=已加好友
    friend_added_at = Column(String(50))  # 加好友时间
    friend_channel = Column(String(100))  # 加好友渠道（脉脉/微信/LinkedIn等）
    
    # 沟通记录
    communication_logs = Column(JSON)  # [{time, channel, action, content, direction}, ...] 按时间倒序
    last_communication_at = Column(DateTime)  # 最近一次沟通时间（用于高效排序）
    scheduled_contact_date = Column(String(20))  # 预约沟通日期 (格式: YYYY-MM-DD)
    
    # 运营管道
    pipeline_stage = Column(String(50), default='new')  # new/contacted/following_up/replied/wechat_connected/in_pipeline/closed
    contacted_channels = Column(JSON)  # ["linkedin", "maimai", "email"] 已触达的渠道
    follow_up_date = Column(String(20))  # 下次跟进日期 (YYYY-MM-DD)
    wechat_id = Column(String(100))  # 微信号

    # 向量数据库关联
    vector_id = Column(String(100)) # ChromaDB 中的 ID
    
    # 来源信息
    source = Column(Text)  # 候选人来源（如：脉脉、LinkedIn、图片OCR等）
    
    # 奖项与科研成果
    awards_achievements = Column(JSON)  # 奖项/荣誉/科研成果 [{type, title, time, description}, ...]
    
    # AI结构化标签
    structured_tags = Column(JSON)  # AI提取的结构化标签
    
    # 人才分级
    talent_tier = Column(String(10))  # S=顶尖大牛, A=优秀, B=不错, C=一般关注
    tier_updated_at = Column(DateTime)  # 评级时间戳，用于追踪重新评级
    
    # 人工运营标签（不被"重新打标签"覆盖）
    talent_labels = Column(JSON, default=[])  # ["高潜", "重点关注", ...]
    
    # 长期培育 (Nurturing) 状态
    # pending -> stage1_sent -> stage1_accepted -> stage2_sent -> stage3_sent -> long_term_pool
    nurture_status = Column(String(50), default='pending')
    nurture_due_date = Column(DateTime) # 下一步行动的截止日期/触发日期

    # ==================== Phase 1.2 新增字段 ====================
    # Stop Rule计数
    outreach_count = Column(Integer, default=0)

    # 最后触达信息
    last_outreach_channel = Column(String(20))  # 'linkedin', 'maimai', 'email', 'wechat', 'phone'
    last_outreach_date = Column(DateTime)

    # 触达里程碑
    linkedin_accepted_at = Column(DateTime)
    maimai_accepted_at = Column(DateTime)
    email_replied_at = Column(DateTime)
    phone_exchanged_at = Column(DateTime)

    # A/B测试
    ab_test_group = Column(String(10))

    # 拒绝原因
    rejection_reason = Column(String(50))
    rejection_details = Column(Text)
    # ==================== Phase 1.2 新增字段 ====================

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "title": self.current_title,
            "company": self.current_company,
            "education": self.education_level,
            "education_details": self.education_details,
            "work_experiences": self.work_experiences,
            "project_experiences": self.project_experiences,
            "experience": self.experience_years,
            "age": self.age,
            "expect_location": self.expect_location,
            "skills": self.skills,
            "summary": self.ai_summary,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "twitter_url": self.twitter_url,
            "personal_website": self.personal_website,
            "website_content": self.website_content,
            "talent_tier": self.talent_tier,
        }

class EmailOutreach(Base):
    """每封系统生成的邮件的完整生命周期记录"""
    __tablename__ = 'email_outreach'

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    pipeline_stage = Column(String(50))       # 邮件对应的 pipeline 阶段 (new/contacted/following_up/...)
    subject = Column(Text)                    # 邮件主题
    body = Column(Text)                       # 邮件正文
    status = Column(String(20), default='draft')  # draft / approved / sent / rejected
    to_email = Column(String(200))            # 收件人邮箱
    sent_at = Column(DateTime)               # 实际发送时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OutreachRecord(Base):
    """统一的多渠道触达记录表"""
    __tablename__ = 'outreach_records'

    id = Column(Integer, primary_key=True)

    # 关联
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False, index=True)
    related_job_id = Column(Integer, ForeignKey('jobs.id'))

    # 渠道和类型
    channel = Column(String(20), nullable=False, index=True)  # 'linkedin', 'maimai', 'email', 'wechat', 'phone'
    outreach_type = Column(String(50), nullable=False, index=True)  # 具体类型
    status = Column(String(20), nullable=False, index=True)  # 'draft', 'sent', 'accepted', 'replied', 'rejected', 'no_response'

    # 内容
    subject = Column(String(500))  # 仅Email
    content = Column(Text, nullable=False)
    prompt_name = Column(String(100))

    # 响应数据
    response_content = Column(Text)
    response_sentiment = Column(String(20))  # 'positive', 'neutral', 'negative'

    # 时间戳
    sent_at = Column(DateTime, index=True)
    responded_at = Column(DateTime)
    accepted_at = Column(DateTime)  # 接受时间 (LinkedIn/脉脉Connect)

    # Stop Rule计数
    is_counted = Column(Boolean, default=True)  # 所有触达都计数（草稿除外）

    # 元数据（JSON，SQLite TEXT存储）
    # 注意: 不能使用metadata（SQLAlchemy保留字）
    meta_data = Column(Text)  # {"profile_url": "...", "alumni_status": "LAMDA", "to_email": "..."}

    # A/B测试
    ab_test_group = Column(String(10))  # 'A', 'B', 'control'
    ab_test_name = Column(String(50))

    # 效果评估
    effectiveness_score = Column(Integer)  # 1-5分，人工评分
    quality_tag = Column(String(20))  # 'high_quality', 'spam_complaint', 'no_response'

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "channel": self.channel,
            "outreach_type": self.outreach_type,
            "status": self.status,
            "subject": self.subject,
            "content": self.content[:100] + "..." if self.content and len(self.content) > 100 else self.content,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "related_job_id": self.related_job_id,
        }


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    company = Column(String(200))
    
    # 原始数据
    raw_jd_text = Column(Text)
    
    # AI 分析数据
    ai_analysis = Column(JSON) # 包含必须技能、软技能、亮点等
    salary_range = Column(String(100))
    location = Column(String(100))
    required_experience_years = Column(Integer)
    
    # 存储完整的 Excel 行数据或解析后的结构化数据
    detail_fields = Column(JSON)
    
    # 新增字段
    job_code = Column(String(100)) # 职位ID/编码
    project_tags = Column(JSON) # 项目标签（用户自定义）
    structured_tags = Column(Text) # AI结构化标签（JSON字符串）
    notes = Column(Text) # 职位备注
    
    # 扩展字段
    department = Column(String(200)) # 部门
    seniority_level = Column(String(100)) # 职级（如P7/P8、高级专家等）
    hr_contact = Column(String(200)) # HR联系人
    jd_link = Column(String(500)) # JD原始链接（客户发布给猎头的来源链接）
    urgency = Column(Integer, default=0) # 紧急程度: 0=普通, 1=较急, 2=紧急, 3=非常紧急
    headcount = Column(Integer) # 职位数量/HC，表示该职位要招聘的人数
    sourcing_notes = Column(Text) # HR提供的sourcing策略原文（对标公司、搜索方向等）
    # 二次发布渠道追踪（猎头在招聘平台发布的记录，与 jd_link 客户原始来源不同）
    # 格式: [{"channel": "MM", "published_at": "2026-02-07T10:00:00"}, {"channel": "LI", ...}]
    # 渠道代码: MM=脉脉, LI=LinkedIn, BOSS=Boss直聘
    published_channels = Column(JSON)

    # 向量数据库关联
    vector_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Integer, default=1) # 1=Active, 0=Closed

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "salary": self.salary_range,
            "analysis": self.ai_analysis,
            "detail_fields": self.detail_fields
        }

class MatchRecord(Base):
    __tablename__ = 'match_records'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    
    match_score = Column(Float) # AI 计算的初始匹配分
    match_reason = Column(Text) # AI 给出的匹配理由
    
    # 人工反馈
    status = Column(String(50), default='pending') # pending, like, dislike, interview, hired
    feedback_notes = Column(Text) # 人工备注
    
    created_at = Column(DateTime, default=datetime.now)


class ResumeTask(Base):
    """后台简历解析任务队列"""
    __tablename__ = 'resume_tasks'
    
    id = Column(Integer, primary_key=True)
    
    # 文件信息
    file_path = Column(String(500), nullable=False)  # 保存的文件路径
    file_name = Column(String(200))  # 原始文件名
    file_type = Column(String(20))  # pdf, txt, jpg, png
    
    # 任务状态
    status = Column(String(20), default='pending')  # pending, processing, done, failed
    
    # 处理结果
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=True)  # 创建的候选人ID
    error_message = Column(Text, nullable=True)  # 失败原因
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime, nullable=True)  # 开始处理时间
    finished_at = Column(DateTime, nullable=True)  # 完成时间


class JobImportTask(Base):
    """后台职位导入任务队列"""
    __tablename__ = 'job_import_tasks'
    
    id = Column(Integer, primary_key=True)
    
    # 文件信息
    file_path = Column(String(500), nullable=False)  # 保存的文件路径
    file_name = Column(String(200))  # 原始文件名
    file_type = Column(String(20))  # csv, xlsx
    
    # 任务状态
    status = Column(String(20), default='pending')  # pending, processing, done, failed
    
    # 处理结果
    jobs_imported = Column(Integer, default=0)  # 成功导入的职位数
    jobs_skipped = Column(Integer, default=0)  # 跳过的职位数（重复）
    jobs_failed = Column(Integer, default=0)  # 失败的职位数
    tags_extracted = Column(Integer, default=0)  # 提取标签的职位数
    error_message = Column(Text, nullable=True)  # 失败原因
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime, nullable=True)  # 开始处理时间
    finished_at = Column(DateTime, nullable=True)  # 完成时间


class BatchRun(Base):
    """Pipeline 批次运行记录 — 用于不同数据源的质量比对"""
    __tablename__ = 'batch_runs'

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(100), nullable=False, unique=True)  # e.g. "phase4_20260225_094524"
    source = Column(String(100), nullable=False)  # "phase4_social_expansion", "new_seed_pipeline", "脉脉"

    # 时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # 种子/输入配置
    seed_config = Column(JSON)  # {"tier": "S,A+,A", "count": 431, "min_cooccurrence": 3}

    # 各阶段数据（JSON 存储完整 phases 对象）
    phase_data = Column(JSON)  # { "phase4_crawl": {...}, "phase3_enrich": {...}, ... }

    # ========== 关键汇总指标（独立列，便于直接查询比对）==========
    # 人数
    total_input = Column(Integer)         # 输入总人数
    total_imported = Column(Integer)      # 新入库人数
    duplicates_skipped = Column(Integer)  # 去重跳过

    # 评级分布
    tier_s = Column(Integer, default=0)
    tier_a_plus = Column(Integer, default=0)
    tier_a = Column(Integer, default=0)
    tier_b_plus = Column(Integer, default=0)
    tier_b = Column(Integer, default=0)
    tier_c = Column(Integer, default=0)
    tier_d = Column(Integer, default=0)

    # 可联系信息覆盖率
    has_email = Column(Integer, default=0)       # 有邮箱
    has_linkedin = Column(Integer, default=0)    # 有 LinkedIn
    has_github = Column(Integer, default=0)      # 有 GitHub
    has_phone = Column(Integer, default=0)       # 有电话
    has_website = Column(Integer, default=0)     # 有个人网站

    # 数据库全局快照
    db_total_candidates = Column(Integer)
    db_total_github = Column(Integer)
    db_total_linkedin = Column(Integer)

    created_at = Column(DateTime, default=datetime.now)


# Database Initialization
# 优先从 DATABASE_URL 环境变量读取（Railway 标准）
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Railway 使用 postgres://，SQLAlchemy 2.0 需要 postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print(f"📦 Using PostgreSQL: {DATABASE_URL[:50]}...") # Debug info
else:
    # 本地开发环境使用 SQLite
    db_env_path = os.getenv("DB_PATH")
    if db_env_path:
        if not os.path.isabs(db_env_path):
            db_path = os.path.abspath(db_env_path)
        else:
            db_path = db_env_path
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 本地默认使用 dev 库，避免误连历史 headhunter.db 导致字段不一致
        db_path = os.path.join(base_dir, "data", "headhunter_dev.db")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    print(f"📦 Using SQLite: {db_path}") # Debug info

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_legacy_schema_compatibility():
    """
    兼容历史数据库：
    老库可能缺少新增字段，导致 ORM 查询直接崩溃。
    启动时自动补齐，避免连接中断。
    """
    try:
        inspector = inspect(engine)
        if "jobs" not in inspector.get_table_names():
            return

        job_cols = {c["name"] for c in inspector.get_columns("jobs")}
        migrations = {
            "urgency": "ALTER TABLE jobs ADD COLUMN urgency INTEGER DEFAULT 0",
            "sourcing_notes": "ALTER TABLE jobs ADD COLUMN sourcing_notes TEXT",
        }
        
        cand_cols = {c["name"] for c in inspector.get_columns("candidates")}
        cand_migrations = {
            "nurture_status": "ALTER TABLE candidates ADD COLUMN nurture_status VARCHAR(50) DEFAULT 'pending'",
            "nurture_due_date": "ALTER TABLE candidates ADD COLUMN nurture_due_date TIMESTAMP",
        }
        
        for col, sql in migrations.items():
            if col not in job_cols:
                with engine.begin() as conn:
                    conn.execute(text(sql))
                print(f"🔧 Auto-migrated: added jobs.{col}")
                
        for col, sql in cand_migrations.items():
            if col not in cand_cols:
                with engine.begin() as conn:
                    conn.execute(text(sql))
                print(f"🔧 Auto-migrated: added candidates.{col}")
    except Exception as e:
        print(f"⚠️ Legacy schema compatibility check failed: {e}")


_ensure_legacy_schema_compatibility()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # 为高频筛选字段创建索引（幂等）
    with engine.begin() as conn:
        # Job indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_job_code ON jobs(job_code)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_urgency ON jobs(urgency)"))
        
        # Candidate indexes - 加速筛选查询
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_company ON candidates(current_company)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_tier ON candidates(talent_tier)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_source ON candidates(source)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_is_friend ON candidates(is_friend)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_last_comm ON candidates(last_communication_at DESC)"))

        # OutreachRecord indexes - Phase 1 新增
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_id ON outreach_records(id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_candidate ON outreach_records(candidate_id, sent_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_channel_type ON outreach_records(channel, outreach_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_records(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_counted ON outreach_records(is_counted)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_sent_at ON outreach_records(sent_at DESC)"))

        # Candidate Phase 1.2 新增字段索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_outreach_count ON candidates(outreach_count)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_linkedin_accepted ON candidates(linkedin_accepted_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_phone_exchanged ON candidates(phone_exchanged_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_last_outreach ON candidates(last_outreach_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidates_ab_test ON candidates(ab_test_group)"))

    
    # 初始化默认 Prompt
    session = SessionLocal()
    
    # Check if defaults exist
    if session.query(SystemPrompt).count() == 0:
        default_candidate_prompt = """
        你是一个专业的招聘专家。请分析以下简历文本，并提取关键信息。
        请严格返回 JSON 格式，不要包含 Markdown 代码块标记。
        
        需要提取的字段说明：
        - summary: 【核心评价】请生成一份 200-300 字的深度分析，包含：1) 核心竞争力与亮点；2) 职业发展路径总结；3) 潜在风险或短板。请使用 Markdown 格式进行分点描述。
        - skills: 技能列表 (数组)
        - name: 姓名
        - email: 邮箱
        - phone: 电话
        - age: 年龄 (数字，估算)
        - expect_location: 期望工作地点
        - education_level: 最高学历
        - current_company: 当前或最近一家公司
        - current_title: 当前或最近职位
        - experience_years: 工作年限 (数字)
        - education_details: 教育经历列表，每项包含: {"school": "学校名", "degree": "学位", "major": "专业", "year": "年份范围"}
        - work_experiences: 工作经历列表，每项包含: {"company": "公司名", "title": "职位", "time": "起止时间", "description": "主要工作内容，请提取关键项目和成果"}
        - project_experiences: 项目经历列表，每项包含: {"name": "项目名", "role": "角色", "time": "时间", "description": "项目描述与职责"}
        """
        
        default_job_prompt = """
        你是一个专业的招聘专家。请分析以下职位描述 (JD)，并提取关键信息。
        请严格返回 JSON 格式。
        需要提取的字段：
        - title: 职位名称
        - company: 公司名称 (如果找不到，返回 "Unknown")
        - location: 工作地点
        - salary_range: 薪资范围
        - required_experience_years: 要求年限 (数字)
        - analysis: {
            "must_have": [核心硬性要求],
            "nice_to_have": [加分项],
            "soft_skills": [软技能],
            "selling_points": [职位亮点]
        }
        """
        
        p1 = SystemPrompt(prompt_type='candidate', prompt_role='system', prompt_name='Default V1', content=default_candidate_prompt, is_active=True)
        p2 = SystemPrompt(prompt_type='job', prompt_role='system', prompt_name='Default V1', content=default_job_prompt, is_active=True)
        
        # Add default User Prompts (Templates)
        user_cand_prompt = """
        【候选人简历内容】：
        {raw_text}
        
        请根据上述系统指令进行分析。
        """
        user_job_prompt = """
        【职位 JD 内容】：
        {raw_text}
        
        请根据上述系统指令进行分析。
        """
        
        p3 = SystemPrompt(prompt_type='candidate', prompt_role='user', prompt_name='Standard Resume Analysis', content=user_cand_prompt, is_active=True)
        p4 = SystemPrompt(prompt_type='job', prompt_role='user', prompt_name='Standard JD Analysis', content=user_job_prompt, is_active=True)
        
        session.add(p1)
        session.add(p2)
        session.add(p3)
        session.add(p4)
        session.commit()
        print("Initialized default prompts.")
        
    session.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
