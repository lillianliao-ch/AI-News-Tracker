#!/bin/bash
# AI News Tracker - 稳定启动脚本（含健康检查和自动重启）

set -u
set -o pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
RUNTIME_DIR="$PROJECT_ROOT/.runtime"
PID_DIR="$RUNTIME_DIR/pids"
LOG_DIR="$RUNTIME_DIR/logs"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-4321}"
CHECK_INTERVAL="${CHECK_INTERVAL:-15}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
MONITOR_PID_FILE="$PID_DIR/monitor.pid"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
MONITOR_LOG="$LOG_DIR/monitor.log"

mkdir -p "$PID_DIR" "$LOG_DIR"

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

read_pid() {
  local pid_file="$1"
  if [ -f "$pid_file" ]; then
    cat "$pid_file"
  fi
}

stop_by_pid_file() {
  local name="$1"
  local pid_file="$2"
  local pid
  pid="$(read_pid "$pid_file")"

  if [ -z "${pid:-}" ]; then
    return 0
  fi

  if is_pid_running "$pid"; then
    log "停止 $name (PID: $pid)"
    kill "$pid" 2>/dev/null || true
    sleep 1
    if is_pid_running "$pid"; then
      log "$name 未在预期时间退出，执行强制停止 (PID: $pid)"
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi

  rm -f "$pid_file"
}

kill_process_on_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti :"$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    log "端口 $port 已被占用，清理占用进程: $pids"
    kill $pids 2>/dev/null || true
    sleep 1
    pids="$(lsof -ti :"$port" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

wait_http_ok() {
  local url="$1"
  local timeout="$2"
  local elapsed=0

  while [ "$elapsed" -lt "$timeout" ]; do
    local code
    code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
    if [ "$code" -ge 200 ] && [ "$code" -lt 400 ]; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  return 1
}

prepare_backend() {
  cd "$BACKEND_DIR" || return 1

  if [ ! -d "venv" ]; then
    log "创建后端虚拟环境"
    python3 -m venv venv || return 1
  fi

  # shellcheck disable=SC1091
  source venv/bin/activate || return 1

  if [ ! -f "venv/.installed" ]; then
    log "安装后端依赖"
    pip install -q --upgrade pip || return 1
    pip install -q -r requirements.txt || return 1
    touch venv/.installed
  fi

  if [ -f "migrate_add_language.py" ]; then
    python3 migrate_add_language.py >/dev/null 2>&1 || true
  fi
}

prepare_frontend() {
  cd "$FRONTEND_DIR" || return 1

  if [ ! -d "node_modules" ]; then
    log "安装前端依赖"
    npm install || return 1
  fi
}

start_backend() {
  log "启动后端服务 (:$BACKEND_PORT)"
  prepare_backend || return 1

  kill_process_on_port "$BACKEND_PORT"
  : >"$BACKEND_LOG"

  # shellcheck disable=SC1091
  source "$BACKEND_DIR/venv/bin/activate"
  nohup python3 -m uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" >>"$BACKEND_LOG" 2>&1 &
  local pid=$!
  echo "$pid" >"$BACKEND_PID_FILE"

  if wait_http_ok "http://127.0.0.1:${BACKEND_PORT}/health" "$HEALTH_TIMEOUT"; then
    log "后端健康检查通过 (PID: $pid)"
    return 0
  fi

  log "后端健康检查失败，查看日志: $BACKEND_LOG"
  stop_by_pid_file "后端服务" "$BACKEND_PID_FILE"
  return 1
}

start_frontend() {
  log "启动前端服务 (:$FRONTEND_PORT)"
  prepare_frontend || return 1

  kill_process_on_port "$FRONTEND_PORT"
  : >"$FRONTEND_LOG"

  cd "$FRONTEND_DIR" || return 1
  nohup npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" >>"$FRONTEND_LOG" 2>&1 &
  local pid=$!
  echo "$pid" >"$FRONTEND_PID_FILE"

  if wait_http_ok "http://127.0.0.1:${FRONTEND_PORT}" "$HEALTH_TIMEOUT"; then
    log "前端健康检查通过 (PID: $pid)"
    return 0
  fi

  log "前端健康检查失败，尝试修复 esbuild 依赖后重试"
  stop_by_pid_file "前端服务" "$FRONTEND_PID_FILE"

  cd "$FRONTEND_DIR" || return 1
  rm -rf node_modules
  npm install >>"$FRONTEND_LOG" 2>&1 || return 1

  nohup npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" >>"$FRONTEND_LOG" 2>&1 &
  pid=$!
  echo "$pid" >"$FRONTEND_PID_FILE"

  if wait_http_ok "http://127.0.0.1:${FRONTEND_PORT}" "$HEALTH_TIMEOUT"; then
    log "前端重试后健康检查通过 (PID: $pid)"
    return 0
  fi

  log "前端健康检查失败，查看日志: $FRONTEND_LOG"
  stop_by_pid_file "前端服务" "$FRONTEND_PID_FILE"
  return 1
}

restart_backend() {
  log "后端状态异常，执行自动重启"
  stop_by_pid_file "后端服务" "$BACKEND_PID_FILE"
  start_backend >>"$MONITOR_LOG" 2>&1 || log "后端自动重启失败，请检查 $BACKEND_LOG"
}

restart_frontend() {
  log "前端状态异常，执行自动重启"
  stop_by_pid_file "前端服务" "$FRONTEND_PID_FILE"
  start_frontend >>"$MONITOR_LOG" 2>&1 || log "前端自动重启失败，请检查 $FRONTEND_LOG"
}

monitor_loop() {
  log "守护进程已启动，检查间隔: ${CHECK_INTERVAL}s"
  while true; do
    sleep "$CHECK_INTERVAL"

    local backend_pid frontend_pid
    backend_pid="$(read_pid "$BACKEND_PID_FILE")"
    frontend_pid="$(read_pid "$FRONTEND_PID_FILE")"

    if ! is_pid_running "${backend_pid:-}"; then
      restart_backend
    else
      local backend_code
      backend_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${BACKEND_PORT}/health" || true)"
      if [ "$backend_code" -lt 200 ] || [ "$backend_code" -ge 400 ]; then
        restart_backend
      fi
    fi

    if ! is_pid_running "${frontend_pid:-}"; then
      restart_frontend
    else
      local frontend_code
      frontend_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${FRONTEND_PORT}" || true)"
      if [ "$frontend_code" -lt 200 ] || [ "$frontend_code" -ge 400 ]; then
        restart_frontend
      fi
    fi
  done
}

if [ -f "$MONITOR_PID_FILE" ]; then
  old_monitor_pid="$(cat "$MONITOR_PID_FILE")"
  if is_pid_running "$old_monitor_pid"; then
    log "检测到已有守护实例运行中 (PID: $old_monitor_pid)"
    log "如需重启，请先执行: ./stable_stop.sh"
    exit 1
  fi
  rm -f "$MONITOR_PID_FILE"
fi

log "=================================================="
log "AI News Tracker 稳定启动"
log "=================================================="

start_backend || exit 1
start_frontend || exit 1

(
  monitor_loop
) >>"$MONITOR_LOG" 2>&1 &
MONITOR_PID=$!
echo "$MONITOR_PID" >"$MONITOR_PID_FILE"

log "启动成功"
log "前端: http://localhost:${FRONTEND_PORT}"
log "后端: http://localhost:${BACKEND_PORT}"
log "API文档: http://localhost:${BACKEND_PORT}/docs"
log "守护进程 PID: $MONITOR_PID"
log "日志目录: $LOG_DIR"
log "停止命令: ./stable_stop.sh"
