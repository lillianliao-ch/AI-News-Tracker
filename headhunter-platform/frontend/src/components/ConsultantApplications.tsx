'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface ConsultantApplication {
  id: string;
  status: 'pending' | 'approved' | 'rejected';
  reason?: string;
  rejectReason?: string;
  appliedAt: string;
  reviewedAt?: string;
  consultant: {
    id: string;
    username: string;
    email: string;
    phone: string;
    createdAt: string;
  };
  reviewedBy?: {
    id: string;
    username: string;
  };
}

export default function ConsultantApplications() {
  const [applications, setApplications] = useState<ConsultantApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState<string | null>(null);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const queryString = filter === 'all' ? '' : `?status=${filter}`;
      const response = await api.get(`/consultant-applications${queryString}`);
      setApplications(response.applications || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [filter]);

  const handleApprove = async (applicationId: string) => {
    setProcessingId(applicationId);
    try {
      await api.patch(`/consultant-applications/${applicationId}/review`, {
        action: 'approve'
      });
      await fetchApplications(); // Refresh the list
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to approve application');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (applicationId: string) => {
    setProcessingId(applicationId);
    try {
      await api.patch(`/consultant-applications/${applicationId}/review`, {
        action: 'reject',
        rejectReason
      });
      await fetchApplications(); // Refresh the list
      setShowRejectModal(null);
      setRejectReason('');
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to reject application');
    } finally {
      setProcessingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">待审核</span>;
      case 'approved':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">已通过</span>;
      case 'rejected':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">已拒绝</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">顾问申请管理</h1>
          <p className="mt-2 text-sm text-gray-700">
            管理申请加入贵公司的顾问申请
          </p>
        </div>
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Filter tabs */}
      <div className="mt-6">
        <nav className="flex space-x-8" aria-label="Tabs">
          {(['all', 'pending', 'approved', 'rejected'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                filter === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'all' && '全部'}
              {tab === 'pending' && '待审核'}
              {tab === 'approved' && '已通过'}
              {tab === 'rejected' && '已拒绝'}
            </button>
          ))}
        </nav>
      </div>

      {/* Applications table */}
      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              {loading ? (
                <div className="bg-white px-6 py-12 text-center">
                  <p className="text-gray-500">加载中...</p>
                </div>
              ) : applications.length === 0 ? (
                <div className="bg-white px-6 py-12 text-center">
                  <p className="text-gray-500">暂无申请</p>
                </div>
              ) : (
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        申请人
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        申请时间
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        状态
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {applications.map((application) => (
                      <tr key={application.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {application.consultant.username}
                            </div>
                            <div className="text-sm text-gray-500">
                              {application.consultant.email}
                            </div>
                            <div className="text-sm text-gray-500">
                              {application.consultant.phone}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(application.appliedAt).toLocaleString('zh-CN')}
                          {application.reviewedAt && (
                            <div className="text-xs text-gray-400 mt-1">
                              审核时间: {new Date(application.reviewedAt).toLocaleString('zh-CN')}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(application.status)}
                          {application.reviewedBy && (
                            <div className="text-xs text-gray-500 mt-1">
                              审核人: {application.reviewedBy.username}
                            </div>
                          )}
                          {application.rejectReason && (
                            <div className="text-sm text-red-600 mt-1">
                              拒绝理由: {application.rejectReason}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {application.status === 'pending' && (
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleApprove(application.id)}
                                disabled={processingId === application.id}
                                className="text-green-600 hover:text-green-900 disabled:opacity-50"
                              >
                                {processingId === application.id ? '处理中...' : '通过'}
                              </button>
                              <button
                                onClick={() => setShowRejectModal(application.id)}
                                disabled={processingId === application.id}
                                className="text-red-600 hover:text-red-900 disabled:opacity-50"
                              >
                                拒绝
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 text-center">
                拒绝申请
              </h3>
              <div className="mt-4">
                <label htmlFor="rejectReason" className="block text-sm font-medium text-gray-700">
                  拒绝理由
                </label>
                <textarea
                  id="rejectReason"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  rows={3}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="请输入拒绝理由..."
                />
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowRejectModal(null);
                    setRejectReason('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={() => handleReject(showRejectModal)}
                  disabled={processingId === showRejectModal}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {processingId === showRejectModal ? '处理中...' : '确认拒绝'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}