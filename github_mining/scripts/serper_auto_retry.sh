#!/bin/bash
# Serper 自动重试脚本 — 检测退出码 → 切换 Key → 重启
#
# 用法:
#   ./scripts/serper_auto_retry.sh \
#     --input <full.json> \
#     --cache <cache.json> \
#     --output <output_dir> \
#     --tiers "C" \
#     --log <log_file>
#
# 功能:
#   1. 按顺序尝试所有可用 Key
#   2. 脚本退出后自动切换下一个 Key 重启
#   3. 缓存自动跳过已完成的（断点续传）
#   4. 所有 Key 用完或任务完成 → 停止

set -euo pipefail

# ===== Serper API Keys Pool =====
KEYS=(
  "633165fa15b2f68d512ccee4a7c5128eea03da68"
  "8cf7569e266a49026e8bc401e40286b5019bdc27"
  "291e00a3bda2a2266a54f28a0e4fbc30b422fff9"
  "07710687e4a725a1d5334e1fd0c85dec1dc7e73d"
  "71f44084beb2971b691ceba38f5935b5190971d9"
  "47f22063c60923cafbf7b634e42fdb9ae339130c"
  "ac3140b8332761219fd8d1788ad0535ecd7d34f6"
  "e915d3a6aaca5c7892b77235bae616525d99892f"
  "73b4e0a39126533a602c3bdae2e2b4e7e8415871"
  "dc03c4fc92e7f788c667fce356f0b457e36ed6c9"
)

# ===== 参数解析 =====
INPUT=""
CACHE=""
OUTPUT=""
TIERS=""
LOG=""
START_KEY=0  # 从第几个 Key 开始 (0-indexed)

while [[ $# -gt 0 ]]; do
  case $1 in
    --input) INPUT="$2"; shift 2 ;;
    --cache) CACHE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --tiers) TIERS="$2"; shift 2 ;;
    --log) LOG="$2"; shift 2 ;;
    --start-key) START_KEY="$2"; shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

if [[ -z "$INPUT" || -z "$CACHE" || -z "$OUTPUT" || -z "$TIERS" ]]; then
  echo "❌ 缺少必要参数"
  echo "用法: $0 --input <file> --cache <file> --output <dir> --tiers <tiers> [--log <file>] [--start-key <n>]"
  exit 1
fi

# 默认 log 文件
if [[ -z "$LOG" ]]; then
  LOG="${OUTPUT}/serper_auto_retry_$(date +%Y%m%d_%H%M%S).log"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENRICHER="${SCRIPT_DIR}/academic_contact_enricher.py"

echo "============================================================" | tee -a "$LOG"
echo "🔄 Serper 自动重试启动" | tee -a "$LOG"
echo "   输入: $INPUT" | tee -a "$LOG"
echo "   缓存: $CACHE" | tee -a "$LOG"
echo "   输出: $OUTPUT" | tee -a "$LOG"
echo "   Tiers: $TIERS" | tee -a "$LOG"
echo "   可用 Keys: ${#KEYS[@]}, 从第 $START_KEY 个开始" | tee -a "$LOG"
echo "   日志: $LOG" | tee -a "$LOG"
echo "============================================================" | tee -a "$LOG"

EXHAUSTED_KEYS=()

for i in $(seq $START_KEY $((${#KEYS[@]} - 1))); do
  KEY="${KEYS[$i]}"
  KEY_SHORT="${KEY:0:8}..."
  
  echo "" | tee -a "$LOG"
  echo "[$(date '+%H:%M:%S')] 🔑 尝试 Key #$((i+1)): $KEY_SHORT" | tee -a "$LOG"
  
  # 运行 enricher
  set +e
  SERPER_API_KEY="$KEY" python3 "$ENRICHER" \
    --input "$INPUT" \
    --output "$OUTPUT" \
    --cache "$CACHE" \
    --serper-only \
    --serper-tiers "$TIERS" \
    >> "$LOG" 2>&1
  EXIT_CODE=$?
  set -e
  
  echo "[$(date '+%H:%M:%S')] Key #$((i+1)) 退出码: $EXIT_CODE" | tee -a "$LOG"
  
  if [[ $EXIT_CODE -eq 0 ]]; then
    echo "[$(date '+%H:%M:%S')] ✅ 任务完成！" | tee -a "$LOG"
    echo "" | tee -a "$LOG"
    echo "📊 已用 Keys: $((i - START_KEY + 1))/${#KEYS[@]}" | tee -a "$LOG"
    echo "   耗尽的 Keys: ${EXHAUSTED_KEYS[*]:-无}" | tee -a "$LOG"
    exit 0
  fi
  
  # 记录耗尽的 key
  EXHAUSTED_KEYS+=("$KEY_SHORT")
  
  echo "[$(date '+%H:%M:%S')] ⚠️  Key #$((i+1)) 退出 (code=$EXIT_CODE), 切换下一个..." | tee -a "$LOG"
  
  # 短暂等待避免 API 速率限制
  sleep 3
done

echo "" | tee -a "$LOG"
echo "[$(date '+%H:%M:%S')] ❌ 所有 Keys 已用完！" | tee -a "$LOG"
echo "   耗尽: ${EXHAUSTED_KEYS[*]}" | tee -a "$LOG"
echo "   缓存已保存，添加新 Key 后可继续" | tee -a "$LOG"
exit 1
