#!/bin/bash
set -e

NLM="/Users/lillianliao/Library/Python/3.12/bin/notebooklm"
JD_DIR="/Users/lillianliao/notion_rag/skill_research/multimodal_jds"

echo "=================================================="
echo "          全量多模态 JD 对标自动化脚本            "
echo "=================================================="

# Check if there are any files
file_count=$(ls -1q "$JD_DIR"/MEGA_CHUNK_*.txt 2>/dev/null | wc -l || echo 0)
if [ "$file_count" -eq 0 ]; then
    echo "未找到任何 JD 文本文件 ($JD_DIR)"
    exit 1
fi
echo "✅ 准备导入 $file_count 份聚合过的真实 JD 数据"

echo "1. 创建大基座 Notebook [全量多模态岗位深度对标分析]..."
NB_JSON=$($NLM create "全量多模态岗位深度对标分析" --json)
NB_ID=$(echo "$NB_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notebook', {}).get('id', ''))")

if [ -z "$NB_ID" ]; then
    echo "创建失败，未能获取 Notebook ID。"
    exit 1
fi
echo "✅ Notebook ID 获取成功: $NB_ID"

echo "2. 开始批量异步推流所有 JD 文件到 Google (这可能会比较慢，取决于文件数量)..."
for file in "$JD_DIR"/MEGA_CHUNK_*.txt; do
    echo "   -> 正在上传: $(basename "$file")"
    $NLM source add "$file" -n "$NB_ID"
done

echo "✅ 所有文件已加入队列，开始轮询等待解析完成 (此过程可能需要 1-3 分钟)..."
# 使用 API 自带的 source wait 轮询状态
$NLM source wait All -n "$NB_ID" --timeout 300

echo "3. 触发超大上下文交叉推理分析..."
prompt="请系统地分析目前你收到的所有有关『多模态大模型』的真实招聘需求 JD。
请输出一份万字的详尽【多模态赛道招聘风向报告】，包含以下核心：
1. 【模型框架与工具栈】目前各家最统一要求的底层技术是什么？（按提及频率从高到低）
2. 【业务场景差异】挑出具有代表性的 3 家不同公司，详细对比他们在多模态使用场景上的商业/研究侧重点差异。
3. 【工程vs算法】结合 JD，目前行业是更稀缺偏向底层架构优化的『工程黑客』，还是理论前沿的『算法科学家』？给出论据。
4. 【红牌排雷点】有哪些经验或背景是这些 JD 普遍不看重、甚至明确排斥的？
请使用极为专业、清晰的 Markdown 结构输出。"

echo "-------------------📝 分 析 报 告 正 文 -------------------"
$NLM ask "$prompt" -n "$NB_ID" > "$JD_DIR/final_report.md"
cat "$JD_DIR/final_report.md"
echo "---------------------------------------------------"
echo "🎉 分析报告已完整生成并保存至: $JD_DIR/final_report.md"
