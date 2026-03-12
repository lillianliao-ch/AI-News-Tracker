#!/bin/bash
# ======================================================================
# 全量学术会议抓取流水线 (Batch Isolation Version v2)
# ======================================================================
# v2 改进：串行执行避免限流灾难、支持 --resume 断点续传、自动备份守护
# 用法:
#   ./run_all_conferences.sh              # 新建一个全新批次
#   ./run_all_conferences.sh --resume     # 自动恢复最新一次未完成的批次
#   ./run_all_conferences.sh --resume /path/to/batch_dir  # 恢复指定批次

set -e

# 获取当前脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$SCRIPT_DIR/.."
DATA_DIR="$BASE_DIR/data/academic"

# ======================================================================
# 解析参数：支持 --resume
# ======================================================================
RESUME_MODE=false
RESUME_DIR=""

if [ "$1" = "--resume" ]; then
    RESUME_MODE=true
    if [ -n "$2" ] && [ -d "$2" ]; then
        RESUME_DIR="$2"
    else
        # 自动找到最新的批次目录
        RESUME_DIR=$(ls -dt "$DATA_DIR/runs"/conference_full_* 2>/dev/null | head -n 1)
        if [ -z "$RESUME_DIR" ]; then
            echo "❌ 没有找到可以恢复的历史批次目录！请新建批次。"
            exit 1
        fi
    fi
fi

# ======================================================================
# 确定批次目录
# ======================================================================
if [ "$RESUME_MODE" = true ]; then
    BATCH_DIR="$RESUME_DIR"
    BATCH_NAME=$(basename "$BATCH_DIR")
    echo "============================================================"
    echo "🔄 恢复已有批次 (Batch: $BATCH_NAME)"
    echo "📂 数据目录: $BATCH_DIR"
    echo "   底层脚本将自动检测 _s2_cache.json 和 _contact_cache.json，"
    echo "   跳过所有已完成的 API 查询，直接从断点继续！"
    echo "============================================================"
else
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BATCH_NAME="conference_full_$TIMESTAMP"
    BATCH_DIR="$DATA_DIR/runs/$BATCH_NAME"

    mkdir -p "$BATCH_DIR/logs"
    mkdir -p "$BATCH_DIR/outputs"

    # 生成批次 Summary
    SUMMARY_FILE="$BATCH_DIR/SUMMARY.md"
    cat <<EOF > "$SUMMARY_FILE"
# 顶会人才全量挖掘批次记录
- **批次编号**: $BATCH_NAME
- **启动时间**: $(date +"%Y-%m-%d %H:%M:%S")
- **安全隔离目录**: $BATCH_DIR

## 运行特性
1. **无人值守**: 采用 \`nohup\` 后台挂机运行，关闭终端不影响拉取。
2. **串行执行**: 年份按 2024→2023→2022 依次执行，避免多进程抢占限流配额。
3. **断点续传**:
   - 依赖底层 \`_s2_cache.json\` 和 \`_contact_cache.json\`。
   - 重启命令: \`./run_all_conferences.sh --resume\`
4. **数据备份隔离**: 带时间戳目录，历史数据绝对安全。
5. **自动备份守护**: 每 15 分钟自动创建快照，最多保留 20 份。

## 实时监控
\`tail -f $BATCH_DIR/logs/run_serial.log\`
EOF

    echo "============================================================"
    echo "🚀 启动全量顶会抓取 (Batch: $BATCH_NAME)"
    echo "📂 数据与 Summary 保存路径: $BATCH_DIR"
    echo "============================================================"
fi

# 确保目录存在（恢复模式下也确保）
mkdir -p "$BATCH_DIR/logs"
mkdir -p "$BATCH_DIR/outputs"

# ======================================================================
# 自动启动备份守护进程
# ======================================================================
echo "🛡️ 自动启动缓存备份守护进程..."
nohup python3 "$SCRIPT_DIR/backup_cache.py" \
    --watch-dir "$BATCH_DIR/outputs" \
    --interval 15 \
    --max-snapshots 20 \
    > "$BATCH_DIR/logs/backup_service.log" 2>&1 &
BACKUP_PID=$!
echo "  -> 备份守护 PID: $BACKUP_PID"

# ======================================================================
# 串行执行：2024 → 2023 → 2022（避免限流灾难）
# ======================================================================
CONFS="iclr,acl,neurips,icml,cvpr"
YEARS="2025 2024"
LOG_FILE="$BATCH_DIR/logs/run_serial.log"

# 使用后台串行执行
(
    echo "[$(date '+%H:%M:%S')] 🚀 开始串行执行全量采集" >> "$LOG_FILE"

    for YEAR in $YEARS; do
        echo "============================================================" >> "$LOG_FILE"
        echo "[$(date '+%H:%M:%S')] 📅 开始采集 ${YEAR} 年数据..." >> "$LOG_FILE"
        echo "============================================================" >> "$LOG_FILE"

        python3 "$SCRIPT_DIR/academic_miner.py" \
            --conference "$CONFS" \
            --year "$YEAR" \
            --output-prefix "all_conf_${YEAR}" \
            --output-dir "$BATCH_DIR/outputs" \
            >> "$LOG_FILE" 2>&1

        echo "[$(date '+%H:%M:%S')] ✅ ${YEAR} 年采集完成！" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
    done

    echo "[$(date '+%H:%M:%S')] 🎉 全部 3 个年份采集完成！" >> "$LOG_FILE"

    # 采集完成后，杀掉备份守护进程
    kill $BACKUP_PID 2>/dev/null || true
    echo "[$(date '+%H:%M:%S')] 🛡️ 备份守护进程已停止" >> "$LOG_FILE"
) &

MAIN_PID=$!
echo ""
echo "============================================================"
echo "✅ 串行采集任务已在后台启动！"
echo "   主进程 PID: $MAIN_PID"
echo "   备份守护 PID: $BACKUP_PID"
echo ""
echo "📋 监控进度:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🔄 如果中断后需要恢复:"
echo "   ./run_all_conferences.sh --resume"
echo "============================================================"
