#!/bin/bash
# 简单的测试运行脚本

cd "$(dirname "$0")"

echo "========================================="
echo "   LAMDA 猎头数据采集 - 测试运行"
echo "========================================="
echo ""
echo "⏱️ 采集数量: 10人"
echo "⏳ 预计耗时: 5-8分钟"
echo ""

python3 lamda_scraper.py --limit 10 --output hunter_test --delay 1.0

echo ""
echo "========================================="
echo "✓ 数据采集完成！"
echo "========================================="
echo ""
echo "文件位置:"
echo "  - hunter_test.csv (原始数据)"
echo "  - hunter_test.json (结构化数据)"
echo ""
echo "下一步: 运行评分分析"
echo "  python3 talent_analyzer.py --input hunter_test.json --output hunter_test_scored.csv"
echo ""
