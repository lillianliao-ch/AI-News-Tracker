'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface Notification {
  id: string
  type: 'job_shared' | 'job_closed' | 'submission_status_changed' | 'maintainer_change_request' | 'system_announcement'
  title: string
  content: string
  relatedId?: string
  isRead: boolean
  createdAt: string
}

interface Message {
  id: string
  title: string
  content: string
  isRead: boolean
  createdAt: string
}

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'notifications' | 'messages'>('notifications')
  const [unreadCount, setUnreadCount] = useState(0)
  const [showSendMessage, setShowSendMessage] = useState(false)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  
  const [messageForm, setMessageForm] = useState({
    recipientId: '',
    subject: '',
    content: '',
    relatedJobId: '',
    relatedCandidateId: ''
  })

  const [filters, setFilters] = useState({
    unreadOnly: false,
    type: ''
  })

  const fetchNotifications = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        unreadOnly: filters.unreadOnly.toString(),
        ...(filters.type && { type: filters.type })
      })
      
      const response = await api.get(`/collaborations/notifications?${params}`)
      setNotifications(response.notifications)
      setUnreadCount(response.unreadCount)
      setTotalPages(response.pagination.pages)
    } catch (err) {
      setError('Failed to fetch notifications')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchMessages = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        unreadOnly: filters.unreadOnly.toString()
      })
      
      const response = await api.get(`/messaging/messages?${params}`)
      setMessages(response.messages)
      setTotalPages(response.pagination.pages)
    } catch (err) {
      setError('Failed to fetch messages')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const markNotificationsAsRead = async (notificationIds: string[]) => {
    try {
      await api.patch('/collaborations/notifications/mark-read', { notificationIds })
      fetchNotifications()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to mark notifications as read')
    }
  }

  const markAllAsRead = async () => {
    try {
      if (activeTab === 'notifications') {
        await api.patch('/collaborations/notifications/mark-all-read')
        fetchNotifications()
      } else {
        const messageIds = messages.filter(m => !m.isRead).map(m => m.id)
        if (messageIds.length > 0) {
          await api.patch('/messaging/messages/mark-read', { messageIds })
          fetchMessages()
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to mark all as read')
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/messaging/messages', messageForm)
      setShowSendMessage(false)
      setMessageForm({
        recipientId: '',
        subject: '',
        content: '',
        relatedJobId: '',
        relatedCandidateId: ''
      })
      alert('Message sent successfully!')
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to send message')
    }
  }

  const deleteNotification = async (notificationId: string) => {
    try {
      await api.delete(`/collaborations/notifications/${notificationId}`)
      fetchNotifications()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete notification')
    }
  }

  useEffect(() => {
    if (activeTab === 'notifications') {
      fetchNotifications()
    } else {
      fetchMessages()
    }
  }, [activeTab, page, filters])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 1) {
      return 'Just now'
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'job_shared': return '📋'
      case 'job_closed': return '🔒'
      case 'submission_status_changed': return '📝'
      case 'maintainer_change_request': return '👥'
      case 'system_announcement': return '📢'
      default: return '📌'
    }
  }

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'job_shared': return 'border-l-blue-500'
      case 'job_closed': return 'border-l-red-500'
      case 'submission_status_changed': return 'border-l-green-500'
      case 'maintainer_change_request': return 'border-l-yellow-500'
      case 'system_announcement': return 'border-l-purple-500'
      default: return 'border-l-gray-500'
    }
  }

  if (loading) return <div className="p-6">Loading...</div>

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Communication Center</h1>
        <div className="flex space-x-2">
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
            >
              Mark All Read ({unreadCount})
            </button>
          )}
          <button
            onClick={() => setShowSendMessage(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Send Message
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-1 mb-6">
        <button
          onClick={() => {setActiveTab('notifications'); setPage(1)}}
          className={`px-4 py-2 rounded-lg ${
            activeTab === 'notifications' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Notifications {unreadCount > 0 && `(${unreadCount})`}
        </button>
        <button
          onClick={() => {setActiveTab('messages'); setPage(1)}}
          className={`px-4 py-2 rounded-lg ${
            activeTab === 'messages' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Messages
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.unreadOnly}
              onChange={(e) => setFilters({...filters, unreadOnly: e.target.checked})}
              className="mr-2"
            />
            Unread only
          </label>
          
          {activeTab === 'notifications' && (
            <select
              value={filters.type}
              onChange={(e) => setFilters({...filters, type: e.target.value})}
              className="border border-gray-300 rounded px-3 py-1"
            >
              <option value="">All types</option>
              <option value="job_shared">Job Shared</option>
              <option value="job_closed">Job Closed</option>
              <option value="submission_status_changed">Status Changed</option>
              <option value="maintainer_change_request">Maintainer Change</option>
              <option value="system_announcement">System Announcement</option>
            </select>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {activeTab === 'notifications' ? (
          notifications.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No notifications found
            </div>
          ) : (
            notifications.map((notification) => (
              <div
                key={notification.id}
                className={`bg-white p-4 rounded-lg shadow border-l-4 ${getNotificationColor(notification.type)} ${
                  !notification.isRead ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-lg">{getNotificationIcon(notification.type)}</span>
                      <h3 className={`font-medium ${!notification.isRead ? 'font-bold' : ''}`}>
                        {notification.title}
                      </h3>
                      {!notification.isRead && (
                        <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                          New
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700 mb-2">{notification.content}</p>
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>{formatDate(notification.createdAt)}</span>
                      <div className="flex space-x-2">
                        {!notification.isRead && (
                          <button
                            onClick={() => markNotificationsAsRead([notification.id])}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            Mark as Read
                          </button>
                        )}
                        <button
                          onClick={() => deleteNotification(notification.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )
        ) : (
          messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No messages found
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`bg-white p-4 rounded-lg shadow ${
                  !message.isRead ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className={`font-medium mb-1 ${!message.isRead ? 'font-bold' : ''}`}>
                      {message.title}
                      {!message.isRead && (
                        <span className="ml-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                          New
                        </span>
                      )}
                    </h3>
                    <p className="text-gray-700 mb-2">{message.content}</p>
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>{formatDate(message.createdAt)}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )
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

      {/* Send Message Modal */}
      {showSendMessage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">Send Message</h2>
              <form onSubmit={sendMessage} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recipient ID *
                  </label>
                  <input
                    type="text"
                    required
                    value={messageForm.recipientId}
                    onChange={(e) => setMessageForm({...messageForm, recipientId: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="Enter recipient user ID"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subject
                  </label>
                  <input
                    type="text"
                    value={messageForm.subject}
                    onChange={(e) => setMessageForm({...messageForm, subject: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="Message subject"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Message Content *
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={messageForm.content}
                    onChange={(e) => setMessageForm({...messageForm, content: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="Type your message here..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Related Job ID
                    </label>
                    <input
                      type="text"
                      value={messageForm.relatedJobId}
                      onChange={(e) => setMessageForm({...messageForm, relatedJobId: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      placeholder="Optional"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Related Candidate ID
                    </label>
                    <input
                      type="text"
                      value={messageForm.relatedCandidateId}
                      onChange={(e) => setMessageForm({...messageForm, relatedCandidateId: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      placeholder="Optional"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-4 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowSendMessage(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Send Message
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}