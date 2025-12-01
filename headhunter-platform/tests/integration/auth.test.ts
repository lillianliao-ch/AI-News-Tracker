import request from 'supertest';
import { PrismaClient } from '@prisma/client';
import { testUsers, testCompanies } from '../fixtures/testData';
import { TestHelper } from '../utils/testHelper';

// Mock the backend app - in real tests, this would import the actual app
const mockApp = {
  // This would be the actual Fastify app instance
};

describe('Authentication and Authorization Integration Tests', () => {
  let testHelper: TestHelper;
  let prisma: PrismaClient;
  let app: any;

  beforeAll(async () => {
    // Initialize test database and app
    prisma = new PrismaClient();
    // app = await createApp(); // This would initialize the actual app
    testHelper = new TestHelper(app, prisma);
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  beforeEach(async () => {
    await testHelper.cleanup();
  });

  describe('User Registration', () => {
    it('should register a new consultant user successfully', async () => {
      const userData = testUsers.consultant;
      
      const response = await request(app)
        .post('/api/auth/register')
        .send(userData)
        .expect(201);

      expect(response.body).toHaveProperty('message');
      expect(response.body).toHaveProperty('userId');
      expect(response.body.message).toContain('successfully');
    });

    it('should register a company admin with company info', async () => {
      const userData = {
        ...testUsers.companyAdmin,
        companyName: 'TechCorp Solutions',
        businessLicense: 'TC001234567890',
      };

      const response = await request(app)
        .post('/api/auth/register')
        .send(userData)
        .expect(201);

      expect(response.body).toHaveProperty('userId');
      
      // Verify company was created
      const user = await prisma.user.findFirst({
        where: { email: userData.email },
        include: { company: true },
      });
      
      expect(user?.company).toBeDefined();
      expect(user?.company?.name).toBe(userData.companyName);
    });

    it('should reject registration with duplicate email', async () => {
      await testHelper.createTestUser(testUsers.consultant);
      
      const response = await request(app)
        .post('/api/auth/register')
        .send(testUsers.consultant)
        .expect(409);

      expect(response.body.error).toContain('already exists');
    });

    it('should validate required fields', async () => {
      const invalidData = {
        username: 'test',
        // missing email, phone, password
        role: 'consultant',
      };

      const response = await request(app)
        .post('/api/auth/register')
        .send(invalidData)
        .expect(400);

      expect(response.body.error).toBeDefined();
    });
  });

  describe('User Login', () => {
    beforeEach(async () => {
      await testHelper.createTestUser(testUsers.consultant);
      await testHelper.createTestUser(testUsers.platformAdmin);
    });

    it('should login with valid credentials', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: testUsers.consultant.email,
          password: testUsers.consultant.password,
        })
        .expect(200);

      expect(response.body).toHaveProperty('token');
      expect(response.body).toHaveProperty('user');
      expect(response.body.token).toBeValidToken();
      testHelper.expectValidUser(response.body.user);
    });

    it('should reject invalid credentials', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: testUsers.consultant.email,
          password: 'wrongpassword',
        })
        .expect(401);

      expect(response.body.error).toContain('Invalid credentials');
    });

    it('should reject login for pending users', async () => {
      await testHelper.createTestUser(testUsers.pendingUser);

      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: testUsers.pendingUser.email,
          password: testUsers.pendingUser.password,
        })
        .expect(403);

      expect(response.body.error).toContain('pending approval');
    });
  });

  describe('User Profile', () => {
    beforeEach(async () => {
      await testHelper.createTestUser(testUsers.consultant);
    });

    it('should get user profile with valid token', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/auth/profile',
        testUsers.consultant.email
      ).expect(200);

      testHelper.expectValidUser(response.body);
      expect(response.body.email).toBe(testUsers.consultant.email);
    });

    it('should reject requests without token', async () => {
      const response = await request(app)
        .get('/api/auth/profile')
        .expect(401);

      expect(response.body.error).toContain('No token provided');
    });

    it('should reject requests with invalid token', async () => {
      const response = await request(app)
        .get('/api/auth/profile')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);

      expect(response.body.error).toContain('Invalid token');
    });
  });

  describe('Role-based Access Control', () => {
    beforeEach(async () => {
      await testHelper.createTestUser(testUsers.platformAdmin);
      await testHelper.createTestUser(testUsers.companyAdmin);
      await testHelper.createTestUser(testUsers.consultant);
      await testHelper.createTestUser(testUsers.soho);
    });

    describe('Platform Admin Access', () => {
      it('should allow platform admin to access pending users', async () => {
        const response = await testHelper.authenticatedRequest(
          'get',
          '/api/auth/pending-users',
          testUsers.platformAdmin.email
        ).expect(200);

        expect(response.body).toHaveProperty('users');
        expect(Array.isArray(response.body.users)).toBe(true);
      });

      it('should allow platform admin to approve users', async () => {
        const { user: pendingUser } = await testHelper.createTestUser({
          ...testUsers.pendingUser,
          status: 'pending',
        });

        const response = await testHelper.authenticatedRequest(
          'patch',
          `/api/auth/approve-user/${pendingUser.id}`,
          testUsers.platformAdmin.email,
          { action: 'approve' }
        ).expect(200);

        expect(response.body.message).toContain('approved');
        
        // Verify user status was updated
        const updatedUser = await prisma.user.findUnique({
          where: { id: pendingUser.id },
        });
        expect(updatedUser?.status).toBe('approved');
      });
    });

    describe('Company Admin Access', () => {
      it('should allow company admin to access company endpoints', async () => {
        const response = await testHelper.authenticatedRequest(
          'get',
          '/api/companies',
          testUsers.companyAdmin.email
        ).expect(200);

        expect(response.body).toBeDefined();
      });

      it('should not allow company admin to access platform admin endpoints', async () => {
        const response = await testHelper.authenticatedRequest(
          'get',
          '/api/auth/pending-users',
          testUsers.companyAdmin.email
        ).expect(403);

        expect(response.body.error).toContain('Insufficient permissions');
      });
    });

    describe('Consultant and SOHO Access', () => {
      it('should allow consultants to access jobs', async () => {
        const response = await testHelper.authenticatedRequest(
          'get',
          '/api/jobs',
          testUsers.consultant.email
        ).expect(200);

        expect(response.body).toBeDefined();
      });

      it('should allow SOHO to access jobs', async () => {
        const response = await testHelper.authenticatedRequest(
          'get',
          '/api/jobs',
          testUsers.soho.email
        ).expect(200);

        expect(response.body).toBeDefined();
      });

      it('should not allow consultants to access admin endpoints', async () => {
        const response = await testHelper.authenticatedRequest(
          'get',
          '/api/auth/pending-users',
          testUsers.consultant.email
        ).expect(403);

        expect(response.body.error).toContain('Insufficient permissions');
      });
    });
  });

  describe('User Management (Admin Functions)', () => {
    beforeEach(async () => {
      await testHelper.createTestUser(testUsers.platformAdmin);
    });

    it('should list pending users', async () => {
      // Create some pending users
      await testHelper.createTestUser({
        ...testUsers.pendingUser,
        email: 'pending1@test.com',
        status: 'pending',
      });
      await testHelper.createTestUser({
        ...testUsers.pendingUser,
        email: 'pending2@test.com',
        status: 'pending',
      });

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/auth/pending-users',
        testUsers.platformAdmin.email
      ).expect(200);

      expect(response.body.users).toHaveLength(2);
      expect(response.body.users.every((user: any) => user.status === 'pending')).toBe(true);
    });

    it('should approve pending user', async () => {
      const { user: pendingUser } = await testHelper.createTestUser({
        ...testUsers.pendingUser,
        status: 'pending',
      });

      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/auth/approve-user/${pendingUser.id}`,
        testUsers.platformAdmin.email,
        { action: 'approve' }
      ).expect(200);

      expect(response.body.user.status).toBe('approved');
      expect(response.body.message).toContain('approved');
    });

    it('should reject pending user', async () => {
      const { user: pendingUser } = await testHelper.createTestUser({
        ...testUsers.pendingUser,
        status: 'pending',
      });

      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/auth/approve-user/${pendingUser.id}`,
        testUsers.platformAdmin.email,
        { action: 'reject', reason: 'Incomplete information' }
      ).expect(200);

      expect(response.body.user.status).toBe('rejected');
      expect(response.body.message).toContain('rejected');
    });
  });
});