import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import bcrypt from 'bcryptjs';
import { z } from 'zod';
import { UserRole, UserStatus } from '@/types';
import { ValidationError, UnauthorizedError, ConflictError, NotFoundError } from '@/middleware/error';

const registerSchema = z.object({
  username: z.string().min(2).max(50),
  email: z.string().email(),
  phone: z.string().min(10).max(20),
  password: z.string().min(6),
  role: z.enum([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT, UserRole.SOHO]),
  companyName: z.string().optional(),
  businessLicense: z.string().optional(),
  companyId: z.string().uuid().optional(),
  applicationReason: z.string().optional(),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

export const authRoutes = async (fastify: FastifyInstance) => {
  // Register user
  fastify.post('/register', {
    schema: {
      tags: ['Authentication'],
      body: {
        type: 'object',
        required: ['username', 'email', 'phone', 'password', 'role'],
        properties: {
          username: { type: 'string', minLength: 2, maxLength: 50 },
          email: { type: 'string', format: 'email' },
          phone: { type: 'string', minLength: 10, maxLength: 20 },
          password: { type: 'string', minLength: 6 },
          role: { type: 'string', enum: ['company_admin', 'consultant', 'soho'] },
          companyName: { type: 'string' },
          businessLicense: { type: 'string' },
          companyId: { type: 'string', format: 'uuid' },
          applicationReason: { type: 'string' },
        },
      },
      response: {
        201: {
          type: 'object',
          properties: {
            message: { type: 'string' },
            userId: { type: 'string' },
          },
        },
      },
    },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = registerSchema.parse(request.body);

    // Check if user already exists
    const existingUser = await fastify.prisma.user.findFirst({
      where: {
        OR: [
          { email: body.email },
          { phone: body.phone },
        ],
      },
    });

    if (existingUser) {
      throw new ConflictError('User with this email or phone already exists');
    }

    const hashedPassword = await bcrypt.hash(body.password, 10);

    // If registering as company admin, create company first
    let companyId: string | undefined;
    if (body.role === UserRole.COMPANY_ADMIN && body.companyName && body.businessLicense) {
      const company = await fastify.prisma.company.create({
        data: {
          name: body.companyName,
          businessLicense: body.businessLicense,
          contactName: body.username,
          contactPhone: body.phone,
          contactEmail: body.email,
          status: 'pending',
        },
      });
      companyId = company.id;
    }

    const user = await fastify.prisma.user.create({
      data: {
        username: body.username,
        email: body.email,
        phone: body.phone,
        password: hashedPassword,
        role: body.role,
        status: UserStatus.PENDING,
        companyId,
      },
    });

    // If consultant is applying to join an existing company, create application
    if (body.role === UserRole.CONSULTANT && body.companyId) {
      // Verify the company exists and is approved
      const targetCompany = await fastify.prisma.company.findUnique({
        where: { id: body.companyId },
      });

      if (!targetCompany) {
        throw new NotFoundError('Selected company not found');
      }

      if (targetCompany.status !== 'approved') {
        throw new ValidationError('Cannot apply to a company that is not approved');
      }

      // Create consultant application
      await fastify.prisma.consultantApplication.create({
        data: {
          consultantId: user.id,
          companyId: body.companyId,
          reason: body.applicationReason || null,
          status: 'pending',
        },
      });

      // TODO: Send notification to company admins
    }

    reply.status(201).send({
      message: 'User registered successfully. Please wait for approval.',
    });
  });

  // Login user
  fastify.post('/login', {
    schema: {
      tags: ['Authentication'],
      body: {
        type: 'object',
        required: ['email', 'password'],
        properties: {
          email: { type: 'string', format: 'email' },
          password: { type: 'string' },
        },
      },
      response: {
        200: {
          type: 'object',
          properties: {
            token: { type: 'string' },
            user: {
              type: 'object',
              properties: {
                id: { type: 'string' },
                username: { type: 'string' },
                email: { type: 'string' },
                role: { type: 'string' },
                status: { type: 'string' },
                companyId: { type: 'string', nullable: true },
              },
            },
          },
        },
      },
    },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = loginSchema.parse(request.body);

    const user = await fastify.prisma.user.findUnique({
      where: { email: body.email },
      include: { company: true },
    });

    if (!user) {
      throw new UnauthorizedError('Invalid email or password');
    }

    if (user.status !== UserStatus.ACTIVE) {
      throw new UnauthorizedError('Account is not active. Please wait for approval or contact support.');
    }

    const passwordMatch = await bcrypt.compare(body.password, user.password);
    if (!passwordMatch) {
      throw new UnauthorizedError('Invalid email or password');
    }

    const token = fastify.jwt.sign({
      id: user.id,
      email: user.email,
      role: user.role,
      companyId: user.companyId,
    });

    reply.send({
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        status: user.status,
        companyId: user.companyId,
        company: user.company,
      },
    });
  });

  // Get current user profile
  fastify.get('/profile', {
    schema: {
      tags: ['Authentication'],
      security: [{ Bearer: [] }],
      response: {
        200: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            username: { type: 'string' },
            email: { type: 'string' },
            phone: { type: 'string' },
            role: { type: 'string' },
            status: { type: 'string' },
            companyId: { type: 'string', nullable: true },
            company: {
              type: 'object',
              nullable: true,
              properties: {
                id: { type: 'string' },
                name: { type: 'string' },
                status: { type: 'string' },
              },
            },
          },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const user = await fastify.prisma.user.findUnique({
      where: { id: request.user!.id },
      select: {
        id: true,
        username: true,
        email: true,
        phone: true,
        role: true,
        status: true,
        companyId: true,
        company: {
          select: {
            id: true,
            name: true,
            status: true,
          },
        },
        createdAt: true,
        updatedAt: true,
      },
    });

    reply.send(user);
  });

  // Refresh token
  fastify.post('/refresh', {
    schema: {
      tags: ['Authentication'],
      security: [{ Bearer: [] }],
      response: {
        200: {
          type: 'object',
          properties: {
            token: { type: 'string' },
          },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const token = fastify.jwt.sign({
      id: request.user!.id,
      email: request.user!.email,
      role: request.user!.role,
      companyId: request.user!.companyId,
    });

    reply.send({ token });
  });

  // Logout (for completeness, mainly clears client-side token)
  fastify.post('/logout', {
    schema: {
      tags: ['Authentication'],
      security: [{ Bearer: [] }],
      response: {
        200: {
          type: 'object',
          properties: {
            message: { type: 'string' },
          },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    reply.send({ message: 'Logged out successfully' });
  });

  // Get pending users (platform admin only - excludes consultants)
  fastify.get('/pending-users', {
    schema: {
      tags: ['Authentication'],
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
                  company: {
                    type: 'object',
                    nullable: true,
                    properties: {
                      id: { type: 'string' },
                      name: { type: 'string' },
                      status: { type: 'string' },
                    },
                  },
                  createdAt: { type: 'string' },
                },
              },
            },
          },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    // Platform admin only reviews company_admin and soho, not consultants
    const pendingUsers = await fastify.prisma.user.findMany({
      where: {
        status: UserStatus.PENDING,
        role: {
          in: [UserRole.COMPANY_ADMIN, UserRole.SOHO] // Exclude consultants
        }
      },
      include: {
        company: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    reply.send({
      users: pendingUsers.map(user => ({
        id: user.id,
        username: user.username,
        email: user.email,
        phone: user.phone,
        role: user.role,
        status: user.status,
        company: user.company,
        createdAt: user.createdAt,
      })),
    });
  });

  // Approve or reject user (platform admin only - for company_admin and soho only)
  fastify.patch('/approve-user/:userId', {
    schema: {
      tags: ['Authentication'],
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
              },
            },
          },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
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

    // Platform admin can only approve company_admin and soho, not consultants
    if (user.role === UserRole.CONSULTANT) {
      throw new ValidationError('Consultants should be approved by company admins, not platform admin');
    }

    const newStatus = action === 'approve' ? UserStatus.ACTIVE : UserStatus.INACTIVE;
    
    const updatedUser = await fastify.prisma.user.update({
      where: { id: userId },
      data: { status: newStatus },
    });

    // Also approve associated company if user is company_admin
    if (action === 'approve' && user.role === UserRole.COMPANY_ADMIN && user.companyId) {
      await fastify.prisma.company.update({
        where: { id: user.companyId },
        data: { status: 'approved' },
      });
    }

    // TODO: Send notification email to user

    reply.send({
      message: `User ${action}ed successfully`,
      user: {
        id: updatedUser.id,
        status: updatedUser.status,
      },
    });
  });
};