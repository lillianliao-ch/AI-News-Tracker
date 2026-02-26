#!/usr/bin/env python3
"""
端到端完整执行脚本 - Phase 4 → Phase 3 → Phase 3.5

解决Phase 4输出不完整的问题，端到端生成完整可用的候选人数据
"""

import os
import sys
import time
import argparse
from datetime import datetime

# 添加scripts目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from github_network_miner import GitHubNetworkMiner
from pathlib import Path

def print_header(title):
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

def print_step(step_num, description):
    print(f"\n【步骤 {step_num}/4】{description}")
    print("-" * 70)

def run_phase4():
    """Phase 4: 社交网络扩展"""
    print_step(1, "Phase 4 - 社交网络扩展（发现新人才）")

    # 检查phase4_expanded.json是否已存在
    phase4_file = Path(script_dir) / "github_mining" / "phase4_expanded.json"
    if phase4_file.exists():
        print(f"✅ Phase 4 输出文件已存在: {phase4_file}")
        import json
        data = json.load(open(phase4_file))
        print(f"   已发现 {len(data)} 个AI人才")
        return True

    # 从环境变量或配置文件获取token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        # 尝试从配置文件读取
        try:
            import importlib.util
            config_path = script_dir / "github_hunter_config.py"
            spec = importlib.util.spec_from_file_location("github_hunter_config", config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            token = config_module.GITHUB_CONFIG.get("token")
            if token:
                print(f"🔑 从配置文件读取到 GitHub Token")
        except Exception as e:
            pass

    if not token:
        print("❌ 错误: 未设置GITHUB_TOKEN环境变量")
        print("   方法1: 执行 export GITHUB_TOKEN='your_token_here'")
        print("   方法2: 编辑 scripts/github_hunter_config.py，设置 token 字段")
        print("   获取Token: GitHub Settings -> Developer settings -> Personal access tokens")
        return False

    miner = GitHubNetworkMiner(token=token)
    try:
        miner.phase4_expand(
            seed_tier="S,A+,A",
            min_cooccurrence=3
        )
        return True
    except Exception as e:
        print(f"❌ Phase 4 执行失败: {e}")
        return False

def run_phase3():
    """Phase 3: Repos深度信息补强"""
    print_step(2, "Phase 3 - Repos深度信息补强（获取技术栈）")

    phase4_file = Path(script_dir) / "github_mining" / "phase4_expanded.json"
    if not phase4_file.exists():
        print(f"❌ 错误: 未找到Phase 4输出文件: {phase4_file}")
        print("   请先运行Phase 4")
        return False

    # 从环境变量或配置文件获取token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        # 尝试从配置文件读取
        try:
            import importlib.util
            config_path = script_dir / "github_hunter_config.py"
            spec = importlib.util.spec_from_file_location("github_hunter_config", config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            token = config_module.GITHUB_CONFIG.get("token")
            if token:
                print(f"🔑 从配置文件读取到 GitHub Token")
        except Exception as e:
            pass

    if not token:
        print("❌ 错误: 未设置GITHUB_TOKEN环境变量")
        print("   方法1: 执行 export GITHUB_TOKEN='your_token_here'")
        print("   方法2: 编辑 scripts/github_hunter_config.py，设置 token 字段")
        print("   获取Token: GitHub Settings -> Developer settings -> Personal access tokens")
        return False

    miner = GitHubNetworkMiner(token=token)
    try:
        # 指定输入文件为Phase 4输出
        phase3_output = Path(script_dir) / "github_mining" / "phase3_from_phase4.json"
        miner.phase3_enrich(input_file=str(phase4_file))
        print(f"✅ Phase 3 补强完成，输出: {phase3_output}")
        return True
    except Exception as e:
        print(f"❌ Phase 3 执行失败: {e}")
        return False

def run_phase3_5():
    """Phase 3.5: 个人主页深度信息补强"""
    print_step(3, "Phase 3.5 - 个人主页爬取（LinkedIn、经历、论文）")

    phase3_output = Path(script_dir) / "github_mining" / "phase3_from_phase4.json"
    if not phase3_output.exists():
        print(f"❌ 错误: 未找到Phase 3输出文件: {phase3_output}")
        print("   请先运行Phase 3")
        return False

    miner = GitHubNetworkMiner(token=os.environ.get("GITHUB_TOKEN"))
    try:
        # 指定输入文件为Phase 3补强输出
        final_output = Path(script_dir) / "github_mining" / "phase4_final_enriched.json"
        miner.phase3_5_enrich(input_file=str(phase3_output))
        print(f"✅ Phase 3.5 补强完成，输出: {final_output}")
        return True
    except Exception as e:
        print(f"❌ Phase 3.5 执行失败: {e}")
        return False

def show_final_stats():
    """显示最终统计数据"""
    print_step(4, "数据质量统计")

    final_file = Path(script_dir) / "github_mining" / "phase4_final_enriched.json"
    if not final_file.exists():
        print(f"❌ 错误: 未找到最终输出文件: {final_file}")
        return

    import json
    from collections import Counter

    data = json.load(open(final_file))
    total = len(data)

    print(f"✅ 总用户数: {total}")

    # 统计关键字段
    has_linkedin = sum(1 for d in data if d.get('linkedin_url'))
    has_work_exp = sum(1 for d in data if d.get('work_experience'))
    has_education = sum(1 for d in data if d.get('education'))
    has_extra_emails = sum(1 for d in data if d.get('extra_emails'))
    has_scholar = sum(1 for d in data if d.get('scholar_url'))
    has_venues = sum(1 for d in data if d.get('top_venues_count', 0) > 0)

    print(f"\n📊 深度信息覆盖率:")
    print(f"   LinkedIn:        {has_linkedin:4d}/{total:4d} ({has_linkedin*100//total}%)")
    print(f"   工作经历:        {has_work_exp:4d}/{total:4d} ({has_work_exp*100//total}%)")
    print(f"   教育背景:        {has_education:4d}/{total:4d} ({has_education*100//total}%)")
    print(f"   额外邮箱:        {has_extra_emails:4d}/{total:4d} ({has_extra_emails*100//total}%)")
    print(f"   Google Scholar:  {has_scholar:4d}/{total:4d} ({has_scholar*100//total}%)")
    print(f"   顶会论文:        {has_venues:4d}/{total:4d} ({has_venues*100//total}%)")

    # 检查数据完整性
    print(f"\n✅ 数据完整性检查:")
    has_primary_email = sum(1 for d in data if d.get('email'))
    has_any_email = sum(1 for d in data if d.get('email') or d.get('all_emails'))
    total_email = has_any_email
    print(f"   邮箱覆盖率:      {total_email:4d}/{total:4d} ({total_email*100//total}%)")

    # AI评分统计
    ai_scores = [d.get('ai_score', 0) for d in data]
    avg_score = sum(ai_scores) / len(ai_scores) if ai_scores else 0
    high_score = sum(1 for s in ai_scores if s >= 2.0)
    print(f"   AI评分:          平均 {avg_score:.2f}, 高分(≥2.0) {high_score} 人")

    print(f"\n📂 最终输出文件:")
    print(f"   JSON: {final_file}")
    csv_file = final_file.with_suffix('.csv')
    print(f"   CSV:  {csv_file}")

    return True

def main():
    parser = argparse.ArgumentParser(
        description="端到端完整执行: Phase 4 → Phase 3 → Phase 3.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 完整执行所有阶段
  python3 end_to_end_pipeline.py

  # 跳过已完成的阶段
  python3 end_to_end_pipeline.py --skip-phase4

  # 指定Phase 4种子tier
  python3 end_to_end_pipeline.py --seed-tier S,A --min-cooccurrence 5
        """
    )

    parser.add_argument("--skip-phase4", action="store_true", help="跳过Phase 4（如果已完成）")
    parser.add_argument("--skip-phase3", action="store_true", help="跳过Phase 3（如果已完成）")
    parser.add_argument("--skip-phase3_5", action="store_true", help="跳过Phase 3.5（如果已完成）")
    parser.add_argument("--seed-tier", type=str, default="S,A+,A", help="Phase 4种子tier")
    parser.add_argument("--min-cooccurrence", type=int, default=3, help="Phase 4最小共现次数")

    args = parser.parse_args()

    # 检查环境变量或配置文件中的token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        # 尝试从配置文件读取
        try:
            import importlib.util
            config_path = script_dir / "github_hunter_config.py"
            spec = importlib.util.spec_from_file_location("github_hunter_config", config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            token = config_module.GITHUB_CONFIG.get("token")
        except Exception:
            pass

    if not token:
        print("❌ 错误: 未设置GITHUB_TOKEN环境变量")
        print("   方法1: 执行 export GITHUB_TOKEN='your_token_here'")
        print("   方法2: 编辑 scripts/github_hunter_config.py，设置 token 字段")
        print("   获取Token: GitHub Settings -> Developer settings -> Personal access tokens")
        sys.exit(1)

    print_header("GitHub 网络挖掘 - 端到端完整执行")

    results = []

    # Phase 4: 社交网络扩展
    if not args.skip_phase4:
        if not run_phase4():
            print("\n❌ Phase 4 失败，终止执行")
            sys.exit(1)
        results.append("✅ Phase 4 完成")
        time.sleep(2)  # 等待文件保存

    # Phase 3: Repos深度信息补强
    if not args.skip_phase3:
        if not run_phase3():
            print("\n❌ Phase 3 失败，终止执行")
            sys.exit(1)
        results.append("✅ Phase 3 补强完成")
        time.sleep(2)

    # Phase 3.5: 个人主页深度信息补强
    if not args.skip_phase3_5:
        if not run_phase3_5():
            print("\n❌ Phase 3.5 失败，终止执行")
            sys.exit(1)
        results.append("✅ Phase 3.5 补强完成")

    # 显示最终统计
    if not show_final_stats():
        sys.exit(1)

    print_header("🎉 端到端执行完成")
    for result in results:
        print(f"  {result}")

    print(f"\n📋 下一步:")
    print(f"  1. 查看最终数据: cat github_mining/phase4_final_enriched.json")
    print(f"  2. 导入数据库: cd ../personal-ai-headhunter && python3 import_github_candidates.py --file github_mining/phase4_final_enriched.json")
    print(f"  3. 运行评级: python3 batch_update_tiers.py")
    print(f"  4. 生成触达邮件: python3 batch_ai_outreach.py --tiers S,A+,A")

if __name__ == "__main__":
    main()