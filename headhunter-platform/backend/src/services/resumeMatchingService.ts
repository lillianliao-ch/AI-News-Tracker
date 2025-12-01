import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// 匹配算法接口
export interface MatchingResult {
  jobId: string;
  overallScore: number;
  dimensionScores: {
    skills: number;
    experience: number;
    industry: number;
    location: number;
    salary: number;
    education: number;
  };
  matchDetails: {
    matchedSkills: SkillMatch[];
    missingSkills: string[];
    matchReasons: string[];
    experienceMatch: ExperienceMatch;
    salaryFit: SalaryFit;
  };
  confidence: number;
}

export interface SkillMatch {
  skill: string;
  candidateLevel: string;
  requiredLevel: string;
  score: number;
  isKeySkill: boolean;
}

export interface ExperienceMatch {
  yearsMatch: boolean;
  industryMatch: boolean;
  roleMatch: boolean;
  score: number;
}

export interface SalaryFit {
  expectationMet: boolean;
  fitPercentage: number;
  currentVsOffered: number;
}

// 匹配权重配置
export interface MatchingWeights {
  skills: number;         // 技能匹配权重: 35%
  experience: number;     // 经验匹配权重: 25%
  industry: number;       // 行业匹配权重: 15%
  location: number;       // 地点匹配权重: 10%
  salary: number;         // 薪资匹配权重: 10%
  education: number;      // 教育背景权重: 5%
}

export class ResumeMatchingService {
  private defaultWeights: MatchingWeights = {
    skills: 0.35,
    experience: 0.25,
    industry: 0.15,
    location: 0.10,
    salary: 0.10,
    education: 0.05
  };

  /**
   * 为候选人匹配最合适的岗位
   */
  async findMatchingJobs(
    candidateId: string, 
    limit: number = 20,
    weights?: Partial<MatchingWeights>
  ): Promise<MatchingResult[]> {
    console.log(`🎯 开始为候选人 ${candidateId} 匹配岗位...`);
    
    // 1. 获取候选人简历信息
    const resume = await this.getCandidateResume(candidateId);
    if (!resume) {
      throw new Error('候选人简历不存在');
    }

    // 2. 获取所有开放的岗位
    const openJobs = await this.getOpenJobs();
    console.log(`📋 找到 ${openJobs.length} 个开放岗位`);

    // 3. 计算匹配分数
    const matchingPromises = openJobs.map(job => 
      this.calculateJobMatch(resume, job, weights)
    );
    
    const matchingResults = await Promise.all(matchingPromises);

    // 4. 按总分排序并返回前N个
    const sortedResults = matchingResults
      .sort((a, b) => b.overallScore - a.overallScore)
      .slice(0, limit);

    console.log(`✅ 完成匹配，返回前 ${sortedResults.length} 个结果`);
    return sortedResults;
  }

  /**
   * 为岗位匹配最合适的候选人
   */
  async findMatchingCandidates(
    jobId: string,
    limit: number = 50,
    weights?: Partial<MatchingWeights>
  ): Promise<MatchingResult[]> {
    console.log(`🎯 开始为岗位 ${jobId} 匹配候选人...`);
    
    // 1. 获取岗位信息
    const job = await this.getJobDetails(jobId);
    if (!job) {
      throw new Error('岗位不存在');
    }

    // 2. 获取所有候选人简历
    const resumes = await this.getAllResumes();
    console.log(`👥 找到 ${resumes.length} 个候选人简历`);

    // 3. 计算匹配分数
    const matchingPromises = resumes.map(resume => 
      this.calculateJobMatch(resume, job, weights)
    );
    
    const matchingResults = await Promise.all(matchingPromises);

    // 4. 按总分排序并返回前N个
    const sortedResults = matchingResults
      .filter(result => result.overallScore > 30) // 过滤掉分数太低的
      .sort((a, b) => b.overallScore - a.overallScore)
      .slice(0, limit);

    console.log(`✅ 完成匹配，返回前 ${sortedResults.length} 个结果`);
    return sortedResults;
  }

