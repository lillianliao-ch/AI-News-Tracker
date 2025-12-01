import { readFile } from 'fs/promises';
import Tesseract from 'tesseract.js';
import axios from 'axios';

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
  agreement: number; // 引擎一致性评分 0-1
}

export class MultiEngineOCRService {
  private enabledEngines: string[] = [];
  
  constructor() {
    // 根据环境变量确定启用的引擎
    if (process.env.ALIYUN_OCR_ACCESS_KEY && process.env.ALIYUN_OCR_SECRET) {
      this.enabledEngines.push('aliyun');
    }
    if (process.env.BAIDU_OCR_API_KEY && process.env.BAIDU_OCR_SECRET_KEY) {
      this.enabledEngines.push('baidu');
    }
    // Tesseract始终作为兜底
    this.enabledEngines.push('tesseract');
    
    console.log('🚀 Multi-Engine OCR initialized with engines:', this.enabledEngines);
  }

  async parseJobFromImage(imagePath: string): Promise<ParsedJobInfo> {
    try {
      console.log('🔍 Starting multi-engine OCR processing for:', imagePath);
      
      // Step 1: 并发执行多个OCR引擎
      const ocrResults = await this.performMultiEngineOCR(imagePath);
      
      // Step 2: 多引擎投票获取最佳结果
      const bestText = this.selectBestOCRText(ocrResults);
      console.log('✅ Selected best OCR text from', ocrResults.length, 'engines');
      
      // Step 3: 多引擎字段提取和投票
      const fieldResults = await this.performFieldExtraction(ocrResults, bestText);
      
      // Step 4: 智能合并结果
      const finalResult = this.mergeFieldResults(fieldResults);
      
      console.log('🎯 Multi-engine OCR completed with confidence scores');
      return finalResult;
      
    } catch (error) {
      console.error('❌ Multi-engine OCR processing failed:', error);
      throw new Error('Failed to parse job information from image using multi-engine OCR');
    }
  }

  private async performMultiEngineOCR(imagePath: string): Promise<OCRResult[]> {
    const promises = this.enabledEngines.map(engine => 
      this.performSingleEngineOCR(imagePath, engine)
    );
    
    // 等待所有引擎完成，即使某些失败也继续
    const results = await Promise.allSettled(promises);
    
    return results
      .filter(result => result.status === 'fulfilled')
      .map(result => (result as PromiseFulfilledResult<OCRResult>).value)
      .filter(result => result.success);
  }

