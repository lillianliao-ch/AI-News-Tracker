#!/bin/bash
# 1,105 人富化进度监控

echo "=========================================="
echo "1,105 人富化进度监控"
echo "=========================================="
echo ""

# 检查进程
PROCESS_ID=$(ps aux | grep "enrich_missing_1105.py" | grep -v grep | awk '{print $2}')
if [ -n "$PROCESS_ID" ]; then
    echo "✅ 进程运行中 (PID: $PROCESS_ID)"
else
    echo "❌ 进程未运行"
fi
echo ""

# 显示最新进度
echo "📊 最新进度:"
echo "----------------------------------------"
tail -20 phase45_missing_1105.log | grep -E "(\[.*\]|✅|⚠️)" | tail -10
echo ""

# 统计已处理人数
LATEST=$(grep -E "^\[[0-9]+/[0-9]+\]" phase45_missing_1105.log | tail -1)
if [ -n "$LATEST" ]; then
    echo "$LATEST"
fi
echo ""

# 检查输出文件
echo "📁 输出文件:"
echo "----------------------------------------"
if [ -f "github_mining/scripts/github_mining/phase45_missing_1105_enriched.json" ]; then
    SIZE=$(du -h github_mining/scripts/github_mining/phase45_missing_1105_enriched.json | awk '{print $1}')
    echo "✅ 输出文件已生成: $SIZE"
    
    # 统计已富化人数
    ENRICHED=$(python3 -c "import json; data=json.load(open('github_mining/scripts/github_mining/phase45_missing_1105_enriched.json')); print(f'{len(data)}')" 2>/dev/null || echo "0")
    echo "   已富化: $ENRICHED 人"
else
    echo "⏳ 输出文件尚未生成"
fi
echo ""

echo "💡 实时日志:"
echo "   tail -f phase45_missing_1105.log"
echo ""
echo "💡 停止进程:"
echo "   kill $PROCESS_ID"
