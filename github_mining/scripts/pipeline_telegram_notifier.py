#!/usr/bin/env python3
"""
GitHub Mining 流水线进度通报（每小时推 Telegram）
===================================================
复用 personal-ai-headhunter/telegram_notifier.py 的 notify()，
无需重复配置 token，直接从 config.env 读取。

用法:
  # 后台启动（无人值守）
  nohup python3 pipeline_telegram_notifier.py > /tmp/tg_notifier.log 2>&1 &

  # 立即测试一条消息
  python3 pipeline_telegram_notifier.py --test
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 复用已有的 telegram_notifier ────────────────────────────────
HEADHUNTER_DIR = Path("/Users/lillianliao/notion_rag/personal-ai-headhunter")
sys.path.insert(0, str(HEADHUNTER_DIR))
from telegram_notifier import notify  # BOT_TOKEN/CHAT_ID 从 config.env 读取

# ── 文件路径 ─────────────────────────────────────────────────────
DATE      = datetime.now().strftime("%Y%m%d")
BASE_DIR  = Path("/Users/lillianliao/notion_rag/github_mining")
WRITE_DIR = BASE_DIR / "scripts" / "github_mining"

STATE_FILE    = WRITE_DIR / f"academic_cooc_state_{DATE}.json"
PROGRESS_FILE = WRITE_DIR / f"academic_cooc_progress_{DATE}.json"
LOG_FILE      = BASE_DIR  / f"academic_cooc_pipeline_{DATE}.log"
EXPANDED_FILE = WRITE_DIR / f"academic_cooc_expanded_{DATE}.json"
PHASE3_FILE   = WRITE_DIR / f"academic_cooc_phase3_{DATE}.json"
PHASE35_FILE  = WRITE_DIR / f"academic_cooc_phase35_{DATE}.json"

TOTAL_SEEDS     = 3849
NOTIFY_INTERVAL = 3600  # 每小时

# ── 工具 ──────────────────────────────────────────────────────────
def load_json_safe(path: Path):
    try:
        return json.load(open(path))
    except Exception:
        return None

def get_last_log_lines(n: int = 5) -> str:
    try:
        raw = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        clean = [re.sub(r'\x1b\[[0-9;]*m', '', l) for l in raw[-n:]]
        return "\n".join(clean)
    except Exception:
        return "（日志不可读）"

def build_message() -> str:
    now = datetime.now().strftime("%m-%d %H:%M")
    lines = [f"📡 *Academic-GitHub 共现挖掘 进度播报*", f"🕐 {now}\n"]

    # ── 流水线步骤 ──────────────────────────────────────────
    state = load_json_safe(STATE_FILE) or {}
    step_map = [
        ("cooc_done",    "①共现"),
        ("phase3_done",  "②Phase3"),
        ("phase35_done", "③网站爬取"),
        ("import_done",  "④入库"),
        ("tier_done",    "⑤分级"),
    ]
    step_line = "  ".join(
        f"{'✅' if state.get(k) == 'true' else '⏳'}{label}"
        for k, label in step_map
    )
    lines.append(step_line)

    # ── 共现进度 ────────────────────────────────────────────
    progress = load_json_safe(PROGRESS_FILE)
    if progress:
        processed = len(progress.get("processed_seeds", []))
        total_new = len(progress.get("cooccurrence", {}))
        high_co   = sum(1 for v in progress.get("cooccurrence", {}).values() if v >= 2)
        pct = round(processed / TOTAL_SEEDS * 100, 1)
        bar = "█" * int(pct // 10) + "░" * (10 - int(pct // 10))
        lines.append(f"\n🌐 *共现分析* {bar} {pct}%")
        lines.append(f"   已处理: *{processed:,}* / {TOTAL_SEEDS:,}")
        lines.append(f"   新发现: *{total_new:,}*（共现≥2: *{high_co:,}*）")

    # ── 阶段产出 ────────────────────────────────────────────
    for label, path in [
        ("共现结果", EXPANDED_FILE),
        ("Phase3",   PHASE3_FILE),
        ("Phase3.5", PHASE35_FILE),
    ]:
        if path.exists():
            try:
                cnt = len(json.load(open(path)))
                lines.append(f"✅ {label}: *{cnt:,}* 人")
            except Exception:
                lines.append(f"❓ {label}: 文件存在但无法读取")

    # ── 最新日志 ────────────────────────────────────────────
    lines.append(f"\n```\n{get_last_log_lines(5)}\n```")

    if all(state.get(k) == "true" for k, _ in step_map):
        lines.append("🎉 *全部完成！*")

    return "\n".join(lines)

def is_done() -> bool:
    state = load_json_safe(STATE_FILE) or {}
    return all(state.get(k) == "true"
               for k in ["cooc_done","phase3_done","phase35_done","import_done","tier_done"])

# ── 主入口 ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="发一条测试消息后退出")
    parser.add_argument("--interval", type=int, default=NOTIFY_INTERVAL,
                        help="通报间隔（秒），默认 3600")
    args = parser.parse_args()

    if args.test:
        ok = notify(build_message())
        print("✅ 测试消息已发送" if ok else "❌ 发送失败，检查 config.env 中的 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
        return

    print(f"[{datetime.now():%H:%M:%S}] 🚀 Telegram 通报机器人启动，间隔 {args.interval//60} 分钟")
    notify(f"🚀 *Academic-GitHub 共现挖掘已启动！*\n种子: {TOTAL_SEEDS:,}人 | 共现≥2\n每小时自动播报进度 📡")

    while True:
        time.sleep(args.interval)
        notify(build_message())
        if is_done():
            notify("🎉 *流水线全部完成！请查看数据库结果。*")
            print(f"[{datetime.now():%H:%M:%S}] 完成，通报机器人退出")
            break

if __name__ == "__main__":
    main()
