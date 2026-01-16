#!/usr/bin/env python3
"""
Railway启动脚本
确保正确的应用启动
"""
import sys
import os
from pathlib import Path

# 强制刷新输出，确保日志立即显示
sys.stdout.reconfigure(line_buffering=True)

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建必要的目录（确保 SQLite 数据库可以被创建）
data_dir = Path("./data")
cache_dir = Path("./data/cache")
data_dir.mkdir(parents=True, exist_ok=True)
cache_dir.mkdir(parents=True, exist_ok=True)
print(f"📁 数据目录已确保存在: {data_dir.absolute()}", flush=True)


if __name__ == "__main__":
    # 调试：打印所有环境变量
    print("=" * 60, flush=True)
    print("🔍 环境变量检查:", flush=True)
    print("=" * 60, flush=True)

    # 打印所有环境变量（帮助调试）
    print("所有环境变量:", flush=True)
    env_count = 0
    for key, value in sorted(os.environ.items()):
        # 隐藏敏感信息
        if 'KEY' in key or 'SECRET' in key or 'TOKEN' in key:
            if value:
                value = value[:10] + "..." if len(value) > 10 else "***"
        print(f"  {key} = {value}", flush=True)
        env_count += 1

    print(f"总计: {env_count} 个环境变量", flush=True)
    print("=" * 60, flush=True)

    required_vars = ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'CLASSIFY_MODEL']
    missing_vars = []

    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: 未设置", flush=True)
        else:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked}", flush=True)

    print("=" * 60, flush=True)

    # 警告但不退出（允许应用启动，但AI功能会受限）
    if missing_vars:
        print(f"⚠️  警告: 缺少环境变量: {', '.join(missing_vars)}", flush=True)
        print("应用将启动，但部分功能可能无法使用", flush=True)
        print("请在Railway Service的Settings > Variables中设置", flush=True)
        print("=" * 60, flush=True)
    else:
        print("✅ 所有必要的环境变量已设置", flush=True)
        print("=" * 60, flush=True)

    import uvicorn
    from main import app

    # 获取Railway分配的端口
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 启动应用，端口: {port}", flush=True)
    print("=" * 60, flush=True)

    # 启动应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True  # 确保访问日志被记录
    )
