#!/usr/bin/env bash
# =============================================================================
# run_phase4_full_pipeline.sh — Phase 4 社交网络扩展全链路无人值守流水线
# =============================================================================
# 用途: 从现有高质量 AI 候选人出发，进行社交网络共现分析扩展新人才，
#       然后自动完成富化、入库、分级，全程无需人工干预。
#
# 完整流程:
#   Phase 4 (扩展爬取) → Phase 3 (仓库深度富化) → Phase 3.5 (主页爬取)
#   → 入库 (import_github_candidates.py) → 分级 (batch_update_tiers.py)
#
# 使用方式:
#   1. 标准模式（默认参数）:
#      cd /Users/lillianliao/notion_rag
#      bash github_mining/scripts/run_phase4_full_pipeline.sh
#
#   2. 后台无人值守（推荐）:
#      nohup bash github_mining/scripts/run_phase4_full_pipeline.sh \
#        > /tmp/phase4_pipeline.log 2>&1 &
#      tail -f /tmp/phase4_pipeline.log
#
#   3. 自定义种子和参数:
#      SEED_TOP=500 MIN_CO=2 bash github_mining/scripts/run_phase4_full_pipeline.sh
#
#   4. 按 Tier 选种子（从数据库选 S/A 级别）:
#      SEED_TIER=S,A bash github_mining/scripts/run_phase4_full_pipeline.sh
#
#   5. 跳过 Phase 4 爬取（已有 phase4_expanded.json 时）:
#      SKIP_PHASE4=1 bash github_mining/scripts/run_phase4_full_pipeline.sh
#
#   6. 断点续传（上次中断后恢复）:
#      bash github_mining/scripts/run_phase4_full_pipeline.sh
#      (脚本自动检测 state 文件，跳过已完成步骤)
#
# 监控:
#   tail -f /tmp/phase4_pipeline.log
#   cat github_mining/scripts/github_mining/pipeline_state_phase4.json
# =============================================================================

set -euo pipefail

# ======================== 配置 ========================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTION_RAG_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
GITHUB_MINING_DIR="${NOTION_RAG_DIR}/github_mining"
HEADHUNTER_DIR="${NOTION_RAG_DIR}/personal-ai-headhunter"
MINING_SCRIPTS="${SCRIPT_DIR}"
DATA_DIR="${MINING_SCRIPTS}/github_mining"

# Phase 4 产出文件
PHASE4_OUTPUT="${DATA_DIR}/phase4_expanded.json"
# 流水线状态文件（独立于 run_phase4_enrichment.py 的 pipeline_state.json）
PIPELINE_STATE="${DATA_DIR}/pipeline_state_phase4.json"
LOG_FILE="${DATA_DIR}/pipeline_phase4_full.log"

# Phase 4 爬取参数
SEED_TOP="${SEED_TOP:-300}"                 # 从 AI 候选人中取前 N 为种子
MIN_CO="${MIN_CO:-3}"                       # 最小共现次数
SEED_TIER="${SEED_TIER:-}"                  # 按 Tier 选种子(如 S,A)，空=从文件取
SKIP_PHASE4="${SKIP_PHASE4:-0}"             # 1=跳过爬取，直接用已有 phase4_expanded.json

# ======================== 工具函数 ========================
log() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${ts}] $*" | tee -a "${LOG_FILE}"
}

step_done() {
    local step="$1"
    python3 -c "
import json, os
f = '${PIPELINE_STATE}'
d = json.load(open(f)) if os.path.exists(f) else {}
d['$step'] = True
json.dump(d, open(f,'w'), indent=2)
"
}

step_is_done() {
    python3 -c "
import json, os
f = '${PIPELINE_STATE}'
if not os.path.exists(f): print('false'); exit()
d = json.load(open(f))
print('true' if d.get('$1') else 'false')
" 2>/dev/null || echo "false"
}

run_with_retry() {
    local description="$1"; shift
    local attempt=0
    while [[ $attempt -lt 5 ]]; do
        attempt=$((attempt + 1))
        log "▶️  [${attempt}/5] ${description}"
        if "$@"; then
            log "✅ ${description} 成功"
            return 0
        else
            local exit_code=$?
            if [[ $attempt -lt 5 ]]; then
                log "⚠️  失败 (exit=${exit_code})，60s 后重试..."
                sleep 60
            else
                log "❌ ${description} 达到最大重试次数，终止"
                return 1
            fi
        fi
    done
}

