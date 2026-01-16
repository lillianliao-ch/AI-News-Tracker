"""
FastAPI 主应用
"""

import random
import re
import time
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings, get_ai_config, get_feishu_config
from app.schemas import (
    ProcessRequest,
    ProcessResponse,
    ErrorResponse,
    HealthResponse
)
from app.services.ai_parser import AIResumeParser
from app.services.feishu_client import feishu_client


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 猎头助手 - 简历解析与评估 API"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 路由 ==========

@app.get("/", response_model=HealthResponse)
async def root():
    """根路径"""
    return HealthResponse()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse()


@app.get("/api/feishu/health")
async def feishu_health_check():
    """飞书 API 健康检查"""
    result = await feishu_client.health_check()
    return JSONResponse(content=result)


def generate_mock_result(candidate_info, jd_config):
    """
    生成用于联调阶段的模拟结果
    """
    name = candidate_info.name or "候选人"
    base_seed = sum(ord(c) for c in name)
    random.seed(base_seed)
    
    skills_list = candidate_info.skills or []
    aggregated_text = " ".join([
        candidate_info.current_position or "",
        candidate_info.advantage or "",
        " ".join(skills_list)
    ]).lower()
    
    matched = 0.0
    for skill in jd_config.get("核心技能", []):
        cleaned = re.sub(r"[（(].*?[）)]", "", skill).strip()
        if not cleaned:
            continue
        cleaned_lower = cleaned.lower()
        if cleaned_lower in aggregated_text:
            matched += 1
            continue
        tokens = [t for t in re.split(r"[、,，/\s]+", cleaned_lower) if len(t) >= 2]
        token_hits = sum(1 for token in tokens if token in aggregated_text)
        matched += min(1, token_hits * 0.5)
    
    tag_bonus = min(len(skills_list), 8) * 1.5
    skill_score = min(95, 55 + matched * 12 + tag_bonus + random.randint(0, 6))
    skill_score = int(round(skill_score))
    
    work_years = candidate_info.work_years or 0
    required_years_text = jd_config.get("工作年限", "")
    required_numbers = [int(num) for num in re.findall(r"\d+", required_years_text)]
    required_min_years = required_numbers[0] if required_numbers else 0
    required_max_years = required_numbers[1] if len(required_numbers) > 1 else None
    
    experience_score = 55 + min(work_years * 3, 20)
    if work_years and work_years >= required_min_years:
        experience_score += 8
    if required_max_years and work_years and work_years <= required_max_years:
        experience_score += 4
    if candidate_info.current_company:
        experience_score += 5
    experience_score = int(max(50, min(92, experience_score + random.randint(-3, 5))))
    
    education_text = (candidate_info.education or "").lower()
    education_score = 65
    if "博士" in education_text or "phd" in education_text:
        education_score += 18
    elif "硕士" in education_text or "master" in education_text:
        education_score += 12
    elif "本科" in education_text or "bachelor" in education_text:
        education_score += 6
    education_score = int(min(95, education_score + random.randint(-4, 4)))
    
    stability_base = 60 + min(work_years * 2, 15)
    stability_base += random.randint(-5, 5)
    stability_score = int(max(50, min(90, stability_base)))
    
    overall = int(
        skill_score * jd_config["评估权重"]["技能匹配"]
        + experience_score * jd_config["评估权重"]["经验匹配"]
        + education_score * jd_config["评估权重"]["教育背景"]
        + stability_score * jd_config["评估权重"]["稳定性"]
    )
    
    if overall >= 75:
        level = "推荐"
    elif overall >= 60:
        level = "一般"
    else:
        level = "不推荐"
    
    structured_resume = {
        "基本信息": {
            "姓名": name,
            "年龄": candidate_info.age or random.randint(30, 45),
            "工作年限": work_years or random.randint(5, 12),
            "当前公司": candidate_info.current_company or "保密公司",
            "当前职位": candidate_info.current_position or "产品负责人",
            "学历": candidate_info.education or "本科",
            "毕业院校": "双一流高校",
            "期望薪资": candidate_info.expected_salary or jd_config["薪资范围"],
            "到岗状态": candidate_info.employment_status or "沟通后确定",
            "活跃度": candidate_info.active_status or "活跃情况未知",
        },
        "工作经历": [
            {
                "公司": candidate_info.current_company or "保密公司",
                "职位": candidate_info.current_position or "AI 产品经理",
                "时间": "2021.03-至今",
                "工作内容": [
                    "负责AI产品规划与落地，推动多项智能化功能上线",
                    "与研发团队协作，确保算法模型与业务场景匹配"
                ],
                "核心成果": [
                    "主导上线智能化招聘产品，支撑核心业务场景",
                    "搭建指标体系，显著提升团队效率"
                ]
            },
            *[
                {
                    "公司": company,
                    "职位": "核心骨干",
                    "时间": "往期经历",
                    "工作内容": ["核心项目经验描述"],
                    "核心成果": ["取得阶段性成果"]
                }
                for company in (candidate_info.previous_companies or [])
            ]
        ],
        "项目经验": [
            {
                "项目名称": "智能招聘助手",
                "项目描述": "构建基于大模型的自动候选人筛选与推荐系统",
                "个人职责": "需求分析、产品设计、数据指标设计",
                "技术栈": ["LLM", "RAG", "Python", "FastAPI"],
                "项目成果": "每日自动处理候选人 200+，节省人力 80%"
            }
        ],
        "技能清单": skills_list or [
            "大模型产品规划", "数据驱动决策", "RAG 方案设计", "招聘业务流程"
        ],
        "教育背景": [
            {
                "学校": candidate_info.schools[0] if candidate_info.schools else "上海交通大学",
                "学历": candidate_info.education or "本科",
                "专业": "计算机科学与技术",
                "时间": "2012-2016"
            },
            *[
                {
                    "学校": school,
                    "学历": "研究生" if "硕士" in school or "研究生" in school else "本科",
                    "专业": "相关专业",
                    "时间": "往期"
                }
                for school in (candidate_info.schools or [])[1:2]
            ]
        ]
    }
    
    evaluation = {
        "技能匹配度": skill_score,
        "技能匹配分析": (
            f"与JD关键技能匹配度较高，覆盖 {int(matched)} 项核心方向。"
            if matched >= 1 else "与JD核心技能存在一定差距，可进一步沟通。"
        ),
        "经验匹配度": experience_score,
        "经验匹配分析": f"累计 {work_years or '多年'} 年相关经验，角色与目标岗位接近。",
        "教育背景得分": education_score,
        "教育分析": f"学历背景为 {candidate_info.education or '本科'}，满足岗位要求。",
        "稳定性得分": stability_score,
        "稳定性分析": (
            "履历稳健，具备持续负责核心模块的能力。"
            + (f" 当前活跃状态：{candidate_info.active_status}。" if candidate_info.active_status else "")
        ),
        "综合匹配度": overall,
        "推荐等级": level,
        "核心优势": [
            "熟悉AI/数据产品规划与迭代",
            "具备跨部门推进与落地能力",
            "对招聘业务流程有实践经验"
        ],
        "潜在风险": [
            "团队管理经验需进一步验证",
            "对海外业务经验相对有限"
        ],
        "推荐理由": f"{name} 在AI产品方向有扎实积累，匹配目标岗位核心需求。",
        "技能标签": (skills_list[:5] if skills_list else ["AI产品", "RAG", "招聘自动化"])
    }
    
    if candidate_info.active_status:
        evaluation["核心优势"].append(f"{candidate_info.active_status}，响应速度快")
    if candidate_info.previous_companies:
        evaluation["核心优势"].append(f"具备 {len(candidate_info.previous_companies)+1} 家公司的核心经验")
    if candidate_info.schools:
        evaluation["核心优势"].append(f"教育背景覆盖：{'、'.join(candidate_info.schools[:2])}")
    
    return {
        "structured_resume": structured_resume,
        "evaluation": evaluation
    }


