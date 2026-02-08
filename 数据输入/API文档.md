# 猎头协作平台 API 文档

## 一、API 概览

### 1.1 基本信息

- **API 版本**: v1.0
- **基础 URL**: `https://api.headhunter-platform.com/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

### 1.2 通用响应格式

```typescript
interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: ValidationError[];
  meta?: PaginationMeta;
  timestamp: string;
}

interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
  hasPrev: boolean;
}

interface ValidationError {
  field: string;
  message: string;
  code: string;
}
```

### 1.3 HTTP 状态码

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权，需要登录 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如重复创建） |
| 422 | Unprocessable Entity | 参数验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |

## 二、认证授权 API

### 2.1 用户注册

**POST** `/auth/register`

```yaml
summary: 用户注册
description: 注册新用户账号，支持猎头公司、SOHO顾问等角色
security: []
```

**请求体**:
```json
{
  "email": "user@example.com",
  "phone": "13800138000",
  "password": "password123",
  "name": "张三",
  "role": "consultant", // consultant, soho, company_admin
  "companyName": "XX猎头公司", // role为consultant时必填
  "industry": "互联网" // SOHO顾问时填写擅长领域
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-123",
    "email": "user@example.com",
    "name": "张三",
    "role": "consultant",
    "status": "pending"
  },
  "message": "注册成功，请等待审核",
  "timestamp": "2025-09-10T12:00:00Z"
}
```

### 2.2 用户登录

**POST** `/auth/login`

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-123",
      "email": "user@example.com",
      "name": "张三",
      "role": "consultant",
      "companyId": "uuid-456"
    },
    "tokens": {
      "accessToken": "jwt-access-token",
      "refreshToken": "jwt-refresh-token",
      "expiresIn": 3600
    }
  },
  "timestamp": "2025-09-10T12:00:00Z"
}
```

### 2.3 刷新令牌

**POST** `/auth/refresh`

**请求体**:
```json
{
  "refreshToken": "jwt-refresh-token"
}
```

### 2.4 用户登出

**POST** `/auth/logout`

**Headers**:
```
Authorization: Bearer <access-token>
```

## 三、用户管理 API

### 3.1 获取用户信息

**GET** `/users/me`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-123",
    "email": "user@example.com",
    "name": "张三",
    "phone": "13800138000",
    "role": "consultant",
    "status": "active",
    "company": {
      "id": "uuid-456",
      "name": "XX猎头公司"
    },
    "permissions": ["job.create", "candidate.submit"],
    "createdAt": "2025-09-01T10:00:00Z"
  }
}
```

### 3.2 更新用户信息

**PUT** `/users/me`

**请求体**:
```json
{
  "name": "张三丰",
  "phone": "13900139000",
  "industry": "金融"
}
```

### 3.3 获取用户列表（管理员）

**GET** `/users?page=1&limit=20&role=consultant&status=active`

**查询参数**:
- `page`: 页码，默认 1
- `limit`: 每页数量，默认 20
- `role`: 用户角色筛选
- `status`: 状态筛选
- `companyId`: 公司ID筛选

## 四、公司管理 API

### 4.1 创建公司

**POST** `/companies`

**请求体**:
```json
{
  "name": "XX猎头公司",
  "businessLicense": "91330100123456789X",
  "industry": "人力资源",
  "scale": "medium",
  "contactPerson": "李经理",
  "contactPhone": "13700137000",
  "contactEmail": "manager@company.com",
  "address": "杭州市西湖区XX路XX号"
}
```

### 4.2 获取公司详情

**GET** `/companies/{companyId}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-456",
    "name": "XX猎头公司",
    "industry": "人力资源",
    "scale": "medium",
    "status": "approved",
    "memberCount": 15,
    "activeJobs": 8,
    "createdAt": "2025-08-01T10:00:00Z"
  }
}
```

### 4.3 获取公司成员

**GET** `/companies/{companyId}/members`

## 五、职位管理 API

### 5.1 创建职位

**POST** `/jobs`

**请求体**:
```json
{
  "title": "高级Java开发工程师",
  "industry": "互联网",
  "location": "杭州",
  "salaryMin": 20000,
  "salaryMax": 35000,
  "description": "负责核心业务系统开发...",
  "requirements": "3年以上Java开发经验...",
  "benefits": "五险一金，年终奖金...",
  "urgency": "urgent",
  "reportTo": "技术总监",
  "companyClientId": "uuid-789",
  "profitSharing": {
    "publisherSharePct": 60,
    "referrerSharePct": 35,
    "platformSharePct": 5
  },
  "permissions": {
    "openTo": ["company", "user"],
    "companies": ["uuid-111", "uuid-222"],
    "users": ["uuid-333"]
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-job-123",
    "title": "高级Java开发工程师",
    "status": "open",
    "publisherId": "uuid-123",
    "shareUrl": "https://platform.com/jobs/share/uuid-job-123",
    "createdAt": "2025-09-10T12:00:00Z"
  },
  "message": "职位创建成功"
}
```

### 5.2 获取职位列表

**GET** `/jobs?page=1&limit=20&status=open&industry=互联网`

**查询参数**:
- `page`: 页码
- `limit`: 每页数量  
- `status`: 职位状态 (open, paused, closed)
- `industry`: 行业筛选
- `location`: 地点筛选
- `salaryMin`, `salaryMax`: 薪资范围
- `urgency`: 紧急程度
- `publisherId`: 发布人ID
- `hasPermission`: 只显示有权限的职位

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-job-123",
      "title": "高级Java开发工程师",
      "industry": "互联网",
      "location": "杭州",
      "salaryMin": 20000,
      "salaryMax": 35000,
      "urgency": "urgent",
      "status": "open",
      "publisher": {
        "id": "uuid-123",
        "name": "张三"
      },
      "clientCompany": {
        "name": "ABC科技公司"
      },
      "profitSharing": {
        "publisherSharePct": 60,
        "referrerSharePct": 35
      },
      "submissionCount": 5,
      "createdAt": "2025-09-10T12:00:00Z"
    }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "hasNext": true,
    "hasPrev": false
  }
}
```

