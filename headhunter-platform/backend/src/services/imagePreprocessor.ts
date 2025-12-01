import sharp from 'sharp';
import { promises as fs } from 'fs';
import path from 'path';

export interface ImagePreprocessorOptions {
  enhance?: boolean;
  denoise?: boolean;
  sharpen?: boolean;
  contrast?: number; // 1.0 = no change, > 1.0 = more contrast
  brightness?: number; // 1.0 = no change, > 1.0 = brighter
  threshold?: boolean; // Convert to black and white
  dpi?: number; // DPI for better OCR
}

export class ImagePreprocessorService {
  private readonly outputDir: string;

  constructor() {
    this.outputDir = path.join(process.cwd(), 'uploads', 'processed-images');
    this.ensureOutputDir();
  }

  private async ensureOutputDir(): Promise<void> {
    try {
      await fs.access(this.outputDir);
    } catch {
      await fs.mkdir(this.outputDir, { recursive: true });
    }
  }

  /**
   * 预处理图片以提高OCR识别准确率
   */
  async preprocessImage(
    inputPath: string, 
    options: ImagePreprocessorOptions = {}
  ): Promise<string> {
    const {
      enhance = true,
      denoise = true,
      sharpen = true,
      contrast = 1.2,
      brightness = 1.1,
      threshold = false,
      dpi = 300
    } = options;

    console.log('🖼️  Starting image preprocessing:', path.basename(inputPath));
    const startTime = Date.now();

    try {
      // 生成输出文件路径
      const ext = path.extname(inputPath);
      const basename = path.basename(inputPath, ext);
      const outputPath = path.join(this.outputDir, `processed_${basename}_${Date.now()}${ext}`);

      let pipeline = sharp(inputPath);

      // 获取图片信息
      const metadata = await pipeline.metadata();
      console.log(`📊 Original image: ${metadata.width}x${metadata.height}, format: ${metadata.format}`);

      // 1. 调整DPI以提高OCR精度
      if (dpi > 0) {
        pipeline = pipeline.withMetadata({ density: dpi });
      }

      // 2. 如果图片太小，进行放大
      if (metadata.width && metadata.width < 1000) {
        const scaleFactor = Math.max(1000 / metadata.width, 1.5);
        pipeline = pipeline.resize({
          width: Math.round(metadata.width * scaleFactor),
          height: metadata.height ? Math.round(metadata.height * scaleFactor) : undefined,
          kernel: sharp.kernel.lanczos3
        });
        console.log(`🔍 Upscaling image by factor ${scaleFactor.toFixed(2)}`);
      }

      // 3. 增强对比度和亮度
      if (enhance) {
        pipeline = pipeline.modulate({
          brightness: brightness,
          saturation: 1.1
        });
        
        // 调整对比度
        pipeline = pipeline.linear(contrast, -(128 * contrast) + 128);
        console.log('✨ Enhanced brightness and contrast');
      }

      // 4. 锐化处理
      if (sharpen) {
        pipeline = pipeline.sharpen({
          sigma: 1,
          flat: 1,
          jagged: 2
        });
        console.log('🔪 Applied sharpening');
      }

      // 5. 降噪处理
      if (denoise) {
        pipeline = pipeline.median(3); // 中值滤波去噪
        console.log('🧹 Applied denoising');
      }

      // 6. 二值化处理（黑白图片，增强文字对比度）
      if (threshold) {
        pipeline = pipeline
          .greyscale()
          .threshold(128)
          .negate({ alpha: false });
        console.log('⚫ Applied thresholding');
      }

      // 7. 确保输出为高质量格式
      pipeline = pipeline.png({
        compressionLevel: 0, // 无压缩
        quality: 100
      });

      // 执行处理并保存
      await pipeline.toFile(outputPath);

      const processingTime = Date.now() - startTime;
      console.log(`✅ Image preprocessing completed in ${processingTime}ms`);
      console.log(`📤 Processed image saved: ${path.basename(outputPath)}`);

      // 验证输出文件
      const stats = await fs.stat(outputPath);
      console.log(`📁 Output file size: ${(stats.size / 1024).toFixed(2)} KB`);

      return outputPath;

    } catch (error) {
      console.error('❌ Image preprocessing failed:', error);
      throw new Error(`Image preprocessing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * 批量预处理多个图片
   */
  async preprocessBatch(
    inputPaths: string[], 
    options: ImagePreprocessorOptions = {}
  ): Promise<string[]> {
    console.log(`🔄 Starting batch preprocessing of ${inputPaths.length} images`);
    
    const results: string[] = [];
    
    for (let i = 0; i < inputPaths.length; i++) {
      const inputPath = inputPaths[i];
      console.log(`📷 Processing image ${i + 1}/${inputPaths.length}: ${path.basename(inputPath)}`);
      
      try {
        const outputPath = await this.preprocessImage(inputPath, options);
        results.push(outputPath);
      } catch (error) {
        console.error(`❌ Failed to process ${path.basename(inputPath)}:`, error);
        // 如果处理失败，使用原图
        results.push(inputPath);
      }
    }
    
    console.log(`✅ Batch preprocessing completed: ${results.length} images processed`);
    return results;
  }

  /**
   * 智能选择最佳预处理选项
   */
  async getOptimalOptions(imagePath: string): Promise<ImagePreprocessorOptions> {
    try {
      const metadata = await sharp(imagePath).metadata();
      const stats = await sharp(imagePath).stats();

      const options: ImagePreprocessorOptions = {
        enhance: true,
        denoise: true,
        sharpen: true,
        contrast: 1.2,
        brightness: 1.1,
        threshold: false,
        dpi: 300
      };

      // 根据图片特征调整参数
      if (metadata.width && metadata.width < 800) {
        // 小图片需要更强的增强
        options.contrast = 1.4;
        options.sharpen = true;
        options.dpi = 400;
      }

      // 如果图片很暗，增加亮度
      if (stats.channels && stats.channels[0] && stats.channels[0].mean < 100) {
        options.brightness = 1.3;
        console.log('🌙 Dark image detected, increasing brightness');
      }

      // 如果图片对比度很低，进行二值化
      if (stats.channels && stats.channels[0] && 
          stats.channels[0].max - stats.channels[0].min < 100) {
        options.threshold = true;
        console.log('📊 Low contrast detected, enabling threshold');
      }

      return options;

    } catch (error) {
      console.warn('⚠️  Failed to analyze image, using default options:', error);
      return {
        enhance: true,
        denoise: true,
        sharpen: true,
        contrast: 1.2,
        brightness: 1.1,
        threshold: false,
        dpi: 300
      };
    }
  }

  /**
   * 清理临时处理文件
   */
  async cleanup(maxAge: number = 24 * 60 * 60 * 1000): Promise<void> {
    try {
      const files = await fs.readdir(this.outputDir);
      const now = Date.now();
      
      for (const file of files) {
        const filePath = path.join(this.outputDir, file);
        const stats = await fs.stat(filePath);
        
        if (now - stats.mtime.getTime() > maxAge) {
          await fs.unlink(filePath);
          console.log(`🗑️  Cleaned up old processed image: ${file}`);
        }
      }
    } catch (error) {
      console.warn('⚠️  Cleanup failed:', error);
    }
  }
}

export const imagePreprocessorService = new ImagePreprocessorService();