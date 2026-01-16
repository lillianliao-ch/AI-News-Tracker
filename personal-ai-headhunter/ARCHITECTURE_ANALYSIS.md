# Personal AI Headhunter - 项目架构分析报告

**分析日期**: 2025-01-14
**项目路径**: `/Users/lillianliao/notion_rag/personal-ai-headhunter`
**分析工具**: repo-research-analyst (Claude Compound Engineering Plugin)

---

## 📊 Repository Research Summary

### Architecture & Structure

**项目类型**: 个人 AI 猎头助手系统
**架构模式**: 单体应用 (Monolithic Application)
**技术栈**: Python + Streamlit + SQLite + ChromaDB

#### 核心架构层次

```
┌─────────────────────────────────────────────────┐
│         Presentation Layer (展示层)              │
│           Streamlit Web UI (app.py)              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          Business Logic Layer (业务层)           │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ AIService    │  │ MatchingEngine│             │
│  │ (AI分析)     │  │  (匹配引擎)   │             │
│  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Data Access Layer (数据层)               │
│  ┌──────────────┐  ┌──────────────┐             │
│  │   SQLite     │  │   ChromaDB   │             │
│  │ (结构化数据) │  │  (向量搜索)   │             │
│  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────┘
```

#### 项目组织结构

```
personal-ai-headhunter/
├── app.py                      # 主应用入口 (Streamlit UI)
├── database.py                 # 数据模型 & ORM
├── ai_service.py              # AI 服务 (OpenAI API, Embedding)
├── matching_engine.py         # 人岗匹配引擎
├── prompt_config_module.py    # 提示词配置模块
├── pages/
│   └── prompt_config.py       # 提示词配置页面
├── data/
│   ├── headhunter.db          # SQLite 数据库
│   ├── chroma_db/             # ChromaDB 向量存储
│   └── uploads/               # 上传文件存储
├── Antigravity-Manager/       # 子项目 (Chrome Extension)
│   ├── manifest.json
│   ├── content.js
│   └── popup/
└── [辅助脚本]
    ├── import_maimai_candidates.py
    ├── import_ali_jobs.py
    ├── migrate_db.py
    └── check_db_connection.py
```

---

### 技术栈分析

#### 1. 前端技术
- **框架**: Streamlit
- **特点**: 快速原型开发，适合数据驱动应用
- **UI 模块**:
  - Dashboard (概览)
  - 人才库管理
  - 职位库管理
  - 智能匹配
  - 提示词配置

#### 2. 后端技术
- **语言**: Python 3.x
- **Web 框架**: Streamlit (全栈)
- **API 集成**:
  - OpenAI API (GPT-3.5/4)
  - 阿里云 Qwen (备选)
  - Embedding API

#### 3. 数据库技术

**SQLite (结构化数据)**:
- 表结构:
  - `candidates` - 候选人信息
  - `jobs` - 职位信息
  - `match_records` - 匹配记录
  - `system_prompts` - 提示词管理

**ChromaDB (向量搜索)**:
- Collections:
  - `candidates` - 候选人向量
  - `jobs` - 职位向量
- 用途: 语义搜索 (简历-JD 匹配)

---

### 核心功能模块

#### 1. 人才管理模块 (Candidate Management)

**核心实体**: `Candidate`

```python
# 数据模型
Candidate:
  - 基本信息: name, email, phone
  - AI 分析: ai_summary, skills, experience_years
  - 详细经历: education_details, work_experiences, project_experiences
  - 社交链接: linkedin_url, github_url
  - 好友标记: is_friend, friend_added_at, friend_channel
  - 沟通记录: communication_logs
  - 向量关联: vector_id
```

**关键功能**:
- Excel 批量导入候选人
- AI 自动生成画像 (技能、经验评估)
- 手动编辑 AI 标签
- 删除候选人

#### 2. 职位管理模块 (Job Management)

**核心实体**: `Job`

```python
# 数据模型
Job:
  - 基本信息: title, company
  - AI 分析: ai_analysis, structured_tags
  - 职位要求: salary_range, location, required_experience_years
  - 详细标签: tech_stack, tech_domain, role_type, etc.
```

**关键功能**:
- Excel 导入职位
- AI 生成职位标签
- 标签结构化存储

