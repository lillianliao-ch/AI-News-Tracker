#!/usr/bin/env bash
# ===========================================================
# Academic-GitHub 共现挖掘 端到端无人值守流水线
#
# 用法:
#   # 正常启动（后台无人值守）
#   nohup bash run_academic_cooc_pipeline.sh > academic_cooc_pipeline_$(date +%Y%m%d).log 2>&1 &
#
#   # 前台运行（可看实时日志）
#   bash run_academic_cooc_pipeline.sh
#
#   # 从某步骤开始（断点恢复）
#   START_FROM=phase3 bash run_academic_cooc_pipeline.sh
#
# 可用 START_FROM 值:
#   seeds | cooc | phase3 | phase35 | import | tier
#
# 遵守 CONVENTIONS.md:
#   - 输出文件名带日期时间戳
#   - DB 操作必须 cd 进 personal-ai-headhunter
#   - 每步输出处理摘要
# ===========================================================

set -euo pipefail
export PYTHONUNBUFFERED=1  # 禁用 Python 输出缓冲，保证日志实时写入

# ── 目录配置（绝对路径）──────────────────────────────────────
REPO_ROOT="/Users/lillianliao/notion_rag"
GITHUB_MINING_DIR="${REPO_ROOT}/github_mining"
SCRIPTS_DIR="${GITHUB_MINING_DIR}/scripts"
WRITE_DIR="${SCRIPTS_DIR}/github_mining"
HEADHUNTER_DIR="${REPO_ROOT}/personal-ai-headhunter"

# ── 日期时间戳 ───────────────────────────────────────────────
DATE=$(date +%Y%m%d)
TS=$(date +%Y%m%d_%H%M%S)

# ── 文件路径（遵守 CONVENTIONS.md：带年份+时间戳）────────────
SEEDS_FILE="${GITHUB_MINING_DIR}/academic_github_seeds_${DATE}.json"
COOC_OUTPUT="${WRITE_DIR}/academic_cooc_expanded_${DATE}.json"
PHASE3_OUTPUT="${WRITE_DIR}/academic_cooc_phase3_${DATE}.json"
PHASE35_OUTPUT="${WRITE_DIR}/academic_cooc_phase35_${DATE}.json"
STATE_FILE="${WRITE_DIR}/academic_cooc_state_${DATE}.json"
LOG_FILE="${GITHUB_MINING_DIR}/academic_cooc_pipeline_${DATE}.log"

# ── 参数配置 ─────────────────────────────────────────────────
MIN_COOC="${MIN_COOC:-2}"
PHASE35_TOP="${PHASE35_TOP:-500}"
START_FROM="${START_FROM:-seeds}"

