#!/bin/bash
# ======================================================================
# 快速小样本测试：全量学术会议抓取流水线 (Batch Isolation Version)
# ======================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$SCRIPT_DIR/.."
DATA_DIR="$BASE_DIR/data/academic"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BATCH_NAME="conference_test_$TIMESTAMP"
BATCH_DIR="$DATA_DIR/runs/$BATCH_NAME"

mkdir -p "$BATCH_DIR/logs"
mkdir -p "$BATCH_DIR/outputs"

echo "============================================================"
echo "🧪 启动小样本测试抓取 (Batch: $BATCH_NAME, max-papers=2)"
echo "📂 数据保存路径: $BATCH_DIR/outputs"
echo "============================================================"

CONFS="iclr,acl,neurips,icml,cvpr"
MAX_PAPERS=2

echo "[1/3] 测试抓取 2024 年..."
nohup python3 "$SCRIPT_DIR/academic_miner.py" \
    --conference "$CONFS" \
    --year 2024 \
    --max-papers $MAX_PAPERS \
    --output-prefix "test_conf_2024" \
    --output-dir "$BATCH_DIR/outputs" \
    > "$BATCH_DIR/logs/run_2024.log" 2>&1 &
PID_2024=$!
echo "  -> PID: $PID_2024"

echo "[2/3] 测试抓取 2023 年..."
nohup python3 "$SCRIPT_DIR/academic_miner.py" \
    --conference "$CONFS" \
    --year 2023 \
    --max-papers $MAX_PAPERS \
    --output-prefix "test_conf_2023" \
    --output-dir "$BATCH_DIR/outputs" \
    > "$BATCH_DIR/logs/run_2023.log" 2>&1 &
PID_2023=$!
echo "  -> PID: $PID_2023"

echo "[3/3] 测试抓取 2022 年..."
nohup python3 "$SCRIPT_DIR/academic_miner.py" \
    --conference "$CONFS" \
    --year 2022 \
    --max-papers $MAX_PAPERS \
    --output-prefix "test_conf_2022" \
    --output-dir "$BATCH_DIR/outputs" \
    > "$BATCH_DIR/logs/run_2022.log" 2>&1 &
PID_2022=$!
echo "  -> PID: $PID_2022"

echo "============================================================"
echo "✅ 测试任务已经全部分发到后台！"
echo "监控最慢的一条日志: tail -f $BATCH_DIR/logs/run_2024.log"
echo "============================================================"
