import axios from 'axios';
import * as cheerio from 'cheerio';

interface JobInfo {
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

interface ParsedJobsResult {
  jobs: JobInfo[];
  totalFound: number;
  parseSuccess: number;
  errors: string[];
}

export class WebJobParserService {
  
  async parseJobsFromUrl(url: string): Promise<ParsedJobsResult> {
    console.log('🌐 Starting web job parsing for:', url);
    
    try {
      const response = await this.fetchWebContent(url);
      const jobs = await this.extractJobsFromContent(response, url);
      
      console.log(`✅ Successfully parsed ${jobs.length} jobs from URL`);
      
      return {
        jobs,
        totalFound: jobs.length,
        parseSuccess: jobs.length,
        errors: []
      };
    } catch (error) {
      console.error('❌ Web job parsing failed:', error);
      return {
        jobs: [],
        totalFound: 0,
        parseSuccess: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      };
    }
  }

  async parseJobsFromText(text: string): Promise<ParsedJobsResult> {
    console.log('📝 Starting text job parsing...');
    
    try {
      const jobs = await this.parseJobsWithAI(text);
      
      console.log(`✅ Successfully parsed ${jobs.length} jobs from text`);
      
      return {
        jobs,
        totalFound: jobs.length,
        parseSuccess: jobs.length,
        errors: []
      };
    } catch (error) {
      console.error('❌ Text job parsing failed:', error);
      return {
        jobs: [],
        totalFound: 0,
        parseSuccess: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      };
    }
  }

  private async fetchWebContent(url: string): Promise<string> {
    console.log('📥 Fetching web content...');
    
    const headers = {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
      'Accept-Encoding': 'gzip, deflate',
      'Cache-Control': 'no-cache'
    };

    try {
      const response = await axios.get(url, { 
        headers,
        timeout: 30000,
        maxRedirects: 5
      });
      return response.data;
    } catch (error) {
      // 对于某些特殊网址（如腾讯文档），可能需要特殊处理
      if (url.includes('docs.qq.com')) {
        throw new Error('腾讯文档需要特殊的API访问权限，建议复制内容到文本框进行解析');
      }
      throw error;
    }
  }

  private async extractJobsFromContent(htmlContent: string, sourceUrl: string): Promise<JobInfo[]> {
    console.log('🔍 Extracting job information from content...');
    
    const $ = cheerio.load(htmlContent);
    const jobs: JobInfo[] = [];

    // 通用文本内容提取
    const pageText = $('body').text();
    
    // 如果是结构化的职位列表
    const structuredJobs = this.parseStructuredJobs($);
    if (structuredJobs.length > 0) {
      jobs.push(...structuredJobs);
    } else {
      // 使用AI解析非结构化文本
      const aiParsedJobs = await this.parseJobsWithAI(pageText);
      jobs.push(...aiParsedJobs);
    }

    return jobs;
  }

  private parseStructuredJobs($: cheerio.CheerioAPI): JobInfo[] {
    const jobs: JobInfo[] = [];
    
    // 常见的招聘网站结构模式
    const jobSelectors = [
      '.job-item', '.position-item', '.job-list-item',
      '[data-job]', '.recruitment-item', '.vacancy'
    ];

    for (const selector of jobSelectors) {
      $(selector).each((_, element) => {
        const job = this.extractJobFromElement($, $(element));
        if (job.title) {
          jobs.push(job);
        }
      });
      
      if (jobs.length > 0) break; // 找到匹配的结构就停止
    }

    return jobs;
  }

  private extractJobFromElement($: cheerio.CheerioAPI, $element: cheerio.Cheerio<cheerio.Element>): JobInfo {
    const job: JobInfo = {};

    // 提取职位标题
    const titleSelectors = ['h1', 'h2', 'h3', '.title', '.job-title', '.position-name'];
    for (const sel of titleSelectors) {
      const title = $element.find(sel).first().text().trim();
      if (title) {
        job.title = title;
        break;
      }
    }

    // 提取位置信息
    const locationText = $element.text();
    const locationMatch = locationText.match(/(北京|上海|广州|深圳|杭州|成都|西安|武汉|南京|天津|重庆|苏州|无锡|厦门|青岛|大连|长沙|济南|哈尔滨|沈阳|合肥|郑州|南昌|太原|石家庄|呼和浩特|银川|西宁|兰州|乌鲁木齐|拉萨|海口|三亚|香港|澳门|台北)/);
    if (locationMatch) {
      job.location = locationMatch[1];
    }

    // 提取薪资信息
    const salaryMatch = $element.text().match(/(\d+(?:,\d{3})*)\s*[-~至到—]\s*(\d+(?:,\d{3})*)/);
    if (salaryMatch) {
      job.salaryMin = parseInt(salaryMatch[1].replace(/,/g, ''));
      job.salaryMax = parseInt(salaryMatch[2].replace(/,/g, ''));
    }

    return job;
  }

