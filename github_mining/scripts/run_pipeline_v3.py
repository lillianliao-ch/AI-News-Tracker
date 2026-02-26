import os
import subprocess
import time
from datetime import datetime
import argparse

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"🚀 自动流水线步骤 {step_num}: {title}")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

def run_command(command, description):
    try:
        print(f"▶️ 执行命令: {command}")
        # 使用 subprocess.run，加上 check=True，如果有非0退出码会抛异常
        result = subprocess.run(
            command, 
            shell=True,
            capture_output=False, # 直接打印到终端
            text=True
        )
        if result.returncode != 0:
            print(f"\n❌ {description} 失败 (Exit Code: {result.returncode})")
            return False
        print(f"\n✅ {description} 成功完成！")
        return True
    except Exception as e:
        print(f"\n❌ {description} 执行异常: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="AI猎头: Phase 4 产出数据的后续全自动处理流水线")
    parser.add_argument("--file", type=str, default="phase4_expanded.json", help="Phase 4 挖掘生成的 JSON 结果文件")
    parser.add_argument("--skip-import", action="store_true", help="跳过导入步骤，直接运行 V3 探活与打分")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir) # github_mining
    root_dir = os.path.dirname(project_dir) # notion_rag
    
    target_file = os.path.join(project_dir, args.file)

    print(f"\n🎯 准备启动 AI猎头数据收割全自动流水线")
    print(f"📂 目标处理文件: {target_file}")

    if not args.skip_import:
        if not os.path.exists(target_file):
            print(f"\n⚠️ 错误: 找不到文件 {target_file}")
            print("请确认 Phase 4 爬虫是否已经跑完并生成了该文件。")
            return

        # ==================== 步骤 1: Phase 5 导入数据 ====================
        print_step(1, "Phase 5 - 批量将爬虫结果导入 SQLite 数据库")
        cmd_import = f"cd {os.path.join(root_dir, 'personal-ai-headhunter')} && python3 import_github_candidates.py --file {target_file}"
        if not run_command(cmd_import, "数据入库 (Phase 5)"):
            return
        
        # 为了防止数据库锁，稍微等两秒
        time.sleep(2)

    # ==================== 步骤 2: Phase 2 V3 探活过滤 ====================
    print_step(2, "Phase 2 V3 - 运行本地 AI 浓度探测算法（过滤非AI人才）")
    cmd_phase2 = f"python3 {os.path.join(script_dir, 'github_network_miner.py')} phase2_v3 --input {target_file}"
    if not run_command(cmd_phase2, "V3 AI探索与过滤 (Phase 2)"):
        return
        
    time.sleep(2)

    # ==================== 步骤 3: Phase 3 V3 打标签分级 ====================
    print_step(3, "Phase 3 V3 - 运行 Tier 评级算法（判定 S/A/B 级）")
    cmd_phase3 = f"python3 {os.path.join(script_dir, 'github_network_miner.py')} phase3_v3"
    
    # 这一步同样需要切到 personal-ai-headhunter 目录执行打标
    cmd_tier_update = f"cd {os.path.join(root_dir, 'personal-ai-headhunter')} && python3 batch_update_tiers.py"
    
    if not run_command(cmd_phase3, "V3 AI 联合判定 (Phase 3)"):
        return
        
    if not run_command(cmd_tier_update, "V3 统一落库评级 (Phase 5 打标)"):
        return

    print(f"\n{'='*60}")
    print(f"🎉 全部自动化流水线执行完毕！")
    print(f"📌 下一步建议: 你可以运行 Batch AI Outreach 脚本，为新产生的 S/A+/A 大牛自动生成破冰邮件。")
    print(f"   命令参考: python3 personal-ai-headhunter/scripts/batch_ai_outreach.py --tiers S,A+,A")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
