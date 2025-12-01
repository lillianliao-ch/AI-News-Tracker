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
    wechat?: string;
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

export interface NavigationItem {
  name: string;
  href: string;
  external?: boolean;
}

export interface Service {
  id: string;
  title: string;
  description: string;
  icon: string;
  features: string[];
  price: string;
  cta: string;
}