import React, { useState } from 'react'
import { api } from '@/lib/api'

interface QuickCandidateCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onCandidateCreated: (candidate: any) => void
}

export default function QuickCandidateCreateModal({
  isOpen,
  onClose,
  onCandidateCreated
}: QuickCandidateCreateModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    currentAddress: '',
    nationality: '',
    workPermit: '',
    workYears: '',
    education: '',
    linkedinUrl: '',
    personalWebsite: ''
  })
  
  // 工作经历数组
  const [workExperiences, setWorkExperiences] = useState([{
    company: '',
    position: '',
    startDate: '',
    endDate: '',
    description: ''
  }])
  
  // 教育经历数组
  const [educationExperiences, setEducationExperiences] = useState([{
    startDate: '',
    endDate: '',
    degree: '',
    school: '',
    major: '',
    description: ''
  }])
  
  // 项目经历数组
  const [projectExperiences, setProjectExperiences] = useState([])
  
  // 培训经历数组
  const [trainingExperiences, setTrainingExperiences] = useState([])
  
  // 文件上传状态
  const [files, setFiles] = useState({
    resume: null,
    coverLetter: null,
    portfolio: null
  })
  const [uploadingFiles, setUploadingFiles] = useState({
    resume: false,
    coverLetter: false,
    portfolio: false
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  // 工作经历处理函数
  const handleWorkExperienceChange = (index: number, field: string, value: string) => {
    const newExperiences = [...workExperiences]
    newExperiences[index] = { ...newExperiences[index], [field]: value }
    setWorkExperiences(newExperiences)
  }

  const addWorkExperience = () => {
    setWorkExperiences([...workExperiences, {
      company: '',
      position: '',
      startDate: '',
      endDate: '',
      description: ''
    }])
  }

  const removeWorkExperience = (index: number) => {
    if (workExperiences.length > 1) {
      setWorkExperiences(workExperiences.filter((_, i) => i !== index))
    }
  }

  // 教育经历处理函数
  const handleEducationChange = (index: number, field: string, value: string) => {
    const newEducation = [...educationExperiences]
    newEducation[index] = { ...newEducation[index], [field]: value }
    setEducationExperiences(newEducation)
  }

  const addEducationExperience = () => {
    setEducationExperiences([...educationExperiences, {
      startDate: '',
      endDate: '',
      degree: '',
      school: '',
      major: '',
      description: ''
    }])
  }

  const removeEducationExperience = (index: number) => {
    if (educationExperiences.length > 1) {
      setEducationExperiences(educationExperiences.filter((_, i) => i !== index))
    }
  }

  // 项目经历处理函数
  const addProjectExperience = () => {
    setProjectExperiences([...projectExperiences, {
      name: '',
      role: '',
      startDate: '',
      endDate: '',
      description: '',
      technologies: ''
    }])
  }

  const removeProjectExperience = (index: number) => {
    setProjectExperiences(projectExperiences.filter((_, i) => i !== index))
  }

  const handleProjectChange = (index: number, field: string, value: string) => {
    const newProjects = [...projectExperiences]
    newProjects[index] = { ...newProjects[index], [field]: value }
    setProjectExperiences(newProjects)
  }

  // 培训经历处理函数
  const addTrainingExperience = () => {
    setTrainingExperiences([...trainingExperiences, {
      name: '',
      institution: '',
      startDate: '',
      endDate: '',
      certificate: '',
      description: ''
    }])
  }

  const removeTrainingExperience = (index: number) => {
    setTrainingExperiences(trainingExperiences.filter((_, i) => i !== index))
  }

  const handleTrainingChange = (index: number, field: string, value: string) => {
    const newTraining = [...trainingExperiences]
    newTraining[index] = { ...newTraining[index], [field]: value }
    setTrainingExperiences(newTraining)
  }

  // 文件上传处理函数
  const handleFileUpload = async (fileType: 'resume' | 'coverLetter' | 'portfolio', file: File) => {
    try {
      setUploadingFiles(prev => ({ ...prev, [fileType]: true }))
      
      let uploadResponse
      if (fileType === 'resume') {
        uploadResponse = await api.uploadResume(file)
      } else {
        uploadResponse = await api.uploadFile(file)
      }
      
      setFiles(prev => ({ ...prev, [fileType]: uploadResponse.file }))
    } catch (err: any) {
      console.error(`Upload ${fileType} failed:`, err)
      setError(`上传${fileType === 'resume' ? '简历' : fileType === 'coverLetter' ? '求职信' : '作品'}失败: ${err.message}`)
    } finally {
      setUploadingFiles(prev => ({ ...prev, [fileType]: false }))
    }
  }

  const handleFileInput = (fileType: 'resume' | 'coverLetter' | 'portfolio') => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = fileType === 'portfolio' ? '*/*' : '.pdf,.doc,.docx,.txt'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        // 文件大小检查
        const maxSize = fileType === 'portfolio' ? 500 * 1024 * 1024 : 10 * 1024 * 1024 // 作品500M，其他10M
        if (file.size > maxSize) {
          setError(`文件大小超过限制${fileType === 'portfolio' ? '500M' : '10M'}`)
          return
        }
        handleFileUpload(fileType, file)
      }
    }
    input.click()
  }

  const removeFile = (fileType: 'resume' | 'coverLetter' | 'portfolio') => {
    setFiles(prev => ({ ...prev, [fileType]: null }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim() || !formData.phone.trim()) {
      setError('姓名和手机号码为必填项')
      return
    }

    if (!files.resume) {
      setError('简历文件为必填项')
      return
    }

    try {
      setLoading(true)
      setError('')
      
      // 准备完整的候选人数据
      const candidateData = {
        name: formData.name.trim(),
        phone: formData.phone.trim(),
        email: formData.email.trim() || undefined,
        currentAddress: formData.currentAddress.trim() || undefined,
        nationality: formData.nationality.trim() || undefined,
        workPermit: formData.workPermit.trim() || undefined,
        workYears: formData.workYears.trim() || undefined,
        education: formData.education.trim() || undefined,
        linkedinUrl: formData.linkedinUrl.trim() || undefined,
        personalWebsite: formData.personalWebsite.trim() || undefined,
        workExperiences: workExperiences.filter(exp => exp.company.trim() || exp.position.trim()),
        educationExperiences: educationExperiences.filter(edu => edu.school.trim() || edu.degree.trim()),
        projectExperiences: projectExperiences.filter(proj => proj.name.trim()),
        trainingExperiences: trainingExperiences.filter(train => train.name.trim()),
        attachments: {
          resume: files.resume,
          coverLetter: files.coverLetter,
          portfolio: files.portfolio
        },
        tags: [] // 可以根据需要添加标签
      }
      
      const response = await api.createCandidate(candidateData)

      onCandidateCreated(response.candidate)
      onClose()
      
      // Reset form
      setFormData({
        name: '',
        phone: '',
        email: '',
        currentAddress: '',
        nationality: '',
        workPermit: '',
        workYears: '',
        education: '',
        linkedinUrl: '',
        personalWebsite: ''
      })
      setWorkExperiences([{
        company: '',
        position: '',
        startDate: '',
        endDate: '',
        description: ''
      }])
      setEducationExperiences([{
        startDate: '',
        endDate: '',
        degree: '',
        school: '',
        major: '',
        description: ''
      }])
      setProjectExperiences([])
      setTrainingExperiences([])
      setFiles({ resume: null, coverLetter: null, portfolio: null })
    } catch (err: any) {
      setError(err.message || '创建候选人失败')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
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

        <form onSubmit={handleSubmit} className="p-6">
          {/* Info Banner */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg flex items-center">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center mr-3">
              <span className="text-white text-sm">i</span>
            </div>
            <span className="text-blue-800 text-sm">
              亲，如您已经有候选人的简历文件，请点击右边按钮上传简历，上传后系统会自动解析详细内容 (格式目前仅支持Word、txt、pdf、html)
            </span>
            <button
              type="button"
              onClick={() => handleFileInput('resume')}
              className="ml-4 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              点此上传
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          {/* Basic Information Section */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 border-b border-orange-400 pb-2">基础信息</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 姓名：
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="请输入"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  国家/地区：
                </label>
                <select
                  name="nationality"
                  value={formData.nationality}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择</option>
                  <option value="中国">中国</option>
                  <option value="美国">美国</option>
                  <option value="其他">其他</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 手机号码：
                </label>
                <div className="flex">
                  <select className="w-20 px-2 py-2 border border-r-0 border-gray-300 rounded-l-lg bg-gray-50">
                    <option value="+86">86</option>
                  </select>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    placeholder="请输入电话号码"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-r-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  邮箱地址：
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="请输入"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 现居住地：
                </label>
                <input
                  type="text"
                  name="currentAddress"
                  value={formData.currentAddress}
                  onChange={handleInputChange}
                  placeholder="请输入"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 工作年限：
                </label>
                <select
                  name="workYears"
                  value={formData.workYears}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择</option>
                  <option value="应届毕业生">应届毕业生</option>
                  <option value="1年以下">1年以下</option>
                  <option value="1-3年">1-3年</option>
                  <option value="3-5年">3-5年</option>
                  <option value="5-10年">5-10年</option>
                  <option value="10年以上">10年以上</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 最高学历：
                </label>
                <select
                  name="education"
                  value={formData.education}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择</option>
                  <option value="高中及以下">高中及以下</option>
                  <option value="大专">大专</option>
                  <option value="本科">本科</option>
                  <option value="硕士">硕士</option>
                  <option value="博士">博士</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  LinkedIn主页：
                </label>
                <input
                  type="url"
                  name="linkedinUrl"
                  value={formData.linkedinUrl}
                  onChange={handleInputChange}
                  placeholder="请输入"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  个人主页：
                </label>
                <input
                  type="url"
                  name="personalWebsite"
                  value={formData.personalWebsite}
                  onChange={handleInputChange}
                  placeholder="请输入"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Work Experience Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-orange-400 pb-2">
                工作经历 
                <span className="text-blue-600 text-sm ml-2">请从最近一份工作经历开始填写</span>
              </h3>
            </div>
            
            {workExperiences.map((experience, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-700">工作经历 {index + 1}</span>
                  {workExperiences.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeWorkExperience(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      删除
                    </button>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="text-red-500">*</span> 工作单位：
                    </label>
                    <input
                      type="text"
                      value={experience.company}
                      onChange={(e) => handleWorkExperienceChange(index, 'company', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="text-red-500">*</span> 职位：
                    </label>
                    <input
                      type="text"
                      value={experience.position}
                      onChange={(e) => handleWorkExperienceChange(index, 'position', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      时间：
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="date"
                        value={experience.startDate}
                        onChange={(e) => handleWorkExperienceChange(index, 'startDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <span>-</span>
                      <input
                        type="date"
                        value={experience.endDate}
                        onChange={(e) => handleWorkExperienceChange(index, 'endDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      职责描述：
                    </label>
                    <textarea
                      value={experience.description}
                      onChange={(e) => handleWorkExperienceChange(index, 'description', e.target.value)}
                      placeholder="请输入"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
            
            <button
              type="button"
              onClick={addWorkExperience}
              className="w-full py-2 border-2 border-dashed border-orange-300 text-orange-600 rounded-lg hover:bg-orange-50 transition-colors"
            >
              添加一条
            </button>
          </div>

          {/* Education Experience Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-orange-400 pb-2">
                教育经历
              </h3>
            </div>
            
            {educationExperiences.map((education, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-700">教育经历 {index + 1}</span>
                  {educationExperiences.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeEducationExperience(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      删除
                    </button>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      时间：
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="date"
                        value={education.startDate}
                        onChange={(e) => handleEducationChange(index, 'startDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <span>-</span>
                      <input
                        type="date"
                        value={education.endDate}
                        onChange={(e) => handleEducationChange(index, 'endDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="text-red-500">*</span> 学历：
                    </label>
                    <select
                      value={education.degree}
                      onChange={(e) => handleEducationChange(index, 'degree', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">请选择</option>
                      <option value="高中及以下">高中及以下</option>
                      <option value="大专">大专</option>
                      <option value="本科">本科</option>
                      <option value="硕士">硕士</option>
                      <option value="博士">博士</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="text-red-500">*</span> 学校：
                    </label>
                    <input
                      type="text"
                      value={education.school}
                      onChange={(e) => handleEducationChange(index, 'school', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="text-red-500">*</span> 专业：
                    </label>
                    <input
                      type="text"
                      value={education.major}
                      onChange={(e) => handleEducationChange(index, 'major', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      专业描述：
                    </label>
                    <textarea
                      value={education.description}
                      onChange={(e) => handleEducationChange(index, 'description', e.target.value)}
                      placeholder="请输入"
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
            
            <button
              type="button"
              onClick={addEducationExperience}
              className="w-full py-2 border-2 border-dashed border-orange-300 text-orange-600 rounded-lg hover:bg-orange-50 transition-colors"
            >
              添加一条
            </button>
          </div>

          {/* Project Experience Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-orange-400 pb-2">
                项目经历
              </h3>
            </div>
            
            {projectExperiences.length > 0 && projectExperiences.map((project, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-700">项目经历 {index + 1}</span>
                  <button
                    type="button"
                    onClick={() => removeProjectExperience(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    删除
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      项目名称：
                    </label>
                    <input
                      type="text"
                      value={project.name}
                      onChange={(e) => handleProjectChange(index, 'name', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      担任角色：
                    </label>
                    <input
                      type="text"
                      value={project.role}
                      onChange={(e) => handleProjectChange(index, 'role', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      时间：
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="date"
                        value={project.startDate}
                        onChange={(e) => handleProjectChange(index, 'startDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <span>-</span>
                      <input
                        type="date"
                        value={project.endDate}
                        onChange={(e) => handleProjectChange(index, 'endDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      技术栈：
                    </label>
                    <input
                      type="text"
                      value={project.technologies}
                      onChange={(e) => handleProjectChange(index, 'technologies', e.target.value)}
                      placeholder="如：React, Node.js, MongoDB"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      项目描述：
                    </label>
                    <textarea
                      value={project.description}
                      onChange={(e) => handleProjectChange(index, 'description', e.target.value)}
                      placeholder="请输入"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
            
            <button
              type="button"
              onClick={addProjectExperience}
              className="w-full py-2 border-2 border-dashed border-orange-300 text-orange-600 rounded-lg hover:bg-orange-50 transition-colors"
            >
              添加一条
            </button>
          </div>

          {/* Training Experience Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-orange-400 pb-2">
                培训经历
              </h3>
            </div>
            
            {trainingExperiences.length > 0 && trainingExperiences.map((training, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-700">培训经历 {index + 1}</span>
                  <button
                    type="button"
                    onClick={() => removeTrainingExperience(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    删除
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      培训名称：
                    </label>
                    <input
                      type="text"
                      value={training.name}
                      onChange={(e) => handleTrainingChange(index, 'name', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      培训机构：
                    </label>
                    <input
                      type="text"
                      value={training.institution}
                      onChange={(e) => handleTrainingChange(index, 'institution', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      时间：
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="date"
                        value={training.startDate}
                        onChange={(e) => handleTrainingChange(index, 'startDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <span>-</span>
                      <input
                        type="date"
                        value={training.endDate}
                        onChange={(e) => handleTrainingChange(index, 'endDate', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      获得证书：
                    </label>
                    <input
                      type="text"
                      value={training.certificate}
                      onChange={(e) => handleTrainingChange(index, 'certificate', e.target.value)}
                      placeholder="请输入"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      培训内容：
                    </label>
                    <textarea
                      value={training.description}
                      onChange={(e) => handleTrainingChange(index, 'description', e.target.value)}
                      placeholder="请输入"
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
            
            <button
              type="button"
              onClick={addTrainingExperience}
              className="w-full py-2 border-2 border-dashed border-orange-300 text-orange-600 rounded-lg hover:bg-orange-50 transition-colors"
            >
              添加一条
            </button>
          </div>

          {/* Attachment Section */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 border-b border-orange-400 pb-2">
              附件信息
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="text-red-500">*</span> 简历：
                </label>
                <div className="flex items-center space-x-4">
                  {files.resume ? (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-green-600">✅ {files.resume.originalName}</span>
                      <button
                        type="button"
                        onClick={() => removeFile('resume')}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        删除
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleFileInput('resume')}
                      disabled={uploadingFiles.resume}
                      className="px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                    >
                      {uploadingFiles.resume ? '上传中...' : '添加附件'}
                    </button>
                  )}
                  <span className="text-sm text-blue-600">
                    格式仅支持Word、txt、pdf，大小不超过10M
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  求职信：
                </label>
                <div className="flex items-center space-x-4">
                  {files.coverLetter ? (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-green-600">✅ {files.coverLetter.originalName}</span>
                      <button
                        type="button"
                        onClick={() => removeFile('coverLetter')}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        删除
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleFileInput('coverLetter')}
                      disabled={uploadingFiles.coverLetter}
                      className="px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                    >
                      {uploadingFiles.coverLetter ? '上传中...' : '添加附件'}
                    </button>
                  )}
                  <span className="text-sm text-blue-600">
                    格式仅支持Word、txt、pdf，大小不超过10M
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  作品：
                </label>
                <div className="flex items-center space-x-4">
                  {files.portfolio ? (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-green-600">✅ {files.portfolio.originalName}</span>
                      <button
                        type="button"
                        onClick={() => removeFile('portfolio')}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        删除
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleFileInput('portfolio')}
                      disabled={uploadingFiles.portfolio}
                      className="px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                    >
                      {uploadingFiles.portfolio ? '上传中...' : '添加附件'}
                    </button>
                  )}
                  <span className="text-sm text-blue-600">
                    大小不超过500M
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-4 flex items-center">
              <input
                type="checkbox"
                id="agreement"
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="agreement" className="ml-2 text-sm text-gray-700">
                我已详细阅读
                <a href="#" className="text-blue-600 hover:text-blue-800 underline">
                  阿里巴巴招聘资料通知书
                </a>
                并理解其中内容。
              </label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              disabled={loading}
            >
              取消
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? '创建中...' : '确定'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}