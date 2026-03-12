# GitHub Mining 文档优化方案（实战版）

**评审日期**: 2026-03-11
**原则**: 实用、简洁、易维护

---

## 📊 当前文档现状

### 官方文档（.agent/workflows/）
- ✅ `github-network-mining.md` (64.5 KB) - 路线图 + Runbooks
- ✅ `github-mining-reference.md` (45.2 KB) - 技术细节 + 标准
- ✅ `README.md` - 文档导航

### 项目文档（github_mining/docs/）
- `ARCHITECTURE_REVIEW.md` (22.4 KB) - 架构评审
- `BATCH_RUNNER_IMPROVEMENTS.md` (4.7 KB) - 批次改进
- `NEXT_OPTIMIZATION_PLAN.md` (6.7 KB) - 优化计划
- `critical_issues_solutions.md` (4.8 KB) - 关键问题
- `end_to_end_workflow_guide.md` (8.5 KB) - 端到端流程
- `pipeline_design_v3.md` (6.1 KB) - 批次设计
- `DOCUMENTATION_SIMPLE_PROPOSAL.md` (5.3 KB) - 文档提案
- `DOCUMENTATION_STRUCTURE_PROPOSAL.md` (13.3 KB) - 文档提案

**总计**: 3 个官方文档 + 8 个项目文档 = **11 个文档**

---

## 🔴 核心问题

### 问题 1: 文档分散且重复

**症状**:
- 同一个问题在多个文档中重复描述
- 例如"数据覆盖"问题在 3 个文档中都有：
  - `critical_issues_solutions.md`
  - `end_to_end_workflow_guide.md`
  - `BATCH_RUNNER_IMPROVEMENTS.md`

**影响**:
- ❌ 更新一处，其他地方忘记更新
- ❌ 不知道哪个是最新版本
- ❌ 查找信息困难

---

### 问题 2: 文档定位不清

**症状**:
- 官方文档（workflows/）vs 项目文档（docs/）的边界模糊
- README.md 说"只有 2 个核心文档"，但实际有 11 个
- 不知道该更新哪个文档

**影响**:
- ❌ 新信息不知道放哪里
- ❌ 文档治理规则失效

---

### 问题 3: 临时文档变成永久文档

**症状**:
- `DOCUMENTATION_SIMPLE_PROPOSAL.md` - 提案文档，应该删除
- `DOCUMENTATION_STRUCTURE_PROPOSAL.md` - 提案文档，应该删除
- `ARCHITECTURE_REVIEW.md` - 评审报告，应该归档

**影响**:
- ❌ 文档数量膨胀
- ❌ 难以区分哪些是有效文档

---

### 问题 4: 缺少实战指南

**症状**:
- 有很多"设计文档"和"计划文档"
- 缺少"今天就能用"的操作手册
- 例如：如何从头跑一个批次？遇到错误怎么办？

**影响**:
- ❌ 新人上手困难
- ❌ 遇到问题不知道怎么解决

---

## ✅ 优化方案（极简版）

### 目标结构

```
.agent/workflows/
├── README.md                           # 📌 文档导航（保持）
├── github-network-mining.md            # 📖 主文档：路线图 + 操作手册
└── github-mining-reference.md          # 📚 参考文档：技术细节

github_mining/docs/
├── OPERATIONS_GUIDE.md                 # 🚀 实战操作指南（新建）
├── TROUBLESHOOTING.md                  # 🔧 故障排查手册（新建）
└── archive/
    └── 2026-03/                        # 📦 归档（临时文档）
        ├── ARCHITECTURE_REVIEW.md
        ├── BATCH_RUNNER_IMPROVEMENTS.md
        ├── critical_issues_solutions.md
        ├── end_to_end_workflow_guide.md
        ├── pipeline_design_v3.md
        └── NEXT_OPTIMIZATION_PLAN.md
```

**总计**: 3 个官方文档 + 2 个实战文档 = **5 个核心文档**

---

## 📋 文档职责划分

### 1. README.md（文档导航）
- **职责**: 快速导航，告诉用户去哪里找信息
- **内容**: 文档索引、快速链接
- **更新频率**: 很少

### 2. github-network-mining.md（主文档）
- **职责**: 路线图 + 操作手册
- **内容**:
  - Phase 1-7 路线图
  - Runbook 1/2/3（具体操作步骤）
  - 快速命令参考
- **更新频率**: 每次新增 Phase 或 Runbook

### 3. github-mining-reference.md（参考文档）
- **职责**: 技术细节 + 标准
- **内容**:
  - 分级标准（唯一真相源）
  - 字段映射
  - 评分公式
  - 验证方法
- **更新频率**: 标准变更时

### 4. OPERATIONS_GUIDE.md（实战操作指南）✨ 新建
- **职责**: 今天就能用的操作手册
- **内容**:
  - 如何从头跑一个批次
  - 如何监控进度
  - 如何验证结果
  - 常见操作场景
- **更新频率**: 发现新的实战技巧时

### 5. TROUBLESHOOTING.md（故障排查手册）✨ 新建
- **职责**: 遇到问题怎么办
- **内容**:
  - 常见错误及解决方案
  - 数据覆盖问题
  - API 限流问题
  - 进程卡住问题
