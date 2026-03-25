---
name: self-upgrade
description: 主动查阅 ClawHub 和外部资源，发现对猎头业务有用的新 skills，评估并推荐安装。持续自我优化。
---

# Self-Upgrade Skill

## 触发场景

- 每周一次主动检查（Lumi 自发）
- Lilian 提到新工具或新平台
- 完成一个新的复杂任务后，发现缺少一个可复用的 skill

## 查阅流程

### 1. 查阅 ClawHub

访问 https://clawhub.ai，筛选与以下类别相关的 skill：
- 猎头 / 人才招募 / Talent Sourcing
- 内容创作 / Social Media
- 数据分析 / Database
- 邮件 / Outreach
- GitHub / 代码库分析

### 2. 评估标准

| 维度 | 问题 |
|------|------|
| 相关性 | 这个 skill 对猎头业务有直接帮助吗？ |
| 可用性 | 它需要的工具/API 我们已经有吗？ |
| 重复性 | 现有 skill 已经覆盖了吗？ |
| 复杂度 | 安装配置成本高不高？ |

### 3. 推荐格式

当我发现值得推荐的 skill，向 Lilian 报告：

```
🦦 发现新 skill 值得看：

**[Skill 名]**（来源：ClawHub / GitHub / 其他）
- 是什么：一句话说清楚
- 对业务的价值：具体场景
- 需要：[API/工具依赖]
- 我的判断：推荐 / 可以不装（原因）
```

### 4. 安装流程

如果 Lilian 确认安装：
1. 将 skill 文件下载/创建到 `skills/[skill-name]/SKILL.md`
2. 在 `MEMORY.md` 的"已安装 Skills"表中记录
3. 在 `TOOLS.md` 中补充相关工具引用（如有）
4. 简短测试，确认能跑

### 5. 自我生成新 Skill

如果发现重复做同一件事超过 3 次，主动提议：
- "这个流程值得做成一个 skill，我来写 SKILL.md"
- 写完后放到 `skills/` 目录，更新 MEMORY.md

## 已查阅记录

详见 `MEMORY.md` → "ClawHub 已评估 Skills" 表

## 原则

- 不是为了装更多 skill，是为了让每个 session 开始时我能做更多事
- 安装的 skill 要能用，不能只是摆着
- 如果某个已安装的 skill 几个月没用过，考虑清理（节省上下文）
