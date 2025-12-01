import fs from 'fs';
import path from 'path';
import { pipeline } from 'stream';
import { promisify } from 'util';
import crypto from 'crypto';
import { FastifyRequest } from 'fastify';

const pump = promisify(pipeline);

export interface UploadOptions {
  allowedTypes?: string[];
  maxSize?: number;
  uploadDir?: string;
}

export interface UploadedFile {
  filename: string;
  originalName: string;
  path: string;
  size: number;
  mimetype: string;
  url: string;
}

export class FileUploadService {
  private uploadDir: string;
  private baseUrl: string;

  constructor(uploadDir: string = 'uploads', baseUrl: string = 'http://localhost:4000') {
    this.uploadDir = path.resolve(uploadDir);
    this.baseUrl = baseUrl;
    this.ensureUploadDir();
  }

  private ensureUploadDir() {
    if (!fs.existsSync(this.uploadDir)) {
      fs.mkdirSync(this.uploadDir, { recursive: true });
    }

    // Create subdirectories
    const subDirs = ['resumes', 'avatars', 'temp', 'job-images'];
    subDirs.forEach(dir => {
      const fullPath = path.join(this.uploadDir, dir);
      if (!fs.existsSync(fullPath)) {
        fs.mkdirSync(fullPath, { recursive: true });
      }
    });
  }

  private generateFileName(originalName: string): string {
    const ext = path.extname(originalName);
    const basename = path.basename(originalName, ext);
    const hash = crypto.randomBytes(16).toString('hex');
    const timestamp = Date.now();
    return `${basename}_${timestamp}_${hash}${ext}`;
  }

  async uploadFile(
    request: FastifyRequest, 
    options: UploadOptions = {}
  ): Promise<UploadedFile[]> {
    const {
      allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/png',
        'image/gif'
      ],
      maxSize = 50 * 1024 * 1024, // 50MB
      uploadDir = 'temp'
    } = options;

    const files = request.files();
    const uploadedFiles: UploadedFile[] = [];

    for await (const file of files) {
      // Validate file type
      if (!allowedTypes.includes(file.mimetype)) {
        throw new Error(`File type ${file.mimetype} not allowed. Allowed types: ${allowedTypes.join(', ')}`);
      }

      // Generate unique filename
      const filename = this.generateFileName(file.filename);
      const filePath = path.join(this.uploadDir, uploadDir, filename);

      // Create write stream and save file
      await pump(file.file, fs.createWriteStream(filePath));

      // Get file stats
      const stats = fs.statSync(filePath);

      // Check file size
      if (stats.size > maxSize) {
        fs.unlinkSync(filePath); // Delete the file
        throw new Error(`File size ${stats.size} exceeds maximum allowed size ${maxSize}`);
      }

      const uploadedFile: UploadedFile = {
        filename,
        originalName: file.filename,
        path: filePath,
        size: stats.size,
        mimetype: file.mimetype,
        url: `${this.baseUrl}/uploads/${uploadDir}/${filename}`
      };

      uploadedFiles.push(uploadedFile);
    }

    return uploadedFiles;
  }

  async uploadResume(request: FastifyRequest): Promise<UploadedFile> {
    const files = await this.uploadFile(request, {
      allowedTypes: [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ],
      maxSize: 10 * 1024 * 1024, // 10MB
      uploadDir: 'resumes'
    });

    if (files.length === 0) {
      throw new Error('No file uploaded');
    }

    if (files.length > 1) {
      throw new Error('Only one resume file allowed');
    }

    return files[0];
  }

  async uploadAvatar(request: FastifyRequest): Promise<UploadedFile> {
    const files = await this.uploadFile(request, {
      allowedTypes: [
        'image/jpeg',
        'image/png',
        'image/gif'
      ],
      maxSize: 5 * 1024 * 1024, // 5MB
      uploadDir: 'avatars'
    });

    if (files.length === 0) {
      throw new Error('No file uploaded');
    }

    if (files.length > 1) {
      throw new Error('Only one avatar file allowed');
    }

    return files[0];
  }

  deleteFile(filePath: string): boolean {
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error deleting file:', error);
      return false;
    }
  }

  getFileInfo(filename: string, subDir: string = 'temp'): UploadedFile | null {
    const filePath = path.join(this.uploadDir, subDir, filename);
    
    if (!fs.existsSync(filePath)) {
      return null;
    }

    const stats = fs.statSync(filePath);

    return {
      filename,
      originalName: filename,
      path: filePath,
      size: stats.size,
      mimetype: this.getMimeType(filename),
      url: `${this.baseUrl}/uploads/${subDir}/${filename}`
    };
  }

  private getMimeType(filename: string): string {
    const ext = path.extname(filename).toLowerCase();
    const mimeTypes: { [key: string]: string } = {
      '.pdf': 'application/pdf',
      '.doc': 'application/msword',
      '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif'
    };

    return mimeTypes[ext] || 'application/octet-stream';
  }
}

export const fileUploadService = new FileUploadService();