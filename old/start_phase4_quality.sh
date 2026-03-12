#!/bin/bash
#
# Phase 4 高质量人群扩展启动脚本
# 种子: S, A+, A 层级 (1,466 人)
# 共现阈值: 2 次
#

set -e

# 设置正确的数据库路径
export DB_PATH="/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db"

SCRIPT_DIR="/Users/lillianliao/notion_rag/github_mining/scripts"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🚀 Phase 4 高质量人群扩展"
echo "============================================================"
echo "种子: S, A+, A 层级 (1,466 人)"
echo "共现阈值: 2 次"
echo "数据库: $DB_PATH"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# 后台运行
nohup bash run_phase4_full_pipeline.sh \
  > /tmp/phase4_quality_expansion.log 2>&1 &

PID=$!
echo "✅ 流程已启动 (PID: $PID)"
echo ""
echo "📄 日志文件: /tmp/phase4_quality_expansion.log"
echo "📊 批报告: github_mining/scripts/github_mining/batch_report_*.json"
echo ""
echo "查看实时日志:"
echo "  tail -f /tmp/phase4_quality_expansion.log"
echo ""
echo "停止流程:"
echo "  pkill -f run_phase4_full_pipeline"
echo ""
