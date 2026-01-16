# Hunter Share Mobile - Railway 部署指南

## 🚀 部署到 Railway

Railway 是一个现代化的云平台，非常适合部署全栈应用。本指南将帮助你将 Hunter Share Mobile 项目部署到 Railway。

## 📋 前置要求

1. **Railway 账户**
   - 访问 [railway.app](https://railway.app)
   - 注册并登录账户
   - 添加支付方式（免费额度已足够）

2. **GitHub 账户**
   - 项目已推送到 GitHub: https://github.com/lillianliao-ch/Headhunter-MobileInfor

## 🛠️ 部署步骤

### 第一步：部署后端服务

1. **创建新项目**
   - 在 Railway 控制台点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库: `lillianliao-ch/Headhunter-MobileInfor`

2. **配置后端服务**
   - Root Directory: `backend`
   - Build Command: `npm run build && npm run db:generate`
   - Start Command: `npm start`

3. **添加 PostgreSQL 数据库**
   - 在项目中点击 "New Service"
   - 选择 "Database"
   - 选择 "PostgreSQL"
   - Railway 会自动提供 `DATABASE_URL` 环境变量

4. **配置环境变量**
   在后端服务的 "Variables" 标签页添加：
   
   ```bash
   NODE_ENV=production
   PORT=3001
   JWT_SECRET=your-strong-production-jwt-secret-key
   API_SECRET=your-api-secret-key
   LOG_LEVEL=info
   CORS_ORIGIN=https://your-frontend-domain.railway.app
   ```

5. **设置健康检查**
   - Healthcheck Path: `/health`
   - Healthcheck Timeout: `100ms`

### 第二步：部署前端服务

1. **添加新服务**
   - 在同一个 Railway 项目中
   - 点击 "New Service"
   - 再次选择 "Deploy from GitHub repo"
   - Root Directory: `frontend`

2. **配置前端服务**
   - Build Command: `npm run build`
   - Start Command: `npm start`

3. **配置环境变量**
   在前端服务的 "Variables" 标签页添加：
   
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend-domain.railway.app
   NEXT_PUBLIC_APP_NAME=猎头协作
   NEXT_PUBLIC_APP_URL=https://your-frontend-domain.railway.app
   NODE_ENV=production
   ```

4. **设置域名和健康检查**
   - Healthcheck Path: `/`
   - Generate Domain: 点击 "Generate Domain"

### 第三步：连接服务

1. **获取后端域名**
   - 在后端服务中找到生成的域名
   - 格式: `https://your-backend-service.railway.app`

2. **更新前端环境变量**
   - 将 `NEXT_PUBLIC_API_URL` 设置为后端域名
   - 将 `CORS_ORIGIN`（后端）设置为前端域名

3. **重新部署**
   - 更新环境变量后，Railway 会自动重新部署
   - 等待部署完成（约 2-3 分钟）

### 第四步：运行数据库迁移

1. **访问 Railway Console**
   - 在后端服务中点击 "Console"
   - 你会得到一个交互式终端

2. **运行 Prisma 迁移**
   ```bash
   cd backend
   npm run db:migrate
   ```

3. **验证数据库**
   ```bash
   npm run db:studio
   ```
   这将启动 Prisma Studio 来查看数据库

## 🔧 配置说明

### Railway 配置文件

项目包含以下 Railway 配置文件：

1. **根目录 `railway.json`**
   - 通用项目配置
   - 健康检查设置
   - 重启策略

2. **前端 `frontend/railway.json`**
   - Next.js 构建配置
   - 监听文件变化模式

3. **后端 `backend/railway.json`**
   - Node.js 构建配置
   - 数据库迁移命令

### 环境变量参考

参考 `.env.railway.example` 文件查看所有需要的环境变量。

## 🌐 自定义域名

### 设置自定义域名

1. **在 Railway 中**
   - 进入服务设置
   - 点击 "Settings" > "Networking"
   - 点击 "Custom Domain"

2. **配置 DNS**
   - 添加 A 记录指向 Railway 提供的 IP
   - 或添加 CNAME 记录指向 Railway 域名

3. **SSL 证书**
   - Railway 会自动提供 Let's Encrypt SSL 证书
   - 通常在几分钟内生效

## 📊 监控和日志

### 查看日志
- 在服务中点击 "Logs" 标签
- 实时查看应用日志
- 可以按时间、级别过滤

### 性能监控
- Railway 提供内置的监控仪表板
- CPU、内存使用情况
- 请求响应时间

### 告警设置
- 设置 CPU、内存使用告警
- 配置邮件或 Slack 通知

## 🔄 持续部署

### 自动部署
Railway 默认配置为：
- 推送到 `main` 分支时自动部署
- 支持从 Pull Request 预览部署

### 手动部署
1. 在 Railway 控制台选择服务
2. 点击 "Deploy" 按钮
3. 选择特定的 commit 或分支

## 🐛 故障排查

### 常见问题

#### 1. 前端无法连接后端
**症状**: 前端页面加载但API调用失败

**解决方案**:
- 检查 `NEXT_PUBLIC_API_URL` 是否正确
- 确认后端 CORS 配置包含前端域名
- 查看后端日志是否有错误

#### 2. 数据库连接失败
**症状**: 后端启动时数据库错误

**解决方案**:
- 确保 PostgreSQL 服务正在运行
- 检查 `DATABASE_URL` 环境变量
- 运行数据库迁移: `npm run db:migrate`

#### 3. 构建失败
**症状**: 部署时构建错误

**解决方案**:
- 检查 `package.json` 中的脚本是否正确
- 确保所有依赖都在 `package.json` 中
- 查看构建日志中的具体错误

#### 4. 健康检查失败
**症状**: 服务频繁重启

**解决方案**:
- 确认健康检查端点可访问
- 检查服务是否真的在运行
- 增加健康检查超时时间

## 💰 成本估算

### Railway 定价
- **免费版**: 每月 $5 额度
  - 512MB RAM
  - 0.5 vCPU
  - 1GB 存储
  
- **付费版**: 按使用量计费
  - $10/月起
  - 更好的性能
  - 更多功能

### 成本优化建议
1. **开发环境**: 使用免费版
2. **生产环境**: 从付费版开始，按需扩展
3. **数据库**: 使用 Railway 提供的 PostgreSQL（包含在免费额度中）

## 🔒 安全配置

### 生产环境安全检查清单

- [ ] 更改所有默认密钥和密码
- [ ] 使用强 JWT_SECRET
- [ ] 启用 HTTPS（Railway 自动提供）
- [ ] 配置适当的 CORS 策略
- [ ] 限制数据库访问权限
- [ ] 定期更新依赖包
- [ ] 监控异常访问

## 📈 扩展和优化

### 性能优化
1. **启用缓存**
   - 使用 Redis 缓存（Railway 支持）
   - CDN 静态资源

2. **数据库优化**
   - 添加适当的索引
   - 定期清理旧数据

3. **负载均衡**
   - 增加服务副本数
   - 使用 Railway 的负载均衡

### 监控设置
1. **设置告警**
   - CPU 使用率 > 80%
   - 内存使用率 > 85%
   - 服务不可用

2. **日志聚合**
   - 集成第三方日志服务
   - 设置日志保留策略

## 🎯 部署后验证

### 功能检查清单
- [ ] 前端页面可以正常访问
- [ ] 用户注册登录功能正常
- [ ] API 调用成功
- [ ] 数据库读写正常
- [ ] 文件上传功能正常（如果有）
- [ ] 二维码生成功能正常

### 性能检查
- [ ] 页面加载时间 < 3秒
- [ ] API 响应时间 < 500ms
- [ ] 服务稳定性 > 99%

## 📚 相关资源

- **Railway 文档**: https://docs.railway.app
- **Next.js 部署**: https://nextjs.org/docs/deployment
- **Prisma 部署**: https://www.prisma.io/docs/guides/deployment

## 🆘 获取帮助

如果遇到问题：
1. 查看 Railway 日志
2. 检查 GitHub Issues
3. 参考 Railway 社区论坛
4. 联系 Railway 支持团队

---

**部署完成后，你的猎头协作应用将在几分钟内上线，可以在全球范围内访问！**