#!/bin/bash
# 查看联系信息挖掘结果

cd "$(dirname "$0")"

echo "================================"
echo "📊 LAMDA 联系信息挖掘结果"
echo "================================"
echo ""

echo "✅ 核心成果:"
echo "---"
echo "  • 27 位候选人找到邮箱 (5.8%)"
echo "  • 44 位候选人找到工作单位 (9.5%)"
echo "  • 49 位候选人找到个人网站 (10.6%)"
echo ""

echo "🎯 高质量且有邮箱的候选人 (立即可联系):"
echo "---"
python3 << 'PYEOF'
import csv

with open('high_quality_with_email.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    candidates = list(reader)

for i, c in enumerate(candidates[:10], 1):
    print(f"{i}. {c['姓名']} | {c['github_score']}分 | {c['邮箱']}")
    print(f"   工作单位: {c['工作单位'][:50]}")
    print(f"   GitHub: https://github.com/{c['github_username']} | Stars: {c['github_stars']}")
    print()
PYEOF

echo "📁 可用文件:"
echo "---"
ls -lh high_quality_with_email.csv candidates_with_email.csv candidates_with_contacts.csv lamda_candidates_final.csv 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""

echo "🎯 快速操作:"
echo "---"
echo "1. 查看立即可联系: open high_quality_with_email.csv"
echo "2. 查看所有有邮箱:   open candidates_with_email.csv"
echo "3. 查看完整数据:     open lamda_candidates_final.csv"
echo "4. 阅读详细报告:     open CONTACT_RESULTS_SUMMARY.md"
echo ""

echo "================================"
echo "✅ 联系信息挖掘完成！"
echo "================================"
