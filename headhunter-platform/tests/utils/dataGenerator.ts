import { PrismaClient } from '@prisma/client';
import { testUsers, testCompanies, testCompanyClients, testJobs, testCandidates } from '../fixtures/testData';
import { TestHelper } from './testHelper';

export class TestDataGenerator {
  private prisma: PrismaClient;
  private testHelper: TestHelper;

  constructor(prisma: PrismaClient, testHelper: TestHelper) {
    this.prisma = prisma;
    this.testHelper = testHelper;
  }

  async generateFullTestDataset(): Promise<{
    users: any[];
    companies: any[];
    companyClients: any[];
    jobs: any[];
    candidates: any[];
    submissions: any[];
    permissions: any[];
    notifications: any[];
    messages: any[];
  }> {
    console.log('🏗️  Generating comprehensive test dataset...');

    // 1. Create Users
    console.log('👥 Creating users...');
    const users = await this.createUsers();

    // 2. Create Companies
    console.log('🏢 Creating companies...');
    const companies = await this.createCompanies();

    // 3. Create Company Clients
    console.log('🏬 Creating company clients...');
    const companyClients = await this.createCompanyClients();

    // 4. Create Jobs
    console.log('💼 Creating jobs...');
    const jobs = await this.createJobs(users, companyClients);

    // 5. Create Candidates
    console.log('👤 Creating candidates...');
    const candidates = await this.createCandidates(users);

    // 6. Create Submissions
    console.log('📄 Creating candidate submissions...');
    const submissions = await this.createSubmissions(candidates, jobs, users);

    // 7. Create Job Permissions (Sharing)
    console.log('🔐 Creating job permissions...');
    const permissions = await this.createJobPermissions(jobs, users);

    // 8. Create Notifications
    console.log('🔔 Creating notifications...');
    const notifications = await this.createNotifications(users, jobs, candidates);

    // 9. Create Messages
    console.log('💬 Creating messages...');
    const messages = await this.createMessages(users, jobs, candidates);

    console.log('✅ Test dataset generation completed!');

    return {
      users,
      companies,
      companyClients,
      jobs,
      candidates,
      submissions,
      permissions,
      notifications,
      messages,
    };
  }

  private async createUsers(): Promise<any[]> {
    const users = [];

    // Create main test users
    for (const [key, userData] of Object.entries(testUsers)) {
      const { user } = await this.testHelper.createTestUser(userData);
      users.push(user);
    }

    // Create additional users for scaling tests
    const additionalUsers = [
      {
        username: 'consultant_wang',
        email: 'wang@techcorp.com',
        phone: '+86-13800001001',
        password: 'consultant123',
        role: 'consultant',
      },
      {
        username: 'consultant_li',
        email: 'li@innovationlabs.com',
        phone: '+86-13800001002',
        password: 'consultant123',
        role: 'consultant',
      },
      {
        username: 'soho_chen',
        email: 'chen@freelance.com',
        phone: '+86-13800001003',
        password: 'soho123456',
        role: 'soho',
      },
      {
        username: 'soho_liu',
        email: 'liu@independent.com',
        phone: '+86-13800001004',
        password: 'soho123456',
        role: 'soho',
      },
    ];

    for (const userData of additionalUsers) {
      const { user } = await this.testHelper.createTestUser(userData);
      users.push(user);
    }

    return users;
  }

  private async createCompanies(): Promise<any[]> {
    const companies = [];

    for (const companyData of testCompanies) {
      const company = await this.testHelper.createTestCompany(companyData);
      companies.push(company);
    }

    return companies;
  }

  private async createCompanyClients(): Promise<any[]> {
    const clients = [];

    for (const clientData of testCompanyClients) {
      const client = await this.testHelper.createTestCompanyClient(clientData);
      clients.push(client);
    }

    // Create additional clients
    const additionalClients = [
      {
        name: '美团',
        industry: 'Food Delivery',
        location: 'Beijing',
        description: 'Leading food delivery platform',
      },
      {
        name: '滴滴出行',
        industry: 'Transportation',
        location: 'Beijing',
        description: 'Ride-hailing and transportation platform',
      },
      {
        name: '小红书',
        industry: 'Social Commerce',
        location: 'Shanghai',
        description: 'Social commerce and lifestyle platform',
      },
    ];

    for (const clientData of additionalClients) {
      const client = await this.testHelper.createTestCompanyClient(clientData);
      clients.push(client);
    }

    return clients;
  }

