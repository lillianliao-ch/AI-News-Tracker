'use client';

import { useAuth } from './AuthProvider';
import { UserRole } from '@/types';
import Navigation from './Navigation';

export default function UserDashboard() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  const getRoleName = (role: UserRole) => {
    switch (role) {
      case UserRole.PLATFORM_ADMIN:
        return '平台管理员';
      case UserRole.COMPANY_ADMIN:
        return '公司管理员';
      case UserRole.CONSULTANT:
        return '顾问';
      case UserRole.SOHO:
        return 'SOHO';
      default:
        return role;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="border-b border-gray-200 pb-4 mb-6">
              <h1 className="text-2xl font-bold text-gray-900">
                欢迎回来，{user.username}！
              </h1>
              <p className="text-gray-600 mt-1">
                您的角色：{getRoleName(user.role)}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* 基础信息卡片 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-blue-900 mb-2">个人信息</h3>
                <div className="space-y-2 text-sm text-blue-700">
                  <p><span className="font-medium">用户名:</span> {user.username}</p>
                  <p><span className="font-medium">邮箱:</span> {user.email}</p>
                  <p><span className="font-medium">角色:</span> {getRoleName(user.role)}</p>
                  <p><span className="font-medium">状态:</span> 
                    <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                      user.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {user.status === 'active' ? '已激活' : user.status}
                    </span>
                  </p>
                  {user.company && (
                    <p><span className="font-medium">公司:</span> {user.company.name}</p>
                  )}
                </div>
              </div>

              {/* 功能说明卡片 */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-green-900 mb-2">可用功能</h3>
                <div className="space-y-2 text-sm text-green-700">
                  {user.role === UserRole.CONSULTANT && (
                    <>
                      <p>• 查看职位信息</p>
                      <p>• 推荐候选人</p>
                      <p>• 管理客户关系</p>
                      <p>• 查看佣金记录</p>
                    </>
                  )}
                  {user.role === UserRole.SOHO && (
                    <>
                      <p>• 浏览职位机会</p>
                      <p>• 提交候选人</p>
                      <p>• 查看推荐记录</p>
                      <p>• 个人业绩统计</p>
                    </>
                  )}
                  {user.role === UserRole.COMPANY_ADMIN && (
                    <>
                      <p>• 发布职位需求</p>
                      <p>• 管理公司用户</p>
                      <p>• 审核候选人</p>
                      <p>• 结算管理</p>
                    </>
                  )}
                </div>
              </div>

              {/* 开发中提示 */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-yellow-900 mb-2">开发进度</h3>
                <div className="space-y-2 text-sm text-yellow-700">
                  <p>✅ 用户认证系统</p>
                  <p>✅ 权限管理</p>
                  <p>✅ 用户审核流程</p>
                  <p>🚧 职位管理系统</p>
                  <p>🚧 候选人管理</p>
                  <p>🚧 协作功能</p>
                </div>
              </div>
            </div>

            <div className="mt-8 bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-2">系统状态</h3>
              <p className="text-sm text-gray-600">
                当前正在开发中，更多功能即将上线。如有问题请联系平台管理员。
              </p>
              {user.role !== UserRole.PLATFORM_ADMIN && (
                <p className="text-xs text-gray-500 mt-2">
                  注意：管理功能仅限平台管理员使用
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}