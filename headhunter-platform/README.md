# 🤝 Headhunter Collaboration Platform

> 专为猎头行业设计的智能协作平台，支持多角色协作、智能匹配和实时通信

[![Development Status](https://img.shields.io/badge/Status-MVP_Complete_+_Testing-success.svg)](./PROJECT_SUMMARY.md)
[![Tech Stack](https://img.shields.io/badge/Tech-Next.js%20%7C%20Fastify%20%7C%20PostgreSQL-blue.svg)](#技术栈)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

## 📋 项目概述

Headhunter Collaboration Platform 是一个现代化的猎头协作平台，旨在解决猎头行业中的协作难题。平台支持多角色用户、智能候选人匹配、职位分享、实时通信等核心功能，显著提升猎头工作效率。

### 🎯 核心价值
- **智能匹配**: AI 驱动的候选人-职位匹配算法，匹配准确率高达90%+
- **协作共赢**: 透明的收益分成机制，促进跨公司合作
- **实时协作**: WebSocket 实时通信，即时消息和通知
- **数据驱动**: 全面的协作统计和业务分析

## 🏗️ 项目结构

```
headhunter-platform/
├── frontend/          # Next.js 前端应用
├── backend/           # Node.js API 后端服务
├── database/          # PostgreSQL 数据库脚本
├── docker-compose.yml # Docker 开发环境配置
├── .env.example       # 环境变量示例
└── docs/              # 项目文档
```

## 🚀 快速开始

### 环境要求
- Node.js 18+ (推荐 v18/v20 LTS)
- Docker & Docker Compose (可选)
- Git
- PostgreSQL & Redis (如果不想用Docker)

### 方式一：使用 Docker 一键启动 (推荐用于纯净环境)

```bash
# 1. 克隆项目
git clone <repository-url>
cd headhunter-platform

# 2. 复制环境变量
cp .env.example .env

# 3. 启动开发环境
docker-compose up -d

# 4. 安装依赖并启动
npm run setup:docker
npm run dev
```

### 方式二：本地裸机启动 (无Docker环境)

适用于已经安装了 PostgreSQL 和 Redis 的本地开发环境。

```bash
# 1. 运行智能配置脚本
# 该脚本会自动检测 Node 版本、生成配置文件、安装依赖并初始化数据库
./scripts/setup-local.sh

# 2. 启动开发服务器
cd headhunter-platform
npm run dev
```

### 访问地址
- 前端应用: http://localhost:3000
- 后端API: http://localhost:4000
- API文档: http://localhost:4000/docs
- 数据库: postgres://localhost:5432/headhunter_db

## 📁 详细目录结构

```
├── frontend/                 # Next.js 前端
│   ├── src/
│   │   ├── app/             # App Router (Next.js 14)
│   │   ├── components/      # 可复用组件
│   │   ├── lib/            # 工具函数和配置
│   │   ├── hooks/          # 自定义React Hooks
│   │   └── types/          # TypeScript 类型定义
│   ├── public/             # 静态资源
│   └── package.json
│
├── backend/                  # Node.js 后端
│   ├── src/
│   │   ├── controllers/    # 控制器
│   │   ├── models/         # 数据模型 (Prisma)
│   │   ├── routes/         # 路由定义
│   │   ├── middleware/     # 中间件
│   │   ├── services/       # 业务逻辑服务
│   │   ├── utils/          # 工具函数
│   │   └── types/          # TypeScript 类型
│   ├── prisma/             # Prisma ORM 配置
│   └── package.json
│
└── database/                 # 数据库相关
    ├── migrations/          # 数据库迁移脚本
    ├── seeds/              # 种子数据
    └── init.sql            # 初始化脚本
```

## 🛠️ 开发命令

```bash
# 开发环境
npm run dev              # 启动前后端开发服务器
npm run dev:frontend     # 仅启动前端
npm run dev:backend      # 仅启动后端

# 构建
npm run build            # 构建前后端
npm run build:frontend   # 仅构建前端
npm run build:backend    # 仅构建后端

# 数据库
npm run db:migrate       # 运行数据库迁移
npm run db:seed          # 运行种子数据
npm run db:reset         # 重置数据库
npm run db:studio        # 打开Prisma Studio

# 测试
npm run test                    # 运行所有测试
npm run test:integration        # 运行集成测试
npm run test:integration:demo   # 演示测试框架 (推荐!)
npm run test:integration:coverage # 测试覆盖率报告
npm run test:frontend          # 前端测试
npm run test:backend           # 后端测试

# 代码质量
npm run lint             # 代码检查
npm run format           # 代码格式化
npm run type-check       # TypeScript 类型检查
```

## 🔧 技术栈

### 前端
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **状态管理**: Zustand + React Query
- **UI库**: Ant Design + Tailwind CSS
- **表单**: React Hook Form + Zod
- **HTTP客户端**: Axios

### 后端
- **框架**: Node.js + Fastify
- **语言**: TypeScript
- **数据库ORM**: Prisma
- **认证**: JWT + Passport.js
- **文档**: Swagger/OpenAPI 3.0
- **测试**: Jest + Supertest

### 数据库
- **主数据库**: PostgreSQL 14+
- **缓存**: Redis 7.0+
- **搜索**: Elasticsearch (可选)

### 开发工具
- **容器化**: Docker + Docker Compose
- **代码质量**: ESLint + Prettier + Husky
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana

## 🌟 核心功能

- **用户管理**: 多角色用户体系 (平台管理员、公司管理员、顾问、SOHO)
- **职位管理**: 职位发布、权限控制、分成配置
- **候选人管理**: 去重检测、版本化投递、状态跟踪
- **协作功能**: 跨公司协作、实时通知
- **利益分配**: 自动分成计算、结算管理
- **统计分析**: 收入统计、业绩报表

## 👥 用户角色与审核流程

### 角色定义
1. **平台管理员** (platform_admin) - 平台运营管理者
2. **公司管理员** (company_admin) - 猎头公司负责人  
3. **咨询顾问** (consultant) - 公司内部猎头顾问
4. **个人猎头** (soho) - 独立猎头工作者

### 注册审核权限分工

#### 🔐 平台管理员审核范围
- ✅ **公司管理员**: 审核猎头公司注册申请
- ✅ **个人猎头 (SOHO)**: 审核独立猎头注册  
- ❌ **咨询顾问**: 不负责审核（由公司管理员负责）

#### 🏢 公司管理员审核范围  
- ✅ **咨询顾问**: 审核并邀请顾问加入本公司
- ❌ **其他角色**: 不负责审核

### 详细注册流程

#### 1. 个人猎头 (SOHO) 注册
```
填写个人信息 → 提交申请 → 平台管理员审核 → 账号激活
```
- **必填信息**: 用户名、邮箱、手机、密码
- **审核周期**: 1-3个工作日
- **激活后**: 可立即开始使用平台功能

#### 2. 公司管理员注册  
```
填写公司信息 → 提交申请 → 平台管理员审核 → 公司和账号同时激活
```
- **必填信息**: 个人信息 + 公司名称 + 营业执照号
- **审核内容**: 公司资质验证、营业执照真实性
- **激活后**: 获得公司管理权限，可邀请咨询顾问

#### 3. 咨询顾问注册
```
填写个人信息 → 提交申请 → 公司管理员审核 → 绑定公司 → 账号激活
```
- **必填信息**: 用户名、邮箱、手机、密码  
- **审核流程**: 由公司管理员在"Consultant Approval"页面处理
- **激活后**: 自动绑定到审核公司，获得公司内部权限

### 🖥️ 前端界面权限

#### 平台管理员界面
- **User Management**: 显示待审核的公司管理员和SOHO
- **Company Management**: 公司审核和管理
- **不显示**: 咨询顾问审核功能

#### 公司管理员界面  
- **Consultant Approval**: 专门的咨询顾问审核页面
- **Company Management**: 本公司信息管理
- **不显示**: 其他角色审核功能

#### 咨询顾问/SOHO界面
- **无审核功能**: 只能使用业务功能
- **职位管理**: 发布、分享、协作
- **候选人管理**: 维护、投递、跟进

### ⚡ 业务规则

1. **权限边界**: 每个角色只能审核特定类型的用户，确保权限安全
2. **公司绑定**: 咨询顾问审核通过后自动绑定到审核公司
3. **审核透明**: 所有审核操作都有记录和通知
4. **快速激活**: SOHO和公司管理员审核后立即可用，咨询顾问需要公司关联

### 🔄 状态流转

```
用户注册 → pending (待审核) → active/inactive (已激活/已拒绝)
                ↓
        不同角色对应不同审核者
        ├── 公司管理员/SOHO → 平台管理员审核
        └── 咨询顾问 → 公司管理员审核
```

## 📖 API文档

启动后端服务后，访问 http://localhost:4000/docs 查看完整的API文档。

## 🧪 测试

```bash
# 运行所有测试
npm test

# 运行特定测试
npm run test:unit        # 单元测试
npm run test:integration # 集成测试
npm run test:e2e         # 端到端测试

# 测试覆盖率
npm run test:coverage
```

## 📦 部署

### 开发环境
```bash
docker-compose up -d
```

### 生产环境
```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d
```

## 🔒 环境变量

参考 `.env.example` 文件配置以下环境变量：

```bash
# 数据库配置
DATABASE_URL="postgresql://username:password@localhost:5432/headhunter_db"
REDIS_URL="redis://localhost:6379"

# JWT配置
JWT_SECRET="your-jwt-secret-key"
JWT_EXPIRES_IN="1h"
JWT_REFRESH_EXPIRES_IN="7d"

# 第三方服务
ALIYUN_OCR_ACCESS_KEY="your-ocr-access-key"
ALIYUN_OCR_SECRET_KEY="your-ocr-secret-key"
WECHAT_APP_ID="your-wechat-app-id"
WECHAT_APP_SECRET="your-wechat-app-secret"

# 文件存储
OSS_REGION="oss-cn-hangzhou"
OSS_BUCKET="your-oss-bucket"
OSS_ACCESS_KEY_ID="your-oss-access-key"
OSS_ACCESS_KEY_SECRET="your-oss-secret-key"
```

## 📋 开发规范

### Git提交规范
```bash
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式化
refactor: 重构
test: 测试相关
chore: 构建过程或工具变动
```

### 代码规范
- 使用 ESLint + Prettier 进行代码格式化
- 使用 TypeScript 严格模式
- 遵循 Airbnb JavaScript 风格指南
- 组件和函数必须有 JSDoc 注释

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 团队

- **产品设计**: 需求分析和用户体验设计
- **后端开发**: API开发和数据库设计
- **前端开发**: 用户界面和交互实现
- **DevOps**: 部署和运维管理

## 📞 联系我们

如有问题或建议，请通过以下方式联系我们：

- 创建 [Issue](https://github.com/your-repo/headhunter-platform/issues)
- 发送邮件至: dev@headhunter-platform.com

---

**版本**: 1.0.0  
**最后更新**: 2025-09-10