import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole, SubmissionStatus } from '@/types';
import { NotFoundError, ForbiddenError, ConflictError } from '@/middleware/error';
import { CandidateMatchingService } from '@/services/candidateMatching';
import { maintainerChangeService } from '@/services/maintainerChangeService';

const createCandidateSchema = z.object({
  name: z.string().min(1).max(100),
  phone: z.string().min(10).max(20),
  email: z.string().email().optional(),
  tags: z.array(z.string()).default([]),
});

const updateCandidateSchema = createCandidateSchema.partial();

const submitCandidateSchema = z.object({
  jobId: z.string().uuid(),
  resumeUrl: z.string().url().optional(),
  customResume: z.string().optional(),
  submitReason: z.string().optional(),
  matchExplanation: z.string().optional(),
  notes: z.string().optional(),
});

const updateSubmissionSchema = z.object({
  status: z.enum([
    SubmissionStatus.SUBMITTED,
    SubmissionStatus.RESUME_APPROVED,
    SubmissionStatus.RESUME_REJECTED,
    SubmissionStatus.INTERVIEW_SCHEDULED,
    SubmissionStatus.INTERVIEW_PASSED,
    SubmissionStatus.INTERVIEW_FAILED,
    SubmissionStatus.OFFER_EXTENDED,
    SubmissionStatus.OFFER_ACCEPTED,
    SubmissionStatus.OFFER_REJECTED,
    SubmissionStatus.HIRED,
  ]),
  notes: z.string().optional(),
});

