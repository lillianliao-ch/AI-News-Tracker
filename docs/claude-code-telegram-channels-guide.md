# Claude Code × Telegram 远程操控配置指南

> 基于视频：[不在电脑前也能用 Claude Code 啦！Telegram 远程操控教程](https://www.youtube.com/watch?v=YMY6_psF7Mo)（01Coder，2026-03-23）

## 功能说明

Claude Code 2.1.80+ 新增 **Channels（通道）** 功能，允许通过 Telegram Bot 将外部消息推送进正在运行的 Claude Code 会话，实现**手机远程发消息 → Claude 在电脑上执行任务 → 结果推回 Telegram** 的工作流。

适用场景：外出时远程触发代码生成、脚本执行、爬虫任务等，无需 SSH 或打开电脑。

---

## 前置条件

| 条件 | 说明 |
|------|------|
| Claude Code 版本 | **≥ 2.1.80**（`claude --version` 确认） |
| Bun | 官方 Telegram 插件基于 Bun，需先安装 |
| Telegram 账号 | 用于创建和使用 Bot |

### 安装 Bun

```bash
curl -fsSL https://bun.sh/install | bash
```

安装后验证版本，并将 Bun 路径添加到 `~/.zshrc` 或 `~/.bashrc` 的 `PATH` 中。

---

## 配置步骤

### 第一步：创建 Telegram Bot

1. 在 Telegram 搜索并打开 `@BotFather`
2. 发送 `/newbot`
3. 输入 Bot 名称（如 `Claude Code 助手`）
4. 输入 Bot ID（必须以 `bot` 结尾，如 `myClaudeCodeBot`）
5. 获得 **Token**，保存备用

### 第二步：安装插件

在 Claude Code 中执行：

```bash
# 安装官方插件市场
claude mcp add https://github.com/anthropics/claude-code-marketplace

# 安装 Telegram 插件
claude plugin install telegram
```

首次安装时选择安装层级（用户级 / 项目级），根据需求选择。

### 第三步：激活并配置 Token

在 Claude Code 会话中执行：

```
/reload-plugins
```

然后配置 Token：

```
/telegram:config
```

粘贴第一步获得的 Bot Token，系统会自动写入 `.env` 文件。

### 第四步：启动（带 Channels 参数）

退出当前会话，重新启动 Claude Code 时加入参数：

```bash
claude --channels plugin:telegram
```

启动后终端会显示：**"正在监听所有 channel 消息"**

### 第五步：配对绑定

1. 在 Telegram 打开你创建的 Bot
2. 发送任意消息，Bot 会返回一条配对命令
3. 将配对命令复制并粘贴到 Claude Code 会话中
4. 配对完成，即可开始使用

---

## 持久运行（推荐配合 tmux）

为防止关闭终端后会话中断，使用 tmux 保持后台运行：

```bash
# 创建新 session
tmux new -s claude

# 在 session 内启动
claude --channels plugin:telegram

# 分离 session（不关闭）
Ctrl+B, D

# 之后重新连接
tmux attach -t claude
```

---

## 权限问题处理

**问题：** Claude Code 执行某些命令时会弹出授权确认，在 Telegram 端无法远程批准。

**解决方案：** 启动时加 `--dangerously-skip-permissions` 参数：

```bash
claude --channels plugin:telegram --dangerously-skip-permissions
```

> [!CAUTION]
> 该参数会让 Claude Code **跳过所有权限确认**，直接执行命令。仅在你完全信任所发送任务的情况下使用，注意安全风险。

---

## 使用示例

配置完成后，直接在 Telegram 给 Bot 发消息即可：

```
帮我在 personal-ai-headhunter 项目里跑一下 sourcing pipeline
```

```
检查一下 GitHub mining 脚本有没有报错
```

```
帮我在网站上创建一个新的标签归档页
```

---

## 当前状态与注意事项

- Channels 功能目前处于 **Research Preview（预览阶段）**，命令格式后续可能变化
- 除 Telegram 外，官方还支持 **Discord** 插件
- 底层通信走 **MCP 协议**
- 体验与 OpenClaw（小龙虾）的 Telegram 集成模式完全一致

---

*整理时间：2026-03-24*
