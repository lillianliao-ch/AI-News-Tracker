# 猎头系统自动化同步工具

## 当前项目概述
利用 Playwright 编写的自动化脚本，尝试连接第三方猎头系统（阿里猎头、谷露 CRM 等），抓取候选人信息并为后续同步到“猎头协作平台”做准备。近期工作重心改为针对谷露 CRM 的自动化登录与数据提取。

## 目录结构（截至 2025-09-25）
```
headhunter_automation/
├── gllue_scraper.py        # 谷露 CRM 自动化脚本（Playwright）
├── run_unassigned_orders.py# （旧）阿里猎头相关脚本入口，保留用于参考
├── config/
│   └── settings.yaml       # 通用配置（仍保留历史配置）
├── data/
│   ├── debug/              # 调试输出（HTML、截图等）
│   └── gllue_candidates_*.json
├── logs/
│   └── automation.log
├── requirements.txt        # Python 依赖
└── src/                    # 历史模块残余（尚未完全清理）
```
> 说明：原先的 `auto_scraper.py`、`manual_login_scraper.py` 等文件已删除；若需恢复旧版阿里猎头脚本，可回溯 Git 历史或从备份中还原。

## 最新进展
- ✅ **Playwright 环境搭建完成**：`gllue_scraper.py` 支持 Chromium 无头/有头运行，并通过 `.env` 读取账号。
- ✅ **谷露 CRM 自动登录成功**：脚本可以自动访问登录页、识别输入框（支持 iframe/多上下文）、提交凭据并跳转至 Dashboard。
- ✅ **失败日志与调试输出完善**：当无法解析列表时，会在 `data/debug/` 下保存 HTML、截图，方便后续排查。

- ⚠️ **候选人列表尚未解析成功**：
  - 谷露的候选人列表由前端 JS 动态渲染，无传统 `<table><tr>` 结构，脚本目前抓取到的行数为 0。
  - 尚未找到公开的候选人列表 API；Network 面板主要出现轮询 `/rest/user` 请求，列表数据接口仍待定位。
- ⚠️ **数据字段提取局限**：目前只在候选人详情页确认了“姓名、所在城市、工作经历”等字段的 DOM 选择器，但尚未批量遍历列表。

## 遇到的问题 / 风险
1. **动态渲染列表**：需要进一步研究页面框架（可能是自研 SPA），确定如何获取候选人 ID 或直接调用内部接口。
2. **接口调试尚未完成**：Network 面板暂未发现 `candidate/list` 等明显接口；后续需通过筛选、查看 Initiator 或阅读加载脚本来定位。
3. **项目结构待整理**：`src/` 目录仍包含历史代码；本次工作以 `gllue_scraper.py` 为主，其它模块未来可根据需要重构或删除。

## 下一步计划（待恢复时参考）
1. 在浏览器开发者工具中确认候选人列表真实 DOM 或 API 请求路径。
2. 更新 `SELECTORS["candidate_rows"]` / `SELECTORS["candidate_link"]`，或直接在脚本中调用 API 获取候选人 ID。
3. 完善遍历逻辑：从列表拿到 ID → 打开详情页 → 提取姓名、所在城市、工作经历等字段 → 保存结果。
4. 若后续继续对接“猎头协作平台”，需重新设计同步模块（现已删除）。

## 使用说明（简化版）
1. 在 `headhunter_automation/` 下创建 `.env`（可从历史模板复制）：
   ```
   GLLUE_USERNAME=账号
   GLLUE_PASSWORD=密码
   GLLUE_HEADLESS=false
   GLLUE_MAX_CANDIDATES=5
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. 运行脚本：
   ```bash
   python gllue_scraper.py
   ```
   登陆成功后会在 `data/` 下生成 JSON 数据，以及调试用的 HTML/截图。

## 历史记录
- 2025-09：完成谷露 CRM 登录流程，发现列表需要进一步解析；自动化项目暂时搁置。
- 2024-2025：早期版本用于阿里猎头系统（代码已归档）。

如需恢复旧逻辑或继续突破列表抓取，可以参考以上“下一步计划”。
