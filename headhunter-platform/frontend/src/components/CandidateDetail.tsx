'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useAuth } from './AuthProvider'
import CandidateEditModal from './CandidateEditModal'
import ContactCandidateModal from './ContactCandidateModal'
import CommunicationRecordsList from './CommunicationRecordsList'

interface CandidateDetail {
  id: string
  name: string
  phone: string
  email?: string
  tags: string[]
  location?: string
  experience?: string
  education?: string
  currentPosition?: string
  expectedSalary?: string
  status?: 'active' | 'inactive' | 'hired' | 'interviewing'
  avatar?: string
  lastContact?: string
  rating?: number
  maintainer: {
    username: string
    company?: {
      name: string
    }
  }
  createdAt: string
  personalInfo?: {
    age?: number
    gender?: string
    maritalStatus?: string
    workPermit?: string
    nationality?: string
    linkedIn?: string
    github?: string
    portfolio?: string
  }
  workHistory?: Array<{
    company: string
    position: string
    startDate: string
    endDate?: string
    description: string
    industry: string
    achievements: string[]
  }>
  educationHistory?: Array<{
    school: string
    degree: string
    major: string
    startDate: string
    endDate: string
    gpa?: string
  }>
  projectExperience?: Array<{
    projectName: string
    startDate: string
    endDate: string | null
    role: string
    description: string
    responsibilities: string[]
    technologies?: string[]
    achievements?: string[]
  }>
  skills?: Array<{
    name: string
    level: 'beginner' | 'intermediate' | 'advanced' | 'expert'
    yearsOfExperience: number
    category: string
  }>
  languages?: Array<{
    language: string
    proficiency: 'basic' | 'conversational' | 'business' | 'native'
  }>
  resumes?: Array<{
    id: string
    filename: string
    uploadDate: string
    fileSize: string
    type: string
    isActive: boolean
  }>
  applications?: Array<{
    id: string
    jobTitle: string
    companyName: string
    status: 'submitted' | 'reviewing' | 'interview' | 'offer' | 'rejected'
    appliedDate: string
    notes?: string
  }>
  notes?: Array<{
    id: string
    content: string
    createdBy: string
    createdAt: string
    type: 'interview' | 'call' | 'email' | 'meeting' | 'other'
  }>
}

interface CandidateDetailProps {
  candidateId: string
  onBack: () => void
}

