'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Job {
  id: string;
  title: string;
  company: string;
  industry: string;
  location: string;
  salaryRange: { min: number; max: number };
  description: string;
  requirements: string;
}

interface Candidate {
  id: string;
  name: string;
  email: string;
  phone: string;
  tags: string[];
  hasResume: boolean;
}

interface JobMatch {
  job: Job;
  scores: {
    skills: number;
    experience: number;
    industry: number;
    location: number;
    salary: number;
    education: number;
    overall: number;
  };
  confidence: number;
  ranking: number;
  matchReasons: string[];
}

interface CandidateMatch {
  resume: {
    id: string;
    candidateId: string;
    filename: string;
    parsedData: {
      personalInfo: {
        name: string;
        email: string;
        phone: string;
        location: string;
      };
      skills: Array<{
        name: string;
        level: string;
        yearsOfExperience: number;
      }>;
      workExperience: Array<{
        company: string;
        position: string;
        startDate: Date;
        endDate: Date | null;
        description: string;
        industry: string;
      }>;
      summary: string;
    };
    confidence: number;
  };
  scores: {
    skills: number;
    experience: number;
    industry: number;
    location: number;
    salary: number;
    education: number;
    overall: number;
  };
  confidence: number;
  ranking: number;
  matchReasons: string[];
}

