# AI Tech Explorer - UI设计和组件规划文档

## 设计系统 (Design System)

### 品牌色彩
```css
/* Primary Colors - 技术蓝 */
--primary-50: #eff6ff;
--primary-100: #dbeafe;
--primary-500: #3b82f6;   /* 主色 */
--primary-600: #2563eb;
--primary-700: #1d4ed8;

/* Secondary Colors - 创新绿 */
--secondary-500: #10b981;
--secondary-600: #059669;

/* Accent Colors - 活力橙 */
--accent-500: #f59e0b;
--accent-600: #d97706;

/* Neutral Colors */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-800: #1f2937;
--gray-900: #111827;
```

### 字体系统
```css
/* 中文优先字体栈 */
--font-sans: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;

/* 字体大小 */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
--text-3xl: 1.875rem;   /* 30px */
--text-4xl: 2.25rem;    /* 36px */
```

### 间距系统
```css
/* 8px 基础单位 */
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
```

## 页面布局和线框图

### 1. 首页 (Home Page)

```
┌─────────────────────────────────────────────────────┐
│                    Header                            │
│  [Logo] [导航]              [搜索] [深色模式] [联系]    │
├─────────────────────────────────────────────────────┤
│                  Hero Section                       │
│              AI Tech Explorer                       │
│        AI技术分享者 & 人才连接专家                     │
│                                                     │
│      [技术博客] [招聘服务] [关于我] [订阅Newsletter]    │
│                                                     │
│               个人头像 + 简介                         │
├─────────────────────────────────────────────────────┤
│               Featured Articles                     │
│  精选文章 (3篇)                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ 文章1    │ │ 文章2    │ │ 文章3    │              │
│  │ 封面图   │ │ 封面图   │ │ 封面图   │              │
│  │ 标题     │ │ 标题     │ │ 标题     │              │
│  │ 摘要     │ │ 摘要     │ │ 摘要     │              │
│  └─────────┘ └─────────┘ └─────────┘              │
├─────────────────────────────────────────────────────┤
│                  Services                           │
│               我的服务介绍                           │
│  ┌─────────────┐  ┌─────────────┐                 │
│  │ 技术咨询    │  │ 招聘服务     │                 │
│  │ 图标+描述   │  │ 图标+描述    │                 │
│  └─────────────┘  └─────────────┘                 │
├─────────────────────────────────────────────────────┤
│               Recent Posts                          │
│               最新文章 (6篇)                        │
│  ┌───────┐ ┌───────┐ ┌───────┐                   │
│  │ 文章卡片│ │ 文章卡片│ │ 文章卡片│                   │
│  └───────┘ └───────┘ └───────┘                   │
├─────────────────────────────────────────────────────┤
│                   Footer                            │
│     [社交链接] [订阅] [版权信息] [友情链接]           │
└─────────────────────────────────────────────────────┘
```

### 2. 博客列表页 (Blog List)

```
┌─────────────────────────────────────────────────────┐
│                    Header                            │
├─────────────────────────────────────────────────────┤
│               Blog Header                            │
│                技术博客                              │
│           分享AI技术洞察和实践经验                     │
├─────────────────────────────────────────────────────┤
│  [搜索框]          [分类筛选] [标签筛选] [排序]       │
├─────────────────────────────────────────────────────┤
│  ┌─左侧文章列表─────────────┐  ┌─右侧侧边栏───┐     │
│  │                         │  │               │     │
│  │ ┌─────────────────────┐ │  │ 分类导航      │     │
│  │ │ 文章1              │ │  │ ├ AI技术      │     │
│  │ │ [封面] [标题]      │ │  │ ├ 工具评测    │     │
│  │ │ [摘要] [标签] [日期]│ │  │ ├ 行业趋势    │     │
│  │ └─────────────────────┘ │  │ └ 职业指导    │     │
│  │                         │  │               │     │
│  │ ┌─────────────────────┐ │  │ 热门标签      │     │
│  │ │ 文章2              │ │  │ #LLM #GPT     │     │
│  │ └─────────────────────┘ │  │ #招聘 #面试   │     │
│  │                         │  │               │     │
│  │ ┌─────────────────────┐ │  │ 最新评论      │     │
│  │ │ 文章3              │ │  │ ...           │     │
│  │ └─────────────────────┘ │  │               │     │
│  │                         │  │ Newsletter    │     │
│  │      [加载更多]          │  │ 订阅表单      │     │
│  └─────────────────────────┘  └───────────────┘     │
├─────────────────────────────────────────────────────┤
│                   Footer                            │
└─────────────────────────────────────────────────────┘
```

### 3. 文章详情页 (Blog Post)

```
┌─────────────────────────────────────────────────────┐
│                    Header                            │
├─────────────────────────────────────────────────────┤
│               Article Header                         │
│                  文章标题                           │
│         [作者] [发布日期] [阅读时间] [分类]          │
│                  封面图片                           │
├─────────────────────────────────────────────────────┤
│  ┌─左侧文章内容─────────────┐  ┌─右侧目录───┐     │
│  │                         │  │             │     │
│  │ # 文章内容              │  │ 文章目录    │     │
│  │                         │  │ 1. 章节1   │     │
│  │ 正文内容...             │  │ 2. 章节2   │     │
│  │                         │  │   2.1 子节 │     │
│  │ ```code```              │  │ 3. 章节3   │     │
│  │                         │  │             │     │
│  │ > 引用块                │  │ 分享文章    │     │
│  │                         │  │ [微信][微博] │     │
│  │ ![图片](url)            │  │             │     │
│  │                         │  │ 作者卡片    │     │
│  │                         │  │ [头像+简介]  │     │
│  │                         │  │             │     │
│  │ [标签] [上一篇] [下一篇] │  │ 相关文章    │     │
│  └─────────────────────────┘  │ 1. 文章A   │     │
│                               │ 2. 文章B   │     │
│              评论区           │ 3. 文章C   │     │
│         [评论组件]            └─────────────┘     │
├─────────────────────────────────────────────────────┤
│                   Footer                            │
└─────────────────────────────────────────────────────┘
```

