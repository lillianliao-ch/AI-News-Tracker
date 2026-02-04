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

from database import init_db, SessionLocal, Candidate

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
    skills: List[str] = []
    maimaiUserId: str = ""
    source: str = "maimai"
    sourceUrl: str = ""
    extractedAt: str = ""

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
            education_json.append({
                "school": edu.school,
                "degree": edu.degree,
                "major": edu.major,
                "start_year": edu.startYear,
                "end_year": edu.endYear
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
        
        # 异步提取标签（可选）
        # TODO: 调用 extract_tags_for_candidate
        
        return {
            "success": True,
            "candidateId": candidate.id,
            "message": f"成功导入候选人: {candidate.name}"
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

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8502))
    print(f"🚀 启动 AI Headhunter API 服务器 (端口: {port})")
    uvicorn.run(app, host="0.0.0.0", port=port)
