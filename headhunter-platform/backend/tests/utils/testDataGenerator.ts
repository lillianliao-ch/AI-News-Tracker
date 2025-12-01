import { faker } from '@faker-js/faker';
import { Resume, JobPosition, WorkExperience, Education, Skill, Project, Certification, Language } from '../../src/types';

// 配置faker为中文环境
faker.setLocale('zh_CN');

export interface TestDataConfig {
  // 简历生成配置
  resumeCount?: number;
  skillsPerResume?: { min: number; max: number };
  experiencePerResume?: { min: number; max: number };
  educationPerResume?: { min: number; max: number };
  projectsPerResume?: { min: number; max: number };
  
  // 职位生成配置
  jobCount?: number;
  skillsPerJob?: { min: number; max: number };
  
  // 数据质量配置
  dataQuality?: 'high' | 'medium' | 'low';
  includeEdgeCases?: boolean;
}

export class TestDataGenerator {
  private static readonly SKILLS = [
    // 前端技能
    'JavaScript', 'TypeScript', 'React', 'Vue.js', 'Angular', 'HTML5', 'CSS3', 'SASS', 'Webpack', 'Vite',
    // 后端技能
    'Node.js', 'Python', 'Java', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Express.js', 'NestJS', 'Django', 'Flask',
    // 数据库
    'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch', 'Oracle', 'SQL Server',
    // 云服务
    'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI/CD',
    // 其他技能
    'Git', 'Linux', 'Nginx', 'Apache', 'GraphQL', 'RESTful API', 'Microservices', 'Machine Learning'
  ];

  private static readonly INDUSTRIES = [
    '互联网', '金融科技', '电子商务', '人工智能', '大数据', '云计算',
    '移动互联网', '区块链', '物联网', '游戏', '教育科技', '医疗健康',
    '企业服务', '社交网络', '电商平台', '在线教育', '数字营销', '智能制造'
  ];

  private static readonly LOCATIONS = [
    '北京', '上海', '广州', '深圳', '杭州', '成都', '南京', '武汉',
    '西安', '苏州', '天津', '重庆', '青岛', '大连', '厦门', '长沙'
  ];

  private static readonly COMPANIES = [
    '腾讯', '阿里巴巴', '百度', '字节跳动', '美团', '滴滴出行', '京东', '网易',
    '小米', '华为', '拼多多', '快手', '哔哩哔哩', '蚂蚁集团', '顺丰科技', '新浪',
    '搜狐', '58同城', '携程', '去哪儿', '爱奇艺', '优酷', '陌陌', '知乎'
  ];

  private static readonly UNIVERSITIES = [
    '清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学', '南京大学',
    '中山大学', '华中科技大学', '西安交通大学', '哈尔滨工业大学', '北京航空航天大学',
    '同济大学', '东南大学', '天津大学', '大连理工大学', '华南理工大学'
  ];

  private static readonly MAJORS = [
    '计算机科学与技术', '软件工程', '信息与计算科学', '网络工程', '物联网工程',
    '数据科学与大数据技术', '人工智能', '网络空间安全', '电子信息工程', '通信工程'
  ];

  private static readonly EXPERIENCE_LEVELS = ['初级', '中级', '高级', '资深', '专家'];
  private static readonly EDUCATION_LEVELS = ['大专', '本科', '硕士', '博士'];
  private static readonly SKILL_LEVELS = ['初级', '中级', '高级', '专家'];

  /**
   * 生成测试简历数据
   */
  static generateResumes(config: TestDataConfig = {}): Resume[] {
    const {
      resumeCount = 50,
      skillsPerResume = { min: 3, max: 8 },
      experiencePerResume = { min: 1, max: 4 },
      educationPerResume = { min: 1, max: 2 },
      projectsPerResume = { min: 0, max: 3 },
      dataQuality = 'high',
      includeEdgeCases = false
    } = config;

    const resumes: Resume[] = [];

    for (let i = 0; i < resumeCount; i++) {
      const resume = this.generateSingleResume(i, {
        skillsPerResume,
        experiencePerResume,
        educationPerResume,
        projectsPerResume,
        dataQuality,
        includeEdgeCases: includeEdgeCases && i < resumeCount * 0.1 // 10%的边缘案例
      });
      resumes.push(resume);
    }

    return resumes;
  }

