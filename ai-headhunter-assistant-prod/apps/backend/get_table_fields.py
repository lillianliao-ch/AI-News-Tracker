#!/usr/bin/env python3
"""
获取飞书表格的字段列表
"""
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
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    return None

def get_table_fields(token):
    """获取表格字段列表"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/fields"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    print("=" * 70)
    print("飞书表格字段列表")
    print("=" * 70)
    print(f"\nApp Token: {APP_TOKEN}")
    print(f"Table ID: {TABLE_ID}\n")
    
    response = requests.get(url, headers=headers)
    result = response.json()
    
    if result.get("code") == 0:
        fields = result.get("data", {}).get("items", [])
        print(f"找到 {len(fields)} 个字段:\n")
        print(f"{'序号':<5} {'字段名':<25} {'字段类型':<15} {'Field ID'}")
        print("-" * 70)
        
        for idx, field in enumerate(fields, 1):
            field_name = field.get("field_name", "")
            field_type = field.get("type", "")
            field_id = field.get("field_id", "")
            print(f"{idx:<5} {field_name:<25} {field_type:<15} {field_id}")
        
        print("\n" + "=" * 70)
        print("字段类型说明:")
        print("=" * 70)
        print("1  - 多行文本")
        print("2  - 数字")
        print("3  - 单选")
        print("4  - 多选")
        print("5  - 日期")
        print("7  - 复选框")
        print("11 - 人员")
        print("13 - 电话号码")
        print("15 - 超链接")
        print("17 - 附件")
        print("18 - 关联")
        print("20 - 公式")
        print("21 - 双向关联")
        print("1001 - 创建时间")
        print("1002 - 最后更新时间")
        print("1003 - 创建人")
        print("1004 - 修改人")
        print("1005 - 自动编号")
        
        return fields
    else:
        print(f"❌ 获取字段失败: {result}")
        return None

def main():
    token = get_tenant_access_token()
    if not token:
        print("❌ 无法获取 token")
        return
    
    fields = get_table_fields(token)

if __name__ == "__main__":
    main()


