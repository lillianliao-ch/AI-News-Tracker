#!/bin/bash
# GitHub Mining 实时进度监控
# 用法: bash check_progress.sh        (单次查看)
#       bash check_progress.sh -w     (每10秒自动刷新)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

WATCH_MODE=false
[[ "$1" == "-w" || "$1" == "--watch" ]] && WATCH_MODE=true

show_progress() {
python3 << 'PYTHON'
import json, os, subprocess
from datetime import datetime, timedelta
from pathlib import Path

RUNS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "runs"
ACAD_BASE = RUNS_DIR.parent.parent / "data" / "academic" / "runs"

def bar(pct, width=30):
    filled = int(width * pct / 100)
    return f"[{'█' * filled}{'░' * (width - filled)}]"

def fmt_dur(m):
    if m < 60: return f"{m:.0f}m"
    h, m = divmod(int(m), 60)
    return f"{h}h{m:02d}m"

now = datetime.now()
print(f"  ⏰ {now.strftime('%H:%M:%S')}")
print()

# ── GitHub Mining ──
runs = sorted([d for d in os.listdir(RUNS_DIR) if d.startswith("2026")], reverse=True) if RUNS_DIR.exists() else []
if runs:
    latest = runs[0]
    out = RUNS_DIR / latest / "outputs"
    try:
        start = datetime.strptime(latest[:15], "%Y%m%d_%H%M%S")
        elapsed = (now - start).total_seconds() / 60
    except: start, elapsed = None, 0

    pf = out / "pre_filtered.json"
    total = len(json.load(open(pf))) if pf.exists() else 0
    # Phase 3+ 实际处理的是 db_dedup 后的人数
    dd = out / "db_deduped.json"
    deduped_total = len(json.load(open(dd))) if dd.exists() else total

    short_name = latest.split("_", 2)[-1] if latest.count("_") >= 2 else latest
    print(f"  🔬 GitHub Mining — {short_name}")
    print(f"     {total:,} candidates | deduped {deduped_total:,} | running {fmt_dur(elapsed)}")
    print()

    # Phase 3 & 3.5: 用 deduped_total 作为分母（这是实际处理的人数）
    for label, fname in [
        ("Phase 3   S2学术富化", "phase3_enriched.json"),
        ("Phase 3.5 网络挖掘  ", "phase3_5_enriched.json"),
    ]:
        fp = out / fname
        if fp.exists():
            count = len(json.load(open(fp)))
            pct = count / deduped_total * 100 if deduped_total else 0
            mod = datetime.fromtimestamp(os.path.getmtime(fp))
            speed = count / elapsed if elapsed > 0 else 0
            remain = (deduped_total - count) / speed if speed > 0 and count < deduped_total else 0
            eta_str = f"ETA {(now + timedelta(minutes=remain)).strftime('%H:%M')}" if count < deduped_total else "Done ✅"
            print(f"     {label}  {bar(pct)} {pct:5.1f}%  {count:,}/{deduped_total:,}")
            print(f"     {'':25s}  {speed:.1f}/min  {eta_str}")
        else:
            print(f"     {label}  {bar(0)} {'waiting...':>12s}")

    # Phase 4.5: 从 phase4_5_progress.json 读取实时进度
    p45 = out / "phase4_5_progress.json"
    p45_label = "Phase 4.5 LLM深度富化"
    if p45.exists():
        try:
            pd = json.load(open(p45))
            done = len(pd.get("completed", []))
            stats = pd.get("stats", {})
            success = stats.get("success", 0)
            failed = stats.get("failed", 0)
            last_ts = pd.get("last_update", "")
            # 从 phase3_5 输出计算 target 数（有 blog URL 的候选人数）
            p35 = out / "phase3_5_enriched.json"
            if p35.exists():
                p35_data = json.load(open(p35))
                p45_total = sum(1 for c in p35_data if c.get('homepage_scraped') or c.get('blog'))
            else:
                p45_total = total
            processed = success + failed
            pct = processed / p45_total * 100 if p45_total else 0
            # 速率: 从日志第一行提取 Phase 4.5 实际启动时间
            mod = datetime.fromtimestamp(os.path.getmtime(p45))
            p45_start = None
            p45_log = out.parent / "logs" / "phase4_5_v2.log"
            if p45_log.exists():
                try:
                    with open(p45_log) as f:
                        for line in f:
                            if line.startswith("["):
                                ts_str = line[1:20]  # [2026-03-12 06:55:20]
                                p45_start = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                                break
                except: pass
            if not p45_start:
                p45_start = start
            p45_elapsed = (now - mod).total_seconds() / 60  # minutes since last update
            p45_run = (now - p45_start).total_seconds() / 60
            speed = processed / p45_run if p45_run > 1 else 0
            remain = (p45_total - processed) / speed if speed > 0 else 0
            if processed >= p45_total:
                eta_str = "Done ✅"
            elif p45_elapsed > 5:
                eta_str = f"⚠️ stale ({p45_elapsed:.0f}m ago)"
            else:
                eta_str = f"ETA {(now + timedelta(minutes=remain)).strftime('%H:%M')}"
            print(f"     {p45_label}  {bar(pct)} {pct:5.1f}%  {processed:,}/{p45_total:,}")
            print(f"     {'':25s}  {speed:.1f}/min  ✓{success} ✗{failed}  {eta_str}")
        except Exception as e:
            print(f"     {p45_label}  {bar(0)} {'error':>12s}  {e}")
    else:
        # 也检查旧格式的输出文件
        for alt in ["phase45_final.json", "phase4_5_enriched.json"]:
            fp = out / alt
            if fp.exists():
                count = len(json.load(open(fp)))
                pct = count / total * 100 if total else 0
                print(f"     {p45_label}  {bar(pct)} {pct:5.1f}%  {count:,}/{total:,}  Done ✅")
                break
        else:
            print(f"     {p45_label}  {bar(0)} {'waiting...':>12s}")
    print()

# ── Academic Pipeline ──
if ACAD_BASE.exists():
    acad_runs = sorted([d for d in os.listdir(ACAD_BASE) if d.startswith("conference_full")], reverse=True)
    if acad_runs:
        ad = ACAD_BASE / acad_runs[0]
        bk = ad / "backups"
        snaps = sorted(os.listdir(bk)) if bk.exists() else []
        print(f"  📚 Academic Pipeline — {acad_runs[0].split('_',2)[-1]}")
        if snaps:
            print(f"     Snapshots: {len(snaps)} | Latest: {snaps[-1].replace('snapshot_','')}")
        print()

# ── Active Processes ──
res = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
procs = []
for l in res.stdout.split('\n'):
    if 'grep' in l or 'check_progress' in l: continue
    if 'batch_runner' in l: procs.append("batch_runner")
    elif 'github_network_miner' in l:
        p = "phase3.5" if "phase3_5" in l else "phase3"
        procs.append(f"network_miner({p})")
    elif 'llm_enrichment' in l or 'phase4_5' in l.lower(): procs.append("llm_enrichment")
    elif 'academic_miner' in l: procs.append("academic_miner")
    elif 'run_all_conferences' in l: procs.append("conference_runner")

status = ", ".join(procs) if procs else "⏸️ idle"
print(f"  🔧 Processes: {status}")
PYTHON
}

if $WATCH_MODE; then
    while true; do
        clear
        echo "═══════════════════════════════════════════════════"
        echo "  📊 Mining Progress Monitor  (Ctrl+C to exit)"
        echo "═══════════════════════════════════════════════════"
        show_progress
        sleep 10
    done
else
    echo "═══════════════════════════════════════════════════"
    echo "  📊 Mining Progress"
    echo "═══════════════════════════════════════════════════"
    show_progress
    echo ""
    echo "  💡 Tip: bash check_progress.sh -w  ← 实时刷新模式"
fi
