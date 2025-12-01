import { PrismaClient } from '@prisma/client';
import { UserRole, MaintainerChangeStatus } from '@/types';

export interface CreateMaintainerChangeRequest {
  candidateId: string;
  requestedMaintainerId: string;
  reason: string;
}

export interface ReviewMaintainerChangeRequest {
  requestId: string;
  status: MaintainerChangeStatus;
  reviewedById: string;
}

export class MaintainerChangeService {
  constructor(private prisma: PrismaClient) {}

  async createChangeRequest(
    data: CreateMaintainerChangeRequest,
    requesterId: string
  ) {
    // Get candidate to verify current maintainer
    const candidate = await this.prisma.candidate.findUnique({
      where: { id: data.candidateId },
      select: { 
        id: true, 
        name: true, 
        maintainerId: true,
        maintainer: {
          select: {
            id: true,
            username: true,
            email: true,
          },
        },
      },
    });

    if (!candidate) {
      throw new Error('Candidate not found');
    }

    // Check if requester has permission (admin, current maintainer, or requested maintainer)
    const requester = await this.prisma.user.findUnique({
      where: { id: requesterId },
      select: { id: true, role: true, companyId: true },
    });

    if (!requester) {
      throw new Error('Requester not found');
    }

    // Verify requested maintainer exists
    const requestedMaintainer = await this.prisma.user.findUnique({
      where: { id: data.requestedMaintainerId },
      select: { 
        id: true, 
        username: true, 
        email: true, 
        role: true,
        companyId: true,
      },
    });

    if (!requestedMaintainer) {
      throw new Error('Requested maintainer not found');
    }

    // Validate requested maintainer role
    if (![UserRole.CONSULTANT, UserRole.SOHO, UserRole.COMPANY_ADMIN].includes(requestedMaintainer.role)) {
      throw new Error('Requested maintainer must be a consultant, soho, or company admin');
    }

    // Check if there's already a pending request for this candidate
    const existingRequest = await this.prisma.maintainerChangeRequest.findFirst({
      where: {
        candidateId: data.candidateId,
        status: MaintainerChangeStatus.PENDING,
      },
    });

    if (existingRequest) {
      throw new Error('There is already a pending maintainer change request for this candidate');
    }

    // Create the request
    const request = await this.prisma.maintainerChangeRequest.create({
      data: {
        candidateId: data.candidateId,
        currentMaintainerId: candidate.maintainerId,
        requestedMaintainerId: data.requestedMaintainerId,
        requesterId: requesterId,
        reason: data.reason,
      },
      include: {
        candidate: {
          select: { id: true, name: true, phone: true },
        },
        currentMaintainer: {
          select: { id: true, username: true, email: true },
        },
        requestedMaintainer: {
          select: { id: true, username: true, email: true },
        },
        requester: {
          select: { id: true, username: true, email: true },
        },
      },
    });

    // Create notifications
    const notificationTargets = [];
    
    // Notify current maintainer
    if (candidate.maintainerId !== requesterId) {
      notificationTargets.push(candidate.maintainerId);
    }
    
    // Notify requested maintainer
    if (data.requestedMaintainerId !== requesterId) {
      notificationTargets.push(data.requestedMaintainerId);
    }

    // Notify platform admins
    const platformAdmins = await this.prisma.user.findMany({
      where: { role: UserRole.PLATFORM_ADMIN },
      select: { id: true },
    });
    notificationTargets.push(...platformAdmins.map(admin => admin.id));

    // Create notifications
    for (const targetId of notificationTargets) {
      await this.prisma.notification.create({
        data: {
          recipientId: targetId,
          type: 'maintainer_change_request',
          title: 'Maintainer Change Request',
          content: `${requester.role === UserRole.PLATFORM_ADMIN ? 'Admin' : 'User'} ${requestedMaintainer.username} has requested to become the maintainer of candidate "${candidate.name}"`,
          relatedId: request.id,
        },
      });
    }

    return request;
  }

