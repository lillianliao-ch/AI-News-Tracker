import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface Candidate {
  id: string
  name: string
  phone: string
  email?: string
  tags: string[]
  createdAt: string
}

interface CandidateSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectCandidate: (candidate: Candidate) => void
  onCreateNew: () => void
  jobTitle?: string
  jobId?: string
}

export default function CandidateSelectionModal({
  isOpen,
  onClose,
  onSelectCandidate,
  onCreateNew,
  jobTitle,
  jobId
}: CandidateSelectionModalProps) {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [submittedCandidates, setSubmittedCandidates] = useState<Set<string>>(new Set())
  const pageSize = 10

  const fetchCandidates = async (page: number = 1, search: string = '') => {
    try {
      setLoading(true)
      const response = await api.getCandidates({
        page,
        limit: pageSize,
        search: search || undefined
      })
      setCandidates(response.candidates || [])
      setTotalPages(Math.ceil((response.pagination?.total || 0) / pageSize))
      setCurrentPage(page)
    } catch (err: any) {
      setError('获取候选人列表失败')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchSubmittedCandidates = async () => {
    if (!jobId) return
    
    try {
      // 获取该职位的所有投递记录
      const response = await api.get(`/candidates/submissions/job/${jobId}`)
      const submittedIds = new Set(response.submissions?.map((sub: any) => sub.candidateId) || [])
      setSubmittedCandidates(submittedIds)
    } catch (err: any) {
      console.error('获取已投递候选人失败:', err)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchCandidates(1, searchTerm)
      fetchSubmittedCandidates()
    }
  }, [isOpen, jobId])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchCandidates(1, searchTerm)
  }

  const handleCandidateClick = (candidate: Candidate) => {
    if (submittedCandidates.has(candidate.id)) {
      const confirmed = confirm(`候选人 ${candidate.name} 已经投递过此职位，确定要重复投递吗？`)
      if (!confirmed) return
    }
    onSelectCandidate(candidate)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-orange-500 text-white px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-medium">投递简历</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {/* Job Info */}
          {jobTitle && (
            <div className="mb-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">投递职位：</p>
              <p className="font-medium text-gray-900">{jobTitle}</p>
            </div>
          )}

          {/* Candidate Selection */}
          <div className="mb-6">
            <div className="flex items-center mb-4">
              <span className="text-red-500 mr-1">*</span>
              <label className="text-sm font-medium text-gray-700">候选人</label>
              <select className="ml-4 px-3 py-1 border border-gray-300 rounded text-sm">
                <option>请选择</option>
              </select>
            </div>

            {/* Search */}
            <form onSubmit={handleSearch} className="mb-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="搜索候选人姓名、电话或邮箱..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  搜索
                </button>
              </div>
            </form>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-500">加载中...</p>
              </div>
            )}

            {/* Candidates List */}
            {!loading && (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                {candidates.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    暂无候选人数据
                  </div>
                ) : (
                  <>
                    <div className="max-h-96 overflow-y-auto">
                      {candidates.map((candidate) => {
                        const isSubmitted = submittedCandidates.has(candidate.id)
                        return (
                          <div
                            key={candidate.id}
                            className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer flex items-center justify-between ${
                              isSubmitted ? 'bg-yellow-50 border-yellow-200' : ''
                            }`}
                            onClick={() => handleCandidateClick(candidate)}
                          >
                            <div className="flex items-center space-x-4">
                              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                <span className="text-blue-600 font-medium">
                                  {candidate.name.charAt(0)}
                                </span>
                              </div>
                              <div>
                                <h4 className="font-medium text-gray-900">{candidate.name}</h4>
                                <div className="text-sm text-gray-600">
                                  <p>电话: {candidate.phone}</p>
                                  {candidate.email && <p>邮箱: {candidate.email}</p>}
                                </div>
                                {candidate.tags.length > 0 && (
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {candidate.tags.map((tag, index) => (
                                      <span
                                        key={index}
                                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                                      >
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-gray-500">
                              <div>添加时间: {new Date(candidate.createdAt).toLocaleDateString('zh-CN')}</div>
                              {isSubmitted && (
                                <div className="mt-1">
                                  <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">
                                    已投递
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                        <div className="text-sm text-gray-700">
                          第 {currentPage} 页，共 {totalPages} 页
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => currentPage > 1 && fetchCandidates(currentPage - 1, searchTerm)}
                            disabled={currentPage <= 1}
                            className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
                          >
                            上一页
                          </button>
                          <button
                            onClick={() => currentPage < totalPages && fetchCandidates(currentPage + 1, searchTerm)}
                            disabled={currentPage >= totalPages}
                            className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
                          >
                            下一页
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          {/* Add New Candidate Info */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg flex items-center">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center mr-3">
              <span className="text-white text-sm">i</span>
            </div>
            <span className="text-blue-800 text-sm">
              如候选人简历还未录入，你可以&nbsp;
              <button
                onClick={onCreateNew}
                className="text-blue-600 hover:text-blue-800 underline font-medium"
              >
                添加新简历
              </button>
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              取消
            </button>
            <button
              disabled
              className="px-6 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed"
            >
              确定
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}