#!/bin/bash
# Phase 4 Round 2 - 自动重启监控脚本
# 如果进程崩溃，自动从进度恢复并重启

cd /Users/lillianliao/notion_rag/github_mining

LOG_FILE="phase4_round2_autorestart.log"
MAX_RETRIES=10
RETRY_COUNT=0
RESTART_DELAY=60  # 崩溃后等待60秒再重启

echo "==========================================" | tee -a "$LOG_FILE"
echo "🛡️  自动重启监控已启动" | tee -a "$LOG_FILE"
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "" | tee -a "$LOG_FILE"
    echo "🚀 启动 Phase 4 Round 2 (尝试 #$((RETRY_COUNT + 1))/$MAX_RETRIES)..." | tee -a "$LOG_FILE"
    echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"

    # 运行主脚本
    bash run_phase4_round2.sh 2>&1 | tee -a phase4_round2_full.log

    EXIT_CODE=${PIPESTATUS[0]}

    if [ $EXIT_CODE -eq 0 ]; then
        echo "" | tee -a "$LOG_FILE"
        echo "✅ 脚本正常完成！" | tee -a "$LOG_FILE"
        echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
        exit 0
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))

    echo "" | tee -a "$LOG_FILE"
    echo "❌ 脚本异常退出 (退出码: $EXIT_CODE)" | tee -a "$LOG_FILE"
    echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"

    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        # 检查进度文件
        if [ -f "scripts/github_mining/phase5_progress.json" ]; then
            echo "" | tee -a "$LOG_FILE"
            echo "📊 当前进度:" | tee -a "$LOG_FILE"
            cat scripts/github_mining/phase5_progress.json | tee -a "$LOG_FILE"
        fi

        echo "" | tee -a "$LOG_FILE"
        echo "⏳ ${RESTART_DELAY}秒后自动重启 (剩余重试: $((MAX_RETRIES - RETRY_COUNT)))..." | tee -a "$LOG_FILE"
        echo "==========================================" | tee -a "$LOG_FILE"

        sleep $RESTART_DELAY
    fi
done

echo "" | tee -a "$LOG_FILE"
echo "❌ 达到最大重试次数 ($MAX_RETRIES)，停止自动重启" | tee -a "$LOG_FILE"
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

exit 1
