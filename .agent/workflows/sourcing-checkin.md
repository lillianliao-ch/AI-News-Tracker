---
description: 每日 Sourcing Check-in — 查看昨日数据、分析进展、输出今日行动计划
---

// turbo-all

## 每日 Sourcing Check-in 流程

每天开工时运行此 workflow，自动完成 sourcing 工作台初始化。

### Step 1: 读取 Sourcing 执行日志

读取 `personal-ai-headhunter/data/sourcing_推进.md` 文件，获取最新的多渠道执行数据（脉脉打招呼/加好友、LinkedIn Connection、Email 发送等）。

### Step 2: 读取 Sourcing 执行规划

读取 `personal-ai-headhunter/data/sourcing_execution_plan.md`，确认今日目标公司、搜索关键词、各渠道目标数量。

### Step 3: 运行每日工作台获取 DB 最新状态

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter && python daily_planner.py --no-llm
```

### Step 4: 分析与行动建议

基于以上三步收集的信息，综合分析：

1. **昨日回顾**:
   - 昨日各渠道实际数量 vs 目标数量
   - 回复率/转化率计算
   - 覆盖了哪些方向/对标公司

2. **今日行动计划**:
   - 按执行日历确认今日目标公司和搜索关键词
   - 各渠道目标分配 (脉脉打招呼/加好友、LinkedIn、Email)
   - 优先跟进昨日有回复的候选人
   - S/A 级候选人邮件 review 队列

3. **异常信号检测**:
   - 某方向连续 2 天零回复 → 建议调整关键词或对标公司
   - 某渠道回复率 > 8% → 建议加大投入
   - 脉脉搜索结果重复率高 → 建议换关键词或渠道

4. **动态调整建议**:
   - 根据累计数据，建议是否需要调整两周计划中的优先级
   - 是否有 JD 已 close 需要降优先级
   - 是否发现新的高产方向

### Step 5: 更新执行日志

将今日计划追加到 `sourcing_推进.md` 的执行日志部分，格式参照现有日志格式。

### 注意事项

- 每次 check-in 都要输出一个简洁的"今日 Dashboard"，包含：昨日数据 + 今日目标 + 优先事项 Top 3
- 如果是周一，额外做一次周复盘总结
- 如果发现数据异常（如执行天数缺失），主动提醒补录
