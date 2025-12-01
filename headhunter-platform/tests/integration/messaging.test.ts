import request from 'supertest';
import { PrismaClient } from '@prisma/client';
import { testUsers, testNotifications, testMessages } from '../fixtures/testData';
import { TestHelper } from '../utils/testHelper';

describe('Messaging and Notification Integration Tests', () => {
  let testHelper: TestHelper;
  let prisma: PrismaClient;
  let app: any;
  let sender: any;
  let recipient: any;
  let admin: any;

  beforeAll(async () => {
    prisma = new PrismaClient();
    testHelper = new TestHelper(app, prisma);
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  beforeEach(async () => {
    await testHelper.cleanup();
    
    // Create test users
    const senderResult = await testHelper.createTestUser(testUsers.consultant);
    sender = senderResult.user;
    
    const recipientResult = await testHelper.createTestUser({
      ...testUsers.soho,
      email: 'recipient@test.com',
    });
    recipient = recipientResult.user;

    const adminResult = await testHelper.createTestUser(testUsers.platformAdmin);
    admin = adminResult.user;
  });

  describe('Direct Messaging', () => {
    it('should send direct message between users', async () => {
      const messageData = {
        recipientId: recipient.id,
        content: testMessages[0].content,
        metadata: testMessages[0].metadata,
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        messageData
      ).expect(201);

      expect(response.body.message).toContain('sent successfully');
      expect(response.body.messageId).toBeDefined();
    });

    it('should get conversation between two users', async () => {
      // Send a few messages
      await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        {
          recipientId: recipient.id,
          content: 'Hello, how are you?',
        }
      );

      await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        'recipient@test.com',
        {
          recipientId: sender.id,
          content: 'Hi, I am doing well!',
        }
      );

      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/messaging/conversation/${recipient.id}`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.messages.length).toBe(2);
      expect(response.body.messages[0].content).toContain('Hello');
    });

    it('should get user conversations list', async () => {
      // Send messages to create conversations
      await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        {
          recipientId: recipient.id,
          content: 'Test message',
        }
      );

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/messaging/conversations',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.conversations.length).toBe(1);
      expect(response.body.conversations[0].lastMessage).toBeDefined();
    });

    it('should mark messages as read', async () => {
      // Send message
      const sendResponse = await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        {
          recipientId: recipient.id,
          content: 'Test message',
        }
      );

      const messageId = sendResponse.body.messageId;

      // Mark as read
      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/messaging/messages/${messageId}/read`,
        'recipient@test.com'
      ).expect(200);

      expect(response.body.message).toContain('marked as read');
    });

    it('should get unread messages count', async () => {
      // Send unread messages
      await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        {
          recipientId: recipient.id,
          content: 'Unread message 1',
        }
      );

      await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        {
          recipientId: recipient.id,
          content: 'Unread message 2',
        }
      );

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/messaging/unread-count',
        'recipient@test.com'
      ).expect(200);

      expect(response.body.unreadCount).toBe(2);
    });
  });

  describe('Notification System', () => {
    it('should create notification for user', async () => {
      const notificationData = {
        userId: recipient.id,
        type: testNotifications[0].type,
        title: testNotifications[0].title,
        content: testNotifications[0].content,
        data: testNotifications[0].data,
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications',
        testUsers.platformAdmin.email,
        notificationData
      ).expect(201);

      expect(response.body.message).toContain('created successfully');
    });

    it('should get user notifications', async () => {
      // Create notifications
      await Promise.all(testNotifications.map(notification =>
        testHelper.authenticatedRequest(
          'post',
          '/api/notifications',
          testUsers.platformAdmin.email,
          {
            userId: recipient.id,
            ...notification,
          }
        )
      ));

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications',
        'recipient@test.com'
      ).expect(200);

      expect(response.body.notifications.length).toBe(3);
      expect(response.body.notifications[0].type).toBe(testNotifications[0].type);
    });

    it('should filter notifications by type', async () => {
      // Create different types of notifications
      await testHelper.authenticatedRequest(
        'post',
        '/api/notifications',
        testUsers.platformAdmin.email,
        {
          userId: recipient.id,
          type: 'job_shared',
          title: 'Job Shared',
          content: 'A job was shared with you',
        }
      );

      await testHelper.authenticatedRequest(
        'post',
        '/api/notifications',
        testUsers.platformAdmin.email,
        {
          userId: recipient.id,
          type: 'job_closed',
          title: 'Job Closed',
          content: 'A job was closed',
        }
      );

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications?type=job_shared',
        'recipient@test.com'
      ).expect(200);

      expect(response.body.notifications.length).toBe(1);
      expect(response.body.notifications[0].type).toBe('job_shared');
    });

    it('should mark notifications as read', async () => {
      // Create notification
      const createResponse = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications',
        testUsers.platformAdmin.email,
        {
          userId: recipient.id,
          type: 'job_shared',
          title: 'Test Notification',
          content: 'Test content',
        }
      );

      // Get notification ID
      const listResponse = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications',
        'recipient@test.com'
      );

      const notificationId = listResponse.body.notifications[0].id;

      // Mark as read
      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/notifications/${notificationId}/read`,
        'recipient@test.com'
      ).expect(200);

      expect(response.body.message).toContain('marked as read');
    });

    it('should mark all notifications as read', async () => {
      // Create multiple notifications
      await Promise.all([1, 2, 3].map(i =>
        testHelper.authenticatedRequest(
          'post',
          '/api/notifications',
          testUsers.platformAdmin.email,
          {
            userId: recipient.id,
            type: 'job_shared',
            title: `Notification ${i}`,
            content: `Content ${i}`,
          }
        )
      ));

      const response = await testHelper.authenticatedRequest(
        'patch',
        '/api/notifications/mark-all-read',
        'recipient@test.com'
      ).expect(200);

      expect(response.body.message).toContain('marked as read');
    });

    it('should delete notifications', async () => {
      // Create notification
      await testHelper.authenticatedRequest(
        'post',
        '/api/notifications',
        testUsers.platformAdmin.email,
        {
          userId: recipient.id,
          type: 'job_shared',
          title: 'Test Notification',
          content: 'Test content',
        }
      );

      const listResponse = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications',
        'recipient@test.com'
      );

      const notificationId = listResponse.body.notifications[0].id;

      const response = await testHelper.authenticatedRequest(
        'delete',
        `/api/notifications/${notificationId}`,
        'recipient@test.com'
      ).expect(200);

      expect(response.body.message).toContain('deleted successfully');
    });

    it('should get notification statistics', async () => {
      // Create various notifications
      await Promise.all([
        testHelper.authenticatedRequest(
          'post',
          '/api/notifications',
          testUsers.platformAdmin.email,
          {
            userId: recipient.id,
            type: 'job_shared',
            title: 'Job Shared',
            content: 'Job shared',
          }
        ),
        testHelper.authenticatedRequest(
          'post',
          '/api/notifications',
          testUsers.platformAdmin.email,
          {
            userId: recipient.id,
            type: 'job_closed',
            title: 'Job Closed',
            content: 'Job closed',
          }
        ),
      ]);

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications/stats',
        'recipient@test.com'
      ).expect(200);

      expect(response.body).toHaveProperty('total');
      expect(response.body).toHaveProperty('unread');
      expect(response.body).toHaveProperty('byType');
    });
  });

  describe('System Announcements', () => {
    it('should create system announcement', async () => {
      const announcementData = {
        title: 'System Maintenance Notice',
        content: 'The system will be under maintenance from 2AM to 4AM',
        targetRole: 'all',
        priority: 'high',
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications/announcements',
        testUsers.platformAdmin.email,
        announcementData
      ).expect(201);

      expect(response.body.message).toContain('created successfully');
    });

    it('should create role-specific announcement', async () => {
      const announcementData = {
        title: 'New Feature for Consultants',
        content: 'We have added new matching algorithms',
        targetRole: 'consultant',
        priority: 'medium',
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications/announcements',
        testUsers.platformAdmin.email,
        announcementData
      ).expect(201);

      expect(response.body.message).toContain('created successfully');
      
      // Verify it was sent to consultant users
      const notifications = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications',
        testUsers.consultant.email
      );

      expect(notifications.body.notifications.some((n: any) => 
        n.title === announcementData.title
      )).toBe(true);
    });

    it('should create company-specific announcement', async () => {
      const company = await testHelper.createTestCompany({
        name: 'Target Company',
        industry: 'Technology',
      });

      const announcementData = {
        title: 'Company Update',
        content: 'Important update for your company',
        targetCompanyId: company.id,
        priority: 'high',
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications/announcements',
        testUsers.platformAdmin.email,
        announcementData
      ).expect(201);

      expect(response.body.message).toContain('created successfully');
    });

    it('should get announcements list', async () => {
      // Create announcements
      await testHelper.authenticatedRequest(
        'post',
        '/api/notifications/announcements',
        testUsers.platformAdmin.email,
        {
          title: 'Announcement 1',
          content: 'Content 1',
          targetRole: 'all',
        }
      );

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications/announcements',
        testUsers.platformAdmin.email
      ).expect(200);

      expect(response.body.announcements.length).toBeGreaterThan(0);
    });

    it('should only allow admins to create announcements', async () => {
      const announcementData = {
        title: 'Unauthorized Announcement',
        content: 'This should fail',
        targetRole: 'all',
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications/announcements',
        testUsers.consultant.email,
        announcementData
      ).expect(403);

      expect(response.body.error).toContain('Insufficient permissions');
    });
  });

  describe('Real-time Notifications', () => {
    it('should send real-time notification via WebSocket', async () => {
      // This would test WebSocket functionality
      // In a real test, you would establish WebSocket connection and verify events
      
      const notificationData = {
        userId: recipient.id,
        type: 'job_shared',
        title: 'Real-time Notification',
        content: 'This is a real-time notification',
        realTime: true,
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications',
        testUsers.platformAdmin.email,
        notificationData
      ).expect(201);

      expect(response.body.message).toContain('created successfully');
      // In real test, verify WebSocket event was emitted
    });

    it('should handle notification delivery status', async () => {
      const notificationData = {
        userId: recipient.id,
        type: 'job_shared',
        title: 'Delivery Test',
        content: 'Testing delivery status',
      };

      const createResponse = await testHelper.authenticatedRequest(
        'post',
        '/api/notifications',
        testUsers.platformAdmin.email,
        notificationData
      );

      const listResponse = await testHelper.authenticatedRequest(
        'get',
        '/api/notifications',
        'recipient@test.com'
      );

      const notification = listResponse.body.notifications[0];
      expect(notification).toHaveProperty('deliveredAt');
      expect(notification.status).toBe('delivered');
    });
  });

  describe('Message Threading and Context', () => {
    it('should associate messages with jobs', async () => {
      const companyClient = await testHelper.createTestCompanyClient({
        name: 'Test Client',
        industry: 'Technology',
      });

      const job = await testHelper.createTestJob({
        title: 'Test Job',
        publisherId: sender.id,
        companyClientId: companyClient.id,
        description: 'Test job description',
        requirements: 'Test requirements',
      });

      const messageData = {
        recipientId: recipient.id,
        content: 'Message about the test job',
        metadata: { jobId: job.id },
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        messageData
      ).expect(201);

      expect(response.body.message).toContain('sent successfully');
    });

    it('should associate messages with candidates', async () => {
      const candidate = await testHelper.createTestCandidate({
        name: 'Test Candidate',
        phone: '+86-13900000999',
        email: 'testcandidate@email.com',
        maintainerId: sender.id,
      });

      const messageData = {
        recipientId: recipient.id,
        content: 'Message about the candidate',
        metadata: { candidateId: candidate.id },
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        messageData
      ).expect(201);

      expect(response.body.message).toContain('sent successfully');
    });

    it('should get messages by context', async () => {
      const companyClient = await testHelper.createTestCompanyClient({
        name: 'Test Client',
        industry: 'Technology',
      });

      const job = await testHelper.createTestJob({
        title: 'Context Test Job',
        publisherId: sender.id,
        companyClientId: companyClient.id,
        description: 'Test description',
        requirements: 'Test requirements',
      });

      // Send job-related messages
      await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        {
          recipientId: recipient.id,
          content: 'First job message',
          metadata: { jobId: job.id },
        }
      );

      await testHelper.authenticatedRequest(
        'post',
        '/api/messaging/send',
        testUsers.consultant.email,
        {
          recipientId: recipient.id,
          content: 'Second job message',
          metadata: { jobId: job.id },
        }
      );

      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/messaging/context/job/${job.id}`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.messages.length).toBe(2);
      expect(response.body.messages.every((m: any) => 
        m.metadata.jobId === job.id
      )).toBe(true);
    });
  });
});