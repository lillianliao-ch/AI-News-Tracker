#!/usr/bin/env python3
"""
Phase 4 候选人完整丰富流水线 - 无人值守 + 断点续传 + 自动验证

功能:
  1. Phase 3: 仓库深度信息补强（892人）→ 自动验证
  2. Phase 3.5: 个人主页爬取（LinkedIn/论文/经历）→ 自动验证
  3. 入库: 导入猎头系统数据库（自动去重）
  4. 分级: 自动打 S/A+/A/B+/B/C Tier 标签 → 自动验证

崩溃恢复:
  - Phase 3: 每50人自动保存，--resume 跳过已处理
  - Phase 3.5: 每50人自动保存，--resume 跳过已处理
  - 配合 auto_restart_wrapper.py 实现无人值守

使用方法:
  # 直接运行
  cd /Users/lillianliao/notion_rag/github_mining/scripts
  python3 run_phase4_enrichment.py

  # 无人值守（推荐）
  nohup python3 auto_restart_wrapper.py -- python3 run_phase4_enrichment.py > enrichment.log 2>&1 &

  # 查看进度
  tail -f enrichment.log
"""

import os
import sys
import json
import time
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# 强制刷新输出
import functools
print = functools.partial(print, flush=True)

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR / "github_mining"
ROOT_DIR = SCRIPT_DIR.parent.parent  # notion_rag
HEADHUNTER_DIR = ROOT_DIR / "personal-ai-headhunter"
PHASE4_INPUT = BASE_DIR / "phase4_expanded.json"
PHASE3_OUTPUT = BASE_DIR / "phase3_from_phase4.json"
PHASE3_5_OUTPUT = BASE_DIR / "phase3_5_enriched.json"  # 中间保存用
FINAL_OUTPUT = BASE_DIR / "phase4_final_enriched.json"
PIPELINE_STATE = BASE_DIR / "pipeline_state.json"

# ============================================================
# 状态管理
# ============================================================

def load_state() -> dict:
    """加载流水线状态（用于断点续传）"""
    if PIPELINE_STATE.exists():
        with open(PIPELINE_STATE) as f:
            return json.load(f)
    return {"phase3_done": False, "phase3_verified": False,
            "phase3_5_done": False, "phase3_5_verified": False,
            "import_done": False, "tier_done": False}

def save_state(state: dict):
    with open(PIPELINE_STATE, 'w') as f:
        json.dump(state, f, indent=2)

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

# ============================================================
# 验证函数
# ============================================================

def verify_phase3(expected_min: int) -> bool:
    """验证 Phase 3 输出质量"""
    log("--- Phase 3 验证开始 ---")

    if not PHASE3_OUTPUT.exists():
        log(f"FAIL: 输出文件不存在 {PHASE3_OUTPUT}")
        return False

    data = json.load(open(PHASE3_OUTPUT))
    total = len(data)
    log(f"总人数: {total}")

    if total < expected_min * 0.9:
        log(f"FAIL: 人数 {total} 低于预期 {expected_min} 的 90%")
        return False

    # 检查关键字段是否被填充
    has_stars = sum(1 for d in data if d.get('total_stars') is not None)
    has_langs = sum(1 for d in data if d.get('primary_languages'))
    has_score = sum(1 for d in data if d.get('final_score', 0) > 0)
    has_email = sum(1 for d in data if d.get('all_emails'))

    star_rate = has_stars / total if total else 0
    lang_rate = has_langs / total if total else 0
    score_rate = has_score / total if total else 0

    log(f"Stars 覆盖率:    {has_stars}/{total} ({star_rate:.0%})")
    log(f"语言 覆盖率:     {has_langs}/{total} ({lang_rate:.0%})")
    log(f"评分 覆盖率:     {has_score}/{total} ({score_rate:.0%})")
    log(f"邮箱 覆盖率:     {has_email}/{total} ({has_email*100//total}%)")

    # Stars 覆盖率必须 > 90%（核心指标）
    if star_rate < 0.90:
        log(f"FAIL: Stars 覆盖率 {star_rate:.0%} < 90%，数据不完整")
        return False

    log("--- Phase 3 验证通过 ---")
    return True

