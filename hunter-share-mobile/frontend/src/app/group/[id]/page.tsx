'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';

interface Post {
  id: string;
  type: 'job_seeking' | 'talent_recommendation';
  title: string;
  content: string;
  publisherName: string;
  viewCount: number;
  createdAt: string;
}

interface GroupInfo {
  id: string;
  name: string;
  description: string;
  memberCount: number;
}

export default function GroupDetailPage() {
  const router = useRouter();
  const params = useParams();
  const groupId = params.id as string;
  
  const [groupInfo, setGroupInfo] = useState<GroupInfo | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPosts, setExpandedPosts] = useState<Set<string>>(new Set());

  // Mock data based on group ID
  const mockGroupData: Record<string, GroupInfo> = {
    '1': {
      id: '1',
      name: '互联网技术人才群',
      description: '专注互联网技术岗位',
      memberCount: 128
    },
    '2': {
      id: '2', 
      name: '金融行业精英圈',
      description: '金融投资领域',
      memberCount: 85
    },
    '3': {
      id: '3',
      name: 'AI & 算法专家',
      description: '人工智能方向', 
      memberCount: 156
    }
  };

  const mockPosts: Post[] = [
    {
      id: '1',
      type: 'job_seeking',
      title: '资深前端工程师',
      content: '字节跳动招聘资深前端工程师，要求5年以上React开发经验，熟悉TypeScript、Node.js，有大型项目经验优先。',
      publisherName: '张猎头',
      viewCount: 23,
      createdAt: '2024-01-15T14:20:00Z'
    },
    {
      id: '2',
      type: 'talent_recommendation',
      title: '前端架构师',
      content: '推荐一位8年前端开发经验的架构师，曾在阿里巴巴负责大型电商系统架构设计，精通Vue、React技术栈。',
      publisherName: '李猎头',
      viewCount: 45,
      createdAt: '2024-01-15T14:25:00Z'
    }
  ];

  const fetchPosts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 开发环境：直接使用模拟数据
      // 生产环境：可以取消注释下面的API调用
      
      // const token = localStorage.getItem('hunter_token');
      // const headers: Record<string, string> = {
      //   'Content-Type': 'application/json'
      // };
      // 
      // if (token) {
      //   headers['Authorization'] = `Bearer ${token}`;
      // }
      //
      // const response = await fetch('/api/hunter-posts?limit=20', {
      //   headers
      // });
      //
      // const data = await response.json();
      // 
      // if (data.success) {
      //   setPosts(data.data);
      // } else {
      //   throw new Error(data.error || '获取信息失败');
      // }
      
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // 使用模拟数据
      setPosts(mockPosts);
    } catch (err) {
      console.error('Error fetching posts:', err);
      // 不显示错误提示，直接使用模拟数据
      setPosts(mockPosts);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load group info
    const group = mockGroupData[groupId];
    if (group) {
      setGroupInfo(group);
    }
    
    // 获取真实数据
    fetchPosts();
  }, [groupId]);

  // 监听页面焦点变化，用于从发布页面返回时刷新数据
  useEffect(() => {
    const handleFocus = () => {
      fetchPosts();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
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

  const handlePublishClick = () => {
    router.push(`/publish?groupId=${groupId}`);
  };

  const togglePostExpand = (postId: string) => {
    setExpandedPosts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(postId)) {
        newSet.delete(postId);
      } else {
        newSet.add(postId);
      }
      return newSet;
    });
  };

  if (!groupInfo) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">群组不存在</div>
      </div>
    );
  }

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
            <div className="flex-1 text-center">
              <h1 className="text-lg font-semibold text-gray-900">{groupInfo.name}</h1>
              <div className="text-xs text-gray-500">
                👥 {groupInfo.memberCount} 名成员 • {groupInfo.description}
              </div>
            </div>
            <button 
              onClick={handlePublishClick}
              className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center hover:bg-blue-700"
            >
              <span className="text-white text-lg">+</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="pb-20">
        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-8">
            <div className="text-gray-500">加载中...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 mx-4 mt-4">
            <div className="flex items-center space-x-2">
              <span className="text-red-600">⚠️</span>
              <span className="text-red-800 text-sm">{error}</span>
              <button 
                onClick={fetchPosts}
                className="text-red-600 font-medium text-sm underline ml-auto"
              >
                重试
              </button>
            </div>
          </div>
        )}

        {/* Posts List */}
        {!loading && posts.length > 0 && (
          <div className="space-y-3 p-4">
            {posts.map((post) => (
              <div key={post.id} className="bg-white rounded-2xl relative">
                {/* Header with Avatar and Info */}
                <div className="flex items-center p-4 pb-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gray-900 rounded-full flex items-center justify-center">
                      <span className="text-white text-lg">👤</span>
                    </div>
                    <div>
                      <div className="text-base font-medium text-gray-900">{post.publisherName}</div>
                      <div className="flex items-center space-x-1 text-sm text-gray-500">
                        <span>👥</span>
                        <span>专注猎头协作</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Message Card */}
                <div className="px-4 pb-4">
                  <div 
                    className={`rounded-2xl p-4 cursor-pointer transition-all ${
                      post.type === 'job_seeking' 
                        ? 'bg-blue-50 active:bg-blue-100' 
                        : 'bg-green-50 active:bg-green-100'
                    }`}
                    onClick={() => togglePostExpand(post.id)}
                  >
                    {/* Action Type */}
                    <div className="flex items-center space-x-2 mb-3">
                      <span className="text-lg">
                        {post.type === 'job_seeking' ? '🔍' : '👥'}
                      </span>
                      <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-900 text-white">
                        {post.type === 'job_seeking' ? '找人' : '推人'}
                      </span>
                    </div>

                    {/* Job Title */}
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{post.title}</h3>

                    {/* Content */}
                    <div className="relative">
                      <p className={`text-gray-700 text-sm leading-relaxed transition-all duration-300 ${
                        expandedPosts.has(post.id) 
                          ? 'line-clamp-none' 
                          : 'line-clamp-3'
                      }`}>
                        {post.content}
                      </p>
                      
                      {/* Expand/Collapse Indicator */}
                      {post.content.length > 80 && (
                        <div className="flex items-center justify-center mt-2">
                          <span className="text-xs text-gray-500 flex items-center space-x-1">
                            <span>{expandedPosts.has(post.id) ? '收起' : '展开'}</span>
                            <span>{expandedPosts.has(post.id) ? '▲' : '▼'}</span>
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && posts.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📋</div>
            <div className="text-gray-500 text-sm">暂无信息</div>
            <div className="text-gray-400 text-xs mt-1">成为第一个发布信息的人</div>
            <button 
              onClick={handlePublishClick}
              className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg text-sm"
            >
              立即发布
            </button>
          </div>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="flex">
          <button 
            onClick={() => router.push('/')}
            className="flex-1 py-3 text-center"
          >
            <div className="text-gray-400 text-sm">🏠</div>
            <div className="text-gray-400 text-xs mt-1">群组</div>
          </button>
          <button 
            onClick={() => router.push('/my-posts')}
            className="flex-1 py-3 text-center"
          >
            <div className="text-gray-400 text-sm">📋</div>
            <div className="text-gray-400 text-xs mt-1">我的发布</div>
          </button>
        </div>
      </div>
    </div>
  );
}