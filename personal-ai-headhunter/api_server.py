"""
候选人导入 API 服务
用于接收脉脉插件发送的候选人数据
"""
import os
import sys
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()
load_dotenv('config.env')  # 加载 LLM API keys

from database import init_db, SessionLocal, Candidate, Job

app = FastAPI(title="AI Headhunter API", version="1.0.0")

# CORS 配置 - 允许脉脉页面跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://maimai.cn", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class WorkExperience(BaseModel):
    company: str = ""
    position: str = ""
    startDate: str = ""
    endDate: str = ""
    duration: str = ""
    description: str = ""

class Education(BaseModel):
    school: str = ""
    degree: str = ""
    major: str = ""
    startYear: str = ""
    endYear: str = ""
    description: str = ""
    tags: List[str] = []

class Project(BaseModel):
    name: str = ""
    time: str = ""
    description: str = ""

class CandidateCheckRequest(BaseModel):
    name: str
    school: str = ""
    companies: List[str] = []
    maimaiUserId: str = ""

class CandidateImportRequest(BaseModel):
    name: str
    currentCompany: str = ""
    currentPosition: str = ""
    location: str = ""
    workExperiences: List[WorkExperience] = []
    educations: List[Education] = []
    projects: List[Project] = []
    skills: List[str] = []
    maimaiUserId: str = ""
    source: str = "maimai"
    sourceUrl: str = ""
    extractedAt: str = ""
    experienceYears: int = 0
    education: str = ""
    gender: str = ""
    statusTags: List[str] = []

# 初始化数据库
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Headhunter API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/candidate/check")
def check_candidate(request: CandidateCheckRequest):
    """
    检查候选人是否已存在于数据库
    匹配策略:
    1. 脉脉用户ID精确匹配
    2. 姓名 + 学校 匹配
    3. 姓名 + 任一公司 匹配
    """
    db = SessionLocal()
    try:
        # 策略1: 脉脉用户ID
        if request.maimaiUserId:
            # 检查 notes 字段中是否包含脉脉ID
            candidates = db.query(Candidate).filter(
                Candidate.notes.contains(f"maimai_id:{request.maimaiUserId}")
            ).all()
            if candidates:
                return {"exists": True, "candidateId": candidates[0].id, "matchType": "maimaiUserId"}

        # 策略2: 姓名 + 学校 (从 education_details JSON 字段中匹配)
        if request.name and request.school:
            candidates = db.query(Candidate).filter(
                Candidate.name == request.name
            ).all()
            for candidate in candidates:
                # 检查 education_details 中是否包含该学校
                if candidate.education_details:
                    try:
                        edu_list = json.loads(candidate.education_details) if isinstance(candidate.education_details, str) else candidate.education_details
                        for edu in edu_list:
                            if isinstance(edu, dict) and request.school in str(edu.get('school', '')):
                                return {"exists": True, "candidateId": candidate.id, "matchType": "name+school"}
                    except:
                        pass

        # 策略3: 姓名 + 公司
        if request.name and request.companies:
            # 先按姓名查询
            candidates = db.query(Candidate).filter(
                Candidate.name == request.name
            ).all()
            
            for candidate in candidates:
                # 检查公司匹配
                candidate_companies = []
                if candidate.current_company:
                    candidate_companies.append(candidate.current_company)
                
                # 解析工作经历中的公司 (work_experiences 字段)
                if candidate.work_experiences:
                    try:
                        exps = json.loads(candidate.work_experiences) if isinstance(candidate.work_experiences, str) else candidate.work_experiences
                        for exp in exps:
                            if isinstance(exp, dict) and exp.get('company'):
                                candidate_companies.append(exp['company'])
                    except:
                        pass
                
                # 检查是否有匹配的公司
                for company in request.companies:
                    if company and any(company in c or c in company for c in candidate_companies):
                        return {"exists": True, "candidateId": candidate.id, "matchType": "name+company"}

        return {"exists": False}
    finally:
        db.close()

