#!/bin/bash
# ======================================================================
# Academic Pipeline Orchestrator
# ======================================================================
# 全自动学术流水线：一条命令跑完一个年度的全流程
#
# 用法:
#   ./scripts/academic_pipeline.sh --year 2025 --phase all
#   ./scripts/academic_pipeline.sh --year 2023 --phase deep   # 从 deep 开始
#   ./scripts/academic_pipeline.sh --year 2025 --phase serper --tiers "C"
#
# 环境变量:
#   S2_API_KEY       — Semantic Scholar API Key
#   TELEGRAM_BOT_TOKEN — Telegram 通知 (可选)
#   TELEGRAM_CHAT_ID   — Telegram Chat ID (可选)
# ======================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HEADHUNTER_DIR="$(dirname "$PROJECT_DIR")/personal-ai-headhunter"
DB_PATH="${HEADHUNTER_DIR}/data/headhunter_dev.db"

# ===== 参数 =====
YEAR=""
PHASE="all"
TIERS=""
DRY_RUN=""
CONFERENCES="ICLR ACL NeurIPS ICML CVPR"
EXPLICIT_RUN_DIR=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --year) YEAR="$2"; shift 2 ;;
    --phase) PHASE="$2"; shift 2 ;;
    --tiers) TIERS="$2"; shift 2 ;;
    --dry-run) DRY_RUN="--dry-run"; shift ;;
    --conferences) CONFERENCES="$2"; shift 2 ;;
    --run-dir) EXPLICIT_RUN_DIR="$2"; shift 2 ;;
    *) echo "❌ 未知参数: $1"; exit 1 ;;
  esac
done

if [[ -z "$YEAR" ]]; then
  echo "❌ 必须指定 --year"
  echo "用法: $0 --year 2025 [--phase all|miner|s2|serper|pdf|deep|llm|import] [--tiers S,A+,A,B] [--run-dir <dir>]"
  exit 1
fi

# ===== 目录设置 =====
if [[ -n "$EXPLICIT_RUN_DIR" ]]; then
  RUN_DIR="$EXPLICIT_RUN_DIR"
  echo "📂 使用指定目录: $RUN_DIR"
elif [[ "$PHASE" != "all" && "$PHASE" != "miner" ]]; then
  # 从中间步骤开始时，查找最新的 run 目录
  EXISTING_RUN=$(ls -dt "${PROJECT_DIR}/data/academic/runs/"*"${YEAR}"* 2>/dev/null | head -1)
  if [[ -n "$EXISTING_RUN" ]]; then
    RUN_DIR="$EXISTING_RUN"
    echo "📂 使用已有批次目录: $RUN_DIR"
  else
    RUN_DIR="${PROJECT_DIR}/data/academic/runs/pipeline_${YEAR}_$(date +%Y%m%d_%H%M%S)"
  fi
else
  RUN_DIR="${PROJECT_DIR}/data/academic/runs/pipeline_${YEAR}_$(date +%Y%m%d_%H%M%S)"
fi

OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
CACHE_DIR="${OUTPUT_DIR}"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

# ===== 工具函数 =====

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_DIR}/pipeline.log"
}

notify() {
  local msg="$1"
  log "📨 $msg"
  
  if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_CHAT_ID:-}" ]]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TELEGRAM_CHAT_ID}" \
      -d text="🎓 Academic Pipeline [${YEAR}]
${msg}" \
      -d parse_mode="Markdown" > /dev/null 2>&1 || true
  fi
}

# 查找最新的 full.json
find_full_json() {
  # 先在 outputs 目录找
  local found=$(ls -t ${OUTPUT_DIR}/all_conf_${YEAR}_*_full.json 2>/dev/null | head -1)
  # 如果没有，在整个 runs 目录下所有含 YEAR 的目录中找
  if [[ -z "$found" ]]; then
    found=$(find "${PROJECT_DIR}/data/academic/runs/" -name "all_conf_${YEAR}_*_full.json" -type f 2>/dev/null | head -1)
  fi
  echo "$found"
}

