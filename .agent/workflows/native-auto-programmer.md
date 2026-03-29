---
description: 自动化编程与轮子测试原生工作流 (Native Auto-Programmer), 提供 GitHub Repo 即可全自动执行调研评估、跑通 PoC 并集成代码
---

# Native Auto-Programmer Workflow

本工作流旨在彻底抛弃旧版基于爬虫和外部 Web UI（如 Kimi）的易碎自动化脚本。我们全盘转向 **“Antigravity 原生执行域”**，利用系统的本机终端操作、文件读写、自主容错能力，实现端到端的“拿到 Github Repo -> 闭环本地跑通 -> 自动改写为业务插件”一体化流程。

## 触发条件
在对话框中输入 `/native-auto-programmer` 或直接向我（Antigravity）提供：
1. **目标 Github Repository 的 URL**。
2. **您的业务诉求（可选）**：例如“我想用它来解析简历 / 替换原有的微信群发模块”。

---

## 自动化流水线执行步骤 (Automated Pipeline)

当本工作流被触发时，系统底层将**全自动**按以下顺序执行，并对每一步出具验证结果：

### Phase 1: Native 仓库克隆与价值判定 (Value Assessment)
1. **环境隔离**：自主在终端运行 `git clone`，将目标仓库克隆至本地临时目录（如 `/tmp/auto_research_xxx`）。
2. **源码阅读**：系统利用深度文件读取能力扫描 `README.md`、`setup.py`/`requirements.txt` 及核心代码逻辑。
3. **输出判定报告**：
   - 评判该库的功能与您的“业务诉求”是否匹配。
   - 提示是否活跃、是否可用于生产。
   - ⚠️ 若确认该库不符要求或已废弃，系统主动中止流程并汇报原因。

### Phase 2: 沙盒测试与自主修 Bug (Sandbox Verification)
**（核心优势：无惧报错栈，由系统独立跑通）**
1. **依赖拉取**：自主在隔离的虚拟环境中使用 `pip install` / `npm install` 安装必需依赖项。
2. **原型代码（PoC）生成**：基于 `README` 的范例，系统自主从零编写一个 `test_poc.py` (或对应的语言原型文件)。
3. **闭环自驱动运行**：
   - 系统调用命令行执行 `python test_poc.py`。
   - 如果发生崩溃（`ModuleNotFoundError`、`TypeError` 等），将触发“自修复节点”，系统自动重写代码、调整依赖包并不断重试。
   - 直至终端输出 0 错误（完美跑通）或彻底死胡同（宣告该库本地环境水土不服不可用）。

### Phase 3: 业务架构融合 (Seamless Code Integration)
当原型验证圆满通过后，代表该能力“可用”。
1. **扫描项目骨架**：进入您指定的项目核心路径（如 `universal_content_orchestrator`），读取当前的路由、配置与基类抽象规范。
2. **生产级代码改写**：将上述仅仅是“能跑通”的临时脚本代码，封装、复写成标准的 Python Module、Class 或者适配器插件。
3. **输出落盘**：将格式化优美的业务集成代码落盘到具体目录，您甚至可直接运行原有测试套件或查看文件变更效果。

---

## 注意事项与最佳实践
- **权限安全**：执行任何涉及更改宿主系统的操作（如全局 `brew install` 的高危操作），我会在执行命令前拦截并请求您的授权（SafeToAutoRun=False）。
- **工具混用**：如果您在此自动化闭环中仍需向部分网站提交授权或点击按钮，系统会随时调起**浏览器子智能体 (Browser Subagent)** 或利用 **OpenCLI** 作为动作延伸执行。
- **状态跟进**：系统会在面板中生成实时的 `task.md` 给您反馈阶段性进展。
