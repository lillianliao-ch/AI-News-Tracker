# API 接口文档

## 📡 API概览

**Base URL**: `http://localhost:5000/api`  
**认证方式**: JWT Bearer Token  
**数据格式**: JSON  
**字符编码**: UTF-8

---

## 🔐 认证相关 API

### 1. 快速注册

**端点**: `POST /hunter-auth/quick-register`

**描述**: 用户快速注册，系统自动生成临时密码

**请求头**:
```http
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "张三",
  "phone": "13900000001",
  "wechatId": "wx_zhang123",  // 可选
  "reason": "希望加入猎头协作平台，专注互联网人才推荐"  // 至少10个字符
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 用户姓名，2-50字符 |
| phone | string | ✅ | 手机号，11位数字 |
| wechatId | string | ❌ | 微信号，便于联系 |
| reason | string | ✅ | 申请理由，至少10个字符 |

**成功响应** (201):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "name": "张三",
      "phone": "13900000001",
      "role": "soho",
      "status": "registered"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tempPassword": "Abc12345"
  },
  "message": "注册成功，请妥善保管临时密码"
}
```

**错误响应** (409):
```json
{
  "success": false,
  "error": "手机号已注册"
}
```

**错误响应** (400):
```json
{
  "success": false,
  "error": "申请理由至少需要10个字符"
}
```

---

### 2. 用户登录

**端点**: `POST /hunter-auth/login`

**描述**: 使用手机号和密码登录

**请求体**:
```json
{
  "phone": "13900000001",
  "password": "Abc12345"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "name": "张三",
      "phone": "13900000001",
      "role": "soho",
      "status": "registered"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "登录成功"
}
```

**错误响应** (401):
```json
{
  "success": false,
  "error": "手机号或密码错误"
}
```

---

### 3. 获取用户资料

**端点**: `GET /hunter-auth/profile`

**描述**: 获取当前登录用户的资料

**请求头**:
```http
Authorization: Bearer {token}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "张三",
    "email": "13900000001@hunter.temp",
    "phone": "13900000001",
    "role": "soho",
    "status": "registered",
    "wechatId": "wx_zhang123",
    "bio": null,
    "avatar": null,
    "postsCount": 5,
    "approvedPosts": 5,
    "totalViews": 123,
    "createdAt": "2024-11-07T10:00:00.000Z",
    "updatedAt": "2024-11-07T10:00:00.000Z"
  }
}
```

**错误响应** (401):
```json
{
  "success": false,
  "error": "未授权，请先登录"
}
```

---

### 4. 获取待审核用户列表（管理员）

**端点**: `GET /hunter-auth/pending-users`

**描述**: 管理员查看待审核的用户列表

**请求头**:
```http
Authorization: Bearer {admin_token}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "username": "李四",
      "phone": "13900000002",
      "status": "registered",
      "createdAt": "2024-11-07T10:00:00.000Z"
    }
  ]
}
```

---

### 5. 审核用户（管理员）

**端点**: `PATCH /hunter-auth/approve-user/:userId`

**描述**: 管理员审核用户

**请求头**:
```http
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**请求体**:
```json
{
  "action": "approve",  // 或 "reject"
  "reason": "审核通过"   // 拒绝时必填
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "李四",
    "status": "verified"  // 或 "suspended"
  },
  "message": "用户审核成功"
}
```

---

## 📝 信息发布相关 API

### 6. 获取信息列表

**端点**: `GET /hunter-posts`

**描述**: 获取信息列表（支持权限分级）

**请求头**:
```http
Authorization: Bearer {token}  // 可选，游客也可访问
```

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| type | string | ❌ | all | 信息类型：all, job_seeking, talent_recommendation |
| page | number | ❌ | 1 | 页码 |
| limit | number | ❌ | 10 | 每页数量（1-50） |
| status | string | ❌ | approved | 审核状态：pending, approved, rejected |

**示例请求**:
```http
GET /hunter-posts?type=job_seeking&page=1&limit=10
```

**成功响应** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "type": "job_seeking",
      "title": "资深前端工程师",
      "content": "知名互联网公司招聘...",
      "publisherName": "张三",
      "viewCount": 45,
      "createdAt": "2024-11-07T10:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "totalPages": 3,
    "hasMore": true
  },
  "userPermissions": {
    "status": "guest",        // guest, registered, verified
    "canPublish": false,
    "viewDays": 1,            // 可查看的天数
    "remainingPosts": 2       // 剩余可查看数量
  }
}
```