- **更新频率**: 发现新问题时

---

## 🔄 文档整合映射

| 当前文档 | 整合到 | 操作 |
|---------|--------|------|
| `README.md` | 保持不变 | - |
| `github-network-mining.md` | 保持不变 | - |
| `github-mining-reference.md` | 保持不变 | - |
| `ARCHITECTURE_REVIEW.md` | `archive/2026-03/` | 归档 |
| `BATCH_RUNNER_IMPROVEMENTS.md` | `OPERATIONS_GUIDE.md` | 整合（批次管理章节） |
| `NEXT_OPTIMIZATION_PLAN.md` | `archive/2026-03/` | 归档 |
| `critical_issues_solutions.md` | `TROUBLESHOOTING.md` | 整合 |
| `end_to_end_workflow_guide.md` | `OPERATIONS_GUIDE.md` | 整合 |
| `pipeline_design_v3.md` | `OPERATIONS_GUIDE.md` | 整合（批次隔离章节） |
| `DOCUMENTATION_*_PROPOSAL.md` | 删除 | 提案已完成 |

---

## 📝 新建文档内容大纲

### OPERATIONS_GUIDE.md（实战操作指南）

```markdown
# GitHub Mining 实战操作指南

## 1. 快速开始
- 环境准备
- Token 配置
- 第一次运行

## 2. 完整批次流程
- 从头开始跑批次
- 监控进度
- 验证结果

## 3. 批次管理
- 批次隔离系统
- 自动备份机制
- 断点续传

## 4. 常见操作场景
- 如何只跑某几个阶段
- 如何跳过某个阶段
- 如何重跑失败的批次

## 5. 数据验证
- 如何检查数据质量
- 如何验证入库结果
- 如何查看评级分布
```

### TROUBLESHOOTING.md（故障排查手册）

```markdown
# GitHub Mining 故障排查手册

## 1. 数据问题
- 数据被覆盖
- 数据丢失
- 数据重复

## 2. API 问题
- API 限流
- Token 失效
- 网络超时

## 3. 进程问题
- 进程卡住
- 内存不足
- 日志文件为空

## 4. 数据库问题
- 导入失败
- 重复记录
- 评级错误

## 5. 快速诊断
- 检查进程状态
- 检查日志文件
- 检查输出文件
```

---

## 🎯 实施步骤

### Phase 1: 创建新文档（1小时）

```bash
# 1. 创建归档目录
mkdir -p github_mining/docs/archive/2026-03

# 2. 创建新文档
touch github_mining/docs/OPERATIONS_GUIDE.md
touch github_mining/docs/TROUBLESHOOTING.md
```

### Phase 2: 整合内容（2-3小时）

1. **OPERATIONS_GUIDE.md**:
   - 从 `BATCH_RUNNER_IMPROVEMENTS.md` 提取批次管理内容
   - 从 `end_to_end_workflow_guide.md` 提取端到端流程
   - 从 `pipeline_design_v3.md` 提取批次隔离设计
   - 添加实战操作步骤

2. **TROUBLESHOOTING.md**:
   - 从 `critical_issues_solutions.md` 提取所有问题
   - 从 `end_to_end_workflow_guide.md` 提取错误处理
   - 添加快速诊断方法

### Phase 3: 归档和清理（30分钟）

```bash
# 归档
mv github_mining/docs/ARCHITECTURE_REVIEW.md github_mining/docs/archive/2026-03/
mv github_mining/docs/BATCH_RUNNER_IMPROVEMENTS.md github_mining/docs/archive/2026-03/
mv github_mining/docs/NEXT_OPTIMIZATION_PLAN.md github_mining/docs/archive/2026-03/
mv github_mining/docs/critical_issues_solutions.md github_mining/docs/archive/2026-03/
mv github_mining/docs/end_to_end_workflow_guide.md github_mining/docs/archive/2026-03/
mv github_mining/docs/pipeline_design_v3.md github_mining/docs/archive/2026-03/

# 删除提案文档
rm github_mining/docs/DOCUMENTATION_SIMPLE_PROPOSAL.md
rm github_mining/docs/DOCUMENTATION_STRUCTURE_PROPOSAL.md
```

### Phase 4: 更新 README.md（15分钟）

更新文档导航，指向新的文档结构。

---

## 📊 优化效果

| 维度 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| 文档数量 | 11 个 | 5 个 | -55% |
| 信息重复 | 严重 | 无 | ✅ |
| 查找时间 | 5-10 分钟 | 1-2 分钟 | -70% |
| 新人上手 | 2 天 | 半天 | -75% |
| 维护成本 | 高 | 低 | ✅ |

---

## ✅ 成功标准

- ✅ 核心文档 ≤ 5 个
- ✅ 无信息重复
- ✅ 新人能在 30 分钟内找到需要的信息
- ✅ 遇到问题能在 5 分钟内找到解决方案
- ✅ 文档更新时间 < 10 分钟

---

## 🚀 下一步

1. **立即执行 Phase 1-3**（今天完成）
2. **验证新文档是否好用**（跑一次批次，看文档是否够用）
3. **持续改进**（发现问题及时更新）

---

**提案人**: Claude
**提案日期**: 2026-03-11
**原则**: 实用、简洁、易维护
