#!/bin/bash

# AI Headhunter Assistant - 后台服务状态检查脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/apps/backend"
PID_FILE="$BACKEND_DIR/backend.pid"
LOG_FILE="$BACKEND_DIR/logs/backend.log"

echo "📊 AI Headhunter Assistant 服务状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查 PID 文件
if [ ! -f "$PID_FILE" ]; then
    echo "❌ 服务未运行（未找到 PID 文件）"
    echo ""
    echo "启动服务: ./scripts/start_backend.sh"
    exit 0
fi

PID=$(cat "$PID_FILE")

# 检查进程
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "❌ 服务未运行（进程不存在）"
    echo "   PID 文件存在但进程已结束，清理 PID 文件..."
    rm -f "$PID_FILE"
    echo ""
    echo "启动服务: ./scripts/start_backend.sh"
    exit 0
fi

# 获取进程信息
PROCESS_INFO=$(ps -p "$PID" -o pid,etime,command --no-headers 2>/dev/null)
RUNTIME=$(echo "$PROCESS_INFO" | awk '{print $2}')

echo "✅ 服务正在运行"
echo "   PID: $PID"
echo "   运行时间: $RUNTIME"
echo ""

# 检查 API 是否可访问
echo "🔍 检查 API 健康状态..."
if command -v curl &> /dev/null; then
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        echo "✅ API 健康检查通过 (http://localhost:8000/health)"
    else
        echo "⚠️  API 健康检查失败 (HTTP $HEALTH_RESPONSE)"
    fi
else
    echo "ℹ️  未安装 curl，跳过 API 检查"
fi

echo ""
echo "📋 服务信息："
echo "   API 地址: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo "   日志文件: $LOG_FILE"
echo ""
echo "📋 管理命令："
echo "   查看日志: tail -f $LOG_FILE"
echo "   停止服务: ./scripts/stop_backend.sh"
echo "   重启服务: ./scripts/stop_backend.sh && ./scripts/start_backend.sh"

