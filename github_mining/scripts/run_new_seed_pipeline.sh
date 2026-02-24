#!/usr/bin/env bash
# =============================================================================
# run_new_seed_pipeline.sh — 新 Seed 全链路无人值守流水线
# =============================================================================
# 用途: Phase 1 采集完成后，自动串联 Phase 2V3 → 3V3 → 3.5 → 入库 → 分级
#
# 使用方式:
#   1. 正常模式:
#      cd /Users/lillianliao/notion_rag
#      bash github_mining/scripts/run_new_seed_pipeline.sh
#
#   2. 后台无人值守（推荐）:
#      nohup bash github_mining/scripts/run_new_seed_pipeline.sh \
#        > github_mining/scripts/github_mining/pipeline_seed.log 2>&1 &
#      tail -f github_mining/scripts/github_mining/pipeline_seed.log
#
#   3. 跳过 Phase 1（已有数据时）:
#      SKIP_PHASE1=1 bash github_mining/scripts/run_new_seed_pipeline.sh
#
#   4. 从某步骤重新开始:
#      START_FROM=phase3_5 bash github_mining/scripts/run_new_seed_pipeline.sh
#      (可选值: phase2_v3 | phase3_v3 | phase3_5 | import | tier)
#
# 断点续传说明:
#   - 脚本使用 STATE_FILE 记录各步骤完成状态
#   - 崩溃/中断后直接重新执行，已完成步骤自动跳过
#   - Phase 2V3/3.5 内部支持 --resume，不会重复处理
# =============================================================================

set -euo pipefail

# ======================== 配置 ========================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTION_RAG_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"        # /Users/lillianliao/notion_rag
GITHUB_MINING_DIR="${NOTION_RAG_DIR}/github_mining"
HEADHUNTER_DIR="${NOTION_RAG_DIR}/personal-ai-headhunter"
MINING_SCRIPTS="${SCRIPT_DIR}"
DATA_DIR="${MINING_SCRIPTS}/github_mining"

STATE_FILE="${DATA_DIR}/pipeline_new_seed_state.json"
LOG_FILE="${DATA_DIR}/pipeline_new_seed.log"

# Phase 3.5 爬取 Top N 候选人（按 AI 评分排序）
PHASE35_TOP="${PHASE35_TOP:-500}"

# 起始阶段（用于断点重跑）
START_FROM="${START_FROM:-auto}"     # auto | phase2_v3 | phase3_v3 | phase3_5 | import | tier

# ======================== 工具函数 ========================
log() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${ts}] $*" | tee -a "${LOG_FILE}"
}

step_done() {
    local step="$1"
    # 读取现有 state，设置该步骤为 true
    python3 -c "
import json, os
f = '${STATE_FILE}'
d = json.load(open(f)) if os.path.exists(f) else {}
d['${step}'] = True
json.dump(d, open(f,'w'), indent=2)
print('state saved: ${step} = done')
"
}

step_is_done() {
    local step="$1"
    python3 -c "
import json, os
f = '${STATE_FILE}'
if not os.path.exists(f):
    print('false'); exit()
d = json.load(open(f))
print('true' if d.get('${step}') else 'false')
" 2>/dev/null || echo "false"
}

should_skip() {
    local step="$1"
    # 如果 START_FROM 明确指定了更靠后的步骤，则跳过当前步骤
    local steps=("phase2_v3" "phase3_v3" "phase3_5" "import" "tier")
    if [[ "${START_FROM}" == "auto" ]]; then
        # auto 模式：根据 state 文件判断
        [[ "$(step_is_done "${step}")" == "true" ]]
    else
        # 手动指定：从指定步骤之前的所有步骤都跳过
        local found=false
        for s in "${steps[@]}"; do
            if [[ "${s}" == "${START_FROM}" ]]; then
                found=true
            fi
            if [[ "${s}" == "${step}" ]]; then
                # 如果还没找到 START_FROM，说明当前步骤在前面，跳过
                [[ "${found}" == "false" ]]
                return
            fi
        done
        return 1  # 不跳过
    fi
}

run_with_retry() {
    local description="$1"
    shift
    local max_retries=5
    local retry_delay=30
    local attempt=0

    while [[ $attempt -lt $max_retries ]]; do
        attempt=$((attempt + 1))
        log "▶️  [${attempt}/${max_retries}] ${description}"
        if "$@"; then
            log "✅ ${description} 成功"
            return 0
        else
            local exit_code=$?
            if [[ $attempt -lt $max_retries ]]; then
                log "⚠️  失败 (exit=${exit_code})，${retry_delay}s 后重试..."
                sleep "${retry_delay}"
            else
                log "❌ ${description} 达到最大重试次数，放弃"
                return 1
            fi
        fi
    done
}

# ======================== 主流程 ========================
mkdir -p "${DATA_DIR}"
log ""
log "============================================================"
log "🚀 新 Seed 全链路 Pipeline 启动"
log "   NOTION_RAG: ${NOTION_RAG_DIR}"
log "   STATE_FILE: ${STATE_FILE}"
log "   START_FROM: ${START_FROM}"
log "============================================================"

# -------------------- Step 1: Phase 1 确认 --------------------
if [[ "${SKIP_PHASE1:-0}" == "1" ]]; then
    log "⏭️  [跳过] Phase 1（SKIP_PHASE1=1）"
