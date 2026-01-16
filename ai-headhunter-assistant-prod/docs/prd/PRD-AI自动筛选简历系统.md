# AI 自动筛选简历 + 自动打招呼系统 PRD v2.0

## 📋 文档信息

- **项目名称**: AI 猎头助手（混合架构版）
- **版本**: v2.0
- **创建日期**: 2025-11-13
- **技术架构**: Chrome 浏览器插件 + Python 后台服务
- **目标平台**: Boss 直聘（后续扩展猎聘/脉脉）

---

## 1. 项目目标

### 1.1 核心价值
构建一个可用于真实猎头场景的 **AI 自动化招聘助手系统**，实现：

- ✅ 自动读取 Boss 直聘的候选人列表
- ✅ 自动打开每一份候选人简历并下载
- ✅ 自动解析简历内容（PDF 解析 + OCR）
- ✅ 自动通过大模型评估简历 → 输出"匹配度 + 推荐等级 + 标签"
- ✅ 自动将简历和分析结果记录到飞书多维表格
- ✅ 对高匹配度候选人自动生成话术并执行"打招呼"
- ✅ 全流程自动化执行 50-200 份/天

**核心目标**：
> 每天自动筛选 200+ 候选人，减少 80% 猎头重复劳动，让 AI 自动做"看简历 + 打招呼 + 入库"。

### 1.2 项目边界

**✅ 本期做（MVP）**：
- Boss 直聘平台自动化
- PDF 简历解析 + 基础 OCR
- AI 匹配度评估
- 飞书多维表格入库
- 自动打招呼（可选开关）

**❌ 暂不做（后续迭代）**：
- 猎聘/脉脉/LinkedIn 平台
- 候选人回复的自动应答
- 面试安排自动化
- 数据分析看板

---

## 2. 技术架构：混合模式

### 2.1 整体架构图

```
┌───────────────────────────────────────────────────────────┐
│                   用户层（猎头HR）                         │
│              Chrome 浏览器 + Boss 直聘网页                 │
└───────────────────────────────────────────────────────────┘
                            ↕
┌───────────────────────────────────────────────────────────┐
│              Chrome 插件（采集控制层）                      │
│  • 页面注入控制面板                                        │
│  • 自动滚动列表、点击候选人                                 │
│  • 提取候选人信息、下载简历 PDF                             │
│  • 调用后台 API 发送数据                                   │
│  • 显示实时进度                                            │
└───────────────────────────────────────────────────────────┘
                            ↕ HTTP API
┌───────────────────────────────────────────────────────────┐
│              Python 后台服务（处理层）                      │
│  • FastAPI / Flask 提供 RESTful API                       │
│  • PDF 解析 + OCR                                         │
│  • OpenAI / Claude AI 评估                                │
│  • 生成个性化话术                                          │
│  • 飞书 API 集成                                          │
│  • 任务队列（Celery + Redis）                             │
└───────────────────────────────────────────────────────────┘
                            ↕
┌───────────────────────────────────────────────────────────┐
│              数据存储层                                     │
│  • PostgreSQL：任务、候选人、日志                          │
│  • Redis：缓存、任务队列                                   │
│  • 飞书多维表格：最终结果展示                               │
│  • 对象存储（阿里云OSS/腾讯COS）：简历文件                  │
└───────────────────────────────────────────────────────────┘
```

### 2.2 为什么选择混合架构？

| 对比项 | 纯插件方案 | 纯 Selenium 方案 | **混合方案（选择）** |
|--------|-----------|-----------------|---------------------|
| 反爬风险 | 🟢 低 | 🔴 高 | 🟢 低 |
| 自动化程度 | 🟡 半自动 | 🟢 全自动 | 🟢 全自动 |
| 多账号支持 | 🔴 不支持 | 🟢 支持 | 🟢 支持（多用户） |
| 用户体验 | 🟢 好 | 🔴 差 | 🟢 好 |
| 开发复杂度 | 🟢 低 | 🟡 中 | 🟡 中 |
| 稳定性 | 🟡 中 | 🟢 高 | 🟢 高 |

