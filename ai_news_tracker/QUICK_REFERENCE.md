# 🚀 AI News Tracker - 快速参考

## 📡 服务状态

| 服务 | 端口 | 状态 | 访问地址 |
|------|------|------|---------|
| 后端 (FastAPI) | 8000 | ✅ 运行中 | http://localhost:8000 |
| 前端 (Astro) | 4321 | ✅ 运行中 | http://localhost:4321 |
| AI 服务 (千问) | - | ✅ 已集成 | qwen-max |

## 🎯 核心功能

### 1. AI 资讯追踪
- ✅ 多源聚合（36氪、InfoQ、TechCrunch）
- ✅ AI 相关性过滤（80+ 关键词）
- ✅ 智能分类（产品、模型、融资、观点、研究、应用）
- ✅ 自动摘要生成

### 2. 小红书文案生成
- ✅ 三种风格（硬核技术、轻松科普、热点观点）
- ✅ 千问 API 驱动
- ✅ 可配置提示词
- ✅ 一键复制

## 📝 常用命令

### 启动服务
```bash
# 后端
cd /Users/lillianliao/notion_rag/ai_news_tracker/backend
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd /Users/lillianliao/notion_rag/ai_news_tracker/frontend
npm run dev
```

### 停止服务
```bash
# 后端
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill -9

# 前端
ps aux | grep "astro" | grep -v grep | awk '{print $2}' | xargs kill -9
```

### 测试 AI 服务
```bash
cd /Users/lillianliao/notion_rag/ai_news_tracker/backend
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 test_qwen.py
```

### 运行爬虫
```bash
cd /Users/lillianliao/notion_rag/ai_news_tracker/backend
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m tasks.crawler
```

### 查看日志
```bash
# 后端日志
tail -f /tmp/backend.log

# 或查看最近30行
tail -30 /tmp/backend.log
```

## 🔧 配置文件

| 文件 | 用途 |
|------|------|
| `backend/.env` | 环境变量（API Keys、模型配置） |
| `backend/config/base_config.py` | 基础配置 |
| `backend/config/prompts.py` | 提示词模板 |
| `backend/config/SOURCES_CONFIG` | RSS 数据源 |

## 🤖 AI 模型配置

### 千问（当前使用）
```env
OPENAI_API_KEY=sk-4e2bb9108e1541f9b7dd88855922c7a3
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max
```

### 切换到 OpenAI
```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

CLASSIFY_MODEL=gpt-4o-mini
SUMMARY_MODEL=gpt-3.5-turbo
GENERATE_MODEL=gpt-4o
```

### 切换到 Claude
```env
ANTHROPIC_API_KEY=sk-ant-your-api-key

CLASSIFY_MODEL=claude-3-5-sonnet-20241022
SUMMARY_MODEL=claude-3-5-haiku-20241022
GENERATE_MODEL=claude-3-5-sonnet-20241022
```

## 💰 成本参考

### 千问（qwen-max）
- **输入**: ¥0.02 / 1K tokens
- **输出**: ¥0.06 / 1K tokens
- **单次生成**: ~¥0.017
- **月度估算（100次/天）**: ~¥51

### OpenAI (GPT-4o)
- **输入**: $0.005 / 1K tokens
- **输出**: $0.015 / 1K tokens
- **单次生成**: ~$0.004
- **月度估算（100次/天）**: ~$12

### Claude (3.5 Sonnet)
- **输入**: $0.003 / 1K tokens
- **输出**: $0.015 / 1K tokens
- **单次生成**: ~$0.003
- **月度估算（100次/天）**: ~$9

## 🎨 小红书文案风格

### 版本 A: 硬核技术风
- **目标**: 技术人员、开发者
- **特点**: 专业术语、数据驱动、技术分析
- **提示词**: `config/prompts.py` → `PROMPT_VERSION_A`

### 版本 B: 轻松科普风
- **目标**: 大众用户、AI 初学者
- **特点**: 口语化、表情符号、生活化比喻
- **提示词**: `config/prompts.py` → `PROMPT_VERSION_B`

### 版本 C: 热点观点风
- **目标**: 行业从业者、投资机构
- **特点**: 有观点、有立场、引发讨论
- **提示词**: `config/prompts.py` → `PROMPT_VERSION_C`

