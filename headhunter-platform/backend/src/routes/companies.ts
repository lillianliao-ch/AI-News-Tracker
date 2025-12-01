import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole, CompanyStatus } from '@/types';
import { NotFoundError, ForbiddenError } from '@/middleware/error';

const createCompanySchema = z.object({
  name: z.string().min(1).max(255),
  businessLicense: z.string().optional(),
  industry: z.string().max(100).optional(),
  scale: z.string().max(50).optional(),
  contactName: z.string().max(100).optional(),
  contactPhone: z.string().max(20).optional(),
  contactEmail: z.string().email().optional(),
  address: z.string().optional(),
});

const updateCompanySchema = createCompanySchema.partial();

const approveCompanySchema = z.object({
  action: z.enum(['approve', 'reject']),
  reason: z.string().optional(),
});

export const companyRoutes = async (fastify: FastifyInstance) => {
  // Get all companies (admin only)
  fastify.get('/', {
    schema: {
      tags: ['Companies'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          status: { type: 'string', enum: ['pending', 'approved', 'rejected', 'suspended'] },
          search: { type: 'string' },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { page = 1, limit = 20, status, search } = request.query as any;
    const skip = (page - 1) * limit;

    const where: any = {};
    if (status) where.status = status;
    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { contactName: { contains: search, mode: 'insensitive' } },
        { contactEmail: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [companies, total] = await Promise.all([
      fastify.prisma.company.findMany({
        where,
        skip,
        take: limit,
        include: {
          users: {
            select: {
              id: true,
              username: true,
              email: true,
              role: true,
              status: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
      }),
      fastify.prisma.company.count({ where }),
    ]);

    reply.send({
      companies,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  });

  // Get pending companies
  fastify.get('/pending', {
    schema: {
      tags: ['Companies'],
      security: [{ Bearer: [] }],
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const pendingCompanies = await fastify.prisma.company.findMany({
      where: {
        status: CompanyStatus.PENDING,
      },
      include: {
        users: {
          select: {
            id: true,
            username: true,
            email: true,
            role: true,
            status: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    reply.send({ companies: pendingCompanies });
  });

  // Get company by ID
  fastify.get('/:id', {
    schema: {
      tags: ['Companies'],
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

    // Check access permissions
    if (request.user!.role !== UserRole.PLATFORM_ADMIN && request.user!.companyId !== id) {
      throw new ForbiddenError('Access denied to this company');
    }

    const company = await fastify.prisma.company.findUnique({
      where: { id },
      include: {
        users: {
          select: {
            id: true,
            username: true,
            email: true,
            phone: true,
            role: true,
            status: true,
            createdAt: true,
          },
        },
      },
    });

    if (!company) {
      throw new NotFoundError('Company not found');
    }

    reply.send(company);
  });

  // Create company (platform admin only)
  fastify.post('/', {
    schema: {
      tags: ['Companies'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['name'],
        properties: {
          name: { type: 'string', minLength: 1, maxLength: 255 },
          businessLicense: { type: 'string' },
          industry: { type: 'string', maxLength: 100 },
          scale: { type: 'string', maxLength: 50 },
          contactName: { type: 'string', maxLength: 100 },
          contactPhone: { type: 'string', maxLength: 20 },
          contactEmail: { type: 'string', format: 'email' },
          address: { type: 'string' },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = createCompanySchema.parse(request.body);

    const company = await fastify.prisma.company.create({
      data: {
        ...body,
        status: CompanyStatus.APPROVED, // Direct approval for admin-created companies
      },
    });

    reply.status(201).send(company);
  });

  // Update company
  fastify.patch('/:id', {
    schema: {
      tags: ['Companies'],
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
    const body = updateCompanySchema.parse(request.body);

    // Check access permissions
    if (request.user!.role !== UserRole.PLATFORM_ADMIN && request.user!.companyId !== id) {
      throw new ForbiddenError('Access denied to this company');
    }

    const company = await fastify.prisma.company.findUnique({
      where: { id },
    });

    if (!company) {
      throw new NotFoundError('Company not found');
    }

    const updatedCompany = await fastify.prisma.company.update({
      where: { id },
      data: body,
    });

    reply.send(updatedCompany);
  });

  // Approve or reject company (platform admin only)
  fastify.patch('/:id/approve', {
    schema: {
      tags: ['Companies'],
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
          action: { type: 'string', enum: ['approve', 'reject'] },
          reason: { type: 'string' },
        },
        required: ['action'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { action, reason } = approveCompanySchema.parse(request.body);

    const company = await fastify.prisma.company.findUnique({
      where: { id },
    });

    if (!company) {
      throw new NotFoundError('Company not found');
    }

    const newStatus = action === 'approve' ? CompanyStatus.APPROVED : CompanyStatus.REJECTED;
    
    const updatedCompany = await fastify.prisma.company.update({
      where: { id },
      data: { status: newStatus },
    });

    // Also update company admin status if approving
    if (action === 'approve') {
      await fastify.prisma.user.updateMany({
        where: {
          companyId: id,
          role: UserRole.COMPANY_ADMIN,
        },
        data: {
          status: 'active',
        },
      });
    }

    // TODO: Send notification to company admin

    reply.send({
      message: `Company ${action}ed successfully`,
      company: updatedCompany,
    });
  });

  // Get company statistics
  fastify.get('/:id/stats', {
    schema: {
      tags: ['Companies'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireCompanyAccess],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };

    const [
      totalUsers,
      activeUsers,
      totalJobs,
      activeJobs,
      totalSubmissions,
      totalCandidates,
    ] = await Promise.all([
      fastify.prisma.user.count({ where: { companyId: id } }),
      fastify.prisma.user.count({ where: { companyId: id, status: 'active' } }),
      fastify.prisma.job.count({ where: { publisher: { companyId: id } } }),
      fastify.prisma.job.count({ where: { publisher: { companyId: id }, status: 'open' } }),
      fastify.prisma.candidateSubmission.count({ where: { submitter: { companyId: id } } }),
      fastify.prisma.candidate.count({ where: { maintainer: { companyId: id } } }),
    ]);

    reply.send({
      users: { total: totalUsers, active: activeUsers },
      jobs: { total: totalJobs, active: activeJobs },
      submissions: totalSubmissions,
      candidates: totalCandidates,
    });
  });
};