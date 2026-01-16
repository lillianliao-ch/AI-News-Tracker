# 🚀 AI News Tracker - 部署脚本生成完成

## ✅ 已创建的文件

### 1. **railway.json** - Railway配置文件
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

### 2. **deploy_to_railway.sh** - 自动部署脚本（可执行）
```bash
#!/bin/bash
# 一键部署到Railway
./deploy_to_railway.sh
```

**功能**:
- ✅ 自动检查环境
- ✅ 安装Railway CLI
- ✅ 配置项目
- ✅ 设置环境变量
- ✅ 添加PostgreSQL数据库
- ✅ 部署到Railway

### 3. **Dockerfile** - Docker镜像配置
用于Railway、Docker Hub等平台部署

### 4. **docker-compose.yml** - Docker Compose配置
用于本地Docker部署或自托管

**服务**:
- backend: FastAPI后端 (端口8000)
- postgres: PostgreSQL数据库 (端口5432)
- frontend: Astro前端 (端口4321，可选)

### 5. **.env.railway.example** - 环境变量示例
需要配置的关键变量：
- OPENAI_API_KEY
- OPENAI_BASE_URL
- DATABASE_URL (Railway自动提供)
- MODEL配置

### 6. **RAILWAY_DEPLOYMENT_GUIDE.md** - 详细部署指南
包含：
- 前置准备
- 部署步骤（方式一：GitHub，方式二：CLI）
- 配置说明
- 故障排查
- 成本估算

### 7. **README_RAILWAY.md** - Railway快速部署指南
快速开始指南

## 🎯 快速开始

### 方式一：自动部署（推荐）

```bash
cd /Users/lillianliao/notion_rag/ai_news_tracker
./deploy_to_railway.sh
```

### 方式二：手动部署

```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录
railway login

# 3. 初始化
railway init

# 4. 配置环境变量
railway variables set OPENAI_API_KEY=sk-4e2bb9108e1541f9b7dd88855922c7a3
railway variables set OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 5. 添加数据库
railway add postgresql

# 6. 部署
railway up
```

### 方式三：GitHub部署（最简单）

1. 访问 https://railway.app/new
2. 点击 "Deploy from GitHub repo"
3. 选择 `lillianliao-ch/AI-News-Tracker`
4. 配置环境变量
5. 点击 Deploy

## 📊 部署架构

```
┌─────────────────────────────────────┐
│         Railway Platform             │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │   FastAPI Backend           │   │
│  │   - Python 3.12             │   │
│  │   - Port: $PORT             │   │
│  │   - Auto-scaling            │   │
│  └──────────┬───────────────────┘   │
│             │                        │
│             ▼                        │
│  ┌──────────────────────────────┐   │
│  │   PostgreSQL Database       │   │
│  │   - Managed by Railway       │   │
│  │   - Auto backups            │   │
│  └──────────────────────────────┘   │
│                                     │
│  Environment Variables:              │
│  - OPENAI_API_KEY                   │
│  - OPENAI_BASE_URL                  │
│  - DATABASE_URL (auto)              │
└─────────────────────────────────────┘
```

## 🔧 配置说明

### Railway自动配置

Railway会自动：
- ✅ 检测Python项目
- ✅ 安装依赖 (requirements.txt)
- ✅ 分配PORT
- ✅ 提供DATABASE_URL
- ✅ 健康检查
- ✅ 自动重启

### 手动配置

需要在Railway控制台配置：
- OPENAI_API_KEY
- OPENAI_BASE_URL
- CLASSIFY_MODEL
- SUMMARY_MODEL
- GENERATE_MODEL

## 📱 部署后

### 访问应用

部署成功后，Railway会提供一个URL：
```
https://your-app-name.up.railway.app
```

### 测试API

```bash
# 健康检查
curl https://your-app.up.railway.app/health

# 获取新闻
curl https://your-app.up.railway.app/api/news?limit=10

# 触发爬虫
curl -X POST https://your-app.up.railway.app/api/crawl
```

### 查看日志

```bash
# CLI方式
railway logs

# 或访问Railway控制台
https://railway.app
```

## 💰 成本估算

### 免费额度
- ✅ $5/月免费额度
- ✅ 512MB RAM
- ✅ 1GB 存储
- ✅ 无限项目

### 付费计划
- 💳 $20/月起
- 💳 更多资源
- 💳 优先支持

### 预估用量
- 轻量使用：免费额度足够
- 中等使用：$5-10/月
- 重度使用：$20+/月

## 🛠️ 故障排查

### 常见问题

1. **构建失败**
   - 检查 requirements.txt
   - 查看构建日志

2. **数据库连接失败**
   - 等待1-2分钟让数据库启动
   - 检查DATABASE_URL

3. **API返回404**
   - 检查startCommand配置
   - 查看应用日志

4. **内存不足**
   - 升级到付费计划
   - 优化代码

### 调试命令

```bash
# 查看详细日志
railway logs --verbose

# 查看构建日志
railway logs --build

# 查看服务状态
railway status

# 重新部署
railway up --detach
```

## 📚 参考资源

- **Railway官方文档**: https://docs.railway.app/
- **Railway CLI**: https://github.com/railwayapp/cli
- **Python部署**: https://docs.railway.app/deploying/deploying-a-python-service/
- **环境变量**: https://docs.railway.app/develop/variables/

## ✅ 部署检查清单

部署前检查：
- [ ] 代码已推送到GitHub
- [ ] requirements.txt包含所有依赖
- [ ] railway.json配置正确
- [ ] 环境变量已准备

部署后验证：
- [ ] 应用启动成功
- [ ] 健康检查通过
- [ ] API正常响应
- [ ] 数据库连接正常
- [ ] 日志无错误

## 🎉 部署成功！

部署成功后，你会得到：
- ✅ 一个公网URL
- ✅ 自动HTTPS
- ✅ 自动扩容
- ✅ 数据库自动备份
- ✅ 实时日志监控
- ✅ 健康检查

## 📞 支持

遇到问题？
1. 查看 [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md)
2. 访问 Railway官方文档
3. 查看 Railway控制台日志

---

**创建时间**: 2026-01-14 16:20
**部署平台**: Railway
**状态**: ✅ 准备就绪
**下一步**: 运行 `./deploy_to_railway.sh` 开始部署