  private async createJobs(users: any[], companyClients: any[]): Promise<any[]> {
    const jobs = [];
    const publishers = users.filter(u => ['consultant', 'soho'].includes(u.role));

    // Create jobs from test data
    for (let i = 0; i < testJobs.length; i++) {
      const jobData = testJobs[i];
      const publisher = publishers[i % publishers.length];
      const companyClient = companyClients[i % companyClients.length];

      const job = await this.testHelper.createTestJob({
        ...jobData,
        publisherId: publisher.id,
        companyClientId: companyClient.id,
      });
      jobs.push(job);
    }

    // Create additional jobs for variety
    const additionalJobs = [
      {
        title: '资深DevOps工程师',
        industry: 'Technology',
        location: 'Shenzhen',
        salaryMin: 350000,
        salaryMax: 650000,
        description: '负责容器化部署、CI/CD流水线建设和云基础设施管理',
        requirements: '5年以上DevOps经验；熟练掌握Docker、Kubernetes；有AWS/阿里云经验',
      },
      {
        title: 'UI/UX设计师',
        industry: 'Design',
        location: 'Hangzhou',
        salaryMin: 200000,
        salaryMax: 400000,
        description: '负责产品界面设计和用户体验优化',
        requirements: '3年以上设计经验；熟练使用Figma、Sketch；有移动端设计经验',
      },
      {
        title: '数据科学家',
        industry: 'Data Science',
        location: 'Beijing',
        salaryMin: 450000,
        salaryMax: 800000,
        description: '负责数据挖掘、机器学习模型开发和业务分析',
        requirements: '硕士及以上学历；精通Python、R；有深度学习经验',
      },
    ];

    for (let i = 0; i < additionalJobs.length; i++) {
      const jobData = additionalJobs[i];
      const publisher = publishers[(testJobs.length + i) % publishers.length];
      const companyClient = companyClients[(testJobs.length + i) % companyClients.length];

      const job = await this.testHelper.createTestJob({
        ...jobData,
        publisherId: publisher.id,
        companyClientId: companyClient.id,
      });
      jobs.push(job);
    }

    return jobs;
  }

  private async createCandidates(users: any[]): Promise<any[]> {
    const candidates = [];
    const maintainers = users.filter(u => ['consultant', 'soho'].includes(u.role));

    // Create candidates from test data
    for (let i = 0; i < testCandidates.length; i++) {
      const candidateData = testCandidates[i];
      const maintainer = maintainers[i % maintainers.length];

      const candidate = await this.testHelper.createTestCandidate({
        ...candidateData,
        maintainerId: maintainer.id,
      });
      candidates.push(candidate);
    }

    // Create additional candidates
    const additionalCandidates = [
      {
        name: '赵敏',
        phone: '+86-13900000010',
        email: 'zhaomin@email.com',
        tags: ['DevOps', 'Docker', 'Kubernetes', '云计算'],
        location: 'Shenzhen',
        experience: '6年DevOps经验，擅长容器化部署和云基础设施',
      },
      {
        name: '孙悟空',
        phone: '+86-13900000011',
        email: 'sunwukong@email.com',
        tags: ['UI设计', 'UX设计', 'Figma', '用户研究'],
        location: 'Hangzhou',
        experience: '4年设计经验，专注移动端和Web端产品设计',
      },
      {
        name: '唐三藏',
        phone: '+86-13900000012',
        email: 'tangsanzang@email.com',
        tags: ['数据科学', 'Python', '机器学习', '深度学习'],
        location: 'Beijing',
        experience: '7年数据科学经验，有大规模数据处理经验',
      },
      {
        name: '猪八戒',
        phone: '+86-13900000013',
        email: 'zhubajie@email.com',
        tags: ['全栈开发', 'Node.js', 'React', 'MongoDB'],
        location: 'Chengdu',
        experience: '5年全栈开发经验，熟悉前后端技术栈',
      },
      {
        name: '沙悟净',
        phone: '+86-13900000014',
        email: 'shawujing@email.com',
        tags: ['测试工程师', '自动化测试', 'Selenium', 'Jest'],
        location: 'Nanjing',
        experience: '4年测试经验，专注自动化测试和质量保证',
      },
    ];

    for (let i = 0; i < additionalCandidates.length; i++) {
      const candidateData = additionalCandidates[i];
      const maintainer = maintainers[(testCandidates.length + i) % maintainers.length];

      const candidate = await this.testHelper.createTestCandidate({
        ...candidateData,
        maintainerId: maintainer.id,
      });
      candidates.push(candidate);
    }

    return candidates;
  }

