# 🚀 AI News Tracker - 快速启动指南

## ✅ 项目已完全启动！

当前服务状态：
- ✅ **前端界面**: http://localhost:4321
- ✅ **后端API**: http://localhost:8000
- ✅ **API文档**: http://localhost:8000/docs

---

## 📋 启动方式

### 方式1: 一键启动（推荐）

**macOS/Linux:**
```bash
cd /Users/lillianliao/notion_rag/ai_news_tracker
./start.sh
```

**Windows:**
```cmd
cd \path\to\ai_news_tracker
start-all.bat
```

这个脚本会自动启动前端和后端。

### 方式2: 分别启动

**启动后端API (端口8000):**
```bash
cd backend
./start_local.sh        # macOS/Linux
# 或
start_local.bat         # Windows
```

**启动前端界面 (端口4321):**
```bash
cd frontend
./start.sh              # macOS/Linux
# 或
start.bat               # Windows
```

---

## 📍 访问地址

- **前端界面**: http://localhost:4321
  - 这是主要的用户界面
  - 可以浏览资讯、筛选、生成内容

- **后端API**: http://localhost:8000
  - API基础地址
  - 健康检查: http://localhost:8000/health

- **API文档**: http://localhost:8000/docs
  - Swagger UI界面
  - 可以在线测试所有API

---

## 🛑 停止服务

### 如果使用一键启动
按 `Ctrl+C` 即可自动停止所有服务

### 如果分别启动
```bash
# 停止后端
kill $(cat /tmp/ai-news-tracker-backend.pid)

# 停止前端
kill $(cat /tmp/ai-news-tracker-frontend.pid)

# 或查找端口
lsof -ti:8000 | xargs kill -9  # 后端
lsof -ti:4321 | xargs kill -9  # 前端
```

---

## 📊 项目结构

```
ai_news_tracker/
├── backend/              # 后端API (FastAPI)
│   ├── start_local.sh    # 后端启动脚本
│   ├── start_local.bat   # Windows启动脚本
│   └── ...
├── frontend/             # 前端界面 (Astro + React)
│   ├── start.sh          # 前端启动脚本
│   ├── start.bat         # Windows启动脚本
│   └── ...
├── start.sh              # 一键启动脚本（推荐）
└── README_START.md       # 本文档
```

---

## 🔧 常见问题

### Q: 前端无法连接后端？
A: 确保后端API已启动在 http://localhost:8000

### Q: 端口被占用？
A: 启动脚本会自动尝试关闭占用端口的进程

### Q: 依赖安装失败？
A:
- 后端: 删除 `backend/venv` 重新运行
- 前端: 删除 `frontend/node_modules` 重新运行

---

## 📝 更多信息

- **完整文档**: [README.md](README.md)
- **Railway部署**: [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md)
- **优化计划**: [plans/add-international-media-and-twitter-integration.md](plans/add-international-media-and-twitter-integration.md)

---

**当前版本**: v0.2.0
**更新内容**:
- ✅ 添加5个国际AI媒体源
- ✅ 支持中英文双语
- ✅ 语言自动检测
- ✅ 完整的启动脚本

**最后更新**: 2026-01-16