else
    SEED_FILE="${GITHUB_MINING_DIR}/phase1_seed_users.json"
    if [[ ! -f "${SEED_FILE}" ]]; then
        log "❌ 未找到 ${SEED_FILE}，请先运行 Phase 1！"
        exit 1
    fi
    SEED_COUNT=$(python3 -c "import json; d=json.load(open('${SEED_FILE}')); print(len(d))")
    log "✅ Phase 1 数据已就绪: ${SEED_COUNT} 人 → ${SEED_FILE}"
fi

# -------------------- Step 2: Phase 2 V3 全量轻富化 --------------------
if should_skip "phase2_v3"; then
    log "⏭️  [跳过] Phase 2 V3（已完成）"
else
    log ""
    log "=============================="
    log "📡 Phase 2 V3: 全量轻富化"
    log "=============================="
    run_with_retry "Phase 2 V3 全量轻富化" \
        python3 "${MINING_SCRIPTS}/github_network_miner.py" phase2_v3 --resume
    step_done "phase2_v3"
fi

# -------------------- Step 3: Phase 3 V3 AI 判定 --------------------
if should_skip "phase3_v3"; then
    log "⏭️  [跳过] Phase 3 V3（已完成）"
else
    log ""
    log "=============================="
    log "🔬 Phase 3 V3: AI 相关性判定"
    log "=============================="
    run_with_retry "Phase 3 V3 AI 判定" \
        python3 "${MINING_SCRIPTS}/github_network_miner.py" phase3_v3
    step_done "phase3_v3"

    # 打印统计
    python3 -c "
import json, os
ai_file = '${DATA_DIR}/phase3_v3_ai_candidates.json'
rej_file = '${DATA_DIR}/phase3_v3_rejected.json'
if os.path.exists(ai_file):
    ai = json.load(open(ai_file))
    rej = json.load(open(rej_file)) if os.path.exists(rej_file) else []
    total = len(ai) + len(rej)
    pct = len(ai)*100//total if total else 0
    print(f'  📊 AI 相关: {len(ai)} 人 ({pct}%)，非 AI: {len(rej)} 人')
" 2>/dev/null || true
fi

# -------------------- Step 4: Phase 3.5 主页深度爬取 --------------------
if should_skip "phase3_5"; then
    log "⏭️  [跳过] Phase 3.5（已完成）"
else
    log ""
    log "=============================="
    log "🌐 Phase 3.5: 个人主页深度爬取 (Top ${PHASE35_TOP})"
    log "=============================="
    run_with_retry "Phase 3.5 主页爬取" \
        python3 "${MINING_SCRIPTS}/github_network_miner.py" phase3_5 \
            --top "${PHASE35_TOP}" \
            --input phase3_v3_ai_candidates.json \
            --resume
    step_done "phase3_5"

    # 打印统计
    python3 -c "
import json, os
f = '${DATA_DIR}/phase3_5_enriched.json'
if os.path.exists(f):
    d = json.load(open(f))
    scraped = sum(1 for u in d if u.get('homepage_scraped'))
    has_li = sum(1 for u in d if u.get('linkedin_url'))
    print(f'  📊 Phase 3.5 完成: {len(d)} 人，主页成功: {scraped}，有 LinkedIn: {has_li}')
" 2>/dev/null || true
fi

# -------------------- Step 5: 入库 --------------------
if should_skip "import"; then
    log "⏭️  [跳过] 入库（已完成）"
else
    log ""
    log "=============================="
    log "📥 入库: 导入猎头系统数据库"
    log "=============================="
    # ⚠️ 必须 cd 到 personal-ai-headhunter 目录，.env 里 DB_PATH 是相对路径
    run_with_retry "导入猎头数据库" \
        bash -c "cd '${HEADHUNTER_DIR}' && python3 import_github_candidates.py \
            --file '${DATA_DIR}/phase3_5_enriched.json'"
    step_done "import"
fi

# -------------------- Step 6: 分级 --------------------
if should_skip "tier"; then
    log "⏭️  [跳过] 分级（已完成）"
else
    log ""
    log "=============================="
    log "🏆 分级: Tier S/A/B/C 评分"
    log "=============================="
    run_with_retry "Tier 评分" \
        bash -c "cd '${HEADHUNTER_DIR}' && python3 batch_update_tiers.py"
    step_done "tier"
fi

# ======================== 验证 ========================
log ""
log "=============================="
log "🔍 最终验证"
log "=============================="
bash -c "cd '${HEADHUNTER_DIR}' && python3 -c \"
from database import SessionLocal, Candidate
from collections import Counter
session = SessionLocal()
all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
tier_dist = Counter(c.talent_tier for c in all_gh)
untiered = tier_dist.get(None, 0)
print(f'GitHub 候选人总数: {len(all_gh)}')
for tier in ['S', 'A', 'B', 'C']:
    print(f'  {tier}: {tier_dist.get(tier, 0)} 人')
if untiered > 0:
    print(f'  ⚠️  未分级: {untiered} 人（需重新运行分级步骤）')
else:
    print('✅ 全部已分级')
session.close()
\""

log ""
log "============================================================"
log "🎉 全流程 Pipeline 执行完毕！"
log "   下一步: 针对新入库 S/A 候选人启动触达"
log "   命令: python3 personal-ai-headhunter/scripts/batch_ai_outreach.py --tiers S,A"
log "============================================================"
