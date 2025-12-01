import axios from 'axios';
import { performance } from 'perf_hooks';

interface LoadTestConfig {
  baseUrl: string;
  concurrent: number;
  duration: number; // seconds
  rampUp: number; // seconds
}

interface LoadTestResult {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  minResponseTime: number;
  maxResponseTime: number;
  requestsPerSecond: number;
  errors: string[];
}

class LoadTestRunner {
  private config: LoadTestConfig;
  private results: LoadTestResult;
  private responseTimes: number[] = [];
  private errors: string[] = [];
  private isRunning = false;

  constructor(config: LoadTestConfig) {
    this.config = config;
    this.results = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      minResponseTime: Infinity,
      maxResponseTime: 0,
      requestsPerSecond: 0,
      errors: []
    };
  }

  async runLoadTest(): Promise<LoadTestResult> {
    this.isRunning = true;
    const startTime = performance.now();
    const endTime = startTime + (this.config.duration * 1000);
    
    // 生成测试数据
    const testCandidateId = 'test-candidate-123';
    const testJobId = 'test-job-456';
    
    const workers: Promise<void>[] = [];
    
    // 启动并发工作线程
    for (let i = 0; i < this.config.concurrent; i++) {
      const delay = (i / this.config.concurrent) * (this.config.rampUp * 1000);
      workers.push(this.workerThread(testCandidateId, testJobId, endTime, delay));
    }
    
    await Promise.all(workers);
    
    this.calculateResults(performance.now() - startTime);
    this.isRunning = false;
    
    return this.results;
  }

  private async workerThread(
    candidateId: string, 
    jobId: string, 
    endTime: number, 
    delay: number
  ): Promise<void> {
    // 等待ramp-up延迟
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    while (this.isRunning && performance.now() < endTime) {
      await this.makeRequest(candidateId, jobId);
      
      // 随机延迟以模拟真实用户行为
      const thinkTime = Math.random() * 100 + 50; // 50-150ms
      await new Promise(resolve => setTimeout(resolve, thinkTime));
    }
  }

  private async makeRequest(candidateId: string, jobId: string): Promise<void> {
    const requestStart = performance.now();
    
    try {
      // 随机选择API端点
      const endpoint = Math.random() < 0.5 
        ? '/api/v1/matching/jobs-for-candidate'
        : '/api/v1/matching/candidates-for-job';
      
      const payload = endpoint.includes('jobs-for-candidate')
        ? { candidateId, config: { thresholds: { maxResults: 20 } } }
        : { jobId, config: { thresholds: { maxResults: 20 } } };

      const response = await axios.post(`${this.config.baseUrl}${endpoint}`, payload, {
        timeout: 5000,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        }
      });

      const responseTime = performance.now() - requestStart;
      this.recordSuccess(responseTime);
      
    } catch (error: any) {
      const responseTime = performance.now() - requestStart;
      this.recordFailure(responseTime, error.message || 'Unknown error');
    }
  }

  private recordSuccess(responseTime: number): void {
    this.results.totalRequests++;
    this.results.successfulRequests++;
    this.responseTimes.push(responseTime);
    
    this.results.minResponseTime = Math.min(this.results.minResponseTime, responseTime);
    this.results.maxResponseTime = Math.max(this.results.maxResponseTime, responseTime);
  }

  private recordFailure(responseTime: number, error: string): void {
    this.results.totalRequests++;
    this.results.failedRequests++;
    this.errors.push(error);
    this.responseTimes.push(responseTime);
  }

  private calculateResults(totalDuration: number): void {
    if (this.responseTimes.length > 0) {
      this.results.averageResponseTime = 
        this.responseTimes.reduce((sum, time) => sum + time, 0) / this.responseTimes.length;
    }
    
    this.results.requestsPerSecond = this.results.totalRequests / (totalDuration / 1000);
    this.results.errors = [...new Set(this.errors)]; // 去重
    
    if (this.results.minResponseTime === Infinity) {
      this.results.minResponseTime = 0;
    }
  }
}

