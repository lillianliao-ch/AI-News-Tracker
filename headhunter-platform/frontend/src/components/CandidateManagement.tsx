'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import CandidateDetail from './CandidateDetail'
import QuickCandidateCreateModal from './QuickCandidateCreateModal'
import CandidateEditModal from './CandidateEditModal'

interface Candidate {
  id: string
  name: string
  phone: string
  email?: string
  tags: string[]
  maintainer: {
    username: string
    company?: {
      name: string
    }
  }
  createdAt: string
  _count: {
    candidateSubmissions: number
  }
  // 扩展字段
  location?: string
  experience?: string
  education?: string
  currentPosition?: string
  expectedSalary?: string
  status?: 'active' | 'inactive' | 'hired' | 'interviewing'
  avatar?: string
  lastContact?: string
  rating?: number
}

interface CreateCandidateData {
  name: string
  phone: string
  email?: string
  tags: string[]
}

interface MatchingResult {
  candidateId: string
  score: number
  matchingFactors: string[]
  candidate: {
    id: string
    name: string
    email?: string
    phone: string
    tags: string[]
    maintainer: {
      username: string
      company?: {
        name: string
      }
    }
  }
}

export default function CandidateManagement() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showMatchingForm, setShowMatchingForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [editingCandidateId, setEditingCandidateId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchResults, setSearchResults] = useState<MatchingResult[]>([])
  const [jobMatchingResults, setJobMatchingResults] = useState<any[]>([])
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [showDetailView, setShowDetailView] = useState(false)

  const [filters, setFilters] = useState({
    search: '',
    tags: '',
    maintainerId: ''
  })
  
  // 搜索表单状态 - 用于存储用户输入但还未提交的搜索条件
  const [searchForm, setSearchForm] = useState({
    search: '',
    tags: '',
    maintainerId: ''
  })

  const [newCandidate, setNewCandidate] = useState<CreateCandidateData>({
    name: '',
    phone: '',
    email: '',
    tags: []
  })

  const [newTag, setNewTag] = useState('')

  const fetchCandidates = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10',
        ...Object.fromEntries(Object.entries(filters).filter(([_, value]) => value))
      })
      
      const response = await api.get(`/candidates?${params}`)
      setCandidates(response.candidates)
      setTotalPages(response.pagination.pages)
    } catch (err) {
      setError('Failed to fetch candidates')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const createCandidate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/candidates', newCandidate)
      setShowCreateForm(false)
      setNewCandidate({
        name: '',
        phone: '',
        email: '',
        tags: []
      })
      fetchCandidates()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create candidate')
    }
  }

  const handleCandidateCreated = (candidate: any) => {
    fetchCandidates() // 重新获取候选人列表
    setShowCreateForm(false) // 关闭模态框
  }

  const handleEditCandidate = (candidateId: string) => {
    setEditingCandidateId(candidateId)
    setShowEditForm(true)
  }

  const handleCandidateUpdated = (candidate: any) => {
    fetchCandidates() // 重新获取候选人列表
    setShowEditForm(false) // 关闭模态框
    setEditingCandidateId(null)
  }

  // 处理搜索提交
  const handleSearch = () => {
    setFilters(searchForm) // 将搜索表单的值设置为过滤条件
    setPage(1) // 重置到第一页
  }

  // 处理清空搜索条件
  const handleClearSearch = () => {
    const emptyForm = { search: '', tags: '', maintainerId: '' }
    setSearchForm(emptyForm)
    setFilters(emptyForm)
    setPage(1)
  }

  const searchCandidates = async () => {
    try {
      const searchData = {
        keywords: filters.search ? [filters.search] : [],
        tags: filters.tags ? [filters.tags] : [],
        page: 1,
        limit: 20
      }
      
      const response = await api.post('/candidates/search', searchData)
      setSearchResults(response.candidates)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to search candidates')
    }
  }

  const findCandidatesForJob = async (jobId: string) => {
    try {
      const response = await api.get(`/candidates/match-for-job/${jobId}`)
      setJobMatchingResults(response.matches)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to find matching candidates')
    }
  }

  const submitCandidateToJob = async (candidateId: string, jobId: string, notes?: string) => {
    try {
      await api.post(`/candidates/${candidateId}/submit`, {
        jobId,
        notes,
        submitReason: 'Good match based on skills and experience'
      })
      alert('Candidate submitted successfully!')
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to submit candidate')
    }
  }

  const addTag = () => {
    if (newTag && !newCandidate.tags.includes(newTag)) {
      setNewCandidate({
        ...newCandidate,
        tags: [...newCandidate.tags, newTag]
      })
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setNewCandidate({
      ...newCandidate,
      tags: newCandidate.tags.filter(tag => tag !== tagToRemove)
    })
  }

  const handleViewCandidate = (candidateId: string) => {
    setSelectedCandidateId(candidateId)
    setShowDetailView(true)
  }

  const handleBackToList = () => {
    setShowDetailView(false)
    setSelectedCandidateId(null)
    fetchCandidates() // Refresh the list
  }

  useEffect(() => {
    fetchCandidates()
  }, [page, filters])

  if (loading) return <div className="p-6">Loading candidates...</div>

  // Show candidate detail view
  if (showDetailView && selectedCandidateId) {
    return (
      <CandidateDetail
        candidateId={selectedCandidateId}
        onBack={handleBackToList}
      />
    )
  }

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">简历库</h1>
          <p className="text-gray-600 mt-1">管理候选人信息和简历档案</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors flex items-center space-x-2"
          >
            <span>➕</span>
            <span>新增简历</span>
          </button>
          <button
            onClick={() => setShowMatchingForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <span>🔍</span>
            <span>智能匹配</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Enhanced Filters */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">搜索和筛选</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">姓名</label>
            <input
              type="text"
              placeholder="请输入候选人姓名"
              value={searchForm.search}
              onChange={(e) => setSearchForm({...searchForm, search: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">技能标签</label>
            <input
              type="text"
              placeholder="请选择技能"
              value={searchForm.tags}
              onChange={(e) => setSearchForm({...searchForm, tags: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">工作年限</label>
            <select className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
              <option value="">请选择</option>
              <option value="1-3">1-3年</option>
              <option value="3-5">3-5年</option>
              <option value="5-10">5-10年</option>
              <option value="10+">10年以上</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
            <select className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
              <option value="">全部状态</option>
              <option value="active">可联系</option>
              <option value="interviewing">面试中</option>
              <option value="hired">已入职</option>
              <option value="inactive">暂不联系</option>
            </select>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <button
            onClick={handleSearch}
            className="bg-orange-500 text-white px-6 py-2 rounded-lg hover:bg-orange-600 transition-colors"
          >
            查询
          </button>
          <button
            onClick={handleClearSearch}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            清空搜索条件
          </button>
        </div>
      </div>

      {/* Enhanced Candidates Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {/* Table Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">候选人列表</h3>
            <span className="text-sm text-gray-500">共 {candidates.length} 位候选人</span>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">候选人</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">投递职位</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">更新人</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">更新时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {candidates.map((candidate) => (
                <tr key={candidate.id} className="hover:bg-gray-50 transition-colors cursor-pointer">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-12 w-12">
                        <div className="h-12 w-12 rounded-full bg-orange-100 flex items-center justify-center">
                          <span className="text-orange-600 font-medium text-lg">
                            {candidate.name?.charAt(0) || '?'}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div 
                          className="text-sm font-medium text-gray-900 hover:text-blue-600 cursor-pointer"
                          onClick={() => handleViewCandidate(candidate.id)}
                        >
                          {candidate.name}
                        </div>
                        <div className="text-sm text-gray-500 space-y-1">
                          <div className="flex items-center space-x-4">
                            <span>📧 {candidate.email || 'N/A'}</span>
                            <span>📱 {candidate.phone}</span>
                          </div>
                          <div className="flex items-center space-x-4">
                            <span>📍 {candidate.location || '北京'}</span>
                            <span>💼 {candidate.experience || '5年以上'}</span>
                            <span>🎓 {candidate.education || '本科'}</span>
                          </div>
                          {candidate.tags && candidate.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {candidate.tags.slice(0, 3).map((tag, index) => (
                                <span
                                  key={index}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                                >
                                  {tag}
                                </span>
                              ))}
                              {candidate.tags.length > 3 && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                                  +{candidate.tags.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {candidate.currentPosition || '高德-风险治理策略-资深运营专家'}
                    </div>
                    <div className="text-sm text-gray-500">
                      状态: 
                      <span className={`ml-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        candidate.status === 'active' ? 'bg-green-100 text-green-800' :
                        candidate.status === 'interviewing' ? 'bg-yellow-100 text-yellow-800' :
                        candidate.status === 'hired' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {candidate.status === 'active' ? '可联系' :
                         candidate.status === 'interviewing' ? '面试中' :
                         candidate.status === 'hired' ? '已入职' : '可联系'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {candidate.maintainer.username}
                    {candidate.maintainer.company && (
                      <div className="text-xs text-gray-400">{candidate.maintainer.company.name}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>{new Date(candidate.createdAt).toLocaleDateString('zh-CN')}</div>
                    <div className="text-xs text-gray-400">
                      {new Date(candidate.createdAt).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const jobId = prompt('输入职位ID推荐候选人:')
                          if (jobId) submitCandidateToJob(candidate.id, jobId)
                        }}
                        className="text-green-600 hover:text-green-900 transition-colors"
                        title="推荐职位"
                      >
                        📧
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditCandidate(candidate.id);
                        }}
                        className="text-gray-600 hover:text-gray-900 transition-colors"
                        title="编辑"
                      >
                        ✏️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {candidates.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-2">📋</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无候选人数据</h3>
            <p className="text-gray-500 mb-4">还没有添加任何候选人，点击上方按钮开始添加</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              添加第一个候选人
            </button>
          </div>
        )}
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

      {/* Enhanced Candidate Create Modal */}
      <QuickCandidateCreateModal
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onCandidateCreated={handleCandidateCreated}
      />

      {/* Enhanced Candidate Edit Modal */}
      <CandidateEditModal
        isOpen={showEditForm}
        onClose={() => {
          setShowEditForm(false)
          setEditingCandidateId(null)
        }}
        candidateId={editingCandidateId}
        onCandidateUpdated={handleCandidateUpdated}
      />

      {/* Search & Matching Modal */}
      {showMatchingForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">Search & Match Candidates</h2>
              
              <div className="flex space-x-4 mb-6">
                <button
                  onClick={searchCandidates}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Search Candidates
                </button>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Job ID for matching"
                    className="border border-gray-300 rounded-lg px-3 py-2"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        findCandidatesForJob((e.target as HTMLInputElement).value)
                      }
                    }}
                  />
                  <button
                    onClick={() => {
                      const input = document.querySelector('input[placeholder="Job ID for matching"]') as HTMLInputElement
                      if (input?.value) findCandidatesForJob(input.value)
                    }}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                  >
                    Find Matches
                  </button>
                </div>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">Search Results</h3>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {searchResults.map((result) => (
                      <div key={result.candidateId} className="border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium">{result.candidate.name}</p>
                            <p className="text-sm text-gray-600">{result.candidate.phone}</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {result.candidate.tags.map((tag, i) => (
                                <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-500">Score: {result.score.toFixed(1)}</p>
                            <p className="text-xs text-gray-400">{result.matchingFactors.join(', ')}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Job Matching Results */}
              {jobMatchingResults.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">Job Matching Results</h3>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {jobMatchingResults.map((result) => (
                      <div key={result.candidateId} className="border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium">{result.candidate.name}</p>
                            <p className="text-sm text-gray-600">{result.candidate.phone}</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {result.candidate.tags.map((tag: string, i: number) => (
                                <span key={i} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-500">Score: {result.score.toFixed(1)}</p>
                            <p className="text-xs text-gray-400">{result.matchingFactors.join(', ')}</p>
                            <button
                              onClick={() => {
                                const jobId = prompt('Confirm job ID:')
                                if (jobId) submitCandidateToJob(result.candidateId, jobId, 'Auto-matched candidate')
                              }}
                              className="mt-1 bg-green-600 text-white px-2 py-1 rounded text-xs hover:bg-green-700"
                            >
                              Submit
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end">
                <button
                  onClick={() => {
                    setShowMatchingForm(false)
                    setSearchResults([])
                    setJobMatchingResults([])
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}