**核心优势**：
- ✅ **低风险**：插件在真实浏览器中运行，不会被反爬检测
- ✅ **高可控**：用户可随时暂停、查看进度
- ✅ **易扩展**：后台服务可以支持多个插件实例
- ✅ **职责分离**：插件负责采集，后台负责处理

---

## 3. 详细功能需求

### 3.1 Chrome 插件功能（前端）

#### 3.1.1 控制面板 UI

**位置**：左下角浮动面板（可拖拽）

```
┌─────────────────────────────────┐
│  🤖 AI 猎头助手                  │
├─────────────────────────────────┤
│  账号状态: ●已登录 @138****1234  │
│  后台服务: ●已连接               │
├─────────────────────────────────┤
│  任务配置:                       │
│  JD模板: [AI产品经理 ▼]         │
│  起始位置: [1]                   │
│  处理数量: [50]                  │
│  ☑ 自动打招呼（推荐等级）         │
├─────────────────────────────────┤
│  [🚀 开始任务]  [⏸ 暂停]  [⏹ 停止]│
├─────────────────────────────────┤
│  进度: ████████░░░░  35/50 (70%)│
│  状态: 🔄 正在处理：王女士        │
│  • 已推荐: 12                    │
│  • 一般: 15                      │
│  • 不推荐: 8                     │
│  • 已打招呼: 12                  │
├─────────────────────────────────┤
│  [📊 查看飞书表] [⚙️ 设置]       │
└─────────────────────────────────┘
```

#### 3.1.2 核心功能模块

**模块 1：列表采集**
```javascript
// 功能描述
- 自动滚动到指定起始位置
- 逐个提取候选人卡片信息：
  • 姓名
  • 年龄
  • 工作年限
  • 当前公司
  • 当前职位
  • 期望薪资
  • 在线状态（本周活跃/刚刚活跃）
  • 简历预览 URL

// 去重逻辑
- 检查候选人是否已处理（查询后台）
- 如果已存在，跳过并标记"已处理"
```

**模块 2：简历下载**
```javascript
// 功能描述
- 自动点击候选人卡片进入详情页
- 判断简历格式：
  • PDF 可下载 → 点击下载按钮
  • 网页版简历 → 提取 HTML 内容
  • 加密简历 → 截图整页（滚动截图）

// 异常处理
- 简历加载超时（>10秒）→ 重试3次
- 需付费查看 → 标记"付费简历"，跳过
- 简历不可用 → 标记"无简历"，跳过
```

**模块 3：数据上传**
```javascript
// 功能描述
- 将候选人信息 + 简历文件发送到后台 API
- 等待后台返回 AI 评估结果
- 在面板显示实时状态

// API 接口
POST /api/candidates/process
Body: {
  "candidateInfo": { ... },
  "resumeFile": "<base64_encoded_pdf>",
  "taskConfig": {
    "jdTemplate": "AI产品经理",
    "autoGreeting": true
  }
}

Response: {
  "candidateId": "BOSS_20251113_001",
  "matchScore": 78,
  "recommendLevel": "推荐",
  "tags": ["AI经验", "大厂背景"],
  "greeting": "王女士，看到您在腾讯负责的AI产品很有亮点...",
  "feishuUrl": "https://feishu.cn/base/xxx"
}
```

**模块 4：自动打招呼**
```javascript
// 功能描述（可选，通过开关控制）
- 仅对"推荐"等级候选人执行
- 自动点击"打招呼"按钮
- 填入后台返回的个性化话术
- 模拟人类输入（逐字输入，随机延迟）
- 确认发送
- 更新后台状态

// 限流策略
- 每次发送间隔 30-90 秒（随机）
- 每日上限 100 条（Boss 限制）
- 发送时间窗口：9:00-21:00
```

#### 3.1.3 用户设置页