# 查找缓存文件 (兼容不同命名: _serper_cache.json / serper_cache_2025.json / all_conf_2025_contact_cache.json)
find_cache() {
  local cache_type="$1"  # serper | deep | enrichment | llm
  
  # 按优先级尝试多种命名
  local candidates=()
  case "$cache_type" in
    serper)
      candidates=(
        "${CACHE_DIR}/_serper_cache.json"
        "${CACHE_DIR}/serper_cache_${YEAR}.json"
        "${CACHE_DIR}/all_conf_${YEAR}_contact_cache.json"
      ) ;;
    deep)
      candidates=(
        "${CACHE_DIR}/_deep_cache.json"
        "${CACHE_DIR}/deep_cache_${YEAR}.json"
      ) ;;
    enrichment)
      candidates=(
        "${CACHE_DIR}/_enrichment_cache.json"
        "${CACHE_DIR}/enrichment_cache_${YEAR}.json"
      ) ;;
    llm)
      candidates=(
        "${CACHE_DIR}/_llm_enrichment_results.json"
        "${CACHE_DIR}/llm_enrichment_${YEAR}.json"
      ) ;;
  esac
  
  for f in "${candidates[@]}"; do
    if [[ -f "$f" ]]; then
      echo "$f"
      return
    fi
  done
  # 如果都不存在，返回第一个候选 (新建时用)
  echo "${candidates[0]}"
}

# 质量检查
quality_check() {
  local full_json="$1"
  local step_name="$2"
  
  python3 -c "
import json, sys

with open('${full_json}') as f:
    data = json.load(f)

serper_cache = {}
try:
    import glob
    cache_files = glob.glob('${CACHE_DIR}/*serper*cache*.json')
    for cf in cache_files:
        with open(cf) as f:
            serper_cache.update(json.load(f))
except: pass

pdf_cache = {}
try:
    cache_files = glob.glob('${CACHE_DIR}/*enrichment*cache*.json')
    for cf in cache_files:
        with open(cf) as f:
            pdf_cache.update(json.load(f))
except: pass

total = len(data)
has_email = sum(1 for a in data if a.get('email') or 
    serper_cache.get(a.get('name',''), {}).get('emails') or
    pdf_cache.get(a.get('name',''), {}).get('email'))
has_homepage = sum(1 for a in data if a.get('personal_website') or 
    serper_cache.get(a.get('name',''), {}).get('homepage_url'))
has_github = sum(1 for a in data if a.get('github_url') or 
    serper_cache.get(a.get('name',''), {}).get('github_url'))

by_tier = {}
for a in data:
    t = a.get('tier', 'C')
    if t not in by_tier: by_tier[t] = {'total': 0, 'email': 0, 'homepage': 0}
    by_tier[t]['total'] += 1
    name = a.get('name', '')
    if a.get('email') or serper_cache.get(name, {}).get('emails') or pdf_cache.get(name, {}).get('email'):
        by_tier[t]['email'] += 1
    if a.get('personal_website') or serper_cache.get(name, {}).get('homepage_url'):
        by_tier[t]['homepage'] += 1

print(f'📊 质量报告 [{step_name}]')
print(f'   总人数: {total}')
print(f'   邮箱: {has_email} ({has_email*100//max(total,1)}%)')
print(f'   主页: {has_homepage} ({has_homepage*100//max(total,1)}%)')
print(f'   GitHub: {has_github} ({has_github*100//max(total,1)}%)')
for t in ['S','A+','A','B','C']:
    if t in by_tier:
        d = by_tier[t]
        print(f'   [{t:2s}] {d[\"total\"]:5d} | email {d[\"email\"]*100//max(d[\"total\"],1):2d}% | homepage {d[\"homepage\"]*100//max(d[\"total\"],1):2d}%')
" 2>&1 | tee -a "${LOG_DIR}/pipeline.log"
}

# 判断是否应该运行某个 phase
should_run() {
  local step="$1"
  local phases=("miner" "s2" "serper" "pdf" "deep" "llm" "import")
  
  if [[ "$PHASE" == "all" ]]; then
    return 0
  fi
  
  local phase_idx=-1
  local step_idx=-1
  for i in "${!phases[@]}"; do
    [[ "${phases[$i]}" == "$PHASE" ]] && phase_idx=$i
    [[ "${phases[$i]}" == "$step" ]] && step_idx=$i
  done
  
  [[ $step_idx -ge $phase_idx ]]
}

# ===== PIPELINE 开始 =====

