import { SiteConfig } from '@/types/site';

export const siteConfig: SiteConfig = {
  name: 'AI Tech Explorer',
  title: 'AI Tech Explorer - AI技术分享与人才服务',
  description: '专业的AI技术博客，提供深度技术解析、工具评测和职业指导。连接AI技术与人才需求。',
  url: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
  language: 'zh-CN',
  author: 'Lillian Liao',
  keywords: [
    'AI',
    '人工智能', 
    '技术博客',
    '大语言模型',
    'LLM',
    '机器学习',
    '深度学习',
    'ChatGPT',
    '技术招聘',
    '职业指导',
    'AI工具评测',
    '提示工程'
  ],
  social: {
    twitter: '@lillian_ai',
    github: 'lillianliao',
    linkedin: 'lillian-liao',
    wechat: 'lillian_ai_tech'
  },
  analytics: {
    google: process.env.NEXT_PUBLIC_GA_ID,
    vercel: true
  },
  features: {
    newsletter: true,
    comments: true,
    search: true,
    darkMode: true
  }
};

export const navigation = [
  { name: '首页', href: '/' },
  { name: '博客', href: '/blog' },
  { name: '关于', href: '/about' },
  { name: '联系', href: '/contact' },
];

export const categories = [
  {
    id: 'ai-tech',
    name: 'AI技术',
    slug: 'ai-tech',
    description: '人工智能核心技术解析',
    color: '#3B82F6',
    order: 1,
  },
  {
    id: 'tools-review',
    name: '工具评测',
    slug: 'tools-review',
    description: 'AI工具深度评测和对比',
    color: '#10B981',
    order: 2,
  },
  {
    id: 'industry-trends',
    name: '行业趋势',
    slug: 'industry-trends',
    description: 'AI行业动态和发展趋势',
    color: '#F59E0B',
    order: 3,
  },
  {
    id: 'career-guide',
    name: '职业指导',
    slug: 'career-guide',
    description: 'AI领域职业发展指导',
    color: '#EF4444',
    order: 4,
  },
];

export const services = [
  {
    id: 'tech-consulting',
    title: '技术咨询',
    description: 'AI产品策略规划、技术架构设计评审、团队技术能力提升',
    icon: '🎯',
    features: [
      'AI产品策略规划',
      '技术架构设计评审',
      '团队技术能力提升',
      'AI项目落地指导'
    ],
    price: '500-2000元/小时',
    cta: '了解详情'
  },
  {
    id: 'recruitment',
    title: '招聘服务',
    description: 'AI人才精准匹配、简历优化面试指导、薪资谈判策略',
    icon: '💼',
    features: [
      'AI人才精准匹配',
      '简历优化与面试指导',
      '薪资谈判策略',
      '职业发展规划'
    ],
    price: '年薪15-25%',
    cta: '立即咨询'
  }
];