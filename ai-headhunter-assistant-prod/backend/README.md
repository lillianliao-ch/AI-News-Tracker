# 后台 API 服务

## 📋 项目概述

AI 猎头助手后台服务，提供简历解析和评估 API。

**技术栈**：
- FastAPI 0.104.1
- Python 3.12
- 通义千问 AI
- pdfplumber（PDF 解析）

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板：
```bash
cp env.example .env
```

编辑 `.env` 文件，填入你的配置：
```env
AI_PROVIDER=qwen
AI_MODEL=qwen-turbo
AI_API_KEY=sk-your-api-key-here
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### 3. 启动服务

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后：
- API 地址：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

---

## 📡 API 接口

### 1. 健康检查

```bash
GET /health
```

**响应**：
```json
{
  "status": "ok",
  "service": "AI Headhunter API",
  "version": "1.0.0-mvp"
}
```

---

### 2. 处理候选人简历

```bash
POST /api/candidates/process
```

**请求体**：
```json
{
  "candidate_info": {
    "name": "张三",
    "source_platform": "Boss直聘",
    "current_company": "某公司",
    "current_position": "产品经理",
    "work_years": 5,
    "expected_salary": "30-50K",
    "education": "本科",
    "active_status": "本周活跃"
  },
  "resume_file": "<Base64 编码的 PDF>",
  "jd_config": {
    "position": "AI产品经理",
    "location": ["北京", "深圳"],
    "salary_range": "30-60K",
    "work_years": "3-5年",
    "education": "本科及以上",
    "required_skills": [
      "AI产品经验",
      "C端产品经验"
    ],
    "optional_skills": [
      "大厂背景"
    ]
  }
}
```

**响应**：
```json
{
  "success": true,
  "candidate_id": "BOSS_1763025426_4570ab",
  "candidate_info": { ... },
  "structured_resume": {
    "基本信息": {
      "姓名": "张三",
      "年龄": 30,
      "工作年限": 5,
      "当前公司": "某公司",
      "当前职位": "产品经理",
      "学历": "本科",
      "毕业院校": "某大学"
    },
    "工作经历": [ ... ],
    "技能清单": [ ... ],
    "教育背景": [ ... ]
  },
  "evaluation": {
    "技能匹配度": 85,
    "经验匹配度": 75,
    "教育背景得分": 90,
    "稳定性得分": 70,
    "综合匹配度": 78,
    "推荐等级": "推荐",
    "核心优势": [
      "大厂背景",
      "技术能力强"
    ],
    "潜在风险": [
      "跳槽频繁"
    ],
    "推荐理由": "候选人经验丰富...",
    "技能标签": ["AI", "产品", "大数据"]
  },
  "processing_time": 57.34,
  "message": "处理成功"
}
```

---

## 🧪 测试

### 使用测试脚本

```bash
python3 test_api.py
```

### 使用 curl

```bash
# 健康检查
curl http://localhost:8000/health

# 处理候选人（需要准备 request.json）
curl -X POST http://localhost:8000/api/candidates/process \
  -H "Content-Type: application/json" \
  -d @request.json
```

### 使用 Swagger 文档

访问 http://localhost:8000/docs，可以直接在浏览器中测试 API。

---

## 📁 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主应用
│   ├── config.py            # 配置管理
│   ├── schemas.py           # 数据模型
│   └── services/
│       ├── __init__.py
│       └── ai_parser.py     # AI 解析服务
├── data/
│   ├── resumes/             # 简历文件
│   └── cache/               # 缓存
├── requirements.txt         # 依赖
├── .env                     # 环境变量（不提交）
├── env.example              # 环境变量模板
├── test_api.py              # 测试脚本
└── README.md                # 本文件
```

---

## ⚙️ 配置说明

### AI 提供商

**通义千问**（推荐，默认）：
```env
AI_PROVIDER=qwen
AI_MODEL=qwen-turbo  # 或 qwen-plus, qwen-max
AI_API_KEY=sk-xxx
```

**OpenAI**（备选）：
```env
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini  # 或 gpt-4o
AI_API_KEY=sk-xxx
```

### 模型选择

| 模型 | 提供商 | 价格 | 速度 | 适用场景 |
|------|--------|------|------|---------|
| qwen-turbo | 通义千问 | ¥0.003/1K | 最快 | 日常使用（推荐） |
| qwen-plus | 通义千问 | ¥0.008/1K | 中等 | 复杂简历 |
| gpt-4o-mini | OpenAI | $0.15/1M | 快 | OpenAI 用户 |
| gpt-4o | OpenAI | $2.50/1M | 中等 | 高质量要求 |

---

## 🐛 常见问题

### Q1: 启动失败，提示模块导入错误

**解决**：确保在 `backend` 目录下运行命令
```bash
cd backend
python3 -m uvicorn app.main:app --reload
```

### Q2: API Key 无效

**解决**：检查 `.env` 文件中的 API Key 是否正确

### Q3: 简历解析失败

**可能原因**：
- PDF 是扫描件（需要 OCR，暂不支持）
- PDF 加密
- PDF 格式特殊

**解决**：尝试其他 PDF 简历

### Q4: 处理太慢

**优化方案**：
- 使用更快的模型（qwen-turbo）
- 限制简历长度（前 8000 字符）
- 升级服务器配置

---

## 📊 性能指标

**测试环境**：MacBook Pro M1, 16GB RAM

| 指标 | 数值 |
|------|------|
| PDF 解析 | 2-5 秒 |
| AI 提取 | 15-20 秒 |
| AI 评估 | 15-20 秒 |
| 总耗时 | 40-60 秒 |
| 成本（qwen-turbo） | ¥0.03/份 |

---

## 🔒 安全建议

1. **不要提交 `.env` 文件**到 Git
2. **定期更换 API Key**
3. **生产环境设置 `DEBUG=false`**
4. **配置 CORS 白名单**（不要使用 `*`）
5. **添加 API 认证**（生产环境）

---

## 📈 下一步

- [ ] 添加数据库（存储处理记录）
- [ ] 添加缓存（Redis）
- [ ] 添加任务队列（Celery）
- [ ] 添加用户认证
- [ ] 添加速率限制
- [ ] 添加日志系统
- [ ] 添加监控告警

---

## 📄 许可

MIT License

