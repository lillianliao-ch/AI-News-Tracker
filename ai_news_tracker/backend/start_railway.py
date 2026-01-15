#!/usr/bin/env python3
"""
Railway启动脚本
确保正确的应用启动
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 调试：打印所有环境变量
    print("=" * 60)
    print("🔍 环境变量检查:")
    print("=" * 60)

    # 打印所有环境变量（帮助调试）
    print("所有环境变量:")
    for key, value in sorted(os.environ.items()):
        # 隐藏敏感信息
        if 'KEY' in key or 'SECRET' in key or 'TOKEN' in key:
            if value:
                value = value[:10] + "..." if len(value) > 10 else "***"
        print(f"  {key} = {value}")

    print("=" * 60)

    required_vars = ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'CLASSIFY_MODEL']
    missing_vars = []

    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: 未设置")
        else:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked}")

    print("=" * 60)

    # 警告但不退出（允许应用启动，但AI功能会受限）
    if missing_vars:
        print(f"⚠️  警告: 缺少环境变量: {', '.join(missing_vars)}")
        print("应用将启动，但部分功能可能无法使用")
        print("请在Railway Service的Settings > Variables中设置")
        print("=" * 60)
    else:
        print("✅ 所有必要的环境变量已设置")
        print("=" * 60)

    import uvicorn
    from main import app

    # 获取Railway分配的端口
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 启动应用，端口: {port}")
    print("=" * 60)

    # 启动应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