@app.post("/api/candidate/import")
def import_candidate(request: CandidateImportRequest):
    """
    导入新候选人到数据库
    """
    db = SessionLocal()
    try:
        # 构建工作经历 JSON
        experiences = []
        for exp in request.workExperiences:
            experiences.append({
                "company": exp.company,
                "position": exp.position,
                "start_date": exp.startDate,
                "end_date": exp.endDate,
                "duration": exp.duration,
                "description": exp.description
            })
        
        # 提取第一个学校
        school = ""
        if request.educations:
            school = request.educations[0].school
        
        # 构建教育经历 JSON
        education_json = []
        for edu in request.educations:
            edu_item = {
                "school": edu.school,
                "degree": edu.degree,
                "major": edu.major,
                "start_year": edu.startYear,
                "end_year": edu.endYear
            }
            if edu.description:
                edu_item["description"] = edu.description
            if edu.tags:
                edu_item["tags"] = edu.tags
            education_json.append(edu_item)
        
        # 构建项目经历 JSON
        projects_json = []
        for proj in request.projects:
            projects_json.append({
                "name": proj.name,
                "time": proj.time,
                "description": proj.description
            })
        
        # 构建 notes
        notes_parts = []
        if request.maimaiUserId:
            notes_parts.append(f"maimai_id:{request.maimaiUserId}")
        if request.sourceUrl:
            notes_parts.append(f"source_url:{request.sourceUrl}")
        notes_parts.append(f"imported_at:{datetime.now().isoformat()}")
        
        # ============ 推测年龄、工作年限、最高学历 ============
        current_year = datetime.now().year
        
        # 1. 推测最高学历
        education_level = ""
        degree_priority = {"博士": 4, "PhD": 4, "硕士": 3, "Master": 3, "本科": 2, "Bachelor": 2, "专科": 1}
        max_priority = 0
        for edu in education_json:
            degree = edu.get("degree", "")
            priority = degree_priority.get(degree, 0)
            if priority > max_priority:
                max_priority = priority
                education_level = degree
        
        # 2. 推测工作年限 (从最早工作开始年份计算)
        experience_years = 0
        earliest_work_year = current_year
        for exp in experiences:
            start_date = exp.get("start_date", "")
            if start_date:
                # 解析年份: "2012.3" -> 2012
                try:
                    year = int(start_date.split(".")[0])
                    if year < earliest_work_year:
                        earliest_work_year = year
                except:
                    pass
        if earliest_work_year < current_year:
            experience_years = current_year - earliest_work_year
        
        # 3. 推测年龄 (基于本科入学年份，假设18岁入学)
        age = None
        bachelor_start_year = None
        for edu in education_json:
            degree = edu.get("degree", "")
            start_year = edu.get("start_year", "")
            if degree in ["本科", "Bachelor"] and start_year:
                try:
                    bachelor_start_year = int(start_year)
                    break
                except:
                    pass
        
        if bachelor_start_year:
            age = current_year - bachelor_start_year + 18
        elif earliest_work_year < current_year:
            # 备用推测: 假设毕业后工作，本科毕业22岁
            age = current_year - earliest_work_year + 22
        
        print(f"  📊 推测: 学历={education_level}, 工作年限={experience_years}年, 年龄={age}岁")
        
        # 创建候选人 (使用正确的字段名)
        candidate = Candidate(
            name=request.name,
            current_company=request.currentCompany,
            current_title=request.currentPosition,
            expect_location=request.location,
            work_experiences=experiences if experiences else None,
            education_details=education_json if education_json else None,
            project_experiences=projects_json if projects_json else None,
            skills=request.skills if request.skills else None,
            source=request.source,
            notes="\n".join(notes_parts),
            education_level=education_level if education_level else None,
            experience_years=experience_years if experience_years > 0 else None,
            age=age,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        print(f"✅ 导入候选人成功: {candidate.name} (ID: {candidate.id})")
        
        # 异步：提取标签 + 创建专属门户（后台线程，不阻塞响应）
        import threading
        def _post_import_bg(cid, cname):
            # 1. 提取标签
            try:
                from extract_tags import extract_tags_for_candidate_by_id
                print(f"🏷️ 开始为 {cname} (ID={cid}) 提取标签...")
                tags = extract_tags_for_candidate_by_id(cid)
                if tags:
                    print(f"🏷️ ✅ {cname} 标签提取完成")
                else:
                    print(f"🏷️ ⚠️ {cname} 标签提取失败")
            except Exception as e:
                print(f"🏷️ ❌ {cname} 标签提取异常: {e}")
            
            # 2. 创建专属门户
            try:
                import hashlib, requests
                PORTAL_BASE = "https://jobs.rupro-consulting.com"
                token = hashlib.sha256('ruproAI'.encode()).hexdigest()
                resp = requests.post(f"{PORTAL_BASE}/api/portal/create", json={
                    'candidate_id': cid,
                    'candidate_name': cname,
                }, cookies={'auth_token': token}, timeout=15)
                if resp.status_code == 200 and resp.json().get('success'):
                    portal_code = resp.json()['portal_code']
                    print(f"🔗 ✅ {cname} 门户已创建: /p/{portal_code}")
                else:
                    print(f"🔗 ⚠️ {cname} 门户创建失败: {resp.text[:100]}")
            except Exception as e:
                print(f"🔗 ❌ {cname} 门户创建异常: {e}")
        
        threading.Thread(target=_post_import_bg, args=(candidate.id, candidate.name), daemon=True).start()
        
        return {
            "success": True,
            "candidateId": candidate.id,
            "message": f"成功导入候选人: {candidate.name}（标签提取+门户创建中...）"
        }
    except Exception as e:
        db.rollback()
        print(f"❌ 导入候选人失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/candidate/{candidate_id}")
def get_candidate(candidate_id: int):
    """
    获取候选人详情
    """
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        return {
            "id": candidate.id,
            "name": candidate.name,
            "current_company": candidate.current_company,
            "current_title": candidate.current_title,
            "location": candidate.expect_location,
            "education_details": candidate.education_details,
            "skills": candidate.skills,
            "source": candidate.source
        }
    finally:
        db.close()

# ============ 职位相关 API (供脉脉发布职位使用) ============

@app.get("/api/jobs")
def list_jobs(company: Optional[str] = None, active_only: bool = True, limit: int = 200, has_description: bool = False, search: Optional[str] = None):
    """
    获取职位列表，供脉脉插件选择要发布的职位
    has_description=True 时只返回有描述的职位
    search: 按 job_code 或 title 模糊搜索
    """
    db = SessionLocal()
    try:
        query = db.query(Job)
        
        # 搜索（job_code 或 title）
        if search:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Job.job_code.contains(search),
                    Job.title.contains(search),
                    Job.company.contains(search)
                )
            )
        
        # 过滤公司
        if company:
            query = query.filter(Job.company == company)
        
        # 只获取活跃职位
        if active_only:
            query = query.filter(Job.is_active == 1)
        
        # 只获取有描述的职位
        if has_description:
            query = query.filter(Job.raw_jd_text != None)
            query = query.filter(Job.raw_jd_text != '')
        
        # 获取所有职位
        all_jobs = query.order_by(Job.created_at.desc()).limit(limit * 2).all()
        
        # 排序：有描述的排前面
        jobs_with_desc = [j for j in all_jobs if j.raw_jd_text and j.raw_jd_text.strip()]
        jobs_without_desc = [j for j in all_jobs if not j.raw_jd_text or not j.raw_jd_text.strip()]
        sorted_jobs = (jobs_with_desc + jobs_without_desc)[:limit]
        
        return {
            "success": True,
            "count": len(sorted_jobs),
            "jobs": [
                {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "department": job.department,
                    "location": job.location,
                    "salary_range": job.salary_range,
                    "job_code": job.job_code,
                    "urgency": job.urgency,
                    "headcount": job.headcount,
                    "is_active": job.is_active,
                    "has_description": bool(job.raw_jd_text and job.raw_jd_text.strip()),
                    "description_length": len(job.raw_jd_text) if job.raw_jd_text else 0,
                    "published_channels": job.published_channels or []
                }
                for job in sorted_jobs
            ]
        }
    finally:
        db.close()

