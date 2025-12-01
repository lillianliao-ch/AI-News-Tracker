'use client';

import { useAuth } from './AuthProvider';
import { UserRole } from '@/types';

export default function Navigation() {
  const { user, logout } = useAuth();

  if (!user) return null;

  const isAdmin = user.role === UserRole.PLATFORM_ADMIN;

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              Headhunter Platform
            </h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Welcome,</span>
              <span className="text-sm font-medium text-gray-900">{user.username || 'Unknown User'}</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                isAdmin 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {user.role?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
            
            <button
              onClick={logout}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}