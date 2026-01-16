#!/bin/bash

# ========================================
# 启动生产环境（稳定版本）
# ========================================

echo "🚀 启动 AI 猎头助手 - 生产环境（稳定版）"
echo "📍 端口: 18001"
echo "🔒 调试模式: 关闭"
echo ""

# 切换到后端目录
cd "$(dirname "$0")"

# 复制生产环境配置
if [ -f ".env.production" ]; then
    cp .env.production .env
    echo "✅ 已加载生产环境配置"
else
    echo "❌ 错误: .env.production 文件不存在"
    exit 1
fi

# 启动服务
echo "🔄 启动服务..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 18001

# 注意：不使用 --reload 参数，确保稳定性