# ======================== 主流程 ========================
mkdir -p "${DATA_DIR}"
log ""
log "============================================================"
log "🚀 Phase 4 全链路 Pipeline 启动"
log "   NOTION_RAG: ${NOTION_RAG_DIR}"
log "   SEED_TOP:   ${SEED_TOP}"
log "   MIN_CO:     ${MIN_CO}"
log "   SEED_TIER:  ${SEED_TIER:-（从文件取 Top ${SEED_TOP}）}"
log "   SKIP_P4:    ${SKIP_PHASE4}"
log "   STATE_FILE: ${PIPELINE_STATE}"
log "============================================================"

# ==================== Step 1: Phase 4 社交网络扩展爬取 ====================
if [[ "${SKIP_PHASE4}" == "1" ]]; then
    log "⏭️  [跳过] Phase 4 爬取（SKIP_PHASE4=1）"
    if [[ ! -f "${PHASE4_OUTPUT}" ]]; then
        log "❌ 找不到 ${PHASE4_OUTPUT}，且 SKIP_PHASE4=1。请先手动运行 Phase 4 爬取。"
        exit 1
    fi
elif [[ "$(step_is_done phase4_crawl)" == "true" ]]; then
    log "⏭️  [跳过] Phase 4 爬取（State 已记录完成）"
else
    log ""
    log "=============================="
    log "🕸️  Phase 4: 社交网络扩展爬取"
    log "=============================="

    # 构建 Phase 4 命令
    P4_CMD="python3 ${MINING_SCRIPTS}/github_network_miner.py phase4 --seed-top ${SEED_TOP} --min-cooccurrence ${MIN_CO}"
    if [[ -n "${SEED_TIER}" ]]; then
        P4_CMD="${P4_CMD} --seed-tier ${SEED_TIER}"
    fi

    # Phase 4 本身有内部断点续传逻辑（通过 phase4_progress.json）
    run_with_retry "Phase 4 社交网络扩展爬取" bash -c "${P4_CMD}"
    step_done "phase4_crawl"

    # 验证输出
    if [[ ! -f "${PHASE4_OUTPUT}" ]]; then
        log "❌ Phase 4 产出文件不存在: ${PHASE4_OUTPUT}"
        exit 1
    fi
    PHASE4_COUNT=$(python3 -c "import json; print(len(json.load(open('${PHASE4_OUTPUT}'))))")
    log "📊 Phase 4 扩展发现: ${PHASE4_COUNT} 人 → ${PHASE4_OUTPUT}"
fi

# ==================== Step 2+: 富化 → 入库 → 分级（复用 run_phase4_enrichment.py）====================
log ""
log "=============================="
log "🔬 启动富化/入库/分级流水线"
log "=============================="
log "复用 run_phase4_enrichment.py（内置断点续传 + 验证 + 自动重启）"

# run_phase4_enrichment.py 有自己的 state 文件（pipeline_state.json）
# 它的 auto_restart_wrapper 会自动重试，这里给它一个最大重试层
run_with_retry "Phase 4 富化→入库→分级全流程" \
    python3 "${MINING_SCRIPTS}/auto_restart_wrapper.py" -- \
    python3 "${MINING_SCRIPTS}/run_phase4_enrichment.py"

step_done "enrichment_done"

# ==================== 最终汇报 ====================
log ""
log "=============================="
log "🔍 最终数据库验证"
log "=============================="
bash -c "cd '${HEADHUNTER_DIR}' && python3 -c \"
from database import SessionLocal, Candidate
from collections import Counter
session = SessionLocal()
all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
tier_dist = Counter(c.talent_tier for c in all_gh)
has_li = sum(1 for c in all_gh if c.linkedin_url)
print(f'GitHub 候选人总数: {len(all_gh)}')
for t in ['S', 'A', 'B', 'C']:
    print(f'  {t}: {tier_dist.get(t, 0)} 人')
print(f'有 LinkedIn: {has_li} 人')
session.close()
\""

log ""
log "============================================================"
log "🎉 Phase 4 全链路 Pipeline 执行完毕！"
log "   建议下一步: 针对新增 S/A 候选人启动触达"
log "   命令: cd personal-ai-headhunter && python3 scripts/batch_ai_outreach.py --tiers S,A"
log "============================================================"
