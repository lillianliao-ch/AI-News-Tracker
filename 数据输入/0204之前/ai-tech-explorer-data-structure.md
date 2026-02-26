# AI Tech Explorer - 数据结构设计文档

## 数据存储策略

由于采用静态站点生成 (SSG) 架构，主要使用文件系统作为数据存储，配合少量JSON文件管理元数据。

## 文件系统组织结构

```
content/
├── blog/                  # 博客文章目录
│   ├── 2024/              # 按年份分类
│   │   ├── 12/            # 按月份分类
│   │   │   ├── understanding-llm-attention.mdx
│   │   │   ├── ai-tools-comparison-2024.mdx
│   │   │   └── career-guide-ai-engineer.mdx
│   │   └── 11/
│   │       ├── chatgpt-api-best-practices.mdx
│   │       └── ai-startup-trends.mdx
│   ├── 2025/
│   │   └── 01/
│   │       ├── ai-trends-2025.mdx
│   │       └── prompt-engineering-advanced.mdx
│   ├── categories.json    # 分类元数据
│   ├── tags.json         # 标签元数据
│   └── featured.json     # 精选文章配置
├── pages/                 # 静态页面内容
│   ├── about.mdx         # 关于页面
│   ├── services.mdx      # 服务介绍
│   └── contact.mdx       # 联系页面
└── data/                 # 结构化数据
    ├── author.json       # 作者信息
    ├── site.json         # 站点配置
    └── navigation.json   # 导航配置
```

## MDX文章格式规范

### Frontmatter结构
```yaml
---
title: "理解大语言模型的注意力机制"
description: "深入解析Transformer架构中注意力机制的工作原理，以及在实际应用中的优化策略"
date: "2024-12-15"
lastModified: "2024-12-16"
author: "Lillian Liao"
tags: ["LLM", "Transformer", "注意力机制", "深度学习"]
categories: ["AI技术"]
featured: true
image: "/images/blog/llm-attention-cover.jpg"
imageAlt: "大语言模型注意力机制示意图"
readingTime: 8
difficulty: "中级"
status: "published"
seo:
  keywords: ["LLM", "注意力机制", "Transformer", "BERT", "GPT"]
  canonical: "/blog/2024/12/understanding-llm-attention"
---
```

### Frontmatter字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| title | string | ✅ | 文章标题，用于H1和SEO |
| description | string | ✅ | 文章描述，用于meta description |
| date | string | ✅ | 发布日期，ISO格式 |
| lastModified | string | ❌ | 最后修改日期 |
| author | string | ✅ | 作者名称 |
| tags | string[] | ✅ | 文章标签，用于分类和搜索 |
| categories | string[] | ✅ | 文章分类 |
| featured | boolean | ❌ | 是否为精选文章 |
| image | string | ❌ | 封面图片路径 |
| imageAlt | string | ❌ | 图片alt文本 |
| readingTime | number | ❌ | 预估阅读时间（分钟） |
| difficulty | string | ❌ | 难度等级：初级/中级/高级 |
| status | string | ✅ | 发布状态：draft/published |

## JSON数据文件

### 分类配置 (categories.json)
```json
{
  "categories": [
    {
      "id": "ai-tech",
      "name": "AI技术",
      "slug": "ai-tech",
      "description": "人工智能核心技术解析",
      "color": "#3B82F6",
      "order": 1,
      "count": 0
    },
    {
      "id": "tools-review",
      "name": "工具评测",
      "slug": "tools-review", 
      "description": "AI工具深度评测和对比",
      "color": "#10B981",
      "order": 2,
      "count": 0
    },
    {
      "id": "industry-trends",
      "name": "行业趋势",
      "slug": "industry-trends",
      "description": "AI行业动态和发展趋势",
      "color": "#F59E0B",
      "order": 3,
      "count": 0
    },
    {
      "id": "career-guide",
      "name": "职业指导",
      "slug": "career-guide",
      "description": "AI领域职业发展指导",
      "color": "#EF4444",
      "order": 4,
      "count": 0
    }
  ]
}
```

### 标签配置 (tags.json)
```json
{
  "tags": [
    {
      "id": "llm",
      "name": "LLM",
      "slug": "llm",
      "description": "大语言模型相关内容",
      "category": "ai-tech",
      "count": 0
    },
    {
      "id": "chatgpt",
      "name": "ChatGPT", 
      "slug": "chatgpt",
      "description": "ChatGPT相关技术和应用",
      "category": "tools-review",
      "count": 0
    },
    {
      "id": "prompt-engineering",
      "name": "提示工程",
      "slug": "prompt-engineering",
      "description": "提示工程技巧和实践",
      "category": "ai-tech",
      "count": 0
    }
  ]
}
```

