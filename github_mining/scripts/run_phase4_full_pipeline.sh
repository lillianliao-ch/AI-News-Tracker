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
#
# 批次报告:
#   每次运行完成后自动生成 batch_report_phase4_{timestamp}.json
#   包含每个阶段的关键指标，可用于数据源质量比对
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
# 流水线状态文件（本脚本自身的状态）
PIPELINE_STATE="${DATA_DIR}/pipeline_state_phase4.json"
# enrichment 脚本使用的状态文件（需要在新批次时重置）
ENRICHMENT_STATE="${DATA_DIR}/pipeline_state.json"
LOG_FILE="${DATA_DIR}/pipeline_phase4_full.log"

# 批次标识
BATCH_TS="$(date +%Y%m%d_%H%M%S)"
BATCH_ID="phase4_${BATCH_TS}"
REPORT_FILE="${DATA_DIR}/batch_report_${BATCH_ID}.json"

# Phase 4 爬取参数
SEED_TOP="${SEED_TOP:-300}"
MIN_CO="${MIN_CO:-3}"
SEED_TIER="${SEED_TIER:-}"
SKIP_PHASE4="${SKIP_PHASE4:-0}"

# 流程开始时间
STARTED_AT="$(date '+%Y-%m-%d %H:%M:%S')"

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

# 记录阶段数据到报告
record_phase() {
    local phase_name="$1"
    shift
    # 接受 key=value 形式的参数
    python3 -c "
import json, os
f = '${REPORT_FILE}'
d = json.load(open(f)) if os.path.exists(f) else {}
if 'phases' not in d: d['phases'] = {}
phase = d['phases'].get('${phase_name}', {})
pairs = '''$*'''.strip().split()
for pair in pairs:
    if '=' in pair:
        k, v = pair.split('=', 1)
        try:
            v = int(v)
        except:
            try:
                v = float(v)
            except:
                pass
        phase[k] = v
d['phases']['${phase_name}'] = phase
json.dump(d, open(f,'w'), indent=2, ensure_ascii=False)
"
}

# ======================== 主流程 ========================
mkdir -p "${DATA_DIR}"

# 初始化批次报告
python3 -c "
import json
report = {
    'batch_id': '${BATCH_ID}',
    'started_at': '${STARTED_AT}',
    'source': 'phase4_social_expansion',
    'seed_config': {
        'tier': '${SEED_TIER:-file_top}',
        'seed_top': ${SEED_TOP},
        'min_cooccurrence': ${MIN_CO}
    },
    'phases': {}
}
json.dump(report, open('${REPORT_FILE}', 'w'), indent=2, ensure_ascii=False)
"

log ""
log "============================================================"
log "🚀 Phase 4 全链路 Pipeline 启动"
log "   BATCH_ID:   ${BATCH_ID}"
log "   NOTION_RAG: ${NOTION_RAG_DIR}"
log "   SEED_TOP:   ${SEED_TOP}"
log "   MIN_CO:     ${MIN_CO}"
log "   SEED_TIER:  ${SEED_TIER:-（从文件取 Top ${SEED_TOP}）}"
log "   SKIP_P4:    ${SKIP_PHASE4}"
log "   REPORT:     ${REPORT_FILE}"
log "============================================================"

# ==================== Step 1: Phase 4 社交网络扩展爬取 ====================
if [[ "${SKIP_PHASE4}" == "1" ]]; then
    log "⏭️  [跳过] Phase 4 爬取（SKIP_PHASE4=1）"
    if [[ ! -f "${PHASE4_OUTPUT}" ]]; then
        log "❌ 找不到 ${PHASE4_OUTPUT}，且 SKIP_PHASE4=1。请先手动运行 Phase 4 爬取。"
        exit 1
    fi
    PHASE4_COUNT=$(python3 -c "import json; print(len(json.load(open('${PHASE4_OUTPUT}'))))")
    record_phase "phase4_crawl" "status=skipped total=${PHASE4_COUNT}"
elif [[ "$(step_is_done phase4_crawl)" == "true" ]]; then
    log "⏭️  [跳过] Phase 4 爬取（State 已记录完成）"
    # 确保变量有值（断点续传场景）
    if [[ -f "${PHASE4_OUTPUT}" ]]; then
        PHASE4_COUNT=$(python3 -c "import json; print(len(json.load(open('${PHASE4_OUTPUT}'))))")
        log "   已有 Phase 4 数据: ${PHASE4_COUNT} 人"
    fi