### 5.3 获取职位详情

**GET** `/jobs/{jobId}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-job-123",
    "title": "高级Java开发工程师",
    "description": "负责核心业务系统开发...",
    "requirements": "3年以上Java开发经验...",
    "benefits": "五险一金，年终奖金...",
    "industry": "互联网",
    "location": "杭州",
    "salaryMin": 20000,
    "salaryMax": 35000,
    "urgency": "urgent",
    "reportTo": "技术总监",
    "status": "open",
    "publisher": {
      "id": "uuid-123",
      "name": "张三",
      "company": "XX猎头公司"
    },
    "companyClient": {
      "id": "uuid-789",
      "name": "ABC科技公司",
      "industry": "互联网",
      "partnerCompany": {
        "id": "uuid-company-456",
        "name": "XX猎头公司"
      }
    },
    "profitSharing": {
      "publisherSharePct": 60,
      "referrerSharePct": 35,
      "platformSharePct": 5
    },
    "submissions": {
      "total": 8,
      "submitted": 3,
      "reviewed": 2,
      "interview": 2,
      "offer": 1
    },
    "hasPermission": true,
    "canSubmit": true,
    "shareUrl": "https://platform.com/jobs/share/uuid-job-123",
    "createdAt": "2025-09-10T12:00:00Z",
    "updatedAt": "2025-09-10T14:00:00Z"
  }
}
```

### 5.4 更新职位

**PUT** `/jobs/{jobId}`

### 5.5 关闭职位

**POST** `/jobs/{jobId}/close`

**请求体**:
```json
{
  "reason": "客户已找到合适候选人"
}
```

### 5.6 设置职位权限

**POST** `/jobs/{jobId}/permissions`

**请求体**:
```json
{
  "granteeType": "company", // user or company
  "granteeId": "uuid-company-111",
  "expiresAt": "2025-12-31T23:59:59Z" // 可选，权限过期时间
}
```

### 5.7 生成职位分享

