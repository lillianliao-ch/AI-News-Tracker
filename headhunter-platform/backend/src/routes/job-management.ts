import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { UserRole, AssignmentStatus, PermissionType } from '@/types';
import { NotFoundError, ForbiddenError, ValidationError } from '@/middleware/error';

// Schema definitions
const assignPMSchema = z.object({
  pmUserId: z.string().uuid(),
  notes: z.string().optional(),
});

const assignJobSchema = z.object({
  assigneeId: z.string().uuid(),
  assigneeType: z.enum(['consultant', 'soho']),
  assignAsPM: z.boolean().default(false),
  notes: z.string().optional(),
});

const batchAssignSchema = z.object({
  jobIds: z.array(z.string().uuid()).min(1),
  assigneeId: z.string().uuid(),
  assigneeType: z.enum(['consultant', 'soho']),
  notes: z.string().optional(),
});

const updateCandidateStatusSchema = z.object({
  status: z.string(),
  notes: z.string().optional(),
});

// Permission check middleware
const requirePMOrAdmin = async (request: FastifyRequest, reply: FastifyReply) => {
  const { jobId } = request.params as { jobId: string };
  const user = request.user!;
  
  const job = await request.server.prisma.job.findUnique({
    where: { id: jobId },
    include: { 
      projectManager: true,
      publisher: { select: { companyId: true } }
    }
  });
  
  if (!job) {
    throw new NotFoundError('Job not found');
  }
  
  const hasPermission = 
    user.role === UserRole.PLATFORM_ADMIN ||
    (user.role === UserRole.COMPANY_ADMIN && user.companyId === job.publisher.companyId) ||
    (job.projectManager?.pmUserId === user.id && job.projectManager.isActive);
    
  if (!hasPermission) {
    throw new ForbiddenError('需要职位管理权限');
  }
  
  (request as any).job = job;
};

