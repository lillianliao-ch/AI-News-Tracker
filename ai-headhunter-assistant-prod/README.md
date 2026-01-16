# AI 猎头助手 - 自动筛选简历系统

> **混合架构**：Chrome 浏览器插件 + Python 后台服务

一个帮助猎头自动化处理候选人简历的 AI 助手系统，可以自动采集、解析、评估简历，并自动打招呼。

---

## 📋 项目文档

### 产品文档 (docs/prd/)
| 文档 | 说明 |
|------|------|
| [PRD-AI自动筛选简历系统](./docs/prd/PRD-AI自动筛选简历系统.md) | 完整产品需求文档 |
| [开发路线图](./docs/prd/开发路线图.md) | 4周开发计划 |
| [MVP-开发计划](./docs/prd/MVP-开发计划.md) | MVP 快速迭代计划 |

### 技术文档 (docs/tech/)
| 文档 | 说明 |
|------|------|
| [CURSOR-SUBAGENT-使用指南](./docs/tech/CURSOR-SUBAGENT-使用指南.md) | 如何使用 Cursor AI 开发 |
| [Cursor-Multi-Agent-指南](./docs/tech/Cursor-Multi-Agent-指南.md) | 多 Agent 协作开发指南 |
| [如何选择合适的Agent](./docs/tech/如何选择合适的Agent.md) | Agent 选择速查表 ⭐ 新手必读 |
| [通义千问-使用指南](./docs/tech/通义千问-使用指南.md) | Qwen API 使用说明 |
| [快速测试](./docs/tech/快速测试.md) | 插件测试指南 |

### MVP 文档 (docs/mvp/)
| 文档 | 说明 |
|------|------|
| [项目进度](./docs/mvp/项目进度.md) | Day 1-7 开发总结 |
| [Day8-10开发规划](./docs/mvp/Day8-10开发规划.md) | 剩余任务详细规划 ⭐ 当前 |
| [Day3-插件测试清单](./docs/mvp/Day3-插件测试清单.md) | 插件功能测试 |
| [项目启动指南](./docs/mvp/项目启动指南.md) | 快速上手指南 |

### 其他文档 (docs/)
| 文档 | 说明 |
|------|------|
| [项目重构计划-Monorepo](./docs/项目重构计划-Monorepo.md) | Monorepo 架构设计 |
| [项目目录整理建议](./docs/项目目录整理建议.md) | 目录结构优化方案 |

### 变更日志
| 文档 | 说明 |
|------|------|
| [CHANGELOG](./CHANGELOG.md) | 版本更新记录 |

---

## 🎯 核心功能

### ✅ 已规划功能

1. **自动采集候选人**
   - 在 Boss 直聘自动读取候选人列表
   - 自动滚动、点击、进入详情页
   - 提取候选人基本信息

2. **简历下载与解析**
   - 自动下载 PDF 简历
   - PDF 解析 + OCR（兜底）
   - 结构化提取简历内容

3. **AI 智能评估**
   - OpenAI / Claude 结构化简历
   - 匹配度评估（0-100分）
   - 推荐等级（推荐/一般/不推荐）
   - 自动生成标签

4. **飞书多维表入库**
   - 自动写入候选人信息
   - 上传简历文件
   - 去重逻辑
   - 实时更新状态

5. **自动打招呼**
   - AI 生成个性化话术
   - 模拟人类操作发送
   - 限流策略（避免封号）

---

## 🏗️ 技术架构

```
┌────────────────────────────────────────────┐
│     Chrome 插件（采集控制层）               │
│  • 页面操作自动化                          │
│  • 简历下载                                │
│  • 实时进度显示                            │
└────────────────────────────────────────────┘
                    ↕ HTTP API
┌────────────────────────────────────────────┐
│     Python 后台（处理层）                   │
│  • FastAPI RESTful API                    │
│  • AI 评估（OpenAI/Claude）                │
│  • PDF 解析 + OCR                          │
│  • 飞书 API 集成                           │
└────────────────────────────────────────────┘
                    ↕
┌────────────────────────────────────────────┐
│     数据存储层                              │
│  • PostgreSQL（候选人、任务）              │
│  • Redis（缓存、任务队列）                 │
│  • 飞书多维表（结果展示）                  │
│  • 对象存储（简历文件）                    │
└────────────────────────────────────────────┘
```

