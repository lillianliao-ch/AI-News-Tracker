'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { HunterLogin, HunterQuickRegister } from '../../components/HunterAuth';

interface UserProfile {
  name: string;
  phone: string;
  avatar?: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [totalPosts, setTotalPosts] = useState(0);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkLoginStatus();
  }, []);

  const checkLoginStatus = async () => {
    setLoading(true);
    const token = localStorage.getItem('hunter_token');
    
    if (token) {
      setIsLoggedIn(true);
      // 模拟获取用户数据
      await new Promise(resolve => setTimeout(resolve, 300));
      setProfile({
        name: '演示用户',
        phone: '139****0001',
        avatar: undefined
      });
      setTotalPosts(5);
    } else {
      setIsLoggedIn(false);
    }
    
    setLoading(false);
  };

  const handleLoginSuccess = (token: string) => {
    setShowLoginModal(false);
    setShowRegisterModal(false);
    checkLoginStatus();
  };

  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      localStorage.removeItem('hunter_token');
      setIsLoggedIn(false);
      setProfile(null);
      setTotalPosts(0);
    }
  };

  const handleEditProfile = () => {
    setShowEditModal(true);
  };

  const handleSaveProfile = (newName: string) => {
    // 模拟保存
    if (profile) {
      setProfile({ ...profile, name: newName });
      alert('资料修改成功！');
      setShowEditModal(false);
    }
  };

  const handleChangePassword = (oldPassword: string, newPassword: string) => {
    // 模拟修改密码
    alert('密码修改成功！（演示模式）');
    setShowPasswordModal(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
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
            <h1 className="text-lg font-semibold text-gray-900">我的</h1>
            <div className="w-12"></div>
          </div>
        </div>
      </div>

      <div className="px-4 pb-20 pt-6">
        {/* 未登录状态 */}
        {!isLoggedIn && (
          <div className="space-y-4">
            {/* 未登录提示卡片 */}
            <div className="bg-white rounded-2xl p-8 text-center shadow-sm border border-gray-200">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">👤</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">欢迎来到猎头协作</h2>
              <p className="text-gray-600 text-sm mb-6">登录后可发布信息、查看更多内容</p>
              
              <div className="space-y-3">
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
                >
                  登录
                </button>
                <button
                  onClick={() => setShowRegisterModal(true)}
                  className="w-full py-3 bg-white border-2 border-blue-600 text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition-all"
                >
                  注册账号
                </button>
              </div>
            </div>

            {/* 功能介绍 */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-4">平台功能</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg">🔍</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">寻找人才</div>
                    <div className="text-xs text-gray-500">发布职位需求，快速匹配</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg">👥</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">推荐候选人</div>
                    <div className="text-xs text-gray-500">分享优质人才资源</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg">🤝</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">协作共赢</div>
                    <div className="text-xs text-gray-500">猎头之间互助合作</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 已登录状态 */}
        {isLoggedIn && profile && (
          <div className="space-y-4">
            {/* 用户信息卡片 */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center space-x-4 mb-4">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-2xl">
                    {profile.avatar || profile.name.charAt(0)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl font-bold text-gray-900">{profile.name}</h2>
                  <p className="text-gray-600 text-sm">{profile.phone}</p>
                </div>
                <button
                  onClick={handleEditProfile}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                >
                  编辑
                </button>
              </div>

              {/* 发布数量 */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-100">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">我的发布</div>
                    <div className="text-2xl font-bold text-gray-900">{totalPosts} 条</div>
                  </div>
                  <button
                    onClick={() => router.push('/my-posts')}
                    className="px-4 py-2 bg-white text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors border border-blue-200"
                  >
                    查看详情 →
                  </button>
                </div>
              </div>
            </div>

            {/* 功能菜单 */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <button
                onClick={() => setShowPasswordModal(true)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg">🔒</span>
                  </div>
                  <span className="text-gray-900 font-medium">修改密码</span>
                </div>
                <span className="text-gray-400">›</span>
              </button>
            </div>

            {/* 退出登录 */}
            <button
              onClick={handleLogout}
              className="w-full py-3 bg-white text-red-600 rounded-xl font-semibold border-2 border-red-200 hover:bg-red-50 transition-all"
            >
              退出登录
            </button>
          </div>
        )}
      </div>

      {/* 登录弹窗 */}
      {showLoginModal && (
        <HunterLogin
          onSuccess={handleLoginSuccess}
          onCancel={() => setShowLoginModal(false)}
          onRegister={() => {
            setShowLoginModal(false);
            setShowRegisterModal(true);
          }}
        />
      )}

      {/* 注册弹窗 */}
      {showRegisterModal && (
        <HunterQuickRegister
          onSuccess={handleLoginSuccess}
          onCancel={() => setShowRegisterModal(false)}
        />
      )}

      {/* 编辑资料弹窗 */}
      {showEditModal && profile && (
        <EditProfileModal
          currentName={profile.name}
          onSave={handleSaveProfile}
          onCancel={() => setShowEditModal(false)}
        />
      )}

      {/* 修改密码弹窗 */}
      {showPasswordModal && (
        <ChangePasswordModal
          onSave={handleChangePassword}
          onCancel={() => setShowPasswordModal(false)}
        />
      )}
    </div>
  );
}

// 编辑资料弹窗组件
function EditProfileModal({ 
  currentName, 
  onSave, 
  onCancel 
}: { 
  currentName: string; 
  onSave: (name: string) => void; 
  onCancel: () => void;
}) {
  const [name, setName] = useState(currentName);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">编辑资料</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">姓名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="请输入姓名"
            />
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              className="flex-1 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50"
            >
              取消
            </button>
            <button
              onClick={() => onSave(name)}
              disabled={!name.trim()}
              className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// 修改密码弹窗组件
function ChangePasswordModal({ 
  onSave, 
  onCancel 
}: { 
  onSave: (oldPassword: string, newPassword: string) => void; 
  onCancel: () => void;
}) {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = () => {
    setError('');
    
    if (!oldPassword || !newPassword || !confirmPassword) {
      setError('请填写所有字段');
      return;
    }
    
    if (newPassword.length < 6) {
      setError('新密码至少6个字符');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setError('两次输入的新密码不一致');
      return;
    }
    
    onSave(oldPassword, newPassword);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">修改密码</h2>
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <span className="text-red-800 text-sm">{error}</span>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">原密码</label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="请输入原密码"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">新密码</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="至少6个字符"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">确认新密码</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="再次输入新密码"
            />
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              className="flex-1 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
