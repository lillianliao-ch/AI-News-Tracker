"""
AI 猎头 API Server (FastAPI, port 8502)
========================================
候选人导入 & 数据管理 API，供浏览器插件（脉脉/LinkedIn）和 Streamlit 前端调用。

端点一览:
─────────────────────────────────────────────────────────────
候选人 - 导入与同步
  POST /api/candidate/check          检查候选人是否已存在（maimai_id/姓名+学校/姓名+公司）
  POST /api/candidate/import         脉脉插件导入新候选人（仅新建，不更新）
  POST /api/candidate/maimai-sync    脉脉 Upsert 同步：不存在→新建，已存在→合并更新
  POST /api/candidate/linkedin-sync  LinkedIn Upsert 同步：按 linkedin_url 去重，合并更新

候选人 - 数据增强
  POST /api/candidate/{id}/re-tier        重新 AI 评级（调用 LLM）
  POST /api/candidate/{id}/refresh-github 刷新 GitHub 数据
  GET  /api/candidate/{id}/search-scholar 搜索 Google Scholar 候选匹配
  POST /api/candidate/{id}/fetch-scholar  获取并保存 Scholar 论文数据
  GET  /api/candidate/{id}                获取候选人详情

职位 (JD)
  GET  /api/jobs                 职位列表（支持公司/关键词筛选）
  GET  /api/jobs/active          活跃职位简要列表
  GET  /api/jobs/{id}            职位详情
  GET  /api/jobs/{id}/maimai-form 脉脉发布表单数据
  POST /api/jobs/{id}/publish    标记职位已发布

沟通 & 招聘管线
  POST /api/generate-message     AI 生成个性化沟通消息
  POST /api/comm-log             记录沟通日志
  POST /api/pipeline/update      更新招聘管线状态
  GET  /api/pipeline/follow-ups  获取待跟进列表
  GET  /api/pipeline/stats       管线统计数据
─────────────────────────────────────────────────────────────
"""
import os
import sys
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()
load_dotenv('config.env')  # 加载 LLM API keys

from database import init_db, SessionLocal, Candidate, Job, EmailOutreach, OutreachRecord
import json
from prompts import (
    LINKEDIN_SYSTEM_PROMPT,
    LINKEDIN_CONNECT_ONLY_PROMPT,
    MESSAGE_SYSTEM_PROMPT,
    EMAIL_PROMPT_ACADEMIC,
    EMAIL_PROMPT_HAS_WEBSITE,
    EMAIL_PROMPT_GITHUB_ONLY,
    EMAIL_PROMPT_EMAIL_ONLY,
)

app = FastAPI(title="AI Headhunter API", version="1.0.0")

# CORS 配置 - 允许所有来源（本地开发API）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    source: str = "脉脉"
    sourceUrl: str = ""
    extractedAt: str = ""
    experienceYears: int = 0
    education: str = ""
    gender: str = ""
    statusTags: List[str] = []
    talentTier: str = None

class LinkedInSyncRequest(BaseModel):
    """LinkedIn ContactOut Scraper 同步请求"""
    name: str
    linkedinUrl: str = ""
    currentTitle: str = ""
    location: str = ""
    workExperiences: List[WorkExperience] = []
    educations: List[Education] = []
    notes: str = ""
    source: str = "linkedin"

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

class DebugGenerateRequest(BaseModel):
    prompt: str
    temperature: float = 0.7

@app.post("/api/debug/generate-raw")
def debug_generate_raw(req: DebugGenerateRequest):
    """
    调试用接口：直接调用 LLM 生成文本
    """
    try:
        # 尝试复用 job_search.py 或其他地方的 LLM 客户端
        # 这里为了简单，直接从 os.environ 读取配置并调用 OpenAI 兼容接口
        # 或者如果有 job_search.py 中的 client，可以直接用
        
        # 简单起见，这里直接 import openai
        import openai
        from openai import OpenAI
        
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = os.getenv("LLM_MODEL", "qwen-plus")
        
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing API Key config")
            
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': req.prompt}
            ],
            temperature=req.temperature,
            stream=False
        )
        return {"text": completion.choices[0].message.content}
        
    except Exception as e:
        print(f"LLM Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
                PORTAL_BASE = "https://job-share-service-production.up.railway.app"
                token = hashlib.sha256('ruproAI'.encode()).hexdigest()
                resp = requests.post(f"{PORTAL_BASE}/api/portal/create", json={
                    'candidate_id': cid,
                    'candidate_name': cname,
                }, cookies={'auth_token': token}, timeout=15)
                if resp.status_code == 200 and resp.json().get('success'):
                    portal_code = resp.json()['portal_code']
                    print(f"🔗 ✅ {cname} 门户已创建: {PORTAL_BASE}/p/{portal_code}")
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


@app.post("/api/candidate/maimai-sync")
def maimai_sync(request: CandidateImportRequest):
    """
    脉脉候选人同步（upsert）：
    1. 匹配策略：maimai_id → 姓名+学校 → 姓名+公司
    2. 不存在 → 新建（复用 import 逻辑）
    3. 已存在 → 比较后补充更新（参考 linkedin-sync）
    """
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="姓名不能为空")
    
    db = SessionLocal()
    try:
        # ===== Step 1: 查找已有候选人 =====
        existing = None
        match_type = ""
        
        # 策略1: maimai_id 精确匹配
        if request.maimaiUserId:
            candidates = db.query(Candidate).filter(
                Candidate.notes.contains(f"maimai_id:{request.maimaiUserId}")
            ).all()
            if candidates:
                existing = candidates[0]
                match_type = "maimaiUserId"
        
        # 策略2: 姓名 + 学校
        if not existing and request.name and request.educations:
            first_school = request.educations[0].school if request.educations else ""
            if first_school:
                candidates = db.query(Candidate).filter(
                    Candidate.name == request.name.strip()
                ).all()
                for candidate in candidates:
                    if candidate.education_details:
                        try:
                            edu_list = json.loads(candidate.education_details) if isinstance(candidate.education_details, str) else candidate.education_details
                            for edu in (edu_list or []):
                                if isinstance(edu, dict) and first_school in str(edu.get('school', '')):
                                    existing = candidate
                                    match_type = "name+school"
                                    break
                        except:
                            pass
                    if existing:
                        break
        
        # 策略3: 姓名 + 公司
        if not existing and request.name:
            req_companies = [request.currentCompany] if request.currentCompany else []
            for exp in request.workExperiences:
                if exp.company and exp.company not in req_companies:
                    req_companies.append(exp.company)
            
            if req_companies:
                candidates = db.query(Candidate).filter(
                    Candidate.name == request.name.strip()
                ).all()
                for candidate in candidates:
                    candidate_companies = []
                    if candidate.current_company:
                        candidate_companies.append(candidate.current_company)
                    if candidate.work_experiences:
                        try:
                            exps = json.loads(candidate.work_experiences) if isinstance(candidate.work_experiences, str) else candidate.work_experiences
                            for exp in (exps or []):
                                if isinstance(exp, dict) and exp.get('company'):
                                    candidate_companies.append(exp['company'])
                        except:
                            pass
                    for company in req_companies:
                        if company and any(company in c or c in company for c in candidate_companies):
                            existing = candidate
                            match_type = "name+company"
                            break
                    if existing:
                        break
        
        # ===== 构建数据 =====
        new_work_exps = []
        for exp in request.workExperiences:
            new_work_exps.append({
                "company": exp.company,
                "position": exp.position,
                "start_date": exp.startDate,
                "end_date": exp.endDate,
                "duration": exp.duration,
                "description": exp.description
            })
        
        new_edu_list = []
        for edu in request.educations:
            edu_item = {
                "school": edu.school,
                "degree": edu.degree,
                "major": edu.major,
                "start_year": edu.startYear,
                "end_year": edu.endYear,
            }
            if edu.description:
                edu_item["description"] = edu.description
            if edu.tags:
                edu_item["tags"] = edu.tags
            new_edu_list.append(edu_item)
        
        new_projects = []
        for proj in request.projects:
            new_projects.append({
                "name": proj.name,
                "time": proj.time,
                "description": proj.description
            })
        
        if existing:
            # ===== 更新模式：只补充空字段 + 合并去重 =====
            from sqlalchemy.orm.attributes import flag_modified
            updated_fields = []
            
            # 简单字段：只补充空的
            if not existing.current_title and request.currentPosition:
                existing.current_title = request.currentPosition
                updated_fields.append("current_title")
            
            if request.talentTier:
                existing.talent_tier = request.talentTier
                updated_fields.append("talent_tier")
            elif not existing.talent_tier:
                # 默认给 B
                existing.talent_tier = "B"
                updated_fields.append("talent_tier (default)")
            
            if not existing.current_company and request.currentCompany:
                existing.current_company = request.currentCompany
                updated_fields.append("current_company")
            
            if not existing.expect_location and request.location:
                existing.expect_location = request.location
                updated_fields.append("expect_location")
            
            if not existing.experience_years and request.experienceYears:
                existing.experience_years = request.experienceYears
                updated_fields.append("experience_years")
            
            if not existing.education_level and request.education:
                existing.education_level = request.education
                updated_fields.append("education_level")
            
            # work_experiences: 合并去重（按 company + position）
            if new_work_exps:
                existing_exps = []
                if existing.work_experiences:
                    existing_exps = json.loads(existing.work_experiences) if isinstance(existing.work_experiences, str) else existing.work_experiences
                    existing_exps = existing_exps or []
                
                for new_exp in new_work_exps:
                    if not new_exp.get("company"):
                        continue
                    is_dup = any(
                        e.get("company", "").strip() == new_exp["company"].strip() and
                        e.get("position", "").strip() == new_exp["position"].strip()
                        for e in existing_exps
                    )
                    if not is_dup:
                        existing_exps.append(new_exp)
                        updated_fields.append(f"work:{new_exp['company']}")
                
                existing.work_experiences = existing_exps
                flag_modified(existing, "work_experiences")
            
            # education_details: 合并去重（按 school）
            if new_edu_list:
                existing_edus = []
                if existing.education_details:
                    existing_edus = json.loads(existing.education_details) if isinstance(existing.education_details, str) else existing.education_details
                    existing_edus = existing_edus or []
                
                for new_edu in new_edu_list:
                    if not new_edu.get("school"):
                        continue
                    is_dup = any(
                        e.get("school", "").strip() == new_edu["school"].strip()
                        for e in existing_edus
                    )
                    if not is_dup:
                        existing_edus.append(new_edu)
                        updated_fields.append(f"edu:{new_edu['school']}")
                
                existing.education_details = existing_edus
                flag_modified(existing, "education_details")
            
            # project_experiences: 合并去重（按 name）
            if new_projects:
                existing_projs = []
                if existing.project_experiences:
                    existing_projs = json.loads(existing.project_experiences) if isinstance(existing.project_experiences, str) else existing.project_experiences
                    existing_projs = existing_projs or []
                
                for new_proj in new_projects:
                    if not new_proj.get("name"):
                        continue
                    is_dup = any(
                        p.get("name", "").strip() == new_proj["name"].strip()
                        for p in existing_projs
                    )
                    if not is_dup:
                        existing_projs.append(new_proj)
                        updated_fields.append(f"proj:{new_proj['name']}")
                
                existing.project_experiences = existing_projs
                flag_modified(existing, "project_experiences")
            
            # skills: 合并去重
            if request.skills:
                existing_skills = existing.skills or []
                if isinstance(existing_skills, str):
                    try:
                        existing_skills = json.loads(existing_skills)
                    except:
                        existing_skills = []
                
                for skill in request.skills:
                    if skill and skill not in existing_skills:
                        existing_skills.append(skill)
                        updated_fields.append(f"skill:{skill}")
                
                existing.skills = existing_skills
                flag_modified(existing, "skills")
            
            # source: 追加 maimai 标记
            if existing.source:
                if "脉脉" not in existing.source:
                    existing.source = existing.source + ", 脉脉"
                    updated_fields.append("source")
            else:
                existing.source = "脉脉"
                updated_fields.append("source")
            
            # notes: 追加
            notes_parts = []
            if request.maimaiUserId and (not existing.notes or f"maimai_id:{request.maimaiUserId}" not in existing.notes):
                notes_parts.append(f"maimai_id:{request.maimaiUserId}")
            if request.sourceUrl:
                notes_parts.append(f"maimai_url:{request.sourceUrl}")
            if request.statusTags:
                notes_parts.append(f"status_tags:{','.join(request.statusTags)}")
            
            if notes_parts:
                existing_notes = existing.notes or ""
                separator = "\n" if existing_notes else ""
                new_note = f"[maimai_sync {datetime.now().strftime('%Y-%m-%d')}] " + " | ".join(notes_parts)
                if new_note not in existing_notes:
                    existing.notes = existing_notes + separator + new_note
                    updated_fields.append("notes")
            
            existing.updated_at = datetime.now()
            db.commit()
            
            action = "updated" if updated_fields else "unchanged"
            print(f"🔄 脉脉同步 [{action}] ({match_type}): {existing.name} (ID: {existing.id}) 字段: {updated_fields}")
            
            return {
                "success": True,
                "action": action,
                "candidateId": existing.id,
                "matchType": match_type,
                "updatedFields": updated_fields,
                "message": f"{'已更新 ' + str(len(updated_fields)) + ' 个字段' if updated_fields else '已在库中，无新数据'}"
            }
        
        else:
            # ===== 新建模式（复用 import 逻辑）=====
            current_year = datetime.now().year
            
            # 推测最高学历
            education_level = request.education or ""
            if not education_level:
                degree_priority = {"博士": 4, "PhD": 4, "硕士": 3, "Master": 3, "本科": 2, "Bachelor": 2, "专科": 1}
                max_priority = 0
                for edu in new_edu_list:
                    degree = edu.get("degree", "")
                    priority = degree_priority.get(degree, 0)
                    if priority > max_priority:
                        max_priority = priority
                        education_level = degree
            
            # 推测工作年限
            experience_years = request.experienceYears or 0
            earliest_work_year = current_year
            if not experience_years:
                for exp in new_work_exps:
                    start_date = exp.get("start_date", "")
                    if start_date:
                        try:
                            year = int(start_date.split(".")[0])
                            if year < earliest_work_year:
                                earliest_work_year = year
                        except:
                            pass
                if earliest_work_year < current_year:
                    experience_years = current_year - earliest_work_year
            
            # 推测年龄
            age = None
            for edu in new_edu_list:
                degree = edu.get("degree", "")
                start_year = edu.get("start_year", "")
                if degree in ["本科", "Bachelor"] and start_year:
                    try:
                        age = current_year - int(start_year) + 18
                        break
                    except:
                        pass
            if not age and earliest_work_year < current_year:
                age = current_year - earliest_work_year + 22
            
            # 构建 notes
            notes_parts = []
            if request.maimaiUserId:
                notes_parts.append(f"maimai_id:{request.maimaiUserId}")
            if request.sourceUrl:
                notes_parts.append(f"source_url:{request.sourceUrl}")
            notes_parts.append(f"imported_at:{datetime.now().isoformat()}")
            
            candidate = Candidate(
                name=request.name.strip(),
                current_company=request.currentCompany,
                current_title=request.currentPosition,
                expect_location=request.location,
                work_experiences=new_work_exps if new_work_exps else None,
                education_details=new_edu_list if new_edu_list else None,
                project_experiences=new_projects if new_projects else None,
                skills=request.skills if request.skills else None,
                source="脉脉",
                notes="\n".join(notes_parts),
                education_level=education_level if education_level else None,
                experience_years=experience_years if experience_years > 0 else None,
                age=age,
                talent_tier=request.talentTier if request.talentTier else "B",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            print(f"✅ 脉脉同步 [created]: {candidate.name} (ID: {candidate.id})")
            
            # 异步：提取标签 + 创建门户
            import threading
            def _post_maimai_sync_bg(cid, cname):
                try:
                    from extract_tags import extract_tags_for_candidate_by_id
                    print(f"🏷️ 脉脉候选人 {cname} (ID={cid}) 标签提取中...")
                    tags = extract_tags_for_candidate_by_id(cid)
                    if tags:
                        print(f"🏷️ ✅ {cname} 标签提取完成")
                except Exception as e:
                    print(f"🏷️ ❌ {cname} 标签提取异常: {e}")
                
                try:
                    import hashlib, requests
                    PORTAL_BASE = "https://job-share-service-production.up.railway.app"
                    token = hashlib.sha256('ruproAI'.encode()).hexdigest()
                    resp = requests.post(f"{PORTAL_BASE}/api/portal/create", json={
                        'candidate_id': cid,
                        'candidate_name': cname,
                    }, cookies={'auth_token': token}, timeout=15)
                    if resp.status_code == 200 and resp.json().get('success'):
                        portal_code = resp.json()['portal_code']
                        print(f"🔗 ✅ {cname} 门户已创建: /p/{portal_code}")
                except Exception as e:
                    print(f"🔗 ❌ {cname} 门户创建异常: {e}")
            
            threading.Thread(target=_post_maimai_sync_bg, args=(candidate.id, candidate.name), daemon=True).start()
            
            return {
                "success": True,
                "action": "created",
                "candidateId": candidate.id,
                "message": f"新建候选人: {candidate.name}（标签提取+门户创建中...）"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 脉脉同步失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


class RecordFriendRequestPayload(BaseModel):
    linkedinUrl: str
    name: str = ""
    message: str = ""   # AI 生成的加好友消息内容

@app.post("/api/candidate/record-friend-request")
def record_friend_request(req: RecordFriendRequestPayload):
    """
    记录 LinkedIn 加好友操作（由插件"复制"按钮触发）
    按 linkedin_url 匹配候选人，更新好友状态并追加沟通记录
    """
    db = SessionLocal()
    try:
        from datetime import datetime as _dt
        from sqlalchemy import or_

        # URL 标准化
        url = req.linkedinUrl.strip().rstrip('/')
        if url.startswith('http://'):
            url = 'https://' + url[len('http://'):]

        candidate = db.query(Candidate).filter(
            or_(
                Candidate.linkedin_url == url,
                Candidate.linkedin_url == url + '/'
            )
        ).first()

        if not candidate:
            return {"success": False, "error": f"未找到候选人: {req.name or url}"}

        # 更新好友状态
        candidate.is_friend = 1
        candidate.friend_added_at = _dt.now().strftime('%Y-%m-%d %H:%M')
        candidate.friend_channel = 'LinkedIn'

        # 追加沟通记录
        logs = candidate.communication_logs or []
        logs.insert(0, {
            "time": _dt.now().strftime('%Y-%m-%d %H:%M'),
            "channel": "LinkedIn",
            "action": "sent_friend_request",
            "content": req.message[:500] if req.message else "",
            "direction": "outbound"
        })
        candidate.communication_logs = logs

        # 更新 pipeline_stage（如果还是 new 就推进到 contacted）
        if candidate.pipeline_stage in (None, 'new'):
            candidate.pipeline_stage = 'contacted'

        candidate.last_communication_at = _dt.now()

        # ========== 新系统：创建 outreach_records 记录 ==========
        try:
            from outreach_service import OutreachService, OutreachChannel, OutreachType, OutreachStatus
            outreach_record = OutreachService.create_outreach(
                candidate_id=candidate.id,
                channel=OutreachChannel.LINKEDIN,
                outreach_type=OutreachType.LINKEDIN_CONNECT,
                content=req.message or "LinkedIn 加好友请求",
                status=OutreachStatus.SENT,
                sent_at=_dt.now(),
                meta_data={"linkedin_url": url, "source": "browser_extension"}
            )

            # 更新 candidates 表的新字段
            candidate.outreach_count = OutreachService.get_candidate_outreach_count(
                candidate.id, count_only=True
            )
            candidate.last_outreach_channel = OutreachChannel.LINKEDIN
            candidate.last_outreach_date = _dt.now()

            # 同时更新 contacted_channels（兼容旧系统）
            channels = candidate.contacted_channels or {}
            if isinstance(channels, str):
                try: channels = json.loads(channels)
                except: channels = {}
            if isinstance(channels, list):
                channels = {ch: '' for ch in channels}
            channels['linkedin'] = _dt.now().strftime('%Y-%m-%d %H:%M')
            candidate.contacted_channels = channels

            print(f"✅ 已创建outreach记录: record_id={outreach_record.id}")
        except Exception as e:
            print(f"⚠️ 创建outreach记录失败（旧系统仍可用）: {e}")
        # ========== 新系统结束 ==========

        db.commit()
        print(f"🤝 已记录LinkedIn加好友: {candidate.name} (ID: {candidate.id})")
        return {
            "success": True,
            "candidateId": candidate.id,
            "candidateName": candidate.name,
            "message": f"已记录 {candidate.name} 的LinkedIn好友请求"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def _parse_contact_from_notes(notes_text: str) -> dict:
    """
    从备注文本中解析联系方式：
    - GitHub URL → github_url
    - Google Scholar URL → google_scholar_url (存入 personal_website 或 notes)
    - 邮箱 → email
    - 手机号 → phone
    - 微信号 → wechat_id
    - 其他网站 → personal_website
    """
    import re
    result = {}
    if not notes_text:
        return result
    
    text = notes_text.strip()
    
    # 1. GitHub URL
    gh_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)', text, re.IGNORECASE)
    if gh_match:
        result['github_url'] = f"https://github.com/{gh_match.group(1)}"
    
    # 2. Google Scholar URL
    scholar_match = re.search(r'(?:https?://)?scholar\.google\.com[^\s）)]*', text, re.IGNORECASE)
    if scholar_match:
        url = scholar_match.group(0)
        if not url.startswith('http'):
            url = 'https://' + url
        result['google_scholar_url'] = url
    
    # 3. 邮箱
    email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    if email_match:
        result['email'] = email_match.group(0)
    
    # 4. 手机号（中国大陆：1开头11位 | 国际：+开头含空格分隔）
    phone_match = re.search(r'\+\d{1,3}[\s-]?\d[\d\s-]{6,12}\d|1[3-9]\d{9}', text)
    if phone_match:
        result['phone'] = re.sub(r'\s+', ' ', phone_match.group(0)).strip()
    
    # 5. 微信号（常见格式：微信：xxx / WeChat: xxx / wx: xxx）
    wechat_match = re.search(r'(?:微信|wechat|wx)\s*[:：]\s*(\S+)', text, re.IGNORECASE)
    if wechat_match:
        result['wechat_id'] = wechat_match.group(1).strip()
    
    # 6. 其他个人网站（排除已匹配的 github/scholar/linkedin + 邮箱域名）
    # 收集邮箱域名用于排除
    email_domains = set()
    for em in re.finditer(r'[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})', text):
        email_domains.add(em.group(1).lower())
    
    url_pattern = re.compile(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/[^\s）)]*)?', re.IGNORECASE)
    for m in url_pattern.finditer(text):
        domain = m.group(1).lower()
        # 排除已匹配的、邮箱域名、和常见非个人网站
        if domain in email_domains:
            continue
        if any(skip in domain for skip in ['github.com', 'github.io', 'scholar.google', 'linkedin.com', 'google.com/citations', 'mailto:', 'gmail.com', 'outlook.com', 'qq.com', '163.com', 'hotmail.com']):
            # *.github.io → 当作 github_url（如果尚未有）
            if 'github.io' in domain and 'github_url' not in result:
                full_url = m.group(0)
                if not full_url.startswith('http'):
                    full_url = 'https://' + full_url
                result['github_url'] = full_url
            continue
        full_url = m.group(0)
        if not full_url.startswith('http'):
            full_url = 'https://' + full_url
        result['personal_website'] = full_url
        break  # 只取第一个
    
    return result


    return result




    return result


def _translate_profile_if_needed(req: LinkedInSyncRequest):
    """
    智能翻译中间件：如果检测到英文简历，自动生成中文摘要和Title
    """
    # 1. 检测英文含量
    check_text = (req.currentTitle or "") + (req.notes or "")
    if len(check_text) < 10: 
        return None
    
    en_count = sum(1 for c in check_text if ord(c) < 128)
    if en_count / len(check_text) < 0.5: 
        return None  # 中文内容 > 50%，无需翻译

    print(f"🌍 检测到英文简历 (EN ratio: {en_count/len(check_text):.2f})，开始自动翻译...")

    # 2. 构建 Prompt
    profile_text = f"Name: {req.name}\nTitle: {req.currentTitle}\n"
    if req.notes: profile_text += f"About: {req.notes}\n"
    
    profile_text += "\nExperience:\n"
    for exp in req.workExperiences[:5]: # 只看最近5段
        profile_text += f"- {exp.position} @ {exp.company} ({exp.duration})\n"
        if exp.description: 
            profile_text += f"  Desc: {exp.description[:300]}...\n" # 截断描述
        
    profile_text += "\nEducation:\n"
    for edu in req.educations:
        profile_text += f"- {edu.degree} in {edu.major} @ {edu.school}\n"

    # 3. 调用 LLM
    try:
        import os
        from openai import OpenAI
        import json
        
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = os.getenv("LLM_MODEL", "qwen-plus")
        
        if not api_key: return None

        client = OpenAI(api_key=api_key, base_url=base_url)
        
        prompt = f"""
You are an expert AI Headhunter Assistant.
Analyze and Summarize the following LinkedIn profile for a Chinese recruitment database.

Profile Data:
{profile_text}

Task:
1. Translate "Title" to standard Chinese (e.g. "Senior Engineer" -> "高级工程师").
2. Generate a "Chinese Summary" (ai_summary_cn) of the candidate's background, highlight skills, seniority, and key achievements.
3. Extract Tags (skills_cn).

Output valid JSON:
{{
  "translated_title": "...",
  "ai_summary_cn": "...",
  "skills_cn": ["...", "..."]
}}
"""
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        # 简单验证 JSON
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"❌ 自动翻译失败: {e}")
        return None