---

## 📁 项目结构（规划）

```
ai-headhunter-assistant/
├── README.md                          # 本文件
├── PRD-AI自动筛选简历系统.md           # 产品需求文档
├── CURSOR-SUBAGENT-使用指南.md        # Subagent 使用指南
│
├── chrome-extension/                  # Chrome 浏览器插件
│   ├── manifest.json                  # 插件配置
│   ├── popup.html                     # 插件弹窗（设置页）
│   ├── popup.js
│   ├── content.js                     # 注入 Boss 页面的脚本
│   ├── content.css                    # 控制面板样式
│   ├── background.js                  # 后台任务
│   ├── config.js                      # 配置管理
│   ├── api.js                         # 后台 API 调用
│   ├── utils.js                       # 工具函数
│   └── icons/                         # 插件图标
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
├── backend/                           # Python 后台服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI 入口
│   │   ├── config.py                  # 配置管理
│   │   │
│   │   ├── api/                       # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── candidates.py          # 候选人 API
│   │   │   ├── jd_templates.py        # JD 模板 API
│   │   │   └── health.py              # 健康检查
│   │   │
│   │   ├── services/                  # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── resume_parser.py       # 简历解析
│   │   │   ├── ai_evaluator.py        # AI 评估
│   │   │   ├── greeting_generator.py  # 话术生成
│   │   │   └── feishu_client.py       # 飞书集成
│   │   │
│   │   ├── models/                    # 数据库模型
│   │   │   ├── __init__.py
│   │   │   ├── candidate.py
│   │   │   ├── jd_template.py
│   │   │   └── task.py
│   │   │
│   │   ├── schemas/                   # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── candidate.py
│   │   │   ├── jd_template.py
│   │   │   └── response.py
│   │   │
│   │   ├── database/                  # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # 数据库连接
│   │   │   └── redis_client.py        # Redis 客户端
│   │   │
│   │   └── utils/                     # 工具函数
│   │       ├── __init__.py
│   │       ├── logger.py              # 日志配置
│   │       └── ocr.py                 # OCR 工具
│   │
│   ├── tests/                         # 测试
│   │   ├── __init__.py
│   │   ├── test_parser.py
│   │   ├── test_ai.py
│   │   └── test_api.py
│   │
│   ├── alembic/                       # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── requirements.txt               # Python 依赖
│   ├── Dockerfile                     # Docker 配置
│   ├── docker-compose.yml             # Docker Compose 配置
│   └── .env.example                   # 环境变量示例
│
├── docs/                              # 文档
│   ├── 技术架构设计.md
│   ├── API文档.md
│   ├── 部署指南.md
│   ├── 用户手册.md
│   └── FAQ.md
│
├── scripts/                           # 脚本
│   ├── init_database.py               # 初始化数据库
│   ├── test_connection.py             # 测试连接
│   └── migrate.sh                     # 数据库迁移
│
└── .gitignore
```

---

## 🚀 开发计划（4周）

### Week 1: 基础架构（Day 1-5）

**目标**：搭建插件和后台的基础框架

- [ ] Chrome 插件项目初始化
  - [ ] manifest.json 配置
  - [ ] 控制面板 UI
  - [ ] 基础文件结构

- [ ] 后台服务项目初始化
  - [ ] FastAPI 项目搭建
  - [ ] 数据库设计与迁移
  - [ ] Docker 配置

- [ ] 核心功能 MVP
  - [ ] 候选人列表采集
  - [ ] 简历下载
  - [ ] PDF 解析
  - [ ] API 通信

**交付物**：能完整跑通"采集→上传→解析"流程

---

### Week 2: AI 评估与飞书集成（Day 6-10）

