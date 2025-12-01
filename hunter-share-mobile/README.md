# 猎头协作移动端 (Hunter Share Mobile)

一个专为猎头顾问打造的移动端信息分享与协作平台。

## 📱 功能特性

- ✅ **群组管理** - 按行业分类的猎头协作群组
- ✅ **信息发布** - 发布找人才/推人才信息
- ✅ **快速注册** - 简化的注册流程，快速加入协作网络
- ✅ **权限分级** - 游客、注册用户、认证用户三级权限
- ✅ **实时统计** - 浏览量、发布数等数据统计
- ✅ **移动优先** - 完全适配移动端的响应式设计

## 🛠️ 技术栈

### 前端
- **框架**: Next.js 15.5.2
- **UI**: React 19 + Tailwind CSS 4
- **语言**: TypeScript 5

### 后端
- **框架**: Fastify 4
- **ORM**: Prisma 5
- **数据库**: PostgreSQL 14
- **认证**: JWT

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd hunter-share-mobile

# 2. 启动所有服务
docker-compose up -d

# 3. 等待服务就绪（约30-60秒）
docker-compose logs -f

# 4. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:4000
# 健康检查: http://localhost:4000/health
```

### 方式二：本地开发

#### 前置要求
- Node.js 20+
- PostgreSQL 14+
- npm或yarn

#### 后端设置

```bash
cd backend

# 安装依赖
npm install

# 配置环境变量（复制并修改）
cp .env.example .env

# 生成Prisma Client
npm run db:generate

# 运行数据库迁移
npm run db:migrate:dev

# 启动开发服务器
npm run dev

# 后端将运行在 http://localhost:4000
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量（创建 .env.local）
echo "NEXT_PUBLIC_API_URL=http://localhost:4000" > .env.local

# 启动开发服务器
npm run dev

# 前端将运行在 http://localhost:3000
```

## 📦 项目结构

```
hunter-share-mobile/
├── frontend/                 # 前端应用
│   ├── src/
│   │   ├── app/             # Next.js页面
│   │   │   ├── page.tsx     # 首页（群组列表）
│   │   │   ├── group/       # 群组详情
│   │   │   ├── publish/     # 发布信息
│   │   │   ├── my-posts/    # 我的发布
│   │   │   ├── profile/     # 个人中心
│   │   │   └── admin/       # 管理后台
│   │   ├── components/      # React组件
│   │   │   └── HunterAuth.tsx
│   │   └── lib/             # 工具库
│   │       ├── api.ts       # API客户端
│   │       └── config.ts    # 配置文件
│   ├── package.json
│   ├── next.config.js
│   └── Dockerfile
│
├── backend/                  # 后端API
│   ├── src/
│   │   ├── routes/          # API路由
│   │   │   ├── hunter-auth.ts    # 认证相关
│   │   │   └── hunter-posts.ts   # 信息发布相关
│   │   └── index.ts         # 入口文件
│   ├── prisma/
│   │   └── schema.prisma    # 数据库模型
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml        # Docker编排配置
└── README.md                 # 本文档
```

## 📊 数据库设计

### 核心表

- **users** - 用户表
- **hunter_posts** - 猎头信息发布表
- **notifications** - 通知表
- **share_links** - 分享链接表（可选）
- **share_tracking** - 分享追踪表（可选）

## 🔑 API接口

### 认证相关

- `POST /api/hunter-auth/quick-register` - 快速注册
- `POST /api/hunter-auth/login` - 登录
- `GET /api/hunter-auth/profile` - 获取用户资料
- `GET /api/hunter-auth/pending-users` - 获取待审核用户（管理员）
- `PATCH /api/hunter-auth/approve-user/:id` - 审核用户（管理员）

### 信息发布相关

- `GET /api/hunter-posts` - 获取信息列表
- `POST /api/hunter-posts` - 发布信息
- `GET /api/hunter-posts/my` - 获取我的发布
- `DELETE /api/hunter-posts/:id` - 删除信息
- `PATCH /api/hunter-posts/:id/approve` - 审核信息（管理员）

## 👥 用户角色

- **游客** - 可浏览近1天内的前3条信息
- **注册用户** - 可浏览近3天内的前10条信息
- **认证用户** - 可浏览所有信息，可发布信息
- **管理员** - 审核用户和信息

## 🔒 环境变量

### 后端 (.env)

```bash
DATABASE_URL="postgresql://username:password@localhost:5432/hunter_share_mobile"
JWT_SECRET="your-super-secret-key"
PORT=4000
HOST=0.0.0.0
NODE_ENV=development
```

### 前端 (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:4000
```

## 📝 开发命令

### 后端

```bash
npm run dev            # 启动开发服务器
npm run build          # 构建生产版本
npm run start          # 启动生产服务器
npm run db:generate    # 生成Prisma Client
npm run db:migrate:dev # 运行数据库迁移（开发）
npm run db:push        # 推送schema到数据库
npm run db:studio      # 打开Prisma Studio
```

### 前端

```bash
npm run dev      # 启动开发服务器
npm run build    # 构建生产版本
npm run start    # 启动生产服务器
npm run lint     # 代码检查
```

## 🐛 常见问题

### 1. Docker启动失败

```bash
# 清理并重新启动
docker-compose down -v
docker-compose up -d --build
```

### 2. 数据库连接失败

确保PostgreSQL正在运行，并检查DATABASE_URL配置。

### 3. 前端无法连接后端

检查NEXT_PUBLIC_API_URL配置，确保后端服务已启动。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发团队** | 猎头协作平台