export const jobManagementRoutes = async (fastify: FastifyInstance) => {
  
  // Get jobs for management (pending assignment and assigned)
  fastify.get('/management', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 5 },
          assignmentStatus: { 
            type: 'string', 
            enum: ['pending_assignment', 'assigned', 'completed'] 
          },
          jobName: { type: 'string' },
          companyLocation: { type: 'string' },
          jobCategory: { type: 'string' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { 
      page = 1, 
      limit = 5, 
      assignmentStatus, 
      jobName,
      companyLocation,
      jobCategory 
    } = request.query as any;
    
    const user = request.user!;
    const skip = (page - 1) * limit;
    const where: any = {};
    
    // Apply filters
    if (assignmentStatus) {
      where.assignmentStatus = assignmentStatus;
    }
    
    if (jobName) {
      where.title = { contains: jobName, mode: 'insensitive' };
    }
    
    if (companyLocation) {
      where.OR = [
        { 
          companyClient: {
            name: { contains: companyLocation, mode: 'insensitive' }
          }
        },
        { location: { contains: companyLocation, mode: 'insensitive' } }
      ];
    }
    
    if (jobCategory) {
      where.industry = { contains: jobCategory, mode: 'insensitive' };
    }
    
    // Role-based access control for management
    if (user.role === UserRole.COMPANY_ADMIN) {
      if (user.companyId) {
        where.publisher = { companyId: user.companyId };
      } else {
        where.id = 'non-existent-id';
      }
    } else if (user.role === UserRole.CONSULTANT || user.role === UserRole.SOHO) {
      // Only show jobs where user is PM
      where.projectManager = {
        pmUserId: user.id,
        isActive: true
      };
    }
    
    // Check if specific assignment status is requested
    if (assignmentStatus === 'assigned') {
      // Get only assigned jobs with pagination
      const assignedWhere = { ...where };
      console.log('🔥 DEBUG: Assigned jobs query where clause:', JSON.stringify(assignedWhere, null, 2));
      const [assignedJobs, totalAssigned] = await Promise.all([
        fastify.prisma.job.findMany({
          where: assignedWhere,
          skip,
          take: limit,
          include: {
            publisher: {
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
            companyClient: {
              select: {
                id: true,
                name: true,
                industry: true,
                location: true,
              },
            },
            projectManager: {
              include: {
                pmUser: {
                  select: {
                    id: true,
                    username: true,
                    email: true,
                  },
                },
              },
            },
            jobPermissions: {
              where: {
                permissionType: PermissionType.PROGRESSION,
              },
              include: {
                grantedToUser: {
                  select: {
                    id: true,
                    username: true,
                    email: true,
                    role: true,
                  },
                },
              },
              orderBy: {
                grantedAt: 'desc'
              },
            },
            _count: {
              select: {
                candidateSubmissions: true,
              },
            },
          },
          orderBy: { createdAt: 'desc' },
        }),
        fastify.prisma.job.count({ where: assignedWhere })
      ]);

      console.log('🔥 DEBUG: Returning assigned jobs response:', { 
        assignedJobsCount: assignedJobs.length,
        totalAssigned,
        assignedJobIds: assignedJobs.map(j => j.id),
        assignmentStatuses: assignedJobs.map(j => j.assignmentStatus)
      });
      
      return reply.send({
        assignedJobs,
        totalAssigned,
        pagination: {
          page,
          limit,
          total: totalAssigned,
          pages: Math.ceil(totalAssigned / limit),
        },
      });
    }

    // Get pending jobs with pagination (default behavior)
    const pendingWhere = { ...where, assignmentStatus: 'pending_assignment' };
    const [pendingJobs, totalPending] = await Promise.all([
      fastify.prisma.job.findMany({
        where: pendingWhere,
        skip,
        take: limit,
        include: {
          publisher: {
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
          companyClient: {
            select: {
              id: true,
              name: true,
              industry: true,
              location: true,
            },
          },
          projectManager: {
            include: {
              pmUser: {
                select: {
                  id: true,
                  username: true,
                  email: true,
                },
              },
            },
          },
          _count: {
            select: {
              candidateSubmissions: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
      }),
      fastify.prisma.job.count({ where: pendingWhere })
    ]);

    // Get assigned jobs (without pagination for now)
    const assignedWhere = { ...where, assignmentStatus: 'assigned' };
    const assignedJobs = await fastify.prisma.job.findMany({
      where: assignedWhere,
      include: {
        publisher: {
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
        companyClient: {
          select: {
            id: true,
            name: true,
            industry: true,
            location: true,
          },
        },
        projectManager: {
          include: {
            pmUser: {
              select: {
                id: true,
                username: true,
                email: true,
              },
            },
          },
        },
        jobPermissions: {
          where: {
            permissionType: PermissionType.PROGRESSION,
          },
          include: {
            grantedToUser: {
              select: {
                id: true,
                username: true,
                email: true,
                role: true,
              },
            },
          },
        },
        _count: {
          select: {
            candidateSubmissions: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    reply.send({
      pendingJobs,
      assignedJobs,
      totalPending,
      pagination: {
        page,
        limit,
        total: totalPending,
        pages: Math.ceil(totalPending / limit),
      },
    });
  });

  // Get jobs for progression (jobs user can submit to)
  fastify.get('/progression', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      querystring: {
        type: 'object',
        properties: {
          page: { type: 'integer', minimum: 1, default: 1 },
          limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          search: { type: 'string' },
          status: { type: 'string' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { page = 1, limit = 20, search, status } = request.query as any;
    const user = request.user!;
    const skip = (page - 1) * limit;
    
    const where: any = {
      status: 'open', // Only show open jobs for progression
    };
    
    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } },
      ];
    }
    
    // Role-based access control for progression
    if (user.role === UserRole.CONSULTANT) {
      // Company consultants can progress all company jobs
      if (user.companyId) {
        where.publisher = { companyId: user.companyId };
      } else {
        where.id = 'non-existent-id';
      }
    } else if (user.role === UserRole.SOHO) {
      // SOHO can only progress jobs explicitly assigned to them
      where.jobPermissions = {
        some: {
          grantedToUserId: user.id,
          permissionType: PermissionType.PROGRESSION,
          OR: [
            { expiresAt: null },
            { expiresAt: { gt: new Date() } },
          ],
        }
      };
    }
    
    const [jobs, total] = await Promise.all([
      fastify.prisma.job.findMany({
        where,
        skip,
        take: limit,
        include: {
          publisher: {
            select: {
              id: true,
              username: true,
              company: {
                select: {
                  id: true,
                  name: true,
                },
              },
            },
          },
          companyClient: {
            select: {
              id: true,
              name: true,
              industry: true,
            },
          },
          candidateSubmissions: {
            where: { submitterId: user.id },
            select: {
              id: true,
              status: true,
              createdAt: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
      }),
      fastify.prisma.job.count({ where }),
    ]);

    reply.send({
      jobs,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  });

  // Assign PM to a job
  fastify.post('/:jobId/assign-pm', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          jobId: { type: 'string', format: 'uuid' },
        },
        required: ['jobId'],
      },
      body: {
        type: 'object',
        properties: {
          pmUserId: { type: 'string', format: 'uuid' },
          notes: { type: 'string' },
        },
        required: ['pmUserId'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { jobId } = request.params as { jobId: string };
    const body = assignPMSchema.parse(request.body);
    const user = request.user!;

    // Only company admin can assign PM
    if (user.role !== UserRole.COMPANY_ADMIN && user.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Only company admin can assign PM');
    }

    const job = await fastify.prisma.job.findUnique({
      where: { id: jobId },
      include: {
        publisher: { select: { companyId: true } },
        projectManager: true,
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    // Check if user can manage this job
    if (user.role === UserRole.COMPANY_ADMIN && user.companyId !== job.publisher.companyId) {
      throw new ForbiddenError('Can only assign PM to your company jobs');
    }

    // Verify PM user exists and is in same company
    const pmUser = await fastify.prisma.user.findUnique({
      where: { id: body.pmUserId },
    });

    if (!pmUser) {
      throw new NotFoundError('PM user not found');
    }

    if (user.role === UserRole.COMPANY_ADMIN && pmUser.companyId !== user.companyId) {
      throw new ValidationError('PM must be from the same company');
    }

    if (pmUser.role !== UserRole.CONSULTANT) {
      throw new ValidationError('PM must be a consultant');
    }

    // Deactivate existing PM if any
    if (job.projectManager) {
      await fastify.prisma.jobProjectManager.update({
        where: { id: job.projectManager.id },
        data: { isActive: false },
      });
    }

    // Create new PM assignment
    const pm = await fastify.prisma.jobProjectManager.create({
      data: {
        jobId,
        pmUserId: body.pmUserId,
        assignedById: user.id,
        notes: body.notes,
      },
      include: {
        pmUser: {
          select: {
            id: true,
            username: true,
            email: true,
          },
        },
      },
    });

    reply.status(201).send({
      message: 'PM assigned successfully',
      pm,
    });
  });

  // Remove PM from job
  fastify.delete('/:jobId/remove-pm', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          jobId: { type: 'string', format: 'uuid' },
        },
        required: ['jobId'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { jobId } = request.params as { jobId: string };
    const user = request.user!;

    if (user.role !== UserRole.COMPANY_ADMIN && user.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Only company admin can remove PM');
    }

    const job = await fastify.prisma.job.findUnique({
      where: { id: jobId },
      include: {
        publisher: { select: { companyId: true } },
        projectManager: true,
      },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    if (user.role === UserRole.COMPANY_ADMIN && user.companyId !== job.publisher.companyId) {
      throw new ForbiddenError('Can only remove PM from your company jobs');
    }

    if (!job.projectManager) {
      throw new ValidationError('Job has no PM assigned');
    }

    await fastify.prisma.jobProjectManager.update({
      where: { id: job.projectManager.id },
      data: { isActive: false },
    });

    reply.send({ message: 'PM removed successfully' });
  });

  // Assign job to consultant/SOHO
  fastify.post('/:jobId/assign', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          jobId: { type: 'string', format: 'uuid' },
        },
        required: ['jobId'],
      },
      body: {
        type: 'object',
        properties: {
          assigneeId: { type: 'string', format: 'uuid' },
          assigneeType: { type: 'string', enum: ['consultant', 'soho'] },
          assignAsPM: { type: 'boolean', default: false },
          notes: { type: 'string' },
        },
        required: ['assigneeId', 'assigneeType'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { jobId } = request.params as { jobId: string };
    const body = assignJobSchema.parse(request.body);
    const user = request.user!;

    if (user.role !== UserRole.COMPANY_ADMIN && user.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Only company admin can assign jobs');
    }

    const job = await fastify.prisma.job.findUnique({
      where: { id: jobId },
      include: { publisher: { select: { companyId: true } } },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    if (user.role === UserRole.COMPANY_ADMIN && user.companyId !== job.publisher.companyId) {
      throw new ForbiddenError('Can only assign your company jobs');
    }

    // Verify assignee exists
    const assignee = await fastify.prisma.user.findUnique({
      where: { id: body.assigneeId },
    });

    if (!assignee) {
      throw new NotFoundError('Assignee not found');
    }

    // Validate assignee type matches user role
    if (
      (body.assigneeType === 'consultant' && assignee.role !== UserRole.CONSULTANT) ||
      (body.assigneeType === 'soho' && assignee.role !== UserRole.SOHO)
    ) {
      throw new ValidationError('Assignee type does not match user role');
    }

    // Create job permission for progression
    const existingPermission = await fastify.prisma.jobPermission.findFirst({
      where: {
        jobId,
        grantedToUserId: body.assigneeId,
        permissionType: PermissionType.PROGRESSION,
      },
    });

    if (!existingPermission) {
      await fastify.prisma.jobPermission.create({
        data: {
          jobId,
          grantedToUserId: body.assigneeId,
          grantedById: user.id,
          permissionType: PermissionType.PROGRESSION,
        },
      });
    }

    // Assign as PM if requested
    if (body.assignAsPM && assignee.role === UserRole.CONSULTANT) {
      // Deactivate existing PM if any
      const existingPM = await fastify.prisma.jobProjectManager.findFirst({
        where: { jobId, isActive: true },
      });

      if (existingPM) {
        await fastify.prisma.jobProjectManager.update({
          where: { id: existingPM.id },
          data: { isActive: false },
        });
      }

      // Create new PM assignment
      await fastify.prisma.jobProjectManager.create({
        data: {
          jobId,
          pmUserId: body.assigneeId,
          assignedById: user.id,
          notes: body.notes,
        },
      });
    }

    // Update job assignment status
    console.log('🔥 DEBUG: Updating job assignment status for jobId:', jobId);
    const updatedJob = await fastify.prisma.job.update({
      where: { id: jobId },
      data: {
        assignmentStatus: AssignmentStatus.ASSIGNED,
        assignedAt: new Date(),
        assignedById: user.id,
      },
    });
    console.log('🔥 DEBUG: Job updated successfully:', { 
      id: updatedJob.id, 
      assignmentStatus: updatedJob.assignmentStatus,
      assignedAt: updatedJob.assignedAt 
    });

    // Create notification
    await fastify.prisma.notification.create({
      data: {
        recipientId: body.assigneeId,
        type: 'job_shared',
        title: 'Job Assigned',
        content: `Job "${job.title}" has been assigned to you${body.assignAsPM ? ' as PM' : ''}`,
        relatedId: jobId,
      },
    });

    reply.status(201).send({
      message: `Job assigned successfully${body.assignAsPM ? ' with PM role' : ''}`,
    });
  });

  // Update candidate submission status (PM/Admin only)
  fastify.patch('/submissions/:submissionId/status', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          submissionId: { type: 'string', format: 'uuid' },
        },
        required: ['submissionId'],
      },
      body: {
        type: 'object',
        properties: {
          status: { type: 'string' },
          notes: { type: 'string' },
        },
        required: ['status'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { submissionId } = request.params as { submissionId: string };
    const body = updateCandidateStatusSchema.parse(request.body);
    const user = request.user!;

    const submission = await fastify.prisma.candidateSubmission.findUnique({
      where: { id: submissionId },
      include: {
        job: {
          include: {
            publisher: { select: { companyId: true } },
            projectManager: { where: { isActive: true } },
          },
        },
      },
    });

    if (!submission) {
      throw new NotFoundError('Submission not found');
    }

    // Check if user can update this submission
    const canUpdate = 
      user.role === UserRole.PLATFORM_ADMIN ||
      (user.role === UserRole.COMPANY_ADMIN && user.companyId === submission.job.publisher.companyId) ||
      (submission.job.projectManager?.[0]?.pmUserId === user.id);

    if (!canUpdate) {
      throw new ForbiddenError('No permission to update this submission');
    }

    // Update submission status
    const updatedSubmission = await fastify.prisma.candidateSubmission.update({
      where: { id: submissionId },
      data: { status: body.status as any },
    });

    // Log status change
    await fastify.prisma.candidateStatusLog.create({
      data: {
        submissionId,
        previousStatus: submission.status,
        newStatus: body.status,
        updatedById: user.id,
        notes: body.notes,
      },
    });

    // Create notification for submitter
    await fastify.prisma.notification.create({
      data: {
        recipientId: submission.submitterId,
        type: 'submission_status_changed',
        title: 'Submission Status Updated',
        content: `Your submission status has been updated to: ${body.status}`,
        relatedId: submissionId,
      },
    });

    reply.send({
      message: 'Submission status updated successfully',
      submission: updatedSubmission,
    });
  });

  // Get job submissions (PM/Admin only)
  fastify.get('/:jobId/submissions', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          jobId: { type: 'string', format: 'uuid' },
        },
        required: ['jobId'],
      },
    },
    preHandler: [fastify.authenticate, requirePMOrAdmin],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { jobId } = request.params as { jobId: string };

    const submissions = await fastify.prisma.candidateSubmission.findMany({
      where: { jobId },
      include: {
        candidate: {
          select: {
            id: true,
            name: true,
            phone: true,
            email: true,
          },
        },
        submitter: {
          select: {
            id: true,
            username: true,
            email: true,
          },
        },
        statusLogs: {
          include: {
            updatedBy: {
              select: {
                id: true,
                username: true,
              },
            },
          },
          orderBy: { updatedAt: 'desc' },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    reply.send({ submissions });
  });

  // Get user's managed jobs
  fastify.get('/users/:userId/managed-jobs', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          userId: { type: 'string', format: 'uuid' },
        },
        required: ['userId'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { userId } = request.params as { userId: string };
    const user = request.user!;

    // Users can only see their own managed jobs unless admin
    if (user.id !== userId && user.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Access denied');
    }

    const managedJobs = await fastify.prisma.jobProjectManager.findMany({
      where: { 
        pmUserId: userId,
        isActive: true,
      },
      include: {
        job: {
          include: {
            companyClient: {
              select: {
                id: true,
                name: true,
              },
            },
            _count: {
              select: {
                candidateSubmissions: true,
              },
            },
          },
        },
      },
      orderBy: { assignedAt: 'desc' },
    });

    reply.send({ managedJobs });
  });

  // Remove specific consultant assignment from job
  fastify.delete('/:jobId/assignments/:userId', {
    schema: {
      tags: ['Job Management'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          jobId: { type: 'string', format: 'uuid' },
          userId: { type: 'string', format: 'uuid' },
        },
        required: ['jobId', 'userId'],
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { jobId, userId } = request.params as { jobId: string; userId: string };
    const user = request.user!;

    // Check if user has permission to modify job assignments
    if (user.role !== UserRole.COMPANY_ADMIN && user.role !== UserRole.PLATFORM_ADMIN) {
      throw new ForbiddenError('Only company admin can remove job assignments');
    }

    const job = await fastify.prisma.job.findUnique({
      where: { id: jobId },
      include: { publisher: { select: { companyId: true } } },
    });

    if (!job) {
      throw new NotFoundError('Job not found');
    }

    if (user.role === UserRole.COMPANY_ADMIN && user.companyId !== job.publisher.companyId) {
      throw new ForbiddenError('Can only remove assignments from your company jobs');
    }

    // Find and delete the specific job permission
    const permission = await fastify.prisma.jobPermission.findFirst({
      where: {
        jobId,
        grantedToUserId: userId,
        permissionType: PermissionType.PROGRESSION,
      },
    });

    if (!permission) {
      throw new NotFoundError('Assignment not found');
    }

    await fastify.prisma.jobPermission.delete({
      where: { id: permission.id },
    });

    // Check if there are any remaining assignments
    const remainingAssignments = await fastify.prisma.jobPermission.count({
      where: {
        jobId,
        permissionType: PermissionType.PROGRESSION,
      },
    });

    // If no assignments remain, update job status back to pending
    if (remainingAssignments === 0) {
      await fastify.prisma.job.update({
        where: { id: jobId },
        data: {
          assignmentStatus: AssignmentStatus.PENDING_ASSIGNMENT,
          assignedAt: null,
          assignedById: null,
        },
      });
    }

    reply.send({ 
      message: 'Assignment removed successfully',
      remainingAssignments 
    });
  });
};