#!/usr/bin/env python3
import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

# ========================================================
# Playwright CDP 核心交互封装 (直连受控 Chrome 9224)
# ========================================================

def find_active_ai_page(context):
    """尝试找到一个可能开着 AI 对话的页面"""
    for page in context.pages:
        try:
            title = page.title().lower()
            url = page.url.lower()
            if any(keyword in url or keyword in title for keyword in ['chatgpt', 'claude', 'deepseek', 'kimi', 'qwen', 'yuanbao', 'doubao']):
                return page
        except Exception:
            continue
    
    # 如果没找到特定的，就返回第一个打开且未报错的页面
    for page in context.pages:
        try:
            page.title()
            return page
        except Exception:
            continue
    return None

def inject_prompt_and_send(page, prompt):
    """通过 Playwright 物理模拟键盘注入 Prompt"""
    print(f"   🤖 [CDP] 正在向 {page.title()} 注入指令...")
    
    editor = page.locator('textarea, div[contenteditable="true"]').last
    if editor.count() == 0 or not editor.is_visible():
        print("   ⚠️ 无法定位到输入框，尝试使用 fallback 键盘输入！请确保光标已经在输入框内。")
        page.keyboard.type(prompt, delay=5)
        page.keyboard.press("Meta+Enter") 
        page.keyboard.press("Enter")
        time.sleep(30)
        return

    editor.click()
    page.keyboard.press("Meta+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(prompt, delay=2) # 提速打字
    
    send_btn = page.locator('button[aria-label="Send message"], button[data-testid="send-button"], button:has(svg)').last
    if send_btn.count() > 0 and send_btn.is_visible() and not send_btn.is_disabled():
        send_btn.click()
    else:
         page.keyboard.press("Meta+Enter")
         page.keyboard.press("Enter")
         
    print("   ⏳ 等待 AI 思考与生成 (休眠30秒以保证生成完毕)...")
    time.sleep(30)

def extract_latest_code(page) -> str:
    """提取页面上最新的代码块"""
    print("   📥 [CDP] 正在提取页面最新生成内容...")
    locators = page.locator('pre code, .code-block, div[class*="code"], code').all()
    if not locators:
        return ""
    for loc in reversed(locators):
        if loc.is_visible():
            text = loc.inner_text()
            if text.strip() and len(text) > 20:
                return text.strip()
    return ""

def connect_browser_and_run(url, scenario_desc):
    print("🚀 正在通过 CDP 物理接管受控浏览器...")
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
        
        # 1. 评估
        decision_dict, repo_dir = phase_1_valuation(page, url, scenario_desc)
        
        try:
            if decision_dict.get("is_valuable", False):
                poc = decision_dict.get("poc_plan", "请结合库的介绍尝试测试。")
                if phase_2_verification(page, repo_dir, poc):
                    phase_3_integration(page, repo_dir, url)
                else:
                    print("\n   🚫 停止推进：沙盒复现未能通过。")
            else:
                print("\n   🚫 停止推进：该库被判定为完全脱离场景价值。")
        finally:
            cleanup_sandbox(repo_dir)

# ========================================================
# 阶段 1：库价值评估 (Valuation)
# ========================================================

def phase_1_valuation(page, repo_url: str, scenario: str) -> dict:
    print(f"\n🚀 === [Phase 1] 价值评估: {repo_url} ===")
    
    sandbox_dir = "/tmp/ai_research_sandbox"
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    target_dir = os.path.join(sandbox_dir, repo_name)
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir) # 每次运行前强行清理旧文件
        
    print(f"   📦 正在克隆仓库至 {target_dir} (阅后即焚)...")
    subprocess.run(["git", "clone", "--depth", "1", repo_url, target_dir], capture_output=True)
    
    readme_paths = [os.path.join(target_dir, "README.md"), os.path.join(target_dir, "readme.md"), os.path.join(target_dir, "docs/README_en.md")]
    readme_content = ""
    for rp in readme_paths:
        if os.path.exists(rp):
            with open(rp, "r", encoding="utf-8") as f:
                readme_content = f.read()[:8000]
            break
            
    if not readme_content:
        return {"is_valuable": False}, target_dir

    prompt = (
        f"我现在的业务场景是：【{scenario}】\n\n"
        f"请阅读这个 Github 项目的 README（节选）：\n{readme_content}\n\n"
        "请分析这个库对我的场景是否有用。\n"
        "请你只输出一段纯净的 JSON 代码块：\n"
        "{\n"
        '  "is_valuable": true/false,\n'
        '  "reason": "原因",\n'
        '  "poc_plan": "如果 true，简述验证其核心功能的测试脚本逻辑"\n'
        "}"
    )
    
    inject_prompt_and_send(page, prompt)
    output = extract_latest_code(page)
    
    try:
        if output.startswith("```json"): output = output[7:]
        elif output.startswith("```"): output = output[3:]
        if output.endswith("```"): output = output[:-3]
            
        decision = json.loads(output.strip())
        print(f"   📊 评估结论: {decision.get('is_valuable', False)} | 理由: {decision.get('reason', '')}")
        return decision, target_dir
    except Exception as e:
        print(f"   ❌ JSON 解析失败, 输出截抄: {output[:100]}")
        return {"is_valuable": False}, target_dir


