'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Company, CompanyStatus } from '@/types';

interface CompanyWithUsers extends Company {
  users?: Array<{
    id: string;
    username: string;
    email: string;
    role: string;
    status: string;
  }>;
}

export default function CompanyManagement() {
  const [pendingCompanies, setPendingCompanies] = useState<CompanyWithUsers[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPendingCompanies();
  }, []);

  const loadPendingCompanies = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getPendingCompanies();
      setPendingCompanies(response.companies);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pending companies');
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyAction = async (
    companyId: string,
    action: 'approve' | 'reject',
    reason?: string
  ) => {
    try {
      await apiClient.approveCompany(companyId, action, reason);
      await loadPendingCompanies(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} company`);
    }
  };

  const getStatusBadgeColor = (status: CompanyStatus) => {
    switch (status) {
      case CompanyStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case CompanyStatus.APPROVED:
        return 'bg-green-100 text-green-800';
      case CompanyStatus.REJECTED:
        return 'bg-red-100 text-red-800';
      case CompanyStatus.SUSPENDED:
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

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-600">Error: {error}</p>
        <button
          onClick={loadPendingCompanies}
          className="mt-2 text-sm text-red-600 underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Pending Company Approvals</h2>
        <button
          onClick={loadPendingCompanies}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {pendingCompanies.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 text-lg">No pending companies to review</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-1">
          {pendingCompanies.map((company) => (
            <div
              key={company.id}
              className="bg-white shadow rounded-lg border border-gray-200 p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="text-lg font-medium text-gray-900">{company.name}</h3>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(
                        company.status
                      )}`}
                    >
                      {company.status.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="space-y-2 text-sm text-gray-600">
                    <p><span className="font-medium">Business License:</span> {company.businessLicense}</p>
                    <p><span className="font-medium">Contact:</span> {company.contactName}</p>
                    <p><span className="font-medium">Phone:</span> {company.contactPhone}</p>
                    <p><span className="font-medium">Email:</span> {company.contactEmail}</p>
                    <p><span className="font-medium">Applied:</span> {new Date(company.createdAt).toLocaleDateString()}</p>
                  </div>

                  {company.users && company.users.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Associated Users:</h4>
                      <div className="space-y-1">
                        {company.users.map((user) => (
                          <div key={user.id} className="text-sm text-gray-600 flex items-center space-x-2">
                            <span>{user.username}</span>
                            <span className="text-gray-400">({user.email})</span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              user.role === 'company_admin' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {user.role.replace('_', ' ').toUpperCase()}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex flex-col space-y-2 ml-4">
                  <button
                    onClick={() => handleCompanyAction(company.id, 'approve')}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 transition-colors"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleCompanyAction(company.id, 'reject')}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}