**权限说明**:
- **游客**: 可查看近1天的前3条信息
- **注册用户**: 可查看近3天的前10条信息
- **认证用户**: 可查看所有信息，无限制

---

### 7. 发布信息

**端点**: `POST /hunter-posts`

**描述**: 发布新的找人才/推人才信息

**请求头**:
```http
Authorization: Bearer {token}  // 必须登录
Content-Type: application/json
```

**请求体**:
```json
{
  "type": "job_seeking",              // 或 "talent_recommendation"
  "title": "资深前端工程师",
  "content": "知名互联网公司招聘资深前端工程师，要求5年以上React开发经验..."
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | enum | ✅ | job_seeking（找人才）或 talent_recommendation（推人才） |
| title | string | ✅ | 标题，1-100字符 |
| content | string | ✅ | 详细内容，1-1000字符 |

**成功响应** (201):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "type": "job_seeking",
    "title": "资深前端工程师",
    "content": "知名互联网公司招聘...",
    "status": "approved",
    "publisherId": "uuid",
    "viewCount": 0,
    "createdAt": "2024-11-07T10:00:00.000Z"
  },
  "message": "发布成功"
}
```

**错误响应** (403):
```json
{
  "success": false,
  "error": "您没有发布权限，请等待管理员审核"
}
```

**错误响应** (400):
```json
{
  "success": false,
  "error": "标题不能为空"
}
```

---

### 8. 获取我的发布

**端点**: `GET /hunter-posts/my`

**描述**: 获取当前用户的所有发布

**请求头**:
```http
Authorization: Bearer {token}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "type": "job_seeking",
      "title": "资深前端工程师",
      "content": "知名互联网公司招聘...",
      "status": "approved",
      "urgency": 0,
      "viewCount": 45,
      "replyCount": 3,
      "shareCount": 2,
      "createdAt": "2024-11-07T10:00:00.000Z",
      "updatedAt": "2024-11-07T10:00:00.000Z"
    }
  ]
}
```

---

### 9. 获取信息详情

**端点**: `GET /hunter-posts/:id`

**描述**: 获取单条信息的详细内容

**请求头**:
```http
Authorization: Bearer {token}  // 可选
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "type": "job_seeking",
    "title": "资深前端工程师",
    "content": "知名互联网公司招聘资深前端工程师，要求：\n1. 5年以上React开发经验\n2. 熟悉TypeScript...",
    "status": "approved",
    "urgency": 0,
    "viewCount": 46,  // 自动+1
    "replyCount": 3,
    "shareCount": 2,
    "publisher": {
      "id": "uuid",
      "username": "张三",
      "phone": "139****0001"
    },
    "createdAt": "2024-11-07T10:00:00.000Z",
    "updatedAt": "2024-11-07T10:00:00.000Z"
  }
}
```

**错误响应** (404):
```json
{
  "success": false,
  "error": "信息不存在"
}
```

---

### 10. 删除信息

**端点**: `DELETE /hunter-posts/:id`

**描述**: 删除自己发布的信息

**请求头**:
```http
Authorization: Bearer {token}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "删除成功"
}
```

**错误响应** (403):
```json
{
  "success": false,
  "error": "您只能删除自己的信息"
}
```

---

### 11. 审核信息（管理员）

**端点**: `PATCH /hunter-posts/:id/approve`

**描述**: 管理员审核信息

**请求头**:
```http
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**请求体**:
```json
{
  "action": "approve",  // 或 "reject"
  "reason": "内容不符合规范"  // 拒绝时必填
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "approved"  // 或 "rejected"
  },
  "message": "审核成功"
}
```

---

## 📊 通用响应格式

### 成功响应结构

```typescript
interface SuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasMore: boolean;
  };
}
```

### 错误响应结构

```typescript
interface ErrorResponse {
  success: false;
  error: string;
  code?: number;
  details?: any;
}
```

---

## 🔢 HTTP 状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|---------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证或token无效 |
| 403 | Forbidden | 无权限访问 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如手机号已存在） |
| 500 | Internal Server Error | 服务器内部错误 |

---

## 🔐 认证说明

### Token 使用方式

**请求头格式**:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token 存储

前端存储在 `localStorage`:
```javascript
// 存储
localStorage.setItem('hunter_token', token);

