#!/bin/bash

echo "🚀 Starting Personal AI Headhunter - Production Environment"
echo "=================================================="
echo "Environment: Production"
echo "Database: data/headhunter.db"
echo "Port: 8502"
echo "=================================================="

# 设置数据库路径
export DB_PATH="data/headhunter.db"
export ENV=production

# 确保数据目录存在
mkdir -p data

# 启动 Streamlit 应用
streamlit run app.py --server.port 8502