**POST** `/jobs/{jobId}/share`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "shareUrl": "https://platform.com/jobs/share/uuid-job-123",
    "qrCode": "data:image/png;base64,iVBORw0KGgoAAAANSU...",
    "shareCard": {
      "title": "高级Java开发工程师",
      "company": "ABC科技公司",
      "location": "杭州",
      "salary": "20K-35K",
      "urgency": "急招",
      "profitSharing": "推荐分成35%"
    }
  }
}
```

### 5.8 OCR解析职位JD

**POST** `/jobs/parse-jd`

**请求体** (multipart/form-data):
```
file: [PDF/Word/Image file]
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "title": "高级Java开发工程师",
    "location": "杭州",
    "salaryMin": 20000,
    "salaryMax": 35000,
    "requirements": "3年以上Java开发经验...",
    "description": "负责核心业务系统开发...",
    "benefits": "五险一金，年终奖金...",
    "confidence": 0.95,
    "extractedText": "原始提取文本内容..."
  }
}
```

## 六、候选人管理 API

### 6.1 检查候选人重复

**POST** `/candidates/check-duplicate`

**请求体**:
```json
{
  "name": "王小明",
  "phone": "13800138000"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "isDuplicate": true,
    "existingCandidate": {
      "id": "uuid-candidate-123",
      "name": "王小明",
      "phone": "13800138000",
      "maintainer": {
        "id": "uuid-user-456",
        "name": "李四"
      },
      "createdAt": "2025-09-01T10:00:00Z"
    },
    "suggestions": [
      "查看现有候选人详情",
      "申请成为维护人", 
      "在备注中补充信息"
    ]
  }
}
```

### 6.2 创建候选人

**POST** `/candidates`

**请求体**:
```json
{
  "name": "王小明",
  "phone": "13800138000",
  "email": "wangxm@example.com",
  "educationBackground": "本科，计算机科学与技术",
  "workExperience": "5年Java开发经验，曾在阿里巴巴工作...",
  "skills": ["Java", "Spring Boot", "MySQL", "Redis"],
  "forceCreate": false // 检测到重复时是否强制创建
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-candidate-789",
    "name": "王小明",
    "phone": "13800138000",
    "maintainerId": "uuid-123",
    "createdAt": "2025-09-10T12:00:00Z"
  },
  "message": "候选人创建成功，您已成为该候选人的维护人"
}
```

### 6.3 获取候选人列表

**GET** `/candidates?page=1&limit=20&maintainer=me&skills=Java`

**查询参数**:
- `page`, `limit`: 分页参数
- `maintainer`: 维护人筛选 (me, all, userId)
- `skills`: 技能标签筛选
- `keyword`: 关键词搜索（姓名、技能）

### 6.4 获取候选人详情

**GET** `/candidates/{candidateId}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-candidate-123",
    "name": "王小明",
    "phone": "13800138000",
    "email": "wangxm@example.com",
    "educationBackground": "本科，计算机科学与技术",
    "workExperience": "5年Java开发经验...",
    "skills": ["Java", "Spring Boot", "MySQL", "Redis"],
    "maintainer": {
      "id": "uuid-456",
      "name": "李四"
    },
    "isMaintainer": false,
    "submissionHistory": [
      {
        "id": "uuid-submission-111",
        "job": {
          "title": "Java开发工程师",
          "company": "ABC公司"
        },
        "status": "interview_scheduled",
        "submittedAt": "2025-09-08T10:00:00Z"
      }
    ],
    "createdAt": "2025-09-01T10:00:00Z",
    "updatedAt": "2025-09-10T12:00:00Z"
  }
}
```

### 6.5 更新候选人信息

**PUT** `/candidates/{candidateId}`

**说明**: 只有维护人可以更新候选人基础信息，非维护人只能在备注中补充信息

### 6.6 申请成为维护人

**POST** `/candidates/{candidateId}/change-maintainer`

**请求体**:
```json
{
  "reason": "我与该候选人有更直接的联系，掌握更完整的信息"
}
```

## 七、候选人投递 API

### 7.1 投递候选人

**POST** `/submissions`

**请求体**:
```json
{
  "candidateId": "uuid-candidate-123",
  "jobId": "uuid-job-456",
  "customizedResume": "针对该职位优化的简历内容...",
  "submissionReason": "该候选人有5年Java经验，与职位要求高度匹配",
  "matchScore": 85,
  "notes": "候选人对这个机会很感兴趣，可以立即面试"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-submission-789",
    "candidateId": "uuid-candidate-123",
    "jobId": "uuid-job-456",
    "status": "submitted",
    "submitterId": "uuid-123",
    "createdAt": "2025-09-10T12:00:00Z"
  },
  "message": "候选人投递成功"
}
```

### 7.2 获取投递列表

**GET** `/submissions?page=1&limit=20&status=submitted&jobId=uuid-job-456`

**查询参数**:
- `jobId`: 职位ID筛选
- `candidateId`: 候选人ID筛选
- `submitterId`: 投递人ID筛选
- `status`: 状态筛选
- `dateFrom`, `dateTo`: 时间范围

### 7.3 获取投递详情

**GET** `/submissions/{submissionId}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-submission-789",
    "candidate": {
      "id": "uuid-candidate-123",
      "name": "王小明",
      "phone": "138****8000",
      "skills": ["Java", "Spring Boot"]
    },
    "job": {
      "id": "uuid-job-456",
      "title": "高级Java开发工程师",
      "company": "ABC科技公司"
    },
    "submitter": {
      "id": "uuid-123",
      "name": "张三"
    },
    "customizedResume": "针对该职位优化的简历内容...",
    "submissionReason": "该候选人有5年Java经验，与职位要求高度匹配",
    "matchScore": 85,
    "notes": "候选人对这个机会很感兴趣，可以立即面试",
    "status": "interview_scheduled",
    "statusHistory": [
      {
        "fromStatus": "submitted",
        "toStatus": "reviewed",
        "comment": "简历符合要求",
        "changedBy": "uuid-publisher-123",
        "changedAt": "2025-09-10T14:00:00Z"
      },
      {
        "fromStatus": "reviewed", 
        "toStatus": "interview_scheduled",
        "comment": "安排明天下午面试",
        "changedBy": "uuid-publisher-123",
        "changedAt": "2025-09-10T16:00:00Z"
      }
    ],
    "createdAt": "2025-09-10T12:00:00Z",
    "updatedAt": "2025-09-10T16:00:00Z"
  }
}
```

### 7.4 更新投递状态

**PUT** `/submissions/{submissionId}/status`

**请求体**:
```json
{
  "status": "interview_passed",
  "comment": "面试表现优秀，技术能力符合要求"
}
```

**说明**: 只有职位发布人可以更新投递状态

## 八、客户企业管理 API

### 8.1 创建客户企业

**POST** `/client-companies`

**请求体**:
```json
{
  "name": "ABC科技公司",
  "industry": "互联网",
  "size": "large",
  "contactName": "HR经理",
  "contactPhone": "13700137000",
  "contactEmail": "hr@abc.com",
  "location": "杭州市滨江区XX路XX号",
  "tags": ["互联网", "AI", "高薪", "期权"],
  "partnerCompanyId": "uuid-company-456"
}
```

### 8.2 获取客户企业列表

**GET** `/client-companies?page=1&limit=20&industry=互联网&maintainer=me&partnerCompanyId=uuid-company-456`

**查询参数**:
- `page`: 页码，默认 1
- `limit`: 每页数量，默认 20
- `industry`: 行业筛选
- `maintainer`: 维护人筛选 (me, all, userId)
- `partnerCompanyId`: 合作伙伴公司ID筛选
- `size`: 企业规模筛选
- `location`: 地点筛选

### 8.3 获取客户企业详情

**GET** `/client-companies/{clientCompanyId}`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-client-123",
    "name": "ABC科技公司",
    "industry": "互联网",
    "size": "large",
    "contactName": "HR经理",
    "contactPhone": "13700137000",
    "contactEmail": "hr@abc.com",
    "location": "杭州市滨江区XX路XX号",
    "tags": ["互联网", "AI", "高薪", "期权"],
    "partnerCompany": {
      "id": "uuid-company-456",
      "name": "XX猎头公司"
    },
    "maintainer": {
      "id": "uuid-456",
      "name": "李四"
    },
    "recentJobs": [
      {
        "title": "Java开发工程师",
        "status": "open",
        "createdAt": "2025-09-08T10:00:00Z"
      }
    ],
    "createdAt": "2025-08-15T10:00:00Z"
  }
}
```