**JD 模板管理**：
```
【JD 模板列表】
• AI产品经理（C端）
• AI产品经理（B端）
• 产品运营（增长方向）
[+ 新建模板]

【编辑 JD 模板】
职位名称: AI产品经理（C端）
工作地点: [北京] [深圳] [+添加]
薪资范围: 30K - 60K
工作年限: 3-5 年
学历要求: 本科及以上

核心技能（必须）:
☑ AI产品经验（2年以上）
☑ C端产品（DAU>100万）
☑ 大模型应用（RAG/Agent）

加分技能（可选）:
☐ 大厂背景
☐ 0-1产品经验
☐ B端+C端复合背景

[保存]  [测试评估]
```

**后台服务配置**：
```
后台 API 地址: http://localhost:8000
API Token: sk-xxx
状态: ●已连接  [测试连接]

飞书配置:
App ID: cli_xxx
App Secret: ***
多维表格: [选择表格 ▼]
状态: ●已授权  [重新授权]
```

---

### 3.2 后台服务功能（Python）

#### 3.2.1 API 接口设计

**接口 1：处理候选人**
```python
POST /api/candidates/process

请求参数:
{
  "candidateInfo": {
    "name": "王女士",
    "age": 26,
    "workYears": 3,
    "currentCompany": "腾讯科技（深圳）",
    "currentPosition": "产品经理",
    "expectedSalary": "30-60K",
    "education": "本科",
    "university": "东北财经大学",
    "activeStatus": "本周活跃",
    "sourceUrl": "https://www.zhipin.com/..."
  },
  "resumeFile": "<base64_pdf_or_image>",
  "resumeType": "pdf | image | html",
  "taskConfig": {
    "jdTemplate": "AI产品经理（C端）",
    "autoGreeting": true
  }
}

返回结果:
{
  "success": true,
  "data": {
    "candidateId": "BOSS_20251113_001",
    "structuredResume": { ... },
    "evaluation": {
      "matchScore": 78,
      "recommendLevel": "推荐",
      "skillMatch": 85,
      "experienceMatch": 75,
      "educationMatch": 90,
      "stabilityScore": 70,
      "tags": ["AI经验", "大厂背景", "C端产品"],
      "strengths": ["腾讯C端产品经验", "AI方向深耕2年"],
      "risks": ["跳槽频率偏高", "B端经验不足"],
      "summary": "候选人在腾讯负责过AI产品，经验与JD高度匹配..."
    },
    "greeting": "王女士，看到您在腾讯负责的AI产品很有亮点！...",
    "feishuRecordId": "recXXX",
    "feishuUrl": "https://feishu.cn/base/xxx"
  }
}
```

**接口 2：查询候选人是否已存在**
```python
GET /api/candidates/check?name=王女士&company=腾讯科技

返回:
{
  "exists": true,
  "candidateId": "BOSS_20251113_001",
  "lastProcessedAt": "2025-11-13T10:23:45Z"
}
```

**接口 3：获取 JD 模板列表**
```python
GET /api/jd-templates

返回:
{
  "templates": [
    {
      "id": "jd_001",
      "name": "AI产品经理（C端）",
      "position": "AI产品经理",
      "location": ["北京", "深圳"],
      "salaryRange": "30-60K",
      "requiredSkills": [...],
      "optionalSkills": [...],
      "weights": {
        "skillMatch": 0.4,
        "experienceMatch": 0.3,
        "education": 0.15,
        "stability": 0.15
      }
    }
  ]
}
```

**接口 4：更新打招呼状态**
```python
POST /api/candidates/{candidateId}/greeting-status

请求参数:
{
  "status": "已发送 | 发送失败",
  "sentAt": "2025-11-13T10:25:30Z",
  "greetingContent": "王女士，看到您在腾讯..."
}

返回:
{
  "success": true
}
```

#### 3.2.2 核心处理流程

