#!/bin/bash

# ========================================
# 部署到生产环境脚本
# ========================================

echo "🚀 开始部署到生产环境..."
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 1. 确保在 main 分支
echo "📍 步骤 1/6: 切换到 main 分支"
git checkout main
if [ $? -ne 0 ]; then
    echo "❌ 错误: 切换到 main 分支失败"
    exit 1
fi
echo "✅ 已切换到 main 分支"
echo ""

# 2. 合并 develop 分支
echo "📍 步骤 2/6: 合并 develop 分支"
git merge develop
if [ $? -ne 0 ]; then
    echo "❌ 错误: 合并失败，请手动解决冲突"
    exit 1
fi
echo "✅ develop 分支已合并到 main"
echo ""

# 3. 询问是否打标签
echo "📍 步骤 3/6: 版本标签"
read -p "是否打版本标签？(y/n): " create_tag
if [ "$create_tag" = "y" ] || [ "$create_tag" = "Y" ]; then
    read -p "请输入版本号（如 v1.1）: " version
    if [ ! -z "$version" ]; then
        git tag -a "$version" -m "版本 $version"
        echo "✅ 已创建标签: $version"
    fi
else
    echo "⏭️  跳过打标签"
fi
echo ""

# 4. 推送到 GitHub
echo "📍 步骤 4/6: 推送到 GitHub"
git push origin main --tags
if [ $? -ne 0 ]; then
    echo "⚠️  警告: 推送到 GitHub 失败（可能是网络问题）"
else
    echo "✅ 已推送到 GitHub"
fi
echo ""

# 5. 同步到生产环境
echo "📍 步骤 5/6: 同步代码到生产环境"
rsync -av --delete \
  --exclude='.git' \
  --exclude='data/' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='backend.pid' \
  --exclude='*.log' \
  --exclude='.DS_Store' \
  ./ ../ai-headhunter-assistant-prod/

if [ $? -ne 0 ]; then
    echo "❌ 错误: 同步到生产环境失败"
    exit 1
fi
echo "✅ 代码已同步到生产环境"
echo ""

# 6. 切回 develop 分支
echo "📍 步骤 6/6: 切回 develop 分支"
git checkout develop
echo "✅ 已切回 develop 分支"
echo ""

echo "🎉 部署完成！"
echo ""
echo "💡 下一步操作："
echo "   1. 在 GitHub 上将默认分支改为 main"
echo "   2. 重启生产环境："
echo "      cd ../ai-headhunter-assistant-prod/backend"
echo "      ./start_prod.sh"
echo ""