## 九、利益分配与结算 API

### 9.1 获取结算列表

**GET** `/settlements?page=1&limit=20&status=pending&userId=uuid-123`

**查询参数**:
- `status`: 结算状态 (pending, calculated, paid, disputed)
- `userId`: 用户ID筛选（查看自己相关的结算）
- `dateFrom`, `dateTo`: 结算时间范围

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-settlement-123",
      "submission": {
        "id": "uuid-submission-456",
        "candidate": "王小明",
        "job": "Java开发工程师"
      },
      "totalAmount": 50000,
      "publisherAmount": 30000,
      "referrerAmount": 17500,
      "platformAmount": 2500,
      "status": "calculated",
      "publisherId": "uuid-publisher-123",
      "referrerId": "uuid-referrer-456",
      "settlementDate": "2025-09-15T00:00:00Z",
      "createdAt": "2025-09-10T12:00:00Z"
    }
  ],
  "meta": {
    "total": 25,
    "totalAmount": 1250000,
    "myAmount": 87500
  }
}
```

### 9.2 计算分成金额

**POST** `/settlements/{submissionId}/calculate`

**请求体**:
```json
{
  "totalAmount": 50000
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "submissionId": "uuid-submission-456",
    "totalAmount": 50000,
    "publisherAmount": 30000,
    "referrerAmount": 17500,
    "platformAmount": 2500,
    "profitSharing": {
      "publisherSharePct": 60,
      "referrerSharePct": 35,
      "platformSharePct": 5
    }
  }
}
```

### 9.3 标记结算已支付

**POST** `/settlements/{settlementId}/pay`

**请求体**:
```json
{
  "paymentMethod": "bank_transfer",
  "transactionId": "TXN202509101234567890",
  "note": "已通过银行转账支付"
}
```

### 9.4 获取收入统计

**GET** `/settlements/reports?period=month&year=2025&month=9`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "period": "2025-09",
    "totalIncome": 125000,
    "publisherIncome": 75000,
    "referrerIncome": 50000,
    "settlementCount": 8,
    "breakdown": {
      "paid": 100000,
      "pending": 25000
    },
    "monthlyTrend": [
      {"month": "2025-07", "income": 80000},
      {"month": "2025-08", "income": 95000},
      {"month": "2025-09", "income": 125000}
    ]
  }
}
```

