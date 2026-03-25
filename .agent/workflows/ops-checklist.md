---
description: 高危操作前置检查清单 — git提交、DB操作、Pipeline执行，必须先验证环境
---

# 高危操作前置检查清单

> 以下每类操作执行前，**必须先跑对应的验证命令**，确认环境正确后再执行。

---

## 1. Git 提交

**提交前必须确认仓库归属：**

```bash
# Step 1: 确认当前目录属于哪个 git 仓库
git rev-parse --show-toplevel

# Step 2: 确认远程仓库
git remote -v
```

**本项目已知 git 仓库（嵌套结构，极易搞混）：**

| 路径 | 仓库说明 |
|------|----------|
| `/Users/lillianliao/notion_rag/` | 父仓库（AI猎头系统整体） |
| `/Users/lillianliao/notion_rag/github_mining/` | 独立子仓库（GitHub挖掘专项） |

> ⚠️ `github_mining/` 有自己的 `.git`，不归父仓库管理。提交 github_mining 的文件必须 `cd github_mining` 再 commit。

**正确流程：**
```bash
cd /Users/lillianliao/notion_rag/github_mining
git rev-parse --show-toplevel   # 应输出 .../github_mining
git add -A -- ':!*.db' ':!*.json' ':!*.csv' ':!*.log' ':!data/'
git commit -m "..."
```

---

## 2. 数据库操作

**操作前必须确认 DB 路径：**

```bash
# 正确的 DB 路径
DB_PATH=/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db

# 验证：必须 cd 进 personal-ai-headhunter 目录
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 -c "from database import SessionLocal; s=SessionLocal(); print('✅ DB OK')"
```

> ⚠️ 如果不在 `personal-ai-headhunter` 目录下运行，会在当前目录生成影子 DB。

---

## 3. GitHub Mining Pipeline 执行

**执行前必须先阅读 `batch_runner.py` 开头的「给 AI 的强制规范」注释（第 25-57 行）：**

```bash
head -60 /Users/lillianliao/notion_rag/github_mining/scripts/batch_runner.py
```

**标准命令：**
```bash
cd /Users/lillianliao/notion_rag/github_mining/scripts
python3 batch_runner.py \
  --input <数据源产出.json> \
  --phases prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update \
  --batch-name "<批次名称>"
```

> ❌ 禁止另写独立脚本替代 batch_runner.py 的过滤/富化/入库步骤。
