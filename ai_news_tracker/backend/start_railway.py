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
    import uvicorn
    from main import app

    # 获取Railway分配的端口
    port = int(os.environ.get("PORT", 8000))

    # 启动应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
