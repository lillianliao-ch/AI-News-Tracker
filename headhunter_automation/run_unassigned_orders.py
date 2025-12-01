#!/usr/bin/env python3
"""
未分配订单抓取启动脚本
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from automation.unassigned_orders_scraper import UnassignedOrdersScraper

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 未分配订单抓取工具")
    print("=" * 60)
    print("这个工具会登录猎头系统，抓取最新的3条未分配订单")
    print("并获取详细信息包括：职位名称、部门、岗位描述")
    print("=" * 60)
    
    try:
        # 创建抓取器实例
        scraper = UnassignedOrdersScraper()
        
        # 运行自动化流程
        orders = scraper.run_full_automation(count=3)
        
        if orders:
            print(f"\n✅ 成功获取 {len(orders)} 条最新未分配订单的详细信息")
            print("\n📊 数据摘要:")
            print("-" * 60)
            
            for i, order in enumerate(orders, 1):
                print(f"{i}. 职位名称: {order['职位名称']}")
                print(f"   部门: {order['部门']}")
                print(f"   岗位描述: {order['岗位描述'][:100]}{'...' if len(order['岗位描述']) > 100 else ''}")
                print(f"   更新日期: {order['更新日期']}")
                print("-" * 60)
            
            print(f"\n💾 详细数据已保存到 data/ 目录")
            print("📄 您可以查看生成的JSON文件获取完整信息")
        else:
            print("\n❌ 未获取到任何订单数据")
            print("请检查登录凭据和网络连接")
            
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        print("请查看日志文件获取详细错误信息")

if __name__ == "__main__":
    main()
