# ⚠️ 重要：请先阅读官方文档

**在修改任何代码或文档之前，必须先阅读官方文档！**

---

## 📚 官方文档位置

```
/.agent/workflows/
├── github-network-mining.md        ← 主文档（路线图 + 操作手册）
└── github-mining-reference.md      ← 参考文档（技术标准）
```

---

## 🎯 为什么要先读官方文档？

### ✅ 官方文档包含：
- 完整的项目路线图（Phase 1-7）
- 所有阶段的详细说明
- 分级标准（唯一真相源）
- 标准操作流程（Runbook）
- 历史执行记录

### ❌ 项目 docs/ 下的文档：
- 是补充材料，不完整
- 是实战指南和故障排查
- 需要配合官方文档使用

---

## 📖 文档阅读顺序

### 新手入门
1. **第一步**: 阅读 `github-network-mining.md`（了解项目）
2. **第二步**: 阅读 `github-mining-reference.md`（了解标准）
3. **第三步**: 阅读 `docs/OPERATIONS_GUIDE.md`（学习操作）

### 执行任务时
1. 查看 `github-network-mining.md` 的"待办事项"
2. 参考 `docs/OPERATIONS_GUIDE.md` 的操作步骤
3. 遇到问题查看 `docs/TROUBLESHOOTING.md`

### 跑批次后
1. 更新 `docs/BATCH_HISTORY.md`（记录批次）
2. 如有问题，更新 `docs/TROUBLESHOOTING.md`
3. 如有优化点，更新 `github-network-mining.md` 的"待办事项"

---

## 🚨 给 AI 的重要提示

**如果你是 AI，请确保：**

1. ✅ 已经读取 `/.agent/workflows/github-network-mining.md`
2. ✅ 已经读取 `/.agent/workflows/github-mining-reference.md`
3. ✅ 了解项目的完整路线图和标准
4. ✅ 查看了"待办事项"，知道接下来要做什么

**不要：**
- ❌ 只看 `docs/` 下的文档就开始工作
- ❌ 基于不完整的信息做决策
- ❌ 重复已经解决的问题

---

## 📂 完整文档结构

```
/.agent/workflows/                      # 官方文档（必读）
├── README.md                           # 文档导航
├── github-network-mining.md            # 主文档：路线图 + 待办 + 操作
└── github-mining-reference.md          # 参考：技术标准

/github_mining/docs/                    # 实战文档（补充）
├── 00-START-HERE.md                    # 本文件（强制入口）
├── OPERATIONS_GUIDE.md                 # 实战操作指南
├── TROUBLESHOOTING.md                  # 故障排查手册
├── BATCH_HISTORY.md                    # 批次执行历史
└── archive/                            # 归档文档
```

---

## 🔗 快速链接

- [主文档 - 路线图](../../.agent/workflows/github-network-mining.md)
- [参考文档 - 技术标准](../../.agent/workflows/github-mining-reference.md)
- [实战操作指南](./OPERATIONS_GUIDE.md)
- [故障排查手册](./TROUBLESHOOTING.md)
- [批次执行历史](./BATCH_HISTORY.md)

---

**最后更新**: 2026-03-11
**维护者**: GitHub Mining Team
