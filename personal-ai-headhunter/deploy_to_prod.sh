#!/bin/bash

echo "📦 Deploying to Production Environment..."
echo "=================================================="

# 确保在项目根目录
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a Git repository"
    exit 1
fi

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: You are on branch '$CURRENT_BRANCH', not 'main'"
    echo "Recommended: Deploy from 'main' branch for production"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes"
    git status --short
    read -p "Continue deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 部署到生产环境
echo "📋 Copying files to production..."
rsync -av --exclude='.git' --exclude='data/' --exclude='__pycache__' \
    /Users/lillianliao/notion_rag/personal-ai-headhunter/ \
    /Users/lillianliao/notion_rag/personal-ai-headhunter-prod/

echo ""
echo "✅ Deployment complete!"
echo "=================================================="
echo "Production environment updated at:"
echo "/Users/lillianliao/notion_rag/personal-ai-headhunter-prod/"
echo ""
echo "To start production:"
echo "  cd /Users/lillianliao/notion_rag/personal-ai-headhunter-prod"
echo "  ./start.sh"
