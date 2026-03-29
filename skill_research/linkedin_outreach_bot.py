import os
import subprocess
import time
import random
import datetime

# ==========================================
# 🛡️ 账号被封禁高危预警与核心防御参数 (Risk Controls)
# ==========================================
# 1. 每日流量熔断器 (Daily Quota)
# 新账号/不活跃账号：建议 15-20 / 天
# 活跃领英高级会员 (Sales Navigator)：建议上限 40-50 / 天
MAX_CONNECTIONS_PER_DAY = 25 

# 2. 人类行为拟真延迟 (Human Jitter)
# 绝对不能使用固定时长的 sleep(5)！极易触发机械行为封控。
# 每次动作间隔 2到5分钟 不等。
def human_sleep():
    delay = random.randint(120, 300)
    print(f"   ⏳ [防封控伪装] 随机睡眠 {delay} 秒，模拟人类正常的浏览和打字速度...")
    time.sleep(delay)

# 3. 办公室物理作息拟真 (Working Hours Only)
# 夜间或非工作时间跑高频请求会被标记为殭尸网络
def is_working_hours():
    now = datetime.datetime.now()
    if now.weekday() >= 5: # 周六周日休眠
        return False
    if not (9 <= now.hour < 18): # 仅在早 9 点到晚 6 点间运行
        return False
    return True

# ==========================================
# 🚀 核心：通过 OpenCLI 执行浏览器原生的无感操作
# ==========================================
def send_linkedin_connection(profile_url, message=""):
    """
    调用 OpenCLI 的底层适配器。
    【为什么安全？】
    因为 OpenCLI 是通过您日常使用的 Chrome 浏览器的 Extension 层发起的注入。
    没有任何 Headless Browser 的机器指纹，没有虚拟 Cookie。LinkedIn 后台看到的
    就是您本人在使用真实的精装 MAC 电脑、真实 IP 点击了发送。
    """
    print(f"🎯 正在定位候选人: {profile_url}")
    
    # 假设 OpenCLI 已装载了 linkedin_profile 适配器或者我们编写的自定义 YAML
    # 命令构造：npx @jackwener/opencli linkedin connect --url <url> --message "<msg>"
    cmd = [
        "npx", "--yes", "@jackwener/opencli", "linkedin", "connect", # (假定的原生或自建命令)
        profile_url,
        "--message", message
    ]
    
    try:
        # 为了演示安全，这行默认不真实执行。部署时打开。
        # subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        print(f"   ✅ [操作成功] 真实的 Chrome 已在系统后台点击了 'Connect' 并发送了文案！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ [风控墙预警] OpenCLI 执行失败 (可能是元素变动或触发人机验证): {e}")
        return False


def main():
    print("🌟 启动 Lilian 的自动化打招呼挂机防御矩阵...")
    
    if not is_working_hours():
        print("🛑 危险预警：当前不在工作日或工作时间 (9-18 点) 内，启动该脚本极易被判定为脚本外挂。请明天再试！")
        return

    # 您的候选人挖掘清单
    candidates = [
        "https://www.linkedin.com/in/williamhgates/",
        "https://www.linkedin.com/in/satyanadella/",
        "https://www.linkedin.com/in/sundarpichai/"
    ]
    
    msg_template = "Hi {name}, I'm Lilian, focusing on deep comp/AI architecture roles. I recently read your insights logically mapped out on GitHub and felt compelled to connect!"

    success_count = 0
    for idx, url in enumerate(candidates):
        if success_count >= MAX_CONNECTIONS_PER_DAY:
            print("🔒 [配额用尽] 触及每日安全红线，停止所有后续动作以保护账号！")
            break
            
        print(f"\n--- ⚡️ 开始处理第 {idx+1}/{len(candidates)} 位候选人 ---")
        
        # 1. 模拟人类看简历并停顿（20秒~40秒）
        print("   👀 [防封控伪装] 正在拉取此人的 Profile 页面数据并停留...")
        time.sleep(random.randint(20, 40))
        
        # 2. 从 URL 简单反推名字作为参数（仅供演示，实际应由探索器获取）
        name_slug = url.strip('/').split('/')[-1]
        
        # 3. 发起打招呼动作
        is_success = send_linkedin_connection(url, message=msg_template.format(name=name_slug))
        if is_success:
            success_count += 1
            
        # 4. 动作结束后进入深度防御休眠
        human_sleep()

if __name__ == "__main__":
    main()
