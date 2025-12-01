'use client';

import { useState } from 'react';

interface AuthResponse {
  success: boolean;
  data?: {
    user: {
      id: string;
      name: string;
      phone: string;
      status: string;
    };
    token: string;
    tempPassword?: string;
  };
  error?: string;
  message?: string;
}

export function HunterQuickRegister({ onSuccess, onCancel }: { 
  onSuccess: (token: string) => void; 
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    wechatId: '',
    reason: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // 演示模式：模拟注册
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 生成模拟token和临时密码
      const mockToken = 'register_token_' + Date.now();
      const tempPassword = 'Demo' + Math.random().toString(36).slice(2, 8);
      
      localStorage.setItem('hunter_token', mockToken);
      alert(`注册成功！（演示模式）\n临时密码：${tempPassword}\n请保存好密码，用于后续登录。`);
      onSuccess(mockToken);
      
      // const response = await fetch('/api/hunter-auth/quick-register', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify(formData)
      // });

      // const data: AuthResponse = await response.json();

      // if (!response.ok) {
      //   throw new Error(data.error || '注册失败');
      // }

      // if (data.success && data.data) {
      //   // Store token
      //   localStorage.setItem('hunter_token', data.data.token);
      //   
      //   // Show temp password if provided
      //   if (data.data.tempPassword) {
      //     alert(`注册成功！临时密码：${data.data.tempPassword}\n请保存好密码，用于后续登录。`);
      //   }
      //   
      //   onSuccess(data.data.token);
      // } else {
      //   throw new Error(data.error || '注册失败');
      // }
    } catch (err) {
      console.error('Registration error:', err);
      setError(err instanceof Error ? err.message : '注册失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-sm max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">快速注册</h2>
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <div className="flex items-center space-x-2">
              <span className="text-red-600">⚠️</span>
              <span className="text-red-800 text-sm">{error}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              姓名 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="请输入真实姓名"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              手机号 <span className="text-red-500">*</span>
            </label>
            <input
              type="tel"
              required
              value={formData.phone}
              onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="用于登录和联系"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">微信授权</label>
            <button
              type="button"
              onClick={async () => {
                // 模拟微信授权
                try {
                  await new Promise(resolve => setTimeout(resolve, 800));
                  const mockWechatId = 'wx_' + Math.random().toString(36).slice(2, 10);
                  setFormData(prev => ({ ...prev, wechatId: mockWechatId }));
                  alert('微信授权成功！（演示模式）\n未来可通过微信直接登录');
                } catch (err) {
                  alert('微信授权失败，请稍后重试');
                }
              }}
              className={`w-full py-3 rounded-lg font-medium flex items-center justify-center space-x-2 ${
                formData.wechatId 
                  ? 'bg-green-500 text-white' 
                  : 'bg-green-500 text-white hover:bg-green-600'
              }`}
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8.5 11.5c.5 0 1-.5 1-1s-.5-1-1-1-1 .5-1 1 .5 1 1 1zm6 0c.5 0 1-.5 1-1s-.5-1-1-1-1 .5-1 1 .5 1 1 1zm4.5-2c0-4.4-4.5-8-10-8S0 5.1 0 9.5c0 2.4 1.2 4.5 3 6l-1 3 3.5-2c1 .3 2 .5 3 .5 5.5.5 10.5-3.1 10.5-7.5zm-4 7c-.5 0-1-.1-1.5-.2l-2.5 1.5.5-2c-1.5-1-2.5-2.5-2.5-4.3 0-3 3-5.5 6.5-5.5S22 10.5 22 13.5 19 19 15.5 19z"/>
              </svg>
              <span>{formData.wechatId ? '✓ 已授权' : '点击授权微信'}</span>
            </button>
            <p className="text-xs text-gray-500 mt-1">
              授权后可通过微信一键登录
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              申请原因 <span className="text-red-500">*</span>
              <span className="text-xs text-gray-500 ml-1">(至少3个字符)</span>
            </label>
            <textarea
              rows={3}
              required
              minLength={3}
              value={formData.reason}
              onChange={(e) => setFormData(prev => ({ ...prev, reason: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="简述申请加入猎头协作平台的原因（至少3个字符）"
            />
            {formData.reason.length > 0 && formData.reason.length < 3 && (
              <p className="text-xs text-red-500 mt-1">
                还需要 {3 - formData.reason.length} 个字符
              </p>
            )}
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`flex-1 py-3 rounded-lg font-medium ${
                isSubmitting
                  ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isSubmitting ? '注册中...' : '提交申请'}
            </button>
          </div>
        </form>

        <p className="text-xs text-gray-500 text-center mt-4">
          提交后等待管理员审核，审核通过后即可发布信息
        </p>
      </div>
    </div>
  );
}

export function HunterLogin({ onSuccess, onCancel, onRegister }: {
  onSuccess: (token: string) => void;
  onCancel: () => void;
  onRegister: () => void;
}) {
  const [formData, setFormData] = useState({
    phone: '',
    password: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // 演示模式：模拟登录
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // 生成模拟token
      const mockToken = 'demo_token_' + Date.now();
      localStorage.setItem('hunter_token', mockToken);
      onSuccess(mockToken);
      
      // const response = await fetch('/api/hunter-auth/login', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify(formData)
      // });

      // const data: AuthResponse = await response.json();

      // if (!response.ok) {
      //   throw new Error(data.error || '登录失败');
      // }

      // if (data.success && data.data) {
      //   localStorage.setItem('hunter_token', data.data.token);
      //   onSuccess(data.data.token);
      // } else {
      //   throw new Error(data.error || '登录失败');
      // }
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : '登录失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleWechatLogin = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      // 演示模式：模拟微信登录
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 生成模拟token
      const mockToken = 'wechat_token_' + Date.now();
      localStorage.setItem('hunter_token', mockToken);
      alert('微信授权登录成功！（演示模式）');
      onSuccess(mockToken);
    } catch (err) {
      console.error('Wechat login error:', err);
      setError('微信登录失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">猎头登录</h2>
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <div className="flex items-center space-x-2">
              <span className="text-red-600">⚠️</span>
              <span className="text-red-800 text-sm">{error}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">手机号</label>
            <input
              type="tel"
              required
              value={formData.phone}
              onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="注册时使用的手机号"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="密码"
            />
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`flex-1 py-3 rounded-lg font-medium ${
                isSubmitting
                  ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isSubmitting ? '登录中...' : '登录'}
            </button>
          </div>
        </form>

        {/* 分隔线 */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-white text-gray-500">或</span>
          </div>
        </div>

        {/* 微信登录按钮 */}
        <button
          onClick={handleWechatLogin}
          disabled={isSubmitting}
          className="w-full py-3 rounded-lg font-medium bg-green-500 text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.5 11.5c.5 0 1-.5 1-1s-.5-1-1-1-1 .5-1 1 .5 1 1 1zm6 0c.5 0 1-.5 1-1s-.5-1-1-1-1 .5-1 1 .5 1 1 1zm4.5-2c0-4.4-4.5-8-10-8S0 5.1 0 9.5c0 2.4 1.2 4.5 3 6l-1 3 3.5-2c1 .3 2 .5 3 .5 5.5.5 10.5-3.1 10.5-7.5zm-4 7c-.5 0-1-.1-1.5-.2l-2.5 1.5.5-2c-1.5-1-2.5-2.5-2.5-4.3 0-3 3-5.5 6.5-5.5S22 10.5 22 13.5 19 19 15.5 19z"/>
          </svg>
          <span>{isSubmitting ? '登录中...' : '微信授权登录'}</span>
        </button>

        <div className="mt-4 text-center">
          <button
            onClick={onRegister}
            className="text-blue-600 text-sm underline"
          >
            没有账号？立即注册
          </button>
        </div>
      </div>
    </div>
  );
}