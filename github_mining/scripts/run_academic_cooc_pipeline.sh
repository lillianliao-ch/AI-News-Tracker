#!/usr/bin/env bash
# ===========================================================
# Academic-GitHub 共现挖掘 端到端无人值守流水线 v2
#
# 架构说明:
#   Step 1 (唯一独有): academic 共现分析，产出原始 JSON
#   Step 2+ (标准化): 调用 batch_runner.py 完成过滤/富化/入库
#
# 用法:
#   # 正常启动（后台无人值守）
#   nohup bash run_academic_cooc_pipeline.sh > academic_cooc_pipeline_$(date +%Y%m%d).log 2>&1 &
#
#   # 跳过共现分析，直接用已有共现结果跑入库
#   SKIP_COOC=true bash run_academic_cooc_pipeline.sh
#
#   # 使用已有共现文件（直接从 batch_runner 开始）
#   COOC_INPUT=/path/to/existing.json bash run_academic_cooc_pipeline.sh
#
# 标准 7 步 (by batch_runner.py):
#   prefilter → db_dedup → phase3 → phase3_5 → phase4_5 → db_import → tier_update
#
# CONVENTIONS.md:
#   - 输出文件名带日期时间戳
#   - DB 操作通过 batch_runner.py 代理（自动 cd 进 personal-ai-headhunter）
# ===========================================================

set -euo pipefail
export PYTHONUNBUFFERED=1

# ── 目录配置 ──────────────────────────────────────────────────
REPO_ROOT="/Users/lillianliao/notion_rag"
GITHUB_MINING_DIR="${REPO_ROOT}/github_mining"
SCRIPTS_DIR="${GITHUB_MINING_DIR}/scripts"
WRITE_DIR="${SCRIPTS_DIR}/github_mining"
HEADHUNTER_DIR="${REPO_ROOT}/personal-ai-headhunter"

# ── 时间戳 ───────────────────────────────────────────────────
DATE=$(date +%Y%m%d)

# ── 文件路径 ─────────────────────────────────────────────────
SEEDS_FILE="${GITHUB_MINING_DIR}/academic_github_seeds_${DATE}.json"
COOC_OUTPUT="${WRITE_DIR}/academic_cooc_expanded_${DATE}.json"
LOG_FILE="${GITHUB_MINING_DIR}/academic_cooc_pipeline_${DATE}.log"

# ── 参数配置 ─────────────────────────────────────────────────
MIN_COOC="${MIN_COOC:-2}"
SKIP_COOC="${SKIP_COOC:-false}"
COOC_INPUT="${COOC_INPUT:-${COOC_OUTPUT}}"   # 可外部指定已有共现文件
BATCH_NAME="academic_cooc_${DATE}"

# ── 颜色输出 ─────────────────────────────────────────────────
GREEN='\033[0;32m'; BLUE='\033[0;34m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $*" | tee -a "${LOG_FILE}"; }
ok()  { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $*${NC}" | tee -a "${LOG_FILE}"; }
err() { echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $*${NC}" | tee -a "${LOG_FILE}"; exit 1; }

mkdir -p "${WRITE_DIR}"

log "=================================================="
log "🚀 Academic-GitHub 共现挖掘流水线 v2"
log "   日期: ${DATE}"
log "   共现阈值: min_cooccurrence=${MIN_COOC}"
log "   SKIP_COOC: ${SKIP_COOC}"
log "=================================================="

# ── Telegram 通报（后台子进程）───────────────────────────────
_tg_pid=""
( sleep 30; while true; do
    python3 "${SCRIPTS_DIR}/pipeline_telegram_notifier.py" --test 2>/dev/null || true
    sleep 3600
  done ) &
_tg_pid=$!
log "📡 Telegram 机器人已启动 (PID: ${_tg_pid})"
trap 'kill "${_tg_pid}" 2>/dev/null || true' EXIT

# 发启动通知
python3 -c "
import sys; sys.path.insert(0, '${HEADHUNTER_DIR}')
try:
    from telegram_notifier import notify
    notify('🚀 *Academic-GitHub 共现挖掘流水线 v2 已启动！*')
except: pass
" 2>/dev/null || true

# ============================================================
# Step 1: 共现分析（唯一独有步骤）
# ============================================================
if [ "${SKIP_COOC}" = "true" ]; then
    log "跳过 Step 1 (SKIP_COOC=true)，使用: ${COOC_INPUT}"
    if [ ! -f "${COOC_INPUT}" ]; then
        err "COOC_INPUT 文件不存在: ${COOC_INPUT}"
    fi
else
    log "Step 1: 共现分析（auto_restart 包装）"
    cd "${REPO_ROOT}"
    python3 "${SCRIPTS_DIR}/auto_restart_wrapper.py" \
        --max-restarts 50 \
        --delay 30 \
        -- \
        python3 "${SCRIPTS_DIR}/academic_cooccurrence_miner.py" \
            --min-cooccurrence "${MIN_COOC}" \
            --resume \
            --date "${DATE}" \
        2>&1 | tee -a "${LOG_FILE}"

    if [ ! -f "${COOC_OUTPUT}" ]; then
        err "共现分析产出文件不存在: ${COOC_OUTPUT}"
    fi
    COUNT=$(python3 -c "import json; print(len(json.load(open('${COOC_OUTPUT}'))))")
    ok "共现分析完成！新发现用户: ${COUNT} 人 → ${COOC_OUTPUT}"
    COOC_INPUT="${COOC_OUTPUT}"
fi

# ============================================================
# Step 2-8: 标准 7 步流程（全部委托给 batch_runner.py）
# ============================================================
#
# ⚠️  注意：所有过滤/富化/入库步骤由 batch_runner.py 统一管理
# 不在此处自行实现 prefilter / phase3 / phase3_5 / phase4_5 / db_import
# 如需修改这些步骤，请修改 batch_runner.py，不要改此脚本
#
log "Step 2-8: 交给 batch_runner.py 执行标准 7 步流程..."
log "   输入: ${COOC_INPUT}"
log "   批次名: ${BATCH_NAME}"

cd "${SCRIPTS_DIR}"
python3 batch_runner.py \
    --input "${COOC_INPUT}" \
    --phases "prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update" \
    --batch-name "${BATCH_NAME}" \
    2>&1 | tee -a "${LOG_FILE}"

ok "=================================================="
ok "🎉 Academic-GitHub 共现挖掘流水线全部完成！"
ok "   日志: ${LOG_FILE}"
ok "   批次目录: ${SCRIPTS_DIR}/runs/*${BATCH_NAME}*"
ok "   下一步: 更新 BATCH_HISTORY.md 执行记录"
ok "=================================================="

# 发完成通知
python3 -c "
import sys; sys.path.insert(0, '${HEADHUNTER_DIR}')
try:
    from telegram_notifier import notify
    notify('🎉 *Academic-GitHub 共现挖掘完成！*\n批次: ${BATCH_NAME}')
except: pass
" 2>/dev/null || true
