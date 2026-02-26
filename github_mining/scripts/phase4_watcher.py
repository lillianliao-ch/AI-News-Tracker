import os
import time
import subprocess
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def is_mining_running():
    """检查 Phase 4 (auto_restart_wrapper 或 phase4) 是否还在跑"""
    try:
        # 使用 ps 查找包含相应用法特征的进程，过滤掉 grep 自己和这个 watcher 本身
        # 只要有个包含 phase4 和 auto_restart_wrapper 关键字的进行就代表存在
        cmd = "ps -ef | grep '[a]uto_restart_wrapper' | grep 'phase4'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        # 如果长度大于 0，说明存在
        return len(result.stdout.strip()) > 0
    except Exception as e:
        log(f"检查进程时出错: {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir) # github_mining
    root_dir = os.path.dirname(project_dir) # notion_rag
    
    pipeline_script = os.path.join(script_dir, 'run_pipeline_v3.py')
    expanded_file = os.path.join(project_dir, 'phase4_expanded.json')
    
    log("👁️  Phase 4 盯梢守护进程启动...")
    log(f"将每隔 5 分钟检查一次爬虫状态。")
    
    # 核心监控循环
    while True:
        if not is_mining_running():
            log("👀 未检测到 Phase 4 进程...")
            
            # 再等 35 秒，确保如果是 auto_restart 正在重启（默认30秒休眠）也被避开
            log("等待 35 秒确认是否为临时崩溃或延时重启...")
            time.sleep(35)
            
            if is_mining_running():
                log("🔙 发现进程又活了，是被 Wrapper 自动重启拉起来了。继续监控。")
                continue
                
            log("✨ 确认 AutoRestartWrapper 已经彻底退出。准备触发全量自动清洗流水线...")
            
            # 构建触发命令
            trigger_cmd = f"python3 {pipeline_script} --file {expanded_file}"
            log(f"▶️ 执行: {trigger_cmd}")
            
            try:
                # 触发并等它跑到结束
                subprocess.run(trigger_cmd, shell=True)
                log("✅ 全量自动化流水线 (Phase 5 -> Phase 2 -> Phase 3) 触发并执行完毕！")
                
                # 最后甚至可以静默触发发信脚本
                outreach_script = os.path.join(root_dir, 'personal-ai-headhunter', 'scripts', 'batch_ai_outreach.py')
                outreach_cmd = f"python3 {outreach_script} --tiers S,A+,A --channel linkedin"
                log(f"▶️ 开始自动起草顶牛跟进邮件: {outreach_cmd}")
                subprocess.run(outreach_cmd, shell=True)
                log("✅ S/A+/A 级大牛求撩草稿全部生成完毕！")
                
            except Exception as e:
                log(f"❌ 触发流水线时发生错误: {e}")
                
            log("🏁 盯梢守护进程历史使命完成，安全随之退出。")
            break
        else:
            log("✅ 爬虫正在疯狂吸入数据中... 休眠 5 分钟。")
            
        # 每隔 5 分钟检查一次
        time.sleep(300)

if __name__ == "__main__":
    main()
