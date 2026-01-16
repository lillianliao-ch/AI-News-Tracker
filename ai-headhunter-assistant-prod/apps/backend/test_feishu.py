"""
测试飞书 API 连接
"""

import asyncio
import sys
from app.services.feishu_client import feishu_client


async def main():
    """测试飞书 API"""
    print("=" * 60)
    print("测试飞书 API 连接")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n1. 检查飞书配置...")
    if not feishu_client.is_enabled():
        print("❌ 飞书集成未启用")
        print("\n请确保以下环境变量已配置:")
        print("  - FEISHU_APP_ID")
        print("  - FEISHU_APP_SECRET")
        print("  - FEISHU_APP_TOKEN")
        print("  - FEISHU_TABLE_ID")
        print("  - FEISHU_ENABLED=true")
        sys.exit(1)
    
    print("✅ 飞书集成已启用")
    print(f"   App ID: {feishu_client.config['app_id'][:15]}...")
    print(f"   App Token: {feishu_client.config['app_token'][:15]}...")
    print(f"   Table ID: {feishu_client.config['table_id']}")
    
    # 2. 测试 Token 获取
    print("\n2. 测试获取 tenant_access_token...")
    try:
        token = await feishu_client.get_tenant_access_token()
        
        if token:
            print(f"✅ Token 获取成功")
            print(f"   Token 前缀: {token[:20]}...")
        else:
            print("❌ Token 获取失败")
            print("\n请检查:")
            print("  - App ID 和 App Secret 是否正确")
            print("  - 网络连接是否正常")
            print("  - 飞书开放平台应用是否已启用")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Token 获取异常: {e}")
        print("\n这可能是因为:")
        print("  - App ID 或 App Secret 错误")
        print("  - 飞书应用未启用")
        print("  - 网络连接问题")
        sys.exit(1)
    
    # 3. 健康检查
    print("\n3. 执行健康检查...")
    health = await feishu_client.health_check()
    print(f"   状态: {health['status']}")
    print(f"   消息: {health['message']}")
    
    if health['status'] == 'healthy':
        print("\n" + "=" * 60)
        print("✅ 飞书 API 连接测试通过！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 启动后端服务: uvicorn app.main:app --reload")
        print("2. 访问健康检查: http://localhost:8000/api/feishu/health")
        print("3. 使用 Chrome 插件测试完整流程")
    else:
        print("\n" + "=" * 60)
        print("❌ 飞书 API 连接测试失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

