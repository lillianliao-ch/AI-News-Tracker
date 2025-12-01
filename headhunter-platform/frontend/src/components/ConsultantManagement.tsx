'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { User, UserStatus, UserRole } from '@/types';

interface PendingConsultant extends User {
  createdAt: string;
}

export default function ConsultantManagement() {
  const [pendingConsultants, setPendingConsultants] = useState<PendingConsultant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPendingConsultants();
  }, []);

  const loadPendingConsultants = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getPendingConsultants();
      setPendingConsultants(response.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pending consultants');
    } finally {
      setLoading(false);
    }
  };

  const handleConsultantAction = async (
    userId: string,
    action: 'approve' | 'reject',
    reason?: string
  ) => {
    try {
      await apiClient.approveConsultant(userId, action, reason);
      await loadPendingConsultants(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} consultant`);
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
          onClick={loadPendingConsultants}
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
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Pending Consultant Approvals</h2>
          <p className="text-sm text-gray-600 mt-1">
            Review and approve consultants to join your company
          </p>
        </div>
        <button
          onClick={loadPendingConsultants}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {pendingConsultants.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">👥</div>
          <p className="text-gray-500 text-lg">No pending consultants to review</p>
          <p className="text-gray-400 text-sm mt-2">
            New consultant registrations will appear here for approval
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {pendingConsultants.map((consultant) => (
              <li key={consultant.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 bg-green-300 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-green-800">
                            {consultant.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {consultant.username}
                          </p>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            CONSULTANT
                          </span>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            PENDING
                          </span>
                        </div>
                        <p className="text-sm text-gray-500">{consultant.email}</p>
                        <p className="text-sm text-gray-500">{consultant.phone}</p>
                        <p className="text-xs text-gray-400">
                          Applied: {new Date(consultant.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleConsultantAction(consultant.id, 'approve')}
                      className="px-4 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 transition-colors flex items-center space-x-1"
                    >
                      <span>✓</span>
                      <span>Approve & Add to Company</span>
                    </button>
                    <button
                      onClick={() => handleConsultantAction(consultant.id, 'reject')}
                      className="px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors flex items-center space-x-1"
                    >
                      <span>✗</span>
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}