#### 3. 智能匹配模块 (Smart Matching)

**匹配引擎**: `MatchingEngine`

**匹配维度权重**:
```python
WEIGHTS = {
    "tech_domain": 0.30,      # 技术方向
    "role_type": 0.15,        # 岗位类型
    "role_orientation": 0.15, # 角色定位
    "tech_stack": 0.15,       # 技术栈
    "industry_exp": 0.10,     # 行业背景
    "seniority": 0.10,        # 职级层次
    "education": 0.05         # 教育背景
}
```

**匹配策略**:
- 基于结构化标签的多维度匹配
- 技术方向相似度矩阵 (如 LLM ↔ Agent 相似度 0.7)
- 向量语义搜索 (ChromaDB)
- 综合打分 & 排序

**输出**:
- 总分
- 各维度分数
- 匹配详情
- 推荐理由
- 风险提示

#### 4. AI 服务模块 (AI Service)

**核心功能**:
- 候选人画像生成
- 职位标签提取
- 文本 Embedding
- 提示词管理

**AI 模型**:
- 主模型: GPT-3.5/GPT-4
- Embedding: text-embedding-v1 (阿里云 Qwen)
- 备选模型: DeepSeek

**提示词管理**:
- 数据库存储 (`system_prompts` 表)
- 支持多版本
- 支持启用/禁用
- 类型分类: candidate / job

#### 5. 提示词配置模块 (Prompt Config)

**功能**:
- UI 编辑提示词
- 支持变量插值
- 实时预览
- 版本管理

---

### 数据流分析

#### 1. 候选人录入流程

```
Excel 上传
   ↓
解析 Excel (pandas)
   ↓
提取简历文本
   ↓
AI 画像生成 (AIService.analyze_candidate)
   ├─ 技能提取
   ├─ 经验评估
   └─ 标签生成
   ↓
保存到 SQLite (Candidate 表)
   ↓
生成 Embedding (AIService.get_embedding)
   ↓
保存到 ChromaDB (candidates collection)
```

#### 2. 智能匹配流程

```
选择职位 (Job)
   ↓
获取职位标签 (structured_tags)
   ↓
MatchingEngine.match_job_to_candidates()
   ├─ 遍历所有候选人
   ├─ 多维度打分 (7 个维度)
   ├─ 向量相似度搜索
   └─ 综合排序
   ↓
返回 Top K 候选人
   ├─ 总分
   ├─ 各维度分数
   ├─ 匹配详情
   └─ 推荐理由/风险
```

---

### 代码模式与约定

#### 1. 数据库模式

**ORM**: SQLAlchemy
**模式**: Declarative Base
**Session 管理**: Context Manager (`get_db()`)

```python
# 约定: 使用 to_dict() 序列化
candidate.to_dict()  # 返回字典
```

#### 2. AI 服务模式

**JSON 清理工具**: `_clean_json_string()`
```python
# 处理 AI 返回的 JSON (去除 markdown 格式)
text = AIService._clean_json_string(ai_response)
```

**提示词获取**: `get_active_prompt()`
```python
# 从数据库获取当前激活的提示词
prompt = AIService.get_active_prompt('candidate')
```

#### 3. Streamlit 模式

**Session State 管理**:
```python
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'list'
```

**导航模式**: Sidebar Radio
```python
page = st.sidebar.radio("导航", nav_options)
st.session_state.nav_page = page
```

#### 4. 文件存储约定

```
data/
├── headhunter.db       # SQLite 主数据库
├── chroma_db/          # ChromaDB 持久化存储
└── uploads/            # 上传文件临时存储
```

#### 5. 环境变量管理

**优先级**:
1. `config.env` (优先，规避 gitignore)
2. `.env.local`
3. `.env`

**必需变量**:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `MODEL_NAME`
- `EMBEDDING_MODEL`

---

### 潜在问题与改进建议

#### ⚠️ 发现的问题

1. **数据库路径硬编码**
   ```python
   # app.py line 32
   if not os.path.exists("personal-ai-headhunter/data/headhunter.db"):
   ```
   **问题**: 相对路径会导致在不同目录运行时找不到数据库
   **建议**: 使用 `base_dir = os.path.dirname(__file__)`

