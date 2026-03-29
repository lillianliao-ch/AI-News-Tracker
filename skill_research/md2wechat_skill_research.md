# md2wechat-skill 研究与实验记录

## 1. 工具定位
`md2wechat-skill` 是一个开源的 Go CLI 命令行工具，核心能力是将 Markdown 本地文件直接转换为精美的微信公众号图文格式，并能够利用微信官方接口自动推送到公众号草稿箱。
它专为包含大语言模型的自动化流水线（Agentic Workflow）设计，自带发现接口（Discovery），使得像 Claude Code 这样的 Agent 可以非常流畅地调用它完成本地写作到公众号分发的全链路闭环。

## 2. 核心竞争力分析

- **终端原生工作流**：支持本地执行 `preview` 极速预览排版；配合 `--draft` 直接把 Markdown 中的图片自动上传至微信服务器，免除了复制粘贴和单独加图的痛点。
- **Agent 首选（Skill 扩展）**：它自带 `.claude-plugin` 标准并兼容 OpenClaw。内置了诸如 `md2wechat capabilities / themes / providers / prompts` 这样的命令供 AI 查询机器人的当前能力，方便大模型精准执行指令。
- **AI 去味（Humanize）**：针对越来越多使用 LLM 生成文章的场景，内置了 AI 去痕引擎，能按不同强度削弱大模型文章里常见的套话（如“强调了...的重要性”、“结论”、“而且...”等）。
- **多种排版模式**：
  - 调用作者维护的 API 接口 (`md2wechat.cn`) 实现内联排版转换（如 default、minimal 等）。
  - 大模型 Prompt 直接排版。
- **创作者风格仿写 (`write` 功能)**：输入核心素材，让工具模仿特定的创作者（例如 Dan Koe 深度且犀利的风格）去撰写/润色文案。

## 3. 业务结合点（与 Lillian 当前的工作流）

由于平时深度使用 Notion、大语言模型生成以及 Python 脚本收集资料（如 `AI News Tracker`）：
1. 可以完美对接之前使用大模型生成的小红书/全平台分发文字稿，直接变成微信格式。
2. 对于“AI 猎头/AI 技术观察”频道的深度长文，可跳过第三方坑爹的排版助手软件，实现在 VS Code 终端里直接一键推送私密草稿等待发布。
3. 结合“小绿书图文”模式（`create_image_post`），直接发布含少量前言配合多图的简要动态（类似小红书图文）。

## 4. 实验与测试计划 (Testing Plan)
1. **安装工具**: 通过本地 `brew` 或 curl 脚本安装该 CLI 工具。
2. **连接微信后台**: 初始化 `md2wechat config init`，并填入测试公众号（如新申请的 ThinkCast 或其他准备建立账号的）的 `AppID` 和 `AppSecret`，验证白名单。
3. **文本转换与预览实验**: 创建一个简单的 Markdown 文档，利用 `md2wechat preview test.md` 生成 HTML 效果。
4. **草稿推送闭环实验**: （等安全配置好 AppSecret 后）通过 `md2wechat convert test.md --draft` 完成从本地文件到微信公众平台草稿的穿透测试。

## 5. 当前最新代码与技术突破进展 (基于 2026-03 存档双轨并行方案)

目前我们其实在并行探索**两套不同架构**的方案应对微信推送闭环，详情如下：

### 第 1 轨：物理级注入方案 (Playwright CDP 直连本地 Chrome)
本方案目前已在内容分发管线 (`universal_content_orchestrator`) 中跑通闭环工作流。
- **核心逻辑与引擎**: 新建 `src/publishers/wechat_adapter.py`，入口跑通至 `run_single_wechat_test.py`。
- **关键突破点**:
  1. **无视 API 额度与反爬封控**：基于底层 Playwright CDP 协议直连开发者本机内建好 Token 的 Chrome（端口 `9224`），以完全拟人形态在微信物理页面操作。
  2. **跨越 UEditor 富文本图片防御**：突破了系统阻止悬空 Blob 注入拦截的限制。应用自动将 2.35:1 原本原生海报转成 Base64 二进制文件留存，通过构造底层内存事件 `ClipboardEvent('paste')`（实体剪贴板物理粘贴）实现图片直传微信服务器；后续利用 HTML 水化完成最终图文混合的极值组装。
  3. **原生基线重排版**：采用统一的“苹果硅谷审美基线 CSS”（`-apple-system, 15px, 1.8行高`），通过 JavaScript 原生 `insertHTML` 写入，实测已可实现落锁草稿箱的一锤定音验证。

### 第 2 轨：CLI 官方 API / Agent 方案 (即本 md2wechat 工具链)
这是本研究文档追踪的另一个体系：
- **方案协同点**：对比第 1 轨须要求维护一台具备活跃登录态的实体机 Chrome 常量，CLI 路线基于云端 `AppID / AppSecret` 鉴权，结构上更完美契合独立云端 Serverless / 托管环境需求（如 Railway / Vercel）。
- **Agent 化潜力大**：由于带有 `.claude-plugin` 标准并自带内置 AI 重排版去痕算法，极大方便我们的 Claude 等大模型管线把该工具融入 Tool API 使用规范里。
- **当前瓶颈/Action Item**：要解决接口鉴权屏障，需要严格地去测试新账号（如 ThinkCast 后台），申请开打白名单系统，生成 Token 并走通授权。故在真正落地前，其依赖云端基础设施完备度高。
