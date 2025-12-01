# 技术架构文档

## 📐 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层 (User Layer)                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  移动浏览器   │  │  Chrome Dev  │  │    Safari    │      │
│  │  (游客/用户)  │  │    Tools     │  │   响应式     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (Frontend Layer)                    │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Next.js 15.5.2 (App Router)              │  │
│  │                                                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │  Pages   │  │Components│  │   Libs   │           │  │
│  │  │          │  │          │  │          │           │  │
│  │  │ • 首页    │  │ • Auth   │  │ • API    │           │  │
│  │  │ • 群组    │  │ • Modal  │  │ • Config │           │  │
│  │  │ • 发布    │  │          │  │          │           │  │
│  │  └──────────┘  └──────────┘  └──────────┘           │  │
│  │                                                        │  │
│  │  React 19 + TypeScript 5 + Tailwind CSS 4            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  运行端口: 4000                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    HTTP/HTTPS REST API
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    后端层 (Backend Layer)                     │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Fastify 4.24.3                        │  │
│  │                                                        │  │
│  │  ┌────────────────┐        ┌────────────────┐        │  │
│  │  │  Auth Routes   │        │  Posts Routes  │        │  │
│  │  │                │        │                │        │  │
│  │  │ • 快速注册      │        │ • 发布信息      │        │  │
│  │  │ • 登录         │        │ • 查看列表      │        │  │
│  │  │ • 获取资料      │        │ • 我的发布      │        │  │
│  │  │ • 审核用户      │        │ • 审核信息      │        │  │
│  │  └────────────────┘        └────────────────┘        │  │
│  │                                                        │  │
│  │  ┌───────────────────────────────────────┐           │  │
│  │  │         Prisma 5.6.0 (ORM)            │           │  │
│  │  └───────────────────────────────────────┘           │  │
│  │                                                        │  │
│  │  JWT Authentication + Zod Validation                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  运行端口: 5000                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
                         SQL Queries
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   数据层 (Database Layer)                     │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              PostgreSQL 14 (Alpine)                    │  │
│  │                                                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │  users   │  │  hunter  │  │  notifi  │           │  │
│  │  │   表     │  │  _posts  │  │ cations  │           │  │
│  │  │          │  │   表     │  │    表    │           │  │
│  │  │ • 15字段  │  │ • 15字段  │  │ • 10字段  │           │  │
│  │  └──────────┘  └──────────┘  └──────────┘           │  │
│  │                                                        │  │
│  │  + share_links, share_tracking (可选)                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  运行端口: 5433 (映射到容器的5432)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 技术选型

### 前端技术栈

| 技术 | 版本 | 选型理由 |
|------|------|---------|
| **Next.js** | 15.5.2 | • 服务端渲染(SSR)提升SEO<br>• App Router提供更好的路由体验<br>• 内置API代理简化开发<br>• 优秀的TypeScript支持 |
| **React** | 19.1.0 | • 组件化开发<br>• 虚拟DOM高性能<br>• 丰富的生态系统<br>• Hooks提供状态管理 |
| **TypeScript** | 5.x | • 类型安全<br>• IDE智能提示<br>• 减少运行时错误<br>• 更好的代码维护性 |
| **Tailwind CSS** | 4.x | • 原子化CSS<br>• 快速开发<br>• 响应式设计<br>• 打包体积小 |

### 后端技术栈

| 技术 | 版本 | 选型理由 |
|------|------|---------|
| **Fastify** | 4.24.3 | • 性能优于Express(2-3倍)<br>• 内置schema验证<br>• 优秀的TypeScript支持<br>• 插件系统完善 |
| **Prisma** | 5.6.0 | • 类型安全的ORM<br>• 直观的数据建模<br>• 强大的迁移工具<br>• 自动生成类型 |
| **PostgreSQL** | 14 | • 功能强大的关系型数据库<br>• 支持JSON字段<br>• 优秀的性能<br>• 成熟稳定 |
| **JWT** | 9.0.2 | • 无状态认证<br>• 跨域友好<br>• 易于扩展<br>• 标准化 |
| **Zod** | 3.22.4 | • 运行时类型验证<br>• 与TypeScript集成<br>• 清晰的错误信息<br>• 链式API |

---

## 📊 数据库设计

### ER图

