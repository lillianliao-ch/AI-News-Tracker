# 🏗️ 项目重构计划 - Monorepo 结构

## 🎯 目标

- ✅ 创建清晰的、可扩展的 Monorepo 目录结构
- ✅ 保持所有现有文件原地不动
- ✅ 为未来迁移做准备
- ✅ 不做破坏性修改

---

## 📂 新目录结构

```
ai-headhunter-assistant/
│
├── 📁 apps/                          # 🚀 应用层（多个独立应用）
│   ├── web/                          # 前端 Web 应用（未来）
│   │   ├── package.json
│   │   ├── README.md
│   │   └── .gitkeep
│   │
│   ├── backend/                      # 后端服务（未来迁移）
│   │   ├── package.json
│   │   ├── README.md
│   │   └── .gitkeep
│   │
│   └── extension/                    # Chrome 插件（未来迁移）
│       ├── package.json
│       ├── README.md
│       └── .gitkeep
│
├── 📁 packages/                      # 📦 共享包（可复用模块）
│   ├── ai-pipeline/                  # AI 处理流程
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── parsers/              # 简历解析器
│   │   │   ├── evaluators/           # 评估器
│   │   │   └── generators/           # 内容生成器
│   │   └── .gitkeep
│   │
│   ├── shared/                       # 共享工具和类型
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── types/                # TypeScript 类型定义
│   │   │   ├── utils/                # 工具函数
│   │   │   ├── constants/            # 常量
│   │   │   └── config/               # 配置
│   │   └── .gitkeep
│   │
│   └── scrapers/                     # 爬虫模块
│       ├── package.json
│       ├── README.md
│       ├── src/
│       │   ├── boss/                 # Boss 直聘爬虫
│       │   ├── liepin/               # 猎聘爬虫
│       │   ├── linkedin/             # LinkedIn 爬虫
│       │   └── base/                 # 基础爬虫类
│       └── .gitkeep
│
├── 📁 docs/                          # 📝 文档目录（结构化）
│   ├── prd/                          # 产品需求文档
│   │   ├── README.md
│   │   └── .gitkeep
│   │
│   ├── tech/                         # 技术文档
│   │   ├── README.md
│   │   └── .gitkeep
│   │
│   └── mvp/                          # MVP 开发文档
│       ├── README.md
│       └── .gitkeep
│
├── 📁 demo/                          # 🎯 技术验证 Demo
│   ├── README.md
│   └── .gitkeep
│
├── 📁 scripts/                       # 🔧 构建和部署脚本（新增）
│   ├── setup.sh                      # 环境设置
│   ├── deploy.sh                     # 部署脚本
│   └── README.md
│
├── 📁 config/                        # ⚙️ 全局配置（新增）
│   ├── tsconfig.base.json            # TypeScript 基础配置
│   ├── eslint.config.js              # ESLint 配置
│   └── README.md
│
├── 📄 package.json                   # Monorepo 根配置（新增）
├── 📄 pnpm-workspace.yaml            # pnpm workspace 配置（新增）
├── 📄 turbo.json                     # Turborepo 配置（新增，可选）
├── 📄 .gitignore                     # Git 忽略文件（更新）
└── 📄 README.md                      # 项目主文档（更新）

```

---

## 📋 将要创建的目录和文件

### 目录结构 (PR Diff 格式)