**目标**：实现 AI 智能评估和数据入库

- [ ] AI 模块
  - [ ] OpenAI API 集成
  - [ ] 简历结构化提取
  - [ ] 匹配度评估算法
  - [ ] 标签自动生成
  - [ ] 话术生成器

- [ ] 飞书集成
  - [ ] 飞书 API 认证
  - [ ] 多维表格 CRUD
  - [ ] 文件上传
  - [ ] 去重逻辑

**交付物**：完整的"采集→解析→评估→入库"流程

---

### Week 3: 自动打招呼（Day 11-15）

**目标**：实现自动打招呼功能

- [ ] 打招呼自动化
  - [ ] 自动点击、填充、发送
  - [ ] 模拟人类输入
  - [ ] 限流控制
  - [ ] 状态更新

- [ ] 任务队列
  - [ ] Celery 集成
  - [ ] 异步任务处理
  - [ ] 任务重试机制

**交付物**：全流程自动化（包含打招呼）

---

### Week 4: 测试与优化（Day 16-20）

**目标**：完善功能，准备生产部署

- [ ] 测试
  - [ ] 单元测试
  - [ ] 集成测试
  - [ ] 真实环境测试（处理 50 份简历）

- [ ] 优化
  - [ ] 异常处理完善
  - [ ] 性能优化
  - [ ] OCR 支持（兜底）
  - [ ] 日志完善

- [ ] 文档
  - [ ] 用户手册
  - [ ] 部署文档
  - [ ] API 文档

**交付物**：可生产使用的稳定版本 v1.0

---

## 🛠️ 技术栈

### Chrome 插件
- **框架**: Vanilla JavaScript (Manifest V3)
- **UI**: HTML + CSS
- **通信**: Chrome Extension API + Fetch API

### 后台服务
- **框架**: FastAPI (Python 3.10+)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **任务队列**: Celery
- **简历解析**: PyPDF2, pdfplumber, Tesseract OCR
- **AI**: OpenAI GPT-4o / Claude 3.5 Sonnet
- **飞书**: lark-oapi-python

### 部署
- **容器化**: Docker + Docker Compose
- **服务器**: 阿里云 ECS / 腾讯云 CVM
- **存储**: 阿里云 OSS / 腾讯云 COS

---

## 📦 快速开始

### 前置要求

1. **开发环境**
   - Node.js 18+ (Chrome 插件打包)
   - Python 3.10+
   - PostgreSQL 15
   - Redis 7

2. **账号准备**
   - OpenAI API Key
   - 飞书应用凭证（App ID + App Secret）
   - Boss 直聘账号（已登录）

### 安装步骤

> ⚠️ 注意：项目尚未开始开发，以下为规划中的安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/ai-headhunter-assistant.git
cd ai-headhunter-assistant
```

#### 2. 安装 Chrome 插件
```bash
cd chrome-extension
# 在 Chrome 中打开 chrome://extensions/
# 启用"开发者模式"
# 点击"加载已解压的扩展程序"
# 选择 chrome-extension 目录
```

#### 3. 启动后台服务

**方式一：后台运行（推荐，适合长期运行）**
```bash
# 在项目根目录执行
./scripts/start_backend.sh

# 查看服务状态
./scripts/status_backend.sh

# 停止服务
./scripts/stop_backend.sh
```

**方式二：前台运行（开发调试）**
```bash
cd apps/backend

# 复制环境变量配置
cp env.example .env
# 编辑 .env 填入你的 API Key 等信息

# 安装依赖
pip install -r requirements.txt

# 启动服务（开发模式，带热重载）
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> 💡 **提示**：使用后台运行方式，服务会在后台持续运行，你可以同时进行其他项目开发。详细说明请查看 [后台服务管理指南](./scripts/README_BACKEND.md)

#### 4. 初始化数据库
```bash
python scripts/init_database.py
```

#### 5. 测试连接
```bash
# 测试后台 API
curl http://localhost:8000/api/health

# 测试飞书连接
python scripts/test_connection.py --service feishu
```

---

