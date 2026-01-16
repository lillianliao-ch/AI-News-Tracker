# 后端服务

FastAPI 后端服务 - AI 简历解析与评估

## ✅ 迁移状态

- ✅ FastAPI 应用已迁移
- ✅ AI 解析服务已集成
- ✅ API 路由已配置
- ⏳ pnpm 脚本待配置
- ⏳ Docker 支持待添加

## 🎯 功能

- ✅ 健康检查 API (`/health`)
- ✅ 候选人处理 API (`/api/candidates/process`)
- ✅ PDF 简历解析
- ✅ AI 结构化提取（通义千问）
- ✅ 匹配度评估
- ✅ Mock 数据生成（用于测试）

## 🛠️ 技术栈

- **框架**: FastAPI
- **Python**: 3.11+
- **AI**: 通义千问 (Qwen-turbo)
- **PDF**: pdfplumber
- **数据验证**: Pydantic
- **HTTP**: httpx

## 📁 目录结构

```
apps/backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── schemas.py           # Pydantic 数据模型
│   ├── services/
│   │   ├── __init__.py
│   │   └── ai_parser.py     # AI 解析服务
│   └── utils/
│       └── __init__.py
├── data/                    # 数据目录
│   ├── cache/               # 缓存
│   └── resumes/             # 简历文件
├── requirements.txt         # Python 依赖
├── env.example              # 环境变量模板
├── .env                     # 环境变量（不提交）
├── test_api.py              # API 测试脚本
├── package.json             # npm 脚本配置
├── 快速开始.md              # 快速上手指南
└── README.md                # 本文件
```

## 🚀 快速开始

查看 [快速开始.md](./快速开始.md) 了解详细步骤。

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp env.example .env
# 编辑 .env，填入 QWEN_API_KEY
```

### 3. 启动服务
```bash
uvicorn app.main:app --reload
```

### 4. 访问文档
- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📡 API 端点

### GET `/health`
健康检查

**响应**:
```json
{
  "status": "ok",
  "message": "API is running"
}
```

### POST `/api/candidates/process`
处理候选人简历

**请求体**:
```json
{
  "candidate_info": {
    "name": "张三",
    "age": 30,
    "work_years": 8,
    // ... 更多字段
  },
  "resume_text": "简历文本内容...",
  "resume_file": "base64编码的PDF",
  "jd_config": {
    "position": "AI工程师",
    "requirements": ["Python", "AI"]
  }
}
```

**响应**:
```json
{
  "success": true,
  "structured_resume": { /* 结构化简历 */ },
  "evaluation": { /* AI 评估结果 */ },
  "resume_text": "原始简历文本",
  "processing_time": 2.5,
  "message": "处理成功"
}
```

## 🧪 测试

```bash
# 运行测试脚本
python test_api.py

# 使用 curl 测试
curl http://localhost:8000/health
```

## 🔧 开发

### 添加新的 API 端点

1. 在 `app/main.py` 中添加路由
2. 在 `app/schemas.py` 中定义数据模型
3. 在 `app/services/` 中实现业务逻辑

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `QWEN_API_KEY` | 通义千问 API Key | 必填 |
| `QWEN_MODEL` | 模型名称 | `qwen-turbo` |
| `QWEN_API_BASE` | API 地址 | 官方地址 |

## 📊 性能

- **处理时间**: 2-5 秒/份简历
- **并发支持**: FastAPI 异步支持
- **成本**: ~¥0.03/份简历（通义千问）

## 🔄 下一步

- [ ] 添加数据库支持（PostgreSQL）
- [ ] 添加缓存层（Redis）
- [ ] 实现批量处理队列
- [ ] 添加飞书 API 集成
- [ ] 配置 Docker 部署
- [ ] 添加单元测试

## 📖 相关文档

- [项目进度](../../docs/mvp/项目进度.md)
- [API 使用示例](./test_api.py)
- [通义千问指南](../../docs/tech/通义千问-使用指南.md)
