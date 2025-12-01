import { describe, beforeAll, afterAll, beforeEach, afterEach, it, expect, jest } from '@jest/globals';
import { build } from '../helper';
import { FastifyInstance } from 'fastify';
import { PrismaClient } from '@prisma/client';
import FormData from 'form-data';
import fs from 'fs';
import path from 'path';

describe('Resume Matching API Routes', () => {
  let app: FastifyInstance;
  let prisma: PrismaClient;

  beforeAll(async () => {
    app = await build({ logger: false });
    prisma = new PrismaClient();
    await app.ready();
  });

  afterAll(async () => {
    await app.close();
    await prisma.$disconnect();
  });

  beforeEach(async () => {
    // 清理测试数据
    await prisma.$transaction([
      prisma.jobMatchingScore.deleteMany(),
      prisma.candidateSubmission.deleteMany(),
      prisma.candidate.deleteMany(),
      prisma.job.deleteMany(),
      prisma.resume.deleteMany()
    ]);
  });

  describe('POST /api/v1/resume/upload', () => {
    it('应该成功上传和解析简历', async () => {
      // 创建测试候选人
      const candidate = await prisma.candidate.create({
        data: {
          name: '张三',
          phone: '13800138000',
          email: 'zhangsan@example.com',
          maintainerId: 'test-user-id'
        }
      });

      // 创建模拟简历文件
      const form = new FormData();
      const mockResumeContent = Buffer.from('Test resume content');
      form.append('candidateId', candidate.id);
      form.append('file', mockResumeContent, {
        filename: 'resume.pdf',
        contentType: 'application/pdf'
      });

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/resume/upload',
        headers: {
          ...form.getHeaders(),
          authorization: 'Bearer mock-token'
        },
        payload: form.getBuffer()
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      expect(data.data.resumeId).toBeDefined();
      expect(data.data.parseStatus).toBeDefined();
    });

    it('应该拒绝无效的文件上传', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/resume/upload',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          candidateId: 'invalid-id'
        }
      });

      expect(response.statusCode).toBe(400);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(false);
      expect(data.message).toContain('未检测到上传文件');
    });

    it('应该要求候选人ID', async () => {
      const form = new FormData();
      form.append('file', Buffer.from('test'), 'resume.pdf');

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/resume/upload',
        headers: {
          ...form.getHeaders(),
          authorization: 'Bearer mock-token'
        },
        payload: form.getBuffer()
      });

      expect(response.statusCode).toBe(400);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(false);
      expect(data.message).toContain('候选人ID不能为空');
    });
  });

  describe('GET /api/v1/resume/:candidateId/status', () => {
    it('应该返回简历解析状态', async () => {
      // 创建测试数据
      const candidate = await prisma.candidate.create({
        data: {
          name: '李四',
          phone: '13800138001',
          maintainerId: 'test-user-id'
        }
      });

      const resume = await prisma.resume.create({
        data: {
          candidateId: candidate.id,
          parseStatus: 'completed',
          fullName: '李四',
          email: 'lisi@example.com',
          yearsExp: 3
        }
      });

      const response = await app.inject({
        method: 'GET',
        url: `/api/v1/resume/${candidate.id}/status`,
        headers: {
          authorization: 'Bearer mock-token'
        }
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      expect(data.data.parseStatus).toBe('completed');
    });

    it('应该处理不存在的候选人', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/resume/non-existent-id/status',
        headers: {
          authorization: 'Bearer mock-token'
        }
      });

      expect(response.statusCode).toBe(404);
    });
  });

  describe('POST /api/v1/matching/jobs-for-candidate', () => {
    let candidate: any;
    let jobs: any[];

    beforeEach(async () => {
      // 创建测试候选人和简历
      candidate = await prisma.candidate.create({
        data: {
          name: '王五',
          phone: '13800138002',
          maintainerId: 'test-user-id'
        }
      });

      await prisma.resume.create({
        data: {
          candidateId: candidate.id,
          parseStatus: 'completed',
          fullName: '王五',
          currentTitle: 'Java开发工程师',
          yearsExp: 5,
          expectedSalary: 20000,
          location: '北京市'
        }
      });

      // 创建技能数据
      await prisma.resumeSkill.createMany({
        data: [
          {
            resumeId: candidate.id,
            name: 'Java',
            category: 'programming_language',
            level: 'advanced',
            yearsUsed: 5,
            isKeySkill: true
          },
          {
            resumeId: candidate.id,
            name: 'Spring',
            category: 'framework',
            level: 'intermediate',
            yearsUsed: 3,
            isKeySkill: false
          }
        ]
      });

      // 创建测试岗位
      const companyClient = await prisma.companyClient.create({
        data: {
          name: '测试公司',
          contactName: '联系人',
          contactPhone: '13800138888',
          partnerCompanyId: 'company-id',
          maintainerId: 'user-id'
        }
      });

      jobs = await Promise.all([
        prisma.job.create({
          data: {
            title: 'Java高级开发工程师',
            industry: '互联网',
            location: '北京市',
            salaryMin: 18000,
            salaryMax: 25000,
            description: 'Java后端开发',
            requirements: '要求3年以上Java开发经验，熟悉Spring框架',
            status: 'open',
            publisherSharePct: 50,
            referrerSharePct: 40,
            platformSharePct: 10,
            publisherId: 'publisher-id',
            companyClientId: companyClient.id
          }
        }),
        prisma.job.create({
          data: {
            title: 'Python开发工程师',
            industry: '人工智能',
            location: '上海市',
            salaryMin: 15000,
            salaryMax: 20000,
            description: 'Python后端开发',
            requirements: '要求Python开发经验',
            status: 'open',
            publisherSharePct: 50,
            referrerSharePct: 40,
            platformSharePct: 10,
            publisherId: 'publisher-id',
            companyClientId: companyClient.id
          }
        })
      ]);
    });

    it('应该成功匹配候选人的岗位', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          candidateId: candidate.id,
          limit: 10,
          strategy: 'overall'
        }
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      expect(data.data.candidateId).toBe(candidate.id);
      expect(data.data.matches).toBeInstanceOf(Array);
      expect(data.data.totalMatches).toBeGreaterThan(0);
      expect(data.data.processingTime).toBeGreaterThan(0);

      // 验证匹配结果结构
      const firstMatch = data.data.matches[0];
      expect(firstMatch).toHaveProperty('jobId');
      expect(firstMatch).toHaveProperty('overallScore');
      expect(firstMatch).toHaveProperty('dimensionScores');
      expect(firstMatch).toHaveProperty('matchDetails');
      expect(firstMatch).toHaveProperty('priority');
    });

    it('应该支持不同的匹配策略', async () => {
      const strategies = ['overall', 'skillFirst', 'experienceFirst', 'salaryFirst'];

      for (const strategy of strategies) {
        const response = await app.inject({
          method: 'POST',
          url: '/api/v1/matching/jobs-for-candidate',
          headers: {
            'content-type': 'application/json',
            authorization: 'Bearer mock-token'
          },
          payload: {
            candidateId: candidate.id,
            strategy,
            limit: 5
          }
        });

        expect(response.statusCode).toBe(200);
        const data = JSON.parse(response.payload);
        expect(data.success).toBe(true);
      }
    });

    it('应该支持过滤器', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          candidateId: candidate.id,
          filters: ['minimumScore', 'minimumSkillMatch'],
          limit: 10
        }
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      
      // 验证过滤器生效
      data.data.matches.forEach((match: any) => {
        expect(match.overallScore).toBeGreaterThanOrEqual(30);
        expect(match.dimensionScores.skills).toBeGreaterThanOrEqual(40);
      });
    });

    it('应该验证必需参数', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          // 缺少 candidateId
          limit: 10
        }
      });

      expect(response.statusCode).toBe(400);
    });

    it('应该限制查询数量', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          candidateId: candidate.id,
          limit: 999 // 超过最大限制
        }
      });

      expect(response.statusCode).toBe(400);
    });
  });

  describe('POST /api/v1/matching/candidates-for-job', () => {
    let job: any;
    let candidates: any[];

    beforeEach(async () => {
      // 创建测试岗位
      const companyClient = await prisma.companyClient.create({
        data: {
          name: '测试公司2',
          contactName: '联系人2',
          contactPhone: '13800138999',
          partnerCompanyId: 'company-id',
          maintainerId: 'user-id'
        }
      });

      job = await prisma.job.create({
        data: {
          title: 'React前端工程师',
          industry: '互联网',
          location: '深圳市',
          salaryMin: 15000,
          salaryMax: 22000,
          description: 'React前端开发',
          requirements: '要求2年以上React开发经验，熟悉JavaScript',
          status: 'open',
          publisherSharePct: 50,
          referrerSharePct: 40,
          platformSharePct: 10,
          publisherId: 'publisher-id',
          companyClientId: companyClient.id
        }
      });

      // 创建测试候选人
      candidates = await Promise.all([
        prisma.candidate.create({
          data: {
            name: '候选人A',
            phone: '13800000001',
            maintainerId: 'test-user-id'
          }
        }),
        prisma.candidate.create({
          data: {
            name: '候选人B',
            phone: '13800000002',
            maintainerId: 'test-user-id'
          }
        })
      ]);

      // 创建简历数据
      for (const candidate of candidates) {
        await prisma.resume.create({
          data: {
            candidateId: candidate.id,
            parseStatus: 'completed',
            fullName: candidate.name,
            currentTitle: 'Frontend Developer',
            yearsExp: 3,
            expectedSalary: 18000,
            location: '深圳市'
          }
        });
      }
    });

    it('应该成功匹配岗位的候选人', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/candidates-for-job',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          jobId: job.id,
          limit: 20,
          strategy: 'overall'
        }
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      expect(data.data.jobId).toBe(job.id);
      expect(data.data.matches).toBeInstanceOf(Array);
      expect(data.data.totalMatches).toBeGreaterThan(0);

      // 验证候选人信息
      const firstMatch = data.data.matches[0];
      expect(firstMatch).toHaveProperty('candidateName');
      expect(firstMatch).toHaveProperty('candidateEmail');
      expect(firstMatch).toHaveProperty('currentTitle');
    });

    it('应该处理不存在的岗位', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/candidates-for-job',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          jobId: 'non-existent-job-id'
        }
      });

      expect(response.statusCode).toBe(404);
    });
  });

  describe('POST /api/v1/matching/batch-analysis', () => {
    let jobs: any[];

    beforeEach(async () => {
      const companyClient = await prisma.companyClient.create({
        data: {
          name: '批量测试公司',
          contactName: '联系人',
          contactPhone: '13800111111',
          partnerCompanyId: 'company-id',
          maintainerId: 'user-id'
        }
      });

      jobs = await Promise.all([
        prisma.job.create({
          data: {
            title: '批量测试岗位1',
            industry: '互联网',
            location: '北京',
            salaryMin: 10000,
            salaryMax: 15000,
            description: '测试描述1',
            requirements: '测试要求1',
            status: 'open',
            publisherSharePct: 50,
            referrerSharePct: 40,
            platformSharePct: 10,
            publisherId: 'publisher-id',
            companyClientId: companyClient.id
          }
        }),
        prisma.job.create({
          data: {
            title: '批量测试岗位2',
            industry: '金融',
            location: '上海',
            salaryMin: 12000,
            salaryMax: 18000,
            description: '测试描述2',
            requirements: '测试要求2',
            status: 'open',
            publisherSharePct: 50,
            referrerSharePct: 40,
            platformSharePct: 10,
            publisherId: 'publisher-id',
            companyClientId: companyClient.id
          }
        })
      ]);
    });

    it('应该成功执行批量匹配分析', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/batch-analysis',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          jobIds: jobs.map(job => job.id),
          strategy: 'overall'
        }
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      expect(data.data.totalJobs).toBe(jobs.length);
      expect(data.data.results).toBeDefined();
      expect(data.data.processingTime).toBeGreaterThan(0);
    });

    it('应该限制批量查询的岗位数量', async () => {
      const tooManyJobs = Array.from({ length: 15 }, (_, i) => `job-${i}`);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/batch-analysis',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          jobIds: tooManyJobs
        }
      });

      expect(response.statusCode).toBe(400);
    });
  });

  describe('GET /api/v1/matching/explanation/:candidateId/:jobId', () => {
    let candidate: any;
    let job: any;

    beforeEach(async () => {
      // 创建测试数据
      candidate = await prisma.candidate.create({
        data: {
          name: '解释测试候选人',
          phone: '13800222222',
          maintainerId: 'test-user-id'
        }
      });

      const companyClient = await prisma.companyClient.create({
        data: {
          name: '解释测试公司',
          contactName: '联系人',
          contactPhone: '13800333333',
          partnerCompanyId: 'company-id',
          maintainerId: 'user-id'
        }
      });

      job = await prisma.job.create({
        data: {
          title: '解释测试岗位',
          industry: '测试',
          location: '测试市',
          salaryMin: 10000,
          salaryMax: 15000,
          description: '测试描述',
          requirements: '测试要求',
          status: 'open',
          publisherSharePct: 50,
          referrerSharePct: 40,
          platformSharePct: 10,
          publisherId: 'publisher-id',
          companyClientId: companyClient.id
        }
      });

      await prisma.resume.create({
        data: {
          candidateId: candidate.id,
          parseStatus: 'completed',
          fullName: candidate.name
        }
      });
    });

    it('应该返回详细的匹配解释', async () => {
      const response = await app.inject({
        method: 'GET',
        url: `/api/v1/matching/explanation/${candidate.id}/${job.id}`,
        headers: {
          authorization: 'Bearer mock-token'
        }
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      expect(data.data).toHaveProperty('overallScore');
      expect(data.data).toHaveProperty('explanation');
      expect(data.data).toHaveProperty('dimensionBreakdown');
      expect(data.data).toHaveProperty('skillsAnalysis');
      expect(data.data).toHaveProperty('improvementSuggestions');
    });
  });

  describe('GET /api/v1/matching/statistics', () => {
    it('应该返回匹配统计信息', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/matching/statistics',
        headers: {
          authorization: 'Bearer mock-token'
        },
        query: {
          period: 'week'
        }
      });

      expect(response.statusCode).toBe(200);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(true);
      expect(data.data).toHaveProperty('averageScore');
      expect(data.data).toHaveProperty('totalMatches');
      expect(data.data).toHaveProperty('period');
      expect(data.data.period).toBe('week');
    });

    it('应该支持不同的统计周期', async () => {
      const periods = ['day', 'week', 'month'];

      for (const period of periods) {
        const response = await app.inject({
          method: 'GET',
          url: '/api/v1/matching/statistics',
          headers: {
            authorization: 'Bearer mock-token'
          },
          query: { period }
        });

        expect(response.statusCode).toBe(200);
        const data = JSON.parse(response.payload);
        expect(data.data.period).toBe(period);
      }
    });
  });

  describe('认证和授权测试', () => {
    it('应该要求认证令牌', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json'
          // 没有 authorization header
        },
        payload: {
          candidateId: 'test-id'
        }
      });

      expect(response.statusCode).toBe(401);
    });

    it('应该拒绝无效的认证令牌', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer invalid-token'
        },
        payload: {
          candidateId: 'test-id'
        }
      });

      expect(response.statusCode).toBe(403);
    });
  });

  describe('错误处理测试', () => {
    it('应该正确处理数据库连接错误', async () => {
      // 模拟数据库错误
      jest.spyOn(prisma.candidate, 'findMany').mockRejectedValue(new Error('Database connection failed'));

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/candidates-for-job',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          jobId: 'test-job-id'
        }
      });

      expect(response.statusCode).toBe(500);
      const data = JSON.parse(response.payload);
      expect(data.success).toBe(false);
      expect(data.message).toContain('失败');
    });

    it('应该正确处理无效的JSON输入', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: 'invalid json{'
      });

      expect(response.statusCode).toBe(400);
    });
  });

  describe('性能测试', () => {
    it('匹配API应该在合理时间内响应', async () => {
      // 创建测试数据
      const candidate = await prisma.candidate.create({
        data: {
          name: '性能测试候选人',
          phone: '13800444444',
          maintainerId: 'test-user-id'
        }
      });

      await prisma.resume.create({
        data: {
          candidateId: candidate.id,
          parseStatus: 'completed',
          fullName: candidate.name
        }
      });

      const startTime = Date.now();

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/matching/jobs-for-candidate',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer mock-token'
        },
        payload: {
          candidateId: candidate.id,
          limit: 10
        }
      });

      const endTime = Date.now();
      const responseTime = endTime - startTime;

      expect(response.statusCode).toBe(200);
      expect(responseTime).toBeLessThan(5000); // 应该在5秒内完成

      const data = JSON.parse(response.payload);
      expect(data.data.processingTime).toBeLessThan(3000); // 处理时间应该在3秒内
    });
  });
});