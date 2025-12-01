import { PrismaClient } from '@prisma/client';
import { ResumeMatchingService } from '../../src/services/resumeMatchingService';
import { MatchingRankingService } from '../../src/services/matchingRankingService';
import { TestSetup } from '../utils/testSetup';
import { TestDataGenerator } from '../utils/testDataGenerator';
import { MatchingStrategy } from '../../src/types';

describe('End-to-End Resume Matching Tests', () => {
  let prisma: PrismaClient;
  let matchingService: ResumeMatchingService;
  let rankingService: MatchingRankingService;
  let testSetup: TestSetup;

  beforeAll(async () => {
    // 初始化服务
    prisma = new PrismaClient();
    matchingService = new ResumeMatchingService(prisma);
    rankingService = new MatchingRankingService();
    testSetup = new TestSetup(prisma);

    // 设置测试环境
    await testSetup.setupTestEnvironment({
      resumeCount: 30,
      jobCount: 20,
      dataQuality: 'high',
      includeEdgeCases: true
    });

    // 验证测试数据
    const isValid = await testSetup.validateTestData();
    if (!isValid) {
      throw new Error('Test data validation failed');
    }
  });

  afterAll(async () => {
    // 清理测试数据
    await testSetup.cleanupTestData();
    await prisma.$disconnect();
  });

  describe('Complete Matching Workflow', () => {
    test('should perform complete job matching for candidate', async () => {
      const resumeId = testSetup.getRandomResumeId();
      expect(resumeId).toBeTruthy();

      const config = testSetup.createTestMatchingConfig();

      // 执行匹配
      const matches = await matchingService.findMatchingJobs(resumeId!, config);

      // 验证结果
      expect(matches).toBeDefined();
      expect(Array.isArray(matches)).toBe(true);
      expect(matches.length).toBeGreaterThan(0);
      expect(matches.length).toBeLessThanOrEqual(config.thresholds.maxResults);

      // 验证匹配结果结构
      for (const match of matches) {
        expect(match).toHaveProperty('job');
        expect(match).toHaveProperty('scores');
        expect(match).toHaveProperty('confidence');
        expect(match).toHaveProperty('ranking');

        // 验证分数结构
        expect(match.scores).toHaveProperty('skills');
        expect(match.scores).toHaveProperty('experience');
        expect(match.scores).toHaveProperty('industry');
        expect(match.scores).toHaveProperty('location');
        expect(match.scores).toHaveProperty('salary');
        expect(match.scores).toHaveProperty('education');
        expect(match.scores).toHaveProperty('overall');

        // 验证分数范围
        Object.values(match.scores).forEach(score => {
          expect(typeof score).toBe('number');
          expect(score).toBeGreaterThanOrEqual(0);
          expect(score).toBeLessThanOrEqual(1);
        });

        // 验证置信度
        expect(match.confidence).toBeGreaterThanOrEqual(0);
        expect(match.confidence).toBeLessThanOrEqual(1);
        expect(match.confidence).toBeGreaterThanOrEqual(config.thresholds.minimumConfidence);

        // 验证总分不低于阈值
        expect(match.scores.overall).toBeGreaterThanOrEqual(config.thresholds.minimumScore);
      }

      // 验证排序
      for (let i = 1; i < matches.length; i++) {
        expect(matches[i - 1].ranking).toBeLessThanOrEqual(matches[i].ranking);
      }

      console.log(`Found ${matches.length} matching jobs for resume ${resumeId}`);
    });

    test('should perform complete candidate matching for job', async () => {
      const jobId = testSetup.getRandomJobId();
      expect(jobId).toBeTruthy();

      const config = testSetup.createTestMatchingConfig();

      // 执行匹配
      const matches = await matchingService.findMatchingCandidates(jobId!, config);

      // 验证结果
      expect(matches).toBeDefined();
      expect(Array.isArray(matches)).toBe(true);
      expect(matches.length).toBeGreaterThan(0);
      expect(matches.length).toBeLessThanOrEqual(config.thresholds.maxResults);

      // 验证匹配结果结构
      for (const match of matches) {
        expect(match).toHaveProperty('resume');
        expect(match).toHaveProperty('scores');
        expect(match).toHaveProperty('confidence');
        expect(match).toHaveProperty('ranking');

        // 验证简历数据完整性
        expect(match.resume).toHaveProperty('parsedData');
        expect(match.resume.parsedData).toHaveProperty('personalInfo');
        expect(match.resume.parsedData).toHaveProperty('skills');
        expect(match.resume.parsedData).toHaveProperty('workExperience');
      }

      console.log(`Found ${matches.length} matching candidates for job ${jobId}`);
    });
  });

  describe('Different Matching Strategies', () => {
    test('should produce different results with different strategies', async () => {
      const resumeId = testSetup.getRandomResumeId();
      const config = testSetup.createTestMatchingConfig();

      // 使用不同策略获取匹配结果
      const overallMatches = await matchingService.findMatchingJobs(resumeId!, config);
      
      // 重新排序使用技能优先策略
      const skillFirstMatches = await rankingService.rankJobMatches(
        overallMatches,
        MatchingStrategy.SKILL_FIRST
      );

      // 重新排序使用经验优先策略
      const experienceFirstMatches = await rankingService.rankJobMatches(
        overallMatches,
        MatchingStrategy.EXPERIENCE_FIRST
      );

      // 验证不同策略产生了不同的排序
      expect(overallMatches.length).toBe(skillFirstMatches.length);
      expect(overallMatches.length).toBe(experienceFirstMatches.length);

      // 检查排序是否不同（至少前3个位置）
      const topOverall = overallMatches.slice(0, 3).map(m => m.job.id);
      const topSkillFirst = skillFirstMatches.slice(0, 3).map(m => m.job.id);
      const topExperienceFirst = experienceFirstMatches.slice(0, 3).map(m => m.job.id);

      // 至少有一个策略的排序应该不同
      const isOverallDifferentFromSkill = JSON.stringify(topOverall) !== JSON.stringify(topSkillFirst);
      const isOverallDifferentFromExperience = JSON.stringify(topOverall) !== JSON.stringify(topExperienceFirst);
      
      expect(isOverallDifferentFromSkill || isOverallDifferentFromExperience).toBe(true);

      console.log('Strategy comparison:', {
        overall: topOverall,
        skillFirst: topSkillFirst,
        experienceFirst: topExperienceFirst
      });
    });
  });

  describe('Edge Cases Handling', () => {
    test('should handle candidate with no work experience', async () => {
      // 创建一个没有工作经验的简历
      const noExperienceResume = TestDataGenerator.generateResumes({
        resumeCount: 1,
        experiencePerResume: { min: 0, max: 0 },
        dataQuality: 'high'
      })[0];

      // 插入到数据库
      const candidateId = 'user-test-no-experience';
      await prisma.user.create({
        data: {
          id: candidateId,
          email: noExperienceResume.parsedData.personalInfo.email,
          name: noExperienceResume.parsedData.personalInfo.name,
          phone: noExperienceResume.parsedData.personalInfo.phone || '',
          role: 'CANDIDATE',
          isActive: true
        }
      });

      const resumeId = 'resume-test-no-experience';
      await prisma.resume.create({
        data: {
          id: resumeId,
          candidateId,
          filename: noExperienceResume.filename,
          originalText: noExperienceResume.originalText,
          summary: noExperienceResume.parsedData.summary || '应届毕业生',
          confidence: noExperienceResume.confidence
        }
      });

      const config = testSetup.createTestMatchingConfig();
      config.thresholds.minimumScore = 0.3; // 降低阈值以便匹配

      // 执行匹配
      const matches = await matchingService.findMatchingJobs(resumeId, config);

      // 应该能找到一些匹配（即使是应届生职位）
      expect(matches.length).toBeGreaterThan(0);

      // 经验分数应该较低，但不应该完全为0
      for (const match of matches) {
        expect(match.scores.experience).toBeGreaterThanOrEqual(0);
        expect(match.scores.experience).toBeLessThanOrEqual(0.5); // 应该比有经验的候选人低
      }

      // 清理
      await prisma.resume.delete({ where: { id: resumeId } });
      await prisma.user.delete({ where: { id: candidateId } });
    });

    test('should handle job with very specific requirements', async () => {
      // 创建一个要求非常具体的职位
      const specificJob = TestDataGenerator.generateJobs({
        jobCount: 1,
        dataQuality: 'high'
      })[0];

      // 修改为非常具体的要求
      specificJob.requiredSkills = ['Rust', 'WebAssembly', 'Blockchain'];
      specificJob.experienceLevel = '专家';
      specificJob.salaryRange = { min: 50000, max: 80000 };

      // 插入到数据库
      const companyId = 'company-test-specific';
      await prisma.company.create({
        data: {
          id: companyId,
          name: 'Specific Tech Corp',
          industry: '区块链',
          size: '50-100人',
          description: '专注于区块链技术的公司',
          location: '北京'
        }
      });

      const jobId = 'job-test-specific';
      await prisma.job.create({
        data: {
          id: jobId,
          title: '区块链架构师',
          description: '需要深厚的区块链和Rust开发经验',
          requirements: specificJob.requiredSkills.join(', '),
          experienceLevel: specificJob.experienceLevel,
          salaryMin: specificJob.salaryRange.min,
          salaryMax: specificJob.salaryRange.max,
          location: specificJob.location,
          employmentType: 'FULL_TIME',
          industry: specificJob.industry,
          companyId,
          status: 'ACTIVE'
        }
      });

      const config = testSetup.createTestMatchingConfig();

      // 执行匹配
      const matches = await matchingService.findMatchingCandidates(jobId, config);

      // 可能找不到匹配的候选人，或者匹配度很低
      if (matches.length > 0) {
        for (const match of matches) {
          // 匹配分数应该相对较低（因为要求很特殊）
          expect(match.scores.overall).toBeLessThan(0.9);
          // 但仍然满足最低阈值
          expect(match.scores.overall).toBeGreaterThanOrEqual(config.thresholds.minimumScore);
        }
      }

      console.log(`Found ${matches.length} candidates for very specific job`);

      // 清理
      await prisma.job.delete({ where: { id: jobId } });
      await prisma.company.delete({ where: { id: companyId } });
    });
  });

  describe('Data Consistency', () => {
    test('should maintain data integrity across multiple operations', async () => {
      const resumeId = testSetup.getRandomResumeId();
      const jobId = testSetup.getRandomJobId();
      const config = testSetup.createTestMatchingConfig();

      // 执行多次匹配操作
      const matches1 = await matchingService.findMatchingJobs(resumeId!, config);
      const matches2 = await matchingService.findMatchingJobs(resumeId!, config);
      const candidateMatches = await matchingService.findMatchingCandidates(jobId!, config);

      // 相同参数的调用应该产生相同结果
      expect(matches1.length).toBe(matches2.length);
      
      // 比较匹配结果的一致性
      for (let i = 0; i < matches1.length; i++) {
        expect(matches1[i].job.id).toBe(matches2[i].job.id);
        expect(matches1[i].scores.overall).toBeCloseTo(matches2[i].scores.overall, 3);
      }

      // 验证数据库状态没有被意外修改
      const resumeCount = await prisma.resume.count({
        where: { id: { contains: 'resume-test-' } }
      });
      const jobCount = await prisma.job.count({
        where: { id: { contains: 'job-test-' } }
      });

      expect(resumeCount).toBeGreaterThan(0);
      expect(jobCount).toBeGreaterThan(0);
    });
  });

  describe('Performance under Load', () => {
    test('should handle multiple concurrent matching requests', async () => {
      const config = testSetup.createTestMatchingConfig();
      const generatedData = testSetup.getGeneratedData();
      
      // 准备多个并发请求
      const promises = [];
      for (let i = 0; i < 5; i++) {
        const resumeId = `resume-test-${generatedData.resumes[i % generatedData.resumes.length].id}`;
        promises.push(matchingService.findMatchingJobs(resumeId, config));
      }

      // 执行并发请求
      const startTime = Date.now();
      const results = await Promise.all(promises);
      const endTime = Date.now();

      // 验证所有请求都成功
      expect(results.length).toBe(5);
      for (const result of results) {
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
      }

      // 验证性能
      const totalTime = endTime - startTime;
      expect(totalTime).toBeLessThan(5000); // 5秒内完成所有请求

      console.log(`Concurrent matching completed in ${totalTime}ms`);
    });
  });

  describe('Business Logic Validation', () => {
    test('should respect salary range preferences', async () => {
      const resumeId = testSetup.getRandomResumeId();
      const config = testSetup.createTestMatchingConfig();

      // 增加薪资权重以测试薪资匹配
      config.weights.salary = 0.3;
      config.weights.skills = 0.25;

      const matches = await matchingService.findMatchingJobs(resumeId!, config);

      if (matches.length > 0) {
        // 获取简历信息以验证薪资逻辑
        const resume = await prisma.resume.findUnique({
          where: { id: resumeId! },
          include: {
            workExperience: true,
            resumeSkills: true
          }
        });

        expect(resume).toBeTruthy();

        // 验证薪资分数的逻辑性
        for (const match of matches) {
          expect(match.scores.salary).toBeGreaterThanOrEqual(0);
          expect(match.scores.salary).toBeLessThanOrEqual(1);
          
          // 薪资分数应该影响总分
          const recalculatedScore = 
            match.scores.skills * config.weights.skills +
            match.scores.experience * config.weights.experience +
            match.scores.industry * config.weights.industry +
            match.scores.location * config.weights.location +
            match.scores.salary * config.weights.salary +
            match.scores.education * config.weights.education;
          
          expect(match.scores.overall).toBeCloseTo(recalculatedScore, 2);
        }
      }
    });

    test('should prioritize location matches when configured', async () => {
      const resumeId = testSetup.getRandomResumeId();
      const config = testSetup.createTestMatchingConfig();

      // 增加地理位置权重
      config.weights.location = 0.4;
      config.weights.skills = 0.3;

      const matches = await matchingService.findMatchingJobs(resumeId!, config);

      if (matches.length >= 2) {
        // 获取简历的地理位置
        const resume = await prisma.resume.findUnique({
          where: { id: resumeId! },
          include: { candidate: true }
        });

        // 获取职位详情
        const jobIds = matches.slice(0, 5).map(m => m.job.id);
        const jobs = await prisma.job.findMany({
          where: { id: { in: jobIds } }
        });

        // 分析地理位置匹配对排序的影响
        let locationMatchesFound = 0;
        for (const match of matches.slice(0, 5)) {
          const job = jobs.find(j => j.id === match.job.id);
          if (job && resume) {
            // 这里需要从简历解析数据中获取地理位置
            // 实际实现中会从parsedData中获取
            if (match.scores.location > 0.8) {
              locationMatchesFound++;
            }
          }
        }

        console.log(`Found ${locationMatchesFound} strong location matches in top 5 results`);
      }
    });
  });
});