import { PrismaClient } from '@prisma/client';

export interface SearchFilters {
  keywords?: string[];
  tags?: string[];
  experience?: {
    min?: number;
    max?: number;
  };
  location?: string;
  availability?: string;
  maintainerId?: string;
  excludeSubmittedToJob?: string;
}

export interface MatchingResult {
  candidateId: string;
  score: number;
  matchingFactors: string[];
  candidate: {
    id: string;
    name: string;
    email?: string;
    phone: string;
    tags: string[];
    maintainer: {
      username: string;
      company?: {
        name: string;
      };
    };
  };
}

export interface JobMatchingCriteria {
  jobId: string;
  title: string;
  industry?: string;
  location?: string;
  requirements: string;
  salaryMin?: number;
  salaryMax?: number;
  tags?: string[];
}

export class CandidateMatchingService {
  constructor(private prisma: PrismaClient) {}

  // Extract keywords from job requirements
  private extractKeywords(text: string): string[] {
    const commonWords = new Set([
      'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by',
      'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would',
      'could', 'should', 'may', 'might', 'can', 'must', 'years', 'year', 'experience',
      'skills', 'knowledge', 'ability', 'proficiency', 'familiarity'
    ]);

    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 2 && !commonWords.has(word))
      .slice(0, 20); // Limit to top 20 keywords
  }

  // Calculate matching score between candidate and job
  private calculateMatchScore(
    candidate: any,
    jobCriteria: JobMatchingCriteria
  ): { score: number; factors: string[] } {
    let score = 0;
    const factors: string[] = [];
    const jobKeywords = this.extractKeywords(jobCriteria.requirements);

    // Tag matching (40% weight)
    if (candidate.tags && candidate.tags.length > 0 && jobCriteria.tags) {
      const matchingTags = candidate.tags.filter((tag: string) => 
        jobCriteria.tags?.some(jobTag => 
          jobTag.toLowerCase().includes(tag.toLowerCase()) ||
          tag.toLowerCase().includes(jobTag.toLowerCase())
        )
      );
      
      if (matchingTags.length > 0) {
        const tagScore = (matchingTags.length / Math.max(candidate.tags.length, jobCriteria.tags.length)) * 40;
        score += tagScore;
        factors.push(`Tag match: ${matchingTags.join(', ')}`);
      }
    }

    // Industry matching (20% weight)
    if (jobCriteria.industry && candidate.tags) {
      const industryMatch = candidate.tags.some((tag: string) => 
        tag.toLowerCase().includes(jobCriteria.industry!.toLowerCase()) ||
        jobCriteria.industry!.toLowerCase().includes(tag.toLowerCase())
      );
      
      if (industryMatch) {
        score += 20;
        factors.push(`Industry alignment: ${jobCriteria.industry}`);
      }
    }

    // Location matching (10% weight)
    if (jobCriteria.location && candidate.tags) {
      const locationMatch = candidate.tags.some((tag: string) => 
        tag.toLowerCase().includes(jobCriteria.location!.toLowerCase()) ||
        jobCriteria.location!.toLowerCase().includes(tag.toLowerCase())
      );
      
      if (locationMatch) {
        score += 10;
        factors.push(`Location match: ${jobCriteria.location}`);
      }
    }

    // Keyword matching from job requirements (30% weight)
    if (candidate.tags && jobKeywords.length > 0) {
      const matchingKeywords = jobKeywords.filter(keyword => 
        candidate.tags.some((tag: string) => 
          tag.toLowerCase().includes(keyword) || 
          keyword.includes(tag.toLowerCase())
        )
      );
      
      if (matchingKeywords.length > 0) {
        const keywordScore = (matchingKeywords.length / jobKeywords.length) * 30;
        score += keywordScore;
        factors.push(`Skill keywords: ${matchingKeywords.slice(0, 5).join(', ')}`);
      }
    }

    return { score: Math.min(score, 100), factors };
  }

  // Search candidates with filters
  async searchCandidates(
    filters: SearchFilters,
    page: number = 1,
    limit: number = 20
  ): Promise<{
    candidates: any[];
    total: number;
    page: number;
    limit: number;
    pages: number;
  }> {
    const skip = (page - 1) * limit;
    const where: any = {};

    // Text search across name, email, and tags
    if (filters.keywords && filters.keywords.length > 0) {
      const keywordConditions = filters.keywords.map(keyword => ({
        OR: [
          { name: { contains: keyword, mode: 'insensitive' } },
          { email: { contains: keyword, mode: 'insensitive' } },
          { 
            tags: {
              hasSome: [keyword]
            }
          }
        ]
      }));
      
      where.AND = keywordConditions;
    }

    // Tag filtering
    if (filters.tags && filters.tags.length > 0) {
      where.tags = {
        hasSome: filters.tags
      };
    }

    // Location filtering
    if (filters.location) {
      where.tags = {
        ...where.tags,
        hasSome: [filters.location]
      };
    }

    // Maintainer filtering
    if (filters.maintainerId) {
      where.maintainerId = filters.maintainerId;
    }

    // Exclude candidates already submitted to a specific job
    if (filters.excludeSubmittedToJob) {
      where.candidateSubmissions = {
        none: {
          jobId: filters.excludeSubmittedToJob
        }
      };
    }

    const [candidates, total] = await Promise.all([
      this.prisma.candidate.findMany({
        where,
        skip,
        take: limit,
        include: {
          maintainer: {
            select: {
              id: true,
              username: true,
              email: true,
              company: {
                select: {
                  id: true,
                  name: true,
                }
              }
            }
          },
          _count: {
            select: {
              candidateSubmissions: true
            }
          }
        },
        orderBy: { createdAt: 'desc' }
      }),
      this.prisma.candidate.count({ where })
    ]);

    return {
      candidates,
      total,
      page,
      limit,
      pages: Math.ceil(total / limit)
    };
  }

  // Find matching candidates for a specific job
  async findCandidatesForJob(
    jobId: string,
    limit: number = 50
  ): Promise<MatchingResult[]> {
    // Get job details
    const job = await this.prisma.job.findUnique({
      where: { id: jobId },
      select: {
        id: true,
        title: true,
        industry: true,
        location: true,
        requirements: true,
        salaryMin: true,
        salaryMax: true
      }
    });

    if (!job) {
      throw new Error('Job not found');
    }

    // Extract potential tags from job requirements
    const jobKeywords = this.extractKeywords(job.requirements);
    const jobTags = [...jobKeywords];
    
    if (job.industry) {
      jobTags.push(job.industry.toLowerCase());
    }
    
    if (job.location) {
      jobTags.push(job.location.toLowerCase());
    }

    const jobCriteria: JobMatchingCriteria = {
      jobId: job.id,
      title: job.title,
      industry: job.industry || undefined,
      location: job.location || undefined,
      requirements: job.requirements,
      salaryMin: job.salaryMin || undefined,
      salaryMax: job.salaryMax || undefined,
      tags: jobTags
    };

    // Get candidates not already submitted to this job
    const candidates = await this.prisma.candidate.findMany({
      where: {
        candidateSubmissions: {
          none: {
            jobId: jobId
          }
        }
      },
      include: {
        maintainer: {
          select: {
            username: true,
            company: {
              select: {
                name: true
              }
            }
          }
        }
      },
      take: limit * 2 // Get more candidates to have options after scoring
    });

    // Calculate matching scores
    const matchingResults: MatchingResult[] = candidates
      .map(candidate => {
        const { score, factors } = this.calculateMatchScore(candidate, jobCriteria);
        
        return {
          candidateId: candidate.id,
          score,
          matchingFactors: factors,
          candidate: {
            id: candidate.id,
            name: candidate.name,
            email: candidate.email || undefined,
            phone: candidate.phone,
            tags: candidate.tags as string[],
            maintainer: {
              username: candidate.maintainer.username,
              company: candidate.maintainer.company || undefined
            }
          }
        };
      })
      .filter(result => result.score > 10) // Only include candidates with meaningful match
      .sort((a, b) => b.score - a.score) // Sort by score descending
      .slice(0, limit); // Limit results

    return matchingResults;
  }

  // Find recommended jobs for a candidate
  async findJobsForCandidate(
    candidateId: string,
    limit: number = 20
  ): Promise<{
    jobId: string;
    score: number;
    matchingFactors: string[];
    job: any;
  }[]> {
    // Get candidate details
    const candidate = await this.prisma.candidate.findUnique({
      where: { id: candidateId },
      select: {
        id: true,
        name: true,
        tags: true
      }
    });

    if (!candidate) {
      throw new Error('Candidate not found');
    }

    // Get open jobs that candidate hasn't been submitted to
    const jobs = await this.prisma.job.findMany({
      where: {
        status: 'open',
        candidateSubmissions: {
          none: {
            candidateId: candidateId
          }
        }
      },
      include: {
        companyClient: {
          select: {
            name: true,
            industry: true,
            location: true
          }
        },
        publisher: {
          select: {
            username: true,
            company: {
              select: {
                name: true
              }
            }
          }
        }
      },
      take: limit * 2
    });

    // Score jobs for the candidate
    const jobMatches = jobs
      .map(job => {
        const jobCriteria: JobMatchingCriteria = {
          jobId: job.id,
          title: job.title,
          industry: job.industry || undefined,
          location: job.location || undefined,
          requirements: job.requirements,
          salaryMin: job.salaryMin || undefined,
          salaryMax: job.salaryMax || undefined,
          tags: this.extractKeywords(job.requirements)
        };

        const { score, factors } = this.calculateMatchScore(candidate, jobCriteria);

        return {
          jobId: job.id,
          score,
          matchingFactors: factors,
          job: {
            id: job.id,
            title: job.title,
            industry: job.industry,
            location: job.location,
            salaryMin: job.salaryMin,
            salaryMax: job.salaryMax,
            description: job.description,
            requirements: job.requirements,
            status: job.status,
            companyClient: job.companyClient,
            publisher: job.publisher,
            createdAt: job.createdAt
          }
        };
      })
      .filter(result => result.score > 15)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);

    return jobMatches;
  }
}