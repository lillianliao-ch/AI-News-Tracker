# 🚀 快速启动指南

## 立即开始使用猎头协作移动端

### 📋 前提条件

- Node.js 20+ 
- npm 或 yarn
- Docker 和 Docker Compose（如使用Docker方式）
- PostgreSQL 14+（如本地开发）

---

## 方式一：Docker Compose（最简单）⭐

### 1. 进入项目目录
```bash
cd /Users/lillianliao/notion_rag/hunter-share-mobile
```

### 2. 启动所有服务
```bash
docker-compose up -d
```

### 3. 查看服务状态
```bash
docker-compose ps
docker-compose logs -f
```

### 4. 访问应用
- 🌐 前端：http://localhost:3000
- 🔌 后端API：http://localhost:4000
- ❤️ 健康检查：http://localhost:4000/health

### 5. 停止服务
```bash
docker-compose down
```

---

## 方式二：本地开发

### Step 1: 安装后端依赖

```bash
cd /Users/lillianliao/notion_rag/hunter-share-mobile/backend
npm install
```

### Step 2: 配置后端环境变量

创建 `.env` 文件：
```bash
cat > .env << EOF
DATABASE_URL="postgresql://hunter_admin:hunter_password_2024@localhost:5433/hunter_share_mobile?schema=public"
JWT_SECRET="hunter-share-jwt-secret-dev-only"
PORT=4000
HOST=0.0.0.0
NODE_ENV=development
EOF
```

### Step 3: 启动PostgreSQL（使用Docker）

```bash
docker run -d \
  --name hunter-share-postgres \
  -e POSTGRES_DB=hunter_share_mobile \
  -e POSTGRES_USER=hunter_admin \
  -e POSTGRES_PASSWORD=hunter_password_2024 \
  -p 5433:5432 \
  postgres:14-alpine
```

### Step 4: 初始化数据库

```bash
# 生成Prisma Client
npm run db:generate

# 运行数据库迁移
npm run db:push
```

### Step 5: 启动后端服务

```bash
npm run dev
```

✅ 后端已启动：http://localhost:4000

---

### Step 6: 安装前端依赖

**新开一个终端窗口：**

```bash
cd /Users/lillianliao/notion_rag/hunter-share-mobile/frontend
npm install
```

### Step 7: 配置前端环境变量

创建 `.env.local` 文件：
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:4000" > .env.local
```

### Step 8: 启动前端服务

```bash
npm run dev
```

✅ 前端已启动：http://localhost:3000

---

## 📱 测试应用

### 1. 打开浏览器
访问：http://localhost:3000

### 2. 快速注册
点击"登录查看更多群组" → "没有账号？立即注册"

填写信息：
- 姓名：测试用户
- 手机号：13900000001
- 申请原因：测试系统功能

### 3. 浏览群组
注册后可以看到5个mock群组

### 4. 查看群组详情
点击任意群组进入详情页

### 5. 发布信息
点击右上角"+"按钮发布信息

---

## 🔍 验证服务状态

### 后端健康检查
```bash
curl http://localhost:4000/health
```

预期输出：
```json
{
  "status": "ok",
  "timestamp": "2024-11-07T..."
}
```

### 测试注册API
```bash
curl -X POST http://localhost:4000/api/hunter-auth/quick-register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试用户",
    "phone": "13900000001",
    "reason": "测试系统功能测试系统功能"
  }'
```

### 查看数据库
```bash
cd backend
npm run db:studio
```

访问：http://localhost:5555

---

## 🛠️ 常用命令

### Docker

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 清理并重启
docker-compose down -v && docker-compose up -d --build

# 只重启某个服务
docker-compose restart backend
docker-compose restart frontend
```

### 数据库

```bash
cd backend

# 查看数据库
npm run db:studio

# 重置数据库
npx prisma db push --force-reset

# 查看迁移状态
npx prisma migrate status
```

### 开发

```bash
# 后端热重载（已自动）
cd backend && npm run dev

# 前端热重载（已自动）
cd frontend && npm run dev

# 构建生产版本
cd backend && npm run build
cd frontend && npm run build
```

---

## 🐛 常见问题解决

### 问题1：端口被占用

```bash
# 查看占用端口的进程
lsof -i :3000
lsof -i :4000
lsof -i :5433

# 杀死进程
kill -9 <PID>
```

### 问题2：Docker启动失败

```bash
# 清理所有容器和卷
docker-compose down -v

# 重新构建镜像
docker-compose build --no-cache

# 重新启动
docker-compose up -d
```

### 问题3：数据库连接失败

检查PostgreSQL是否运行：
```bash
docker ps | grep postgres
```

检查数据库连接字符串：
```bash
cat backend/.env
```

### 问题4：Prisma Client未生成

```bash
cd backend
rm -rf node_modules/.prisma
npm run db:generate
```

### 问题5：前端无法连接后端

1. 确认后端正在运行：`curl http://localhost:4000/health`
2. 检查 `.env.local` 配置
3. 重启前端开发服务器

---

## 📊 服务端口

| 服务 | 端口 | URL |
|------|------|-----|
| 前端Web | 3000 | http://localhost:3000 |
| 后端API | 4000 | http://localhost:4000 |
| PostgreSQL | 5433 | localhost:5433 |
| Prisma Studio | 5555 | http://localhost:5555 |

---

## 🎯 下一步

1. ✅ 启动服务
2. ✅ 测试注册和登录
3. ✅ 浏览群组和信息
4. 📝 创建管理员账号
5. 🎨 自定义UI样式
6. 🚀 部署到生产环境

---

## 💡 提示

- 开发环境下前后端都有热重载功能
- 修改代码后会自动重启服务
- 使用 Prisma Studio 可视化管理数据库
- Chrome DevTools可以模拟移动设备查看效果

---

**祝开发顺利！** 🎉

如有问题，请查看 `README.md` 或 `MIGRATION_COMPLETE.md`

