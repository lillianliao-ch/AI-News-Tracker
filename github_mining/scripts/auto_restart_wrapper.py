#!/usr/bin/env python3
"""
自动重启包装器 - 为长时间任务提供无人值守自动重启能力

解决痛点:
- 网络闪断导致任务崩溃
- API 502 错误导致脚本退出
- 临时故障需要人工手动重启

使用方法:
    # 直接运行（会自动捕获崩溃并重启）
    python3 auto_restart_wrapper.py -- python3 github_network_miner.py phase4 --seed-top 264

    # 后台运行
    nohup python3 auto_restart_wrapper.py -- python3 github_network_miner.py phase4 --seed-top 264 > /dev/null 2>&1 &

    # 查看日志
    tail -f github_mining/auto_restart.log

原理:
    外层监控器捕获内层命令的所有异常，并在指定时间后自动重启
    配合 github_network_miner.py 的 --resume 参数实现断点续传
"""

import sys
import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path

# 配置
MAX_RESTARTS = 100          # 最大重启次数
RESTART_DELAY = 30          # 重启延迟（秒）
LOG_FILE = Path(__file__).parent / "github_mining" / "auto_restart.log"


def log(message: str):
    """日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line, flush=True)

    # 写入日志文件
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')


def run_with_auto_restart(command: list, max_restarts: int = MAX_RESTARTS, restart_delay: int = RESTART_DELAY):
    """
    执行命令并自动重启

    Args:
        command: 命令列表（如 ['python3', 'github_network_miner.py', 'phase4']）
        max_restarts: 最大重启次数
        restart_delay: 重启延迟（秒）
    """
    restart_count = 0

    log("🚀 自动重启包装器启动")
    log(f"📝 执行命令: {' '.join(command)}")
    log(f"⚙️  配置: 最大重启 {max_restarts} 次，延迟 {restart_delay} 秒")

    while restart_count < max_restarts:
        try:
            log(f"🔄 启动任务（第 {restart_count + 1} 次尝试）")

            # 执行命令
            result = subprocess.run(
                command,
                check=False,  # 不抛出异常，我们自己处理返回码
                # 不捕获输出，让子进程直接输出到终端
            )

            # 检查返回码
            if result.returncode == 0:
                log("✅ 任务成功完成！")
                return result.returncode

            # 非零返回码视为失败
            restart_count += 1
            log(f"⚠️  任务异常退出（返回码: {result.returncode}）")

            if restart_count < max_restarts:
                log(f"🔁 {restart_delay} 秒后自动重启（第 {restart_count}/{max_restarts} 次）...")
                time.sleep(restart_delay)
                log("🔄 继续执行（将自动从断点恢复）")
            else:
                log(f"❌ 达到最大重启次数（{max_restarts}），放弃")
                return result.returncode

        except KeyboardInterrupt:
            log("\n⚠️  用户中断（Ctrl+C），退出")
            return 130  # 标准的 Ctrl+C 返回码

        except Exception as e:
            restart_count += 1
            log(f"❌ 执行失败: {str(e)}")

            if restart_count < max_restarts:
                log(f"🔁 {restart_delay} 秒后自动重启（第 {restart_count}/{max_restarts} 次）...")
                time.sleep(restart_delay)
                log("🔄 继续执行（将自动从断点恢复）")
            else:
                log(f"❌ 达到最大重启次数（{max_restarts}），放弃")
                return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="自动重启包装器 - 为长时间任务提供无人值守能力",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 标准 Phase 4（自动重启）
  python3 auto_restart_wrapper.py -- python3 github_network_miner.py phase4 --seed-top 264

  # 后台运行
  nohup python3 auto_restart_wrapper.py -- python3 github_network_miner.py phase4 --seed-top 264 > /dev/null 2>&1 &

  # 自定义重启次数和延迟
  python3 auto_restart_wrapper.py --max-restarts 50 --delay 60 -- python3 github_network_miner.py phase4
        """
    )

    parser.add_argument(
        '--max-restarts',
        type=int,
        default=MAX_RESTARTS,
        help=f'最大重启次数（默认: {MAX_RESTARTS}）'
    )

    parser.add_argument(
        '--delay',
        type=int,
        default=RESTART_DELAY,
        help=f'重启延迟秒数（默认: {RESTART_DELAY}）'
    )

    parser.add_argument(
        'command',
        nargs=argparse.REMAINDER,
        help='要执行的命令（用 -- 分隔）'
    )

    args = parser.parse_args()

    # 检查命令
    if not args.command or args.command[0] != '--':
        parser.print_help()
        print("\n❌ 错误: 命令必须用 '--' 分隔")
        print("   正确用法: python3 auto_restart_wrapper.py -- 你的命令")
        sys.exit(1)

    # 移除 '--' 分隔符
    command = args.command[1:]

    if not command:
        parser.print_help()
        print("\n❌ 错误: 未指定要执行的命令")
        sys.exit(1)

    # 确保日志目录存在
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 执行
    exit_code = run_with_auto_restart(command, args.max_restarts, args.delay)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
