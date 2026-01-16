# 🔧 Railway部署故障排查

## 🚨 问题现象

根据你提供的Deploy Logs，Railway部署失败，错误信息：

```
ERROR - 缺少必要的环境变量：NOTION_TOKEN, NOTION_DATABASE_ID
ERROR - 环境配置检查失败，请先配置必要的环境变量
```

**关键发现**：应用在启动时**立即检查环境变量并失败退出**。

## 🔍 问题分析

### 问题根源

1. **Railway可能缓存了旧的代码或配置**
2. **或者Railway运行了错误的Python文件**
3. **缺少明确的启动脚本**

### 为什么会出现Notion相关错误？

这个项目**完全不使用Notion**，但日志显示有Notion环境变量检查，这说明：
- Railway可能运行了父目录（notion_rag）的其他代码
- 或者缓存了之前的构建

## ✅ 已实施的修复

### 1. 添加健康检查端点

在 `backend/main.py` 中添加：

```python
@app.get("/health")
async def health_check():
    """健康检查端点（用于Railway等平台）"""
    return {
        "status": "healthy",
        "service": "ai-news-tracker",
        "version": "0.1.0"
    }
```

### 2. 创建专用启动脚本

创建 `backend/start_railway.py`：

```python
#!/usr/bin/env python3
"""
Railway启动脚本
确保正确的应用启动
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from main import app

    # 获取Railway分配的端口
    port = int(os.environ.get("PORT", 8000))

    # 启动应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
```

### 3. 更新Railway配置

更新 `backend/railway.json`：

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python start_railway.py",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 4. 已推送到GitHub

✅ Commit: `9ac6de69`
✅ 已推送: `https://github.com/lillianliao-ch/AI-News-Tracker`

## 🚀 重新部署步骤

### 方法一：在Railway控制台重新部署

1. **访问Railway项目**
   - 访问 https://railway.app
   - 选择 `ai-news-tracker` 项目

2. **清除缓存并重新构建**
   - 点击你的服务
   - 点击 "Settings" 标签
   - 找到 "Root Directory" → 确认是 `backend`
   - 返回 "Deployments" 标签
   - 点击 "New Deploy" 或 "Redeploy"
   - **重要**：如果有 "Force Rebuild" 或 "Clear Cache" 选项，点击它

3. **等待新部署**
   - GitHub会自动拉取最新代码
   - Railway会重新构建
   - 等待2-3分钟

4. **验证部署**
   - 查看Deploy Logs
   - 应该看到：
     ```
     INFO:     Started server process [1]
     INFO:     Waiting for application startup.
     INFO:     Application startup complete.
     INFO:     Uvicorn running on port 8000
     ```

### 方法二：使用Railway CLI

```bash
# 重新部署（会自动拉取GitHub最新代码）
cd /Users/lillianliao/notion_rag/ai_news_tracker
railway up --detach
```

## 🧪 验证部署成功

### 1. 检查健康状态

```bash
curl https://ai-news-tracker-production.up.railway.app/health
```

**应该返回**：
```json
{"status":"healthy","service":"ai-news-tracker","version":"0.1.0"}
```

### 2. 访问根路径

```bash
curl https://ai-news-tracker-production.up.railway.app/
```

**应该返回**：
```json
{
  "message": "AI News Tracker API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

### 3. 查看API文档

在浏览器访问：
```
https://ai-news-tracker-production.up.railway.app/docs
```

应该看到FastAPI的Swagger文档界面。

## 📝 环境变量配置

虽然这个项目不需要Notion，但仍然需要配置以下环境变量：

### 必需的环境变量

在Railway的 "Variables" 标签添加：

```env
# OpenAI API配置（千问）
OPENAI_API_KEY=sk-4e2bb9108e1541f9b7dd88855922c7a3
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 模型配置
CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max

# 日志配置
LOG_LEVEL=INFO
DEBUG=false
```

### Railway自动提供的环境变量

- `PORT` - Railway自动分配
- `DATABASE_URL` - 如果添加了PostgreSQL服务

## 🔧 如果还有问题

### 问题1：仍然看到Notion错误

**原因**：Railway缓存了旧构建

**解决**：
1. 在Railway控制台，删除当前服务
2. 重新创建服务，从GitHub部署
3. 确保Root Directory设置为 `backend`

### 问题2：应用启动失败

**检查**：
1. Deploy Logs中的完整错误信息
2. Build Logs中是否有依赖安装失败
3. 环境变量是否全部配置

### 问题3：健康检查失败

**解决**：
1. 确认 `/health` 端点存在（已在main.py中添加）
2. 检查railway.json中的healthcheckPath配置
3. 查看应用日志确认启动成功

## 📊 成功标志

当部署成功时，你应该看到：

### Deploy Logs
```
Starting Container
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on port 8000 (Press CTRL+C to quit)
```

### 应用状态
- Status: **Running** (绿色)
- Health: **Healthy**
- URL可访问

### 访问测试
```bash
$ curl https://ai-news-tracker-production.up.railway.app/health
{"status":"healthy","service":"ai-news-tracker","version":"0.1.0"}
```

## 📚 相关文档

- [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md) - 完整部署指南
- [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) - 部署总结
- [README_RAILWAY.md](./README_RAILWAY.md) - 快速开始

## ✅ 下一步

1. **推送到GitHub**：✅ 已完成
2. **在Railway重新部署**：等待你操作
3. **验证部署**：测试健康检查和API
4. **配置环境变量**：确保所有必需变量已设置
5. **测试爬虫功能**：手动触发爬虫测试

---

**更新时间**: 2026-01-14 17:20
**Commit**: 9ac6de69
**状态**: ✅ 修复已推送到GitHub
**下一步**: 在Railway重新部署并验证