@app.get("/api/jobs/active")
def api_active_jobs(limit: int = 50):
    """获取活跃JD列表（按紧急度排序，供消息生成时选择JD）"""
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(
            Job.is_active == 1
        ).order_by(
            Job.urgency.desc(),
            Job.created_at.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "count": len(jobs),
            "jobs": [_job_orm_to_dict(j) for j in jobs]
        }
    finally:
        db.close()

@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: int):
    """
    获取职位详情，返回用于脉脉表单填写的所有必要字段
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="职位不存在")
        
        # 解析薪资范围 (格式: "30K-60K" 或 "20-40万")
        salary_min = ""
        salary_max = ""
        salary_months = "12"  # 默认12薪
        if job.salary_range:
            salary_str = job.salary_range.upper()
            # 尝试解析 "30K-60K" 格式
            import re
            match = re.search(r'(\d+)K?\s*[-~]\s*(\d+)K?', salary_str)
            if match:
                salary_min = match.group(1)
                salary_max = match.group(2)
        
        # 解析经验要求
        experience_text = ""
        if job.required_experience_years:
            years = job.required_experience_years
            if years <= 1:
                experience_text = "1年以内"
            elif years <= 3:
                experience_text = "1-3年"
            elif years <= 5:
                experience_text = "3-5年"
            elif years <= 10:
                experience_text = "5-10年"
            else:
                experience_text = "10年以上"
        
        # 从 notes 或 detail_fields 中提取关键词
        keywords = []
        if job.notes:
            # 尝试从备注中提取【关键词】部分
            import re
            kw_match = re.search(r'【关键词】\s*(.*?)(?=【|$)', job.notes, re.DOTALL)
            if kw_match:
                kw_text = kw_match.group(1).strip()
                # 分割关键词
                keywords = [k.strip() for k in re.split(r'[,，、\n]', kw_text) if k.strip()]
        
        return {
            "success": True,
            "job": {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "department": job.department,
                "location": job.location,
                
                # 职位描述 (使用 raw_jd_text)
                "description": job.raw_jd_text or "",
                
                # 薪资相关
                "salary_range": job.salary_range,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_months": salary_months,
                
                # 要求
                "experience_text": experience_text,
                "required_experience_years": job.required_experience_years,
                "seniority_level": job.seniority_level,
                
                # 关键词与标签
                "keywords": keywords,
                "project_tags": job.project_tags if isinstance(job.project_tags, list) else [],
                
                # 其他信息
                "job_code": job.job_code,
                "headcount": job.headcount,
                "urgency": job.urgency,
                "hr_contact": job.hr_contact,
                "jd_link": job.jd_link,
                "notes": job.notes,
                
                # 脉脉表单专用字段 (需要用户在系统中配置)
                "maimai_position_type": "",  # 职位类别（需要映射）
                "maimai_industry": "",       # 行业要求（需要映射）
                "maimai_education": "",      # 学历要求
                "receive_email": ""          # 接收简历邮箱
            }
        }
    finally:
        db.close()

@app.get("/api/jobs/{job_id}/maimai-form")
def get_maimai_form_data(job_id: int, email: str = ""):
    """
    获取专门用于填写脉脉表单的数据格式
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="职位不存在")
        
        # 提取关键词
        import re
        keywords = []
        if job.notes:
            kw_match = re.search(r'【关键词】\s*(.*?)(?=【|$)', job.notes, re.DOTALL)
            if kw_match:
                kw_text = kw_match.group(1).strip()
                keywords = [k.strip() for k in re.split(r'[,，、\n]', kw_text) if k.strip()][:5]  # 最多5个
        
        return {
            "success": True,
            "formData": {
                # 基本信息
                "position": job.title,
                "description": job.raw_jd_text or "",
                
                # 职位要求
                "salary_min": "",  # 需要根据 salary_range 解析
                "salary_max": "",
                "experience": str(job.required_experience_years) if job.required_experience_years else "",
                
                # 可选信息
                "keywords": keywords,
                "location": job.location or "",
                "email": email,
                
                # 元信息
                "job_id": job.id,
                "job_code": job.job_code
            }
        }
    finally:
        db.close()

