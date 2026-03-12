#!/usr/bin/env python3
"""
Cache Backup Utility (缓存定期快照备份工具) v2
定期对正在不断写入的 *_cache.json 文件进行全量快照备份。
支持自动清理旧快照，避免磁盘空间爆炸。

用法:
    python3 backup_cache.py --watch-dir ../data/academic/runs/xxxxx/outputs --interval 15 --max-snapshots 20
"""

import argparse
import time
import shutil
from pathlib import Path
from datetime import datetime


def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def cleanup_old_snapshots(backup_base: Path, max_snapshots: int):
    """保留最近 N 个快照，删除最旧的"""
    snapshots = sorted(backup_base.glob("snapshot_*"), key=lambda p: p.name)
    if len(snapshots) > max_snapshots:
        to_remove = snapshots[:len(snapshots) - max_snapshots]
        for old in to_remove:
            shutil.rmtree(old)
            log(f"  🗑️ 清理旧快照: {old.name}")


def main():
    parser = argparse.ArgumentParser(description="学术爬虫缓存备份进程")
    parser.add_argument("--watch-dir", type=str, required=True, help="需要被监控并备份的 outputs 目录")
    parser.add_argument("--interval", type=int, default=15, help="自动备份的时间间隔（分钟，默认 15）")
    parser.add_argument("--max-snapshots", type=int, default=20, help="保留最多 N 个快照，自动清理旧的（默认 20）")
    args = parser.parse_args()

    watch_path = Path(args.watch_dir).resolve()
    if not watch_path.exists():
        log(f"❌ 监控目录不存在: {watch_path}")
        return

    # 建立独立的快照文件夹
    backup_base = watch_path.parent / "backups"
    backup_base.mkdir(parents=True, exist_ok=True)

    log("============================================================")
    log(f"🛡️ 开启增量缓存备份保护 v2")
    log(f"监控目录: {watch_path}")
    log(f"备份间隔: {args.interval} 分钟")
    log(f"最大保留快照数: {args.max_snapshots}")
    log("============================================================")

    while True:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_dir = backup_base / f"snapshot_{timestamp}"

            # 找到所有当前目录下的关键文件
            cache_files = list(watch_path.glob("*_cache.json"))
            raw_files = list(watch_path.glob("*_raw_*.json"))
            files_to_backup = cache_files + raw_files

            if files_to_backup:
                snapshot_dir.mkdir(parents=True, exist_ok=True)
                backup_count = 0
                total_mb = 0

                for f in files_to_backup:
                    if f.exists() and f.stat().st_size > 0:
                        shutil.copy2(f, snapshot_dir / f.name)
                        backup_count += 1
                        total_mb += f.stat().st_size / (1024 * 1024)

                log(f"✅ 创建快照 [snapshot_{timestamp}]: 备份了 {backup_count} 个文件 ({total_mb:.1f} MB)")

                # 清理超出限额的旧快照
                cleanup_old_snapshots(backup_base, args.max_snapshots)
            else:
                log(f"⚠️ 暂未发现需要备份的缓存数据文件，继续等候...")

        except Exception as e:
            log(f"❌ 备份执行时出现异常: {e}")

        # 等待指定的间隔时间
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
