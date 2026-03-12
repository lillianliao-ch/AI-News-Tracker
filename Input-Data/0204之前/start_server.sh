#!/bin/bash

# 猎头联盟网站启动脚本

echo "🚀 启动猎头联盟网站..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖是否安装
echo "📦 检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "📥 安装依赖..."
    pip3 install -r requirements.txt
fi

# 启动应用
echo "🌐 启动Web服务器..."
echo "📍 网站地址：http://localhost:8080"
echo "🛑 按 Ctrl+C 停止服务器"
echo ""

python3 app.py 