## 📂 项目结构

```
ai_news_tracker/
├── backend/                    # 后端（FastAPI）
│   ├── config/                 # 配置
│   │   ├── base_config.py      # 基础配置
│   │   ├── prompts.py          # 提示词模板 ⭐
│   │   └── PROMPT_GUIDE.md     # 提示词指南
│   ├── services/               # 服务
│   │   └── ai_service.py       # AI服务
│   ├── tasks/                  # 任务
│   │   └── crawler.py          # RSS爬虫
│   ├── models/                 # 数据模型
│   ├── main.py                 # FastAPI应用
│   ├── test_qwen.py            # 千问测试脚本
│   └── .env                    # 环境变量 ⭐
│
├── frontend/                   # 前端（Astro）
│   └── src/
│       ├── components/         # 组件
│       │   ├── NewsCard.astro  # 资讯卡片
│       │   └── NewsGrid.astro  # 资讯网格
│       └── pages/              # 页面
│           └── index.astro     # 主页
│
├── QWEN_SETUP.md               # 千问配置指南
├── QWEN_INTEGRATION_COMPLETE.md # 集成完成文档
├── OPTIMIZATION_COMPLETE.md    # 优化完成文档
└── QUICK_REFERENCE.md          # 本文档
```

## 🐛 常见问题

### 后端无法启动
```bash
# 检查端口占用
lsof -i:8000

# 杀死占用进程
lsof -ti:8000 | xargs kill -9

# 重新启动
cd backend && /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 生成失败
```bash
# 检查 API Key 配置
cat backend/.env | grep OPENAI_API_KEY

# 查看后端日志
tail -f /tmp/backend.log

# 测试千问连接
cd backend && /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 test_qwen.py
```

### 前端无法连接后端
```bash
# 检查后端是否运行
curl http://localhost:8000/api/stats

# 检查前端配置
cat frontend/src/pages/index.astro | grep localhost:8000
```

### 文案质量不佳
```bash
# 1. 修改提示词
vim backend/config/prompts.py

# 2. 调整 temperature
# 编辑 backend/services/ai_service.py
# 找到 _generate_with_openai 方法
# 修改 temperature 参数（0.7-0.9）

# 3. 尝试不同模型
# 编辑 backend/.env
# 修改 GENERATE_MODEL（qwen-max/plus/turbo）
```

## 📚 参考文档

| 文档 | 描述 |
|------|------|
| [QWEN_SETUP.md](QWEN_SETUP.md) | 千问 API 完整配置指南 |
| [QWEN_INTEGRATION_COMPLETE.md](QWEN_INTEGRATION_COMPLETE.md) | 千问集成完成总结 |
| [OPTIMIZATION_COMPLETE.md](OPTIMIZATION_COMPLETE.md) | 系统优化完成总结 |
| [backend/config/PROMPT_GUIDE.md](backend/config/PROMPT_GUIDE.md) | 提示词优化指南 |
| [USAGE_GUIDE.md](USAGE_GUIDE.md) | 使用指南 |

## 🎯 快速开始

### 新手入门
1. ✅ 访问 http://localhost:4321
2. ✅ 点击任意新闻的 "✍️ 生成文案" 按钮
3. ✅ 查看生成的三个版本
4. ✅ 点击 "📋 复制" 按钮复制文案

### 优化提示词
1. ✅ 打开 `backend/config/prompts.py`
2. ✅ 找到对应版本的提示词（A/B/C）
3. ✅ 修改提示词内容
4. ✅ 保存文件，重新生成即可看到效果

### 切换 AI 模型
1. ✅ 编辑 `backend/.env`
2. ✅ 修改 `GENERATE_MODEL` 变量
3. ✅ 重启后端服务
4. ✅ 重新测试生成功能

## 📞 获取帮助

### 查看日志
```bash
tail -f /tmp/backend.log
```

### 测试连接
```bash
cd backend
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 test_qwen.py
```

### 重启服务
```bash
# 后端
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill -9
cd backend && nohup /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

---

**最后更新**: 2025-01-13
**版本**: v1.0
**状态**: ✅ 生产就绪
