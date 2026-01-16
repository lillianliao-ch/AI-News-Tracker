"""
测试新的AI数据源和过滤逻辑
"""
import sys
import os
import asyncio
import feedparser
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.prompts import is_ai_related

# 测试新的数据源
NEW_SOURCES = {
    "量子位": "https://www.qbitai.com/feed",
    "机器之心": "https://www.jiqizhixin.com/feed",
    "VentureBeat AI": "https://venturebeat.com/ai/feed/",
    "Reddit AI": "https://www.reddit.com/r/artificial/.rss",
}

def test_source(name, url):
    """测试单个数据源"""
    print(f"\n{'='*80}")
    print(f"测试数据源: {name}")
    print(f"{'='*80}")

    try:
        feed = feedparser.parse(url)
        total = len(feed.entries)
        print(f"✅ RSS 解析成功，共 {total} 条")

        # 分析前10条
        ai_count = 0
        for i, entry in enumerate(feed.entries[:10], 1):
            title = entry.get('title', '')
            summary = entry.get('summary', '')[:100]

            # 测试过滤逻辑
            is_ai = is_ai_related(title, summary)

            if is_ai:
                ai_count += 1
                status = "✅ AI相关"
            else:
                status = "❌ 非AI"

            print(f"{i}. [{status}] {title}")

            if summary:
                print(f"   摘要: {summary}...")
            print()

        ai_rate = (ai_count / min(10, total)) * 100
        print(f"📊 AI相关率: {ai_count}/{min(10, total)} = {ai_rate:.1f}%")

        return ai_rate

    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return 0

def test_filter_logic():
    """测试过滤逻辑"""
    print(f"\n{'='*80}")
    print("测试过滤逻辑")
    print(f"{'='*80}")

    test_cases = [
        # AI相关
        ("OpenAI发布GPT-5，性能提升300%", "", True),
        ("月之暗面完成10亿美元融资", "", True),
        ("大模型微调实践指南", "", True),
        ("AI Agent在客服领域的应用", "", True),
        ("深度学习框架对比：PyTorch vs TensorFlow", "", True),

        # 非AI
        ("苹果发布新款iPhone 16", "", False),
        ("特斯拉Model Y降价促销", "", False),
        ("腾讯宣布回购1000万股", "", False),
        ("北京新增5条地铁线路", "", False),

        # 边界案例
        ("AI公司完成新一轮融资", "", True),  # AI公司
        ("马斯克收购Twitter后的变化", "", False),  # 虽有科技名人，但非AI
        ("ChatGPT之父：AI将改变世界", "", True),  # 明确AI
    ]

    passed = 0
    for title, summary, expected in test_cases:
        result = is_ai_related(title, summary)
        status = "✅" if result == expected else "❌"

        if result == expected:
            passed += 1

        print(f"{status} {title}")
        print(f"   预期: {expected}, 实际: {result}")
        print()

    accuracy = (passed / len(test_cases)) * 100
    print(f"📊 过滤准确率: {passed}/{len(test_cases)} = {accuracy:.1f}%")

    return accuracy

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 AI News Tracker - 新数据源和过滤逻辑测试")
    print("=" * 80)

    # 测试所有新数据源
    results = {}
    for name, url in NEW_SOURCES.items():
        ai_rate = test_source(name, url)
        results[name] = ai_rate

    # 测试过滤逻辑
    filter_accuracy = test_filter_logic()

    # 总结
    print(f"\n{'='*80}")
    print("📊 测试总结")
    print(f"{'='*80}")

    print("\n数据源AI相关率:")
    for name, rate in results.items():
        print(f"  {name}: {rate:.1f}%")

    avg_rate = sum(results.values()) / len(results) if results else 0
    print(f"\n  平均AI相关率: {avg_rate:.1f}%")

    print(f"\n过滤逻辑准确率: {filter_accuracy:.1f}%")

    # 评估
    print(f"\n{'='*80}")
    print("✅ 评估结果")
    print(f"{'='*80}")

    if avg_rate >= 80:
        print("🎉 优秀！新数据源AI相关率非常高")
    elif avg_rate >= 70:
        print("👍 良好！新数据源AI相关率较高")
    else:
        print("⚠️  需要优化，数据源AI相关率偏低")

    if filter_accuracy >= 90:
        print("🎉 过滤逻辑优秀！")
    elif filter_accuracy >= 80:
        print("👍 过滤逻辑良好！")
    else:
        print("⚠️  过滤逻辑需要优化")

    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