  private async parseJobsWithAI(text: string): Promise<JobInfo[]> {
    console.log('🤖 Using AI to parse job information...');
    
    // 清理和预处理文本
    const cleanText = this.preprocessText(text);
    
    // 智能识别职位信息
    const jobPatterns = this.identifyJobPatterns(cleanText);
    
    return jobPatterns;
  }

  private preprocessText(text: string): string {
    // 移除多余空白和特殊字符
    let cleaned = text.replace(/\s+/g, ' ').trim();
    
    // 移除页面导航、版权等无关信息
    const removePatterns = [
      /版权所有.*$/gm,
      /Copyright.*$/gm,
      /首页|导航|菜单|登录|注册/g,
      /\d{4}-\d{2}-\d{2}.*更新/g
    ];
    
    for (const pattern of removePatterns) {
      cleaned = cleaned.replace(pattern, '');
    }
    
    return cleaned;
  }

  private identifyJobPatterns(text: string): JobInfo[] {
    const jobs: JobInfo[] = [];
    
    // 按照常见分隔符分割可能的职位信息
    const sections = text.split(/(?:\n\s*\n|\d+[\.\、]\s*|\*\s*|【.*?】)/);
    
    for (const section of sections) {
      if (section.trim().length < 50) continue; // 跳过太短的片段
      
      const job = this.extractJobFromText(section.trim());
      if (job.title && job.title.length > 2) {
        jobs.push(job);
      }
    }

    return jobs;
  }

  private extractJobFromText(text: string): JobInfo {
    const job: JobInfo = {};

    // 提取职位标题 - 通常在开头
    const titlePatterns = [
      /^([^\n。；;]+?)(?:岗位|职位|招聘)/,
      /^([^\n。；;]{2,20})(?=.*(?:要求|职责|描述))/,
      /岗位名称[:：]\s*([^\n]+)/,
      /职位[:：]\s*([^\n]+)/
    ];

    for (const pattern of titlePatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        job.title = match[1].trim();
        break;
      }
    }

    // 提取工作地点
    const locationMatch = text.match(/(?:工作地点|地点|位置)[:：]\s*([^\n]+)/);
    if (locationMatch) {
      job.location = locationMatch[1].trim();
    } else {
      // 从文本中查找城市名
      const cityMatch = text.match(/(北京|上海|广州|深圳|杭州|成都|西安|武汉|南京|天津)/);
      if (cityMatch) {
        job.location = cityMatch[1];
      }
    }

    // 提取薪资范围
    const salaryMatch = text.match(/(\d+(?:,\d{3})*)\s*[-~至到—]\s*(\d+(?:,\d{3})*)/);
    if (salaryMatch) {
      job.salaryMin = parseInt(salaryMatch[1].replace(/,/g, ''));
      job.salaryMax = parseInt(salaryMatch[2].replace(/,/g, ''));
    }

    // 提取职位描述
    const descPatterns = [
      /(?:岗位描述|职位描述|工作内容|职责)[:：]\s*([^]*?)(?=(?:岗位要求|职位要求|任职要求)|$)/,
      /(?:职位详情|岗位描述)[^]*?([^]*?)(?=岗位要求|任职要求|$)/
    ];

    for (const pattern of descPatterns) {
      const match = text.match(pattern);
      if (match && match[1] && match[1].trim().length > 20) {
        job.description = match[1].trim();
        break;
      }
    }

    // 提取职位要求
    const reqMatch = text.match(/(?:岗位要求|职位要求|任职要求|要求)[:：]\s*([^]*?)(?=(?:福利待遇|联系方式)|$)/);
    if (reqMatch && reqMatch[1] && reqMatch[1].trim().length > 20) {
      job.requirements = reqMatch[1].trim();
    }

    // 提取福利待遇
    const benefitsMatch = text.match(/(?:福利待遇|待遇|福利)[:：]\s*([^]*?)(?=(?:联系方式|联系人)|$)/);
    if (benefitsMatch && benefitsMatch[1]) {
      job.benefits = benefitsMatch[1].trim();
    }

    return job;
  }
}

export const webJobParserService = new WebJobParserService();