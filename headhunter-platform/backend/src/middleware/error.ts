import { FastifyRequest, FastifyReply, FastifyInstance } from 'fastify';
import fp from 'fastify-plugin';
import { ZodError } from 'zod';
import { Prisma } from '@prisma/client';

export interface APIError extends Error {
  statusCode?: number;
  code?: string;
}

export class ValidationError extends Error implements APIError {
  statusCode = 400;
  code = 'VALIDATION_ERROR';

  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends Error implements APIError {
  statusCode = 404;
  code = 'NOT_FOUND';

  constructor(message: string = 'Resource not found') {
    super(message);
    this.name = 'NotFoundError';
  }
}

export class UnauthorizedError extends Error implements APIError {
  statusCode = 401;
  code = 'UNAUTHORIZED';

  constructor(message: string = 'Unauthorized') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class ForbiddenError extends Error implements APIError {
  statusCode = 403;
  code = 'FORBIDDEN';

  constructor(message: string = 'Forbidden') {
    super(message);
    this.name = 'ForbiddenError';
  }
}

export class ConflictError extends Error implements APIError {
  statusCode = 409;
  code = 'CONFLICT';

  constructor(message: string) {
    super(message);
    this.name = 'ConflictError';
  }
}

export const errorHandler = fp(async (fastify: FastifyInstance) => {
  fastify.setErrorHandler((error: any, req: any, res: any) => {
    req.log.error(error);

    // Zod validation errors
    if (error instanceof ZodError) {
      return res.status(400).send({
        error: 'Validation failed',
        code: 'VALIDATION_ERROR',
        details: error.errors.map((err: any) => ({
          path: err.path.join('.'),
          message: err.message,
        })),
      });
    }

    // Prisma errors
    if (error instanceof Prisma.PrismaClientKnownRequestError) {
      switch (error.code) {
        case 'P2002': // Unique constraint violation
          return res.status(409).send({
            error: 'Resource already exists',
            code: 'UNIQUE_CONSTRAINT_VIOLATION',
            field: error.meta?.target,
          });
        case 'P2025': // Record not found
          return res.status(404).send({
            error: 'Resource not found',
            code: 'NOT_FOUND',
          });
        default:
          return res.status(500).send({
            error: 'Database error',
            code: 'DATABASE_ERROR',
          });
      }
    }

    // Custom API errors
    if (error.statusCode) {
      return res.status(error.statusCode || 500).send({
        error: error.message,
        code: error.code || 'API_ERROR',
      });
    }

    // JWT errors
    if (error.message && error.message.includes('jwt')) {
      return res.status(401).send({
        error: 'Invalid or expired token',
        code: 'JWT_ERROR',
      });
    }

    // Default server error
    return res.status(500).send({
      error: 'Internal server error',
      code: 'INTERNAL_ERROR',
    });
  });
});