# ============ 发布渠道追踪 API ============
# 用于记录职位在各招聘平台的二次发布状态
# 注意：这里记录的是猎头在招聘平台的发布，不是客户原始JD来源(jd_link)
# 支持渠道: MM=脉脉, LI=LinkedIn, BOSS=Boss直聘
# 数据格式: [{"channel": "MM", "published_at": "2026-02-07T10:00:00"}, ...]

@app.post("/api/jobs/{job_id}/publish")
def mark_job_published(job_id: int, channel: str = "MM"):
    """
    标记职位已在某渠道发布（二次发布追踪）
    - 同渠道重复调用 → 更新发布时间
    - 不同渠道调用 → 追加记录
    - channel: MM=脉脉, LI=LinkedIn, BOSS=Boss直聘
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="职位不存在")
        
        # 读取现有发布记录（兼容 JSON 字符串和列表两种格式）
        channels = job.published_channels or []
        if isinstance(channels, str):
            import json
            channels = json.loads(channels)
        
        # 检查是否已发布到该渠道：已有则更新时间，否则追加
        existing = [c for c in channels if c.get("channel") == channel]
        if existing:
            existing[0]["published_at"] = datetime.now().isoformat()
        else:
            channels.append({
                "channel": channel,
                "published_at": datetime.now().isoformat()
            })
        
        job.published_channels = channels
        db.commit()
        
        return {
            "success": True,
            "message": f"已标记职位 {job.job_code or job.id} 发布到 {channel}",
            "published_channels": channels
        }
    finally:
        db.close()

# ============ 个性化消息生成 API ============
# 为脉脉招聘「立即沟通」场景生成 AI 个性化消息（300字限制）

from pydantic import BaseModel as _BaseModel

class MessageGenerateRequest(_BaseModel):
    candidate: dict  # 候选人 profile（从页面提取）
    job_id: Optional[int] = None  # 指定JD（可选，不传则自动匹配）

class CommLogRequest(_BaseModel):
    candidate_name: str
    message: str = ""
    channel: str = "maimai_direct"  # maimai_direct | maimai_friend
    job_id: Optional[int] = None
    candidate_company: str = ""
    candidate_position: str = ""


MESSAGE_SYSTEM_PROMPT = """你是Lillian的AI助手。Lillian是一位专注AI/高科技领域的猎头。