**流程 1：简历解析**
```python
# 步骤
1. 接收简历文件（PDF/图片/HTML）
2. 根据类型选择解析方式：
   - PDF: PyPDF2 + pdfplumber
   - 图片: 腾讯OCR / 百度OCR
   - HTML: BeautifulSoup
3. 提取文本内容
4. 调用大模型进行结构化提取

# 结构化输出
{
  "基本信息": {
    "姓名": "王女士",
    "年龄": 26,
    "工作年限": 3,
    "当前公司": "腾讯科技（深圳）",
    "当前职位": "产品经理",
    "学历": "本科",
    "毕业院校": "东北财经大学"
  },
  "工作经历": [
    {
      "公司": "腾讯科技（深圳）",
      "职位": "产品经理",
      "时间": "2022.04-2023.04",
      "工作内容": [
        "负责AI社区产品的迭代优化",
        "通过AI推荐算法提升用户留存20%"
      ],
      "核心成果": [
        "DAU提升35%",
        "用户满意度提升10%"
      ]
    }
  ],
  "项目经验": [
    {
      "项目名称": "AI内容推荐系统",
      "项目描述": "基于大模型的个性化推荐",
      "个人职责": "产品设计、需求分析",
      "技术栈": ["大模型", "推荐算法", "A/B测试"],
      "项目成果": "推荐点击率提升20%"
    }
  ],
  "技能清单": ["AI产品", "用户研究", "数据分析", "Figma", "Axure"],
  "教育背景": [
    {
      "学校": "东北财经大学",
      "学历": "本科",
      "专业": "工商管理",
      "时间": "2016-2020"
    }
  ]
}
```

**流程 2：AI 匹配度评估**
```python
# AI Prompt 设计
"""
你是一个专业的猎头顾问。
请根据职位需求（JD）和候选人简历，评估匹配度。

【职位需求】
{jd_config}

【候选人简历】
{structured_resume}

请按以下维度评分（0-100分）：

1. **技能匹配度（权重40%）**
   - 核心技能覆盖率
   - 技能深度（年限、项目复杂度）
   - 加分技能

2. **经验匹配度（权重30%）**
   - 行业经验
   - 公司规模经验
   - 产品类型经验
   - 项目成果量化

3. **教育背景（权重15%）**
   - 学历匹配
   - 专业相关性
   - 学校档次

4. **稳定性（权重15%）**
   - 平均任职时长
   - 跳槽频率
   - 职业发展路径连贯性

输出JSON格式：
{
  "技能匹配度": 85,
  "技能匹配分析": "...",
  "经验匹配度": 75,
  "经验匹配分析": "...",
  "教育背景得分": 90,
  "教育分析": "...",
  "稳定性得分": 70,
  "稳定性分析": "...",
  "综合匹配度": 78,
  "推荐等级": "推荐",
  "核心优势": ["大厂背景", "C端产品经验丰富"],
  "潜在风险": ["跳槽频率偏高"],
  "推荐理由": "候选人在腾讯负责过AI产品，经验与JD高度匹配"
}
"""

# 推荐等级映射
综合匹配度 >= 75%  → "推荐"（绿色）
综合匹配度 60-74% → "一般"（黄色）
综合匹配度 < 60%  → "不推荐"（红色）
```

**流程 3：话术生成**
```python
# AI Prompt 设计
"""
你是一位专业的猎头顾问。
请根据候选人简历和职位信息，生成一条个性化的打招呼话术。

【职位信息】
职位: {jd_name}
公司: {company_name}
亮点: {company_highlights}

【候选人信息】
姓名: {candidate_name}
当前公司: {current_company}
核心优势: {core_strengths}

【话术要求】
1. 字数: 80-100字（Boss直聘限制100字）
2. 称呼: 使用{candidate_name}+职位
3. 亮点: 提及具体项目/公司/技能
4. 吸引力: 突出职位亮点
5. 行动: 明确下一步
6. 避免: 敏感词（挖人/跳槽）

【示例】
"{candidate_name}，看到您在{current_company}负责的{project_name}项目很有亮点！
我这边有个{company_name}的{jd_name}机会，团队在做{product_direction}，
薪资{salary_range}，和您的背景很匹配，方便简单聊几句吗？"

请生成话术（纯文本）：
"""

# 长度控制
if len(greeting) > 100:
    greeting = greeting[:97] + "..."
```

