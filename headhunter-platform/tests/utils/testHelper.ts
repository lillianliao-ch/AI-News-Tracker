import request from 'supertest';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';

export class TestHelper {
  private app: any;
  private prisma: PrismaClient;
  private tokens: Map<string, string> = new Map();

  constructor(app: any, prisma: PrismaClient) {
    this.app = app;
    this.prisma = prisma;
  }

  // Generate JWT token for testing
  generateToken(userId: string, role: string): string {
    const payload = { userId, role };
    return jwt.sign(payload, process.env.JWT_SECRET!, { expiresIn: '1h' });
  }

  // Create and authenticate test users
  async createTestUser(userData: {
    username: string;
    email: string;
    phone: string;
    password: string;
    role: string;
    status?: string;
    companyId?: string;
  }) {
    const user = await this.prisma.user.create({
      data: {
        ...userData,
        status: userData.status || 'active',
        // Note: using mock password for testing - in production this would be hashed
      },
    });

    const token = this.generateToken(user.id, user.role);
    this.tokens.set(user.email, token);

    return { user, token };
  }

  // Get authentication headers
  getAuthHeaders(email: string): { Authorization: string } {
    const token = this.tokens.get(email);
    if (!token) {
      throw new Error(`No token found for user: ${email}`);
    }
    return { Authorization: `Bearer ${token}` };
  }

  // Make authenticated requests
  async authenticatedRequest(method: 'get' | 'post' | 'put' | 'patch' | 'delete', url: string, userEmail: string, data?: any) {
    const headers = this.getAuthHeaders(userEmail);
    const req = request(this.app)[method](url).set(headers);
    
    if (data && (method === 'post' || method === 'put' || method === 'patch')) {
      return req.send(data);
    }
    
    return req;
  }

  // Clean database between tests
  async cleanup() {
    await this.prisma.candidateSubmission.deleteMany();
    await this.prisma.jobPermission.deleteMany();
    await this.prisma.maintainerChangeRequest.deleteMany();
    await this.prisma.notification.deleteMany();
    await this.prisma.candidate.deleteMany();
    await this.prisma.job.deleteMany();
    await this.prisma.companyClient.deleteMany();
    await this.prisma.user.deleteMany();
    await this.prisma.company.deleteMany();
    this.tokens.clear();
  }

  // Create test company
  async createTestCompany(companyData: {
    name: string;
    industry?: string;
    location?: string;
    status?: string;
    businessLicense?: string;
  }) {
    return await this.prisma.company.create({
      data: {
        ...companyData,
        status: companyData.status || 'approved',
      },
    });
  }

  // Create test company client
  async createTestCompanyClient(clientData: {
    name: string;
    industry?: string;
    location?: string;
    description?: string;
    contactName?: string;
    contactPhone?: string;
    maintainerId?: string;
  }) {
    return await this.prisma.companyClient.create({
      data: {
        ...clientData,
        contactName: clientData.contactName || 'Test Contact',
        contactPhone: clientData.contactPhone || '+86-13900001234',
        maintainerId: clientData.maintainerId || 'test-maintainer-id',
      },
    });
  }

  // Create test job
  async createTestJob(jobData: {
    title: string;
    publisherId: string;
    companyClientId: string;
    industry?: string;
    location?: string;
    description: string;
    requirements: string;
    status?: string;
    publisherSharePct?: number;
    referrerSharePct?: number;
    platformSharePct?: number;
  }) {
    return await this.prisma.job.create({
      data: {
        ...jobData,
        status: jobData.status || 'open',
        publisherSharePct: jobData.publisherSharePct || 60,
        referrerSharePct: jobData.referrerSharePct || 30,
        platformSharePct: jobData.platformSharePct || 10,
      },
    });
  }

  // Create test candidate
  async createTestCandidate(candidateData: {
    name: string;
    phone: string;
    email: string;
    maintainerId: string;
    tags?: string[];
    location?: string;
    experience?: string;
  }) {
    return await this.prisma.candidate.create({
      data: candidateData,
    });
  }

  // Assertion helpers
  expectValidUser(user: any) {
    expect(user).toHaveProperty('id');
    expect(user).toHaveProperty('username');
    expect(user).toHaveProperty('email');
    expect(user).toHaveProperty('role');
    expect(user).toHaveProperty('status');
    expect(user).not.toHaveProperty('passwordHash');
  }

  expectValidJob(job: any) {
    expect(job).toHaveProperty('id');
    expect(job).toHaveProperty('title');
    expect(job).toHaveProperty('description');
    expect(job).toHaveProperty('requirements');
    expect(job).toHaveProperty('status');
    expect(job).toHaveProperty('publisherId');
    expect(job).toHaveProperty('companyClientId');
  }

  expectValidCandidate(candidate: any) {
    expect(candidate).toHaveProperty('id');
    expect(candidate).toHaveProperty('name');
    expect(candidate).toHaveProperty('phone');
    expect(candidate).toHaveProperty('email');
    expect(candidate).toHaveProperty('maintainerId');
  }
}