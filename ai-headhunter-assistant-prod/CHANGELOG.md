# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - Day 9-10 功能开发

### 待开发
- [ ] AI 自动打招呼功能
- [ ] 限流与反爬策略
- [ ] 批量处理优化
- [ ] 共享包提取（packages/）

---

## [1.1.0] - 2025-11-14

### Added - 飞书 API 集成 (Day 8)

#### 核心功能
- ✅ 飞书 API 客户端 (`apps/backend/app/services/feishu_client.py`)
  - Token 管理（自动获取和缓存 `tenant_access_token`）
  - 健康检查（验证 API 连接状态）
  - 图片上传（Base64 → 飞书云盘文件 Token）
  - 记录创建（新增候选人到多维表格）
  - 去重检查（姓名 + 公司判重）

#### 后端集成
- 新增 `/api/feishu/health` 端点
- `process_candidate` 自动上传推荐候选人到飞书
- 自动上传简历截图到飞书云盘

#### 配置管理
- 更新 `apps/backend/app/config.py` 支持飞书配置
- 更新 `apps/backend/env.example` 飞书环境变量模板
- 更新根目录 `env.example` 修正 `FEISHU_APP_TOKEN` 值

#### 测试工具
- 新增 `apps/backend/test_feishu.py` 连接测试脚本
- 新增 `apps/backend/你的飞书配置.txt` 配置说明

#### 文档
- 新增 `docs/飞书开放平台注册指南.md`
- 新增 `docs/飞书AI自动化配置指南.md`
- 新增 `docs/mvp/Day8-飞书集成完成报告.md`

#### Bug 修复
- 修复飞书 SDK 响应结构兼容性问题
- 修复配置文件路径混乱（`backend/.env` → `apps/backend/.env`）

---

### Added - Multi-Agent 配置 (2025-11-14)
- 新增 `.cursorrules` 文件，配置 10 个专业 Agents
- 新增 `docs/tech/Cursor-Multi-Agent-指南.md` 使用指南
- 新增 `docs/Multi-Agent-配置完成报告.md` 配置报告
- 更新 `README.md` 添加 Multi-Agent 指南链接

**Agents**:
1. Web Agent, 2. Backend Agent, 3. Extension Agent, 4. AI Pipeline Agent
5. Scraper Agent, 6. Shared Agent, 7. Docs Agent, 8. Reviewer Agent
9. Refactor Agent, 10. DevOps Agent

---

## [1.0.0] - 2025-11-14

### Added - Monorepo 结构

#### 新增目录
- `apps/` - 应用层
  - `apps/web/` - Web 前端（未来）
  - `apps/backend/` - 后端服务（待迁移）
  - `apps/extension/` - Chrome 插件（待迁移）
- `packages/` - 共享包
  - `packages/ai-pipeline/` - AI 处理流程
  - `packages/shared/` - 共享工具和类型
  - `packages/scrapers/` - 爬虫模块
- `docs/` - 文档
  - `docs/prd/` - 产品需求文档
  - `docs/tech/` - 技术文档
  - `docs/mvp/` - MVP 开发文档
- `demo/` - 技术验证 Demo
- `scripts/` - 构建和部署脚本
- `config/` - 全局配置

#### 新增文件
- `package.json` - Monorepo 根配置
- `pnpm-workspace.yaml` - pnpm workspace 配置
- `turbo.json` - Turborepo 配置
- `config/tsconfig.base.json` - TypeScript 基础配置
- `scripts/setup.sh` - 环境设置脚本
- 各目录 README.md 文件

#### 更新文件
- `.gitignore` - 添加 Monorepo 相关规则

### Added - Day 6-7 功能

#### Chrome 插件 (v1.0.3)
- 两轮处理逻辑（快速筛选 + 深度分析）
- 简历弹层自动打开与内容提取
- 简历截图功能（处理 Canvas 加密）
- Markdown 导出（包含 AI 分析和原文）
- PNG 图片单独导出
- 控件 UI 优化（尺寸缩小 50%）
- 防止插件重复注入

#### 技术亮点
- 处理 Boss 直聘 WebAssembly + Canvas 加密
- 使用 Background Service Worker 处理截图
- Content Script 和 Background Script 消息通信
- Base64 图片编码支持
- 截图前自动隐藏控件

---

## Git Commits

### 2025-11-14 - Commit: (待提交)
**feat: 迁移代码到 apps/ 目录**

- 迁移后端服务到 apps/backend/
- 迁移 Chrome 插件到 apps/extension/
- 新增 package.json 配置（后端 + 插件）
- 新增快速开始指南（后端 + 插件）
- 更新 README 文档（后端 + 插件）
- 新增代码迁移完成报告
- 复制插件图标文件

### 2025-11-14 - Commit: 262cc30
**docs: 添加文档迁移完成报告**

- 新增文档迁移完成报告
- 更新 CHANGELOG.md

### 2025-11-14 - Commit: 6a3e86b
**docs: 迁移文档到 docs/ 子目录**

- 迁移 17 个文件
- 文档重组为 prd/tech/mvp 三个分类
- Demo 文件整理到 demo/ 目录
- README.md 更新所有文档链接
- 新增 CHANGELOG.md
- 新增文档迁移完成报告

### 2025-11-14 - Commit: 5ddb4b6
**chore: 创建 Monorepo 目录结构**

- 新增 44 个文件
- 新增 1307 行代码
- 创建完整的 Monorepo 架构
- 保持所有现有文件原地不动

### 2025-11-14 - Commit: 5ec305c
**feat: Day 6-7 完成 - 简历详情提取与截图导出功能**

- 新增 45 个文件
- 新增 11284 行代码
- 完成核心 MVP 功能

---

## 项目完成度

- **核心功能**: 90% ████████████████████░░
- **文档**: 80% ████████████████░░░░░░
- **测试**: 30% ██████░░░░░░░░░░░░░░░░
- **部署**: 0% ░░░░░░░░░░░░░░░░░░░░░░

---

## 下一步计划

### Day 8-10
- [ ] 飞书表格自动入库
- [ ] 自动打招呼功能
- [ ] 批量测试与优化
- [ ] 文档迁移到新目录结构

### Day 11+
- [ ] 代码迁移到 Monorepo 结构
- [ ] 配置 CI/CD
- [ ] 性能优化
- [ ] 部署到生产环境