def verify_phase3_5(expected_min: int) -> bool:
    """验证 Phase 3.5 输出质量"""
    log("--- Phase 3.5 验证开始 ---")

    # 检查最终输出文件
    check_file = FINAL_OUTPUT if FINAL_OUTPUT.exists() else PHASE3_5_OUTPUT
    if not check_file.exists():
        log(f"FAIL: 输出文件不存在")
        return False

    data = json.load(open(check_file))
    total = len(data)
    log(f"总人数: {total} (文件: {check_file.name})")

    if total < expected_min * 0.9:
        log(f"FAIL: 人数 {total} 低于预期 {expected_min} 的 90%")
        return False

    # Phase 3.5 特有字段
    has_scraped = sum(1 for d in data if d.get('homepage_scraped') is not None)
    has_linkedin = sum(1 for d in data if d.get('linkedin_url'))
    has_work = sum(1 for d in data if d.get('work_experience'))
    has_edu = sum(1 for d in data if d.get('education'))
    has_scholar = sum(1 for d in data if d.get('scholar_url'))
    has_pubs = sum(1 for d in data if d.get('top_venues_count', 0) > 0)
    has_v2_score = sum(1 for d in data if d.get('final_score_v2', 0) > 0)

    log(f"主页爬取标记:    {has_scraped}/{total}")
    log(f"LinkedIn:        {has_linkedin}/{total}")
    log(f"工作经历:        {has_work}/{total}")
    log(f"教育背景:        {has_edu}/{total}")
    log(f"Scholar:         {has_scholar}/{total}")
    log(f"顶会论文:        {has_pubs}/{total}")
    log(f"V2评分:          {has_v2_score}/{total}")

    # 核心检查：homepage_scraped 标记必须覆盖大部分人
    if has_scraped < total * 0.5:
        log(f"FAIL: 主页爬取标记覆盖率过低 ({has_scraped}/{total})")
        return False

    log("--- Phase 3.5 验证通过 ---")
    return True

# ============================================================
# 执行步骤
# ============================================================

def run_phase3():
    """执行 Phase 3 仓库丰富（带 resume）"""
    log("========== Phase 3: 仓库深度信息补强 ==========")

    # 获取 token
    sys.path.insert(0, str(SCRIPT_DIR))
    from github_network_miner import GitHubNetworkMiner

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            from github_hunter_config import GITHUB_CONFIG
            token = GITHUB_CONFIG.get("token")
        except ImportError:
            pass

    if not token:
        log("ERROR: 未找到 GITHUB_TOKEN")
        sys.exit(1)

    miner = GitHubNetworkMiner(token=token)
    miner.phase3_enrich(
        resume=True,
        input_file=str(PHASE4_INPUT)
    )
    log("Phase 3 执行完毕")

def run_phase3_5():
    """执行 Phase 3.5 个人主页丰富（带 resume）"""
    log("========== Phase 3.5: 个人主页深度数据提取 ==========")

    sys.path.insert(0, str(SCRIPT_DIR))
    from github_network_miner import GitHubNetworkMiner

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            from github_hunter_config import GITHUB_CONFIG
            token = GITHUB_CONFIG.get("token")
        except ImportError:
            pass

    miner = GitHubNetworkMiner(token=token)
    miner.phase3_5_enrich(
        resume=True,
        input_file=str(PHASE3_OUTPUT)
    )

    # Phase 3.5 的最终输出可能在 phase3_5_enriched.json
    # 需要确保 phase4_final_enriched.json 也存在
    if PHASE3_5_OUTPUT.exists() and not FINAL_OUTPUT.exists():
        log(f"复制最终输出: {PHASE3_5_OUTPUT.name} -> {FINAL_OUTPUT.name}")
        shutil.copy2(PHASE3_5_OUTPUT, FINAL_OUTPUT)

    log("Phase 3.5 执行完毕")

def run_import():
    """执行入库：将富化数据导入猎头系统数据库"""
    log("========== Step 3: 入库 ==========")

    final = FINAL_OUTPUT if FINAL_OUTPUT.exists() else PHASE3_5_OUTPUT
    if not final.exists():
        log(f"ERROR: 找不到富化输出文件")
        sys.exit(1)

    cmd = [
        sys.executable,
        str(HEADHUNTER_DIR / "import_github_candidates.py"),
        "--file", str(final),
    ]
    log(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(HEADHUNTER_DIR))
    if result.returncode != 0:
        log(f"ERROR: 入库失败 (exit code {result.returncode})")
        sys.exit(1)
    log("入库完成")

def run_tier_update():
    """执行分级：对入库候选人自动打 Tier 标签"""
    log("========== Step 4: 自动分级 ==========")

    cmd = [sys.executable, str(HEADHUNTER_DIR / "batch_update_tiers.py")]
    log(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(HEADHUNTER_DIR))
    if result.returncode != 0:
        log(f"ERROR: 分级失败 (exit code {result.returncode})")
        sys.exit(1)
    log("分级完成")

