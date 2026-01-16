#!/usr/bin/env python3
"""
测试飞书写入权限（包含重试和详细错误信息）
"""
import asyncio
import sys
from app.services.feishu_client import feishu_client

async def test_write_with_details():
    print("=" * 70)
    print("飞书权限详细测试")
    print("=" * 70)
    
    # 1. 检查配置
    print("\n【步骤 1】检查配置")
    config = feishu_client.config
    print(f"✅ App ID: {config['app_id']}")
    print(f"✅ App Token: {config['app_token']}")
    print(f"✅ Table ID: {config['table_id']}")
    
    # 2. 获取 Token
    print("\n【步骤 2】获取 tenant_access_token")
    token = await feishu_client.get_tenant_access_token()
    if not token:
        print("❌ Token 获取失败")
        return False
    print(f"✅ Token: {token[:30]}...")
    
    # 3. 测试写入
    print("\n【步骤 3】尝试创建测试记录")
    test_data = {
        "候选人ID": "TEST_FINAL_20251114",
        "姓名": "最终权限测试",
        "年龄": 30,
        "工作年限": 5,
        "学历": "本科",
        "当前公司": "测试公司",
        "当前职位": "测试职位",
        "期望薪资": "面议",
        "匹配度": 80,
        "推荐等级": "推荐",
        "核心优势": "权限测试记录",
        "潜在风险": "无",
        "数据来源": "测试",
        "活跃度": "测试",
        "到岗状态": "测试"
    }
    
    # 打印请求 URL
    print(f"\n请求 URL: https://open.feishu.cn/open-apis/bitable/v1/apps/{config['app_token']}/tables/{config['table_id']}/records")
    
    record_id = await feishu_client.add_record(test_data, None)
    
    if record_id:
        print(f"\n" + "=" * 70)
        print("🎉 成功！飞书集成配置完成！")
        print("=" * 70)
        print(f"\nRecord ID: {record_id}")
        print("\n你现在可以:")
        print("1. 在 Boss 直聘页面重新测试插件")
        print("2. 推荐候选人会自动同步到飞书表格")
        return True
    else:
        print(f"\n" + "=" * 70)
        print("❌ 仍然失败 (403 Forbidden)")
        print("=" * 70)
        print("\n这说明应用虽然有全局权限，但没有被授权访问这个具体表格。")
        print("\n最后一步操作：")
        print("\n【方法 1】通过表格分享（推荐）")
        print("1. 打开飞书表格")
        print("2. 点击右上角「分享」按钮")
        print("3. 点击「添加协作者」")
        print("4. 搜索「AIING」(你的应用名)")
        print("5. 选择「可编辑」权限")
        print("6. 保存")
        print("\n【方法 2】使用表格 URL 直接授权")
        print("1. 访问飞书开放平台")
        print("2. 应用详情 → 添加能力 → 机器人")
        print("3. 将机器人添加到群组或表格")
        print("\n【方法 3】检查应用可用范围")
        print("1. 飞书开放平台 → 你的应用 → 版本管理与发布")
        print("2. 确认「可用范围」包含你的账号或「所有成员」")
        print("3. 如果是「部分成员」，添加你的账号")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_write_with_details())
    sys.exit(0 if result else 1)


