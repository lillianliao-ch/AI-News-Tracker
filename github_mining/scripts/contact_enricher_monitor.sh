#!/bin/bash
# contact_enricher_monitor.sh — 每小时推送联系方式富化进度

LOG="/tmp/contact_enricher_20260324.log"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTIFIER="$(dirname "$SCRIPT_DIR")/personal-ai-headhunter/telegram_notifier.py"

send_progress() {
    python3 -c "
import sys, re, subprocess
sys.path.insert(0, '$(dirname "$SCRIPT_DIR")/personal-ai-headhunter')
from telegram_notifier import notify

# 读日志
try:
    with open('$LOG', 'r') as f:
        lines = f.readlines()
except:
    lines = []

last_lines = ''.join(lines[-20:])

# 提取进度
processed = re.findall(r'(\d+)/8460', last_lines)
emails = re.findall(r'邮箱.*?(\d+)', last_lines)
progress_num = processed[-1] if processed else '?'
email_num = emails[-1] if emails else '?'
progress_pct = int(progress_num)*100//8460 if progress_num.isdigit() else 0

# 判断是否完成
done = '完成' in last_lines or 'DONE' in last_lines.upper()

from datetime import datetime
now = datetime.now().strftime('%H:%M')

if done:
    msg = f'✅ *联系方式富化完成！*\n\n📊 8,460 人全部处理完毕\n⏰ {now}'
else:
    msg = f'🔄 *联系方式富化进度* ({now})\n\n进度: {progress_num}/8,460 ({progress_pct}%)\n预计完成: 待计算'

notify(msg)
print(msg)
" 2>/dev/null
}

echo "📡 监控启动，每 1 小时推送一次进度..."

while true; do
    sleep 3600
    send_progress
    
    # 检查进程是否还在跑
    if ! pgrep -f "academic_contact_enricher.py" > /dev/null; then
        python3 -c "
import sys
sys.path.insert(0, '$(dirname "$SCRIPT_DIR")/personal-ai-headhunter')
from telegram_notifier import notify
notify('🏁 *联系方式富化进程已结束*\n\n请检查输出文件，准备入库。')
"
        echo "进程已结束，监控退出"
        break
    fi
done
