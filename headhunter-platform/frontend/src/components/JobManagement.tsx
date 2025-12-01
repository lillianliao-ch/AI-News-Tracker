'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useAuth } from './AuthProvider'
import { UserRole } from '@/types'
import JobDetail from './JobDetail'

interface Job {
  id: string
  title: string
  industry?: string
  location?: string
  salaryMin?: number
  salaryMax?: number
  description: string
  requirements: string
  status: 'pending_approval' | 'approved' | 'open' | 'paused' | 'closed' | 'rejected'
  publisher: {
    id: string
    username: string
    company?: {
      id: string
      name: string
    }
  }
  companyClient: {
    name: string
    industry?: string
    location?: string
  }
  _count: {
    candidateSubmissions: number
  }
  createdAt: string
}

interface CreateJobData {
  title: string
  industry?: string
  location?: string
  salaryMin?: number
  salaryMax?: number
  description: string
  requirements: string
  benefits?: string
  urgency?: string
  reportTo?: string
  publisherSharePct: number
  referrerSharePct: number
  platformSharePct: number
  companyClientId: string
}

export default function JobManagement() {
  const { user } = useAuth()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [companyClients, setCompanyClients] = useState<any[]>([])
  const [filters, setFilters] = useState({
    status: '',
    companyClient: '',
    location: '',
    search: ''
  })
  const [isParsingImage, setIsParsingImage] = useState(false)
  const [parsedJobData, setParsedJobData] = useState<CreateJobData | null>(null)
  const [showParsedJobConfirmation, setShowParsedJobConfirmation] = useState(false)
  const [lastUploadedFile, setLastUploadedFile] = useState<File | null>(null)
  
  // SOHO assignment modal states
  const [showSohoModal, setShowSohoModal] = useState(false)
  const [selectedJobForAssignment, setSelectedJobForAssignment] = useState<string | null>(null)
  const [sohoConsultants, setSohoConsultants] = useState<any[]>([])
  const [sohoSearchTerm, setSohoSearchTerm] = useState('')
  const [selectedSohoId, setSelectedSohoId] = useState<string | null>(null)
  const [assignmentNotes, setAssignmentNotes] = useState('')

  const [newJob, setNewJob] = useState<CreateJobData>({
    title: '',
    industry: '',
    location: '',
    salaryMin: undefined,
    salaryMax: undefined,
    description: '',
    requirements: '',
    benefits: '',
    urgency: '',
    reportTo: '',
    publisherSharePct: 60,
    referrerSharePct: 30,
    platformSharePct: 10,
    companyClientId: ''
  })

  const fetchJobs = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10',
        ...Object.fromEntries(Object.entries(filters).filter(([_, value]) => value))
      })
      
      const response = await api.get(`/jobs?${params}`)
      setJobs(response.jobs)
      setTotalPages(response.pagination.pages)
    } catch (err) {
      setError('Failed to fetch jobs')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchCompanyClients = async () => {
    try {
      // 只获取当前用户公司合作的客户公司
      const response = await api.getCompanyClients({ 
        limit: 100
        // API已经根据用户的companyId进行过滤，返回partnerCompanyId匹配的客户公司
      })
      console.log('Fetched company clients:', response.companyClients)
      setCompanyClients(response.companyClients || [])
    } catch (err) {
      console.error('Failed to fetch company clients:', err)
    }
  }

  const createJob = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('') // Clear previous errors
    try {
      console.log('Creating job with data:', newJob)
      
      // Validate share percentages
      const totalShare = newJob.publisherSharePct + newJob.referrerSharePct + newJob.platformSharePct
      if (Math.abs(totalShare - 100) > 0.01) {
        setError('Share percentages must sum to 100%')
        return
      }

      // Validate required fields
      if (!newJob.companyClientId) {
        setError('Please select a company client')
        return
      }

      const response = await api.post('/jobs', newJob)
      console.log('Job created successfully:', response)
      
      setShowCreateForm(false)
      setNewJob({
        title: '',
        industry: '',
        location: '',
        salaryMin: undefined,
        salaryMax: undefined,
        description: '',
        requirements: '',
        benefits: '',
        urgency: '',
        reportTo: '',
        publisherSharePct: 60,
        referrerSharePct: 30,
        platformSharePct: 10,
        companyClientId: ''
      })
      fetchJobs()
    } catch (err: any) {
      console.error('Error creating job:', err)
      const errorMessage = err.response?.data?.message || err.message || 'Failed to create job'
      setError(errorMessage)
    }
  }

  const updateJobStatus = async (jobId: string, status: 'pending_approval' | 'approved' | 'open' | 'paused' | 'closed' | 'rejected') => {
    try {
      await api.patch(`/jobs/${jobId}/status`, { status })
      fetchJobs()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update job status')
    }
  }

  const approveJob = async (jobId: string) => {
    try {
      await api.patch(`/jobs/${jobId}/approve`, {})
      fetchJobs()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to approve job')
    }
  }

  // Load SOHO consultants
  const loadSohoConsultants = async () => {
    try {
      const response = await api.get('/users/soho-consultants')
      if (response.success) {
        setSohoConsultants(response.data)
      }
    } catch (err) {
      console.error('Error loading SOHO consultants:', err)
    }
  }

  const assignJobToSoho = async (jobId: string) => {
    setSelectedJobForAssignment(jobId)
    await loadSohoConsultants()
    setShowSohoModal(true)
  }

  const confirmSohoAssignment = async () => {
    if (!selectedSohoId || !selectedJobForAssignment) return
    
    const selectedConsultant = sohoConsultants.find(c => c.id === selectedSohoId)
    if (!selectedConsultant) return

    try {
      await api.post(`/jobs/${selectedJobForAssignment}/assign-soho`, { 
        email: selectedConsultant.email,
        notes: assignmentNotes 
      })
      
      // Close modal and reset states
      setShowSohoModal(false)
      setSelectedJobForAssignment(null)
      setSelectedSohoId(null)
      setAssignmentNotes('')
      setSohoSearchTerm('')
      
      // Refresh jobs list
      fetchJobs()
      
      alert(`职位已成功分配给 ${selectedConsultant.username}！`)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to assign job')
    }
  }

  const parseJobFromImage = async (file: File) => {
    try {
      console.log('🔥 DEBUGGING: parseJobFromImage called with file:', file.name, file.type)
      setIsParsingImage(true)
      setError('')
      
      // Clear previous parsed data to avoid showing stale information
      setParsedJobData(null)
      setShowParsedJobConfirmation(false)
      
      // Save the file for potential re-parsing
      setLastUploadedFile(file)
      
      const formData = new FormData()
      formData.append('image', file)
      console.log('🔥 DEBUGGING: FormData created with entries:')
      for (let [key, value] of formData.entries()) {
        console.log('🔥', key, ':', value)
      }
      console.log('🔥 DEBUGGING: File details - name:', file.name, 'type:', file.type, 'size:', file.size)
      
      // Use fetch directly to bypass any caching issues
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`http://localhost:4002/api/upload/parse-job-image?timestamp=${Date.now()}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          // Let browser set Content-Type with boundary for FormData
        },
        body: formData,
        cache: 'no-cache'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      console.log('🔥 DEBUGGING: Response received:', result)
      
      if (result.success && result.parsedJob) {
        const parsed = result.parsedJob
        const parsedData: CreateJobData = {
          title: parsed.title || '',
          industry: parsed.industry || '',
          location: parsed.location || '',
          salaryMin: parsed.salaryMin || undefined,
          salaryMax: parsed.salaryMax || undefined,
          description: parsed.description || '',
          requirements: parsed.requirements || '',
          benefits: parsed.benefits || '',
          urgency: parsed.urgency || '',
          reportTo: parsed.reportTo || '',
          publisherSharePct: 60,
          referrerSharePct: 30,
          platformSharePct: 10,
          companyClientId: ''
        }
        
        setParsedJobData(parsedData)
        setShowParsedJobConfirmation(true)
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to parse image. Please try again.')
    } finally {
      setIsParsingImage(false)
    }
  }

  const handleImageUpload = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        // Clear any existing parsed data when selecting a new file
        setParsedJobData(null)
        setShowParsedJobConfirmation(false)
        parseJobFromImage(file)
      }
    }
    input.click()
  }

  const confirmParsedJob = () => {
    if (parsedJobData) {
      setNewJob(parsedJobData)
      setShowParsedJobConfirmation(false)
      setShowCreateForm(true)
    }
  }

  const rejectParsedJob = async () => {
    // Clear current parsed data first
    setParsedJobData(null)
    setShowParsedJobConfirmation(false)
    
    if (lastUploadedFile) {
      // Re-parse the same image file
      console.log('🔄 Re-parsing file:', lastUploadedFile.name)
      await parseJobFromImage(lastUploadedFile)
    } else {
      // No file to re-parse, close the modal and allow user to upload again
      console.log('⚠️ No file to re-parse, closing modal')
    }
  }

  const closeParsedJobModal = () => {
    setParsedJobData(null)
    setShowParsedJobConfirmation(false)
    setLastUploadedFile(null)
  }

  const submitResume = async (jobId: string) => {
    // TODO: Implement file upload for resume
    const fileInput = document.createElement('input')
    fileInput.type = 'file'
    fileInput.accept = '.pdf,.doc,.docx'
    fileInput.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return
      
      const formData = new FormData()
      formData.append('resume', file)
      formData.append('jobId', jobId)
      
      try {
        await api.post(`/candidate-submissions`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        alert('简历提交成功！')
        fetchJobs() // Refresh to show updated submission count
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to submit resume')
      }
    }
    fileInput.click()
  }

  const shareJob = async (jobId: string, targetUserId?: string, targetCompanyId?: string) => {
    try {
      const data: any = {}
      if (targetUserId) data.targetUserId = targetUserId
      if (targetCompanyId) data.targetCompanyId = targetCompanyId
      
      await api.post(`/jobs/${jobId}/share`, data)
      alert('Job shared successfully!')
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to share job')
    }
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

  const canAssignJob = (job: Job) => {
    if (!user) return false

    switch (user.role) {
      case UserRole.COMPANY_ADMIN:
        // 公司admin可以分配该公司所有的职位给soho顾问
        return user.companyId && job.publisher.company?.id === user.companyId
      
      case UserRole.SOHO:
        // soho顾问可以将自己创建的职位分配给其他soho顾问，或者分配给其他公司的admin
        return job.publisher.id === user.id
      
      case UserRole.CONSULTANT:
        // 公司顾问不能分配职位
        return false
      
      case UserRole.PLATFORM_ADMIN:
        // 平台管理员可以分配所有职位
        return true
      
      default:
        return false
    }
  }

  const canUpdateJobStatus = (job: Job) => {
    if (!user) return false

    switch (user.role) {
      case UserRole.COMPANY_ADMIN:
        // 公司admin可以更新该公司所有的职位状态
        return user.companyId && job.publisher.company?.id === user.companyId
      
      case UserRole.CONSULTANT:
        // 公司顾问只能更新自己发布的职位状态
        return job.publisher.id === user.id
      
      case UserRole.SOHO:
        // SOHO顾问只能更新自己发布的职位状态
        return job.publisher.id === user.id
      
      case UserRole.PLATFORM_ADMIN:
        // 平台管理员可以更新所有职位状态
        return true
      
      default:
        return false
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [page, filters])

  useEffect(() => {
    fetchCompanyClients()
  }, [])

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return 'Salary not specified'
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`
    if (min) return `From $${min.toLocaleString()}`
    if (max) return `Up to $${max.toLocaleString()}`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending_approval': return 'text-orange-600 bg-orange-100'
      case 'approved': return 'text-blue-600 bg-blue-100'
      case 'open': return 'text-green-600 bg-green-100'
      case 'paused': return 'text-yellow-600 bg-yellow-100'
      case 'closed': return 'text-red-600 bg-red-100'
      case 'rejected': return 'text-red-600 bg-red-200'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  if (loading) return <div className="p-6">Loading jobs...</div>

  // Show job detail page if a job is selected
  if (selectedJobId) {
    return <JobDetail jobId={selectedJobId} onBack={() => setSelectedJobId(null)} />
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Job Management</h1>
        <div className="flex space-x-3">
          <button
            onClick={handleImageUpload}
            disabled={isParsingImage}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isParsingImage ? (
              <>
                <span className="animate-spin">⏳</span>
                <span>解析中...</span>
              </>
            ) : (
              <>
                <span>📷</span>
                <span>从图片创建</span>
              </>
            )}
          </button>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            手动创建
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Search jobs..."
            value={filters.search}
            onChange={(e) => setFilters({...filters, search: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          />
          <select
            value={filters.status}
            onChange={(e) => setFilters({...filters, status: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="">All Status</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="approved">Approved</option>
            <option value="open">Open</option>
            <option value="paused">Paused</option>
            <option value="closed">Closed</option>
            <option value="rejected">Rejected</option>
          </select>
          <select
            value={filters.companyClient}
            onChange={(e) => setFilters({...filters, companyClient: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="">All Company Clients</option>
            {companyClients.map((client) => (
              <option key={client.id} value={client.name}>
                {client.name}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Location"
            value={filters.location}
            onChange={(e) => setFilters({...filters, location: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          />
        </div>
      </div>

      {/* Jobs List - Table Format */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input type="checkbox" className="rounded border-gray-300" />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                招聘职位
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                工作地点
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                更新日期
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                职位发布人
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <input type="checkbox" className="rounded border-gray-300" />
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-col">
                    <button 
                      onClick={() => setSelectedJobId(job.id)}
                      className="text-sm font-medium text-blue-600 hover:text-blue-800 text-left"
                    >
                      {job.title}
                    </button>
                    <div className="text-sm text-gray-500">
                      {job.companyClient.name}
                      {job.industry && ` · ${job.industry}`}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {formatSalary(job.salaryMin, job.salaryMax)}
                    </div>
                    <div className="flex items-center mt-2">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(job.status)}`}>
                        {job.status === 'pending_approval' ? '待审核' : 
                         job.status === 'approved' ? '已审核' :
                         job.status === 'open' ? '开放' :
                         job.status === 'paused' ? '暂停' :
                         job.status === 'closed' ? '关闭' :
                         job.status === 'rejected' ? '已拒绝' : job.status}
                      </span>
                      <span className="ml-2 text-xs text-gray-500">
                        {job._count.candidateSubmissions} 个投递
                      </span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {job.location || '未指定'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {new Date(job.updatedAt).toLocaleDateString('zh-CN', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {job.publisher.username}
                    {job.publisher.company && (
                      <div className="text-xs text-gray-500">
                        {job.publisher.company.name}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex space-x-2">
                    {job.status === 'pending_approval' && user?.role === 'company_admin' && (
                      <button
                        onClick={() => approveJob(job.id)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        生效
                      </button>
                    )}
                    {canAssignJob(job) && job.status === 'open' && (
                      <button
                        onClick={() => assignJobToSoho(job.id)}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                      >
                        分配给SOHO
                      </button>
                    )}
                    <button
                      onClick={() => submitResume(job.id)}
                      className="bg-orange-500 text-white px-3 py-1 rounded text-sm hover:bg-orange-600"
                    >
                      递交简历
                    </button>
                    {(job.status === 'approved' || job.status === 'open') && (
                      <button
                        onClick={() => copyShareLink(job.id)}
                        className="bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600"
                        title="复制分享链接"
                      >
                        🔗 分享
                      </button>
                    )}
                    {canUpdateJobStatus(job) ? (
                      <select
                        value={job.status}
                        onChange={(e) => updateJobStatus(job.id, e.target.value as any)}
                        className="border border-gray-300 rounded px-2 py-1 text-xs"
                      >
                        <option value="pending_approval">待审核</option>
                        <option value="approved">已审核</option>
                        <option value="open">开放</option>
                        <option value="paused">暂停</option>
                        <option value="closed">关闭</option>
                        <option value="rejected">已拒绝</option>
                      </select>
                    ) : (
                      <span className="px-2 py-1 text-xs text-gray-600 bg-gray-100 rounded">
                        {job.status === 'pending_approval' ? '待审核' : 
                         job.status === 'approved' ? '已审核' :
                         job.status === 'open' ? '开放' :
                         job.status === 'paused' ? '暂停' :
                         job.status === 'closed' ? '关闭' :
                         job.status === 'rejected' ? '已拒绝' : job.status}
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-center mt-6">
        <div className="flex space-x-2">
          <button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-3 py-1">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      {/* Create Job Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">Create New Job</h2>
              <form onSubmit={createJob} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={newJob.title}
                    onChange={(e) => setNewJob({...newJob, title: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Industry
                    </label>
                    <input
                      type="text"
                      value={newJob.industry}
                      onChange={(e) => setNewJob({...newJob, industry: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <input
                      type="text"
                      value={newJob.location}
                      onChange={(e) => setNewJob({...newJob, location: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Minimum Salary
                    </label>
                    <input
                      type="number"
                      value={newJob.salaryMin || ''}
                      onChange={(e) => setNewJob({...newJob, salaryMin: e.target.value ? Number(e.target.value) : undefined})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Maximum Salary
                    </label>
                    <input
                      type="number"
                      value={newJob.salaryMax || ''}
                      onChange={(e) => setNewJob({...newJob, salaryMax: e.target.value ? Number(e.target.value) : undefined})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Client *
                  </label>
                  <select
                    required
                    value={newJob.companyClientId}
                    onChange={(e) => setNewJob({...newJob, companyClientId: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="">Select Company Client</option>
                    {companyClients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Description *
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={newJob.description}
                    onChange={(e) => setNewJob({...newJob, description: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Requirements *
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={newJob.requirements}
                    onChange={(e) => setNewJob({...newJob, requirements: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Share Percentages (must sum to 100%)
                  </label>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs text-gray-600">Publisher %</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={newJob.publisherSharePct}
                        onChange={(e) => setNewJob({...newJob, publisherSharePct: Number(e.target.value)})}
                        className="w-full border border-gray-300 rounded px-2 py-1"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600">Referrer %</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={newJob.referrerSharePct}
                        onChange={(e) => setNewJob({...newJob, referrerSharePct: Number(e.target.value)})}
                        className="w-full border border-gray-300 rounded px-2 py-1"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600">Platform %</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={newJob.platformSharePct}
                        onChange={(e) => setNewJob({...newJob, platformSharePct: Number(e.target.value)})}
                        className="w-full border border-gray-300 rounded px-2 py-1"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Total: {newJob.publisherSharePct + newJob.referrerSharePct + newJob.platformSharePct}%
                  </p>
                </div>

                <div className="flex justify-end space-x-4 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Create Job
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Parsed Job Confirmation Modal */}
      {showParsedJobConfirmation && parsedJobData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">📷 图片解析结果确认</h2>
                <button
                  onClick={closeParsedJobModal}
                  className="text-gray-400 hover:text-gray-600 p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  ✕
                </button>
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p className="text-blue-700 text-sm">
                  ✅ 已成功解析图片中的职位信息。请检查并确认以下信息是否正确，然后点击"确认并创建"进入编辑页面。
                </p>
              </div>

              {/* 基本信息 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">职位标题</label>
                  <input
                    type="text"
                    value={parsedJobData.title || ''}
                    onChange={(e) => setParsedJobData(prev => prev ? {...prev, title: e.target.value} : prev)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="请输入职位标题"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">行业</label>
                  <input
                    type="text"
                    value={parsedJobData.industry || ''}
                    onChange={(e) => setParsedJobData(prev => prev ? {...prev, industry: e.target.value} : prev)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="请输入行业"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">工作地点</label>
                  <input
                    type="text"
                    value={parsedJobData.location || ''}
                    onChange={(e) => setParsedJobData(prev => prev ? {...prev, location: e.target.value} : prev)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="请输入工作地点"
                  />
                </div>
              </div>

              {/* 薪资信息 */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">最低薪资</label>
                  <input
                    type="number"
                    value={parsedJobData.salaryMin || ''}
                    onChange={(e) => setParsedJobData(prev => prev ? {...prev, salaryMin: e.target.value ? parseInt(e.target.value) : undefined} : prev)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="最低薪资"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">最高薪资</label>
                  <input
                    type="number"
                    value={parsedJobData.salaryMax || ''}
                    onChange={(e) => setParsedJobData(prev => prev ? {...prev, salaryMax: e.target.value ? parseInt(e.target.value) : undefined} : prev)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="最高薪资"
                  />
                </div>
              </div>

              {/* 详细信息 - 更大的文本区域 */}
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">职位描述</label>
                  <textarea
                    value={parsedJobData.description || ''}
                    onChange={(e) => setParsedJobData(prev => prev ? {...prev, description: e.target.value} : prev)}
                    className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                    rows={6}
                    placeholder="请输入职位描述，包括工作职责、岗位要求等详细信息..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">职位要求</label>
                  <textarea
                    value={parsedJobData.requirements || ''}
                    onChange={(e) => setParsedJobData(prev => prev ? {...prev, requirements: e.target.value} : prev)}
                    className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                    rows={6}
                    placeholder="请输入职位要求，包括技能要求、工作经验、学历要求等..."
                  />
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t">
                <h3 className="text-lg font-medium text-gray-900 mb-4">其他信息</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">福利待遇</label>
                    <input
                      type="text"
                      value={parsedJobData.benefits || ''}
                      onChange={(e) => setParsedJobData(prev => prev ? {...prev, benefits: e.target.value} : prev)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="请输入福利待遇"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">紧急程度</label>
                    <input
                      type="text"
                      value={parsedJobData.urgency || ''}
                      onChange={(e) => setParsedJobData(prev => prev ? {...prev, urgency: e.target.value} : prev)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="请输入紧急程度"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">汇报对象</label>
                    <input
                      type="text"
                      value={parsedJobData.reportTo || ''}
                      onChange={(e) => setParsedJobData(prev => prev ? {...prev, reportTo: e.target.value} : prev)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="请输入汇报对象"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-4 pt-6 border-t mt-6">
                <button
                  onClick={rejectParsedJob}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  重新解析
                </button>
                <button
                  onClick={confirmParsedJob}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  确认并创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SOHO Assignment Modal */}
      {showSohoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">分配职位给SOHO顾问</h2>
                <button
                  onClick={() => {
                    setShowSohoModal(false)
                    setSelectedJobForAssignment(null)
                    setSelectedSohoId(null)
                    setAssignmentNotes('')
                    setSohoSearchTerm('')
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {/* Search Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    搜索SOHO顾问
                  </label>
                  <input
                    type="text"
                    value={sohoSearchTerm}
                    onChange={(e) => setSohoSearchTerm(e.target.value)}
                    placeholder="输入顾问姓名或邮箱进行搜索..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* SOHO Consultants List */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    选择SOHO顾问
                  </label>
                  <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-lg">
                    {sohoConsultants
                      .filter(consultant => 
                        sohoSearchTerm === '' || 
                        consultant.username.toLowerCase().includes(sohoSearchTerm.toLowerCase()) ||
                        consultant.email.toLowerCase().includes(sohoSearchTerm.toLowerCase())
                      )
                      .map((consultant) => (
                        <div 
                          key={consultant.id} 
                          className={`p-3 border-b border-gray-200 last:border-b-0 cursor-pointer hover:bg-gray-50 ${
                            selectedSohoId === consultant.id ? 'bg-blue-50 border-blue-200' : ''
                          }`}
                          onClick={() => setSelectedSohoId(consultant.id)}
                        >
                          <div className="flex items-center space-x-3">
                            <input
                              type="radio"
                              checked={selectedSohoId === consultant.id}
                              onChange={() => setSelectedSohoId(consultant.id)}
                              className="text-blue-600"
                            />
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                                  <span className="text-orange-600 font-medium text-sm">
                                    {consultant.username?.charAt(0) || '?'}
                                  </span>
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-900">{consultant.username}</h4>
                                  <p className="text-sm text-gray-600">{consultant.email}</p>
                                </div>
                              </div>
                              {consultant.profile && (
                                <div className="mt-2 text-sm text-gray-600">
                                  <p>专业领域: {consultant.profile.specialization || '未设置'}</p>
                                  <p>工作经验: {consultant.profile.experience || '未设置'}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    }
                    {sohoConsultants.filter(consultant => 
                      sohoSearchTerm === '' || 
                      consultant.username.toLowerCase().includes(sohoSearchTerm.toLowerCase()) ||
                      consultant.email.toLowerCase().includes(sohoSearchTerm.toLowerCase())
                    ).length === 0 && (
                      <div className="p-4 text-center text-gray-500">
                        {sohoSearchTerm ? '没有找到匹配的SOHO顾问' : '暂无SOHO顾问'}
                      </div>
                    )}
                  </div>
                </div>

                {/* Assignment Notes */}
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
                    setShowSohoModal(false)
                    setSelectedJobForAssignment(null)
                    setSelectedSohoId(null)
                    setAssignmentNotes('')
                    setSohoSearchTerm('')
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={confirmSohoAssignment}
                  disabled={!selectedSohoId}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  确认分配
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}