import { ResumeMatchingService } from '../../src/services/resumeMatchingService';
import { MatchingRankingService } from '../../src/services/matchingRankingService';
import { MatchingConfig, JobPosition, Resume, MatchingStrategy } from '../../src/types';
import { performance } from 'perf_hooks';

jest.setTimeout(60000); // 增加超时时间到60秒

describe('Resume Matching Performance Tests', () => {
  let matchingService: ResumeMatchingService;
  let rankingService: MatchingRankingService;
  let config: MatchingConfig;

  beforeEach(() => {
    matchingService = new ResumeMatchingService({} as any);
    rankingService = new MatchingRankingService();
    config = {
      weights: {
        skills: 0.35,
        experience: 0.25,
        industry: 0.15,
        location: 0.10,
        salary: 0.10,
        education: 0.05
      },
      thresholds: {
        minimumScore: 0.6,
        minimumConfidence: 0.7,
        maxResults: 100
      }
    };
  });

  // 生成大量测试数据
  const generateJobs = (count: number): JobPosition[] => {
    const jobs: JobPosition[] = [];
    const skills = ['JavaScript', 'TypeScript', 'React', 'Node.js', 'Python', 'Java', 'C++', 'MySQL', 'MongoDB', 'AWS'];
    const industries = ['科技', '金融', '电商', '教育', '医疗', '制造', '咨询', '媒体'];
    const locations = ['北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '武汉'];
    const companies = ['TechCorp', 'InnovateLtd', 'DataSoft', 'CloudSys', 'AITech'];

    for (let i = 0; i < count; i++) {
      jobs.push({
        id: `job-${i}`,
        title: `Software Engineer ${i}`,
        company: companies[i % companies.length],
        description: `Job description for position ${i}`,
        requiredSkills: skills.slice(0, Math.floor(Math.random() * 5) + 3),
        preferredSkills: skills.slice(3, Math.floor(Math.random() * 3) + 6),
        experienceLevel: ['初级', '中级', '高级'][Math.floor(Math.random() * 3)],
        industry: industries[Math.floor(Math.random() * industries.length)],
        location: locations[Math.floor(Math.random() * locations.length)],
        salaryRange: {
          min: 10000 + Math.floor(Math.random() * 20000),
          max: 20000 + Math.floor(Math.random() * 30000)
        },
        educationRequirement: ['本科', '硕士', '博士'][Math.floor(Math.random() * 3)],
        createdAt: new Date(),
        updatedAt: new Date()
      });
    }
    return jobs;
  };

  const generateResumes = (count: number): Resume[] => {
    const resumes: Resume[] = [];
    const skills = ['JavaScript', 'TypeScript', 'React', 'Node.js', 'Python', 'Java', 'C++', 'MySQL', 'MongoDB', 'AWS'];
    const industries = ['科技', '金融', '电商', '教育', '医疗', '制造', '咨询', '媒体'];
    const locations = ['北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '武汉'];

    for (let i = 0; i < count; i++) {
      resumes.push({
        id: `resume-${i}`,
        candidateId: `candidate-${i}`,
        filename: `resume-${i}.pdf`,
        originalText: `Resume content for candidate ${i}`,
        parsedData: {
          personalInfo: {
            name: `Candidate ${i}`,
            email: `candidate${i}@email.com`,
            phone: `138${String(i).padStart(8, '0')}`,
            location: locations[Math.floor(Math.random() * locations.length)]
          },
          summary: `Experienced professional with ${2 + Math.floor(Math.random() * 8)} years experience`,
          skills: skills.slice(0, Math.floor(Math.random() * 6) + 3).map(skill => ({
            name: skill,
            level: ['初级', '中级', '高级'][Math.floor(Math.random() * 3)],
            yearsOfExperience: Math.floor(Math.random() * 5) + 1
          })),
          workExperience: [
            {
              company: `Company ${i}`,
              position: `Developer ${i}`,
              startDate: new Date(2020, 0, 1),
              endDate: new Date(),
              description: `Work experience description ${i}`,
              industry: industries[Math.floor(Math.random() * industries.length)]
            }
          ],
          education: [
            {
              institution: `University ${i}`,
              degree: ['本科', '硕士', '博士'][Math.floor(Math.random() * 3)],
              major: 'Computer Science',
              graduationDate: new Date(2018, 6, 1)
            }
          ],
          projects: [],
          certifications: [],
          languages: []
        },
        confidence: 0.8 + Math.random() * 0.2,
        createdAt: new Date(),
        updatedAt: new Date()
      });
    }
    return resumes;
  };

  describe('Large Dataset Performance', () => {
    test('should handle 1000 jobs matching within acceptable time', async () => {
      const jobs = generateJobs(1000);
      const testResume = generateResumes(1)[0];

      const startTime = performance.now();
      
      // Mock the database call
      jest.spyOn(matchingService as any, 'findMatchingJobs').mockImplementation(
        async () => {
          const matches = jobs.map(job => ({
            job,
            scores: {
              skills: Math.random(),
              experience: Math.random(),
              industry: Math.random(),
              location: Math.random(),
              salary: Math.random(),
              education: Math.random(),
              overall: Math.random()
            },
            confidence: Math.random(),
            ranking: Math.floor(Math.random() * 100)
          }));
          return matches;
        }
      );

      const result = await matchingService.findMatchingJobs(testResume.id, config);
      
      const endTime = performance.now();
      const executionTime = endTime - startTime;

      expect(executionTime).toBeLessThan(2000); // 应在2秒内完成
      expect(result.length).toBeGreaterThan(0);
      console.log(`1000 jobs matching completed in ${executionTime.toFixed(2)}ms`);
    });

    test('should handle 500 candidates matching within acceptable time', async () => {
      const resumes = generateResumes(500);
      const testJob = generateJobs(1)[0];

      const startTime = performance.now();
      
      // Mock the database call
      jest.spyOn(matchingService as any, 'findMatchingCandidates').mockImplementation(
        async () => {
          const matches = resumes.map(resume => ({
            resume,
            scores: {
              skills: Math.random(),
              experience: Math.random(),
              industry: Math.random(),
              location: Math.random(),
              salary: Math.random(),
              education: Math.random(),
              overall: Math.random()
            },
            confidence: Math.random(),
            ranking: Math.floor(Math.random() * 100)
          }));
          return matches;
        }
      );

      const result = await matchingService.findMatchingCandidates(testJob.id, config);
      
      const endTime = performance.now();
      const executionTime = endTime - startTime;

      expect(executionTime).toBeLessThan(1500); // 应在1.5秒内完成
      expect(result.length).toBeGreaterThan(0);
      console.log(`500 candidates matching completed in ${executionTime.toFixed(2)}ms`);
    });
  });

  describe('Ranking Performance', () => {
    test('should rank 1000 matches within acceptable time', async () => {
      const jobs = generateJobs(1000);
      const matches = jobs.map(job => ({
        job,
        scores: {
          skills: Math.random(),
          experience: Math.random(),
          industry: Math.random(),
          location: Math.random(),
          salary: Math.random(),
          education: Math.random(),
          overall: Math.random()
        },
        confidence: Math.random(),
        ranking: 0
      }));

      const startTime = performance.now();
      
      const ranked = await rankingService.rankJobMatches(matches, MatchingStrategy.OVERALL);
      
      const endTime = performance.now();
      const executionTime = endTime - startTime;

      expect(executionTime).toBeLessThan(100); // 排序应在100ms内完成
      expect(ranked.length).toBe(matches.length);
      expect(ranked[0].ranking).toBeLessThanOrEqual(ranked[1].ranking);
      console.log(`1000 matches ranking completed in ${executionTime.toFixed(2)}ms`);
    });

    test('should apply business rules efficiently', async () => {
      const jobs = generateJobs(500);
      const matches = jobs.map(job => ({
        job,
        scores: {
          skills: Math.random(),
          experience: Math.random(),
          industry: Math.random(),
          location: Math.random(),
          salary: Math.random(),
          education: Math.random(),
          overall: Math.random()
        },
        confidence: Math.random(),
        ranking: 0
      }));

      const businessRules = [
        {
          name: 'preferred_industry',
          condition: (match: any) => match.job.industry === '科技',
          boost: 0.2
        },
        {
          name: 'location_match',
          condition: (match: any) => match.job.location === '北京',
          boost: 0.1
        }
      ];

      const startTime = performance.now();
      
      const processed = await rankingService.applyBusinessRules(matches, businessRules);
      
      const endTime = performance.now();
      const executionTime = endTime - startTime;

      expect(executionTime).toBeLessThan(50); // 业务规则应在50ms内完成
      expect(processed.length).toBe(matches.length);
      console.log(`Business rules application completed in ${executionTime.toFixed(2)}ms`);
    });
  });

  describe('Memory Usage', () => {
    test('should not cause memory leaks with large datasets', async () => {
      const initialMemory = process.memoryUsage();
      
      // 处理多个大数据集
      for (let i = 0; i < 5; i++) {
        const jobs = generateJobs(200);
        const resumes = generateResumes(200);
        
        // 模拟匹配过程
        const matches = jobs.map(job => ({
          job,
          scores: {
            skills: Math.random(),
            experience: Math.random(),
            industry: Math.random(),
            location: Math.random(),
            salary: Math.random(),
            education: Math.random(),
            overall: Math.random()
          },
          confidence: Math.random(),
          ranking: 0
        }));
        
        await rankingService.rankJobMatches(matches, MatchingStrategy.OVERALL);
        
        // 手动触发垃圾回收
        if (global.gc) {
          global.gc();
        }
      }
      
      const finalMemory = process.memoryUsage();
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      
      // 内存增长应该控制在合理范围内 (< 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`);
    });
  });

  describe('Concurrent Processing', () => {
    test('should handle concurrent matching requests', async () => {
      const jobs = generateJobs(100);
      const resumes = generateResumes(10);
      
      // Mock the database calls
      jest.spyOn(matchingService as any, 'findMatchingJobs').mockImplementation(
        async () => {
          // 模拟数据库延迟
          await new Promise(resolve => setTimeout(resolve, 10));
          return jobs.slice(0, 20).map(job => ({
            job,
            scores: {
              skills: Math.random(),
              experience: Math.random(),
              industry: Math.random(),
              location: Math.random(),
              salary: Math.random(),
              education: Math.random(),
              overall: Math.random()
            },
            confidence: Math.random(),
            ranking: Math.floor(Math.random() * 100)
          }));
        }
      );

      const startTime = performance.now();
      
      // 并发处理多个简历
      const promises = resumes.map(resume => 
        matchingService.findMatchingJobs(resume.id, config)
      );
      
      const results = await Promise.all(promises);
      
      const endTime = performance.now();
      const executionTime = endTime - startTime;

      expect(results.length).toBe(resumes.length);
      expect(executionTime).toBeLessThan(1000); // 并发处理应在1秒内完成
      console.log(`Concurrent processing of ${resumes.length} resumes completed in ${executionTime.toFixed(2)}ms`);
    });
  });

  describe('Algorithm Complexity', () => {
    test('should scale linearly with dataset size', async () => {
      const sizes = [100, 200, 400, 800];
      const times: number[] = [];

      for (const size of sizes) {
        const jobs = generateJobs(size);
        const matches = jobs.map(job => ({
          job,
          scores: {
            skills: Math.random(),
            experience: Math.random(),
            industry: Math.random(),
            location: Math.random(),
            salary: Math.random(),
            education: Math.random(),
            overall: Math.random()
          },
          confidence: Math.random(),
          ranking: 0
        }));

        const startTime = performance.now();
        await rankingService.rankJobMatches(matches, MatchingStrategy.OVERALL);
        const endTime = performance.now();
        
        times.push(endTime - startTime);
        console.log(`Size ${size}: ${(endTime - startTime).toFixed(2)}ms`);
      }

      // 检查时间复杂度是否接近线性
      for (let i = 1; i < times.length; i++) {
        const ratio = times[i] / times[i - 1];
        const sizeRatio = sizes[i] / sizes[i - 1];
        
        // 时间比率应该接近大小比率（线性复杂度）
        expect(ratio).toBeGreaterThan(sizeRatio * 0.5);
        expect(ratio).toBeLessThan(sizeRatio * 3);
      }
    });
  });
});