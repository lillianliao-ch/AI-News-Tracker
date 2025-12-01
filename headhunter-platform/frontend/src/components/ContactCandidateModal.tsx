'use client'

import React, { useState } from 'react'
import { api } from '@/lib/api'

interface Candidate {
  id: string
  name: string
  phone: string
  email?: string
}

interface ContactCandidateModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate
  onContactRecorded?: () => void
}

interface EmailTemplate {
  id: string
  name: string
  icon: string
  subject: string
  content: string
}

export default function ContactCandidateModal({
  isOpen,
  onClose,
  candidate,
  onContactRecorded
}: ContactCandidateModalProps) {
  const [contactMethod, setContactMethod] = useState<'phone' | 'email' | 'wechat' | ''>('')
  const [emailMode, setEmailMode] = useState<'template' | 'custom' | 'external'>('template')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  // 电话联系表单
  const [phoneData, setPhoneData] = useState({
    duration: '',
    content: '',
    outcome: '',
    nextFollowUp: '',
    notes: ''
  })

  // 邮件联系表单
  const [emailData, setEmailData] = useState({
    subject: '',
    content: '',
    purpose: '',
    notes: ''
  })

  // 微信联系表单
  const [wechatData, setWechatData] = useState({
    content: '',
    outcome: '',
    duration: '',
    nextFollowUp: '',
    notes: '',
    wechatId: ''
  })

  const [selectedTemplate, setSelectedTemplate] = useState<string>('')

  // 邮件模板
  const emailTemplates: EmailTemplate[] = [
    {
      id: 'interview_invitation',
      name: '面试邀请',
      icon: '📅',
      subject: '面试邀请 - {jobTitle}',
      content: `尊敬的{candidateName}，

您好！

我们对您的简历非常感兴趣，诚邀您参加我们的面试。

面试详情：
- 职位：{jobTitle}
- 时间：请回复确认您的可用时间
- 地点：将根据您的确认另行通知

期待与您的进一步沟通！

此致
敬礼

{senderName}
{companyName}`
    },
    {
      id: 'job_recommendation',
      name: '职位推荐',
      icon: '💼',
      subject: '职位推荐 - {jobTitle}',
      content: `尊敬的{candidateName}，

您好！

根据您的工作经验和技能背景，我们有一个非常适合您的职位机会：

职位信息：
- 职位名称：{jobTitle}
- 薪资范围：面议
- 工作地点：{location}

如果您感兴趣，欢迎与我们进一步沟通。

此致
敬礼

{senderName}
{companyName}`
    },
    {
      id: 'follow_up',
      name: '跟进沟通',
      icon: '🔄',
      subject: '职位跟进',
      content: `尊敬的{candidateName}，

您好！

希望您一切都好。我想跟进一下我们之前讨论的职位机会。

如果您有任何问题或需要更多信息，请随时联系我。

期待您的回复！

此致
敬礼

{senderName}
{companyName}`
    }
  ]

  const handlePhoneContact = async () => {
    if (!phoneData.content.trim()) {
      setError('请填写沟通内容')
      return
    }

    try {
      setLoading(true)
      setError('')

      // 保存沟通记录
      await api.post(`/candidates/${candidate.id}/communications`, {
        communicationType: 'phone',
        content: phoneData.content,
        duration: phoneData.duration,
        outcome: phoneData.outcome,
        nextFollowUpDate: phoneData.nextFollowUp || null,
        notes: phoneData.notes,
        metadata: {
          phoneNumber: candidate.phone
        }
      })

      onContactRecorded?.()
      onClose()
      
      // 重置表单
      setPhoneData({
        duration: '',
        content: '',
        outcome: '',
        nextFollowUp: '',
        notes: ''
      })
    } catch (err: any) {
      setError('保存沟通记录失败：' + (err.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  const handleEmailContact = async (sendExternal: boolean = false) => {
    if (!emailData.subject.trim() || !emailData.content.trim()) {
      setError('请填写邮件主题和内容')
      return
    }

    try {
      setLoading(true)
      setError('')

      if (sendExternal) {
        // 打开外部邮件客户端
        openExternalEmailClient()
      }

      // 保存沟通记录
      await api.post(`/candidates/${candidate.id}/communications`, {
        communicationType: 'email',
        subject: emailData.subject,
        content: emailData.content,
        purpose: emailData.purpose,
        notes: emailData.notes,
        metadata: {
          emailAddress: candidate.email,
          emailSubject: emailData.subject,
          sentViaExternal: sendExternal
        }
      })

      onContactRecorded?.()
      onClose()
      
      // 重置表单
      setEmailData({
        subject: '',
        content: '',
        purpose: '',
        notes: ''
      })
    } catch (err: any) {
      setError('保存沟通记录失败：' + (err.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  const handleWechatContact = async () => {
    if (!wechatData.content.trim()) {
      setError('请填写沟通内容')
      return
    }

    try {
      setLoading(true)
      setError('')

      // 保存沟通记录
      await api.post(`/candidates/${candidate.id}/communications`, {
        communicationType: 'wechat',
        content: wechatData.content,
        duration: wechatData.duration,
        outcome: wechatData.outcome,
        nextFollowUpDate: wechatData.nextFollowUp || null,
        notes: wechatData.notes,
        metadata: {
          wechatId: wechatData.wechatId
        }
      })

      onContactRecorded?.()
      onClose()
      
      // 重置表单
      setWechatData({
        content: '',
        outcome: '',
        duration: '',
        nextFollowUp: '',
        notes: '',
        wechatId: ''
      })
    } catch (err: any) {
      setError('保存沟通记录失败：' + (err.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  const openExternalEmailClient = () => {
    // 检测用户设备和偏好，选择最佳的邮件客户端
    const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    const isApple = /Mac|iPhone|iPad|iPod/i.test(navigator.userAgent)

    let emailUrl = ''
    
    // 正确处理邮件内容编码
    const encodedSubject = encodeURIComponent(emailData.subject)
    const encodedContent = encodeURIComponent(emailData.content)

    if (isMobile) {
      // 移动设备使用 mailto
      emailUrl = `mailto:${candidate.email}?subject=${encodedSubject}&body=${encodedContent}`
    } else {
      // 桌面设备优先使用 Gmail Web
      emailUrl = `https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1&source=mailto&to=${candidate.email}&subject=${encodedSubject}&body=${encodedContent}`
    }

    window.open(emailUrl, '_blank')
  }

  const populateTemplate = (template: EmailTemplate) => {
    const populatedContent = template.content
      .replace(/{candidateName}/g, candidate.name)
      .replace(/{jobTitle}/g, '待确认职位')
      .replace(/{location}/g, '待确认')
      .replace(/{senderName}/g, '招聘顾问')
      .replace(/{companyName}/g, '猎头公司')

    setEmailData({
      ...emailData,
      subject: template.subject.replace(/{jobTitle}/g, '待确认职位'),
      content: populatedContent,
      purpose: template.name
    })
    setSelectedTemplate(template.id)
    setEmailMode('custom')
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-blue-600 text-white px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-medium">联系候选人</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {/* 候选人信息 */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-medium text-lg">
                  {candidate.name.charAt(0)}
                </span>
              </div>
              <div>
                <h3 className="font-medium text-gray-900">{candidate.name}</h3>
                <div className="text-sm text-gray-600">
                  <p>📞 {candidate.phone}</p>
                  {candidate.email && <p>📧 {candidate.email}</p>}
                </div>
              </div>
            </div>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          {/* 联系方式选择 */}
          {!contactMethod && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4">选择联系方式</h3>
              
              <button
                onClick={() => setContactMethod('phone')}
                className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex items-center space-x-4"
              >
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-2xl">📞</span>
                </div>
                <div className="text-left">
                  <h4 className="font-medium text-gray-900">电话联系</h4>
                  <p className="text-sm text-gray-600">记录通话内容和结果</p>
                </div>
              </button>

              {candidate.email && (
                <button
                  onClick={() => setContactMethod('email')}
                  className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex items-center space-x-4"
                >
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 text-2xl">📧</span>
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium text-gray-900">邮件联系</h4>
                    <p className="text-sm text-gray-600">发送邮件并记录沟通</p>
                  </div>
                </button>
              )}

              <button
                onClick={() => setContactMethod('wechat')}
                className="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors flex items-center space-x-4"
              >
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-2xl">💬</span>
                </div>
                <div className="text-left">
                  <h4 className="font-medium text-gray-900">微信联系</h4>
                  <p className="text-sm text-gray-600">通过微信沟通并记录</p>
                </div>
              </button>
            </div>
          )}

          {/* 电话联系表单 */}
          {contactMethod === 'phone' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">📞 电话联系</h3>
                <button
                  onClick={() => setContactMethod('')}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  ← 返回选择
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    通话时长
                  </label>
                  <input
                    type="text"
                    value={phoneData.duration}
                    onChange={(e) => setPhoneData({...phoneData, duration: e.target.value})}
                    placeholder="例：30分钟"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    沟通结果
                  </label>
                  <select
                    value={phoneData.outcome}
                    onChange={(e) => setPhoneData({...phoneData, outcome: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">请选择结果</option>
                    <option value="感兴趣">感兴趣</option>
                    <option value="需考虑">需考虑</option>
                    <option value="暂无意向">暂无意向</option>
                    <option value="已有工作">已有工作</option>
                    <option value="薪资不符">薪资不符</option>
                    <option value="地点不合适">地点不合适</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 沟通内容
                </label>
                <textarea
                  value={phoneData.content}
                  onChange={(e) => setPhoneData({...phoneData, content: e.target.value})}
                  placeholder="记录详细的沟通内容..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  下次跟进时间
                </label>
                <input
                  type="datetime-local"
                  value={phoneData.nextFollowUp}
                  onChange={(e) => setPhoneData({...phoneData, nextFollowUp: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  备注
                </label>
                <textarea
                  value={phoneData.notes}
                  onChange={(e) => setPhoneData({...phoneData, notes: e.target.value})}
                  placeholder="其他备注信息..."
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <button
                  onClick={() => setContactMethod('')}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handlePhoneContact}
                  disabled={loading}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? '保存中...' : '完成联系'}
                </button>
              </div>
            </div>
          )}

          {/* 邮件联系表单 */}
          {contactMethod === 'email' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">📧 邮件联系</h3>
                <button
                  onClick={() => setContactMethod('')}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  ← 返回选择
                </button>
              </div>

              {/* 邮件模式选择 */}
              {emailMode === 'template' && (
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">选择邮件模板</h4>
                  <div className="grid grid-cols-1 gap-3">
                    {emailTemplates.map((template) => (
                      <button
                        key={template.id}
                        onClick={() => populateTemplate(template)}
                        className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex items-center space-x-3"
                      >
                        <span className="text-2xl">{template.icon}</span>
                        <div className="text-left">
                          <h5 className="font-medium text-gray-900">{template.name}</h5>
                          <p className="text-sm text-gray-600">{template.subject}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                  
                  <button
                    onClick={() => setEmailMode('custom')}
                    className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    <span className="text-blue-600">✏️ 自定义邮件</span>
                  </button>
                </div>
              )}

              {/* 自定义邮件编辑 */}
              {emailMode === 'custom' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">编辑邮件</h4>
                    <button
                      onClick={() => {
                        setEmailMode('template')
                        setEmailData({ subject: '', content: '', purpose: '', notes: '' })
                      }}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      ← 选择模板
                    </button>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      收件人
                    </label>
                    <input
                      type="email"
                      value={candidate.email}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="text-red-500">*</span> 邮件主题
                    </label>
                    <input
                      type="text"
                      value={emailData.subject}
                      onChange={(e) => setEmailData({...emailData, subject: e.target.value})}
                      placeholder="输入邮件主题..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="text-red-500">*</span> 邮件内容
                    </label>
                    <textarea
                      value={emailData.content}
                      onChange={(e) => setEmailData({...emailData, content: e.target.value})}
                      placeholder="输入邮件内容..."
                      rows={8}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      联系目的
                    </label>
                    <input
                      type="text"
                      value={emailData.purpose}
                      onChange={(e) => setEmailData({...emailData, purpose: e.target.value})}
                      placeholder="例：面试邀请、职位推荐、跟进沟通"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      备注
                    </label>
                    <textarea
                      value={emailData.notes}
                      onChange={(e) => setEmailData({...emailData, notes: e.target.value})}
                      placeholder="其他备注信息..."
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* 发送选项 */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-900 mb-3">发送方式</h5>
                    <div className="space-y-2">
                      <button
                        onClick={() => handleEmailContact(true)}
                        disabled={loading}
                        className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                      >
                        <span>🚀</span>
                        <span>{loading ? '处理中...' : '打开邮件客户端发送'}</span>
                      </button>
                      
                      <div className="text-xs text-gray-500 text-center">
                        将打开您的默认邮件客户端，同时记录沟通记录
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-4 pt-4">
                    <button
                      onClick={() => setContactMethod('')}
                      className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                    >
                      取消
                    </button>
                    <button
                      onClick={() => handleEmailContact(false)}
                      disabled={loading}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {loading ? '保存中...' : '仅记录邮件'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 微信联系表单 */}
          {contactMethod === 'wechat' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">💬 微信联系</h3>
                <button
                  onClick={() => setContactMethod('')}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  ← 返回选择
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    微信号/昵称
                  </label>
                  <input
                    type="text"
                    value={wechatData.wechatId}
                    onChange={(e) => setWechatData({...wechatData, wechatId: e.target.value})}
                    placeholder="候选人的微信号或昵称"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    沟通时长
                  </label>
                  <input
                    type="text"
                    value={wechatData.duration}
                    onChange={(e) => setWechatData({...wechatData, duration: e.target.value})}
                    placeholder="例：30分钟"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  沟通结果
                </label>
                <select
                  value={wechatData.outcome}
                  onChange={(e) => setWechatData({...wechatData, outcome: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择结果</option>
                  <option value="感兴趣">感兴趣</option>
                  <option value="需考虑">需考虑</option>
                  <option value="暂无意向">暂无意向</option>
                  <option value="已有工作">已有工作</option>
                  <option value="薪资不符">薪资不符</option>
                  <option value="地点不合适">地点不合适</option>
                  <option value="需要更多信息">需要更多信息</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 沟通内容
                </label>
                <textarea
                  value={wechatData.content}
                  onChange={(e) => setWechatData({...wechatData, content: e.target.value})}
                  placeholder="记录详细的微信沟通内容，包括候选人反馈、关心的问题等..."
                  rows={5}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  下次跟进时间
                </label>
                <input
                  type="datetime-local"
                  value={wechatData.nextFollowUp}
                  onChange={(e) => setWechatData({...wechatData, nextFollowUp: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  备注
                </label>
                <textarea
                  value={wechatData.notes}
                  onChange={(e) => setWechatData({...wechatData, notes: e.target.value})}
                  placeholder="其他备注信息，如候选人特殊要求、偏好等..."
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-start space-x-3">
                  <span className="text-green-600 text-lg">💡</span>
                  <div className="text-sm text-green-700">
                    <p className="font-medium mb-1">微信沟通提示：</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>记录关键信息：候选人的求职意向、薪资期望、工作时间偏好</li>
                      <li>注意沟通语气：微信相对轻松，可以更自然地交流</li>
                      <li>及时跟进：微信回复较快，建议及时响应候选人疑问</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <button
                  onClick={() => setContactMethod('')}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleWechatContact}
                  disabled={loading}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? '保存中...' : '完成沟通记录'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}