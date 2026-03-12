#!/bin/bash
# 监控 0308 整合版本 AI 项目扩展进度

echo "======================================================================"
echo "📊 AI项目扩展进度监控"
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"
echo ""

# 1. 检查进程
echo "📌 1. 进程状态:"
if ps aux | grep -v grep | grep "run_ai_repo_expansion.sh" > /dev/null; then
    echo "   ✅ 运行中"
    ps aux | grep -v grep | grep "run_ai_repo_expansion.sh" | awk '{print "   PID:", $2}'
else
    echo "   ❌ 未运行"
fi
echo ""

# 2. 检查输出文件
echo "📌 2. 输出文件:"
for file in "ai_repo_users.json" "phase3_from_ai_repos.json" "phase4_5_from_ai_repos.json" "phase4_5_llm_enriched_merged.json"; do
    if [ -f "$file" ]; then
        size=$(ls -lh "$file" | awk '{print $5}')
        count=$(python3 -c "import json; print(len(json.load(open('$file'))))" 2>/dev/null || echo "?")
        echo "   ✅ $file: $count 人 ($size)"
    else
        echo "   ⏳ $file: 未生成"
    fi
done
echo ""

# 3. 查看最新日志
echo "📌 3. 最新日志 (最后20行):"
echo "-----------------------------------------------------------------------"
tail -20 expansion_0308_integrated.log
echo "-----------------------------------------------------------------------"
echo ""

# 4. 实时日志命令
echo "📌 4. 查看实时日志:"
echo "   tail -f expansion_0308_integrated.log"
