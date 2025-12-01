import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole, UserStatus } from '@/types';
import { NotFoundError, ForbiddenError } from '@/middleware/error';

const updateUserSchema = z.object({
  username: z.string().min(2).max(50).optional(),
  phone: z.string().min(10).max(20).optional(),
  status: z.enum([UserStatus.ACTIVE, UserStatus.SUSPENDED, UserStatus.INACTIVE]).optional(),
});

const bindCompanySchema = z.object({
  companyId: z.string().uuid(),
});

export const userRoutes = async (fastify: FastifyInstance) => {
  // Get all users (platform admin only)
  fastify.get('/', {
    schema: {
      tags: ['Users'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          role: { type: 'string', enum: ['platform_admin', 'company_admin', 'consultant', 'soho'] },
          status: { type: 'string', enum: ['pending', 'active', 'suspended', 'inactive'] },
          search: { type: 'string' },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { page = 1, limit = 20, role, status, search } = request.query as any;
    const skip = (page - 1) * limit;

    const where: any = {};
    if (role) where.role = role;
    if (status) where.status = status;
    if (search) {
      where.OR = [
        { username: { contains: search, mode: 'insensitive' } },
        { email: { contains: search, mode: 'insensitive' } },
        { phone: { contains: search } },
      ];
    }

    const [users, total] = await Promise.all([
      fastify.prisma.user.findMany({
        where,
        skip,
        take: limit,
        include: { company: true },
        orderBy: { createdAt: 'desc' },
      }),
      fastify.prisma.user.count({ where }),
    ]);

    reply.send({
      users: users.map(user => ({
        id: user.id,
        username: user.username,
        email: user.email,
        phone: user.phone,
        role: user.role,
        status: user.status,
        company: user.company,
        createdAt: user.createdAt,
        updatedAt: user.updatedAt,
      })),
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  });

  // Get user by ID
  fastify.get('/:id', {
    schema: {
      tags: ['Users'],
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

    // Users can view their own profile, admins can view any profile
    if (request.user!.id !== id && request.user!.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Access denied');
    }

    const user = await fastify.prisma.user.findUnique({
      where: { id },
      include: { company: true },
    });

    if (!user) {
      throw new NotFoundError('User not found');
    }

    reply.send(user);
  });

  // Update user
  fastify.patch('/:id', {
    schema: {
      tags: ['Users'],
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
          username: { type: 'string', minLength: 2, maxLength: 50 },
          phone: { type: 'string', minLength: 10, maxLength: 20 },
          status: { type: 'string', enum: ['active', 'suspended', 'inactive'] },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const body = updateUserSchema.parse(request.body);

    // Users can update their own profile (except status), admins can update any user
    const isOwnProfile = request.user!.id === id;
    const isAdmin = request.user!.role === UserRole.PLATFORM_ADMIN;

    if (!isOwnProfile && !isAdmin) {
      throw new ForbiddenError('Access denied');
    }

    // Only admins can change user status
    if (body.status && !isAdmin) {
      throw new ForbiddenError('Only administrators can change user status');
    }

    const user = await fastify.prisma.user.findUnique({
      where: { id },
    });

    if (!user) {
      throw new NotFoundError('User not found');
    }

    const updatedUser = await fastify.prisma.user.update({
      where: { id },
      data: body,
      include: { company: true },
    });

    reply.send(updatedUser);
  });

  // Request to bind to company (for consultants)
  fastify.post('/:id/bind-company', {
    schema: {
      tags: ['Users'],
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
          companyId: { type: 'string', format: 'uuid' },
        },
        required: ['companyId'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const body = bindCompanySchema.parse(request.body);

    // Users can only bind themselves, or company admins can bind users to their company
    const isOwnRequest = request.user!.id === id;
    const isCompanyAdmin = request.user!.role === UserRole.COMPANY_ADMIN && 
                           request.user!.companyId === body.companyId;

    if (!isOwnRequest && !isCompanyAdmin) {
      throw new ForbiddenError('Access denied');
    }

    const [user, company] = await Promise.all([
      fastify.prisma.user.findUnique({ where: { id } }),
      fastify.prisma.company.findUnique({ where: { id: body.companyId } }),
    ]);

    if (!user) {
      throw new NotFoundError('User not found');
    }

    if (!company) {
      throw new NotFoundError('Company not found');
    }

    if (user.companyId) {
      throw new ForbiddenError('User is already bound to a company');
    }

    const updatedUser = await fastify.prisma.user.update({
      where: { id },
      data: { companyId: body.companyId },
      include: { company: true },
    });

    reply.send({
      message: 'User successfully bound to company',
      user: {
        id: updatedUser.id,
        username: updatedUser.username,
        email: updatedUser.email,
        role: updatedUser.role,
        companyId: updatedUser.companyId,
        company: updatedUser.company,
      },
    });
  });

  // Unbind user from company
  fastify.delete('/:id/bind-company', {
    schema: {
      tags: ['Users'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
        required: ['id'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN, UserRole.COMPANY_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };

    const user = await fastify.prisma.user.findUnique({
      where: { id },
      include: { company: true },
    });

    if (!user) {
      throw new NotFoundError('User not found');
    }

    // Company admins can only unbind users from their own company
    if (request.user!.role === UserRole.COMPANY_ADMIN &&
        request.user!.companyId !== user.companyId) {
      throw new ForbiddenError('Access denied');
    }

    const updatedUser = await fastify.prisma.user.update({
      where: { id },
      data: { companyId: null },
    });

    reply.send({
      message: 'User successfully unbound from company',
      user: {
        id: updatedUser.id,
        username: updatedUser.username,
        email: updatedUser.email,
        role: updatedUser.role,
        companyId: updatedUser.companyId,
      },
    });
  });

  // Get company users (for company admins)
  fastify.get('/company/:companyId', {
    schema: {
      tags: ['Users'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          companyId: { type: 'string', format: 'uuid' },
        },
        required: ['companyId'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireCompanyAccess],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { companyId } = request.params as { companyId: string };

    const users = await fastify.prisma.user.findMany({
      where: { companyId },
      select: {
        id: true,
        username: true,
        email: true,
        phone: true,
        role: true,
        status: true,
        createdAt: true,
      },
      orderBy: { createdAt: 'desc' },
    });

    reply.send({ users });
  });

  // Get pending consultants for company admin to approve
  fastify.get('/pending-consultants', {
    schema: {
      tags: ['Users'],
      security: [{ Bearer: [] }],
      response: {
        200: {
          type: 'object',
          properties: {
            users: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  id: { type: 'string' },
                  username: { type: 'string' },
                  email: { type: 'string' },
                  phone: { type: 'string' },
                  role: { type: 'string' },
                  status: { type: 'string' },
                  createdAt: { type: 'string' },
                },
              },
            },
          },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    // Get pending consultants that are not yet bound to any company
    const pendingConsultants = await fastify.prisma.user.findMany({
      where: {
        status: UserStatus.PENDING,
        role: UserRole.CONSULTANT,
        companyId: null, // Only unbound consultants
      },
      select: {
        id: true,
        username: true,
        email: true,
        phone: true,
        role: true,
        status: true,
        createdAt: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    reply.send({
      users: pendingConsultants,
    });
  });

  // Approve consultant and bind to company (company admin only)
  fastify.patch('/approve-consultant/:userId', {
    schema: {
      tags: ['Users'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          userId: { type: 'string', format: 'uuid' },
        },
        required: ['userId'],
      },
      body: {
        type: 'object',
        properties: {
          action: { type: 'string', enum: ['approve', 'reject'] },
          reason: { type: 'string' },
        },
        required: ['action'],
      },
      response: {
        200: {
          type: 'object',
          properties: {
            message: { type: 'string' },
            user: {
              type: 'object',
              properties: {
                id: { type: 'string' },
                status: { type: 'string' },
                companyId: { type: 'string', nullable: true },
              },
            },
          },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { userId } = request.params as { userId: string };
    const { action, reason } = request.body as { action: 'approve' | 'reject'; reason?: string };

    const user = await fastify.prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      throw new NotFoundError('User not found');
    }

    if (user.status !== UserStatus.PENDING) {
      throw new ValidationError('User is not pending approval');
    }

    if (user.role !== UserRole.CONSULTANT) {
      throw new ValidationError('Only consultants can be approved through this endpoint');
    }

    if (user.companyId) {
      throw new ValidationError('Consultant is already bound to a company');
    }

    const newStatus = action === 'approve' ? UserStatus.ACTIVE : UserStatus.INACTIVE;
    const companyId = action === 'approve' ? request.user!.companyId : null;
    
    const updatedUser = await fastify.prisma.user.update({
      where: { id: userId },
      data: { 
        status: newStatus,
        companyId: companyId
      },
    });

    // TODO: Send notification email to consultant

    reply.send({
      message: `Consultant ${action}ed successfully${action === 'approve' ? ' and bound to company' : ''}`,
      user: {
        id: updatedUser.id,
        status: updatedUser.status,
        companyId: updatedUser.companyId,
      },
    });
  });

  // Get consultants (both company consultants and SOHO) for job assignment
  fastify.get('/consultants', {
    schema: {
      tags: ['Users'],
      security: [{ Bearer: [] }],
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            consultants: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  id: { type: 'string' },
                  username: { type: 'string' },
                  email: { type: 'string' },
                  role: { type: 'string' },
                  companyId: { type: 'string', format: 'uuid' },
                }
              }
            }
          }
        }
      }
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const user = request.user!;

    try {
      const baseWhere = {
        status: UserStatus.ACTIVE,
      };

      let where;
      if (user.role === UserRole.COMPANY_ADMIN) {
        // Company admin sees own company consultants and all SOHO
        where = {
          ...baseWhere,
          OR: [
            { companyId: user.companyId, role: UserRole.CONSULTANT },
            { role: UserRole.SOHO }
          ]
        };
      } else {
        // Platform admin or others see all consultants and SOHO
        where = {
          ...baseWhere,
          OR: [
            { role: UserRole.CONSULTANT },
            { role: UserRole.SOHO }
          ]
        };
      }

      const consultants = await fastify.prisma.user.findMany({
        where,
        select: {
          id: true,
          username: true,
          email: true,
          role: true,
          companyId: true,
        },
        orderBy: { username: 'asc' }
      });

      reply.send({
        success: true,
        consultants
      });
    } catch (error) {
      console.error('Error fetching consultants:', error);
      reply.status(500).send({
        success: false,
        message: 'Failed to fetch consultants'
      });
    }
  });

  // Get SOHO consultants for job assignment
  fastify.get('/soho-consultants', {
    schema: {
      tags: ['Users'],
      security: [{ Bearer: [] }],
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  id: { type: 'string' },
                  username: { type: 'string' },
                  email: { type: 'string' },
                  profile: {
                    type: 'object',
                    properties: {
                      specialization: { type: 'string' },
                      experience: { type: 'string' }
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN, UserRole.COMPANY_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const sohoConsultants = await fastify.prisma.user.findMany({
        where: {
          role: UserRole.SOHO,
          status: 'active'
        },
        select: {
          id: true,
          username: true,
          email: true
        },
        orderBy: {
          username: 'asc'
        }
      });

      reply.send({
        success: true,
        data: sohoConsultants
      });
    } catch (error) {
      fastify.log.error(error);
      reply.status(500).send({
        success: false,
        message: 'Failed to fetch SOHO consultants'
      });
    }
  });
};