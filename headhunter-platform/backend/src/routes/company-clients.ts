import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole, CompanyClientStatus } from '@/types';
import { NotFoundError, ForbiddenError } from '@/middleware/error';

const createCompanyClientSchema = z.object({
  name: z.string().min(1).max(255),
  industry: z.string().max(100).optional(),
  size: z.string().max(50).optional(),
  contactName: z.string().min(1).max(100),
  contactPhone: z.string().min(1).max(20),
  contactEmail: z.string().email().or(z.literal('')).optional(),
  location: z.string().max(255).optional(),
  tags: z.array(z.string()).optional(),
});

const updateCompanyClientSchema = createCompanyClientSchema.partial();

const updateStatusSchema = z.object({
  status: z.enum(['active', 'suspended', 'terminated']),
  reason: z.string().optional(),
});

export const companyClientRoutes = async (fastify: FastifyInstance) => {
  // Get all company clients
  fastify.get('/', {
    schema: {
      tags: ['Company Clients'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          industry: { type: 'string' },
          location: { type: 'string' },
          search: { type: 'string' },
          status: { type: 'string', enum: ['active', 'suspended', 'terminated'] },
          maintainerId: { type: 'string', format: 'uuid' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const {
      page = 1,
      limit = 20,
      industry,
      location,
      search,
      status,
      maintainerId
    } = request.query as any;

    const skip = (page - 1) * limit;
    const where: any = {};

    // Apply filters
    if (industry) where.industry = { contains: industry, mode: 'insensitive' };
    if (location) where.location = { contains: location, mode: 'insensitive' };
    if (status) where.status = status;
    if (maintainerId) where.maintainerId = maintainerId;

    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { contactName: { contains: search, mode: 'insensitive' } },
        { contactEmail: { contains: search, mode: 'insensitive' } },
      ];
    }

    // Role-based access control
    const user = request.user!;
    if (user.role === UserRole.COMPANY_ADMIN || user.role === UserRole.CONSULTANT) {
      if (user.companyId) {
        // Show company clients that are partnered with the user's company
        where.partnerCompanyId = user.companyId;
      } else {
        where.id = 'non-existent-id';
      }
    } else if (user.role === UserRole.SOHO) {
      // SOHO users can only see their own maintained clients
      where.maintainerId = user.id;
    }
    // Platform admins can see all clients

    const [companyClients, total] = await Promise.all([
      fastify.prisma.companyClient.findMany({
        where,
        skip,
        take: limit,
        include: {
          maintainer: {
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
          partnerCompany: {
            select: {
              id: true,
              name: true,
            },
          },
          _count: {
            select: {
              jobs: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
      }),
      fastify.prisma.companyClient.count({ where }),
    ]);

    reply.send({
      companyClients,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  });

  // Get company client by ID
  fastify.get('/:id', {
    schema: {
      tags: ['Company Clients'],
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

    const companyClient = await fastify.prisma.companyClient.findUnique({
      where: { id },
      include: {
        maintainer: {
          select: {
            id: true,
            username: true,
            email: true,
            companyId: true,
            company: {
              select: {
                id: true,
                name: true,
              },
            },
          },
        },
        partnerCompany: {
          select: {
            id: true,
            name: true,
          },
        },
        jobs: {
          select: {
            id: true,
            title: true,
            status: true,
            createdAt: true,
            publisher: {
              select: {
                id: true,
                username: true,
              },
            },
          },
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    if (!companyClient) {
      throw new NotFoundError('Company client not found');
    }

    // Check access permissions  
    const hasAccess = 
      user.role === UserRole.PLATFORM_ADMIN ||
      companyClient.maintainerId === user.id ||
      (user.companyId && companyClient.partnerCompanyId === user.companyId);

    if (!hasAccess) {
      throw new ForbiddenError('Access denied to this company client');
    }

    reply.send(companyClient);
  });

  // Create new company client
  fastify.post('/', {
    schema: {
      tags: ['Company Clients'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['name', 'contactName', 'contactPhone'],
        properties: {
          name: { type: 'string', minLength: 1, maxLength: 255 },
          industry: { type: 'string', maxLength: 100 },
          size: { type: 'string', maxLength: 50 },
          contactName: { type: 'string', minLength: 1, maxLength: 100 },
          contactPhone: { type: 'string', minLength: 1, maxLength: 20 },
          contactEmail: { type: 'string' },
          location: { type: 'string', maxLength: 255 },
          tags: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = createCompanyClientSchema.parse(request.body);
    const user = request.user!;

    const companyClient = await fastify.prisma.companyClient.create({
      data: {
        ...body,
        contactEmail: body.contactEmail === '' ? null : body.contactEmail,
        tags: body.tags || [],
        maintainerId: user.id,
        partnerCompanyId: user.companyId || (
          // For SOHO users without company, create a default partnership
          await fastify.prisma.company.findFirst({
            where: { status: 'approved' },
            select: { id: true }
          })?.id
        ),
      },
      include: {
        maintainer: {
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
        partnerCompany: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    reply.status(201).send(companyClient);
  });

  // Update company client
  fastify.patch('/:id', {
    schema: {
      tags: ['Company Clients'],
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
    const body = updateCompanyClientSchema.parse(request.body);
    const user = request.user!;

    const companyClient = await fastify.prisma.companyClient.findUnique({
      where: { id },
      include: {
        maintainer: {
          select: {
            companyId: true,
          },
        },
      },
    });

    if (!companyClient) {
      throw new NotFoundError('Company client not found');
    }

    // Check permissions
    const canEdit = 
      user.role === UserRole.PLATFORM_ADMIN ||
      companyClient.maintainerId === user.id ||
      (user.companyId && companyClient.partnerCompanyId === user.companyId);

    if (!canEdit) {
      throw new ForbiddenError('Access denied to edit this company client');
    }

    const updatedCompanyClient = await fastify.prisma.companyClient.update({
      where: { id },
      data: body,
      include: {
        maintainer: {
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
        partnerCompany: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    reply.send(updatedCompanyClient);
  });

  // Update company client status
  fastify.patch('/:id/status', {
    schema: {
      tags: ['Company Clients'],
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
          status: { type: 'string', enum: ['active', 'suspended', 'terminated'] },
          reason: { type: 'string' },
        },
        required: ['status'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { status, reason } = updateStatusSchema.parse(request.body);
    const user = request.user!;

    const companyClient = await fastify.prisma.companyClient.findUnique({
      where: { id },
      include: {
        maintainer: {
          select: {
            companyId: true,
          },
        },
      },
    });

    if (!companyClient) {
      throw new NotFoundError('Company client not found');
    }

    // Check permissions - only company admins can change client status
    const canChangeStatus = 
      user.role === UserRole.PLATFORM_ADMIN ||
      (user.role === UserRole.COMPANY_ADMIN && user.companyId && companyClient.partnerCompanyId === user.companyId);

    if (!canChangeStatus) {
      throw new ForbiddenError('Access denied to change client status');
    }

    const updatedCompanyClient = await fastify.prisma.companyClient.update({
      where: { id },
      data: { status },
      include: {
        maintainer: {
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
        partnerCompany: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    reply.send({
      message: `Client status updated to ${status}`,
      client: updatedCompanyClient,
    });
  });

  // Delete company client
  fastify.delete('/:id', {
    schema: {
      tags: ['Company Clients'],
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

    const companyClient = await fastify.prisma.companyClient.findUnique({
      where: { id },
      include: {
        maintainer: {
          select: {
            companyId: true,
          },
        },
        _count: {
          select: {
            jobs: true,
          },
        },
      },
    });

    if (!companyClient) {
      throw new NotFoundError('Company client not found');
    }

    // Check permissions
    const canDelete = 
      user.role === UserRole.PLATFORM_ADMIN ||
      companyClient.maintainerId === user.id ||
      (user.companyId && companyClient.partnerCompanyId === user.companyId);

    if (!canDelete) {
      throw new ForbiddenError('Access denied to delete this company client');
    }

    // Check if client has jobs
    if (companyClient._count.jobs > 0) {
      throw new ForbiddenError('Cannot delete company client with existing jobs');
    }

    await fastify.prisma.companyClient.delete({
      where: { id },
    });

    reply.send({
      message: 'Company client deleted successfully',
    });
  });
};