# ========================================================
# 阶段 2：安全沙盒盲测 (TDD Verification without Pollution)
# ========================================================

def phase_2_verification(page, target_dir: str, poc_plan: str) -> bool:
    print("\n🔬 === [Phase 2] 创建纯净隔离沙盒并进行验证 ===")
    venv_dir = os.path.join(target_dir, ".venv")
    print(f"   🛡️ 正在创建一次性虚拟环境隔离依赖: {venv_dir}")
    subprocess.run([sys.executable, "-m", "venv", venv_dir], capture_output=True)
    
    pip_exe = os.path.join(venv_dir, "bin", "pip")
    python_exe = os.path.join(venv_dir, "bin", "python")
    
    requirements_path = os.path.join(target_dir, "requirements.txt")
    if os.path.exists(requirements_path):
        print("   📦 发现依赖文件，正在虚拟环境中静默安装依赖...")
        subprocess.run([pip_exe, "install", "-r", requirements_path], capture_output=True)

    prompt = (
        f"该库的评估通过了。既然有用，请根据你提议的方案：【{poc_plan}】\n"
        f"为我写一个完全可以独立运行的 Python 验证脚本 (test_poc.py)。\n"
        "只输出包含完整测试逻辑的纯 Python 代码块！"
    )
    inject_prompt_and_send(page, prompt)
    
    max_retries = 3
    retry_count = 0
    poc_script_path = os.path.join(target_dir, "test_poc.py")
    
    while retry_count < max_retries:
        code = extract_latest_code(page)
        if not code:
            print("⚠️ 未能提取到代码块，增加 10 秒等待...")
            time.sleep(10)
            code = extract_latest_code(page)

        if code.startswith("```python"): code = code[9:]
        elif code.startswith("```"): code = code[3:]
        if code.endswith("```"): code = code[:-3]
        
        with open(poc_script_path, "w", encoding="utf-8") as f:
            f.write(code.strip())
            
        print(f"   🔄 正在沙盒中隔离执行代码... (尝试 {retry_count+1}/{max_retries})")
        res = subprocess.run([python_exe, "test_poc.py"], cwd=target_dir, capture_output=True, text=True)
        
        if res.returncode == 0:
            print("   ✅ PoC 测试在本地跑通了！该库确有可用价值。")
            return True
        else:
            error_log = res.stderr if res.stderr else res.stdout
            print(f"   ❌ 测试失败！准备让 AI 修复代码... 报错摘录: {error_log[-200:].strip()}")
            feedback = f"你在上面写的 PoC 脚本执行测试失败了，这是终端抛出的报错日志：\n{error_log}\n请修复 Bug 并重新输出代码块。"
            inject_prompt_and_send(page, feedback)
            retry_count += 1
            
    print("   ☠️ 彻底修不好，判定该库太坑或文档过期，放弃验证。")
    return False

# ========================================================
# 阶段 3：输出独立调研报告 (Research Report Generation)
# ========================================================

def phase_3_integration(page, target_dir: str, repo_url: str):
    print("\n📝 === [Phase 3] 输出独立调研报告与 Adapter 建议 ===")
    
    prompt = (
        f"该 Github 库 ({repo_url}) 的核心验证已经跑通。\n"
        "请你写一份给资深架构师的《调研与应用独立报告》，包含：\n"
        "1. 这个库的杀手级功能总结。\n"
        "2. 一段独立的 Adapter/Wrapper 示例代码，展示将来我们如果要整合它，可以怎么写。\n"
        "3. 它的优缺点分析。\n"
        "只输出完整的 Markdown 文档，不要包含针对本步骤的额外解释。"
    )
    inject_prompt_and_send(page, prompt)
    
    print("   💾 正在提取调研报告...")
    report_md = extract_latest_code(page)
    
    report_dir = "/Users/lillianliao/notion_rag/skill_research/auto_reports"
    os.makedirs(report_dir, exist_ok=True)
    
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    out_file = os.path.join(report_dir, f"{repo_name}_research_report.md")
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_md.strip())
        
    print(f"   🎉 全自动调研流结束！详细的选型报告和示例代码已生成到: {out_file}")

# ========================================================
# 终极清理机制 (Cleanup)
# ========================================================
def cleanup_sandbox(target_dir: str):
    if os.path.exists(target_dir):
        print(f"\n   🧹 [安全回收] 正在彻底擦除临时沙盒与虚拟环境: {target_dir}")
        shutil.rmtree(target_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 github_auto_researcher.py <Github_URL> <你的使用场景描述>")
        sys.exit(1)
        
    url = sys.argv[1]
    scenario_desc = sys.argv[2]
    connect_browser_and_run(url, scenario_desc)
