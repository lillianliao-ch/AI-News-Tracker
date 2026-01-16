# 🚀 AI News Tracker - Railway 部署指南

## 📋 部署前准备

### 1. Railway 账号
- 访问 https://railway.app/
- 注册或登录账号
- 确认已验证邮箱

### 2. GitHub 仓库
- 代码已推送至: https://github.com/lillianliao-ch/AI-News-Tracker
- 确认最新提交: `22f15906` - "feat: Add international AI media sources and multi-language support"

---

## 🔧 Railway 环境变量配置

### ⚙️ 必须设置的环境变量

在 Railway 项目的 **Variables** 标签页中添加以下变量：

#### 1. API Keys（必需 - 至少设置一个）

```bash
# 选项A: 使用千问API（推荐，稳定且免费额度大）
OPENAI_API_KEY=sk-your-qwen-api-key-here
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 选项B: 使用OpenAI官方API
OPENAI_API_KEY=sk-proj-your-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# 选项C: 使用Anthropic Claude（可选）
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

**如何获取API Key:**

**千问（阿里云）:**
1. 访问 https://dashscope.aliyun.com/
2. 登录阿里云账号
3. 进入 "API-KEY管理"
4. 创建新的API Key
5. 复制API Key（格式: `sk-xxxxxxxxxxxxxxxxxxxxxxxx`）

**OpenAI:**
1. 访问 https://platform.openai.com/api-keys
2. 登录并创建新的API Key
3. 复制API Key（格式: `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx`）

**Anthropic:**
1. 访问 https://console.anthropic.com/
2. 进入 "API Keys"
3. 创建新的API Key
4. 复制API Key（格式: `sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx`）

#### 2. 数据库配置（使用Railway PostgreSQL）

```bash
# Railway会自动提供 DATABASE_URL（PostgreSQL）
# 格式: postgresql://postgres:xxx@xxx.railway.app/xxx
# 无需手动设置
```

**或者使用SQLite（简单但性能较低）:**
```bash
DATABASE_URL=sqlite:///./data/ai_news.db
```

#### 3. AI模型配置

```bash
# 使用千问模型
CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max

# 或使用OpenAI模型
CLASSIFY_MODEL=gpt-4o-mini
SUMMARY_MODEL=gpt-4o-mini
GENERATE_MODEL=gpt-4o
```

#### 4. 应用配置

```bash
# 应用端口（Railway自动分配，可选设置）
PORT=8000

# 日志级别
LOG_LEVEL=INFO

# 调试模式（生产环境建议关闭）
DEBUG=false
```

---

## 📝 完整环境变量列表（推荐配置）

复制以下内容到 Railway Variables：

```bash
# ==================== API Keys ====================
OPENAI_API_KEY=sk-your-qwen-api-key-here
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ANTHROPIC_API_KEY=

# ==================== Database ====================
DATABASE_URL=postgresql://postgres:${{Postgres.PASSWORD}}@${{Postgres.HOST}}:5432/${{Postgres.DATABASE}}
# 如果使用SQLite:
# DATABASE_URL=sqlite:///./data/ai_news.db

# ==================== Cache ====================
ENABLE_CACHE=true
CACHE_TTL=1800

# ==================== Crawler ====================
CRAWL_INTERVAL=7200
MIN_REQUEST_INTERVAL=2.0
MAX_RETRIES=3

# ==================== AI Models ====================
CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max

# ==================== Logging ====================
LOG_LEVEL=INFO
LOG_FILE=ai_news_tracker.log

