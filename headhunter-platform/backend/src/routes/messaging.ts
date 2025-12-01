import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole } from '@/types';
import { NotFoundError, ForbiddenError } from '@/middleware/error';

const sendMessageSchema = z.object({
  recipientId: z.string().uuid(),
  subject: z.string().min(1).max(200).optional(),
  content: z.string().min(1).max(5000),
  relatedJobId: z.string().uuid().optional(),
  relatedCandidateId: z.string().uuid().optional(),
});

const markReadSchema = z.object({
  messageIds: z.array(z.string().uuid()),
});

export const messagingRoutes = async (fastify: FastifyInstance) => {
  // Send a message
  fastify.post('/messages', {
    schema: {
      tags: ['Messaging'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['recipientId', 'content'],
        properties: {
          recipientId: { type: 'string', format: 'uuid' },
          subject: { type: 'string', minLength: 1, maxLength: 200 },
          content: { type: 'string', minLength: 1, maxLength: 5000 },
          relatedJobId: { type: 'string', format: 'uuid' },
          relatedCandidateId: { type: 'string', format: 'uuid' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = sendMessageSchema.parse(request.body);
    const user = request.user!;

    // Verify recipient exists
    const recipient = await fastify.prisma.user.findUnique({
      where: { id: body.recipientId },
      select: { id: true, username: true, email: true },
    });

    if (!recipient) {
      throw new NotFoundError('Recipient not found');
    }

    // Create message record in notifications table with a special type
    const message = await fastify.prisma.notification.create({
      data: {
        recipientId: body.recipientId,
        type: 'system_announcement', // We'll use this for messages
        title: body.subject || 'New Message',
        content: body.content,
        relatedId: body.relatedJobId || body.relatedCandidateId,
      },
    });

    // Send real-time notification if WebSocket is available
    try {
      fastify.websocket?.sendNotificationToUser(body.recipientId, {
        type: 'message',
        id: message.id,
        from: {
          id: user.id,
          username: user.username,
        },
        subject: body.subject,
        content: body.content,
        timestamp: message.createdAt,
        relatedJobId: body.relatedJobId,
        relatedCandidateId: body.relatedCandidateId,
      });
    } catch (error) {
      // WebSocket not available, continue without real-time notification
      console.warn('WebSocket not available for real-time messaging');
    }

    reply.status(201).send({
      message: 'Message sent successfully',
      messageId: message.id,
      recipient: recipient.username,
    });
  });

  // Get conversations/messages
  fastify.get('/messages', {
    schema: {
      tags: ['Messaging'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          conversationWith: { type: 'string', format: 'uuid' },
          unreadOnly: { type: 'boolean', default: false },
          relatedJobId: { type: 'string', format: 'uuid' },
          relatedCandidateId: { type: 'string', format: 'uuid' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { 
      page = 1, 
      limit = 20, 
      conversationWith, 
      unreadOnly = false,
      relatedJobId,
      relatedCandidateId,
    } = request.query as any;
    const skip = (page - 1) * limit;
    const user = request.user!;

    const where: any = {
      recipientId: user.id,
      type: 'system_announcement', // Our message type
    };

    if (unreadOnly) {
      where.isRead = false;
    }

    if (relatedJobId) {
      where.relatedId = relatedJobId;
    }

    if (relatedCandidateId) {
      where.relatedId = relatedCandidateId;
    }

    const [messages, total, unreadCount] = await Promise.all([
      fastify.prisma.notification.findMany({
        where,
        skip,
        take: limit,
        orderBy: { createdAt: 'desc' },
      }),
      fastify.prisma.notification.count({ where }),
      fastify.prisma.notification.count({
        where: {
          recipientId: user.id,
          type: 'system_announcement',
          isRead: false,
        },
      }),
    ]);

    reply.send({
      messages,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
      unreadCount,
    });
  });

  // Mark messages as read
  fastify.patch('/messages/mark-read', {
    schema: {
      tags: ['Messaging'],
      security: [{ Bearer: [] }],
      body: {
        type: 'object',
        required: ['messageIds'],
        properties: {
          messageIds: { type: 'array', items: { type: 'string', format: 'uuid' } },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const body = markReadSchema.parse(request.body);
    const user = request.user!;

    await fastify.prisma.notification.updateMany({
      where: {
        id: { in: body.messageIds },
        recipientId: user.id,
        type: 'system_announcement',
      },
      data: {
        isRead: true,
      },
    });

    reply.send({ message: 'Messages marked as read' });
  });

  // Get conversation partners
  fastify.get('/conversations', {
    schema: {
      tags: ['Messaging'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          limit: { type: 'integer', minimum: 1, maximum: 50, default: 20 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { limit = 20 } = request.query as any;
    const user = request.user!;

    // Get unique conversation partners based on job collaborations
    const collaborators = await fastify.prisma.candidateSubmission.findMany({
      where: {
        OR: [
          { submitterId: user.id },
          { job: { publisherId: user.id } },
        ],
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
      distinct: ['submitterId', 'jobId'],
      take: limit,
    });

    const conversationPartners = new Map();

    collaborators.forEach(collab => {
      if (collab.submitter.id !== user.id && !conversationPartners.has(collab.submitter.id)) {
        conversationPartners.set(collab.submitter.id, collab.submitter);
      }
      if (collab.job.publisher.id !== user.id && !conversationPartners.has(collab.job.publisher.id)) {
        conversationPartners.set(collab.job.publisher.id, collab.job.publisher);
      }
    });

    reply.send({
      conversationPartners: Array.from(conversationPartners.values()),
    });
  });

  // Get message thread between two users
  fastify.get('/messages/thread/:userId', {
    schema: {
      tags: ['Messaging'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          userId: { type: 'string', format: 'uuid' },
        },
        required: ['userId'],
      },
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 50 },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { userId } = request.params as { userId: string };
    const { page = 1, limit = 50 } = request.query as any;
    const skip = (page - 1) * limit;
    const currentUser = request.user!;

    // Get messages between current user and target user
    // This is a simplified version - in a real app you'd have a proper messages table
    const messages = await fastify.prisma.notification.findMany({
      where: {
        type: 'system_announcement',
        OR: [
          {
            recipientId: currentUser.id,
            // Ideally we'd have a senderId field to filter by
          },
          {
            recipientId: userId,
            // Messages sent by current user to target user
          },
        ],
      },
      skip,
      take: limit,
      orderBy: { createdAt: 'asc' },
    });

    reply.send({
      messages,
      pagination: {
        page,
        limit,
        total: messages.length,
        pages: Math.ceil(messages.length / limit),
      },
    });
  });

  // WebSocket endpoint for real-time status
  fastify.get('/status', {
    schema: {
      tags: ['Messaging'],
      security: [{ Bearer: [] }],
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const user = request.user!;
    
    try {
      const isConnected = fastify.websocket?.isUserConnected(user.id) || false;
      const connectionCount = fastify.websocket?.getConnectionCount() || 0;
      const healthStatus = fastify.websocket?.getHealthStatus() || { connected: false };

      reply.send({
        userConnected: isConnected,
        totalConnectedUsers: connectionCount,
        websocketStatus: healthStatus,
      });
    } catch (error) {
      reply.send({
        userConnected: false,
        totalConnectedUsers: 0,
        websocketStatus: { connected: false },
        error: 'WebSocket service not available',
      });
    }
  });
};