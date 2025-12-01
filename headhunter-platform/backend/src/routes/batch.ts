import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { webJobParserService } from '@/services/webJobParser';
import { UserRole, JobUrgency, JobStatus } from '@/types';
import { ValidationError } from '@/middleware/error';
import { z } from 'zod';

const urlSchema = z.object({
  url: z.string().url('请提供有效的URL地址')
});

const textSchema = z.object({
  text: z.string().min(50, '文本内容过短，请提供详细的岗位信息')
});

export const batchRoutes = async (fastify: FastifyInstance) => {
  
  // 从URL批量解析岗位
  fastify.post('/jobs/parse-url', {
    schema: {
      tags: ['Batch Import'],
      security: [{ Bearer: [] }],
      description: '从网址批量解析岗位信息',
      body: {
        type: 'object',
        properties: {
          url: { type: 'string', format: 'uri' },
        },
        required: ['url'],
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                jobs: { 
                  type: 'array',
                  items: {
                    type: 'object',
                    properties: {
                      title: { type: 'string' },
                      industry: { type: 'string' },
                      location: { type: 'string' },
                      salaryMin: { type: 'number' },
                      salaryMax: { type: 'number' },
                      description: { type: 'string' },
                      requirements: { type: 'string' },
                      benefits: { type: 'string' }
                    }
                  }
                },
                totalFound: { type: 'number' },
                parseSuccess: { type: 'number' },
                errors: { type: 'array', items: { type: 'string' } }
              }
            }
          }
        }
      }
    },
    preHandler: [
      fastify.authenticate, 
      fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT])
    ],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = urlSchema.parse(request.body);
      console.log('🌐 Starting URL parsing for:', body.url);

      const result = await webJobParserService.parseJobsFromUrl(body.url);
      
      reply.send({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('❌ URL parsing error:', error);
      if (error instanceof z.ZodError) {
        throw new ValidationError(error.errors[0].message);
      }
      throw new ValidationError(error instanceof Error ? error.message : '网址解析失败');
    }
  });

  // 从文本批量解析岗位
  fastify.post('/jobs/parse-text', {
    schema: {
      tags: ['Batch Import'],
      security: [{ Bearer: [] }],
      description: '从文本批量解析岗位信息',
      body: {
        type: 'object',
        properties: {
          text: { type: 'string', minLength: 50 },
        },
        required: ['text'],
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                jobs: { 
                  type: 'array',
                  items: {
                    type: 'object',
                    properties: {
                      title: { type: 'string' },
                      industry: { type: 'string' },
                      location: { type: 'string' },
                      salaryMin: { type: 'number' },
                      salaryMax: { type: 'number' },
                      description: { type: 'string' },
                      requirements: { type: 'string' },
                      benefits: { type: 'string' }
                    }
                  }
                },
                totalFound: { type: 'number' },
                parseSuccess: { type: 'number' },
                errors: { type: 'array', items: { type: 'string' } }
              }
            }
          }
        }
      }
    },
    preHandler: [
      fastify.authenticate, 
      fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT])
    ],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = textSchema.parse(request.body);
      console.log('📝 Starting text parsing...');

      const result = await webJobParserService.parseJobsFromText(body.text);
      
      reply.send({
        success: true,
        data: result
      });
    } catch (error) {
      console.error('❌ Text parsing error:', error);
      if (error instanceof z.ZodError) {
        throw new ValidationError(error.errors[0].message);
      }
      throw new ValidationError(error instanceof Error ? error.message : '文本解析失败');
    }
  });

  // 批量创建岗位
  fastify.post('/jobs/create-batch', {
    schema: {
      tags: ['Batch Import'],
      security: [{ Bearer: [] }],
      description: '批量创建岗位',
      body: {
        type: 'object',
        properties: {
          jobs: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                title: { type: 'string' },
                industry: { type: 'string' },
                location: { type: 'string' },
                salaryMin: { type: 'number' },
                salaryMax: { type: 'number' },
                description: { type: 'string' },
                requirements: { type: 'string' },
                benefits: { type: 'string' },
                urgency: { type: 'string', enum: ['low', 'medium', 'high'] },
                reportTo: { type: 'string' }
              },
              required: ['title']
            },
            minItems: 1,
            maxItems: 50 // 限制批量数量
          }
        },
        required: ['jobs']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                created: { type: 'number' },
                failed: { type: 'number' },
                errors: { type: 'array', items: { type: 'string' } },
                jobIds: { type: 'array', items: { type: 'string' } }
              }
            }
          }
        }
      }
    },
    preHandler: [
      fastify.authenticate, 
      fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT])
    ],
  }, async (request: FastifyRequest<{
    Body: { jobs: Array<{
      title: string;
      industry?: string;
      location?: string;
      salaryMin?: number;
      salaryMax?: number;
      description?: string;
      requirements?: string;
      benefits?: string;
      urgency?: string;
      reportTo?: string;
    }> }
  }>, reply: FastifyReply) => {
    try {
      const { jobs } = request.body;
      const user = (request as any).user;
      
      console.log(`📦 Starting batch creation of ${jobs.length} jobs...`);

      const results = {
        created: 0,
        failed: 0,
        errors: [] as string[],
        jobIds: [] as string[]
      };

      // 批量创建岗位
      for (let i = 0; i < jobs.length; i++) {
        const job = jobs[i];
        try {
          const createdJob = await fastify.prisma.job.create({
            data: {
              title: job.title,
              industry: job.industry || '',
              location: job.location || '',
              salaryMin: job.salaryMin || null,
              salaryMax: job.salaryMax || null,
              description: job.description || '',
              requirements: job.requirements || '',
              benefits: job.benefits || '',
              urgency: (job.urgency as JobUrgency) || JobUrgency.MEDIUM,
              reportTo: job.reportTo || '',
              status: JobStatus.DRAFT,
              companyId: user.companyId,
              createdById: user.id,
            }
          });

          results.created++;
          results.jobIds.push(createdJob.id);
          console.log(`✅ Created job ${i + 1}/${jobs.length}: ${job.title}`);
        } catch (error) {
          results.failed++;
          const errorMsg = `Job ${i + 1} (${job.title}): ${error instanceof Error ? error.message : '创建失败'}`;
          results.errors.push(errorMsg);
          console.error(`❌ Failed to create job ${i + 1}:`, errorMsg);
        }
      }

      console.log(`🎯 Batch creation completed: ${results.created} created, ${results.failed} failed`);
      
      reply.send({
        success: true,
        data: results
      });
    } catch (error) {
      console.error('❌ Batch creation error:', error);
      throw new ValidationError(error instanceof Error ? error.message : '批量创建失败');
    }
  });

  // 一站式：从URL解析并批量创建岗位
  fastify.post('/jobs/import-from-url', {
    schema: {
      tags: ['Batch Import'],
      security: [{ Bearer: [] }],
      description: '从网址一站式导入岗位（解析+创建）',
      body: {
        type: 'object',
        properties: {
          url: { type: 'string', format: 'uri' },
          autoCreate: { type: 'boolean', default: false },
          urgency: { type: 'string', enum: ['low', 'medium', 'high'], default: 'medium' }
        },
        required: ['url']
      }
    },
    preHandler: [
      fastify.authenticate, 
      fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT])
    ],
  }, async (request: FastifyRequest<{
    Body: { url: string; autoCreate?: boolean; urgency?: string }
  }>, reply: FastifyReply) => {
    try {
      const { url, autoCreate = false, urgency = 'medium' } = request.body;
      console.log('🚀 Starting one-stop job import from URL:', url);

      // 第一步：解析岗位
      const parseResult = await webJobParserService.parseJobsFromUrl(url);
      
      let createResult = null;
      if (autoCreate && parseResult.jobs.length > 0) {
        // 第二步：自动创建岗位
        const jobsToCreate = parseResult.jobs.map(job => ({
          ...job,
          urgency,
        }));

        const user = (request as any).user;
        const created = 0;
        const failed = 0;
        const errors: string[] = [];
        const jobIds: string[] = [];

        for (const job of jobsToCreate) {
          try {
            const createdJob = await fastify.prisma.job.create({
              data: {
                title: job.title || '未命名职位',
                industry: job.industry || '',
                location: job.location || '',
                salaryMin: job.salaryMin || null,
                salaryMax: job.salaryMax || null,
                description: job.description || '',
                requirements: job.requirements || '',
                benefits: job.benefits || '',
                urgency: urgency as JobUrgency,
                reportTo: job.reportTo || '',
                status: JobStatus.DRAFT,
                companyId: user.companyId,
                createdById: user.id,
              }
            });
            
            jobIds.push(createdJob.id);
          } catch (error) {
            errors.push(error instanceof Error ? error.message : '创建失败');
          }
        }

        createResult = {
          created: jobIds.length,
          failed: errors.length,
          errors,
          jobIds
        };
      }

      reply.send({
        success: true,
        data: {
          parsing: parseResult,
          creation: createResult
        }
      });
    } catch (error) {
      console.error('❌ One-stop import error:', error);
      throw new ValidationError(error instanceof Error ? error.message : '一站式导入失败');
    }
  });
};