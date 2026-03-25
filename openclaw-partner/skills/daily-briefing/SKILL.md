---
name: daily-briefing
description: 每日猎头业务简报。汇总昨日数据、当前 pipeline 状态、今日行动建议，Telegram 推送。
---

# Daily Briefing Skill

## 触发场景

- Lilian 说"今天数据怎么样" / "给我看看昨天" / "简报"
- 或由定时任务每天早上自动触发

## 执行步骤

### 1. 查询昨日数据

```sql
-- 昨日新增候选人
SELECT COUNT(*), source FROM candidates 
WHERE DATE(created_at) = DATE('now', '-1 day')
GROUP BY source;

-- 昨日触达数
SELECT COUNT(*), channel, status FROM outreach_records
WHERE DATE(created_at) = DATE('now', '-1 day')
GROUP BY channel, status;

-- 当前 pipeline 分布
SELECT pipeline_stage, COUNT(*) FROM candidates
WHERE pipeline_stage NOT IN ('new', 'closed')
GROUP BY pipeline_stage ORDER BY COUNT(*) DESC;

-- 今日跟进优先级（next_follow_up <= today）
SELECT name, talent_tier, pipeline_stage, next_follow_up 
FROM candidates
WHERE next_follow_up <= DATE('now') AND pipeline_stage NOT IN ('closed', 'new')
ORDER BY talent_tier, next_follow_up
LIMIT 10;
```

### 2. 生成简报

格式（中文，简洁）：

```
📊 [日期] 业务简报

昨日新增：X人（来源分布）
昨日触达：X次（渠道分布）

🔥 今日重点跟进（Top 5）：
• [候选人名] [Tier] - [阶段] - [原因]

💼 Pipeline 状态：
• contacted: X人 | replied: X人 | wechat: X人

💡 今日建议：
[1-2条基于数据的具体建议]
```

### 3. 通知

```python
from telegram_notifier import notify
notify(briefing_text)
```

## 输出规范

- 简报控制在 300 字以内
- 今日建议要具体（"建议重点跟进 X，因为已经 7 天未回复"），不要泛泛而谈
- 如果没有特别值得关注的，直接说"今天没有明显信号，按常规推进"
