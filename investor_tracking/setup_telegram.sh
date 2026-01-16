#!/bin/bash
# Telegram 通知配置脚本

echo "🔔 投资人持仓监控 - Telegram 通知配置"
echo "========================================"
echo ""

# 检查是否已配置
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    echo "✅ Telegram 已配置"
    echo "   Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
    echo "   Chat ID: $TELEGRAM_CHAT_ID"
    echo ""
    echo "发送测试消息..."
    python3 -c "
import requests
response = requests.post(
    f'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage',
    json={'chat_id': '${TELEGRAM_CHAT_ID}', 'text': '🔔 投资人持仓监控系统测试消息 ✅'}
)
print('✅ 测试消息发送成功!' if response.ok else f'❌ 发送失败: {response.text}')
"
    exit 0
fi

echo "❌ Telegram 未配置"
echo ""
echo "📝 配置步骤："
echo ""
echo "1. 创建 Telegram Bot："
echo "   - 打开 Telegram，搜索 @BotFather"
echo "   - 发送 /newbot"
echo "   - 按提示设置 bot 名称"
echo "   - 保存获得的 Bot Token"
echo ""
echo "2. 获取 Chat ID："
echo "   - 向你的 bot 发送任意消息"
echo "   - 访问: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
echo "   - 找到 chat.id 字段"
echo ""
echo "3. 设置环境变量（添加到 ~/.zshrc 或 ~/.bashrc）："
echo ""
echo "   export TELEGRAM_BOT_TOKEN=\"your_bot_token_here\""
echo "   export TELEGRAM_CHAT_ID=\"your_chat_id_here\""
echo ""
echo "4. 重新加载配置："
echo "   source ~/.zshrc"
echo ""
echo "5. 运行此脚本测试："
echo "   ./setup_telegram.sh"
echo ""
