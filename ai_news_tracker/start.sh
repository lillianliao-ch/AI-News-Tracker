#!/bin/bash
# AI News Tracker - 完整启动脚本（前端+后端）

set -e

echo "=================================================="
echo "🚀 AI News Tracker - 完整启动"
echo "=================================================="
echo ""

PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 检查目录
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ 错误: 未找到 backend 目录"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 错误: 未找到 frontend 目录"
    exit 1
fi

echo "✅ 项目结构检查通过"
echo ""

# 启动后端
echo "=================================================="
echo "1️⃣  启动后端 API (端口 8000)..."
echo "=================================================="
cd "$BACKEND_DIR"

# 检查后端虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建后端虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# 运行数据库迁移
python3 migrate_add_language.py 2>/dev/null || true

# 后台启动后端
echo "🔄 后台启动后端API..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/ai-news-tracker-backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端已启动 (PID: $BACKEND_PID)"
echo ""

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 3

# 检查后端健康状态
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端API就绪: http://localhost:8000"
else
    echo "❌ 后端启动失败，请检查日志: /tmp/ai-news-tracker-backend.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo ""

# 启动前端
echo "=================================================="
echo "2️⃣  启动前端界面 (端口 4321)..."
echo "=================================================="
cd "$FRONTEND_DIR"

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 检查端口
if lsof -Pi :4321 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 4321 已被占用，正在关闭..."
    lsof -ti:4321 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 启动前端
echo "🔄 启动前端..."
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端已启动 (PID: $FRONTEND_PID)"
echo ""

# 等待前端启动
echo "⏳ 等待前端启动..."
sleep 5

# 总结
echo "=================================================="
echo "✅ AI News Tracker 已完全启动！"
echo "=================================================="
echo ""
echo "📍 前端界面: http://localhost:4321"
echo "📍 后端API: http://localhost:8000"
echo "📍 API文档: http://localhost:8000/docs"
echo ""
echo "📝 进程信息:"
echo "   - 后端 PID: $BACKEND_PID"
echo "   - 前端 PID: $FRONTEND_PID"
echo ""
echo "🛑 停止服务:"
echo "   按 Ctrl+C 或运行: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=================================================="
echo ""

# 保存PID到文件
echo $BACKEND_PID > /tmp/ai-news-tracker-backend.pid
echo $FRONTEND_PID > /tmp/ai-news-tracker-frontend.pid

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f /tmp/ai-news-tracker-*.pid; echo '✅ 所有服务已停止'; exit 0" INT TERM

# 保持脚本运行
wait
