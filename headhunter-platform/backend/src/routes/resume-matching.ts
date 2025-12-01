import { FastifyInstance } from 'fastify';
import { resumeMatchingService } from '../services/resumeMatchingService';
import { matchingRankingService } from '../services/matchingRankingService';
import { authMiddleware } from '../middleware/auth';

// API 响应类型定义
interface ResumeUploadRequest {
  candidateId: string;
  file: Buffer;
  filename: string;
}

interface JobMatchingRequest {
  candidateId: string;
  limit?: number;
  strategy?: string;
  filters?: string[];
}

interface CandidateMatchingRequest {
  jobId: string;
  limit?: number;
  strategy?: string;
  filters?: string[];
}

interface BatchMatchingRequest {
  jobIds: string[];
  candidateIds?: string[];
  strategy?: string;
}

export async function resumeMatchingRoutes(fastify: FastifyInstance) {
  
  // ====================== 简历管理 ======================

  /**
   * 上传和解析简历
   * POST /api/v1/resume/upload
   */
  fastify.post('/api/v1/resume/upload', {
    preHandler: authMiddleware,
    schema: {
      consumes: ['multipart/form-data'],
      body: {
        type: 'object',
        properties: {
          candidateId: { type: 'string' },
          file: { isFile: true }
        },
        required: ['candidateId', 'file']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                resumeId: { type: 'string' },
                parseStatus: { type: 'string' },
                extractedFields: {
                  type: 'object',
                  properties: {
                    name: { type: 'string' },
                    email: { type: 'string' },
                    phone: { type: 'string' },
                    yearsExp: { type: 'number' },
                    skills: { type: 'array' },
                    workExperience: { type: 'array' }
                  }
                }
              }
            }
          }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const data = await request.file();
      if (!data) {
        return reply.code(400).send({
          success: false,
          message: '未检测到上传文件'
        });
      }

      const buffer = await data.toBuffer();
      const candidateId = data.fields.candidateId?.value as string;

      if (!candidateId) {
        return reply.code(400).send({
          success: false,
          message: '候选人ID不能为空'
        });
      }

      console.log(`📄 开始处理候选人 ${candidateId} 的简历...`);

      // 1. 保存文件并解析
      const resumeResult = await resumeParsingService.parseResume(
        candidateId,
        buffer,
        data.filename
      );

      reply.send({
        success: true,
        data: resumeResult,
        message: '简历上传和解析成功'
      });

    } catch (error) {
      console.error('简历上传失败:', error);
      reply.code(500).send({
        success: false,
        message: '简历上传失败',
        error: error instanceof Error ? error.message : '未知错误'
      });
    }
  });

  /**
   * 获取简历解析状态
   * GET /api/v1/resume/:candidateId/status
   */
  fastify.get('/api/v1/resume/:candidateId/status', {
    preHandler: authMiddleware,
    schema: {
      params: {
        type: 'object',
        properties: {
          candidateId: { type: 'string' }
        },
        required: ['candidateId']
      }
    }
  }, async (request, reply) => {
    try {
      const { candidateId } = request.params as { candidateId: string };
      
      const resumeStatus = await resumeParsingService.getResumeStatus(candidateId);
      
      reply.send({
        success: true,
        data: resumeStatus
      });

    } catch (error) {
      console.error('获取简历状态失败:', error);
      reply.code(500).send({
        success: false,
        message: '获取简历状态失败'
      });
    }
  });

  // ====================== 智能匹配 ======================

  /**
   * 为候选人匹配岗位
   * POST /api/v1/matching/jobs-for-candidate
   */
  fastify.post('/api/v1/matching/jobs-for-candidate', {
    preHandler: authMiddleware,
    schema: {
      body: {
        type: 'object',
        properties: {
          candidateId: { type: 'string' },
          limit: { type: 'number', minimum: 1, maximum: 100, default: 20 },
          strategy: { 
            type: 'string', 
            enum: ['overall', 'skillFirst', 'experienceFirst', 'salaryFirst', 'locationFirst'],
            default: 'overall'
          },
          filters: {
            type: 'array',
            items: { type: 'string' }
          }
        },
        required: ['candidateId']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                candidateId: { type: 'string' },
                totalMatches: { type: 'number' },
                processingTime: { type: 'number' },
                matches: {
                  type: 'array',
                  items: {
                    type: 'object',
                    properties: {
                      jobId: { type: 'string' },
                      jobTitle: { type: 'string' },
                      companyName: { type: 'string' },
                      overallScore: { type: 'number' },
                      finalScore: { type: 'number' },
                      priority: { type: 'string' },
                      recommendationStrength: { type: 'number' },
                      dimensionScores: {
                        type: 'object',
                        properties: {
                          skills: { type: 'number' },
                          experience: { type: 'number' },
                          industry: { type: 'number' },
                          location: { type: 'number' },
                          salary: { type: 'number' },
                          education: { type: 'number' }
                        }
                      },
                      matchDetails: {
                        type: 'object',
                        properties: {
                          matchedSkills: { type: 'array' },
                          missingSkills: { type: 'array' },
                          matchReasons: { type: 'array' },
                          salaryFit: { type: 'object' }
                        }
                      },
                      businessTags: { type: 'array' },
                      rankingReasons: { type: 'array' }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { candidateId, limit = 20, strategy = 'overall', filters } = request.body as JobMatchingRequest;
      const startTime = Date.now();

      console.log(`🎯 开始为候选人 ${candidateId} 匹配岗位 (策略: ${strategy})`);

      // 1. 执行匹配算法
      const matchingResults = await resumeMatchingService.findMatchingJobs(
        candidateId,
        limit,
        this.getWeightsForStrategy(strategy)
      );

      // 2. 智能排序
      const rankedResults = await matchingRankingService.rankMatchingResults(
        matchingResults,
        {
          primaryStrategy: matchingRankingService.strategies[strategy],
          filters: filters?.map(f => matchingRankingService.filters[f]).filter(Boolean)
        }
      );

      // 3. 获取岗位详细信息
      const enhancedResults = await this.enhanceJobDetails(rankedResults);

      const processingTime = Date.now() - startTime;

      reply.send({
        success: true,
        data: {
          candidateId,
          totalMatches: enhancedResults.length,
          processingTime,
          matches: enhancedResults
        },
        message: `成功匹配到 ${enhancedResults.length} 个岗位`
      });

    } catch (error) {
      console.error('岗位匹配失败:', error);
      reply.code(500).send({
        success: false,
        message: '岗位匹配失败',
        error: error instanceof Error ? error.message : '未知错误'
      });
    }
  });

  /**
   * 为岗位匹配候选人
   * POST /api/v1/matching/candidates-for-job
   */
  fastify.post('/api/v1/matching/candidates-for-job', {
    preHandler: authMiddleware,
    schema: {
      body: {
        type: 'object',
        properties: {
          jobId: { type: 'string' },
          limit: { type: 'number', minimum: 1, maximum: 200, default: 50 },
          strategy: { 
            type: 'string', 
            enum: ['overall', 'skillFirst', 'experienceFirst', 'confidenceFirst'],
            default: 'overall'
          },
          filters: {
            type: 'array',
            items: { type: 'string' }
          }
        },
        required: ['jobId']
      }
    }
  }, async (request, reply) => {
    try {
      const { jobId, limit = 50, strategy = 'overall', filters } = request.body as CandidateMatchingRequest;
      const startTime = Date.now();

      console.log(`🎯 开始为岗位 ${jobId} 匹配候选人 (策略: ${strategy})`);

      // 1. 执行匹配算法
      const matchingResults = await resumeMatchingService.findMatchingCandidates(
        jobId,
        limit,
        this.getWeightsForStrategy(strategy)
      );

      // 2. 智能排序
      const rankedResults = await matchingRankingService.rankMatchingResults(
        matchingResults,
        {
          primaryStrategy: matchingRankingService.strategies[strategy],
          filters: filters?.map(f => matchingRankingService.filters[f]).filter(Boolean)
        }
      );

      // 3. 获取候选人详细信息
      const enhancedResults = await this.enhanceCandidateDetails(rankedResults);

      const processingTime = Date.now() - startTime;

      reply.send({
        success: true,
        data: {
          jobId,
          totalMatches: enhancedResults.length,
          processingTime,
          matches: enhancedResults
        },
        message: `成功匹配到 ${enhancedResults.length} 个候选人`
      });

    } catch (error) {
      console.error('候选人匹配失败:', error);
      reply.code(500).send({
        success: false,
        message: '候选人匹配失败',
        error: error instanceof Error ? error.message : '未知错误'
      });
    }
  });

  /**
   * 批量匹配分析
   * POST /api/v1/matching/batch-analysis
   */
  fastify.post('/api/v1/matching/batch-analysis', {
    preHandler: authMiddleware,
    schema: {
      body: {
        type: 'object',
        properties: {
          jobIds: {
            type: 'array',
            items: { type: 'string' },
            minItems: 1,
            maxItems: 10
          },
          candidateIds: {
            type: 'array',
            items: { type: 'string' },
            maxItems: 100
          },
          strategy: { type: 'string', default: 'overall' }
        },
        required: ['jobIds']
      }
    }
  }, async (request, reply) => {
    try {
      const { jobIds, candidateIds, strategy = 'overall' } = request.body as BatchMatchingRequest;
      const startTime = Date.now();

      console.log(`📊 开始批量匹配分析: ${jobIds.length} 个岗位`);

      const batchResults = await this.performBatchMatching(jobIds, candidateIds, strategy);
      const processingTime = Date.now() - startTime;

      reply.send({
        success: true,
        data: {
          totalJobs: jobIds.length,
          totalCandidates: candidateIds?.length || 'all',
          processingTime,
          results: batchResults
        },
        message: '批量匹配分析完成'
      });

    } catch (error) {
      console.error('批量匹配失败:', error);
      reply.code(500).send({
        success: false,
        message: '批量匹配失败',
        error: error instanceof Error ? error.message : '未知错误'
      });
    }
  });

  // ====================== 匹配分析 ======================

  /**
   * 获取匹配详情解释
   * GET /api/v1/matching/explanation/:candidateId/:jobId
   */
  fastify.get('/api/v1/matching/explanation/:candidateId/:jobId', {
    preHandler: authMiddleware,
    schema: {
      params: {
        type: 'object',
        properties: {
          candidateId: { type: 'string' },
          jobId: { type: 'string' }
        },
        required: ['candidateId', 'jobId']
      }
    }
  }, async (request, reply) => {
    try {
      const { candidateId, jobId } = request.params as { candidateId: string; jobId: string };

      console.log(`📝 生成匹配解释: 候选人 ${candidateId} vs 岗位 ${jobId}`);

      const explanation = await this.generateDetailedExplanation(candidateId, jobId);

      reply.send({
        success: true,
        data: explanation
      });

    } catch (error) {
      console.error('生成匹配解释失败:', error);
      reply.code(500).send({
        success: false,
        message: '生成匹配解释失败'
      });
    }
  });

  /**
   * 获取匹配统计信息
   * GET /api/v1/matching/statistics
   */
  fastify.get('/api/v1/matching/statistics', {
    preHandler: authMiddleware,
    schema: {
      querystring: {
        type: 'object',
        properties: {
          period: { type: 'string', enum: ['day', 'week', 'month'], default: 'week' },
          jobId: { type: 'string' },
          candidateId: { type: 'string' }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { period = 'week', jobId, candidateId } = request.query as any;

      console.log(`📈 获取匹配统计信息 (周期: ${period})`);

      const statistics = await this.getMatchingStatistics(period, jobId, candidateId);

      reply.send({
        success: true,
        data: statistics
      });

    } catch (error) {
      console.error('获取统计信息失败:', error);
      reply.code(500).send({
        success: false,
        message: '获取统计信息失败'
      });
    }
  });

  // ====================== 辅助方法 ======================

  /**
   * 根据策略获取权重配置
   */
  function getWeightsForStrategy(strategy: string) {
    const strategies = {
      skillFirst: { skills: 0.5, experience: 0.2, industry: 0.1, location: 0.1, salary: 0.05, education: 0.05 },
      experienceFirst: { skills: 0.3, experience: 0.4, industry: 0.15, location: 0.05, salary: 0.05, education: 0.05 },
      salaryFirst: { skills: 0.25, experience: 0.25, industry: 0.1, location: 0.05, salary: 0.3, education: 0.05 },
      locationFirst: { skills: 0.3, experience: 0.2, industry: 0.1, location: 0.3, salary: 0.05, education: 0.05 },
      overall: { skills: 0.35, experience: 0.25, industry: 0.15, location: 0.1, salary: 0.1, education: 0.05 }
    };
    
    return strategies[strategy as keyof typeof strategies] || strategies.overall;
  }

  /**
   * 增强岗位详细信息
   */
  async function enhanceJobDetails(results: any[]) {
    // 批量获取岗位信息，减少数据库查询
    const jobIds = results.map(r => r.jobId);
    const jobs = await prisma.job.findMany({
      where: { id: { in: jobIds } },
      include: { companyClient: true }
    });

    const jobMap = new Map(jobs.map(job => [job.id, job]));

    return results.map(result => {
      const job = jobMap.get(result.jobId);
      return {
        ...result,
        jobTitle: job?.title,
        companyName: job?.companyClient.name,
        jobLocation: job?.location,
        salaryRange: job?.salaryMin && job?.salaryMax ? 
          `${job.salaryMin}-${job.salaryMax}` : null
      };
    });
  }

  /**
   * 增强候选人详细信息
   */
  async function enhanceCandidateDetails(results: any[]) {
    // 类似的逻辑增强候选人信息
    const candidateIds = results.map(r => r.candidateId);
    const candidates = await prisma.candidate.findMany({
      where: { id: { in: candidateIds } },
      include: { 
        resume: {
          include: {
            workExperience: true,
            skills: true
          }
        }
      }
    });

    const candidateMap = new Map(candidates.map(c => [c.id, c]));

    return results.map(result => {
      const candidate = candidateMap.get(result.candidateId);
      return {
        ...result,
        candidateName: candidate?.name,
        candidateEmail: candidate?.email,
        candidatePhone: candidate?.phone,
        currentTitle: candidate?.resume?.currentTitle,
        yearsExperience: candidate?.resume?.yearsExp
      };
    });
  }

  /**
   * 执行批量匹配
   */
  async function performBatchMatching(jobIds: string[], candidateIds?: string[], strategy: string) {
    const results = new Map();

    for (const jobId of jobIds) {
      const jobMatches = await resumeMatchingService.findMatchingCandidates(
        jobId,
        candidateIds ? candidateIds.length : 50,
        getWeightsForStrategy(strategy)
      );

      // 如果指定了候选人ID，则过滤结果
      const filteredMatches = candidateIds ? 
        jobMatches.filter(match => candidateIds.includes(match.candidateId)) :
        jobMatches;

      const rankedMatches = await matchingRankingService.rankMatchingResults(filteredMatches);
      results.set(jobId, rankedMatches.slice(0, 10)); // 每个岗位返回前10个
    }

    return Object.fromEntries(results);
  }

  /**
   * 生成详细匹配解释
   */
  async function generateDetailedExplanation(candidateId: string, jobId: string) {
    // 重新计算这一对的详细匹配信息
    const detailedMatch = await resumeMatchingService.calculateDetailedMatch(candidateId, jobId);
    const explanation = matchingRankingService.generateRecommendationExplanation(detailedMatch);

    return {
      overallScore: detailedMatch.overallScore,
      explanation,
      dimensionBreakdown: detailedMatch.dimensionScores,
      skillsAnalysis: {
        matched: detailedMatch.matchDetails.matchedSkills,
        missing: detailedMatch.matchDetails.missingSkills,
        recommendations: this.generateSkillRecommendations(detailedMatch.matchDetails.missingSkills)
      },
      experienceAnalysis: detailedMatch.matchDetails.experienceMatch,
      salaryAnalysis: detailedMatch.matchDetails.salaryFit,
      improvementSuggestions: this.generateImprovementSuggestions(detailedMatch)
    };
  }

  /**
   * 获取匹配统计信息
   */
  async function getMatchingStatistics(period: string, jobId?: string, candidateId?: string) {
    // 从数据库查询统计信息
    const stats = await prisma.jobMatchingScore.aggregate({
      _avg: { overallScore: true },
      _max: { overallScore: true },
      _min: { overallScore: true },
      _count: true,
      where: {
        ...(jobId && { jobId }),
        ...(candidateId && { resumeId: candidateId }),
        calculatedAt: {
          gte: this.getPeriodStartDate(period)
        }
      }
    });

    return {
      averageScore: stats._avg.overallScore,
      maxScore: stats._max.overallScore,
      minScore: stats._min.overallScore,
      totalMatches: stats._count,
      period,
      generatedAt: new Date().toISOString()
    };
  }

  function getPeriodStartDate(period: string): Date {
    const now = new Date();
    switch (period) {
      case 'day':
        return new Date(now.getTime() - 24 * 60 * 60 * 1000);
      case 'week':
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      case 'month':
        return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      default:
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    }
  }
}