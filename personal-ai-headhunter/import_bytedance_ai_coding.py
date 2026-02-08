#!/usr/bin/env python3
"""
批量导入字节跳动 AI Coding 岗位
来源: 飞书文档 - 字节跳动岗位list-AI Coding（HR夏丹伦+张宇）for猎头
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, Job
from sqlalchemy import text
import re

# HR信息
HR_XIA = "夏丹伦 (xiadanlun@bytedance.com)"
HR_ZHANG = "张宇 (zhangyu.vicky@bytedance.com)"

# 完整岗位数据（从飞书文档提取）
JOBS = [
    # ========== AI 编程助手 (Trae) —— 负责人：夏丹伦 ==========
    {
        "title": "AI Coding产品经理（开发工具设计方向）-Trae",
        "department": "AI 编程助手 (Trae)",
        "location": "北京/上海",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7494208027257784594",
    },
    {
        "title": "高级全栈开发工程师-AI编程助手",
        "department": "AI 编程助手 (Trae)",
        "location": "北京/上海/杭州/深圳",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7439660623468841234",
    },
    {
        "title": "高级研发工程师-LLM for Code 方向",
        "department": "AI 编程助手 (Trae)",
        "location": "北京/上海/杭州/深圳",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7439661684443433234",
    },
    {
        "title": "AI应用服务端工程师-Trae",
        "department": "AI 编程助手 (Trae)",
        "location": "北京/上海/杭州/广州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7083680612222454023",
    },
    {
        "title": "AI应用前端工程师-Trae",
        "department": "AI 编程助手 (Trae)",
        "location": "北京/上海/杭州/深圳/广州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7319788361391900965",
    },
    
    # ========== Stone-Dev Platform —— 负责人：夏丹伦 ==========
    {
        "title": "AI编码策略产品专家",
        "department": "Stone-Dev Platform",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7447731549913532690",
    },
    {
        "title": "AI产品研发工程师",
        "department": "Stone-Dev Platform",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1/3-2",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7444821233546545416",
    },
    {
        "title": "AI Coding大模型工程师/算法专家",
        "department": "Stone-Dev Platform",
        "location": "上海/杭州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "https://jobs.bytedance.com/experienced/position/7530567393682016519/detail",
    },
    {
        "title": "资深大模型算法工程师/研究员-软件开发方向",
        "department": "Stone-Dev Platform",
        "location": "上海/杭州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "https://jobs.bytedance.com/experienced/position/7439251458647918856/detail",
    },
    {
        "title": "大模型开发平台后端研发工程师(Coze)",
        "department": "Stone-Dev Platform (Coze/扣子)",
        "location": "北京",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7423404999906134281",
    },
    {
        "title": "后端研发架构师(Coze)",
        "department": "Stone-Dev Platform (Coze/扣子)",
        "location": "北京",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7428489347824371994",
    },
    {
        "title": "服务端开发工程师/专家-AgentOps方向",
        "department": "Stone-Dev Platform",
        "location": "上海",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7471107025285171464",
    },
    {
        "title": "高级研发工程师/架构师-AI智能化方向",
        "department": "Stone-Dev Platform",
        "location": "北京",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7305980970300639538",
    },
    {
        "title": "资深服务端开发/架构师-AI应用平台",
        "department": "Stone-Dev Platform",
        "location": "北京",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7434742484503120167",
    },
    
    # ========== 开发者服务团队 —— 负责人：夏丹伦 ==========
    {
        "title": "开发者工具链产品专家-开发者服务",
        "department": "开发者服务",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1/3-2",
        "hr": HR_XIA,
        "jd_link": "https://jobs.bytedance.com/society/position/detail/7490550385191815432",
    },
    {
        "title": "程序分析工程师/专家",
        "department": "开发者服务",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7303928941215467813",
    },
    {
        "title": "大模型算法架构师/Leader-Dev AI方向",
        "department": "开发者服务",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7447770600603535624",
    },
    {
        "title": "端智能平台开发工程师",
        "department": "开发者服务",
        "location": "北京/深圳",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7385113819154860314",
    },
    {
        "title": "高级研发工程师/架构师-DevOps AI方向",
        "department": "开发者服务",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7473798623828003079",
    },
    {
        "title": "前端开发Leader - Dev Infra",
        "department": "开发者服务",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1/3-2",
        "hr": HR_XIA,
        "jd_link": "https://jobs.bytedance.com/experienced/position/7161404296638105863/detail",
    },
    {
        "title": "高级研发工程师-代码基础设施方向",
        "department": "开发者服务",
        "location": "北京/上海/杭州",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/6834682107822934279",
    },
    {
        "title": "数据平台负责人",
        "department": "开发者服务",
        "location": "北京/深圳",
        "seniority_level": "3-1/3-2",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/7418109560323541299",
    },
    
    # ========== 质量技术团队 —— 负责人：张宇 ==========
    {
        "title": "大模型算法专家/工程师-代码质量方向",
        "department": "质量技术",
        "location": "北京/上海",
        "seniority_level": "3-1",
        "hr": HR_ZHANG,
        "jd_link": "http://job.toutiao.com/society/position/detail/7366594602470115594",
    },
    {
        "title": "大模型算法架构师-质量智能",
        "department": "质量技术",
        "location": "北京/上海/杭州/深圳",
        "seniority_level": "3-1",
        "hr": HR_ZHANG,
        "jd_link": "http://job.toutiao.com/society/position/detail/7476082497924303122",
    },
    {
        "title": "大模型应用开发架构师-代码/资金/变更领域",
        "department": "质量技术",
        "location": "北京/上海/杭州/深圳",
        "seniority_level": "3-1",
        "hr": HR_ZHANG,
        "jd_link": "http://job.toutiao.com/society/position/detail/7478627859923290376",
    },
]


def generate_job_code(db, prefix="BT"):
    """生成职位编号"""
    result = db.execute(text(f"SELECT job_code FROM jobs WHERE job_code LIKE '{prefix}%' ORDER BY job_code DESC LIMIT 1")).fetchone()
    
    if result and result[0]:
        match = re.search(r'(\d+)$', result[0])
        if match:
            next_num = int(match.group(1)) + 1
        else:
            next_num = 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:03d}"


def main():
    db = next(get_db())
    
    imported = 0
    skipped = 0
    
    for job_data in JOBS:
        # 检查是否已存在（按标题+公司去重）
        existing = db.query(Job).filter(
            Job.title == job_data["title"],
            Job.company == "字节跳动"
        ).first()
        
        if existing:
            print(f"⏭️ 跳过 (已存在): {job_data['title']}")
            skipped += 1
            continue
        
        # 生成职位编号
        job_code = generate_job_code(db)
        
        # 创建职位
        new_job = Job(
            job_code=job_code,
            title=job_data["title"],
            company="字节跳动",
            department=job_data["department"],
            location=job_data["location"],
            seniority_level=job_data["seniority_level"],
            hr_contact=job_data["hr"],
            jd_link=job_data["jd_link"],
            raw_jd_text=f"【职位】{job_data['title']}\n【部门】{job_data['department']}\n【职级】{job_data['seniority_level']}\n【地点】{job_data['location']}\n\n请访问原始JD链接查看完整职位描述。",
        )
        
        db.add(new_job)
        db.commit()
        
        print(f"✅ 导入: {job_code} | {job_data['title']} | {job_data['department']} | {job_data['seniority_level']}")
        imported += 1
    
    print(f"\n📊 导入完成: 成功 {imported} 个, 跳过 {skipped} 个")


if __name__ == "__main__":
    main()
