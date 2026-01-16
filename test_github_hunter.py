#!/usr/bin/env python3
"""
GitHub Hunter 测试脚本
快速验证功能是否正常
"""

from github_hunter_simple import GitHubHunter

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("GitHub Hunter - 功能测试")
    print("=" * 60)

    # 初始化（不使用 token，速率限制 60次/小时）
    print("\n📌 初始化 GitHub Hunter...")
    hunter = GitHubHunter(token=None)
    print("✅ 初始化成功")

    # 测试 URL 提取
    print("\n📌 测试 URL 提取...")
    test_urls = [
        'https://github.com/torvalds',
        'https://github.com/python/cpython',
        'github.com/gvanrossum',
    ]

    for url in test_urls:
        username = hunter.extract_username(url)
        print(f"  {url} → {username}")

    # 测试单个用户分析
    print("\n📌 测试单个用户分析...")
    test_username = 'torvalds'

    profile = hunter.get_user_profile(test_username)
    if profile:
        print(f"✅ 成功获取 {test_username} 信息:")
        print(f"  姓名: {profile['name']}")
        print(f"  公司: {profile['company']}")
        print(f"  位置: {profile['location']}")
        print(f"  Bio: {profile['bio']}")
        print(f"  仓库数: {profile['public_repos']}")
        print(f"  粉丝: {profile['followers']}")
    else:
        print(f"❌ 获取 {test_username} 失败")

    # 测试仓库获取
    print("\n📌 测试仓库信息获取...")
    repos = hunter.get_user_repos(test_username, limit=5)
    print(f"✅ 获取到 {len(repos)} 个仓库:")
    for repo in repos[:3]:
        print(f"  • {repo['repo_name']} - {repo['language']} ({repo['stars']}★)")

    # 测试语言统计
    print("\n📌 测试编程语言统计...")
    languages = hunter.get_user_languages(repos)
    print(f"✅ 主要语言: {', '.join(list(languages.keys())[:5])}")

    # 测试邮箱提取
    print("\n📌 测试邮箱提取...")
    emails = hunter.get_user_emails(test_username)
    if emails:
        print(f"✅ 找到邮箱: {', '.join(emails)}")
    else:
        print(f"⚠️ 未找到公开邮箱")

    # 测试完整分析
    print("\n📌 测试完整候选人分析...")
    candidate = hunter.analyze_candidate('https://github.com/torvalds')
    if candidate:
        print("✅ 完整分析成功:")
        print(f"  GitHub: {candidate['github_url']}")
        print(f"  邮箱: {candidate['emails']}")
        print(f"  主要语言: {candidate['primary_languages']}")
        print(f"  总Stars: {candidate['total_stars']}")
        print(f"  原创仓库: {candidate['original_repos']}")
    else:
        print("❌ 完整分析失败")

    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)

def test_batch_analysis():
    """测试批量分析"""
    print("\n" + "=" * 60)
    print("批量分析测试")
    print("=" * 60)

    hunter = GitHubHunter(token=None)

    # 测试 URL 列表
    test_urls = [
        'https://github.com/torvalds',
        'https://github.com/gvanrossum',
        'https://github.com/NanmiCoder',
    ]

    print(f"\n📌 批量分析 {len(test_urls)} 个用户...")

    results = hunter.batch_analyze(test_urls, delay=2)

    print(f"\n✅ 成功分析 {len(results)} 个用户:")
    for result in results:
        print(f"  • {result['username']} ({result['name']}) - {result['company']}")

    # 保存结果
    print("\n📌 保存结果...")
    hunter.save_to_excel(results, 'test_candidates.xlsx')
    hunter.save_to_json(results, 'test_candidates.json')

    print("\n✅ 批量分析测试完成！")

if __name__ == "__main__":
    # 运行基本功能测试
    test_basic_functionality()

    # 运行批量分析测试（可选，注释掉以避免 GitHub API 限制）
    # test_batch_analysis()

    print("\n💡 提示:")
    print("  1. 添加 GitHub Token 可提升速率限制到 5000次/小时")
    print("  2. 详见 GITHUB_HUNTER_GUIDE.md")
    print("  3. 配置文件: github_hunter_config.py")
