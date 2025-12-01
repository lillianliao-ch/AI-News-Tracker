import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import fp from 'fastify-plugin';
import { UserRole } from '@/types';

declare module '@fastify/jwt' {
  interface FastifyJWT {
    user: {
      id: string;
      email: string;
      role: UserRole;
      companyId?: string;
    };
  }
}


export const authMiddleware = fp(async (fastify: FastifyInstance) => {
  fastify.decorate('authenticate', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      await request.jwtVerify();
      // request.user is automatically populated by @fastify/jwt after verification
    } catch (err) {
      reply.code(401).send({ error: 'Unauthorized' });
    }
  });

  fastify.decorate('requireRole', (roles: UserRole[]) => {
    return async (request: FastifyRequest, reply: FastifyReply) => {
      if (!request.user) {
        return reply.code(401).send({ error: 'Authentication required' });
      }

      if (!roles.includes(request.user.role)) {
        return reply.code(403).send({ error: 'Insufficient permissions' });
      }
    };
  });

  fastify.decorate('requireCompanyAccess', async (request: FastifyRequest, reply: FastifyReply) => {
    if (!request.user) {
      return reply.code(401).send({ error: 'Authentication required' });
    }

    const params = request.params as any;
    const companyId = params.companyId || params.id;
    
    if (request.user.role === UserRole.PLATFORM_ADMIN) {
      return; // Platform admin has access to all companies
    }

    if (request.user.companyId !== companyId) {
      return reply.code(403).send({ error: 'Access denied to this company' });
    }
  });
});

declare module 'fastify' {
  interface FastifyInstance {
    authenticate: (request: FastifyRequest, reply: FastifyReply) => Promise<void>;
    requireRole: (roles: UserRole[]) => (request: FastifyRequest, reply: FastifyReply) => Promise<void>;
    requireCompanyAccess: (request: FastifyRequest, reply: FastifyReply) => Promise<void>;
  }
}