  async reviewChangeRequest(data: ReviewMaintainerChangeRequest) {
    const request = await this.prisma.maintainerChangeRequest.findUnique({
      where: { id: data.requestId },
      include: {
        candidate: true,
        currentMaintainer: true,
        requestedMaintainer: true,
        requester: true,
      },
    });

    if (!request) {
      throw new Error('Maintainer change request not found');
    }

    if (request.status !== MaintainerChangeStatus.PENDING) {
      throw new Error('Request has already been reviewed');
    }

    // Update request status
    const updatedRequest = await this.prisma.maintainerChangeRequest.update({
      where: { id: data.requestId },
      data: {
        status: data.status,
        reviewedById: data.reviewedById,
        reviewedAt: new Date(),
      },
      include: {
        candidate: true,
        currentMaintainer: true,
        requestedMaintainer: true,
        requester: true,
        reviewedBy: {
          select: { id: true, username: true, email: true },
        },
      },
    });

    // If approved, change the candidate's maintainer
    if (data.status === MaintainerChangeStatus.APPROVED) {
      await this.prisma.candidate.update({
        where: { id: request.candidateId },
        data: { maintainerId: request.requestedMaintainerId },
      });
    }

    // Create notifications for all involved parties
    const notificationTargets = [
      request.requesterId,
      request.currentMaintainerId,
      request.requestedMaintainerId,
    ];

    const statusText = data.status === MaintainerChangeStatus.APPROVED ? 'approved' : 'rejected';
    
    for (const targetId of notificationTargets) {
      if (targetId !== data.reviewedById) { // Don't notify the reviewer
        await this.prisma.notification.create({
          data: {
            recipientId: targetId,
            type: 'maintainer_change_request',
            title: `Maintainer Change Request ${statusText.charAt(0).toUpperCase() + statusText.slice(1)}`,
            content: `The maintainer change request for candidate "${request.candidate.name}" has been ${statusText}`,
            relatedId: request.id,
          },
        });
      }
    }

    return updatedRequest;
  }

  async getChangeRequests(
    filters: {
      status?: MaintainerChangeStatus;
      candidateId?: string;
      requesterId?: string;
      currentMaintainerId?: string;
      requestedMaintainerId?: string;
    },
    pagination: { page: number; limit: number }
  ) {
    const skip = (pagination.page - 1) * pagination.limit;
    const where: any = {};

    if (filters.status) where.status = filters.status;
    if (filters.candidateId) where.candidateId = filters.candidateId;
    if (filters.requesterId) where.requesterId = filters.requesterId;
    if (filters.currentMaintainerId) where.currentMaintainerId = filters.currentMaintainerId;
    if (filters.requestedMaintainerId) where.requestedMaintainerId = filters.requestedMaintainerId;

    const [requests, total] = await Promise.all([
      this.prisma.maintainerChangeRequest.findMany({
        where,
        skip,
        take: pagination.limit,
        include: {
          candidate: {
            select: { id: true, name: true, phone: true, email: true },
          },
          currentMaintainer: {
            select: { id: true, username: true, email: true },
          },
          requestedMaintainer: {
            select: { id: true, username: true, email: true },
          },
          requester: {
            select: { id: true, username: true, email: true },
          },
          reviewedBy: {
            select: { id: true, username: true, email: true },
          },
        },
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.maintainerChangeRequest.count({ where }),
    ]);

    return {
      requests,
      pagination: {
        page: pagination.page,
        limit: pagination.limit,
        total,
        pages: Math.ceil(total / pagination.limit),
      },
    };
  }

  async getRequestById(requestId: string) {
    return await this.prisma.maintainerChangeRequest.findUnique({
      where: { id: requestId },
      include: {
        candidate: {
          select: { id: true, name: true, phone: true, email: true },
        },
        currentMaintainer: {
          select: { id: true, username: true, email: true },
        },
        requestedMaintainer: {
          select: { id: true, username: true, email: true },
        },
        requester: {
          select: { id: true, username: true, email: true },
        },
        reviewedBy: {
          select: { id: true, username: true, email: true },
        },
      },
    });
  }

  async getRequestsForUser(
    userId: string,
    role: UserRole,
    pagination: { page: number; limit: number }
  ) {
    const skip = (pagination.page - 1) * pagination.limit;
    let where: any = {};

    if (role === UserRole.PLATFORM_ADMIN) {
      // Platform admins can see all requests
      where = {};
    } else {
      // Other users can see requests they're involved in
      where = {
        OR: [
          { requesterId: userId },
          { currentMaintainerId: userId },
          { requestedMaintainerId: userId },
        ],
      };
    }

    const [requests, total] = await Promise.all([
      this.prisma.maintainerChangeRequest.findMany({
        where,
        skip,
        take: pagination.limit,
        include: {
          candidate: {
            select: { id: true, name: true, phone: true, email: true },
          },
          currentMaintainer: {
            select: { id: true, username: true, email: true },
          },
          requestedMaintainer: {
            select: { id: true, username: true, email: true },
          },
          requester: {
            select: { id: true, username: true, email: true },
          },
          reviewedBy: {
            select: { id: true, username: true, email: true },
          },
        },
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.maintainerChangeRequest.count({ where }),
    ]);

    return {
      requests,
      pagination: {
        page: pagination.page,
        limit: pagination.limit,
        total,
        pages: Math.ceil(total / pagination.limit),
      },
    };
  }
}

export const maintainerChangeService = new MaintainerChangeService(new PrismaClient());