#!/bin/bash
# Phase 5 进度监控脚本

echo "=================================================="
echo "🚀 GitHub Mining Phase 5 - 实时监控"
echo "=================================================="
echo ""

# 1. 检查进程状态
echo "📌 进程状态:"
if ps -p 15705 > /dev/null 2>&1; then
    echo "✅ Phase 5 脚本运行中 (PID: 15705)"
    ps -p 15705 -o pid,state,%cpu,%mem,etime,command | tail -1
else
    echo "❌ Phase 5 脚本未运行"
fi
echo ""

# 2. 检查监控脚本
if ps -p 15670 > /dev/null 2>&1; then
    echo "✅ 自动重启脚本运行中 (PID: 15670)"
else
    echo "⚠️  自动重启脚本未运行"
fi
echo ""

# 3. 当前数据统计
echo "📊 数据统计:"
JSON_FILE="/Users/lillianliao/notion_rag/github_mining/scripts/github_mining/phase5_expanded.json"

if [ -f "$JSON_FILE" ]; then
    FILE_SIZE=$(ls -lh "$JSON_FILE" | awk '{print $5}')
    UPDATE_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$JSON_FILE")

    # 使用 Python 获取用户数
    USER_COUNT=$(python3 -c "import json; print(len(json.load(open('$JSON_FILE'))))" 2>/dev/null || echo "N/A")

    echo "  📁 文件: $JSON_FILE"
    echo "  📦 大小: $FILE_SIZE"
    echo "  👥 用户数: $USER_COUNT"
    echo "  🕐 更新: $UPDATE_TIME"
else
    echo "❌ 文件不存在"
fi
echo ""

# 4. 数据质量
if [ -f "$JSON_FILE" ]; then
    echo "📈 数据质量:"
    python3 << EOF
import json
with open('$JSON_FILE', 'r') as f:
    data = json.load(f)

total = len(data)
with_company = len([u for u in data if u.get('company')])
with_email = len([u for u in data if u.get('email')])
followers_1k = len([u for u in data if u.get('followers', 0) > 1000])
followers_10k = len([u for u in data if u.get('followers', 0) > 10000])

print(f"  🏢 有公司: {with_company:,} ({with_company/total*100:.1f}%)")
print(f"  📧 有邮箱: {with_email:,} ({with_email/total*100:.1f}%)")
print(f"  ⭐ >1K粉丝: {followers_1k:,} ({followers_1k/total*100:.1f}%)")
print(f"  🌟 >10K粉丝: {followers_10k:,} ({followers_10k/total*100:.1f}%)")

# TOP 5
top_users = sorted(data, key=lambda x: x.get('followers', 0), reverse=True)[:5]
print(f"\n  👑 粉丝 TOP 5:")
for i, u in enumerate(top_users, 1):
    print(f"    {i}. {u['username']}: {u.get('followers', 0):,} 粉丝 - {u.get('company', 'N/A')}")
EOF
fi

echo ""
echo "=================================================="
echo "💡 使用 './monitor_phase5.sh' 随时查看进度"
echo "=================================================="
