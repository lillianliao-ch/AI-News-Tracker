from database import SessionLocal, SystemPrompt
from datetime import datetime

def update_prompts():
    session = SessionLocal()
    
    # New Detailed Prompt
    new_candidate_prompt = """
    你是一个专业的招聘专家。请分析以下简历文本，并提取关键信息。
    请严格返回 JSON 格式，不要包含 Markdown 代码块标记。
    
    需要提取的字段说明：
    - summary: 【核心评价】请生成一份 200-300 字的深度分析，包含：1) 核心竞争力与亮点；2) 职业发展路径总结；3) 潜在风险或短板。请使用 Markdown 格式进行分点描述。
    - skills: 技能列表 (数组)
    - name: 姓名 (如果找不到，返回 "Unknown")
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
    
    # Deactivate old prompts
    session.query(SystemPrompt).filter(SystemPrompt.prompt_type == 'candidate', SystemPrompt.is_active == True).update({"is_active": False})
    
    # Add new prompt
    p = SystemPrompt(prompt_type='candidate', prompt_name='Detailed V2', content=new_candidate_prompt, is_active=True)
    session.add(p)
    session.commit()
    print("Successfully updated Candidate Parsing Prompt to V2 (Detailed).")
    session.close()

if __name__ == "__main__":
    update_prompts()

