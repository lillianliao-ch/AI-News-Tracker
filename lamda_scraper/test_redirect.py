#!/usr/bin/env python3
"""
测试重定向跟随功能
验证陈雄辉案例和其他重定向案例
"""

import requests
from bs4 import BeautifulSoup


def test_redirect(url, name):
    """测试单个 URL 的重定向"""
    print(f"\n{'='*80}")
    print(f"测试: {name}")
    print(f"{'='*80}")
    print(f"原始 URL: {url}")

    try:
        # 发送请求，跟随重定向
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        resp = session.get(url, timeout=30, verify=True, allow_redirects=True)

        # 获取最终 URL
        final_url = resp.url
        redirect_count = len(resp.history)

        print(f"状态码: {resp.status_code}")
        print(f"重定向次数: {redirect_count}")
        print(f"最终 URL: {final_url}")

        if final_url != url:
            print(f"\n✓ 发生重定向!")
            print(f"  {url}")
            print(f"     ↓")
            print(f"  {final_url}")

            # 显示重定向链
            if resp.history:
                print(f"\n重定向链:")
                for i, r in enumerate(resp.history, 1):
                    print(f"  {i}. {r.url} → {r.status_code}")
                print(f"  {len(resp.history)+1}. {final_url} → {resp.status_code}")

        # 尝试提取邮箱
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 查找 Cloudflare 邮件保护
        cloudflare_links = soup.find_all('a', href=lambda x: x and '/cdn-cgi/l/email-protection' in x)
        if cloudflare_links:
            print(f"\n✓ 发现 {len(cloudflare_links)} 个 Cloudflare 保护邮箱")
            for link in cloudflare_links[:3]:  # 只显示前3个
                print(f"  - {link.get('href')}")

        # 查找明文邮箱
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, resp.text)

        # 过滤邮箱
        valid_emails = [
            e for e in emails
            if 'noreply' not in e and
               'github' not in e and
               'example' not in e and
               'localhost' not in e and
               'test' not in e.lower() and
               'w3.org' not in e
        ]

        if valid_emails:
            print(f"\n✓ 发现 {len(valid_emails)} 个邮箱:")
            for email in valid_emails[:5]:  # 只显示前5个
                print(f"  - {email}")

        return {
            'original_url': url,
            'final_url': final_url,
            'redirect_count': redirect_count,
            'status_code': resp.status_code,
            'cloudflare_emails': len(cloudflare_links),
            'plain_emails': len(valid_emails),
            'emails': valid_emails[:5]
        }

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return None


def main():
    """主函数"""
    print("="*80)
    print("重定向跟随功能测试")
    print("="*80)

    # 测试案例
    test_cases = [
        {
            'name': '陈雄辉 - LAMDA 主页',
            'url': 'http://www.lamda.nju.edu.cn/chenxh/',
            'expected': 'https://xionghuichen.github.io/'
        },
        {
            'name': '杨嘉祺 - 个人网站',
            'url': 'https://academic.thyrixyang.com',
            'expected': '无重定向（已有 Cloudflare 保护）'
        },
        {
            'name': 'GitHub Pages 重定向',
            'url': 'http://pages.github.com/',
            'expected': 'https://pages.github.com/'
        }
    ]

    results = []

    for case in test_cases:
        result = test_redirect(case['url'], case['name'])
        if result:
            result['name'] = case['name']
            result['expected'] = case['expected']
            results.append(result)

    # 总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")

    for r in results:
        print(f"\n{r['name']}:")
        print(f"  重定向: {r['redirect_count']} 次")
        print(f"  最终 URL: {r['final_url']}")
        print(f"  预期: {r['expected']}")

        if r['final_url'] == r['expected'] or r['expected'] in r['final_url']:
            print(f"  状态: ✅ 符合预期")
        else:
            print(f"  状态: ⚠️ 需要检查")

        if r['cloudflare_emails'] > 0:
            print(f"  Cloudflare 邮箱: {r['cloudflare_emails']} 个")

        if r['plain_emails'] > 0:
            print(f"  明文邮箱: {r['plain_emails']} 个")
            print(f"  示例: {r['emails'][0] if r['emails'] else 'N/A'}")

    print(f"\n{'='*80}")
    print("✅ 重定向功能测试完成!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