log "============================================================"
log "🚀 Academic Pipeline 启动"
log "   年份: ${YEAR}"
log "   起始: ${PHASE}"
log "   目录: ${RUN_DIR}"
log "============================================================"
notify "🚀 Pipeline 启动 (year=${YEAR}, phase=${PHASE})"

PIPELINE_START=$(date +%s)

# ----- Step 1: 论文采集 -----
if should_run "miner"; then
  log "📝 Step 1/7: 论文采集"
  
  for CONF in $CONFERENCES; do
    log "  → ${CONF} ${YEAR}"
    python3 "${SCRIPT_DIR}/academic_miner.py" \
      --conference "$CONF" --year "$YEAR" \
      --output-dir "$OUTPUT_DIR" \
      >> "${LOG_DIR}/miner.log" 2>&1
    
    if [[ $? -ne 0 ]]; then
      notify "❌ Step 1 失败: ${CONF} 采集出错"
      exit 1
    fi
  done
  
  # 合并各会议 JSON
  FULL_JSON=$(find_full_json)
  if [[ -z "$FULL_JSON" ]]; then
    log "  合并各会议文件..."
    python3 -c "
import json, glob
all_authors = {}
for f in glob.glob('${OUTPUT_DIR}/*${YEAR}*.json'):
    with open(f) as fh:
        for a in json.load(fh):
            key = a.get('name', '')
            if key and key not in all_authors:
                all_authors[key] = a
            elif key in all_authors:
                # merge conferences
                existing_confs = all_authors[key].get('conferences', [])
                new_confs = a.get('conferences', [])
                all_authors[key]['conferences'] = list(set(existing_confs + new_confs))
result = list(all_authors.values())
out = '${OUTPUT_DIR}/all_conf_${YEAR}_$(date +%Y%m%d_%H%M%S)_full.json'
with open(out, 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f'合并完成: {len(result)} 人 → {out}')
" >> "${LOG_DIR}/miner.log" 2>&1
  fi
  
  FULL_JSON=$(find_full_json)
  TOTAL=$(python3 -c "import json; print(len(json.load(open('${FULL_JSON}'))))")
  log "  ✅ Step 1 完成: ${TOTAL} 人"
  notify "✅ Step 1 完成: ${TOTAL} 人采集"
fi

# ----- Step 2: S2 富化 -----
if should_run "s2"; then
  FULL_JSON=$(find_full_json)
  log "📚 Step 2/7: S2 富化"
  
  if [[ -z "${S2_API_KEY:-}" ]]; then
    log "  ⚠️ 未设置 S2_API_KEY, 跳过 S2 富化"
    notify "⚠️ Step 2 跳过: 未设置 S2_API_KEY"
  else
    S2_API_KEY="${S2_API_KEY}" python3 "${SCRIPT_DIR}/academic_miner.py" \
      --input "$FULL_JSON" --score-only \
      --output-dir "$OUTPUT_DIR" \
      >> "${LOG_DIR}/s2_enrich.log" 2>&1
    
    FULL_JSON=$(find_full_json)
    log "  ✅ Step 2 完成"
    quality_check "$FULL_JSON" "S2 富化后"
    notify "✅ Step 2 完成: S2 富化"
  fi
fi

# ----- Step 3: Serper 搜索 -----
if should_run "serper"; then
  FULL_JSON=$(find_full_json)
  SERPER_CACHE=$(find_cache serper)
  log "🔍 Step 3/7: Serper 搜索"
  log "  缓存: $SERPER_CACHE"
  
  # B+ 级
  if [[ -z "$TIERS" || "$TIERS" == *"B"* || "$TIERS" == *"A"* || "$TIERS" == *"S"* ]]; then
    log "  → B+ 级 (S,A+,A,B)"
    "${SCRIPT_DIR}/serper_auto_retry.sh" \
      --input "$FULL_JSON" \
      --cache "$SERPER_CACHE" \
      --output "$OUTPUT_DIR" \
      --tiers "S,A+,A,B" \
      --log "${LOG_DIR}/serper_bplus.log"
    log "  ✅ B+ 级 Serper 完成"
  fi
  
  # C 级 (串行，避免缓存冲突)
  if [[ -z "$TIERS" || "$TIERS" == *"C"* ]]; then
    log "  → C 级"
    "${SCRIPT_DIR}/serper_auto_retry.sh" \
      --input "$FULL_JSON" \
      --cache "$SERPER_CACHE" \
      --output "$OUTPUT_DIR" \
      --tiers "C" \
      --log "${LOG_DIR}/serper_c.log"
    log "  ✅ C 级 Serper 完成"
  fi
  
  quality_check "$FULL_JSON" "Serper 后"
  notify "✅ Step 3 完成: Serper 搜索"
