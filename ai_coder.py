import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

def find_active_ai_page(context):
    """尝试找到一个可能开着 AI 对话的页面"""
    for page in context.pages:
        try:
            title = page.title().lower()
            url = page.url.lower()
            if any(keyword in url or keyword in title for keyword in ['chatgpt', 'claude', 'deepseek', 'kimi', 'qwen', 'yuanbao', 'doubao']):
                return page
        except Exception:
            # 忽略因导航或页面销毁导致的报错
            continue
    
    # 如果没找到特定的，就返回第一个打开且未报错的页面
    for page in context.pages:
        try:
            page.title()
            return page
        except Exception:
            continue
    return None

def extract_latest_code(page):
    """尝试从页面提取最新的代码块"""
    # 很多 AI 界面使用 <pre><code> 或者带 copy 按钮的代码块
    locators = page.locator('pre code, .code-block, div[class*="code"], code').all()
    if not locators:
        return ""
    # 取最后一个（通常是最新的回复）
    for loc in reversed(locators):
        if loc.is_visible():
            text = loc.inner_text()
            if text.strip() and len(text) > 20: # 简单的过滤，防止取到单行行内代码
                return text
    return ""

def inject_prompt_and_send(page, prompt):
    print(f"   ⌨️ 正在输入 Prompt:\n     {prompt[:50]}...")
    
    # 尝试找到常见的输入框 (textarea 或者 contenteditable)
    editor = page.locator('textarea, div[contenteditable="true"]').last
    if editor.count() == 0 or not editor.is_visible():
        print("   ⚠️ 无法定位到输入框，尝试使用 fallback 键盘输入！请确保光标已经在输入框内。")
        page.keyboard.type(prompt, delay=10)
        page.keyboard.press("Meta+Enter") # 很多网页版需要 Cmd+Enter 发送
        page.keyboard.press("Enter")
        return

    editor.click()
    # 全选并清空（防止有旧内容）
    page.keyboard.press("Meta+A")
    page.keyboard.press("Backspace")
    
    # 注入内容
    page.keyboard.type(prompt, delay=5)
    
    # 尝试点击发送按钮，一般是 SVG 或者是带 Send 关键字的 button
    send_btn = page.locator('button[aria-label="Send message"], button[data-testid="send-button"], button:has(svg)').last
    if send_btn.count() > 0 and send_btn.is_visible() and not send_btn.is_disabled():
        send_btn.click()
    else:
         page.keyboard.press("Meta+Enter")
         page.keyboard.press("Enter")

def main():
    print("🚀 正在启动 CDP 物理接管 (TDD Loop)...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9224")
        except Exception as e:
            print("❌ 无法连接到浏览器！请确认已通过 --remote-debugging-port=9224 启动 Chrome。")
            return

        context = browser.contexts[0]
        page = find_active_ai_page(context)
        
        if not page:
            print("❌ 没有找到可用的页面！")
            return
            
        print(f"✅ 成功穿透页面: 【{page.title()}】")
        page.bring_to_front()
        
        # 初始任务
        initial_prompt = (
            "请使用 Python 写一个函数，用于验证字符串是否为合法的电子邮箱格式。"
            "同时在文件内部包含完整的 unittest 测试用例（涵盖正常邮箱、没有@、没有域名等异常情况）。"
            "极其重要：请你只输出包含代码的 Markdown 代码块，不要有任何前言后语和汉字解释！"
            "只需直接给我写最终的完整 Python 代码即可。"
        )
        
        inject_prompt_and_send(page, initial_prompt)
        print("⏳ 等待 AI 生成初始代码 (休眠 15 秒)...")
        time.sleep(15)

        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            code = extract_latest_code(page)
            if not code:
                print("⚠️ 未能提取到代码块，增加 10 秒等待...")
                time.sleep(10)
                code = extract_latest_code(page)
                
            if not code:
                print("❌ 提取代码彻底失败，请人工检查当前页面上 AI 是否输出了代码框。")
                break
                
            # 去除一些可能的 markdown 标记
            if code.startswith("```python"):
                code = code[9:]
            elif code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()
            
            # 保存到本地文件
            test_file = "/tmp/auto_tdd_test.py"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(code)
                
            print(f"💾 提取到代码 ({len(code)} 字符)，已保存至 {test_file}")
            print(f"🔄 正在本地执行测试... (第 {retry_count+1} 次尝试)")
            
            # 本地运行
            result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("🎉 测试通过！核心逻辑代码生成成功，自动化编码结束。")
                print("==== AI 最终代码 ====")
                print(code)
                print("=====================")
                break
            else:
                error_log = result.stderr if result.stderr else result.stdout
                print(f"❌ 测试失败！准备将错误日志回传给 AI 修复...\n【日志摘要】: {error_log[-300:]}")
                
                feedback_prompt = (
                    "你在上面写的代码执行测试失败了，这是终端的报错日志：\n"
                    f"{error_log}\n"
                    "请分析原因，修复 Bug，并重新输出完整的包含测试的 Python 代码块。且依然只输出代码块，不要其他废话。"
                )
                inject_prompt_and_send(page, feedback_prompt)
                
                print("⏳ 等待 AI 修复生成 (休眠 15 秒)...")
                time.sleep(15)
                retry_count += 1
                
        if retry_count == max_retries:
             print("⚠️ 达到最大重试次数，AI 修复失败，请人工介入。")

if __name__ == "__main__":
    main()
