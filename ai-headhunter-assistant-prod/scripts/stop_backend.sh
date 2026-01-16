#!/bin/bash

# AI Headhunter Assistant - 后台服务停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/apps/backend"
PID_FILE="$BACKEND_DIR/backend.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "ℹ️  服务未运行（未找到 PID 文件）"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "ℹ️  服务未运行（进程不存在）"
    rm -f "$PID_FILE"
    exit 0
fi

echo "🛑 正在停止服务 (PID: $PID)..."

# 尝试优雅停止
kill "$PID" 2>/dev/null

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 如果还在运行，强制停止
if ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  进程未响应，强制停止..."
    kill -9 "$PID" 2>/dev/null
    sleep 1
fi

# 清理 PID 文件
if ! ps -p "$PID" > /dev/null 2>&1; then
    rm -f "$PID_FILE"
    echo "✅ 服务已停止"
else
    echo "❌ 无法停止服务，请手动检查进程: $PID"
    exit 1
fi

