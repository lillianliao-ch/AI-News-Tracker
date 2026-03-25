---
name: maimai-ops
description: 脉脉平台操作：发布 JD、查看投递简历、检查消息回复、筛选候选人。依赖 browser-agent skill。
---

# Maimai Ops Skill

> 依赖：browser-agent skill（必须先读）
> 所有操作在 Lilian 已登录的脉脉 Chrome Profile 中执行

---

## 场景一：发布职位 JD

### 触发
Lilian 说"帮我在脉脉发这个 JD" + 提供职位信息

### 步骤

```python
# 1. 调用 browser-agent 打开浏览器
# 2. 导航到脉脉招聘发布页
page.goto("https://maimai.cn/job/publish")  # 实际 URL 需调试

# 3. 填写 JD 信息（从 jobs 表读取 or Lilian 提供）
page.fill("#job-title", job_title)
page.fill("#job-desc", job_description)
# ... 其他字段

# 4. 截图给 Lilian 预览
page.screenshot(path="/tmp/maimai_jd_preview.png")
# notify() 发送截图 + "确认发布？"

# 5. 收到确认后点击发布
page.click("#publish-btn")
```

### 输出
- 发布成功 → Telegram 通知 + 职位链接
- 发布失败 → 截图 + 错误描述

---

## 场景二：查看谁投了简历

### 触发
"帮我看看有哪些人投了 [职位名]"

### 步骤

1. 打开脉脉招聘后台
2. 进入对应职位的投递列表
3. 抓取投递者基本信息（姓名 / 当前职位 / 公司 / 学历）
4. 用 Qwen 做初步筛选（与 JD 要求对比）
5. 生成结构化报告

### 输出格式

```
📋 [职位名] 投递情况

新简历 X 份（最近7天）

🟢 推荐跟进（X人）：
• 张三 - 字节跳动 AI算法工程师 (3年) - 匹配度: ★★★★
• ...

🟡 待评估（X人）：
• ...

🔴 不符（X人）：略
```

---

## 场景三：查看消息回复

### 触发
"帮我看看有没有人回消息" / 每日简报调用

### 步骤

1. 打开脉脉消息中心
2. 遍历最近 24 小时的回复
3. 与候选人数据库对比（是否已在 outreach_records）
4. 生成回复摘要

### 输出

```
💬 脉脉消息回复（过去24小时）

X 人有新回复：
• 李四（字节 AI方向）- "感谢联系，可以了解一下" → 建议：推进
• 王五（阿里 算法）- "目前暂无换工作打算" → 建议：进长期池
```

---

## 场景四：主动搜索人才

### 触发
Lilian 提供搜索关键词 or 从 JD 自动提取

### 步骤

1. 打开脉脉搜索
2. 搜索关键词（技术方向 + 公司 or 职位）
3. 翻页抓取候选人基本信息
4. 初步筛选（tier 评估逻辑）
5. 导出列表 → 调用 `import_maimai_candidates.py` 入库

> ⚠️ 注意：脉脉有反爬限制，每次搜索控制在 20-30 人，间隔 3-5 秒翻页

---

## 现阶段限制

- **无法直接触发脉脉 Chrome 插件的导入按钮**（扩展 API 不对外暴露）
- 入库方式：Lumi 抓取数据 → 生成标准格式 → 调用 `import_maimai_candidates.py`
