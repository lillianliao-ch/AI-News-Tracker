'use client';

// 强制动态渲染
export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { HunterLogin, HunterQuickRegister } from '../../components/HunterAuth';

export default function PublishPage() {
  const router = useRouter();
  const [groupId, setGroupId] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const searchParams = new URLSearchParams(window.location.search);
      setGroupId(searchParams.get('groupId'));
      
      // 检查登录状态
      const token = localStorage.getItem('hunter_token');
      if (token) {
        setIsLoggedIn(true);
      } else {
        // 未登录，显示登录提示
        setShowLoginModal(true);
      }
    }
  }, []);
  
  const [postType, setPostType] = useState<'job_seeking' | 'talent_recommendation'>('job_seeking');
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    groupId: ''
  });
  
  useEffect(() => {
    if (groupId) {
      setFormData(prev => ({ ...prev, groupId }));
    }
  }, [groupId]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoginSuccess = (token: string) => {
    setShowLoginModal(false);
    setShowRegisterModal(false);
    setIsLoggedIn(true);
  };

  const handleRegisterSuccess = (token: string) => {
    setShowLoginModal(false);
    setShowRegisterModal(false);
    setIsLoggedIn(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 再次检查登录状态
    if (!isLoggedIn) {
      setShowLoginModal(true);
      setError('请先登录后再发布');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);

    try {
      // 开发环境：模拟发布成功
      // const token = localStorage.getItem('hunter_token');
      // if (!token) {
      //   setError('请先登录后再发布信息');
      //   return;
      // }

      // const response = await fetch('/api/hunter-posts', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${token}`
      //   },
      //   body: JSON.stringify({
      //     type: postType,
      //     title: formData.title,
      //     content: formData.content
      //   })
      // });

      // const data = await response.json();

      // if (!response.ok) {
      //   throw new Error(data.error || '发布失败');
      // }

      // if (data.success) {
      //   alert('发布成功！信息已在首页显示');
      //   // 如果是从群组页面跳转过来的，返回并刷新
      //   if (groupId) {
      //     router.push(`/mobile/hunter-share/group/${groupId}`);
      //   } else {
      //     router.back();
      //   }
      // } else {
      //   throw new Error(data.error || '发布失败');
      // }
      
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // 模拟发布成功
      alert('发布成功！（演示模式）');
      router.back();
    } catch (err) {
      console.error('Error publishing post:', err);
      setError(err instanceof Error ? err.message : '发布失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
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
            <h1 className="text-lg font-semibold text-gray-900">发布信息</h1>
            <div className="w-12"></div>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-4 space-y-6">
        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <span className="text-red-600">⚠️</span>
              <span className="text-red-800 text-sm">{error}</span>
            </div>
          </div>
        )}

        {/* Group Info */}
        {groupId && (
          <div className="bg-white rounded-2xl mx-2 p-4 shadow-sm mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gray-900 rounded-full flex items-center justify-center">
                <span className="text-white text-lg">👥</span>
              </div>
              <div>
                <div className="font-medium text-gray-900">发布到群组</div>
                <div className="text-sm text-gray-500">互联网技术人才群</div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Type Selection */}
        <div className="bg-white rounded-2xl mx-2 p-6 shadow-sm">
          <h3 className="font-medium text-gray-900 mb-4">信息类型</h3>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setPostType('job_seeking')}
              className={`p-4 rounded-2xl border-2 transition-all ${
                postType === 'job_seeking'
                  ? 'bg-blue-50 border-blue-500'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <div className="text-center">
                <div className="text-3xl mb-2">🔍</div>
                <div className="font-semibold text-gray-900">找人才</div>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setPostType('talent_recommendation')}
              className={`p-4 rounded-2xl border-2 transition-all ${
                postType === 'talent_recommendation'
                  ? 'bg-green-50 border-green-500'
                  : 'border-gray-200 hover:border-green-300'
              }`}
            >
              <div className="text-center">
                <div className="text-3xl mb-2">👥</div>
                <div className="font-semibold text-gray-900">推人才</div>
              </div>
            </button>
          </div>
        </div>

        {/* Form Fields */}
        <div className="bg-white rounded-2xl mx-2 p-6 shadow-sm space-y-6">
          {/* Title */}
          <div>
            <label className="block text-base font-medium text-gray-900 mb-3">
              {postType === 'job_seeking' ? '职位标题' : '候选人描述'} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder={postType === 'job_seeking' ? '如：资深前端工程师' : '如：5年React开发经验'}
              className="w-full px-4 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
            />
          </div>


          {/* Content */}
          <div>
            <label className="block text-base font-medium text-gray-900 mb-3">
              详细描述 <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={6}
              value={formData.content}
              onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
              placeholder={postType === 'job_seeking' 
                ? '职位要求：\n• 5年以上前端开发经验\n• 熟练掌握React、TypeScript\n• 有团队管理经验优先\n...' 
                : '候选人介绍：\n• 8年前端开发经验\n• 擅长React、Vue技术栈\n• 曾在字节跳动、阿里工作\n...'
              }
              className="w-full px-4 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
            <div className="text-sm text-gray-500 mt-2">建议详细描述，便于匹配合适的人选</div>
          </div>

        </div>

        {/* Submit Button */}
        <div className="sticky bottom-0 bg-white p-4 border-t border-gray-100">
          <div className="mx-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full py-4 rounded-2xl font-semibold text-lg transition-all transform active:scale-95 ${
                isSubmitting 
                  ? 'bg-gray-400 text-gray-200 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl'
              }`}
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-5 h-5 border-2 border-gray-300 border-t-transparent rounded-full animate-spin"></div>
                  <span>发布中...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center space-x-2">
                  <span>🚀</span>
                  <span>发布信息</span>
                </div>
              )}
            </button>
            <p className="text-sm text-gray-500 text-center mt-3 leading-relaxed">
              信息将立即发布到首页，其他猎头可以看到并联系您
            </p>
          </div>
        </div>
      </form>

      {/* Login Modal */}
      {showLoginModal && (
        <HunterLogin
          onSuccess={handleLoginSuccess}
          onCancel={() => {
            setShowLoginModal(false);
            router.back();
          }}
          onRegister={() => {
            setShowLoginModal(false);
            setShowRegisterModal(true);
          }}
        />
      )}

      {/* Register Modal */}
      {showRegisterModal && (
        <HunterQuickRegister
          onSuccess={handleRegisterSuccess}
          onCancel={() => {
            setShowRegisterModal(false);
            router.back();
          }}
        />
      )}
    </div>
  );
}