```
┌─────────────────────┐
│       users         │
├─────────────────────┤
│ id (PK)             │
│ username            │
│ email               │
│ phone (UNIQUE)      │
│ password            │
│ role                │◄──┐
│ status              │   │
│ wechatId            │   │
│ bio                 │   │
│ avatar              │   │
│ postsCount          │   │
│ approvedPosts       │   │
│ totalViews          │   │
│ createdAt           │   │
│ updatedAt           │   │
│ lastLoginAt         │   │
└─────────────────────┘   │
          │               │
          │ 1:N           │
          ▼               │
┌─────────────────────┐   │
│    hunter_posts     │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ type                │   │
│ title               │   │
│ content             │   │
│ status              │   │
│ urgency             │   │
│ viewCount           │   │
│ replyCount          │   │
│ shareCount          │   │
│ publisherId (FK)    │───┘
│ reviewedAt          │
│ reviewedBy          │
│ rejectionReason     │
│ createdAt           │
│ updatedAt           │
│ expiresAt           │
└─────────────────────┘

┌─────────────────────┐
│   notifications     │
├─────────────────────┤
│ id (PK)             │
│ userId (FK)         │───┐
│ type                │   │
│ title               │   │
│ content             │   │
│ relatedId           │   │ 1:N
│ relatedType         │   │
│ isRead              │   ▼
│ readAt              │ ┌─────────────────────┐
│ createdAt           │ │       users         │
└─────────────────────┘ │   (referenced)      │
                        └─────────────────────┘

┌─────────────────────┐
│    share_links      │
├─────────────────────┤
│ id (PK)             │
│ shortCode (UNIQUE)  │
│ jobId               │
│ postId              │
│ consultantId (FK)   │───┐
│ viewCount           │   │
│ clickCount          │   │ 1:N
│ registerCount       │   │
│ createdAt           │   ▼
│ expiresAt           │ ┌─────────────────────┐
└─────────────────────┘ │       users         │
          │             │   (referenced)      │
          │ 1:N         └─────────────────────┘
          ▼
┌─────────────────────┐
│  share_tracking     │
├─────────────────────┤
│ id (PK)             │
│ linkId (FK)         │
│ userId (FK)         │
│ action              │
│ source              │
│ userAgent           │
│ ipAddress           │
│ createdAt           │
└─────────────────────┘
```

### 核心表详解

#### 1. users 表
**用途**：存储所有用户信息

**关键字段**：
- `role`: 用户角色（platform_admin, company_admin, consultant, soho）
- `status`: 用户状态（registered, verified, active, suspended）
- `postsCount`: 发布总数（冗余字段，提升查询性能）
- `approvedPosts`: 已通过的发布数
- `totalViews`: 总浏览量

**索引**：
```sql
INDEX idx_users_phone ON users(phone)
INDEX idx_users_email ON users(email)
INDEX idx_users_role_status ON users(role, status)
```

#### 2. hunter_posts 表
**用途**：存储猎头发布的信息

**关键字段**：
- `type`: 信息类型（job_seeking=找人才, talent_recommendation=推人才）
- `status`: 审核状态（pending, approved, rejected）
- `urgency`: 紧急程度（0-5，影响排序）
- `expiresAt`: 过期时间（自动下架）

**索引**：
```sql
INDEX idx_posts_publisher ON hunter_posts(publisherId)
INDEX idx_posts_type_status ON hunter_posts(type, status)
INDEX idx_posts_created ON hunter_posts(createdAt)
INDEX idx_posts_status_urgency ON hunter_posts(status, urgency)
```

#### 3. notifications 表
**用途**：系统通知

**通知类型**：
- `system`: 系统通知
- `user_approved`: 用户审核通过
- `user_rejected`: 用户审核拒绝
- `post_approved`: 信息审核通过
- `post_rejected`: 信息审核拒绝
- `new_post`: 新信息发布

**索引**：
```sql
INDEX idx_notifications_user_read ON notifications(userId, isRead)
INDEX idx_notifications_created ON notifications(createdAt)
```

---

## 🔄 数据流设计

### 用户注册流程

```
用户填写注册信息
    ↓
前端验证 (客户端)
    ↓
POST /api/hunter-auth/quick-register
    ↓
后端验证 (Zod Schema)
    ↓
检查手机号是否存在
    ↓
生成临时密码 + bcrypt加密
    ↓
创建用户记录 (status=registered)
    ↓
生成JWT Token
    ↓
创建通知给管理员
    ↓
返回 { user, token, tempPassword }
    ↓
前端存储 token 到 localStorage
    ↓
显示临时密码给用户
```