2. **缺少错误处理**
   ```python
   # ai_service.py
   client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
   ```
   **问题**: 如果 API key 为空或无效，会导致崩溃
   **建议**: 添加配置验证和异常处理

3. **JSON 解析容错性**
   - 虽然有 `_clean_json_string()`，但 AI 可能返回不完整的 JSON
   **建议**: 添加更健壮的 JSON 解析 (如 `json5` 或 `repair_json`)

4. **缺少数据验证**
   - `structured_tags` 直接存储 JSON，没有 schema 验证
   **建议**: 使用 Pydantic 验证标签结构

5. **匹配引擎硬编码权重**
   ```python
   WEIGHTS = {...}  # 硬编码
   ```
   **问题**: 不同行业/职位可能需要不同权重
   **建议**: 存储在数据库，支持动态调整

#### 💡 改进建议

**架构层面**:

1. **模块化重构**
   - 将 `app.py` (600+ 行) 拆分为多个模块
   - 建议:
     ```
     pages/
       ├── __init__.py
       ├── dashboard.py
       ├── candidates.py
       ├── jobs.py
       ├── matching.py
       └── prompt_config.py
     ```

2. **配置管理**
   - 创建 `config.py` 集中管理配置
   - 支持多环境配置 (dev/prod)

3. **日志系统**
   - 添加 `logging` 模块
   - 记录 API 调用、错误信息

**功能层面**:

4. **缓存机制**
   - AI 分析结果缓存
   - Embedding 结果缓存
   - 减少重复 API 调用

5. **异步处理**
   - 批量导入时使用后台任务
   - 避免 Streamlit 阻塞

6. **导出功能**
   - 支持导出匹配结果为 Excel/PDF
   - 生成候选人报告

**性能层面**:

7. **数据库优化**
   - 添加索引:
     ```python
     __table_args__ = (
         Index('idx_candidate_skills', 'skills'),
         Index('idx_job_tags', 'structured_tags'),
     )
     ```

8. **向量搜索优化**
   - 批量生成 embeddings
   - 减少 API 调用次数

**安全层面**:

9. **API Key 管理**
   - 使用环境变量 (✅ 已做)
   - 添加 API Key 验证
   - 支持 Key 轮换

10. **输入验证**
    - 验证上传文件类型
    - 限制文件大小
    - 防止路径遍历攻击

---

### 测试与部署

#### 测试覆盖

**现状**: 缺少测试文件
**建议添加**:
```
tests/
├── test_ai_service.py
├── test_matching_engine.py
├── test_database.py
└── test_app.py
```

#### 部署方式

**文档**: `DEPLOYMENT_GUIDE.md`
**部署目标**: Railway (根据 `migrate_to_railway.py`)

**部署步骤**:
1. 环境变量配置
2. 数据库迁移
3. Streamlit Cloud 或 Railway 部署

---

### 文档完整性

#### ✅ 现有文档

- [README.md](README.md) - 项目介绍
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - 环境配置
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 部署指南
- [WORKFLOW.md](WORKFLOW.md) - 工作流程

#### ❌ 缺失文档

- **API 文档**: 没有 AIService / MatchingEngine 的 API 说明
- **数据模型文档**: 缺少数据库 schema 图
- **开发指南**: 没有贡献指南
- **测试文档**: 没有测试说明

---

### 子项目分析: Antigravity-Manager

**类型**: Chrome Extension
**功能**: 脉脉/LinkedIn 数据抓取
**技术栈**: Vanilla JavaScript + Chrome Extension APIs

**结构**:
```
Antigravity-Manager/
├── manifest.json
├── content.js          # 内容脚本
├── popup/
│   ├── index.html
│   └── popup.js
└── docs/               # 技术文档
```

**集成方式**:
- 需要与主系统通信
- 可能需要添加 API 端点

---

### 依赖项分析

**核心依赖**:
```python
streamlit      # Web UI
sqlalchemy     # ORM
chromadb       # 向量数据库
openai         # AI API
pandas         # 数据处理
python-dotenv  # 环境变量
```

**建议添加**:
- `pydantic` - 数据验证
- `pytest` - 测试框架
- `black` - 代码格式化
- `ruff` - Linting

