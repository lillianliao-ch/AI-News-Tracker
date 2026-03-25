#!/usr/bin/env python3
"""
2019-2022 顶会挖掘批次 — Telegram 每小时进度播报
================================================
用法:
    # 后台启动（无人值守）
    nohup python3 conf_miner_notifier.py > /tmp/conf_notifier.log 2>&1 &

    # 立即测试发一条
    python3 conf_miner_notifier.py --test
"""
import sys
import time
import re
import sqlite3
from pathlib import Path
from datetime import datetime

# ── 复用已有 Telegram 通知模块 ──────────────────────────────────
HEADHUNTER_DIR = Path("/Users/lillianliao/notion_rag/personal-ai-headhunter")
sys.path.insert(0, str(HEADHUNTER_DIR))
from telegram_notifier import notify

# ── 路径配置 ────────────────────────────────────────────────────
DATA_DIR = Path("/Users/lillianliao/notion_rag/github_mining/data/conf_2019_2022")
DB_PATH  = HEADHUNTER_DIR / "data" / "headhunter_dev.db"

BATCH_LOGS = {
    "A (NeurIPS/ICML/ICLR/AAAI)": DATA_DIR / "batch_A_ai.log",
    "B (CVPR/ICCV/ECCV)":          DATA_DIR / "batch_B_cv.log",
    "C (ACL/EMNLP/NAACL)":         DATA_DIR / "batch_C_nlp.log",
}

NOTIFY_INTERVAL = 3600  # 每小时
START_TIME      = datetime.now()


def tail_log(path: Path, n: int = 6) -> str:
    """读日志最后 n 行，去除 ANSI 颜色码"""
    if not path.exists():
        return "（日志尚未生成）"
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        clean = [re.sub(r'\x1b\[[0-9;]*m', '', l) for l in lines[-n:]]
        return "\n".join(clean)
    except Exception:
        return "（无法读取日志）"


def parse_log_summary(path: Path) -> dict:
    """从日志解析关键数字"""
    result = {"done": False, "new_candidates": None, "last_conf": ""}
    if not path.exists():
        return result
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        # 完成标志
        m = re.search(r'✅ 完成! 新增 (\d+) 名候选人', text)
        if m:
            result["done"] = True
            result["new_candidates"] = int(m.group(1))
        # 最后处理的会议
        confs = re.findall(r'📚 (.*?)\s*\(', text)
        if confs:
            result["last_conf"] = confs[-1]
        # 进度中的作者池
        pools = re.findall(r'(\d+) 条作者记录', text)
        if pools:
            result["author_pool"] = int(pools[-1])
    except Exception:
        pass
    return result


def count_db_candidates() -> int:
    """统计本次批次写入 DB 的总人数"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM candidates WHERE source_file LIKE 'conf_2019_2022_%'")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return -1


def build_message() -> str:
    now     = datetime.now().strftime("%m-%d %H:%M")
    elapsed = (datetime.now() - START_TIME).seconds // 60

    lines = [
        f"📡 *2019-2022 顶会挖掘 进度播报*",
        f"🕐 {now}  |  已运行 {elapsed}m\n"
    ]

    all_done = True
    for batch_name, log_path in BATCH_LOGS.items():
        info = parse_log_summary(log_path)
        if not log_path.exists():
            lines.append(f"⬜ *批次 {batch_name}*: 尚未启动")
            all_done = False
        elif info["done"]:
            lines.append(f"✅ *批次 {batch_name}*: 完成，新增 `{info['new_candidates']:,}` 人")
        else:
            last = info.get("last_conf", "采集中")
            pool = info.get("author_pool", "?")
            lines.append(f"🔄 *批次 {batch_name}*: 进行中")
            lines.append(f"   当前: {last}  |  已采集: {pool} 条")
            all_done = False

    # DB 统计
    db_count = count_db_candidates()
    if db_count >= 0:
        lines.append(f"\n🗄  已入库 (conf_2019_2022): *{db_count:,}* 人")

    # 最新日志片段（取 Batch A）
    log_a = BATCH_LOGS["A (NeurIPS/ICML/ICLR/AAAI)"]
    snippet = tail_log(log_a, 4)
    lines.append(f"\n```\n{snippet}\n```")

    if all_done:
        lines.append("🎉 *所有批次已完成！*")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test",     action="store_true", help="立即发一条测试消息后退出")
    parser.add_argument("--interval", type=int, default=NOTIFY_INTERVAL)
    args = parser.parse_args()

    if args.test:
        msg = build_message()
        ok  = notify(msg)
        print("✅ 发送成功" if ok else "❌ 发送失败，检查 config.env")
        return

    print(f"[{datetime.now():%H:%M:%S}] 🚀 Telegram 通报启动，间隔 {args.interval//60} 分钟")
    notify(
        "🚀 *2019-2022 顶会挖掘 已启动！*\n"
        "目标: NeurIPS / ICML / ICLR / AAAI / CVPR / ICCV / ECCV / ACL / EMNLP / NAACL\n"
        "年份: 2019-2022 | 预计每小时自动播报进度 📡"
    )

    while True:
        time.sleep(args.interval)
        msg = build_message()
        notify(msg)
        # 所有批次完成则退出
        all_done = all(
            parse_log_summary(p).get("done") for p in BATCH_LOGS.values() if p.exists()
        ) and all(p.exists() for p in BATCH_LOGS.values())
        if all_done:
            notify("🎉 *2019-2022 顶会挖掘全部完成！*\n请查看数据库结果。")
            print(f"[{datetime.now():%H:%M:%S}] 全部完成，通报机器人退出")
            break


if __name__ == "__main__":
    main()
