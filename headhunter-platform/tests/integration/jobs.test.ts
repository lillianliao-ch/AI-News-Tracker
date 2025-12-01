import request from 'supertest';
import { PrismaClient } from '@prisma/client';
import { testUsers, testJobs, testCompanyClients } from '../fixtures/testData';
import { TestHelper } from '../utils/testHelper';

describe('Job Management and Collaboration Integration Tests', () => {
  let testHelper: TestHelper;
  let prisma: PrismaClient;
  let app: any;
  let publisher: any;
  let referrer: any;
  let companyClient: any;

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
    const publisherResult = await testHelper.createTestUser(testUsers.consultant);
    publisher = publisherResult.user;
    
    const referrerResult = await testHelper.createTestUser({
      ...testUsers.soho,
      email: 'referrer@test.com',
    });
    referrer = referrerResult.user;

    // Create test company client
    companyClient = await testHelper.createTestCompanyClient(testCompanyClients[0]);
  });

  describe('Job Creation', () => {
    it('should create a new job successfully', async () => {
      const jobData = {
        ...testJobs[0],
        companyClientId: companyClient.id,
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/jobs',
        testUsers.consultant.email,
        jobData
      ).expect(201);

      testHelper.expectValidJob(response.body);
      expect(response.body.title).toBe(jobData.title);
      expect(response.body.publisherId).toBe(publisher.id);
      expect(response.body.companyClientId).toBe(companyClient.id);
    });

    it('should validate share percentages sum to 100%', async () => {
      const jobData = {
        ...testJobs[0],
        companyClientId: companyClient.id,
        publisherSharePct: 50,
        referrerSharePct: 30,
        platformSharePct: 15, // Total = 95%, should fail
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/jobs',
        testUsers.consultant.email,
        jobData
      ).expect(400);

      expect(response.body.error).toContain('must sum to 100%');
    });

    it('should require valid company client', async () => {
      const jobData = {
        ...testJobs[0],
        companyClientId: 'invalid-client-id',
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/jobs',
        testUsers.consultant.email,
        jobData
      ).expect(400);

      expect(response.body.error).toContain('Invalid company client');
    });

    it('should set default share percentages if not provided', async () => {
      const jobData = {
        title: 'Test Job',
        description: 'Test description',
        requirements: 'Test requirements',
        companyClientId: companyClient.id,
        // No share percentages provided
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/jobs',
        testUsers.consultant.email,
        jobData
      ).expect(201);

      expect(response.body.publisherSharePct).toBe(60);
      expect(response.body.referrerSharePct).toBe(30);
      expect(response.body.platformSharePct).toBe(10);
    });
  });

  describe('Job Listing and Filtering', () => {
    let jobs: any[];

    beforeEach(async () => {
      // Create multiple jobs for testing
      jobs = await Promise.all([
        testHelper.createTestJob({
          ...testJobs[0],
          publisherId: publisher.id,
          companyClientId: companyClient.id,
        }),
        testHelper.createTestJob({
          ...testJobs[1],
          publisherId: publisher.id,
          companyClientId: companyClient.id,
          status: 'paused',
        }),
        testHelper.createTestJob({
          ...testJobs[2],
          publisherId: publisher.id,
          companyClientId: companyClient.id,
          status: 'closed',
        }),
      ]);
    });

    it('should list all jobs with pagination', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/jobs?page=1&limit=10',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('jobs');
      expect(response.body).toHaveProperty('pagination');
      expect(response.body.jobs).toHaveLength(3);
      expect(response.body.pagination.total).toBe(3);
    });

    it('should filter jobs by status', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/jobs?status=open',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.jobs).toHaveLength(1);
      expect(response.body.jobs[0].status).toBe('open');
    });

    it('should filter jobs by industry', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/jobs?industry=Technology',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.jobs.length).toBeGreaterThan(0);
      expect(response.body.jobs.every((job: any) => job.industry === 'Technology')).toBe(true);
    });

    it('should search jobs by title', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/jobs?search=${encodeURIComponent('算法')}`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.jobs.length).toBeGreaterThan(0);
      expect(response.body.jobs.some((job: any) => job.title.includes('算法'))).toBe(true);
    });
  });

  describe('Job Status Management', () => {
    let job: any;

    beforeEach(async () => {
      job = await testHelper.createTestJob({
        ...testJobs[0],
        publisherId: publisher.id,
        companyClientId: companyClient.id,
      });
    });

    it('should update job status', async () => {
      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/jobs/${job.id}/status`,
        testUsers.consultant.email,
        { status: 'paused' }
      ).expect(200);

      expect(response.body.status).toBe('paused');
    });

    it('should only allow job publisher to update status', async () => {
      const { user: otherUser } = await testHelper.createTestUser({
        ...testUsers.soho,
        email: 'other@test.com',
      });

      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/jobs/${job.id}/status`,
        'other@test.com',
        { status: 'paused' }
      ).expect(403);

      expect(response.body.error).toContain('permission');
    });

    it('should validate status values', async () => {
      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/jobs/${job.id}/status`,
        testUsers.consultant.email,
        { status: 'invalid-status' }
      ).expect(400);

      expect(response.body.error).toContain('Invalid status');
    });
  });

  describe('Job Sharing and Permissions', () => {
    let job: any;

    beforeEach(async () => {
      job = await testHelper.createTestJob({
        ...testJobs[0],
        publisherId: publisher.id,
        companyClientId: companyClient.id,
      });
    });

    it('should share job with another user', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/jobs/${job.id}/share`,
        testUsers.consultant.email,
        { targetUserId: referrer.id }
      ).expect(200);

      expect(response.body.message).toContain('shared successfully');
      
      // Verify permission was created
      const permission = await prisma.jobPermission.findFirst({
        where: {
          jobId: job.id,
          grantedToUserId: referrer.id,
        },
      });
      expect(permission).toBeDefined();
    });

    it('should share job with a company', async () => {
      const company = await testHelper.createTestCompany({
        name: 'Test Company',
        industry: 'Technology',
      });

      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/jobs/${job.id}/share`,
        testUsers.consultant.email,
        { targetCompanyId: company.id }
      ).expect(200);

      expect(response.body.message).toContain('shared successfully');
    });

    it('should set expiration date for shared jobs', async () => {
      const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days from now

      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/jobs/${job.id}/share`,
        testUsers.consultant.email,
        { 
          targetUserId: referrer.id,
          expiresAt: expiresAt.toISOString(),
        }
      ).expect(200);

      const permission = await prisma.jobPermission.findFirst({
        where: {
          jobId: job.id,
          grantedToUserId: referrer.id,
        },
      });
      
      expect(permission?.expiresAt).toBeDefined();
    });

    it('should revoke job sharing permissions', async () => {
      // First share the job
      await testHelper.authenticatedRequest(
        'post',
        `/api/jobs/${job.id}/share`,
        testUsers.consultant.email,
        { targetUserId: referrer.id }
      );

      // Then revoke the permission
      const permission = await prisma.jobPermission.findFirst({
        where: {
          jobId: job.id,
          grantedToUserId: referrer.id,
        },
      });

      const response = await testHelper.authenticatedRequest(
        'delete',
        `/api/jobs/${job.id}/permissions/${permission?.id}`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.message).toContain('revoked');
    });

    it('should list shared jobs for a user', async () => {
      // Share job with referrer
      await testHelper.authenticatedRequest(
        'post',
        `/api/jobs/${job.id}/share`,
        testUsers.consultant.email,
        { targetUserId: referrer.id }
      );

      // Get shared jobs
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/jobs/shared',
        'referrer@test.com'
      ).expect(200);

      expect(response.body.jobs).toHaveLength(1);
      expect(response.body.jobs[0].id).toBe(job.id);
    });
  });

  describe('Job Collaboration Statistics', () => {
    let jobs: any[];

    beforeEach(async () => {
      // Create multiple jobs and shares for statistics
      jobs = await Promise.all([
        testHelper.createTestJob({
          ...testJobs[0],
          publisherId: publisher.id,
          companyClientId: companyClient.id,
        }),
        testHelper.createTestJob({
          ...testJobs[1],
          publisherId: publisher.id,
          companyClientId: companyClient.id,
        }),
      ]);

      // Share jobs
      await testHelper.authenticatedRequest(
        'post',
        `/api/jobs/${jobs[0].id}/share`,
        testUsers.consultant.email,
        { targetUserId: referrer.id }
      );
    });

    it('should get collaboration overview statistics', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/collaborations/overview',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('totalJobs');
      expect(response.body).toHaveProperty('sharedJobs');
      expect(response.body).toHaveProperty('activeCollaborations');
      expect(response.body.totalJobs).toBeGreaterThan(0);
    });

    it('should get collaboration network data', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/collaborations/network',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('nodes');
      expect(response.body).toHaveProperty('links');
      expect(Array.isArray(response.body.nodes)).toBe(true);
      expect(Array.isArray(response.body.links)).toBe(true);
    });

    it('should get user collaboration statistics', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/collaborations/stats',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('publishedJobs');
      expect(response.body).toHaveProperty('sharedJobs');
      expect(response.body).toHaveProperty('receivedShares');
      expect(response.body).toHaveProperty('collaborations');
    });

    it('should restrict admin-only statistics to platform admins', async () => {
      const { user: admin } = await testHelper.createTestUser(testUsers.platformAdmin);

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/collaborations/admin-stats',
        testUsers.platformAdmin.email
      ).expect(200);

      expect(response.body).toHaveProperty('systemMetrics');
    });

    it('should deny admin statistics to non-admin users', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/collaborations/admin-stats',
        testUsers.consultant.email
      ).expect(403);

      expect(response.body.error).toContain('Insufficient permissions');
    });
  });

  describe('Job Search and Recommendations', () => {
    beforeEach(async () => {
      // Create jobs with different characteristics
      await Promise.all([
        testHelper.createTestJob({
          title: '高级React开发工程师',
          industry: 'Technology',
          location: 'Shanghai',
          description: 'React前端开发，需要有丰富的前端经验',
          requirements: 'React, JavaScript, TypeScript, 前端框架',
          publisherId: publisher.id,
          companyClientId: companyClient.id,
        }),
        testHelper.createTestJob({
          title: '算法工程师',
          industry: 'AI',
          location: 'Beijing',
          description: '机器学习算法开发，推荐系统优化',
          requirements: 'Python, 机器学习, 算法设计, TensorFlow',
          publisherId: publisher.id,
          companyClientId: companyClient.id,
        }),
      ]);
    });

    it('should search jobs with advanced filters', async () => {
      const searchParams = {
        keywords: ['React', '前端'],
        location: 'Shanghai',
        industry: 'Technology',
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/jobs/search',
        testUsers.consultant.email,
        searchParams
      ).expect(200);

      expect(response.body.jobs.length).toBeGreaterThan(0);
      expect(response.body.jobs[0].title).toContain('React');
    });

    it('should get job recommendations', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/jobs/recommendations',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('recommendations');
      expect(Array.isArray(response.body.recommendations)).toBe(true);
    });

    it('should get similar jobs', async () => {
      const job = await testHelper.createTestJob({
        title: 'Senior React Developer',
        publisherId: publisher.id,
        companyClientId: companyClient.id,
      });

      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/jobs/${job.id}/similar`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('similarJobs');
      expect(Array.isArray(response.body.similarJobs)).toBe(true);
    });
  });
});