**流程 4：飞书入库**
```python
# 飞书多维表结构
table_fields = {
    "候选人ID": "BOSS_20251113_001",
    "姓名": "王女士",
    "来源平台": "Boss直聘",
    "简历文件": [{"file_token": "xxx"}],  # 上传到飞书云文档
    "匹配度": 78,
    "推荐等级": "推荐",
    "评估状态": "分析成功",
    "技能标签": ["AI经验", "大厂背景"],
    "AI分析摘要": "候选人在腾讯负责过AI产品...",
    "核心优势": "1. 腾讯C端产品经验\n2. AI方向深耕2年",
    "潜在风险": "跳槽频率偏高",
    "当前公司": "腾讯科技（深圳）",
    "当前职位": "产品经理",
    "工作年限": 3,
    "期望薪资": "30-60K",
    "学历": "本科",
    "毕业院校": "东北财经大学",
    "在线状态": "本周活跃",
    "打招呼状态": "已发送",
    "打招呼时间": "2025-11-13 10:25:30",
    "打招呼内容": "王女士，看到您在腾讯...",
    "求职岗位": "AI产品经理（C端）",
    "负责HR": "@张猎头",
    "数据来源链接": "https://www.zhipin.com/...",
    "采集时间": "2025-11-13 10:23:15",
    "更新时间": "2025-11-13 10:25:30"
}

# 去重逻辑
existing_record = feishu_client.search_records(
    filter={
        "姓名": candidate_name,
        "当前公司": current_company
    }
)

if existing_record:
    # 更新记录
    feishu_client.update_record(record_id, new_data)
else:
    # 创建新记录
    feishu_client.create_record(table_fields)
```

---

### 3.3 飞书多维表结构

**表名**: `AI招聘-候选人库`

| 字段名 | 字段类型 | 说明 | 示例 |
|--------|---------|------|------|
| 候选人ID | 单行文本（主键） | 自动生成 | `BOSS_20251113_001` |
| 姓名 | 单行文本 | - | 王女士 |
| 来源平台 | 单选 | Boss/猎聘/脉脉 | Boss直聘 |
| 简历文件 | 附件 | PDF/截图 | 📄 resume.pdf |
| 匹配度 | 数字 | 0-100 | 78 |
| 推荐等级 | 单选 | 推荐/一般/不推荐 | 推荐 ✅ |
| 评估状态 | 单选 | 分析成功/失败/待分析 | 分析成功 |
| 技能标签 | 多选 | 自动生成 | AI经验、大厂背景 |
| AI分析摘要 | 多行文本 | - | 候选人在腾讯... |
| 核心优势 | 多行文本 | - | 1. C端产品经验... |
| 潜在风险 | 多行文本 | - | 跳槽频率偏高 |
| 当前公司 | 单行文本 | - | 腾讯科技（深圳） |
| 当前职位 | 单行文本 | - | 产品经理 |
| 工作年限 | 数字 | - | 3 |
| 期望薪资 | 单行文本 | - | 30-60K |
| 学历 | 单选 | 本科/硕士/博士 | 本科 |
| 毕业院校 | 单行文本 | - | 东北财经大学 |
| 在线状态 | 单选 | 本周活跃/一周前活跃 | 本周活跃 |
| 打招呼状态 | 单选 | 未联系/已发送/已回复/已拒绝 | 已发送 |
| 打招呼时间 | 日期时间 | - | 2025-11-13 10:25 |
| 打招呼内容 | 多行文本 | - | 王女士，看到您... |
| 求职岗位 | 单行文本 | JD名称 | AI产品经理（C端） |
| 负责HR | 人员 | @某某 | @张猎头 |
| 备注 | 多行文本 | 人工标注 | 候选人对薪资敏感 |
| 数据来源链接 | URL | Boss原始链接 | https://... |
| 采集时间 | 日期时间 | - | 2025-11-13 10:23 |
| 更新时间 | 日期时间 | 自动更新 | 2025-11-13 10:25 |

