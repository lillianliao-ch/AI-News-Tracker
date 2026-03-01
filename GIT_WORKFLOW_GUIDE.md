# Git 工作流与安全规范

为了避免代码和工作进度的意外丢失，请所有 AI 助手（包括我在内）在执行任何不可逆的 Git 操作前，**严格遵守以下第一安全准则**：

## 🚨 核心安全准则：Check-in Before Checkout 🚨

**在执行任何类似 `git checkout`、`git reset` 或 `git clean` 等可能会覆盖或丢弃本地工作目录中未提交（Uncommitted）代码的操作之前，必须：**

1. **首先运行 `git status`** 检查当前工作目录的状态，确认是否有未提交（Untracked，Modified，Deleted）的文件。
2. **务必先 Commit 或 Stash** 将当前有价值的工作进度安全保存（Check-in）。
   - 如果确定是部分完成的阶段性代码，也必须打一个 `WIP (Work In Progress)` 的 commit，或者使用 `git stash` 暂存。
3. **确认无丢失风险后**，才允许执行大面积的恢复或重置命令（例如 `git checkout HEAD -- .` 这种危险命令）。

### 为什么需要这个规则？
即使是因为某些文件被误删（例如服务报 `ModuleNotFoundError`）需要把环境恢复到干净状态，如果不优先保存刚才人工或 AI 修改过的新文件，全量 `checkout` 或 `reset --hard` 会把刚刚写完但还没提交的新逻辑一并抹除，导致严重的回溯和重工。

### 常用安全命令
- 保存重置前状态：`git add . && git commit -m "chore: wipe safety backup before reset"`
- 安全暂存：`git stash save "temp backup before checkout"`
