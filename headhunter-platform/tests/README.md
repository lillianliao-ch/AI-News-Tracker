# 猎头协作平台集成测试套件

## 概述

本测试套件为猎头协作平台提供全面的集成测试，覆盖用户认证、职位管理、候选人管理、协作功能、消息通知等核心业务场景。

## 测试架构

```
tests/
├── integration/          # 集成测试案例
│   ├── auth.test.ts      # 用户认证和权限测试
│   ├── jobs.test.ts      # 职位管理和协作测试
│   ├── candidates.test.ts # 候选人管理和匹配测试
│   └── messaging.test.ts # 消息和通知测试
├── fixtures/             # 测试数据
│   └── testData.ts       # 测试数据定义
├── utils/                # 测试工具
│   ├── testHelper.ts     # 测试辅助类
│   └── dataGenerator.ts  # 测试数据生成器
├── setup.ts              # 测试环境设置
├── testRunner.ts         # 自动化测试运行器
└── README.md             # 本文档
```

## 测试覆盖范围

### 1. 用户认证和权限 (auth.test.ts)
- ✅ 用户注册流程（不同角色）
- ✅ 用户登录验证
- ✅ JWT token 验证
- ✅ 角色权限控制
- ✅ 用户审核流程
- ✅ 权限边界测试

### 2. 职位管理和协作 (jobs.test.ts)
- ✅ 职位 CRUD 操作
- ✅ 职位状态管理
- ✅ 职位分享和权限
- ✅ 协作统计分析
- ✅ 职位搜索和推荐
- ✅ 收益分成验证

### 3. 候选人管理和匹配 (candidates.test.ts)
- ✅ 候选人 CRUD 操作
- ✅ 重复候选人检测
- ✅ 智能匹配算法
- ✅ 候选人投递流程
- ✅ 维护者变更管理
- ✅ 文件上传处理

### 4. 消息和通知 (messaging.test.ts)
- ✅ 直接消息发送
- ✅ 消息线程管理
- ✅ 通知系统
- ✅ 系统公告
- ✅ 实时通知
- ✅ 消息上下文关联

## 测试数据

### 用户类型
```typescript
- Platform Admin (平台管理员)
- Company Admin (公司管理员)  
- Consultant (咨询顾问)
- SOHO (个人猎头)
```

### 测试场景数据
- **用户**: 9个不同角色的测试用户
- **公司**: 3个不同状态的公司
- **客户**: 6个行业客户
- **职位**: 6个不同类型的职位
- **候选人**: 10个不同背景的候选人
- **投递**: 7个不同状态的投递记录
- **权限**: 4个职位分享场景
- **通知**: 5种不同类型的通知
- **消息**: 5个不同上下文的消息

## 智能匹配测试

### 匹配算法权重
- **标签匹配**: 40%
- **行业匹配**: 20%  
- **地点匹配**: 10%
- **技能关键词**: 30%

### 测试场景
1. **高匹配度**: 算法工程师 + 机器学习候选人 (90%+)
2. **中匹配度**: 前端职位 + React开发者 (70%+)
3. **低匹配度**: 金融产品 + 技术候选人 (<50%)

## 运行测试

### 环境要求
- Node.js 18+
- PostgreSQL (测试数据库)
- Redis (可选)

### 安装依赖
```bash
npm install
```

### 运行单个测试
```bash
# 认证测试
npm run test:integration -- auth.test.ts

# 职位管理测试
npm run test:integration -- jobs.test.ts

# 候选人测试
npm run test:integration -- candidates.test.ts

# 消息测试
npm run test:integration -- messaging.test.ts
```

### 运行完整测试套件
```bash
# 标准集成测试
npm run test:integration

# 覆盖率测试
npm run test:integration:coverage

# 观察模式
npm run test:integration:watch

# 自动化测试运行器
npm run test:integration:runner
```

### 自动化测试流程
```bash
npm run test:integration:runner
```

自动化测试包括：
1. 🔧 环境设置
2. 🏗️ 生成测试数据
3. 🧪 运行核心场景测试
4. ⚡ 性能测试
5. 🔍 边界情况测试
6. 📊 生成测试报告
7. 🧹 清理环境

## 性能基准

### 响应时间要求
- **用户认证**: < 200ms
- **职位搜索**: < 500ms
- **候选人匹配**: < 2s
- **消息发送**: < 100ms

### 并发测试
- **同时在线用户**: 50+
- **数据库连接池**: 10-20
- **内存使用**: < 512MB

## 测试报告示例

```
📊 Test Dataset Report:
====================
👥 Users: 9
🏢 Companies: 3
🏬 Company Clients: 6
💼 Jobs: 6
👤 Candidates: 10
📄 Submissions: 7
🔐 Permissions: 4
🔔 Notifications: 5
💬 Messages: 5

✅ Test Summary:
Total Tests: 92
Passed: 92
Failed: 0
Success Rate: 100%

📈 Coverage Report:
Lines: 92.5%
Functions: 94.2%
Branches: 89.7%
Statements: 92.1%

⚡ Performance Metrics:
Average Response Time: 125ms
Max Response Time: 450ms
Throughput: 1200 req/min
Concurrent Users Tested: 50
```

## 调试和故障排查

### 常见问题
1. **数据库连接失败**: 检查 DATABASE_URL 环境变量
2. **Token 验证失败**: 确认 JWT_SECRET 配置
3. **测试数据冲突**: 运行 `npm run db:reset` 重置数据库

### 调试技巧
```bash
# 启用详细日志
DEBUG=* npm run test:integration

# 单独运行失败的测试
npm run test:integration -- --testNamePattern="specific test name"

# 生成覆盖率报告
npm run test:integration:coverage
```

## 持续集成

### GitHub Actions 配置
```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: headhunter_test
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npm run test:integration:coverage
```

## 贡献指南

### 添加新测试
1. 在相应的 `*.test.ts` 文件中添加测试用例
2. 更新 `testData.ts` 添加必要的测试数据
3. 运行测试确保通过
4. 更新文档

### 测试规范
- 使用描述性的测试名称
- 每个测试应该独立运行
- 使用 `beforeEach` 清理测试数据
- 验证正面和负面场景
- 添加必要的断言和验证

## 许可证

MIT License - 详见 [LICENSE](../LICENSE) 文件。