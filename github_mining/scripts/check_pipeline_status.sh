#!/bin/bash
# ============================================================
# Pipeline Completion Check — 定时检查 Task 10 & 11 完成情况
# 用法: 直接运行或 at/sleep 调度
# ============================================================

LOG_FILE="/Users/lillianliao/notion_rag/github_mining/data/academic/pipeline_check_$(date +%Y%m%d_%H%M%S).log"
HEADHUNTER_DIR="/Users/lillianliao/notion_rag/personal-ai-headhunter"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_telegram() {
  local msg="$1"
  python3 -c "
import sys
sys.path.insert(0, '${HEADHUNTER_DIR}')
from telegram_notifier import notify
notify('''$msg''')
" 2>/dev/null || echo "⚠️ Telegram 发送失败"
}

log "============================================================"
log "🔍 Academic Pipeline 完成情况检查"
log "============================================================"

REPORT=""
ISSUES=""

# ===== Task 10: 2024 Deep+LLM+Import (PID 13579) =====
log ""
log "📋 Task 10: 2024 Deep+LLM+Import"

if ps -p 13579 > /dev/null 2>&1; then
  log "  ⚠️  PID 13579 仍在运行"
  TAIL_2024=$(tail -1 /Users/lillianliao/notion_rag/github_mining/data/academic/runs/conference_full_20260311_131547/logs/llm_enrich.log 2>/dev/null)
  log "  最新日志: $TAIL_2024"
  REPORT="${REPORT}📋 *Task 10 (2024)*: ⚠️ 仍在运行
${TAIL_2024}
"
  ISSUES="${ISSUES}⚠️ Task 10 仍在运行\n"
else
  log "  ✅ PID 13579 已结束"
  RERUN_LOG="/Users/lillianliao/notion_rag/github_mining/data/academic/runs/conference_full_20260311_131547/logs/pipeline_deep_2024_rerun.log"
  if grep -q "🎉 Pipeline 全部完成" "$RERUN_LOG" 2>/dev/null; then
    log "  ✅ Pipeline 报告成功完成"
    LLM_COUNT=$(python3 -c "import json; d=json.load(open('/Users/lillianliao/notion_rag/github_mining/data/academic/runs/conference_full_20260311_131547/outputs/_llm_enrichment_results.json')); print(len(d))" 2>/dev/null)
    log "  📊 LLM 结果: ${LLM_COUNT} 条"
    IMPORT_RESULT=$(tail -10 /Users/lillianliao/notion_rag/github_mining/data/academic/runs/conference_full_20260311_131547/logs/import.log 2>/dev/null | grep -E '新增|补充|跳过|总处理' | head -5)
    log "  📦 入库: $IMPORT_RESULT"
    REPORT="${REPORT}📋 *Task 10 (2024)*: ✅ 完成
  LLM: ${LLM_COUNT} 条
  ${IMPORT_RESULT}
"
  else
    log "  ❌ Pipeline 未报告成功"
    TAIL=$(tail -5 "$RERUN_LOG" 2>/dev/null)
    log "  最新日志: $TAIL"
    REPORT="${REPORT}📋 *Task 10 (2024)*: ❌ 失败
  ${TAIL}
"
    ISSUES="${ISSUES}❌ Task 10 失败\n"
  fi
fi

# ===== Task 11: 2023 Deep+LLM+Import (PID 19426) =====
log ""
log "📋 Task 11: 2023 Deep+LLM+Import (B+ 级)"

if ps -p 19426 > /dev/null 2>&1; then
  log "  ⚠️  PID 19426 仍在运行"
  TAIL_2023=$(tail -1 /Users/lillianliao/notion_rag/github_mining/data/academic/runs/pipeline_2023_20260315_070407/logs/llm_enrich.log 2>/dev/null)
  log "  最新日志: $TAIL_2023"
  REPORT="${REPORT}📋 *Task 11 (2023)*: ⚠️ 仍在运行
${TAIL_2023}
"
  ISSUES="${ISSUES}⚠️ Task 11 仍在运行\n"
else
  log "  ✅ PID 19426 已结束"
  RERUN_LOG="/Users/lillianliao/notion_rag/github_mining/data/academic/runs/pipeline_2023_20260315_070407/logs/pipeline_rerun.log"
  if tail -30 "$RERUN_LOG" 2>/dev/null | grep -q "🎉 Pipeline 全部完成"; then
    log "  ✅ Pipeline 报告成功完成"
    IMPORT_RESULT=$(tail -10 /Users/lillianliao/notion_rag/github_mining/data/academic/runs/pipeline_2023_20260315_070407/logs/import.log 2>/dev/null | grep -E '新增|补充|跳过|总处理' | head -5)
    log "  📦 入库: $IMPORT_RESULT"
    REPORT="${REPORT}📋 *Task 11 (2023 B+)*: ✅ 完成
  ${IMPORT_RESULT}
"
  else
    log "  ❌ Pipeline 未报告成功"
    TAIL=$(tail -5 "$RERUN_LOG" 2>/dev/null)
    log "  最新日志: $TAIL"
    REPORT="${REPORT}📋 *Task 11 (2023 B+)*: ❌ 失败
  ${TAIL}
"
    ISSUES="${ISSUES}❌ Task 11 失败\n"
  fi
fi

# ===== DB 总览 =====
log ""
log "📊 数据库总览:"
DB_STATS=$(python3 -c "
import sqlite3
db = sqlite3.connect('${HEADHUNTER_DIR}/data/headhunter_dev.db')
cur = db.cursor()
cur.execute(\"SELECT COUNT(*) FROM candidates\")
total = cur.fetchone()[0]
cur.execute(\"SELECT COUNT(*) FROM candidates WHERE source='academic'\")
academic = cur.fetchone()[0]
cur.execute(\"SELECT COUNT(*) FROM candidates WHERE source='academic' AND email IS NOT NULL AND email != ''\")
with_email = cur.fetchone()[0]
cur.execute(\"SELECT COUNT(*) FROM candidates WHERE source='academic' AND linkedin_url IS NOT NULL AND linkedin_url != ''\")
with_li = cur.fetchone()[0]
print(f'全库: {total} | Academic: {academic} | 邮箱: {with_email} ({100*with_email/max(academic,1):.1f}%) | LinkedIn: {with_li} ({100*with_li/max(academic,1):.1f}%)')
db.close()
" 2>/dev/null)
log "  $DB_STATS"

# ===== 发送 Telegram 报告 =====
log ""
log "============================================================"

HEADER="🔍 *Pipeline 定时检查报告*
$(date '+%Y-%m-%d %H:%M')"

if [[ -z "$ISSUES" ]]; then
  FULL_MSG="${HEADER}

${REPORT}
📊 *DB 状态*: ${DB_STATS}

✅ 所有任务已完成！

⏭️ 下一步: 2023 C 级 Serper 重跑"
  log "✅ 所有任务已完成！"
else
  FULL_MSG="${HEADER}

${REPORT}
📊 *DB 状态*: ${DB_STATS}

$(echo -e $ISSUES)"
  log "⚠️  发现问题:"
  echo -e "$ISSUES" | tee -a "$LOG_FILE"
fi

send_telegram "$FULL_MSG"

log "============================================================"
log "📄 完整报告: $LOG_FILE"

