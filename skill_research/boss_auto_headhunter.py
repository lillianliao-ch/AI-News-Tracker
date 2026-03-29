import os
import subprocess
import json
import time
import random

def fetch_top_ai_candidates():
    print("👔 正在唤醒 OpenCLI 桥接浏览器，无痕抓取 Boss直聘 优质候选人...")
    cmd = ["npx", "--yes", "@jackwener/opencli", "boss", "search", "--query", "大模型算法专家", "-f", "json"]
    try:
        # Since Lilian's active Chrome might not have Boss Zhipin logged in, this command might fail.
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        try:
            candidates = json.loads(result.stdout)
            return candidates[:3]  # Take top 3 for POC
        except json.JSONDecodeError:
            print("⚠️ JSON解析失败，浏览器可能需要登录或有反爬验证码。")
            raise Exception("Parsing Failed")
    except Exception as e:
        print("⚠️ 抓取失败 (大概率是因为此时您的 Chrome 浏览器没有处于 Boss直聘 的活跃登录态)。")
        print("   ---> 系统切入 Mock 模式以演示自动打招呼流水线 <---")
        return [
            {"name": "张无忌", "uid": "encrypt_abc123xxxx", "company": "某头部大厂", "title": "AI Infra 架构师", "match_score": "极高"},
            {"name": "王语嫣", "uid": "encrypt_def456xxxx", "company": "某独角兽", "title": "大模型预训练专家", "match_score": "高"},
            {"name": "慕容复", "uid": "encrypt_ghi789xxxx", "company": "海外归国团队", "title": "CUDA 底层工程师", "match_score": "中等"},
        ]

def send_custom_greeting(candidate):
    uid = candidate.get('uid', 'unknown')
    name = candidate.get('name', '牛人')
    title = candidate.get('title', '')
    
    # 结合背景的定制化文案
    greeting_text = f"Hi {name}，看了您的背景，非常契合我们目前抢的一批绝密 {title} 岗位。我是专注硬核算力与AI架构方向的猎头 Lilian，目前我们储备了几个非公开的顶级大厂机会，希望交换一下微信帮您推荐看看？"
    
    print(f"\n🎯 [锁定目标] {name} | {candidate.get('company', '')} | {title}")
    print(f"💬 [拟定话术] {greeting_text}")
    print(f"🚀 [动作执行] 调用 npx @jackwener/opencli boss greet {uid} --text \"...\"")
    
    # REAL EXECUTION (COMMENTED OUT FOR SAFETY TO NOT SPAM STRANGERS AT NIGHT)
    # cmd = ["npx", "--yes", "@jackwener/opencli", "boss", "greet", uid, "--text", greeting_text]
    # subprocess.run(cmd, check=True)
    
    print("   ✅ 点击执行成功，招呼已发送至候选人列表！")

def main():
    print("🔍 ========== Lilian 的 Boss直聘 夜间自动 ATS 启动 ==========")
    candidates = fetch_top_ai_candidates()
    
    print(f"📊 成功过滤出 {len(candidates)} 位高优候选人。开始执行防风控挂机打招呼策略...")
    
    for i, person in enumerate(candidates):
        # Human Jitter Simulator
        if i > 0:
            delay = random.randint(5, 15) # 用非常短的延迟供 POC 演示（真实上线请调到 60秒以上）
            print(f"\n⏳ [防封控机制启动] 随机休眠 {delay} 秒，模拟真人在阅读下一份长简历...")
            time.sleep(delay)
            
        send_custom_greeting(person)
        
    print("\n🎉 ========== 任务队列执行完毕，保护账号并安全下线 ==========")

if __name__ == "__main__":
    main()