// 获取
const token = localStorage.getItem('hunter_token');

// 删除（登出）
localStorage.removeItem('hunter_token');
```

### Token 过期

- **有效期**: 7天
- **过期后**: 返回401错误，需要重新登录

---

## 📝 数据类型说明

### UserRole 枚举

```typescript
enum UserRole {
  platform_admin = 'platform_admin',  // 平台管理员
  company_admin = 'company_admin',    // 公司管理员
  consultant = 'consultant',          // 猎头顾问
  soho = 'soho'                       // SOHO猎头
}
```

### UserStatus 枚举

```typescript
enum UserStatus {
  registered = 'registered',  // 已注册（待审核）
  verified = 'verified',      // 已认证（可发布）
  active = 'active',          // 活跃
  suspended = 'suspended'     // 已暂停
}
```

### PostType 枚举

```typescript
enum PostType {
  job_seeking = 'job_seeking',                    // 找人才
  talent_recommendation = 'talent_recommendation'  // 推人才
}
```

### PostStatus 枚举

```typescript
enum PostStatus {
  pending = 'pending',      // 待审核
  approved = 'approved',    // 已通过
  rejected = 'rejected'     // 已拒绝
}
```

---

## 🧪 测试示例

### 使用 curl 测试

#### 1. 注册用户
```bash
curl -X POST http://localhost:5000/api/hunter-auth/quick-register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试用户",
    "phone": "13900000001",
    "reason": "测试猎头协作平台功能测试"
  }'
```

#### 2. 登录
```bash
curl -X POST http://localhost:5000/api/hunter-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13900000001",
    "password": "your_password"
  }'
```

#### 3. 获取信息列表（游客）
```bash
curl http://localhost:5000/api/hunter-posts
```

#### 4. 获取信息列表（已登录）
```bash
curl http://localhost:5000/api/hunter-posts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 5. 发布信息
```bash
curl -X POST http://localhost:5000/api/hunter-posts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "job_seeking",
    "title": "资深前端工程师",
    "content": "知名互联网公司招聘..."
  }'
```

---

### 使用 JavaScript Fetch

```javascript
// 1. 注册
const register = async () => {
  const response = await fetch('http://localhost:5000/api/hunter-auth/quick-register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: '测试用户',
      phone: '13900000001',
      reason: '测试猎头协作平台功能测试',
    }),
  });
  const data = await response.json();
  if (data.success) {
    localStorage.setItem('hunter_token', data.data.token);
  }
  return data;
};

// 2. 获取信息列表
const getPosts = async () => {
  const token = localStorage.getItem('hunter_token');
  const response = await fetch('http://localhost:5000/api/hunter-posts', {
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  });
  return await response.json();
};

// 3. 发布信息
const createPost = async (postData) => {
  const token = localStorage.getItem('hunter_token');
  const response = await fetch('http://localhost:5000/api/hunter-posts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(postData),
  });
  return await response.json();
};
```

---

## ⚠️ 注意事项

### 1. 频率限制
- 目前**未实施**频率限制
- 生产环境建议添加 rate limiting

### 2. 数据验证
- 所有输入都经过 Zod Schema 验证
- 手机号必须是有效的11位数字
- 标题和内容有长度限制

### 3. 安全建议
- ✅ 使用HTTPS传输
- ✅ 不要在URL中传递敏感信息
- ✅ Token应设置合理的过期时间
- ✅ 敏感信息（如密码）应加密传输

### 4. 最佳实践
- ✅ 始终检查 `success` 字段
- ✅ 处理所有可能的错误状态码
- ✅ 实现Token自动刷新机制
- ✅ 使用请求拦截器统一添加Token

---

## 📞 技术支持

- **API问题**: 查看服务器日志
- **认证问题**: 检查Token是否有效
- **权限问题**: 确认用户角色和状态

---

**文档版本**: v1.0.0  
**最后更新**: 2024-11-07  
**维护者**: 开发团队