---

## 4. 技术实现细节

### 4.1 Chrome 插件技术栈

```javascript
// manifest.json (Manifest V3)
{
  "manifest_version": 3,
  "name": "AI猎头助手",
  "version": "1.0.0",
  "permissions": [
    "storage",
    "downloads",
    "tabs",
    "scripting"
  ],
  "host_permissions": [
    "*://www.zhipin.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["*://www.zhipin.com/*"],
      "js": ["content.js"],
      "css": ["content.css"]
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": "icon.png"
  }
}
```

**文件结构**：
```
chrome-extension/
├── manifest.json
├── popup.html              # 插件弹窗（设置页）
├── popup.js
├── content.js              # 注入Boss页面的脚本
├── content.css             # 控制面板样式
├── background.js           # 后台任务
├── config.js               # 配置管理
├── api.js                  # 后台API调用
└── utils.js                # 工具函数
```

### 4.2 后台服务技术栈

**框架**: FastAPI (Python 3.10+)

**核心依赖**：
```txt
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# 简历解析
PyPDF2==3.0.1
pdfplumber==0.10.3
pytesseract==0.3.10
Pillow==10.1.0

# AI
openai==1.3.0
anthropic==0.7.0  # Claude

# 飞书
lark-oapi==1.2.8

# 数据库
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1

# 任务队列
celery==5.3.4

# 工具
python-dotenv==1.0.0
loguru==0.7.2
tenacity==8.2.3  # 重试
```

**项目结构**：
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── candidates.py       # 候选人API
│   │   ├── jd_templates.py     # JD模板API
│   │   └── health.py           # 健康检查
│   ├── services/
│   │   ├── __init__.py
│   │   ├── resume_parser.py    # 简历解析
│   │   ├── ai_evaluator.py     # AI评估
│   │   ├── greeting_generator.py  # 话术生成
│   │   └── feishu_client.py    # 飞书集成
│   ├── models/
│   │   ├── __init__.py
│   │   ├── candidate.py        # 数据模型
│   │   └── jd_template.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── candidate.py        # Pydantic 模型
│   │   └── response.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py          # 数据库连接
│   │   └── redis_client.py     # Redis客户端
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # 日志配置
│       └── ocr.py              # OCR工具
├── tests/
│   ├── test_parser.py
│   ├── test_ai.py
│   └── test_api.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

### 4.3 数据库设计

**PostgreSQL 表结构**：

