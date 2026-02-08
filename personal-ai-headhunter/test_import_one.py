#!/usr/bin/env python3
"""
测试导入一条字节跳动岗位
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, Job
import re

def generate_job_code(db, prefix="BT"):
    """生成职位编号"""
    from sqlalchemy import text
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
    
    # 测试导入第一条
    test_job = {
        "title": "AI Coding产品经理-Trae",
        "company": "字节跳动",
        "department": "AI 编程助手 (Trae)",
        "location": "北京",
        "seniority_level": "3-1",
        "hr_contact": "夏丹伦 (xiadanlun@bytedance.com)",
        "jd_link": "http://job.toutiao.com/society/position/detail/7360527198607395109",
        "jd_text": """团队介绍：字节跳动 AI Coding 团队致力于为开发者打造下一代智能化开发工具。我们相信人工智能将推动软件开发方式的深刻变革。团队打造的 Trae 产品系列涵盖 native IDE、编程助手等多元形态，通过智能化功能和无缝体验，能极大提升开发者的效率与创造力。我们正在寻找充满热情、富有创造力的技术和产品人才加入，共同定义未来开发的形态。

职位描述
1. 负责字节跳动AI Coding产品相关的产品管理工作，包括用户调研、行业分析、产品设计、用户体验设计、用户运营等；
2. 与产品运营和市场团队保持紧密协作，与开发者社区、用户社区保持紧密沟通，充分传递产品价值，理解客户需求，并落实有效需求到产品中，持续跟进产品的关键数据指标和用户反馈，持续迭代优化产品；
3. 与研发、算法、测试团队保持紧密合作，提升端到端AI效果，推动产品发布和项目落地；
4. 与UI/UX团队保持紧密合作，持续提升产品的视觉交互体验，设计新一代的交互方式；
5. 对产品竞争力负责，包括不限于行业发展研究、产品路线规划等。

职位要求
1. 本科及以上学历，计算机相关专业优先；
2. 3年及以上产品经理经验，有AI相关产品或模块设计经验优先；
3. 了解基础的AI技术，例如NLP、机器学习、LLM的大致原理，能够与技术无障碍沟通，具备开发能力者优先；
4. 了解Prompt Engineering和评测机制，能与AI算法、模型团队紧密合作，端到端提升AI效果；
5. 良好的英语读写能力，能够阅读和理解产品、技术文档和学术论文；
6. 有足够的主人翁意识和逻辑思维，有创新意识和意愿，有良好的分析能力，愿意独立思考，不盲从；有责任感，有跨团队协作能力，以用户价值为先，做热爱用户的产品经理，做用户喜爱的产品。"""
    }
    
    # 检查是否已存在
    existing = db.query(Job).filter(Job.title == test_job["title"], Job.company == test_job["company"]).first()
    if existing:
        print(f"⏭️ 跳过 (已存在): ID={existing.id} | {test_job['title']}")
        print(f"   职级: {existing.seniority_level}")
        print(f"   部门: {existing.department}")
        print(f"   HR: {existing.hr_contact}")
        print(f"   链接: {existing.jd_link}")
        return
    
    # 生成职位编号
    job_code = generate_job_code(db)
    
    # 创建职位
    new_job = Job(
        job_code=job_code,
        title=test_job["title"],
        company=test_job["company"],
        department=test_job["department"],
        location=test_job["location"],
        seniority_level=test_job["seniority_level"],
        hr_contact=test_job["hr_contact"],
        jd_link=test_job["jd_link"],
        raw_jd_text=test_job["jd_text"],
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    print(f"✅ 导入成功!")
    print(f"   ID: {new_job.id}")
    print(f"   编号: {job_code}")
    print(f"   职位: {test_job['title']}")
    print(f"   公司: {test_job['company']}")
    print(f"   部门: {test_job['department']}")
    print(f"   职级: {test_job['seniority_level']}")
    print(f"   地点: {test_job['location']}")
    print(f"   HR: {test_job['hr_contact']}")
    print(f"   链接: {test_job['jd_link']}")


if __name__ == "__main__":
    main()
