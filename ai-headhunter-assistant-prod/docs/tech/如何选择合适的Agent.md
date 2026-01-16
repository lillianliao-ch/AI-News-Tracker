# 如何选择合适的 Agent - 快速指南

## 🤔 我应该用哪个 Agent？

### 方法 1: 根据任务类型选择（推荐）

#### 场景：我想添加/修改功能

| 功能描述 | 推荐 Agent | 示例提问 |
|---------|-----------|---------|
| 📱 前端界面、用户交互 | **Web Agent** | "添加一个候选人列表页面" |
| 🔌 浏览器插件功能 | **Extension Agent** | "在 Boss 页面添加一键导出按钮" |
| 🔧 后端 API、业务逻辑 | **Backend Agent** | "实现候选人搜索接口" |
| 🤖 AI 评估、匹配算法 | **AI Pipeline Agent** | "优化简历匹配度计算" |
| 🕷️ 数据采集、页面解析 | **Scraper Agent** | "提取候选人的教育背景" |
| 📦 共享代码、类型定义 | **Shared Agent** | "定义候选人信息的类型" |

#### 场景：我想改进代码质量

| 需求描述 | 推荐 Agent | 示例提问 |
|---------|-----------|---------|
| 🔍 检查代码问题 | **Reviewer Agent** | "审查这段代码的安全性" |
| ♻️ 重构优化代码 | **Refactor Agent** | "这个函数太长了，帮我拆分" |
| 📝 编写/更新文档 | **Docs Agent** | "为这个 API 写使用文档" |
| 🚀 部署、CI/CD | **DevOps Agent** | "配置自动部署流程" |

---

## 📋 根据文件路径选择

### 直接看你要修改哪个文件

```bash
# 示例 1: 我要修改 apps/extension/content-full.js
→ 这是 Chrome 插件文件
→ 使用 @ExtensionAgent

# 示例 2: 我要修改 apps/backend/app/main.py
→ 这是后端代码
→ 使用 @BackendAgent

# 示例 3: 我要修改 packages/shared/src/types/candidate.ts
→ 这是共享类型定义
→ 使用 @SharedAgent

# 示例 4: 我要修改 docs/tech/guide.md
→ 这是文档
→ 使用 @DocsAgent
```

### 文件路径 → Agent 映射表

| 文件路径 | Agent | 说明 |
|---------|-------|------|
| `apps/web/**/*` | Web Agent | Next.js Web 应用 |
| `apps/backend/**/*` | Backend Agent | FastAPI 后端 |
| `apps/extension/**/*` | Extension Agent | Chrome 插件 |
| `packages/ai-pipeline/**/*` | AI Pipeline Agent | AI 处理逻辑 |
| `packages/scrapers/**/*` | Scraper Agent | 爬虫模块 |
| `packages/shared/**/*` | Shared Agent | 共享代码 |
| `docs/**/*`, `*.md` | Docs Agent | 文档文件 |
| `.github/workflows/**/*` | DevOps Agent | CI/CD 配置 |
| `scripts/**/*` | DevOps Agent | 部署脚本 |

---

## 🎯 实战示例：如何提问

### 示例 1: 新功能开发

#### ❌ 不好的提问
```
帮我做一个功能
```
**问题**: 太模糊，无法判断 Agent

#### ✅ 好的提问
```
我想在 Chrome 插件中添加一个"导出推荐候选人"的按钮，
点击后自动下载所有推荐等级的候选人信息为 Excel 文件
```
**Cursor 会识别**: Extension Agent（插件 UI + 导出逻辑）

#### ⭐ 更好的提问（明确指定）
```
@ExtensionAgent 
在控制面板添加"导出推荐候选人"按钮，使用 SheetJS 导出 Excel

@DocsAgent 
为这个导出功能编写使用文档
```

---

### 示例 2: 跨模块功能

