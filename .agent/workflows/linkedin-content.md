---
description: 生成 LinkedIn 帖子内容或职位发布文案，基于数据库中的紧急职位和 Lilian 的个人风格
---

# LinkedIn 内容生成

## 参考资料
1. 查看历史发帖内容和风格参考：
   ```
   cat /Users/lillianliao/notion_rag/personal-ai-headhunter/data/linkedin-content/posting_plan_2025_02.md
   ```

2. 查询数据库中的紧急职位（urgency >= 2）：
   ```python
   from database import SessionLocal, Job
   db = SessionLocal()
   jobs = db.query(Job).filter(Job.is_active == 1, Job.urgency >= 2).order_by(Job.urgency.desc()).all()
   for j in jobs:
       print(f'[紧急度{j.urgency}] {j.job_code} | {j.company} | {j.title} | HC:{j.headcount} | {j.location}')
   db.close()
   ```

## 写作风格（Lilian 的专业高效风）
- **行业洞察起手**：不废话，直接陈述行业趋势或技术落地现状
- **语气冷静专业**：去除自嘲和过多情绪化用词，展现顾问视角的客观性
- **强调核心价值**：点出"大厂"、"核心业务线"、"HC"等关键硬指标
- **结构化排版**：
  - Emoji 作为列表符号 (🎬, 🎵, 🎨, 📐, ✨)
  - 核心岗位 + HC (如有)
- **联系方式**：
  - 微信：13585841775
  - Email：lillianliao123@gmail.com

## 帖子结构
1. **行业观察/趋势**（1-2句，如"多模态 AI 正在快速落地..."）
2. **招聘背景**（几家大厂、核心业务线、积极招聘）
3. **岗位列表**（emoji + 岗位名 + HC）
4. **工作地点**
5. **联系引导**（简单直接）

## 输出位置
- 所有内容保存到 `/Users/lillianliao/notion_rag/personal-ai-headhunter/data/linkedin-content/` 目录下
