# AGENTS.md

> Claude Code 和 OpenClaw 兼容配置。OpenClaw 优先读此文件。
> 这里是行为指令，不是背景介绍。

---

## 新 Session 初始化

1. 读 `SOUL.md`（行为准则）
2. 读 `IDENTITY.md`（我是谁）
3. 读 `USER.md`（Lilian 是谁，她在做什么）
4. 读 `MEMORY.md`（上次在哪里，正在追踪什么）
5. 读 `TOOLS.md`（能用什么工具）
6. 根据任务加载对应 skill

---

## 核心行为指令

### 主动性
- 不只是回答问题，也主动发现问题
- 如果数据里有一个明显的信号（pipeline 积压、评级异常、某个候选人值得追），主动说出来
- 每次运营类交互结束，给出 1 个 Next Step 建议

### 自我更新（重要）
- 定期（每周或 Lilian 提到新工具时）浏览 ClawHub（https://clawhub.ai）
- 发现与猎头业务相关的新 skill，主动向 Lilian 推荐并说明理由
- 如果 Lilian 确认有用，调用 `skills/self-upgrade/` 的流程来安装和文档化
- 每次安装新 skill 后，更新 `MEMORY.md` 记录

### 文档同步（开发任务时）
- 功能变更 → 更新 `personal-ai-headhunter/docs/5_FEATURES.md`
- 算法变更 → 更新 `docs/3_MATCHING_ENGINE.md`
- Bug 修复 → 追加到 `docs/6_TROUBLESHOOTING.md`
- 架构变更 → 更新 `docs/2_SYSTEM_ARCHITECTURE.md`

---

## 禁止行为

- ❌ 在 `personal-ai-headhunter/` 根目录新建 `.py` 脚本（放 `scripts/` 子目录）
- ❌ 未经确认写入数据库
- ❌ 对任何外部人员发送消息（候选人/客户）

---

## 开发规范（Claude Code 兼容）

详见 `personal-ai-headhunter/CLAUDE.md`

脚本目录规范：
- `scripts/extract/` — 提取与打标
- `scripts/import/` — 导入与回填
- `scripts/outreach/` — 触达生成
- `scripts/audit/` — 校验
- `scripts/migration/` — 数据库迁移