---

## 🎯 项目成熟度评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **功能完整性** | ⭐⭐⭐⭐ | 核心功能完整，缺少导出/报告 |
| **代码质量** | ⭐⭐⭐ | 结构清晰，但缺少测试和错误处理 |
| **文档完整性** | ⭐⭐⭐ | 有基础文档，缺少 API/开发文档 |
| **可维护性** | ⭐⭐⭐ | 单体文件过大，需要模块化 |
| **可扩展性** | ⭐⭐ | 硬编码配置，需要重构 |
| **安全性** | ⭐⭐ | 缺少输入验证和错误处理 |
| **性能** | ⭐⭐⭐ | 基本满足需求，缺少缓存 |

---

## 📋 建议的优先级任务

### 🔴 高优先级 (立即处理)

1. **修复数据库路径硬编码**
   - 文件: [app.py:32](app.py#L32)
   - 影响: 跨目录运行失败

2. **添加错误处理**
   - 文件: [ai_service.py](ai_service.py)
   - 影响: API 调用失败导致崩溃

3. **环境变量验证**
   - 启动时检查必需的配置
   - 提供友好的错误提示

### 🟡 中优先级 (2 周内)

4. **模块化拆分**
   - 将 app.py 拆分为多个页面模块
   - 提高可维护性

5. **添加测试**
   - 核心 AI 服务测试
   - 匹配引擎测试

6. **配置管理重构**
   - 创建 config.py
   - 支持动态权重配置

### 🟢 低优先级 (后续优化)

7. **性能优化**
   - 添加缓存机制
   - 批量 Embedding

8. **功能增强**
   - 导出功能
   - 报告生成
   - 后台任务

---

## 🔍 代码模式示例

### 推荐模式 (项目中已使用)

**1. 数据库 Session 管理** ✅
```python
def get_session():
    return next(get_db())
```

**2. JSON 清理工具** ✅
```python
@staticmethod
def _clean_json_string(text):
    # 提取纯 JSON，去除 markdown
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    return text[start_idx : end_idx + 1]
```

**3. 向量搜索集成** ✅
```python
candidates_collection = chroma_client.get_or_create_collection(name="candidates")
results = candidates_collection.query(query_texts=[query], n_results=top_k)
```

### 不推荐模式 (需要改进)

**1. 硬编码路径** ❌
```python
# 当前
if not os.path.exists("personal-ai-headhunter/data/headhunter.db"):

# 应该改为
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "data", "headhunter.db")
```

**2. 缺少错误处理** ❌
```python
# 当前
client = OpenAI(api_key=OPENAI_API_KEY)

# 应该改为
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    client.models.list()  # 验证连接
except Exception as e:
    logger.error(f"OpenAI 初始化失败: {e}")
    raise ConfigurationError("AI 服务配置错误")
```

---

## 🚀 如何使用这份分析报告

### 对于新开发者

1. **了解架构**: 阅读 "Architecture & Structure" 章节
2. **快速开始**: 遵循 README.md 和 ENVIRONMENT_SETUP.md
3. **代码模式**: 参考 "代码模式示例" 章节

### 对于功能开发

1. **添加新功能**:
   - 阅读 "核心功能模块"
   - 参考 "数据流分析"
   - 遵循 "代码模式与约定"

2. **修改现有功能**:
   - 查看相关模块的实现
   - 注意 "潜在问题" 章节
   - 添加测试

### 对于代码审查

1. **检查清单**:
   - [ ] 是否使用了硬编码路径?
   - [ ] 是否添加了错误处理?
   - [ ] 是否验证了输入数据?
   - [ ] 是否需要添加测试?

2. **参考标准**:
   - "推荐模式" 章节
   - "代码质量" 评估

---

## 📚 相关资源

- **项目文档**: [README.md](README.md)
- **环境配置**: [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)
- **部署指南**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **工作流程**: [WORKFLOW.md](WORKFLOW.md)

---

**分析完成时间**: 2025-01-14
**分析工具**: repo-research-analyst (Claude Compound Engineering Plugin v2.23.1)
**Token 消耗**: ~12K tokens
**下次建议**: 1 个月后重新评估，或架构调整后更新
