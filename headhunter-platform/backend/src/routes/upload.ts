import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { fileUploadService } from '@/services/fileUpload';
import { enhancedOcrService } from '@/services/enhancedOcrService';
import { UserRole } from '@/types';
import { ValidationError } from '@/middleware/error';

export const uploadRoutes = async (fastify: FastifyInstance) => {
  // Upload resume
  fastify.post('/resume', {
    schema: {
      tags: ['Upload'],
      security: [{ Bearer: [] }],
      consumes: ['multipart/form-data'],
      description: 'Upload a resume file (PDF, DOC, DOCX)',
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const uploadedFile = await fileUploadService.uploadResume(request);
      
      reply.send({
        success: true,
        file: {
          filename: uploadedFile.filename,
          originalName: uploadedFile.originalName,
          url: uploadedFile.url,
          size: uploadedFile.size,
          mimetype: uploadedFile.mimetype,
        },
      });
    } catch (error) {
      throw new ValidationError(error instanceof Error ? error.message : 'Upload failed');
    }
  });

  // Upload avatar
  fastify.post('/avatar', {
    schema: {
      tags: ['Upload'],
      security: [{ Bearer: [] }],
      consumes: ['multipart/form-data'],
      description: 'Upload an avatar image (JPG, PNG, GIF)',
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const uploadedFile = await fileUploadService.uploadAvatar(request);
      
      reply.send({
        success: true,
        file: {
          filename: uploadedFile.filename,
          originalName: uploadedFile.originalName,
          url: uploadedFile.url,
          size: uploadedFile.size,
          mimetype: uploadedFile.mimetype,
        },
      });
    } catch (error) {
      throw new ValidationError(error instanceof Error ? error.message : 'Upload failed');
    }
  });

  // Upload general file
  fastify.post('/file', {
    schema: {
      tags: ['Upload'],
      security: [{ Bearer: [] }],
      consumes: ['multipart/form-data'],
      description: 'Upload a general file',
    },
    preHandler: [fastify.authenticate, fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT, UserRole.SOHO])],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const uploadedFiles = await fileUploadService.uploadFile(request);
      
      reply.send({
        success: true,
        files: uploadedFiles.map(file => ({
          filename: file.filename,
          originalName: file.originalName,
          url: file.url,
          size: file.size,
          mimetype: file.mimetype,
        })),
      });
    } catch (error) {
      throw new ValidationError(error instanceof Error ? error.message : 'Upload failed');
    }
  });

  // Get file info
  fastify.get('/info/:filename', {
    schema: {
      tags: ['Upload'],
      security: [{ Bearer: [] }],
      params: {
        type: 'object',
        properties: {
          filename: { type: 'string' },
        },
        required: ['filename'],
      },
      querystring: {
        type: 'object',
        properties: {
          type: { type: 'string', enum: ['resume', 'avatar', 'temp'], default: 'temp' },
        },
      },
    },
    preHandler: [fastify.authenticate],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { filename } = request.params as { filename: string };
    const { type = 'temp' } = request.query as { type: string };
    
    const fileInfo = fileUploadService.getFileInfo(filename, type);
    
    if (!fileInfo) {
      return reply.code(404).send({ error: 'File not found' });
    }
    
    reply.send({
      success: true,
      file: {
        filename: fileInfo.filename,
        originalName: fileInfo.originalName,
        url: fileInfo.url,
        size: fileInfo.size,
        mimetype: fileInfo.mimetype,
      },
    });
  });

  // Parse job from image
  fastify.post('/parse-job-image', {
    schema: {
      tags: ['Upload'],
      security: [{ Bearer: [] }],
      consumes: ['multipart/form-data'],
      description: 'Upload job image and parse job information using OCR',
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            parsedJob: {
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
                urgency: { type: 'string' },
                reportTo: { type: 'string' },
              },
            },
            file: {
              type: 'object',
              properties: {
                filename: { type: 'string' },
                originalName: { type: 'string' },
                url: { type: 'string' },
                size: { type: 'number' },
                mimetype: { type: 'string' },
              },
            },
          },
        },
      },
    },
    preHandler: [
      async function ensureMultipart(request: FastifyRequest, reply: FastifyReply) {
        console.log('🔍 Multipart pre-handler check');
        console.log('📝 Request headers:', request.headers);
        console.log('📝 Content-Type:', request.headers['content-type']);
        console.log('📝 Request isMultipart:', request.isMultipart());
        
        if (!request.isMultipart()) {
          throw new ValidationError('Request is not multipart/form-data');
        }
      },
      fastify.authenticate, 
      fastify.requireRole([UserRole.COMPANY_ADMIN, UserRole.CONSULTANT])
    ],
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {

      // Upload the image file
      const uploadedFile = await fileUploadService.uploadFile(request, {
        allowedTypes: [
          'image/jpeg',
          'image/png',
          'image/gif',
          'image/bmp',
          'image/webp'
        ],
        maxSize: 10 * 1024 * 1024, // 10MB
        uploadDir: 'job-images'
      });

      if (uploadedFile.length === 0) {
        throw new ValidationError('No image file uploaded');
      }

      if (uploadedFile.length > 1) {
        throw new ValidationError('Only one image file allowed');
      }

      const file = uploadedFile[0];
      if (!file) {
        throw new ValidationError('No file uploaded');
      }

      console.log('✅ File uploaded successfully:', file.filename);

      // Parse job information from the image using enhanced multi-engine OCR with preprocessing
      const parsedJob = await enhancedOcrService.parseJobFromImage(file.path, {
        usePreprocessing: true,
        useNLP: true,
        confidenceThreshold: 0.6,
        enableBaiduOCR: true,
        enableAliyunOCR: true
      });

      reply.send({
        success: true,
        parsedJob,
        file: {
          filename: file.filename,
          originalName: file.originalName,
          url: file.url,
          size: file.size,
          mimetype: file.mimetype,
        },
      });
    } catch (error) {
      console.error('❌ Parse job image error:', error);
      throw new ValidationError(error instanceof Error ? error.message : 'Image parsing failed');
    }
  });
};