else
    log ""
    log "=============================="
    log "🕸️  Phase 4: 社交网络扩展爬取"
    log "=============================="

    P4_CMD="python3 ${MINING_SCRIPTS}/github_network_miner.py phase4 --seed-top ${SEED_TOP} --min-cooccurrence ${MIN_CO}"
    if [[ -n "${SEED_TIER}" ]]; then
        P4_CMD="${P4_CMD} --seed-tier ${SEED_TIER}"
    fi

    run_with_retry "Phase 4 社交网络扩展爬取" bash -c "${P4_CMD}"
    step_done "phase4_crawl"

    if [[ ! -f "${PHASE4_OUTPUT}" ]]; then
        log "❌ Phase 4 产出文件不存在: ${PHASE4_OUTPUT}"
        exit 1
    fi
    PHASE4_COUNT=$(python3 -c "import json; print(len(json.load(open('${PHASE4_OUTPUT}'))))")
    log "📊 Phase 4 扩展发现: ${PHASE4_COUNT} 人 → ${PHASE4_OUTPUT}"
    record_phase "phase4_crawl" "total=${PHASE4_COUNT}"

    # ==================== 关键：重置 enrichment 状态 ====================
    # 新的 Phase 4 数据到来时，必须重置 enrichment 的状态文件
    # 否则旧批次的 "all done" 状态会导致新数据被跳过
    if [[ -f "${ENRICHMENT_STATE}" ]]; then
        log ""
        log "🔄 检测到旧的 enrichment 状态文件，自动重置..."
        log "   旧状态: $(cat ${ENRICHMENT_STATE})"
        cp "${ENRICHMENT_STATE}" "${ENRICHMENT_STATE}.bak_${BATCH_TS}"
        echo '{"phase3_done": false, "phase3_verified": false, "phase3_5_done": false, "phase3_5_verified": false, "import_done": false, "tier_done": false}' > "${ENRICHMENT_STATE}"
        log "   ✅ 已重置 enrichment 状态"
    fi

    # 清理旧的中间产出文件，避免新旧数据混淆
    for old_file in "phase3_from_phase4.json" "phase4_final_enriched.json"; do
        if [[ -f "${DATA_DIR}/${old_file}" ]]; then
            mv "${DATA_DIR}/${old_file}" "${DATA_DIR}/${old_file}.bak_${BATCH_TS}"
            log "   🔄 已备份旧中间文件: ${old_file}"
        fi
    done
fi

# ==================== Step 2+: 富化 → 入库 → 分级 ====================
log ""
log "=============================="
log "🔬 启动富化/入库/分级流水线"
log "=============================="
log "复用 run_phase4_enrichment.py（内置断点续传 + 验证 + 自动重启）"

run_with_retry "Phase 4 富化→入库→分级全流程" \
    python3 "${MINING_SCRIPTS}/auto_restart_wrapper.py" -- \
    python3 "${MINING_SCRIPTS}/run_phase4_enrichment.py"

step_done "enrichment_done"

# ==================== 收集各阶段关键数据 ====================
log ""
log "=============================="
log "📊 收集各阶段关键数据"
log "=============================="

python3 -c "
import json, os, sys
sys.path.insert(0, '${HEADHUNTER_DIR}')
os.chdir('${HEADHUNTER_DIR}')

report_f = '${REPORT_FILE}'
report = json.load(open(report_f))
data_dir = '${DATA_DIR}'

# Phase 3 数据
p3f = os.path.join(data_dir, 'phase3_from_phase4.json')
if os.path.exists(p3f):
    p3 = json.load(open(p3f))
    has_stars = sum(1 for u in p3 if u.get('total_stars') is not None)
    has_email = sum(1 for u in p3 if u.get('all_emails'))
    has_langs = sum(1 for u in p3 if u.get('primary_languages'))
    report['phases']['phase3_enrich'] = {
        'total': len(p3),
        'stars_coverage': f'{has_stars*100//max(len(p3),1)}%',
        'email_coverage': f'{has_email*100//max(len(p3),1)}%',
        'language_coverage': f'{has_langs*100//max(len(p3),1)}%',
    }
    print(f'  Phase 3: {len(p3)} 人, Stars={has_stars}, Email={has_email}')

# Phase 3.5 / Final 数据
for fname, label in [('phase4_final_enriched.json', 'phase3_5'), ('phase3_5_enriched.json', 'phase3_5')]:
    ff = os.path.join(data_dir, fname)
    if os.path.exists(ff):
        d = json.load(open(ff))
        scraped = sum(1 for u in d if u.get('homepage_scraped'))
        has_li = sum(1 for u in d if u.get('linkedin_url'))
        has_work = sum(1 for u in d if u.get('work_experience'))
        has_edu = sum(1 for u in d if u.get('education'))
        report['phases']['phase3_5_scrape'] = {
            'total': len(d),
            'homepage_success': scraped,
            'linkedin_found': has_li,
            'work_experience': has_work,
            'education': has_edu,
        }
        print(f'  Phase 3.5: {len(d)} 人, 主页={scraped}, LinkedIn={has_li}')
        break

# 数据库快照
try:
    from database import SessionLocal, Candidate
    from collections import Counter
    session = SessionLocal()
    all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
    tier_dist = Counter(c.talent_tier for c in all_gh)
    has_li_db = sum(1 for c in all_gh if c.linkedin_url)
    report['phases']['tier'] = {t: tier_dist.get(t, 0) for t in ['S', 'A', 'A+', 'B', 'B+', 'C', 'D'] if tier_dist.get(t, 0) > 0}
    report['db_snapshot'] = {
        'total_github': len(all_gh),
        'total_linkedin': has_li_db,
    }
    print(f'  DB: {len(all_gh)} GitHub候选人, {has_li_db} 有LinkedIn')
    session.close()
except Exception as e:
    print(f'  ⚠️  数据库查询失败: {e}')

from datetime import datetime
report['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

json.dump(report, open(report_f, 'w'), indent=2, ensure_ascii=False)
print(f'  📄 报告已保存: {report_f}')
"

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
log "🎉 Phase 4 全链路 Pipeline [${BATCH_ID}] 执行完毕！"
log "   📄 批次报告: ${REPORT_FILE}"
log "   建议下一步: 针对新增 S/A 候选人启动触达"
log "   命令: cd personal-ai-headhunter && python3 scripts/batch_ai_outreach.py --tiers S,A"
log "============================================================"
