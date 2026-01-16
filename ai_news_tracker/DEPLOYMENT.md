# 部署指南 - AI News Tracker

本文档提供 AI News Tracker 系统的完整部署指南，包括开发环境、生产环境和常见问题排查。

## 📋 目录

- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [环境变量配置](#环境变量配置)
- [数据库管理](#数据库管理)
- [常见问题排查](#常见问题排查)

---

## 开发环境部署

### 前置要求检查

```bash
# 检查 Python 版本（需要 3.9+）
python --version

# 检查 Node.js 版本（需要 18+）
node --version

# 检查 npm 版本
npm --version
```

### 1. 后端部署

#### 步骤 1：创建虚拟环境

```bash
cd ai_news_tracker/backend

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 步骤 2：安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

**依赖列表说明:**
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `sqlalchemy` - ORM
- `aiosqlite` - 异步 SQLite
- `feedparser` - RSS 解析
- `openai` - OpenAI API
- `anthropic` - Anthropic API
- `loguru` - 日志
- `pydantic` - 数据验证
- `python-dotenv` - 环境变量

#### 步骤 3：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

**必须配置的环境变量:**

```bash
# API Keys（必填）
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx

# 数据库（可选，默认值即可）
DATABASE_URL=sqlite+aiosqlite:///./data/ai_news.db

# 服务端口（可选）
PORT=8000
```

#### 步骤 4：初始化数据库

```bash
# 方式1：使用初始化脚本
python models/init_db.py

# 方式2：让应用自动创建（首次启动时）
# main.py 中已配置自动创建表
```

#### 步骤 5：启动后端服务

```bash
# 开发模式（支持热重载）
python main.py

# 或使用 uvicorn（更灵活）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 后台运行（nohup）
nohup python main.py > backend.log 2>&1 &
```

**验证后端是否正常运行:**

```bash
# 访问根路径
curl http://localhost:8000/

# 访问 API 文档
open http://localhost:8000/docs

# 测试 API
curl http://localhost:8000/api/news?limit=5
```

### 2. 前端部署

#### 步骤 1：安装依赖

```bash
cd ai_news_tracker/frontend

# 使用 npm
npm install

# 或使用 pnpm（推荐，更快）
pnpm install

# 或使用 yarn
yarn install
```

#### 步骤 2：配置环境变量（如需要）

创建 `frontend/.env` 文件：

```bash
# 后端 API 地址
VITE_API_URL=http://localhost:8000
```

#### 步骤 3：启动开发服务器

```bash
# 开发模式
npm run dev

# 访问
open http://localhost:4321
```

**验证前端是否正常运行:**
- 检查页面是否正常加载
- 点击"刷新资讯"按钮，观察是否正常工作
- 打开浏览器开发者工具，检查 Network 请求

---

## 生产环境部署

### 1. 后端生产部署

#### 使用 Gunicorn + Uvicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 启动（4个worker进程）
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

#### 使用 Systemd 服务（Linux）

创建 `/etc/systemd/system/ai-news-tracker.service`:

```ini
[Unit]
Description=AI News Tracker Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/ai_news_tracker/backend
Environment="PATH=/path/to/ai_news_tracker/backend/venv/bin"
ExecStart=/path/to/ai_news_tracker/backend/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
# 重载配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ai-news-tracker

# 开机自启
sudo systemctl enable ai-news-tracker

# 查看状态
sudo systemctl status ai-news-tracker

# 查看日志
sudo journalctl -u ai-news-tracker -f
```

#### 使用 Nginx 反向代理

创建 `/etc/nginx/sites-available/ai-news-tracker`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/ai_news_tracker/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置:

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/ai-news-tracker /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 2. 前端生产部署

#### 构建静态文件

```bash
cd frontend

# 构建
npm run build

# 输出在 dist/ 目录
```

#### 部署到 Vercel

```bash
# 安装 Vercel CLI
npm install -g vercel

# 部署
cd frontend
vercel
```

创建 `vercel.json` 配置:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    {
      "source": "/api/:match*",
      "destination": "https://your-backend-api.com/api/:match*"
    }
  ]
}
```

#### 部署到 Netlify

创建 `netlify.toml`:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/api/*"
  to = "https://your-backend-api.com/api/:splat"
  status = 200
```

#### 部署到 Nginx

```bash
# 构建后，复制 dist/ 目录到 Nginx 根路径
cp -r dist/* /var/www/ai-news-tracker/
```

---

## Docker 部署

### 1. 后端 Dockerfile

创建 `backend/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 前端 Dockerfile

创建 `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源码
COPY . .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置（如需要）
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3. Docker Compose

创建项目根目录的 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: ai-news-backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=sqlite+aiosqlite:///./data/ai_news.db
    volumes:
      - ./backend/data:/app/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: ai-news-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

启动:

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 环境变量配置

### 完整的环境变量列表

创建 `backend/.env`:

```bash
# ==================== API Keys ====================
# OpenAI API Key（必填）
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx

# Anthropic API Key（必填）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx

# ==================== Database ====================
# 数据库连接字符串
DATABASE_URL=sqlite+aiosqlite:///./data/ai_news.db

# ==================== Cache ====================
# 是否启用缓存
ENABLE_CACHE=true
# 缓存过期时间（秒），默认30分钟
CACHE_TTL=1800

# ==================== Crawler ====================
# 爬取间隔（秒），默认2小时
CRAWL_INTERVAL=7200
# 最小请求间隔（秒），防止被封
MIN_REQUEST_INTERVAL=2.0
# 最大重试次数
MAX_RETRIES=3

# ==================== AI Models ====================
# 分类模型（推荐使用便宜的模型）
CLASSIFY_MODEL=gpt-4o-mini

# 摘要模型
SUMMARY_MODEL=claude-3-5-sonnet-20241022

# 生成模型
GENERATE_MODEL=claude-3-5-sonnet-20241022

# ==================== Logging ====================
# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
# 日志文件路径
LOG_FILE=ai_news_tracker.log

# ==================== Application ====================
# 应用端口
PORT=8000
# 前端地址（用于 CORS）
FRONTEND_URL=http://localhost:4321
# 是否启用调试模式
DEBUG=false
```

### 安全注意事项

⚠️ **重要提示:**

1. **永远不要将 `.env` 文件提交到 Git 仓库**
   ```bash
   # .gitignore 应该包含
   .env
   *.log
   data/
   ```

2. **生产环境使用强密码和密钥**
   - 使用随机生成的密钥
   - 定期轮换 API Keys

3. **使用环境变量管理服务**（推荐）
   - [Doppler](https://www.doppler.com/)
   - [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
   - [HashiCorp Vault](https://www.vaultproject.io/)

---

## 数据库管理

### 查看数据库

```bash
# 使用 SQLite 命令行
sqlite3 backend/data/ai_news.db

# 查看所有表
.tables

# 查看表结构
.schema news

# 查询数据
SELECT * FROM news LIMIT 10;

# 退出
.quit
```

### 数据库备份

```bash
# 备份数据库
cp backend/data/ai_news.db backend/data/ai_news_backup_$(date +%Y%m%d).db

# 或使用 SQLite 导出
sqlite3 backend/data/ai_news.db .dump > backup.sql
```

### 数据库迁移（如需要）

```bash
# 使用 Alembic（项目暂未实现，可扩展）
pip install alembic

# 初始化
alembic init migrations

# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

---

## 常见问题排查

### 问题1：后端启动失败

**症状:** `ModuleNotFoundError: No module named 'xxx'`

**解决方案:**
```bash
# 确保虚拟环境已激活
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 重新安装依赖
pip install -r requirements.txt
```

### 问题2：API 调用失败

**症状:** `401 Unauthorized` 或 `Invalid API Key`

**解决方案:**
```bash
# 检查 .env 文件是否正确配置
cat backend/.env | grep API_KEY

# 确保 API Keys 有效
# 测试 OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 测试 Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY"
```

### 问题3：爬虫无法获取数据

**症状:** 爬取数量为 0 或报错

**解决方案:**
```bash
# 检查网络连接
curl https://36kr.com/feed

# 检查数据源配置
cat backend/config/base_config.py | grep rss_url

# 查看爬虫日志
tail -f backend/ai_news_tracker.log

# 手动测试爬虫
cd backend
python -c "
import asyncio
from sources.base import SourceFactory
from config.base_config import SOURCES_CONFIG

async def test():
    sources = SourceFactory.create_all_sources(SOURCES_CONFIG)
    for source in sources:
        if source.enabled:
            items = await source.get_data()
            print(f'{source.name}: {len(items)} items')

asyncio.run(test())
"
```

### 问题4：前端无法连接后端

**症状:** `Network Error` 或 `CORS Error`

**解决方案:**
```bash
# 检查后端是否运行
curl http://localhost:8000/

# 检查 CORS 配置（main.py）
# 确保 allow_origins 包含前端地址

# 如果使用不同的域名/端口，更新 .env
VITE_API_URL=http://your-backend-url.com
```

### 问题5：数据库锁定

**症状:** `sqlite3.OperationalError: database is locked`

**解决方案:**
```bash
# 确保只有一个进程在写入数据库
ps aux | grep python

# 检查数据库文件权限
ls -la backend/data/ai_news.db

# 如果有锁文件，删除它
rm backend/data/ai_news.db-wal
rm backend/data/ai_news.db-shm
```

### 问题6：内存不足

**症状:** 系统变慢或 OOM (Out of Memory)

**解决方案:**
```bash
# 检查内存使用
free -h  # Linux
# 或
top  # macOS/Linux

# 减少并发数
# 编辑 backend/tasks/crawler.py
# 限制每次爬取的数量

# 定期清理旧数据
sqlite3 backend/data/ai_news.db "DELETE FROM news WHERE crawl_time < datetime('now', '-30 days');"
```

---

## 监控和日志

### 查看日志

```bash
# 实时查看日志
tail -f backend/ai_news_tracker.log

# 查看最近100行
tail -n 100 backend/ai_news_tracker.log

# 搜索错误
grep ERROR backend/ai_news_tracker.log
```

### 性能监控

```bash
# 使用 Python profiler
pip install scalene

# 运行分析
scalene main.py
```

### API 健康检查

创建健康检查脚本 `health_check.sh`:

```bash
#!/bin/bash

# 检查后端
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ $response -eq 200 ]; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is down (HTTP $response)"
    # 发送告警（如需要）
fi

# 检查数据库
if [ -f backend/data/ai_news.db ]; then
    echo "✅ Database exists"
else
    echo "❌ Database not found"
fi
```

---

## 更新和维护

### 更新依赖

```bash
# 后端
cd backend
pip install --upgrade -r requirements.txt

# 前端
cd frontend
npm update
```

### 数据备份策略

```bash
# 创建备份脚本 backup.sh
#!/bin/bash

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
cp backend/data/ai_news.db $BACKUP_DIR/ai_news_$DATE.db

# 保留最近7天的备份
find $BACKUP_DIR -name "ai_news_*.db" -mtime +7 -delete
```

添加到 crontab:
```bash
# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

---

## 下一步

部署完成后，你可以：

1. **测试完整流程**:
   - 手动触发爬虫
   - 生成小红书内容
   - 测试所有 API 端点

2. **配置定时任务**:
   - 使用 APScheduler 自动爬取
   - 配置数据清理任务

3. **添加监控**:
   - 设置错误告警
   - 配置性能监控

4. **优化性能**:
   - 添加缓存层
   - 优化数据库查询
   - 使用 CDN 加速前端

如有问题，请查看 [GitHub Issues](https://github.com/your-repo/issues) 或提交新的 Issue。
