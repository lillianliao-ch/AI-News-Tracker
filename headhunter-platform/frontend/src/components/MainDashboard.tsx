'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from './AuthProvider'
import { UserRole } from '@/types'
import AdminDashboard from './AdminDashboard'
import UserDashboard from './UserDashboard'
import UserManagement from './UserManagement'
import CompanyManagement from './CompanyManagement'
import JobManagementDual from './JobManagementDual'
import CandidateManagement from './CandidateManagement'
import CollaborationDashboard from './CollaborationDashboard'
import NotificationCenter from './NotificationCenter'
import ConsultantManagement from './ConsultantManagement'
import MyCompanyInfo from './MyCompanyInfo'
import CompanyInfo from './CompanyInfo'
import ClientCompanyManagement from './ClientCompanyManagement'
import ConsultantApplications from './ConsultantApplications'
import ResumeMatchingSimple from './ResumeMatchingSimple'

type ActiveComponent = 
  | 'dashboard' 
  | 'users' 
  | 'companies' 
  | 'mycompany'
  | 'companyinfo'
  | 'clientcompanies'
  | 'jobs' 
  | 'candidates' 
  | 'collaboration' 
  | 'notifications'
  | 'consultants'
  | 'consultant-applications'
  | 'resume-matching'

export default function MainDashboard() {
  const { user, logout } = useAuth()
  const [activeComponent, setActiveComponent] = useState<ActiveComponent>('jobs')
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const profileMenuRef = useRef<HTMLDivElement>(null)

  // Close profile menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false)
      }
    }

    if (showProfileMenu) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [showProfileMenu])

  if (!user) return null

  const isAdmin = user.role === UserRole.PLATFORM_ADMIN
  const isCompanyAdmin = user.role === UserRole.COMPANY_ADMIN
  const isConsultant = user.role === UserRole.CONSULTANT
  const isConsultantOrSoho = user.role === UserRole.CONSULTANT || user.role === UserRole.SOHO

  const navigationItems = [
    { id: 'jobs', label: 'Jobs', icon: '💼', visible: true },
    { id: 'candidates', label: 'Candidates', icon: '👥', visible: true },
    { id: 'resume-matching', label: 'Resume Matching', icon: '🎯', visible: isConsultantOrSoho },
    { id: 'collaboration', label: 'Collaboration', icon: '🤝', visible: true },
    { id: 'users', label: 'User Management', icon: '👤', visible: isAdmin },
    { id: 'companies', label: 'Company Management', icon: '🏢', visible: isAdmin },
    { id: 'mycompany', label: 'My Company', icon: '🏢', visible: isCompanyAdmin },
    { id: 'clientcompanies', label: 'Client Companies', icon: '🤝', visible: isCompanyAdmin },
    { id: 'consultant-applications', label: 'Consultant Applications', icon: '📝', visible: isCompanyAdmin },
  ]

  const renderActiveComponent = () => {
    switch (activeComponent) {
      case 'users':
        return <UserManagement />
      case 'companies':
        return <CompanyManagement />
      case 'mycompany':
        return <MyCompanyInfo />
      case 'clientcompanies':
        return <ClientCompanyManagement />
      case 'jobs':
        return <JobManagementDual />
      case 'candidates':
        return <CandidateManagement />
      case 'resume-matching':
        return <ResumeMatchingSimple />
      case 'collaboration':
        return <CollaborationDashboard />
      case 'notifications':
        return <NotificationCenter />
      case 'consultants':
        return <ConsultantManagement />
      case 'consultant-applications':
        return <ConsultantApplications />
      default:
        return <JobManagementDual />
    }
  }

  const getActiveStyle = (itemId: string) => {
    return activeComponent === itemId
      ? 'bg-blue-600 text-white'
      : 'text-gray-700 hover:bg-gray-100'
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-lg">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Headhunter Platform</h1>
          <div className="mt-2">
            <p className="text-sm text-gray-600">{user.username || 'Unknown User'}</p>
            <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
              isAdmin 
                ? 'bg-red-100 text-red-800' 
                : isCompanyAdmin
                ? 'bg-green-100 text-green-800'
                : 'bg-blue-100 text-blue-800'
            }`}>
              {user.role?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
            </span>
          </div>
        </div>

        <nav className="mt-4">
          {navigationItems
            .filter(item => item.visible)
            .map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveComponent(item.id as ActiveComponent)}
                className={`w-full flex items-center px-4 py-3 text-left transition-colors ${getActiveStyle(item.id)}`}
              >
                <span className="text-lg mr-3">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
        </nav>

      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {navigationItems.find(item => item.id === activeComponent)?.label || 'Dashboard'}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {activeComponent === 'jobs' && 'Manage job postings and collaborations'}
                {activeComponent === 'candidates' && 'Manage candidate profiles and submissions'}
                {activeComponent === 'resume-matching' && 'AI-powered resume matching and candidate recommendations'}
                {activeComponent === 'collaboration' && 'View collaboration network and shared opportunities'}
                {activeComponent === 'notifications' && 'Messages and notifications center'}
                {activeComponent === 'users' && 'Platform user management (Admin only)'}
                {activeComponent === 'companies' && 'Company management and verification'}
                {activeComponent === 'clientcompanies' && 'Manage client company partnerships and relationships'}
                {activeComponent === 'consultants' && 'Review and approve consultant applications (Company Admin only)'}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Notification Bell */}
              <button 
                onClick={() => setActiveComponent('notifications')}
                className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <span className="text-xl">🔔</span>
                <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400"></span>
              </button>
              
              {/* Profile Menu */}
              <div className="relative" ref={profileMenuRef}>
                <button 
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 transition-colors"
                >
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                    {user.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                </button>
                
                {/* Profile Dropdown */}
                {showProfileMenu && (
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <h3 className="font-medium text-gray-900">个人信息</h3>
                    </div>
                    <div className="px-4 py-2 space-y-2">
                      <div>
                        <span className="text-sm text-gray-500">用户名：</span>
                        <span className="text-sm font-medium text-gray-900">{user.username || 'Unknown'}</span>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">邮箱：</span>
                        <span className="text-sm font-medium text-gray-900">{user.email || 'Unknown'}</span>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">角色：</span>
                        <span className="text-sm font-medium text-gray-900">{user.role?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}</span>
                      </div>
                      {user.company && (
                        <div>
                          <span className="text-sm text-gray-500">公司名称：</span>
                          <span className="text-sm font-medium text-gray-900">{user.company.name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Sign Out Button */}
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-md transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto bg-gray-50">
          {renderActiveComponent()}
        </div>
      </div>
    </div>
  )
}