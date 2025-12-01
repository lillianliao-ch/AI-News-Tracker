'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useAuth } from './AuthProvider'
import { UserRole, Job, AssignmentStatus, JobProjectManager, PermissionType } from '@/types'
import JobDetail from './JobDetail'
import CandidateSelectionModal from './CandidateSelectionModal'
import QuickCandidateCreateModal from './QuickCandidateCreateModal'

interface ManagementAreaProps {
  user: any
}

interface ProgressionAreaProps {
  user: any
}

// Management Area Component - For job management permissions
function ManagementArea({ user }: ManagementAreaProps) {
  const [pendingJobs, setPendingJobs] = useState<Job[]>([])
  const [assignedJobs, setAssignedJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [consultants, setConsultants] = useState<any[]>([])
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [selectedJobForAssignment, setSelectedJobForAssignment] = useState<string | null>(null)
  const [selectedConsultantId, setSelectedConsultantId] = useState<string | null>(null)
  const [selectedConsultant, setSelectedConsultant] = useState<any | null>(null)
  const [assignmentNotes, setAssignmentNotes] = useState('')
  const [consultantSearch, setConsultantSearch] = useState('')
  const [filteredConsultants, setFilteredConsultants] = useState<any[]>([])
  const [assigningJob, setAssigningJob] = useState(false)
  
  // 分页和筛选状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(5)
  const [totalItems, setTotalItems] = useState(0)
  const [filters, setFilters] = useState({
    jobName: '',
    companyLocation: '',
    jobCategory: ''
  })
  const [searchFilters, setSearchFilters] = useState({
    jobName: '',
    companyLocation: '',
    jobCategory: ''
  })
  const [companyClients, setCompanyClients] = useState<any[]>([])
  
  // 已分配职位的分页和搜索状态
  const [assignedCurrentPage, setAssignedCurrentPage] = useState(1)
  const [assignedPageSize, setAssignedPageSize] = useState(5)
  const [assignedTotalItems, setAssignedTotalItems] = useState(0)
  const [assignedFilters, setAssignedFilters] = useState({
    jobName: '',
    companyLocation: '',
    jobCategory: ''
  })
  const [assignedSearchFilters, setAssignedSearchFilters] = useState({
    jobName: '',
    companyLocation: '',
    jobCategory: ''
  })

  const fetchManagementJobs = async (page = 1, pageSize = 5, searchFilters = {}) => {
    try {
      setLoading(true)
      const params = {
        page,
        limit: pageSize,
        ...searchFilters
      }
      const response = await api.getManagementJobs(params)
      setPendingJobs(response.pendingJobs || [])
      setTotalItems(response.totalPending || 0)
    } catch (err: any) {
      setError('Failed to fetch management jobs')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchAssignedJobs = async (page = 1, pageSize = 5, searchFilters = {}) => {
    try {
      setLoading(true)
      const params = {
        page,
        limit: pageSize,
        assignmentStatus: 'assigned',
        ...searchFilters
      }
      const response = await api.getManagementJobs(params)
      console.log('🔥 Assigned jobs response:', response)
      setAssignedJobs(response.assignedJobs || response.pendingJobs || []) // 先尝试assignedJobs
      setAssignedTotalItems(response.totalAssigned || response.totalPending || 0)
    } catch (err: any) {
      setError('Failed to fetch assigned jobs')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchConsultants = async () => {
    try {
      // Fetch both company consultants and SOHO consultants
      const response = await api.getConsultants()
      setConsultants(response.consultants || [])
    } catch (err) {
      console.error('Failed to fetch consultants:', err)
    }
  }

  const fetchCompanyClients = async () => {
    try {
      const response = await api.getCompanyClients()
      setCompanyClients(response.companyClients || [])
    } catch (err) {
      console.error('Failed to fetch company clients:', err)
    }
  }

  const assignPM = async (jobId: string, pmUserId: string, notes?: string) => {
    try {
      await api.assignPM(jobId, pmUserId, notes)
      fetchManagementJobs()
      alert('PM assigned successfully!')
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to assign PM')
    }
  }

  const assignJob = async (jobId: string, consultant: any, notes?: string) => {
    try {
      await api.assignJobToConsultant(jobId, consultant.id, consultant.role, notes)
      fetchManagementJobs(currentPage, pageSize, searchFilters)
      fetchAssignedJobs(assignedCurrentPage, assignedPageSize, assignedSearchFilters)
      setShowAssignModal(false)
      setSelectedJobForAssignment(null)
      setSelectedConsultantId(null)
      setSelectedConsultant(null)
      setAssignmentNotes('')
      alert('职位分配成功！')
    } catch (err: any) {
      setError(err.message || 'Failed to assign job')
      throw err
    }
  }

  const removeAssignment = async (jobId: string, userId: string, userName: string) => {
    if (!confirm(`确定要删除 ${userName} 的分配吗？`)) {
      return
    }
    
    try {
      await api.removeJobAssignment(jobId, userId)
      fetchManagementJobs(currentPage, pageSize, searchFilters)
      fetchAssignedJobs(assignedCurrentPage, assignedPageSize, assignedSearchFilters)
      alert('顾问分配已删除！')
    } catch (err: any) {
      setError(err.message || 'Failed to remove assignment')
      console.error(err)
    }
  }

  const openAssignModal = async (jobId: string) => {
    setSelectedJobForAssignment(jobId)
    await fetchConsultants()
    setConsultantSearch('')
    setSelectedConsultantId(null)
    setSelectedConsultant(null)
    setAssignmentNotes('')
    setShowAssignModal(true)
  }

  const filterConsultants = (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setFilteredConsultants([])
      return
    }
    
    const filtered = consultants.filter(consultant => 
      consultant.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      consultant.email?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    setFilteredConsultants(filtered)
  }

  const handleConsultantSearch = (value: string) => {
    setConsultantSearch(value)
    filterConsultants(value)
    setSelectedConsultantId(null)
    setSelectedConsultant(null)
  }

  const selectConsultant = (consultant: any) => {
    setSelectedConsultantId(consultant.id)
    setSelectedConsultant(consultant)
    setConsultantSearch(`${consultant.username} (${consultant.email})`)
    setFilteredConsultants([])
  }

  const confirmAssignment = async () => {
    if (selectedJobForAssignment && selectedConsultant && !assigningJob) {
      setAssigningJob(true)
      try {
        await assignJob(selectedJobForAssignment, selectedConsultant, assignmentNotes)
      } catch (error) {
        console.error('Assignment failed:', error)
      } finally {
        setAssigningJob(false)
      }
    }
  }

  useEffect(() => {
    fetchManagementJobs(currentPage, pageSize, searchFilters)
    fetchAssignedJobs(assignedCurrentPage, assignedPageSize, assignedSearchFilters)
    fetchCompanyClients()
  }, [currentPage, pageSize, assignedCurrentPage, assignedPageSize])

  useEffect(() => {
    setCurrentPage(1)
    fetchManagementJobs(1, pageSize, searchFilters)
  }, [searchFilters])

  useEffect(() => {
    setAssignedCurrentPage(1)
    fetchAssignedJobs(1, assignedPageSize, assignedSearchFilters)
  }, [assignedSearchFilters])

  const handleSearch = () => {
    setSearchFilters(filters)
    setCurrentPage(1)
  }

  const handleReset = () => {
    setFilters({
      jobName: '',
      companyLocation: '',
      jobCategory: ''
    })
    setSearchFilters({
      jobName: '',
      companyLocation: '',
      jobCategory: ''
    })
    setCurrentPage(1)
  }

  const handleAssignedSearch = () => {
    setAssignedSearchFilters(assignedFilters)
    setAssignedCurrentPage(1)
  }

  const handleAssignedReset = () => {
    setAssignedFilters({
      jobName: '',
      companyLocation: '',
      jobCategory: ''
    })
    setAssignedSearchFilters({
      jobName: '',
      companyLocation: '',
      jobCategory: ''
    })
    setAssignedCurrentPage(1)
  }

  const handleJobStatusChange = async (jobId: string, status: string) => {
    try {
      // 调用更新职位状态的API
      await api.patch(`/jobs/${jobId}/status`, { status })
      // 刷新数据
      fetchManagementJobs(currentPage, pageSize, searchFilters)
      fetchAssignedJobs(assignedCurrentPage, assignedPageSize, assignedSearchFilters)
      const statusText = {
        'paused': '暂停',
        'closed': '关闭', 
        'open': '开启'
      }[status] || status
      alert(`职位状态已更新为: ${statusText}`)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update job status')
    }
  }

  const handleBatchExportResumes = async (jobId: string) => {
    try {
      // 这里调用批量导出简历的API
      const response = await api.get(`/jobs/${jobId}/resumes/export`)
      // 处理文件下载
      alert('简历导出功能开发中...')
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to export resumes')
    }
  }

  const canManageJobs = () => {
    return user?.role === UserRole.COMPANY_ADMIN || user?.role === UserRole.PLATFORM_ADMIN
  }

  if (!canManageJobs()) {
    return null
  }

  if (loading) return <div className="p-4">Loading management jobs...</div>

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Pending Assignments Section */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">待分配职位</h3>
          <p className="text-sm text-gray-600">需要指定项目经理和负责顾问的职位</p>
        </div>
        
        {/* 条件查询部分 */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">职位名称</label>
              <input
                type="text"
                value={filters.jobName}
                onChange={(e) => setFilters({...filters, jobName: e.target.value})}
                placeholder="请输入职位名称"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">公司/地点</label>
              <input
                type="text"
                value={filters.companyLocation}
                onChange={(e) => setFilters({...filters, companyLocation: e.target.value})}
                placeholder="请输入公司或地点"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">职位类别</label>
              <input
                type="text"
                value={filters.jobCategory}
                onChange={(e) => setFilters({...filters, jobCategory: e.target.value})}
                placeholder="请输入职位类别"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={handleReset}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 text-sm font-medium transition-colors"
            >
              重置
            </button>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium transition-colors"
            >
              搜索
            </button>
          </div>
        </div>

        <div className="p-6">
          {pendingJobs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无待分配职位</p>
          ) : (
            <>
              {/* 表格形式展示 */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">职位名称</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">公司</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">行业/地点</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">薪资</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">发布信息</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pendingJobs.map((job) => (
                      <tr key={job.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{job.title}</div>
                          {job.urgency && (
                            <div className="mt-1">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                                {job.urgency}
                              </span>
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{job.companyClient?.name || '-'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {job.industry && job.location ? `${job.industry} / ${job.location}` : 
                             job.industry || job.location || '-'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {job.salaryMin && job.salaryMax 
                              ? `¥${job.salaryMin.toLocaleString()} - ¥${job.salaryMax.toLocaleString()}` 
                              : job.salaryMin 
                              ? `¥${job.salaryMin.toLocaleString()}+` 
                              : job.salaryMax 
                              ? `¥${job.salaryMax.toLocaleString()}以下` 
                              : '-'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {new Date(job.createdAt).toLocaleDateString('zh-CN', {
                              year: 'numeric',
                              month: '2-digit', 
                              day: '2-digit'
                            })}
                          </div>
                          <div className="text-xs text-gray-500">{job.publisher?.username}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => openAssignModal(job.id)}
                            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium transition-colors"
                          >
                            分配职位
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* 分页控件 */}
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  显示第 {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, totalItems)} 条，共 {totalItems} 条记录
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-700">每页显示</label>
                    <select
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value))
                        setCurrentPage(1)
                      }}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value={5}>5</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                    </select>
                    <span className="text-sm text-gray-700">条</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      上一页
                    </button>
                    <span className="text-sm text-gray-700">
                      第 {currentPage} 页，共 {Math.ceil(totalItems / pageSize)} 页
                    </span>
                    <button
                      onClick={() => setCurrentPage(Math.min(Math.ceil(totalItems / pageSize), currentPage + 1))}
                      disabled={currentPage >= Math.ceil(totalItems / pageSize)}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Assigned Jobs Section */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">已分配职位</h3>
          <p className="text-sm text-gray-600">已指定项目经理和负责顾问的职位</p>
        </div>
        
        {/* 已分配职位搜索部分 */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">职位名称</label>
              <input
                type="text"
                value={assignedFilters.jobName}
                onChange={(e) => setAssignedFilters({...assignedFilters, jobName: e.target.value})}
                placeholder="请输入职位名称"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleAssignedSearch()}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">公司/地点</label>
              <input
                type="text"
                value={assignedFilters.companyLocation}
                onChange={(e) => setAssignedFilters({...assignedFilters, companyLocation: e.target.value})}
                placeholder="请输入公司或地点"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleAssignedSearch()}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">职位类别</label>
              <input
                type="text"
                value={assignedFilters.jobCategory}
                onChange={(e) => setAssignedFilters({...assignedFilters, jobCategory: e.target.value})}
                placeholder="请输入职位类别"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleAssignedSearch()}
              />
            </div>
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={handleAssignedReset}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 text-sm font-medium transition-colors"
            >
              重置
            </button>
            <button
              onClick={handleAssignedSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium transition-colors"
            >
              搜索
            </button>
          </div>
        </div>

        <div className="p-6">
          {assignedJobs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无已分配职位</p>
          ) : (
            <>
              {/* 表格形式展示 */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">招聘职位</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">职位状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">订单分配时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">投递状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">猎头顾问</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {assignedJobs.map((job) => (
                      <tr key={job.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-blue-600">{job.title}</div>
                            <div className="text-sm text-gray-600">{job.companyClient?.name}</div>
                            <div className="text-sm text-gray-500">
                              {job.industry && job.location ? `${job.industry} / ${job.location}` : 
                               job.industry || job.location || '-'}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            job.status === 'open' ? 'bg-green-100 text-green-800' : 
                            job.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                            job.status === 'closed' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {job.status === 'open' ? '招聘中' : 
                             job.status === 'paused' ? '暂停' :
                             job.status === 'closed' ? '关闭' : job.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {job.assignedAt ? new Date(job.assignedAt).toLocaleDateString('zh-CN', {
                              year: 'numeric',
                              month: '2-digit',
                              day: '2-digit'
                            }) + ' ' + new Date(job.assignedAt).toLocaleTimeString('zh-CN', {
                              hour: '2-digit',
                              minute: '2-digit'
                            }) : '未分配'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            已投递: {job._count?.candidateSubmissions || 0}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {(() => {
                              const consultantPermissions = job.jobPermissions
                                ?.filter(p => p.permissionType === 'progression' && p.grantedToUser?.username) || [];
                              
                              if (consultantPermissions.length === 0) return '未分配';
                              if (consultantPermissions.length === 1) {
                                const permission = consultantPermissions[0];
                                return (
                                  <div className="flex items-center justify-between text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded group">
                                    <span>{permission.grantedToUser.username}</span>
                                    <button
                                      onClick={() => removeAssignment(job.id, permission.grantedToUser.id, permission.grantedToUser.username)}
                                      className="ml-2 text-red-600 hover:text-red-800 opacity-0 group-hover:opacity-100 transition-opacity"
                                      title="删除分配"
                                    >
                                      ×
                                    </button>
                                  </div>
                                );
                              }
                              return (
                                <div className="space-y-1">
                                  {consultantPermissions.map((permission, index) => (
                                    <div key={index} className="flex items-center justify-between text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded group">
                                      <span>{permission.grantedToUser.username}</span>
                                      <button
                                        onClick={() => removeAssignment(job.id, permission.grantedToUser.id, permission.grantedToUser.username)}
                                        className="ml-2 text-red-600 hover:text-red-800 opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="删除分配"
                                      >
                                        ×
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              );
                            })()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex space-x-2 flex-wrap gap-1">
                            {/* 根据职位状态显示不同的操作按钮 */}
                            {job.status === 'open' && (
                              <>
                                <button
                                  onClick={() => openAssignModal(job.id)}
                                  className="text-blue-600 hover:text-blue-800 text-sm font-medium whitespace-nowrap"
                                >
                                  分配职位
                                </button>
                                <button
                                  onClick={() => handleJobStatusChange(job.id, 'paused')}
                                  className="text-yellow-600 hover:text-yellow-800 text-sm font-medium whitespace-nowrap"
                                >
                                  暂停职位
                                </button>
                                <button
                                  onClick={() => handleJobStatusChange(job.id, 'closed')}
                                  className="text-red-600 hover:text-red-800 text-sm font-medium whitespace-nowrap"
                                >
                                  关闭职位
                                </button>
                              </>
                            )}
                            
                            {job.status === 'paused' && (
                              <>
                                <button
                                  onClick={() => openAssignModal(job.id)}
                                  className="text-blue-600 hover:text-blue-800 text-sm font-medium whitespace-nowrap"
                                >
                                  分配职位
                                </button>
                                <button
                                  onClick={() => handleJobStatusChange(job.id, 'open')}
                                  className="text-green-600 hover:text-green-800 text-sm font-medium whitespace-nowrap"
                                >
                                  重新开启
                                </button>
                                <button
                                  onClick={() => handleJobStatusChange(job.id, 'closed')}
                                  className="text-red-600 hover:text-red-800 text-sm font-medium whitespace-nowrap"
                                >
                                  关闭职位
                                </button>
                              </>
                            )}
                            
                            {job.status === 'closed' && (
                              <>
                                <button
                                  onClick={() => handleBatchExportResumes(job.id)}
                                  className="text-green-600 hover:text-green-800 text-sm font-medium whitespace-nowrap"
                                >
                                  批量导出简历
                                </button>
                              </>
                            )}
                            
                            {/* 其他状态的默认操作 */}
                            {!['open', 'paused', 'closed'].includes(job.status) && (
                              <span className="text-gray-400 text-sm">无可用操作</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* 已分配职位分页控件 */}
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  显示第 {(assignedCurrentPage - 1) * assignedPageSize + 1} - {Math.min(assignedCurrentPage * assignedPageSize, assignedTotalItems)} 条，共 {assignedTotalItems} 条记录
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-700">每页显示</label>
                    <select
                      value={assignedPageSize}
                      onChange={(e) => {
                        setAssignedPageSize(Number(e.target.value))
                        setAssignedCurrentPage(1)
                      }}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value={5}>5</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                    </select>
                    <span className="text-sm text-gray-700">条</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setAssignedCurrentPage(Math.max(1, assignedCurrentPage - 1))}
                      disabled={assignedCurrentPage === 1}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      上一页
                    </button>
                    <span className="text-sm text-gray-700">
                      第 {assignedCurrentPage} 页，共 {Math.ceil(assignedTotalItems / assignedPageSize)} 页
                    </span>
                    <button
                      onClick={() => setAssignedCurrentPage(Math.min(Math.ceil(assignedTotalItems / assignedPageSize), assignedCurrentPage + 1))}
                      disabled={assignedCurrentPage >= Math.ceil(assignedTotalItems / assignedPageSize)}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Assignment Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">分配职位</h2>
                <button
                  onClick={() => {
                    setShowAssignModal(false)
                    setSelectedJobForAssignment(null)
                    setSelectedConsultantId(null)
                    setSelectedConsultant(null)
                    setAssignmentNotes('')
                    setConsultantSearch('')
                    setFilteredConsultants([])
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    分派给顾问: <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={consultantSearch}
                      onChange={(e) => handleConsultantSearch(e.target.value)}
                      placeholder="输入姓名可快速搜索"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {filteredConsultants.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        {filteredConsultants.map((consultant) => (
                          <div
                            key={consultant.id}
                            className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                            onClick={() => selectConsultant(consultant)}
                          >
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                <span className="text-blue-600 font-medium text-sm">
                                  {consultant.username?.charAt(0) || '?'}
                                </span>
                              </div>
                              <div>
                                <h4 className="font-medium text-gray-900">{consultant.username}</h4>
                                <p className="text-sm text-gray-600">{consultant.email}</p>
                                <p className="text-sm text-gray-500">
                                  {consultant.role === UserRole.CONSULTANT ? '公司顾问' : 
                                   consultant.role === UserRole.SOHO ? 'SOHO顾问' : consultant.role}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedConsultant && (
                    <div className="mt-2 p-2 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">已选择: {consultantSearch}</p>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    分配说明 (可选)
                  </label>
                  <textarea
                    value={assignmentNotes}
                    onChange={(e) => setAssignmentNotes(e.target.value)}
                    placeholder="请输入分配说明或特殊要求..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-4 mt-6 pt-4 border-t">
                <button
                  onClick={() => {
                    setShowAssignModal(false)
                    setSelectedJobForAssignment(null)
                    setSelectedConsultantId(null)
                    setSelectedConsultant(null)
                    setAssignmentNotes('')
                    setConsultantSearch('')
                    setFilteredConsultants([])
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={confirmAssignment}
                  disabled={!selectedConsultant || assigningJob}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {assigningJob ? '分配中...' : '确认分配'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Progression Area Component - For job progression permissions
function ProgressionArea({ user }: ProgressionAreaProps) {
  const [myJobs, setMyJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalJobs, setTotalJobs] = useState(0)
  const pageSize = 10
  
  // Candidate selection modal states
  const [showCandidateModal, setShowCandidateModal] = useState(false)
  const [selectedJobForSubmission, setSelectedJobForSubmission] = useState<Job | null>(null)
  
  // Quick candidate create modal states
  const [showQuickCreateModal, setShowQuickCreateModal] = useState(false)

  const fetchProgressionJobs = async (page: number = 1) => {
    try {
      setLoading(true)
      const response = await api.get(`/job-management/progression?page=${page}&limit=${pageSize}`)
      setMyJobs(response.jobs || [])
      setTotalJobs(response.pagination?.total || 0)
      setTotalPages(Math.ceil((response.pagination?.total || 0) / pageSize))
      setCurrentPage(page)
    } catch (err: any) {
      setError('Failed to fetch progression jobs')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const openCandidateSelection = (job: Job) => {
    setSelectedJobForSubmission(job)
    setShowCandidateModal(true)
  }

  const copyShareLink = async (jobId: string) => {
    try {
      const shareUrl = `${window.location.origin}/jobs/share/${jobId}`
      await navigator.clipboard.writeText(shareUrl)
      alert('分享链接已复制到剪贴板!')
    } catch (err) {
      const shareUrl = `${window.location.origin}/jobs/share/${jobId}`
      console.log('Share URL:', shareUrl)
      alert(`分享链接: ${shareUrl}`)
    }
  }

  const handleCandidateSelection = async (candidate: any) => {
    if (!selectedJobForSubmission) return
    
    try {
      await api.submitCandidateToJob(candidate.id, {
        jobId: selectedJobForSubmission.id,
        submitReason: '通过系统投递',
        matchExplanation: '候选人技能匹配职位要求'
      })
      alert('候选人投递成功！')
      setShowCandidateModal(false)
      setSelectedJobForSubmission(null)
      fetchProgressionJobs(currentPage)
    } catch (err: any) {
      setError(err.message || '投递失败')
      console.error(err)
    }
  }

  const handleCreateNewCandidate = () => {
    setShowCandidateModal(false)
    setShowQuickCreateModal(true)
  }

  const handleCandidateCreated = async (candidate: any) => {
    if (!selectedJobForSubmission) return
    
    // Automatically submit the newly created candidate to the job
    try {
      await api.submitCandidateToJob(candidate.id, {
        jobId: selectedJobForSubmission.id,
        submitReason: '新建候选人并投递',
        matchExplanation: '新创建的候选人投递到职位'
      })
      alert('候选人创建并投递成功！')
      setShowQuickCreateModal(false)
      setSelectedJobForSubmission(null)
      fetchProgressionJobs(currentPage)
    } catch (err: any) {
      setError(err.message || '投递失败')
      console.error(err)
    }
  }

  useEffect(() => {
    fetchProgressionJobs(1)
  }, [])

  if (loading) return <div className="p-4">Loading progression jobs...</div>

  // Show job detail page if a job is selected
  if (selectedJobId) {
    return <JobDetail jobId={selectedJobId} onBack={() => setSelectedJobId(null)} />
  }

  const getSubmissionStatus = (job: any) => {
    if (!job.candidateSubmissions || job.candidateSubmissions.length === 0) {
      return { status: '未投递', color: 'gray' }
    }
    
    const submissionCount = job.candidateSubmissions.length
    if (submissionCount === 1) {
      const submission = job.candidateSubmissions[0]
      const statusMap: Record<string, { status: string, color: string }> = {
        'pending': { status: '待审核', color: 'yellow' },
        'reviewed': { status: '已审核', color: 'blue' },
        'shortlisted': { status: '已入选', color: 'green' },
        'rejected': { status: '已拒绝', color: 'red' },
        'interview_scheduled': { status: '面试安排', color: 'purple' },
        'offer_made': { status: '已发Offer', color: 'green' },
        'hired': { status: '已录用', color: 'green' },
      }
      return statusMap[submission.status] || { status: submission.status, color: 'gray' }
    } else {
      // 多个投递记录时显示投递数量
      return { status: `已投递 ${submissionCount} 人`, color: 'blue' }
    }
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* My Jobs Section with Table Layout */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium text-gray-900">我的职位</h3>
              <p className="text-sm text-gray-600">
                {user?.role === UserRole.CONSULTANT ? '公司内可投递的职位' : 
                 user?.role === UserRole.SOHO ? '分配给我的职位' : '可投递的职位'}
                {totalJobs > 0 && ` (共 ${totalJobs} 个职位)`}
              </p>
            </div>
          </div>
        </div>

        {myJobs.length === 0 ? (
          <div className="p-6">
            <p className="text-gray-500 text-center py-8">暂无可投递职位</p>
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      招聘职位
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      订单状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      订单分配时间
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      投递状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {myJobs.map((job) => {
                    const submissionStatus = getSubmissionStatus(job)
                    return (
                      <tr key={job.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <button 
                              onClick={() => setSelectedJobId(job.id)}
                              className="text-sm font-medium text-blue-600 hover:text-blue-800 text-left"
                            >
                              {job.title}
                            </button>
                            <div className="text-sm text-gray-600 mt-1">
                              {job.companyClient?.name}
                            </div>
                            {(job.industry || job.location) && (
                              <div className="text-xs text-gray-500 mt-1">
                                {job.industry && job.location ? `${job.industry} • ${job.location}` : 
                                 job.industry || job.location}
                              </div>
                            )}
                            {(job.salaryMin || job.salaryMax) && (
                              <div className="text-xs text-gray-600 mt-1">
                                {job.salaryMin && job.salaryMax ? `¥${job.salaryMin.toLocaleString()} - ¥${job.salaryMax.toLocaleString()}` : 
                                 job.salaryMin ? `¥${job.salaryMin.toLocaleString()}+` : 
                                 job.salaryMax ? `¥${job.salaryMax.toLocaleString()}以下` : ''}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            {job.status === 'open' ? '开放' : job.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {job.assignedAt ? new Date(job.assignedAt).toLocaleDateString('zh-CN') : new Date(job.createdAt).toLocaleDateString('zh-CN')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                            ${submissionStatus.color === 'green' ? 'bg-green-100 text-green-800' :
                              submissionStatus.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                              submissionStatus.color === 'blue' ? 'bg-blue-100 text-blue-800' :
                              submissionStatus.color === 'red' ? 'bg-red-100 text-red-800' :
                              submissionStatus.color === 'purple' ? 'bg-purple-100 text-purple-800' :
                              'bg-gray-100 text-gray-800'}`}>
                            {submissionStatus.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => setSelectedJobId(job.id)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              查看
                            </button>
                            <button
                              onClick={() => openCandidateSelection(job)}
                              className="text-orange-600 hover:text-orange-900"
                            >
                              投递简历
                            </button>
                            <button
                              onClick={() => copyShareLink(job.id)}
                              className="text-purple-600 hover:text-purple-900 flex items-center space-x-1"
                              title="复制分享链接"
                            >
                              <span>🔗</span>
                              <span>分享</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => currentPage > 1 && fetchProgressionJobs(currentPage - 1)}
                    disabled={currentPage <= 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => currentPage < totalPages && fetchProgressionJobs(currentPage + 1)}
                    disabled={currentPage >= totalPages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    下一页
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      显示第 <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> 到{' '}
                      <span className="font-medium">{Math.min(currentPage * pageSize, totalJobs)}</span> 条，共{' '}
                      <span className="font-medium">{totalJobs}</span> 条记录
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => currentPage > 1 && fetchProgressionJobs(currentPage - 1)}
                        disabled={currentPage <= 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        上一页
                      </button>
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        const pageNum = currentPage <= 3 ? i + 1 : 
                                       currentPage >= totalPages - 2 ? totalPages - 4 + i : 
                                       currentPage - 2 + i;
                        if (pageNum < 1 || pageNum > totalPages) return null;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => fetchProgressionJobs(pageNum)}
                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                              pageNum === currentPage
                                ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                      <button
                        onClick={() => currentPage < totalPages && fetchProgressionJobs(currentPage + 1)}
                        disabled={currentPage >= totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        下一页
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Candidate Selection Modal */}
      <CandidateSelectionModal
        isOpen={showCandidateModal}
        onClose={() => {
          setShowCandidateModal(false)
          setSelectedJobForSubmission(null)
        }}
        onSelectCandidate={handleCandidateSelection}
        onCreateNew={handleCreateNewCandidate}
        jobTitle={selectedJobForSubmission?.title}
        jobId={selectedJobForSubmission?.id}
      />

      {/* Quick Candidate Create Modal */}
      <QuickCandidateCreateModal
        isOpen={showQuickCreateModal}
        onClose={() => {
          setShowQuickCreateModal(false)
          setSelectedJobForSubmission(null)
        }}
        onCandidateCreated={handleCandidateCreated}
      />
    </div>
  )
}

// Main Dual Area Job Management Component
export default function JobManagementDual() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'management' | 'progression'>('progression')

  const canManageJobs = () => {
    return user?.role === UserRole.COMPANY_ADMIN || user?.role === UserRole.PLATFORM_ADMIN
  }

  const canProgressJobs = () => {
    return user?.role === UserRole.CONSULTANT || user?.role === UserRole.SOHO || 
           user?.role === UserRole.COMPANY_ADMIN || user?.role === UserRole.PLATFORM_ADMIN
  }

  // Default to management tab if user can manage but not progress (unlikely scenario)
  useEffect(() => {
    if (canManageJobs() && !canProgressJobs()) {
      setActiveTab('management')
    } else if (!canManageJobs() && canProgressJobs()) {
      setActiveTab('progression')
    }
  }, [user])

  if (!user) {
    return <div className="p-6">Please log in to access job management.</div>
  }

  if (!canManageJobs() && !canProgressJobs()) {
    return <div className="p-6">You don't have permission to access job management.</div>
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">职位管理</h1>
        <p className="text-gray-600">管理职位分配和投递简历</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {canProgressJobs() && (
            <button
              onClick={() => setActiveTab('progression')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'progression'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              职位推进
            </button>
          )}
          {canManageJobs() && (
            <button
              onClick={() => setActiveTab('management')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'management'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              职位管理
            </button>
          )}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'management' && canManageJobs() && <ManagementArea user={user} />}
      {activeTab === 'progression' && canProgressJobs() && <ProgressionArea user={user} />}
    </div>
  )
}