你的任务：根据候选人背景和职位信息，生成一条个性化的招聘沟通消息。

## 称呼规则
- 消息开头的称呼已经在下方指定，请直接使用，不要修改

## 内容要求
1. 自我介绍：我是Lillian，专注AI/互联网/高科技领域的猎头
2. 提到对方具体的亮点（公司/职位/技术方向/教育背景），要具体不要泛泛而谈。例如"字节跳动6年商业化和搜广推经验"比"工作经历非常丰富"好得多
3. ⚠️ 准确判断候选人的核心方向：
   - 以最长/最核心的全职工作经历为主，兼职/合同工/众包经历不要当主要亮点
   - 准确使用方向词：数据分析师说"数据方向"，商业分析师说"商业分析/数据方向"，后端工程师说"工程方向"，算法工程师说"算法方向"。不要给非算法背景的人说"算法方向"
   - 不要过度包装：标注员/AI训练师不等于"LLM专家"，助理不等于"管理层"
4. 关联职位机会时注意：
   - 如果提供的JD和候选人背景高度相关（同方向同类型），可以提公司+岗位名称+为什么匹配
   - 🚫 其他情况下，不要提任何具体公司名或岗位名！直接说"我们有一些机会跟您比较匹配"
   - 🚫🚫 绝对禁止"虽然目前职位与您不完全一致"这类句式！不要提任何"不一致/不匹配"的字眼，只说正面的
   - 第一次打招呼的目的是建立联系，不是硬推某个JD
5. 行动呼吁：用"希望能与您进一步交流"，不要说"了解您的职业规划和发展方向"这种套话
6. 末尾附上：我的电话/微信 13585841775，方便时联系我～
7. 语气：专业但亲切自然，像朋友推荐机会一样，不要过于正式或吹捧