### 信息发布流程

```
用户点击"发布"按钮
    ↓
前端检查登录状态
    ↓
填写信息 (type, title, content)
    ↓
POST /api/hunter-posts
    ↓
后端验证 JWT Token
    ↓
后端验证数据 (Zod Schema)
    ↓
检查用户权限 (canPublish)
    ↓
创建发布记录 (status=approved)
    ↓
更新用户 postsCount
    ↓
返回 { success, data }
    ↓
前端跳转到首页
    ↓
显示发布成功提示
```

### 信息查看流程（权限分级）

```
用户访问首页
    ↓
GET /api/hunter-posts
    ↓
后端检查 Authorization Header
    ↓
解析用户状态 (guest/registered/verified)
    ↓
应用权限规则:
  • guest: 近1天, 最多3条
  • registered: 近3天, 最多10条
  • verified: 所有, 无限制
    ↓
构建查询条件 (WHERE + LIMIT)
    ↓
Prisma 查询数据库
    ↓
格式化返回数据
    ↓
返回 { success, data, pagination, userPermissions }
    ↓
前端渲染列表
```

---

## 🔐 认证授权机制

### JWT Token 结构

```typescript
// Token Payload
{
  id: string,        // 用户ID
  role: UserRole,    // 用户角色
  status: UserStatus, // 用户状态
  iat: number,       // 签发时间
  exp: number        // 过期时间 (7天)
}

// Token 签名
JWT_SECRET: "hunter-share-jwt-secret-dev"
Algorithm: HS256
```

### 权限控制矩阵

| 功能 | 游客 | 注册用户 | 认证用户 | 管理员 |
|------|-----|---------|---------|--------|
| 查看信息 | ✅ (限制) | ✅ (限制) | ✅ | ✅ |
| 发布信息 | ❌ | ❌ | ✅ | ✅ |
| 删除自己的信息 | ❌ | ❌ | ✅ | ✅ |
| 审核信息 | ❌ | ❌ | ❌ | ✅ |
| 审核用户 | ❌ | ❌ | ❌ | ✅ |
| 查看所有用户 | ❌ | ❌ | ❌ | ✅ |

### 中间件认证流程

```typescript
// authenticateUser 中间件
async function authenticateUser(request, reply) {
  const authHeader = request.headers.authorization
  
  if (!authHeader) {
    // 游客用户
    request.user = { id: null, status: 'guest', role: null }
    return
  }
  
  try {
    const token = authHeader.replace('Bearer ', '')
    const decoded = jwt.verify(token, JWT_SECRET)
    
    const user = await prisma.user.findUnique({
      where: { id: decoded.id }
    })
    
    if (user) {
      request.user = { id: user.id, status: user.status, role: user.role }
    } else {
      request.user = { id: null, status: 'guest', role: null }
    }
  } catch (error) {
    request.user = { id: null, status: 'guest', role: null }
  }
}
```

---

## 📂 目录结构

### 前端目录

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── page.tsx              # 首页（群组列表）
│   │   ├── layout.tsx            # 根布局
│   │   ├── globals.css           # 全局样式
│   │   ├── group/
│   │   │   └── [id]/
│   │   │       └── page.tsx      # 群组详情页
│   │   ├── publish/
│   │   │   └── page.tsx          # 发布信息页
│   │   ├── my-posts/
│   │   │   └── page.tsx          # 我的发布页
│   │   ├── profile/
│   │   │   └── page.tsx          # 个人中心页
│   │   └── admin/
│   │       └── page.tsx          # 管理后台页
│   │
│   ├── components/               # React组件
│   │   └── HunterAuth.tsx        # 认证组件（登录/注册）
│   │
│   └── lib/                      # 工具库
│       ├── api.ts                # API客户端
│       └── config.ts             # 配置文件
│
├── public/                       # 静态资源
├── .env.local                    # 环境变量
├── next.config.js                # Next.js配置
├── tailwind.config.js            # Tailwind配置
├── postcss.config.js             # PostCSS配置
├── tsconfig.json                 # TypeScript配置
└── package.json                  # 依赖管理
```

### 后端目录

```
backend/
├── src/
│   ├── index.ts                  # 服务器入口
│   ├── routes/                   # API路由
│   │   ├── hunter-auth.ts        # 认证相关路由
│   │   └── hunter-posts.ts       # 信息发布路由
│   │
│   └── middleware/               # 中间件（预留）
│
├── prisma/
│   ├── schema.prisma             # 数据库模型
│   ├── migrations/               # 数据库迁移
│   └── seed.ts                   # 种子数据（预留）
│
├── .env                          # 环境变量
├── tsconfig.json                 # TypeScript配置
└── package.json                  # 依赖管理
```

---

## 🔌 API设计原则

### RESTful规范

```
GET    /api/hunter-posts          # 获取列表
POST   /api/hunter-posts          # 创建资源
GET    /api/hunter-posts/:id      # 获取详情
PATCH  /api/hunter-posts/:id      # 部分更新
DELETE /api/hunter-posts/:id      # 删除资源
```

### 响应格式统一

```typescript
// 成功响应
{
  success: true,
  data: {...},
  pagination?: {...},
  message?: string
}

