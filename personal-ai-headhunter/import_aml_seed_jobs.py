#!/usr/bin/env python3
"""
批量导入杜英英团队职位 (AML & 智创 & 语音 & Seed Application)
来源: https://bytedance.larkoffice.com/docx/I1QLdm6HroZTyExLloHcmL9VnPh
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Job
from datetime import datetime

# 职位数据 - 从飞书文档提取
JOBS = [
    # ========== AML (火山引擎 - 机器学习平台) ==========
    {
        "title": "机器学习训练框架研发工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海/杭州/深圳",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7597685495678372149/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "负责机器学习训练框架研发，支持万亿参数大模型训练。",
        "hr_contact": "杜英英",
    },
    {
        "title": "机器学习推理框架研发工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海/杭州/深圳",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7276328181376272700/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "负责机器学习推理引擎/HPC优化。",
        "hr_contact": "杜英英",
    },
    {
        "title": "大模型Agent平台研发工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7599925395534711045/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "负责ToB Agent平台研发。",
        "hr_contact": "杜英英",
    },
    {
        "title": "大模型训练系统工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7579103608538368309/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "火山方舟大模型训练系统研发。",
        "hr_contact": "杜英英",
    },
    {
        "title": "大模型推理系统工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7424067290041239817/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "火山方舟大模型推理系统研发。",
        "hr_contact": "杜英英",
    },
    {
        "title": "方舟服务端研发工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7580305675965303045/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "链路架构/MaaS服务端研发。",
        "hr_contact": "杜英英",
    },
    {
        "title": "机器学习异构硬件开发工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7503446961607297298/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "异构加速/硬件研发。",
        "hr_contact": "杜英英",
    },
    {
        "title": "强化学习训练框架工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7504181595093764359/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "RL训练框架研发。",
        "hr_contact": "杜英英",
    },
    {
        "title": "Agent技术研发工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7486005250659338504/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "智能体应用研发。",
        "hr_contact": "杜英英",
    },
    {
        "title": "MaaS平台架构师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7486005256011778312/detail",
        "seniority_level": "3-2/4-1",
        "raw_jd_text": "云原生/MaaS架构设计。",
        "hr_contact": "杜英英",
    },
    {
        "title": "大模型训推框架工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "深圳",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7435956684584339720/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "算法工程，深圳优先。",
        "hr_contact": "杜英英",
    },
    {
        "title": "AI智能体应用开发工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7431591471264663827/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "AI搜索产品背景优先。",
        "hr_contact": "杜英英",
    },
    {
        "title": "资深后端开发工程师-AI计算效率",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7580331932727855413/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "AI计算效率方向。",
        "hr_contact": "杜英英",
    },
    {
        "title": "机器学习平台SRE工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7445125822421813512/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "GPU/K8S大规模集群运维。",
        "hr_contact": "杜英英",
    },
    {
        "title": "大模型应用算法工程师",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7393304052891486473/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "搜索/Agent/RAG方向。",
        "hr_contact": "杜英英",
    },
    {
        "title": "大模型搜索算法专家/Leader",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7475643973677041928/detail",
        "seniority_level": "3-2/4-1",
        "raw_jd_text": "搜索算法专家/Leader。",
        "hr_contact": "杜英英",
    },
    {
        "title": "高级前端开发工程师-大模型方向",
        "company": "字节跳动",
        "department": "Data-AML",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7386221711612053810/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "大模型前端方向。",
        "hr_contact": "杜英英",
    },
    
    # ========== Seed Application (豆包/大模型研发) ==========
    {
        "title": "大语言模型算法工程师-豆包",
        "company": "字节跳动",
        "department": "Seed Application",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7470038020822075656/detail",
        "seniority_level": "2-2~3-2",
        "raw_jd_text": "豆包大语言模型算法研发，Posttrain/推理/RL方向。",
        "hr_contact": "杜英英",
    },
    {
        "title": "AIGC模型应用算法工程师-Seed",
        "company": "字节跳动",
        "department": "Seed Application",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7445512109403162915/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "AIGC模型应用算法。",
        "hr_contact": "杜英英",
    },
    {
        "title": "AIGC视频生成算法工程师",
        "company": "字节跳动",
        "department": "Seed Application",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7522773300025280776/detail",
        "seniority_level": "3-1~3-2",
        "raw_jd_text": "AIGC视频生成算法。",
        "hr_contact": "杜英英",
    },
    {
        "title": "AIGC图像生成算法工程师",
        "company": "字节跳动",
        "department": "Seed Application",
        "location": "北京/上海",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7600977479868516661/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "多模态图像生成算法。",
        "hr_contact": "杜英英",
    },
    {
        "title": "大模型算法工程师-语音",
        "company": "字节跳动",
        "department": "Seed Application",
        "location": "北京/上海/杭州/深圳",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7585034089091336501/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "语音大模型算法。",
        "hr_contact": "杜英英",
    },
    {
        "title": "豆包大模型算法工程师-互动娱乐",
        "company": "字节跳动",
        "department": "Seed Application",
        "location": "北京",
        "jd_link": "https://jobs.bytedance.com/experienced/position/7535024639476893959/detail",
        "seniority_level": "3-1",
        "raw_jd_text": "豆包互动娱乐应用算法。",
        "hr_contact": "杜英英",
    },
]


def extract_job_id(link: str) -> str:
    """从链接中提取职位ID作为job_code"""
    if not link:
        return None
    # 提取数字ID
    import re
    match = re.search(r'/(\d{15,})', link)
    if match:
        return f"BT-{match.group(1)[-6:]}"  # 取后6位作为简短ID
    return None


def main():
    db = SessionLocal()
    
    imported = 0
    skipped = 0
    
    for job_data in JOBS:
        # 检查是否已存在（通过链接去重）
        existing = db.query(Job).filter(Job.jd_link == job_data["jd_link"]).first()
        if existing:
            print(f"⏭️  跳过已存在: {job_data['title']}")
            skipped += 1
            continue
        
        # 生成job_code
        job_code = extract_job_id(job_data["jd_link"])
        
        # 创建职位
        job = Job(
            title=job_data["title"],
            company=job_data["company"],
            department=job_data.get("department"),
            location=job_data.get("location"),
            jd_link=job_data.get("jd_link"),
            seniority_level=job_data.get("seniority_level"),
            raw_jd_text=job_data.get("raw_jd_text"),
            hr_contact=job_data.get("hr_contact"),
            job_code=job_code,
            is_active=1,
            created_at=datetime.now(),
        )
        
        db.add(job)
        print(f"✅ 导入: {job_data['title']} ({job_code})")
        imported += 1
    
    db.commit()
    print(f"\n📊 导入完成: 新增 {imported} 个职位, 跳过 {skipped} 个已存在")


if __name__ == "__main__":
    main()
