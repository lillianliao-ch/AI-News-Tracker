#!/usr/bin/env python3
"""
学术流水线健康检查 + Telegram 推送
每 30 分钟自动运行，统计 DB 联系方式覆盖率并推送变化。

用法:
  # 单次运行
  python3 scripts/academic_health_check.py

  # 后台循环 (每 30 分钟)
  nohup python3 scripts/academic_health_check.py --loop --interval 1800 &

  # 自定义间隔 + 日志
  nohup python3 scripts/academic_health_check.py --loop --interval 1800 \
    >> data/academic/logs/health_check.log 2>&1 &
"""

import os
import sys
import json
import time
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# Telegram
HEADHUNTER_DIR = Path(__file__).parent.parent.parent / "personal-ai-headhunter"
sys.path.insert(0, str(HEADHUNTER_DIR))

DB_PATH = os.environ.get(
    'DB_PATH',
    str(HEADHUNTER_DIR / 'data' / 'headhunter_dev.db')
)


def get_stats():
    """从 DB 获取 academic 各年份 × tier 的联系方式统计"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Total by source
    c.execute("SELECT COUNT(*) FROM candidates WHERE source='academic'")
    total_academic = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM candidates")
    total_all = c.fetchone()[0]

    # Year × Tier × Contact
    c.execute("""
        SELECT structured_tags, email, linkedin_url, github_url, personal_website
        FROM candidates
        WHERE source='academic' AND structured_tags IS NOT NULL
    """)
    rows = c.fetchall()

    from collections import defaultdict
    year_data = defaultdict(lambda: defaultdict(lambda: {
        'total': 0, 'email': 0, 'linkedin': 0, 'github': 0, 'website': 0, 'reachable': 0
    }))

    for st_str, email, li, gh, ws in rows:
        try:
            st = json.loads(st_str)
        except:
            continue
        tier = st.get('academic_tier', '?')
        confs = st.get('conferences', [])
        years = set()
        for conf in confs:
            for y in ['2025', '2024', '2023']:
                if y in str(conf):
                    years.add(y)
        if not years:
            years.add('unknown')

        has_email = bool(email and email.strip())
        has_li = bool(li and li.strip())
        has_gh = bool(gh and gh.strip())
        has_ws = bool(ws and ws.strip())

        for y in years:
            d = year_data[y][tier]
            d['total'] += 1
            if has_email: d['email'] += 1
            if has_li: d['linkedin'] += 1
            if has_gh: d['github'] += 1
            if has_ws: d['website'] += 1
            if has_email or has_li: d['reachable'] += 1

    # Check running processes
    import subprocess
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'academic'],
            capture_output=True, text=True
        )
        running_pids = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except:
        running_pids = 0

    conn.close()
    return {
        'total_all': total_all,
        'total_academic': total_academic,
        'year_data': dict(year_data),
        'running_pids': running_pids,
    }


def format_report(stats, prev_stats=None):
    """格式化 Telegram 报告"""
    now = datetime.now().strftime('%H:%M')
    tier_order = ['S', 'A+', 'A', 'B', 'C']

    lines = [
        f"🏥 学术流水线健康检查 [{now}]",
        f"",
        f"📦 全库: {stats['total_all']:,} | Academic: {stats['total_academic']:,}",
    ]

    # Running processes
    if stats['running_pids'] > 0:
        lines.append(f"⚙️ 运行中进程: {stats['running_pids']}")
    else:
        lines.append(f"✅ 无运行中进程")

    lines.append("")

    for year in ['2025', '2024', '2023']:
        yd = stats['year_data'].get(year, {})
        if not yd:
            continue

        # B+ subtotals
        bp = {'total': 0, 'email': 0, 'linkedin': 0, 'website': 0, 'reachable': 0}
        all_t = {'total': 0, 'email': 0, 'linkedin': 0, 'website': 0, 'reachable': 0}
        for tier, d in yd.items():
            for k in bp:
                all_t[k] += d[k]
                if tier in ['S', 'A+', 'A', 'B']:
                    bp[k] += d[k]

        t = all_t['total']
        bt = bp['total']
        if t == 0:
            continue

        bp_reach_pct = 100 * bp['reachable'] / bt if bt > 0 else 0

        # Delta from previous
        delta_str = ""
        if prev_stats and year in prev_stats['year_data']:
            prev_yd = prev_stats['year_data'][year]
            prev_bp_reach = sum(
                prev_yd.get(tier, {}).get('reachable', 0)
                for tier in ['S', 'A+', 'A', 'B']
            )
            delta = bp['reachable'] - prev_bp_reach
            if delta > 0:
                delta_str = f" (+{delta})"
            elif delta < 0:
                delta_str = f" ({delta})"

        lines.append(
            f"{'━' * 20} {year} {'━' * 20}"
        )
        lines.append(
            f"B+ 可触达: {bp['reachable']}/{bt} ({bp_reach_pct:.0f}%){delta_str}"
        )
        lines.append(
            f"  邮箱: {bp['email']} | LI: {bp['linkedin']} | 主页: {bp['website']}"
        )

    lines.append("")
    lines.append(f"ALL 可触达: {all_t['reachable']}/{all_t['total']} ({100*all_t['reachable']/all_t['total']:.0f}%)" if all_t['total'] > 0 else "")

    return '\n'.join(lines)


def run_check(prev_stats=None, send_telegram=True):
    """执行一次健康检查"""
    stats = get_stats()
    report = format_report(stats, prev_stats)

    print(f"\n{'=' * 50}")
    print(report)
    print(f"{'=' * 50}")

    if send_telegram:
        try:
            from telegram_notifier import notify
            result = notify(report)
            if result:
                print("✅ Telegram 已发送")
            else:
                print("⚠️ Telegram 发送失败")
        except Exception as e:
            print(f"⚠️ Telegram 异常: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="学术流水线健康检查")
    parser.add_argument('--loop', action='store_true', help='循环模式')
    parser.add_argument('--interval', type=int, default=1800, help='间隔秒数 (默认 1800=30min)')
    parser.add_argument('--no-telegram', action='store_true', help='不发送 Telegram')
    args = parser.parse_args()

    send_tg = not args.no_telegram

    if args.loop:
        print(f"🔄 循环模式启动 | 间隔: {args.interval}s ({args.interval//60}min)")
        prev = None
        while True:
            try:
                prev = run_check(prev, send_telegram=send_tg)
                print(f"⏰ 下次检查: {args.interval//60} 分钟后")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n🛑 已停止")
                break
            except Exception as e:
                print(f"❌ 异常: {e}")
                time.sleep(60)
    else:
        run_check(send_telegram=send_tg)


if __name__ == '__main__':
    main()
