#!/bin/bash
# 完整采集脚本 - 采集所有 LAMDA 人才 (462+人)

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     LAMDA 猎头数据采集 - 完整版 (462+ 候选人)               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  警告: 这将需要 2-3 小时完成"
echo "⏱️  预计耗时: 2-3 小时"
echo "📊 采集数量: 392 校友 + 94 博士生 = 462+ 人"
echo ""
read -p "是否继续? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "🚀 开始采集..."
echo ""

# Step 1: 数据采集
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/3: 数据采集 (2-3小时)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 lamda_scraper.py --output lamda_full --delay 1.5

if [ ! -f "lamda_full.json" ]; then
    echo "❌ 采集失败"
    exit 1
fi

echo ""
echo "✓ 数据采集完成"
echo ""

# Step 2: 评分分析
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/3: 评分分析 (5分钟)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 talent_analyzer.py --input lamda_full.json --output lamda_full_scored.csv

echo ""
echo "✓ 评分分析完成"
echo ""

# Step 3: 导出优先联系人
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/3: 导出优先联系人 (2分钟)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 export_contacts.py \
    --input lamda_full_scored.csv \
    --output priority_contacts.csv \
    --tier B \
    --priority Warm

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║             ✅ 完整流程执行成功！                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 生成的文件:"
echo "  ✓ lamda_full.csv              - 原始数据"
echo "  ✓ lamda_full.json             - 结构化数据"
echo "  ✓ lamda_full_scored.csv       - 评分结果 (⭐ 推荐)"
echo "  ✓ priority_contacts.csv       - 优先联系人 (⭐ 推荐)"
echo ""
echo "🎯 建议下一步:"
echo "  1. 用 Excel 打开 lamda_full_scored.csv"
echo "  2. 查看 Tier A/B + Hot 候选人"
echo "  3. 查看 priority_contacts.csv 获取联系方式"
echo "  4. 开始联系！"
echo ""