```diff
+ apps/
+   web/
+     .gitkeep
+     README.md
+     package.json
+   backend/
+     .gitkeep
+     README.md
+     package.json
+   extension/
+     .gitkeep
+     README.md
+     package.json
+
+ packages/
+   ai-pipeline/
+     .gitkeep
+     README.md
+     package.json
+     src/
+       parsers/.gitkeep
+       evaluators/.gitkeep
+       generators/.gitkeep
+   shared/
+     .gitkeep
+     README.md
+     package.json
+     src/
+       types/.gitkeep
+       utils/.gitkeep
+       constants/.gitkeep
+       config/.gitkeep
+   scrapers/
+     .gitkeep
+     README.md
+     package.json
+     src/
+       boss/.gitkeep
+       liepin/.gitkeep
+       linkedin/.gitkeep
+       base/.gitkeep
+
+ docs/
+   prd/
+     .gitkeep
+     README.md
+   tech/
+     .gitkeep
+     README.md
+   mvp/
+     .gitkeep
+     README.md
+
+ demo/
+   .gitkeep
+   README.md
+
+ scripts/
+   .gitkeep
+   setup.sh
+   deploy.sh
+   README.md
+
+ config/
+   .gitkeep
+   tsconfig.base.json
+   eslint.config.js
+   README.md
+
+ package.json           (新增 - Monorepo 根配置)
+ pnpm-workspace.yaml    (新增 - pnpm workspace)
+ turbo.json             (新增 - Turborepo 配置，可选)
~ .gitignore             (更新 - 添加新的忽略规则)
~ README.md              (更新 - 更新项目说明)
```

---

## 📝 新文件内容预览

### 1. `package.json` (根目录)

```json
{
  "name": "ai-headhunter-assistant",
  "version": "1.0.0",
  "private": true,
  "description": "AI 自动筛选简历 + 自动打招呼系统",
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "clean": "turbo run clean"
  },
  "devDependencies": {
    "turbo": "^1.10.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=8.0.0"
  },
  "packageManager": "pnpm@8.0.0"
}
```

### 2. `pnpm-workspace.yaml`

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

### 3. `turbo.json` (可选)

```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    },
    "lint": {
      "outputs": []
    }
  }
}
```

### 4. `.gitignore` (追加内容)

```diff
+ # Monorepo
+ node_modules/
+ dist/
+ build/
+ .turbo/
+ 
+ # Apps
+ apps/*/dist/
+ apps/*/build/
+ apps/*/.next/
+ 
+ # Packages
+ packages/*/dist/
+ packages/*/build/
```

### 5. `apps/web/README.md`

```markdown
# Web 应用

前端 Web 管理界面（未来开发）

## 技术栈（规划）

- Next.js 14
- TypeScript
- Tailwind CSS
- React Query
- Zustand

## 功能（规划）

- 候选人管理
- 职位管理
- AI 评估结果展示
- 飞书集成
- 数据统计和报表
```

### 6. `apps/backend/README.md`

```markdown
# 后端服务

FastAPI 后端服务（待迁移）

## 当前位置

现有后端代码在根目录 `backend/`，待迁移到此处。

## 迁移计划

- [ ] 迁移 FastAPI 应用
- [ ] 配置 pnpm 脚本
- [ ] 集成 Monorepo 构建系统
- [ ] 添加 Docker 支持
```

### 7. `apps/extension/README.md`

```markdown
# Chrome 插件

Boss 直聘候选人采集插件（待迁移）

## 当前位置

现有插件代码在根目录 `chrome-extension-v2/`，待迁移到此处。

## 迁移计划

- [ ] 迁移插件代码
- [ ] 配置打包脚本
- [ ] 集成 Monorepo 构建系统
- [ ] 添加自动化测试
```

### 8. `packages/ai-pipeline/README.md`

```markdown
# AI Pipeline

AI 处理流程的共享包

## 功能模块

### Parsers (解析器)
- PDF 解析
- 简历结构化
- 信息提取

### Evaluators (评估器)
- 匹配度评估
- 技能评分
- 推荐等级计算

### Generators (生成器)
- 招呼语生成
- 标签生成
- 摘要生成

## 使用示例

```typescript
import { ResumeParser, Evaluator } from '@ai-headhunter/ai-pipeline';

const parser = new ResumeParser();
const resume = await parser.parse(pdfBuffer);

const evaluator = new Evaluator();
const score = await evaluator.evaluate(resume, jobDescription);
```
```

### 9. `packages/shared/README.md`

```markdown
# Shared Package

跨应用共享的工具和类型定义

## 包含内容

### Types
- 候选人类型
- 职位类型
- 评估结果类型
- API 响应类型

### Utils
- 日期处理
- 字符串处理
- 验证函数
- 格式化函数

### Constants
- 配置常量
- 枚举定义
- 错误代码

### Config
- 环境配置
- API 配置
- 功能开关

## 使用示例

```typescript
import { CandidateInfo, formatDate } from '@ai-headhunter/shared';