# ==================== Application ====================
PORT=8000
FRONTEND_URL=
DEBUG=false
```

**注意:** 如果使用Railway PostgreSQL，`${{Postgres.PASSWORD}}` 等变量会自动替换。

---

## 🚀 部署步骤

### 步骤 1: 在Railway创建新项目

1. 登录 Railway: https://railway.app/
2. 点击 **"New Project"**
3. 选择 **"Deploy from GitHub repo"**
4. 选择仓库: `lillianliao-ch/AI-News-Tracker`

### 步骤 2: 配置项目设置

1. **Root Directory**: 设置为 `backend`
   - 点击项目设置
   - 找到 "Root Directory"
   - 输入: `backend`

2. **Start Command**: 设置为
   ```bash
   python start_railway.py
   ```

3. **Healthcheck Path**: 设置为
   ```
   /health
   ```

### 步骤 3: 添加数据库（可选但推荐）

1. 在项目中点击 **"New Service"**
2. 选择 **"Database"**
3. 选择 **"PostgreSQL"**
4. Railway会自动添加 `DATABASE_URL` 环境变量

### 步骤 4: 配置环境变量

1. 点击项目进入 **"Variables"** 标签页
2. 逐个添加上面列出的环境变量
3. **必须设置的变量:**
   - ✅ `OPENAI_API_KEY` - 千问/OpenAI API密钥
   - ✅ `OPENAI_BASE_URL` - API基础URL
   - ✅ `CLASSIFY_MODEL` - 分类模型
   - ✅ `SUMMARY_MODEL` - 摘要模型
   - ✅ `GENERATE_MODEL` - 生成模型

### 步骤 5: 部署

1. 点击 **"Deploy"** 按钮
2. 等待部署完成（通常2-5分钟）
3. Railway会自动：
   - 安装依赖 (pip install)
   - 运行数据库迁移（如果需要）
   - 启动应用
   - 运行健康检查

### 步骤 6: 验证部署

1. 查看 **"Logs"** 标签页，确认没有错误
2. 访问部署成功的URL
3. 测试健康检查端点:
   ```bash
   curl https://your-app.railway.app/health
   ```

   应该返回:
   ```json
   {
     "status": "healthy",
     "service": "ai-news-tracker",
     "version": "0.1.0"
   }
   ```

4. 测试API:
   ```bash
   curl https://your-app.railway.app/api/news?limit=5
   ```

---

## ⚠️ 常见问题排查

### 问题1: 部署失败 - "Missing OPENAI_API_KEY"

**解决方法:**
- 确认在Railway Variables中设置了 `OPENAI_API_KEY`
- 确认API Key格式正确（`sk-` 开头）
- 保存后点击 **"Redeploy"**

### 问题2: 数据库连接失败

**解决方法:**
- 如果使用Railway PostgreSQL:
  - 确认数据库服务正在运行
  - 确认 `DATABASE_URL` 使用Railway自动生成的变量

- 如果使用SQLite:
  - 设置 `DATABASE_URL=sqlite:///./data/ai_news.db`
  - Railway会自动创建 `data` 目录

### 问题3: 爬虫无法获取数据

**解决方法:**
- 检查日志确认具体哪个数据源失败
- 部分数据源可能需要魔法访问（Railway服务器在国外，应该没问题）
- 查看是否有网络超时错误

### 问题4: 健康检查失败

**解决方法:**
- 确认 `/health` 端点存在
- 确认 `start_railway.py` 启动脚本正确
- 查看应用日志确认启动成功

---

## 🔍 监控和日志

### 查看日志

1. 进入项目 **"Logs"** 标签页
2. 可以看到实时日志输出
3. 关键日志:
   - `✅ 数据库初始化成功` - 数据库连接正常
   - `Application startup complete` - 应用启动成功
   - `成功爬取 XX 新闻` - 爬虫运行正常

### 查看指标

1. 进入项目 **"Metrics"** 标签页
2. 可以查看:
   - CPU使用率
   - 内存使用
   - 网络流量
   - 请求响应时间

---

## 📊 部署后验证清单

部署完成后，请验证以下功能：

- [ ] ✅ 健康检查端点返回正常: `/health`
- [ ] ✅ API可以获取新闻列表: `/api/news`
- [ ] ✅ 可以按语言筛选: `/api/news?language=en`
- [ ] ✅ 日志显示爬虫成功运行
- [ ] ✅ 国际媒体源成功获取数据
- [ ] ✅ 数据库正常存储数据

---

## 🎯 下一步

部署成功后，你可以：

1. **设置定时爬虫** - 在Railway中添加Cron Job或手动触发
2. **监控数据源** - 查看日志确认所有9个数据源正常工作
3. **测试API** - 使用Postman或curl测试各个接口
4. **配置前端** - 部署前端应用并连接到后端API

---

## 📞 获取帮助

如果遇到问题:

1. 查看 [Railway Docs](https://docs.railway.app/)
2. 查看 [GitHub Issues](https://github.com/lillianliao-ch/AI-News-Tracker/issues)
3. 检查应用日志获取详细错误信息

---

**创建时间**: 2026-01-14
**最后更新**: 2026-01-14
**部署版本**: commit 22f15906
