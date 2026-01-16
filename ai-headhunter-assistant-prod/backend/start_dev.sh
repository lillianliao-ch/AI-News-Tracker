#!/bin/bash

# ========================================
# 启动开发环境（开发版本）
# ========================================

echo "🔧 启动 AI 猎头助手 - 开发环境"
echo "📍 端口: 18002"
echo "🐛 调试模式: 开启"
echo "🔄 热重载: 开启"
echo ""

# 切换到后端目录
cd "$(dirname "$0")"

# 复制开发环境配置
if [ -f ".env.development" ]; then
    cp .env.development .env
    echo "✅ 已加载开发环境配置"
else
    echo "❌ 错误: .env.development 文件不存在"
    exit 1
fi

# 启动服务（带热重载）
echo "🔄 启动服务（热重载模式）..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 18002 --reload

# 使用 --reload 参数，代码修改后自动重启
