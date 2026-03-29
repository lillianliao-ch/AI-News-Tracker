import os
import time
import subprocess
try:
    import telebot
    from dotenv import load_dotenv
except ImportError:
    print("❌ 缺少依赖包！请执行: pip install pyTelegramBotAPI python-dotenv")
    exit(1)

# 加载环境变量
load_dotenv(".env.antigravity_tg")
TOKEN = os.getenv("TG_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID", "")

if not TOKEN or TOKEN == "your_token_here":
    print("❌ 请在 .env.antigravity_tg 文件中填入您的真实 TG_BOT_TOKEN！")
    exit(1)

bot = telebot.TeleBot(TOKEN)

def run_cli_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout
    except Exception as e:
        return f"Error executing {cmd}: {e}"

def is_authorized(message):
    if not ALLOWED_USER_ID or ALLOWED_USER_ID == "your_telegram_short_id":
        return True # 如果没设限制，暂时所有人都可访问
    return str(message.from_user.id) == ALLOWED_USER_ID

@bot.message_handler(commands=['start', 'new', 'clear'])
def send_welcome(message):
    if not is_authorized(message): return
    bot.reply_to(message, "🚀 Pocket-Antigravity 节点已唤醒！桌面端会话已重置。您可以随时下发任务，遇到危险底层操作，我的弹窗问题也会实时转发给您审批。")
    run_cli_cmd("opencli antigravity new")

@bot.message_handler(func=lambda message: True)
def handle_conversation(message):
    if not is_authorized(message):
        bot.reply_to(message, "⛔️ 权限拒绝：未授权的用户请求。")
        return
        
    user_text = message.text
    status_msg = bot.reply_to(message, "⏳ 正在连接您家里的 Antigravity 主机...")
    
    # 1. 抓取发送前的底图（聊天记录长度）
    base_text = run_cli_cmd("opencli antigravity read")
    
    # 2. 从外部注您的话入大主机的桌面框架中
    safe_text = user_text.replace('"', '\\"') 
    run_cli_cmd(f'opencli antigravity send "{safe_text}"')
    
    bot.edit_message_text("🔄 大脑正在思考或深度执行...\n(如果我遇到需要授权的操作，会立刻把弹窗文字转发给您，请随时准备回复指令)", chat_id=message.chat.id, message_id=status_msg.message_id)
    
    # 3. 轮询防抖：检测输出是否稳定（连续8秒不吐新字眼，代表回答结束或被阻塞等待授权）
    stable_count = 0
    current_text = ""
    current_len = len(run_cli_cmd("opencli antigravity read"))
    
    while stable_count < 4:
        time.sleep(2)
        current_text = run_cli_cmd("opencli antigravity read")
        new_len = len(current_text)
        
        if new_len == current_len and new_len > len(base_text):
            stable_count += 1
        elif new_len == current_len and new_len == len(base_text):
            stable_count += 1
        else:
            stable_count = 0
            current_len = new_len

    # 4. 抽取大主机对您的全新回复 / 授权弹窗说明
    new_reply = current_text[len(base_text):].strip()
    
    # 5. 回拨到 Telegram
    if len(new_reply) > 4000:
        bot.edit_message_text(f"✅ 处理结束。结果文字较巨量，拆包发送中：", chat_id=message.chat.id, message_id=status_msg.message_id)
        for i in range(0, len(new_reply), 4000):
            bot.send_message(message.chat.id, new_reply[i:i+4000])
    else:
        if new_reply:
            bot.edit_message_text(f"💡 [主脑响应]\n\n{new_reply}", chat_id=message.chat.id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text("⚠️ 接收空响应，也许大主机还在疯狂运算，或被静默阻塞，请检查本地界面。", chat_id=message.chat.id, message_id=status_msg.message_id)

if __name__ == "__main__":
    print("🤖 Telegram-Antigravity 桥接守护进程启动中！正在监听您的手机指令...")
    bot.infinity_polling()
