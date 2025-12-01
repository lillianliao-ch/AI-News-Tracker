'use client';

import { useState, useEffect } from 'react';

interface PendingPost {
  id: string;
  type: 'job_seeking' | 'talent_recommendation';
  title: string;
  content: string;
  contactInfo: string;
  publisherName: string;
  publisherPhone: string;
  publisherStatus: 'registered' | 'verified';
  createdAt: string;
}

interface PendingUser {
  id: string;
  name: string;
  phone: string;
  wechatInfo: string;
  registeredAt: string;
  reason: string;
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'posts' | 'users'>('posts');
  const [pendingPosts, setPendingPosts] = useState<PendingPost[]>([]);
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);

  const mockPendingPosts: PendingPost[] = [
    {
      id: '1',
      type: 'job_seeking',
      title: '急招高级Java工程师',
      content: '知名互联网公司急招高级Java工程师，要求5年+开发经验，熟悉SpringBoot、微服务架构，base杭州，年薪35-50w，股票期权，有合适人选请尽快联系',
      contactInfo: '微信: java_hunter_2024',
      publisherName: '张猎头',
      publisherPhone: '138****1234',
      publisherStatus: 'registered',
      createdAt: '10分钟前'
    },
    {
      id: '2',
      type: 'talent_recommendation',
      title: '推荐优秀前端架构师',
      content: '推荐前端架构师，8年前端经验，前腾讯T3.2，擅长React/Vue生态，有大型项目架构经验，目前在找新机会，期望在一线城市发展',
      contactInfo: '电话: 186****5678',
      publisherName: '李HR',
      publisherPhone: '186****5678',
      publisherStatus: 'verified',
      createdAt: '25分钟前'
    }
  ];

  const mockPendingUsers: PendingUser[] = [
    {
      id: '1',
      name: '王小明',
      phone: '139****7890',
      wechatInfo: 'wxid_example123',
      registeredAt: '2小时前',
      reason: '希望加入猎头协作群，专注互联网人才推荐'
    },
    {
      id: '2',
      name: '陈美丽',
      phone: '188****4567',
      wechatInfo: 'wxid_example456',
      registeredAt: '3小时前',
      reason: '资深HR，在人力资源行业5年经验'
    }
  ];

  useEffect(() => {
    setPendingPosts(mockPendingPosts);
    setPendingUsers(mockPendingUsers);
  }, []);

  const handleApprovePost = (postId: string) => {
    setPendingPosts(prev => prev.filter(post => post.id !== postId));
    // TODO: 实际审核逻辑
    alert('信息已通过审核');
  };

  const handleRejectPost = (postId: string) => {
    const reason = prompt('请输入拒绝原因:');
    if (reason) {
      setPendingPosts(prev => prev.filter(post => post.id !== postId));
      // TODO: 实际拒绝逻辑
      alert('信息已拒绝');
    }
  };

  const handleApproveUser = (userId: string) => {
    setPendingUsers(prev => prev.filter(user => user.id !== userId));
    // TODO: 实际审核逻辑
    alert('用户已通过审核');
  };

  const handleRejectUser = (userId: string) => {
    const reason = prompt('请输入拒绝原因:');
    if (reason) {
      setPendingUsers(prev => prev.filter(user => user.id !== userId));
      // TODO: 实际拒绝逻辑
      alert('用户已拒绝');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold text-gray-900">审核管理</h1>
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">
                  {pendingPosts.length + pendingUsers.length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex bg-gray-50 mx-4 rounded-lg p-1 mb-2">
          <button
            onClick={() => setActiveTab('posts')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all relative ${
              activeTab === 'posts'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600'
            }`}
          >
            信息审核
            {pendingPosts.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-white text-xs flex items-center justify-center">
                {pendingPosts.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all relative ${
              activeTab === 'users'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600'
            }`}
          >
            用户审核
            {pendingUsers.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-white text-xs flex items-center justify-center">
                {pendingUsers.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'posts' ? (
          <div className="space-y-4">
            {pendingPosts.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">📭</div>
                <div className="text-gray-500">暂无待审核信息</div>
              </div>
            ) : (
              pendingPosts.map((post) => (
                <div key={post.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  {/* Post Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${
                        post.type === 'job_seeking' 
                          ? 'bg-orange-100 text-orange-700' 
                          : 'bg-green-100 text-green-700'
                      }`}>
                        <span>{post.type === 'job_seeking' ? '🔍' : '👨‍💼'}</span>
                        <span>{post.type === 'job_seeking' ? '找人才' : '推人才'}</span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">{post.createdAt}</div>
                  </div>

                  {/* Post Content */}
                  <h3 className="font-semibold text-gray-900 mb-2">{post.title}</h3>
                  <p className="text-gray-700 text-sm mb-3 leading-relaxed">{post.content}</p>


                  {/* Publisher Info */}
                  <div className="bg-gray-50 rounded-lg p-3 mb-4">
                    <div className="text-sm text-gray-600 mb-1">发布者信息</div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{post.publisherName}</div>
                        <div className="text-xs text-gray-500">{post.publisherPhone}</div>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs ${
                        post.publisherStatus === 'verified' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {post.publisherStatus === 'verified' ? '✅ 已认证' : '⏳ 待认证'}
                      </div>
                    </div>
                    <div className="text-sm text-gray-700 mt-2">
                      <span className="font-medium">联系方式:</span> {post.contactInfo}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-3">
                    <button
                      onClick={() => handleApprovePost(post.id)}
                      className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
                    >
                      ✅ 通过
                    </button>
                    <button
                      onClick={() => handleRejectPost(post.id)}
                      className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 transition-colors"
                    >
                      ❌ 拒绝
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {pendingUsers.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">👥</div>
                <div className="text-gray-500">暂无待审核用户</div>
              </div>
            ) : (
              pendingUsers.map((user) => (
                <div key={user.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 text-lg">👤</span>
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.phone}</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">{user.registeredAt}</div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-3 mb-4">
                    <div className="text-sm text-gray-600 mb-2">申请说明</div>
                    <div className="text-sm text-gray-900">{user.reason}</div>
                  </div>

                  <div className="text-xs text-gray-500 mb-4">
                    微信信息: {user.wechatInfo}
                  </div>

                  <div className="flex space-x-3">
                    <button
                      onClick={() => handleApproveUser(user.id)}
                      className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
                    >
                      ✅ 通过审核
                    </button>
                    <button
                      onClick={() => handleRejectUser(user.id)}
                      className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 transition-colors"
                    >
                      ❌ 拒绝申请
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}