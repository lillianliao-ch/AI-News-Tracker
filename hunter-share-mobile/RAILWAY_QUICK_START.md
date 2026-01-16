# Railway 快速部署指南

根据你的截图，这是当前状态下的快速部署步骤：

## 🎯 当前状态分析

Railway已经成功：
- ✅ 连接到你的GitHub仓库
- ✅ 识别到项目结构
- ✅ 准备好部署配置

## 🚀 具体部署步骤

### 1. 在Railway控制台操作

#### 选择部署类型
在看到的项目选择界面：
- 选择 **"Deploy from GitHub repo"**
- 找到并选择 `lillianliao-ch/Headhunter-MobileInfor` 仓库

#### 部署配置
Railway会自动检测到多个服务：

**选项A: 分别部署（推荐）**
1. **先部署后端**：
   - Root: `backend/`
   - Build: `npm run build && npm run db:generate`
   - Start: `npm start`

2. **添加数据库**：
   - 点击 "+ New Service"
   - 选择 "Database" → "PostgreSQL"
   
3. **部署前端**：
   - Root: `frontend/`
   - Build: `npm run build`
   - Start: `npm start`

**选项B: 整体部署（快速）**
- Root: `/` (项目根目录)
- 使用现有的 `docker-compose.yml`
- Railway会自动识别Docker配置

### 2. 环境变量配置

#### 后端服务
点击后端服务 → Variables → Add Variable:

```bash
NODE_ENV=production
PORT=3001
JWT_SECRET=railway-production-jwt-secret-2024
API_SECRET=railway-api-secret-key-2024
LOG_LEVEL=info
```

#### 前端服务
```bash
NEXT_PUBLIC_API_URL=https://your-backend-service.railway.app
NEXT_PUBLIC_APP_NAME=猎头协作
NEXT_PUBLIC_APP_URL=https://your-frontend-service.railway.app
NODE_ENV=production
```

### 3. 数据库连接

Railway会自动提供 `DATABASE_URL`：
- 在PostgreSQL服务中查看
- 会自动添加到后端服务的环境变量

### 4. 域名和访问

#### 自动生成域名
- 部署完成后，Railway会自动生成域名
- 格式: `https://xxx.railway.app`

#### 自定义域名（可选）
- Settings → Networking → Custom Domain
- 添加你自己的域名

## 🔍 验证部署

### 检查服务状态
1. 在Railway控制台查看服务状态
2. 确认所有服务都是 "Running" 状态
3. 查看日志确认没有错误

### 访问应用
1. **前端**: 点击生成的域名
2. **后端API**: `https://your-backend.railway.app/health`
3. **数据库**: 使用Prisma Studio连接

## 🐛 常见问题解决

### 1. 构建失败
**问题**: 部署时出现构建错误

**解决方案**:
- 检查 `package.json` 中的脚本
- 确保所有依赖都在依赖列表中
- 查看Railway构建日志

### 2. 数据库连接错误
**问题**: 后端无法连接数据库

**解决方案**:
- 确认PostgreSQL服务正在运行
- 检查 `DATABASE_URL` 环境变量
- 运行数据库迁移

### 3. API调用失败
**问题**: 前端无法调用后端API

**解决方案**:
- 更新前端的 `NEXT_PUBLIC_API_URL`
- 检查后端CORS配置
- 确认后端服务正在运行

## 📱 部署后测试

1. **基础功能测试**
   - 访问前端页面
   - 尝试用户注册/登录
   - 创建一个测试帖子

2. **API健康检查**
   ```bash
   curl https://your-backend.railway.app/health
   ```

3. **数据库检查**
   - 在Railway控制台查看数据库状态
   - 确认表结构正确创建

## 🎉 完成部署

部署成功后，你将拥有：
- 🌐 生产级的应用URL
- 📊 实时监控和日志
- 🔄 自动持续部署
- 🔒 SSL安全证书
- 📈 可扩展的基础设施

## 📞 获取帮助

如果遇到问题：
1. 查看Railway文档: https://docs.railway.app
2. 检查项目中的 `RAILWAY_DEPLOYMENT.md`
3. 查看Railway控制台的日志
4. 联系Railway支持团队

## 💡 专业提示

1. **先部署后端和数据库**，确认API工作正常
2. **再部署前端**，配置正确的API地址
3. **使用Railway的环境变量**，不要硬编码敏感信息
4. **设置监控告警**，及时了解服务状态
5. **定期检查日志**，发现潜在问题

按照这个指南，你的应用应该在10-15分钟内完成部署并上线！