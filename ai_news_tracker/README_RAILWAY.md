# 🚀 Railway快速部署

## 一键部署

```bash
./deploy_to_railway.sh
```

## 手动部署

### 1. 安装Railway CLI

```bash
npm install -g @railway/cli
```

### 2. 登录

```bash
railway login
```

### 3. 初始化项目

```bash
railway init
```

### 4. 配置环境变量

```bash
railway variables set OPENAI_API_KEY=sk-4e2bb9108e1541f9b7dd88855922c7a3
railway variables set OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
railway variables set CLASSIFY_MODEL=qwen-max
railway variables set SUMMARY_MODEL=qwen-plus
railway variables set GENERATE_MODEL=qwen-max
```

### 5. 添加数据库

```bash
railway add postgresql
```

### 6. 部署

```bash
railway up
```

## 部署后

### 查看项目URL

```bash
railway domain
```

### 查看日志

```bash
railway logs
```

### 打开项目

```bash
railway open
```

## 文件说明

- **railway.json** - Railway配置文件
- **deploy_to_railway.sh** - 自动部署脚本
- **RAILWAY_DEPLOYMENT_GUIDE.md** - 详细部署指南

## 部署URL示例

部署成功后，你会得到类似这样的URL：
```
https://ai-news-tracker.up.railway.app
```

## 常用命令

```bash
# 查看服务状态
railway status

# 查看环境变量
railway variables

# 重新部署
railway up

# 查看构建日志
railway logs --build

# 查看运行日志
railway logs --running
```

## 故障排查

### 构建失败
检查 `backend/requirements.txt` 是否包含所有依赖

### 数据库连接失败
等待1-2分钟让数据库完全启动

### API 404错误
检查 `railway.json` 中的 `startCommand` 是否正确

## 更多信息

查看详细部署指南: [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md)
