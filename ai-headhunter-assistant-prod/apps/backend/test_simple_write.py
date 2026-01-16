#!/usr/bin/env python3
"""简单的飞书写入测试"""
import asyncio
from app.services.feishu_client import feishu_client

async def test_write():
    print("=" * 60)
    print("测试飞书表格写入权限")
    print("=" * 60)
    
    print("\n1. 准备测试数据...")
    test_data = {
        "候选人ID": "TEST_20251114",
        "姓名": "权限测试候选人",
        "年龄": 30,
        "工作年限": 5,
        "学历": "本科",
        "当前公司": "测试公司",
        "当前职位": "测试职位",
        "期望薪资": "面议",
        "匹配度": 80,
        "推荐等级": "推荐",
        "核心优势": "这是一条权限测试记录",
        "潜在风险": "无",
        "数据来源": "测试",
        "活跃度": "测试",
        "到岗状态": "测试"
    }
    
    print("\n2. 尝试创建记录...")
    record_id = await feishu_client.add_record(test_data, None)
    
    if record_id:
        print(f"\n✅ 成功！Record ID: {record_id}")
        print("\n飞书权限配置正确！")
        return True
    else:
        print("\n❌ 失败！")
        print("\n请按以下步骤操作：")
        print("\n【方法 1】通过表格设置添加协作者（最简单）")
        print("1. 打开你的飞书表格")
        print("2. 点击右上角「分享」按钮")
        print("3. 点击「添加协作者」")
        print("4. 搜索「AI Headhunter」或粘贴应用 ID")
        print(f"   应用 ID: cli_a99c635ace69501c")
        print("5. 选择「可编辑」权限")
        print("6. 点击「确定」")
        print("\n【方法 2】通过飞书开放平台配置")
        print("1. 访问: https://open.feishu.cn/app")
        print("2. 找到你的应用")
        print("3. 左侧「权限管理」→ 添加以下权限:")
        print("   - 查看、评论、编辑和管理多维表格")
        print("   - 新增数据记录")
        print("   - 查看数据记录")
        print("4. 发布新版本")
        return False

if __name__ == "__main__":
    asyncio.run(test_write())


