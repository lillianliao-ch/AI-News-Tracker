#!/bin/bash
# AI News Tracker - 前端启动脚本

set -e

echo "=================================================="
echo "🚀 AI News Tracker - 前端启动脚本"
echo "=================================================="

# 进入frontend目录
cd "$(dirname "$0")"
FRONTEND_DIR="$(pwd)"
echo "📂 工作目录: $FRONTEND_DIR"
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo "请先安装 Node.js 18+"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js 版本: $NODE_VERSION"
echo ""

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm"
    exit 1
fi

echo "✅ npm 版本: $(npm --version)"
echo ""

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 未找到 node_modules，正在安装依赖..."
    npm install
    echo "✅ 依赖安装完成"
    echo ""
fi

# 检查端口占用
PORT=4321
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 $PORT 已被占用"
    echo "正在尝试关闭现有进程..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 1
    echo "✅ 端口已释放"
    echo ""
fi

# 启动前端
echo "=================================================="
echo "🚀 启动 Astro 开发服务器..."
echo "=================================================="
echo ""
echo "📍 前端地址: http://localhost:$PORT"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=================================================="
echo ""

# 启动Astro
npm run dev