```sql
-- 候选人表
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100),
    source_platform VARCHAR(20),
    current_company VARCHAR(200),
    current_position VARCHAR(100),
    work_years INTEGER,
    education VARCHAR(20),
    university VARCHAR(200),
    expected_salary VARCHAR(50),
    active_status VARCHAR(50),
    source_url TEXT,
    resume_file_path TEXT,
    structured_resume JSONB,
    match_score INTEGER,
    recommend_level VARCHAR(20),
    tags TEXT[],
    strengths TEXT,
    risks TEXT,
    summary TEXT,
    greeting_status VARCHAR(20),
    greeting_content TEXT,
    greeting_sent_at TIMESTAMP,
    jd_template_id INTEGER,
    hr_user_id INTEGER,
    feishu_record_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- JD 模板表
CREATE TABLE jd_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    position VARCHAR(100),
    location TEXT[],
    salary_range VARCHAR(50),
    work_years_range VARCHAR(20),
    education_requirement VARCHAR(20),
    required_skills JSONB,
    optional_skills JSONB,
    evaluation_weights JSONB,
    company_highlights TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任务表
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(200),
    jd_template_id INTEGER,
    start_position INTEGER,
    target_count INTEGER,
    processed_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    status VARCHAR(20),  -- pending/running/paused/completed/failed
    auto_greeting BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表（HR）
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    boss_account VARCHAR(50),
    api_token VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. 开发计划

### Phase 1: 基础架构（Week 1）

**Chrome 插件**：
- [x] 项目初始化
- [ ] 控制面板 UI 开发
- [ ] 候选人列表采集逻辑
- [ ] 简历下载功能
- [ ] 后台 API 通信

**后台服务**：
- [ ] FastAPI 项目搭建
- [ ] 数据库设计 & 迁移
- [ ] API 接口开发
- [ ] 简历解析（PDF优先）

**交付物**：
- 能完整跑通"采集→上传→解析"流程

---

### Phase 2: AI 评估（Week 2）

**后台服务**：
- [ ] OpenAI API 集成
- [ ] 结构化简历提取
- [ ] 匹配度评估算法
- [ ] 标签自动生成
- [ ] 话术生成

**飞书集成**：
- [ ] 飞书 API 认证
- [ ] 多维表格写入
- [ ] 文件上传到飞书云文档
- [ ] 去重逻辑

**交付物**：
- 完整的"采集→解析→评估→入库"流程

---

### Phase 3: 自动打招呼（Week 3）

**Chrome 插件**：
- [ ] 自动打招呼逻辑
- [ ] 模拟人类输入
- [ ] 限流控制
- [ ] 状态更新

**后台服务**：
- [ ] 打招呼状态管理
- [ ] 任务队列（Celery）
- [ ] 日志记录

**交付物**：
- 全流程自动化（包含打招呼）

---

### Phase 4: 优化与测试（Week 4）

**功能优化**：
- [ ] 异常处理完善
- [ ] 性能优化
- [ ] OCR 支持（兜底）
- [ ] 实时进度展示

**测试**：
- [ ] 单元测试
- [ ] 集成测试
- [ ] 真实环境测试（处理50份简历）

**文档**：
- [ ] 用户手册
- [ ] 部署文档
- [ ] API 文档

**交付物**：
- 可生产使用的稳定版本

---

## 6. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| **Boss 账号封禁** | 🔴 高 | 1. 限流策略（30-90秒间隔）<br>2. 仅在9:00-21:00发送<br>3. 每日上限100条<br>4. 准备备用账号 |
| **平台 UI 变化** | 🟡 中 | 1. 选择器多重备份<br>2. 定期检查<br>3. 快速更新机制 |
| **AI 成本** | 🟡 中 | 1. GPT-4o-mini 做话术<br>2. 批量处理<br>3. 结果缓存 |
| **简历格式多样** | 🟡 中 | 1. PDF优先<br>2. OCR兜底<br>3. 人工复核异常 |
| **法律合规** | 🔴 高 | 1. 仅内部使用<br>2. 隐私保护<br>3. 咨询法律顾问 |

---

## 7. 成本估算

### 7.1 开发成本
- 开发周期: 4 周
- 人力: 1 全栈工程师

### 7.2 运营成本（每月）
```
OpenAI API: $60-100
OCR: $10-20
服务器: ¥300
飞书: 免费版
─────────────────
总计: ~¥1000/月
```

### 7.3 ROI 分析
```
猎头时间节省: 4小时/天 × 22天 = 88小时/月
按时薪¥200计算: ¥17,600/月
ROI: 1700%
```

---

## 8. 后续扩展（v2.0+）

**平台扩展**：
- [ ] 猎聘网
- [ ] 脉脉
- [ ] LinkedIn

**功能扩展**：
- [ ] 候选人回复自动分类
- [ ] A/B 测试话术
- [ ] 数据分析看板
- [ ] 面试安排自动化

**智能化**：
- [ ] 智能推荐 JD 匹配候选人
- [ ] 自动学习优化评估标准
- [ ] 预测候选人回复率

---

## 附录

### A. 飞书授权配置指南
[待补充]

### B. Chrome 插件安装指南
[待补充]

### C. API 文档
[待补充]

### D. 常见问题 FAQ
[待补充]

---

**文档版本历史**：
- v2.0 (2025-11-13): 混合架构设计完成
- v1.0 (2025-11-12): 初始需求梳理

