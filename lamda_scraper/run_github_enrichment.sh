#!/bin/bash
# LAMDA GitHub 信息挖掘 - 一键启动脚本

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     LAMDA 候选人 GitHub 信息深度挖掘工具                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "功能说明:"
echo "  - 从候选人的 GitHub 链接提取详细信息"
echo "  - 计算技术能力评分 (0-100分)"
echo "  - 识别技术栈 (机器学习、深度学习、NLP等)"
echo "  - 统计影响力 (Stars、Followers、Forks)"
echo ""

# 检查输入文件
if [ ! -f "lamda_candidates_full.csv" ]; then
    echo "❌ 未找到 lamda_candidates_full.csv"
    echo "   请先运行完整采集:"
    echo "   ./run_full_collection.sh"
    exit 1
fi

# 检查 GitHub Token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  未设置 GITHUB_TOKEN 环境变量"
    echo "   请求限制: 60次/小时 (未认证)"
    echo "   推荐设置: export GITHUB_TOKEN=your_token_here"
    echo ""
    echo "获取 Token 步骤:"
    echo "  1. 访问 https://github.com/settings/tokens"
    echo "  2. 点击 'Generate new token (classic)'"
    echo "  3. 勾选 'public_repo', 'read:user', 'read:org'"
    echo "  4. 生成并复制 Token"
    echo "  5. 设置环境变量: export GITHUB_TOKEN=your_token"
    echo ""
fi

echo "📊 数据统计:"
echo "  输入文件: lamda_candidates_full.csv"
github_count=$(grep -c "github.com" lamda_candidates_full.csv 2>/dev/null || echo "0")
echo "  有 GitHub 的候选人: ~$(echo "scale=0; $github_count * 0.5" | bc)"
echo ""

echo "🚀 开始处理..."
echo ""

# 运行 GitHub 增强工具
python3 github_enricher.py \
    --input lamda_candidates_full.csv \
    --output lamda_candidates_github_enhanced.csv

if [ $? -eq 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              ✅ GitHub 信息挖掘完成！                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 输出文件:"
    echo "  ✓ lamda_candidates_github_enhanced.csv"
    echo ""
    echo "🎯 新增字段:"
    echo "  • github_score - GitHub 活跃度总分 (0-100)"
    echo "  • github_activity - 活跃度评分 (0-40)"
    echo "  • github_influence - 影响力评分 (0-30)"
    echo "  • github_quality - 质量评分 (0-30)"
    echo "  • github_repos - 公开仓库数量"
    echo "  • github_stars - 总 Stars 数"
    echo "  • github_followers - Followers 数"
    echo "  • github_tech_stack - 技术栈识别"
    echo "  • github_languages - 编程语言统计"
    echo "  • github_top_repos - Top 10 仓库详情"
    echo ""
    echo "💡 查看结果:"
    echo "  Excel/Numbers: open lamda_candidates_github_enhanced.csv"
    echo ""
    echo "🔍 筛选高分候选人:"
    echo "  查看 github_score >= 60 的候选人"
    echo ""
else
    echo ""
    echo "❌ 处理失败"
    echo ""
fi
