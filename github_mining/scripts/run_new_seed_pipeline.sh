#!/usr/bin/env bash
# =============================================================================
# run_new_seed_pipeline.sh — 新 Seed 全链路无人值守流水线
# =============================================================================
# 用途: Phase 1 采集完成后，自动串联 Phase 2V3 → 3V3 → 3.5 → 入库 → 分级
#
# 使用方式:
#   1. 全新独立批次（推荐，每次新 seed 时用这个）:
#      BATCH_NAME=cncoderhunter FRESH=1 bash github_mining/scripts/run_new_seed_pipeline.sh
#
#   2. 后台无人值守:
#      BATCH_NAME=cncoderhunter FRESH=1 nohup bash github_mining/scripts/run_new_seed_pipeline.sh \
#        > /tmp/pipeline_cncoderhunter.log 2>&1 &
#      tail -f /tmp/pipeline_cncoderhunter.log
#
#   3. 断点续传（崩溃后恢复，不加 FRESH）:
#      BATCH_NAME=cncoderhunter bash github_mining/scripts/run_new_seed_pipeline.sh
#
#   4. 从某步骤重新开始:
#      BATCH_NAME=cncoderhunter START_FROM=phase3_5 bash github_mining/scripts/run_new_seed_pipeline.sh
#      (可选值: phase2_v3 | phase3_v3 | phase3_5 | import | tier)
#
#   5. 调整 Phase 3.5 爬取数量（默认 Top 500）:
#      BATCH_NAME=cncoderhunter FRESH=1 PHASE35_TOP=300 bash github_mining/scripts/run_new_seed_pipeline.sh
#
# 断点续传说明:
#   - 用 STATE_FILE 记录各步完成状态，崩溃后重启自动跳过已完成步骤
#   - Phase 2V3/3.5 内部支持 --resume，不重复处理
# =============================================================================

set -euo pipefail

# ======================== 配置 ========================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTION_RAG_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
GITHUB_MINING_DIR="${NOTION_RAG_DIR}/github_mining"
HEADHUNTER_DIR="${NOTION_RAG_DIR}/personal-ai-headhunter"
MINING_SCRIPTS="${SCRIPT_DIR}"
# Phase 1/2/3 数据存放在 scripts/github_mining/ 子目录（miner 脚本的工作目录）
DATA_DIR="${MINING_SCRIPTS}/github_mining"
# Phase 1 --target 产出路径
SEED_FILE_INNER="${DATA_DIR}/phase1_seed_users.json"

# 批次名（用于隔离存档）
BATCH_NAME="${BATCH_NAME:-batch_$(date +%Y%m%d)}"
BATCH_DIR="${DATA_DIR}/batches/${BATCH_NAME}"

STATE_FILE="${BATCH_DIR}/pipeline_state.json"
LOG_FILE="${BATCH_DIR}/pipeline.log"

# 是否全新开始（清除旧中间文件）
FRESH="${FRESH:-0}"

# Phase 3.5 爬取 Top N
PHASE35_TOP="${PHASE35_TOP:-9999}"   # 默认全量处理所有 AI 候选人

# 起始阶段（用于断点重跑）
START_FROM="${START_FROM:-auto}"

# 中间文件列表（需要隔离的 miner 产出）
INTERMEDIATE_FILES=(
    "phase2_v3_enriched.json"
    "phase3_v3_ai_candidates.json"
    "phase3_v3_rejected.json"
    "phase3_5_enriched.json"
)

# ======================== 工具函数 ========================
log() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${ts}] $*" | tee -a "${LOG_FILE}"
}

step_done() {
    python3 -c "
import json, os
f = '${STATE_FILE}'
d = json.load(open(f)) if os.path.exists(f) else {}
d['$1'] = True
json.dump(d, open(f,'w'), indent=2)
"
}

step_is_done() {
    python3 -c "
import json, os
f = '${STATE_FILE}'
if not os.path.exists(f): print('false'); exit()
d = json.load(open(f))
print('true' if d.get('$1') else 'false')
" 2>/dev/null || echo "false"
}