  /**
   * 计算单个岗位与简历的匹配度
   */
  private async calculateJobMatch(
    resume: any,
    job: any,
    customWeights?: Partial<MatchingWeights>
  ): Promise<MatchingResult> {
    const weights = { ...this.defaultWeights, ...customWeights };
    
    // 1. 技能匹配分析
    const skillsScore = await this.calculateSkillsMatch(resume, job);
    
    // 2. 经验匹配分析
    const experienceScore = await this.calculateExperienceMatch(resume, job);
    
    // 3. 行业匹配分析
    const industryScore = this.calculateIndustryMatch(resume, job);
    
    // 4. 地点匹配分析
    const locationScore = this.calculateLocationMatch(resume, job);
    
    // 5. 薪资匹配分析
    const salaryScore = this.calculateSalaryMatch(resume, job);
    
    // 6. 教育背景匹配
    const educationScore = this.calculateEducationMatch(resume, job);

    // 7. 计算加权总分
    const overallScore = Math.round(
      skillsScore.score * weights.skills +
      experienceScore.score * weights.experience +
      industryScore * weights.industry +
      locationScore * weights.location +
      salaryScore.score * weights.salary +
      educationScore * weights.education
    );

    // 8. 计算置信度 (基于数据完整性和匹配一致性)
    const confidence = this.calculateConfidence(resume, job, overallScore);

    return {
      jobId: job.id,
      overallScore,
      dimensionScores: {
        skills: skillsScore.score,
        experience: experienceScore.score,
        industry: industryScore,
        location: locationScore,
        salary: salaryScore.score,
        education: educationScore
      },
      matchDetails: {
        matchedSkills: skillsScore.matchedSkills,
        missingSkills: skillsScore.missingSkills,
        matchReasons: this.generateMatchReasons(resume, job, overallScore),
        experienceMatch: experienceScore.details,
        salaryFit: salaryScore.details
      },
      confidence
    };
  }

  /**
   * 技能匹配算法
   */
  private async calculateSkillsMatch(resume: any, job: any): Promise<{
    score: number;
    matchedSkills: SkillMatch[];
    missingSkills: string[];
  }> {
    console.log('🔧 计算技能匹配度...');
    
    // 1. 从岗位要求中提取技能关键词
    const requiredSkills = await this.extractSkillsFromJobDescription(
      job.requirements + ' ' + job.description
    );
    
    // 2. 获取候选人技能
    const candidateSkills = resume.skills || [];
    
    const matchedSkills: SkillMatch[] = [];
    const missingSkills: string[] = [];
    
    let totalScore = 0;
    let maxPossibleScore = 0;

    // 3. 对每个要求的技能进行匹配
    for (const requiredSkill of requiredSkills) {
      const skillWeight = requiredSkill.isKeySkill ? 3 : 1;
      maxPossibleScore += 100 * skillWeight;
      
      const candidateSkill = candidateSkills.find((skill: any) => 
        this.isSkillMatch(skill.name, requiredSkill.name)
      );
      
      if (candidateSkill) {
        const skillScore = this.calculateSkillLevelScore(
          candidateSkill.level,
          requiredSkill.level,
          candidateSkill.yearsUsed
        );
        
        matchedSkills.push({
          skill: requiredSkill.name,
          candidateLevel: candidateSkill.level,
          requiredLevel: requiredSkill.level,
          score: skillScore,
          isKeySkill: requiredSkill.isKeySkill
        });
        
        totalScore += skillScore * skillWeight;
      } else {
        missingSkills.push(requiredSkill.name);
      }
    }

    const finalScore = maxPossibleScore > 0 ? (totalScore / maxPossibleScore) * 100 : 0;
    
    console.log(`🔧 技能匹配完成: ${finalScore.toFixed(1)}% (${matchedSkills.length}/${requiredSkills.length})`);
    
    return {
      score: Math.round(finalScore),
      matchedSkills,
      missingSkills
    };
  }

  /**
   * 经验匹配算法
   */
  private async calculateExperienceMatch(resume: any, job: any): Promise<{
    score: number;
    details: ExperienceMatch;
  }> {
    console.log('💼 计算经验匹配度...');
    
    const workExperiences = resume.workExperience || [];
    const requiredYears = this.extractRequiredYears(job.requirements);
    
    // 1. 工作年限匹配
    const totalYears = resume.yearsExp || 0;
    const yearsMatch = totalYears >= requiredYears;
    const yearsScore = Math.min((totalYears / Math.max(requiredYears, 1)) * 100, 100);
    
    // 2. 行业经验匹配
    const industryMatch = workExperiences.some((exp: any) => 
      exp.industry && this.isIndustryMatch(exp.industry, job.industry)
    );
    const industryScore = industryMatch ? 100 : 0;
    
    // 3. 职位相关性匹配
    const roleMatch = workExperiences.some((exp: any) =>
      this.isRoleMatch(exp.position, job.title)
    );
    const roleScore = roleMatch ? 100 : 0;
    
    // 4. 综合评分 (年限50% + 行业30% + 职位20%)
    const overallScore = Math.round(
      yearsScore * 0.5 + industryScore * 0.3 + roleScore * 0.2
    );
    
    console.log(`💼 经验匹配完成: ${overallScore}% (${totalYears}年/${requiredYears}年)`);
    
    return {
      score: overallScore,
      details: {
        yearsMatch,
        industryMatch,
        roleMatch,
        score: overallScore
      }
    };
  }