#### ❌ 不好的提问
```
我想改一下候选人信息的结构
```
**问题**: 不清楚要改哪里

#### ✅ 好的提问
```
我想在候选人信息中新增"期望薪资"字段，需要：
1. 在共享类型中定义这个字段
2. 后端 API 支持这个字段
3. 前端插件采集这个信息
```
**Cursor 会建议**: 需要 3 个 Agents 协作

#### ⭐ 更好的提问（分步骤）
```
第 1 步:
@SharedAgent 
在 CandidateInfo 类型中添加 expected_salary 字段

第 2 步:
@BackendAgent 
更新 API 以支持 expected_salary 字段

第 3 步:
@ExtensionAgent 
在页面采集逻辑中提取期望薪资信息
```

---

### 示例 3: Bug 修复

#### ❌ 不好的提问
```
有个 bug，帮我修一下
```
**问题**: 没说是哪里的 bug

#### ✅ 好的提问
```
Chrome 插件在点击"开始处理"后没有反应，
控制台显示 "Cannot read property 'length' of undefined"
```
**Cursor 会识别**: Extension Agent（插件问题）

#### ⭐ 更好的提问
```
@ExtensionAgent 
修复 content-full.js 中的 bug：
- 位置: getCandidates() 函数
- 错误: candidateList 为 undefined
- 原因: 可能是选择器失效或元素未加载
```

---

### 示例 4: 代码优化

#### ❌ 不好的提问
```
这段代码不太好，改一下
```
**问题**: 不清楚要怎么改

#### ✅ 好的提问
```
apps/backend/app/main.py 的 process_candidate 函数太长了（200行），
能帮我拆分一下吗？
```
**Cursor 会识别**: Refactor Agent（重构任务）

#### ⭐ 更好的提问
```
@RefactorAgent 
重构 apps/backend/app/main.py:45-245
- 提取简历解析逻辑到 services/resume_parser.py
- 提取 AI 评估逻辑到 services/evaluator.py
- 主函数只保留流程编排
```

---

## 🚨 常见错误和解决方案

### 错误 1: Agent 拒绝修改文件

**错误提示**:
```
❌ Extension Agent 无法修改 apps/backend/app/main.py
这个文件不在我的职责范围内
```

**原因**: 选错了 Agent

**解决方案**:
```
✅ 使用正确的 Agent
@BackendAgent 修改 apps/backend/app/main.py
```

---

### 错误 2: 需要多个 Agent 协作

**错误提示**:
```
⚠️ 这个任务涉及多个模块，建议分步骤进行
```

**解决方案**:
```
✅ 分步骤执行

第 1 步: @SharedAgent 定义共享类型
第 2 步: @BackendAgent 实现后端逻辑
第 3 步: @ExtensionAgent 实现前端交互
第 4 步: @DocsAgent 更新文档
```

---

### 错误 3: 不确定用哪个 Agent

**解决方案 A: 直接问**
```
我想实现以下功能，应该用哪个 Agent？
- [描述你的需求]
```

**解决方案 B: 先不指定，让 Cursor 判断**
```
# 不用 @Agent，直接描述任务
我想在 Boss 直聘页面添加一个快速筛选按钮
```

**解决方案 C: 查看决策树**
```
→ 功能在浏览器页面上？
  → 是 Boss 直聘等外部页面？
    → 是: Extension Agent
    → 否: Web Agent
  → 否: 继续判断...
```

---

## 🎓 决策树：我该用哪个 Agent？

