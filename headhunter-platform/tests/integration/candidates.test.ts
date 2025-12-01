import request from 'supertest';
import { PrismaClient } from '@prisma/client';
import { testUsers, testCandidates, testJobs, testMatchingCriteria, testCompanyClients } from '../fixtures/testData';
import { TestHelper } from '../utils/testHelper';

describe('Candidate Management and Matching Integration Tests', () => {
  let testHelper: TestHelper;
  let prisma: PrismaClient;
  let app: any;
  let maintainer: any;
  let otherUser: any;
  let job: any;
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
    const maintainerResult = await testHelper.createTestUser(testUsers.consultant);
    maintainer = maintainerResult.user;
    
    const otherResult = await testHelper.createTestUser({
      ...testUsers.soho,
      email: 'other@test.com',
    });
    otherUser = otherResult.user;

    // Create test company client and job
    companyClient = await testHelper.createTestCompanyClient(testCompanyClients[0]);
    job = await testHelper.createTestJob({
      ...testJobs[0],
      publisherId: maintainer.id,
      companyClientId: companyClient.id,
    });
  });

  describe('Candidate Creation and Management', () => {
    it('should create a new candidate successfully', async () => {
      const candidateData = {
        ...testCandidates[0],
        maintainerId: maintainer.id,
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates',
        testUsers.consultant.email,
        candidateData
      ).expect(201);

      testHelper.expectValidCandidate(response.body);
      expect(response.body.name).toBe(candidateData.name);
      expect(response.body.maintainerId).toBe(maintainer.id);
    });

    it('should detect duplicate candidates by name and phone', async () => {
      const candidateData = {
        ...testCandidates[0],
        maintainerId: maintainer.id,
      };

      // Create first candidate
      await testHelper.authenticatedRequest(
        'post',
        '/api/candidates',
        testUsers.consultant.email,
        candidateData
      ).expect(201);

      // Try to create duplicate
      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates',
        testUsers.consultant.email,
        candidateData
      ).expect(409);

      expect(response.body.error).toContain('already exists');
    });

    it('should allow same name with different phone', async () => {
      const candidateData1 = {
        ...testCandidates[0],
        maintainerId: maintainer.id,
      };

      const candidateData2 = {
        ...testCandidates[0],
        phone: '+86-13900000999',
        email: 'different@email.com',
        maintainerId: maintainer.id,
      };

      await testHelper.authenticatedRequest(
        'post',
        '/api/candidates',
        testUsers.consultant.email,
        candidateData1
      ).expect(201);

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates',
        testUsers.consultant.email,
        candidateData2
      ).expect(201);

      expect(response.body.name).toBe(candidateData2.name);
    });

    it('should validate required fields', async () => {
      const invalidData = {
        name: 'Test Candidate',
        // missing phone, email, maintainerId
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates',
        testUsers.consultant.email,
        invalidData
      ).expect(400);

      expect(response.body.error).toBeDefined();
    });
  });

  describe('Candidate Search and Filtering', () => {
    let candidates: any[];

    beforeEach(async () => {
      // Create multiple candidates with different characteristics
      candidates = await Promise.all([
        testHelper.createTestCandidate({
          ...testCandidates[0], // 张伟 - 算法工程师
          maintainerId: maintainer.id,
        }),
        testHelper.createTestCandidate({
          ...testCandidates[1], // 李娜 - 前端工程师
          maintainerId: maintainer.id,
        }),
        testHelper.createTestCandidate({
          ...testCandidates[2], // 王强 - 产品经理
          maintainerId: maintainer.id,
        }),
      ]);
    });

    it('should search candidates with basic filters', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/search',
        testUsers.consultant.email,
        {
          keywords: ['算法'],
          page: 1,
          limit: 10,
        }
      ).expect(200);

      expect(response.body.candidates.length).toBeGreaterThan(0);
      expect(response.body.candidates.some((c: any) => c.tags.includes('算法'))).toBe(true);
    });

    it('should filter candidates by tags', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/search',
        testUsers.consultant.email,
        {
          tags: ['React', 'Vue'],
        }
      ).expect(200);

      expect(response.body.candidates.length).toBeGreaterThan(0);
      expect(response.body.candidates.every((c: any) => 
        c.tags.some((tag: string) => ['React', 'Vue'].includes(tag))
      )).toBe(true);
    });

    it('should filter candidates by location', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/search',
        testUsers.consultant.email,
        {
          location: 'Beijing',
        }
      ).expect(200);

      expect(response.body.candidates.length).toBeGreaterThan(0);
      expect(response.body.candidates.every((c: any) => c.location === 'Beijing')).toBe(true);
    });

    it('should filter candidates by maintainer', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/search',
        testUsers.consultant.email,
        {
          maintainerId: maintainer.id,
        }
      ).expect(200);

      expect(response.body.candidates.length).toBe(3);
      expect(response.body.candidates.every((c: any) => c.maintainerId === maintainer.id)).toBe(true);
    });

    it('should exclude candidates already submitted to specific job', async () => {
      // Submit one candidate to the job
      await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidates[0].id}/submit`,
        testUsers.consultant.email,
        { jobId: job.id }
      );

      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/search',
        testUsers.consultant.email,
        {
          excludeSubmittedToJob: job.id,
        }
      ).expect(200);

      expect(response.body.candidates.length).toBe(2);
      expect(response.body.candidates.every((c: any) => c.id !== candidates[0].id)).toBe(true);
    });
  });

  describe('Intelligent Candidate Matching', () => {
    let candidates: any[];

    beforeEach(async () => {
      candidates = await Promise.all([
        testHelper.createTestCandidate({
          ...testCandidates[0], // High match for algorithm job
          maintainerId: maintainer.id,
        }),
        testHelper.createTestCandidate({
          ...testCandidates[1], // Medium match for frontend job
          maintainerId: maintainer.id,
        }),
        testHelper.createTestCandidate({
          ...testCandidates[2], // Low match for algorithm job
          maintainerId: maintainer.id,
        }),
      ]);
    });

    it('should get candidate recommendations for a job', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/jobs/${job.id}/candidate-recommendations`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('recommendations');
      expect(Array.isArray(response.body.recommendations)).toBe(true);
      expect(response.body.recommendations.length).toBeGreaterThan(0);
      
      // Check that recommendations are sorted by score
      const scores = response.body.recommendations.map((r: any) => r.score);
      expect(scores).toEqual([...scores].sort((a, b) => b - a));
    });

    it('should calculate matching scores correctly', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/match',
        testUsers.consultant.email,
        {
          jobCriteria: testMatchingCriteria.highMatch,
          candidateIds: candidates.map(c => c.id),
        }
      ).expect(200);

      expect(response.body).toHaveProperty('matches');
      expect(response.body.matches.length).toBe(3);
      
      // Find the algorithm candidate match
      const algorithmMatch = response.body.matches.find((m: any) => 
        m.candidate.name === testCandidates[0].name
      );
      
      expect(algorithmMatch.score).toBeGreaterThan(60); // Should be high match
      expect(algorithmMatch.factors.length).toBeGreaterThan(0);
    });

    it('should provide matching factors explanation', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/match',
        testUsers.consultant.email,
        {
          jobCriteria: testMatchingCriteria.highMatch,
          candidateIds: [candidates[0].id],
        }
      ).expect(200);

      const match = response.body.matches[0];
      expect(match).toHaveProperty('factors');
      expect(Array.isArray(match.factors)).toBe(true);
      expect(match.factors.some((f: string) => f.includes('Tag match'))).toBe(true);
    });

    it('should match candidates with different weights', async () => {
      // Test with different matching criteria
      const techMatch = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/match',
        testUsers.consultant.email,
        {
          jobCriteria: testMatchingCriteria.mediumMatch,
          candidateIds: candidates.map(c => c.id),
        }
      );

      const productMatch = await testHelper.authenticatedRequest(
        'post',
        '/api/candidates/match',
        testUsers.consultant.email,
        {
          jobCriteria: testMatchingCriteria.lowMatch,
          candidateIds: candidates.map(c => c.id),
        }
      );

      // Scores should be different for different criteria
      expect(techMatch.body.matches[0].score).not.toBe(productMatch.body.matches[0].score);
    });
  });

  describe('Candidate Submission and Status Management', () => {
    let candidate: any;

    beforeEach(async () => {
      candidate = await testHelper.createTestCandidate({
        ...testCandidates[0],
        maintainerId: maintainer.id,
      });
    });

    it('should submit candidate to job', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/submit`,
        testUsers.consultant.email,
        { 
          jobId: job.id,
          notes: 'Perfect match for this role',
        }
      ).expect(201);

      expect(response.body).toHaveProperty('submissionId');
      expect(response.body.message).toContain('submitted successfully');
    });

    it('should prevent duplicate submissions', async () => {
      // First submission
      await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/submit`,
        testUsers.consultant.email,
        { jobId: job.id }
      ).expect(201);

      // Duplicate submission
      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/submit`,
        testUsers.consultant.email,
        { jobId: job.id }
      ).expect(409);

      expect(response.body.error).toContain('already submitted');
    });

    it('should update candidate submission status', async () => {
      // Submit candidate first
      const submitResponse = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/submit`,
        testUsers.consultant.email,
        { jobId: job.id }
      );

      const submissionId = submitResponse.body.submissionId;

      // Update status
      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/candidates/submissions/${submissionId}/status`,
        testUsers.consultant.email,
        { 
          status: 'interviewing',
          notes: 'Moved to interview stage',
        }
      ).expect(200);

      expect(response.body.status).toBe('interviewing');
    });

    it('should track submission history', async () => {
      // Submit and update status multiple times
      const submitResponse = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/submit`,
        testUsers.consultant.email,
        { jobId: job.id }
      );

      const submissionId = submitResponse.body.submissionId;

      await testHelper.authenticatedRequest(
        'patch',
        `/api/candidates/submissions/${submissionId}/status`,
        testUsers.consultant.email,
        { status: 'interviewing' }
      );

      await testHelper.authenticatedRequest(
        'patch',
        `/api/candidates/submissions/${submissionId}/status`,
        testUsers.consultant.email,
        { status: 'offered' }
      );

      // Get submission history
      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/candidates/submissions/${submissionId}/history`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.history.length).toBeGreaterThan(0);
      expect(response.body.history).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ status: 'submitted' }),
          expect.objectContaining({ status: 'interviewing' }),
          expect.objectContaining({ status: 'offered' }),
        ])
      );
    });

    it('should get submission statistics', async () => {
      // Create multiple submissions
      const candidates = await Promise.all([
        testHelper.createTestCandidate({
          ...testCandidates[0],
          email: 'candidate1@test.com',
          maintainerId: maintainer.id,
        }),
        testHelper.createTestCandidate({
          ...testCandidates[1],
          email: 'candidate2@test.com',
          maintainerId: maintainer.id,
        }),
      ]);

      await Promise.all([
        testHelper.authenticatedRequest(
          'post',
          `/api/candidates/${candidates[0].id}/submit`,
          testUsers.consultant.email,
          { jobId: job.id }
        ),
        testHelper.authenticatedRequest(
          'post',
          `/api/candidates/${candidates[1].id}/submit`,
          testUsers.consultant.email,
          { jobId: job.id }
        ),
      ]);

      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/jobs/${job.id}/submission-stats`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.totalSubmissions).toBe(2);
      expect(response.body.statusBreakdown).toBeDefined();
    });
  });

  describe('Candidate Maintainer Changes', () => {
    let candidate: any;

    beforeEach(async () => {
      candidate = await testHelper.createTestCandidate({
        ...testCandidates[0],
        maintainerId: maintainer.id,
      });
    });

    it('should request maintainer change', async () => {
      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/request-maintainer-change`,
        'other@test.com',
        {
          reason: 'Better industry expertise for this candidate',
        }
      ).expect(201);

      expect(response.body.message).toContain('request submitted');
    });

    it('should list maintainer change requests', async () => {
      // Create a request first
      await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/request-maintainer-change`,
        'other@test.com',
        { reason: 'Test reason' }
      );

      const response = await testHelper.authenticatedRequest(
        'get',
        '/api/candidates/maintainer-requests',
        testUsers.consultant.email
      ).expect(200);

      expect(response.body.requests.length).toBe(1);
      expect(response.body.requests[0].requestedById).toBe(otherUser.id);
    });

    it('should approve maintainer change request', async () => {
      // Create request
      const requestResponse = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/request-maintainer-change`,
        'other@test.com',
        { reason: 'Test reason' }
      );

      // Find the request
      const listResponse = await testHelper.authenticatedRequest(
        'get',
        '/api/candidates/maintainer-requests',
        testUsers.consultant.email
      );

      const requestId = listResponse.body.requests[0].id;

      // Approve request
      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/candidates/maintainer-requests/${requestId}`,
        testUsers.consultant.email,
        { action: 'approve' }
      ).expect(200);

      expect(response.body.message).toContain('approved');
      
      // Verify maintainer was changed
      const updatedCandidate = await prisma.candidate.findUnique({
        where: { id: candidate.id },
      });
      expect(updatedCandidate?.maintainerId).toBe(otherUser.id);
    });

    it('should reject maintainer change request', async () => {
      // Create and reject request
      await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/request-maintainer-change`,
        'other@test.com',
        { reason: 'Test reason' }
      );

      const listResponse = await testHelper.authenticatedRequest(
        'get',
        '/api/candidates/maintainer-requests',
        testUsers.consultant.email
      );

      const requestId = listResponse.body.requests[0].id;

      const response = await testHelper.authenticatedRequest(
        'patch',
        `/api/candidates/maintainer-requests/${requestId}`,
        testUsers.consultant.email,
        { 
          action: 'reject',
          reason: 'Insufficient justification',
        }
      ).expect(200);

      expect(response.body.message).toContain('rejected');
      
      // Verify maintainer was not changed
      const candidate_unchanged = await prisma.candidate.findUnique({
        where: { id: candidate.id },
      });
      expect(candidate_unchanged?.maintainerId).toBe(maintainer.id);
    });
  });

  describe('Candidate File Upload and Management', () => {
    let candidate: any;

    beforeEach(async () => {
      candidate = await testHelper.createTestCandidate({
        ...testCandidates[0],
        maintainerId: maintainer.id,
      });
    });

    it('should upload candidate resume', async () => {
      // Mock file upload - in real tests, this would include actual file data
      const mockFileData = {
        originalname: 'resume.pdf',
        mimetype: 'application/pdf',
        size: 1024000,
        buffer: Buffer.from('mock pdf content'),
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/upload-resume`,
        testUsers.consultant.email,
        { file: mockFileData }
      ).expect(200);

      expect(response.body.message).toContain('uploaded successfully');
      expect(response.body.filePath).toBeDefined();
    });

    it('should validate file type and size', async () => {
      const invalidFile = {
        originalname: 'invalid.txt',
        mimetype: 'text/plain',
        size: 1024000,
      };

      const response = await testHelper.authenticatedRequest(
        'post',
        `/api/candidates/${candidate.id}/upload-resume`,
        testUsers.consultant.email,
        { file: invalidFile }
      ).expect(400);

      expect(response.body.error).toContain('Invalid file type');
    });

    it('should get candidate files', async () => {
      const response = await testHelper.authenticatedRequest(
        'get',
        `/api/candidates/${candidate.id}/files`,
        testUsers.consultant.email
      ).expect(200);

      expect(response.body).toHaveProperty('files');
      expect(Array.isArray(response.body.files)).toBe(true);
    });
  });
});