should_skip() {
    local step="$1"
    local steps=("phase2_v3" "phase3_v3" "phase3_5" "import" "tier")
    if [[ "${START_FROM}" == "auto" ]]; then
        [[ "$(step_is_done "${step}")" == "true" ]]
    else
        local found=false
        for s in "${steps[@]}"; do
            [[ "${s}" == "${START_FROM}" ]] && found=true
            if [[ "${s}" == "${step}" ]]; then
                [[ "${found}" == "false" ]]; return
            fi
        done
        return 1
    fi
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
                log "⚠️  失败 (exit=${exit_code})，30s 后重试..."
                sleep 30
            else
                log "❌ ${description} 达到最大重试次数，放弃"
                return 1
            fi
        fi
    done
}

# ======================== 主流程 ========================
mkdir -p "${BATCH_DIR}"
log ""
log "============================================================"
log "🚀 新 Seed 全链路 Pipeline 启动"
log "   批次名:   ${BATCH_NAME}"
log "   批次目录: ${BATCH_DIR}"
log "   FRESH:    ${FRESH}"
log "   START_FROM: ${START_FROM}"
log "============================================================"

# -------------------- FRESH 模式: 备份旧中间文件 --------------------
if [[ "${FRESH}" == "1" ]]; then
    log ""
    log "🧹 FRESH 模式: 备份旧中间文件，从头开始..."
    BACKUP_DIR="${DATA_DIR}/batches/_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${BACKUP_DIR}"
    for fname in "${INTERMEDIATE_FILES[@]}"; do
        src="${DATA_DIR}/${fname}"
        if [[ -f "${src}" ]]; then
            cp "${src}" "${BACKUP_DIR}/${fname}"
            rm "${src}"
            log "  📦 已备份并清除: ${fname}"
        fi
    done
    log "✅ 旧数据已备份到: ${BACKUP_DIR}"
    log ""
fi

# -------------------- Step 1: Phase 1 确认 --------------------
if [[ "${SKIP_PHASE1:-0}" == "1" ]]; then
    log "⏭️  [跳过] Phase 1（SKIP_PHASE1=1）"
else
    if [[ ! -f "${SEED_FILE_INNER}" ]]; then
        log "❌ 未找到 ${SEED_FILE_INNER}，请先运行 Phase 1！"
        exit 1
    fi
    SEED_COUNT=$(python3 -c "import json; d=json.load(open('${SEED_FILE_INNER}')); print(len(d))")
    log "✅ Phase 1 数据已就绪: ${SEED_COUNT} 人 → ${SEED_FILE_INNER}"
fi

# -------------------- Step 2: Phase 2 V3 全量轻富化 --------------------
if should_skip "phase2_v3"; then
    log "⏭️  [跳过] Phase 2 V3（已完成）"
else
    log ""; log "=============================="; log "📡 Phase 2 V3: 全量轻富化"; log "=============================="
    run_with_retry "Phase 2 V3 全量轻富化" \
        python3 "${MINING_SCRIPTS}/github_network_miner.py" phase2_v3 --resume
    step_done "phase2_v3"
    # 存档到批次目录
    cp "${DATA_DIR}/phase2_v3_enriched.json" "${BATCH_DIR}/" 2>/dev/null || true
fi

# -------------------- Step 3: Phase 3 V3 AI 判定 --------------------
if should_skip "phase3_v3"; then
    log "⏭️  [跳过] Phase 3 V3（已完成）"
else
    log ""; log "=============================="; log "🔬 Phase 3 V3: AI 相关性判定"; log "=============================="
    run_with_retry "Phase 3 V3 AI 判定" \
        python3 "${MINING_SCRIPTS}/github_network_miner.py" phase3_v3
    step_done "phase3_v3"
    cp "${DATA_DIR}/phase3_v3_ai_candidates.json" "${BATCH_DIR}/" 2>/dev/null || true
    cp "${DATA_DIR}/phase3_v3_rejected.json"      "${BATCH_DIR}/" 2>/dev/null || true
    python3 -c "