describe('Matching API Load Tests', () => {
  const baseUrl = process.env.TEST_API_URL || 'http://localhost:3001';
  
  beforeAll(async () => {
    // 检查服务是否可用
    try {
      await axios.get(`${baseUrl}/health`, { timeout: 5000 });
    } catch (error) {
      console.warn('API server not available, skipping load tests');
      return;
    }
  });

  test('should handle light load (10 concurrent users for 30 seconds)', async () => {
    const config: LoadTestConfig = {
      baseUrl,
      concurrent: 10,
      duration: 30,
      rampUp: 5
    };

    const runner = new LoadTestRunner(config);
    const results = await runner.runLoadTest();

    console.log('Light Load Test Results:', {
      ...results,
      averageResponseTime: `${results.averageResponseTime.toFixed(2)}ms`,
      requestsPerSecond: results.requestsPerSecond.toFixed(2)
    });

    // 性能断言
    expect(results.averageResponseTime).toBeLessThan(500); // 平均响应时间 < 500ms
    expect(results.maxResponseTime).toBeLessThan(2000);    // 最大响应时间 < 2s
    expect(results.successfulRequests / results.totalRequests).toBeGreaterThan(0.95); // 成功率 > 95%
    expect(results.requestsPerSecond).toBeGreaterThan(5);   // RPS > 5
  }, 60000);

  test('should handle medium load (25 concurrent users for 60 seconds)', async () => {
    const config: LoadTestConfig = {
      baseUrl,
      concurrent: 25,
      duration: 60,
      rampUp: 10
    };

    const runner = new LoadTestRunner(config);
    const results = await runner.runLoadTest();

    console.log('Medium Load Test Results:', {
      ...results,
      averageResponseTime: `${results.averageResponseTime.toFixed(2)}ms`,
      requestsPerSecond: results.requestsPerSecond.toFixed(2)
    });

    // 性能断言
    expect(results.averageResponseTime).toBeLessThan(1000); // 平均响应时间 < 1s
    expect(results.maxResponseTime).toBeLessThan(5000);     // 最大响应时间 < 5s
    expect(results.successfulRequests / results.totalRequests).toBeGreaterThan(0.90); // 成功率 > 90%
    expect(results.requestsPerSecond).toBeGreaterThan(10);  // RPS > 10
  }, 120000);

  test('should handle heavy load (50 concurrent users for 30 seconds)', async () => {
    const config: LoadTestConfig = {
      baseUrl,
      concurrent: 50,
      duration: 30,
      rampUp: 15
    };

    const runner = new LoadTestRunner(config);
    const results = await runner.runLoadTest();

    console.log('Heavy Load Test Results:', {
      ...results,
      averageResponseTime: `${results.averageResponseTime.toFixed(2)}ms`,
      requestsPerSecond: results.requestsPerSecond.toFixed(2)
    });

    // 性能断言（更宽松的要求）
    expect(results.averageResponseTime).toBeLessThan(2000);  // 平均响应时间 < 2s
    expect(results.maxResponseTime).toBeLessThan(10000);     // 最大响应时间 < 10s
    expect(results.successfulRequests / results.totalRequests).toBeGreaterThan(0.80); // 成功率 > 80%
    expect(results.requestsPerSecond).toBeGreaterThan(15);   // RPS > 15
  }, 90000);

  test('should perform spike test (sudden traffic increase)', async () => {
    // 第一阶段：正常负载
    const normalConfig: LoadTestConfig = {
      baseUrl,
      concurrent: 10,
      duration: 10,
      rampUp: 2
    };

    const normalRunner = new LoadTestRunner(normalConfig);
    const normalResults = await normalRunner.runLoadTest();

    // 第二阶段：突发负载
    const spikeConfig: LoadTestConfig = {
      baseUrl,
      concurrent: 100,
      duration: 15,
      rampUp: 1 // 快速上升
    };

    const spikeRunner = new LoadTestRunner(spikeConfig);
    const spikeResults = await spikeRunner.runLoadTest();

    console.log('Spike Test Results:', {
      normal: {
        ...normalResults,
        averageResponseTime: `${normalResults.averageResponseTime.toFixed(2)}ms`,
        requestsPerSecond: normalResults.requestsPerSecond.toFixed(2)
      },
      spike: {
        ...spikeResults,
        averageResponseTime: `${spikeResults.averageResponseTime.toFixed(2)}ms`,
        requestsPerSecond: spikeResults.requestsPerSecond.toFixed(2)
      }
    });

    // 系统应该能够在突发负载下保持基本功能
    expect(spikeResults.successfulRequests / spikeResults.totalRequests).toBeGreaterThan(0.70); // 成功率 > 70%
    expect(spikeResults.averageResponseTime).toBeLessThan(5000); // 平均响应时间 < 5s
  }, 60000);

  test('should handle stress test (find breaking point)', async () => {
    const stressLevels = [20, 40, 60, 80, 100];
    const results: any[] = [];

    for (const concurrent of stressLevels) {
      const config: LoadTestConfig = {
        baseUrl,
        concurrent,
        duration: 20,
        rampUp: 5
      };

      const runner = new LoadTestRunner(config);
      const result = await runner.runLoadTest();
      
      results.push({
        concurrent,
        successRate: result.successfulRequests / result.totalRequests,
        averageResponseTime: result.averageResponseTime,
        requestsPerSecond: result.requestsPerSecond
      });

      console.log(`Stress Level ${concurrent}:`, {
        successRate: `${(result.successfulRequests / result.totalRequests * 100).toFixed(1)}%`,
        averageResponseTime: `${result.averageResponseTime.toFixed(2)}ms`,
        requestsPerSecond: result.requestsPerSecond.toFixed(2)
      });

      // 如果成功率下降到50%以下，认为达到了极限
      if (result.successfulRequests / result.totalRequests < 0.5) {
        console.log(`Breaking point reached at ${concurrent} concurrent users`);
        break;
      }
    }

    // 至少应该能处理20个并发用户
    expect(results[0].successRate).toBeGreaterThan(0.8);
    
    // 输出压力测试总结
    console.log('Stress Test Summary:', results);
  }, 300000); // 5分钟超时

  test('should measure database connection pool performance', async () => {
    // 测试数据库连接池的性能
    const config: LoadTestConfig = {
      baseUrl,
      concurrent: 30,
      duration: 60,
      rampUp: 5
    };

    const runner = new LoadTestRunner(config);
    const results = await runner.runLoadTest();

    console.log('Database Connection Pool Test:', {
      ...results,
      averageResponseTime: `${results.averageResponseTime.toFixed(2)}ms`,
      requestsPerSecond: results.requestsPerSecond.toFixed(2)
    });

    // 数据库连接池应该能有效处理并发请求
    expect(results.successfulRequests / results.totalRequests).toBeGreaterThan(0.85);
    expect(results.averageResponseTime).toBeLessThan(1500);
    
    // 检查是否有连接超时错误
    const connectionErrors = results.errors.filter(error => 
      error.includes('timeout') || error.includes('connection')
    );
    expect(connectionErrors.length).toBeLessThan(results.errors.length * 0.1); // 连接错误 < 10%
  }, 120000);
});