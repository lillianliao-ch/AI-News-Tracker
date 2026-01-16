#!/usr/bin/env python3
"""
手动测试飞书 API - 直接使用 HTTP 请求
验证 tenant_access_token 是否有效
"""
import asyncio
import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")
TABLE_ID = os.getenv("FEISHU_TABLE_ID")

def get_tenant_access_token():
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    
    print("=" * 70)
    print("步骤 1: 获取 tenant_access_token")
    print("=" * 70)
    print(f"请求 URL: {url}")
    print(f"App ID: {APP_ID}")
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print(f"响应状态: {response.status_code}")
    print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") == 0:
        token = result.get("tenant_access_token")
        print(f"\n✅ Token 获取成功: {token[:30]}...")
        return token
    else:
        print(f"\n❌ Token 获取失败")
        return None

def test_create_record(token):
    """测试创建记录"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    from datetime import datetime
    
    data = {
        "fields": {
            "文本": "TEST_MANUAL_20251114",
            "姓名": "手动测试",
            "年龄": 30,
            "工作年限": 5,
            "学历": "本科",
            "当前公司": "测试公司",
            "当前职位": "测试职位",
            "期望薪资": "面议",
            "匹配度": 80,
            "推荐等级": "推荐",
            "核心优势": "这是手动 HTTP 请求测试",
            "潜在风险": "无",
            "数据来源": {
                "link": "https://www.zhipin.com/web/chat/recommend",
                "text": "Boss直聘"
            },
            "活跃度": "测试",
            "到岗状态": "测试",
            "采集时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    print("\n" + "=" * 70)
    print("步骤 2: 创建记录")
    print("=" * 70)
    print(f"请求 URL: {url}")
    print(f"Authorization: Bearer {token[:30]}...")
    print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print(f"\n响应状态: {response.status_code}")
    print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200 and result.get("code") == 0:
        print("\n" + "=" * 70)
        print("🎉 成功！记录已创建！")
        print("=" * 70)
        print(f"Record ID: {result.get('data', {}).get('record', {}).get('record_id')}")
        print("\n✅ 飞书集成配置完全正确！")
        print("\n现在可以:")
        print("1. 在 Boss 直聘页面使用插件")
        print("2. 推荐候选人会自动同步到飞书")
        return True
    else:
        print("\n" + "=" * 70)
        print("❌ 失败！")
        print("=" * 70)
        
        error_code = result.get("code")
        error_msg = result.get("msg")
        
        print(f"\n错误码: {error_code}")
        print(f"错误信息: {error_msg}")
        
        if error_code == 91403 or "403" in str(error_code):
            print("\n【诊断】403 Forbidden - 权限不足")
            print("\n最可能的原因:")
            print("1. ⚠️ 应用虽然有全局权限，但这个表格没有授权给应用")
            print("2. ⚠️ 需要在表格中手动添加应用为协作者")
            print("\n解决方法:")
            print("由于通过「添加协作者」搜索不到应用，请尝试:")
            print("\n【方法 A】通过飞书工作台")
            print("1. 打开飞书客户端 → 底部「工作台」")
            print("2. 搜索「AIING」")
            print("3. 点击「添加」或「启用」")
            print("4. 授权应用访问多维表格")
            print("5. 然后再回到表格尝试添加协作者")
            print("\n【方法 B】使用 Open App Token（推荐）")
            print("1. 打开飞书表格")
            print("2. 点击右上角「...」→「高级设置」")
            print("3. 找到「API」或「开放平台」设置")
            print("4. 添加应用并授权")
            print("\n【方法 C】联系表格创建者")
            print("如果你不是表格创建者，请联系创建者:")
            print("1. 请求创建者在表格设置中添加协作者")
            print("2. 或请求创建者将表格所有权转移给你")
            
        elif error_code == 91402:
            print("\n【诊断】91402 - 表格不存在")
            print("请检查 APP_TOKEN 和 TABLE_ID 是否正确")
            
        return False

def main():
    print("\n" + "=" * 70)
    print("飞书 API 手动测试")
    print("=" * 70)
    print(f"\n配置信息:")
    print(f"App ID: {APP_ID}")
    print(f"App Token: {APP_TOKEN}")
    print(f"Table ID: {TABLE_ID}")
    
    # 1. 获取 token
    token = get_tenant_access_token()
    if not token:
        return
    
    # 2. 测试创建记录
    test_create_record(token)

if __name__ == "__main__":
    main()