import json, os
ai = json.load(open('${DATA_DIR}/phase3_v3_ai_candidates.json'))
rej = json.load(open('${DATA_DIR}/phase3_v3_rejected.json')) if os.path.exists('${DATA_DIR}/phase3_v3_rejected.json') else []
total = len(ai)+len(rej)
pct = len(ai)*100//total if total else 0
print(f'  📊 AI 相关: {len(ai)} 人 ({pct}%)，非 AI: {len(rej)} 人')
" 2>/dev/null || true
fi

# -------------------- Step 4: Phase 3.5 主页深度爬取 --------------------
if should_skip "phase3_5"; then
    log "⏭️  [跳过] Phase 3.5（已完成）"
else
    log ""; log "=============================="; log "🌐 Phase 3.5: 个人主页爬取 (Top ${PHASE35_TOP})"; log "=============================="
    run_with_retry "Phase 3.5 主页爬取" \
        python3 "${MINING_SCRIPTS}/github_network_miner.py" phase3_5 \
            --top "${PHASE35_TOP}" \
            --input "${DATA_DIR}/phase3_v3_ai_candidates.json" \
            --resume
    step_done "phase3_5"
    cp "${DATA_DIR}/phase3_5_enriched.json" "${BATCH_DIR}/" 2>/dev/null || true
    python3 -c "
import json
d = json.load(open('${DATA_DIR}/phase3_5_enriched.json'))
scraped = sum(1 for u in d if u.get('homepage_scraped'))
has_li = sum(1 for u in d if u.get('linkedin_url'))
print(f'  📊 Phase 3.5 完成: {len(d)} 人，主页成功: {scraped}，有 LinkedIn: {has_li}')
" 2>/dev/null || true
fi

# -------------------- Step 5: 入库 --------------------
if should_skip "import"; then
    log "⏭️  [跳过] 入库（已完成）"
else
    log ""; log "=============================="; log "📥 入库: 导入猎头系统数据库"; log "=============================="
    run_with_retry "导入猎头数据库" \
        bash -c "cd '${HEADHUNTER_DIR}' && python3 import_github_candidates.py \
            --file '${DATA_DIR}/phase3_5_enriched.json'"
    step_done "import"
fi

# -------------------- Step 6: 分级 --------------------
if should_skip "tier"; then
    log "⏭️  [跳过] 分级（已完成）"
else
    log ""; log "=============================="; log "🏆 分级: Tier S/A/B/C 评分"; log "=============================="
    run_with_retry "Tier 评分" \
        bash -c "cd '${HEADHUNTER_DIR}' && python3 batch_update_tiers.py"
    step_done "tier"
fi

# ======================== 验证 + 批次报告 ========================
log ""; log "=============================="; log "🔍 最终验证 + 批次报告"; log "=============================="

REPORT_FILE="${BATCH_DIR}/batch_report.json"
COMPLETED_AT="$(date '+%Y-%m-%d %H:%M:%S')"

python3 -c "
import json, os, sys
sys.path.insert(0, '${HEADHUNTER_DIR}')
os.chdir('${HEADHUNTER_DIR}')

report = {
    'batch_id': '${BATCH_NAME}',
    'started_at': '$(head -n 5 ${LOG_FILE} | grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}' | head -1 2>/dev/null || echo 'unknown')',
    'completed_at': '${COMPLETED_AT}',
    'source': 'new_seed_pipeline',
    'seed_user': '${BATCH_NAME}',
    'phases': {}
}

data_dir = '${DATA_DIR}'

# Phase 1
p1f = os.path.join(data_dir, 'phase1_seed_users.json')
if os.path.exists(p1f):
    p1 = json.load(open(p1f))
    report['phases']['phase1'] = {'total': len(p1)}
    print(f'  Phase 1: {len(p1)} 人')

