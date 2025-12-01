'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { useAuth } from './AuthProvider';

interface CompanyInfo {
  id: string;
  name: string;
  businessLicense?: string;
  industry?: string;
  scale?: string;
  contactName?: string;
  contactPhone?: string;
  contactEmail?: string;
  address?: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  users?: Array<{
    id: string;
    username: string;
    email: string;
    phone?: string;
    role: string;
    status: string;
    createdAt: string;
  }>;
}

interface CompanyStats {
  users: { total: number; active: number };
  jobs: { total: number; active: number };
  submissions: number;
  candidates: number;
}

export default function CompanyInfo() {
  const { user } = useAuth();
  const [company, setCompany] = useState<CompanyInfo | null>(null);
  const [stats, setStats] = useState<CompanyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.companyId) {
      loadCompanyInfo();
      loadCompanyStats();
    }
  }, [user?.companyId]);

  const loadCompanyInfo = async () => {
    if (!user?.companyId) return;
    
    try {
      setLoading(true);
      const companyData = await apiClient.getCompany(user.companyId);
      setCompany(companyData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load company information');
    } finally {
      setLoading(false);
    }
  };

  const loadCompanyStats = async () => {
    if (!user?.companyId) return;
    
    try {
      const statsData = await apiClient.getCompanyStats(user.companyId);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load company stats:', err);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'suspended':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-48">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <p className="text-yellow-600">No company information found. Please contact your administrator.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Company Information</h2>
          <p className="text-sm text-gray-600 mt-1">
            View your company profile and team information
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">You are a consultant at</p>
          <p className="text-lg font-medium text-gray-900">{company.name}</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">Error: {error}</p>
          <button
            onClick={loadCompanyInfo}
            className="mt-2 text-sm text-red-600 underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Company Stats */}
      {stats && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Company Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-600">Team Members</p>
              <p className="text-2xl font-bold text-blue-900">
                {stats.users.active}/{stats.users.total}
              </p>
              <p className="text-xs text-blue-700">Active/Total</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm font-medium text-green-600">Job Positions</p>
              <p className="text-2xl font-bold text-green-900">
                {stats.jobs.active}/{stats.jobs.total}
              </p>
              <p className="text-xs text-green-700">Active/Total</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm font-medium text-purple-600">Submissions</p>
              <p className="text-2xl font-bold text-purple-900">{stats.submissions}</p>
              <p className="text-xs text-purple-700">Total</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <p className="text-sm font-medium text-orange-600">Candidates</p>
              <p className="text-2xl font-bold text-orange-900">{stats.candidates}</p>
              <p className="text-xs text-orange-700">Managed</p>
            </div>
          </div>
        </div>
      )}

      {/* Company Information */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">Company Details</h3>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(
              company.status
            )}`}
          >
            {company.status.toUpperCase()}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Name
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">{company.name}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business License
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {company.businessLicense || 'Not provided'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Industry
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {company.industry || 'Not specified'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Scale
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {company.scale || 'Not specified'}
              </p>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contact Person
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {company.contactName || 'Not provided'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contact Phone
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {company.contactPhone || 'Not provided'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contact Email
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {company.contactEmail || 'Not provided'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Office Address
              </label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {company.address || 'Not provided'}
              </p>
            </div>
          </div>
        </div>

        {/* Note for consultants */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-blue-400 text-lg">ℹ️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Information Notice
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  As a consultant, you can view company information but cannot modify it. 
                  If you need to update any company details, please contact your company administrator.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Timestamps */}
        <div className="mt-6 pt-6 border-t border-gray-200 text-sm text-gray-500">
          <div className="flex justify-between">
            <span>Company Founded: {new Date(company.createdAt).toLocaleDateString()}</span>
            <span>Last Updated: {new Date(company.updatedAt).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Team Members */}
      {company.users && company.users.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Team Members</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {company.users.map((member) => (
                  <tr key={member.id} className={member.id === user?.id ? 'bg-blue-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {member.username}
                      {member.id === user?.id && (
                        <span className="ml-2 text-xs text-blue-600 font-medium">(You)</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {member.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded text-xs ${
                        member.role === 'company_admin' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {member.role.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded text-xs ${
                        member.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {member.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(member.createdAt).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}