fi

# ----- Step 4: PDF 邮箱提取 -----
if should_run "pdf"; then
  FULL_JSON=$(find_full_json)
  PDF_CACHE=$(find_cache enrichment)
  log "📄 Step 4/7: PDF 邮箱提取"
  log "  缓存: $PDF_CACHE"
  
  python3 "${SCRIPT_DIR}/academic_contact_enricher.py" \
    --input "$FULL_JSON" \
    --output "$OUTPUT_DIR" \
    --cache "$PDF_CACHE" \
    --pdf-only \
    >> "${LOG_DIR}/pdf_email.log" 2>&1
  
  log "  ✅ Step 4 完成"
  quality_check "$FULL_JSON" "PDF 邮箱后"
  notify "✅ Step 4 完成: PDF 邮箱提取"
fi

# ----- Step 5: Deep 爬取 -----
if should_run "deep"; then
  FULL_JSON=$(find_full_json)
  SERPER_CACHE=$(find_cache serper)
  DEEP_CACHE=$(find_cache deep)
  log "🕸️ Step 5/7: Deep 爬取 (主页 + GitHub)"
  log "  Serper缓存: $SERPER_CACHE"
  log "  Deep缓存: $DEEP_CACHE"
  
  python3 "${SCRIPT_DIR}/academic_deep_enrich.py" \
    --input "$FULL_JSON" \
    --serper-cache "$SERPER_CACHE" \
    --output-dir "$OUTPUT_DIR" \
    --cache "$DEEP_CACHE" \
    --mode all --workers 10 \
    >> "${LOG_DIR}/deep_enrich.log" 2>&1
  
  log "  ✅ Step 5 完成"
  notify "✅ Step 5 完成: Deep 爬取"
fi

# ----- Step 6: LLM 富化 -----
if should_run "llm"; then
  FULL_JSON=$(find_full_json)
  SERPER_CACHE=$(find_cache serper)
  DEEP_CACHE=$(find_cache deep)
  LLM_CACHE=$(find_cache llm)
  log "🤖 Step 6/7: LLM 富化"
  log "  Deep缓存: $DEEP_CACHE"
  log "  LLM输出: $LLM_CACHE"
  
  python3 "${SCRIPT_DIR}/academic_llm_enrich.py" \
    --deep-cache "$DEEP_CACHE" \
    --serper-cache "$SERPER_CACHE" \
    --input "$FULL_JSON" \
    --output "$LLM_CACHE" \
    --workers 5 \
    >> "${LOG_DIR}/llm_enrich.log" 2>&1
  
  log "  ✅ Step 6 完成"
  notify "✅ Step 6 完成: LLM 富化"
fi

# ----- Step 7: 入库 -----
if should_run "import"; then
  FULL_JSON=$(find_full_json)
  log "📦 Step 7/7: 入库"
  
  DB_PATH="$DB_PATH" python3 "${SCRIPT_DIR}/academic_import.py" \
    --input "$FULL_JSON" \
    --update ${DRY_RUN} \
    >> "${LOG_DIR}/import.log" 2>&1
  
  log "  ✅ Step 7 完成"
  notify "✅ Step 7 完成: 入库"
fi

# ===== 完成 =====
PIPELINE_END=$(date +%s)
DURATION=$(( (PIPELINE_END - PIPELINE_START) / 60 ))

log ""
log "============================================================"
log "🎉 Pipeline 全部完成！"
log "   年份: ${YEAR}"
log "   耗时: ${DURATION} 分钟"
log "   目录: ${RUN_DIR}"
log "============================================================"

FULL_JSON=$(find_full_json)
if [[ -n "$FULL_JSON" ]]; then
  quality_check "$FULL_JSON" "最终报告"
fi

notify "🎉 Pipeline 完成！耗时 ${DURATION} 分钟。请查看 ${LOG_DIR}/pipeline.log"
