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

export interface BlogMetadata {
  title: string;
  description: string;
  date: string;
  lastModified?: string;
  author: string;
  tags: string[];
  categories: string[];
  featured?: boolean;
  image?: string;
  imageAlt?: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  status?: 'draft' | 'published';
  seo?: {
    keywords?: string[];
    canonical?: string;
  };
}