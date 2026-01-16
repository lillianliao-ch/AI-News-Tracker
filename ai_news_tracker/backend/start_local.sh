#!/bin/bash
# AI News Tracker - 本地快速启动脚本

set -e  # 遇到错误立即退出

echo "=================================================="
echo "🚀 AI News Tracker - 本地启动脚本"
echo "=================================================="

# 进入backend目录
cd "$(dirname "$0")"
BACKEND_DIR="$(pwd)"
echo "📂 工作目录: $BACKEND_DIR"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    echo "请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件"
    echo "正在从 .env.example 创建 .env..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已创建 .env 文件"
        echo ""
        echo "⚠️  请编辑 .env 文件，设置你的 API Keys:"
        echo "   - OPENAI_API_KEY"
        echo "   - OPENAI_BASE_URL"
        echo ""
        read -p "按回车键继续，或按 Ctrl+C 退出..."
    else
        echo "❌ 错误: 未找到 .env.example 文件"
        exit 1
    fi
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 未找到虚拟环境，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
    echo ""
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate
echo "✅ 虚拟环境已激活"
echo ""

# 安装/更新依赖
echo "📥 检查依赖..."
if [ ! -f "venv/.installed" ]; then
    echo "正在安装依赖（首次运行，可能需要几分钟）..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    touch venv/.installed
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖已安装"
fi
echo ""

# 运行数据库迁移（如果需要）
if [ -f "migrate_add_language.py" ]; then
    echo "🗄️  检查数据库迁移..."
    python3 migrate_add_language.py 2>/dev/null || echo "数据库已是最新版本"
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

# 启动应用
echo "=================================================="
echo "🚀 启动 AI News Tracker..."
echo "=================================================="
echo ""
echo "📍 API 地址: http://localhost:$PORT"
echo "📍 API 文档: http://localhost:$PORT/docs"
echo "📍 健康检查: http://localhost:$PORT/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=================================================="
echo ""

# 启动uvicorn
python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload
