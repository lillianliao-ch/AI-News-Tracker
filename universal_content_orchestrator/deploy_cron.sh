#!/bin/bash

# ==========================================================
# 万物编排器（Universal Content Orchestrator）自动挂机引擎
# ==========================================================

LOG_FILE="/tmp/universal_orchestrator.log"
touch $LOG_FILE
echo "======================================================" >> $LOG_FILE
echo "🚀 Orchestrator Boot Sequence Initiated at $(date)" >> $LOG_FILE

# 1. 重载全局机器环境变量，捕获 Token (API_KEY, TG_TOKEN)
if [ -f "$HOME/.zshrc" ]; then
    source $HOME/.zshrc
elif [ -f "$HOME/.bashrc" ]; then
    source $HOME/.bashrc
fi

# 确保加载 .env 文件中的变量作为兜底
if [ -f "/Users/lillianliao/notion_rag/.env" ]; then
    export $(grep -v '^#' "/Users/lillianliao/notion_rag/.env" | xargs)
fi

# 2. 定位工作区
cd /Users/lillianliao/notion_rag/universal_content_orchestrator || exit 1

# 3. 引爆主板脑区
/usr/bin/python3 main.py >> $LOG_FILE 2>&1

echo "🛑 Orchestrator Sequence Terminated at $(date)" >> $LOG_FILE
echo "======================================================" >> $LOG_FILE
