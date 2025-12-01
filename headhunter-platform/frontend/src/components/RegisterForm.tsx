'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { UserRole } from '@/types';

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    role: UserRole.CONSULTANT,
    companyName: '',
    businessLicense: '',
    companyId: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [companies, setCompanies] = useState<Array<{id: string, name: string, industry?: string}>>([]);
  const [loadingCompanies, setLoadingCompanies] = useState(false);

  const fetchCompanies = async () => {
    setLoadingCompanies(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4002/api'}/consultant-applications/companies`);
      const data = await response.json();
      setCompanies(data.companies || []);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
    } finally {
      setLoadingCompanies(false);
    }
  };

  useEffect(() => {
    // Fetch companies when component mounts
    fetchCompanies();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Basic validation
    if (formData.password !== formData.confirmPassword) {
      setError('密码和确认密码不匹配');
      return;
    }

    if (formData.role === UserRole.COMPANY_ADMIN && (!formData.companyName || !formData.businessLicense)) {
      setError('公司管理员角色需要填写公司名称和营业执照');
      return;
    }

    if (formData.role === UserRole.CONSULTANT && !formData.companyId) {
      setError('顾问角色需要选择要申请加入的猎头公司');
      return;
    }

    setLoading(true);

    try {
      const registerData = {
        username: formData.username,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        role: formData.role,
        ...(formData.role === UserRole.COMPANY_ADMIN && {
          companyName: formData.companyName,
          businessLicense: formData.businessLicense,
        }),
        ...(formData.role === UserRole.CONSULTANT && {
          companyId: formData.companyId,
        }),
      };

      const response = await apiClient.register(registerData);
      setSuccess('注册成功！');
      
      // Reset form
      setFormData({
        username: '',
        email: '',
        phone: '',
        password: '',
        confirmPassword: '',
        role: UserRole.CONSULTANT,
        companyName: '',
        businessLicense: '',
        companyId: '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败');
    } finally {
      setLoading(false);
    }
  };

  const getRoleDisplayName = (role: UserRole) => {
    switch (role) {
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            用户注册
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            注册新账户
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <p className="text-green-600 text-sm">{success}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                用户名
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="输入用户名"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                邮箱地址
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="输入邮箱地址"
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                手机号码
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                required
                value={formData.phone}
                onChange={handleChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="输入手机号码"
              />
            </div>

            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700">
                角色
              </label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value={UserRole.CONSULTANT}>{getRoleDisplayName(UserRole.CONSULTANT)}</option>
                <option value={UserRole.SOHO}>{getRoleDisplayName(UserRole.SOHO)}</option>
                <option value={UserRole.COMPANY_ADMIN}>{getRoleDisplayName(UserRole.COMPANY_ADMIN)}</option>
              </select>
            </div>

            {formData.role === UserRole.COMPANY_ADMIN && (
              <>
                <div>
                  <label htmlFor="companyName" className="block text-sm font-medium text-gray-700">
                    公司名称
                  </label>
                  <input
                    id="companyName"
                    name="companyName"
                    type="text"
                    required={formData.role === UserRole.COMPANY_ADMIN}
                    value={formData.companyName}
                    onChange={handleChange}
                    className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="输入公司名称"
                  />
                </div>

                <div>
                  <label htmlFor="businessLicense" className="block text-sm font-medium text-gray-700">
                    营业执照号
                  </label>
                  <input
                    id="businessLicense"
                    name="businessLicense"
                    type="text"
                    required={formData.role === UserRole.COMPANY_ADMIN}
                    value={formData.businessLicense}
                    onChange={handleChange}
                    className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="输入营业执照号"
                  />
                </div>
              </>
            )}

            {formData.role === UserRole.CONSULTANT && (
              <>
                <div>
                  <label htmlFor="companyId" className="block text-sm font-medium text-gray-700">
                    选择猎头公司
                  </label>
                  <select
                    id="companyId"
                    name="companyId"
                    required={formData.role === UserRole.CONSULTANT}
                    value={formData.companyId}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    disabled={loadingCompanies}
                  >
                    <option value="">请选择要申请的猎头公司</option>
                    {companies.map((company) => (
                      <option key={company.id} value={company.id}>
                        {company.name} {company.industry && `(${company.industry})`}
                      </option>
                    ))}
                  </select>
                  {loadingCompanies && (
                    <p className="mt-1 text-sm text-gray-500">加载公司列表中...</p>
                  )}
                </div>

              </>
            )}

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                密码
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={handleChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="输入密码"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                确认密码
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="再次输入密码"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  注册中...
                </div>
              ) : (
                '注册'
              )}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => window.location.href = '/'}
              className="text-blue-600 hover:text-blue-500 text-sm"
            >
              返回登录
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}