## 格式要求
- 严格控制在250字以内（给300字限制留余量）
- 直接输出消息文本，不要加引号或markdown标记
- 不要分点列举，写成自然的一段话
- 不要用"巨大价值"、"非常匹配"、"非常丰富"、"令人印象深刻"等空洞的吹捧词
- 🚫 不要加"祝好""Best regards"等签名，不要单独一行写"您好，"，直接写成连贯的一段话"""


import re

def _determine_greeting(name: str) -> str:
    """用代码判断称呼，不依赖LLM"""
    if not name:
        return "您好"
    name = name.strip()
    # 检查是否全是中文字符
    if re.match(r'^[\u4e00-\u9fff]{2,4}$', name):
        # 正常中文名：用姓+先生（默认先生，因为无法确定性别）
        surname = name[0]
        if len(name) == 2:
            return f"{name}您好"  # 两字名直接用全名
        else:
            return f"{surname}先生"  # 三四字名用姓+先生
    else:
        return "您好"


def _build_candidate_description(profile: dict) -> str:
    """构建候选人文本描述"""
    lines = [f"候选人信息："]
    lines.append(f"- 姓名: {profile.get('name', '未知')}")
    lines.append(f"- 当前公司: {profile.get('currentCompany', profile.get('company', '未知'))}")
    lines.append(f"- 当前职位: {profile.get('currentPosition', profile.get('position', '未知'))}")

    exp = profile.get('experienceYears', profile.get('experience', ''))
    if exp:
        lines.append(f"- 工作年限: {exp}")

    edu = profile.get('education', '')
    if edu:
        lines.append(f"- 学历: {edu}")

    loc = profile.get('location', '')
    if loc:
        lines.append(f"- 所在地: {loc}")

    skills = profile.get('skills', [])
    if skills:
        skill_str = ', '.join(skills[:10]) if isinstance(skills, list) else str(skills)
        lines.append(f"- 技能: {skill_str}")

    # 工作经历
    work_exp = profile.get('workExperiences', profile.get('work_experiences', []))
    if work_exp and isinstance(work_exp, list):
        lines.append("- 工作经历:")
        for exp in work_exp[:3]:
            if isinstance(exp, dict):
                company = exp.get('company', '')
                title = exp.get('title', exp.get('position', ''))
                period = exp.get('period', exp.get('time', exp.get('duration', '')))
                desc = exp.get('description', '')[:80]
                lines.append(f"  · {company} {title} ({period})")
                if desc:
                    lines.append(f"    {desc}")

    # 教育经历
    educations = profile.get('educations', profile.get('education_details', []))
    if educations and isinstance(educations, list):
        lines.append("- 教育经历:")
        for e in educations[:2]:
            if isinstance(e, dict):
                school = e.get('school', '')
                degree = e.get('degree', '')
                major = e.get('major', '')
                tags = e.get('tags', [])
                desc = e.get('description', '')[:150]
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                lines.append(f"  · {school} {degree} {major}{tag_str}")
                if desc:
                    lines.append(f"    {desc}")

    # 项目经历
    projects = profile.get('projects', [])
    if projects and isinstance(projects, list):
        lines.append("- 项目经历:")
        for p in projects[:2]:
            if isinstance(p, dict):
                name = p.get('name', '')
                desc = p.get('description', '')[:100]
                lines.append(f"  · {name}")
                if desc:
                    lines.append(f"    {desc}")

    return '\n'.join(lines)


def _build_job_description(job_info: dict) -> str:
    """构建JD文本描述"""
    lines = ["\n推荐职位："]
    lines.append(f"- 职位: {job_info.get('title', '未知')}")
    lines.append(f"- 公司: {job_info.get('company', '未知')}")

    if job_info.get('location'):
        lines.append(f"- 地点: {job_info['location']}")
    if job_info.get('salary_range'):
        lines.append(f"- 薪资: {job_info['salary_range']}")
    if job_info.get('headcount'):
        lines.append(f"- HC: {job_info['headcount']}")
    if job_info.get('job_code'):
        lines.append(f"- 职位编号: {job_info['job_code']}")

    # JD核心要求
    ai_analysis = job_info.get('ai_analysis')
    if ai_analysis and isinstance(ai_analysis, dict):
        must = ai_analysis.get('must_have_skills', [])
        if must:
            lines.append(f"- 核心要求: {', '.join(must[:5])}")

    return '\n'.join(lines)


def _job_orm_to_dict(job) -> dict:
    """Job ORM对象 → dict"""
    tags = None
    if job.structured_tags:
        try:
            tags = json.loads(job.structured_tags) if isinstance(job.structured_tags, str) else job.structured_tags
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location or "",
        "salary_range": job.salary_range or "",
        "job_code": job.job_code or "",
        "urgency": job.urgency or 0,
        "headcount": job.headcount or 0,
        "department": job.department or "",
        "ai_analysis": job.ai_analysis,
        "structured_tags": tags,
    }


@app.post("/api/generate-message")
def api_generate_message(req: MessageGenerateRequest):
    """
    生成个性化招聘消息（for 脉脉立即沟通 300字场景）
    """
    from openai import OpenAI

    candidate_profile = req.candidate
    if not candidate_profile.get('name'):
        raise HTTPException(status_code=400, detail="缺少候选人姓名")

    # 获取JD信息
    job_info = None
    db = SessionLocal()
    try:
        if req.job_id:
            job = db.query(Job).filter(Job.id == req.job_id).first()
            if job:
                job_info = _job_orm_to_dict(job)
        else:
            # 自动匹配：优先紧急JD
            urgent = db.query(Job).filter(
                Job.is_active == 1, Job.urgency >= 2
            ).order_by(Job.urgency.desc()).first()
            if urgent:
                job_info = _job_orm_to_dict(urgent)
            else:
                latest = db.query(Job).filter(
                    Job.is_active == 1
                ).order_by(Job.created_at.desc()).first()
                if latest:
                    job_info = _job_orm_to_dict(latest)
    finally:
        db.close()

    # 构建 prompt
    profile_text = _build_candidate_description(candidate_profile)
    job_text = _build_job_description(job_info) if job_info else ""
    greeting = _determine_greeting(candidate_profile.get('name', ''))

    user_content = f"""{profile_text}{job_text}

