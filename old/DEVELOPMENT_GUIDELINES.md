# 开发规范与发布流程

本文档定义了所有项目必须遵守的开发规范、测试要求和发布流程。

## ⚠️ 核心原则

**第一条规则：测试先行，发布在后**

所有代码在推送到 GitHub 并触发部署前，必须经过完整的本地测试。

---

## 🚀 发布流程（强制执行）

### 第一步：开发阶段

```bash
# 1. 从 dev 分支创建功能分支
git checkout dev
git checkout -b feature/your-feature-name

# 2. 开发功能
# ... 编写代码 ...

# 3. 本地测试（必须完成）
npm test        # 运行自动化测试
npm run lint    # 代码检查
# 手动测试所有新功能

# 4. 修复测试中发现的问题
```

### 第二步：测试阶段（⭐ 必须完成）

#### 测试检查清单

在推送到 GitHub 前，必须完成以下测试：

- [ ] **功能测试**：所有新功能按需求正常工作
- [ ] **回归测试**：原有功能不受影响
- [ ] **兼容性测试**：Chrome/Firefox/Safari/移动端
- [ ] **性能测试**：加载时间 < 3秒，API 响应 < 5秒
- [ ] **文档检查**：README.md 已更新
- [ ] **代码质量**：无调试代码，符合规范

### 第三步：提交到 dev

```bash
git checkout dev
git merge feature/your-feature-name
git push origin dev
```

### 第四步：合并到 main（⚠️ 只有测试通过后）

```bash
git checkout main
git merge dev
git push origin main  # 触发自动部署
```

---

## ❌ 禁止行为

1. ❌ **未经本地测试直接推送到 main**
2. ❌ **跳过 dev 分支直接推送到 main**
3. ❌ **在 main 分支直接开发**
4. ❌ **推送未完成或有明显 bug 的代码**
5. ❌ **不更新文档就发布新功能**

---

## 🌳 Git 分支策略

```
main (生产环境) ← 只接受从 dev 合并
  ↑
dev (开发环境)
  ↑
feature/* / fix/*
```

---

## 📝 Commit 规范

格式：`<type>(<scope>): <subject>`

类型：feat/fix/docs/style/refactor/perf/test/chore

---

## 🔐 安全规范

- ❌ 禁止将密钥提交到代码库
- ✅ 使用环境变量
- ✅ 使用 .env.example 模板

---

**⚠️ 重要提醒**：

1. **测试是发布的前提**
2. **main 分支受保护**
3. **文档必须同步**
4. **安全第一**

---

**最后更新**: 2025-01-21
