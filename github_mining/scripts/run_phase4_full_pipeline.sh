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
#   4. 按文件使用种子（JSON array of usernames）:
#      SEED_FILE=seed_today_sa.json bash github_mining/scripts/run_phase4_full_pipeline.sh
#
#   5. 按 Tier 选种子（从数据库选 S/A 级别）:
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
MIN_CO="${MIN_CO:-2}"
SEED_TIER="${SEED_TIER:-}"
SEED_FILE="${SEED_FILE:-}"
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
        'tier': '${SEED_TIER:-}',
        'seed_top': ${SEED_TOP},
        'seed_file': '${SEED_FILE:-}',
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
log "   SEED_FILE:  ${SEED_FILE:-（未使用）}"
log "   SEED_TIER:  ${SEED_TIER:-（未使用）}"
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
    if [[ -n "${SEED_FILE}" ]]; then
        P4_CMD="${P4_CMD} --seeds-file ${SEED_FILE}"
    elif [[ -n "${SEED_TIER}" ]]; then
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

# ==================== 批次级统计 + 入库 ====================
log ""
log "=============================="
log "📊 批次级数据统计 + 入库"
log "=============================="

python3 -c "
import json, os, sys
from datetime import datetime
from collections import Counter

sys.path.insert(0, '${HEADHUNTER_DIR}')
os.chdir('${HEADHUNTER_DIR}')

report_f = '${REPORT_FILE}'
report = json.load(open(report_f))
data_dir = '${DATA_DIR}'
batch_id = '${BATCH_ID}'

# ===== 1. 收集 Phase 中间数据 =====
p3f = os.path.join(data_dir, 'phase3_from_phase4.json')
if os.path.exists(p3f):
    p3 = json.load(open(p3f))
    report['phases']['phase3_enrich'] = {
        'total': len(p3),
        'has_stars': sum(1 for u in p3 if u.get('total_stars') is not None),
        'has_email': sum(1 for u in p3 if u.get('all_emails')),
    }

for fname in ['phase4_final_enriched.json', 'phase3_5_enriched.json']:
    ff = os.path.join(data_dir, fname)
    if os.path.exists(ff):
        d = json.load(open(ff))
        report['phases']['phase3_5_scrape'] = {
            'total': len(d),
            'homepage_success': sum(1 for u in d if u.get('homepage_scraped')),
            'linkedin_found': sum(1 for u in d if u.get('linkedin_url')),
        }
        break

# ===== 2. 查询本批次入库的候选人（今日新增的 GitHub 源）=====
from database import SessionLocal, Candidate, BatchRun, Base, engine
Base.metadata.create_all(bind=engine)

session = SessionLocal()
today = datetime.now().strftime('%Y-%m-%d')
batch_candidates = session.query(Candidate).filter(
    Candidate.source == 'github',
    Candidate.created_at >= today
).all()

total_input = report.get('phases', {}).get('phase4_crawl', {}).get('total', 0)
total_imported = len(batch_candidates)

# 评级分布（本批次）
tier_dist = Counter(c.talent_tier for c in batch_candidates)

# 可联系信息（本批次）
has_email = sum(1 for c in batch_candidates if c.email)
has_linkedin = sum(1 for c in batch_candidates if c.linkedin_url)
has_github = sum(1 for c in batch_candidates if c.github_url)
has_phone = sum(1 for c in batch_candidates if c.phone)
has_website = sum(1 for c in batch_candidates if c.personal_website)

# 全局 DB 快照
all_count = session.query(Candidate).count()
gh_count = session.query(Candidate).filter(Candidate.source == 'github').count()
li_count = session.query(Candidate).filter(Candidate.linkedin_url != None).count()

# ===== 3. 更新 JSON 报告 =====
report['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
report['batch_stats'] = {
    'total_input': total_input,
    'total_imported': total_imported,
    'import_rate': f'{total_imported*100//max(total_input,1)}%',
    'tier': {t: tier_dist.get(t, 0) for t in ['S','A+','A','B+','B','C','D'] if tier_dist.get(t, 0)>0},
    'contact': {'email': has_email, 'linkedin': has_linkedin, 'github': has_github, 'phone': has_phone, 'website': has_website},
}
report['db_snapshot'] = {'total': all_count, 'github': gh_count, 'linkedin': li_count}
json.dump(report, open(report_f, 'w'), indent=2, ensure_ascii=False)

# ===== 4. 写入 batch_runs 表 =====
existing = session.query(BatchRun).filter(BatchRun.batch_id == batch_id).first()
if not existing:
    run = BatchRun(
        batch_id=batch_id,
        source=report.get('source', 'phase4_social_expansion'),
        started_at=datetime.strptime(report['started_at'], '%Y-%m-%d %H:%M:%S') if report.get('started_at') else None,
        completed_at=datetime.now(),
        seed_config=report.get('seed_config'),
        phase_data=report.get('phases'),
        total_input=total_input,
        total_imported=total_imported,
        tier_s=tier_dist.get('S', 0),
        tier_a_plus=tier_dist.get('A+', 0),
        tier_a=tier_dist.get('A', 0),
        tier_b_plus=tier_dist.get('B+', 0),
        tier_b=tier_dist.get('B', 0),
        tier_c=tier_dist.get('C', 0),
        tier_d=tier_dist.get('D', 0),
        has_email=has_email,
        has_linkedin=has_linkedin,
        has_github=has_github,
        has_phone=has_phone,
        has_website=has_website,
        db_total_candidates=all_count,
        db_total_github=gh_count,
        db_total_linkedin=li_count,
    )
    session.add(run)
    session.commit()
    print(f'  ✅ 已写入 batch_runs 表 (id={run.id})')
else:
    print(f'  ⚠️ 批次 {batch_id} 已存在，跳过写入')

# ===== 5. 打印汇总 =====
print(f'')
print(f'  📊 批次 [{batch_id}] 数据报告')
print(f'  输入: {total_input} 人 → 入库: {total_imported} 人 ({total_imported*100//max(total_input,1)}%)')
print(f'  评级: S={tier_dist.get(\"S\",0)} A={tier_dist.get(\"A\",0)} B+={tier_dist.get(\"B+\",0)} B={tier_dist.get(\"B\",0)} C={tier_dist.get(\"C\",0)}')
print(f'  联系: Email={has_email} LinkedIn={has_linkedin} Website={has_website} Phone={has_phone}')
print(f'  DB全局: {all_count} 总候选人, {gh_count} GitHub, {li_count} LinkedIn')
print(f'  📄 JSON报告: {report_f}')

session.close()
"

log ""
log "============================================================"
log "🎉 Phase 4 全链路 Pipeline [${BATCH_ID}] 执行完毕！"
log "   📄 批次报告: ${REPORT_FILE}"
log "   建议下一步: 针对新增 S/A 候选人启动触达"
log "   命令: cd personal-ai-headhunter && python3 scripts/batch_ai_outreach.py --tiers S,A"
log "============================================================"

