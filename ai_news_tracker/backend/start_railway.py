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
    # 调试：打印环境变量
    print("=" * 60)
    print("🔍 环境变量检查:")
    print("=" * 60)

    required_vars = ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'CLASSIFY_MODEL']
    missing_vars = []

    for var in required_vars:
        value = os.environ.get(var, "❌ 未设置")
        # 隐藏API Key的实际值，只显示前10个字符
        if var == 'OPENAI_API_KEY' and value != "❌ 未设置":
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"  {var}: {value}")

        if os.environ.get(var) is None:
            missing_vars.append(var)

    print("=" * 60)

    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请在Railway项目的Variables中设置这些变量")
        sys.exit(1)

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