def verify_import_and_tier() -> bool:
    """验证入库+分级结果"""
    log("--- 入库+分级 验证开始 ---")

    # 通过 subprocess 调用验证，避免直接 import database（路径/依赖问题）
    verify_script = f"""
import sys, os
sys.path.insert(0, '{HEADHUNTER_DIR}')
os.chdir('{HEADHUNTER_DIR}')
from database import SessionLocal, Candidate
from collections import Counter
session = SessionLocal()
all_gh = session.query(Candidate).filter(Candidate.source == 'github').all()
tier_dist = Counter(c.talent_tier for c in all_gh)
untiered = tier_dist.get(None, 0)
print(f'GitHub 候选人总数: {{len(all_gh)}}')
for t in ['S', 'A+', 'A', 'B+', 'B', 'C', 'D']:
    if tier_dist.get(t, 0) > 0:
        print(f'  {{t}}: {{tier_dist[t]}} 人')
if untiered > 0:
    print(f'  未分级: {{untiered}} 人')
print(f'VERIFY_TOTAL={{len(all_gh)}}')
print(f'VERIFY_UNTIERED={{untiered}}')
session.close()
"""
    result = subprocess.run(
        [sys.executable, "-c", verify_script],
        cwd=str(HEADHUNTER_DIR),
        capture_output=True, text=True
    )
    output = result.stdout
    log(output.strip())

    # 解析验证结果
    total = 0
    untiered = 0
    for line in output.splitlines():
        if line.startswith("VERIFY_TOTAL="):
            total = int(line.split("=")[1])
        elif line.startswith("VERIFY_UNTIERED="):
            untiered = int(line.split("=")[1])

    if total == 0:
        log("FAIL: 数据库中无 GitHub 候选人")
        return False
    if untiered > 0:
        log(f"WARN: 仍有 {untiered} 人未分级（可能是新格式不兼容）")

    log("--- 入库+分级 验证通过 ---")
    return True

# ============================================================
# 主流程
# ============================================================

def main():
    log("=" * 60)
    log("Phase 4 候选人完整丰富流水线")
    log("=" * 60)

    # 检查输入文件
    if not PHASE4_INPUT.exists():
        log(f"ERROR: Phase 4 输入文件不存在: {PHASE4_INPUT}")
        sys.exit(1)

    input_data = json.load(open(PHASE4_INPUT))
    expected_count = len(input_data)
    log(f"输入: {expected_count} 个 Phase 4 候选人")

    # 加载流水线状态
    state = load_state()
    log(f"当前状态: {json.dumps(state, ensure_ascii=False)}")

    # ---- Step 1: Phase 3 ----
    if not state.get("phase3_verified"):
        if not state.get("phase3_done"):
            run_phase3()
            state["phase3_done"] = True
            save_state(state)

        # 验证
        if verify_phase3(expected_count):
            state["phase3_verified"] = True
            save_state(state)
            log("Phase 3 验证通过，继续下一步")
        else:
            log("Phase 3 验证失败，退出（等待 auto_restart_wrapper 重试）")
            # 清除 done 标记，下次重试会重新执行（resume 会跳过已处理的）
            state["phase3_done"] = False
            save_state(state)
            sys.exit(1)
    else:
        log("Phase 3 已完成且已验证，跳过")

    time.sleep(2)

    # ---- Step 2: Phase 3.5 ----
    if not state.get("phase3_5_verified"):
        if not state.get("phase3_5_done"):
            run_phase3_5()
            state["phase3_5_done"] = True
            save_state(state)

        # 验证
        if verify_phase3_5(expected_count):
            state["phase3_5_verified"] = True
            save_state(state)
            log("Phase 3.5 验证通过")
        else:
            log("Phase 3.5 验证失败，退出（等待 auto_restart_wrapper 重试）")
            state["phase3_5_done"] = False
            save_state(state)
            sys.exit(1)
    else:
        log("Phase 3.5 已完成且已验证，跳过")

    time.sleep(2)

    # ---- Step 3: 入库 ----
    if not state.get("import_done"):
        run_import()
        state["import_done"] = True
        save_state(state)
    else:
        log("入库已完成，跳过")

    time.sleep(2)

    # ---- Step 4: 分级 ----
    if not state.get("tier_done"):
        run_tier_update()
        if verify_import_and_tier():
            state["tier_done"] = True
            save_state(state)
        else:
            log("分级验证失败，退出（等待 auto_restart_wrapper 重试）")
            sys.exit(1)
    else:
        log("分级已完成，跳过")

    # ---- 完成 ----
    log("=" * 60)
    log("全部完成! (富化 → 入库 → 分级)")
    final = FINAL_OUTPUT if FINAL_OUTPUT.exists() else PHASE3_5_OUTPUT
    if final.exists():
        data = json.load(open(final))
        log(f"富化输出: {final} ({len(data)} 人)")
    log("=" * 60)

if __name__ == "__main__":
    main()