  /**
   * 行业匹配算法
   */
  private calculateIndustryMatch(resume: any, job: any): number {
    console.log('🏢 计算行业匹配度...');
    
    if (!job.industry) return 50; // 无行业要求时给中等分
    
    // 1. 当前行业匹配
    const workExperiences = resume.workExperience || [];
    const hasIndustryExp = workExperiences.some((exp: any) =>
      exp.industry && this.isIndustryMatch(exp.industry, job.industry)
    );
    
    // 2. 偏好行业匹配
    const preferredIndustries = resume.preferredIndustries || [];
    const hasIndustryPreference = preferredIndustries.includes(job.industry);
    
    let score = 0;
    if (hasIndustryExp && hasIndustryPreference) {
      score = 100; // 有经验且有偏好
    } else if (hasIndustryExp) {
      score = 80;  // 仅有经验
    } else if (hasIndustryPreference) {
      score = 60;  // 仅有偏好
    } else {
      score = 30;  // 无匹配
    }
    
    console.log(`🏢 行业匹配完成: ${score}%`);
    return score;
  }

  /**
   * 地点匹配算法
   */
  private calculateLocationMatch(resume: any, job: any): number {
    console.log('📍 计算地点匹配度...');
    
    if (!job.location) return 50; // 无地点要求时给中等分
    
    // 1. 当前居住地匹配
    const currentLocationMatch = resume.location && 
      this.isLocationMatch(resume.location, job.location);
    
    // 2. 期望工作地点匹配
    const preferredLocations = resume.preferredLocations || [];
    const hasLocationPreference = preferredLocations.some((loc: string) =>
      this.isLocationMatch(loc, job.location)
    );
    
    let score = 0;
    if (currentLocationMatch && hasLocationPreference) {
      score = 100; // 当前地点和偏好都匹配
    } else if (currentLocationMatch) {
      score = 90;  // 当前地点匹配
    } else if (hasLocationPreference) {
      score = 70;  // 偏好地点匹配
    } else {
      score = 20;  // 无匹配
    }
    
    console.log(`📍 地点匹配完成: ${score}%`);
    return score;
  }

  /**
   * 薪资匹配算法
   */
  private calculateSalaryMatch(resume: any, job: any): {
    score: number;
    details: SalaryFit;
  } {
    console.log('💰 计算薪资匹配度...');
    
    const currentSalary = resume.currentSalary || 0;
    const expectedSalary = resume.expectedSalary || 0;
    const jobSalaryMin = job.salaryMin || 0;
    const jobSalaryMax = job.salaryMax || 0;
    
    if (jobSalaryMin === 0 && jobSalaryMax === 0) {
      // 无薪资信息时返回中等分
      return {
        score: 50,
        details: {
          expectationMet: true,
          fitPercentage: 50,
          currentVsOffered: 0
        }
      };
    }
    
    const jobSalaryMid = (jobSalaryMin + jobSalaryMax) / 2;
    
    // 1. 期望薪资是否得到满足
    const expectationMet = expectedSalary === 0 || jobSalaryMax >= expectedSalary;
    
    // 2. 薪资匹配度计算
    let fitPercentage = 0;
    if (expectedSalary > 0) {
      if (expectedSalary <= jobSalaryMax && expectedSalary >= jobSalaryMin) {
        fitPercentage = 100; // 完全在范围内
      } else if (expectedSalary > jobSalaryMax) {
        fitPercentage = Math.max(0, 100 - ((expectedSalary - jobSalaryMax) / expectedSalary) * 100);
      } else {
        fitPercentage = Math.max(0, 100 - ((jobSalaryMin - expectedSalary) / jobSalaryMin) * 100);
      }
    } else {
      fitPercentage = 70; // 无期望薪资时给中等分
    }
    
    // 3. 当前薪资 vs 提供薪资
    const currentVsOffered = currentSalary > 0 ? 
      ((jobSalaryMid - currentSalary) / currentSalary) * 100 : 0;
    
    const score = Math.round(fitPercentage);
    
    console.log(`💰 薪资匹配完成: ${score}% (期望:${expectedSalary}, 提供:${jobSalaryMin}-${jobSalaryMax})`);
    
    return {
      score,
      details: {
        expectationMet,
        fitPercentage,
        currentVsOffered
      }
    };
  }

