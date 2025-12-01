import { FastifyInstance } from 'fastify';

export async function resumeMatchingRoutes(fastify: FastifyInstance) {
  // Find matching jobs for a candidate (simplified version)
  fastify.post('/jobs-for-candidate', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    const { candidateId, config } = request.body as any;

    try {
      // For now, return mock data with the existing job
      const mockJobMatches = [
        {
          job: {
            id: '550e8400-e29b-41d4-a716-446655440003',
            title: 'Senior Full-Stack Developer',
            company: 'Tech Startup Inc.',
            description: 'We are looking for a senior full-stack developer...',
            location: 'Beijing, Shanghai',
            salaryRange: { min: 300000, max: 500000 },
            requiredSkills: ['React', 'Node.js', 'TypeScript'],
            industry: 'Technology'
          },
          scores: {
            skills: 0.85,
            experience: 0.75,
            industry: 0.90,
            location: 0.80,
            salary: 0.70,
            education: 0.65,
            overall: 0.78
          },
          confidence: 0.82,
          ranking: 1,
          matchReasons: [
            'Strong match in React and Node.js skills',
            'Industry experience in technology sector',
            'Location preference aligns with job location'
          ]
        }
      ];

      return {
        success: true,
        data: mockJobMatches,
        total: mockJobMatches.length,
        config: config || {}
      };
    } catch (error) {
      fastify.log.error('Error finding matching jobs:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to find matching jobs'
      });
    }
  });

  // Find matching candidates for a job (simplified version)
  fastify.post('/candidates-for-job', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    const { jobId, config } = request.body as any;

    try {
      // For now, return mock data with the existing candidates
      const mockCandidateMatches = [
        {
          resume: {
            id: 'resume-candidate-1',
            candidateId: '550e8400-e29b-41d4-a716-446655440004',
            filename: 'alice_wang_resume.pdf',
            parsedData: {
              personalInfo: {
                name: 'Alice Wang',
                email: 'alice.wang@example.com',
                phone: '+8613900000001',
                location: 'Beijing'
              },
              skills: [
                { name: 'React', level: 'Expert', yearsOfExperience: 5 },
                { name: 'Node.js', level: 'Advanced', yearsOfExperience: 4 },
                { name: 'TypeScript', level: 'Advanced', yearsOfExperience: 3 }
              ],
              workExperience: [
                {
                  company: 'TechCorp',
                  position: 'Senior Frontend Developer',
                  startDate: new Date('2020-01-01'),
                  endDate: null,
                  description: 'Led frontend development for major e-commerce platform',
                  industry: 'Technology'
                }
              ],
              summary: 'Experienced full-stack developer with 6+ years of experience in React and Node.js'
            },
            confidence: 0.89
          },
          scores: {
            skills: 0.88,
            experience: 0.80,
            industry: 0.95,
            location: 0.90,
            salary: 0.75,
            education: 0.70,
            overall: 0.83
          },
          confidence: 0.85,
          ranking: 1,
          matchReasons: [
            'Excellent skills match in React, Node.js, and TypeScript',
            'Strong experience in technology industry',
            'Located in preferred job location (Beijing)'
          ]
        },
        {
          resume: {
            id: 'resume-candidate-2',
            candidateId: '550e8400-e29b-41d4-a716-446655440005',
            filename: 'bob_chen_resume.pdf',
            parsedData: {
              personalInfo: {
                name: 'Bob Chen',
                email: 'bob.chen@example.com',
                phone: '+8613900000002',
                location: 'Shanghai'
              },
              skills: [
                { name: 'JavaScript', level: 'Expert', yearsOfExperience: 6 },
                { name: 'Node.js', level: 'Expert', yearsOfExperience: 5 },
                { name: 'AWS', level: 'Advanced', yearsOfExperience: 3 }
              ],
              workExperience: [
                {
                  company: 'CloudSystems',
                  position: 'Backend Architect',
                  startDate: new Date('2019-06-01'),
                  endDate: null,
                  description: 'Designed and implemented scalable backend systems',
                  industry: 'Technology'
                }
              ],
              summary: 'Senior backend developer and architect with expertise in cloud technologies'
            },
            confidence: 0.82
          },
          scores: {
            skills: 0.75,
            experience: 0.85,
            industry: 0.90,
            location: 0.85,
            salary: 0.80,
            education: 0.75,
            overall: 0.81
          },
          confidence: 0.83,
          ranking: 2,
          matchReasons: [
            'Strong backend and Node.js expertise',
            'Extensive experience with cloud technologies',
            'Located in Shanghai (job location)'
          ]
        }
      ];

      return {
        success: true,
        data: mockCandidateMatches,
        total: mockCandidateMatches.length,
        config: config || {}
      };
    } catch (error) {
      fastify.log.error('Error finding matching candidates:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to find matching candidates'
      });
    }
  });

  // Get available jobs for matching
  fastify.get('/available-jobs', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      // Get jobs from database
      const jobs = await fastify.prisma.job.findMany({
        where: {
          status: 'open'
        },
        include: {
          companyClient: {
            select: {
              name: true,
              industry: true
            }
          }
        },
        take: 50,
        orderBy: {
          createdAt: 'desc'
        }
      });

      const formattedJobs = jobs.map(job => ({
        id: job.id,
        title: job.title,
        company: job.companyClient?.name || 'Unknown Company',
        industry: job.industry || job.companyClient?.industry || 'Unknown',
        location: job.location,
        salaryRange: {
          min: job.salaryMin,
          max: job.salaryMax
        },
        description: job.description,
        requirements: job.requirements
      }));

      return {
        success: true,
        data: formattedJobs,
        total: formattedJobs.length
      };
    } catch (error) {
      fastify.log.error('Error fetching available jobs:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to fetch available jobs'
      });
    }
  });

  // Get available candidates for matching
  fastify.get('/available-candidates', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      // Get candidates from database
      const candidates = await fastify.prisma.candidate.findMany({
        take: 50,
        orderBy: {
          createdAt: 'desc'
        }
      });

      const formattedCandidates = candidates.map(candidate => ({
        id: candidate.id,
        name: candidate.name,
        email: candidate.email,
        phone: candidate.phone,
        tags: candidate.tags || [],
        hasResume: false // Will be updated when we have actual resume data
      }));

      return {
        success: true,
        data: formattedCandidates,
        total: formattedCandidates.length
      };
    } catch (error) {
      fastify.log.error('Error fetching available candidates:', error);
      return reply.status(500).send({
        success: false,
        error: 'Failed to fetch available candidates'
      });
    }
  });
}