```
开始
 │
 ├─ 我要写文档？
 │   └─ 是 → Docs Agent
 │
 ├─ 我要审查代码？
 │   └─ 是 → Reviewer Agent
 │
 ├─ 我要重构代码？
 │   └─ 是 → Refactor Agent
 │
 ├─ 我要配置 CI/CD 或部署？
 │   └─ 是 → DevOps Agent
 │
 ├─ 我要修改功能或添加新功能？
 │   │
 │   ├─ 功能在浏览器页面上？
 │   │   ├─ 是外部网站（Boss 直聘等）？
 │   │   │   └─ 是 → Extension Agent
 │   │   └─ 是我们自己的网站？
 │   │       └─ 是 → Web Agent
 │   │
 │   ├─ 功能在后端 API？
 │   │   └─ 是 → Backend Agent
 │   │
 │   ├─ 功能是 AI 相关（评估、匹配、生成）？
 │   │   └─ 是 → AI Pipeline Agent
 │   │
 │   ├─ 功能是数据采集（爬虫、解析）？
 │   │   └─ 是 → Scraper Agent
 │   │
 │   └─ 功能是共享代码（类型、工具）？
 │       └─ 是 → Shared Agent
 │
 └─ 还是不确定？
     └─ 直接描述任务，让 Cursor 自动选择！
```

---

## 💡 最佳实践

### 1. 任务明确 > Agent 明确

```bash
# ⭐ 推荐：任务描述清楚，Agent 自动识别
我想在插件中添加一个"暂停处理"按钮

# 也可以：明确指定 Agent
@ExtensionAgent 添加"暂停处理"按钮
```

### 2. 大任务分解

```bash
# ❌ 不好：一次性要求太多
实现完整的候选人管理系统

# ✅ 好：分步骤
第 1 步: 数据模型定义
第 2 步: 后端 API 实现
第 3 步: 前端页面实现
第 4 步: 文档编写
```

### 3. 从具体文件入手

```bash
# 如果你知道要改哪个文件
我要修改 apps/extension/content-full.js
→ 自动识别为 Extension Agent

# 如果你不知道要改哪个文件
我想优化候选人信息的采集速度
→ Cursor 会帮你找到相关文件并选择 Agent
```

### 4. 善用多 Agent 协作

```bash
# 复杂功能，明确分工
@SharedAgent 定义 CandidateSearchRequest 类型
@BackendAgent 实现搜索 API
@ExtensionAgent 实现搜索 UI
@DocsAgent 编写搜索功能文档
```

---

## 📚 快速参考卡片

打印或保存这个速查表：

```
┌─────────────────────────────────────────┐
│   Cursor Multi-Agent 快速参考卡片      │
├─────────────────────────────────────────┤
│ 🌐 Web Agent          → apps/web/      │
│ 🔌 Extension Agent    → apps/extension/│
│ 🔧 Backend Agent      → apps/backend/  │
│ 🤖 AI Pipeline Agent  → AI 逻辑         │
│ 🕷️ Scraper Agent      → 爬虫逻辑       │
│ 📦 Shared Agent       → 共享代码        │
│ 📝 Docs Agent         → 文档           │
│ 🔍 Reviewer Agent     → 代码审查        │
│ ♻️ Refactor Agent     → 代码重构        │
│ 🚀 DevOps Agent       → 部署/CI/CD     │
├─────────────────────────────────────────┤
│ 💡 提示：不确定就直接描述任务，       │
│    让 Cursor 自动选择！                │
└─────────────────────────────────────────┘
```

---

## 🎯 总结

### 3 种使用方式（按推荐程度排序）

1. **最简单**：直接描述任务，不指定 Agent
   ```
   我想在插件添加导出功能
   ```

2. **更精确**：根据文件路径或功能类型选择 Agent
   ```
   @ExtensionAgent 在 content-full.js 添加导出功能
   ```

3. **最复杂**：大任务分解，多 Agent 协作
   ```
   @SharedAgent 定义导出数据格式
   @ExtensionAgent 实现导出功能
   @DocsAgent 编写使用文档
   ```

### 记住：

- ✅ **任务清楚比 Agent 清楚更重要**
- ✅ **从文件路径入手最简单**
- ✅ **大任务要分解**
- ✅ **不确定就问 Cursor**

---

**现在开始使用 Multi-Agent 高效开发吧！** 🚀

