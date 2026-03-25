---
name: candidate-nurture
description: 分析当前 pipeline，给出今日 Top 3-5 跟进行动建议。帮 Lilian 决定今天该联系谁、怎么联系。
---

# Candidate Nurture Skill

## 触发场景

- Lilian 说"今天该跟谁"
- Lilian 查看跟进列表时
- 每日简报（daily-briefing skill）调用此 skill

## 执行逻辑

### 1. 查询待跟进列表

```sql
-- 已过 follow-up 时间 or 今天到期
SELECT c.id, c.name, c.talent_tier, c.pipeline_stage, 
       c.next_follow_up, c.outreach_count,
       c.linkedin_url, c.maimai_url, c.email
FROM candidates c
WHERE (c.next_follow_up <= DATE('now') OR c.next_follow_up IS NULL)
  AND c.pipeline_stage NOT IN ('closed', 'new', 'long_term_pool')
ORDER BY 
  CASE c.talent_tier 
    WHEN 'S' THEN 1 WHEN 'A+' THEN 2 WHEN 'A' THEN 3 
    WHEN 'B+' THEN 4 WHEN 'B' THEN 5 ELSE 6 END,
  c.next_follow_up ASC
LIMIT 20;
```

### 2. 评估每个候选人

对每个候选人判断：
- 当前阶段是什么？上次接触是什么时候？
- 下一步动作是什么？（发消息 / 换渠道 / 推 JD / 关闭）
- 有没有匹配的紧急 JD？
- Stop Rule 是否触发？（outreach_count >= 4 → 长期池）

### 3. 输出 Top 3-5 建议

```
🎯 今日跟进建议

1. [候选人名] [Tier] — [当前阶段]
   情况：[上次接触时间] + [已触达次数]  
   建议：[具体动作] + [理由]
   渠道：[LinkedIn / 脉脉 / Email]
   📝 草稿：[是否需要生成消息草稿？]

2. [候选人名] ...

⚠️ 建议关闭（3次+无回复）：
• [候选人名] — 已触达 X 次，移入长期池
```

### 4. 生成消息草稿（按需）

调用 `ai_service.py` + `prompts.py`：
- 参考候选人 profile（最近公司、技术方向、tier）
- 选择合适渠道的 system prompt
- 生成 250 字以内的个性化消息

## 输出规范

- 建议要具体，不要"可以考虑联系 X"，而是"今天联系 X，因为他已经 7 天没回复，要趁热打铁"
- 如果某人是 LAMDA 校友，自动在建议中标注（影响措辞策略）
- 给出建议后等 Lilian 确认，再生成消息草稿