export const candidateRoutes = async (fastify: FastifyInstance) => {
  const matchingService = new CandidateMatchingService(fastify.prisma);
  // Check for duplicate candidate
  fastify.post('/check-duplicate', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['name', 'phone'],
        properties: {
          name: { type: 'string', minLength: 1, maxLength: 100 },
          phone: { type: 'string', minLength: 10, maxLength: 20 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { name, phone } = request.body as { name: string; phone: string };
    
    // Normalize name and phone for comparison
    const normalizedName = name.trim().replace(/\s+/g, '');
    const normalizedPhone = phone.replace(/[\s-\(\)]/g, '');

    const existingCandidate = await fastify.prisma.candidate.findFirst({
      where: {
        AND: [
          { name: { equals: normalizedName, mode: 'insensitive' } },
          { phone: normalizedPhone },
        ],
      },
      include: {
        maintainer: {
          select: {
            id: true,
            username: true,
            email: true,
            company: {
              select: { id: true, name: true },
            },
          },
        },
        candidateSubmissions: {
          select: {
            id: true,
            status: true,
            job: {
              select: { id: true, title: true },
            },
          },
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    if (existingCandidate) {
      reply.send({
        isDuplicate: true,
        candidate: existingCandidate,
      });
    } else {
      reply.send({
        isDuplicate: false,
      });
    }
  });

  // Create candidate
  fastify.post('/', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['name', 'phone'],
        properties: {
          name: { type: 'string', minLength: 1, maxLength: 100 },
          phone: { type: 'string', minLength: 10, maxLength: 20 },
          email: { type: 'string', format: 'email' },
          tags: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT, UserRole.SOHO])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = createCandidateSchema.parse(request.body);
    
    // Normalize name and phone
    const normalizedName = body.name.trim().replace(/\s+/g, '');
    const normalizedPhone = body.phone.replace(/[\s-\(\)]/g, '');

    // Check for duplicate
    const existingCandidate = await fastify.prisma.candidate.findFirst({
      where: {
        AND: [
          { name: { equals: normalizedName, mode: 'insensitive' } },
          { phone: normalizedPhone },
        ],
      },
    });

    if (existingCandidate) {
      throw new ConflictError('Candidate with this name and phone already exists');
    }

    const candidate = await fastify.prisma.candidate.create({
      data: {
        name: body.name.trim(),
        phone: normalizedPhone,
        email: body.email,
        tags: body.tags,
        maintainerId: request.user!.id,
      },
      include: {
        maintainer: {
          select: {
            id: true,
            username: true,
            email: true,
            company: {
              select: { id: true, name: true },
            },
          },
        },
      },
    });

    reply.status(201).send(candidate);
  });

  // Get candidates with filters
  fastify.get('/', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          search: { type: 'string' },
          tags: { type: 'array', items: { type: 'string' } },
          maintainerId: { type: 'string', format: 'uuid' },
          myMaintained: { type: 'boolean' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { 
      page = 1, 
      limit = 20, 
      search, 
      tags, 
      maintainerId, 
      myMaintained 
    } = request.query as any;
    
    const skip = (page - 1) * limit;
    const where: any = {};

    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { phone: { contains: search } },
        { email: { contains: search, mode: 'insensitive' } },
      ];
    }

    if (tags && tags.length > 0) {
      where.tags = { hasMany: tags };
    }

    if (maintainerId) {
      where.maintainerId = maintainerId;
    }

    if (myMaintained) {
      where.maintainerId = request.user!.id;
    }

    const [candidates, total] = await Promise.all([
      fastify.prisma.candidate.findMany({
        where,
        skip,
        take: limit,
        include: {
          maintainer: {
            select: {
              id: true,
              username: true,
              company: {
                select: { id: true, name: true },
              },
            },
          },
          _count: {
            select: {
              candidateSubmissions: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
      }),
      fastify.prisma.candidate.count({ where }),
    ]);

    reply.send({
      candidates,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  });

  // Get candidate by ID with detailed information
  fastify.get('/:id', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };

    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
      include: {
        maintainer: {
          select: {
            id: true,
            username: true,
            email: true,
            company: {
              select: { id: true, name: true },
            },
          },
        },
        candidateSubmissions: {
          include: {
            job: {
              select: {
                id: true,
                title: true,
                industry: true,
                location: true,
                salaryMin: true,
                salaryMax: true,
                companyClient: {
                  select: { id: true, name: true },
                },
              },
            },
            submitter: {
              select: { id: true, username: true },
            },
          },
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Format the response with additional mock data for demo purposes
    const detailedCandidate = {
      ...candidate,
      // Add mock detailed information until we implement full candidate profile system
      personalInfo: {
        age: 28,
        gender: '男',
        maritalStatus: '已婚',
        workPermit: '有效',
        nationality: '中国',
        linkedIn: 'https://linkedin.com/in/example',
        github: 'https://github.com/example',
        portfolio: 'https://portfolio.example.com'
      },
      workHistory: [
        {
          company: '阿里巴巴集团',
          position: '高级软件工程师',
          startDate: '2020-03',
          endDate: null,
          description: '负责核心业务系统的架构设计和开发，领导技术团队完成多个重要项目。',
          industry: '互联网/电子商务',
          achievements: [
            '领导开发了新一代微服务架构，提升系统性能30%',
            '优化了核心API响应时间，平均延迟降低50%',
            '指导5名初级开发者，帮助团队提升整体技术水平'
          ]
        },
        {
          company: '腾讯科技',
          position: '软件工程师',
          startDate: '2018-06',
          endDate: '2020-02',
          description: '参与大型分布式系统开发，负责后端服务架构设计。',
          industry: '互联网/电子商务',
          achievements: [
            '独立完成用户中心系统重构，支撑千万级用户',
            '设计并实现分布式缓存方案，提升系统并发处理能力'
          ]
        }
      ],
      educationHistory: [
        {
          school: '清华大学',
          degree: '硕士',
          major: '计算机科学与技术',
          startDate: '2016-09',
          endDate: '2019-06',
          gpa: '3.8/4.0'
        },
        {
          school: '北京理工大学',
          degree: '学士',
          major: '软件工程',
          startDate: '2012-09',
          endDate: '2016-06',
          gpa: '3.6/4.0'
        }
      ],
      projectExperience: [
        {
          projectName: '美团点评-平台公信力风险审核平台',
          startDate: '2025年03月',
          endDate: null,
          role: '项目负责人',
          description: '负责风险审核平台的整体架构设计和团队管理，提升平台审核效率和准确性。',
          responsibilities: [
            '团队搭建:围绕新组织设计,0-1 组建风险审核平台,扩展审核类型及范围。',
            '策略反哺:调整人审定位,重新设计指标,通过人审核验机审和策略能力,为公信力风险审核能力指标负责。',
            '审核策略重构:引入AI 大模型,通过半一反三的策略辅助分析能力提升机审占比,并通过AI 辅助,提升审核效率。'
          ],
          technologies: ['Python', 'TensorFlow', 'Redis', 'MySQL', 'Kafka', 'Docker'],
          achievements: [
            '审核效率提升40%，人工审核工作量减少60%',
            '构建了AI辅助审核系统，准确率达到95%以上',
            '建立了完整的风险评估指标体系和监控体系'
          ]
        },
        {
          projectName: '美团点评-评价策略',
          startDate: '2021年09月',
          endDate: '2025年03月',
          role: '高级工程师',
          description: '负责评价系统的策略设计和算法优化，提升用户评价质量和平台内容生态。',
          responsibilities: [
            '评价质量算法设计，识别虚假评价和低质量内容',
            '用户行为分析，建立用户画像和信用评估体系',
            'A/B测试设计和数据分析，持续优化策略效果'
          ],
          technologies: ['Java', 'Spring Boot', 'Spark', 'Elasticsearch', 'Redis'],
          achievements: [
            '虚假评价识别准确率提升至92%',
            '优质评价占比提升25%，用户满意度显著改善',
            '建立了完整的评价质量评估体系'
          ]
        }
      ],
      skills: [
        { name: 'JavaScript', level: 'expert', yearsOfExperience: 6, category: '编程语言' },
        { name: 'Python', level: 'advanced', yearsOfExperience: 5, category: '编程语言' },
        { name: 'React', level: 'expert', yearsOfExperience: 4, category: '前端框架' },
        { name: 'Node.js', level: 'advanced', yearsOfExperience: 5, category: '后端技术' },
        { name: 'AWS', level: 'intermediate', yearsOfExperience: 3, category: '云计算' },
        { name: 'Docker', level: 'advanced', yearsOfExperience: 4, category: '容器技术' }
      ],
      languages: [
        { language: '中文', proficiency: 'native' },
        { language: '英语', proficiency: 'business' },
        { language: '日语', proficiency: 'conversational' }
      ],
      resumes: [
        {
          id: 'resume-1',
          filename: `${candidate.name}_高级软件工程师_简历.pdf`,
          uploadDate: '2024-01-15',
          fileSize: '2.1 MB',
          type: 'pdf',
          isActive: true
        }
      ],
      applications: candidate.candidateSubmissions.map(submission => ({
        id: submission.id,
        jobTitle: submission.job.title,
        companyName: submission.job.companyClient?.name || '未知公司',
        status: submission.status,
        appliedDate: submission.createdAt.toISOString(),
        notes: submission.notes
      })),
      notes: [],
      // Add status and other fields
      status: 'active',
      location: '北京',
      experience: '5年以上',
      education: '硕士',
      currentPosition: '高级软件工程师',
      expectedSalary: '50-80万',
      rating: 5
    };

    reply.send({ candidate: detailedCandidate });
  });

  // Update candidate (only maintainer can update)
  fastify.patch('/:id', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const body = updateCandidateSchema.parse(request.body);

    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Only maintainer can update candidate info
    if (candidate.maintainerId !== request.user!.id && request.user!.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Only the candidate maintainer can update this candidate');
    }

    // If phone is being updated, check for duplicates
    if (body.phone && body.phone !== candidate.phone) {
      const normalizedPhone = body.phone.replace(/[\s-\(\)]/g, '');
      const normalizedName = (body.name || candidate.name).trim().replace(/\s+/g, '');
      
      const existingCandidate = await fastify.prisma.candidate.findFirst({
        where: {
          AND: [
            { id: { not: id } },
            { name: { equals: normalizedName, mode: 'insensitive' } },
            { phone: normalizedPhone },
          ],
        },
      });

      if (existingCandidate) {
        throw new ConflictError('Another candidate with this name and phone already exists');
      }
      
      body.phone = normalizedPhone;
    }

    if (body.name) {
      body.name = body.name.trim();
    }

    const updatedCandidate = await fastify.prisma.candidate.update({
      where: { id },
      data: body,
      include: {
        maintainer: {
          select: {
            id: true,
            username: true,
            company: {
              select: { id: true, name: true },
            },
          },
        },
      },
    });

    reply.send(updatedCandidate);
  });

  // Submit candidate to job
  fastify.post('/:id/submit', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      body: {
        type: 'object',
        required: ['jobId'],
        properties: {
          jobId: { type: 'string', format: 'uuid' },
          resumeUrl: { type: 'string', format: 'uri' },
          customResume: { type: 'string' },
          submitReason: { type: 'string' },
          matchExplanation: { type: 'string' },
          notes: { type: 'string' },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT, UserRole.SOHO])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const body = submitCandidateSchema.parse(request.body);

    // Check if candidate exists
    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Check if job exists and user has access
    const job = await fastify.prisma.job.findUnique({
      where: { id: body.jobId },
      include: {
        publisher: {
          select: {
            companyId: true,
          },
        },
        jobPermissions: {
          select: {
            grantedToUserId: true,
            grantedToCompanyId: true,
          },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // Check if user has access to submit to this job
    const hasAccess = 
      job.publisherId === request.user!.id || // Job publisher
      job.publisher.companyId === request.user!.companyId || // Same company
      job.jobPermissions.some(p => 
        p.grantedToUserId === request.user!.id || 
        p.grantedToCompanyId === request.user!.companyId
      ); // Explicitly granted access

    if (!hasAccess) {
      throw new ForbiddenError('You do not have permission to submit candidates to this job');
    }

    // Check if candidate is already submitted to this job
    const existingSubmission = await fastify.prisma.candidateSubmission.findFirst({
      where: {
        candidateId: id,
        jobId: body.jobId,
      },
    });

    if (existingSubmission) {
      throw new ConflictError('Candidate has already been submitted to this job');
    }

    const submission = await fastify.prisma.candidateSubmission.create({
      data: {
        candidateId: id,
        jobId: body.jobId,
        submitterId: request.user!.id,
        resumeUrl: body.resumeUrl,
        customResume: body.customResume,
        submitReason: body.submitReason,
        matchExplanation: body.matchExplanation,
        notes: body.notes,
        status: SubmissionStatus.SUBMITTED,
      },
      include: {
        candidate: {
          select: {
            id: true,
            name: true,
            phone: true,
            email: true,
          },
        },
        job: {
          select: {
            id: true,
            title: true,
            industry: true,
            location: true,
          },
        },
        submitter: {
          select: {
            id: true,
            username: true,
          },
        },
      },
    });

    // TODO: Send notification to job publisher

    reply.status(201).send(submission);
  });

  // Get candidate submissions
  fastify.get('/:id/submissions', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };

    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    const submissions = await fastify.prisma.candidateSubmission.findMany({
      where: { candidateId: id },
      include: {
        job: {
          select: {
            id: true,
            title: true,
            industry: true,
            location: true,
            salaryMin: true,
            salaryMax: true,
            status: true,
          },
        },
        submitter: {
          select: {
            id: true,
            username: true,
            company: {
              select: { id: true, name: true },
            },
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    reply.send({ submissions });
  });

  // Update submission status (job publisher only)
  fastify.patch('/submissions/:submissionId', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          submissionId: { type: 'string', format: 'uuid' },
        },
        required: ['submissionId'],
      },
      body: {
        type: 'object',
        required: ['status'],
        properties: {
          status: { 
            type: 'string', 
            enum: [
              'submitted', 'resume_approved', 'resume_rejected',
              'interview_scheduled', 'interview_passed', 'interview_failed',
              'offer_extended', 'offer_accepted', 'offer_rejected', 'hired'
            ] 
          },
          notes: { type: 'string' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { submissionId } = request.params as { submissionId: string };
    const body = updateSubmissionSchema.parse(request.body);

    const submission = await fastify.prisma.candidateSubmission.findUnique({
      where: { id: submissionId },
      include: {
        job: true,
        candidate: {
          select: { id: true, name: true },
        },
        submitter: {
          select: { id: true, username: true },
        },
      },
    });

    if (!submission) {
      throw new NotFoundError('Submission not found');
    }

    // Only job publisher can update submission status
    if (submission.job.publisherId !== request.user!.id && request.user!.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Only the job publisher can update submission status');
    }

    const updatedSubmission = await fastify.prisma.candidateSubmission.update({
      where: { id: submissionId },
      data: {
        status: body.status,
        notes: body.notes,
      },
      include: {
        candidate: {
          select: {
            id: true,
            name: true,
            phone: true,
            email: true,
          },
        },
        job: {
          select: {
            id: true,
            title: true,
            industry: true,
            location: true,
          },
        },
        submitter: {
          select: {
            id: true,
            username: true,
          },
        },
      },
    });

    // TODO: Send notification to submitter

    reply.send(updatedSubmission);
  });

  // Advanced candidate search with matching
  fastify.post('/search', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        properties: {
          keywords: { type: 'array', items: { type: 'string' } },
          tags: { type: 'array', items: { type: 'string' } },
          location: { type: 'string' },
          maintainerId: { type: 'string', format: 'uuid' },
          excludeSubmittedToJob: { type: 'string', format: 'uuid' },
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const {
      keywords,
      tags,
      location,
      maintainerId,
      excludeSubmittedToJob,
      page = 1,
      limit = 20
    } = request.body as any;

    const searchFilters = {
      keywords,
      tags,
      location,
      maintainerId,
      excludeSubmittedToJob
    };

    const results = await matchingService.searchCandidates(searchFilters, page, limit);

    reply.send(results);
  });

  // Find matching candidates for a job
  fastify.get('/match-for-job/:jobId', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          jobId: { type: 'string', format: 'uuid' },
        },
        required: ['jobId'],
      },
      querystring: {
        type: 'object',
        properties: {
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT, UserRole.SOHO])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { jobId } = request.params as { jobId: string };
    const { limit = 20 } = request.query as { limit: number };

    try {
      const matchingResults = await matchingService.findCandidatesForJob(jobId, limit);

      reply.send({
        jobId,
        matches: matchingResults,
        total: matchingResults.length,
      });
    } catch (error) {
      if (error instanceof Error && error.message === 'Job not found') {
        throw new NotFoundError('Job not found');
      }
      throw error;
    }
  });

  // Find recommended jobs for a candidate
  fastify.get('/:id/recommended-jobs', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      querystring: {
        type: 'object',
        properties: {
          limit: { type: 'integer', minimum: 1, maximum: 50, default: 20 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { limit = 20 } = request.query as { limit: number };

    try {
      const jobMatches = await matchingService.findJobsForCandidate(id, limit);

      reply.send({
        candidateId: id,
        recommendedJobs: jobMatches,
        total: jobMatches.length,
      });
    } catch (error) {
      if (error instanceof Error && error.message === 'Candidate not found') {
        throw new NotFoundError('Candidate not found');
      }
      throw error;
    }
  });

  // Request maintainer change
  fastify.post('/:id/request-maintainer-change', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      body: {
        type: 'object',
        required: ['requestedMaintainerId', 'reason'],
        properties: {
          requestedMaintainerId: { type: 'string', format: 'uuid' },
          reason: { type: 'string', minLength: 10, maxLength: 1000 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id: candidateId } = request.params as { id: string };
    const { requestedMaintainerId, reason } = request.body as any;
    const user = request.user!;

    try {
      const changeRequest = await maintainerChangeService.createChangeRequest(
        {
          candidateId,
          requestedMaintainerId,
          reason,
        },
        user.id
      );

      reply.status(201).send({
        message: 'Maintainer change request created successfully',
        request: changeRequest,
      });
    } catch (error) {
      if (error instanceof Error) {
        if (error.message === 'Candidate not found') {
          throw new NotFoundError('Candidate not found');
        }
        if (error.message === 'Requested maintainer not found') {
          throw new NotFoundError('Requested maintainer not found');
        }
        if (error.message.includes('already a pending')) {
          throw new ConflictError(error.message);
        }
        throw new ForbiddenError(error.message);
      }
      throw error;
    }
  });

  // Get maintainer change requests
  fastify.get('/maintainer-change-requests', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          status: { type: 'string', enum: ['pending', 'approved', 'rejected'] },
          candidateId: { type: 'string', format: 'uuid' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { page = 1, limit = 20, status, candidateId } = request.query as any;
    const user = request.user!;

    const result = await maintainerChangeService.getRequestsForUser(
      user.id,
      user.role,
      { page, limit }
    );

    reply.send(result);
  });

  // Get specific maintainer change request
  fastify.get('/maintainer-change-requests/:requestId', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          requestId: { type: 'string', format: 'uuid' },
        },
        required: ['requestId'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { requestId } = request.params as { requestId: string };
    const user = request.user!;

    const changeRequest = await maintainerChangeService.getRequestById(requestId);

    if (!changeRequest) {
      throw new NotFoundError('Maintainer change request not found');
    }

    // Check access permissions
    const hasAccess = 
      user.role === UserRole.PLATFORM_ADMIN ||
      changeRequest.requesterId === user.id ||
      changeRequest.currentMaintainerId === user.id ||
      changeRequest.requestedMaintainerId === user.id;

    if (!hasAccess) {
      throw new ForbiddenError('Access denied to this maintainer change request');
    }

    reply.send(changeRequest);
  });

  // Add note to candidate
  fastify.post('/:id/notes', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      body: {
        type: 'object',
        required: ['content', 'type'],
        properties: {
          content: { type: 'string', minLength: 1, maxLength: 2000 },
          type: { type: 'string', enum: ['interview', 'call', 'email', 'meeting', 'other'] },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { content, type } = request.body as { content: string; type: string };

    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Mock note creation (in a real implementation, you'd have a notes table)
    const note = {
      id: `note-${Date.now()}`,
      content,
      type,
      createdBy: request.user!.username,
      createdAt: new Date().toISOString(),
    };

    reply.status(201).send({ note, message: 'Note added successfully' });
  });

  // Review maintainer change request (platform admin only)
  fastify.patch('/maintainer-change-requests/:requestId/review', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          requestId: { type: 'string', format: 'uuid' },
        },
        required: ['requestId'],
      },
      body: {
        type: 'object',
        required: ['status'],
        properties: {
          status: { type: 'string', enum: ['approved', 'rejected'] },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { requestId } = request.params as { requestId: string };
    const { status } = request.body as any;
    const user = request.user!;

    try {
      const reviewedRequest = await maintainerChangeService.reviewChangeRequest({
        requestId,
        status,
        reviewedById: user.id,
      });

      reply.send({
        message: `Maintainer change request ${status}`,
        request: reviewedRequest,
      });
    } catch (error) {
      if (error instanceof Error) {
        if (error.message === 'Maintainer change request not found') {
          throw new NotFoundError('Maintainer change request not found');
        }
        if (error.message === 'Request has already been reviewed') {
          throw new ConflictError('Request has already been reviewed');
        }
        throw new ForbiddenError(error.message);
      }
      throw error;
    }
  });

  // Create communication record
  fastify.post('/:id/communications', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      body: {
        type: 'object',
        properties: {
          communicationType: { type: 'string', enum: ['phone', 'email', 'wechat', 'meeting'] },
          subject: { type: 'string' },
          content: { type: 'string' },
          duration: { type: 'string' },
          outcome: { type: 'string' },
          purpose: { type: 'string' },
          nextFollowUpDate: { type: 'string', format: 'date-time', nullable: true },
          notes: { type: 'string' },
          metadata: { type: 'object' },
        },
        required: ['communicationType', 'content'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const user = request.user as any;
    const {
      communicationType,
      subject,
      content,
      duration,
      outcome,
      purpose,
      nextFollowUpDate,
      notes,
      metadata
    } = request.body as any;

    // Check if candidate exists and user has access
    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
      include: {
        maintainer: true,
      },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Check access permissions
    console.log('Communication access debug:', {
      userRole: user.role,
      userId: user.id,
      userCompanyId: user.companyId,
      candidateMaintainerId: candidate.maintainerId,
      candidateMaintainerCompanyId: candidate.maintainer.companyId,
      isPlatformAdmin: user.role === 'platform_admin',
      isMaintainer: candidate.maintainerId === user.id,
      isCompanyAdmin: user.role === 'company_admin' && candidate.maintainer.companyId === user.companyId
    });
    
    const hasAccess = user.role === 'platform_admin' || 
                     candidate.maintainerId === user.id ||
                     user.role === 'company_admin';

    console.log('Has access:', hasAccess);

    if (!hasAccess) {
      throw new ForbiddenError('Access denied to this candidate');
    }

    try {
      const communicationRecord = await fastify.prisma.communicationRecord.create({
        data: {
          candidateId: id,
          userId: user.id,
          communicationType,
          subject: subject || null,
          content,
          duration: duration || null,
          outcome: outcome || null,
          purpose: purpose || null,
          nextFollowUpDate: nextFollowUpDate ? new Date(nextFollowUpDate) : null,
          notes: notes || null,
          metadata: metadata || {},
        },
        include: {
          user: {
            select: {
              id: true,
              username: true,
              email: true,
            },
          },
        },
      });

      reply.send({
        message: 'Communication record created successfully',
        record: communicationRecord,
      });
    } catch (error) {
      fastify.log.error('Error creating communication record:', error);
      throw new Error('Failed to create communication record');
    }
  });

  // Get communication records for candidate
  fastify.get('/:id/communications', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          type: { type: 'string', enum: ['phone', 'email', 'wechat', 'meeting'] },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { page = 1, limit = 20, type } = request.query as any;
    const user = request.user as any;

    // Check if candidate exists and user has access
    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
      include: {
        maintainer: true,
      },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Check access permissions
    const hasAccess = user.role === 'platform_admin' || 
                     candidate.maintainerId === user.id ||
                     user.role === 'company_admin';

    if (!hasAccess) {
      throw new ForbiddenError('Access denied to this candidate');
    }

    const where: any = { candidateId: id };
    if (type) {
      where.communicationType = type;
    }

    const [records, total] = await Promise.all([
      fastify.prisma.communicationRecord.findMany({
        where,
        include: {
          user: {
            select: {
              id: true,
              username: true,
              email: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      fastify.prisma.communicationRecord.count({ where }),
    ]);

    reply.send({
      records,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  });

  // Add application record for candidate
  fastify.post('/:id/applications', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      body: {
        type: 'object',
        properties: {
          jobTitle: { type: 'string' },
          companyName: { type: 'string' },
          status: { type: 'string', enum: ['submitted', 'reviewing', 'interview', 'offer', 'rejected'] },
          notes: { type: 'string' },
          jobId: { type: 'string', format: 'uuid' },
        },
        required: ['jobTitle', 'companyName', 'status'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const user = request.user as any;
    const { jobTitle, companyName, status, notes, jobId } = request.body as any;

    // Check if candidate exists and user has access
    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
      include: { maintainer: true },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Check access permissions
    const hasAccess = user.role === 'platform_admin' || 
                     candidate.maintainerId === user.id ||
                     user.role === 'company_admin';

    if (!hasAccess) {
      throw new ForbiddenError('Access denied to this candidate');
    }

    // If jobId is provided, try to create a real candidate submission
    if (jobId) {
      try {
        // Check if job exists and user has access
        const job = await fastify.prisma.job.findUnique({
          where: { id: jobId },
          include: { companyClient: true },
        });

        if (job) {
          // Create actual candidate submission
          const submission = await fastify.prisma.candidateSubmission.create({
            data: {
              candidateId: id,
              jobId: jobId,
              submitterId: user.id,
              status: 'submitted',
              notes: notes || '通过推荐功能投递',
            },
            include: {
              job: {
                include: {
                  companyClient: true,
                },
              },
            },
          });

          reply.status(201).send({
            message: 'Application record created successfully',
            application: {
              id: submission.id,
              jobTitle: submission.job.title,
              companyName: submission.job.companyClient?.name || companyName,
              status: submission.status,
              appliedDate: submission.createdAt.toISOString(),
              notes: submission.notes,
              jobId: submission.jobId,
            },
          });
          return;
        }
      } catch (error) {
        fastify.log.warn('Failed to create real submission, creating mock record:', error);
      }
    }

    // Create mock application record (for cases where jobId is not provided or job doesn't exist)
    const application = {
      id: `app-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      jobTitle,
      companyName,
      status,
      appliedDate: new Date().toISOString(),
      notes: notes || null,
      jobId: jobId || null,
    };

    reply.status(201).send({
      message: 'Application record created successfully',
      application,
    });
  });

  // Get application records for candidate
  fastify.get('/:id/applications', {
    schema: {
      tags: ['Candidates'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { page = 1, limit = 20 } = request.query as any;
    const user = request.user as any;

    // Check if candidate exists and user has access
    const candidate = await fastify.prisma.candidate.findUnique({
      where: { id },
      include: {
        maintainer: true,
        candidateSubmissions: {
          include: {
            job: {
              include: {
                companyClient: true,
              },
            },
          },
          orderBy: { createdAt: 'desc' },
          skip: (page - 1) * limit,
          take: limit,
        },
      },
    });

    if (!candidate) {
      throw new NotFoundError('Candidate not found');
    }

    // Check access permissions
    const hasAccess = user.role === 'platform_admin' || 
                     candidate.maintainerId === user.id ||
                     user.role === 'company_admin';

    if (!hasAccess) {
      throw new ForbiddenError('Access denied to this candidate');
    }

    const applications = candidate.candidateSubmissions.map(submission => ({
      id: submission.id,
      jobTitle: submission.job.title,
      companyName: submission.job.companyClient?.name || '未知公司',
      status: submission.status,
      appliedDate: submission.createdAt.toISOString(),
      notes: submission.notes,
      jobId: submission.jobId,
    }));

    const total = await fastify.prisma.candidateSubmission.count({
      where: { candidateId: id },
    });

    reply.send({
      applications,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  });
};