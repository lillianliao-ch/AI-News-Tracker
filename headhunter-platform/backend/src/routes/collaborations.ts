import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole, NotificationType } from '@/types';
import { NotFoundError, ForbiddenError } from '@/middleware/error';
import { notificationService } from '@/services/notificationService';

const createNotificationSchema = z.object({
  recipientId: z.string().uuid(),
  type: z.enum([
    NotificationType.JOB_SHARED,
    NotificationType.JOB_CLOSED,
    NotificationType.SUBMISSION_STATUS_CHANGED,
    NotificationType.MAINTAINER_CHANGE_REQUEST,
    NotificationType.SYSTEM_ANNOUNCEMENT,
  ]),
  title: z.string().min(1).max(200),
  content: z.string().min(1),
  relatedId: z.string().uuid().optional(),
});

const markReadSchema = z.object({
  notificationIds: z.array(z.string().uuid()),
});

export const collaborationRoutes = async (fastify: FastifyInstance) => {
  // Get notifications for current user
  fastify.get('/notifications', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          unreadOnly: { type: 'boolean', default: false },
          type: { type: 'string', enum: ['job_shared', 'job_closed', 'submission_status_changed', 'maintainer_change_request', 'system_announcement'] },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { page = 1, limit = 20, unreadOnly = false, type } = request.query as any;
    const user = request.user!;

    const filters = {
      recipientId: user.id,
      isRead: unreadOnly ? false : undefined,
      type: type as NotificationType,
    };

    const result = await notificationService.getNotifications(filters, { page, limit });
    reply.send(result);
  });

  // Mark notifications as read
  fastify.patch('/notifications/mark-read', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['notificationIds'],
        properties: {
          notificationIds: { type: 'array', items: { type: 'string', format: 'uuid' } },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = markReadSchema.parse(request.body);
    const user = request.user!;

    await notificationService.markAsRead(body.notificationIds, user.id);
    reply.send({ message: 'Notifications marked as read' });
  });

  // Mark all notifications as read
  fastify.patch('/notifications/mark-all-read', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const user = request.user!;
    
    await notificationService.markAllAsRead(user.id);
    reply.send({ message: 'All notifications marked as read' });
  });

  // Create notification (admin only)
  fastify.post('/notifications', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['recipientId', 'type', 'title', 'content'],
        properties: {
          recipientId: { type: 'string', format: 'uuid' },
          type: { 
            type: 'string', 
            enum: ['job_shared', 'job_closed', 'submission_status_changed', 'maintainer_change_request', 'system_announcement'] 
          },
          title: { type: 'string', minLength: 1, maxLength: 200 },
          content: { type: 'string', minLength: 1 },
          relatedId: { type: 'string', format: 'uuid' },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = createNotificationSchema.parse(request.body);

    const notification = await notificationService.createNotification(body);
    reply.status(201).send(notification);
  });

  // Get notification statistics
  fastify.get('/notifications/stats', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const user = request.user!;
    
    const stats = await notificationService.getNotificationStats(user.id);
    reply.send(stats);
  });

  // Delete notification
  fastify.delete('/notifications/:id', {
    schema: {
      tags: ['Collaborations'],
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

    const result = await notificationService.deleteNotification(id, user.id);
    
    if (result.count === 0) {
      throw new NotFoundError('Notification not found or already deleted');
    }

    reply.send({ message: 'Notification deleted successfully' });
  });

  // Create system announcement (admin only)
  fastify.post('/notifications/system-announcement', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['title', 'content'],
        properties: {
          title: { type: 'string', minLength: 1, maxLength: 200 },
          content: { type: 'string', minLength: 1 },
          targetRole: { 
            type: 'string', 
            enum: ['platform_admin', 'company_admin', 'consultant', 'soho'],
          },
          targetCompanyId: { type: 'string', format: 'uuid' },
        },
      },
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { title, content, targetRole, targetCompanyId } = request.body as any;

    // Get target users
    const where: any = {};
    if (targetRole) where.role = targetRole;
    if (targetCompanyId) where.companyId = targetCompanyId;

    const targetUsers = await fastify.prisma.user.findMany({
      where,
      select: { id: true },
    });

    const recipientIds = targetUsers.map(user => user.id);

    await notificationService.createSystemAnnouncement(recipientIds, title, content);

    reply.status(201).send({
      message: `System announcement sent to ${recipientIds.length} users`,
      recipientCount: recipientIds.length,
    });
  });

  // Get collaboration statistics
  fastify.get('/stats', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const userId = request.user!.id;
    const companyId = request.user!.companyId;

    // Get user-specific stats
    const [
      myJobsCount,
      mySubmissionsCount,
      myCandidatesCount,
      collaborationsReceivedCount,
      collaborationsSentCount,
      recentNotificationsCount,
    ] = await Promise.all([
      // Jobs I published
      fastify.prisma.job.count({
        where: { publisherId: userId },
      }),
      // Candidate submissions I made
      fastify.prisma.candidateSubmission.count({
        where: { submitterId: userId },
      }),
      // Candidates I maintain
      fastify.prisma.candidate.count({
        where: { maintainerId: userId },
      }),
      // Jobs shared with me or my company
      fastify.prisma.jobPermission.count({
        where: {
          OR: [
            { grantedToUserId: userId },
            { grantedToCompanyId: companyId || 'no-company' },
          ],
        },
      }),
      // Jobs I shared with others
      fastify.prisma.jobPermission.count({
        where: { grantedById: userId },
      }),
      // Unread notifications in the last 7 days
      fastify.prisma.notification.count({
        where: {
          recipientId: userId,
          isRead: false,
          createdAt: {
            gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
          },
        },
      }),
    ]);

    // Get recent activity (last 30 days)
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    const [
      recentJobsPublished,
      recentSubmissions,
      recentCandidatesAdded,
    ] = await Promise.all([
      fastify.prisma.job.count({
        where: {
          publisherId: userId,
          createdAt: { gte: thirtyDaysAgo },
        },
      }),
      fastify.prisma.candidateSubmission.count({
        where: {
          submitterId: userId,
          createdAt: { gte: thirtyDaysAgo },
        },
      }),
      fastify.prisma.candidate.count({
        where: {
          maintainerId: userId,
          createdAt: { gte: thirtyDaysAgo },
        },
      }),
    ]);

    reply.send({
      overview: {
        totalJobs: myJobsCount,
        totalSubmissions: mySubmissionsCount,
        totalCandidates: myCandidatesCount,
        collaborationsReceived: collaborationsReceivedCount,
        collaborationsSent: collaborationsSentCount,
        unreadNotifications: recentNotificationsCount,
      },
      recentActivity: {
        jobsPublished: recentJobsPublished,
        submissions: recentSubmissions,
        candidatesAdded: recentCandidatesAdded,
      },
    });
  });

  // Get collaboration network (who I collaborate with most)
  fastify.get('/network', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          limit: { type: 'integer', minimum: 1, maximum: 50, default: 10 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { limit = 10 } = request.query as any;
    const userId = request.user!.id;

    // Get users who have submitted to my jobs (most active collaborators)
    const collaboratorsFromSubmissions = await fastify.prisma.candidateSubmission.findMany({
      where: {
        job: {
          publisherId: userId,
        },
        submitterId: { not: userId }, // Exclude self
      },
      select: {
        submitter: {
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
      distinct: ['submitterId'],
      take: limit,
    });

    // Get users whose jobs I have submitted to
    const jobOwnersISubmittedTo = await fastify.prisma.candidateSubmission.findMany({
      where: {
        submitterId: userId,
      },
      select: {
        job: {
          select: {
            publisher: {
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
        },
      },
      distinct: ['jobId'],
      take: limit,
    });

    // Combine and deduplicate collaborators
    const collaborators = new Map();
    
    collaboratorsFromSubmissions.forEach(item => {
      const user = item.submitter;
      if (!collaborators.has(user.id)) {
        collaborators.set(user.id, {
          ...user,
          collaborationType: 'submitted_to_me',
          submissionCount: 1,
        });
      } else {
        collaborators.get(user.id).submissionCount++;
      }
    });

    jobOwnersISubmittedTo.forEach(item => {
      const user = item.job.publisher;
      if (!collaborators.has(user.id)) {
        collaborators.set(user.id, {
          ...user,
          collaborationType: 'i_submitted_to',
          submissionCount: 1,
        });
      } else {
        const existing = collaborators.get(user.id);
        existing.collaborationType = 'mutual';
        existing.submissionCount++;
      }
    });

    reply.send({
      collaborators: Array.from(collaborators.values())
        .sort((a, b) => b.submissionCount - a.submissionCount)
        .slice(0, limit),
    });
  });

  // Get system-wide collaboration metrics (admin only)
  fastify.get('/metrics', {
    schema: {
      tags: ['Collaborations'],
      security: [{ Bearer: [] }],
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.PLATFORM_ADMIN])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const [
      totalUsers,
      totalCompanies,
      totalJobs,
      totalCandidates,
      totalSubmissions,
      totalCollaborations,
      activeUsersThisMonth,
    ] = await Promise.all([
      fastify.prisma.user.count(),
      fastify.prisma.company.count(),
      fastify.prisma.job.count(),
      fastify.prisma.candidate.count(),
      fastify.prisma.candidateSubmission.count(),
      fastify.prisma.jobPermission.count(),
      fastify.prisma.user.count({
        where: {
          OR: [
            {
              jobs: {
                some: {
                  createdAt: {
                    gte: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
                  },
                },
              },
            },
            {
              candidateSubmissions: {
                some: {
                  createdAt: {
                    gte: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
                  },
                },
              },
            },
            {
              maintainedCandidates: {
                some: {
                  createdAt: {
                    gte: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
                  },
                },
              },
            },
          ],
        },
      }),
    ]);

    reply.send({
      platform: {
        totalUsers,
        totalCompanies,
        totalJobs,
        totalCandidates,
        totalSubmissions,
        totalCollaborations,
        activeUsersThisMonth,
      },
    });
  });
};