# Phase 2 V3
p2f = os.path.join(data_dir, 'phase2_v3_enriched.json')
if os.path.exists(p2f):
    p2 = json.load(open(p2f))
    has_email = sum(1 for u in p2 if u.get('all_emails'))
    has_py = sum(1 for u in p2 if u.get('has_python'))
    has_scholar = sum(1 for u in p2 if u.get('has_scholar'))
    has_website = sum(1 for u in p2 if u.get('website_status') == 'active')
    report['phases']['phase2_v3'] = {
        'total': len(p2),
        'has_email': has_email,
        'has_python': has_py,
        'has_scholar': has_scholar,
        'has_active_website': has_website,
    }
    print(f'  Phase 2 V3: {len(p2)} 人, Email={has_email}, Python={has_py}, Scholar={has_scholar}')

# Phase 3 V3
p3f = os.path.join(data_dir, 'phase3_v3_ai_candidates.json')
p3rf = os.path.join(data_dir, 'phase3_v3_rejected.json')
if os.path.exists(p3f):
    p3 = json.load(open(p3f))
    p3r = json.load(open(p3rf)) if os.path.exists(p3rf) else []
    total = len(p3) + len(p3r)
    report['phases']['phase3_v3'] = {
        'ai_candidates': len(p3),
        'rejected': len(p3r),
        'ai_rate': f'{len(p3)*100//max(total,1)}%',
    }
    print(f'  Phase 3 V3: AI={len(p3)} ({len(p3)*100//max(total,1)}%), 非AI={len(p3r)}')

# Phase 3.5
p35f = os.path.join(data_dir, 'phase3_5_enriched.json')
if os.path.exists(p35f):
    p35 = json.load(open(p35f))
    scraped = sum(1 for u in p35 if u.get('homepage_scraped'))
    has_li = sum(1 for u in p35 if u.get('linkedin_url'))
    has_work = sum(1 for u in p35 if u.get('work_experience'))
    report['phases']['phase3_5'] = {
        'total': len(p35),
        'homepage_success': scraped,
        'linkedin_found': has_li,
        'work_experience': has_work,
    }
    print(f'  Phase 3.5: {len(p35)} 人, 主页={scraped}, LinkedIn={has_li}')

# 数据库快照
try:
    from database import SessionLocal, Candidate
    from collections import Counter
    session = SessionLocal()
    all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
    tier_dist = Counter(c.talent_tier for c in all_gh)
    has_li_db = sum(1 for c in all_gh if c.linkedin_url)
    untiered = tier_dist.get(None, 0)

    report['phases']['tier'] = {t: tier_dist.get(t, 0) for t in ['S', 'A', 'A+', 'B', 'B+', 'C', 'D'] if tier_dist.get(t, 0) > 0}
    report['db_snapshot'] = {
        'total_github': len(all_gh),
        'total_linkedin': has_li_db,
        'untiered': untiered,
    }

    print(f'  DB: {len(all_gh)} GitHub候选人, {has_li_db} 有LinkedIn')
    for t in ['S', 'A', 'B', 'C']:
        print(f'    {t}: {tier_dist.get(t, 0)} 人')
    if untiered > 0:
        print(f'    ⚠️  未分级: {untiered} 人')
    else:
        print('  ✅ 全部已分级')
    session.close()
except Exception as e:
    print(f'  ⚠️  数据库查询失败: {e}')

json.dump(report, open('${REPORT_FILE}', 'w'), indent=2, ensure_ascii=False)
print(f'  📄 批次报告已保存: ${REPORT_FILE}')
"

log ""
log "============================================================"
log "🎉 Pipeline [${BATCH_NAME}] 执行完毕！"
log "   📄 批次报告: ${REPORT_FILE}"
log "   批次数据存档: ${BATCH_DIR}"
log "   下一步: 针对新入库 S/A 候选人启动触达"
log "   命令: cd personal-ai-headhunter && python3 scripts/batch_ai_outreach.py --tiers S,A"
log "============================================================"

