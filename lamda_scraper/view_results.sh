#!/bin/bash
# 快速查看 GitHub 增强结果

cd "$(dirname "$0")"

echo "================================"
echo "📊 LAMDA GitHub 信息挖掘结果"
echo "================================"
echo ""

echo "🏆 Top 10 技术人才:"
echo "---"
python3 -c "
import csv
with open('lamda_candidates_github_enhanced.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    candidates = list(reader)
    top = sorted(candidates, key=lambda x: float(x.get('github_score', 0)), reverse=True)[:10]
    for i, c in enumerate(top, 1):
        if c.get('github_score') and float(c['github_score']) > 0:
            print(f\"{i:2}. {c['姓名']:10s} | {c['github_username']:20s} | {float(c['github_score']):3.0f}分 | {int(c.get('github_stars', 0)):6} stars\")
"
echo ""

echo "📁 可用文件:"
echo "---"
ls -lh github_*.csv lamda_candidates_github_enhanced.csv 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""

echo "🎯 快速操作:"
echo "---"
echo "1. 查看顶级候选人:     open github_tier_a.csv"
echo "2. 查看高质量候选人:   open github_high_quality.csv"
echo "3. 查看完整数据:       open lamda_candidates_github_enhanced.csv"
echo "4. 阅读详细报告:       open GITHUB_ENRICHMENT_RESULTS.md"
echo ""

echo "💡 按技术栈查看:"
echo "---"
echo "NLP 专家:    open github_nlp_experts.csv"
echo "CV 专家:     open github_computer_vision_experts.csv"
echo "RL 专家:     open github_reinforcement_learning_experts.csv"
echo "ML 专家:     open github_machine_learning_experts.csv"
echo ""

echo "================================"
echo "✅ 处理完成！"
echo "================================"
