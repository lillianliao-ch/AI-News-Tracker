'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface MyPost {
  id: string;
  type: 'job_seeking' | 'talent_recommendation';
  title: string;
  content: string;
  viewCount: number;
  createdAt: string;
}

export default function MyPostsPage() {
  const router = useRouter();
  const [posts, setPosts] = useState<MyPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMyPosts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 开发环境：使用模拟数据
      // const token = localStorage.getItem('hunter_token');
      // if (!token) {
      //   setError('请先登录');
      //   return;
      // }

      // // 使用专门的API获取当前用户的发布信息
      // const response = await fetch('/api/hunter-posts/my', {
      //   headers: {
      //     'Authorization': `Bearer ${token}`
      //   }
      // });

      // if (!response.ok) {
      //   throw new Error('获取失败');
      // }

      // const data = await response.json();
      // 
      // if (data.success) {
      //   setPosts(data.data);
      // } else {
      //   throw new Error('API返回错误');
      // }
      
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // 使用模拟数据
      const mockPosts: MyPost[] = [
        {
          id: '1',
          type: 'job_seeking',
          title: '资深前端工程师',
          content: '字节跳动招聘资深前端工程师，要求5年以上React开发经验，熟悉TypeScript、Node.js。',
          viewCount: 23,
          createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
        },
        {
          id: '2',
          type: 'talent_recommendation',
          title: '前端架构师',
          content: '推荐一位8年前端开发经验的架构师，曾在阿里巴巴负责大型电商系统架构设计。',
          viewCount: 45,
          createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
        }
      ];
      
      setPosts(mockPosts);
    } catch (err) {
      console.error('Error fetching my posts:', err);
      // 开发环境不显示错误
      setPosts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyPosts();
  }, []);

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return '刚刚';
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };


  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <button 
              onClick={() => router.back()}
              className="flex items-center space-x-1 text-gray-600"
            >
              <span className="text-lg">←</span>
              <span className="text-sm">返回</span>
            </button>
            <h1 className="text-lg font-semibold text-gray-900">我的发布</h1>
            <div className="w-12"></div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-20">
        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-8">
            <div className="text-gray-500">加载中...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 mt-4">
            <div className="flex items-center space-x-2">
              <span className="text-red-600">⚠️</span>
              <span className="text-red-800 text-sm">{error}</span>
              <button 
                onClick={fetchMyPosts}
                className="text-red-600 font-medium text-sm underline ml-auto"
              >
                重试
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && posts.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📋</div>
            <div className="text-gray-500 text-sm">您还没有发布任何信息</div>
            <button 
              onClick={() => router.push('/mobile/hunter-share/publish')}
              className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg text-sm"
            >
              立即发布
            </button>
          </div>
        )}

        {/* Posts List */}
        {!loading && !error && posts.length > 0 && (
          <div className="space-y-4 mt-4">
            {posts.map((post) => (
              <div key={post.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                {/* Post Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      post.type === 'job_seeking' 
                        ? 'bg-orange-100 text-orange-700' 
                        : 'bg-green-100 text-green-700'
                    }`}>
                      {post.type === 'job_seeking' ? '找人才' : '推人才'}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-xs text-gray-500">{formatRelativeTime(post.createdAt)}</div>
                  </div>
                </div>

                {/* Post Content */}
                <h3 className="font-semibold text-gray-900 mb-2">{post.title}</h3>
                <p className="text-gray-700 text-sm mb-3 leading-relaxed line-clamp-2">{post.content}</p>


                {/* Stats */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-500 text-xs">👁 {post.viewCount} 次查看</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="text-blue-600 text-sm">编辑</button>
                    <button className="text-red-600 text-sm">删除</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="flex">
          <button 
            onClick={() => router.push('/mobile/hunter-share')}
            className="flex-1 py-3 text-center"
          >
            <div className="text-gray-400 text-sm">🏠</div>
            <div className="text-gray-400 text-xs mt-1">首页</div>
          </button>
          <button className="flex-1 py-3 text-center">
            <div className="text-blue-600 text-sm">📋</div>
            <div className="text-blue-600 text-xs mt-1">我的发布</div>
          </button>
        </div>
      </div>
    </div>
  );
}