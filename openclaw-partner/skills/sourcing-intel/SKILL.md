---
name: sourcing-intel
description: 市场情报主动推送。监控 ArXiv 新论文、GitHub Trending，发现潜在候选人信号，推送给 Lilian。
---

# Sourcing Intel Skill

## 触发场景

- 定时任务（每天一次，早上推送）
- Lilian 说"最近有什么 AI 新人值得关注"
- Lilian 说"帮我看看今天的 arXiv"

## ArXiv 监控

```python
# 文件：arxiv_monitor.py（已存在）
python3 arxiv_monitor.py

# 关注领域：
# cs.LG (Machine Learning)
# cs.AI (Artificial Intelligence)  
# cs.CL (Computation and Language / NLP)
# cs.CV (Computer Vision)
# stat.ML (Statistics - ML)
```

**从论文中提炼**：
- 一作和通讯作者（姓名 + 机构）
- 是否已有 GitHub 主页（搜索 `github.com/[name]`）
- 是否已在 DB 中（查 `candidates` 表 name/github_url）
- 如果是新面孔且背景强：标记为候选人线索

## GitHub Trending 监控

```python
# 文件：github_trending_monitor.py（已存在）
python3 github_trending_monitor.py
```

**从 trending 项目中提炼**：
- 项目作者（个人或团队）
- AI 相关项目优先（含 LLM / diffusion / agent / RAG 等关键词）
- 是否已在 DB 中

## 推送格式

```
🔭 今日情报简报

📄 ArXiv 新面孔（3 人）
• Zhang San (MIT) - "Scaling Laws for..." 一作 → GitHub: zhangsan
  → 已在库 / 未在库，建议添加
  
⭐ GitHub Trending 新星
• [repo] by [author] — X stars 今日
  → 背景：[简短描述]

💡 今日建议添加：[名字列表]
[是否执行导入？]
```

## 导入流程（确认后执行）

```python
# 手动添加到候选人库
# 参考：import_github_candidates.py
```

## 原则

- 只推有实质信号的（论文质量 / star 数量 / 机构背景）
- 不为了推而推，每天 0 个也是合理结果
- 给出我的判断："这个人值得追，因为……"