### 4. 关于页面 (About Page)

```
┌─────────────────────────────────────────────────────┐
│                    Header                            │
├─────────────────────────────────────────────────────┤
│                About Hero                           │
│              [大头照]                               │
│            Lillian Liao                            │
│         AI技术专家 & 人才连接者                      │
├─────────────────────────────────────────────────────┤
│                个人介绍                             │
│            [个人故事和专业背景]                      │
├─────────────────────────────────────────────────────┤
│  ┌─专业技能─┐ ┌─工作经历─┐ ┌─服务内容─┐         │
│  │ 技能列表 │ │ 公司经历 │ │ 咨询服务 │         │
│  │ LLM     │ │ Google  │ │ 技术招聘 │         │
│  │ Python  │ │ 字节跳动 │ │ 职业规划 │         │
│  │ 产品策略 │ │ 自由职业 │ │ 技术分享 │         │
│  └─────────┘ └─────────┘ └─────────┘         │
├─────────────────────────────────────────────────────┤
│                成功案例                             │
│              [客户评价和案例]                        │
├─────────────────────────────────────────────────────┤
│                联系方式                             │
│        [邮箱] [微信] [LinkedIn] [GitHub]          │
└─────────────────────────────────────────────────────┘
```

## 组件库设计

### 基础UI组件 (components/ui/)

#### Button组件
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
}
```

#### Card组件
```typescript
interface CardProps {
  title?: string;
  description?: string;
  image?: string;
  href?: string;
  tags?: string[];
  children: React.ReactNode;
}
```

#### Badge组件
```typescript
interface BadgeProps {
  variant: 'primary' | 'secondary' | 'success' | 'warning';
  size: 'sm' | 'md';
  children: React.ReactNode;
}
```

### 布局组件 (components/layout/)

#### Header组件
```typescript
interface HeaderProps {
  sticky?: boolean;
  transparent?: boolean;
}

// 包含:
// - Logo
// - 导航菜单 (响应式)
// - 搜索框
// - 深色模式切换
// - 移动端汉堡菜单
```

#### Footer组件
```typescript
interface FooterProps {
  showNewsletter?: boolean;
  showSocial?: boolean;
}

// 包含:
// - 社交链接
// - Newsletter订阅
// - 版权信息
// - 友情链接
```

#### Sidebar组件
```typescript
interface SidebarProps {
  position: 'left' | 'right';
  children: React.ReactNode;
}
```

### 博客组件 (components/blog/)

#### ArticleCard组件
```typescript
interface ArticleCardProps {
  post: {
    title: string;
    description: string;
    date: string;
    readingTime: number;
    tags: string[];
    image?: string;
    slug: string;
  };
  variant: 'featured' | 'list' | 'grid';
}
```

#### ArticleList组件
```typescript
interface ArticleListProps {
  posts: BlogPost[];
  pagination?: {
    current: number;
    total: number;
    pageSize: number;
  };
  filters?: {
    category?: string;
    tag?: string;
    search?: string;
  };
}
```

#### CategoryFilter组件
```typescript
interface CategoryFilterProps {
  categories: Category[];
  selected?: string;
  onChange: (category: string) => void;
}
```

#### SearchBox组件
```typescript
interface SearchBoxProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  suggestions?: string[];
}
```

#### TableOfContents组件
```typescript
interface TableOfContentsProps {
  headings: {
    id: string;
    text: string;
    level: number;
  }[];
  activeId?: string;
}
```

## 响应式设计策略

### 断点系统
```css
/* Tailwind CSS 断点 */
sm: 640px   /* 平板竖屏 */
md: 768px   /* 平板横屏 */
lg: 1024px  /* 笔记本 */
xl: 1280px  /* 桌面 */
2xl: 1536px /* 大屏 */
```

### 移动端优化
1. **导航**: 汉堡菜单 + 侧边栏
2. **卡片**: 单列布局
3. **字体**: 适当增大基础字号
4. **间距**: 减少垂直间距
5. **触控**: 增大点击区域

### 桌面端优化
1. **布局**: 多列网格
2. **侧边栏**: 固定位置TOC和过滤器
3. **悬停**: 丰富的交互反馈
4. **键盘**: 完整的快捷键支持

## 深色模式设计

### 色彩适配
```css
/* 深色模式变量 */
.dark {
  --bg-primary: #111827;
  --bg-secondary: #1f2937;
  --text-primary: #f9fafb;
  --text-secondary: #d1d5db;
  --border: #374151;
}
```

### 图片处理
- 自动调整图片亮度
- 代码块深色主题
- Logo暗色版本

## 性能优化

### 图片优化
- Next.js Image组件
- WebP格式支持
- 响应式图片
- 懒加载策略

### 字体优化
- 字体预加载
- 字体显示策略
- Web字体优化

### 代码分割
- 页面级分割
- 组件级分割
- 第三方库分割

---

**文档版本**: v1.0  
**创建日期**: 2025-01-07  
**UI设计师**: Lillian Liao