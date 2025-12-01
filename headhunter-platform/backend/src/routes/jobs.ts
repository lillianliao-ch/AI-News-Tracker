import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole, JobStatus } from '@/types';
import { NotFoundError, ForbiddenError, ValidationError } from '@/middleware/error';

const createJobSchema = z.object({
  title: z.string().min(1).max(255),
  industry: z.string().max(100).optional(),
  location: z.string().max(255).optional(),
  salaryMin: z.number().int().min(0).optional(),
  salaryMax: z.number().int().min(0).optional(),
  description: z.string().min(1),
  requirements: z.string().min(1),
  benefits: z.string().optional(),
  urgency: z.string().max(50).optional(),
  reportTo: z.string().max(100).optional(),
  publisherSharePct: z.number().min(0).max(100),
  referrerSharePct: z.number().min(0).max(100),
  platformSharePct: z.number().min(0).max(100),
  companyClientId: z.string().uuid(),
});

const updateJobSchema = createJobSchema.partial();

const jobStatusSchema = z.object({
  status: z.enum(['pending_approval', 'approved', 'open', 'paused', 'closed', 'rejected']),
});

export const jobRoutes = async (fastify: FastifyInstance) => {
  // Get all jobs with filtering and pagination
  fastify.get('/', {
    schema: {
      tags: ['Jobs'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          status: { type: 'string', enum: ['pending_approval', 'approved', 'open', 'paused', 'closed', 'rejected'] },
          industry: { type: 'string' },
          location: { type: 'string' },
          search: { type: 'string' },
          publisherId: { type: 'string', format: 'uuid' },
          companyClient: { type: 'string' },
          salaryMin: { type: 'integer', minimum: 0 },
          salaryMax: { type: 'integer', minimum: 0 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { 
      page = 1, 
      limit = 20, 
      status, 
      industry, 
      location, 
      search,
      publisherId,
      companyClient,
      salaryMin,
      salaryMax
    } = request.query as any;
    
    const skip = (page - 1) * limit;
    const where: any = {};
    
    if (status) where.status = status;
    if (industry) where.industry = { contains: industry, mode: 'insensitive' };
    if (location) where.location = { contains: location, mode: 'insensitive' };
    if (publisherId) where.publisherId = publisherId;
    if (companyClient) {
      where.companyClient = {
        name: { contains: companyClient, mode: 'insensitive' }
      };
    }
    
    if (salaryMin || salaryMax) {
      where.AND = where.AND || [];
      if (salaryMin) {
        where.AND.push({
          OR: [
            { salaryMax: { gte: salaryMin } },
            { salaryMax: null }
          ]
        });
      }
      if (salaryMax) {
        where.AND.push({
          OR: [
            { salaryMin: { lte: salaryMax } },
            { salaryMin: null }
          ]
        });
      }
    }
    
    // Store search conditions
    let searchConditions = null;
    if (search) {
      searchConditions = [
        { title: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } },
        { requirements: { contains: search, mode: 'insensitive' } },
      ];
    }

    // Role-based access control
    const user = request.user!;
    let roleConditions = null;
    
    if (user.role === UserRole.COMPANY_ADMIN) {
      if (user.companyId) {
        where.publisher = { companyId: user.companyId };
      } else {
        where.id = 'non-existent-id';
      }
    } else if (user.role === UserRole.CONSULTANT) {
      // 公司顾问可以看到：
      // 1. 自己发布的job
      // 2. 分配给自己的job  
      // 3. 分配给所在公司的job
      roleConditions = [
        { publisherId: user.id },
        { 
          jobPermissions: { 
            some: { grantedToUserId: user.id } 
          } 
        },
        { 
          jobPermissions: { 
            some: { grantedToCompanyId: user.companyId } 
          } 
        }
      ];
    } else if (user.role === UserRole.SOHO) {
      // SOHO顾问只能看到：
      // 1. 自己发布的job
      // 2. 明确分配给自己的job
      roleConditions = [
        { publisherId: user.id },
        { 
          jobPermissions: { 
            some: { grantedToUserId: user.id } 
          } 
        }
      ];
    }

    // Combine search and role conditions using AND logic
    if (roleConditions && searchConditions) {
      where.AND = [
        { OR: roleConditions },
        { OR: searchConditions }
      ];
    } else if (roleConditions) {
      where.OR = roleConditions;
    } else if (searchConditions) {
      where.OR = searchConditions;
    }

    const [jobs, total] = await Promise.all([
      fastify.prisma.job.findMany({
        where,
        skip,
        take: limit,
        include: {
          publisher: {
            select: {
              id: true,
              username: true,
              email: true,
              role: true,
              company: {
                select: {
                  id: true,
                  name: true,
                },
              },
            },
          },
          companyClient: {
            select: {
              id: true,
              name: true,
              industry: true,
              location: true,
              contactName: true,
              contactPhone: true,
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
      fastify.prisma.job.count({ where }),
    ]);

    reply.send({
      jobs,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  });

  // Get job by ID
  fastify.get('/:id', {
    schema: {
      tags: ['Jobs'],
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
    const user = request.user!;

    const job = await fastify.prisma.job.findUnique({
      where: { id },
      include: {
        publisher: {
          select: {
            id: true,
            username: true,
            email: true,
            role: true,
            company: {
              select: {
                id: true,
                name: true,
              },
            },
          },
        },
        companyClient: true,
        candidateSubmissions: {
          include: {
            candidate: {
              select: {
                id: true,
                name: true,
                phone: true,
                email: true,
              },
            },
            submitter: {
              select: {
                id: true,
                username: true,
                email: true,
              },
            },
          },
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // Check access permissions
    const hasAccess = 
      user.role === UserRole.PLATFORM_ADMIN ||
      job.publisherId === user.id ||
      (user.companyId && job.publisher.company?.id === user.companyId) ||
      (job.status === JobStatus.OPEN);

    if (!hasAccess) {
      throw new ForbiddenError('Access denied to this job');
    }

    reply.send(job);
  });

  // Create new job (Company Admin only)
  fastify.post('/', {
    schema: {
      tags: ['Jobs'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['title', 'description', 'requirements', 'publisherSharePct', 'referrerSharePct', 'platformSharePct', 'companyClientId'],
        properties: {
          title: { type: 'string', minLength: 1, maxLength: 255 },
          industry: { type: 'string', maxLength: 100 },
          location: { type: 'string', maxLength: 255 },
          salaryMin: { type: 'integer', minimum: 0 },
          salaryMax: { type: 'integer', minimum: 0 },
          description: { type: 'string', minLength: 1 },
          requirements: { type: 'string', minLength: 1 },
          benefits: { type: 'string' },
          urgency: { type: 'string', maxLength: 50 },
          reportTo: { type: 'string', maxLength: 100 },
          publisherSharePct: { type: 'number', minimum: 0, maximum: 100 },
          referrerSharePct: { type: 'number', minimum: 0, maximum: 100 },
          platformSharePct: { type: 'number', minimum: 0, maximum: 100 },
          companyClientId: { type: 'string', format: 'uuid' },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.CONSULTANT, UserRole.COMPANY_ADMIN, UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = createJobSchema.parse(request.body);
    const user = request.user!;

    // Validate share percentages sum to 100
    const totalShare = body.publisherSharePct + body.referrerSharePct + body.platformSharePct;
    if (Math.abs(totalShare - 100) > 0.01) {
      throw new ValidationError('Share percentages must sum to 100%');
    }

    // Validate salary range
    if (body.salaryMin && body.salaryMax && body.salaryMin > body.salaryMax) {
      throw new ValidationError('Minimum salary cannot be greater than maximum salary');
    }

    const job = await fastify.prisma.job.create({
      data: {
        ...body,
        publisherId: user.id,
      },
      include: {
        publisher: {
          select: {
            id: true,
            username: true,
            email: true,
            company: {
              select: {
                id: true,
                name: true,
              },
            },
          },
        },
        companyClient: true,
      },
    });

    reply.status(201).send(job);
  });

  // Approve job (生效按钮) - 审批通过并自动对本公司开放
  fastify.patch('/:id/approve', {
    schema: {
      tags: ['Jobs'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const user = request.user!;

    const job = await fastify.prisma.job.findUnique({
      where: { id },
      include: {
        publisher: {
          select: {
            companyId: true,
          },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // 只能审批待审核的职位
    if (job.status !== 'pending_approval') {
      throw new ValidationError('Job is not pending approval');
    }

    // 检查权限：只有同公司的admin可以审批
    const canApprove = user.role === UserRole.PLATFORM_ADMIN ||
                       (user.role === UserRole.COMPANY_ADMIN && 
                        user.companyId === job.publisher.companyId);

    if (!canApprove) {
      throw new ForbiddenError('Access denied to approve this job');
    }

    // 更新职位状态为approved并开放给本公司
    const updatedJob = await fastify.prisma.job.update({
      where: { id },
      data: { status: 'open' }, // 直接设为open，表示已审批通过并对内部开放
    });

    // 自动创建对本公司的权限分享（如果还没有的话）
    const existingCompanyPermission = await fastify.prisma.jobPermission.findFirst({
      where: {
        jobId: id,
        grantedToCompanyId: job.publisher.companyId,
      },
    });

    if (!existingCompanyPermission) {
      await fastify.prisma.jobPermission.create({
        data: {
          jobId: id,
          grantedToCompanyId: job.publisher.companyId,
          grantedById: user.id,
        },
      });
    }

    reply.send({
      message: 'Job approved and opened to company consultants',
      job: updatedJob,
    });
  });

  // Update job status
  fastify.patch('/:id/status', {
    schema: {
      tags: ['Jobs'],
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
          status: { type: 'string', enum: ['pending_approval', 'approved', 'open', 'paused', 'closed', 'rejected'] },
        },
        required: ['status'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { status } = jobStatusSchema.parse(request.body);
    const user = request.user!;

    const job = await fastify.prisma.job.findUnique({
      where: { id },
      include: {
        publisher: {
          select: {
            companyId: true,
          },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // Check permissions based on status change
    let canEdit = false;

    // Approval/rejection actions - only company admin or platform admin
    if (status === 'approved' || status === 'rejected') {
      canEdit = user.role === UserRole.PLATFORM_ADMIN ||
                (user.role === UserRole.COMPANY_ADMIN && 
                 user.companyId === job.publisher.companyId);
    }
    // Opening job to SOHO consultants - only company admin or platform admin  
    else if (status === 'open' && job.status === 'approved') {
      canEdit = user.role === UserRole.PLATFORM_ADMIN ||
                (user.role === UserRole.COMPANY_ADMIN && 
                 user.companyId === job.publisher.companyId);
    }
    // Other status changes (pause, close) - publisher, company admin, or platform admin
    else {
      canEdit = user.role === UserRole.PLATFORM_ADMIN ||
                job.publisherId === user.id ||
                (user.role === UserRole.COMPANY_ADMIN && 
                 user.companyId === job.publisher.companyId);
    }

    if (!canEdit) {
      throw new ForbiddenError('Access denied to perform this action');
    }

    const updatedJob = await fastify.prisma.job.update({
      where: { id },
      data: { status },
    });

    reply.send({
      message: `Job status updated to ${status}`,
      job: updatedJob,
    });
  });

  // Assign job to SOHO consultant by email
  fastify.post('/:id/assign-soho', {
    schema: {
      tags: ['Jobs'],
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
          email: { type: 'string', format: 'email' },
          expiresAt: { type: 'string', format: 'date-time' },
        },
        required: ['email'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { email, expiresAt } = request.body as { email: string; expiresAt?: string };
    const user = request.user!;

    const job = await fastify.prisma.job.findUnique({
      where: { id },
      include: {
        publisher: {
          select: { companyId: true },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // 只能assign已审批通过的职位
    if (job.status !== 'open') {
      throw new ValidationError('Job must be approved and open before assigning to SOHO consultants');
    }

    // 检查权限：只有同公司的admin可以assign
    const canAssign = user.role === UserRole.PLATFORM_ADMIN ||
                      (user.role === UserRole.COMPANY_ADMIN && 
                       user.companyId === job.publisher.companyId);

    if (!canAssign) {
      throw new ForbiddenError('Access denied to assign this job');
    }

    // 根据邮箱查找SOHO用户
    const sohoUser = await fastify.prisma.user.findUnique({
      where: { email },
    });

    if (!sohoUser) {
      throw new NotFoundError(`SOHO consultant with email ${email} not found`);
    }

    if (sohoUser.role !== 'soho') {
      throw new ValidationError('Target user is not a SOHO consultant');
    }

    // 检查是否已经分配过
    const existingPermission = await fastify.prisma.jobPermission.findFirst({
      where: {
        jobId: id,
        grantedToUserId: sohoUser.id,
      },
    });

    if (existingPermission) {
      throw new ValidationError('Job already assigned to this SOHO consultant');
    }

    const permission = await fastify.prisma.jobPermission.create({
      data: {
        jobId: id,
        grantedToUserId: sohoUser.id,
        grantedById: user.id,
        expiresAt: expiresAt ? new Date(expiresAt) : undefined,
      },
      include: {
        grantedToUser: {
          select: {
            id: true,
            username: true,
            email: true,
          },
        },
      },
    });

    // 创建通知
    await fastify.prisma.notification.create({
      data: {
        recipientId: sohoUser.id,
        type: 'job_shared',
        title: 'New Job Assignment',
        content: `Job "${job.title}" has been assigned to you by ${user.username}`,
        relatedId: job.id,
      },
    });

    reply.status(201).send({
      message: `Job successfully assigned to SOHO consultant ${email}`,
      permission,
    });
  });

  // Share job with user or company
  fastify.post('/:id/share', {
    schema: {
      tags: ['Jobs'],
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
          targetUserId: { type: 'string', format: 'uuid' },
          targetCompanyId: { type: 'string', format: 'uuid' },
          expiresAt: { type: 'string', format: 'date-time' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { targetUserId, targetCompanyId, expiresAt } = request.body as any;
    const user = request.user!;

    if (!targetUserId && !targetCompanyId) {
      throw new ValidationError('Either targetUserId or targetCompanyId must be provided');
    }

    if (targetUserId && targetCompanyId) {
      throw new ValidationError('Cannot specify both targetUserId and targetCompanyId');
    }

    const job = await fastify.prisma.job.findUnique({
      where: { id },
      include: {
        publisher: {
          select: { companyId: true },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // Check permissions based on new business rules
    let canShare = false;
    
    switch (user.role) {
      case UserRole.PLATFORM_ADMIN:
        // 平台管理员可以分配所有职位
        canShare = true;
        break;
        
      case UserRole.COMPANY_ADMIN:
        // 公司admin可以分配该公司所有的职位给soho顾问
        canShare = user.companyId && job.publisher.companyId === user.companyId;
        break;
        
      case UserRole.SOHO:
        // soho顾问可以将自己创建的职位分配给其他soho顾问，或者分配给其他公司的admin
        canShare = job.publisherId === user.id;
        break;
        
      case UserRole.CONSULTANT:
        // 公司顾问不能分配职位
        canShare = false;
        break;
        
      default:
        canShare = false;
    }

    if (!canShare) {
      throw new ForbiddenError('Access denied to assign this job based on your role and permissions');
    }

    // Check if permission already exists
    const existingPermission = await fastify.prisma.jobPermission.findFirst({
      where: {
        jobId: id,
        grantedToUserId: targetUserId || undefined,
        grantedToCompanyId: targetCompanyId || undefined,
      },
    });

    if (existingPermission) {
      throw new ValidationError('Permission already granted to this target');
    }

    const permission = await fastify.prisma.jobPermission.create({
      data: {
        jobId: id,
        grantedToUserId: targetUserId,
        grantedToCompanyId: targetCompanyId,
        grantedById: user.id,
        expiresAt: expiresAt ? new Date(expiresAt) : undefined,
      },
      include: {
        grantedToUser: {
          select: {
            id: true,
            username: true,
            email: true,
          },
        },
        grantedToCompany: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    // Create notification
    const targetUsers = [];
    if (targetUserId) {
      targetUsers.push(targetUserId);
    } else if (targetCompanyId) {
      // Get all users in the target company
      const companyUsers = await fastify.prisma.user.findMany({
        where: { companyId: targetCompanyId },
        select: { id: true },
      });
      targetUsers.push(...companyUsers.map(u => u.id));
    }

    // Create notifications for target users
    for (const userId of targetUsers) {
      await fastify.prisma.notification.create({
        data: {
          recipientId: userId,
          type: 'job_shared',
          title: 'New Job Shared',
          content: `Job "${job.title}" has been shared with you by ${user.username}`,
          relatedId: job.id,
        },
      });
    }

    reply.status(201).send({
      message: 'Job shared successfully',
      permission,
    });
  });

  // Get job permissions
  fastify.get('/:id/permissions', {
    schema: {
      tags: ['Jobs'],
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
    const user = request.user!;

    const job = await fastify.prisma.job.findUnique({
      where: { id },
      include: {
        publisher: {
          select: { companyId: true },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // Check permissions
    const canView = 
      user.role === UserRole.PLATFORM_ADMIN ||
      job.publisherId === user.id ||
      (user.companyId && job.publisher.companyId === user.companyId);

    if (!canView) {
      throw new ForbiddenError('Access denied to view job permissions');
    }

    const permissions = await fastify.prisma.jobPermission.findMany({
      where: { jobId: id },
      include: {
        grantedToUser: {
          select: {
            id: true,
            username: true,
            email: true,
            company: {
              select: {
                id: true,
                name: true,
              },
            },
          },
        },
        grantedToCompany: {
          select: {
            id: true,
            name: true,
          },
        },
        grantedBy: {
          select: {
            id: true,
            username: true,
            email: true,
          },
        },
      },
      orderBy: { grantedAt: 'desc' },
    });

    reply.send({ permissions });
  });

  // Revoke job permission
  fastify.delete('/:id/permissions/:permissionId', {
    schema: {
      tags: ['Jobs'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          permissionId: { type: 'string', format: 'uuid' },
        },
        required: ['id', 'permissionId'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id, permissionId } = request.params as { id: string; permissionId: string };
    const user = request.user!;

    const job = await fastify.prisma.job.findUnique({
      where: { id },
      include: {
        publisher: {
          select: { companyId: true },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // Check permissions
    const canRevoke = 
      user.role === UserRole.PLATFORM_ADMIN ||
      job.publisherId === user.id ||
      (user.companyId && job.publisher.companyId === user.companyId);

    if (!canRevoke) {
      throw new ForbiddenError('Access denied to revoke job permissions');
    }

    const permission = await fastify.prisma.jobPermission.findUnique({
      where: { id: permissionId },
    });

    if (!permission || permission.jobId !== id) {
      throw new NotFoundError('Permission not found');
    }

    await fastify.prisma.jobPermission.delete({
      where: { id: permissionId },
    });

    reply.send({ message: 'Permission revoked successfully' });
  });

  // Get jobs shared with me
  fastify.get('/shared', {
    schema: {
      tags: ['Jobs'],
      security: [{ Bearer: [] }],
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
    const { page = 1, limit = 20 } = request.query as any;
    const skip = (page - 1) * limit;
    const user = request.user!;

    const where = {
      jobPermissions: {
        some: {
          OR: [
            { grantedToUserId: user.id },
            { grantedToCompanyId: user.companyId || 'no-company' },
          ],
          OR: [
            { expiresAt: null },
            { expiresAt: { gt: new Date() } },
          ],
        },
      },
    };

    const [jobs, total] = await Promise.all([
      fastify.prisma.job.findMany({
        where,
        skip,
        take: limit,
        include: {
          publisher: {
            select: {
              id: true,
              username: true,
              email: true,
              company: {
                select: {
                  id: true,
                  name: true,
                },
              },
            },
          },
          companyClient: {
            select: {
              id: true,
              name: true,
              industry: true,
              location: true,
            },
          },
          jobPermissions: {
            where: {
              OR: [
                { grantedToUserId: user.id },
                { grantedToCompanyId: user.companyId || 'no-company' },
              ],
            },
            select: {
              id: true,
              grantedAt: true,
              expiresAt: true,
              grantedBy: {
                select: {
                  id: true,
                  username: true,
                },
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
      fastify.prisma.job.count({ where }),
    ]);

    reply.send({
      jobs,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  });

  // Batch share jobs with SOHO consultants
  fastify.post('/batch-share', {
    schema: {
      tags: ['Jobs'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        properties: {
          jobIds: { 
            type: 'array', 
            items: { type: 'string', format: 'uuid' },
            minItems: 1
          },
          targetUserId: { type: 'string', format: 'uuid' },
          targetCompanyId: { type: 'string', format: 'uuid' },
          expiresAt: { type: 'string', format: 'date-time' },
        },
        required: ['jobIds'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { jobIds, targetUserId, targetCompanyId, expiresAt } = request.body as any;
    const user = request.user!;

    if (!targetUserId && !targetCompanyId) {
      throw new ValidationError('Either targetUserId or targetCompanyId must be provided');
    }

    if (targetUserId && targetCompanyId) {
      throw new ValidationError('Cannot specify both targetUserId and targetCompanyId');
    }

    // Verify all jobs belong to user's company (except platform admin)
    const jobs = await fastify.prisma.job.findMany({
      where: {
        id: { in: jobIds },
        ...(user.role !== UserRole.PLATFORM_ADMIN && {
          publisher: { companyId: user.companyId }
        }),
        status: 'approved', // Only approved jobs can be shared with SOHO
      },
      include: {
        publisher: { select: { companyId: true } }
      }
    });

    if (jobs.length !== jobIds.length) {
      throw new ValidationError('Some jobs not found or not accessible');
    }

    const results = [];
    const errors = [];

    for (const job of jobs) {
      try {
        // Check if permission already exists
        const existingPermission = await fastify.prisma.jobPermission.findFirst({
          where: {
            jobId: job.id,
            grantedToUserId: targetUserId || undefined,
            grantedToCompanyId: targetCompanyId || undefined,
          },
        });

        if (existingPermission) {
          errors.push({ jobId: job.id, error: 'Permission already exists' });
          continue;
        }

        const permission = await fastify.prisma.jobPermission.create({
          data: {
            jobId: job.id,
            grantedToUserId: targetUserId,
            grantedToCompanyId: targetCompanyId,
            grantedById: user.id,
            expiresAt: expiresAt ? new Date(expiresAt) : undefined,
          },
        });

        results.push({ jobId: job.id, permissionId: permission.id });
      } catch (error) {
        errors.push({ jobId: job.id, error: 'Failed to create permission' });
      }
    }

    // Create notifications
    const targetUsers = [];
    if (targetUserId) {
      targetUsers.push(targetUserId);
    } else if (targetCompanyId) {
      const companyUsers = await fastify.prisma.user.findMany({
        where: { companyId: targetCompanyId },
        select: { id: true },
      });
      targetUsers.push(...companyUsers.map(u => u.id));
    }

    for (const userId of targetUsers) {
      await fastify.prisma.notification.create({
        data: {
          recipientId: userId,
          type: 'job_shared',
          title: 'Multiple Jobs Shared',
          content: `${results.length} jobs have been shared with you by ${user.username}`,
          relatedId: null,
        },
      });
    }

    reply.send({
      message: `Batch sharing completed: ${results.length} successful, ${errors.length} errors`,
      results,
      errors,
    });
  });

  // Public job sharing endpoint - no authentication required
  fastify.get('/share/:id', {
    schema: {
      tags: ['Jobs'],
      description: 'Get job details for public sharing (no authentication required)',
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
    },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };

    const job = await fastify.prisma.job.findUnique({
      where: { 
        id,
        // 只显示已审核通过且开放的职位
        status: { in: ['approved', 'open'] }
      },
      include: {
        publisher: {
          select: {
            id: true,
            username: true,
            email: true,
            company: {
              select: {
                id: true,
                name: true,
              },
            },
          },
        },
        companyClient: {
          select: {
            id: true,
            name: true,
            industry: true,
            location: true,
            contactName: true,
            contactPhone: true,
            contactEmail: true,
          },
        },
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found or not available for sharing');
    }

    // 返回公开分享的职位信息（隐藏敏感信息）
    const shareableJob = {
      id: job.id,
      title: job.title,
      industry: job.industry,
      location: job.location,
      salaryMin: job.salaryMin,
      salaryMax: job.salaryMax,
      description: job.description,
      requirements: job.requirements,
      benefits: job.benefits,
      urgency: job.urgency,
      reportTo: job.reportTo,
      status: job.status,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
      companyClient: {
        name: job.companyClient.name,
        industry: job.companyClient.industry,
        location: job.companyClient.location,
      },
      publisher: {
        username: job.publisher.username,
        email: job.publisher.email,
        company: job.publisher.company,
      },
    };

    reply.send({
      success: true,
      job: shareableJob,
    });
  });
};