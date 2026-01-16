# 🎯 AI News Tracker - 项目状态与优化路线图

**更新时间**: 2026-01-16
**当前版本**: v0.2.0
**Git Commit**: 405914e0

---

## 📊 当前项目状态

### ✅ 已完成功能

#### 1. 国际媒体支持（Part 1 - 已实现）
- ✅ 添加5个国际AI媒体源：
  - AI News (12条, 100% AI相关)
  - TechCrunch AI (20条, 67% AI相关)
  - Ars Technica (20条, 67% AI相关)
  - MIT Tech Review (10条, 33% AI相关)
  - The Verge AI (10条, 33% AI相关)
- ✅ 多语言支持（中英文）
- ✅ 自动语言检测
- ✅ 数据库迁移脚本
- ✅ API支持语言筛选

#### 2. 核心功能
- ✅ 9个数据源（4中文 + 5国际）
- ✅ RSS爬虫系统
- ✅ AI内容分类（千问集成）
- ✅ 小红书内容生成
- ✅ FastAPI后端
- ✅ Astro + React前端

#### 3. 部署相关
- ✅ Railway配置文件
- ✅ 健康检查端点 `/health`
- ✅ 完整的启动脚本
- ✅ 环境变量调试功能

### ⏳ 待实现功能

#### Part 2: Twitter集成（优先级：中）
- ⏳ RSSHub部署方案
- ⏳ Twitter API集成
- ⏳ Nitter备用方案
- 📁 详细规划：`plans/add-international-media-and-twitter-integration.md`

---

## 🗂️ 关键文件位置

### 后端核心文件
```
ai_news_tracker/backend/
├── main.py                      # FastAPI主应用 ⭐
├── config/
│   ├── base_config.py          # 数据源配置（包含9个源）⭐
│   └── prompts.py              # AI关键词和提示词
├── models/
│   └── database.py             # 数据库模型（已添加language字段）
├── sources/
│   └── base.py                 # RSS源基类（含语言检测）
├── services/
│   └── ai_service.py           # AI服务（千问集成）
├── tasks/
│   └── crawler.py              # 爬虫任务
├── start_railway.py             # Railway启动脚本（带环境变量调试）
├── start_local.sh              # 本地启动脚本（Linux/Mac）
├── start_local.bat             # 本地启动脚本（Windows）
└── migrate_add_language.py     # 数据库迁移脚本
```

### 前端核心文件
```
ai_news_tracker/frontend/
├── src/                         # Astro源码
├── astro.config.mjs             # Astro配置
├── package.json                 # 前端依赖
├── start.sh                     # 前端启动脚本
└── start.bat                    # Windows启动脚本
```

### 文档
```
ai_news_tracker/
├── README_START.md              # 快速启动指南 ⭐
├── RAILWAY_DEPLOYMENT_GUIDE.md  # Railway部署指南
├── plans/
│   └── add-international-media-and-twitter-integration.md  # 优化规划
└── start.sh                     # 一键启动脚本 ⭐
```

---

## 🔧 当前运行状态

### 服务端口
- **前端**: http://localhost:4321 ✅ 运行中
- **后端API**: http://localhost:8000 ✅ 运行中
- **后台进程ID**:
  - 前端: b86d53c
  - 后端: beeab2b

### 环境配置
- **数据库**: SQLite (`backend/data/ai_news.db`)
- **Python虚拟环境**: `backend/venv/`
- **前端依赖**: `frontend/node_modules/`

---

## 📋 下一步优化任务

### 🔴 高优先级

#### 1. 修复Railway部署环境变量问题
**问题**: Railway环境变量未正确传递到应用

**解决方案**:
1. 在Railway Service级别设置环境变量
2. 使用最新的 `start_railway.py`（带flush输出）
3. 查看Logs验证环境变量是否正确显示

**文件**: `backend/start_railway.py`

**验证命令**:
```bash
# Railway Logs应该显示：
# ============================================================
# 🔍 环境变量检查:
# ============================================================
# 所有环境变量:
#   CLASSIFY_MODEL = qwen-max
#   OPENAI_API_KEY = sk-your-q...
#   OPENAI_BASE_URL = https://dashsc...
#   PORT = 8000
# 总计: XX 个环境变量
# ============================================================
# ✅ OPENAI_API_KEY: sk-your-q...
# ✅ OPENAI_BASE_URL: https://dashsc...
# ✅ CLASSIFY_MODEL: qwen-max
# ============================================================
# ✅ 所有必要的环境变量已设置
# ============================================================
```

#### 2. 完善前端功能
**当前状态**: 前端已启动但有一些Astro警告

**优化方向**:
- 修复Astro组件hydration警告
- 添加语言筛选UI
- 显示数据来源标识
- 添加国际新闻标签

**关键文件**: `frontend/src/`

### 🟡 中优先级

#### 3. 实现Twitter数据获取
**规划文档**: `plans/add-international-media-and-twitter-integration.md`

