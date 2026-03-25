# TOOLS.md

> Lumi 的工具环境速查表。事实，不是说明书。

---

## 系统运行状态

| 服务 | 本机地址 | 远程访问（Lumi 从另一台机器） |
|------|---------|--------------------------|
| FastAPI 后端 | http://localhost:8502 | `http://192.168.3.240:8502` |
| React 前端 | http://localhost:5173 | `http://192.168.3.240:5173` |
| API 文档 | http://localhost:8502/docs | `http://192.168.3.240:8502/docs` |

> API 服务已绑定 `0.0.0.0:8502`，局域网内直接可访问，无需改代码。
> 如果两台机器不在同一局域网，改用 SSH Tunnel：
> `ssh -L 8502:localhost:8502 lillianliao@192.168.3.240`

**CRM Base URL（Lumi 用这个）**：`http://192.168.3.240:8502`


---

## CRM API 端点（Lumi 可调用）

**Base URL**：`http://<Mac-IP>:8502`

### 候选人（只读）
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/candidates` | 候选人列表（支持筛选/分页） |
| GET | `/api/candidate/{id}` | 候选人详情 |
| GET | `/api/candidate/lookup-by-url` | 按 LinkedIn/GitHub URL 查找 |
| GET | `/api/candidate/{id}/emails` | 候选人邮件历史 |

### 候选人（写操作，需 Telegram 确认）
| 方法 | 端点 | 说明 |
|------|------|------|
| PUT | `/api/candidate/{id}` | 更新候选人信息 |
| POST | `/api/candidate/manual-add` | 手动添加候选人 |
| POST | `/api/candidate/maimai-sync` | 脉脉数据同步 |
| POST | `/api/candidate/{id}/re-tier` | 重新评级 |
| PATCH | `/api/candidate/{id}/schedule` | 更新跟进日期/pipeline 阶段 |
| POST | `/api/candidate/{id}/match-jobs` | 匹配候选人与职位 |
| POST | `/api/candidate/{id}/emails/generate` | 生成邮件草稿 |

### 职位
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/jobs` | 职位列表 |
| GET | `/api/jobs/active` | 活跃职位 |
| GET | `/api/jobs/search` | 搜索职位 |
| GET | `/api/jobs/{id}` | 职位详情 |
| GET | `/api/jobs/{id}/recommendations` | 职位推荐候选人 |
| GET | `/api/jobs/{id}/maimai-form` | 脉脉发布表单数据 |
| POST | `/api/jobs/{id}/publish` | 发布职位（触发脉脉发布流程） |

### 统计与分析（直接可用）
> 这些端点 Lumi 可以用来生成每日简报，无需确认

查询参数示例：
```
GET /api/candidates?talent_tier=S&pipeline_stage=contacted&limit=20
GET /api/jobs?is_active=true&urgency=3
```

---

## 数据库

```bash
sqlite3 /Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db
```

**核心表**：candidates / jobs / outreach_records / batch_runs

默认只读，写操作需 Telegram 确认。

---

## 浏览器自动化（Playwright + Chrome Profile）

```python
# 挂载已登录的 Chrome（保留 Cookie + 扩展）
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA = "/Users/lillianliao/Library/Application Support/Google/Chrome"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA,
        executable_path=CHROME_PATH,
        headless=False,  # 有头模式，可观察
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
```

> 这样打开的浏览器带有 Lilian 的登录状态 + 已安装插件（包括脉脉插件）

---

## Telegram 通知与确认

```python
from telegram_notifier import notify, notify_error, notify_progress
```

确认流程（候选人沟通 / 写操作）：
1. Lumi 生成内容 → `notify()` 推送草稿到 Telegram
2. Lilian 回复"确认" / "ok" / "y" → 执行
3. 其他回复 → 修改重来

---

## Telegram Bot 工具集（10 个）

`search_candidates` / `get_candidate_detail` / `get_daily_stats` / `search_jobs` / `semantic_search_jobs` / `semantic_search_candidates` / `get_outreach_history` / `count_candidates` / `draft_outreach_message` / `send_email`

---

## LinkedIn 发布

**方式 A（推荐）**：LinkedIn API + Buffer / n8n 调度
- LinkedIn 有官方 Posts API（需 OAuth）
- Buffer 支持定时发布，合规

**方式 B**：Playwright 操控浏览器（已登录 Chrome）

---

## 小红书发布

**当前路径（半自动）**：
1. Lumi 生成图文文案
2. Playwright 打开小红书创作者后台（已登录）
3. 自动填写文案，截图预览推给 Lilian 确认
4. 确认后自动点击发布

---

## n8n 工作流（可选，待配置）

本地运行：`docker run -p 5678:5678 n8nio/n8n`  
用于：定时触发任务（每天早报 / 内容发布调度 / ArXiv 监控）

---

## 批量操作脚本（常用）

```bash
python3 batch_match_urgent_jobs.py   # 匹配
python3 batch_linkedin_outreach.py   # LinkedIn 触达
python3 batch_email_outreach.py      # Email 触达
python3 batch_update_tiers.py all    # 评级重跑
python3 daily_planner.py             # 日报
```

---

## AI 服务

```python
# ai_service.py + prompts.py
# 支持 Qwen / DeepSeek / Claude（IMDS.ai / z.ai）
```

---

## 相关项目路径

- GitHub Mining：`/Users/lillianliao/notion_rag/github_mining/`
- AI News Tracker：`/Users/lillianliao/notion_rag/ai_news_tracker/`
- 本 Workspace：`/Users/lillianliao/notion_rag/openclaw-partner/`

---

## ClawHub（Skills 市场）

URL：https://clawhub.ai  
Lumi 每周主动查阅，发现有价值的 skill 推荐安装。
