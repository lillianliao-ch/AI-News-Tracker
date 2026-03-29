#!/bin/bash
set -e

NLM="/Users/lillianliao/Library/Python/3.12/bin/notebooklm"

echo "=================================================="
echo "          JD 分析场景自动测试脚本                 "
echo "=================================================="

echo "1. 创建 Notebook [多模态大模型JD对标测试]..."
NB_JSON=$($NLM create "多模态大模型JD对标测试" --json)
# 简单萃取 notebook_id (使用 Python json 模块更稳定)
NB_ID=$(echo "$NB_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notebook', {}).get('id', ''))")

if [ -z "$NB_ID" ]; then
    echo "创建失败，请确认是否已完成 login 登录认证。"
    exit 1
fi
echo "✅ Notebook ID 获取成功: $NB_ID"

echo "2. 开始批量导入 JD 文件作为 Source..."
$NLM source add ./jd_1_ByteDance_Multimodal.txt -n "$NB_ID"
$NLM source add ./jd_2_MiniMax_LLM.txt -n "$NB_ID"
$NLM source add ./jd_3_Tencent_Vision.txt -n "$NB_ID"

echo "✅ 文件上传完毕，等待谷歌后台知识库切片和向量化 (这可能需要 10-20 秒)..."
# 由于当前版本 CLI 没有内置 wait all，我们简单 sleep 一下，或者假定官方后台处理纯文本很快
sleep 15
echo "3. 发起多文档联合深度推理 (NotebookLM 核心能力演示)..."
echo "Prompt: 单独罗列每家的算力和工程能力要求，最后输出一张横向对比表。"

echo "-------------------📝 测 试 结 果-------------------"
$NLM ask "请从：1.底层框架偏好 2.算力体验与工程门槛 3.核心痛点 这三个维度，横向对比导入的这三份多模态大模型JD。请用清晰的 Markdown 格式输出对比表格，并在一句话内总结出哪家的工程落地要求最严苛。" -n "$NB_ID"
echo "---------------------------------------------------"

echo "🎉 测试完成！如果有用，你可以随时进入 Google NotebookLM 的网页端，你会看到刚才那个名为『多模态大模型JD对标测试』的笔记本已经自动建立好，并且内置了所有提问哦！"