@app.post("/api/candidates/process", response_model=ProcessResponse)
async def process_candidate(request: ProcessRequest):
    """
    处理候选人简历
    
    流程：
    1. 解析 PDF 简历
    2. AI 提取结构化信息
    3. AI 评估匹配度
    4. 返回评估结果
    """
    start_time = time.time()
    
    try:
        # 转换 JD 配置
        jd_config = {
            "职位名称": request.jd_config.position,
            "工作地点": request.jd_config.location,
            "薪资范围": request.jd_config.salary_range,
            "工作年限": request.jd_config.work_years,
            "学历要求": request.jd_config.education,
            "核心技能": request.jd_config.required_skills,
            "加分技能": request.jd_config.optional_skills,
            "评估权重": {
                "技能匹配": request.jd_config.weights.get("skill", 0.40),
                "经验匹配": request.jd_config.weights.get("experience", 0.30),
                "教育背景": request.jd_config.weights.get("education", 0.15),
                "稳定性": request.jd_config.weights.get("stability", 0.15)
            }
        }
        
        # 提供 mock 能力，方便前端联调
        use_mock = (not request.resume_file) or (request.resume_file == "mock_data")
        raw_resume_text = request.resume_text

        if use_mock:
            parsed = generate_mock_result(request.candidate_info, jd_config)
            raw_resume_text = raw_resume_text or ""
        else:
            # 获取 AI 配置
            ai_config = get_ai_config()

            # 初始化 AI 解析器
            parser = AIResumeParser(
                api_key=ai_config["api_key"],
                model=ai_config["model"],
                provider=ai_config["provider"]
            )

            # 处理简历
            parsed = parser.process_resume(
                resume_base64=request.resume_file,
                jd_config=jd_config
            )
            raw_resume_text = raw_resume_text or parsed.get("raw_resume_text") or ""
        
        # 生成候选人 ID
        candidate_id = f"BOSS_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 上传到飞书（如果启用且是推荐候选人）
        feishu_record_id = None
        recommend_level = parsed["evaluation"].get("推荐等级", "")
        
        if feishu_client.is_enabled() and recommend_level == "推荐":
            try:
                # 准备飞书数据
                candidate_data = {
                    "candidate_id": candidate_id,
                    "name": request.candidate_info.name,
                    "age": request.candidate_info.age,
                    "work_years": request.candidate_info.work_years,
                    "education": request.candidate_info.education,
                    "current_company": request.candidate_info.current_company,
                    "current_position": request.candidate_info.current_position,
                    "salary": request.candidate_info.expected_salary,
                    "match_score": parsed["evaluation"].get("综合匹配度", 0),
                    "recommend_level": recommend_level,
                    "advantages": "\n".join(parsed["evaluation"].get("核心优势", [])),
                    "risks": "\n".join(parsed["evaluation"].get("潜在风险", [])),
                    "source_url": "",  # 前端可以传入
                    "active_status": request.candidate_info.active_status,
                    "employment_status": request.candidate_info.employment_status,
                }
                
                # 上传截图（如果有）
                screenshot_base64 = request.resume_screenshot if hasattr(request, 'resume_screenshot') else None
                
                # 添加到飞书
                feishu_record_id = await feishu_client.add_record(
                    candidate_data=candidate_data,
                    screenshot_base64=screenshot_base64
                )
                
                if feishu_record_id:
                    print(f"✅ 已上传到飞书: {candidate_id} -> {feishu_record_id}")
                else:
                    print(f"⚠️ 飞书上传失败: {candidate_id}")
                    
            except Exception as e:
                print(f"❌ 飞书上传异常: {e}")
                # 不影响主流程，继续返回结果
        
        # 构造响应
        response = ProcessResponse(
            success=True,
            candidate_id=candidate_id,
            candidate_info=request.candidate_info,
            structured_resume=parsed["structured_resume"],
            evaluation=parsed["evaluation"],
            resume_text=raw_resume_text,
            processing_time=round(processing_time, 2),
            message="处理成功" + (f"，已上传飞书: {feishu_record_id}" if feishu_record_id else "")
        )
        
        return response
    
    except ValueError as e:
        # 参数错误或解析错误
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    except Exception as e:
        # 其他错误
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "detail": str(exc)
        }
    )


# ========== 启动事件 ==========

@app.on_event("startup")
async def startup_event():
    """启动时执行"""
    print(f"🚀 {settings.APP_NAME} 启动成功！")
    print(f"📡 API 文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"🤖 AI 服务: {settings.AI_PROVIDER} ({settings.AI_MODEL})")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时执行"""
    print(f"👋 {settings.APP_NAME} 已关闭")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

