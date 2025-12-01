'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface CollaborationStats {
  overview: {
    totalJobs: number
    totalSubmissions: number
    totalCandidates: number
    collaborationsReceived: number
    collaborationsSent: number
    unreadNotifications: number
  }
  recentActivity: {
    jobsPublished: number
    submissions: number
    candidatesAdded: number
  }
}

interface Collaborator {
  id: string
  username: string
  email: string
  company?: {
    id: string
    name: string
  }
  collaborationType: 'submitted_to_me' | 'i_submitted_to' | 'mutual'
  submissionCount: number
}

interface SharedJob {
  id: string
  title: string
  industry?: string
  location?: string
  status: string
  publisher: {
    id: string
    username: string
    company?: {
      name: string
    }
  }
  companyClient: {
    name: string
    industry?: string
    location?: string
  }
  jobPermissions: Array<{
    id: string
    grantedAt: string
    expiresAt?: string
    grantedBy: {
      id: string
      username: string
    }
  }>
  _count: {
    candidateSubmissions: number
  }
}

export default function CollaborationDashboard() {
  const [stats, setStats] = useState<CollaborationStats | null>(null)
  const [collaborators, setCollaborators] = useState<Collaborator[]>([])
  const [sharedJobs, setSharedJobs] = useState<SharedJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeView, setActiveView] = useState<'overview' | 'collaborators' | 'shared-jobs'>('overview')

  const fetchStats = async () => {
    try {
      const response = await api.get('/collaborations/stats')
      setStats(response)
    } catch (err) {
      setError('Failed to fetch collaboration stats')
      console.error(err)
    }
  }

  const fetchCollaborators = async () => {
    try {
      const response = await api.get('/collaborations/network?limit=20')
      setCollaborators(response.collaborators)
    } catch (err) {
      setError('Failed to fetch collaborators')
      console.error(err)
    }
  }

  const fetchSharedJobs = async () => {
    try {
      const response = await api.get('/jobs/shared?limit=20')
      setSharedJobs(response.jobs)
    } catch (err) {
      setError('Failed to fetch shared jobs')
      console.error(err)
    }
  }

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        await Promise.all([
          fetchStats(),
          fetchCollaborators(),
          fetchSharedJobs()
        ])
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const getCollaborationTypeColor = (type: string) => {
    switch (type) {
      case 'mutual': return 'bg-green-100 text-green-800'
      case 'submitted_to_me': return 'bg-blue-100 text-blue-800'
      case 'i_submitted_to': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getCollaborationTypeLabel = (type: string) => {
    switch (type) {
      case 'mutual': return 'Mutual Collaboration'
      case 'submitted_to_me': return 'Submitted to My Jobs'
      case 'i_submitted_to': return 'I Submitted to Their Jobs'
      default: return 'Unknown'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (loading) return <div className="p-6">Loading collaboration dashboard...</div>

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Collaboration Dashboard</h1>
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveView('overview')}
            className={`px-4 py-2 rounded-lg ${
              activeView === 'overview' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveView('collaborators')}
            className={`px-4 py-2 rounded-lg ${
              activeView === 'collaborators' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Network
          </button>
          <button
            onClick={() => setActiveView('shared-jobs')}
            className={`px-4 py-2 rounded-lg ${
              activeView === 'shared-jobs' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Shared Jobs
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {activeView === 'overview' && stats && (
        <div className="space-y-6">
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-blue-600">{stats.overview.totalJobs}</div>
              <div className="text-sm text-gray-600">Total Jobs</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-green-600">{stats.overview.totalSubmissions}</div>
              <div className="text-sm text-gray-600">Submissions</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-purple-600">{stats.overview.totalCandidates}</div>
              <div className="text-sm text-gray-600">Candidates</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-orange-600">{stats.overview.collaborationsReceived}</div>
              <div className="text-sm text-gray-600">Jobs Shared With Me</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-red-600">{stats.overview.collaborationsSent}</div>
              <div className="text-sm text-gray-600">Jobs I Shared</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-yellow-600">{stats.overview.unreadNotifications}</div>
              <div className="text-sm text-gray-600">Unread Notifications</div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Recent Activity (Last 30 Days)</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-xl font-bold text-blue-600">{stats.recentActivity.jobsPublished}</div>
                <div className="text-sm text-gray-600">Jobs Published</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-green-600">{stats.recentActivity.submissions}</div>
                <div className="text-sm text-gray-600">Candidate Submissions</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-purple-600">{stats.recentActivity.candidatesAdded}</div>
                <div className="text-sm text-gray-600">Candidates Added</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <button className="bg-blue-600 text-white p-4 rounded-lg hover:bg-blue-700 text-center">
                <div className="text-lg font-semibold">Create Job</div>
                <div className="text-sm opacity-90">Post a new job opportunity</div>
              </button>
              <button className="bg-green-600 text-white p-4 rounded-lg hover:bg-green-700 text-center">
                <div className="text-lg font-semibold">Add Candidate</div>
                <div className="text-sm opacity-90">Register a new candidate</div>
              </button>
              <button className="bg-purple-600 text-white p-4 rounded-lg hover:bg-purple-700 text-center">
                <div className="text-lg font-semibold">Search & Match</div>
                <div className="text-sm opacity-90">Find matching candidates</div>
              </button>
              <button className="bg-orange-600 text-white p-4 rounded-lg hover:bg-orange-700 text-center">
                <div className="text-lg font-semibold">Share Job</div>
                <div className="text-sm opacity-90">Collaborate with partners</div>
              </button>
            </div>
          </div>
        </div>
      )}

      {activeView === 'collaborators' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Collaboration Network</h2>
            <span className="text-sm text-gray-600">{collaborators.length} active collaborators</span>
          </div>

          {collaborators.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No collaboration history found. Start by sharing jobs or submitting candidates!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {collaborators.map((collaborator) => (
                <div key={collaborator.id} className="bg-white p-4 rounded-lg shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{collaborator.username}</h3>
                      <p className="text-sm text-gray-600">{collaborator.email}</p>
                      {collaborator.company && (
                        <p className="text-sm text-gray-500">{collaborator.company.name}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-blue-600">{collaborator.submissionCount}</div>
                      <div className="text-xs text-gray-500">collaborations</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCollaborationTypeColor(collaborator.collaborationType)}`}>
                      {getCollaborationTypeLabel(collaborator.collaborationType)}
                    </span>
                    <button className="text-blue-600 hover:text-blue-800 text-sm">
                      Send Message
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeView === 'shared-jobs' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Jobs Shared With Me</h2>
            <span className="text-sm text-gray-600">{sharedJobs.length} shared jobs</span>
          </div>

          {sharedJobs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No jobs have been shared with you yet.
            </div>
          ) : (
            <div className="space-y-4">
              {sharedJobs.map((job) => (
                <div key={job.id} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                      <p className="text-gray-600">{job.companyClient.name}</p>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        {job.industry && <span>{job.industry}</span>}
                        {job.location && <span>{job.location}</span>}
                        <span className="capitalize">{job.status}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-sm text-gray-500">
                        {job._count.candidateSubmissions} submissions
                      </span>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-3 rounded mb-4">
                    <div className="text-sm">
                      <span className="font-medium">Shared by:</span> {job.publisher.username}
                      {job.publisher.company && ` (${job.publisher.company.name})`}
                    </div>
                    {job.jobPermissions.map((permission) => (
                      <div key={permission.id} className="text-xs text-gray-500 mt-1">
                        Granted on {formatDate(permission.grantedAt)}
                        {permission.expiresAt && ` • Expires ${formatDate(permission.expiresAt)}`}
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                      View Details
                    </button>
                    <button className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
                      Submit Candidate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}