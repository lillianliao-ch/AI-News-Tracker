#!/bin/bash
# Phase 5 完整流程脚本 - 无人值守端到端处理
# 从 28,242 个 Phase 5 用户 → 最终导入数据库

set -e

echo "=========================================="
echo "🚀 Phase 5 完整流程 - 无人值守端到端"
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

cd /Users/lillianliao/notion_rag/github_mining

# Step 1: Phase 3 富化（获取 repos 详情）
echo ""
echo "▶️  Step 1/4: Phase 3 富化（获取 repos 详情）..."
echo "   输入: scripts/github_mining/phase5_expanded_latest.json (28,242 人)"
echo "   预计耗时: 30-45 分钟"
echo ""

cd scripts
python3 github_network_miner.py \
  phase3 \
  --input github_mining/phase5_expanded_latest.json

# 检查输出 (Phase 3 脚本会将默认输出写在 base_dir 的 phase3_enriched.json，因为没有匹配 "phase4_expanded" 这个特殊关键字)
PHASE3_OUTPUT="phase3_enriched.json"
if [ -f "$PHASE3_OUTPUT" ]; then
    PHASE3_COUNT=$(python3 -c "import json; print(len(json.load(open('$PHASE3_OUTPUT'))))")
    echo "✅ Phase 3 完成: $PHASE3_COUNT 人"
else
    echo "❌ Phase 3 输出文件未找到"
    exit 1
fi

# Step 2: Phase 3.5 爬取个人网站
echo ""
echo "▶️  Step 2/4: Phase 3.5 爬取个人网站..."
echo "   预计耗时: 1-2 小时"
echo ""

python3 github_network_miner.py \
  phase3_5 \
  --input phase3_enriched.json

# 检查输出 (默认输出到 phase3_5_enriched.json)
PHASE35_OUTPUT="phase3_5_enriched.json"
if [ -f "$PHASE35_OUTPUT" ]; then
    PHASE35_COUNT=$(python3 -c "
import json
data = json.load(open('$PHASE35_OUTPUT'))
print(len([u for u in data if u.get('homepage_scraped')]))
")
    echo "✅ Phase 3.5 完成: $PHASE35_COUNT 人有个人网站"
else
    echo "❌ Phase 3.5 输出文件未找到"
    exit 1
fi

# Step 3: Phase 4.5 LLM 富化（一次性完成所有提取）
echo ""
echo "▶️  Step 3/4: Phase 4.5 LLM 富化（一次性完成所有提取）..."
echo "   包含: 工作履历、教育背景、技能、谈话点、结构化标签"
echo "   预计耗时: 2-3 小时"
echo ""

python3 run_phase4_5_llm_enrichment.py \
  --input phase3_5_enriched.json \
  --output phase45_phase5_final.json

# 检查输出
PHASE45_OUTPUT="phase45_phase5_final.json"
if [ -f "$PHASE45_OUTPUT" ]; then
    PHASE45_COUNT=$(python3 -c "import json; print(len(json.load(open('$PHASE45_OUTPUT'))))")
    echo "✅ Phase 4.5 完成: $PHASE45_COUNT 人"
else
    echo "❌ Phase 4.5 输出文件未找到"
    exit 1
fi

# Step 4: 导入数据库
echo ""
echo "▶️  Step 4/4: 导入数据库..."
echo ""

cd ../personal-ai-headhunter
python3 import_github_candidates.py \
  --file ../github_mining/scripts/phase45_phase5_final.json

echo ""
echo "=========================================="
echo "✅ Phase 5 完整流程成功完成！"
echo "=========================================="
echo ""
echo "📊 最终统计:"
echo "  - Phase 5 发现: 28,242 人"
echo "  - Phase 3 富化: $PHASE3_COUNT 人"
echo "  - Phase 3.5 有网站: $PHASE35_COUNT 人"
echo "  - Phase 4.5 LLM富化: $PHASE45_COUNT 人"
echo ""
echo "🎯 查看新增候选人:"
echo "  sqlite3 personal-ai-headhunter/data/headhunter_dev.db"
echo "  'SELECT name, github_url, current_company FROM candidates WHERE source LIKE \"%github%\" ORDER BY created_at DESC LIMIT 20;'"
echo ""
