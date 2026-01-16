import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    notes = Column(Text)
    
    # 好友标记
    is_friend = Column(Integer, default=0)  # 0=未加好友, 1=已加好友
    friend_added_at = Column(String(50))  # 加好友时间
    friend_channel = Column(String(100))  # 加好友渠道（脉脉/微信/LinkedIn等）
    
    # 沟通记录
    communication_logs = Column(JSON)  # [{time, content, stage}, ...] 按时间倒序

    # 向量数据库关联
    vector_id = Column(String(100)) # ChromaDB 中的 ID
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
            "summary": self.ai_summary
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
    project_tags = Column(JSON) # 项目标签
    notes = Column(Text) # 职位备注

    # 向量数据库关联
    vector_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
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
    
    created_at = Column(DateTime, default=datetime.utcnow)

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
        db_path = os.path.join(base_dir, "data", "headhunter.db")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    print(f"📦 Using SQLite: {db_path}") # Debug info

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
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
