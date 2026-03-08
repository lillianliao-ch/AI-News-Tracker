#!/bin/bash
# Phase 4.5 新输入文件进度监控

echo "=========================================="
echo "Phase 4.5 进度监控（新输入文件）"
echo "=========================================="
echo ""

# 检查进程
PROCESS_ID=$(ps aux | grep "run_phase4_5_llm_enrichment.py" | grep -v grep | awk '{print $2}')
if [ -n "$PROCESS_ID" ]; then
    echo "✅ 进程运行中 (PID: $PROCESS_ID)"
else
    echo "❌ 进程未运行"
fi
echo ""

# 显示最新进度
echo "📊 最新进度:"
echo "----------------------------------------"
tail -30 phase4_5_new_input.log | grep -E "(进度|成功|失败|已处理|完成|\[.*\])" | tail -15
echo ""

# 统计已处理人数
echo "📈 处理统计:"
echo "----------------------------------------"
# 从日志中提取最新进度
LATEST=$(grep -E "^\[[0-9]+/[0-9]+\]" phase4_5_new_input.log | tail -1)
if [ -n "$LATEST" ]; then
    echo "$LATEST"
fi
echo ""

# 检查输出文件
echo "📁 输出文件:"
echo "----------------------------------------"
if [ -f "github_mining/phase4_5_llm_enriched.json" ]; then
    SIZE=$(du -h github_mining/phase4_5_llm_enriched.json | awk '{print $1}')
    MODIFIED=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" github_mining/phase4_5_llm_enriched.json)
    echo "✅ 输出文件: github_mining/phase4_5_llm_enriched.json"
    echo "   大小: $SIZE"
    echo "   更新时间: $MODIFIED"
    
    # 统计已富化人数
    if command -v python3 &> /dev/null; then
        ENRICHED=$(python3 -c "import json; data=json.load(open('github_mining/phase4_5_llm_enriched.json')); print(f'{len(data)}')" 2>/dev/null || echo "0")
        HIGH_QUALITY=$(python3 -c "import json; data=json.load(open('github_mining/phase4_5_llm_enriched.json')); print(f'{sum(1 for d in data if d.get(\"website_quality_score\", 0) >= 90)}')" 2>/dev/null || echo "0")
        echo "   已富化: $ENRICHED 人"
        echo "   高质量(90+): $HIGH_QUALITY 人"
    fi
else
    echo "⏳ 输出文件: 尚未生成"
fi
echo ""

echo "💡 实时日志:"
echo "   tail -f phase4_5_new_input.log"
echo ""
echo "💡 停止进程:"
echo "   kill $PROCESS_ID"
