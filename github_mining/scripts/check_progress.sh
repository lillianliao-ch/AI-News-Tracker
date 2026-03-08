#!/bin/bash
# Phase 3.5 + 4.5 进度监控脚本

echo "=========================================="
echo "Phase 3.5 + 4.5 进度监控"
echo "=========================================="
echo ""

# 检查进程
PROCESS_ID=$(ps aux | grep "run_phase35_45_on_phase4.py" | grep -v grep | awk '{print $2}')
if [ -n "$PROCESS_ID" ]; then
    echo "✅ 进程运行中 (PID: $PROCESS_ID)"
else
    echo "❌ 进程未运行"
fi
echo ""

# 显示最新进度
echo "📊 最新进度:"
echo "----------------------------------------"
tail -30 phase35_45_full.log | grep -E "(进度|成功|失败|已处理|完成)" | tail -10
echo ""

# 统计已处理人数
echo "📈 处理统计:"
echo "----------------------------------------"
PROCESSED=$(grep "已处理" phase35_45_full.log | tail -1 | grep -o "已处理 [0-9]*/" | grep -o "[0-9]*")
SUCCESS=$(grep "成功:" phase35_45_full.log | tail -1 | grep -o "成功: [0-9]*" | grep -o "[0-9]*")
FAILED=$(grep "失败:" phase35_45_full.log | tail -1 | grep -o "失败: [0-9]*" | grep -o "[0-9]*")

if [ -n "$PROCESSED" ]; then
    echo "已处理: $PROCESSED 人"
fi
if [ -n "$SUCCESS" ]; then
    echo "成功: $SUCCESS 人"
fi
if [ -n "$FAILED" ]; then
    echo "失败: $FAILED 人"
fi
echo ""

# 检查输出文件
echo "📁 输出文件:"
echo "----------------------------------------"
if [ -f "github_mining/phase4_final_enriched.json" ]; then
    SIZE=$(du -h github_mining/phase4_final_enriched.json | awk '{print $1}')
    echo "✅ Phase 3.5 输出: github_mining/phase4_final_enriched.json ($SIZE)"
else
    echo "⏳ Phase 3.5 输出: 尚未生成"
fi

if [ -f "phase4_5_llm_enriched.json" ]; then
    SIZE=$(du -h phase4_5_llm_enriched.json | awk '{print $1}')
    echo "✅ Phase 4.5 输出: phase4_5_llm_enriched.json ($SIZE)"
else
    echo "⏳ Phase 4.5 输出: 尚未生成"
fi
echo ""

echo "💡 实时日志:"
echo "   tail -f phase35_45_full.log"
