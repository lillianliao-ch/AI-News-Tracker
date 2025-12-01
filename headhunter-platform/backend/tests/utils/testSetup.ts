import { PrismaClient } from '@prisma/client';
import { TestDataGenerator, TestDataConfig } from './testDataGenerator';
import { Resume, JobPosition } from '../../src/types';

export class TestSetup {
  private prisma: PrismaClient;
  private generatedData: {
    resumes: Resume[];
    jobs: JobPosition[];
    candidates: any[];
    companies: any[];
  } = {
    resumes: [],
    jobs: [],
    candidates: [],
    companies: []
  };

  constructor(prisma: PrismaClient) {
    this.prisma = prisma;
  }

  /**
   * 设置测试环境
   */
  async setupTestEnvironment(config: TestDataConfig = {}): Promise<void> {
    console.log('🚀 Setting up test environment...');
    
    // 清理现有测试数据
    await this.cleanupTestData();
    
    // 生成测试数据
    await this.generateTestData(config);
    
    // 插入到数据库
    await this.insertTestData();
    
    console.log('✅ Test environment setup complete');
  }

  /**
   * 清理测试数据
   */
  async cleanupTestData(): Promise<void> {
    console.log('🧹 Cleaning up existing test data...');
    
    try {
      // 按照外键依赖关系的逆序删除
      await this.prisma.jobMatchingScore.deleteMany({
        where: { id: { contains: 'test-' } }
      });
      
      await this.prisma.resumeSkill.deleteMany({
        where: { resumeId: { contains: 'resume-test-' } }
      });
      
      await this.prisma.language.deleteMany({
        where: { resumeId: { contains: 'resume-test-' } }
      });
      
      await this.prisma.certification.deleteMany({
        where: { resumeId: { contains: 'resume-test-' } }
      });
      
      await this.prisma.project.deleteMany({
        where: { resumeId: { contains: 'resume-test-' } }
      });
      
      await this.prisma.education.deleteMany({
        where: { resumeId: { contains: 'resume-test-' } }
      });
      
      await this.prisma.workExperience.deleteMany({
        where: { resumeId: { contains: 'resume-test-' } }
      });
      
      await this.prisma.resume.deleteMany({
        where: { id: { contains: 'resume-test-' } }
      });
      
      await this.prisma.job.deleteMany({
        where: { id: { contains: 'job-test-' } }
      });
      
      await this.prisma.user.deleteMany({
        where: { id: { contains: 'user-test-' } }
      });
      
      await this.prisma.company.deleteMany({
        where: { id: { contains: 'company-test-' } }
      });
      
      console.log('✅ Test data cleanup complete');
    } catch (error) {
      console.error('❌ Error during cleanup:', error);
      throw error;
    }
  }

  /**
   * 生成测试数据
   */
  private async generateTestData(config: TestDataConfig): Promise<void> {
    console.log('📊 Generating test data...');
    
    // 生成简历和职位数据
    this.generatedData.resumes = TestDataGenerator.generateResumes({
      resumeCount: 20,
      dataQuality: 'high',
      includeEdgeCases: true,
      ...config
    });
    
    this.generatedData.jobs = TestDataGenerator.generateJobs({
      jobCount: 15,
      dataQuality: 'high',
      includeEdgeCases: true,
      ...config
    });
    
    // 生成候选人数据
    this.generatedData.candidates = this.generatedData.resumes.map((resume, index) => ({
      id: `user-test-candidate-${index + 1}`,
      email: resume.parsedData.personalInfo.email,
      name: resume.parsedData.personalInfo.name,
      phone: resume.parsedData.personalInfo.phone,
      role: 'CANDIDATE',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    }));
    
    // 生成公司数据
    const uniqueCompanies = [...new Set(this.generatedData.jobs.map(job => job.company))];
    this.generatedData.companies = uniqueCompanies.map((companyName, index) => ({
      id: `company-test-${index + 1}`,
      name: companyName,
      industry: this.generatedData.jobs.find(job => job.company === companyName)?.industry || '科技',
      size: '100-500人',
      description: `${companyName}是一家专注于技术创新的公司`,
      website: `https://www.${companyName.toLowerCase().replace(/[^a-z0-9]/g, '')}.com`,
      location: this.generatedData.jobs.find(job => job.company === companyName)?.location || '北京',
      createdAt: new Date(),
      updatedAt: new Date()
    }));
    
    console.log(`Generated ${this.generatedData.resumes.length} resumes, ${this.generatedData.jobs.length} jobs, ${this.generatedData.candidates.length} candidates, ${this.generatedData.companies.length} companies`);
  }

