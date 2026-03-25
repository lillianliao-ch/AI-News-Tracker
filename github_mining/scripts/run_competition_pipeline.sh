#!/bin/bash
# ======================================================================
# 竞赛获奖者人才挖掘流水线
# 格式与 run_all_conferences.sh 一致，支持 --resume 断点续传
# ======================================================================
# 用法:
#   ./run_competition_pipeline.sh              # 全量采集 (Kaggle + CF + NOI + ICPC)
#   ./run_competition_pipeline.sh --codeforces # 只跑 Codeforces
#   ./run_competition_pipeline.sh --noi        # 只跑 NOI/ICPC
#   ./run_competition_pipeline.sh --kaggle     # 只跑 Kaggle (需 API Key)
#   ./run_competition_pipeline.sh --resume     # 从上次中断恢复

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$SCRIPT_DIR/.."
DATA_DIR="$BASE_DIR/data/competition"

# ── 参数解析 ──────────────────────────────────────────────────
COMPETITION="all"
RESUME_MODE=false

for arg in "$@"; do
    case "$arg" in
        --codeforces) COMPETITION="codeforces" ;;
        --noi)        COMPETITION="noi,icpc" ;;
        --kaggle)     COMPETITION="kaggle" ;;
        --icpc)       COMPETITION="icpc" ;;
        --resume)     RESUME_MODE=true ;;
    esac
done

# ── 目录 ────────────────────────────────────────────────────
mkdir -p "$DATA_DIR/runs"

if [ "$RESUME_MODE" = true ]; then
    BATCH_DIR=$(ls -dt "$DATA_DIR/runs"/competition_* 2>/dev/null | head -n 1)
    if [ -z "$BATCH_DIR" ]; then
        echo "❌ 没有找到历史批次，请新建批次"
        exit 1
    fi
    BATCH_NAME=$(basename "$BATCH_DIR")
    echo "🔄 恢复批次: $BATCH_NAME"
else
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BATCH_NAME="competition_${COMPETITION}_${TIMESTAMP}"
    BATCH_DIR="$DATA_DIR/runs/$BATCH_NAME"
    mkdir -p "$BATCH_DIR/logs"
fi

mkdir -p "$BATCH_DIR"
LOG_FILE="$BATCH_DIR/logs/run.log"
mkdir -p "$(dirname "$LOG_FILE")"

# ── 运行参数 ──────────────────────────────────────────────────
YEARS="2022,2023,2024"
MIN_RATING=2200   # Codeforces International Master 起步
MAX_USERS=500     # CF 最多 500 人
TOP_N=100         # Kaggle 每个比赛 Top 100

echo "============================================================"
echo "🚀 竞赛获奖者挖掘 | $BATCH_NAME"
echo "   采集渠道: $COMPETITION"
echo "   输出目录: $BATCH_DIR"
echo "============================================================"
echo ""
echo "📋 监控: tail -f $LOG_FILE"
echo ""

# ── 后台串行执行 ───────────────────────────────────────────────
(
    echo "[$(date '+%H:%M:%S')] 🚀 启动采集 (competition=$COMPETITION)" >> "$LOG_FILE"

    python3 "$SCRIPT_DIR/competition_miner.py" \
        --competition "$COMPETITION" \
        --year "$YEARS" \
        --min-rating $MIN_RATING \
        --max-users $MAX_USERS \
        --top-n $TOP_N \
        --output-dir "$BATCH_DIR" \
        >> "$LOG_FILE" 2>&1

    echo "[$(date '+%H:%M:%S')] ✅ 采集完成！" >> "$LOG_FILE"
    echo "[$(date '+%H:%M:%S')] 📂 输出: $BATCH_DIR" >> "$LOG_FILE"

) &

MAIN_PID=$!
echo "✅ 采集任务已在后台启动 (PID: $MAIN_PID)"
echo "   数据目录: $BATCH_DIR"
echo ""
echo "🔄 恢复命令: ./run_competition_pipeline.sh --resume"
