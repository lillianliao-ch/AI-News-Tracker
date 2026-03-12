# Git 工作流指南 - 个人项目最佳实践

## 📋 核心原则

**一个 Git 仓库 + 两个运行环境**

```
项目名/                    ← Git 仓库（开发环境）
├── .git/                 ← 版本控制
├── develop 分支          ← 日常开发
├── main 分支             ← 稳定版本
└── 运行在端口 X

项目名-prod/              ← 生产环境（无 Git）
└── 运行在端口 X+1
```

---

## 🚀 项目初始化

### 1. 创建项目结构

```bash
cd ~/notion_rag  # 或你的项目目录

# 创建开发环境（Git 仓库）
mkdir my-project
cd my-project
git init
git branch -M main

# 创建 develop 分支
git checkout -b develop

# 创建生产环境目录
cd ..
mkdir my-project-prod
```

### 2. 配置 .gitignore

```bash
# 在 my-project/ 中创建 .gitignore
cat > .gitignore << 'EOF'
# 数据文件
data/
*.db
*.sqlite3

# Python
__pycache__/
*.pyc
.env

# IDE
.vscode/
.idea/
.DS_Store
EOF
```

### 3. 创建启动脚本

**开发环境** (`my-project/start.sh`):
```bash
#!/bin/bash
echo "🛠️  Development Environment"
export ENV=development
# 启动命令（根据项目类型调整）
streamlit run app.py --server.port 8501
# 或 python main.py
# 或 npm run dev
```

**生产环境** (`my-project-prod/start.sh`):
```bash
#!/bin/bash
echo "🚀 Production Environment"
export ENV=production
# 启动命令
streamlit run app.py --server.port 8502
```

```bash
chmod +x my-project/start.sh
chmod +x my-project-prod/start.sh
```

### 4. 连接 GitHub（可选）

```bash
cd my-project
git remote add origin https://github.com/你的用户名/项目名.git
```

---

## 💻 日常开发流程

### 开发新功能

```bash
cd my-project

# 1. 确保在 develop 分支
git checkout develop

# 2. 启动开发环境
./start.sh  # 访问 http://localhost:端口

# 3. 修改代码...

# 4. 提交更改
git add .
git commit -m "feat: 功能描述"

# 5. 继续开发或测试
```

### 提交规范

```bash
git commit -m "feat: 添加新功能"      # 新功能
git commit -m "fix: 修复 bug"        # Bug 修复
git commit -m "docs: 更新文档"       # 文档
git commit -m "refactor: 重构代码"   # 重构
git commit -m "test: 添加测试"       # 测试
```

---

## 🎯 发布稳定版本

### 完整发布流程

```bash
cd my-project

# 1. 确保 develop 分支已提交所有更改
git checkout develop
git status  # 确认无未提交的更改

# 2. 切换到 main 分支
git checkout main

# 3. 合并 develop 分支
git merge develop

# 4. 打版本标签
git tag -a v1.0 -m "版本 1.0 - 功能描述"

# 5. 推送到 GitHub（可选，建议做）
git push origin main --tags

# 6. 部署到生产环境
cd ..
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' \
  my-project/ my-project-prod/

# 7. 重启生产环境
cd my-project-prod
./start.sh

# 8. 切回 develop 继续开发
cd ../my-project
git checkout develop
```

---

## 🔄 版本管理

### 查看版本历史

```bash
# 查看所有标签（稳定版本）
git tag

# 查看提交历史
git log --oneline --graph --all

# 查看某个文件的修改历史
git log --oneline -- 文件名
```

### 回退到旧版本

```bash
# 临时查看旧版本
git checkout v1.0
./start.sh  # 测试旧版本

# 回到最新版本
git checkout develop

# 永久回退（谨慎使用）
git reset --hard v1.0
```

### 生产环境版本切换

```bash
cd my-project

# 切换到指定版本
git checkout v1.0  # 或 git checkout main

# 部署到生产
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' \
  my-project/ my-project-prod/

# 重启生产环境
cd my-project-prod
./start.sh
```

---

## 📊 分支策略

### 分支说明

| 分支 | 用途 | 推送到 GitHub |
|------|------|--------------|
| `develop` | 日常开发 | 可选（不推荐） |
| `main` | 稳定版本 | 推荐 |
| `feature/*` | 实验性功能 | 不推荐 |

### 创建功能分支（可选）

```bash
# 从 develop 创建功能分支
git checkout develop
git checkout -b feature/new-feature

# 开发和测试...
git commit -m "feat: 新功能"

# 合并回 develop
git checkout develop
git merge feature/new-feature

# 删除功能分支
git branch -d feature/new-feature
```

---

## 🛠️ 常用命令速查

```bash
# 切换分支
git checkout develop      # 切换到开发分支
git checkout main         # 切换到主分支

# 查看状态
git status               # 查看当前状态
git branch              # 查看所有分支
git tag                 # 查看所有标签

# 提交代码
git add .               # 添加所有更改
git commit -m "消息"    # 提交
git push                # 推送到 GitHub

# 部署到生产
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' \
  项目名/ 项目名-prod/
```

---

## ⚠️ 注意事项

### 1. 数据安全

- ✅ **开发环境**：可以随意测试，数据可以重置
- ⚠️ **生产环境**：数据很重要，定期备份

```bash
# 备份生产数据
cp -r my-project-prod/data/ backup-$(date +%Y%m%d)/
```

### 2. 切换分支前检查

```bash
# 切换分支前，确保提交或暂存更改
git status

# 如果有未提交的更改
git add .
git commit -m "WIP: 开发中"

# 或使用 stash 临时保存
git stash
git checkout main
git stash pop
```

### 3. 端口管理

- 开发环境：8501, 3000, 5000...
- 生产环境：8502, 3001, 5001...（开发端口 +1）

### 4. GitHub 推送策略

- **频繁推送**：如果担心数据丢失
- **定期推送**：每个稳定版本推送一次
- **选择性推送**：只推送 main 分支和标签

---

## 📁 项目模板

```
my-project/                    # Git 仓库 + 开发环境
├── .git/
├── .gitignore
├── README.md
├── start.sh                   # 开发启动脚本
├── data/                      # 开发数据（不提交）
├── src/                       # 源代码
└── requirements.txt           # 依赖

my-project-prod/               # 生产环境
├── start.sh                   # 生产启动脚本
├── data/                      # 生产数据（重要！）
└── [代码文件从 Git 复制]
```

---

## 🎯 快速参考卡片

### 日常开发
```bash
cd my-project
git checkout develop
./start.sh
git commit -m "feat: ..."
```

### 发布版本
```bash
git checkout main
git merge develop
git tag -a v1.0 -m "..."
git push origin main --tags
rsync ... my-project-prod/
```

### 回退版本
```bash
git checkout v1.0
rsync ... my-project-prod/
```

---

## 📞 故障排查

### 问题 1：端口被占用
```bash
lsof -i :8501
kill -9 <PID>
```

### 问题 2：Git 冲突
```bash
git status
git merge --abort  # 取消合并
# 或手动解决冲突后
git add .
git commit
```

### 问题 3：误删文件
```bash
git checkout -- 文件名  # 恢复单个文件
git reset --hard HEAD   # 恢复所有文件
```

---

## 📝 版本号规范

使用语义化版本号：`v主版本.次版本.修订号`

```
v1.0.0 - 初始版本
v1.1.0 - 新功能（兼容）
v1.1.1 - Bug 修复
v2.0.0 - 重大更新（可能不兼容）
```

---

**最后更新**: 2024-12-12  
**适用于**: 个人项目、小团队项目