export default function ResumeMatchingSimple() {
  const [activeTab, setActiveTab] = useState<'jobs-for-candidate' | 'candidates-for-job'>('jobs-for-candidate');
  const [availableJobs, setAvailableJobs] = useState<Job[]>([]);
  const [availableCandidates, setAvailableCandidates] = useState<Candidate[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>('');
  const [jobMatches, setJobMatches] = useState<JobMatch[]>([]);
  const [candidateMatches, setCandidateMatches] = useState<CandidateMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  // Load available jobs and candidates on component mount
  useEffect(() => {
    loadAvailableData();
  }, []);

  const loadAvailableData = async () => {
    try {
      const [jobsResponse, candidatesResponse] = await Promise.all([
        api.getAvailableJobs(),
        api.getAvailableCandidates()
      ]);

      if (jobsResponse.success) {
        setAvailableJobs(jobsResponse.data);
        if (jobsResponse.data.length > 0) {
          setSelectedJobId(jobsResponse.data[0].id);
        }
      }

      if (candidatesResponse.success) {
        setAvailableCandidates(candidatesResponse.data);
        if (candidatesResponse.data.length > 0) {
          setSelectedCandidateId(candidatesResponse.data[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading available data:', error);
      setError('Failed to load available jobs and candidates');
    }
  };

  const findMatchingJobs = async () => {
    if (!selectedCandidateId) {
      setError('Please select a candidate');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.findMatchingJobs(selectedCandidateId, {
        thresholds: { maxResults: 10, minimumScore: 0.5 }
      });

      if (response.success) {
        setJobMatches(response.data);
      } else {
        setError('Failed to find matching jobs');
      }
    } catch (error) {
      console.error('Error finding matching jobs:', error);
      setError('Failed to find matching jobs');
    } finally {
      setLoading(false);
    }
  };

  const findMatchingCandidates = async () => {
    if (!selectedJobId) {
      setError('Please select a job');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.findMatchingCandidates(selectedJobId, {
        thresholds: { maxResults: 10, minimumScore: 0.5 }
      });

      if (response.success) {
        setCandidateMatches(response.data);
      } else {
        setError('Failed to find matching candidates');
      }
    } catch (error) {
      console.error('Error finding matching candidates:', error);
      setError('Failed to find matching candidates');
    } finally {
      setLoading(false);
    }
  };

  const formatSalary = (amount: number) => {
    return `¥${(amount / 10000).toFixed(0)}万`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">简历匹配系统</h1>
        <p className="text-gray-600">使用AI算法进行智能简历匹配，提高招聘效率</p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('jobs-for-candidate')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'jobs-for-candidate'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              为候选人找职位
            </button>
            <button
              onClick={() => setActiveTab('candidates-for-job')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'candidates-for-job'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              为职位找候选人
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'jobs-for-candidate' && (
            <div className="space-y-6">
              {/* Candidate Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择候选人
                </label>
                <select
                  value={selectedCandidateId}
                  onChange={(e) => setSelectedCandidateId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择候选人</option>
                  {availableCandidates.map((candidate) => (
                    <option key={candidate.id} value={candidate.id}>
                      {candidate.name} ({candidate.email})
                    </option>
                  ))}
                </select>
              </div>

              {/* Search Button */}
              <button
                onClick={findMatchingJobs}
                disabled={loading || !selectedCandidateId}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '匹配中...' : '查找匹配职位'}
              </button>

              {/* Job Matches Results */}
              {jobMatches.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">匹配结果 ({jobMatches.length})</h3>
                  {jobMatches.map((match, index) => (
                    <div key={match.job.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="text-lg font-medium text-gray-900">{match.job.title}</h4>
                          <p className="text-gray-600">{match.job.company} • {match.job.location}</p>
                          <p className="text-gray-500 text-sm">
                            {formatSalary(match.job.salaryRange.min)} - {formatSalary(match.job.salaryRange.max)}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(match.scores.overall)}`}>
                            匹配度: {(match.scores.overall * 100).toFixed(0)}%
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            置信度: {(match.confidence * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>

                      {/* Score Details */}
                      <div className="grid grid-cols-3 gap-4 mb-3">
                        <div className="text-sm">
                          <span className="text-gray-500">技能匹配:</span>
                          <span className="ml-2 font-medium">{(match.scores.skills * 100).toFixed(0)}%</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-500">经验匹配:</span>
                          <span className="ml-2 font-medium">{(match.scores.experience * 100).toFixed(0)}%</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-500">地域匹配:</span>
                          <span className="ml-2 font-medium">{(match.scores.location * 100).toFixed(0)}%</span>
                        </div>
                      </div>

                      {/* Match Reasons */}
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">匹配理由:</p>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {match.matchReasons.map((reason, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="text-green-500 mr-2">•</span>
                              {reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'candidates-for-job' && (
            <div className="space-y-6">
              {/* Job Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择职位
                </label>
                <select
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择职位</option>
                  {availableJobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title} - {job.company}
                    </option>
                  ))}
                </select>
              </div>

              {/* Search Button */}
              <button
                onClick={findMatchingCandidates}
                disabled={loading || !selectedJobId}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '匹配中...' : '查找匹配候选人'}
              </button>

              {/* Candidate Matches Results */}
              {candidateMatches.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">匹配结果 ({candidateMatches.length})</h3>
                  {candidateMatches.map((match, index) => (
                    <div key={match.resume.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="text-lg font-medium text-gray-900">{match.resume.parsedData.personalInfo.name}</h4>
                          <p className="text-gray-600">{match.resume.parsedData.personalInfo.email}</p>
                          <p className="text-gray-500 text-sm">{match.resume.parsedData.personalInfo.location}</p>
                        </div>
                        <div className="text-right">
                          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(match.scores.overall)}`}>
                            匹配度: {(match.scores.overall * 100).toFixed(0)}%
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            置信度: {(match.confidence * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>

                      {/* Skills */}
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 mb-1">技能:</p>
                        <div className="flex flex-wrap gap-2">
                          {match.resume.parsedData.skills.map((skill, idx) => (
                            <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              {skill.name} ({skill.level})
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Score Details */}
                      <div className="grid grid-cols-3 gap-4 mb-3">
                        <div className="text-sm">
                          <span className="text-gray-500">技能匹配:</span>
                          <span className="ml-2 font-medium">{(match.scores.skills * 100).toFixed(0)}%</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-500">经验匹配:</span>
                          <span className="ml-2 font-medium">{(match.scores.experience * 100).toFixed(0)}%</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-500">行业匹配:</span>
                          <span className="ml-2 font-medium">{(match.scores.industry * 100).toFixed(0)}%</span>
                        </div>
                      </div>

                      {/* Match Reasons */}
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">匹配理由:</p>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {match.matchReasons.map((reason, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="text-green-500 mr-2">•</span>
                              {reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="text-red-400">⚠️</div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">错误</h3>
                  <div className="mt-2 text-sm text-red-700">{error}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}