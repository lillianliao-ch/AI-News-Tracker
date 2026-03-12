# Notion RAG 系统

基于 Notion 数据库的检索增强生成（RAG）系统，支持智能问答和文档检索。

## 功能特性

- 🔗 **Notion 集成**: 自动从 Notion 数据库获取内容
- 🤖 **智能问答**: 基于文档内容的 AI 问答
- 🔍 **语义搜索**: 向量化文档检索
- 📊 **文档处理**: 自动分块和预处理
- 🌐 **Web API**: RESTful API 接口
- 📈 **实时同步**: 支持数据实时同步

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Notion API    │───▶│  Document Proc  │───▶│  Vector Store   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  RAG System     │◀───│  Web API        │
                       └─────────────────┘    └─────────────────┘
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- Notion API Token
- OpenAI API Key

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境配置

复制环境变量模板并配置：

```bash
cp env_example.txt .env
```

编辑 `.env` 文件，配置以下必要参数：

```env
# Notion API配置
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id

# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# 系统配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./data/vector_db
DOCUMENTS_PATH=./data/documents

# Web服务配置
HOST=0.0.0.0
PORT=8000
```

### 4. 获取 Notion API Token

1. 访问 [Notion Developers](https://developers.notion.com/)
2. 创建新的集成
3. 获取 Integration Token
4. 将集成添加到你的数据库

### 5. 运行测试

```bash
python main.py
```

### 6. 启动 Web API 服务

```bash
python api_server.py
```

服务将在 `http://localhost:8000` 启动

## API 接口

### 基础接口

- `GET /` - 服务状态
- `GET /health` - 健康检查
- `GET /system/info` - 系统信息

### 问答接口

- `POST /question` - 基础问答
- `POST /question/with-sources` - 带源信息的问答
- `POST /question/batch` - 批量问答

### 数据管理

- `POST /sync` - 同步 Notion 数据
- `GET /search` - 文档搜索
- `DELETE /vector-store/reset` - 重置向量存储

## 使用示例

### Python 代码示例

```python
from rag_system import RAGSystem

# 初始化 RAG 系统
rag = RAGSystem()

# 提问
result = rag.ask_question("你的问题")
print(result["answer"])
```

### API 调用示例

```bash
# 提问
curl -X POST "http://localhost:8000/question" \
     -H "Content-Type: application/json" \
     -d '{"question": "你的问题", "k": 5}'

# 同步数据
curl -X POST "http://localhost:8000/sync" \
     -H "Content-Type: application/json" \
     -d '{"force_sync": false}'
```

## 项目结构

```
notion_rag/
├── config.py              # 配置管理
├── notion_client.py       # Notion API 客户端
├── document_processor.py  # 文档处理
├── vector_store.py        # 向量存储管理
├── rag_system.py          # RAG 核心系统
├── api_server.py          # Web API 服务器
├── main.py               # 主程序（测试用）
├── requirements.txt      # 依赖包
├── env_example.txt       # 环境变量模板
├── README.md            # 项目说明
└── data/                # 数据目录
    ├── vector_db/       # 向量数据库
    └── documents/       # 处理后的文档
```

## 配置说明

### 系统参数

- `CHUNK_SIZE`: 文档分块大小（默认: 1000）
- `CHUNK_OVERLAP`: 分块重叠大小（默认: 200）
- `EMBEDDING_MODEL`: 嵌入模型（默认: all-MiniLM-L6-v2）
- `OPENAI_MODEL`: OpenAI 模型（默认: gpt-3.5-turbo）

### 性能优化

- 调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 以优化检索效果
- 使用更强大的嵌入模型提升语义理解
- 配置合适的 `k` 值平衡准确性和性能

## 故障排除

### 常见问题

1. **Notion API 连接失败**
   - 检查 `NOTION_TOKEN` 是否正确
   - 确认集成已添加到数据库

2. **OpenAI API 错误**
   - 验证 `OPENAI_API_KEY` 是否有效
   - 检查 API 配额是否充足

3. **向量存储问题**
   - 删除 `data/vector_db` 目录重新初始化
   - 检查磁盘空间是否充足

### 日志查看

系统使用 Python logging 模块，可以通过修改日志级别获取详细信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 开发指南

### 添加新的文档源

1. 继承 `DocumentProcessor` 类
2. 实现 `process_content` 方法
3. 在 `RAGSystem` 中集成

### 自定义嵌入模型

1. 修改 `EMBEDDING_MODEL` 配置
2. 确保模型与 sentence-transformers 兼容
3. 测试模型性能

### 扩展 API 接口

1. 在 `api_server.py` 中添加新的路由
2. 定义 Pydantic 模型
3. 实现业务逻辑

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持 Notion 数据同步
- 实现基础 RAG 功能
- 提供 Web API 接口 