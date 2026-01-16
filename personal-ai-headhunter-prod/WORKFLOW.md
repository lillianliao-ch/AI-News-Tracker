# Personal AI Headhunter - 项目工作流

> 本项目遵循标准 Git 工作流，详细指南请参考：[/Users/lillianliao/notion_rag/GIT_WORKFLOW_GUIDE.md](file:///Users/lillianliao/notion_rag/GIT_WORKFLOW_GUIDE.md)

## 🎯 项目结构

```
personal-ai-headhunter/          ← Git 仓库 + 开发环境
├── .git/
├── develop 分支                 ← 日常开发
├── main 分支                    ← 稳定版本
└── 端口 8501

personal-ai-headhunter-prod/     ← 生产环境
└── 端口 8502
```

## 🚀 快速开始

### 日常开发

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
git checkout develop
./start.sh  # 访问 http://localhost:8501

# 修改代码...
git add .
git commit -m "feat: 功能描述"
```

### 发布稳定版本

```bash
# 1. 合并到 main 分支
git checkout main
git merge develop

# 2. 打标签
git tag -a v1.0 -m "版本 1.0 - 功能描述"

# 3. 推送到 GitHub（可选）
git push origin main --tags

# 4. 部署到生产
./deploy_to_prod.sh

# 5. 启动生产环境
cd /Users/lillianliao/notion_rag/personal-ai-headhunter-prod
./start.sh  # 访问 http://localhost:8502

# 6. 切回 develop 继续开发
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
git checkout develop
```

## 📋 常用命令

```bash
# 查看当前分支
git branch

# 查看版本历史
git log --oneline
git tag

# 回退到旧版本
git checkout v1.0
./deploy_to_prod.sh

# 回到最新版本
git checkout develop
```

## ⚠️ 注意事项

- **开发环境数据**：可以随意测试，位于 `data/headhunter.db`
- **生产环境数据**：重要数据，定期备份 `personal-ai-headhunter-prod/data/`
- **提交频率**：每完成一个小功能就提交，不要积累太多修改
- **分支切换**：切换分支前确保提交或暂存所有更改

## 🔗 相关文档

- [通用 Git 工作流指南](file:///Users/lillianliao/notion_rag/GIT_WORKFLOW_GUIDE.md)
- [部署指南](file:///Users/lillianliao/notion_rag/personal-ai-headhunter/DEPLOYMENT_GUIDE.md)