  /**
   * 插入测试数据到数据库
   */
  private async insertTestData(): Promise<void> {
    console.log('💾 Inserting test data into database...');
    
    try {
      // 插入公司数据
      for (const company of this.generatedData.companies) {
        await this.prisma.company.create({ data: company });
      }
      
      // 插入候选人数据
      for (const candidate of this.generatedData.candidates) {
        await this.prisma.user.create({ data: candidate });
      }
      
      // 插入职位数据
      for (const job of this.generatedData.jobs) {
        const company = this.generatedData.companies.find(c => c.name === job.company);
        if (!company) continue;
        
        await this.prisma.job.create({
          data: {
            id: `job-test-${job.id}`,
            title: job.title,
            description: job.description,
            requirements: job.requiredSkills.join(', '),
            experienceLevel: job.experienceLevel,
            salaryMin: job.salaryRange.min,
            salaryMax: job.salaryRange.max,
            location: job.location,
            employmentType: 'FULL_TIME',
            industry: job.industry,
            companyId: company.id,
            status: 'ACTIVE',
            createdAt: job.createdAt,
            updatedAt: job.updatedAt
          }
        });
      }
      
      // 插入简历数据
      for (const resume of this.generatedData.resumes) {
        const candidate = this.generatedData.candidates.find(c => 
          c.email === resume.parsedData.personalInfo.email
        );
        if (!candidate) continue;
        
        // 创建简历记录
        await this.prisma.resume.create({
          data: {
            id: `resume-test-${resume.id}`,
            candidateId: candidate.id,
            filename: resume.filename,
            originalText: resume.originalText,
            summary: resume.parsedData.summary,
            confidence: resume.confidence,
            createdAt: resume.createdAt,
            updatedAt: resume.updatedAt
          }
        });
        
        // 插入工作经验
        for (const exp of resume.parsedData.workExperience) {
          await this.prisma.workExperience.create({
            data: {
              id: `work-exp-test-${Date.now()}-${Math.random()}`,
              resumeId: `resume-test-${resume.id}`,
              company: exp.company,
              position: exp.position,
              startDate: exp.startDate,
              endDate: exp.endDate,
              description: exp.description,
              industry: exp.industry
            }
          });
        }
        
        // 插入教育背景
        for (const edu of resume.parsedData.education) {
          await this.prisma.education.create({
            data: {
              id: `education-test-${Date.now()}-${Math.random()}`,
              resumeId: `resume-test-${resume.id}`,
              institution: edu.institution,
              degree: edu.degree,
              major: edu.major,
              graduationDate: edu.graduationDate
            }
          });
        }
        
        // 插入技能
        for (const skill of resume.parsedData.skills) {
          await this.prisma.resumeSkill.create({
            data: {
              id: `skill-test-${Date.now()}-${Math.random()}`,
              resumeId: `resume-test-${resume.id}`,
              skillName: skill.name,
              skillLevel: skill.level,
              yearsOfExperience: skill.yearsOfExperience,
              category: this.categorizeSkill(skill.name)
            }
          });
        }
        
        // 插入项目经历
        for (const project of resume.parsedData.projects) {
          await this.prisma.project.create({
            data: {
              id: `project-test-${Date.now()}-${Math.random()}`,
              resumeId: `resume-test-${resume.id}`,
              name: project.name,
              description: project.description,
              technologies: project.technologies.join(', '),
              startDate: project.startDate,
              endDate: project.endDate,
              role: project.role
            }
          });
        }
        
        // 插入证书
        for (const cert of resume.parsedData.certifications) {
          await this.prisma.certification.create({
            data: {
              id: `cert-test-${Date.now()}-${Math.random()}`,
              resumeId: `resume-test-${resume.id}`,
              name: cert.name,
              issuer: cert.issuer,
              issueDate: cert.issueDate,
              expiryDate: cert.expiryDate
            }
          });
        }
        
        // 插入语言能力
        for (const lang of resume.parsedData.languages) {
          await this.prisma.language.create({
            data: {
              id: `lang-test-${Date.now()}-${Math.random()}`,
              resumeId: `resume-test-${resume.id}`,
              language: lang.name,
              proficiency: lang.level
            }
          });
        }
      }
      
      console.log('✅ Test data insertion complete');
    } catch (error) {
      console.error('❌ Error during data insertion:', error);
      throw error;
    }
  }

