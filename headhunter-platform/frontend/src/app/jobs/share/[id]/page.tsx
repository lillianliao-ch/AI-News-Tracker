'use client'

import React, { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'

interface JobShareData {
  id: string
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
  status: string
  createdAt: string
  updatedAt: string
  companyClient: {
    name: string
    industry?: string
    location?: string
  }
  publisher: {
    username: string
    email: string
    company?: {
      name: string
    }
  }
}

export default function JobSharePage() {
  const params = useParams()
  const jobId = params.id as string
  const [job, setJob] = useState<JobShareData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        setLoading(true)
        setError('')
        
        console.log('Fetching job details for ID:', jobId)
        const response = await fetch(`http://localhost:4000/api/jobs/share/${jobId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          cache: 'no-cache'
        })
        
        console.log('Response status:', response.status, response.statusText)
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error('Response error:', errorText)
          throw new Error(`HTTP ${response.status}: ${errorText || '职位信息加载失败'}`)
        }
        
        const data = await response.json()
        console.log('Job data received:', data)
        
        if (data.success && data.job) {
          setJob(data.job)
        } else {
          throw new Error('职位信息格式错误')
        }
      } catch (err: any) {
        console.error('Error fetching job details:', err)
        setError(err.message || '职位信息加载失败')
      } finally {
        setLoading(false)
      }
    }

    if (jobId) {
      fetchJobDetails()
    }
  }, [jobId])

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return '薪资面议'
    if (min && max) {
      return `${(min / 10000).toFixed(0)}-${(max / 10000).toFixed(0)}万/年`
    }
    if (min) return `${(min / 10000).toFixed(0)}万/年起`
    if (max) return `最高${(max / 10000).toFixed(0)}万/年`
    return '薪资面议'
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  }

  const handleContact = () => {
    const email = job?.publisher.email
    const subject = `关于${job?.title}职位的咨询`
    const body = `您好！\\n\\n我对您发布的"${job?.title}"职位很感兴趣，希望了解更多详情。\\n\\n感谢您的时间！`
    
    window.location.href = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">职位加载失败</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500">Job ID: {jobId}</p>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-gray-400 text-6xl mb-4">📄</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">职位不存在</h1>
          <p className="text-gray-600">该职位可能已被删除或不存在</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 font-semibold text-lg">
                {job.companyClient.name.charAt(0)}
              </span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">{job.title}</h1>
              <p className="text-gray-600 text-sm">{job.companyClient.name}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        
        {/* Job Overview */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">职位概况</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-3">
              <span className="text-gray-400">💰</span>
              <div>
                <span className="text-sm text-gray-500">薪资待遇</span>
                <p className="font-medium">{formatSalary(job.salaryMin, job.salaryMax)}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className="text-gray-400">📍</span>
              <div>
                <span className="text-sm text-gray-500">工作地点</span>
                <p className="font-medium">{job.location || '待确认'}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className="text-gray-400">🏢</span>
              <div>
                <span className="text-sm text-gray-500">所属行业</span>
                <p className="font-medium">{job.industry || job.companyClient.industry || '不限'}</p>
              </div>
            </div>
            
            {job.urgency && (
              <div className="flex items-center space-x-3">
                <span className="text-gray-400">⚡</span>
                <div>
                  <span className="text-sm text-gray-500">紧急程度</span>
                  <p className="font-medium">{job.urgency}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Job Description */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">职位描述</h2>
          <div className="prose prose-sm max-w-none">
            <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{job.description}</p>
          </div>
        </div>

        {/* Job Requirements */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">任职要求</h2>
          <div className="prose prose-sm max-w-none">
            <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{job.requirements}</p>
          </div>
        </div>

        {/* Benefits */}
        {job.benefits && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">福利待遇</h2>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{job.benefits}</p>
            </div>
          </div>
        )}

        {/* Company Info */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">公司信息</h2>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-500">公司名称</span>
              <p className="font-medium">{job.companyClient.name}</p>
            </div>
            {job.companyClient.industry && (
              <div>
                <span className="text-sm text-gray-500">公司行业</span>
                <p className="font-medium">{job.companyClient.industry}</p>
              </div>
            )}
            {job.companyClient.location && (
              <div>
                <span className="text-sm text-gray-500">公司地址</span>
                <p className="font-medium">{job.companyClient.location}</p>
              </div>
            )}
          </div>
        </div>

        {/* Contact Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">联系我们</h2>
          <div className="space-y-4">
            <div>
              <span className="text-sm text-gray-500">猎头顾问</span>
              <p className="font-medium">{job.publisher.username}</p>
              {job.publisher.company && (
                <p className="text-sm text-gray-600">{job.publisher.company.name}</p>
              )}
            </div>
            
            <div className="pt-4">
              <button
                onClick={handleContact}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
              >
                <span>📧</span>
                <span>联系猎头顾问</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-6">
          <p className="text-sm text-gray-500">
            发布时间: {formatDate(job.createdAt)}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            由猎头协作平台提供
          </p>
        </div>
      </div>
    </div>
  )
}