## 十、通知管理 API

### 10.1 获取通知列表

**GET** `/notifications?page=1&limit=20&type=job_opened&isRead=false`

**查询参数**:
- `type`: 通知类型
- `isRead`: 是否已读
- `relatedId`: 关联对象ID

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-notification-123",
      "type": "job_opened",
      "title": "新职位开放协作",
      "content": "职位【Java开发工程师】已对您开放，分成比例为35%",
      "relatedId": "uuid-job-456",
      "isRead": false,
      "createdAt": "2025-09-10T12:00:00Z"
    },
    {
      "id": "uuid-notification-124",
      "type": "status_updated", 
      "title": "候选人状态更新",
      "content": "您推荐的候选人王小明已进入面试阶段",
      "relatedId": "uuid-submission-789",
      "isRead": false,
      "createdAt": "2025-09-10T14:00:00Z"
    }
  ],
  "meta": {
    "total": 50,
    "unreadCount": 8
  }
}
```

### 10.2 标记通知已读

**PUT** `/notifications/{notificationId}/read`

### 10.3 批量标记已读

**POST** `/notifications/mark-all-read`

**请求体**:
```json
{
  "type": "job_opened", // 可选，只标记特定类型
  "olderThan": "2025-09-10T12:00:00Z" // 可选，只标记指定时间之前的
}
```

## 十一、文件管理 API

### 11.1 上传文件

**POST** `/files/upload`

**请求体** (multipart/form-data):
```
file: [File]
type: "resume" | "jd" | "avatar" | "document"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-file-123",
    "filename": "resume.pdf",
    "originalName": "王小明简历.pdf",
    "size": 1024000,
    "mimeType": "application/pdf",
    "url": "https://oss.platform.com/files/uuid-file-123",
    "uploadedAt": "2025-09-10T12:00:00Z"
  }
}
```

### 11.2 获取文件信息

**GET** `/files/{fileId}`

### 11.3 删除文件

**DELETE** `/files/{fileId}`

## 十二、统计分析 API

### 12.1 获取仪表盘数据

**GET** `/analytics/dashboard`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalJobs": 156,
      "activeJobs": 89,
      "totalSubmissions": 2341,
      "successfulPlacements": 234,
      "totalIncome": 2580000
    },
    "thisMonth": {
      "newJobs": 23,
      "newSubmissions": 145,
      "completedPlacements": 18,
      "income": 450000
    },
    "trends": {
      "jobTrend": [
        {"date": "2025-09-01", "count": 5},
        {"date": "2025-09-02", "count": 8}
      ],
      "submissionTrend": [
        {"date": "2025-09-01", "count": 12},
        {"date": "2025-09-02", "count": 15}
      ]
    },
    "topIndustries": [
      {"industry": "互联网", "jobCount": 45, "placementRate": 0.32},
      {"industry": "金融", "jobCount": 28, "placementRate": 0.28}
    ]
  }
}
```