称呼指令：消息必须以"{greeting}"开头。
请生成一条250字以内的个性化招聘沟通消息。"""

    # 调用 LLM
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        model = os.getenv("MODEL_NAME", "qwen-max")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": MESSAGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            timeout=30
        )
        message = response.choices[0].message.content.strip()

        # 清理引号包裹
        for q_open, q_close in [('"', '"'), ('「', '」'), ('"', '"')]:
            if message.startswith(q_open) and message.endswith(q_close):
                message = message[len(q_open):-len(q_close)]
                break

        result = {
            "success": True,
            "message": message,
            "char_count": len(message),
        }
        if job_info:
            result["job_used"] = {
                "id": job_info["id"],
                "title": job_info["title"],
                "company": job_info["company"]
            }
        return result

    except Exception as e:
        print(f"❌ LLM消息生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"LLM调用失败: {str(e)}")



@app.post("/api/comm-log")
def api_comm_log(req: CommLogRequest):
    """记录沟通日志，自动设置管道阶段和跟进时间"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(
            Candidate.name == req.candidate_name
        ).first()

        if not candidate:
            candidate = Candidate(
                name=req.candidate_name,
                source='脉脉',
                current_company=req.candidate_company,
                current_title=req.candidate_position,
                pipeline_stage='contacted',
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(candidate)
            db.flush()

        logs = []
        if candidate.communication_logs:
            try:
                existing = candidate.communication_logs
                if isinstance(existing, str):
                    existing = json.loads(existing)
                if isinstance(existing, list):
                    logs = existing
            except (json.JSONDecodeError, TypeError):
                pass

        new_log = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "channel": req.channel,
            "action": "greeting",
            "content": req.message[:500] if req.message else "",
            "direction": "outbound",
        }
        if req.job_id:
            new_log["job_id"] = req.job_id

        logs.insert(0, new_log)
        candidate.communication_logs = logs
        candidate.last_communication_at = datetime.now()
        candidate.updated_at = datetime.now()

        # 自动设置管道阶段和跟进时间
        # 只要还没进入更高阶段，就自动设为 contacted
        advanced_stages = {'contacted', 'following_up', 'replied', 'wechat_connected', 'in_pipeline'}
        if candidate.pipeline_stage not in advanced_stages:
            candidate.pipeline_stage = 'contacted'
            follow_up = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
            candidate.follow_up_date = follow_up
            print(f"  📅 {candidate.name}: new → contacted, 跟进日期: {follow_up}")

        db.commit()

        return {
            "success": True,
            "candidate_id": candidate.id,
            "pipeline_stage": candidate.pipeline_stage,
            "follow_up_date": candidate.follow_up_date,
            "message": f"已记录与 {candidate.name} 的沟通"
        }
    except Exception as e:
        db.rollback()
        print(f"❌ 记录沟通日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ============ 管道阶段流转 API ============

class PipelineUpdateRequest(BaseModel):
    candidate_id: int
    stage: str  # contacted/following_up/replied/wechat_connected/in_pipeline/closed
    follow_up_days: Optional[int] = None
    wechat_id: Optional[str] = None
    note: Optional[str] = None

STAGE_LABELS = {
    "new": "🆕 新发现",
    "contacted": "📤 已打招呼",
    "following_up": "🔄 跟进中",
    "replied": "💬 已回复",
    "wechat_connected": "💚 已加微信",
    "in_pipeline": "🎯 面试流程中",
    "closed": "⏸️ 暂时关闭",
}

STAGE_DEFAULT_FOLLOWUP = {
    "contacted": 3,
    "following_up": 5,
    "replied": 1,
    "wechat_connected": 2,
    "in_pipeline": 3,
}

@app.post("/api/pipeline/update")
def api_pipeline_update(req: PipelineUpdateRequest):
    """更新候选人管道阶段"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")

        old_stage = candidate.pipeline_stage or 'new'
        candidate.pipeline_stage = req.stage

        follow_up_days = req.follow_up_days or STAGE_DEFAULT_FOLLOWUP.get(req.stage, 0)
        if follow_up_days > 0:
            candidate.follow_up_date = (datetime.now() + timedelta(days=follow_up_days)).strftime("%Y-%m-%d")
        elif req.stage == 'closed':
            candidate.follow_up_date = None

        if req.wechat_id:
            candidate.wechat_id = req.wechat_id

        logs = candidate.communication_logs or []
        if isinstance(logs, str):
            logs = json.loads(logs)
        logs.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "channel": "system",
            "action": "stage_change",
            "content": f"{STAGE_LABELS.get(old_stage, old_stage)} → {STAGE_LABELS.get(req.stage, req.stage)}" + (f" | {req.note}" if req.note else ""),
            "direction": "system",
        })
        candidate.communication_logs = logs
        candidate.updated_at = datetime.now()
        db.commit()

        return {
            "success": True,
            "stage": req.stage,
            "stage_label": STAGE_LABELS.get(req.stage, req.stage),
            "follow_up_date": candidate.follow_up_date,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/pipeline/follow-ups")
def api_follow_ups(date: str = None, include_overdue: bool = True):
    """获取需要跟进的候选人列表"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    db = SessionLocal()
    try:
        query = db.query(Candidate).filter(
            Candidate.pipeline_stage.notin_(['closed', 'new']),
            Candidate.follow_up_date.isnot(None)
        )

        if include_overdue:
            candidates = query.filter(Candidate.follow_up_date <= date).all()
        else:
            candidates = query.filter(Candidate.follow_up_date == date).all()

        results = []
        for c in candidates:
            logs = c.communication_logs or []
            if isinstance(logs, str):
                try:
                    logs = json.loads(logs)
                except:
                    logs = []
            outbound_count = sum(1 for l in logs if isinstance(l, dict) and l.get('direction') == 'outbound')

            days_overdue = 0
            if c.follow_up_date:
                try:
                    days_overdue = (datetime.strptime(date, "%Y-%m-%d") - datetime.strptime(c.follow_up_date, "%Y-%m-%d")).days
                except:
                    pass

            results.append({
                "id": c.id,
                "name": c.name,
                "company": c.current_company or "",
                "title": c.current_title or "",
                "pipeline_stage": c.pipeline_stage,
                "stage_label": STAGE_LABELS.get(c.pipeline_stage, c.pipeline_stage),
                "follow_up_date": c.follow_up_date,
                "days_overdue": max(0, days_overdue),
                "outbound_count": outbound_count,
                "last_comm": logs[0] if logs else None,
                "wechat_id": c.wechat_id,
                "phone": c.phone,
            })

        results.sort(key=lambda x: x['days_overdue'], reverse=True)

        return {
            "success": True,
            "date": date,
            "total": len(results),
            "candidates": results
        }
    finally:
        db.close()


@app.get("/api/pipeline/stats")
def api_pipeline_stats():
    """管道统计：各阶段人数和本周沟通数据"""
    db = SessionLocal()
    try:
        stage_counts = {}
        for stage, label in STAGE_LABELS.items():
            count = db.query(Candidate).filter(
                Candidate.pipeline_stage == stage
            ).count()
            if count > 0:
                stage_counts[stage] = {"label": label, "count": count}

        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_contacted = db.query(Candidate).filter(
            Candidate.last_communication_at >= week_start
        ).count()

        today = datetime.now().strftime("%Y-%m-%d")
        today_followups = db.query(Candidate).filter(
            Candidate.follow_up_date <= today,
            Candidate.pipeline_stage.notin_(['closed', 'new'])
        ).count()

        return {
            "success": True,
            "stages": stage_counts,
            "week_contacted": week_contacted,
            "today_followups": today_followups,
        }
    finally:
        db.close()


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8502))
    print(f"🚀 启动 AI Headhunter API 服务器 (端口: {port})")
    print(f"📋 API 列表:")
    print(f"  POST /api/generate-message    — AI个性化消息生成")
    print(f"  GET  /api/jobs/active          — 活跃JD列表")
    print(f"  POST /api/comm-log             — 记录沟通日志")
    print(f"  POST /api/pipeline/update      — 管道阶段流转")
    print(f"  GET  /api/pipeline/follow-ups  — 今日需跟进列表")
    print(f"  GET  /api/pipeline/stats       — 管道统计")
    uvicorn.run(app, host="0.0.0.0", port=port)

