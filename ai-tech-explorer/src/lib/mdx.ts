import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { BlogPost, BlogMetadata } from '@/types/blog';
import { calculateReadingTime } from './utils';

const contentDirectory = path.join(process.cwd(), 'content');

export async function getPostBySlug(slug: string): Promise<BlogPost | null> {
  try {
    const fullPath = path.join(contentDirectory, 'blog', `${slug}.mdx`);
    const fileContents = fs.readFileSync(fullPath, 'utf8');
    const { data, content } = matter(fileContents);
    
    const metadata = data as BlogMetadata;
    
    return {
      slug,
      title: metadata.title,
      description: metadata.description,
      date: metadata.date,
      lastModified: metadata.lastModified,
      author: metadata.author,
      tags: metadata.tags || [],
      categories: metadata.categories || [],
      featured: metadata.featured || false,
      image: undefined,
      imageAlt: undefined,
      readingTime: calculateReadingTime(content),
      difficulty: metadata.difficulty,
      status: metadata.status || 'published',
      content,
      seo: metadata.seo ? {
        keywords: metadata.seo.keywords || [],
        canonical: metadata.seo.canonical
      } : undefined,
    };
  } catch (error) {
    console.error(`Error reading post ${slug}:`, error);
    return null;
  }
}

export async function getAllPosts(): Promise<BlogPost[]> {
  const posts: BlogPost[] = [];
  const blogDirectory = path.join(contentDirectory, 'blog');
  
  if (!fs.existsSync(blogDirectory)) {
    return posts;
  }
  
  function readPostsFromDirectory(dir: string, relativePath = '') {
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        readPostsFromDirectory(fullPath, path.join(relativePath, file));
      } else if (file.endsWith('.mdx')) {
        const slug = path.join(relativePath, file.replace('.mdx', ''));
        try {
          const fileContents = fs.readFileSync(fullPath, 'utf8');
          const { data, content } = matter(fileContents);
          const metadata = data as BlogMetadata;
          
          if (metadata.status !== 'draft') {
            posts.push({
              slug,
              title: metadata.title,
              description: metadata.description,
              date: metadata.date,
              lastModified: metadata.lastModified,
              author: metadata.author,
              tags: metadata.tags || [],
              categories: metadata.categories || [],
              featured: metadata.featured || false,
              image: metadata.image,
              imageAlt: metadata.imageAlt,
              readingTime: calculateReadingTime(content),
              difficulty: metadata.difficulty,
              status: metadata.status || 'published',
              content,
              seo: metadata.seo ? {
                keywords: metadata.seo.keywords || [],
                canonical: metadata.seo.canonical
              } : undefined,
            });
          }
        } catch (error) {
          console.error(`Error reading post ${slug}:`, error);
        }
      }
    }
  }
  
  readPostsFromDirectory(blogDirectory);
  
  // 按日期排序，最新的在前
  return posts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

export async function getFeaturedPosts(): Promise<BlogPost[]> {
  const allPosts = await getAllPosts();
  return allPosts.filter(post => post.featured).slice(0, 3);
}

export async function getPostsByCategory(category: string): Promise<BlogPost[]> {
  const allPosts = await getAllPosts();
  return allPosts.filter(post => post.categories.includes(category));
}

export async function getPostsByTag(tag: string): Promise<BlogPost[]> {
  const allPosts = await getAllPosts();
  return allPosts.filter(post => post.tags.includes(tag));
}

export async function getAllTags(): Promise<string[]> {
  const allPosts = await getAllPosts();
  const tags = new Set<string>();
  
  allPosts.forEach(post => {
    post.tags.forEach(tag => tags.add(tag));
  });
  
  return Array.from(tags).sort();
}

export async function getAllCategories(): Promise<string[]> {
  const allPosts = await getAllPosts();
  const categories = new Set<string>();
  
  allPosts.forEach(post => {
    post.categories.forEach(category => categories.add(category));
  });
  
  return Array.from(categories).sort();
}