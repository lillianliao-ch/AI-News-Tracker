#!/usr/bin/env python3
"""
对 Phase 4 的 11,976 人运行 Phase 3.5 + 4.5 完整富化流程

执行流程：
1. Phase 3.5: 个人主页爬取（LinkedIn、个人网站、Google Scholar）
2. Phase 4.5: LLM 深度富化（工作履历、教育背景、技能、谈话点）

预计时间：6-8 小时
预计富化：~3,600 人
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加 scripts 目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from github_network_miner import GitHubNetworkMiner

def log(msg: str):
    """日志输出"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def main():
    log("=" * 80)
    log("🚀 Phase 3.5 + 4.5 完整富化流程")
    log("=" * 80)

    # 输入文件
    phase4_input = script_dir / "github_mining" / "phase4_expanded.json"

    if not phase4_input.exists():
        log(f"❌ 错误: Phase 4 输入文件不存在: {phase4_input}")
        return

    import json
    with open(phase4_input) as f:
        data = json.load(f)

    log(f"📖 输入文件: {phase4_input}")
    log(f"   总候选人数: {len(data)} 人")

    # 获取 GitHub Token
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
                log(f"🔑 从配置文件读取到 GitHub Token")
        except Exception as e:
            pass

    if not token:
        log("❌ 错误: 未配置 GitHub Token")
        log("   请设置环境变量或在 github_hunter_config.py 中配置")
        return

    log("✅ GitHub Token 已配置")

    # 初始化 miner
    miner = GitHubNetworkMiner(token=token)

    # Phase 3.5: 个人主页爬取
    log("\n" + "=" * 80)
    log("【步骤 1/2】Phase 3.5: 个人主页深度爬取")
    log("=" * 80)
    log("⏰ 预计时间: 3-4 小时")
    log("🎯 目标: 爬取个人网站、LinkedIn、Google Scholar")

    try:
        miner.phase3_5_enrich(input_file=str(phase4_input))
        log("✅ Phase 3.5 完成")

        # 检查输出文件
        phase35_output = script_dir / "github_mining" / "phase4_final_enriched.json"
        if phase35_output.exists():
            log(f"📁 输出文件: {phase35_output}")
            with open(phase35_output) as f:
                enriched = json.load(f)
            log(f"   富化人数: {len(enriched)} 人")

            # 统计
            with_linkedin = sum(1 for d in enriched if d.get('linkedin_url'))
            with_homepage = sum(1 for d in enriched if d.get('homepage_scraped'))
            with_scholar = sum(1 for d in enriched if d.get('scholar_url'))

            log(f"\n📊 Phase 3.5 统计:")
            log(f"   LinkedIn: {with_linkedin} 人")
            log(f"   个人网站: {with_homepage} 人")
            log(f"   Google Scholar: {with_scholar} 人")

        else:
            log("⚠️  未找到 Phase 3.5 输出文件")
            return

    except Exception as e:
        log(f"❌ Phase 3.5 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # Phase 4.5: LLM 深度富化
    log("\n" + "=" * 80)
    log("【步骤 2/2】Phase 4.5: LLM 深度富化")
    log("=" * 80)
    log("⏰ 预计时间: 3-4 小时")
    log("🎯 目标: 提取工作履历、教育背景、技能、谈话点")

    try:
        # 运行 Phase 4.5
        import subprocess
        phase45_script = script_dir / "run_phase4_5_llm_enrichment.py"

        log(f"📜 执行脚本: {phase45_script}")

        result = subprocess.run(
            [sys.executable, str(phase45_script)],
            cwd=str(script_dir),
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            log("✅ Phase 4.5 完成")

            # 检查输出文件
            phase45_output = script_dir.parent / "phase4_5_llm_enriched.json"
            if phase45_output.exists():
                log(f"📁 输出文件: {phase45_output}")
                with open(phase45_output) as f:
                    llm_enriched = json.load(f)
                log(f"   富化人数: {len(llm_enriched)} 人")

                # 统计质量分布
                high_quality = sum(1 for d in llm_enriched if d.get('website_quality_score', 0) >= 90)
                medium_quality = sum(1 for d in llm_enriched if 60 <= d.get('website_quality_score', 0) < 90)
                low_quality = sum(1 for d in llm_enriched if 30 <= d.get('website_quality_score', 0) < 60)

                log(f"\n📊 Phase 4.5 质量分布:")
                log(f"   高质量 (90-100): {high_quality} 人")
                log(f"   中等质量 (60-89): {medium_quality} 人")
                log(f"   基础质量 (30-59): {low_quality} 人")

        else:
            log(f"❌ Phase 4.5 执行失败，返回码: {result.returncode}")
            return

    except Exception as e:
        log(f"❌ Phase 4.5 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 最终总结
    log("\n" + "=" * 80)
    log("🎉 Phase 3.5 + 4.5 完整流程执行完成")
    log("=" * 80)
    log(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"\n📂 输出文件:")
    log(f"   Phase 3.5: {phase35_output}")
    log(f"   Phase 4.5: {phase45_output}")
    log(f"\n📋 下一步:")
    log(f"   1. 导入数据库: cd ../personal-ai-headhunter && python3 import_github_candidates.py")
    log(f"   2. 查看高质量候选人: SELECT * FROM candidates WHERE website_quality_score >= 90")

if __name__ == "__main__":
    main()