  /**
   * 教育背景匹配算法
   */
  private calculateEducationMatch(resume: any, job: any): number {
    console.log('🎓 计算教育背景匹配度...');
    
    const education = resume.education || [];
    const requiredDegree = this.extractRequiredDegree(job.requirements);
    
    if (!requiredDegree) return 70; // 无学历要求时给较高分
    
    const highestDegree = this.getHighestDegree(education);
    const degreeScore = this.compareDegreeLevel(highestDegree, requiredDegree);
    
    console.log(`🎓 教育背景匹配完成: ${degreeScore}%`);
    return degreeScore;
  }

  // ============= 辅助方法 =============

  private async getCandidateResume(candidateId: string) {
    return await prisma.resume.findUnique({
      where: { candidateId },
      include: {
        workExperience: true,
        education: true,
        skills: true,
        projects: true,
        certifications: true,
        languages: true
      }
    });
  }

  private async getOpenJobs() {
    return await prisma.job.findMany({
      where: { status: 'open' },
      include: {
        companyClient: true
      }
    });
  }

  private async getJobDetails(jobId: string) {
    return await prisma.job.findUnique({
      where: { id: jobId },
      include: {
        companyClient: true
      }
    });
  }

  private async getAllResumes() {
    return await prisma.resume.findMany({
      where: { parseStatus: 'completed' },
      include: {
        workExperience: true,
        education: true,
        skills: true,
        projects: true,
        certifications: true,
        languages: true
      }
    });
  }

  /**
   * 从岗位描述中提取技能要求
   */
  private async extractSkillsFromJobDescription(text: string): Promise<any[]> {
    // 这里可以使用NLP或关键词库匹配
    // 简化实现，使用预定义的技能库
    const skillKeywords = [
      // 编程语言
      { name: 'Java', level: 'intermediate', isKeySkill: true },
      { name: 'Python', level: 'intermediate', isKeySkill: true },
      { name: 'JavaScript', level: 'intermediate', isKeySkill: true },
      { name: 'TypeScript', level: 'intermediate', isKeySkill: false },
      // 框架
      { name: 'Spring', level: 'intermediate', isKeySkill: false },
      { name: 'React', level: 'intermediate', isKeySkill: false },
      { name: 'Vue.js', level: 'intermediate', isKeySkill: false },
      // 数据库
      { name: 'MySQL', level: 'basic', isKeySkill: false },
      { name: 'PostgreSQL', level: 'basic', isKeySkill: false },
      { name: 'Redis', level: 'basic', isKeySkill: false },
    ];
    
    const lowerText = text.toLowerCase();
    return skillKeywords.filter(skill => 
      lowerText.includes(skill.name.toLowerCase())
    );
  }

  private isSkillMatch(candidateSkill: string, requiredSkill: string): boolean {
    return candidateSkill.toLowerCase().includes(requiredSkill.toLowerCase()) ||
           requiredSkill.toLowerCase().includes(candidateSkill.toLowerCase());
  }

  private calculateSkillLevelScore(candidateLevel: string, requiredLevel: string, yearsUsed?: number): number {
    const levelScores = {
      'beginner': 1,
      'intermediate': 2, 
      'advanced': 3,
      'expert': 4
    };
    
    const candidateScore = levelScores[candidateLevel as keyof typeof levelScores] || 1;
    const requiredScore = levelScores[requiredLevel as keyof typeof levelScores] || 2;
    
    let score = (candidateScore / requiredScore) * 100;
    
    // 考虑使用年限的加分
    if (yearsUsed && yearsUsed >= 3) {
      score = Math.min(score + 10, 100);
    }
    
    return Math.min(score, 100);
  }

  private extractRequiredYears(requirements: string): number {
    const yearMatches = requirements.match(/(\d+)年以上|(\d+)\+?\s*年/g);
    if (yearMatches) {
      const years = yearMatches.map(match => parseInt(match.match(/\d+/)?.[0] || '0'));
      return Math.max(...years);
    }
    return 0;
  }

