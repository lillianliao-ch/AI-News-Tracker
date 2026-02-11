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

## 写作风格（Lilian 的口吻）
- 开头直接切入，不要长篇铺垫
- 语气像朋友聊天，不像招聘广告
- 可以加自嘲和幽默（😂😅）
- 用 emoji 分段，方便手机阅读
- **不提公司名**，只说"大厂和新秀"
- 结尾引导加微信 Along-the-path + GitHub: github.com/lillianliao-ch
- 禁止用"极具竞争力""令人印象深刻""非常匹配"等 AI 味词汇

## 帖子结构
1. 一句话观察/感受开头
2. 岗位列表（emoji + 岗位名 + HC）
3. 坐标城市
4. 轻松的互动/转发请求
5. 联系方式签名

## 输出位置
- 所有内容保存到 `/Users/lillianliao/notion_rag/personal-ai-headhunter/data/linkedin-content/` 目录下
