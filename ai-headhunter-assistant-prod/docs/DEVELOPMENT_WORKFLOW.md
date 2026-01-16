# 双环境开发工作流使用指南

## 📋 概述

项目现在支持**稳定版本**和**开发版本**并行运行，互不干扰：

- **稳定版本** (master 分支)：用于日常使用，保证稳定性
- **开发版本** (develop 分支)：用于优化和新功能开发

---

## 🌳 分支结构

```
master (稳定版 - v1.0-mvp)
  └── develop (开发版 - 优化中)
```

---

## 🚀 使用方式

### 方式一：使用稳定版本（日常工作）

#### 1. 切换到 master 分支

```bash
cd /Users/lillianliao/notion_rag/ai-headhunter-assistant
git checkout master
```

#### 2. 启动后端服务

```bash
cd backend
./start_prod.sh
```

服务将在 **http://localhost:8000** 运行

#### 3. 加载 Chrome 插件

1. 打开 `chrome://extensions/`
2. 确保插件配置指向 `http://localhost:8000`
3. 加载 `chrome-extension-v2` 目录

---

### 方式二：进行开发工作

#### 1. 切换到 develop 分支

```bash
cd /Users/lillianliao/notion_rag/ai-headhunter-assistant
git checkout develop
```

#### 2. 启动开发服务器

```bash
cd backend
./start_dev.sh
```

服务将在 **http://localhost:8001** 运行（带热重载）

#### 3. 修改代码

- 修改后端代码，服务会自动重启
- 修改插件代码，需要手动重新加载插件

#### 4. 提交开发进度

```bash
git add .
git commit -m "feat: 添加新功能"
```

---

### 方式三：同时运行两个版本

如果需要对比测试，可以同时运行：

#### 终端 1：稳定版

```bash
git checkout master
cd backend
./start_prod.sh  # 端口 8000
```

#### 终端 2：开发版

```bash
git checkout develop
cd backend
./start_dev.sh   # 端口 8001
```

---

## 📝 配置文件说明

### `.env.production` (稳定版配置)

- 端口：8000
- 调试模式：关闭
- 应用名称：AI猎头助手

### `.env.development` (开发版配置)

- 端口：8001
- 调试模式：开启
- 应用名称：AI猎头助手[开发版]
- 热重载：开启

---

## 🔄 工作流程

### 日常使用流程

```bash
# 1. 使用稳定版本
git checkout master
cd backend && ./start_prod.sh

# 2. 正常使用插件进行工作
```

### 开发优化流程

```bash
# 1. 切换到开发分支
git checkout develop

# 2. 启动开发服务器
cd backend && ./start_dev.sh

# 3. 修改代码、测试

# 4. 提交更改
git add .
git commit -m "feat: 优化功能"

# 5. 测试通过后，合并到 master
git checkout master
git merge develop

# 6. 打新版本标签
git tag -a v1.1 -m "优化版本"

# 7. 推送到 GitHub
git push origin master --tags
```

---

## ⚠️ 注意事项

### 1. 端口冲突

- 稳定版使用 **8000** 端口
- 开发版使用 **8001** 端口
- 确保两个端口都未被占用

### 2. Chrome 插件配置

如果同时运行两个版本，需要：

- 方案 A：使用两个不同的 Chrome 配置文件
- 方案 B：手动修改插件配置切换端口

### 3. 数据库/文件冲突

如果使用本地数据库或文件存储，注意：
- 两个版本共享同一个数据库
- 开发版的修改可能影响稳定版
- 建议在开发版使用测试数据

---

## 🔧 故障排查

### 问题 1：端口已被占用

```bash
# 查看端口占用
lsof -i :8000
lsof -i :8001

# 杀死进程
kill -9 <PID>
```

### 问题 2：环境配置未生效

```bash
# 检查当前使用的配置
cat backend/.env

# 手动复制配置
cp backend/.env.production backend/.env  # 稳定版
cp backend/.env.development backend/.env # 开发版
```

### 问题 3：分支切换后代码未更新

```bash
# 确认当前分支
git branch

# 强制切换分支
git checkout -f master
git checkout -f develop
```

---

## 📊 快速参考

| 操作 | 稳定版 (master) | 开发版 (develop) |
|------|----------------|-----------------|
| 切换分支 | `git checkout master` | `git checkout develop` |
| 启动服务 | `./start_prod.sh` | `./start_dev.sh` |
| 端口 | 8000 | 8001 |
| 调试模式 | 关闭 | 开启 |
| 热重载 | 关闭 | 开启 |
| 用途 | 日常使用 | 开发优化 |

---

## 🎯 最佳实践

1. **保持 master 分支稳定**：只合并经过测试的代码
2. **频繁提交 develop 分支**：小步快跑，便于回滚
3. **使用有意义的提交信息**：遵循 Conventional Commits
4. **定期同步到 GitHub**：`git push origin develop`
5. **测试后再合并**：确保功能完整才合并到 master

---

## 📞 需要帮助？

如果遇到问题，检查：
1. 当前所在分支：`git branch`
2. 服务运行端口：`lsof -i :8000` 和 `lsof -i :8001`
3. 环境配置文件：`cat backend/.env`
