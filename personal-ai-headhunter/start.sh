#!/bin/bash

echo "🛠️  Starting Personal AI Headhunter - Development Environment"
echo "=================================================="
echo "Branch: $(git branch --show-current)"
echo "Environment: Development"
echo "Database: data/headhunter_dev.db"
echo "Port: 8501"
echo "=================================================="

# 设置数据库路径
export DB_PATH="data/headhunter_dev.db"
export ENV=development

# 确保数据目录存在
mkdir -p data

# 启动 Streamlit 应用
streamlit run app.py --server.port 8501
