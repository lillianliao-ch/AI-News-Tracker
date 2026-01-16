# 环境配置与运行指南 (Environment Setup Guide)

本项目采用 **单代码库、多数据环境** 的隔离策略，确保开发测试与真实业务运行互不干扰，同时简化升级流程。

## 1. 环境架构设计

*   **代码 (Code)**: 所有环境共享同一套代码 (`app.py`, `database.py`, `ai_service.py`)。
*   **数据 (Data)**: 通过环境变量 `DB_PATH` 隔离数据库文件。
    *   **开发环境 (Dev)**: 使用 `data/headhunter_dev.db`。用于功能开发、Bug 修复、测试脏数据。
    *   **生产环境 (Prod)**: 使用 `data/headhunter_prod.db`。用于真实业务运营，数据需严格保护。

## 2. 快速启动

我们提供了一个统一的脚本 `run.sh` 来管理环境启动。

### 🛠️ 启动开发环境 (Dev)
```bash
cd personal-ai-headhunter
./run.sh dev
```
*   **特点**: 此时你在操作测试数据库。你可以随意导入、删除数据，测试新功能。
*   **用途**: 日常编码、调试。

### 🚀 启动生产环境 (Prod)
```bash
cd personal-ai-headhunter
./run.sh prod
```
*   **特点**: 此时你连接的是真实业务数据库。请谨慎操作“重制/删除”等高风险功能。
*   **用途**: 真实的猎头业务工作（录入真实候选人、生成画像）。

## 3. 版本升级与发布流程

当你（作为开发者）在 `dev` 环境完成了代码修改（例如增加了新功能），希望应用到 `prod` 环境时，请遵循以下步骤：

1.  **代码更新**: 确保你的代码修改已保存（如果是在服务器上，拉取最新 git 代码）。
2.  **数据库迁移 (Migration)**:
    如果你的代码修改涉及了数据库结构变更（例如新增了字段或表），你需要对生产数据库进行迁移。
    ```bash
    # 对生产数据库执行迁移检查
    export DB_PATH="data/headhunter_prod.db"
    python3 migrate_db.py
    ```
    *注意：目前的 `migrate_db.py` 主要负责创建新表和初始化配置。如果涉及复杂的字段修改，可能需要手动处理或使用 Alembic（进阶）。*

3.  **重启服务**:
    停止当前的 `prod` 服务 (Ctrl+C)，然后重新运行 `./run.sh prod`。新代码即刻生效，且原有数据保持不变。

## 4. 目录结构说明

```text
personal-ai-headhunter/
├── app.py                # 主程序入口 (UI & 业务逻辑)
├── database.py           # 数据库模型定义
├── ai_service.py         # AI 核心服务 (调用 LLM)
├── run.sh                # 环境启动脚本 (入口)
├── migrate_db.py         # 数据库迁移脚本
├── requirements.txt      # 依赖库
├── data/                 # 数据存储目录
│   ├── headhunter_dev.db   # 开发环境数据库 (可随时清理)
│   ├── headhunter_prod.db  # 生产环境数据库 (重要数据!)
│   └── chroma_db/          # 向量数据库 (也会根据环境隔离，目前代码默认共享，后续可优化)
└── ...
```

## 5. 注意事项

*   **向量数据库**: 目前 `ChromaDB` 的路径在代码中配置为 `data/chroma_db`。建议在未来优化中也通过环境变量隔离向量库路径，避免 Dev 和 Prod 的向量数据混杂（虽然影响不大，但为了极致的干净建议隔离）。
*   **API Key**: 两个环境共享同一个 `.env` 中的 API Key。请确保 Key 的额度充足。







