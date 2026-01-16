#!/bin/bash

echo "🚀 AI Headhunter Assistant - 环境设置"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "   请访问 https://nodejs.org/ 安装 Node.js"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 未安装"
    echo "   请访问 https://www.python.org/ 安装 Python 3.11+"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 安装 pnpm..."
    npm install -g pnpm
fi

echo "✅ pnpm 版本: $(pnpm --version)"
echo ""

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
cd backend
pip3 install -r requirements.txt
cd ..

# 设置环境变量
if [ ! -f backend/.env ]; then
    echo "⚙️  创建环境变量文件..."
    cp backend/env.example backend/.env
    echo "⚠️  请编辑 backend/.env 文件，填入你的 API Keys"
fi

echo ""
echo "✅ 设置完成！"
echo ""
echo "下一步："
echo "  1. 编辑 backend/.env 文件，填入你的 API Keys"
echo "  2. 运行 'cd backend && python3 -m uvicorn app.main:app --reload' 启动后端"
echo "  3. 在 Chrome 中加载 chrome-extension-v2/ 插件"
echo ""

