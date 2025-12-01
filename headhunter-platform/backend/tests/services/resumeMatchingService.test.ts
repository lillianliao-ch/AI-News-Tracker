import { describe, beforeEach, afterEach, it, expect, jest } from '@jest/globals';
import { ResumeMatchingService } from '../../src/services/resumeMatchingService';
import { PrismaClient } from '@prisma/client';

// Mock Prisma
jest.mock('@prisma/client');
const mockPrisma = new PrismaClient() as jest.Mocked<PrismaClient>;

describe('ResumeMatchingService', () => {
  let service: ResumeMatchingService;
  
  beforeEach(() => {
    service = new ResumeMatchingService();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('技能匹配算法测试', () => {
    it('应该正确计算技能匹配分数 - 完全匹配', async () => {
      // 准备测试数据
      const mockResume = {
        id: 'resume-1',
        skills: [
          { name: 'Java', level: 'advanced', yearsUsed: 5, isKeySkill: true },
          { name: 'Spring', level: 'intermediate', yearsUsed: 3, isKeySkill: false },
          { name: 'MySQL', level: 'advanced', yearsUsed: 4, isKeySkill: false }
        ]
      };

      const mockJob = {
        id: 'job-1',
        title: 'Java开发工程师',
        requirements: '要求熟练掌握Java、Spring框架，熟悉MySQL数据库',
        description: '负责后端开发工作'
      };

      // 模拟技能提取
      const extractSkillsSpy = jest.spyOn(service as any, 'extractSkillsFromJobDescription')
        .mockResolvedValue([
          { name: 'Java', level: 'intermediate', isKeySkill: true },
          { name: 'Spring', level: 'basic', isKeySkill: false },
          { name: 'MySQL', level: 'intermediate', isKeySkill: false }
        ]);

      // 执行测试
      const result = await (service as any).calculateSkillsMatch(mockResume, mockJob);

      // 验证结果
      expect(result.score).toBeGreaterThan(85); // 高匹配度
      expect(result.matchedSkills).toHaveLength(3);
      expect(result.missingSkills).toHaveLength(0);
      
      // 验证关键技能匹配
      const javaSkill = result.matchedSkills.find(s => s.skill === 'Java');
      expect(javaSkill).toBeDefined();
      expect(javaSkill?.isKeySkill).toBe(true);
      expect(javaSkill?.score).toBeGreaterThan(90); // 技能等级超过要求
    });

    it('应该正确识别缺失技能', async () => {
      const mockResume = {
        skills: [
          { name: 'Java', level: 'intermediate', yearsUsed: 2 }
        ]
      };

      const mockJob = {
        requirements: '要求熟练掌握Java、Python、React技能'
      };

      jest.spyOn(service as any, 'extractSkillsFromJobDescription')
        .mockResolvedValue([
          { name: 'Java', level: 'intermediate', isKeySkill: true },
          { name: 'Python', level: 'intermediate', isKeySkill: true },
          { name: 'React', level: 'basic', isKeySkill: false }
        ]);

      const result = await (service as any).calculateSkillsMatch(mockResume, mockJob);

      expect(result.matchedSkills).toHaveLength(1);
      expect(result.missingSkills).toContain('Python');
      expect(result.missingSkills).toContain('React');
      expect(result.score).toBeLessThan(60); // 技能缺失较多
    });

    it('应该给关键技能更高权重', async () => {
      const mockResume = {
        skills: [
          { name: 'Java', level: 'expert', yearsUsed: 5 },
          { name: 'HTML', level: 'basic', yearsUsed: 1 }
        ]
      };

      const mockJob = {
        requirements: '核心要求Java技能，了解HTML即可'
      };

      jest.spyOn(service as any, 'extractSkillsFromJobDescription')
        .mockResolvedValue([
          { name: 'Java', level: 'advanced', isKeySkill: true },
          { name: 'HTML', level: 'basic', isKeySkill: false }
        ]);

      const result = await (service as any).calculateSkillsMatch(mockResume, mockJob);

      // Java作为关键技能应该获得更高的权重影响
      expect(result.score).toBeGreaterThan(80);
      
      const javaMatch = result.matchedSkills.find(s => s.skill === 'Java');
      expect(javaMatch?.isKeySkill).toBe(true);
    });
  });

  describe('经验匹配算法测试', () => {
    it('应该正确计算工作年限匹配', async () => {
      const mockResume = {
        yearsExp: 5,
        workExperience: [
          {
            position: 'Java开发工程师',
            industry: '互联网',
            company: 'ABC公司',
            startDate: '2019-01-01',
            endDate: '2024-01-01'
          }
        ]
      };

      const mockJob = {
        title: 'Java高级开发工程师',
        industry: '互联网',
        requirements: '要求3年以上Java开发经验'
      };

      // 模拟年限提取
      jest.spyOn(service as any, 'extractRequiredYears')
        .mockReturnValue(3);

      const result = await (service as any).calculateExperienceMatch(mockResume, mockJob);

      expect(result.score).toBeGreaterThan(80);
      expect(result.details.yearsMatch).toBe(true);
      expect(result.details.industryMatch).toBe(true);
      expect(result.details.roleMatch).toBe(true);
    });

    it('应该正确处理经验不足的情况', async () => {
      const mockResume = {
        yearsExp: 1,
        workExperience: [
          {
            position: '实习生',
            industry: '金融',
            company: 'XYZ银行'
          }
        ]
      };

      const mockJob = {
        title: '高级软件工程师',
        industry: '互联网',
        requirements: '要求5年以上开发经验'
      };

      jest.spyOn(service as any, 'extractRequiredYears')
        .mockReturnValue(5);

      const result = await (service as any).calculateExperienceMatch(mockResume, mockJob);

      expect(result.score).toBeLessThan(50);
      expect(result.details.yearsMatch).toBe(false);
      expect(result.details.industryMatch).toBe(false);
    });
  });

  describe('行业匹配算法测试', () => {
    it('应该正确匹配相同行业', () => {
      const mockResume = {
        workExperience: [
          { industry: '互联网' },
          { industry: '金融科技' }
        ],
        preferredIndustries: ['互联网', '人工智能']
      };

      const mockJob = {
        industry: '互联网'
      };

      const score = (service as any).calculateIndustryMatch(mockResume, mockJob);

      expect(score).toBe(100); // 有经验且有偏好
    });

    it('应该正确处理无行业要求的情况', () => {
      const mockResume = { workExperience: [] };
      const mockJob = { industry: null };

      const score = (service as any).calculateIndustryMatch(mockResume, mockJob);

      expect(score).toBe(50); // 无要求时给中等分
    });
  });

  describe('地点匹配算法测试', () => {
    it('应该正确匹配本地候选人', () => {
      const mockResume = {
        location: '北京市朝阳区',
        preferredLocations: ['北京', '上海']
      };

      const mockJob = {
        location: '北京市'
      };

      const score = (service as any).calculateLocationMatch(mockResume, mockJob);

      expect(score).toBe(100); // 当前地点和偏好都匹配
    });

    it('应该正确处理地点不匹配的情况', () => {
      const mockResume = {
        location: '上海市',
        preferredLocations: ['深圳', '杭州']
      };

      const mockJob = {
        location: '北京市'
      };

      const score = (service as any).calculateLocationMatch(mockResume, mockJob);

      expect(score).toBe(20); // 完全不匹配
    });
  });

  describe('薪资匹配算法测试', () => {
    it('应该正确评估薪资匹配度', () => {
      const mockResume = {
        currentSalary: 15000,
        expectedSalary: 20000
      };

      const mockJob = {
        salaryMin: 18000,
        salaryMax: 25000
      };

      const result = (service as any).calculateSalaryMatch(mockResume, mockJob);

      expect(result.score).toBeGreaterThan(80);
      expect(result.details.expectationMet).toBe(true);
      expect(result.details.currentVsOffered).toBeGreaterThan(0);
    });

    it('应该正确处理薪资期望过高的情况', () => {
      const mockResume = {
        expectedSalary: 30000
      };

      const mockJob = {
        salaryMin: 15000,
        salaryMax: 20000
      };

      const result = (service as any).calculateSalaryMatch(mockResume, mockJob);

      expect(result.score).toBeLessThan(50);
      expect(result.details.expectationMet).toBe(false);
    });
  });

  describe('综合匹配算法测试', () => {
    it('应该正确计算综合匹配分数', async () => {
      // 准备完整的测试数据
      const mockResume = {
        id: 'resume-1',
        candidateId: 'candidate-1',
        yearsExp: 5,
        currentSalary: 15000,
        expectedSalary: 20000,
        location: '北京市',
        preferredIndustries: ['互联网'],
        preferredLocations: ['北京'],
        skills: [
          { name: 'Java', level: 'advanced', yearsUsed: 5, isKeySkill: true }
        ],
        workExperience: [
          { position: 'Java开发工程师', industry: '互联网' }
        ],
        education: [
          { degree: 'bachelor', major: '计算机科学' }
        ]
      };

      const mockJob = {
        id: 'job-1',
        title: 'Java高级开发工程师',
        industry: '互联网',
        location: '北京市',
        salaryMin: 18000,
        salaryMax: 25000,
        requirements: '要求3年以上Java开发经验，本科以上学历',
        description: '负责Java后端开发'
      };

      // Mock 各个子方法
      jest.spyOn(service as any, 'calculateSkillsMatch')
        .mockResolvedValue({ score: 90, matchedSkills: [], missingSkills: [] });
      
      jest.spyOn(service as any, 'calculateExperienceMatch')
        .mockResolvedValue({ score: 85, details: {} });
      
      jest.spyOn(service as any, 'calculateIndustryMatch')
        .mockReturnValue(100);
      
      jest.spyOn(service as any, 'calculateLocationMatch')
        .mockReturnValue(100);
      
      jest.spyOn(service as any, 'calculateSalaryMatch')
        .mockReturnValue({ score: 80, details: {} });
      
      jest.spyOn(service as any, 'calculateEducationMatch')
        .mockReturnValue(90);

      jest.spyOn(service as any, 'calculateConfidence')
        .mockReturnValue(85);

      // 执行测试
      const result = await (service as any).calculateJobMatch(mockResume, mockJob);

      // 验证结果
      expect(result.overallScore).toBeGreaterThan(80);
      expect(result.jobId).toBe('job-1');
      expect(result.confidence).toBe(85);
      expect(result.dimensionScores).toBeDefined();
      expect(result.matchDetails).toBeDefined();
    });
  });

  describe('置信度计算测试', () => {
    it('应该基于数据完整性计算置信度', () => {
      const mockResume = {
        skills: [{ name: 'Java' }],
        workExperience: [{ position: 'Engineer' }],
        education: [{ degree: 'bachelor' }],
        yearsExp: 5,
        currentSalary: 15000,
        expectedSalary: 20000,
        preferredIndustries: ['tech']
      };

      const mockJob = {
        salaryMin: 15000,
        salaryMax: 25000,
        industry: 'tech',
        location: 'Beijing'
      };

      const confidence = (service as any).calculateConfidence(mockResume, mockJob, 85);

      expect(confidence).toBeGreaterThan(70);
      expect(confidence).toBeLessThanOrEqual(95);
    });

    it('应该对数据不完整的情况给出较低置信度', () => {
      const mockResume = {
        skills: [],
        workExperience: [],
        education: []
      };

      const mockJob = {};

      const confidence = (service as any).calculateConfidence(mockResume, mockJob, 60);

      expect(confidence).toBeLessThan(50);
    });
  });

  describe('边界情况测试', () => {
    it('应该处理空数据', async () => {
      const mockResume = {
        skills: [],
        workExperience: [],
        education: []
      };

      const mockJob = {
        requirements: '',
        description: ''
      };

      jest.spyOn(service as any, 'extractSkillsFromJobDescription')
        .mockResolvedValue([]);

      const result = await (service as any).calculateSkillsMatch(mockResume, mockJob);

      expect(result.score).toBe(0);
      expect(result.matchedSkills).toHaveLength(0);
      expect(result.missingSkills).toHaveLength(0);
    });

    it('应该处理无效输入', () => {
      expect(() => {
        (service as any).calculateLocationMatch(null, null);
      }).not.toThrow();

      expect(() => {
        (service as any).calculateIndustryMatch(undefined, undefined);
      }).not.toThrow();
    });
  });

  describe('性能测试', () => {
    it('单次匹配应该在合理时间内完成', async () => {
      const startTime = Date.now();
      
      const mockResume = {
        skills: Array.from({ length: 20 }, (_, i) => ({ 
          name: `skill-${i}`, 
          level: 'intermediate' 
        })),
        workExperience: Array.from({ length: 5 }, (_, i) => ({ 
          position: `position-${i}` 
        }))
      };

      const mockJob = {
        requirements: 'Multiple skills required',
        description: 'Complex job description'
      };

      jest.spyOn(service as any, 'extractSkillsFromJobDescription')
        .mockResolvedValue(Array.from({ length: 10 }, (_, i) => ({ 
          name: `skill-${i}`, 
          level: 'intermediate' 
        })));

      await (service as any).calculateSkillsMatch(mockResume, mockJob);

      const endTime = Date.now();
      expect(endTime - startTime).toBeLessThan(1000); // 应该在1秒内完成
    });
  });

  describe('辅助方法测试', () => {
    it('应该正确提取要求年限', () => {
      const testCases = [
        { input: '要求3年以上工作经验', expected: 3 },
        { input: '5年以上Java开发经验', expected: 5 },
        { input: '至少2年相关经验', expected: 2 },
        { input: '10+ years experience', expected: 10 },
        { input: '无经验要求', expected: 0 }
      ];

      testCases.forEach(({ input, expected }) => {
        const result = (service as any).extractRequiredYears(input);
        expect(result).toBe(expected);
      });
    });

    it('应该正确判断技能匹配', () => {
      const testCases = [
        { candidate: 'Java', required: 'Java', expected: true },
        { candidate: 'JavaScript', required: 'JS', expected: false },
        { candidate: 'React.js', required: 'React', expected: true },
        { candidate: 'Python', required: 'Java', expected: false }
      ];

      testCases.forEach(({ candidate, required, expected }) => {
        const result = (service as any).isSkillMatch(candidate, required);
        expect(result).toBe(expected);
      });
    });

    it('应该正确计算技能等级分数', () => {
      const testCases = [
        { candidateLevel: 'expert', requiredLevel: 'intermediate', yearsUsed: 5, expected: 100 },
        { candidateLevel: 'intermediate', requiredLevel: 'advanced', yearsUsed: 2, expected: 66 },
        { candidateLevel: 'beginner', requiredLevel: 'expert', yearsUsed: 1, expected: 25 }
      ];

      testCases.forEach(({ candidateLevel, requiredLevel, yearsUsed, expected }) => {
        const result = (service as any).calculateSkillLevelScore(candidateLevel, requiredLevel, yearsUsed);
        expect(result).toBeCloseTo(expected, 0);
      });
    });
  });
});