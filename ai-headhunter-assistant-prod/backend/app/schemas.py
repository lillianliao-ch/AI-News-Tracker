"""
API 数据模型（Pydantic）
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ========== 请求模型 ==========

class CandidateInfo(BaseModel):
    """候选人基本信息"""
    name: str = Field(..., description="姓名")
    source_platform: str = Field(default="Boss直聘", description="来源平台")
    source_url: Optional[str] = Field(None, description="来源链接")
    current_company: Optional[str] = Field(None, description="当前公司")
    current_position: Optional[str] = Field(None, description="当前职位")
    work_years: Optional[int] = Field(None, description="工作年限")
    expected_salary: Optional[str] = Field(None, description="期望薪资")
    education: Optional[str] = Field(None, description="学历")
    age: Optional[int] = Field(None, description="年龄")
    active_status: Optional[str] = Field(None, description="在线状态")
    employment_status: Optional[str] = Field(None, description="到岗/在职状态")
    recent_location: Optional[str] = Field(None, description="最近关注地点")
    skills: Optional[List[str]] = Field(default=None, description="标签/技能列表")
    advantage: Optional[str] = Field(None, description="候选人优势简介")
    schools: Optional[List[str]] = Field(default=None, description="教育经历学校列表（本科/研究生等）")
    previous_companies: Optional[List[str]] = Field(default=None, description="前公司记录")


class JDConfig(BaseModel):
    """JD 配置"""
    position: str = Field(..., description="职位名称")
    location: List[str] = Field(..., description="工作地点")
    salary_range: str = Field(..., description="薪资范围")
    work_years: str = Field(..., description="工作年限")
    education: str = Field(..., description="学历要求")
    required_skills: List[str] = Field(..., description="核心技能")
    optional_skills: List[str] = Field(default=[], description="加分技能")
    weights: Optional[Dict[str, float]] = Field(
        default={
            "skill": 0.40,
            "experience": 0.30,
            "education": 0.15,
            "stability": 0.15
        },
        description="评估权重"
    )


class ProcessRequest(BaseModel):
    """处理候选人请求"""
    candidate_info: CandidateInfo = Field(..., description="候选人基本信息")
    resume_file: Optional[str] = Field(None, description="Base64 编码的 PDF 简历")
    resume_text: Optional[str] = None
    jd_config: JDConfig = Field(..., description="JD 配置")


# ========== 响应模型 ==========

class BasicInfo(BaseModel):
    """基本信息"""
    name: str
    age: int
    work_years: int
    current_company: str
    current_position: str
    education: str
    university: str
    expected_salary: str


class WorkExperience(BaseModel):
    """工作经历"""
    company: str
    position: str
    time: str
    content: List[str]
    achievements: List[str]


class StructuredResume(BaseModel):
    """结构化简历"""
    basic_info: Dict[str, Any] = Field(..., alias="基本信息")
    work_experience: List[Dict[str, Any]] = Field(..., alias="工作经历")
    project_experience: List[Dict[str, Any]] = Field(default=[], alias="项目经验")
    skills: List[str] = Field(..., alias="技能清单")
    education: List[Dict[str, Any]] = Field(..., alias="教育背景")
    
    class Config:
        populate_by_name = True


class Evaluation(BaseModel):
    """评估结果"""
    skill_match: int = Field(..., alias="技能匹配度")
    experience_match: int = Field(..., alias="经验匹配度")
    education_score: int = Field(..., alias="教育背景得分")
    stability_score: int = Field(..., alias="稳定性得分")
    overall_match: int = Field(..., alias="综合匹配度")
    recommend_level: str = Field(..., alias="推荐等级")
    strengths: List[str] = Field(..., alias="核心优势")
    risks: List[str] = Field(..., alias="潜在风险")
    reason: str = Field(..., alias="推荐理由")
    tags: List[str] = Field(default=[], alias="技能标签")
    
    class Config:
        populate_by_name = True


class ProcessResponse(BaseModel):
    """处理候选人响应"""
    success: bool = Field(..., description="是否成功")
    candidate_id: str = Field(..., description="候选人ID")
    candidate_info: CandidateInfo = Field(..., description="候选人基本信息")
    structured_resume: Dict[str, Any] = Field(..., description="结构化简历")
    evaluation: Dict[str, Any] = Field(..., description="评估结果")
    resume_text: Optional[str] = Field(None, description="原始简历文本")
    processing_time: float = Field(..., description="处理耗时（秒）")
    message: Optional[str] = Field(None, description="消息")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    service: str = "AI Headhunter API"
    version: str = "1.0.0-mvp"