## 🎮 使用指南

### 基本流程

1. **打开 Boss 直聘**，登录你的账号
2. **进入"推荐牛人"页面**
3. **点击插件图标**，打开控制面板
4. **选择 JD 模板**（或新建）
5. **设置处理数量**（建议先测试 10 份）
6. **点击"开始任务"**
7. **查看实时进度**
8. **任务完成后，前往飞书表格查看结果**

### 高级功能

- **自动打招呼**：在设置中开启（仅对"推荐"等级候选人）
- **JD 模板管理**：保存常用岗位的筛选条件
- **批量处理**：支持处理 50-200 份简历/天
- **去重逻辑**：自动跳过已处理的候选人

---

## 📊 效果预期

### 时间节省

| 场景 | 手动操作 | 自动化 | 节省时间 |
|------|---------|--------|---------|
| 看 1 份简历 | ~3 分钟 | ~30 秒 | **83%** |
| 筛选 50 份简历 | ~150 分钟 | ~25 分钟 | **83%** |
| 打招呼 50 人 | ~50 分钟 | ~5 分钟 | **90%** |
| **总计** | **~200 分钟** | **~30 分钟** | **85%** |

### 成本估算

**每月成本**：
```
OpenAI API: $60-100
OCR 服务: $10-20
服务器: ¥300
────────────────
总计: ~¥1000/月
```

**ROI**：
```
猎头时间节省: 4小时/天 × 22天 = 88小时/月
按时薪¥200计算: ¥17,600/月
投资回报率: 1700%
```

---

## 🚨 风险提示

### 1. 账号封禁风险

**Boss 直聘可能封禁自动化账号**

**应对措施**：
- ✅ 限流策略（30-90秒间隔）
- ✅ 仅在工作时间发送（9:00-21:00）
- ✅ 每日上限 100 条
- ✅ 准备备用账号

### 2. 平台 UI 变化

**Boss 网页结构可能改变，导致插件失效**

**应对措施**：
- ✅ 选择器多重备份
- ✅ 定期检查更新
- ✅ 快速更新机制

### 3. 法律合规

**未经候选人同意采集简历可能违规**

**应对措施**：
- ✅ 仅内部使用
- ✅ 数据加密存储
- ✅ 咨询法律顾问

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发规范

- 代码风格：遵循 PEP 8（Python）和 Airbnb（JavaScript）
- 提交规范：使用 Conventional Commits
- 测试：所有 PR 需包含单元测试

---

## 📄 开源协议

MIT License

---

## 📞 联系方式

- **项目负责人**: [你的名字]
- **邮箱**: your-email@example.com
- **问题反馈**: [GitHub Issues](https://github.com/your-username/ai-headhunter-assistant/issues)

---

## 🎓 学习资源

- [Chrome Extension 官方文档](https://developer.chrome.com/docs/extensions/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [飞书开放平台](https://open.feishu.cn/document/)
- [OpenAI API 文档](https://platform.openai.com/docs/)

---

## 🗺️ Roadmap

### v1.0（当前规划）
- [x] 项目立项和需求分析
- [ ] Chrome 插件开发
- [ ] 后台服务开发
- [ ] AI 评估集成
- [ ] 飞书集成
- [ ] 自动打招呼
- [ ] 测试与上线

### v1.1（后续迭代）
- [ ] 支持猎聘平台
- [ ] 支持脉脉平台
- [ ] A/B 测试话术
- [ ] 数据分析看板

### v2.0（远期规划）
- [ ] 候选人回复自动分类
- [ ] 面试安排自动化
- [ ] 智能推荐系统
- [ ] 移动端支持

---

**准备好开始开发了吗？** 

👉 查看 [CURSOR-SUBAGENT-使用指南](./docs/tech/CURSOR-SUBAGENT-使用指南.md) 了解如何使用 Cursor AI 助手高效开发！

📖 查看 [项目进度](./docs/mvp/项目进度.md) 了解当前开发状态（Day 1-7 已完成 90%）

🚀 **让我们继续开发吧！**

