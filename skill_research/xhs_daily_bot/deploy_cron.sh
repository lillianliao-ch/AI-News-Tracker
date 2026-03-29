#!/bin/bash

# ==========================================================
# 小红书 AI 资讯自动发稿定时执行入口 (Daily Deploy script)
# ==========================================================

# 1. 确保日志目录纯净
LOG_FILE="/tmp/xhs_bot.log"
touch $LOG_FILE

# 2. 从本地环境变量文件挂载 Key (CRON 执行时无环境变量隔离坑)
if [ -f "$HOME/.bashrc" ]; then
    source $HOME/.bashrc
fi

# 如果未配置，则使用占位/默认值（如果已在系统中配置 DASHSCOPE_API_KEY，此行会自动生效）
export DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY:-"sk-4e2bb9108e1541f9b7dd88855922c7a3"}

# （请在这里填入您的 Telegram Bot Token 和群组 ID 以免错失提醒）
# export TELEGRAM_BOT_TOKEN="your_bot_token"
# export TELEGRAM_CHAT_ID="your_chat_id"

# 3. 切换工作区并执行编排大脑
echo "Starting campaign at $(date)" >> $LOG_FILE
cd /Users/lillianliao/notion_rag/skill_research/xhs_daily_bot

# MacOS/Linux 环境下自动寻找 python3 的执行路径
/usr/bin/python3 run_campaign.py >> $LOG_FILE 2>&1

echo "Campaign concluded at $(date)" >> $LOG_FILE