  private async createSubmissions(candidates: any[], jobs: any[], users: any[]): Promise<any[]> {
    const submissions = [];
    const submitters = users.filter(u => ['consultant', 'soho'].includes(u.role));

    // Create submissions for testing different scenarios
    const submissionScenarios = [
      { candidateIndex: 0, jobIndex: 0, status: 'submitted', notes: '技术背景完美匹配' },
      { candidateIndex: 0, jobIndex: 1, status: 'interviewing', notes: '通过初筛，安排面试' },
      { candidateIndex: 1, jobIndex: 0, status: 'offered', notes: '表现优秀，已发Offer' },
      { candidateIndex: 1, jobIndex: 2, status: 'rejected', notes: '经验不符合要求' },
      { candidateIndex: 2, jobIndex: 1, status: 'withdrawn', notes: '候选人主动退出' },
      { candidateIndex: 3, jobIndex: 2, status: 'submitted', notes: '新提交的候选人' },
      { candidateIndex: 4, jobIndex: 0, status: 'interviewing', notes: '二轮面试中' },
    ];

    for (const scenario of submissionScenarios) {
      if (scenario.candidateIndex < candidates.length && scenario.jobIndex < jobs.length) {
        const candidate = candidates[scenario.candidateIndex];
        const job = jobs[scenario.jobIndex];
        const submitter = submitters[scenario.candidateIndex % submitters.length];

        const submission = await this.prisma.candidateSubmission.create({
          data: {
            candidateId: candidate.id,
            jobId: job.id,
            submittedById: submitter.id,
            status: scenario.status,
            notes: scenario.notes,
          },
        });

        submissions.push(submission);
      }
    }

    return submissions;
  }

  private async createJobPermissions(jobs: any[], users: any[]): Promise<any[]> {
    const permissions = [];
    const publishers = users.filter(u => ['consultant', 'soho'].includes(u.role));

    // Create job sharing scenarios
    const sharingScenarios = [
      { jobIndex: 0, granterIndex: 0, granteeIndex: 1 },
      { jobIndex: 0, granterIndex: 0, granteeIndex: 2 },
      { jobIndex: 1, granterIndex: 1, granteeIndex: 0 },
      { jobIndex: 2, granterIndex: 2, granteeIndex: 3 },
    ];

    for (const scenario of sharingScenarios) {
      if (scenario.jobIndex < jobs.length && 
          scenario.granterIndex < publishers.length && 
          scenario.granteeIndex < publishers.length) {
        
        const job = jobs[scenario.jobIndex];
        const granter = publishers[scenario.granterIndex];
        const grantee = publishers[scenario.granteeIndex];

        const permission = await this.prisma.jobPermission.create({
          data: {
            jobId: job.id,
            grantedById: granter.id,
            grantedToUserId: grantee.id,
            expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
          },
        });

        permissions.push(permission);
      }
    }

    return permissions;
  }