  /**
   * 生成测试职位数据
   */
  static generateJobs(config: TestDataConfig = {}): JobPosition[] {
    const {
      jobCount = 30,
      skillsPerJob = { min: 3, max: 6 },
      dataQuality = 'high',
      includeEdgeCases = false
    } = config;

    const jobs: JobPosition[] = [];

    for (let i = 0; i < jobCount; i++) {
      const job = this.generateSingleJob(i, {
        skillsPerJob,
        dataQuality,
        includeEdgeCases: includeEdgeCases && i < jobCount * 0.1
      });
      jobs.push(job);
    }

    return jobs;
  }

  /**
   * 生成单个简历
   */
  private static generateSingleResume(index: number, config: any): Resume {
    const isEdgeCase = config.includeEdgeCases;
    const quality = config.dataQuality;
    
    // 生成个人信息
    const personalInfo = {
      name: isEdgeCase ? this.generateEdgeCaseName() : faker.person.fullName(),
      email: faker.internet.email(),
      phone: faker.phone.number('138########'),
      location: faker.helpers.arrayElement(this.LOCATIONS)
    };

    // 生成技能
    const skillCount = faker.number.int(config.skillsPerResume);
    const skills = this.generateSkills(skillCount, quality);

    // 生成工作经验
    const experienceCount = faker.number.int(config.experiencePerResume);
    const workExperience = this.generateWorkExperience(experienceCount, quality);

    // 生成教育背景
    const educationCount = faker.number.int(config.educationPerResume);
    const education = this.generateEducation(educationCount, quality);

    // 生成项目经历
    const projectCount = faker.number.int(config.projectsPerResume);
    const projects = this.generateProjects(projectCount, quality);

    // 生成证书
    const certifications = this.generateCertifications(quality);

    // 生成语言能力
    const languages = this.generateLanguages(quality);

    // 计算总工作年限
    const totalExperience = workExperience.reduce((total, exp) => {
      const years = this.calculateYearsBetween(exp.startDate, exp.endDate || new Date());
      return total + years;
    }, 0);

    // 生成简历摘要
    const summary = this.generateSummary(personalInfo.name, totalExperience, skills, quality);

    const resume: Resume = {
      id: `resume-${index + 1}`,
      candidateId: `candidate-${index + 1}`,
      filename: `resume-${index + 1}.pdf`,
      originalText: this.generateOriginalText(personalInfo, skills, workExperience, quality),
      parsedData: {
        personalInfo,
        summary,
        skills,
        workExperience,
        education,
        projects,
        certifications,
        languages
      },
      confidence: this.generateConfidence(quality, isEdgeCase),
      createdAt: faker.date.past({ years: 1 }),
      updatedAt: new Date()
    };

    return resume;
  }

  /**
   * 生成单个职位
   */
  private static generateSingleJob(index: number, config: any): JobPosition {
    const isEdgeCase = config.includeEdgeCases;
    const quality = config.dataQuality;

    const company = faker.helpers.arrayElement(this.COMPANIES);
    const location = faker.helpers.arrayElement(this.LOCATIONS);
    const industry = faker.helpers.arrayElement(this.INDUSTRIES);
    const experienceLevel = faker.helpers.arrayElement(this.EXPERIENCE_LEVELS);

    // 生成职位标题
    const titles = [
      '前端开发工程师', '后端开发工程师', '全栈开发工程师', '移动端开发工程师',
      '数据分析师', '算法工程师', '产品经理', '技术经理', '架构师', 'DevOps工程师'
    ];
    const title = isEdgeCase ? '特殊职位' : faker.helpers.arrayElement(titles);

    // 生成技能要求
    const skillCount = faker.number.int(config.skillsPerJob);
    const requiredSkills = faker.helpers.arrayElements(this.SKILLS, skillCount);
    const preferredSkills = faker.helpers.arrayElements(
      this.SKILLS.filter(skill => !requiredSkills.includes(skill)),
      Math.min(3, this.SKILLS.length - requiredSkills.length)
    );

    // 生成薪资范围
    const baseSalary = this.generateSalaryByLevel(experienceLevel);
    const salaryRange = {
      min: baseSalary * 0.8,
      max: baseSalary * 1.2
    };

    // 处理边缘案例
    if (isEdgeCase) {
      salaryRange.min = 0; // 实习职位
      salaryRange.max = 5000;
    }

    const job: JobPosition = {
      id: `job-${index + 1}`,
      title,
      company,
      description: this.generateJobDescription(title, requiredSkills, quality),
      requiredSkills,
      preferredSkills,
      experienceLevel,
      industry,
      location,
      salaryRange,
      educationRequirement: faker.helpers.arrayElement(this.EDUCATION_LEVELS),
      createdAt: faker.date.past({ years: 0.5 }),
      updatedAt: new Date()
    };

    return job;
  }

