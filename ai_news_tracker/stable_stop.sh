#!/bin/bash
# AI News Tracker - 稳定服务停止脚本

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_ROOT/.runtime/pids"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
MONITOR_PID_FILE="$PID_DIR/monitor.pid"

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

log() {
  echo "[$(timestamp)] $*"
}

is_pid_running() {
  local pid="$1"
  [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null
}

stop_by_pid_file() {
  local name="$1"
  local pid_file="$2"

  if [ ! -f "$pid_file" ]; then
    log "$name 未运行（PID 文件不存在）"
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"

  if is_pid_running "$pid"; then
    log "停止 $name (PID: $pid)"
    kill "$pid" 2>/dev/null || true
    sleep 1
    if is_pid_running "$pid"; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  else
    log "$name 进程已不存在 (PID: $pid)"
  fi

  rm -f "$pid_file"
}

log "停止 AI News Tracker 稳定服务"
stop_by_pid_file "守护进程" "$MONITOR_PID_FILE"
stop_by_pid_file "前端服务" "$FRONTEND_PID_FILE"
stop_by_pid_file "后端服务" "$BACKEND_PID_FILE"
log "停止完成"