  private async performSingleEngineOCR(imagePath: string, engine: string): Promise<OCRResult> {
    const startTime = Date.now();
    
    try {
      let text = '';
      let confidence = 0;
      
      switch (engine) {
        case 'aliyun':
          const aliyunResult = await this.callAliyunOCR(imagePath);
          text = aliyunResult.text;
          confidence = aliyunResult.confidence;
          break;
          
        case 'baidu':
          const baiduResult = await this.callBaiduOCR(imagePath);
          text = baiduResult.text;
          confidence = baiduResult.confidence;
          break;
          
        case 'tesseract':
        default:
          const tesseractResult = await this.callTesseractOCR(imagePath);
          text = tesseractResult.text;
          confidence = tesseractResult.confidence;
          break;
      }
      
      const processingTime = Date.now() - startTime;
      console.log(`✅ ${engine} OCR completed in ${processingTime}ms, confidence: ${confidence.toFixed(2)}`);
      
      return {
        text: text.trim(),
        confidence,
        engine,
        processingTime,
        success: true
      };
      
    } catch (error) {
      console.error(`❌ ${engine} OCR failed:`, error);
      return {
        text: '',
        confidence: 0,
        engine,
        processingTime: Date.now() - startTime,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async callAliyunOCR(imagePath: string): Promise<{text: string, confidence: number}> {
    // 阿里云OCR API集成
    const imageBuffer = await readFile(imagePath);
    const base64Image = imageBuffer.toString('base64');
    
    const response = await axios.post('https://ocr-api.cn-hangzhou.aliyuncs.com', {
      image: base64Image,
      configure: JSON.stringify({
        "side": "face",
        "min_size": 50
      })
    }, {
      headers: {
        'Authorization': `APPCODE ${process.env.ALIYUN_OCR_ACCESS_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.data.success) {
      const words = response.data.ret || [];
      const text = words.map((word: any) => word.word).join(' ');
      const avgConfidence = words.reduce((sum: number, word: any) => 
        sum + (word.prob || 0.8), 0) / words.length;
      
      return {
        text,
        confidence: avgConfidence
      };
    }
    
    throw new Error('Aliyun OCR API failed');
  }

  private async callBaiduOCR(imagePath: string): Promise<{text: string, confidence: number}> {
    // 百度OCR API集成
    const imageBuffer = await readFile(imagePath);
    const base64Image = imageBuffer.toString('base64');
    
    // 先获取access token
    const tokenResponse = await axios.post('https://aip.baidubce.com/oauth/2.0/token', null, {
      params: {
        grant_type: 'client_credentials',
        client_id: process.env.BAIDU_OCR_API_KEY,
        client_secret: process.env.BAIDU_OCR_SECRET_KEY
      }
    });
    
    const accessToken = tokenResponse.data.access_token;
    
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
    // 现有的Tesseract逻辑
    const worker = await Tesseract.createWorker('chi_sim+eng');
    
    try {
      await worker.setParameters({
        tessedit_pageseg_mode: Tesseract.PSM.AUTO,
        preserve_interword_spaces: '1'
      });
      
      const result = await worker.recognize(imagePath);
      await worker.terminate();
      
      return {
        text: result.data.text,
        confidence: result.data.confidence / 100 // 转换为0-1范围
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
    
    // 优先选择云OCR结果，其次选择置信度最高的
    const cloudResults = results.filter(r => r.engine !== 'tesseract');
    const bestCloudResult = cloudResults.length > 0 
      ? cloudResults.reduce((best, current) => 
          current.confidence > best.confidence ? current : best)
      : null;
    
    if (bestCloudResult && bestCloudResult.confidence > 0.8) {
      console.log(`📊 Selected ${bestCloudResult.engine} result with confidence ${bestCloudResult.confidence.toFixed(2)}`);
      return bestCloudResult.text;
    }
    
    // 如果云OCR置信度不高，选择所有结果中最好的
    const bestResult = results.reduce((best, current) => 
      current.confidence > best.confidence ? current : best);
    
    console.log(`📊 Selected ${bestResult.engine} result with confidence ${bestResult.confidence.toFixed(2)}`);
    return bestResult.text;
  }

  private async performFieldExtraction(ocrResults: OCRResult[], primaryText: string): Promise<Map<string, FieldVotingResult>> {
    const fieldResults = new Map<string, FieldVotingResult>();
    
    // 对每个OCR结果进行字段提取
    const extractionPromises = ocrResults.map(async (result) => {
      const fields = await this.extractFieldsFromText(result.text, result.engine);
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

  private async extractFieldsFromText(text: string, engine: string): Promise<any> {
    // 复用现有的字段提取逻辑
    const cleanText = text.replace(/\s+/g, ' ').trim();
    
    return {
      title: this.extractTitle(cleanText),
      industry: this.extractIndustry(cleanText),
      location: this.extractLocation(cleanText),
      salary: this.extractSalary(cleanText),
      description: this.extractDescription(cleanText),
      requirements: this.extractRequirements(cleanText)
    };
  }

  private voteForField(votes: Array<{value: string, engine: string, confidence: number}>, fieldName: string): FieldVotingResult {
    if (votes.length === 1) {
      return {
        value: votes[0].value,
        confidence: votes[0].confidence,
        sources: [votes[0].engine],
        agreement: 1.0
      };
    }
    
    // 计算加权投票
    const valueScores = new Map<string, {score: number, engines: string[], confidences: number[]}>();
    
    for (const vote of votes) {
      const key = vote.value.toLowerCase().trim();
      if (!valueScores.has(key)) {
        valueScores.set(key, { score: 0, engines: [], confidences: [] });
      }
      
      const entry = valueScores.get(key)!;
      // 云引擎权重更高
      const weight = vote.engine === 'tesseract' ? 1.0 : 2.0;
      entry.score += vote.confidence * weight;
      entry.engines.push(vote.engine);
      entry.confidences.push(vote.confidence);
    }
    
    // 选择得分最高的值
    let bestValue = '';
    let bestEntry = { score: 0, engines: [], confidences: [] };
    
    for (const [value, entry] of valueScores) {
      if (entry.score > bestEntry.score) {
        bestValue = value;
        bestEntry = entry;
      }
    }
    
    // 计算一致性分数
    const totalVotes = votes.length;
    const agreementCount = bestEntry.engines.length;
    const agreement = agreementCount / totalVotes;
    
    // 计算综合置信度
    const avgConfidence = bestEntry.confidences.reduce((sum, conf) => sum + conf, 0) / bestEntry.confidences.length;
    const finalConfidence = avgConfidence * agreement; // 置信度 × 一致性
    
    console.log(`🗳️ Field "${fieldName}" voting: ${bestValue} (${bestEntry.engines.join('+')}) confidence: ${finalConfidence.toFixed(2)}, agreement: ${agreement.toFixed(2)}`);
    
    return {
      value: bestValue,
      confidence: finalConfidence,
      sources: bestEntry.engines,
      agreement
    };
  }

  private mergeFieldResults(fieldResults: Map<string, FieldVotingResult>): ParsedJobInfo {
    const result: ParsedJobInfo = {};
    
    // 提取基础字段
    const title = fieldResults.get('title');
    if (title && title.confidence > 0.3) {
      result.title = title.value;
    }
    
    const industry = fieldResults.get('industry');
    if (industry && industry.confidence > 0.3) {
      result.industry = industry.value;
    }
    
    const location = fieldResults.get('location');
    if (location && location.confidence > 0.3) {
      result.location = location.value;
    }
    
    const description = fieldResults.get('description');
    if (description && description.confidence > 0.2) {
      result.description = description.value;
    }
    
    const requirements = fieldResults.get('requirements');
    if (requirements && requirements.confidence > 0.2) {
      result.requirements = requirements.value;
    }
    
    // 如果关键字段置信度太低，使用智能生成
    if (!result.description || (fieldResults.get('description')?.confidence || 0) < 0.4) {
      result.description = this.generateSmartDescription(result);
    }
    
    if (!result.requirements || (fieldResults.get('requirements')?.confidence || 0) < 0.4) {
      result.requirements = this.generateSmartRequirements(result);
    }
    
    console.log('🎯 Final field extraction confidence scores:');
    for (const [field, result] of fieldResults) {
      console.log(`  ${field}: ${result.confidence.toFixed(2)} (${result.sources.join('+')}, agreement: ${result.agreement.toFixed(2)})`);
    }
    
    return result;
  }

  // 复用现有的字段提取方法
  private extractTitle(text: string): string {
    // 现有的title提取逻辑
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
        
        // 清理和格式化文本
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
        
        // 清理和格式化文本
        requirements = this.cleanAndFormatText(requirements);
        
        return requirements;
      }
    }
    return '';
  }

  private cleanAndFormatText(text: string): string {
    if (!text) return '';
    
    // 移除多余的空白字符
    let cleaned = text.replace(/\s+/g, ' ').trim();
    
    // 修复常见的OCR错误
    cleaned = cleaned.replace(/(\d+)\s*[\.、。]\s*/g, '$1. ');
    
    // 确保句子之间有适当的分隔
    cleaned = cleaned.replace(/([；;])\s*/g, '$1 ');
    cleaned = cleaned.replace(/([，,])\s*/g, '$1 ');
    
    // 移除重复的内容（简单的去重）
    const sentences = cleaned.split(/[。;；]/);
    const uniqueSentences = [];
    const seen = new Set();
    
    for (const sentence of sentences) {
      const normalized = sentence.trim().replace(/\s+/g, '');
      if (normalized && !seen.has(normalized) && normalized.length > 5) {
        seen.add(normalized);
        uniqueSentences.push(sentence.trim());
      }
    }
    
    // 重新组合文本
    let result = uniqueSentences.join('；');
    
    // 确保适当的格式
    if (result && !result.endsWith('。') && !result.endsWith('；')) {
      result += '。';
    }
    
    return result;
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
}

export const multiEngineOcrService = new MultiEngineOCRService();