  /**
   * 生成技能列表
   */
  private static generateSkills(count: number, quality: string): Skill[] {
    const selectedSkills = faker.helpers.arrayElements(this.SKILLS, count);
    
    return selectedSkills.map(skillName => ({
      name: skillName,
      level: faker.helpers.arrayElement(this.SKILL_LEVELS),
      yearsOfExperience: faker.number.int({ min: 1, max: 8 })
    }));
  }

  /**
   * 生成工作经验
   */
  private static generateWorkExperience(count: number, quality: string): WorkExperience[] {
    const experiences: WorkExperience[] = [];
    let currentDate = new Date();
    
    for (let i = 0; i < count; i++) {
      const startDate = faker.date.past({ years: 8, refDate: currentDate });
      const endDate = i === 0 ? null : faker.date.between({ from: startDate, to: currentDate });
      
      const experience: WorkExperience = {
        company: faker.helpers.arrayElement(this.COMPANIES),
        position: this.generatePosition(quality),
        startDate,
        endDate,
        description: this.generateWorkDescription(quality),
        industry: faker.helpers.arrayElement(this.INDUSTRIES)
      };
      
      experiences.push(experience);
      currentDate = startDate;
    }
    
    return experiences.reverse(); // 按时间顺序排列
  }

  /**
   * 生成教育背景
   */
  private static generateEducation(count: number, quality: string): Education[] {
    const educations: Education[] = [];
    
    for (let i = 0; i < count; i++) {
      const education: Education = {
        institution: faker.helpers.arrayElement(this.UNIVERSITIES),
        degree: faker.helpers.arrayElement(this.EDUCATION_LEVELS),
        major: faker.helpers.arrayElement(this.MAJORS),
        graduationDate: faker.date.past({ years: 10 })
      };
      
      educations.push(education);
    }
    
    return educations;
  }

  /**
   * 生成项目经历
   */
  private static generateProjects(count: number, quality: string): Project[] {
    const projects: Project[] = [];
    
    for (let i = 0; i < count; i++) {
      const project: Project = {
        name: this.generateProjectName(quality),
        description: this.generateProjectDescription(quality),
        technologies: faker.helpers.arrayElements(this.SKILLS, faker.number.int({ min: 2, max: 5 })),
        startDate: faker.date.past({ years: 3 }),
        endDate: faker.date.recent({ days: 365 }),
        role: this.generateProjectRole()
      };
      
      projects.push(project);
    }
    
    return projects;
  }

  /**
   * 生成证书
   */
  private static generateCertifications(quality: string): Certification[] {
    const certifications = [
      'AWS认证解决方案架构师', 'Oracle认证Java程序员', 'Microsoft认证Azure开发者',
      'Google Cloud认证工程师', 'PMP项目管理认证', 'Scrum Master认证'
    ];
    
    const count = faker.number.int({ min: 0, max: 3 });
    const selected = faker.helpers.arrayElements(certifications, count);
    
    return selected.map(name => ({
      name,
      issuer: this.getCertificationIssuer(name),
      issueDate: faker.date.past({ years: 3 }),
      expiryDate: faker.date.future({ years: 2 })
    }));
  }

  /**
   * 生成语言能力
   */
  private static generateLanguages(quality: string): Language[] {
    const languages = [
      { name: '中文', level: '母语' },
      { name: '英语', level: faker.helpers.arrayElement(['良好', '流利', '精通']) }
    ];
    
    // 可能添加其他语言
    if (faker.datatype.boolean(0.3)) {
      const otherLanguages = ['日语', '韩语', '法语', '德语'];
      languages.push({
        name: faker.helpers.arrayElement(otherLanguages),
        level: faker.helpers.arrayElement(['基础', '良好', '流利'])
      });
    }
    
    return languages;
  }

