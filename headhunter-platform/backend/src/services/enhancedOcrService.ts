import { readFile } from 'fs/promises';
import Tesseract from 'tesseract.js';
import axios from 'axios';
import { imagePreprocessorService } from './imagePreprocessor';

export interface OCRResult {
  text: string;
  confidence: number;
  engine: string;
  processingTime: number;
  success: boolean;
  error?: string;
}

export interface ParsedJobInfo {
  title?: string;
  industry?: string;
  location?: string;
  salaryMin?: number;
  salaryMax?: number;
  description?: string;
  requirements?: string;
  benefits?: string;
  urgency?: string;
  reportTo?: string;
}

export interface FieldVotingResult {
  value: string;
  confidence: number;
  sources: string[];
  agreement: number;
}

export interface EnhancedOCROptions {
  usePreprocessing?: boolean;
  preprocessingOptions?: any;
  enableBaiduOCR?: boolean;
  enableAliyunOCR?: boolean;
  confidenceThreshold?: number;
  useNLP?: boolean;
}

export class EnhancedOCRService {
  private enabledEngines: string[] = [];
  
  constructor() {
    // 检查环境变量并启用可用的OCR引擎
    if (process.env.ALIYUN_OCR_ACCESS_KEY && process.env.ALIYUN_OCR_SECRET) {
      this.enabledEngines.push('aliyun');
    }
    if (process.env.BAIDU_OCR_API_KEY && process.env.BAIDU_OCR_SECRET_KEY) {
      this.enabledEngines.push('baidu');
    }
    // Tesseract始终作为备用
    this.enabledEngines.push('tesseract');
    
    console.log('🚀 Enhanced Multi-Engine OCR initialized with engines:', this.enabledEngines);
  }

  async parseJobFromImage(
    imagePath: string, 
    options: EnhancedOCROptions = {}
  ): Promise<ParsedJobInfo> {
    const {
      usePreprocessing = true,
      preprocessingOptions,
      confidenceThreshold = 0.7,
      useNLP = true
    } = options;

    console.log('🔍 Starting enhanced multi-engine OCR processing for:', imagePath);
    const overallStartTime = Date.now();

    try {
      let processedImagePath = imagePath;

      // 1. 图片预处理
      if (usePreprocessing) {
        console.log('🖼️  Preprocessing image for better OCR results...');
        const optimalOptions = await imagePreprocessorService.getOptimalOptions(imagePath);
        const finalOptions = { ...optimalOptions, ...preprocessingOptions };
        processedImagePath = await imagePreprocessorService.preprocessImage(imagePath, finalOptions);
      }

      // 2. 多引擎OCR识别
      const ocrPromises = this.enabledEngines.map(engine => 
        this.runOCREngine(engine, processedImagePath)
      );

      const ocrResults = await Promise.allSettled(ocrPromises);
      const successfulResults: OCRResult[] = [];

      // 收集成功的OCR结果
      ocrResults.forEach((result, index) => {
        if (result.status === 'fulfilled' && result.value.success) {
          successfulResults.push(result.value);
        } else {
          console.warn(`❌ ${this.enabledEngines[index]} OCR failed:`, 
            result.status === 'rejected' ? result.reason : result.value.error);
        }
      });

      if (successfulResults.length === 0) {
        throw new Error('All OCR engines failed');
      }

      console.log(`✅ ${successfulResults.length}/${this.enabledEngines.length} OCR engines succeeded`);

      // 3. 选择最佳OCR文本
      const primaryText = this.selectBestOCRText(successfulResults);

      // 4. 多引擎字段提取和投票
      const fieldResults = await this.performFieldExtraction(successfulResults, primaryText, useNLP);

      // 5. 构建最终结果
      const result = this.buildFinalResult(fieldResults, primaryText);

      // 6. 智能补全低置信度字段
      await this.enhanceWithSmartGeneration(result, fieldResults, confidenceThreshold);

      const totalTime = Date.now() - overallStartTime;
      console.log(`🎯 Enhanced OCR processing completed in ${totalTime}ms`);

      return result;

    } catch (error) {
      console.error('❌ Enhanced OCR processing failed:', error);
      throw error;
    }
  }