@app.post("/api/candidate/linkedin-sync")
def linkedin_sync(request: LinkedInSyncRequest):
    """
    LinkedIn 候选人同步（由 linkedin-contactout-scraper 插件调用）：
    1. 用 linkedin_url 精确匹配去重
    2. 不存在 → 新建
    3. 已存在 → 只补充空字段（不覆盖已有数据）
    """
    # 空数据过滤
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="姓名不能为空")
    if not request.linkedinUrl or not request.linkedinUrl.strip():
        raise HTTPException(status_code=400, detail="LinkedIn URL 不能为空")
    
    # 解析备注中的联系方式
    parsed_contacts = _parse_contact_from_notes(request.notes) if request.notes else {}
    if parsed_contacts:
        print(f"📋 从备注中解析到: {list(parsed_contacts.keys())}")
    if parsed_contacts:
        print(f"📋 从备注中解析到: {list(parsed_contacts.keys())}")
    
    if parsed_contacts:
        print(f"📋 从备注中解析到: {list(parsed_contacts.keys())}")
    
    # ===== 自动翻译/摘要 (新增) =====
    translated_data = _translate_profile_if_needed(request)
    if translated_data:
        print(f"✅ 翻译完成: {translated_data.get('translated_title')} | Summary len: {len(translated_data.get('ai_summary_cn', ''))}")
        # 覆盖/填充字段
        if translated_data.get('translated_title'):
            request.currentTitle = translated_data['translated_title']  # 更新 Request 对象中的 Title
    
    
    db = SessionLocal()
    try:
        # URL 标准化：去掉尾部斜杠，统一协议为 https，统一小写
        normalized_url = request.linkedinUrl.strip().rstrip('/').lower()
        # 统一 http → https
        if normalized_url.startswith('http://'):
            normalized_url = 'https://' + normalized_url[7:]
        # 生成所有可能变体用于匹配
        url_http = normalized_url.replace('https://', 'http://')
        
        # 用 linkedin_url 匹配（兼容 http/https + 有/无尾部斜杠 + 大小写不敏感）
        from sqlalchemy import or_, func
        existing = db.query(Candidate).filter(
            or_(
                func.lower(Candidate.linkedin_url) == normalized_url,
                func.lower(Candidate.linkedin_url) == normalized_url + '/',
                func.lower(Candidate.linkedin_url) == url_http,
                func.lower(Candidate.linkedin_url) == url_http + '/',
            )
        ).with_for_update().first()
        
        # 如果匹配上且存的是 http, 顺便修正为 https
        if existing and existing.linkedin_url and existing.linkedin_url.startswith('http://'):
            existing.linkedin_url = normalized_url
        
        # ===== 名字回退匹配：URL 未命中时按名字去重 =====
        name_matched = False
        if not existing:
            import re as _re
            raw_name = request.name.strip()
            # 提取所有名字变体：
            #   "赵黎明 (Liming Zhao)" → ["赵黎明", "Liming Zhao"]
            #   "Liming Zhao" → ["Liming Zhao"]
            #   "Liming Zhao (赵黎明)" → ["Liming Zhao", "赵黎明"]
            name_variants = set()
            # 括号内容提取
            paren_match = _re.search(r'[（(](.+?)[)）]', raw_name)
            if paren_match:
                inner = paren_match.group(1).strip()
                outer = _re.sub(r'[（(].+?[)）]', '', raw_name).strip()
                if inner: name_variants.add(inner)
                if outer: name_variants.add(outer)
            else:
                name_variants.add(raw_name)
            # 追加原始全名
            name_variants.add(raw_name)
            
            # 逐个尝试匹配
            for variant in name_variants:
                if not variant:
                    continue
                existing = db.query(Candidate).filter(
                    func.lower(Candidate.name) == variant.lower()
                ).first()
                if existing:
                    name_matched = True
                    # 回填 linkedin_url
                    if not existing.linkedin_url:
                        existing.linkedin_url = normalized_url
                    print(f"🔗 名字匹配成功: '{variant}' → ID {existing.id} ({existing.name})")
                    break
        
        # 构建工作经历 JSON
        new_work_exps = []
        for exp in request.workExperiences:
            new_work_exps.append({
                "company": exp.company,
                "position": exp.position,
                "start_date": exp.startDate,
                "end_date": exp.endDate,
                "duration": exp.duration,
                "description": exp.description
            })
        
        # 构建教育经历 JSON
        new_edu_list = []
        for edu in request.educations:
            new_edu_list.append({
                "school": edu.school,
                "degree": edu.degree,
                "major": edu.major,
                "start_year": edu.startYear,
                "end_year": edu.endYear,
                "description": edu.description
            })
        
        if existing:
            # ===== 更新模式：只补充空字段 =====
            updated_fields = []
            
            if not existing.current_title and request.currentTitle:
                existing.current_title = request.currentTitle
                updated_fields.append("current_title")
            
            # 如果有翻译后的 Summary，且原 Summary 为空，填充它
            if translated_data and translated_data.get('ai_summary_cn'):
                if not existing.ai_summary:
                    existing.ai_summary = translated_data['ai_summary_cn']
                    updated_fields.append("ai_summary (translated)")
                # 如果有翻译后的 Skills，且原 Skills 为空
                if translated_data.get('skills_cn') and not existing.skills:
                    existing.skills = json.dumps(translated_data['skills_cn'], ensure_ascii=False)
                    updated_fields.append("skills (translated)")


            

            if not existing.expect_location and request.location:
                existing.expect_location = request.location
                updated_fields.append("expect_location")
            
            # work_experiences: 合并去重（用 company + position）
            if new_work_exps:
                existing_exps = []
                if existing.work_experiences:
                    existing_exps = json.loads(existing.work_experiences) if isinstance(existing.work_experiences, str) else existing.work_experiences
                
                for new_exp in new_work_exps:
                    is_dup = any(
                        e.get("company", "").strip() == new_exp["company"].strip() and
                        e.get("position", "").strip() == new_exp["position"].strip()
                        for e in existing_exps
                    ) if new_exp["company"] else False
                    if not is_dup:
                        existing_exps.append(new_exp)
                        updated_fields.append(f"work:{new_exp['company']}")
                
                existing.work_experiences = existing_exps
            
            # education_details: 合并去重（用 school）
            if new_edu_list:
                existing_edus = []
                if existing.education_details:
                    existing_edus = json.loads(existing.education_details) if isinstance(existing.education_details, str) else existing.education_details
                
                for new_edu in new_edu_list:
                    is_dup = any(
                        e.get("school", "").strip() == new_edu["school"].strip()
                        for e in existing_edus
                    ) if new_edu["school"] else False
                    if not is_dup:
                        existing_edus.append(new_edu)
                        updated_fields.append(f"edu:{new_edu['school']}")
                
                existing.education_details = existing_edus
            
            # source: 追加 linkedin 渠道（保留完整渠道历史）
            if existing.source:
                if "linkedin" not in existing.source:
                    existing.source = existing.source + ", linkedin"
                    updated_fields.append("source")
            else:
                existing.source = "linkedin"
                updated_fields.append("source")
            
            # notes: 追加备注
            if request.notes and request.notes.strip():
                existing_notes = existing.notes or ""
                if request.notes.strip() not in existing_notes:
                    separator = "\n" if existing_notes else ""
                    existing.notes = existing_notes + separator + f"[linkedin] {request.notes.strip()}"
                    updated_fields.append("notes")
            
            # 从备注解析的联系方式：只补充空字段
            if parsed_contacts:
                if not existing.github_url and parsed_contacts.get('github_url'):
                    existing.github_url = parsed_contacts['github_url']
                    updated_fields.append("github_url")
                if not existing.email and parsed_contacts.get('email'):
                    existing.email = parsed_contacts['email']
                    updated_fields.append("email")
                if not existing.phone and parsed_contacts.get('phone'):
                    existing.phone = parsed_contacts['phone']
                    updated_fields.append("phone")
                if not existing.wechat_id and parsed_contacts.get('wechat_id'):
                    existing.wechat_id = parsed_contacts['wechat_id']
                    updated_fields.append("wechat_id")
                if not existing.personal_website and parsed_contacts.get('personal_website'):
                    existing.personal_website = parsed_contacts['personal_website']
                    updated_fields.append("personal_website")
                if not existing.personal_website and parsed_contacts.get('google_scholar_url'):
                    existing.personal_website = parsed_contacts['google_scholar_url']
                    updated_fields.append("personal_website(scholar)")
            
            existing.updated_at = datetime.now()
            
            # 强制标记 JSON 字段为已修改（SQLAlchemy 不会自动检测 JSON 的就地修改）
            from sqlalchemy.orm.attributes import flag_modified
            if new_work_exps:
                flag_modified(existing, "work_experiences")
            if new_edu_list:
                flag_modified(existing, "education_details")
            
            db.commit()
            
            action = "updated" if updated_fields else "unchanged"
            print(f"🔄 LinkedIn同步 [{action}]: {existing.name} (ID: {existing.id}) 字段: {updated_fields}")
            
            return {
                "success": True,
                "action": action,
                "candidateId": existing.id,
                "updatedFields": updated_fields,
                "message": f"已存在，{'完成合并（' + str(len(updated_fields)) + ' 个字段）' if updated_fields else '无需合并'}"
            }
        
        else:
            # ===== 新建模式 =====
            education_level = ""
            degree_priority = {"博士": 4, "PhD": 4, "硕士": 3, "Master": 3, "本科": 2, "Bachelor": 2, "专科": 1}
            max_priority = 0
            for edu in new_edu_list:
                degree = edu.get("degree", "")
                priority = degree_priority.get(degree, 0)
                if priority > max_priority:
                    max_priority = priority
                    education_level = degree
            
            # 从 title 提取 current_company（"Position at Company" 格式）
            current_company = ""
            if request.currentTitle and " at " in request.currentTitle:
                parts = request.currentTitle.split(" at ", 1)
                current_company = parts[1].strip() if len(parts) > 1 else ""
            
            candidate = Candidate(
                name=request.name.strip(),
                linkedin_url=request.linkedinUrl,
                current_title=request.currentTitle,
                current_company=current_company,
                expect_location=request.location,
                work_experiences=new_work_exps if new_work_exps else None,
                education_details=new_edu_list if new_edu_list else None,
                education_level=education_level if education_level else None,
                source="linkedin",
                notes=f"[linkedin] {request.notes.strip()}" if request.notes and request.notes.strip() else None,
                # 注入翻译后的 AI Summary 和 Skills
                ai_summary=translated_data.get('ai_summary_cn') if translated_data else None,
                skills=json.dumps(translated_data.get('skills_cn'), ensure_ascii=False) if translated_data and translated_data.get('skills_cn') else None,
                # 从备注解析的联系方式
                github_url=parsed_contacts.get('github_url'),
                email=parsed_contacts.get('email'),
                phone=parsed_contacts.get('phone'),
                wechat_id=parsed_contacts.get('wechat_id'),
                personal_website=parsed_contacts.get('personal_website') or parsed_contacts.get('google_scholar_url'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            print(f"✅ LinkedIn同步 [created]: {candidate.name} (ID: {candidate.id})")
            
            # 异步提取标签 + 创建门户
            import threading
            def _post_sync_bg(cid, cname):
                try:
                    from extract_tags import extract_tags_for_candidate_by_id
                    print(f"🏷️ LinkedIn候选人 {cname} (ID={cid}) 标签提取中...")
                    tags = extract_tags_for_candidate_by_id(cid)
                    if tags:
                        print(f"🏷️ ✅ {cname} 标签提取完成")
                except Exception as e:
                    print(f"🏷️ ❌ {cname} 标签提取异常: {e}")
                
                # 自动评级（需要标签提取完成后）
                try:
                    from batch_update_tiers import auto_tier
                    from database import SessionLocal
                    tier_db = SessionLocal()
                    cand_obj = tier_db.query(Candidate).filter(Candidate.id == cid).first()
                    if cand_obj:
                        new_tier, reason = auto_tier(cand_obj)
                        cand_obj.talent_tier = new_tier
                        cand_obj.talent_tier_reason = reason
                        tier_db.commit()
                        print(f"🏅 ✅ {cname} 自动评级: {new_tier} ({reason})")
                    tier_db.close()
                except Exception as e:
                    print(f"🏅 ❌ {cname} 自动评级异常: {e}")
                
                try:
                    import hashlib, requests
                    PORTAL_BASE = "https://job-share-service-production.up.railway.app"
                    token = hashlib.sha256('ruproAI'.encode()).hexdigest()
                    resp = requests.post(f"{PORTAL_BASE}/api/portal/create", json={
                        'candidate_id': cid,
                        'candidate_name': cname,
                    }, cookies={'auth_token': token}, timeout=15)
                    if resp.status_code == 200 and resp.json().get('success'):
                        portal_code = resp.json()['portal_code']
                        print(f"🔗 ✅ {cname} 门户已创建: /p/{portal_code}")
                except Exception as e:
                    print(f"🔗 ❌ {cname} 门户创建异常: {e}")
            
            threading.Thread(target=_post_sync_bg, args=(candidate.id, candidate.name), daemon=True).start()
            
            return {
                "success": True,
                "action": "created",
                "candidateId": candidate.id,
                "message": f"新建候选人: {candidate.name}（标签提取+门户创建中...）"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ LinkedIn同步失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ===== 重新评级 =====
@app.post("/api/candidate/{candidate_id}/re-tier")
def re_tier_candidate(candidate_id: int):
    """
    用 DB 现有数据重新计算候选人分级
    调用 batch_update_tiers.auto_tier()
    """
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        from batch_update_tiers import auto_tier
        old_tier = candidate.talent_tier or "未分级"
        
        # auto_tier 需要 structured_tags 和 awards_achievements 为 dict/list
        if isinstance(candidate.structured_tags, str):
            candidate.structured_tags = json.loads(candidate.structured_tags)
        if isinstance(candidate.awards_achievements, str):
            candidate.awards_achievements = json.loads(candidate.awards_achievements)
        
        new_tier, reason = auto_tier(candidate)
        
        candidate.talent_tier = new_tier
        candidate.updated_at = datetime.now()
        db.commit()
        
        print(f"🔄 重新评级: {candidate.name} (ID: {candidate.id}) {old_tier} → {new_tier} ({reason})")
        
        return {
            "success": True,
            "oldTier": old_tier,
            "newTier": new_tier,
            "reason": reason,
            "message": f"{old_tier} → {new_tier}（{reason}）"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ===== GitHub 数据刷新 =====
@app.post("/api/candidate/{candidate_id}/refresh-github")
def refresh_github_data(candidate_id: int):
    """
    从 GitHub API 刷新候选人的 followers/stars/repos 数据
    并更新 structured_tags
    """
    import requests as req
    
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        github_url = candidate.github_url
        if not github_url:
            raise HTTPException(status_code=400, detail="该候选人没有 GitHub URL")
        
        # 从 URL 提取 username
        username = github_url.rstrip('/').split('/')[-1]
        if not username:
            raise HTTPException(status_code=400, detail=f"无法从 URL 提取 GitHub username: {github_url}")
        
        # GitHub API headers
        headers = {'Accept': 'application/vnd.github.v3+json'}
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
        
        # 1. 获取用户信息
        user_resp = req.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"GitHub API 错误: {user_resp.status_code} {user_resp.text[:200]}")
        
        user_data = user_resp.json()
        followers = user_data.get('followers', 0)
        public_repos = user_data.get('public_repos', 0)
        
        # 2. 获取仓库数据计算 total stars
        total_stars = 0
        page = 1
        while True:
            repos_resp = req.get(
                f"https://api.github.com/users/{username}/repos?per_page=100&sort=stars&page={page}",
                headers=headers, timeout=10
            )
            if repos_resp.status_code != 200:
                break
            repos = repos_resp.json()
            if not repos:
                break
            for repo in repos:
                total_stars += repo.get('stargazers_count', 0)
            if len(repos) < 100:
                break
            page += 1
        
        # 3. 更新 structured_tags
        from sqlalchemy.orm.attributes import flag_modified
        tags = candidate.structured_tags or {}
        if isinstance(tags, str):
            tags = json.loads(tags)
        
        old_followers = tags.get('github_followers', 0)
        old_stars = tags.get('github_total_stars', 0)
        
        tags['github_username'] = username
        tags['github_followers'] = followers
        tags['github_repos'] = public_repos
        tags['github_total_stars'] = total_stars
        tags['github_refreshed_at'] = datetime.now().isoformat()
        
        candidate.structured_tags = tags
        flag_modified(candidate, "structured_tags")
        candidate.updated_at = datetime.now()
        db.commit()
        
        print(f"🐙 GitHub刷新: {candidate.name} | followers: {old_followers}→{followers} | stars: {old_stars}→{total_stars}")
        
        return {
            "success": True,
            "username": username,
            "followers": followers,
            "publicRepos": public_repos,
            "totalStars": total_stars,
            "message": f"GitHub 数据已更新: ⭐{total_stars} 👥{followers} 📦{public_repos}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ===== Semantic Scholar 搜索作者 =====
@app.get("/api/candidate/{candidate_id}/search-scholar")
def search_scholar(candidate_id: int, query: str = None):
    """
    搜索 Semantic Scholar 作者列表（用于用户确认正确的人）
    """
    import requests as req
    
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        search_name = query or candidate.name
        if not search_name:
            raise HTTPException(status_code=400, detail="搜索名称不能为空")
        
        # Semantic Scholar Author Search API (免费, 无需 key)
        resp = req.get(
            "https://api.semanticscholar.org/graph/v1/author/search",
            params={
                "query": search_name,
                "fields": "name,paperCount,citationCount,hIndex,affiliations",
                "limit": 10
            },
            timeout=15
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Semantic Scholar API 错误: {resp.status_code}")
        
        result = resp.json()
        authors = []
        for a in result.get('data', []):
            authors.append({
                "authorId": a.get('authorId'),
                "name": a.get('name'),
                "paperCount": a.get('paperCount', 0),
                "citationCount": a.get('citationCount', 0),
                "hIndex": a.get('hIndex', 0),
                "affiliations": a.get('affiliations', []),
            })
        
        return {"success": True, "authors": authors, "query": search_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ===== Semantic Scholar 获取学术数据 =====
class FetchScholarRequest(BaseModel):
    authorId: str

@app.post("/api/candidate/{candidate_id}/fetch-scholar")
def fetch_scholar_data(candidate_id: int, request: FetchScholarRequest):
    """
    用 Semantic Scholar authorId 获取论文数据并存入 awards_achievements
    """
    import requests as req
    
    # 顶会列表
    TOP_VENUES = {
        'ICLR', 'NeurIPS', 'NIPS', 'ICML', 'ACL', 'EMNLP', 'NAACL',
        'CVPR', 'ICCV', 'ECCV', 'AAAI', 'IJCAI', 'SIGIR', 'KDD',
        'WWW', 'ICSE', 'OSDI', 'SOSP', 'SIGMOD', 'VLDB',
    }
    
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        # 获取作者详情和论文列表
        resp = req.get(
            f"https://api.semanticscholar.org/graph/v1/author/{request.authorId}",
            params={
                "fields": "name,paperCount,citationCount,hIndex,papers.title,papers.venue,papers.year,papers.citationCount"
            },
            timeout=30
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Semantic Scholar API 错误: {resp.status_code}")
        
        data = resp.json()
        h_index = data.get('hIndex', 0)
        citation_count = data.get('citationCount', 0)
        paper_count = data.get('paperCount', 0)
        
        # 统计顶会论文
        venue_counts = {}
        papers = data.get('papers', [])
        for paper in papers:
            venue = paper.get('venue', '') or ''
            for top_venue in TOP_VENUES:
                if top_venue.lower() in venue.lower():
                    venue_counts[top_venue] = venue_counts.get(top_venue, 0) + 1
                    break
        
        total_top_papers = sum(venue_counts.values())
        
        # 更新 awards_achievements
        from sqlalchemy.orm.attributes import flag_modified
        awards = candidate.awards_achievements or []
        if isinstance(awards, str):
            awards = json.loads(awards)
        
        # 移除旧的学术数据条目
        awards = [a for a in awards if a.get('type') not in ('publications', 'scholar_stats')]
        
        # 添加顶会论文统计
        if venue_counts:
            venue_str = ', '.join(f"{k}: {v}" for k, v in sorted(venue_counts.items(), key=lambda x: -x[1]))
            awards.append({
                'type': 'publications',
                'title': f"顶会论文: {venue_str}",
                'description': f"共 {total_top_papers} 篇顶会论文"
            })
        
        # 添加学术指标
        awards.append({
            'type': 'scholar_stats',
            'title': f"H-index: {h_index} | 引用: {citation_count:,} | 论文: {paper_count}",
            'description': f"Semantic Scholar ID: {request.authorId}"
        })
        
        candidate.awards_achievements = awards
        flag_modified(candidate, "awards_achievements")
        
        # 同步更新 structured_tags 中的数据（auto_tier 需要）
        tags = candidate.structured_tags or {}
        if isinstance(tags, str):
            tags = json.loads(tags)
        tags['scholar_h_index'] = h_index
        tags['scholar_citations'] = citation_count
        tags['scholar_papers'] = paper_count
        tags['scholar_top_venues'] = venue_counts
        tags['scholar_refreshed_at'] = datetime.now().isoformat()
        candidate.structured_tags = tags
        flag_modified(candidate, "structured_tags")
        
        candidate.updated_at = datetime.now()
        db.commit()
        
        print(f"📄 学术数据: {candidate.name} | H-index={h_index} | 顶会={total_top_papers} | 引用={citation_count}")
        
        return {
            "success": True,
            "hIndex": h_index,
            "citationCount": citation_count,
            "paperCount": paper_count,
            "topVenues": venue_counts,
            "totalTopPapers": total_top_papers,
            "message": f"学术数据已更新: H-index={h_index}, 顶会论文={total_top_papers}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/candidate/{candidate_id}")
def get_candidate(candidate_id: int):
    """
    获取候选人完整详情（供详情页使用）
    """
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        return {
            "id": candidate.id,
            "name": candidate.name,
            "talent_tier": candidate.talent_tier,
            "talent_labels": candidate.talent_labels or [],
            "age": candidate.age,
            "experience_years": candidate.experience_years,
            "education_level": candidate.education_level,
            "current_company": candidate.current_company,
            "current_title": candidate.current_title,
            "expect_location": candidate.expect_location,
            "phone": candidate.phone,
            "email": candidate.email,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
            "twitter_url": candidate.twitter_url,
            "personal_website": candidate.personal_website,
            "website_content": candidate.website_content,
            "is_friend": bool(candidate.is_friend),
            "source": candidate.source,
            "skills": candidate.skills or [],
            "work_experiences": candidate.work_experiences or [],
            "education_details": candidate.education_details or [],
            "project_experiences": candidate.project_experiences or [],
            "ai_summary": candidate.ai_summary,
            "notes": candidate.notes,
            "greeting_drafts": candidate.greeting_drafts or {},
            "structured_tags": candidate.structured_tags,
            "communication_logs": candidate.communication_logs or [],
            "pipeline_stage": candidate.pipeline_stage,
            "contacted_channels": candidate.contacted_channels or [],
            "scheduled_contact_date": candidate.scheduled_contact_date,
            "last_communication_at": candidate.last_communication_at.isoformat() if candidate.last_communication_at else None,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "awards_achievements": candidate.awards_achievements or [],
        }
    finally:
        db.close()

@app.post("/api/candidate/{candidate_id}/portal")
def get_or_create_portal(candidate_id: int):
    """获取或创建候选人VIP门户（代理到 job-share-service）"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        import hashlib, requests
        PORTAL_BASE = "https://job-share-service-production.up.railway.app"
        token = hashlib.sha256('ruproAI'.encode()).hexdigest()
        resp = requests.post(f"{PORTAL_BASE}/api/portal/create", json={
            'candidate_id': candidate_id,
            'candidate_name': candidate.name,
        }, cookies={'auth_token': token}, timeout=15)
        
        if resp.status_code == 200 and resp.json().get('success'):
            data = resp.json()
            return {
                "success": True,
                "portal_url": f"{PORTAL_BASE}/p/{data['portal_code']}",
                "portal_code": data['portal_code'],
                "is_existing": data.get('is_existing', False),
            }
        else:
            raise HTTPException(status_code=500, detail=f"门户创建失败: {resp.text[:200]}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"无法连接门户服务: {str(e)}")
    finally:
        db.close()

@app.put("/api/candidate/{candidate_id}")
def update_candidate(candidate_id: int, body: dict = Body(...)):
    """更新候选人基础信息"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        # 允许更新的字段列表
        updatable_fields = [
            'name', 'age', 'experience_years', 'education_level',
            'current_company', 'current_title', 'expect_location',
            'phone', 'email', 'linkedin_url', 'github_url', 'twitter_url',
            'personal_website', 'website_content', 'pipeline_stage', 'wechat_id',
            'scheduled_contact_date', 'talent_tier', 'talent_labels', 'skills', 'notes',
            'awards_achievements', 'project_experiences',
        ]
        
        updated = []
        for field in updatable_fields:
            if field in body:
                val = body[field]
                # 特殊处理空字符串为 None
                if isinstance(val, str) and val.strip() == '' and field not in ('notes',):
                    val = None
                setattr(candidate, field, val)
                updated.append(field)
        
        if updated:
            from datetime import datetime
            candidate.updated_at = datetime.now()
            db.commit()
        
        return {"success": True, "updated_fields": updated}
    finally:
        db.close()

@app.post("/api/candidate/{candidate_id}/match-jobs")
def match_jobs_for_candidate(candidate_id: int, body: dict = Body(default={})):
    """为候选人匹配职位"""
    top_k = body.get('top_k', 15)
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        from job_search import match_candidate_to_jobs
        results = match_candidate_to_jobs(candidate_id, top_k=top_k)
        
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "tags": candidate.structured_tags,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")
    finally:
        db.close()

@app.post("/api/candidate/{candidate_id}/extract-tags")
def extract_tags_api(candidate_id: int):
    """重新提取候选人结构化标签"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        from extract_tags import extract_tags_for_candidate_by_id
        tags = extract_tags_for_candidate_by_id(candidate_id)
        
        if tags:
            return {"success": True, "message": f"标签提取完成", "tags": tags}
        else:
            return {"success": False, "message": "标签提取失败，请检查候选人是否有简历数据"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标签提取失败: {str(e)}")
    finally:
        db.close()

# ============ 手动添加候选人 (供 React 前端调用) ============

class ManualAddRequest(BaseModel):
    """手动添加候选人请求 — 对齐 Streamlit 快速/标准录入"""
    name: str
    current_company: str
    current_title: str
    phone: str = ""
    email: str = ""
    age: Optional[int] = None
    experience_years: Optional[int] = None
    education_level: str = ""
    expect_location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    twitter_url: str = ""
    work_exp_text: str = ""   # 标准录入: 工作经历原始文本
    edu_exp_text: str = ""    # 标准录入: 教育经历原始文本
    tags: str = ""            # 快速录入: 逗号分隔标签
    notes: str = ""
    mode: str = "quick"       # "quick" | "standard"

@app.post("/api/candidate/manual-add")
def manual_add_candidate(req: ManualAddRequest):
    """
    手动添加候选人 (React前端)
    忠实复刻 Streamlit app.py L4742-5104 的快速/标准录入逻辑
    """
    if not req.name or not req.current_company or not req.current_title:
        raise HTTPException(status_code=400, detail="姓名、公司、职位为必填项")
    
    db = SessionLocal()
    try:
        work_experiences = None
        education_details = None
        
        # === 标准录入: 用 LLM 解析经历文本 (与 Streamlit L4897-4957 一致) ===
        if req.mode == "standard" and (req.work_exp_text.strip() or req.edu_exp_text.strip()):
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=os.getenv('DASHSCOPE_API_KEY'),
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                
                parse_prompt = f"""请解析以下工作经历和教育经历文本，返回JSON格式。

工作经历文本：
{req.work_exp_text if req.work_exp_text.strip() else "(无)"}

教育经历文本：
{req.edu_exp_text if req.edu_exp_text.strip() else "(无)"}

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
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                parsed = json.loads(result_text)
                work_experiences = parsed.get("work_experiences", [])
                education_details = parsed.get("education_details", [])
                print(f"🤖 AI解析成功: {len(work_experiences or [])} 段工作经历, {len(education_details or [])} 段教育经历")
                
            except Exception as e:
                print(f"⚠️ AI解析失败，保存原始文本: {e}")
                if req.work_exp_text.strip():
                    work_experiences = [{"raw_text": req.work_exp_text}]
                if req.edu_exp_text.strip():
                    education_details = [{"raw_text": req.edu_exp_text}]
        
        # 解析快速标签
        skills = None
        if req.tags:
            skills = [t.strip() for t in req.tags.split(",") if t.strip()]
        
        # 生成 AI 总结 (与 Streamlit 一致)
        ai_summary = ""
        if req.mode == "quick":
            if skills:
                ai_summary = f"**技能标签**: {', '.join(skills)}\n\n快速录入记录，待完善详细信息。"
            else:
                ai_summary = "快速录入记录，待完善详细信息。"
        else:
            summary_parts = []
            if work_experiences:
                companies = [exp.get('company', '') for exp in work_experiences if exp.get('company')]
                if companies:
                    summary_parts.append(f"**工作经历**: {', '.join(companies[:3])}")
            if education_details:
                schools = [edu.get('school', '') for edu in education_details if edu.get('school')]
                if schools:
                    summary_parts.append(f"**教育背景**: {', '.join(schools[:2])}")
            ai_summary = "\n\n".join(summary_parts) if summary_parts else "标准录入记录。"
        
        # 创建候选人 (与 Streamlit L4772-4979 一致)
        new_candidate = Candidate(
            name=req.name.strip(),
            current_company=req.current_company.strip(),
            current_title=req.current_title.strip(),
            phone=req.phone or None,
            email=req.email or None,
            age=req.age if req.age and req.age > 0 else None,
            experience_years=req.experience_years if req.experience_years and req.experience_years > 0 else None,
            education_level=req.education_level if req.education_level and req.education_level != "未知" else None,
            expect_location=req.expect_location or None,
            linkedin_url=req.linkedin_url or None,
            github_url=req.github_url or None,
            twitter_url=req.twitter_url or None,
            skills=skills,
            work_experiences=work_experiences if work_experiences else None,
            education_details=education_details if education_details else None,
            notes=req.notes or None,
            ai_summary=ai_summary,
            source_file=f'manual_{req.mode}',
            source=f'手动录入({req.mode})',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(new_candidate)
        db.commit()
        db.refresh(new_candidate)
        
        print(f"✅ 手动添加候选人成功: {new_candidate.name} (ID: {new_candidate.id}, mode={req.mode})")
        
        # 异步：提取标签 (与 Streamlit L4792-4813 一致)
        import threading
        def _post_add_bg(cid, cname):
            try:
                from extract_tags import extract_tags_for_candidate_by_id
                print(f"🏷️ 手动录入候选人 {cname} (ID={cid}) 标签提取中...")
                tags = extract_tags_for_candidate_by_id(cid)
                if tags:
                    print(f"🏷️ ✅ {cname} 标签提取完成")
                else:
                    print(f"🏷️ ⚠️ {cname} 标签提取失败")
            except Exception as e:
                print(f"🏷️ ❌ {cname} 标签提取异常: {e}")
        
        threading.Thread(target=_post_add_bg, args=(new_candidate.id, new_candidate.name), daemon=True).start()
        
        result = {
            "success": True,
            "candidateId": new_candidate.id,
            "message": f"成功添加人才: {new_candidate.name}"
        }
        
        if req.mode == "standard" and work_experiences:
            result["parsed_work_count"] = len(work_experiences)
        if req.mode == "standard" and education_details:
            result["parsed_edu_count"] = len(education_details)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 手动添加候选人失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ============ 简历解析 API (供 React 前端调用) ============

from fastapi import File, UploadFile
from typing import List

@app.post("/api/resume/parse")
async def parse_resume_upload(files: List[UploadFile] = File(...)):
    """
    上传简历文件(PDF/TXT/DOCX/图片)，AI解析返回结构化数据。
    支持多文件上传：多张图片会自动拼接。
    
    返回: { success, parsed_data, file_type, file_names }
    前端拿到 parsed_data 后展示预览，用户确认后调用 /api/resume/save 保存。
    """
    from ai_service import AIService
    import base64
    from io import BytesIO
    
    if not files:
        raise HTTPException(status_code=400, detail="没有上传文件")
    
    file_names = [f.filename for f in files]
    first_ext = files[0].filename.split('.')[-1].lower() if files[0].filename else ''
    
    # 判断文件类型
    image_exts = {'png', 'jpg', 'jpeg', 'webp'}
    doc_exts = {'pdf', 'txt', 'docx'}
    
    is_image = first_ext in image_exts
    is_doc = first_ext in doc_exts
    
    if not is_image and not is_doc:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {first_ext}")
    
    try:
        if is_image:
            # --- 图片 OCR 流程 ---
            from PIL import Image
            
            if len(files) > 1:
                # 多张图片拼接
                images = []
                for f in files:
                    img_bytes = await f.read()
                    img = Image.open(BytesIO(img_bytes))
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img)
                
                max_width = max(img.width for img in images)
                total_height = sum(img.height for img in images)
                
                combined = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                y_offset = 0
                for img in images:
                    x_offset = (max_width - img.width) // 2
                    combined.paste(img, (x_offset, y_offset))
                    y_offset += img.height
                
                # 缩放过大图片
                MAX_HEIGHT = 4000
                if total_height > MAX_HEIGHT:
                    scale = MAX_HEIGHT / total_height
                    new_width = int(max_width * scale)
                    combined = combined.resize((new_width, MAX_HEIGHT), Image.Resampling.LANCZOS)
                
                buffer = BytesIO()
                combined.save(buffer, format='JPEG', quality=90)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            else:
                # 单张图片
                img_bytes = await files[0].read()
                image_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            parsed_data = AIService.ocr_resume_image(image_base64)
            
            if not parsed_data or parsed_data.get("name") == "OCR识别失败":
                return {"success": False, "message": "OCR 识别失败，请尝试更清晰的图片", "parsed_data": parsed_data}
            
            return {
                "success": True,
                "parsed_data": parsed_data,
                "file_type": "image",
                "file_names": file_names
            }
        
        else:
            # --- 文档解析流程 (仅处理第一个文件) ---
            file = files[0]
            file_bytes = await file.read()
            resume_content = ""
            
            if first_ext == 'txt':
                resume_content = file_bytes.decode('utf-8')
            
            elif first_ext == 'pdf':
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                resume_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
            
            elif first_ext == 'docx':
                import docx
                doc = docx.Document(BytesIO(file_bytes))
                resume_content = "\n".join([p.text for p in doc.paragraphs])
            
            if not resume_content.strip():
                return {"success": False, "message": "文件内容为空，无法解析"}
            
            parsed_data = AIService.parse_resume(resume_content)
            
            if not parsed_data or parsed_data.get("name") == "Parse Error":
                return {"success": False, "message": "AI 解析失败，请检查简历格式或重试", "parsed_data": parsed_data}
            
            # 保存原始PDF文件
            saved_file_path = None
            if first_ext == 'pdf':
                try:
                    import os
                    resume_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "resumes")
                    os.makedirs(resume_dir, exist_ok=True)
                    import uuid
                    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
                    saved_file_path = os.path.join(resume_dir, unique_name)
                    with open(saved_file_path, 'wb') as f:
                        f.write(file_bytes)
                    print(f"✅ 原始PDF文件已保存: {saved_file_path}")
                except Exception as e:
                    print(f"⚠️ PDF文件保存失败: {e}")
            
            return {
                "success": True,
                "parsed_data": parsed_data,
                "file_type": first_ext,
                "file_names": file_names,
                "raw_text_preview": resume_content[:500],
                "saved_file_path": saved_file_path
            }
    
    except Exception as e:
        print(f"❌ 简历解析失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"简历解析失败: {str(e)}")


class ResumeSaveRequest(BaseModel):
    """保存已解析的简历数据"""
    parsed_data: dict
    file_type: str = ""       # "pdf" | "txt" | "docx" | "image"
    file_names: list = []
    raw_text: str = ""

@app.post("/api/resume/save")
def save_parsed_resume(req: ResumeSaveRequest):
    """
    将前端已确认的解析数据保存为候选人。
    """
    db = SessionLocal()
    try:
        pd = req.parsed_data
        
        # 确定 source
        source_map = {
            "pdf": "PDF解析",
            "txt": "文档解析", 
            "docx": "文档解析",
            "image": "图片OCR"
        }
        source = source_map.get(req.file_type, "简历解析")
        source_file = ", ".join(req.file_names[:3]) if req.file_names else ""
        
        new_candidate = Candidate(
            name=pd.get("name", "未知"),
            email=pd.get("email"),
            phone=pd.get("phone"),
            age=pd.get("age"),
            experience_years=pd.get("experience_years"),
            expect_location=pd.get("expect_location"),
            education_level=pd.get("education_level"),
            current_company=pd.get("current_company"),
            current_title=pd.get("current_title"),
            skills=pd.get("skills"),
            education_details=pd.get("education_details"),
            work_experiences=pd.get("work_experiences"),
            project_experiences=pd.get("project_experiences"),
            awards_achievements=pd.get("awards_achievements"),
            ai_summary=pd.get("summary"),
            notes=pd.get("notes"),
            raw_resume_text=req.raw_text or pd.get("raw_text", ""),
            source_file=source_file,
            source=source,
            created_at=datetime.now()
        )
        
        db.add(new_candidate)
        db.commit()
        db.refresh(new_candidate)
        
        candidate_id = new_candidate.id
        candidate_name = new_candidate.name
        
        # 异步提取标签
        import threading
        def _extract_bg():
            try:
                from extract_tags import extract_tags_for_candidate_by_id
                extract_tags_for_candidate_by_id(candidate_id)
                print(f"✅ 简历解析候选人 {candidate_name} 标签提取完成")
            except Exception as e:
                print(f"⚠️ 标签提取失败: {e}")
        
        threading.Thread(target=_extract_bg, daemon=True).start()
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "message": f"成功添加人才: {candidate_name}"
        }
    
    except Exception as e:
        db.rollback()
        print(f"❌ 保存简历解析候选人失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()




@app.get("/api/candidates")
def list_candidates(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    name: Optional[str] = None,
    company: Optional[str] = None,
    school: Optional[str] = None,
    location: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    email: Optional[str] = None,
    github_url: Optional[str] = None,
    website_url: Optional[str] = None,
    tier: Optional[str] = None,
    source: Optional[str] = None,
    has_phone: Optional[bool] = None,
    has_email: Optional[bool] = None,
    has_linkedin: Optional[bool] = None,
    has_github: Optional[bool] = None,
    has_website: Optional[bool] = None,
    is_friend: Optional[bool] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    exp_min: Optional[int] = None,
    exp_max: Optional[int] = None,
    talent_label: Optional[str] = None,
    outreach_status: Optional[str] = None,
    is_primary_source: Optional[bool] = None,
):
    """
    候选人分页列表 + 筛选 + 排序
    供 React 前端人才库管理页面使用
    """
    from sqlalchemy.orm import defer
    from sqlalchemy import func, case, or_, and_, String as SAString
    import re as _re

    db = SessionLocal()
    try:
        query = db.query(Candidate).options(
            defer(Candidate.raw_resume_text),
            defer(Candidate.ai_summary),
            defer(Candidate.project_experiences),
            defer(Candidate.structured_tags),
            defer(Candidate.communication_logs),
            defer(Candidate.awards_achievements),
        ).filter(Candidate.name != "Parse Error")

        # --- 筛选 ---
        if name:
            is_chinese_name = bool(_re.match(r'^[\u4e00-\u9fff]{2,4}$', name.strip()))
            if is_chinese_name:
                query = query.filter(Candidate.name.contains(name))
            else:
                query = query.filter(
                    Candidate.name.contains(name) | Candidate.skills.cast(SAString).contains(name)
                )

        if company:
            query = query.filter(
                Candidate.company_normalized.contains(company) |
                Candidate.current_company.contains(company) |
                Candidate.work_experiences.cast(SAString).contains(company)
            )

        if school:
            query = query.filter(
                Candidate.education_details.cast(SAString).contains(school)
            )

        if location:
            query = query.filter(Candidate.expect_location.contains(location))

        # URL搜索（精确匹配）
        if linkedin_url:
            query = query.filter(Candidate.linkedin_url.contains(linkedin_url))
        if email:
            query = query.filter(Candidate.email.contains(email))
        if github_url:
            query = query.filter(Candidate.github_url.contains(github_url))
        if website_url:
            query = query.filter(Candidate.personal_website.contains(website_url))

        if tier:
            if tier == "untiered":
                query = query.filter(or_(Candidate.talent_tier == None, Candidate.talent_tier == ''))
            else:
                query = query.filter(Candidate.talent_tier == tier)

        if source:
            source_map = {"maimai": "脉脉", "github": "github", "linkedin": "linkedin", "boss": "Boss"}
            search_term = source_map.get(source, source)
            if is_primary_source:
                # 只匹配以该渠道开头的 (忽略大小写)
                query = query.filter(Candidate.source.ilike(f"{search_term}%"))
            else:
                # 包含该渠道
                query = query.filter(Candidate.source.contains(search_term))

        if has_phone:
            query = query.filter(Candidate.phone != None, Candidate.phone != '')
        if has_email:
            query = query.filter(Candidate.email != None, Candidate.email != '')
        if has_linkedin:
            query = query.filter(Candidate.linkedin_url != None, Candidate.linkedin_url != '')
        if has_github:
            query = query.filter(Candidate.github_url != None, Candidate.github_url != '')
        if has_website:
            query = query.filter(Candidate.personal_website != None, Candidate.personal_website != '')
        if is_friend:
            query = query.filter(Candidate.is_friend == 1)

        if talent_label:
            # SQLite JSON stores Chinese as unicode escapes, so search both forms
            import json as _json
            escaped = _json.dumps(talent_label, ensure_ascii=True).strip('"')
            query = query.filter(
                or_(
                    Candidate.talent_labels.cast(SAString).contains(talent_label),
                    Candidate.talent_labels.cast(SAString).contains(escaped),
                )
            )

        if age_min is not None or age_max is not None:
            _amin = age_min or 18
            _amax = age_max or 60
            query = query.filter(or_(
                Candidate.age == None,
                (Candidate.age >= _amin) & (Candidate.age <= _amax)
            ))

        if exp_min is not None or exp_max is not None:
            _emin = exp_min or 0
            _emax = exp_max or 99
            query = query.filter(or_(
                Candidate.experience_years == None,
                (Candidate.experience_years >= _emin) & (Candidate.experience_years <= _emax)
            ))

        # --- 触达状态筛选 ---
        if outreach_status:
            if outreach_status == "not_contacted":
                from sqlalchemy import exists
                # 新生成未触达：没有任何触达记录(old field) 且 outreach_records 表中无记录
                # 子查询：检查是否有 outreach_records
                has_outreach_stmt = exists().where(OutreachRecord.candidate_id == Candidate.id)
                
                query = query.filter(
                    or_(
                        Candidate.contacted_channels == None,
                        Candidate.contacted_channels == '',
                        Candidate.contacted_channels == '{}'
                    ),
                    ~has_outreach_stmt  # 取反：不存在记录
                )
            elif outreach_status == "contacted_no_reply":
                # 已触达未回复：(有旧字段记录 OR 有 outreach_records) 且 无回复时间戳
                from sqlalchemy import exists
                has_outreach_stmt = exists().where(OutreachRecord.candidate_id == Candidate.id)
                
                query = query.filter(
                    or_(
                        and_(Candidate.contacted_channels != None, Candidate.contacted_channels != '', Candidate.contacted_channels != '{}'),
                        has_outreach_stmt
                    ),
                    Candidate.linkedin_accepted_at == None,
                    Candidate.maimai_accepted_at == None,
                    Candidate.email_replied_at == None
                )
            elif outreach_status == "replied_no_phone":
                # 已回复未交换电话：有任一回复字段非空，但 phone_exchanged_at 为空
                query = query.filter(
                    or_(
                        Candidate.linkedin_accepted_at != None,
                        Candidate.maimai_accepted_at != None,
                        Candidate.email_replied_at != None
                    ),
                    Candidate.phone_exchanged_at == None
                )
            elif outreach_status == "phone_exchanged":
                # 已交换电话：phone_exchanged_at 不为空
                query = query.filter(Candidate.phone_exchanged_at != None)

        # --- 总数 ---
        total = query.with_entities(func.count(Candidate.id)).scalar()

        # --- 排序 ---
        if sort_by == "name":
            order_col = Candidate.name.asc() if sort_order == "asc" else Candidate.name.desc()
            query = query.order_by(order_col)
        elif sort_by == "last_communication_at":
            query = query.order_by(
                case((Candidate.last_communication_at == None, 1), else_=0),
                Candidate.last_communication_at.desc()
            )
        elif sort_by == "last_outreach_date":
            # 最新触达
            query = query.order_by(
                case((Candidate.last_outreach_date == None, 1), else_=0),
                Candidate.last_outreach_date.desc()
            )
        elif sort_by == "latest_reply":
            # 最新回复 (取各个渠道回复时间的最大值)
            # SQLite 支持 MAX(col1, col2...)
            latest_reply_expr = func.max(
                Candidate.linkedin_accepted_at,
                Candidate.maimai_accepted_at,
                Candidate.email_replied_at
            )
            query = query.order_by(
                case((latest_reply_expr == None, 1), else_=0),
                latest_reply_expr.desc()
            )
        else:  # created_at (default)
            query = query.order_by(Candidate.created_at.desc())

        # --- 分页 ---
        offset = (max(1, page) - 1) * page_size
        candidates = query.offset(offset).limit(page_size).all()

        # --- 序列化 ---
        result = []
        for c in candidates:
            result.append({
                "id": c.id,
                "name": c.name,
                "talent_tier": c.talent_tier,
                "talent_labels": c.talent_labels or [],
                "age": c.age,
                "experience_years": c.experience_years,
                "education_level": c.education_level,
                "current_company": c.current_company,
                "company_normalized": c.company_normalized,
                "current_title": c.current_title,
                "phone": c.phone,
                "email": c.email,
                "linkedin_url": c.linkedin_url,
                "github_url": c.github_url,
                "personal_website": c.personal_website,
                "is_friend": bool(c.is_friend),
                "friend_added_at": c.friend_added_at,
                "linkedin_accepted_at": c.linkedin_accepted_at.isoformat() if c.linkedin_accepted_at else None,
                "maimai_accepted_at": c.maimai_accepted_at.isoformat() if c.maimai_accepted_at else None,
                "email_replied_at": c.email_replied_at.isoformat() if c.email_replied_at else None,
                "source": c.source,
                "skills": c.skills or [],
                "work_experiences": c.work_experiences or [],
                "education_details": c.education_details or [],
                "scheduled_contact_date": c.scheduled_contact_date,
                "notes": c.notes,
                "greeting_drafts": c.greeting_drafts or {},
                "pipeline_stage": c.pipeline_stage,
                "contacted_channels": c.contacted_channels or [],
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "candidates": result,
        }
    finally:
        db.close()


@app.delete("/api/candidate/{candidate_id}")
def api_delete_candidate(candidate_id: int):
    """删除候选人及其关联数据"""
    from database import MatchRecord, ResumeTask
    db = SessionLocal()
    try:
        cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not cand:
            raise HTTPException(status_code=404, detail="候选人不存在")
        name = cand.name
        # 清理关联数据（避免孤儿记录）
        del_outreach = db.query(OutreachRecord).filter(OutreachRecord.candidate_id == candidate_id).delete()
        del_match = db.query(MatchRecord).filter(MatchRecord.candidate_id == candidate_id).delete()
        del_resume = db.query(ResumeTask).filter(ResumeTask.candidate_id == candidate_id).delete()
        del_email = db.query(EmailOutreach).filter(EmailOutreach.candidate_id == candidate_id).delete()
        db.delete(cand)
        db.commit()
        print(f"🗑️ 已删除候选人 {name}(ID:{candidate_id}) 及关联数据: outreach={del_outreach}, match={del_match}, resume_task={del_resume}, email={del_email}")
        return {"ok": True, "message": f"已删除候选人: {name}"}
    finally:
        db.close()


class ScheduleUpdateRequest(BaseModel):
    scheduled_contact_date: Optional[str] = None  # "YYYY-MM-DD" or null


@app.patch("/api/candidate/{candidate_id}/schedule")
def api_update_schedule(candidate_id: int, req: ScheduleUpdateRequest):
    """更新预约沟通日期"""
    db = SessionLocal()
    try:
        cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not cand:
            raise HTTPException(status_code=404, detail="候选人不存在")
        cand.scheduled_contact_date = req.scheduled_contact_date
        db.commit()
        return {"ok": True, "scheduled_contact_date": cand.scheduled_contact_date}
    finally:
        db.close()


# ============ 职位相关 API (供脉脉发布职位使用) ============

class CreateJobRequest(BaseModel):
    title: str
    company: str
    department: Optional[str] = None
    location: Optional[str] = None
    seniority_level: Optional[str] = None
    salary_range: Optional[str] = None
    hr_contact: Optional[str] = None
    jd_link: Optional[str] = None
    exp_years: Optional[str] = None
    raw_jd_text: str
    notes: Optional[str] = None


@app.post("/api/jobs")
def create_job(req: CreateJobRequest):
    """创建新职位（含自动编号 + AI标签）"""
    import re
    db = SessionLocal()
    try:
        # 1. 生成 job_code
        def generate_job_code(company_name):
            map_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'company_prefix_map.json')
            try:
                with open(map_file, 'r', encoding='utf-8') as f:
                    prefix_map = json.load(f)
            except:
                prefix_map = {}

            prefix = None
            for key, val in prefix_map.items():
                if key.lower() in company_name.lower() or company_name.lower() in key.lower():
                    prefix = val
                    break

            if not prefix:
                english_words = re.findall(r'[A-Za-z]+', company_name.strip())
                if english_words:
                    if len(english_words) >= 3:
                        prefix = ''.join([w[0].upper() for w in english_words[:3]])
                    elif len(english_words) == 2:
                        prefix = (english_words[0][0] + english_words[1][:2]).upper()
                    else:
                        prefix = english_words[0][:3].upper()
                else:
                    try:
                        import pinyin
                        py = pinyin.get(company_name.strip(), format="strip", delimiter="")
                        prefix = ''.join([c[0].upper() for c in py.split() if c][:3])
                        if len(prefix) < 2:
                            prefix = py[:3].upper()
                    except:
                        prefix = "OTH"

                if len(prefix) < 2:
                    prefix = "OTH"

                prefix_map[company_name] = prefix
                try:
                    with open(map_file, 'w', encoding='utf-8') as f:
                        json.dump(prefix_map, f, ensure_ascii=False, indent=4)
                except:
                    pass

            from sqlalchemy import text
            max_num = 0
            for pv in [prefix.upper(), prefix.lower()]:
                result = db.execute(text(f"SELECT job_code FROM jobs WHERE job_code LIKE '{pv}%' ORDER BY job_code DESC LIMIT 1")).first()
                if result and result[0]:
                    match = re.search(r'(\d+)$', result[0])
                    if match:
                        num = int(match.group(1))
                        if num > max_num:
                            max_num = num

            return f"{prefix.upper()}{max_num + 1:03d}"

        job_code = generate_job_code(req.company) if req.company else None

        # 2. Extract experience years
        final_exp = None
        if req.exp_years:
            num_match = re.search(r'(\d+)', req.exp_years)
            if num_match:
                final_exp = int(num_match.group(1))
        if not final_exp:
            patterns = [r'(\d+)\s*年[及以]?[上以]?经[验历]', r'(\d+)[+＋]?\s*年']
            for p in patterns:
                m = re.search(p, req.raw_jd_text)
                if m:
                    final_exp = int(m.group(1))
                    break

        # 3. Save to DB
        new_job = Job(
            title=req.title, company=req.company, job_code=job_code,
            department=req.department, location=req.location or "",
            seniority_level=req.seniority_level, salary_range=req.salary_range,
            hr_contact=req.hr_contact, jd_link=req.jd_link,
            required_experience_years=final_exp,
            raw_jd_text=req.raw_jd_text, notes=req.notes,
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        # 4. Vector DB
        try:
            from ai_service import AIService
            vector_id = AIService.add_job_to_vector_db(new_job.id, req.raw_jd_text, {"title": req.title, "company": req.company})
            new_job.vector_id = vector_id
            db.commit()
        except:
            pass

        # 5. Structured tags
        tags = None
        try:
            from extract_tags import extract_tags, JD_PROMPT, TAG_SCHEMA
            tag_prompt = JD_PROMPT.format(schema=TAG_SCHEMA, title=req.title or '', company=req.company or '', description=(req.raw_jd_text or '')[:2000])
            tags = extract_tags(tag_prompt)
            if tags:
                new_job.structured_tags = json.dumps(tags, ensure_ascii=False)
                db.commit()
        except:
            pass

        return {
            "success": True,
            "job_id": new_job.id,
            "job_code": job_code,
            "tags": tags,
            "message": f"职位保存成功！编号: {job_code}"
        }
    finally:
        db.close()


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
        
        # 获取全库统计数据 (不受筛选条件影响)
        from sqlalchemy import func
        total_count = db.query(func.count(Job.id)).scalar()
        active_count = db.query(func.count(Job.id)).filter(Job.is_active == 1).scalar()
        urgent_count = db.query(func.count(Job.id)).filter(Job.urgency >= 2).scalar()

        return {
            "success": True,
            "count": len(sorted_jobs),
            "stats": {
                "total": total_count,
                "active": active_count,
                "urgent": urgent_count
            },
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

@app.put("/api/jobs/{job_id}")
def update_job(job_id: int, body: dict = Body(...)):
    """更新职位字段"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="职位不存在")

        updatable_fields = [
            'notes', 'urgency', 'is_active', 'hr_contact', 'headcount',
            'seniority_level', 'salary_range', 'location', 'department',
            'job_code', 'jd_link', 'sourcing_notes', 'project_tags',
        ]
        updated = []
        for field in updatable_fields:
            if field in body:
                val = body[field]
                if isinstance(val, str) and val == '' and field not in ('notes', 'sourcing_notes'):
                    val = None
                setattr(job, field, val)
                updated.append(field)

        if updated:
            db.commit()
        return {"success": True, "updated_fields": updated}
    finally:
        db.close()


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

    # 学术成就/论文（从 Semantic Scholar 等外部数据源获取）
    awards = profile.get('awards_achievements', profile.get('publications', ''))
    if awards:
        lines.append("- 学术成就与论文:")
        # 如果是字符串，直接添加
        if isinstance(awards, str):
            # 限制长度，避免太长
            awards_text = awards[:1500] if len(awards) > 1500 else awards
            lines.append(f"  {awards_text}")
        # 如果是列表，格式化每一条
        elif isinstance(awards, list):
            for award in awards[:5]:  # 最多显示5条
                if isinstance(award, dict):
                    title = award.get('title', '')
                    venue = award.get('venue', award.get('conference', ''))
                    year = award.get('year', '')
                    if title:
                        citation = f"{title}"
                        if venue:
                            citation += f" - {venue}"
                        if year:
                            citation += f" ({year})"
                        lines.append(f"  · {citation}")
                elif isinstance(award, str):
                    lines.append(f"  · {award[:200]}")

    # 个人网站内容（从 personal_website 爬取得内容）
    website_content = profile.get('websiteContent', profile.get('website_content', ''))
    personal_website = profile.get('personalWebsite', profile.get('personal_website', ''))

    if website_content and len(website_content.strip()) > 50:
        lines.append("- 个人网站/GitHub/博客内容:")
        # 如果有网站URL，先显示URL
        if personal_website:
            lines.append(f"  网站: {personal_website}")
        # 限制内容长度，避免太长
        content_text = website_content[:2000] if len(website_content) > 2000 else website_content
        lines.append(f"  {content_text}")
    elif personal_website:
        # 只有URL但没有内容
        lines.append(f"- 个人网站: {personal_website}")

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


# ============ LinkedIn 个性化消息生成 API ============




class LinkedInMessageRequest(_BaseModel):
    candidate_id: int
    extra_context: Optional[str] = None  # 用户粘贴的网站/论文等补充素材


def _linkedin_greeting(name: str) -> str:
    """LinkedIn 消息称呼"""
    if not name:
        return "Hi"
    name_clean = name.strip()
    # 中文名
    if re.search(r'[\u4e00-\u9fff]', name_clean.split('(')[0].split('（')[0]):
        cn_match = re.match(r'^([\u4e00-\u9fff]{2,4})', name_clean)
        if cn_match:
            cn_name = cn_match.group(1)
            return f"{cn_name}您好" if len(cn_name) == 2 else f"{cn_name[0]}先生"
        return "您好"
    else:
        first = name_clean.split()[0] if name_clean else "there"
        return f"Hi {first}"


@app.post("/api/generate-linkedin-message")
def api_generate_linkedin_message(req: LinkedInMessageRequest):
    """为单个候选人生成 LinkedIn Connection Request 消息"""
    from openai import OpenAI

    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")

        # 构建候选人上下文
        lines = [f"候选人信息："]
        lines.append(f"- 姓名: {candidate.name}")
        lines.append(f"- 候选人来源: {candidate.source or '未知'}")
        if candidate.github_url:
            lines.append(f"- GitHub: {candidate.github_url}")
        if candidate.current_company:
            lines.append(f"- 当前公司/机构: {candidate.current_company}")
        if candidate.current_title:
            lines.append(f"- 当前职位: {candidate.current_title}")
        if candidate.talent_tier:
            lines.append(f"- 人才等级: {candidate.talent_tier}")

        skills = candidate.skills
        if skills:
            if isinstance(skills, str):
                try: skills = json.loads(skills)
                except: skills = [skills]
            if isinstance(skills, list) and skills:
                lines.append(f"- 核心技能: {', '.join(skills[:8])}")

        edu = candidate.education_details
        if edu:
            if isinstance(edu, str):
                try: edu = json.loads(edu)
                except: edu = None
            if isinstance(edu, list):
                edu_parts = []
                for e in edu[:2]:
                    if isinstance(e, dict):
                        s = f"{e.get('school','')} {e.get('degree','')} {e.get('major','')}".strip()
                        if s: edu_parts.append(s)
                if edu_parts:
                    lines.append(f"- 教育: {'; '.join(edu_parts)}")

        work = candidate.work_experiences
        if work:
            if isinstance(work, str):
                try: work = json.loads(work)
                except: work = None
            if isinstance(work, list):
                lines.append("- 工作经历:")
                for w in work[:3]:
                    if isinstance(w, dict):
                        c = w.get('company', '')
                        t = w.get('title', w.get('position', ''))
                        p = w.get('time', w.get('period', ''))
                        if c: lines.append(f"  · {c} - {t} ({p})")

        if candidate.ai_summary:
            lines.append(f"- AI摘要: {candidate.ai_summary[:200]}")

        profile_text = '\n'.join(lines)
        greeting = _linkedin_greeting(candidate.name)
        is_cn = bool(re.search(r'[\u4e00-\u9fff]', candidate.name.split('(')[0].split('（')[0]))
        char_limit = "300个汉字" if is_cn else "300 characters"  # 提升到300字

        extra_block = ""
        if req.extra_context and req.extra_context.strip():
            # 提高截断限制到 6000 字符（保留更多论文/项目细节）
            extra_block = f"\n\n## 补充素材（来自候选人个人网站/论文等，请结合以下内容让消息更个性化）:\n{req.extra_context.strip()[:6000]}"

        # 如果候选人数据库中有 website_content 且 extra_context 中没有，自动添加
        if not extra_block and candidate.website_content and len(candidate.website_content.strip()) > 100:
            extra_block = f"\n\n## 补充素材（来自候选人个人网站/论文等，请结合以下内容让消息更个性化）:\n{candidate.website_content.strip()[:6000]}"

        user_content = f"""{profile_text}{extra_block}

称呼指令：消息必须以"{greeting}"开头。

重要要求：
1. **消息要详细、具体、有深度**（目标长度：200-300字）
2. 如果候选人有具体的论文、项目或研究成果，**务必在消息中明确提及2-3项重要成果**。
3. 🚫🚫 **绝对禁止幻觉 (NO HALLUCINATION)** 🚫🚫：
   - **核心红线**：只允许使用上方【候选人详细画像】或【补充素材】中确切存在的信息！
   - **绝不允许** 瞎编乱造具体的论文名字、会议名字（如 ICLR/ACL）或开源项目名字（如 WavLLM）。
   - 如果资料里没有具体的项目细节，就围绕他的**技术方向**或**公司**进行专业且真实的交流，宁可泛化，也绝对不要捏造具体的名词！
4. 展示你对候选人研究领域的理解和欣赏，说明为什么这些真实存在的工作有启发性
5. 避免使用"看到你的工作很感兴趣"这种空泛的说法，要具体到资料中的真实细节
6. 消息长度控制在{char_limit}以内，尽量接近这个限制以提供足够信息
7. **排版要求**：必须分 2-3 个短段落！不要把所有的要素都挤成一整块字！比如：称呼和破冰寒暄后换行，再说具体细节，最后目的再换行。

请生成一条个性化、专业、客观且严谨的 LinkedIn Connection Request 邀请消息。"""

        client = OpenAI(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        model = os.getenv("MODEL_NAME", "qwen-max")

        # 动态选择 Prompt（基于字段，非标签）
        system_prompt = LINKEDIN_SYSTEM_PROMPT
        tier = (candidate.talent_tier or '').strip()
        if tier in ('B', 'C', 'D', ''):
            system_prompt = LINKEDIN_CONNECT_ONLY_PROMPT

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            timeout=30
        )
        message = response.choices[0].message.content.strip()

        # 清理引号包裹
        for q_open, q_close in [('"', '"'), ('「', '」'), ('"', '"'), ("'", "'")]:
            if message.startswith(q_open) and message.endswith(q_close):
                message = message[len(q_open):-len(q_close)]
                break

        # 保存到 greeting_drafts.linkedin（独立字段，不污染 communication_logs）
        drafts = candidate.greeting_drafts or {}
        if isinstance(drafts, str):
            try: drafts = json.loads(drafts)
            except: drafts = {}
        drafts['linkedin'] = message
        candidate.greeting_drafts = drafts
        # 更新时间，确保列表刷新能看到变化
        candidate.updated_at = datetime.now()
        db.commit()

        return {
            "success": True,
            "message": message,
            "char_count": len(message),
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ LinkedIn消息生成失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"LLM调用失败: {str(e)}")
    finally:
        db.close()


# 邮件生成的 Prompt 已提取到 prompts.py


def _scrape_website_summary(url: str, max_chars: int = 4000) -> str:
    """
    抓取个人网站内容摘要。
    处理各种异常情况，返回清理后的文本或空字符串。
    """
    if not url or not url.strip():
        return ""

    url = url.strip()
    # 补全协议
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # 跳过不适合抓取的 URL
    skip_domains = ['mp.weixin.qq.com', 'zhihu.com', 'twitter.com', 'x.com',
                    'linkedin.com', 'github.com', 'scholar.google']
    from urllib.parse import urlparse
    try:
        domain = urlparse(url).netloc.lower()
        if any(skip in domain for skip in skip_domains):
            return f"[网站链接: {url}，属于社交平台，未抓取内容]"
    except:
        pass

    try:
        import requests as req_lib
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        }
        resp = req_lib.get(url, timeout=10, headers=headers, allow_redirects=True,
                          verify=False)
        resp.raise_for_status()

        content_type = resp.headers.get('Content-Type', '')
        if 'html' not in content_type.lower() and 'text' not in content_type.lower():
            return f"[网站链接: {url}，非 HTML 内容]"

        soup = BeautifulSoup(resp.text, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer', 'noscript', 'iframe',
                         'svg', 'button', 'form', 'input']):
            tag.decompose()

        main_content = (soup.find('main') or soup.find('article') or
                       soup.find(class_=re.compile(r'content|post|about|bio', re.I)) or
                       soup.find('body'))

        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
            # If main content is too short but full page is long, use full page (valid for single-page academic sites)
            full_text = soup.get_text(separator='\n', strip=True)
            if len(text) < 2000 and len(full_text) > 3000:
                text = full_text
        else:
            text = soup.get_text(separator='\n', strip=True)

        lines = [re.sub(r'\s+', ' ', line).strip() for line in text.split('\n')]
        lines = [l for l in lines if len(l) > 5]
        text = '\n'.join(lines)

        if len(text) < 30:
            return f"[网站链接: {url}，内容过少无法提取]"

        return text[:max_chars]

    except Exception as e:
        return f"[网站链接: {url}，抓取失败: {type(e).__name__}]"


class EmailDraftRequest(BaseModel):
    candidate_id: int
    website_content: Optional[str] = None


@app.post("/api/generate-email-draft")
def api_generate_email_draft(req: EmailDraftRequest):
    """为候选人生成个性化邮件草稿 (Subject + Body)"""
    from openai import OpenAI

    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        if not candidate.email:
            raise HTTPException(status_code=400, detail="候选人没有邮箱，无法生成邮件")

        # 1. 抓取网站内容
        website_text = req.website_content or ""
        if not website_text and candidate.personal_website:
            website_text = _scrape_website_summary(candidate.personal_website, max_chars=4000)

        # 2. 构建候选人上下文
        lines = ["候选人信息："]
        lines.append(f"- 姓名: {candidate.name}")
        lines.append(f"- 邮箱: {candidate.email}")
        if candidate.github_url:
            lines.append(f"- GitHub: {candidate.github_url}")
        if candidate.personal_website:
            lines.append(f"- 个人网站: {candidate.personal_website}")
        if candidate.current_company:
            lines.append(f"- 当前公司/机构: {candidate.current_company}")
        if candidate.current_title:
            lines.append(f"- 当前职位: {candidate.current_title}")
        if candidate.talent_tier:
            lines.append(f"- 人才等级: {candidate.talent_tier}")
        if candidate.experience_years:
            lines.append(f"- 工作年限: {candidate.experience_years}年")

        skills = candidate.skills
        if skills:
            if isinstance(skills, str):
                try: skills = json.loads(skills)
                except: skills = [skills]
            if isinstance(skills, list) and skills:
                lines.append(f"- 核心技能: {', '.join(skills[:10])}")

        edu = candidate.education_details
        if edu:
            if isinstance(edu, str):
                try: edu = json.loads(edu)
                except: edu = None
            if isinstance(edu, list):
                edu_parts = []
                for e in edu[:2]:
                    if isinstance(e, dict):
                        s = f"{e.get('school','')} {e.get('degree','')} {e.get('major','')}".strip()
                        if s: edu_parts.append(s)
                if edu_parts:
                    lines.append(f"- 教育: {'; '.join(edu_parts)}")

        work = candidate.work_experiences
        if work:
            if isinstance(work, str):
                try: work = json.loads(work)
                except: work = None
            if isinstance(work, list):
                lines.append("- 工作经历:")
                for w in work[:3]:
                    if isinstance(w, dict):
                        c = w.get('company', '')
                        t = w.get('title', w.get('position', ''))
                        p = w.get('time', w.get('period', ''))
                        desc = w.get('description', '')[:100]
                        if c:
                            lines.append(f"  · {c} - {t} ({p})")
                            if desc:
                                lines.append(f"    {desc}")

        if candidate.ai_summary:
            lines.append(f"- AI 评价: {candidate.ai_summary[:300]}")

        profile_text = '\n'.join(lines)

        # 3. 网站内容块
        website_block = ""
        if website_text and not website_text.startswith("[网站链接:"):
            website_block = f"\n\n## 候选人个人网站内容摘要\n以下是从 {candidate.personal_website} 抓取到的内容，请仔细阅读并在邮件中引用具体的项目/研究/博客话题：\n\n{website_text}"
        elif website_text:
            website_block = f"\n\n## 候选人网站\n{website_text}"

        # 4. 组装 user prompt
        user_content = f"""{profile_text}{website_block}

请为这位候选人生成一封个性化邮件（Subject + Body）。"""

        # 5. 调用 LLM
        client = OpenAI(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        model = os.getenv("MODEL_NAME", "qwen-max")

        # 动态选择 Prompt（V4: 基于数据可用性，4 分类）
        website = (candidate.personal_website or '').lower()
        has_scholar = 'scholar.google' in website or '.edu' in website
        if not has_scholar and candidate.structured_tags and isinstance(candidate.structured_tags, dict):
            if candidate.structured_tags.get('google_scholar'):
                has_scholar = True
        if has_scholar:
            system_prompt = EMAIL_PROMPT_ACADEMIC
        elif candidate.personal_website:
            system_prompt = EMAIL_PROMPT_HAS_WEBSITE
        elif candidate.github_url:
            system_prompt = EMAIL_PROMPT_GITHUB_ONLY
        else:
            system_prompt = EMAIL_PROMPT_EMAIL_ONLY

        # 为候选人注入 top_repos 到 user prompt
        if candidate.structured_tags and isinstance(candidate.structured_tags, dict):
            top_repos = candidate.structured_tags.get('top_repos', '')
            if top_repos:
                user_content += f"\n\n## GitHub Top Repos\n{top_repos}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            timeout=60
        )
        raw_output = response.choices[0].message.content.strip()

        # 6. 解析 Subject 和 Body
        subject = ""
        body = raw_output
        if "SUBJECT:" in raw_output and "BODY:" in raw_output:
            parts = raw_output.split("BODY:", 1)
            subject_part = parts[0]
            body = parts[1].strip() if len(parts) > 1 else ""
            if "SUBJECT:" in subject_part:
                subject = subject_part.split("SUBJECT:", 1)[1].strip()
                subject = subject.split('\n')[0].strip()

        for q_open, q_close in [('「', '」'), ('"', '"'), ('"', '"')]:
            if subject.startswith(q_open) and subject.endswith(q_close):
                subject = subject[len(q_open):-len(q_close)]
                break

        # 7. 保存到 greeting_drafts.email
        drafts = candidate.greeting_drafts or {}
        if isinstance(drafts, str):
            try: drafts = json.loads(drafts)
            except: drafts = {}
        drafts['email'] = {"subject": subject, "body": body}
        candidate.greeting_drafts = drafts
        candidate.updated_at = datetime.now()
        db.commit()

        return {
            "success": True,
            "subject": subject,
            "body": body,
            "char_count": len(body),
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "email": candidate.email,
            "website_scraped": bool(website_text and not website_text.startswith("[网站链接:")),
            "website_summary_length": len(website_text) if website_text else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Email草稿生成失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"LLM调用失败: {str(e)}")
    finally:
        db.close()


# ============================================================
# 📧 Email Outreach CRUD — 邮件生命周期管理
# ============================================================

@app.get("/api/candidate/{candidate_id}/emails")
def api_get_candidate_emails(candidate_id: int):
    """获取候选人所有邮件记录（按创建时间倒序）"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")

        emails = db.query(EmailOutreach).filter(
            EmailOutreach.candidate_id == candidate_id
        ).order_by(EmailOutreach.created_at.desc()).all()

        return {
            "success": True,
            "candidate_id": candidate_id,
            "candidate_name": candidate.name,
            "emails": [{
                "id": e.id,
                "pipeline_stage": e.pipeline_stage,
                "subject": e.subject,
                "body": e.body,
                "status": e.status,
                "to_email": e.to_email,
                "sent_at": str(e.sent_at) if e.sent_at else None,
                "created_at": str(e.created_at) if e.created_at else None,
                "updated_at": str(e.updated_at) if e.updated_at else None,
            } for e in emails]
        }
    finally:
        db.close()


class EmailGenerateRequest(BaseModel):
    pipeline_stage: Optional[str] = None
    extra_context: Optional[str] = None


@app.post("/api/candidate/{candidate_id}/emails/generate")
def api_generate_candidate_email(candidate_id: int, req: EmailGenerateRequest = EmailGenerateRequest()):
    """为候选人生成邮件草稿，保存到 email_outreach 表"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")
        if not candidate.email:
            raise HTTPException(status_code=400, detail="候选人没有邮箱地址")

        # 1. 构建候选人信息
        profile_parts = [f"姓名: {candidate.name}"]
        if candidate.current_company:
            profile_parts.append(f"当前公司: {candidate.current_company}")
        if candidate.current_title:
            profile_parts.append(f"当前职位: {candidate.current_title}")
        if candidate.experience_years:
            profile_parts.append(f"经验: {candidate.experience_years}年")
        if candidate.education_level:
            profile_parts.append(f"学历: {candidate.education_level}")
        if candidate.education_details:
            edu = candidate.education_details
            if isinstance(edu, str):
                try: edu = json.loads(edu)
                except: edu = []
            if edu:
                schools = [e.get('school', '') for e in edu if isinstance(e, dict)]
                if schools:
                    profile_parts.append(f"学校: {', '.join(schools)}")
        if candidate.skills:
            skills = candidate.skills
            if isinstance(skills, str):
                try: skills = json.loads(skills)
                except: skills = []
            if skills:
                profile_parts.append(f"技能: {', '.join(skills[:15])}")
        if candidate.github_url:
            profile_parts.append(f"GitHub: {candidate.github_url}")

        profile_text = '\n'.join(profile_parts)

        # 2. 抓取个人网站（如有）
        website_text = ""
        if candidate.personal_website:
            website_text = _scrape_website_summary(candidate.personal_website)

        website_block = ""
        if website_text and not website_text.startswith("[网站链接:"):
            website_block = f"\n\n--- 个人网站内容摘要 ---\n{website_text}"
        elif website_text:
            website_block = f"\n\n{website_text}"

        # 3. 补充素材
        extra_block = ""
        if req.extra_context:
            extra_block = f"\n\n--- 补充素材 ---\n{req.extra_context}"

        # 4. 组装 user prompt
        user_content = f"""{profile_text}{website_block}{extra_block}

请为这位候选人生成一封个性化邮件（Subject + Body）。"""

        # 5. 调用 LLM
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        model = os.getenv("MODEL_NAME", "qwen-max")

        # 动态选择 Prompt（V4: 基于数据可用性，4 分类）
        website = (candidate.personal_website or '').lower()
        has_scholar = 'scholar.google' in website or '.edu' in website
        if not has_scholar and candidate.structured_tags and isinstance(candidate.structured_tags, dict):
            if candidate.structured_tags.get('google_scholar'):
                has_scholar = True
        if has_scholar:
            system_prompt = EMAIL_PROMPT_ACADEMIC
        elif candidate.personal_website:
            system_prompt = EMAIL_PROMPT_HAS_WEBSITE
        elif candidate.github_url:
            system_prompt = EMAIL_PROMPT_GITHUB_ONLY
        else:
            system_prompt = EMAIL_PROMPT_EMAIL_ONLY

        # 为候选人注入 top_repos 到 user prompt
        if candidate.structured_tags and isinstance(candidate.structured_tags, dict):
            top_repos = candidate.structured_tags.get('top_repos', '')
            if top_repos:
                user_content += f"\n\n## GitHub Top Repos\n{top_repos}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            timeout=60
        )
        raw_output = response.choices[0].message.content.strip()

        # 6. 解析 Subject 和 Body
        subject = ""
        body = raw_output
        if "SUBJECT:" in raw_output and "BODY:" in raw_output:
            parts = raw_output.split("BODY:", 1)
            body = parts[1].strip() if len(parts) > 1 else raw_output
            subject_part = parts[0].strip()
            if "SUBJECT:" in subject_part:
                subject = subject_part.split("SUBJECT:", 1)[1].strip()
                subject = subject.split('\n')[0].strip()

        for q_open, q_close in [('「', '」'), ('"', '"'), ('"', '"')]:
            if subject.startswith(q_open) and subject.endswith(q_close):
                subject = subject[len(q_open):-len(q_close)]
                break

        # 7. 保存到 email_outreach 表
        email_record = EmailOutreach(
            candidate_id=candidate.id,
            pipeline_stage=req.pipeline_stage or candidate.pipeline_stage or 'new',
            subject=subject,
            body=body,
            status='draft',
            to_email=candidate.email,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(email_record)
        db.commit()
        db.refresh(email_record)

        return {
            "success": True,
            "email": {
                "id": email_record.id,
                "pipeline_stage": email_record.pipeline_stage,
                "subject": email_record.subject,
                "body": email_record.body,
                "status": email_record.status,
                "to_email": email_record.to_email,
                "created_at": str(email_record.created_at),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Email生成失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"邮件生成失败: {str(e)}")
    finally:
        db.close()


class EmailUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None  # draft / approved / sent / rejected


@app.put("/api/email-outreach/{email_id}")
def api_update_email_outreach(email_id: int, req: EmailUpdateRequest):
    """更新邮件状态或内容"""
    db = SessionLocal()
    try:
        record = db.query(EmailOutreach).filter(EmailOutreach.id == email_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="邮件记录不存在")

        if req.subject is not None:
            record.subject = req.subject
        if req.body is not None:
            record.body = req.body
        if req.status is not None:
            valid_statuses = ['draft', 'approved', 'sent', 'rejected']
            if req.status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"无效状态, 可选: {valid_statuses}")
            record.status = req.status
            if req.status == 'sent':
                record.sent_at = datetime.now()

        record.updated_at = datetime.now()
        db.commit()

        return {
            "success": True,
            "email": {
                "id": record.id,
                "candidate_id": record.candidate_id,
                "subject": record.subject,
                "body": record.body,
                "status": record.status,
                "sent_at": str(record.sent_at) if record.sent_at else None,
                "updated_at": str(record.updated_at),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/email-outreach/{email_id}/send")
def api_send_email_outreach(email_id: int):
    """通过 Gmail API 发送已批准的邮件"""
    db = SessionLocal()
    try:
        record = db.query(EmailOutreach).filter(EmailOutreach.id == email_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="邮件记录不存在")

        if record.status != 'approved':
            raise HTTPException(status_code=400, detail=f"只能发送已批准的邮件，当前状态: {record.status}")

        if not record.to_email:
            raise HTTPException(status_code=400, detail="收件人邮箱为空")

        # Gmail API 发送
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        credentials_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmail_token.json')
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']

        try:
            from google.auth.transport.requests import Request as GRequest
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise HTTPException(status_code=500,
                detail="缺少 Google API 依赖，请安装: pip install google-auth-oauthlib google-api-python-client")

        if not os.path.exists(credentials_file):
            raise HTTPException(status_code=500, detail="未找到 credentials.json")

        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GRequest())
                with open(token_file, 'w') as f:
                    f.write(creds.to_json())
            else:
                raise HTTPException(status_code=401,
                    detail="Gmail 需要授权，请先运行: python send_approved_emails.py --dry-run 完成首次授权")

        service = build('gmail', 'v1', credentials=creds)

        # 构建邮件
        message = MIMEMultipart('alternative')
        message['To'] = record.to_email
        message['Subject'] = record.subject

        text_part = MIMEText(record.body, 'plain', 'utf-8')
        message.attach(text_part)

        html_body = record.body.replace('\n\n', '</p><p>').replace('\n', '<br>')
        html_body = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>{html_body}</p>
</div>"""
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId='me', body={'raw': raw}
        ).execute()

        # 更新状态
        record.status = 'sent'
        record.sent_at = datetime.now()
        record.updated_at = datetime.now()
        db.commit()

        # 记录沟通日志 + 标记 email 渠道
        candidate = db.query(Candidate).filter(Candidate.id == record.candidate_id).first()
        if candidate:
            # 标记已触达
            channels = candidate.contacted_channels or {}
            if isinstance(channels, list):
                channels = {ch: '' for ch in channels}
            channels['email'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            candidate.contacted_channels = channels

            # 更新 pipeline
            if candidate.pipeline_stage in (None, '', 'new'):
                candidate.pipeline_stage = 'contacted'

            # 添加沟通记录
            logs = candidate.communication_logs or []
            if isinstance(logs, str):
                try: logs = json.loads(logs)
                except: logs = []
            logs.append({
                "channel": "email",
                "message": f"[Gmail] Subject: {record.subject}",
                "direction": "我发的",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
            })
            candidate.communication_logs = logs
            candidate.last_communication_at = datetime.now().strftime('%Y-%m-%d %H:%M')
            candidate.updated_at = datetime.now()

            # ========== 新系统：创建 outreach_records 记录 ==========
            try:
                from outreach_service import OutreachService, OutreachChannel, OutreachType, OutreachStatus
                outreach_record = OutreachService.create_outreach(
                    candidate_id=candidate.id,
                    channel=OutreachChannel.EMAIL,
                    outreach_type=OutreachType.EMAIL_INITIAL,
                    content=record.body,
                    subject=record.subject,
                    status=OutreachStatus.SENT,
                    sent_at=datetime.now(),
                    meta_data={
                        "email_outreach_id": record.id,
                        "to_email": record.to_email,
                        "gmail_message_id": result.get('id', ''),
                        "source": "gmail_api"
                    }
                )

                # 更新 candidates 表的新字段
                candidate.outreach_count = OutreachService.get_candidate_outreach_count(
                    candidate.id, count_only=True
                )
                candidate.last_outreach_channel = OutreachChannel.EMAIL
                candidate.last_outreach_date = datetime.now()

                print(f"✅ 已创建outreach记录: record_id={outreach_record.id}, email_id={record.id}")
            except Exception as e:
                print(f"⚠️ 创建outreach记录失败（旧系统仍可用）: {e}")
            # ========== 新系统结束 ==========

            db.commit()

        return {
            "success": True,
            "message_id": result.get('id', ''),
            "email_id": record.id,
            "to_email": record.to_email,
            "status": "sent",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Gmail发送失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")
    finally:
        db.close()


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


@app.post("/api/candidate/{candidate_id}/mark-contacted")
def api_mark_contacted(candidate_id: int, channel: str = Body(..., embed=True)):
    """标记候选人已在某渠道触达（toggle：再次点击取消标记）"""
    VALID_CHANNELS = {"linkedin", "maimai", "email", "wechat"}
    if channel not in VALID_CHANNELS:
        raise HTTPException(status_code=400, detail=f"无效渠道: {channel}，可选: {VALID_CHANNELS}")

    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")

        channels = candidate.contacted_channels or {}
        if isinstance(channels, str):
            try: channels = json.loads(channels)
            except: channels = {}
        # Migrate from old array format to dict
        if isinstance(channels, list):
            channels = {ch: datetime.now().strftime('%Y-%m-%d %H:%M') for ch in channels}

        is_adding = channel not in channels  # 判断是添加还是删除

        if is_adding:
            channels[channel] = datetime.now().strftime('%Y-%m-%d %H:%M')  # toggle on
        else:
            del channels[channel]  # toggle off

        candidate.contacted_channels = channels

        # ✅ 重要：告诉 SQLAlchemy JSON 字段已修改
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(candidate, "contacted_channels")

        # 自动推进 pipeline: 有渠道 → contacted，清空 → new
        if channels and candidate.pipeline_stage in (None, 'new'):
            candidate.pipeline_stage = 'contacted'
        elif not channels and candidate.pipeline_stage == 'contacted':
            candidate.pipeline_stage = 'new'

        candidate.updated_at = datetime.now()

        # ========== 新系统：创建 outreach_records 记录（toggle on 时） ==========
        if is_adding:  # ✅ 修复：只在添加时创建记录
            try:
                from outreach_service import OutreachService, OutreachChannel, OutreachType, OutreachStatus

                # 根据渠道确定触达类型
                outreach_type_map = {
                    'linkedin': OutreachType.LINKEDIN_CONNECT,
                    'maimai': OutreachType.MAIMAI_FRIEND_REQUEST,
                    'email': OutreachType.EMAIL_INITIAL,
                    'wechat': OutreachType.WECHAT_CONNECT,
                }

                current_time = datetime.now()
                outreach_record = OutreachService.create_outreach(
                    candidate_id=candidate.id,
                    channel=channel,
                    outreach_type=outreach_type_map.get(channel, 'contact'),
                    content=f"通过系统标记为{channel}已触达",
                    status=OutreachStatus.SENT,
                    # ✅ 注意：create_outreach 不接受 sent_at 参数，需要单独设置
                    meta_data={"source": "mark_contacted_api"}
                )

                # ✅ 单独设置 sent_at 字段
                outreach_record.sent_at = current_time
                db.add(outreach_record)
                db.flush()  # 确保记录被持久化

                # 更新 candidates 表的新字段
                candidate.outreach_count = OutreachService.get_candidate_outreach_count(
                    candidate.id, count_only=True
                )
                candidate.last_outreach_channel = channel
                candidate.last_outreach_date = current_time

                print(f"✅ 已创建outreach记录: record_id={outreach_record.id}, channel={channel}, candidate={candidate.name}")
            except Exception as e:
                print(f"⚠️ 创建outreach记录失败（旧系统仍可用）: {e}")
                import traceback
                traceback.print_exc()
        # ========== 新系统结束 ==========

        db.commit()

        return {
            "success": True,
            "contacted_channels": channels,
            "pipeline_stage": candidate.pipeline_stage,
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



# ============ 批处理 API (供 React 前端调用) ============

@app.get("/api/batch/stats")
def batch_stats():
    """批处理任务统计"""
    from database import ResumeTask
    db = SessionLocal()
    try:
        pending = db.query(ResumeTask).filter(ResumeTask.status == 'pending').count()
        processing = db.query(ResumeTask).filter(ResumeTask.status == 'processing').count()
        done = db.query(ResumeTask).filter(ResumeTask.status == 'done').count()
        failed = db.query(ResumeTask).filter(ResumeTask.status == 'failed').count()
        return {"pending": pending, "processing": processing, "done": done, "failed": failed}
    finally:
        db.close()


@app.get("/api/batch/tasks")
def batch_tasks(status: str = "all", limit: int = 30):
    """获取最近任务列表"""
    from database import ResumeTask
    db = SessionLocal()
    try:
        q = db.query(ResumeTask)
        if status != "all":
            q = q.filter(ResumeTask.status == status)
        tasks = q.order_by(ResumeTask.id.desc()).limit(limit).all()

        results = []
        for t in tasks:
            cand_name = None
            if t.status == 'done' and t.candidate_id:
                cand = db.query(Candidate).filter(Candidate.id == t.candidate_id).first()
                if cand:
                    cand_name = cand.name
            results.append({
                "id": t.id,
                "file_name": t.file_name,
                "status": t.status,
                "candidate_id": t.candidate_id,
                "candidate_name": cand_name,
                "error_message": t.error_message[:80] if t.error_message else None,
                "created_at": str(t.created_at) if hasattr(t, 'created_at') and t.created_at else None,
            })
        return {"tasks": results}
    finally:
        db.close()


@app.post("/api/batch/import-folder")
def batch_import_folder(folder_path: str = ""):
    """批量导入简历文件夹"""
    import shutil, uuid, glob
    from database import ResumeTask
    if not folder_path or not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="文件夹路径不存在")

    supported_ext = ['*.pdf', '*.txt', '*.jpg', '*.jpeg', '*.png', '*.webp']
    files = []
    for ext in supported_ext:
        files.extend(glob.glob(os.path.join(folder_path, ext)))

    excluded = ['论文', 'paper', 'arxiv', '1908.', '1909.', '2020.', '2021.']
    resume_files = [f for f in files if not any(kw.lower() in os.path.basename(f).lower() for kw in excluded)]

    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    db = SessionLocal()
    try:
        existing = set(t.file_name for t in db.query(ResumeTask).all() if t.file_name)
        added = 0
        skipped = 0

        for filepath in resume_files:
            filename = os.path.basename(filepath)
            if filename in existing:
                skipped += 1
                continue
            ext = os.path.splitext(filename)[1].lower().strip('.')
            unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
            dest_path = os.path.join(UPLOAD_DIR, unique_name)
            try:
                shutil.copy2(filepath, dest_path)
                task = ResumeTask(file_path=dest_path, file_name=filename, file_type=ext, status='pending')
                db.add(task)
                added += 1
            except:
                pass

        db.commit()
        return {"success": True, "added": added, "skipped": skipped, "total_files": len(resume_files)}
    finally:
        db.close()


@app.post("/api/batch/retry-failed")
def batch_retry_failed():
    """重试失败任务"""
    from database import ResumeTask
    db = SessionLocal()
    try:
        failed = db.query(ResumeTask).filter(ResumeTask.status == 'failed').all()
        count = len(failed)
        for t in failed:
            t.status = 'pending'
            t.error_message = None
            t.started_at = None
        db.commit()
        return {"success": True, "retried": count}
    finally:
        db.close()


@app.post("/api/batch/clear-done")
def batch_clear_done():
    """清理已完成任务"""
    from database import ResumeTask
    db = SessionLocal()
    try:
        count = db.query(ResumeTask).filter(ResumeTask.status == 'done').delete()
        db.commit()
        return {"success": True, "cleared": count}
    finally:
        db.close()


# ============ 数据分析 API (供 React 前端调用) ============

@app.get("/api/analytics/overview")
def analytics_overview():
    """数据分析全量数据"""
    from sqlalchemy import func
    db = SessionLocal()
    try:
        # 1) Overview metrics
        cand_count = db.query(Candidate).count()

        # 有效触达：与工作台保持一致的计算逻辑
        from sqlalchemy import or_, and_
        effective_outreach = db.query(Candidate).filter(
            or_(
                Candidate.is_friend == 1,
                and_(Candidate.phone != None, Candidate.phone != ''),
                and_(Candidate.wechat_id != None, Candidate.wechat_id != ''),
                Candidate.pipeline_stage.in_(['contacted', 'replied', 'wechat_connected', 'in_pipeline']),
                Candidate.last_communication_at != None,
                and_(
                    Candidate.communication_logs != None,
                    Candidate.communication_logs != '[]',
                    Candidate.communication_logs != 'null'
                )
            )
        ).count()

        # 紧急JD数量（urgency >= 2）
        urgent_jds_count = db.query(Job).filter(
            Job.is_active == 1,
            Job.urgency >= 2
        ).count()

        job_count = db.query(Job).count()
        try:
            from database import MatchRecord
            match_count = db.query(MatchRecord).count()
        except:
            match_count = 0

        # 2) Company distribution (top 20) — 使用标准化公司名分组
        company_stats = db.query(
            func.coalesce(Candidate.company_normalized, Candidate.current_company), func.count(Candidate.id)
        ).filter(
            Candidate.current_company != None, Candidate.current_company != ''
        ).group_by(func.coalesce(Candidate.company_normalized, Candidate.current_company)).order_by(func.count(Candidate.id).desc()).all()

        friend_company_stats = db.query(
            func.coalesce(Candidate.company_normalized, Candidate.current_company), func.count(Candidate.id)
        ).filter(
            Candidate.current_company != None, Candidate.current_company != '',
            Candidate.is_friend == 1
        ).group_by(func.coalesce(Candidate.company_normalized, Candidate.current_company)).order_by(func.count(Candidate.id).desc()).all()

        # 3) University distribution
        all_edu_candidates = db.query(Candidate).filter(Candidate.education_details != None).all()
        school_counter = {}
        hist_company_counter = {}
        for cand in all_edu_candidates:
            if cand.education_details and isinstance(cand.education_details, list):
                for edu in cand.education_details:
                    school = edu.get('school', '') or ''
                    school = school.strip()
                    if school and school[0] in '·、-':
                        school = school[1:].strip()
                    if school and len(school) >= 2:
                        school_counter[school] = school_counter.get(school, 0) + 1
            if cand.work_experiences and isinstance(cand.work_experiences, list):
                for work in cand.work_experiences:
                    company = work.get('company', '') or ''
                    company = company.strip()
                    if company and len(company) >= 2:
                        hist_company_counter[company] = hist_company_counter.get(company, 0) + 1

        # 4) Channel analysis
        from collections import defaultdict
        channel_data = db.query(
            Candidate.source, Candidate.phone, Candidate.email,
            Candidate.linkedin_url, Candidate.github_url,
            Candidate.personal_website, Candidate.is_friend,
            Candidate.pipeline_stage, Candidate.wechat_id,
            Candidate.last_communication_at, Candidate.communication_logs
        ).all()

        channel_stats = defaultdict(lambda: {
            'total': 0, 'phone': 0, 'email': 0, 'linkedin': 0, 'github': 0, 'website': 0, 'friend': 0, 'reachable': 0,
            'funnel': {'discovery': 0, 'contacted': 0, 'replied': 0, 'phone': 0, 'effective_outreach': 0}
        })
        overall_funnel = {'discovery': 0, 'contacted': 0, 'replied': 0, 'phone': 0, 'effective_outreach': 0}

        for src, phone, email, linkedin, github, website, is_friend, stage, wechat_id, last_comm_at, comm_logs in channel_data:
            # 仅取第一渠道 (例如 "github, linkedin" -> "github")
            ch = src.split(',')[0].strip() if src else '未知'
            channel_stats[ch]['total'] += 1
            if phone: channel_stats[ch]['phone'] += 1
            if email: channel_stats[ch]['email'] += 1
            if linkedin: channel_stats[ch]['linkedin'] += 1
            if github: channel_stats[ch]['github'] += 1
            if website: channel_stats[ch]['website'] += 1
            if is_friend == 1: channel_stats[ch]['friend'] += 1

            # 有效可联: 有邮箱 OR 有LinkedIn OR 有手机 OR 已加好友 (去重)
            if any([email, linkedin, phone, is_friend == 1]):
                channel_stats[ch]['reachable'] += 1

            # 触达转化漏斗 (累计)
            st = (stage or 'new').lower()
            # 1. 新发现 (Discovery) - 全部进入
            channel_stats[ch]['funnel']['discovery'] += 1
            overall_funnel['discovery'] += 1

            # 2. 已触达 (Contacted) - 除了 new 以外的所有阶段
            if st != 'new':
                channel_stats[ch]['funnel']['contacted'] += 1
                overall_funnel['contacted'] += 1

            # 3. 已回复 (Replied) - replied, wechat_connected, in_pipeline, closed
            if st in ['replied', 'wechat_connected', 'in_pipeline', 'closed']:
                channel_stats[ch]['funnel']['replied'] += 1
                overall_funnel['replied'] += 1

            # 4. 已有电话 (Phone) - 有手机号
            if phone:
                channel_stats[ch]['funnel']['phone'] += 1
                overall_funnel['phone'] += 1

            # 5. 有效触达 (Effective Outreach) - 与工作台完全一致的逻辑
            # 工作台SQL: is_friend=1 OR 有手机 OR 有微信 OR pipeline_stage在特定阶段 OR 有沟通时间 OR 有沟通记录
            is_effective = (
                is_friend == 1 or
                (phone and phone.strip() != '') or
                (wechat_id and wechat_id.strip() != '') or
                st in ['contacted', 'replied', 'wechat_connected', 'in_pipeline'] or
                last_comm_at is not None or
                (comm_logs and comm_logs.strip() not in ['[]', 'null', '', '{}'])
            )
            if is_effective:
                channel_stats[ch]['funnel']['effective_outreach'] += 1
                overall_funnel['effective_outreach'] += 1

        sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]['total'], reverse=True)

        # 5) Talent tier
        TIER_ORDER = ['S', 'A', 'B+', 'B', 'C']
        tier_data = db.query(Candidate.source, Candidate.talent_tier).all()
        overall_tier = {}
        channel_tier = {}
        for src, tier in tier_data:
            # 仅取第一渠道
            ch = src.split(',')[0].strip() if src else '未知'
            t = tier if tier and tier in TIER_ORDER else '未评级'
            overall_tier[t] = overall_tier.get(t, 0) + 1
            if ch not in channel_tier:
                channel_tier[ch] = {}
            channel_tier[ch][t] = channel_tier[ch].get(t, 0) + 1

        # 6) JD analysis
        all_jobs = db.query(Job).filter(Job.is_active == 1).all()
        job_company_counter = {}
        role_counter = {}
        tech_domain_counter = {}
        for job in all_jobs:
            company = job.company or "未知"
            job_company_counter[company] = job_company_counter.get(company, 0) + 1
            if job.structured_tags:
                try:
                    tags = json.loads(job.structured_tags) if isinstance(job.structured_tags, str) else job.structured_tags
                    role = tags.get("role_type", "其他")
                    role_counter[role] = role_counter.get(role, 0) + 1
                    for d in tags.get("tech_domain", []):
                        tech_domain_counter[d] = tech_domain_counter.get(d, 0) + 1
                except:
                    pass

        return {
            "success": True,
            "overview": {"candidates": cand_count, "effective_outreach": effective_outreach, "jobs": job_count, "urgent_jds": urgent_jds_count},
            "company_top20": [{"company": c, "count": n} for c, n in company_stats[:20]],
            "friend_company_top20": [{"company": c, "count": n} for c, n in friend_company_stats[:20]],
            "school_top20": sorted(school_counter.items(), key=lambda x: x[1], reverse=True)[:20],
            "hist_company_top20": sorted(hist_company_counter.items(), key=lambda x: x[1], reverse=True)[:20],
            "channels": [{"channel": ch, **stats} for ch, stats in sorted_channels],
            "overall_tier": overall_tier,
            "overall_funnel": overall_funnel,
            "channel_tier": {ch: tiers for ch, tiers in sorted(channel_tier.items(), key=lambda x: sum(x[1].values()), reverse=True)},
            "jd_companies": sorted(job_company_counter.items(), key=lambda x: x[1], reverse=True)[:20],
            "jd_roles": sorted(role_counter.items(), key=lambda x: x[1], reverse=True),
            "jd_tech_domains": sorted(tech_domain_counter.items(), key=lambda x: x[1], reverse=True)[:12],
        }
    finally:
        db.close()


# ============ 智能匹配 API (供 React 前端调用) ============

@app.get("/api/match/jobs-list")
def match_jobs_list(q: str = ""):
    """获取可匹配的职位列表（有标签的活跃职位）"""
    db = SessionLocal()
    try:
        query = db.query(Job).filter(
            Job.structured_tags.isnot(None),
            Job.structured_tags != 'null',
            Job.is_active == True
        )
        jobs = query.order_by(Job.id).all()

        results = []
        for j in jobs:
            label = f"{j.job_code or j.id}: {j.title} - {j.company}"
            if q and q.upper() not in label.upper():
                continue
            results.append({"id": j.id, "label": label, "job_code": j.job_code, "title": j.title, "company": j.company})

        return {"jobs": results[:100]}
    finally:
        db.close()


@app.get("/api/match/candidates-list")
def match_candidates_list(q: str = ""):
    """获取可匹配的候选人列表（有标签的）"""
    db = SessionLocal()
    try:
        query = db.query(Candidate).filter(
            Candidate.structured_tags.isnot(None),
            Candidate.structured_tags != 'null'
        ).order_by(Candidate.name)
        candidates = query.all()

        results = []
        for c in candidates:
            label = f"{c.id}: {c.name} - {c.current_title or '无职位'} @{c.current_company or ''}"
            if q and q.lower() not in label.lower():
                continue
            results.append({"id": c.id, "label": label, "name": c.name, "company": c.current_company, "title": c.current_title})

        return {"candidates": results[:200]}
    finally:
        db.close()


@app.post("/api/match/job-to-candidates")
def match_job_to_candidates(job_id: int = 0, top_k: int = 20):
    """为职位匹配候选人 (6维度加权评分)"""
    import re
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.structured_tags:
            raise HTTPException(status_code=400, detail="职位不存在或无标签")

        job_tags = json.loads(job.structured_tags) if isinstance(job.structured_tags, str) else job.structured_tags

        def clean_tag(s):
            s = s.split(": ")[-1] if ": " in s else s
            s = re.sub(r'\s*[\(（][^)）]*[\)）]', '', s)
            return s.lower().strip()

        SENIORITY_LEVELS = {"初级": 1, "初级(0-3年)": 1, "中级": 2, "中级(3-5年)": 2, "高级": 3, "高级(5-8年)": 3, "专家": 4, "专家(8年+)": 4, "管理层": 5}
        EDU_LEVELS = {"专科": 1, "大专": 1, "本科": 2, "硕士": 3, "博士": 4}
        ROLE_POOLS = {"技术": ["算法工程师", "算法专家", "算法研究员", "高级算法工程师"], "管理": ["技术管理"], "产品": ["产品经理", "AI产品专家", "AI产品经理", "运营"], "工程": ["工程开发", "运维/SRE", "数据工程师"], "销售": ["销售专家", "AI销售专家", "解决方案架构师"]}

        def get_role_pool(role):
            for pool, roles in ROLE_POOLS.items():
                if role in roles:
                    return pool
            return None

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

        candidates = db.query(Candidate).filter(
            Candidate.structured_tags.isnot(None),
            Candidate.structured_tags != 'null'
        ).all()

        results = []
        for c in candidates:
            try:
                cand_tags = json.loads(c.structured_tags) if isinstance(c.structured_tags, str) else c.structured_tags
                if not cand_tags:
                    continue

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

                match_reasons = []
                risk_flags = []

                domain_overlap = cand_domains & job_domains
                tech_score = len(domain_overlap) / max(len(job_domains), 1) * 100 if job_domains else 50
                if domain_overlap:
                    match_reasons.append(f"技术方向: {', '.join(list(domain_overlap)[:2])}")

                core_overlap = cand_core_specs & job_core_specs
                specialty_score = len(core_overlap) / max(len(job_core_specs), 1) * 100 if job_core_specs else 50
                if core_overlap:
                    match_reasons.insert(0, f"🎯 核心专长: {', '.join(list(core_overlap)[:2])}")

                skill_overlap = cand_tech_skills & job_tech_skills
                skill_score = len(skill_overlap) / max(len(job_tech_skills), 1) * 100 if job_tech_skills else 50
                if skill_overlap and not core_overlap:
                    match_reasons.append(f"技能: {', '.join(list(skill_overlap)[:2])}")

                if cand_role == job_role and cand_role:
                    role_score = 100
                    match_reasons.append(f"岗位匹配: {job_role}")
                elif cand_pool == job_pool and cand_pool:
                    role_score = 70
                elif cand_pool and job_pool:
                    role_score = 30
                    risk_flags.append(f"跨池({cand_pool}→{job_pool})")
                else:
                    role_score = 50

                if cand_level > 0 and job_level > 0:
                    level_gap = cand_level - job_level
                    if level_gap == 0:
                        seniority_score = 100
                    elif level_gap == 1:
                        seniority_score = 85
                        risk_flags.append("资历略过高(+1级)")
                    elif level_gap >= 2:
                        seniority_score = 40
                        risk_flags.append(f"资历过高(+{level_gap}级)")
                    elif level_gap == -1:
                        seniority_score = 85
                        risk_flags.append("💡资历略不足(-1级)")
                    elif level_gap == -2:
                        seniority_score = 40
                        risk_flags.append(f"⚠️资历不足({level_gap}级)")
                    else:
                        seniority_score = 20
                        risk_flags.append(f"⛔资历不足({level_gap}级)")
                else:
                    seniority_score = 50

                if cand_edu_level > 0 and job_edu_level > 0:
                    edu_gap = cand_edu_level - job_edu_level
                    edu_score = 100 if edu_gap >= 0 else max(50 + edu_gap * 20, 0)
                else:
                    edu_score = 50

                total = tech_score * 0.25 + specialty_score * 0.30 + skill_score * 0.15 + role_score * 0.15 + seniority_score * 0.10 + edu_score * 0.05

                has_severe = any(f for f in risk_flags if "⚠️" in f or "⛔" in f or "过高" in f or "跨池" in f)
                has_minor = any("资历略过高" in f for f in risk_flags)
                if has_severe:
                    total = min(total, 85)
                elif has_minor:
                    total = min(total, 92)

                if total >= 90 and not has_severe and not has_minor:
                    match_tier = "强匹配"
                elif total >= 75:
                    match_tier = "可转型"
                else:
                    match_tier = "泛化拓展"

                results.append({
                    "id": c.id, "name": c.name, "company": c.current_company or "", "title": c.current_title or "",
                    "score": round(total, 1), "reasons": match_reasons, "risk_flags": risk_flags,
                    "match_tier": match_tier, "is_friend": bool(c.is_friend),
                    "tech": round(tech_score, 1), "role": round(role_score, 1), "stack": round(skill_score, 1),
                })
            except:
                pass

        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "success": True,
            "job": {"id": job.id, "title": job.title, "company": job.company, "tags": job_tags},
            "total_candidates": len(candidates),
            "results": results[:top_k]
        }
    finally:
        db.close()


@app.post("/api/match/candidate-to-jobs")
def match_candidate_to_jobs_api(candidate_id: int = 0, top_k: int = 20):
    """为候选人匹配职位"""
    try:
        from job_search import match_candidate_to_jobs
        results = match_candidate_to_jobs(candidate_id, top_k=top_k)
        
        db = SessionLocal()
        try:
            cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            cand_tags = json.loads(cand.structured_tags) if cand and cand.structured_tags else {}
            return {
                "success": True,
                "candidate": {"id": candidate_id, "name": cand.name if cand else "", "tags": cand_tags},
                "results": results
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match/search-jobs")
def match_search_jobs(query: str = "", top_k: int = 20):
    """AI 语义搜索职位"""
    try:
        from job_search import search_jobs
        results = search_jobs(query, top_k=top_k)
        return {"success": True, "results": results or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match/search-candidates")
def match_search_candidates(query: str = "", top_k: int = 20):
    """AI 语义搜索人才"""
    try:
        from job_search import search_candidates
        results = search_candidates(query, top_k=top_k)
        return {"success": True, "results": results or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 沟通跟进 API (供 React 前端调用) ============

@app.get("/api/comm/scheduled-followups")
def comm_scheduled_followups():
    """获取所有预约跟进候选人，按时间分组"""
    db = SessionLocal()
    try:
        from datetime import date as _date_type
        today = _date_type.today()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)
        next_week_end = today + timedelta(days=14)
        quarter_end = today + timedelta(days=90)

        candidates = db.query(Candidate).filter(
            Candidate.scheduled_contact_date.isnot(None),
            Candidate.scheduled_contact_date != ""
        ).all()

        groups = {
            "today": [], "tomorrow": [], "week": [],
            "next_week": [], "quarter": [], "overdue": [], "completed": []
        }

        for c in candidates:
            try:
                sched_date = datetime.strptime(c.scheduled_contact_date, "%Y-%m-%d").date()
            except:
                continue

            # Check if completed
            is_completed = False
            if c.last_communication_at:
                last_comm_date = c.last_communication_at.date() if hasattr(c.last_communication_at, 'date') else c.last_communication_at
                if last_comm_date >= sched_date:
                    is_completed = True

            logs = c.communication_logs or []
            if isinstance(logs, str):
                try: logs = json.loads(logs)
                except: logs = []

            item = {
                "id": c.id, "name": c.name,
                "company": c.current_company or "", "title": c.current_title or "",
                "pipeline_stage": c.pipeline_stage,
                "stage_label": STAGE_LABELS.get(c.pipeline_stage, c.pipeline_stage or ""),
                "scheduled_date": c.scheduled_contact_date,
                "wechat_id": c.wechat_id, "phone": c.phone,
                "last_comm_at": c.last_communication_at.strftime("%m/%d %H:%M") if c.last_communication_at else None,
                "recent_logs": [
                    {"time": l.get("time", "")[:10], "content": (l.get("content", "")[:40])}
                    for l in sorted(logs, key=lambda x: x.get("time", ""), reverse=True)[:2]
                    if isinstance(l, dict)
                ],
            }

            if is_completed:
                if sched_date >= today - timedelta(days=7):
                    groups["completed"].append(item)
            elif sched_date < today:
                days_overdue = (today - sched_date).days
                item["days_overdue"] = days_overdue
                groups["overdue"].append(item)
            elif sched_date == today:
                groups["today"].append(item)
            elif sched_date == tomorrow:
                groups["tomorrow"].append(item)
            elif sched_date <= week_end:
                groups["week"].append(item)
            elif sched_date <= next_week_end:
                groups["next_week"].append(item)
            elif sched_date <= quarter_end:
                groups["quarter"].append(item)

        return {"success": True, "groups": groups}
    finally:
        db.close()


class CommMarkDoneRequest(BaseModel):
    candidate_id: int
    next_date: Optional[str] = None  # "YYYY-MM-DD" or null


@app.post("/api/comm/mark-done")
def comm_mark_done(req: CommMarkDoneRequest):
    """标记跟进完成，可选预约下次"""
    db = SessionLocal()
    try:
        cand = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
        if not cand:
            raise HTTPException(status_code=404, detail="候选人不存在")

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M")

        note = "已完成跟进"
        if req.next_date:
            note += f"，预约{req.next_date}继续"
            cand.scheduled_contact_date = req.next_date
        # Don't clear scheduled_contact_date if no next_date — it stays for "completed" tracking

        logs = cand.communication_logs or []
        if isinstance(logs, str):
            try: logs = json.loads(logs)
            except: logs = []
        logs.insert(0, {"time": now_str, "content": note, "direction": "system"})
        cand.communication_logs = logs
        cand.last_communication_at = now
        cand.updated_at = now
        db.commit()

        return {"success": True, "message": f"已标记 {cand.name} 完成"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ============ 每日工作台 API (供 React 前端调用) ============

@app.get("/api/dashboard/context")
def dashboard_context():
    """获取每日工作台全部数据（缓存1分钟）"""
    try:
        from daily_planner import collect_daily_context
        context = collect_daily_context()
        return {"success": True, "data": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据采集失败: {str(e)}")


@app.post("/api/dashboard/ai-plan")
def dashboard_ai_plan():
    """调用 LLM 生成今日行动计划"""
    try:
        from daily_planner import collect_daily_context, generate_plan_with_llm, save_daily_report
        context = collect_daily_context()
        plan = generate_plan_with_llm(context)
        if plan:
            save_daily_report(context, plan)
            return {"success": True, "plan": plan}
        else:
            return {"success": False, "message": "AI分析失败，请稍后重试"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析失败: {str(e)}")


@app.get("/api/dashboard/reports")
def dashboard_reports():
    """获取历史日报列表"""
    import glob as _glob
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    if not os.path.isdir(reports_dir):
        return {"reports": []}

    report_files = sorted(_glob.glob(os.path.join(reports_dir, "daily_plan_*.md")), reverse=True)
    reports = []
    for rf in report_files[:10]:
        fname = os.path.basename(rf)
        date_str = fname.replace("daily_plan_", "").replace(".md", "")
        with open(rf, "r", encoding="utf-8") as f:
            content = f.read()
        reports.append({
            "date": date_str,
            "preview": content[:500] + ("..." if len(content) > 500 else ""),
            "full_content": content,
        })
    return {"reports": reports}


@app.get("/api/dashboard/outreach-analytics")
def dashboard_outreach_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取触达效果分析数据，支持时间范围筛选

    Args:
        start_date: 开始日期 (YYYY-MM-DD)，默认为本周一
        end_date: 结束日期 (YYYY-MM-DD)，默认为今天
    """
    try:
        from daily_planner import collect_outreach_analytics

        # 调用带参数的函数
        analytics = collect_outreach_analytics(start_date=start_date, end_date=end_date)
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据采集失败: {str(e)}")


@app.get("/api/dashboard/sourcing-targets")
def get_sourcing_targets():
    """获取 Sourcing 目标配置（旧版，用于排期表）"""
    try:
        from daily_planner import SOURCING_TARGETS
        return {"success": True, "data": {"targets": SOURCING_TARGETS}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取目标失败: {str(e)}")


@app.get("/api/dashboard/monthly-sourcing-targets")
def get_monthly_sourcing_targets():
    """获取月度 Sourcing 目标配置"""
    try:
        from daily_planner import MONTHLY_SOURCING_TARGETS
        return {"success": True, "data": {"targets": MONTHLY_SOURCING_TARGETS}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取月度目标失败: {str(e)}")


class MonthlySourcingTargetsUpdateRequest(BaseModel):
    """更新月度 Sourcing 目标请求"""
    maimai: Optional[int] = None
    linkedin: Optional[int] = None
    github: Optional[int] = None


@app.post("/api/dashboard/monthly-sourcing-targets")
def update_monthly_sourcing_targets(request: MonthlySourcingTargetsUpdateRequest):
    """更新月度 Sourcing 目标配置"""
    try:
        # 读取 daily_planner.py 文件
        import os
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        planner_file = os.path.join(BASE_DIR, 'daily_planner.py')

        with open(planner_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 构建新的 MONTHLY_SOURCING_TARGETS 字典
        new_targets = {}
        target_keys = ['maimai', 'linkedin', 'github']

        # 从现有代码中读取当前值，只更新提供的字段
        import re
        pattern = r"MONTHLY_SOURCING_TARGETS\s*=\s*\{([^}]+)\}"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            targets_block = match.group(1)
            # 解析现有值
            for key in target_keys:
                value_pattern = rf"'{key}':\s*(\d+)"
                value_match = re.search(value_pattern, targets_block)
                if value_match:
                    new_targets[key] = int(value_match.group(1))

        # 更新用户提供的字段
        update_data = request.dict(exclude_unset=True)
        new_targets.update(update_data)

        # 生成新的 MONTHLY_SOURCING_TARGETS 代码块
        new_targets_lines = ["MONTHLY_SOURCING_TARGETS = {"]
        comments = {
            'maimai': '# 脉脉（打招呼+加友）',
            'linkedin': '# LinkedIn（导入+Connection Request）',
            'github': '# GitHub 导入',
        }
        for key, value in new_targets.items():
            new_targets_lines.append(f"    '{key}': {value},           # {comments.get(key, '')}")
        new_targets_lines.append("}")

        new_targets_code = '\n'.join(new_targets_lines)

        # 替换文件中的 MONTHLY_SOURCING_TARGETS
        content = re.sub(
            pattern,
            new_targets_code,
            content,
            flags=re.DOTALL
        )

        # 写回文件
        with open(planner_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return {"success": True, "data": {"targets": new_targets}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新月度目标失败: {str(e)}")


class SourcingTargetsUpdateRequest(BaseModel):
    """更新 Sourcing 目标请求（旧版，用于排期表）"""
    maimai_greeting: Optional[int] = None
    maimai_friend: Optional[int] = None
    linkedin_import: Optional[int] = None
    linkedin_request: Optional[int] = None
    github: Optional[int] = None
    email: Optional[int] = None
    replies: Optional[int] = None
    referrals: Optional[int] = None


@app.post("/api/dashboard/sourcing-targets")
def update_sourcing_targets(request: SourcingTargetsUpdateRequest):
    """更新 Sourcing 目标配置（旧版，用于排期表）"""
    try:
        # 读取 daily_planner.py 文件
        import os
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        planner_file = os.path.join(BASE_DIR, 'daily_planner.py')

        with open(planner_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 构建新的 SOURCING_TARGETS 字典
        new_targets = {}
        target_mappings = {
            'maimai_greeting': 'maimai_greeting',
            'maimai_friend': 'maimai_friend',
            'linkedin_import': 'linkedin_import',
            'linkedin_request': 'linkedin_request',
            'github': 'github',
            'email': 'email',
            'replies': 'replies',
            'referrals': 'referrals',
        }

        # 从现有代码中读取当前值，只更新提供的字段
        import re
        pattern = r"SOURCING_TARGETS\s*=\s*\{([^}]+)\}"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            targets_block = match.group(1)
            # 解析现有值
            for key in target_mappings.keys():
                value_pattern = rf"'{key}':\s*(\d+)"
                value_match = re.search(value_pattern, targets_block)
                if value_match:
                    new_targets[key] = int(value_match.group(1))

        # 更新用户提供的字段
        update_data = request.dict(exclude_unset=True)
        new_targets.update(update_data)

        # 生成新的 SOURCING_TARGETS 代码块
        new_targets_lines = ["SOURCING_TARGETS = {"]
        for key, value in new_targets.items():
            comments = {
                'maimai_greeting': '# 脉脉打招呼总目标 (精准)',
                'maimai_friend': '# 脉脉加好友总目标 (广撒网)',
                'linkedin_import': '# LinkedIn 导入总目标',
                'linkedin_request': '# LinkedIn Connection Request 总目标',
                'github': '# GitHub 导入总目标 (每周~1000)',
                'email': '# Email 发送总目标',
                'replies': '# 全渠道回复总目标',
                'referrals': '# 推荐提交总目标',
            }
            new_targets_lines.append(f"    '{key}': {value},     {comments.get(key, '')}")
        new_targets_lines.append("}")

        new_targets_code = '\n'.join(new_targets_lines)

        # 替换文件中的 SOURCING_TARGETS
        content = re.sub(
            pattern,
            new_targets_code,
            content,
            flags=re.DOTALL
        )

        # 写回文件
        with open(planner_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return {"success": True, "data": {"targets": new_targets}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新目标失败: {str(e)}")


# ============ 触达记录 API (Phase 2.3 新增) ============

class OutreachCreateRequest(BaseModel):
    """创建触达记录请求"""
    candidate_id: int
    channel: str  # 'linkedin', 'maimai', 'email', 'wechat', 'phone'
    outreach_type: str  # 具体类型 (connect_request, message, initial_email, etc.)
    status: str = 'sent'  # 状态，默认为已发送
    content: str
    subject: Optional[str] = None  # 仅Email
    related_job_id: Optional[int] = None
    prompt_name: Optional[str] = None
    meta_data: Optional[dict] = None
    ab_test_group: Optional[str] = None  # 'A', 'B', 'control'
    ab_test_name: Optional[str] = None


class OutreachStatusUpdateRequest(BaseModel):
    """更新触达状态请求"""
    status: str  # 'sent', 'accepted', 'replied', 'rejected', etc.
    responded_at: Optional[str] = None  # ISO format datetime
    accepted_at: Optional[str] = None  # ISO format datetime
    response_content: Optional[str] = None
    response_sentiment: Optional[str] = None  # 'positive', 'neutral', 'negative'


class MarkRepliedRequest(BaseModel):
    """标记候选人回复请求"""
    channel: str  # 'linkedin', 'maimai', 'email', 'phone'
    content: Optional[str] = None  # 回复内容描述
    responded_at: Optional[str] = None  # ISO format datetime, 默认当前时间


@app.post("/api/outreach")
def create_outreach(req: OutreachCreateRequest):
    """
    创建触达记录（完整双写：outreach_records + candidates表字段）

    Args:
        req: 触达记录创建请求

    Returns:
        创建的记录信息
    """
    db = SessionLocal()
    try:
        from outreach_service import OutreachService, OutreachStatus

        # 1. 创建 outreach_records 记录
        record = OutreachService.create_outreach(
            candidate_id=req.candidate_id,
            channel=req.channel,
            outreach_type=req.outreach_type,
            content=req.content,
            status=req.status,
            subject=req.subject,
            related_job_id=req.related_job_id,
            prompt_name=req.prompt_name,
            meta_data=req.meta_data,
            ab_test_group=req.ab_test_group,
            ab_test_name=req.ab_test_name,
        )

        # 2. 更新 candidates 表的字段（双写逻辑）
        candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")

        # 更新 contacted_channels（兼容旧系统）
        channels = candidate.contacted_channels or {}
        if isinstance(channels, str):
            try: channels = json.loads(channels)
            except: channels = {}
        if isinstance(channels, list):
            channels = {ch: '' for ch in channels}

        # 如果是已发送状态，才更新 contacted_channels
        if req.status == OutreachStatus.SENT:
            channels[req.channel] = datetime.now().strftime('%Y-%m-%d %H:%M')
            candidate.contacted_channels = channels

            # 更新 last_outreach_channel 和 last_outreach_date
            candidate.last_outreach_channel = req.channel
            candidate.last_outreach_date = datetime.now()

            # 自动推进 pipeline_stage
            if candidate.pipeline_stage in (None, 'new'):
                candidate.pipeline_stage = 'contacted'

        # 更新 outreach_count
        candidate.outreach_count = OutreachService.get_candidate_outreach_count(
            req.candidate_id, count_only=True
        )

        candidate.updated_at = datetime.now()
        db.commit()

        print(f"✅ 创建触达记录并更新candidates表: candidate_id={req.candidate_id}, channel={req.channel}, status={req.status}")

        return {
            "success": True,
            "record": {
                "id": record.id,
                "candidate_id": record.candidate_id,
                "channel": record.channel,
                "outreach_type": record.outreach_type,
                "status": record.status,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建触达记录失败: {str(e)}")
    finally:
        db.close()


@app.get("/api/outreach/{record_id}")
def get_outreach_record(record_id: int):
    """
    获取触达记录详情

    Args:
        record_id: 记录ID

    Returns:
        触达记录详情
    """
    try:
        from outreach_service import OutreachService

        record = OutreachService.get_outreach_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="触达记录不存在")

        return {
            "success": True,
            "record": {
                "id": record.id,
                "candidate_id": record.candidate_id,
                "channel": record.channel,
                "outreach_type": record.outreach_type,
                "status": record.status,
                "subject": record.subject,
                "content": record.content,
                "sent_at": record.sent_at.isoformat() if record.sent_at else None,
                "responded_at": record.responded_at.isoformat() if record.responded_at else None,
                "accepted_at": record.accepted_at.isoformat() if record.accepted_at else None,
                "response_content": record.response_content,
                "response_sentiment": record.response_sentiment,
                "related_job_id": record.related_job_id,
                "prompt_name": record.prompt_name,
                "meta_data": json.loads(record.meta_data) if record.meta_data else None,
                "ab_test_group": record.ab_test_group,
                "ab_test_name": record.ab_test_name,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取触达记录失败: {str(e)}")


@app.get("/api/candidates/{candidate_id}/outreach")
def get_candidate_outreach_history(candidate_id: int, channel: Optional[str] = None, limit: int = 50):
    """
    获取候选人触达历史记录

    Args:
        candidate_id: 候选人ID
        channel: 过滤渠道（可选）
        limit: 返回记录数限制（默认50）

    Returns:
        触达历史记录列表（按时间倒序）
    """
    try:
        from outreach_service import OutreachService

        records = OutreachService.get_candidate_outreach_history(
            candidate_id=candidate_id,
            channel=channel,
            limit=limit
        )

        return {
            "success": True,
            "candidate_id": candidate_id,
            "count": len(records),
            "records": [
                {
                    "id": r.id,
                    "channel": r.channel,
                    "outreach_type": r.outreach_type,
                    "status": r.status,
                    "subject": r.subject,
                    "content": r.content[:200] + "..." if r.content and len(r.content) > 200 else r.content,
                    "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                    "responded_at": r.responded_at.isoformat() if r.responded_at else None,
                    "accepted_at": r.accepted_at.isoformat() if r.accepted_at else None,
                    "related_job_id": r.related_job_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取触达历史失败: {str(e)}")


@app.put("/api/outreach/{record_id}/status")
def update_outreach_status(record_id: int, req: OutreachStatusUpdateRequest):
    """
    更新触达记录状态

    Args:
        record_id: 记录ID
        req: 状态更新请求

    Returns:
        更新结果
    """
    try:
        from outreach_service import OutreachService
        from datetime import datetime

        # 转换时间字符串为datetime对象
        responded_at = None
        accepted_at = None
        if req.responded_at:
            try:
                responded_at = datetime.fromisoformat(req.responded_at.replace('Z', '+00:00'))
            except:
                responded_at = datetime.now()
        if req.accepted_at:
            try:
                accepted_at = datetime.fromisoformat(req.accepted_at.replace('Z', '+00:00'))
            except:
                accepted_at = datetime.now()

        success = OutreachService.update_outreach_status(
            record_id=record_id,
            status=req.status,
            responded_at=responded_at,
            accepted_at=accepted_at,
            response_content=req.response_content,
            response_sentiment=req.response_sentiment,
        )

        if not success:
            raise HTTPException(status_code=404, detail="触达记录不存在")

        return {"success": True, "message": "状态更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")


@app.delete("/api/outreach/{record_id}")
def delete_outreach_record(record_id: int):
    """
    删除触达记录

    Args:
        record_id: 记录ID

    Returns:
        删除结果
    """
    db = SessionLocal()
    try:
        from outreach_service import OutreachService

        # 获取记录
        record = db.query(OutreachRecord).filter(OutreachRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="触达记录不存在")

        candidate_id = record.candidate_id
        is_counted = record.is_counted

        # 删除记录
        db.delete(record)
        db.commit()

        # 如果删除的是计数记录，需要更新outreach_count
        if is_counted:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate:
                candidate.outreach_count = OutreachService.get_candidate_outreach_count(
                    candidate_id, count_only=True
                )

                # 如果这是最新触达，需要更新last_outreach字段
                latest = db.query(OutreachRecord).filter(
                    OutreachRecord.candidate_id == candidate_id,
                    OutreachRecord.is_counted == True
                ).order_by(OutreachRecord.sent_at.desc()).first()

                if latest:
                    candidate.last_outreach_channel = latest.channel
                    candidate.last_outreach_date = latest.sent_at
                else:
                    candidate.last_outreach_channel = None
                    candidate.last_outreach_date = None

                db.commit()

        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    finally:
        db.close()


@app.post("/api/candidates/{candidate_id}/mark-replied")
def mark_candidate_replied(candidate_id: int, req: MarkRepliedRequest):
    """
    标记候选人对某个渠道的回复

    Args:
        candidate_id: 候选人ID
        req: 标记回复请求

    Request Body:
    {
        "channel": "linkedin",  # linkedin, maimai, email, phone
        "content": "回复内容描述",  # 可选
        "responded_at": "2026-02-17T12:30:00"  # 可选，默认当前时间
    }

    功能:
    1. 创建 outreach_record (type: replied)
    2. 更新候选人字段:
       - linkedin_accepted_at / maimai_accepted_at / email_replied_at / phone_exchanged_at
    3. pipeline_stage 自动流转为 replied (若当前为 new/contacted)

    Returns:
        标记结果
    """
    db = SessionLocal()
    try:
        from datetime import datetime
        from outreach_service import OutreachService, OutreachChannel, OutreachStatus

        # 验证候选人存在
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="候选人不存在")

        # 验证渠道
        valid_channels = ['linkedin', 'maimai', 'email', 'phone']
        if req.channel not in valid_channels:
            raise HTTPException(
                status_code=400,
                detail=f"无效的渠道: {req.channel}。有效值为: {', '.join(valid_channels)}"
            )

        # 转换时间
        responded_at = None
        if req.responded_at:
            try:
                responded_at = datetime.fromisoformat(req.responded_at.replace('Z', '+00:00'))
            except:
                responded_at = datetime.now()
        else:
            responded_at = datetime.now()

        # 1. 创建 outreach_record 记录
        record = OutreachService.create_outreach(
            candidate_id=candidate_id,
            channel=req.channel,
            outreach_type='reply',
            content=req.content or f"通过{req.channel}回复",
            status='accepted' if req.channel in ['linkedin', 'maimai'] else 'replied',
        )

        # 2. 更新 outreach_record 的时间字段
        if req.channel in ['linkedin', 'maimai']:
            record.accepted_at = responded_at
        else:
            record.responded_at = responded_at
        record.status = 'accepted' if req.channel in ['linkedin', 'maimai'] else 'replied'

        # 3. 更新候选人表的回复字段
        if req.channel == 'linkedin':
            candidate.linkedin_accepted_at = responded_at
        elif req.channel == 'maimai':
            candidate.maimai_accepted_at = responded_at
        elif req.channel == 'email':
            candidate.email_replied_at = responded_at
        elif req.channel == 'phone':
            candidate.phone_exchanged_at = responded_at

        # 4. 自动更新 pipeline_stage 到 'replied' (如果当前阶段较早)
        if candidate.pipeline_stage in [None, 'new', 'contacted', 'following_up']:
            old_stage = candidate.pipeline_stage or 'new'
            candidate.pipeline_stage = 'replied'
            
            # 记录阶段变更日志
            logs = candidate.communication_logs or []
            if isinstance(logs, str):
                try: logs = json.loads(logs)
                except: logs = []
            
            logs.insert(0, {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "channel": "system",
                "action": "stage_change",
                "content": f"自动流转: {old_stage} -> replied (触发源: 标记{req.channel}回复)",
                "direction": "system",
            })
            candidate.communication_logs = logs

        db.commit()

        return {
            "success": True,
            "message": f"已标记为{req.channel}回复",
            "candidate_id": candidate_id,
            "channel": req.channel,
            "responded_at": responded_at.isoformat(),
            "updated_field": f"{req.channel}_accepted_at" if req.channel in ['linkedin', 'maimai'] else f"{req.channel}_replied_at"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"标记回复失败: {str(e)}")
    finally:
        db.close()


@app.get("/api/outreach/stats")
def get_outreach_statistics(
    candidate_id: Optional[int] = None,
    channel: Optional[str] = None,
    days: int = 30
):
    """
    获取触达统计信息

    Args:
        candidate_id: 候选人ID（不指定则统计全部）
        channel: 渠道过滤
        days: 统计最近N天（默认30）

    Returns:
        统计数据
    """
    try:
        from outreach_service import OutreachService

        stats = OutreachService.get_outreach_statistics(
            candidate_id=candidate_id,
            channel=channel,
            days=days
        )

        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# ============ 触达作战中心 (Campaign Workspace) API ============

@app.get("/api/campaigns/linkedin")
def get_linkedin_campaign_queue():
    """获取待进行 LinkedIn 触达的优先候选人"""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        # 筛选条件: pipeline_stage='new', tier在(S, A+, A), has linkedin_url
        candidates = db.query(Candidate).filter(
            Candidate.pipeline_stage == 'new',
            Candidate.linkedin_url.isnot(None),
            Candidate.linkedin_url != ''
        ).order_by(
            # Tier 排序: S > A+ > A > B+ > B > C
            text(
                "CASE WHEN talent_tier = 'S' THEN 1 "
                "WHEN talent_tier = 'A+' THEN 2 "
                "WHEN talent_tier = 'A' THEN 3 "
                "WHEN talent_tier = 'B+' THEN 4 "
                "WHEN talent_tier = 'B' THEN 5 "
                "ELSE 6 END"
            )
        ).all()

        queue = []
        for c in candidates:
            # 获取 AI 破冰信 (如果批处理脚本已生成)
            draft = ""
            if c.greeting_drafts:
                if isinstance(c.greeting_drafts, str):
                    try:
                        drafts = json.loads(c.greeting_drafts)
                        draft = drafts.get('linkedin', "")
                    except:
                        pass
                elif isinstance(c.greeting_drafts, dict):
                    draft = c.greeting_drafts.get('linkedin', "")
            
            # extract ai_score if available
            ai_score = 0
            if c.structured_tags:
                try:
                    if isinstance(c.structured_tags, str):
                        tags = json.loads(c.structured_tags)
                    else:
                        tags = c.structured_tags
                    ai_score = tags.get('AI_score', 0)
                except:
                    pass

            queue.append({
                "id": c.id,
                "name": c.name,
                "company": c.current_company,
                "title": c.current_title,
                "tier": c.talent_tier,
                "linkedin_url": c.linkedin_url,
                "github_url": c.github_url,
                "personal_website": c.personal_website,
                "email": c.email,
                "ai_score": ai_score,
                "draft": draft
            })
            
        return {"success": True, "queue": queue}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 LinkedIn 队列失败: {str(e)}")
    finally:
        db.close()


@app.get("/api/campaigns/email")
def get_email_campaign_queue(
    page: int = 1,
    page_size: int = 30,
    tier: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """获取待进行邮件群发的候选人 (双栏布局 + 分页 + 分类筛选)"""
    db = SessionLocal()
    try:
        # 基础筛选: pipeline_stage='new', has email
        query = db.query(Candidate).filter(
            Candidate.pipeline_stage == 'new',
            Candidate.email.isnot(None),
            Candidate.email != ''
        )

        # Tier 筛选
        if tier and tier != 'ALL':
            tier_list = [t.strip() for t in tier.split(',')]
            query = query.filter(Candidate.talent_tier.in_(tier_list))

        # 搜索
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Candidate.name.ilike(search_term)) |
                (Candidate.current_company.ilike(search_term))
            )

        # 先获取全部符合条件的候选人（分类需要后端计算）
        all_candidates = query.order_by(Candidate.id.desc()).all()

        # 计算分类
        def _classify(c):
            website = (c.personal_website or '').lower()
            has_scholar = 'scholar.google' in website or '.edu' in website
            # Also check structured_tags for google_scholar link
            if not has_scholar and c.structured_tags and isinstance(c.structured_tags, dict):
                if c.structured_tags.get('google_scholar'):
                    has_scholar = True
            if has_scholar:
                return 'academic'
            if c.personal_website:
                return 'has_website'
            if c.github_url:
                return 'github_only'
            return 'email_only'

        classified = [(c, _classify(c)) for c in all_candidates]

        # 分类筛选
        if category and category != 'ALL':
            classified = [(c, cat) for c, cat in classified if cat == category]

        total = len(classified)

        # 分类统计（用于前端显示 tab 数量）
        cat_counts = {'academic': 0, 'has_website': 0, 'github_only': 0, 'email_only': 0}
        # 从 all_candidates 统计（不受 category 筛选影响）
        for c in all_candidates:
            cat = _classify(c)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        page_items = classified[start:end]

        queue = []
        for c, cat in page_items:
            # 提取邮件草稿
            draft = ""
            if c.greeting_drafts:
                drafts = c.greeting_drafts
                if isinstance(drafts, str):
                    try:
                        drafts = json.loads(drafts)
                    except:
                        drafts = {}
                if isinstance(drafts, dict):
                    draft = drafts.get('email', "")

            queue.append({
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "tier": c.talent_tier,
                "current_company": c.current_company or "",
                "current_title": c.current_title or "",
                "github_url": c.github_url or "",
                "personal_website": c.personal_website or "",
                "ai_summary": (c.ai_summary or "")[:200],
                "category": cat,
                "ai_score": (c.structured_tags or {}).get('github_score', 0) if isinstance(c.structured_tags, dict) else 0,
                "draft": draft
            })

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "category_counts": cat_counts,
            "queue": queue
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Email 队列失败: {str(e)}")
    finally:
        db.close()


# ============ 每日工作台 API (供 React 前端调用) ============

@app.get("/api/dashboard/context")
def dashboard_context():
    """获取每日工作台全部数据（缓存1分钟）"""
    try:
        from daily_planner import collect_daily_context
        import importlib
        import daily_planner
        importlib.reload(daily_planner)  # Force reload to pick up changes
        context = daily_planner.collect_daily_context()
        print(f"✅ Dashboard context collected with keys: {list(context.keys())}")
        return {"success": True, "data": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据采集失败: {str(e)}")


@app.post("/api/dashboard/ai-plan")
def dashboard_ai_plan():
    """调用 LLM 生成今日行动计划"""
    try:
        from daily_planner import collect_daily_context, generate_plan_with_llm, save_daily_report
        context = collect_daily_context()
        plan = generate_plan_with_llm(context)
        if plan:
            save_daily_report(context, plan)
            return {"success": True, "plan": plan}
        else:
            return {"success": False, "message": "AI分析失败，请稍后重试"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析失败: {str(e)}")


@app.get("/api/dashboard/reports")
def dashboard_reports():
    """获取历史日报列表"""
    import glob as _glob
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    if not os.path.isdir(reports_dir):
        return {"reports": []}

    report_files = sorted(_glob.glob(os.path.join(reports_dir, "daily_plan_*.md")), reverse=True)
    reports = []
    for rf in report_files[:10]:
        fname = os.path.basename(rf)
        date_str = fname.replace("daily_plan_", "").replace(".md", "")
        with open(rf, "r", encoding="utf-8") as f:
            content = f.read()
        reports.append({
            "date": date_str,
            "preview": content[:500] + ("..." if len(content) > 500 else ""),
            "full_content": content,
        })
    return {"reports": reports}


@app.get("/api/dashboard/outreach-analytics")
def dashboard_outreach_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取触达效果分析数据，支持时间范围筛选

    Args:
        start_date: 开始日期 (YYYY-MM-DD)，默认为本周一
        end_date: 结束日期 (YYYY-MM-DD)，默认为今天
    """
    try:
        from daily_planner import collect_outreach_analytics

        # 调用带参数的函数
        analytics = collect_outreach_analytics(start_date=start_date, end_date=end_date)
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据采集失败: {str(e)}")


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
    print(f"  POST /api/outreach            — 创建触达记录")
    print(f"  GET  /api/outreach/{{id}}      — 获取触达记录详情")
    print(f"  GET  /api/candidates/{{id}}/outreach  — 获取候选人触达历史")
    print(f"  PUT  /api/outreach/{{id}}/status — 更新触达状态")
    print(f"  GET  /api/outreach/stats       — 获取触达统计")
    uvicorn.run(app, host="0.0.0.0", port=port)