  /**
   * 生成边缘案例姓名
   */
  private static generateEdgeCaseName(): string {
    const edgeCases = [
      '张三', '李四', '王五', // 常见姓名
      'John Smith', 'Jane Doe', // 英文姓名
      '欧阳修', '司马光', '诸葛亮', // 复姓
      '阿不都·热依木', '买买提·艾合买提' // 少数民族姓名
    ];
    return faker.helpers.arrayElement(edgeCases);
  }

  /**
   * 生成薪资（根据经验等级）
   */
  private static generateSalaryByLevel(level: string): number {
    const salaryMap: Record<string, number> = {
      '初级': 12000,
      '中级': 20000,
      '高级': 35000,
      '资深': 50000,
      '专家': 80000
    };
    
    const base = salaryMap[level] || 15000;
    return base + faker.number.int({ min: -3000, max: 5000 });
  }

  /**
   * 生成职位描述
   */
  private static generateJobDescription(title: string, skills: string[], quality: string): string {
    if (quality === 'low') {
      return `招聘${title}，要求会${skills.slice(0, 2).join('、')}`;
    }
    
    return `我们正在寻找一名优秀的${title}，负责${this.getJobResponsibilities(title)}。
要求掌握${skills.join('、')}等技术，具备良好的团队协作能力和沟通能力。
我们提供有竞争力的薪资待遇和完善的职业发展空间。`;
  }

  /**
   * 生成简历摘要
   */
  private static generateSummary(name: string, experience: number, skills: Skill[], quality: string): string {
    if (quality === 'low') {
      return `${name}，${experience}年工作经验`;
    }
    
    const skillNames = skills.slice(0, 3).map(s => s.name).join('、');
    return `拥有${experience}年软件开发经验，精通${skillNames}等技术。
具备丰富的项目开发经验，熟悉敏捷开发流程，具备良好的团队协作能力和技术创新意识。`;
  }

  /**
   * 生成原始简历文本
   */
  private static generateOriginalText(personalInfo: any, skills: Skill[], experiences: WorkExperience[], quality: string): string {
    if (quality === 'low') {
      return `姓名：${personalInfo.name}\n技能：${skills.map(s => s.name).join('，')}`;
    }
    
    return `姓名：${personalInfo.name}
邮箱：${personalInfo.email}
电话：${personalInfo.phone}
地址：${personalInfo.location}

技能：
${skills.map(s => `- ${s.name}（${s.level}，${s.yearsOfExperience}年经验）`).join('\n')}

工作经历：
${experiences.map(exp => `${exp.company} - ${exp.position} (${exp.startDate.getFullYear()}-${exp.endDate?.getFullYear() || '至今'})`).join('\n')}`;
  }

  /**
   * 辅助方法
   */
  private static generateConfidence(quality: string, isEdgeCase: boolean): number {
    if (isEdgeCase) return faker.number.float({ min: 0.3, max: 0.6 });
    
    const baseConfidence = quality === 'high' ? 0.9 : quality === 'medium' ? 0.75 : 0.6;
    return faker.number.float({ min: baseConfidence - 0.1, max: Math.min(baseConfidence + 0.1, 1.0) });
  }

  private static generatePosition(quality: string): string {
    const positions = [
      '软件工程师', '高级开发工程师', '技术专家', '架构师',
      '前端工程师', '后端工程师', '全栈工程师', '移动开发工程师'
    ];
    return faker.helpers.arrayElement(positions);
  }

  private static generateWorkDescription(quality: string): string {
    if (quality === 'low') {
      return '负责软件开发工作';
    }
    
    const descriptions = [
      '负责公司核心产品的前端开发，参与需求分析、技术方案设计和代码实现',
      '主导后端服务架构设计，优化系统性能，提升服务稳定性',
      '参与移动端应用开发，实现用户界面和业务逻辑',
      '负责数据库设计和优化，编写高质量代码，参与代码评审'
    ];
    return faker.helpers.arrayElement(descriptions);
  }

  private static generateProjectName(quality: string): string {
    if (quality === 'low') {
      return '项目' + faker.number.int({ min: 1, max: 10 });
    }
    
    const projectTypes = ['电商平台', '移动应用', '管理系统', '数据平台', '监控系统'];
    const adjectives = ['智能', '高效', '创新', '先进', '便捷'];
    
    return faker.helpers.arrayElement(adjectives) + faker.helpers.arrayElement(projectTypes);
  }

