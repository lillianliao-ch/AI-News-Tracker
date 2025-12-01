#!/bin/bash

# 检查参数
if [ "$1" == "prod" ]; then
    echo "🚀 Starting Production Environment..."
    export DB_PATH="data/headhunter_prod.db"
    # 可以添加其他生产环境专用的配置
elif [ "$1" == "dev" ]; then
    echo "🛠️ Starting Development Environment..."
    export DB_PATH="data/headhunter_dev.db"
else
    echo "Usage: ./run.sh [dev|prod]"
    exit 1
fi

# 确保数据目录存在
mkdir -p $(dirname $DB_PATH)

# 启动 Streamlit 应用
streamlit run app.py