  /**
   * 技能分类
   */
  private categorizeSkill(skillName: string): string {
    const categories: Record<string, string[]> = {
      'FRONTEND': ['JavaScript', 'TypeScript', 'React', 'Vue.js', 'Angular', 'HTML5', 'CSS3', 'SASS'],
      'BACKEND': ['Node.js', 'Python', 'Java', 'C#', 'Go', 'Rust', 'PHP', 'Ruby'],
      'DATABASE': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch'],
      'CLOUD': ['AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes'],
      'TOOLS': ['Git', 'Linux', 'Nginx', 'Apache', 'Jenkins'],
      'OTHER': []
    };
    
    for (const [category, skills] of Object.entries(categories)) {
      if (skills.includes(skillName)) {
        return category;
      }
    }
    
    return 'OTHER';
  }

  /**
   * 获取生成的测试数据
   */
  getGeneratedData() {
    return this.generatedData;
  }

  /**
   * 创建测试用的匹配配置
   */
  createTestMatchingConfig() {
    return {
      weights: {
        skills: 0.35,
        experience: 0.25,
        industry: 0.15,
        location: 0.10,
        salary: 0.10,
        education: 0.05
      },
      thresholds: {
        minimumScore: 0.5,
        minimumConfidence: 0.6,
        maxResults: 50
      }
    };
  }

  /**
   * 获取随机测试简历ID
   */
  getRandomResumeId(): string | null {
    if (this.generatedData.resumes.length === 0) return null;
    const randomIndex = Math.floor(Math.random() * this.generatedData.resumes.length);
    return `resume-test-${this.generatedData.resumes[randomIndex].id}`;
  }

  /**
   * 获取随机测试职位ID
   */
  getRandomJobId(): string | null {
    if (this.generatedData.jobs.length === 0) return null;
    const randomIndex = Math.floor(Math.random() * this.generatedData.jobs.length);
    return `job-test-${this.generatedData.jobs[randomIndex].id}`;
  }

  /**
   * 验证数据库中的测试数据
   */
  async validateTestData(): Promise<boolean> {
    try {
      const resumeCount = await this.prisma.resume.count({
        where: { id: { contains: 'resume-test-' } }
      });
      
      const jobCount = await this.prisma.job.count({
        where: { id: { contains: 'job-test-' } }
      });
      
      const candidateCount = await this.prisma.user.count({
        where: { id: { contains: 'user-test-candidate-' } }
      });
      
      console.log(`Validation: ${resumeCount} resumes, ${jobCount} jobs, ${candidateCount} candidates in database`);
      
      return resumeCount > 0 && jobCount > 0 && candidateCount > 0;
    } catch (error) {
      console.error('❌ Error during data validation:', error);
      return false;
    }
  }
}