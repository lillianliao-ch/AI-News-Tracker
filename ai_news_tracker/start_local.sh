#!/bin/bash

# ========================================================
# AI News Tracker - 本地启动脚本
# ========================================================

# 获取项目根目录绝对路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 退出清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    # 杀掉当前脚本启动的所有子进程
    pkill -P $$
    exit
}
# 捕获 Ctrl+C 和终止信号
trap cleanup SIGINT SIGTERM

echo "🚀 正在启动 AI News Tracker (本地开发模式)..."

# ==================== 1. 启动后端 ====================
echo "📦 正在启动后端服务 (Port 8002)..."

cd "$PROJECT_ROOT/backend" || exit

# 设置环境变量
export PORT=8002
# 使用绝对路径确保数据库文件位置正确
export DATABASE_URL="sqlite:///$PROJECT_ROOT/backend/data/ai_news.db"
# 加载 .env 文件中的其他配置 (如果存在)
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    VENV_BIN="venv/bin"
elif [ -d ".venv" ]; then
    VENV_BIN=".venv/bin"
elif [ -d "../.venv" ]; then
    VENV_BIN="../.venv/bin"
else
    echo "❌ 未找到 Python 虚拟环境 (venv/.venv)"
    echo "请先运行: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 启动 FastAPI (使用 --reload 进行热重载)
"$VENV_BIN/uvicorn" main:app --host 0.0.0.0 --port 8002 --reload &
BACKEND_PID=$!

echo "✅ 后端已在后台启动 (PID: $BACKEND_PID)"
sleep 3 # 等待后端初始化

# ==================== 2. 启动前端 ====================
echo "🎨 正在启动前端服务 (Port 4321)..."

cd "$PROJECT_ROOT/frontend" || exit

# 设置前端环境变量
export PORT=4321
export PUBLIC_API_URL="http://localhost:8002"

# 启动 Astro
npm run dev &
FRONTEND_PID=$!

# ==================== 3. 完成 ====================
echo ""
echo "🎉 服务启动成功!"
echo "--------------------------------------------------"
echo "🌍 前端访问: http://localhost:4321"
echo "🔌 后端文档: http://localhost:8002/docs"
echo "--------------------------------------------------"
echo "按 Ctrl+C 停止所有服务"

# 等待子进程（保持脚本运行）
wait
