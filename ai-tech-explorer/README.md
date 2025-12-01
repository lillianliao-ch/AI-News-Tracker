# AI Tech Explorer

一个专业的AI技术博客和人才服务平台，专注于分享AI技术洞察、工具评测和职业指导。

## 🌟 项目特色

- **现代化技术栈**: Next.js 14 + TypeScript + Tailwind CSS
- **静态站点生成**: 优秀的SEO性能和加载速度
- **MDX博客系统**: Markdown + React组件的强大内容管理
- **响应式设计**: 完美支持桌面端和移动端
- **组件化架构**: 可复用的UI组件库
- **类型安全**: 完整的TypeScript类型定义

## 🚀 快速开始

### 环境要求

- Node.js 18+
- npm 或 yarn

### 安装依赖

```bash
npm install
```

### 开发环境

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看网站。

### 构建生产版本

```bash
npm run build
npm start
```

## 📁 项目结构

```
ai-tech-explorer/
├── src/                    # 源代码
│   ├── app/               # Next.js App Router 页面
│   ├── components/        # React 组件
│   │   ├── ui/           # 基础 UI 组件
│   │   ├── layout/       # 布局组件
│   │   └── blog/         # 博客相关组件
│   ├── lib/              # 工具函数和配置
│   └── types/            # TypeScript 类型定义
├── content/              # 内容文件
│   └── blog/            # 博客文章 (MDX)
├── public/               # 静态资源
│   └── images/          # 图片资源
└── ...
```

## 📝 内容管理

### 添加新文章

1. 在 `content/blog/YYYY/MM/` 目录下创建 `.mdx` 文件
2. 添加 frontmatter 元数据：

```yaml
---
title: "文章标题"
description: "文章描述"
date: "YYYY-MM-DD"
author: "作者姓名"
tags: ["标签1", "标签2"]
categories: ["分类"]
featured: false
status: "published"
---
```

3. 编写 Markdown 内容

### 文章分类

- **AI技术**: 深度技术解析和原理讲解
- **工具评测**: AI工具对比和使用指南
- **行业趋势**: AI行业动态和发展趋势
- **职业指导**: AI领域职业发展和求职建议

## 🎨 设计系统

### 色彩方案

- **Primary**: 技术蓝 (#3B82F6)
- **Secondary**: 创新绿 (#10B981)
- **Accent**: 活力橙 (#F59E0B)

### 字体

- **Sans-serif**: Inter + Noto Sans SC
- **Monospace**: JetBrains Mono

### 组件库

- `Button`: 按钮组件，支持多种样式和大小
- `Card`: 卡片组件，用于内容展示
- `Badge`: 标签组件，用于分类和状态显示

## 🛠️ 技术栈

### 核心框架

- **Next.js 14**: React 全栈框架
- **TypeScript**: 类型安全的 JavaScript
- **Tailwind CSS**: 实用优先的 CSS 框架

### 内容管理

- **MDX**: Markdown + JSX 支持
- **Gray Matter**: Frontmatter 解析
- **Reading Time**: 阅读时间计算

### 开发工具

- **ESLint**: 代码质量检查
- **Prettier**: 代码格式化
- **Husky**: Git Hooks 管理

## 🔧 配置

### 环境变量

复制 `.env.local.example` 为 `.env.local` 并配置：

```env
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_GA_ID=your-google-analytics-id
```

### SEO 优化

- 自动生成 sitemap.xml
- Open Graph 元标签
- Twitter Card 支持
- 结构化数据 (JSON-LD)

## 📊 性能优化

- **静态站点生成**: 预构建所有页面
- **图片优化**: Next.js Image 组件自动优化
- **代码分割**: 自动按路由分割代码
- **缓存策略**: 静态资源长期缓存

## 🚀 部署

### Vercel (推荐)

1. Fork 本项目到您的 GitHub
2. 在 Vercel 中导入项目
3. 配置环境变量
4. 自动部署

### 其他平台

- **Netlify**: 支持静态站点部署
- **AWS Amplify**: 支持全栈应用部署
- **自托管**: 使用 Docker 容器部署

## 📈 分析和监控

### 内置支持

- **Vercel Analytics**: 页面性能分析
- **Google Analytics**: 用户行为分析
- **Web Vitals**: 核心性能指标

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👨‍💼 关于作者

**Lillian Liao** - AI技术专家 & 人才连接者

- 📧 Email: contact@aitechexplorer.com
- 🔗 LinkedIn: [lillian-liao](https://linkedin.com/in/lillian-liao)
- 🐙 GitHub: [@lillianliao](https://github.com/lillianliao)
- 💬 微信: lillian_ai_tech

---

⭐ 如果这个项目对您有帮助，请给个 Star！