  private isIndustryMatch(candidateIndustry: string, jobIndustry: string): boolean {
    // 简化的行业匹配逻辑
    const normalizedCandidate = candidateIndustry.toLowerCase();
    const normalizedJob = jobIndustry.toLowerCase();
    
    return normalizedCandidate.includes(normalizedJob) ||
           normalizedJob.includes(normalizedCandidate);
  }

  private isRoleMatch(candidateRole: string, jobTitle: string): boolean {
    // 简化的职位匹配逻辑
    const candidateKeywords = candidateRole.toLowerCase().split(/[\s\-\/]+/);
    const jobKeywords = jobTitle.toLowerCase().split(/[\s\-\/]+/);
    
    const commonKeywords = candidateKeywords.filter(keyword => 
      jobKeywords.some(jobKeyword => 
        keyword.includes(jobKeyword) || jobKeyword.includes(keyword)
      )
    );
    
    return commonKeywords.length >= 1;
  }

  private isLocationMatch(candidateLocation: string, jobLocation: string): boolean {
    // 简化的地点匹配逻辑
    return candidateLocation.toLowerCase().includes(jobLocation.toLowerCase()) ||
           jobLocation.toLowerCase().includes(candidateLocation.toLowerCase());
  }

  private extractRequiredDegree(requirements: string): string | null {
    if (requirements.includes('博士')) return 'doctorate';
    if (requirements.includes('硕士') || requirements.includes('研究生')) return 'master';
    if (requirements.includes('本科') || requirements.includes('学士')) return 'bachelor';
    if (requirements.includes('大专') || requirements.includes('专科')) return 'associate';
    return null;
  }

  private getHighestDegree(education: any[]): string | null {
    if (!education.length) return null;
    
    const degreeHierarchy = ['doctorate', 'master', 'bachelor', 'associate', 'high_school'];
    
    for (const degree of degreeHierarchy) {
      if (education.some(edu => edu.degree === degree)) {
        return degree;
      }
    }
    
    return null;
  }

  private compareDegreeLevel(candidateDegree: string | null, requiredDegree: string): number {
    if (!candidateDegree) return 20;
    
    const degreeScores = {
      'high_school': 1,
      'associate': 2,
      'bachelor': 3,
      'master': 4,
      'doctorate': 5
    };
    
    const candidateScore = degreeScores[candidateDegree as keyof typeof degreeScores] || 0;
    const requiredScore = degreeScores[requiredDegree as keyof typeof degreeScores] || 3;
    
    return Math.min((candidateScore / requiredScore) * 100, 100);
  }

  private calculateConfidence(resume: any, job: any, overallScore: number): number {
    // 基于数据完整性和分数一致性计算置信度
    let dataCompleteness = 0;
    
    // 简历数据完整性评估
    if (resume.skills?.length > 0) dataCompleteness += 20;
    if (resume.workExperience?.length > 0) dataCompleteness += 20;
    if (resume.education?.length > 0) dataCompleteness += 15;
    if (resume.yearsExp > 0) dataCompleteness += 15;
    if (resume.currentSalary > 0) dataCompleteness += 10;
    if (resume.expectedSalary > 0) dataCompleteness += 10;
    if (resume.preferredIndustries?.length > 0) dataCompleteness += 10;
    
    // 岗位信息完整性
    let jobCompleteness = 50;
    if (job.salaryMin && job.salaryMax) jobCompleteness += 20;
    if (job.industry) jobCompleteness += 15;
    if (job.location) jobCompleteness += 15;
    
    // 综合置信度
    const confidence = Math.min(
      (dataCompleteness * 0.6 + jobCompleteness * 0.4 + overallScore * 0.1) / 1.1,
      95
    );
    
    return Math.round(confidence);
  }

  private generateMatchReasons(resume: any, job: any, score: number): string[] {
    const reasons: string[] = [];
    
    if (score >= 80) {
      reasons.push('候选人技能与岗位要求高度匹配');
      reasons.push('工作经验符合岗位需求');
    } else if (score >= 60) {
      reasons.push('候选人具备大部分必要技能');
      reasons.push('经验水平基本符合要求');
    } else {
      reasons.push('候选人需要进一步技能培训');
      reasons.push('建议面试进一步了解');
    }
    
    return reasons;
  }
}

export const resumeMatchingService = new ResumeMatchingService();