const candidate: CandidateInfo = {
  name: '张三',
  age: 30,
  // ...
};
```
```

### 10. `packages/scrapers/README.md`

```markdown
# Scrapers Package

多平台爬虫模块

## 支持平台

- ✅ Boss 直聘
- ⏳ 猎聘
- ⏳ LinkedIn
- ⏳ 脉脉

## 使用示例

```typescript
import { BossScraper } from '@ai-headhunter/scrapers';

const scraper = new BossScraper();
const candidates = await scraper.getCandidates({
  count: 10,
  position: 'AI工程师'
});
```

## 架构

- `base/`: 基础爬虫类
- `boss/`: Boss 直聘实现
- `liepin/`: 猎聘实现
- `linkedin/`: LinkedIn 实现
```

### 11. `docs/prd/README.md`

```markdown
# 产品需求文档

## 待迁移文档

- PRD-AI自动筛选简历系统.md
- 开发路线图.md
- MVP-开发计划.md

## 文档结构

- 功能需求
- 用户故事
- 验收标准
- 原型设计
```

### 12. `docs/tech/README.md`

```markdown
# 技术文档

## 待迁移文档

- CURSOR-SUBAGENT-使用指南.md
- 通义千问-使用指南.md
- 快速测试.md

## 文档类型

- 技术架构
- API 文档
- 部署文档
- 开发指南
```

### 13. `docs/mvp/README.md`

```markdown
# MVP 开发文档

## 待迁移文档

- 项目进度-Day1-3总结.md
- Day3-插件测试清单.md
- 🚀-项目启动指南.md

## 内容

- 开发进度
- 测试清单
- 里程碑记录
- 问题追踪
```

### 14. `scripts/setup.sh`

```bash
#!/bin/bash

echo "🚀 AI Headhunter Assistant - 环境设置"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js"
    exit 1
fi

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 安装 pnpm..."
    npm install -g pnpm
fi

# 安装依赖
echo "📦 安装依赖..."
pnpm install

# 设置环境变量
echo "⚙️  设置环境变量..."
cp backend/.env.example backend/.env

echo "✅ 设置完成！"
echo ""
echo "下一步："
echo "  1. 编辑 backend/.env 文件，填入你的 API Keys"
echo "  2. 运行 pnpm dev 启动开发服务器"
```

### 15. `config/tsconfig.base.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "allowJs": true,
    "checkJs": false,
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "composite": true,
    "incremental": true
  }
}
```

---

## 🎯 迁移优先级

### Phase 1: 基础设施（立即）
- ✅ 创建目录结构
- ✅ 添加 README 文件
- ✅ 配置 Monorepo

### Phase 2: 文档迁移（Day 8）
- 📝 移动文档到 `docs/` 子目录
- 📝 更新文档链接

### Phase 3: 代码重构（Day 9-10）
- 🔧 提取共享代码到 `packages/`
- 🔧 迁移应用到 `apps/`

### Phase 4: 优化（Day 11+）
- ⚡ 配置构建优化
- ⚡ 添加自动化测试
- ⚡ CI/CD 集成

---

## ✅ 优势

1. **模块化**：清晰的模块边界
2. **可复用**：共享包可以被多个应用使用
3. **可扩展**：易于添加新的应用和包
4. **类型安全**：统一的 TypeScript 配置
5. **开发效率**：Turborepo 加速构建
6. **团队协作**：清晰的代码组织

---

## 🔄 与现有代码的对应关系

| 现有位置 | 未来位置 | 说明 |
|---------|---------|------|
| `backend/` | `apps/backend/` | 后端服务 |
| `chrome-extension-v2/` | `apps/extension/` | Chrome 插件 |
| `demo_ai_resume_parser.py` | `demo/` | 技术验证 |
| `PRD-*.md` | `docs/prd/` | 产品文档 |
| `项目进度-*.md` | `docs/mvp/` | MVP 文档 |
| `通义千问-*.md` | `docs/tech/` | 技术文档 |

---

**准备好创建这个结构了吗？** 🚀