**推荐方案**: RSSHub自部署
- 成本：免费-$5/月
- 可靠性：高
- 实施难度：中

**实施步骤**:
1. Railway部署RSSHub实例
2. 获取Twitter RSS URL
3. 集成到现有爬虫系统

#### 4. 性能优化
- 添加Redis缓存层
- 实现增量爬取
- 优化数据库查询

### 🟢 低优先级

#### 5. 监控和日志
- 添加Sentry错误追踪
- 实现数据源健康监控
- 添加爬虫统计dashboard

#### 6. 测试
- 单元测试覆盖
- API集成测试
- E2E测试

---

## 🚀 快速恢复工作流程

### Compact后第一步：检查运行状态

```bash
# 1. 检查服务是否运行
curl http://localhost:4321           # 前端
curl http://localhost:8000/health      # 后端

# 2. 如果未运行，一键启动
cd /Users/lillianliao/notion_rag/ai_news_tracker
./start.sh

# 3. 测试API
curl "http://localhost:8000/api/news?language=en&limit=5"
```

### 继续Railway部署

```bash
# 1. 查看最新Railway部署日志
# 在Railway网站 > 项目 > Logs

# 2. 应该看到环境变量调试信息
# 如果看到 "❌ OPENAI_API_KEY: 未设置"
# 说明环境变量在Service级别未正确设置

# 3. 修复步骤：
#    - 点击AI News Tracker service
#    - 进入Settings > Variables
#    - 添加环境变量（见下方配置）

# 4. Railway环境变量配置
OPENAI_API_KEY=sk-your-actual-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max
```

### 继续Twitter集成

```bash
# 1. 查看规划文档
cat ai_news_tracker/plans/add-international-media-and-twitter-integration.md

# 2. 按照规划实施Part 2
# 推荐从RSSHub方案开始

# 3. 测试Twitter源
cd backend
python3 test_twitter_integration.py  # 需要创建
```

---

## 📝 重要配置信息

### 数据源配置文件
`backend/config/base_config.py` 包含所有9个数据源的配置

**关键配置项**:
- `enabled`: 是否启用
- `limit`: 每次爬取数量
- `ai_related_rate`: AI相关率
- `language`: 语言代码（zh/en）

### 数据库Schema
`backend/models/database.py`

**新增字段**:
- `language`: 语言（zh/en）
- `lang_confidence`: 语言检测置信度

### 环境变量模板
`backend/.env.example`

**必需变量**:
- `OPENAI_API_KEY`: 千问/OpenAI API密钥
- `OPENAI_BASE_URL`: API基础URL
- `CLASSIFY_MODEL`: 分类模型名称

---

## 🔍 常用命令

### 本地开发

```bash
# 一键启动
cd ai_news_tracker && ./start.sh

# 只启动后端
cd backend && ./start_local.sh

# 只启动前端
cd frontend && ./start.sh

# 运行爬虫
cd backend
python3 -m tasks.crawler

# 测试国际媒体源
cd backend
python3 test_international_sources.py

# 数据库迁移
cd backend
python3 migrate_add_language.py

# 查看数据库统计
cd backend
python3 -c "
from models.database import SessionLocal, News
db = SessionLocal()
print(f'总数: {db.query(News).count()}')
print(f'中文: {db.query(News).filter(News.language==\"zh\").count()}')
print(f'英文: {db.query(News).filter(News.language==\"en\").count()}')
"
```

### Git操作

```bash
# 查看状态
git status

# 提交更改
git add .
git commit -m "描述"
git push

# 查看最近提交
git log --oneline -5
```

---

## 📊 项目统计

### 代码规模
- **后端**: Python (FastAPI)
- **前端**: Astro + React
- **数据源**: 9个（4中文 + 5国际）
- **API端点**: 6个主要接口

### 依赖关系
- **后端依赖**: 见 `backend/requirements.txt`
- **前端依赖**: 见 `frontend/package.json`
- **Python版本**: 3.10+
- **Node版本**: 18+

---

## 🎯 Compact后继续工作清单

- [ ] 检查Railway部署状态
- [ ] 验证环境变量配置
- [ ] 实现Twitter集成（Part 2）
- [ ] 修复前端Astro警告
- [ ] 添加语言筛选UI
- [ ] 性能优化

---

## 📞 关键信息汇总

### 项目位置
`/Users/lillianliao/notion_rag/ai_news_tracker`

### Git仓库
https://github.com/lillianliao-ch/AI-News-Tracker

### 最新Commit
405914e0 - "feat: Add comprehensive startup scripts for frontend and backend"

### Railway部署
- 项目配置: `railway.json`
- 启动脚本: `backend/start_railway.py`
- 健康检查: `/health`

### 本地服务
- 前端: http://localhost:4321
- 后端: http://localhost:8000
- API文档: http://localhost:8000/docs

---

**文档版本**: v1.0
**最后更新**: 2026-01-16 10:30
**状态**: ✅ 项目运行正常，可以安全compact
