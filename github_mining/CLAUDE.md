# GitHub Mining 项目 — AI 助手必读

> **⚠️ 进入此项目后，第一步必须执行以下命令，没有例外：**

```bash
cat /Users/lillianliao/notion_rag/github_mining/docs/CONVENTIONS.md
```

**不读 CONVENTIONS.md 就动手 = 违规。历史上每次跳过这步都导致了事故。**

---

## 🚨 零号铁律：禁止直接写新脚本

在写任何新脚本/文件之前，必须先检查现有脚本：

```bash
ls /Users/lillianliao/notion_rag/github_mining/scripts/*.sh
ls /Users/lillianliao/notion_rag/github_mining/scripts/*.py
```

**已验证的可复用脚本（优先使用，不要重写）**：

| 任务 | 使用这个 |
|------|---------|
| Serper 联系方式提取 | `run_serper_all_tiers.sh`（改头部变量） |
| 学术管道 | `academic_pipeline.sh --year --phase` |
| GitHub 批次 | `batch_runner.py --input --phases` |
| 进度监控 | `check_pipeline_status.sh` |
| Telegram 通知 | `import telegram_notifier; notify()` |

---

## 📚 核心文档（按需查阅）

| 文档 | 内容 |
|------|------|
| `docs/CONVENTIONS.md` | **脚本规范、缓存命名、目录隔离（必读）** |
| `docs/BATCH_HISTORY.md` | 历史批次记录、经验总结 |
| `docs/academic_sourcing_design.md` | 学术管道完整设计与已验证参数 |
| `docs/TASK.md` | 当前任务进度 |

---

## ⚠️ 高频错误（已发生，禁止重犯）

- ❌ 跳过 `detect_nationality`，用弱版 `is_likely_chinese` 过滤
- ❌ 先跑 PDF，后跑 Serper（应该反过来，Serper 贡献 95% 邮箱）
- ❌ 有现有脚本的情况下写新脚本（见零号铁律）
- ❌ 不读文档直接执行（违反本文件第一条）
