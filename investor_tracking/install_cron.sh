#!/bin/bash
# 安装定时任务 - 每日自动检查 ARK 持仓变动

echo "⏰ 安装定时任务"
echo "==============="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_CMD="30 9 * * 1-5 cd $SCRIPT_DIR && python3 tracker.py check >> cron.log 2>&1"

echo ""
echo "将添加以下定时任务:"
echo "  每周一到周五早上 9:30 运行持仓检查"
echo ""
echo "  $CRON_CMD"
echo ""

read -p "确认安装? (y/n): " confirm
if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    # 添加到 crontab
    (crontab -l 2>/dev/null | grep -v "tracker.py"; echo "$CRON_CMD") | crontab -
    echo ""
    echo "✅ 定时任务已安装!"
    echo ""
    echo "查看当前 crontab:"
    crontab -l | grep tracker
    echo ""
    echo "日志文件: $SCRIPT_DIR/cron.log"
else
    echo "已取消"
fi
