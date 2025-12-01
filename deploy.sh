#!/bin/bash

# 猎头联盟网站部署脚本

echo "🚀 猎头联盟网站部署脚本"
echo "================================"

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

# 获取本机IP地址
get_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1"
    else
        # Linux
        hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1"
    fi
}

LOCAL_IP=$(get_ip)
PORT=8080

echo ""
echo "🌐 网络配置信息："
echo "   本机访问: http://localhost:$PORT"
echo "   局域网访问: http://$LOCAL_IP:$PORT"
echo ""

# 选择部署模式
echo "请选择部署模式："
echo "1) 开发模式 (调试开启，适合开发)"
echo "2) 生产模式 (调试关闭，适合正式使用)"
echo "3) 局域网模式 (允许局域网访问)"
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "🔧 启动开发模式..."
        export FLASK_ENV=development
        ;;
    2)
        echo "🏭 启动生产模式..."
        export FLASK_ENV=production
        ;;
    3)
        echo "🌐 启动局域网模式..."
        export FLASK_ENV=development
        echo "📱 其他设备可以通过以下地址访问："
        echo "   http://$LOCAL_IP:$PORT"
        ;;
    *)
        echo "❌ 无效选择，使用默认开发模式"
        export FLASK_ENV=development
        ;;
esac

echo ""
echo "🚀 启动服务器..."
echo "🛑 按 Ctrl+C 停止服务器"
echo ""

python3 app.py 