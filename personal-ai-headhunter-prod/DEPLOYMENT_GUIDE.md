# Personal AI Headhunter - Deployment Guide

## 📋 环境概述

项目现在分为两个独立的环境：

- **开发环境** (`personal-ai-headhunter-dev/`)：用于开发、测试新功能
- **生产环境** (`personal-ai-headhunter-prod/`)：用于日常业务使用
- **Git 仓库** (`personal-ai-headhunter/`)：代码版本控制

## 🚀 快速启动

### 启动开发环境

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter-dev
./start.sh
```

访问：http://localhost:8501

### 启动生产环境

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter-prod
./start.sh
```

访问：http://localhost:8502

### 同时运行两个环境

可以在不同终端窗口同时启动两个环境，它们使用不同的端口和数据库，互不干扰。

## 🔄 代码更新流程

### 1. 在 Git 仓库中开发

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

# 修改代码
# 提交到 Git
git add .
git commit -m "feat: 新功能描述"
git push
```

### 2. 部署到开发环境测试

```bash
# 复制修改的文件到开发环境
cd /Users/lillianliao/notion_rag
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' personal-ai-headhunter/ personal-ai-headhunter-dev/

# 重启开发环境测试
cd personal-ai-headhunter-dev
./start.sh
```

### 3. 测试通过后部署到生产环境

```bash
# 复制到生产环境
cd /Users/lillianliao/notion_rag
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' personal-ai-headhunter/ personal-ai-headhunter-prod/

# 重启生产环境
cd personal-ai-headhunter-prod
./start.sh
```

## 📊 环境对比

| 特性 | 开发环境 | 生产环境 |
|------|---------|---------|
| 目录 | `personal-ai-headhunter-dev/` | `personal-ai-headhunter-prod/` |
| 端口 | 8501 | 8502 |
| 数据库 | `data/headhunter.db` (测试数据) | `data/headhunter.db` (真实数据) |
| 用途 | 开发、测试 | 日常业务 |
| 数据重要性 | 低 - 可随时清理 | 高 - 需要备份 |

## ⚠️ 注意事项

### 数据安全

- **生产环境数据很重要**：定期备份 `personal-ai-headhunter-prod/data/`
- **开发环境可以随意测试**：不用担心破坏数据

### 数据库迁移

如果代码更新涉及数据库结构变更：

```bash
# 在生产环境执行迁移
cd /Users/lillianliao/notion_rag/personal-ai-headhunter-prod
python migrate_db.py
```

### 端口冲突

如果端口被占用：

```bash
# 查看端口占用
lsof -i :8501
lsof -i :8502

# 杀死进程
kill -9 <PID>
```

## 🛠️ 快速命令参考

```bash
# 更新开发环境
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' personal-ai-headhunter/ personal-ai-headhunter-dev/

# 更新生产环境
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' personal-ai-headhunter/ personal-ai-headhunter-prod/

# 备份生产数据
cp -r personal-ai-headhunter-prod/data/ personal-ai-headhunter-prod/data-backup-$(date +%Y%m%d)/
```

## 📁 目录结构

```
notion_rag/
├── personal-ai-headhunter/          # Git 仓库 (代码源)
│   ├── .git/
│   ├── app.py
│   └── ...
│
├── personal-ai-headhunter-dev/      # 开发环境
│   ├── app.py
│   ├── data/headhunter.db          # 开发数据库
│   ├── .env                         # 开发配置
│   └── start.sh                     # 启动脚本 (端口 8501)
│
└── personal-ai-headhunter-prod/     # 生产环境
    ├── app.py
    ├── data/headhunter.db          # 生产数据库
    ├── .env                         # 生产配置
    └── start.sh                     # 启动脚本 (端口 8502)
```