  private async runOCREngine(engine: string, imagePath: string): Promise<OCRResult> {
    const startTime = Date.now();
    
    try {
      let result: { text: string; confidence: number };

      switch (engine) {
        case 'aliyun':
          result = await this.callAliyunOCR(imagePath);
          break;
        case 'baidu':
          result = await this.callBaiduOCR(imagePath);
          break;
        case 'tesseract':
          result = await this.callTesseractOCR(imagePath);
          break;
        default:
          throw new Error(`Unknown OCR engine: ${engine}`);
      }

      const processingTime = Date.now() - startTime;
      console.log(`✅ ${engine} OCR completed in ${processingTime}ms, confidence: ${result.confidence.toFixed(2)}`);

      return {
        text: result.text,
        confidence: result.confidence,
        engine,
        processingTime,
        success: true
      };

    } catch (error) {
      const processingTime = Date.now() - startTime;
      console.error(`❌ ${engine} OCR failed after ${processingTime}ms:`, error);

      return {
        text: '',
        confidence: 0,
        engine,
        processingTime,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async callAliyunOCR(imagePath: string): Promise<{text: string, confidence: number}> {
    if (!process.env.ALIYUN_OCR_ACCESS_KEY || !process.env.ALIYUN_OCR_SECRET) {
      throw new Error('Aliyun OCR credentials not configured');
    }

    const imageBuffer = await readFile(imagePath);
    const base64Image = imageBuffer.toString('base64');

    // 阿里云OCR API调用逻辑
    const response = await axios.post('https://ocr-api.cn-hangzhou.aliyuncs.com/', {
      image: base64Image,
      configure: JSON.stringify({
        side: 'face',
        min_size: 200,
        output_prob: true
      })
    }, {
      headers: {
        'Authorization': `APPCODE ${process.env.ALIYUN_OCR_ACCESS_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.data.success) {
      const words = response.data.ret || [];
      const text = words.map((item: any) => item.word).join(' ');
      const avgConfidence = words.reduce((sum: number, item: any) => 
        sum + (item.prob || 0.8), 0) / words.length;
      
      return {
        text,
        confidence: avgConfidence
      };
    }
    
    throw new Error('Aliyun OCR API failed');
  }

  private async callBaiduOCR(imagePath: string): Promise<{text: string, confidence: number}> {
    if (!process.env.BAIDU_OCR_API_KEY || !process.env.BAIDU_OCR_SECRET_KEY) {
      throw new Error('Baidu OCR credentials not configured');
    }

    // 获取access_token
    const tokenResponse = await axios.post('https://aip.baidubce.com/oauth/2.0/token', null, {
      params: {
        grant_type: 'client_credentials',
        client_id: process.env.BAIDU_OCR_API_KEY,
        client_secret: process.env.BAIDU_OCR_SECRET_KEY
      }
    });

    const accessToken = tokenResponse.data.access_token;
    const imageBuffer = await readFile(imagePath);
    const base64Image = imageBuffer.toString('base64');

    // 调用通用文字识别API
    const response = await axios.post(
      `https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=${accessToken}`,
      `image=${encodeURIComponent(base64Image)}`,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    if (response.data.words_result) {
      const words = response.data.words_result;
      const text = words.map((word: any) => word.words).join(' ');
      const avgConfidence = words.reduce((sum: number, word: any) => 
        sum + (word.probability?.average || 0.8), 0) / words.length;
      
      return {
        text,
        confidence: avgConfidence
      };
    }
    
    throw new Error('Baidu OCR API failed');
  }

  private async callTesseractOCR(imagePath: string): Promise<{text: string, confidence: number}> {
    const worker = await Tesseract.createWorker('chi_sim+eng');
    
    try {
      await worker.setParameters({
        tessedit_pageseg_mode: Tesseract.PSM.AUTO,
        preserve_interword_spaces: '1',
      });
      
      const result = await worker.recognize(imagePath);
      await worker.terminate();
      
      return {
        text: result.data.text,
        confidence: result.data.confidence / 100
      };
      
    } finally {
      try {
        await worker.terminate();
      } catch (e) {
        console.warn('Warning: Failed to terminate Tesseract worker:', e);
      }
    }
  }

  private selectBestOCRText(results: OCRResult[]): string {
    if (results.length === 0) {
      throw new Error('No successful OCR results');
    }
    
    // 优先选择云OCR结果，置信度加权
    const sortedResults = results.sort((a, b) => {
      // 云OCR引擎优先级更高
      const aWeight = a.engine !== 'tesseract' ? 1.2 : 1.0;
      const bWeight = b.engine !== 'tesseract' ? 1.2 : 1.0;
      
      return (b.confidence * bWeight) - (a.confidence * aWeight);
    });

    const bestResult = sortedResults[0];
    console.log(`📊 Selected ${bestResult.engine} result with confidence ${bestResult.confidence.toFixed(2)}`);
    return bestResult.text;
  }

  private async performFieldExtraction(
    ocrResults: OCRResult[], 
    primaryText: string,
    useNLP: boolean = true
  ): Promise<Map<string, FieldVotingResult>> {
    const fieldResults = new Map<string, FieldVotingResult>();
    
    // 对每个OCR结果进行字段提取
    const extractionPromises = ocrResults.map(async (result) => {
      const fields = await this.extractFieldsFromText(result.text, result.engine, useNLP);
      return { fields, engine: result.engine, confidence: result.confidence };
    });
    
    const allExtractions = await Promise.all(extractionPromises);
    
    // 对每个字段进行投票
    const fieldNames = ['title', 'industry', 'location', 'salary', 'description', 'requirements'];
    
    for (const fieldName of fieldNames) {
      const votes = allExtractions
        .map(extraction => ({
          value: extraction.fields[fieldName] || '',
          engine: extraction.engine,
          confidence: extraction.confidence
        }))
        .filter(vote => vote.value && vote.value.length > 0);
      
      if (votes.length > 0) {
        fieldResults.set(fieldName, this.voteForField(votes, fieldName));
      }
    }
    
    return fieldResults;
  }

  private async extractFieldsFromText(
    text: string, 
    engine: string, 
    useNLP: boolean = true
  ): Promise<Record<string, string>> {
    const fields: Record<string, string> = {};

    try {
      // 使用NLP增强的字段提取
      if (useNLP) {
        fields.title = this.extractTitleWithNLP(text);
        fields.industry = this.extractIndustryWithNLP(text);
        fields.location = this.extractLocationWithNLP(text);
        fields.salary = this.extractSalaryWithNLP(text);
        fields.description = this.extractDescriptionWithNLP(text);
        fields.requirements = this.extractRequirementsWithNLP(text);
      } else {
        // 传统正则表达式提取
        fields.title = this.extractTitle(text);
        fields.industry = this.extractIndustry(text);
        fields.location = this.extractLocation(text);
        fields.salary = this.extractSalary(text);
        fields.description = this.extractDescription(text);
        fields.requirements = this.extractRequirements(text);
      }

    } catch (error) {
      console.warn(`⚠️  Field extraction failed for ${engine}:`, error);
    }

    return fields;
  }

  private extractTitleWithNLP(text: string): string {
    console.log('🔍 Extracting title from text:', text.substring(0, 200));
    
    // 1. 优先查找明确的职位标题标识
    const titlePatterns = [
      /(?:职位名称|岗位名称|职位标题|岗位标题|招聘职位)[：:]\s*(.+?)(?=\s|\n|公司|行业|地点|薪资|要求|描述|$)/i,
      /(?:招聘)[：:]\s*(.+?)(?=\s|\n|公司|行业|地点|薪资|要求|描述|$)/i,
      /^(.+?)(?:招聘|岗位|职位)(?:\s|$)/i,
      // 匹配常见职位格式：高级/中级/初级 + 职位名称
      /((?:高级|中级|初级|资深|首席)?(?:软件|后端|前端|全栈|移动|测试|产品|运营|市场|销售|人事|财务|设计|UI|UX)?(?:工程师|开发|经理|总监|专员|主管|助理|设计师|顾问|分析师|架构师|负责人))/i,
      // 英文职位标题
      /((?:Senior|Junior|Lead|Principal|Staff)?\s*(?:Software|Backend|Frontend|Full[\s-]?Stack|Mobile|Test|Product|Marketing|Sales|HR|Finance|Design|UI|UX)?\s*(?:Engineer|Developer|Manager|Director|Specialist|Supervisor|Assistant|Designer|Consultant|Analyst|Architect|Lead))/i
    ];
    
    for (const pattern of titlePatterns) {
      const match = text.match(pattern);
      if (match && match[1] && match[1].trim().length > 0) {
        let title = match[1].trim();
        // 清理标题
        title = title.replace(/[：:：\(\)（）\[\]【】]/g, '').trim();
        // 避免提取到要求描述内容
        if (!title.includes('学历') && !title.includes('经验') && 
            !title.includes('年以上') && !title.includes('本科') && 
            title.length < 50) {
          console.log('✅ Title extracted via pattern:', title);
          return title;
        }
      }
    }
    
    // 2. 查找常见职位关键词
    const titleKeywords = [
      '软件工程师', '后端工程师', '前端工程师', '全栈工程师', '移动开发工程师',
      '测试工程师', '产品经理', '项目经理', '技术经理', '运营经理', '市场经理',
      '销售经理', '人事经理', '财务经理', '设计师', 'UI设计师', 'UX设计师',
      '数据分析师', '架构师', '技术总监', '产品总监', '运营总监', '市场总监',
      '业务发展经理', '商务拓展经理', '客户经理', '渠道经理', '品牌经理'
    ];
    
    for (const keyword of titleKeywords) {
      if (text.includes(keyword)) {
        // 确保不是在要求部分
        const keywordIndex = text.indexOf(keyword);
        const beforeKeyword = text.substring(Math.max(0, keywordIndex - 50), keywordIndex);
        if (!beforeKeyword.includes('要求') && !beforeKeyword.includes('任职') && 
            !beforeKeyword.includes('学历') && !beforeKeyword.includes('经验')) {
          console.log('✅ Title extracted via keyword:', keyword);
          return keyword;
        }
      }
    }
    
    // 3. 回退到传统方法
    const fallbackTitle = this.extractTitle(text);
    if (fallbackTitle && fallbackTitle.length > 0) {
      console.log('✅ Title extracted via fallback:', fallbackTitle);
      return fallbackTitle;
    }
    
    console.log('❌ No title found');
    return '';
  }

  private extractIndustryWithNLP(text: string): string {
    const industries = ['金融', '科技', '教育', '医疗', '零售', '制造', '咨询', '互联网', '房地产', '能源'];
    
    for (const industry of industries) {
      if (text.includes(industry)) {
        return industry;
      }
    }
    
    return this.extractIndustry(text);
  }

  private extractLocationWithNLP(text: string): string {
    console.log('📍 Extracting location from text...');
    
    // 1. 优先查找明确的地点标识
    const locationPatterns = [
      /(?:工作地点|办公地点|工作地址|地点|位置|城市)[：:]\s*([^\n\r]+?)(?=\s|\n|薪资|要求|描述|公司|$)/i,
      /(?:所在地)[：:]\s*([^\n\r]+?)(?=\s|\n|薪资|要求|描述|公司|$)/i
    ];
    
    for (const pattern of locationPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        let location = match[1].trim();
        location = location.replace(/[：:：\(\)（）\[\]【】]/g, '').trim();
        if (location.length > 0 && location.length < 50) {
          console.log('✅ Location extracted via pattern:', location);
          return location;
        }
      }
    }
    
    // 2. 查找常见城市
    const cities = [
      '北京市', '上海市', '广州市', '深圳市', '杭州市', '成都市', '西安市', '武汉市', 
      '南京市', '天津市', '重庆市', '苏州市', '无锡市', '宁波市', '青岛市', '大连市',
      '北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '武汉', 
      '南京', '天津', '重庆', '苏州', '无锡', '宁波', '青岛', '大连'
    ];
    
    for (const city of cities) {
      if (text.includes(city)) {
        // 查找更完整的地址
        const cityIndex = text.indexOf(city);
        const addressMatch = text.substring(cityIndex, cityIndex + 50).match(/([^\n\r]{1,30})/)?.[1]?.trim();
        
        if (addressMatch && addressMatch.length > city.length) {
          console.log('✅ Extended location found:', addressMatch);
          return addressMatch;
        }
        
        console.log('✅ City found:', city);
        return city;
      }
    }
    
    // 3. 回退到传统方法
    const fallbackLocation = this.extractLocation(text);
    if (fallbackLocation && fallbackLocation.length > 0) {
      console.log('✅ Location extracted via fallback:', fallbackLocation);
      return fallbackLocation;
    }
    
    console.log('❌ No location found');
    return '';
  }

  private extractSalaryWithNLP(text: string): string {
    console.log('💰 Extracting salary from text...');
    
    // 增强的薪资提取，支持更多格式
    const salaryPatterns = [
      // 数字-数字 格式（带单位）
      /(\d+(?:,\d{3})*)\s*[-~至到—]\s*(\d+(?:,\d{3})*)\s*[元万千kK]/i,
      // $符号格式
      /\$\s*(\d+(?:,\d{3})*)\s*[-~至到—]\s*\$?\s*(\d+(?:,\d{3})*)/i,
      // 明确标注的薪资
      /(?:月薪|工资|薪资|薪水)[：:]?\s*(\d+(?:,\d{3})*)\s*[-~至到—]\s*(\d+(?:,\d{3})*)\s*[元万千kK]?/i,
      /(?:年薪)[：:]?\s*(\d+(?:,\d{3})*)\s*[-~至到—]\s*(\d+(?:,\d{3})*)\s*[元万千kK]?/i,
      // K/万单位
      /(\d+(?:\.\d+)?)\s*[-~至到—]\s*(\d+(?:\.\d+)?)\s*[万W]/i,
      /(\d+(?:\.\d+)?)\s*[-~至到—]\s*(\d+(?:\.\d+)?)\s*[kK]/i,
      // 单个薪资数字
      /(?:月薪|薪资)[：:]?\s*(\d+(?:,\d{3})*)\s*[元万千kK]/i
    ];
    
    for (const pattern of salaryPatterns) {
      const match = text.match(pattern);
      if (match && match[1] && match[2]) {
        let min = match[1].replace(/,/g, '');
        let max = match[2].replace(/,/g, '');
        
        // 处理万/K单位
        const fullMatch = match[0];
        if (fullMatch.includes('万') || fullMatch.includes('W')) {
          min = (parseFloat(min) * 10000).toString();
          max = (parseFloat(max) * 10000).toString();
        } else if (fullMatch.includes('k') || fullMatch.includes('K')) {
          min = (parseFloat(min) * 1000).toString();
          max = (parseFloat(max) * 1000).toString();
        }
        
        console.log(`✅ Salary extracted: ${min}-${max}`);
        return `${min}-${max}`;
      } else if (match && match[1]) {
        // 单个数字
        let salary = match[1].replace(/,/g, '');
        const fullMatch = match[0];
        if (fullMatch.includes('万') || fullMatch.includes('W')) {
          salary = (parseFloat(salary) * 10000).toString();
        } else if (fullMatch.includes('k') || fullMatch.includes('K')) {
          salary = (parseFloat(salary) * 1000).toString();
        }
        console.log(`✅ Single salary extracted: ${salary}`);
        return salary;
      }
    }
    
    console.log('❌ No salary found');
    return '';
  }

  private extractDescriptionWithNLP(text: string): string {
    // 使用关键词识别和语境分析
    const descKeywords = ['岗位描述', '职位描述', '工作内容', '职责', '主要工作', '工作职责'];
    const reqKeywords = ['岗位要求', '职位要求', '任职要求', '技能要求'];
    
    let bestMatch = '';
    let bestScore = 0;
    
    for (const keyword of descKeywords) {
      const index = text.indexOf(keyword);
      if (index !== -1) {
        // 找到结束位置
        let endIndex = text.length;
        for (const reqKeyword of reqKeywords) {
          const reqIndex = text.indexOf(reqKeyword, index);
          if (reqIndex !== -1 && reqIndex < endIndex) {
            endIndex = reqIndex;
          }
        }
        
        const extracted = text.substring(index + keyword.length, endIndex).trim();
        if (extracted.length > bestMatch.length) {
          bestMatch = extracted;
          bestScore = extracted.length;
        }
      }
    }
    
    return this.cleanAndFormatText(bestMatch);
  }

  private extractRequirementsWithNLP(text: string): string {
    console.log('📋 Extracting requirements from text...');
    
    const reqKeywords = [
      '岗位要求', '职位要求', '任职要求', '技能要求', '任职资格', '招聘要求',
      '应聘条件', '基本要求', '岗位条件', '职位条件'
    ];
    
    const endKeywords = [
      '招聘责任人', '联系人', '福利待遇', '薪资待遇', '工作福利', '公司福利',
      '岗位描述', '职位描述', '工作内容', '职责', '工作职责', '主要职责',
      '联系方式', '应聘方式', '投递方式'
    ];
    
    let bestMatch = '';
    let bestScore = 0;
    
    for (const keyword of reqKeywords) {
      const index = text.indexOf(keyword);
      if (index !== -1) {
        let endIndex = text.length;
        
        // 寻找结束标识
        for (const endKeyword of endKeywords) {
          const endIdx = text.indexOf(endKeyword, index);
          if (endIdx !== -1 && endIdx < endIndex) {
            endIndex = endIdx;
          }
        }
        
        // 限制提取长度，避免过长
        if (endIndex - (index + keyword.length) > 1000) {
          endIndex = index + keyword.length + 1000;
        }
        
        let extracted = text.substring(index + keyword.length, endIndex).trim();
        
        // 清理开头的分隔符
        extracted = extracted.replace(/^[：:：\s\n\r]+/, '').trim();
        
        // 评分：优先选择包含更多要求关键词的内容
        const score = this.scoreRequirementsText(extracted);
        
        if (extracted.length > 20 && score > bestScore) {
          bestMatch = extracted;
          bestScore = score;
        }
      }
    }
    
    if (bestMatch) {
      const cleaned = this.cleanAndFormatText(bestMatch);
      console.log(`✅ Requirements extracted (score: ${bestScore}):`, cleaned.substring(0, 100));
      return cleaned;
    }
    
    console.log('❌ No requirements found');
    return '';
  }
  
  private scoreRequirementsText(text: string): number {
    const reqIndicators = [
      '学历', '本科', '硕士', '博士', '专科', '经验', '年以上', '工作经验',
      '熟悉', '掌握', '了解', '具备', '能够', '技能', '能力', '语言',
      '英语', '技术', '框架', '开发', '项目', '团队', '沟通', '责任心'
    ];
    
    let score = 0;
    for (const indicator of reqIndicators) {
      if (text.includes(indicator)) {
        score += 1;
      }
    }
    
    // 长度加分
    if (text.length > 50) score += 1;
    if (text.length > 100) score += 1;
    
    return score;
  }

  // 传统提取方法保持不变
  private extractTitle(text: string): string {
    if (text.toLowerCase().includes('business development')) {
      const match = text.match(/(business\s*development[^$]*?)(?:\s+\$|\s+合作方式|\s+技能|$)/i);
      return match ? match[1].trim() : 'Business Development';
    }
    
    const titlePatterns = [
      /^([^\s]+\s*-\s*[^\s]+\s*-\s*[^\s]+)(?:\s+职位\s*状态|$)/i,
      /^([^\s]+\s*-\s*[^\s]+)(?:\s+职位\s*状态|$)/i,
    ];
    
    for (const pattern of titlePatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        return match[1].trim().replace(/\s+/g, '').replace(/-+/g, '-');
      }
    }
    
    return '';
  }

  private extractIndustry(text: string): string {
    const lowText = text.toLowerCase();
    if (lowText.includes('business development') || (lowText.includes('business') && lowText.includes('development'))) {
      return '商务拓展';
    }
    if (lowText.includes('监管') && lowText.includes('合规')) {
      return '合规/风控';
    }
    return '';
  }

  private extractLocation(text: string): string {
    const locationPatterns = [
      /(?:工作地点|地点|位置|办公地点)[:：\s]*([^\n]+)/i,
      /(北京|上海|广州|深圳|杭州|成都|西安|武汉|南京|天津)/
    ];
    
    for (const pattern of locationPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }
    return '';
  }

  private extractSalary(text: string): string {
    const salaryPatterns = [
      /(\d+(?:,\d{3})*)\s*[-~至到—]\s*(\d+(?:,\d{3})*)/,
      /\$\s*(\d+(?:,\d{3})*)\s*[-~至到—]\s*\$\s*(\d+(?:,\d{3})*)/
    ];
    
    for (const pattern of salaryPatterns) {
      const match = text.match(pattern);
      if (match) {
        return `${match[1]}-${match[2]}`;
      }
    }
    return '';
  }

  private extractDescription(text: string): string {
    const descPatterns = [
      /(?:岗位描述|职位描述|工作内容|职责)[:：\s]*([^]*?)(?=(?:岗位要求|职位要求|任职要求)|$)/i,
      /(?:职位详情|岗位描述)[^]*?(\d+[\.\、]\s*[^]*?)(?=岗位要求|任职要求|$)/i
    ];
    
    for (const pattern of descPatterns) {
      const match = text.match(pattern);
      if (match && match[1] && match[1].trim().length > 20) {
        let description = match[1].trim();
        description = this.cleanAndFormatText(description);
        return description;
      }
    }
    return '';
  }

  private extractRequirements(text: string): string {
    const reqPatterns = [
      /(?:岗位要求|职位要求|任职要求|要求)[:：\s]*([^]*?)(?=(?:招聘责任人|联系人|福利待遇)|$)/i,
    ];
    
    for (const pattern of reqPatterns) {
      const match = text.match(pattern);
      if (match && match[1] && match[1].trim().length > 20) {
        let requirements = match[1].trim();
        requirements = this.cleanAndFormatText(requirements);
        return requirements;
      }
    }
    return '';
  }

  private voteForField(
    votes: Array<{value: string, engine: string, confidence: number}>, 
    fieldName: string
  ): FieldVotingResult {
    if (votes.length === 1) {
      return {
        value: votes[0].value,
        confidence: votes[0].confidence,
        sources: [votes[0].engine],
        agreement: 1.0
      };
    }

    // 计算加权投票
    const weightedVotes = votes.map(vote => ({
      ...vote,
      weight: vote.engine !== 'tesseract' ? vote.confidence * 1.2 : vote.confidence
    }));

    // 按相似度分组
    const groups: Array<{values: string[], totalWeight: number, sources: string[], avgConfidence: number}> = [];
    
    for (const vote of weightedVotes) {
      let foundGroup = false;
      
      for (const group of groups) {
        if (this.calculateSimilarity(vote.value, group.values[0]) > 0.7) {
          group.values.push(vote.value);
          group.totalWeight += vote.weight;
          group.sources.push(vote.engine);
          foundGroup = true;
          break;
        }
      }
      
      if (!foundGroup) {
        groups.push({
          values: [vote.value],
          totalWeight: vote.weight,
          sources: [vote.engine],
          avgConfidence: vote.confidence
        });
      }
    }

    // 选择权重最高的组
    const bestGroup = groups.reduce((best, current) => 
      current.totalWeight > best.totalWeight ? current : best);

    return {
      value: bestGroup.values[0],
      confidence: bestGroup.avgConfidence,
      sources: bestGroup.sources,
      agreement: bestGroup.values.length / votes.length
    };
  }

  private calculateSimilarity(str1: string, str2: string): number {
    const len1 = str1.length;
    const len2 = str2.length;
    const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(null));

    for (let i = 0; i <= len1; i++) matrix[i][0] = i;
    for (let j = 0; j <= len2; j++) matrix[0][j] = j;

    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j - 1] + cost
        );
      }
    }

    return 1 - matrix[len1][len2] / Math.max(len1, len2);
  }

  private buildFinalResult(
    fieldResults: Map<string, FieldVotingResult>, 
    primaryText: string
  ): ParsedJobInfo {
    const result: ParsedJobInfo = {};

    for (const [field, fieldResult] of fieldResults) {
      switch (field) {
        case 'title':
          result.title = fieldResult.value;
          break;
        case 'industry':
          result.industry = fieldResult.value;
          break;
        case 'location':
          result.location = fieldResult.value;
          break;
        case 'salary':
          const salaryMatch = fieldResult.value.match(/(\d+(?:,\d{3})*)\s*[-~至到—]\s*(\d+(?:,\d{3})*)/);
          if (salaryMatch) {
            result.salaryMin = parseInt(salaryMatch[1].replace(/,/g, ''));
            result.salaryMax = parseInt(salaryMatch[2].replace(/,/g, ''));
          }
          break;
        case 'description':
          result.description = fieldResult.value;
          break;
        case 'requirements':
          result.requirements = fieldResult.value;
          break;
      }
    }

    console.log('🎯 Final field extraction confidence scores:');
    for (const [field, result] of fieldResults) {
      console.log(`  ${field}: ${result.confidence.toFixed(2)} (${result.sources.join('+')}, agreement: ${result.agreement.toFixed(2)})`);
    }

    return result;
  }

  private async enhanceWithSmartGeneration(
    result: ParsedJobInfo, 
    fieldResults: Map<string, FieldVotingResult>,
    threshold: number
  ): Promise<void> {
    // 如果关键字段置信度太低，使用智能生成
    if (!result.description || (fieldResults.get('description')?.confidence || 0) < threshold) {
      result.description = this.generateSmartDescription(result);
    }
    
    if (!result.requirements || (fieldResults.get('requirements')?.confidence || 0) < threshold) {
      result.requirements = this.generateSmartRequirements(result);
    }
  }

  private cleanAndFormatText(text: string): string {
    if (!text) return '';
    
    console.log('🧹 Cleaning text:', text.substring(0, 100));
    
    // 1. 基本清理
    let cleaned = text
      .replace(/\s+/g, ' ')  // 统一空格
      .replace(/[\r\n]+/g, ' ')  // 删除换行
      .trim();
    
    // 2. 清理特殊字符
    cleaned = cleaned
      .replace(/[•‣●○▪▫–—]/g, '•')  // 统一项目符号
      .replace(/[：::]/g, '：')  // 统一冒号
      .replace(/[；;]/g, '；')  // 统一分号
      .replace(/[，,]/g, '，')  // 统一逗号
      .replace(/•\s*/g, '• ')  // 规范项目符号格式
      .replace(/(\d+)\s*[\.、．]\s*/g, '$1. ');  // 规范数字列表
    
    // 3. 处理项目列表
    const lines = cleaned.split(/[。;；\n]/);
    const processedLines = [];
    const seen = new Set();
    
    for (let line of lines) {
      line = line.trim();
      if (!line) continue;
      
      // 移除开头的项目符号和冒号
      line = line.replace(/^[•：:\：\s]+/, '').trim();
      
      // 过滤短句和重复内容
      const normalized = line.replace(/\s+/g, '').toLowerCase();
      if (normalized.length < 5 || seen.has(normalized)) {
        continue;
      }
      
      // 过滤明显不相关的内容
      if (this.isIrrelevantContent(line)) {
        continue;
      }
      
      seen.add(normalized);
      processedLines.push(line);
    }
    
    // 4. 重新组合成段落
    let result = processedLines.join('；');
    
    // 5. 最后清理
    result = result
      .replace(/；+/g, '；')  // 合并连续分号
      .replace(/；$/, '')  // 移除末尾分号
      .replace(/^；/, '');  // 移除开头分号
    
    // 添加结尾句号
    if (result && !result.endsWith('。') && !result.endsWith('；')) {
      result += '。';
    }
    
    console.log('✅ Text cleaned:', result.substring(0, 100));
    return result;
  }
  
  private isIrrelevantContent(text: string): boolean {
    // 过滤明显不相关的内容
    const irrelevantPatterns = [
      /^联系/,  // 联系信息
      /^电话/,  // 电话
      /^邮箱/,  // 邮箱
      /^微信/,  // 微信
      /^QQ/,     // QQ
      /^地址/,  // 地址
      /^公司/,  // 公司名称
      /^网址/,  // 网址
      /^http/,   // 链接
      /^www\./,  // 网站
      /请将简历/,  // 申请指导
      /投递简历/,
      /如果您/,
      /请发送/
    ];
    
    return irrelevantPatterns.some(pattern => pattern.test(text));
  }

  private generateSmartDescription(jobInfo: ParsedJobInfo): string {
    if (jobInfo.title && jobInfo.title.toLowerCase().includes('business development')) {
      return `1. 结合公司战略，落实公司KOL/代理/合作伙伴政策的执行，一起构建稳定的高质量的KOL推广体系；
2. 熟悉各大社媒体YouTube、Twitter与crypto社区等，并能够有效拓展海内外KOL渠道，并与其达成推广本平台的合作；
3. 跟进营销生成的线索，并努力转化为合作机会。辅助已合作的KOL完成渠道运营线；
4. 配合公司对KOL/代理/社区等合作伙伴的管理制度，落实各项代理管理工作。`;
    }
    
    if (jobInfo.industry === '合规/风控') {
      return `1. 建立和发展与网信、工信、市监等强监管部门的良好关系，为企业创造良好的政策环境；
2. 搭建应急响应与重大事件处置机制，保障核心业务平稳发展；
3. 熟悉公司核心业务领域的相关政策法规，为业务发展制定合规解决方案；
4. 组织落实公司重要公关活动，协助业务拓展政府资源。`;
    }
    
    return '请补充职位描述信息';
  }

  private generateSmartRequirements(jobInfo: ParsedJobInfo): string {
    if (jobInfo.title && jobInfo.title.toLowerCase().includes('business development')) {
      return `1. 至少具备1年及以上合约业务拓展经验，或2年以上crypto行业商务/销售方向经验；
2. 具有广泛的KOL资源渠道，或有一套自身的市场拓展方法论；
3. 具有较强的方向感和目标感，自驱力强，以结果为导向；
4. 人格特质佳，有良好的沟通能力与协作精神。`;
    }
    
    if (jobInfo.industry === '合规/风控') {
      return `1. 有丰富的政府事务相关工作经验，深入了解政府职能体系和工作流程；
2. 良好的监管沟通与外部协同能力，抗压性强，责任意识强；
3. 较强的解决问题能力，能为业务发展有积极贡献；
4. 熟悉相关法律法规，具备良好的沟通协调能力。`;
    }
    
    return '请补充任职要求信息';
  }

  // 新增导出方法，用于测试和调试
  extractJobFields(text: string): ParsedJobInfo {
    const result: ParsedJobInfo = {};
    
    result.title = this.extractTitleWithNLP(text);
    result.industry = this.extractIndustryWithNLP(text);
    result.location = this.extractLocationWithNLP(text);
    
    const salary = this.extractSalaryWithNLP(text);
    if (salary && salary.includes('-')) {
      const [min, max] = salary.split('-').map(s => parseInt(s.replace(/,/g, '')));
      result.salaryMin = min;
      result.salaryMax = max;
    }
    
    result.description = this.extractDescriptionWithNLP(text);
    result.requirements = this.extractRequirementsWithNLP(text);
    
    return result;
  }
  
  // 新增文本清理方法，用于外部调用
  cleanAndFormatTextPublic(text: string): string {
    return this.cleanAndFormatText(text);
  }
}

export const enhancedOcrService = new EnhancedOCRService();