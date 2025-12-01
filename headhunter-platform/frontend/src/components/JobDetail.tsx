'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useAuth } from './AuthProvider'

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
  updatedAt: string
}

interface JobDetailProps {
  jobId: string
  onBack: () => void
}

export default function JobDetail({ jobId, onBack }: JobDetailProps) {
  const { user } = useAuth()
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchJob = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/jobs/${jobId}`)
      setJob(response)
    } catch (err) {
      setError('Failed to fetch job details')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const submitResume = async (jobId: string) => {
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
        fetchJob() // Refresh to show updated submission count
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to submit resume')
      }
    }
    fileInput.click()
  }

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return 'Salary not specified'
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`
    if (min) return `From $${min.toLocaleString()}`
    if (max) return `Up to $${max.toLocaleString()}`
  }

  useEffect(() => {
    fetchJob()
  }, [jobId])

  if (loading) return <div className="p-6">Loading job details...</div>
  if (!job) return <div className="p-6">Job not found</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Header */}
        <div className="bg-white shadow-sm">
          <div className="px-6 py-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h1 className="text-xl font-medium text-gray-900 mb-3 border-b-2 border-orange-500 pb-2 inline-block">
                  {job.title}
                </h1>
                <div className="flex items-center gap-8 text-sm text-gray-600 mt-4">
                  <span>职位状态：<span className="font-medium text-gray-900">
                    {job.status === 'open' ? '招募中' :
                     job.status === 'paused' ? '暂停' :
                     job.status === 'closed' ? '关闭' : job.status}
                  </span></span>
                  <span>更新时间：<span className="font-medium text-gray-900">
                    {new Date(job.updatedAt).toLocaleDateString('zh-CN', {
                      year: 'numeric',
                      month: '2-digit', 
                      day: '2-digit'
                    })}
                  </span></span>
                  <span>有效日期：<span className="font-medium text-gray-900">
                    {new Date(new Date(job.createdAt).getTime() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString('zh-CN', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit'
                    })}
                  </span></span>
                </div>
              </div>
              <button
                onClick={onBack}
                className="text-gray-600 hover:text-gray-800 text-sm bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded transition-colors"
              >
                ← 返回列表
              </button>
            </div>
          </div>
        </div>

        {/* Job Info Grid */}
        <div className="px-6 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-3">
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <table className="w-full">
                  <tbody>
                    <tr className="border-b border-gray-100">
                      <td className="px-6 py-4 bg-gray-50 font-medium text-sm text-gray-700 w-32">部门：</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{job.companyClient.name}</td>
                      <td className="px-6 py-4 bg-gray-50 font-medium text-sm text-gray-700 w-32">学历要求：</td>
                      <td className="px-6 py-4 text-sm text-gray-900">本科</td>
                    </tr>
                    <tr className="border-b border-gray-100">
                      <td className="px-6 py-4 bg-gray-50 font-medium text-sm text-gray-700">工作地点：</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{job.location || '未指定'}</td>
                      <td className="px-6 py-4 bg-gray-50 font-medium text-sm text-gray-700">工作年限要求：</td>
                      <td className="px-6 py-4 text-sm text-gray-900">五年以上</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 bg-gray-50 font-medium text-sm text-gray-700">薪资范围：</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{formatSalary(job.salaryMin, job.salaryMax)}</td>
                      <td className="px-6 py-4 bg-gray-50 font-medium text-sm text-gray-700">招聘人数：</td>
                      <td className="px-6 py-4 text-sm text-gray-900">1</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="font-medium text-sm text-gray-700 mb-2">岗位级别：</h3>
                <p className="text-sm text-gray-900 font-medium">P7</p>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 pb-8">
          <div className="bg-white rounded-lg shadow-sm">
            {/* Content Tabs */}
            <div className="border-b border-gray-200">
              <div className="px-6">
                <div className="flex">
                  <button className="px-4 py-4 border-b-2 border-orange-500 text-orange-600 font-medium text-sm">
                    职位详情
                  </button>
                </div>
              </div>
            </div>

            <div className="p-8">
              {/* Job Description */}
              <div className="mb-10">
                <h3 className="text-base font-medium mb-4 text-orange-600 border-l-4 border-orange-500 pl-3">
                  岗位描述
                </h3>
                <div className="text-sm text-gray-700 leading-7 pl-4">
                  <div className="space-y-2">
                    {job.description.split('\n').map((line, index) => (
                      <p key={index} className={line.trim().startsWith('(') ? 'ml-0' : ''}>
                        {line.trim() || <br />}
                      </p>
                    ))}
                  </div>
                </div>
              </div>

              {/* Job Requirements */}
              <div className="mb-10">
                <h3 className="text-base font-medium mb-4 text-orange-600 border-l-4 border-orange-500 pl-3">
                  岗位要求
                </h3>
                <div className="text-sm text-gray-700 leading-7 pl-4">
                  <div className="space-y-2">
                    {job.requirements.split('\n').map((line, index) => (
                      <p key={index} className={line.trim().startsWith('(') ? 'ml-0' : ''}>
                        {line.trim() || <br />}
                      </p>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recruiter */}
              <div className="mb-8">
                <h3 className="text-base font-medium mb-4 text-orange-600 border-l-4 border-orange-500 pl-3">
                  招聘责任人
                </h3>
                <div className="text-sm text-blue-600 font-medium pl-4">
                  {job.publisher.username}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center gap-4 pt-6 border-t border-gray-100">
                <button
                  onClick={() => submitResume(job.id)}
                  className="bg-orange-500 text-white px-8 py-3 rounded-md hover:bg-orange-600 font-medium transition-colors"
                >
                  递交简历
                </button>
                <button
                  onClick={onBack}
                  className="bg-gray-500 text-white px-8 py-3 rounded-md hover:bg-gray-600 font-medium transition-colors"
                >
                  返回列表
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}