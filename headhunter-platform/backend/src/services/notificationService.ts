import { PrismaClient } from '@prisma/client';
import { NotificationType } from '@/types';

export interface CreateNotification {
  recipientId: string;
  type: NotificationType;
  title: string;
  content: string;
  relatedId?: string;
}

export interface NotificationFilters {
  recipientId?: string;
  type?: NotificationType;
  isRead?: boolean;
  relatedId?: string;
}

export class NotificationService {
  constructor(private prisma: PrismaClient) {}

  async createNotification(data: CreateNotification) {
    return await this.prisma.notification.create({
      data,
    });
  }

  async createBulkNotifications(notifications: CreateNotification[]) {
    return await this.prisma.notification.createMany({
      data: notifications,
    });
  }

  async getNotifications(
    filters: NotificationFilters,
    pagination: { page: number; limit: number }
  ) {
    const skip = (pagination.page - 1) * pagination.limit;
    const where: any = {};

    if (filters.recipientId) where.recipientId = filters.recipientId;
    if (filters.type) where.type = filters.type;
    if (filters.isRead !== undefined) where.isRead = filters.isRead;
    if (filters.relatedId) where.relatedId = filters.relatedId;

    const [notifications, total, unreadCount] = await Promise.all([
      this.prisma.notification.findMany({
        where,
        skip,
        take: pagination.limit,
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.notification.count({ where }),
      filters.recipientId ? this.prisma.notification.count({
        where: {
          recipientId: filters.recipientId,
          isRead: false,
        },
      }) : 0,
    ]);

    return {
      notifications,
      pagination: {
        page: pagination.page,
        limit: pagination.limit,
        total,
        pages: Math.ceil(total / pagination.limit),
      },
      unreadCount,
    };
  }

  async markAsRead(notificationIds: string[], userId: string) {
    return await this.prisma.notification.updateMany({
      where: {
        id: { in: notificationIds },
        recipientId: userId, // Ensure user can only mark their own notifications
      },
      data: {
        isRead: true,
      },
    });
  }

  async markAllAsRead(userId: string) {
    return await this.prisma.notification.updateMany({
      where: {
        recipientId: userId,
        isRead: false,
      },
      data: {
        isRead: true,
      },
    });
  }

  async getUnreadCount(userId: string) {
    return await this.prisma.notification.count({
      where: {
        recipientId: userId,
        isRead: false,
      },
    });
  }

  async deleteNotification(id: string, userId: string) {
    return await this.prisma.notification.deleteMany({
      where: {
        id,
        recipientId: userId, // Ensure user can only delete their own notifications
      },
    });
  }

  // Specific notification creators for different events
  async notifyJobShared(
    recipientIds: string[],
    jobTitle: string,
    sharedBy: string,
    jobId: string
  ) {
    const notifications: CreateNotification[] = recipientIds.map(recipientId => ({
      recipientId,
      type: NotificationType.JOB_SHARED,
      title: 'New Job Shared',
      content: `Job "${jobTitle}" has been shared with you by ${sharedBy}`,
      relatedId: jobId,
    }));

    return await this.createBulkNotifications(notifications);
  }

  async notifyJobClosed(
    recipientIds: string[],
    jobTitle: string,
    jobId: string
  ) {
    const notifications: CreateNotification[] = recipientIds.map(recipientId => ({
      recipientId,
      type: NotificationType.JOB_CLOSED,
      title: 'Job Closed',
      content: `Job "${jobTitle}" has been closed`,
      relatedId: jobId,
    }));

    return await this.createBulkNotifications(notifications);
  }

  async notifySubmissionStatusChanged(
    recipientId: string,
    candidateName: string,
    jobTitle: string,
    newStatus: string,
    submissionId: string
  ) {
    return await this.createNotification({
      recipientId,
      type: NotificationType.SUBMISSION_STATUS_CHANGED,
      title: 'Submission Status Updated',
      content: `Candidate "${candidateName}" submission for job "${jobTitle}" status changed to: ${newStatus}`,
      relatedId: submissionId,
    });
  }

  async notifyMaintainerChangeRequest(
    recipientIds: string[],
    candidateName: string,
    requestedBy: string,
    requestId: string
  ) {
    const notifications: CreateNotification[] = recipientIds.map(recipientId => ({
      recipientId,
      type: NotificationType.MAINTAINER_CHANGE_REQUEST,
      title: 'Maintainer Change Request',
      content: `${requestedBy} has requested to become the maintainer of candidate "${candidateName}"`,
      relatedId: requestId,
    }));

    return await this.createBulkNotifications(notifications);
  }

  async notifyMaintainerChangeReviewed(
    recipientIds: string[],
    candidateName: string,
    status: 'approved' | 'rejected',
    requestId: string
  ) {
    const notifications: CreateNotification[] = recipientIds.map(recipientId => ({
      recipientId,
      type: NotificationType.MAINTAINER_CHANGE_REQUEST,
      title: `Maintainer Change Request ${status.charAt(0).toUpperCase() + status.slice(1)}`,
      content: `The maintainer change request for candidate "${candidateName}" has been ${status}`,
      relatedId: requestId,
    }));

    return await this.createBulkNotifications(notifications);
  }

  async createSystemAnnouncement(
    recipientIds: string[],
    title: string,
    content: string
  ) {
    const notifications: CreateNotification[] = recipientIds.map(recipientId => ({
      recipientId,
      type: NotificationType.SYSTEM_ANNOUNCEMENT,
      title,
      content,
    }));

    return await this.createBulkNotifications(notifications);
  }

  // Get notification statistics
  async getNotificationStats(userId: string) {
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    const [
      totalNotifications,
      unreadNotifications,
      recentNotifications,
      notificationsByType,
    ] = await Promise.all([
      this.prisma.notification.count({
        where: { recipientId: userId },
      }),
      this.prisma.notification.count({
        where: { recipientId: userId, isRead: false },
      }),
      this.prisma.notification.count({
        where: { 
          recipientId: userId,
          createdAt: { gte: thirtyDaysAgo },
        },
      }),
      this.prisma.notification.groupBy({
        by: ['type'],
        where: { 
          recipientId: userId,
          createdAt: { gte: thirtyDaysAgo },
        },
        _count: {
          type: true,
        },
      }),
    ]);

    return {
      total: totalNotifications,
      unread: unreadNotifications,
      recent: recentNotifications,
      byType: notificationsByType.reduce((acc, item) => {
        acc[item.type] = item._count.type;
        return acc;
      }, {} as Record<string, number>),
    };
  }

  // Clean up old notifications (for maintenance)
  async cleanupOldNotifications(daysToKeep: number = 90) {
    const cutoffDate = new Date(Date.now() - daysToKeep * 24 * 60 * 60 * 1000);
    
    const result = await this.prisma.notification.deleteMany({
      where: {
        createdAt: { lt: cutoffDate },
        isRead: true, // Only delete read notifications
      },
    });

    return result.count;
  }
}

export const notificationService = new NotificationService(new PrismaClient());