### 作者信息 (author.json)
```json
{
  "name": "Lillian Liao",
  "bio": "AI技术专家 & 人才连接者。专注于大语言模型、AI工具评测和技术招聘服务。",
  "avatar": "/images/author/lillian-avatar.jpg",
  "email": "contact@aitechexplorer.com",
  "social": {
    "github": "https://github.com/lillianliao",
    "linkedin": "https://linkedin.com/in/lillian-liao",
    "twitter": "https://twitter.com/lillian_ai",
    "wechat": "lillian_ai_tech"
  },
  "expertise": [
    "大语言模型",
    "AI工具评测", 
    "技术招聘",
    "产品策略"
  ],
  "experience": {
    "years": 8,
    "companies": ["Google", "ByteDance", "Freelancer"],
    "specialization": "AI技术与人才服务"
  }
}
```

### 站点配置 (site.json)
```json
{
  "name": "AI Tech Explorer",
  "title": "AI Tech Explorer - AI技术分享与人才服务",
  "description": "专业的AI技术博客，提供深度技术解析、工具评测和职业指导。连接AI技术与人才需求。",
  "url": "https://aitechexplorer.com",
  "language": "zh-CN",
  "author": "Lillian Liao",
  "keywords": ["AI", "技术博客", "机器学习", "人工智能", "技术招聘"],
  "social": {
    "twitter": "@lillian_ai",
    "github": "lillianliao", 
    "linkedin": "lillian-liao"
  },
  "analytics": {
    "google": "G-XXXXXXXXXX",
    "vercel": true
  },
  "features": {
    "newsletter": true,
    "comments": true,
    "search": true,
    "darkMode": true
  }
}
```

## TypeScript类型定义

### 博客相关类型 (types/blog.ts)
```typescript
export interface BlogPost {
  slug: string;
  title: string;
  description: string;
  date: string;
  lastModified?: string;
  author: string;
  tags: string[];
  categories: string[];
  featured: boolean;
  image?: string;
  imageAlt?: string;
  readingTime?: number;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  status: 'draft' | 'published';
  content: string;
  seo?: {
    keywords: string[];
    canonical?: string;
  };
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string;
  color: string;
  order: number;
  count: number;
}

export interface Tag {
  id: string;
  name: string;
  slug: string;
  description: string;
  category: string;
  count: number;
}

export interface Author {
  name: string;
  bio: string;
  avatar: string;
  email: string;
  social: {
    github?: string;
    linkedin?: string;
    twitter?: string;
    wechat?: string;
  };
  expertise: string[];
  experience: {
    years: number;
    companies: string[];
    specialization: string;
  };
}
```

### 站点配置类型 (types/site.ts)
```typescript
export interface SiteConfig {
  name: string;
  title: string;
  description: string;
  url: string;
  language: string;
  author: string;
  keywords: string[];
  social: {
    twitter?: string;
    github?: string;
    linkedin?: string;
  };
  analytics: {
    google?: string;
    vercel: boolean;
  };
  features: {
    newsletter: boolean;
    comments: boolean;
    search: boolean;
    darkMode: boolean;
  };
}
```

## 数据处理逻辑

### 文章数据获取 (lib/blog.ts)
```typescript
import fs from 'fs';
import path from 'path';
import { BlogPost } from '@/types/blog';

export async function getAllPosts(): Promise<BlogPost[]> {
  const postsDirectory = path.join(process.cwd(), 'content/blog');
  const posts: BlogPost[] = [];
  
  // 递归读取所有年份和月份目录下的MDX文件
  const years = fs.readdirSync(postsDirectory);
  
  for (const year of years) {
    if (year.endsWith('.json')) continue;
    
    const yearPath = path.join(postsDirectory, year);
    const months = fs.readdirSync(yearPath);
    
    for (const month of months) {
      const monthPath = path.join(yearPath, month);
      const files = fs.readdirSync(monthPath);
      
      for (const file of files) {
        if (file.endsWith('.mdx')) {
          const post = await getPostBySlug(`${year}/${month}/${file.replace('.mdx', '')}`);
          if (post.status === 'published') {
            posts.push(post);
          }
        }
      }
    }
  }
  
  return posts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}
```

## SEO和搜索优化

### URL结构设计
```
https://aitechexplorer.com/blog/2024/12/understanding-llm-attention
https://aitechexplorer.com/blog/category/ai-tech
https://aitechexplorer.com/blog/tag/llm
https://aitechexplorer.com/about
https://aitechexplorer.com/contact
```

### 元数据生成
- 自动生成 Open Graph 标签
- Twitter Card 元数据
- JSON-LD 结构化数据
- XML Sitemap
- RSS Feed

## 数据迁移和备份策略

### 版本控制
- 所有内容文件使用 Git 管理
- 定期备份到云存储
- 支持内容回滚和历史查看

### 数据导入/导出
- 支持从其他博客平台导入
- 提供数据导出功能
- 批量处理工具

---

**文档版本**: v1.0  
**创建日期**: 2025-01-07  
**数据架构师**: Lillian Liao