# 🚀 AI News Tracker - 本地快速启动指南

## ✅ 服务器已成功启动！

服务器已在后台运行，以下是访问信息：

### 📍 访问地址

- **API 基础地址**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 🎯 快速测试

#### 1. 测试健康检查
```bash
curl http://localhost:8000/health
```

#### 2. 获取最新资讯
```bash
# 获取最近5条资讯
curl http://localhost:8000/api/news?limit=5

# 只获取英文资讯
curl "http://localhost:8000/api/news?language=en&limit=5"

# 只获取中文资讯
curl "http://localhost:8000/api/news?language=zh&limit=5"

# 按分类筛选
curl "http://localhost:8000/api/news?category=国际AI新闻&limit=5"

# 按来源筛选
curl "http://localhost:8000/api/news?source=AI+News&limit=5"
```

#### 3. 测试爬虫（手动触发）
```bash
cd backend
python3 -m tasks.crawler
```

---

## 🛠️ 快速启动脚本

我已为你创建了两个快速启动脚本：

### macOS/Linux
```bash
cd backend
./start_local.sh
```

### Windows
```cmd
cd backend
start_local.bat
```

**脚本功能**：
- ✅ 自动检查Python环境
- ✅ 自动创建虚拟环境（如果不存在）
- ✅ 自动安装依赖（首次运行）
- ✅ 自动运行数据库迁移
- ✅ 自动启动服务器

### 稳定模式（推荐）
提供健康检查 + 自动重启：

```bash
cd /Users/lillianliao/notion_rag/ai_news_tracker
./stable_start.sh
```

停止稳定模式：

```bash
cd /Users/lillianliao/notion_rag/ai_news_tracker
./stable_stop.sh
```

日志目录：
`/Users/lillianliao/notion_rag/ai_news_tracker/.runtime/logs`

---

## 📊 当前数据源

### 中文媒体（4个）
1. **量子位** - 10条/次 (AI相关率: 95%)
2. **雷锋网** - 20条/次 (AI相关率: 85%)
3. **钛媒体** - 17条/次 (AI相关率: 100%)
4. **36氪** - 10条/次 (AI相关率: 30%)

### 国际媒体（5个）✨新增
1. **AI News** - 12条/次 (AI相关率: 100%)
2. **TechCrunch AI** - 20条/次 (AI相关率: 67%)
3. **Ars Technica** - 20条/次 (AI相关率: 67%)
4. **MIT Tech Review** - 10条/次 (AI相关率: 33%)
5. **The Verge AI** - 10条/次 (AI相关率: 33%)

### 社区（1个）
1. **Reddit AI** - 25条/次 (AI相关率: 68%)

**总计**: 9个数据源，每次爬取最多144条资讯

---

## 🔧 常用命令

### 启动服务器
```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 运行爬虫
```bash
cd backend
python3 -m tasks.crawler
```

### 测试国际媒体源
```bash
cd backend
python3 test_international_sources.py
```

### 查看数据库
```bash
cd backend
python3 -c "from models.database import SessionLocal, News; db = SessionLocal(); print(f'总资讯数: {db.query(News).count()}'); print(f'中文资讯: {db.query(News).filter(News.language==\"zh\").count()}'); print(f'英文资讯: {db.query(News).filter(News.language==\"en\").count()}')"
```

---

## 🌐 API 使用示例

### Python 示例
```python
import requests

# 获取所有资讯
response = requests.get('http://localhost:8000/api/news?limit=10')
news_list = response.json()

for news in news_list:
    print(f"标题: {news['title']}")
    print(f"来源: {news['source']}")
    print(f"语言: {news.get('language', 'unknown')}")
    print(f"链接: {news['url']}")
    print("-" * 60)
```

### JavaScript/Node.js 示例
```javascript
// 获取所有资讯
const response = await fetch('http://localhost:8000/api/news?limit=10');
const newsList = await response.json();

newsList.forEach(news => {
    console.log(`标题: ${news.title}`);
    console.log(`来源: ${news.source}`);
    console.log(`语言: ${news.language || 'unknown'}`);
    console.log(`链接: ${news.url}`);
    console.log('-'.repeat(60));
});
```

---

## 📝 环境变量配置

编辑 `backend/.env` 文件：

```bash
# API Keys（必需）
OPENAI_API_KEY=sk-your-qwen-api-key-here
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# AI 模型配置
CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max

# 数据库
DATABASE_URL=sqlite:///./data/ai_news.db

# 应用配置
PORT=8000
LOG_LEVEL=INFO
DEBUG=false
```

---

## 🔄 停止服务器

如果服务器在前台运行，按 `Ctrl+C` 停止。

如果在后台运行，查找并关闭进程：
```bash
# 查找进程
lsof -i :8000

# 关闭进程
kill -9 <PID>
```

或使用：
```bash
pkill -f "uvicorn main:app"
```

---

## 🐛 常见问题

### 问题1: 端口被占用
```bash
# 查找占用端口的进程
lsof -i :8000

# 关闭进程
kill -9 <PID>

# 或使用其他端口
python3 -m uvicorn main:app --port 8001
```

### 问题2: 依赖安装失败
```bash
# 重新安装依赖
cd backend
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

### 问题3: 数据库错误
```bash
# 重新运行迁移
cd backend
python3 migrate_add_language.py
```

---

## 📚 更多资源

- **API 文档**: http://localhost:8000/docs
- **项目规划**: [plans/add-international-media-and-twitter-integration.md](plans/add-international-media-and-twitter-integration.md)
- **Railway 部署指南**: [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md)

---

**创建时间**: 2026-01-14
**版本**: v0.2.0 - 国际媒体支持
**当前数据源**: 9个（4中文 + 5国际）
