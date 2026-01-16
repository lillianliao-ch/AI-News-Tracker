#!/usr/bin/env python3
"""
飞书权限测试脚本
测试应用是否具有必要的权限
"""
import asyncio
import sys
import json
from app.services.feishu_client import feishu_client

async def test_permissions():
    """测试飞书权限"""
    print("=" * 70)
    print("飞书权限诊断测试")
    print("=" * 70)
    
    # 1. 检查配置
    print("\n【步骤 1】检查配置...")
    if not feishu_client.is_enabled():
        print("❌ 飞书集成未启用")
        return False
    
    config = feishu_client.config
    print(f"✅ 配置已加载")
    print(f"   App ID: {config['app_id'][:20]}...")
    print(f"   App Token: {config['app_token'][:20]}...")
    print(f"   Table ID: {config['table_id']}")
    
    # 2. 获取 Token
    print("\n【步骤 2】获取 tenant_access_token...")
    token = await feishu_client.get_tenant_access_token()
    if not token:
        print("❌ Token 获取失败")
        return False
    print(f"✅ Token 获取成功: {token[:30]}...")
    
    # 3. 测试读取表格信息（只需要读权限）
    print("\n【步骤 3】测试读取表格信息...")
    try:
        import lark_oapi as lark
        from lark_oapi.api.bitable.v1 import GetAppTableRequest
        
        # 获取表格元信息
        request = GetAppTableRequest.builder() \
            .app_token(config['app_token']) \
            .table_id(config['table_id']) \
            .build()
        
        response = feishu_client.client.bitable.v1.app_table.get(request)
        
        if not response.success():
            print(f"❌ 读取表格失败")
            print(f"   错误码: {response.code}")
            print(f"   错误信息: {response.msg}")
            print(f"   Log ID: {response.get_log_id()}")
            
            if response.code == 91403:
                print("\n【诊断结果】权限不足！")
                print("\n可能的原因：")
                print("1. 应用未添加到此表格")
                print("2. 应用权限配置不正确")
                print("3. 表格设置中未授权给此应用")
            elif response.code == 91402:
                print("\n【诊断结果】表格不存在或 app_token/table_id 错误！")
            
            return False
        
        print(f"✅ 读取表格成功")
        if hasattr(response, 'data') and response.data:
            print(f"   表格名称: {response.data.name if hasattr(response.data, 'name') else '未知'}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    # 4. 测试创建记录（需要写权限）
    print("\n【步骤 4】测试创建测试记录...")
    try:
        test_data = {
            "候选人ID": "TEST_PERMISSION_CHECK",
            "姓名": "权限测试",
            "年龄": 30,
            "工作年限": 5,
            "学历": "本科",
            "当前公司": "测试公司",
            "当前职位": "测试职位",
            "期望薪资": "面议",
            "匹配度": 80,
            "推荐等级": "推荐",
            "核心优势": "这是一条测试记录，用于验证权限",
            "潜在风险": "无",
            "数据来源": "权限测试",
            "活跃度": "测试",
            "到岗状态": "测试"
        }
        
        # 先检查是否已存在测试记录
        existing_id = await feishu_client.check_duplicate("权限测试", "测试公司")
        if existing_id:
            print(f"   测试记录已存在，record_id: {existing_id}")
            print("✅ 写入权限正常（记录已存在）")
            return True
        
        # 尝试创建记录
        record_id = await feishu_client.add_record(test_data, None)
        
        if record_id:
            print(f"✅ 创建测试记录成功！")
            print(f"   Record ID: {record_id}")
            print("\n" + "=" * 70)
            print("🎉 权限测试通过！飞书集成配置正确！")
            print("=" * 70)
            return True
        else:
            print(f"❌ 创建记录失败")
            return False
            
    except Exception as e:
        print(f"❌ 创建记录异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False


async def main():
    success = await test_permissions()
    
    if not success:
        print("\n" + "=" * 70)
        print("❌ 权限测试失败")
        print("=" * 70)
        print("\n请检查以下内容：")
        print("\n1. 飞书开放平台 → 权限管理")
        print("   必需权限：")
        print("   - 查看、评论、编辑和管理多维表格")
        print("   - 新增数据记录")
        print("   - 查看数据记录")
        print("")
        print("2. 飞书表格 → 设置 → 高级设置 → 协作者")
        print("   添加你的应用为协作者，并授予编辑权限")
        print("")
        print("3. 确认 app_token 和 table_id 正确")
        print(f"   当前 app_token: {feishu_client.config['app_token']}")
        print(f"   当前 table_id: {feishu_client.config['table_id']}")
        print("")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