// 错误响应
{
  success: false,
  error: string,
  code?: number
}
```

### 错误处理

```typescript
// HTTP状态码使用
200 - 成功
201 - 创建成功
400 - 请求参数错误
401 - 未认证
403 - 无权限
404 - 资源不存在
409 - 资源冲突（如手机号已存在）
500 - 服务器错误
```

---

## 🚀 性能优化策略

### 前端优化

1. **代码分割**
   - Next.js自动按路由分割
   - 动态导入大组件
   - 懒加载图片

2. **缓存策略**
   - localStorage存储token
   - React state管理状态
   - 避免不必要的重渲染

3. **打包优化**
   - Tree Shaking移除无用代码
   - CSS按需加载
   - 生产环境压缩

### 后端优化

1. **数据库优化**
   - 合理的索引设计
   - 分页查询减少数据量
   - 使用Prisma的select指定字段

2. **查询优化**
```typescript
// ❌ 不好的查询
const posts = await prisma.hunterPost.findMany()

// ✅ 优化的查询
const posts = await prisma.hunterPost.findMany({
  select: {
    id: true,
    title: true,
    type: true,
    createdAt: true,
    publisher: {
      select: { username: true }
    }
  },
  where: { status: 'approved' },
  orderBy: { createdAt: 'desc' },
  take: 10,
  skip: offset
})
```

3. **未来扩展**
   - Redis缓存热点数据
   - CDN加速静态资源
   - 负载均衡

---

## 📈 可扩展性设计

### 水平扩展

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    Frontend-1     Frontend-2     Frontend-3
         │               │               │
         └───────────────┼───────────────┘
                         │
                    API Gateway
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    Backend-1      Backend-2      Backend-3
         │               │               │
         └───────────────┼───────────────┘
                         │
                    PostgreSQL
                   (Read Replicas)
```

### 模块化设计

- ✅ 前后端完全分离
- ✅ API独立可复用
- ✅ 数据库独立可迁移
- ✅ 认证模块可插拔
- ✅ 通知系统可扩展

---

## 🔒 安全设计

### 1. 密码安全
```typescript
// bcrypt 加密
const hashedPassword = await bcrypt.hash(password, 10)
```

### 2. JWT安全
- Token存储在localStorage
- HTTPS传输
- 7天过期时间
- 敏感操作需重新验证

### 3. 输入验证
```typescript
// Zod Schema验证
const schema = z.object({
  phone: z.string().regex(/^1[3-9]\d{9}$/),
  password: z.string().min(8),
})
```

### 4. SQL注入防护
- Prisma ORM自动防护
- 参数化查询

### 5. XSS防护
- React自动转义
- Content-Type设置

---

## 📊 监控指标

### 关键指标

| 指标 | 目标值 | 监控方式 |
|------|--------|---------|
| API响应时间 | <200ms | 日志记录 |
| 数据库查询 | <50ms | Prisma日志 |
| 页面加载 | <2s | Lighthouse |
| 错误率 | <1% | 错误日志 |
| 并发用户 | >1000 | 压力测试 |

---

## 🔄 版本演进

### v1.0.0 (当前)
- ✅ 基础功能完整
- ✅ 移动端优先设计
- ✅ 权限分级系统
- ✅ 精简的数据库

### v1.1.0 (规划中)
- 📝 图片上传功能
- 📝 实时通知推送
- 📝 搜索和筛选
- 📝 数据统计看板

### v2.0.0 (未来)
- 📝 实时聊天功能
- 📝 智能推荐算法
- 📝 小程序版本
- 📝 社交功能增强

---

**文档维护**: 随着项目演进持续更新  
**最后更新**: 2024-11-07

