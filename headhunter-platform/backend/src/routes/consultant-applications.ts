import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole } from '@/types';
import { NotFoundError, ForbiddenError } from '@/middleware/error';

const reviewApplicationSchema = z.object({
  action: z.enum(['approve', 'reject']),
  rejectReason: z.string().optional(),
});

export const consultantApplicationRoutes = async (fastify: FastifyInstance) => {
  // Get available companies for consultant application
  fastify.get('/companies', {
    schema: {
      tags: ['Consultant Applications'],
      querystring: {
        type: 'object',
        properties: {
          search: { type: 'string' },
        },
      },
    },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { search } = request.query as any;
    
    const where: any = {
      status: 'approved', // Only approved companies
    };

    if (search) {
      where.name = {
        contains: search,
        mode: 'insensitive',
      };
    }

    const companies = await fastify.prisma.company.findMany({
      where,
      select: {
        id: true,
        name: true,
        industry: true,
        scale: true,
      },
      orderBy: { name: 'asc' },
    });

    reply.send({ companies });
  });

  // Get applications for company admin to review
  fastify.get('/', {
    schema: {
      tags: ['Consultant Applications'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          status: { type: 'string', enum: ['pending', 'approved', 'rejected'] },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { status } = request.query as any;
    const user = request.user!;

    const where: any = {
      companyId: user.companyId,
    };

    if (status) {
      where.status = status;
    }

    const applications = await fastify.prisma.consultantApplication.findMany({
      where,
      include: {
        consultant: {
          select: {
            id: true,
            username: true,
            email: true,
            phone: true,
            createdAt: true,
          },
        },
        reviewedBy: {
          select: {
            id: true,
            username: true,
          },
        },
      },
      orderBy: { appliedAt: 'desc' },
    });

    reply.send({ applications });
  });

  // Review consultant application
  fastify.patch('/:id/review', {
    schema: {
      tags: ['Consultant Applications'],
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
          rejectReason: { type: 'string' },
        },
        required: ['action'],
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { id } = request.params as { id: string };
    const { action, rejectReason } = reviewApplicationSchema.parse(request.body);
    const user = request.user!;

    const application = await fastify.prisma.consultantApplication.findUnique({
      where: { id },
      include: {
        consultant: true,
        company: true,
      },
    });

    if (!application) {
      throw new NotFoundError('Application not found');
    }

    if (application.companyId !== user.companyId) {
      throw new ForbiddenError('Cannot review applications for other companies');
    }

    if (application.status !== 'pending') {
      throw new ForbiddenError('Application has already been reviewed');
    }

    const updatedApplication = await fastify.prisma.consultantApplication.update({
      where: { id },
      data: {
        status: action === 'approve' ? 'approved' : 'rejected',
        reviewedAt: new Date(),
        reviewedById: user.id,
        rejectReason: action === 'reject' ? rejectReason : null,
      },
    });

    // If approved, update consultant's company association
    if (action === 'approve') {
      await fastify.prisma.user.update({
        where: { id: application.consultantId },
        data: {
          companyId: application.companyId,
          status: 'active', // Activate the consultant
        },
      });
    }

    // TODO: Send notification to consultant

    reply.send({
      message: `Application ${action}ed successfully`,
      application: updatedApplication,
    });
  });
};