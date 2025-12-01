import Fastify from 'fastify';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import multipart from '@fastify/multipart';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import { PrismaClient } from '@prisma/client';
import { createClient } from 'redis';
import { createServer } from 'http';
import { initializeWebSocketService } from '@/services/websocketService';

import { authMiddleware } from '@/middleware/auth';
import { errorHandler } from '@/middleware/error';
import { authRoutes } from '@/routes/auth';
import { userRoutes } from '@/routes/users';
import { companyRoutes } from '@/routes/companies';
import { jobRoutes } from '@/routes/jobs';
import { jobManagementRoutes } from '@/routes/job-management';
import { companyClientRoutes } from '@/routes/company-clients';
import { candidateRoutes } from '@/routes/candidates';
import { collaborationRoutes } from '@/routes/collaborations';
import { uploadRoutes } from '@/routes/upload';
import { messagingRoutes } from '@/routes/messaging';
import { consultantApplicationRoutes } from '@/routes/consultant-applications';
import { batchRoutes } from '@/routes/batch';
import { resumeMatchingRoutes } from '@/routes/resume-matching-simple';

const prisma = new PrismaClient();
const redis = createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379'
});

const server = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
  },
});

// Create HTTP server for Socket.IO integration
const httpServer = createServer();

async function start() {
  try {
    // Register plugins
    await server.register(cors, {
      origin: true,
      credentials: true,
    });

    await server.register(jwt, {
      secret: process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production',
    });

    await server.register(multipart);

    // Static file serving for uploads
    await server.register(require('@fastify/static'), {
      root: require('path').join(__dirname, '../uploads'),
      prefix: '/uploads/',
    });

    // Swagger documentation
    await server.register(swagger, {
      swagger: {
        info: {
          title: 'Headhunter Collaboration Platform API',
          description: 'API documentation for the Headhunter Collaboration Platform',
          version: '1.0.0',
        },
        host: 'localhost:4000',
        schemes: ['http', 'https'],
        consumes: ['application/json'],
        produces: ['application/json'],
        securityDefinitions: {
          Bearer: {
            type: 'apiKey',
            name: 'Authorization',
            in: 'header',
          },
        },
      },
    });

    await server.register(swaggerUi, {
      routePrefix: '/docs',
      uiConfig: {
        docExpansion: 'full',
        deepLinking: false,
      },
      staticCSP: true,
      transformStaticCSP: (header) => header,
    });

    // Register error handler
    await server.register(errorHandler);
    server.register(authMiddleware);

    // Register routes
    server.register(authRoutes, { prefix: '/api/auth' });
    server.register(userRoutes, { prefix: '/api/users' });
    server.register(companyRoutes, { prefix: '/api/companies' });
    server.register(jobRoutes, { prefix: '/api/jobs' });
    server.register(jobManagementRoutes, { prefix: '/api/job-management' });
    server.register(companyClientRoutes, { prefix: '/api/company-clients' });
    server.register(candidateRoutes, { prefix: '/api/candidates' });
    server.register(collaborationRoutes, { prefix: '/api/collaborations' });
    server.register(uploadRoutes, { prefix: '/api/upload' });
    server.register(messagingRoutes, { prefix: '/api/messaging' });
    server.register(consultantApplicationRoutes, { prefix: '/api/consultant-applications' });
    server.register(batchRoutes, { prefix: '/api/batch' });
    server.register(resumeMatchingRoutes, { prefix: '/api/resume-matching' });

    // Health check
    server.get('/health', async (request, reply) => {
      return { status: 'ok', timestamp: new Date().toISOString() };
    });

    // Connect to Redis
    await redis.connect();

    // Add Prisma and Redis to server context
    server.decorate('prisma', prisma);
    server.decorate('redis', redis);

    // Initialize WebSocket service
    const websocketService = initializeWebSocketService(httpServer, prisma);
    server.decorate('websocket', websocketService);

    const port = Number(process.env.PORT) || 4000;
    const host = process.env.HOST || 'localhost';

    // Start Fastify server first
    await server.listen({ port, host });
    
    // Then start HTTP server for WebSocket on a different port for now
    const wsPort = port + 1;
    httpServer.listen(wsPort, host, () => {
      server.log.info(`WebSocket server listening on http://${host}:${wsPort}`);
    });
    
    server.log.info(`Server listening on http://${host}:${port}`);
    server.log.info(`API documentation available at http://${host}:${port}/docs`);
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  server.log.info('Received SIGINT, shutting down gracefully');
  await server.close();
  await prisma.$disconnect();
  await redis.disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  server.log.info('Received SIGTERM, shutting down gracefully');
  await server.close();
  await prisma.$disconnect();
  await redis.disconnect();
  process.exit(0);
});

start();

// Type declarations for Fastify
declare module 'fastify' {
  interface FastifyInstance {
    prisma: PrismaClient;
    redis: ReturnType<typeof createClient>;
    websocket: any; // WebSocketService type
  }
}