import os
import time
import json
import urllib.request
from typing import Dict
from playwright.sync_api import sync_playwright

# Try to load .env
try:
    from dotenv import load_dotenv
    load_dotenv("/Users/lillianliao/notion_rag/.env")
except ImportError:
    pass

class QwenEngine:
    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")

    def call_qwen(self, prompt: str) -> str:
        data = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        req = urllib.request.Request(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            data=json.dumps(data).encode('utf-8'),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"❌ LLM API 故障: {e}")
            return "您好，您的背景很棒，近期是否有看新机会的打算？"

def generate_greeting(name: str, labels: str, qwen: QwenEngine) -> str:
    prompt = f"""你是一个高级AI行业猎头专家。正在为Boss直聘上的一位候选人打招呼。
候选人信息:
- 姓名: {name}
- 履历关键字: {labels}

请你写一段非常简短、专业、定制化且有诚意的寒暄(1-2句话以内)。
如果履历关键字中含有名校或知名大厂，请作为开场白拉近关系。
只输出打招呼的纯文本，不要包含引号、解释或其他任何内容。"""
    return qwen.call_qwen(prompt)

def process_candidates_dom(page, qwen: QwenEngine):
    print(">> 正在扫描屏幕上的名片...")
    
    # Boss直聘的按钮通常是 <a> 或 <div> 等非标准标签，所以我们摒弃 <button> 限定
    # 使用精确文字匹配来找到屏幕上的这些操作节点
    greet_buttons = []
    for text in ["打招呼", "沟通", "继续沟通", "聊一聊", "获取联系方式"]:
        # 获取匹配且可见的最深层文本节点
        locators = page.locator(f"xpath=//*[text()='{text}']").all()
        greet_buttons.extend(locators)
        
    print(f"✅ 在当前页面找到了 {len(greet_buttons)} 个可操作的沟通按钮！")
    
    for btn in greet_buttons:
        if not btn.is_visible():
            continue
            
        try:
            # 尝试从按钮往上找包含候选人信息的父元素卡片
            # 常见类名：.card-item, .recommend-card-wrapper, li 等
            card = btn.locator('xpath=./ancestor::li | ./ancestor::*[contains(@class, "card")] | ./ancestor::*[contains(@class, "item")]').first
            
            if card.count() == 0:
                print("⚠️ 无法定位到候选人名片主体，跳过此按钮。")
                continue
            
            # 粗略提取纯文本，交给大模型去理解
            card_text = card.inner_text().replace('\n', ' | ')
            # 从文本中简单切前几个词当名字
            name = card_text.split('|')[0].strip() if '|' in card_text else "牛人"
            
            print(f"\n>> 发现候选人: {name[:10]}...")
            print(f"   提取到的履历文本: {card_text[:50]}...")
            
            greeting = generate_greeting(name, card_text, qwen)
            print(f"   🤖 Qwen生成: {greeting}")
            
            # --- 物理外挂：点击并发送 ---
            print("   🖱️ 正在点击[打招呼]...")
            btn.scroll_into_view_if_needed()
            btn.click()
            time.sleep(2) # 等待聊天框弹出
            
            # 寻找输入框
            editor = page.locator('div[contenteditable="true"], textarea').first
            if editor.count() > 0 and editor.is_visible():
                print("   ⌨️ 正在真实模拟键盘输入...")
                editor.click()
                editor.fill("") # 清空
                page.keyboard.type(greeting, delay=50) # 延迟打字，极限模拟真人防封
                time.sleep(1)
                
                # 寻找发送按钮并点击
                send_btn = page.locator('button:has-text("发送")').first
                if send_btn.count() > 0:
                    send_btn.click()
                    print("   ✅ 消息发送成功！")
                else:
                    page.keyboard.press("Enter")
                    print("   ✅ (回车) 消息发送成功！")
                
                # 关闭弹出的聊天窗口，准备找下一个
                close_btn = page.locator('i.icon-close, button:has-text("关闭")').first
                if close_btn.count() > 0 and close_btn.is_visible():
                    close_btn.click()
                
            else:
                print("   ⚠️ 没找到聊天输入框！可能是页面结构变了或者是新标签页。")
            
            print("   💤 真人模式休眠 15 秒...")
            time.sleep(15)
            
        except Exception as e:
            print(f"   ❌ 处理此卡片时发生意外: {e}")

def main():
    print("🚀 正在启动对 Chrome 9224 端口的物理接管...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9224")
        except Exception as e:
            print("❌ 无法连接到浏览器！请确认你已经通过 --remote-debugging-port=9224 执行了 Chrome！")
            return

        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            if "boss" in page.url or "zhipin" in page.url:
                target_page = page
                break
                
        if not target_page:
            print("❌ 在你的 Chrome 中没找到打开着 Boss直聘 的网页，请先手动打开 boss.zhipin.com 并登录！")
            return
            
        print(f"✅ 成功穿透进入页面: {target_page.title()}")
        print("💡 请确保页面现在停留在【推荐】或者【牛人】列表，能看到打招呼的按钮。")
        
        target_page.bring_to_front() # 强制激活到前台
        
        qwen = QwenEngine()
        process_candidates_dom(target_page, qwen)
        
        print("\n🎉 本页名片处理完毕。你可以在屏幕上手动翻页，然后再执行一次本脚本。")

if __name__ == "__main__":
    main()