export default function CandidateDetail({ candidateId, onBack }: CandidateDetailProps) {
  const { user, token, loading: authLoading } = useAuth()
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'overview' | 'resume' | 'applications' | 'notes'>('overview')
  const [showAddNote, setShowAddNote] = useState(false)
  const [newNote, setNewNote] = useState({ content: '', type: 'other' as const })
  
  // Contact candidate modal states
  const [showContactModal, setShowContactModal] = useState(false)
  
  // Recommend job modal states  
  const [showRecommendModal, setShowRecommendModal] = useState(false)
  const [availableJobs, setAvailableJobs] = useState<any[]>([])
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([])
  const [recommendMessage, setRecommendMessage] = useState('')
  
  // Edit candidate modal states
  const [showEditModal, setShowEditModal] = useState(false)
  // const [editForm, setEditForm] = useState<any>({}) // Replaced by CandidateEditModal
  
  // Add application modal states
  const [showAddApplicationModal, setShowAddApplicationModal] = useState(false)
  const [newApplication, setNewApplication] = useState({
    jobTitle: '',
    companyName: '',
    status: 'submitted' as const,
    notes: ''
  })

  useEffect(() => {
    fetchCandidateDetail()
  }, [candidateId])

  const fetchCandidateDetail = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/candidates/${candidateId}`)
      if (response.candidate) {
        setCandidate(response.candidate)
      } else {
        setError('Candidate not found')
      }
    } catch (err: any) {
      console.error('Error fetching candidate details:', err)
      if (err.message?.includes('404') || err.message?.includes('not found')) {
        setError('Candidate not found')
      } else if (err.message?.includes('401') || err.message?.includes('Unauthorized')) {
        setError('Authentication required. Please login again.')
      } else {
        setError(`Failed to fetch candidate details: ${err.message || 'Unknown error'}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const addNote = async () => {
    try {
      await api.post(`/candidates/${candidateId}/notes`, newNote)
      setShowAddNote(false)
      setNewNote({ content: '', type: 'other' })
      fetchCandidateDetail()
    } catch (err) {
      setError('Failed to add note')
    }
  }

  const updateCandidateStatus = async (status: string) => {
    try {
      await api.patch(`/candidates/${candidateId}`, { status })
      fetchCandidateDetail()
    } catch (err) {
      setError('Failed to update status')
    }
  }

  // Job search functionality
  const [jobSearchTerm, setJobSearchTerm] = useState('')
  const [searchedJobs, setSearchedJobs] = useState<any[]>([])
  const [isSearchingJobs, setIsSearchingJobs] = useState(false)
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null)

  // Load available jobs for recommendation
  const loadAvailableJobs = async () => {
    try {
      // Check if user is authenticated
      if (!user || !token) {
        console.error('User not authenticated, cannot load jobs')
        setAvailableJobs([])
        setSearchedJobs([])
        return
      }

      setIsSearchingJobs(true)
      console.log('Loading jobs with auth token:', token ? 'Token present' : 'No token')
      
      const url = '/jobs?' + new URLSearchParams({
        status: 'open',
        limit: '50'
      }).toString()
      
      console.log('Making API request to:', url)
      const response = await api.get(url)
      console.log('Jobs API response:', response)
      
      // Handle direct API response format
      const jobs = response.jobs || []
      console.log('Jobs found:', jobs.length)
      setAvailableJobs(jobs)
      setSearchedJobs(jobs)
    } catch (err) {
      console.error('Error loading jobs:', err)
      setAvailableJobs([])
      setSearchedJobs([])
    } finally {
      setIsSearchingJobs(false)
    }
  }

  // Search jobs by title
  const searchJobs = async (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setSearchedJobs(availableJobs)
      return
    }

    // Check if user is authenticated
    if (!user || !token) {
      console.error('User not authenticated, cannot search jobs')
      return
    }

    try {
      setIsSearchingJobs(true)
      const url = '/jobs?' + new URLSearchParams({
        search: searchTerm,
        status: 'open',
        limit: '20'
      }).toString()
      
      console.log('Searching jobs with term:', searchTerm, 'URL:', url)
      const response = await api.get(url)
      console.log('Search results:', response)
      
      // Handle direct API response format
      const jobs = response.jobs || []
      console.log('Search found jobs:', jobs.length)
      setSearchedJobs(jobs)
    } catch (err) {
      console.error('Error searching jobs:', err)
      // Fallback to local search
      const filtered = availableJobs.filter(job => 
        job.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.companyClient?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.location?.toLowerCase().includes(searchTerm.toLowerCase())
      )
      setSearchedJobs(filtered)
    } finally {
      setIsSearchingJobs(false)
    }
  }

  // Handle contact candidate success callback
  const handleContactSuccess = () => {
    setShowContactModal(false)
    fetchCandidateDetail() // Refresh to show new communication records
  }

  // Handle recommend jobs
  const handleRecommendJobs = async () => {
    try {
      if (selectedJobIds.length === 0) {
        setError('请至少选择一个职位')
        return
      }

      // Submit candidate to selected jobs
      const submissionPromises = selectedJobIds.map(async (jobId) => {
        try {
          const selectedJob = searchedJobs.find(job => job.id === jobId)
          
          // Submit candidate to job
          const submitData: any = {
            jobId: jobId,
            submitReason: recommendMessage || `通过候选人推荐功能投递`,
            matchExplanation: `候选人推荐 - ${selectedJob?.title}`,
            notes: recommendMessage || `通过候选人推荐功能投递`
          }
          // Only include optional fields if they have non-empty values
          if (recommendMessage?.trim()) {
            submitData.customResume = recommendMessage.trim()
          }
          
          await api.post(`/candidates/${candidateId}/submit`, submitData)

          // Add application record for the candidate
          const applicationData = {
            jobTitle: selectedJob?.title || '未知职位',
            companyName: selectedJob?.companyClient?.name || selectedJob?.company || '未知公司',
            status: 'submitted',
            notes: `推荐投递 - ${recommendMessage || '无备注'}`,
            jobId: jobId
          }
          await api.post(`/candidates/${candidateId}/applications`, applicationData)

          return { success: true, jobId, jobTitle: selectedJob?.title }
        } catch (error) {
          // Handle conflict error (already submitted) as success
          if (error.response?.status === 409) {
            return { success: true, jobId, jobTitle: searchedJobs.find(job => job.id === jobId)?.title, alreadySubmitted: true }
          }
          console.error(`Failed to submit to job ${jobId}:`, error)
          return { success: false, jobId, error: error.message || error.toString() }
        }
      })

      const results = await Promise.all(submissionPromises)
      const successCount = results.filter(r => r.success).length
      const failureCount = results.filter(r => !r.success).length

      if (successCount > 0) {
        // Add communication record
        const successfulJobs = results.filter(r => r.success).map(r => r.jobTitle).join(', ')
        await api.post(`/candidates/${candidateId}/communications`, {
          communicationType: 'email',
          content: `成功推荐并投递到 ${successCount} 个职位: ${successfulJobs}。${recommendMessage ? `推荐说明: ${recommendMessage}` : ''}`,
          notes: `推荐职位操作 - 成功: ${successCount}, 失败: ${failureCount}`
        })
      }

      if (failureCount > 0) {
        setError(`部分职位投递失败: ${failureCount}个失败, ${successCount}个成功`)
      } else {
        // Show success message briefly
        const tempError = error
        setError(`成功投递到 ${successCount} 个职位！`)
        setTimeout(() => setError(tempError), 3000)
      }
      
      setShowRecommendModal(false)
      setSelectedJobIds([])
      setRecommendMessage('')
      setJobSearchTerm('')
      fetchCandidateDetail()
    } catch (err) {
      console.error('推荐职位失败:', err)
      setError(`推荐职位失败: ${err.message || '未知错误'}`)
    }
  }

  // Handle edit candidate - Replaced by CandidateEditModal
  // const handleEditCandidate = async () => {
  //   try {
  //     await api.patch(`/candidates/${candidateId}`, editForm)
  //     setShowEditModal(false)
  //     setEditForm({})
  //     fetchCandidateDetail()
  //   } catch (err) {
  //     setError('更新候选人信息失败')
  //   }
  // }

  // Handle add application
  const handleAddApplication = async () => {
    try {
      await api.post(`/candidates/${candidateId}/applications`, newApplication)
      setShowAddApplicationModal(false)
      setNewApplication({
        jobTitle: '',
        companyName: '',
        status: 'submitted',
        notes: ''
      })
      fetchCandidateDetail()
    } catch (err) {
      setError('添加应聘记录失败')
    }
  }

  // Show new enhanced edit modal
  const showEditCandidateModal = () => {
    setShowEditModal(true)
  }

  if (loading) return <div className="p-6">Loading candidate details...</div>

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <button onClick={onBack} className="text-blue-600 hover:text-blue-800">
          ← Back to candidates
        </button>
      </div>
    )
  }

  if (!candidate) return <div className="p-6">Candidate not found</div>

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'interviewing': return 'bg-yellow-100 text-yellow-800'
      case 'hired': return 'bg-blue-100 text-blue-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      default: return 'bg-green-100 text-green-800'
    }
  }

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'active': return '可联系'
      case 'interviewing': return '面试中'
      case 'hired': return '已入职'
      case 'inactive': return '暂不联系'
      default: return '可联系'
    }
  }

  const getSkillLevelColor = (level: string) => {
    switch (level) {
      case 'expert': return 'bg-purple-100 text-purple-800'
      case 'advanced': return 'bg-blue-100 text-blue-800'
      case 'intermediate': return 'bg-green-100 text-green-800'
      case 'beginner': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="text-gray-600 hover:text-gray-800 transition-colors"
            >
              ← 返回候选人列表
            </button>
          </div>
          <div className="flex space-x-2">
            <button 
              onClick={() => setShowContactModal(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              📞 联系候选人
            </button>
            <button 
              onClick={() => {
                console.log('Opening recommend modal...')
                if (!user || !token) {
                  console.error('User not authenticated, cannot open recommend modal')
                  alert('请先登录再进行推荐操作')
                  return
                }
                setShowRecommendModal(true)
                setTimeout(() => {
                  console.log('Loading available jobs...')
                  loadAvailableJobs()
                }, 100)
              }}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              disabled={authLoading || !user}
            >
              📧 推荐职位
            </button>
            <button 
              onClick={showEditCandidateModal}
              className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
            >
              ✏️ 编辑信息
            </button>
          </div>
        </div>
      </div>

      {/* Candidate Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-start space-x-6">
          <div className="flex-shrink-0">
            <div className="h-24 w-24 rounded-full bg-orange-100 flex items-center justify-center">
              <span className="text-orange-600 font-medium text-2xl">
                {candidate.name?.charAt(0) || '?'}
              </span>
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-4 mb-3">
              <h1 className="text-3xl font-bold text-gray-900">{candidate.name}</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(candidate.status)}`}>
                {getStatusText(candidate.status)}
              </span>
              {candidate.rating && (
                <div className="flex items-center">
                  <span className="text-yellow-400">{'★'.repeat(candidate.rating)}</span>
                  <span className="text-gray-300">{'★'.repeat(5 - candidate.rating)}</span>
                </div>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
              <div>
                <span className="text-gray-500">邮箱:</span>
                <p className="font-medium">{candidate.email || 'N/A'}</p>
              </div>
              <div>
                <span className="text-gray-500">电话:</span>
                <p className="font-medium">{candidate.phone}</p>
              </div>
              <div>
                <span className="text-gray-500">地址:</span>
                <p className="font-medium">{candidate.location || '北京'}</p>
              </div>
              <div>
                <span className="text-gray-500">工作经验:</span>
                <p className="font-medium">{candidate.experience || '5年以上'}</p>
              </div>
              <div>
                <span className="text-gray-500">当前职位:</span>
                <p className="font-medium">{candidate.currentPosition || 'N/A'}</p>
              </div>
              <div>
                <span className="text-gray-500">期望薪资:</span>
                <p className="font-medium">{candidate.expectedSalary || 'N/A'}</p>
              </div>
              <div>
                <span className="text-gray-500">维护人:</span>
                <p className="font-medium">{candidate.maintainer.username}</p>
              </div>
              <div>
                <span className="text-gray-500">添加时间:</span>
                <p className="font-medium">{new Date(candidate.createdAt).toLocaleDateString('zh-CN')}</p>
              </div>
            </div>
            {candidate.tags && candidate.tags.length > 0 && (
              <div className="mt-4">
                <span className="text-gray-500 text-sm">技能标签:</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {candidate.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            {[
              { id: 'overview', label: '基本信息', icon: '👤' },
              { id: 'resume', label: '简历文件', icon: '📄' },
              { id: 'applications', label: '应聘记录', icon: '📝' },
              { id: 'notes', label: '沟通记录', icon: '💬' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-6 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Personal Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">个人信息</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-gray-500 text-sm">年龄</span>
                    <p className="font-medium">{candidate.personalInfo?.age || '28'} 岁</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-gray-500 text-sm">性别</span>
                    <p className="font-medium">{candidate.personalInfo?.gender || '男'}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-gray-500 text-sm">婚姻状况</span>
                    <p className="font-medium">{candidate.personalInfo?.maritalStatus || '已婚'}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-gray-500 text-sm">工作许可</span>
                    <p className="font-medium">{candidate.personalInfo?.workPermit || '有效'}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-gray-500 text-sm">国籍</span>
                    <p className="font-medium">{candidate.personalInfo?.nationality || '中国'}</p>
                  </div>
                </div>
              </div>

              {/* Work Experience */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">工作经历</h3>
                <div className="space-y-4">
                  {candidate.workHistory && candidate.workHistory.length > 0 ? (
                    candidate.workHistory.map((work, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-semibold text-gray-900">{work.position}</h4>
                            <p className="text-gray-600">{work.company} • {work.industry}</p>
                          </div>
                          <span className="text-sm text-gray-500">
                            {work.startDate} - {work.endDate || '至今'}
                          </span>
                        </div>
                        <p className="text-gray-700 mb-3">{work.description}</p>
                        {work.achievements && work.achievements.length > 0 && (
                          <div>
                            <span className="text-sm font-medium text-gray-700">主要成就:</span>
                            <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                              {work.achievements.map((achievement, idx) => (
                                <li key={idx}>{achievement}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900">高级软件工程师</h4>
                      <p className="text-gray-600">阿里巴巴集团 • 互联网/电子商务</p>
                      <span className="text-sm text-gray-500">2020-03 - 至今</span>
                      <p className="text-gray-700 mt-2">负责核心业务系统的架构设计和开发，领导技术团队完成多个重要项目。</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Education */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">教育背景</h3>
                <div className="space-y-4">
                  {candidate.educationHistory && candidate.educationHistory.length > 0 ? (
                    candidate.educationHistory.map((edu, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-gray-900">{edu.school}</h4>
                            <p className="text-gray-600">{edu.degree} • {edu.major}</p>
                            {edu.gpa && <p className="text-gray-500 text-sm">GPA: {edu.gpa}</p>}
                          </div>
                          <span className="text-sm text-gray-500">
                            {edu.startDate} - {edu.endDate}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900">清华大学</h4>
                      <p className="text-gray-600">硕士 • 计算机科学与技术</p>
                      <span className="text-sm text-gray-500">2016-09 - 2019-06</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Project Experience */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">项目经历</h3>
                <div className="space-y-4">
                  {candidate.projectExperience && candidate.projectExperience.length > 0 ? (
                    candidate.projectExperience.map((project, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="text-lg font-semibold text-gray-900">{project.projectName}</h4>
                            <p className="text-gray-600 text-sm">{project.role}</p>
                          </div>
                          <span className="text-sm text-gray-500">
                            {project.startDate} - {project.endDate || 'Now'}
                          </span>
                        </div>
                        
                        <div className="mb-3">
                          <p className="text-gray-700">{project.description}</p>
                        </div>

                        {project.responsibilities && project.responsibilities.length > 0 && (
                          <div className="mb-3">
                            <h5 className="text-sm font-medium text-gray-700 mb-2">职责描述:</h5>
                            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                              {project.responsibilities.map((responsibility, idx) => (
                                <li key={idx}>{responsibility}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {project.technologies && project.technologies.length > 0 && (
                          <div className="mb-3">
                            <h5 className="text-sm font-medium text-gray-700 mb-2">技术栈:</h5>
                            <div className="flex flex-wrap gap-1">
                              {project.technologies.map((tech, idx) => (
                                <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                  {tech}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {project.achievements && project.achievements.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-2">项目成果:</h5>
                            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                              {project.achievements.map((achievement, idx) => (
                                <li key={idx}>{achievement}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-gray-900">美团点评-平台公信力风险审核平台</h4>
                      <p className="text-gray-600 text-sm">项目负责人</p>
                      <span className="text-sm text-gray-500">2025年03月 - Now</span>
                      <div className="mt-3">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">职责描述:</h5>
                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                          <li>团队搭建:围绕新组织设计,0-1 组建风险审核平台,扩展审核类型及范围。</li>
                          <li>策略反哺:调整人审定位,重新设计指标,通过人审核验机审和策略能力,为公信力风险审核能力指标负责。</li>
                          <li>审核策略重构:引入AI 大模型,通过半一反三的策略辅助分析能力提升机审占比,并通过AI 辅助,提升审核效率。</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Skills */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">专业技能</h3>
                <div className="space-y-4">
                  {candidate.skills && candidate.skills.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {candidate.skills.map((skill, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-gray-900">{skill.name}</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getSkillLevelColor(skill.level)}`}>
                              {skill.level}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600">
                            <p>经验: {skill.yearsOfExperience} 年</p>
                            <p>类别: {skill.category}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {['JavaScript', 'React', 'Node.js', 'Python', 'AWS', 'Docker'].map((skill) => (
                        <div key={skill} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-gray-900">{skill}</span>
                            <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              高级
                            </span>
                          </div>
                          <div className="text-sm text-gray-600">
                            <p>经验: 5+ 年</p>
                            <p>类别: 技术</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Languages */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">语言能力</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {candidate.languages && candidate.languages.length > 0 ? (
                    candidate.languages.map((lang, index) => (
                      <div key={index} className="bg-gray-50 p-4 rounded-lg">
                        <span className="font-medium text-gray-900">{lang.language}</span>
                        <p className="text-sm text-gray-600">{lang.proficiency}</p>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <span className="font-medium text-gray-900">中文</span>
                        <p className="text-sm text-gray-600">母语</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <span className="font-medium text-gray-900">英语</span>
                        <p className="text-sm text-gray-600">流利</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Resume Tab */}
          {activeTab === 'resume' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">简历文件管理</h3>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                  📤 上传新简历
                </button>
              </div>
              <div className="space-y-3">
                {candidate.resumes && candidate.resumes.length > 0 ? (
                  candidate.resumes.map((resume) => (
                    <div key={resume.id} className="border border-gray-200 rounded-lg p-4 flex justify-between items-center">
                      <div className="flex items-center space-x-3">
                        <div className="text-blue-600">📄</div>
                        <div>
                          <p className="font-medium text-gray-900">{resume.filename}</p>
                          <p className="text-sm text-gray-500">
                            {resume.fileSize} • 上传于 {new Date(resume.uploadDate).toLocaleDateString('zh-CN')}
                          </p>
                        </div>
                        {resume.isActive && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            当前使用
                          </span>
                        )}
                      </div>
                      <div className="flex space-x-2">
                        <button className="text-blue-600 hover:text-blue-800">预览</button>
                        <button className="text-green-600 hover:text-green-800">下载</button>
                        <button className="text-red-600 hover:text-red-800">删除</button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="border border-gray-200 rounded-lg p-4 flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <div className="text-blue-600">📄</div>
                      <div>
                        <p className="font-medium text-gray-900">张三_高级软件工程师_简历.pdf</p>
                        <p className="text-sm text-gray-500">
                          2.1 MB • 上传于 2024-01-15
                        </p>
                      </div>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        当前使用
                      </span>
                    </div>
                    <div className="flex space-x-2">
                      <button className="text-blue-600 hover:text-blue-800">预览</button>
                      <button className="text-green-600 hover:text-green-800">下载</button>
                      <button className="text-red-600 hover:text-red-800">删除</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Applications Tab */}
          {activeTab === 'applications' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">应聘记录</h3>
                <button 
                  onClick={() => setShowAddApplicationModal(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  ➕ 添加应聘记录
                </button>
              </div>
              <div className="space-y-3">
                {candidate.applications && candidate.applications.length > 0 ? (
                  candidate.applications.map((app) => (
                    <div key={app.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-semibold text-gray-900">{app.jobTitle}</h4>
                          <p className="text-gray-600">{app.companyName}</p>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          app.status === 'offer' ? 'bg-green-100 text-green-800' :
                          app.status === 'interview' ? 'bg-yellow-100 text-yellow-800' :
                          app.status === 'reviewing' ? 'bg-blue-100 text-blue-800' :
                          app.status === 'rejected' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {app.status === 'offer' ? 'Offer' :
                           app.status === 'interview' ? '面试中' :
                           app.status === 'reviewing' ? '审核中' :
                           app.status === 'rejected' ? '被拒绝' : '已投递'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">投递时间: {new Date(app.appliedDate).toLocaleDateString('zh-CN')}</p>
                      {app.notes && <p className="text-sm text-gray-700 mt-2">{app.notes}</p>}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-lg mb-2">📝</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">暂无应聘记录</h3>
                    <p className="text-gray-500">还没有为该候选人添加任何应聘记录</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Notes Tab */}
          {activeTab === 'notes' && (
            <CommunicationRecordsList 
              candidateId={candidateId} 
              onRefresh={fetchCandidateDetail}
            />
          )}
        </div>
      </div>

      {/* Add Note Modal */}
      {showAddNote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-lg w-full">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">添加沟通记录</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">类型</label>
                  <select
                    value={newNote.type}
                    onChange={(e) => setNewNote({...newNote, type: e.target.value as any})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="call">电话沟通</option>
                    <option value="email">邮件沟通</option>
                    <option value="interview">面试记录</option>
                    <option value="meeting">会议记录</option>
                    <option value="other">其他</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">内容</label>
                  <textarea
                    value={newNote.content}
                    onChange={(e) => setNewNote({...newNote, content: e.target.value})}
                    placeholder="请输入沟通内容..."
                    rows={4}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-4 mt-6">
                <button
                  onClick={() => setShowAddNote(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={addNote}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  添加记录
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Contact Candidate Modal */}
      <ContactCandidateModal
        isOpen={showContactModal}
        onClose={() => setShowContactModal(false)}
        candidate={candidate}
        onContactSuccess={handleContactSuccess}
      />

      {/* Recommend Jobs Modal */}
      {showRecommendModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">推荐职位</h2>
              <div className="space-y-4">
                {/* Job Search */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">搜索职位</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={jobSearchTerm}
                      onChange={(e) => {
                        const value = e.target.value
                        setJobSearchTerm(value)
                        
                        // Clear previous timeout
                        if (searchTimeout) {
                          clearTimeout(searchTimeout)
                        }
                        
                        // Set new timeout for debounced search
                        const newTimeout = setTimeout(() => {
                          searchJobs(value)
                        }, 300)
                        setSearchTimeout(newTimeout)
                      }}
                      placeholder="输入职位名称、公司名称或地点进行搜索..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-10"
                    />
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                      {isSearchingJobs ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      ) : (
                        <span className="text-gray-400">🔍</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Job Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    选择职位 {searchedJobs.length > 0 && `(${searchedJobs.length} 个可选)`}
                  </label>
                  <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-lg">
                    {searchedJobs.length > 0 ? (
                      searchedJobs.map((job) => (
                        <div key={job.id} className="p-2 border-b border-gray-200 last:border-b-0 hover:bg-gray-50">
                          <label className="flex items-center space-x-3 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={selectedJobIds.includes(job.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedJobIds([...selectedJobIds, job.id])
                                } else {
                                  setSelectedJobIds(selectedJobIds.filter(id => id !== job.id))
                                }
                              }}
                              className="flex-shrink-0"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium text-gray-900 truncate">{job.title}</h4>
                                <div className="flex items-center space-x-2 ml-2">
                                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                    job.status === 'open' ? 'bg-green-100 text-green-800' :
                                    'bg-gray-100 text-gray-800'
                                  }`}>
                                    {job.status === 'open' ? '开放中' : '待定'}
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center justify-between mt-1 text-sm text-gray-600">
                                <span className="truncate">
                                  {job.companyClient?.name || job.company || '未知公司'} • {job.location || '地点待定'}
                                </span>
                                <span className="ml-2 flex-shrink-0 text-gray-700 font-medium">
                                  {job.salaryMin && job.salaryMax 
                                    ? `${(job.salaryMin/10000).toFixed(0)}-${(job.salaryMax/10000).toFixed(0)}万/年` 
                                    : job.salaryRange 
                                      ? `${(job.salaryRange.min/10000).toFixed(0)}-${(job.salaryRange.max/10000).toFixed(0)}万/年`
                                      : '薪资面议'
                                  }
                                </span>
                              </div>
                            </div>
                          </label>
                        </div>
                      ))
                    ) : isSearchingJobs ? (
                      <div className="p-8 text-center text-gray-500">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        正在搜索职位...
                      </div>
                    ) : (
                      <div className="p-8 text-center text-gray-500">
                        <div className="text-4xl mb-2">🔍</div>
                        {jobSearchTerm ? '未找到匹配的职位' : '请输入关键词搜索职位'}
                      </div>
                    )}
                  </div>
                </div>

                {/* Recommendation Message */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">推荐说明</label>
                  <textarea
                    value={recommendMessage}
                    onChange={(e) => setRecommendMessage(e.target.value)}
                    placeholder="请输入推荐理由和说明..."
                    rows={4}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-4 mt-6">
                <button
                  onClick={() => {
                    setShowRecommendModal(false)
                    setSelectedJobIds([])
                    setRecommendMessage('')
                    setJobSearchTerm('')
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleRecommendJobs}
                  disabled={selectedJobIds.length === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title={selectedJobIds.length === 0 ? '请至少选择一个职位' : ''}
                >
                  推荐职位 ({selectedJobIds.length})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Candidate Edit Modal */}
      <CandidateEditModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        candidateId={candidateId}
        onCandidateUpdated={() => {
          setShowEditModal(false)
          fetchCandidateDetail()
        }}
      />

      {/* Add Application Modal */}
      {showAddApplicationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-lg w-full">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">添加应聘记录</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">职位名称</label>
                  <input
                    type="text"
                    value={newApplication.jobTitle}
                    onChange={(e) => setNewApplication({...newApplication, jobTitle: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">公司名称</label>
                  <input
                    type="text"
                    value={newApplication.companyName}
                    onChange={(e) => setNewApplication({...newApplication, companyName: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                  <select
                    value={newApplication.status}
                    onChange={(e) => setNewApplication({...newApplication, status: e.target.value as any})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="submitted">已投递</option>
                    <option value="reviewing">审核中</option>
                    <option value="interview">面试中</option>
                    <option value="offer">已获得Offer</option>
                    <option value="rejected">被拒绝</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
                  <textarea
                    value={newApplication.notes}
                    onChange={(e) => setNewApplication({...newApplication, notes: e.target.value})}
                    placeholder="请输入备注信息..."
                    rows={3}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-4 mt-6">
                <button
                  onClick={() => setShowAddApplicationModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleAddApplication}
                  disabled={!newApplication.jobTitle.trim() || !newApplication.companyName.trim()}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  添加记录
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}