### 12.2 获取个人业绩

**GET** `/analytics/performance?period=month&year=2025&month=9`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "period": "2025-09",
    "metrics": {
      "jobsPublished": 8,
      "candidatesSubmitted": 25,
      "successfulPlacements": 3,
      "placementRate": 0.12,
      "totalIncome": 75000,
      "avgDealSize": 25000
    },
    "rankings": {
      "incomeRank": 3,
      "placementRank": 5,
      "totalUsers": 156
    },
    "recentSuccesses": [
      {
        "candidate": "王小明",
        "job": "Java开发工程师", 
        "income": 25000,
        "placedAt": "2025-09-08T10:00:00Z"
      }
    ]
  }
}
```

## 十三、系统管理 API

### 13.1 获取审计日志（管理员）

**GET** `/admin/audit-logs?page=1&limit=50&userId=uuid-123&action=CREATE`

**查询参数**:
- `userId`: 用户ID筛选
- `action`: 操作类型筛选
- `resourceType`: 资源类型筛选
- `dateFrom`, `dateTo`: 时间范围

### 13.2 获取系统状态

**GET** `/admin/system-status`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "database": {
      "status": "connected",
      "connections": 15
    },
    "redis": {
      "status": "connected",
      "memory": "256MB"
    },
    "services": {
      "ocr": "available",
      "nlp": "available", 
      "notification": "available"
    }
  }
}
```

## 十四、错误码对照表

| 错误码 | HTTP状态码 | 描述 | 解决方案 |
|--------|-----------|------|----------|
| AUTH_001 | 401 | 未提供认证令牌 | 请在Header中提供Authorization |
| AUTH_002 | 401 | 认证令牌无效 | 请重新登录获取有效令牌 |
| AUTH_003 | 401 | 认证令牌已过期 | 请使用refreshToken刷新令牌 |
| PERM_001 | 403 | 权限不足 | 该操作需要更高权限 |
| VALID_001 | 422 | 参数验证失败 | 请检查请求参数格式 |
| DUPLICATE_001 | 409 | 候选人已存在 | 请检查重复候选人处理 |
| NOT_FOUND_001 | 404 | 资源不存在 | 请检查资源ID是否正确 |
| BUSINESS_001 | 400 | 分成比例总和必须为100% | 请调整分成比例配置 |
| BUSINESS_002 | 400 | 职位已关闭，无法投递 | 该职位已关闭 |
| RATE_LIMIT_001 | 429 | 请求过于频繁 | 请稍后再试 |
| SERVER_001 | 500 | 服务器内部错误 | 请联系技术支持 |

## 十五、SDK 示例

### 15.1 JavaScript/TypeScript SDK

```typescript
import HeadhunterAPI from '@headhunter-platform/api-sdk';

const api = new HeadhunterAPI({
  baseURL: 'https://api.headhunter-platform.com/api/v1',
  apiKey: 'your-api-key'
});

// 登录
const loginResult = await api.auth.login({
  email: 'user@example.com',
  password: 'password123'
});

// 创建职位
const job = await api.jobs.create({
  title: '高级Java开发工程师',
  industry: '互联网',
  location: '杭州',
  salaryMin: 20000,
  salaryMax: 35000,
  profitSharing: {
    publisherSharePct: 60,
    referrerSharePct: 35,
    platformSharePct: 5
  }
});

// 投递候选人
const submission = await api.submissions.create({
  candidateId: 'uuid-candidate-123',
  jobId: job.id,
  matchScore: 85
});
```

### 15.2 Python SDK

```python
from headhunter_api import HeadhunterClient

client = HeadhunterClient(
    base_url='https://api.headhunter-platform.com/api/v1',
    api_key='your-api-key'
)

# 登录
login_result = client.auth.login(
    email='user@example.com',
    password='password123'
)

# 检查候选人重复
duplicate_check = client.candidates.check_duplicate(
    name='王小明',
    phone='13800138000'
)

# 创建候选人
if not duplicate_check['isDuplicate']:
    candidate = client.candidates.create({
        'name': '王小明',
        'phone': '13800138000',
        'skills': ['Java', 'Spring Boot']
    })
```

---

**API文档版本**：v1.0  
**最后更新时间**：2025-09-10  
**文档状态**：完整版本  
**维护团队**：技术架构组