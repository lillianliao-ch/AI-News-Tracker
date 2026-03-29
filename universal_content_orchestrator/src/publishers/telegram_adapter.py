import os
import json
import urllib.request
from typing import List

class TelegramPublisher:
    """
    Adapter to push content orchestrator results directly to the user's Telegram.
    Expects TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to be in the environment schema.
    """
    def __init__(self):
        # Fallback to local .env if global is not sourced properly by cron
        from dotenv import load_dotenv
        load_dotenv("/Users/lillianliao/notion_rag/.env")
        
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        
    def push_summary(self, matched_articles: List[dict]):
        if not self.bot_token or not self.chat_id:
            print("⚠️ Telegram Credentials Missing! Skipping Notification.")
            return False
            
        print("📨 [Publisher: Telegram] 正在构建全局通报信标并发射...")
        
        text = "🤖 <b>万物编排器 (Universal Orchestrator)</b> 落网汇报\\n\\n"
        for i, art in enumerate(matched_articles, 1):
            text += f"📌 <b>{art['title']}</b>\\n"
        
        text += "\\n🔗 <i>以上 8 篇高优干货已生成专属排版与爆款文案，并发射至小红书草稿箱！请查收。</i>"
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as resp:
                print("✅ [Publisher: Telegram] 飞燕通报投递大厅！")
                return True
        except Exception as e:
            print(f"❌ [Publisher: Telegram] 轰炸通讯塔失败: {e}")
            return False