  private async createNotifications(users: any[], jobs: any[], candidates: any[]): Promise<any[]> {
    const notifications = [];
    const recipients = users.filter(u => u.role !== 'platform_admin');

    const notificationScenarios = [
      {
        type: 'job_shared',
        title: '职位分享通知',
        content: '张三分享了"高级算法工程师"职位给您',
        data: { jobId: jobs[0]?.id, sharedBy: users[0]?.id },
      },
      {
        type: 'job_closed',
        title: '职位关闭通知',
        content: '"前端技术专家"职位已关闭',
        data: { jobId: jobs[1]?.id, reason: 'position_filled' },
      },
      {
        type: 'submission_status_changed',
        title: '候选人状态更新',
        content: '候选人"李娜"的状态已更新为"面试中"',
        data: { candidateId: candidates[0]?.id, status: 'interviewing' },
      },
      {
        type: 'maintainer_change_request',
        title: '维护者变更请求',
        content: '用户申请变更候选人维护者',
        data: { candidateId: candidates[1]?.id, requestedBy: users[1]?.id },
      },
      {
        type: 'system_announcement',
        title: '系统维护通知',
        content: '系统将于今晚2:00-4:00进行维护升级',
        data: { priority: 'high', maintenanceWindow: '2:00-4:00' },
      },
    ];

    for (let i = 0; i < recipients.length && i < notificationScenarios.length; i++) {
      const recipient = recipients[i];
      const scenario = notificationScenarios[i];

      const notification = await this.prisma.notification.create({
        data: {
          userId: recipient.id,
          type: scenario.type,
          title: scenario.title,
          content: scenario.content,
          data: scenario.data,
          status: Math.random() > 0.5 ? 'delivered' : 'read', // Random read status
        },
      });

      notifications.push(notification);
    }

    return notifications;
  }

  private async createMessages(users: any[], jobs: any[], candidates: any[]): Promise<any[]> {
    const messages = [];
    const messageUsers = users.filter(u => u.role !== 'platform_admin');

    const messageScenarios = [
      {
        content: '您好，关于高级算法工程师这个职位，我有一个很合适的候选人推荐。',
        metadata: { jobId: jobs[0]?.id, candidateId: candidates[0]?.id },
      },
      {
        content: '候选人的技术背景很匹配，是否可以安排面试？',
        metadata: { candidateId: candidates[0]?.id },
      },
      {
        content: '这个职位的薪资范围是多少？客户有什么特殊要求吗？',
        metadata: { jobId: jobs[0]?.id },
      },
      {
        content: '我刚更新了候选人的简历，请查看最新版本。',
        metadata: { candidateId: candidates[1]?.id },
      },
      {
        content: '关于产品经理职位，我们需要讨论一下具体的技能要求。',
        metadata: { jobId: jobs[2]?.id },
      },
    ];

    for (let i = 0; i < messageScenarios.length && messageUsers.length > 1; i++) {
      const scenario = messageScenarios[i];
      const sender = messageUsers[i % messageUsers.length];
      const recipient = messageUsers[(i + 1) % messageUsers.length];

      const message = await this.prisma.message.create({
        data: {
          senderId: sender.id,
          recipientId: recipient.id,
          content: scenario.content,
          metadata: scenario.metadata,
          readAt: Math.random() > 0.3 ? new Date() : null, // 70% chance of being read
        },
      });

      messages.push(message);
    }

    return messages;
  }

  async cleanupTestData(): Promise<void> {
    console.log('🧹 Cleaning up test data...');
    await this.testHelper.cleanup();
    console.log('✅ Test data cleanup completed!');
  }

  async generateTestDataReport(dataset: any): Promise<void> {
    console.log('\n📊 Test Dataset Report:');
    console.log('====================');
    console.log(`👥 Users: ${dataset.users.length}`);
    console.log(`🏢 Companies: ${dataset.companies.length}`);
    console.log(`🏬 Company Clients: ${dataset.companyClients.length}`);
    console.log(`💼 Jobs: ${dataset.jobs.length}`);
    console.log(`👤 Candidates: ${dataset.candidates.length}`);
    console.log(`📄 Submissions: ${dataset.submissions.length}`);
    console.log(`🔐 Permissions: ${dataset.permissions.length}`);
    console.log(`🔔 Notifications: ${dataset.notifications.length}`);
    console.log(`💬 Messages: ${dataset.messages.length}`);
    console.log('====================\n');

    // Additional statistics
    const jobsByStatus = dataset.jobs.reduce((acc: any, job: any) => {
      acc[job.status] = (acc[job.status] || 0) + 1;
      return acc;
    }, {});

    const candidatesByLocation = dataset.candidates.reduce((acc: any, candidate: any) => {
      acc[candidate.location] = (acc[candidate.location] || 0) + 1;
      return acc;
    }, {});

    console.log('📈 Detailed Statistics:');
    console.log('Jobs by Status:', jobsByStatus);
    console.log('Candidates by Location:', candidatesByLocation);
    console.log('====================\n');
  }
}