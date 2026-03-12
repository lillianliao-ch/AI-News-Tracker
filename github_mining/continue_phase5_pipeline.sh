#!/bin/bash
# Phase 5 完整流程 - Phase 3 → Phase 3.5 → Phase 4.5 → 导入数据库

set -e

echo "=========================================="
echo "🚀 Phase 5 数据完整处理流程"
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

cd /Users/lillianliao/notion_rag/github_mining/scripts

# Step 1: Phase 3 富化（获取 repos 详情）
echo ""
echo "▶️  Step 1: Phase 3 富化（获取 repos 详情）..."
echo "   预计耗时: 30-45 分钟"
echo ""

python3 github_network_miner.py \
  phase3 \
  --input github_mining/phase5_expanded_latest.json \
  --output github_mining/phase3_from_phase5.json

PHASE3_COUNT=$(python3 -c "import json; print(len(json.load(open('github_mining/phase3_from_phase5.json'))))")
echo "✅ Phase 3 完成: $PHASE3_COUNT 人"

# Step 2: Phase 3.5 爬取个人网站
echo ""
echo "▶️  Step 2: Phase 3.5 爬取个人网站..."
echo "   预计耗时: 1-2 小时"
echo ""

python3 github_network_miner.py \
  phase3_5 \
  --input github_mining/phase3_from_phase5.json \
  --output github_mining/phase35_from_phase5.json

PHASE35_COUNT=$(python3 -c "
import json
data = json.load(open('github_mining/phase35_from_phase5.json'))
print(len([u for u in data if u.get('homepage_scraped')]))
")
echo "✅ Phase 3.5 完成: $PHASE35_COUNT 人有个人网站"

# Step 3: Phase 4.5 LLM 富化
echo ""
echo "▶️  Step 3: Phase 4.5 LLM 富化..."
echo "   包含: 工作履历、教育背景、技能、谈话点、结构化标签"
echo "   预计耗时: 2-3 小时"
echo ""

python3 run_phase4_5_llm_enrichment.py \
  --input github_mining/phase35_from_phase5.json \
  --output github_mining/phase45_phase5_final.json

PHASE45_COUNT=$(python3 -c "import json; print(len(json.load(open('github_mining/phase45_phase5_final.json'))))")
echo "✅ Phase 4.5 完成: $PHASE45_COUNT 人"

# Step 4: 导入数据库
echo ""
echo "▶️  Step 4: 导入数据库..."
echo ""

cd ../personal-ai-headhunter
python3 import_github_candidates.py \
  --file ../github_mining/phase45_phase5_final.json

echo ""
echo "=========================================="
echo "✅ Phase 5 完整流程完成！"
echo "=========================================="
echo ""
echo "📊 结果汇总:"
echo "  - Phase 5 发现: 28,242 人"
echo "  - Phase 3 富化: $PHASE3_COUNT 人"
echo "  - Phase 3.5 有网站: $PHASE35_COUNT 人"
echo "  - Phase 4.5 LLM富化: $PHASE45_COUNT 人"
echo ""
echo "🎯 查看数据库:"
echo "  sqlite3 data/headhunter_dev.db 'SELECT COUNT(*) FROM candidates WHERE source LIKE \"%github%\";'"
echo ""