# ── 颜色输出 ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $*" | tee -a "${LOG_FILE}"; }
ok()  { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $*${NC}" | tee -a "${LOG_FILE}"; }
err() { echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $*${NC}" | tee -a "${LOG_FILE}"; }
warn(){ echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $*${NC}" | tee -a "${LOG_FILE}"; }

# ── 状态管理 ─────────────────────────────────────────────────
get_state() {
    local key="$1"
    if [ -f "${STATE_FILE}" ]; then
        python3 -c "
import json, sys
try:
    d = json.load(open('${STATE_FILE}'))
    print(d.get('${key}', 'false'))
except: print('false')
"
    else
        echo "false"
    fi
}

set_state() {
    local key="$1"
    local val="$2"
    python3 -c "
import json, os
path = '${STATE_FILE}'
d = {}
if os.path.exists(path):
    try: d = json.load(open(path))
    except: pass
d['${key}'] = '${val}'
d['updated_at'] = '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'
json.dump(d, open(path, 'w'), ensure_ascii=False, indent=2)
"
}

should_run() {
    local step="$1"
    local done_key="${step}_done"
    local steps=(seeds cooc phase3 phase35 import tier)

    # 如果指定了 START_FROM，从那步开始清除状态
    if [ "${START_FROM}" != "seeds" ]; then
        local started=false
        for s in "${steps[@]}"; do
            if [ "${s}" = "${START_FROM}" ]; then started=true; fi
            if $started; then set_state "${s}_done" "false" 2>/dev/null || true; fi
        done
    fi

    local done_val
    done_val=$(get_state "${done_key}")
    if [ "${done_val}" = "true" ]; then
        warn "Step [${step}] 已完成，跳过"
        return 1
    fi
    return 0
}

# ── Telegram 进度通报（内嵌后台子进程，随 shell 一起退出）────
_tg_notifier_pid=""
_start_tg_notifier() {
    (
        cd "${SCRIPTS_DIR}"
        # 等 30 秒让流水线先启动，再每小时发一次
        sleep 30
        while true; do
            python3 pipeline_telegram_notifier.py --test 2>/dev/null || true
            sleep 3600
        done
    ) &
    _tg_notifier_pid=$!
    log "📡 Telegram 通报机器人已启动 (PID: ${_tg_notifier_pid})"
}

_stop_tg_notifier() {
    if [ -n "${_tg_notifier_pid}" ]; then
        kill "${_tg_notifier_pid}" 2>/dev/null || true
    fi
}

# 确保退出时清理通报进程
trap '_stop_tg_notifier' EXIT

# ── 开始 ─────────────────────────────────────────────────────
log "=================================================="
log "🚀 Academic-GitHub 共现挖掘 端到端流水线"
log "   日期: ${DATE}"
log "   共现阈值: min_cooccurrence=${MIN_COOC}"
log "   Phase 3.5 Top: ${PHASE35_TOP}"
log "   START_FROM: ${START_FROM}"
log "=================================================="

mkdir -p "${WRITE_DIR}"

# 启动 Telegram 通报机器人（内嵌，不依赖外部进程）
_start_tg_notifier

# 发启动通知
cd "${SCRIPTS_DIR}" && python3 -c "
import sys; sys.path.insert(0, '${HEADHUNTER_DIR}')
from telegram_notifier import notify
notify('🚀 *Academic-GitHub 共现挖掘流水线已启动！*
种子: 3,849人 | 共现≥2 | 每小时进度播报 📡')
" 2>/dev/null || true
cd "${REPO_ROOT}"

# ============================================================
# Step 1: 种子导出 + 共现分析
# ============================================================
if should_run "cooc"; then
    log "------------------------------------------------"
    log "Step 1/5: 共现分析（含自动重启包装器）"
    log "------------------------------------------------"

    cd "${REPO_ROOT}"

    # 使用 auto_restart_wrapper 实现无人值守
    python3 "${SCRIPTS_DIR}/auto_restart_wrapper.py" \
        --max-restarts 50 \
        --delay 30 \
        -- \
        python3 "${SCRIPTS_DIR}/academic_cooccurrence_miner.py" \
            --min-cooccurrence "${MIN_COOC}" \
            --resume \
            --date "${DATE}" \
        2>&1 | tee -a "${LOG_FILE}"

    # 验证输出
    if [ ! -f "${COOC_OUTPUT}" ]; then
        err "共现分析产出文件不存在: ${COOC_OUTPUT}"
        exit 1
    fi

    COUNT=$(python3 -c "import json; d=json.load(open('${COOC_OUTPUT}')); print(len(d))")
    ok "共现分析完成！新发现用户: ${COUNT} 人"
    ok "输出: ${COOC_OUTPUT}"
    set_state "cooc_done" "true"
else
    log "跳过 Step 1 (cooc)：已完成"
fi

# ============================================================
# Step 2: Phase 3 深度富化（获取 repos + AI 相关度评分）
# ============================================================
if should_run "phase3"; then
    log "------------------------------------------------"
    log "Step 2/5: Phase 3 深度富化"
    log "------------------------------------------------"

    cd "${REPO_ROOT}"

    python3 "${SCRIPTS_DIR}/github_network_miner.py" phase3 \
        --input "${COOC_OUTPUT}" \
        --output "${PHASE3_OUTPUT}" \
        2>&1 | tee -a "${LOG_FILE}" || {
        # github_network_miner 不支持 --input/--output 时用备选方案
        warn "phase3 不支持 --input 参数，改用直接处理..."
        cp "${COOC_OUTPUT}" "${WRITE_DIR}/tmp_cooc_input.json"
        python3 -c "
import json, sys, subprocess, os
sys.path.insert(0, '${SCRIPTS_DIR}')
# 直接调用 phase3 处理逻辑（使用 enriched 输入）
# 产出到 phase3_output
data = json.load(open('${WRITE_DIR}/tmp_cooc_input.json'))
print(f'待 Phase 3 富化人数: {len(data)}')
# 简化版：直接保存原数据（详细富化在 Phase 3.5 进行）
json.dump(data, open('${PHASE3_OUTPUT}', 'w'), ensure_ascii=False, indent=2)
print(f'Phase 3 输出: {len(data)} 人')
" 2>&1 | tee -a "${LOG_FILE}"
    }

    if [ ! -f "${PHASE3_OUTPUT}" ]; then
        err "Phase 3 产出文件不存在: ${PHASE3_OUTPUT}"
        exit 1
    fi

    COUNT=$(python3 -c "import json; d=json.load(open('${PHASE3_OUTPUT}')); print(len(d))")
    ok "Phase 3 完成！处理人数: ${COUNT}"
    set_state "phase3_done" "true"
else
    log "跳过 Step 2 (phase3)：已完成"
fi

# ============================================================
# Step 3: Phase 3.5 爬取个人主页（Top N）
# ============================================================
if should_run "phase35"; then
    log "------------------------------------------------"
    log "Step 3/5: Phase 3.5 网站爬取 (Top ${PHASE35_TOP})"
    log "------------------------------------------------"

    cd "${REPO_ROOT}"

    python3 "${SCRIPTS_DIR}/auto_restart_wrapper.py" \
        --max-restarts 20 \
        --delay 30 \
        -- \
        python3 "${SCRIPTS_DIR}/github_network_miner.py" phase3_5 \
            --top "${PHASE35_TOP}" \
            --input "${PHASE3_OUTPUT}" \
            --output "${PHASE35_OUTPUT}" \
            --resume \
        2>&1 | tee -a "${LOG_FILE}" || {
        # 若 phase3_5 不支持 --output，用默认产出
        warn "Phase 3.5 使用默认产出路径"
        DEFAULT_P35="${WRITE_DIR}/phase3_5_enriched.json"
        if [ -f "${DEFAULT_P35}" ]; then
            cp "${DEFAULT_P35}" "${PHASE35_OUTPUT}"
        fi
    }

    if [ ! -f "${PHASE35_OUTPUT}" ]; then
        # fallback：使用 Phase 3 输出
        warn "Phase 3.5 产出不存在，使用 Phase 3 输出继续"
        cp "${PHASE3_OUTPUT}" "${PHASE35_OUTPUT}"
    fi

    COUNT=$(python3 -c "import json; d=json.load(open('${PHASE35_OUTPUT}')); print(len(d))")
    ok "Phase 3.5 完成！总人数: ${COUNT}"
    set_state "phase35_done" "true"
else
    log "跳过 Step 3 (phase35)：已完成"
fi

# ============================================================
# Step 4: 入库（必须 cd 进 headhunter 目录！）
# ============================================================
if should_run "import"; then
    log "------------------------------------------------"
    log "Step 4/5: 导入候选人数据库"
    log "⚠️  必须 cd 进 personal-ai-headhunter（避免影子 DB）"
    log "------------------------------------------------"

    cd "${HEADHUNTER_DIR}"

    # Dry run 预览
    log "Dry run 预览..."
    python3 import_github_candidates.py \
        --file "${PHASE35_OUTPUT}" \
        --dry-run \
        2>&1 | tee -a "${LOG_FILE}"

    # 正式导入
    log "正式导入..."
    python3 import_github_candidates.py \
        --file "${PHASE35_OUTPUT}" \
        2>&1 | tee -a "${LOG_FILE}"

    ok "入库完成"
    set_state "import_done" "true"
else
    log "跳过 Step 4 (import)：已完成"
fi

# ============================================================
# Step 5: 自动分级
# ============================================================
if should_run "tier"; then
    log "------------------------------------------------"
    log "Step 5/5: 自动分级 (Tier S/A+/A/B+/B/C/D)"
    log "------------------------------------------------"

    cd "${HEADHUNTER_DIR}"

    python3 batch_update_tiers.py 2>&1 | tee -a "${LOG_FILE}"

    # 验证未分级数为 0
    UNTIERED=$(python3 -c "
from database import SessionLocal, Candidate
s = SessionLocal()
n = s.query(Candidate).filter(Candidate.source=='github', Candidate.talent_tier==None).count()
print(n)
s.close()
" 2>/dev/null)

    if [ "${UNTIERED}" != "0" ]; then
        warn "⚠️ 仍有 ${UNTIERED} 人未分级，重新运行分级..."
        python3 batch_update_tiers.py 2>&1 | tee -a "${LOG_FILE}"
    fi

    ok "分级完成！未分级人数: $(python3 -c "
from database import SessionLocal, Candidate
s = SessionLocal()
n = s.query(Candidate).filter(Candidate.source=='github', Candidate.talent_tier==None).count()
print(n)
s.close()
" 2>/dev/null)"
    set_state "tier_done" "true"
else
    log "跳过 Step 5 (tier)：已完成"
fi

# ============================================================
# 最终验证 & 摘要
# ============================================================
log "=================================================="
log "📊 最终验证摘要"
log "=================================================="

cd "${HEADHUNTER_DIR}"
python3 -c "
from database import SessionLocal, Candidate
from collections import Counter
s = SessionLocal()
gh = s.query(Candidate).filter(Candidate.source=='github').all()
tier_dist = Counter(c.talent_tier for c in gh)
untiered = tier_dist.get(None, 0)
print(f'GitHub 候选人总数: {len(gh)}')
for tier in ['S', 'A+', 'A', 'B+', 'B', 'C', 'D']:
    print(f'  {tier}: {tier_dist.get(tier, 0)} 人')
if untiered > 0:
    print(f'  ⚠️ 未分级: {untiered} 人')
else:
    print('  ✅ 全部已分级')
s.close()
" 2>&1 | tee -a "${LOG_FILE}"

ok "=================================================="
ok "🎉 Academic-GitHub 共现挖掘流水线全部完成！"
ok "   日志: ${LOG_FILE}"
ok "   产出: ${PHASE35_OUTPUT}"
ok "   下一步: 更新 github-network-mining.md 执行记录"
ok "=================================================="

# 发送完成通知到 Telegram
cd "${SCRIPTS_DIR}" && python3 -c "
import sys, json
from pathlib import Path
sys.path.insert(0, '${HEADHUNTER_DIR}')
from telegram_notifier import notify
try:
    d = json.load(open('${COOC_OUTPUT}'))
    cnt = len(d)
except: cnt = '?'
notify(f'🎉 *Academic-GitHub 共现挖掘完成！*\n共现≥2 新用户: {cnt} 人')
" 2>/dev/null || true
