'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface CommunicationRecord {
  id: string
  candidateId: string
  userId: string
  communicationType: 'phone' | 'email' | 'wechat' | 'meeting'
  subject?: string
  content: string
  duration?: string
  outcome?: string
  purpose?: string
  nextFollowUpDate?: string
  notes?: string
  metadata?: any
  createdAt: string
  updatedAt: string
  user: {
    username: string
    email: string
  }
}

interface CommunicationRecordsListProps {
  candidateId: string
  onRefresh?: () => void
}

export default function CommunicationRecordsList({ candidateId, onRefresh }: CommunicationRecordsListProps) {
  const [records, setRecords] = useState<CommunicationRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedRecords, setExpandedRecords] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchCommunicationRecords()
  }, [candidateId])

  const fetchCommunicationRecords = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/candidates/${candidateId}/communications`)
      console.log('Communication records response:', response)
      setRecords(response.records || response.data || [])
    } catch (err: any) {
      console.error('Error fetching communication records:', err)
      setError('Failed to load communication records')
    } finally {
      setLoading(false)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'phone': return '📞'
      case 'email': return '📧'
      case 'wechat': return '💬'
      case 'meeting': return '🤝'
      default: return '📝'
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'phone': return '电话沟通'
      case 'email': return '邮件沟通'
      case 'wechat': return '微信沟通'
      case 'meeting': return '会议'
      default: return '其他'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'phone': return 'bg-green-100 text-green-800'
      case 'email': return 'bg-blue-100 text-blue-800'
      case 'wechat': return 'bg-purple-100 text-purple-800'
      case 'meeting': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const toggleExpanded = (recordId: string) => {
    const newExpanded = new Set(expandedRecords)
    if (newExpanded.has(recordId)) {
      newExpanded.delete(recordId)
    } else {
      newExpanded.add(recordId)
    }
    setExpandedRecords(newExpanded)
  }

  const truncateContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content
    // 截断到最近的完整单词或句子
    const truncated = content.substring(0, maxLength)
    const lastSpace = truncated.lastIndexOf(' ')
    const lastNewline = truncated.lastIndexOf('\n')
    
    const cutPoint = Math.max(lastSpace, lastNewline)
    const finalCutPoint = cutPoint > maxLength * 0.7 ? cutPoint : maxLength
    
    return content.substring(0, finalCutPoint).trim() + '...'
  }

  const shouldTruncate = (content: string) => {
    return content.length > 100 || content.split('\n').length > 3
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="border border-gray-200 rounded-lg p-4">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-full mb-1"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error}</p>
        <button 
          onClick={fetchCommunicationRecords}
          className="mt-2 text-red-600 hover:text-red-800 underline"
        >
          重试
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">沟通记录</h3>
        <button
          onClick={fetchCommunicationRecords}
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          🔄 刷新
        </button>
      </div>

      {records.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400 text-lg mb-2">💬</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无沟通记录</h3>
          <p className="text-gray-500">还没有添加任何沟通记录</p>
        </div>
      ) : (
        <div className="space-y-3">
          {records.map((record) => (
            <div key={record.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(record.communicationType)}`}>
                    {getTypeIcon(record.communicationType)} {getTypeLabel(record.communicationType)}
                  </span>
                  {record.subject && (
                    <span className="text-sm font-medium text-gray-900">
                      {record.subject}
                    </span>
                  )}
                </div>
                <div className="text-right text-sm text-gray-500">
                  <p>{record.user.username}</p>
                  <p>{formatDate(record.createdAt)}</p>
                </div>
              </div>

              <div className="mb-3">
                {shouldTruncate(record.content) ? (
                  <div>
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {expandedRecords.has(record.id) 
                        ? record.content 
                        : truncateContent(record.content)
                      }
                    </p>
                    <button
                      onClick={() => toggleExpanded(record.id)}
                      className="text-blue-600 hover:text-blue-800 text-sm mt-2 flex items-center space-x-1 transition-colors"
                    >
                      <span>
                        {expandedRecords.has(record.id) ? '收起' : '展开全部'}
                      </span>
                      <span className="text-xs">
                        {expandedRecords.has(record.id) ? '▲' : '▼'}
                      </span>
                    </button>
                  </div>
                ) : (
                  <p className="text-gray-700 whitespace-pre-wrap">{record.content}</p>
                )}
              </div>

              {/* Additional details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                {record.duration && (
                  <div>
                    <span className="text-gray-500">通话时长:</span>
                    <p className="font-medium">{record.duration}</p>
                  </div>
                )}
                {record.outcome && (
                  <div>
                    <span className="text-gray-500">沟通结果:</span>
                    <p className="font-medium">{record.outcome}</p>
                  </div>
                )}
                {record.purpose && (
                  <div>
                    <span className="text-gray-500">沟通目的:</span>
                    <p className="font-medium">{record.purpose}</p>
                  </div>
                )}
              </div>

              {record.nextFollowUpDate && (
                <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                  <div className="flex items-center space-x-2">
                    <span className="text-yellow-600">⏰</span>
                    <span className="text-sm text-yellow-800">
                      下次跟进时间: {formatDate(record.nextFollowUpDate)}
                    </span>
                  </div>
                </div>
              )}

              {record.notes && (
                <div className="mt-3 p-2 bg-gray-50 border border-gray-200 rounded">
                  <span className="text-sm text-gray-600">备注: {record.notes}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}