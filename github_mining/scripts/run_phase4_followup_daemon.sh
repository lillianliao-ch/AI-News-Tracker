#!/bin/bash
#
# 无人值守运行脚本 - Phase 4 后续补强
# 使用方法: bash run_phase4_followup_daemon.sh
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/github_mining/phase4_followup_daemon.log"

echo "=========================================="
echo "🚀 启动无人值守 Phase 4 后续补强"
echo "=========================================="
echo ""
echo "📝 日志文件: $LOG_FILE"
echo ""
echo "✅ 后台运行中..."
echo ""
echo "📊 查看实时日志:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🛑 停止运行:"
echo "   pkill -f run_phase4_enrichment.py"
echo ""

# 后台运行，输出到日志
nohup python3 "$SCRIPT_DIR/auto_restart_wrapper.py" -- python3 "$SCRIPT_DIR/run_phase4_enrichment.py" > "$LOG_FILE" 2>&1 &

echo "✅ 进程已启动，PID: $!"
echo ""