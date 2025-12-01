import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

interface CardProps {
  title: string;
  description?: string;
  image?: string;
  imageAlt?: string;
  href?: string;
  tags?: string[];
  date?: string;
  readingTime?: number;
  author?: string;
  featured?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  title,
  description,
  image,
  imageAlt,
  href,
  tags,
  date,
  readingTime,
  author,
  featured,
  className,
  children
}) => {
  const CardContent = (
    <div
      className={cn(
        'group relative bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-2xl hover:border-blue-200 transition-all duration-500 overflow-hidden transform hover:-translate-y-1',
        featured && 'ring-2 ring-blue-500 shadow-blue-100',
        className
      )}
    >
      {/* Gradient Header */}
      <div className="relative aspect-video w-full bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative text-center text-white z-10">
          <div className="w-16 h-16 mx-auto mb-3 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div className="text-sm font-medium opacity-90">AI技术洞察</div>
        </div>
        {featured && (
          <div className="absolute top-4 right-4">
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-yellow-400 text-yellow-900 shadow-lg">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
              </svg>
              精选
            </span>
          </div>
        )}
      </div>
      
      <div className="p-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-3 line-clamp-2 group-hover:text-blue-600 transition-colors duration-300">
          {title}
        </h3>
        
        {description && (
          <p className="text-gray-600 text-base mb-6 line-clamp-3 leading-relaxed">
            {description}
          </p>
        )}
        
        {tags && tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {tags.slice(0, 3).map((tag, index) => (
              <span
                key={tag}
                className={cn(
                  "inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium transition-colors duration-200",
                  index === 0 && "bg-blue-100 text-blue-700 hover:bg-blue-200",
                  index === 1 && "bg-green-100 text-green-700 hover:bg-green-200",
                  index === 2 && "bg-purple-100 text-purple-700 hover:bg-purple-200"
                )}
              >
                #{tag}
              </span>
            ))}
            {tags.length > 3 && (
              <span className="text-xs text-gray-500 px-2 py-1">+{tags.length - 3}</span>
            )}
          </div>
        )}
        
        {(date || readingTime || author) && (
          <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t border-gray-100">
            <div className="flex items-center space-x-4">
              {author && (
                <span className="flex items-center font-medium">
                  <svg className="w-4 h-4 mr-1.5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
                  </svg>
                  {author}
                </span>
              )}
              {date && (
                <span className="flex items-center">
                  <svg className="w-4 h-4 mr-1.5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
                  </svg>
                  {new Date(date).toLocaleDateString('zh-CN')}
                </span>
              )}
            </div>
            {readingTime && (
              <span className="flex items-center font-medium text-blue-600">
                <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/>
                </svg>
                {readingTime}分钟
              </span>
            )}
          </div>
        )}
        
        {children}
      </div>
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block">
        {CardContent}
      </Link>
    );
  }

  return CardContent;
};