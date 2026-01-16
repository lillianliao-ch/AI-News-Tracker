#!/bin/bash

# AI Headhunter Assistant - 后台服务启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/apps/backend"
LOG_DIR="$BACKEND_DIR/logs"
PID_FILE="$BACKEND_DIR/backend.pid"
LOG_FILE="$LOG_DIR/backend.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查服务是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  服务已经在运行中 (PID: $PID)"
        echo "   如需重启，请先运行: ./scripts/stop_backend.sh"
        exit 1
    else
        # PID 文件存在但进程不存在，删除旧的 PID 文件
        rm -f "$PID_FILE"
    fi
fi

# 检查 .env 文件
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "⚠️  未找到 .env 文件，正在从 env.example 创建..."
    if [ -f "$BACKEND_DIR/env.example" ]; then
        cp "$BACKEND_DIR/env.example" "$BACKEND_DIR/.env"
        echo "✅ 已创建 .env 文件，请编辑并填入你的配置"
        echo "   文件位置: $BACKEND_DIR/.env"
    else
        echo "❌ 未找到 env.example 文件"
        exit 1
    fi
fi

# 进入后端目录
cd "$BACKEND_DIR" || exit 1

# 检查 Python 依赖
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 正在安装 Python 依赖..."
    pip3 install -r requirements.txt
fi

echo "🚀 启动后台服务..."
echo "   日志文件: $LOG_FILE"
echo "   PID 文件: $PID_FILE"

# 启动服务（后台运行）
nohup python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    > "$LOG_FILE" 2>&1 &

# 保存 PID
echo $! > "$PID_FILE"

# 等待一下，检查服务是否成功启动
sleep 2

if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    PID=$(cat "$PID_FILE")
    echo "✅ 服务启动成功！"
    echo "   PID: $PID"
    echo "   API 地址: http://localhost:8000"
    echo "   API 文档: http://localhost:8000/docs"
    echo "   健康检查: http://localhost:8000/health"
    echo ""
    echo "📋 管理命令："
    echo "   查看日志: tail -f $LOG_FILE"
    echo "   停止服务: ./scripts/stop_backend.sh"
    echo "   查看状态: ./scripts/status_backend.sh"
else
    echo "❌ 服务启动失败，请查看日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