  private static generateProjectDescription(quality: string): string {
    if (quality === 'low') {
      return '项目开发';
    }
    
    return `该项目是基于${faker.helpers.arrayElement(['React', 'Vue', 'Angular'])}的现代化Web应用，
实现了用户管理、数据分析、实时通讯等核心功能。项目采用微服务架构，
支持高并发访问，具备良好的扩展性和可维护性。`;
  }

  private static generateProjectRole(): string {
    const roles = ['项目负责人', '核心开发者', '前端开发', '后端开发', '技术负责人'];
    return faker.helpers.arrayElement(roles);
  }

  private static getCertificationIssuer(certName: string): string {
    const issuerMap: Record<string, string> = {
      'AWS认证解决方案架构师': 'Amazon Web Services',
      'Oracle认证Java程序员': 'Oracle Corporation',
      'Microsoft认证Azure开发者': 'Microsoft',
      'Google Cloud认证工程师': 'Google Cloud',
      'PMP项目管理认证': 'Project Management Institute',
      'Scrum Master认证': 'Scrum Alliance'
    };
    return issuerMap[certName] || '认证机构';
  }

  private static getJobResponsibilities(title: string): string {
    const responsibilityMap: Record<string, string> = {
      '前端开发工程师': '前端页面开发、用户体验优化、前端架构设计',
      '后端开发工程师': '后端服务开发、数据库设计、API接口开发',
      '全栈开发工程师': '前后端开发、系统架构设计、技术选型',
      '移动端开发工程师': '移动应用开发、性能优化、用户体验设计',
      '数据分析师': '数据分析、报表制作、业务洞察',
      '算法工程师': '算法设计、模型优化、性能调优',
      '产品经理': '产品规划、需求分析、项目管理',
      '技术经理': '团队管理、技术决策、项目推进',
      '架构师': '系统架构设计、技术选型、技术规范制定',
      'DevOps工程师': '持续集成、部署自动化、运维监控'
    };
    return responsibilityMap[title] || '相关技术工作';
  }

  private static calculateYearsBetween(startDate: Date, endDate: Date): number {
    const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
    const diffYears = diffTime / (1000 * 60 * 60 * 24 * 365.25);
    return Math.round(diffYears * 10) / 10; // 保留一位小数
  }

  /**
   * 生成匹配的简历和职位对
   */
  static generateMatchedPairs(count: number = 10): { resumes: Resume[]; jobs: JobPosition[]; matches: Array<{ resumeId: string; jobId: string; expectedScore: number }> } {
    const resumes = this.generateResumes({ resumeCount: count, dataQuality: 'high' });
    const jobs = this.generateJobs({ jobCount: count, dataQuality: 'high' });
    const matches: Array<{ resumeId: string; jobId: string; expectedScore: number }> = [];

    // 为每个简历匹配1-3个相关职位
    resumes.forEach(resume => {
      const matchCount = faker.number.int({ min: 1, max: 3 });
      const matchedJobs = faker.helpers.arrayElements(jobs, matchCount);
      
      matchedJobs.forEach(job => {
        const score = this.calculateExpectedMatchScore(resume, job);
        matches.push({
          resumeId: resume.id,
          jobId: job.id,
          expectedScore: score
        });
      });
    });

    return { resumes, jobs, matches };
  }

  /**
   * 计算预期匹配分数（用于测试验证）
   */
  private static calculateExpectedMatchScore(resume: Resume, job: JobPosition): number {
    const resumeSkills = resume.parsedData.skills.map(s => s.name);
    const jobSkills = [...job.requiredSkills, ...job.preferredSkills];
    
    // 技能匹配度
    const skillMatch = resumeSkills.filter(skill => jobSkills.includes(skill)).length / jobSkills.length;
    
    // 地理位置匹配
    const locationMatch = resume.parsedData.personalInfo.location === job.location ? 1 : 0.5;
    
    // 简单的分数计算（实际算法会更复杂）
    const score = skillMatch * 0.6 + locationMatch * 0.2 + Math.random() * 0.2;
    
    return Math.min(score, 1);
  }
}