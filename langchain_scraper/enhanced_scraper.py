#!/usr/bin/env python3
"""
LangChain Contributors Scraper - Enhanced Version
增强版：同时使用 API 和网页解析来提取更完整的联系方式
"""

import requests
import time
import csv
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# GitHub API 配置
GITHUB_API_BASE = "https://api.github.com"
REPO = "langchain-ai/langchain"

# 中国识别关键词
CHINA_LOCATION_KEYWORDS = [
    'china', '中国', 'beijing', 'shanghai', 'hangzhou', 'shenzhen', 
    'guangzhou', 'chengdu', 'nanjing', 'wuhan', 'xian', 'suzhou',
    'tianjin', 'chongqing', 'dongguan', 'foshan', 'hefei', 'zhengzhou',
    'changsha', 'jinan', 'qingdao', 'dalian', 'xiamen', 'fuzhou',
    'ningbo', 'wuxi', 'kunming', 'harbin', 'shenyang', 'zhuhai',
    'cn', 'prc', '北京', '上海', '杭州', '深圳', '广州', '成都'
]

CHINA_COMPANY_KEYWORDS = [
    'alibaba', 'bytedance', 'tencent', 'baidu', 'meituan', 'xiaomi',
    'huawei', 'jd.com', 'jd', 'didi', 'pinduoduo', 'netease', 'kuaishou',
    'bilibili', 'sina', 'weibo', 'douyin', 'ant', 'alipay', 'taobao',
    'tmall', 'cainiao', 'ele.me', 'lazada', 'shopee', 'oppo', 'vivo',
    'lenovo', 'zte', 'sensetime', 'megvii', 'yitu', 'cloudwalk',
    '阿里', '腾讯', '百度', '字节', '美团', '小米', '华为', '京东',
    'kwai', 'toutiao', 'feishu', 'lark', 'zhihu', '知乎', 'xiaoice',
    'milvus', 'zilliz', 'pingcap', 'tidb', 'oceanbase', 'mogdb'
]


def make_api_request(url: str, token: Optional[str] = None) -> Tuple[Optional[Dict], int]:
    """发送 GitHub API 请求"""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LangChain-Contributor-Scraper'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        remaining = int(resp.headers.get('X-RateLimit-Remaining', 60))
        
        if resp.status_code == 200:
            return resp.json(), remaining
        elif resp.status_code == 403:
            print(f"⚠️ Rate limit reached. Remaining: {remaining}")
            return None, 0
        else:
            print(f"❌ API request failed: {resp.status_code}")
            return None, remaining
    except Exception as e:
        print(f"❌ API request error: {e}")
        return None, 0


def scrape_github_profile_page(username: str) -> Dict:
    """
    直接爬取 GitHub 用户主页，提取网页上显示的联系方式
    这可以获取到 API 中不包含的信息 (如邮箱在网页上显示但 API 不返回)
    """
    url = f"https://github.com/{username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    extra_info = {
        'webpage_email': '',
        'webpage_twitter': '',
        'webpage_linkedin': '',
        'webpage_website': ''
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return extra_info
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 方法1: 查找用户信息区域的 itemprop 属性
        # 邮箱通常在 <li class="vcard-detail" itemprop="email">
        email_elem = soup.find('li', {'itemprop': 'email'})
        if email_elem:
            email_link = email_elem.find('a')
            if email_link:
                email = email_link.get_text(strip=True)
                extra_info['webpage_email'] = email
                
        # 方法2: 查找所有 vcard-detail 元素
        vcard_items = soup.find_all('li', class_='vcard-detail')
        for item in vcard_items:
            link = item.find('a')
            if link:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 检查是否是邮箱链接
                if href.startswith('mailto:') or '@' in text:
                    if not extra_info['webpage_email']:
                        email = text if '@' in text else href.replace('mailto:', '')
                        extra_info['webpage_email'] = email
                
                # 检查是否是 Twitter/X 链接
                if 'twitter.com' in href or 'x.com' in href:
                    extra_info['webpage_twitter'] = text
                
                # 检查是否是 LinkedIn 链接
                if 'linkedin.com' in href:
                    extra_info['webpage_linkedin'] = href
                
                # 检查是否是个人网站
                if href.startswith('http') and 'github.com' not in href and 'twitter.com' not in href:
                    if not extra_info['webpage_website']:
                        extra_info['webpage_website'] = href
        
        # 方法3: 正则匹配页面中的邮箱
        if not extra_info['webpage_email']:
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            # 只在 profile 区域搜索，避免匹配到页面其他地方
            profile_div = soup.find('div', class_='js-profile-editable-area')
            if profile_div:
                text = profile_div.get_text()
                emails = re.findall(email_pattern, text)
                if emails:
                    # 过滤掉明显不是个人邮箱的
                    for email in emails:
                        if 'noreply' not in email and 'github' not in email:
                            extra_info['webpage_email'] = email
                            break
        
    except Exception as e:
        print(f"  ⚠️ 网页解析错误 ({username}): {e}")
    
    return extra_info


def contains_chinese(text: str) -> bool:
    """检查文本是否包含中文字符"""
    if not text:
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def is_chinese_user(profile: Dict) -> Tuple[bool, str]:
    """判断用户是否可能是中国用户"""
    if not profile:
        return False, ""
    
    location = (profile.get('location') or '').lower()
    company = (profile.get('company') or '').lower()
    name = profile.get('name') or ''
    bio = profile.get('bio') or ''
    
    reasons = []
    
    for kw in CHINA_LOCATION_KEYWORDS:
        if kw.lower() in location:
            reasons.append(f"Location: {profile.get('location')}")
            break
    
    for kw in CHINA_COMPANY_KEYWORDS:
        if kw.lower() in company:
            reasons.append(f"Company: {profile.get('company')}")
            break
    
    if contains_chinese(name):
        reasons.append(f"Name: {name}")
    
    if contains_chinese(bio):
        reasons.append(f"Bio has Chinese")
    
    return len(reasons) > 0, "; ".join(reasons)


def main():
    """主函数 - 增强版"""
    print("=" * 60)
    print("🦜 LangChain 中国贡献者挖掘工具 (增强版)")
    print("   同时使用 API + 网页解析提取联系方式")
    print("=" * 60)
    
    token = os.environ.get('GITHUB_TOKEN')
    
    # 获取前 100 个贡献者
    print("\n📥 获取 Top 100 贡献者...")
    url = f"{GITHUB_API_BASE}/repos/{REPO}/contributors?per_page=100&page=1"
    contributors, remaining = make_api_request(url, token)
    
    if not contributors:
        print("❌ 获取贡献者失败")
        return
    
    print(f"✅ 获取到 {len(contributors)} 个贡献者 (API 剩余: {remaining})")
    
    # 筛选贡献数 >= 10 的用户
    top_contributors = [c for c in contributors if c.get('contributions', 0) >= 10]
    print(f"📊 其中贡献 >= 10 的有 {len(top_contributors)} 人")
    
    # 分析用户
    chinese_contributors = []
    print(f"\n🔍 正在分析用户画像 (共 {len(top_contributors)} 人)...")
    
    for i, c in enumerate(top_contributors, 1):
        username = c['login']
        contributions = c['contributions']
        
        # 步骤1: 获取 API 数据
        user_url = f"{GITHUB_API_BASE}/users/{username}"
        profile, remaining = make_api_request(user_url, token)
        
        if remaining <= 5:
            print(f"⚠️ API 限额即将用完 ({remaining} 剩余)，停止分析")
            break
        
        if profile:
            is_china, reason = is_chinese_user(profile)
            
            if is_china:
                # 步骤2: 对中国用户，额外爬取网页获取更多联系方式
                print(f"  🔍 [{i}] {username} - 🇨🇳 正在解析网页...")
                webpage_info = scrape_github_profile_page(username)
                
                # 合并 API 和网页数据
                api_email = profile.get('email') or ''
                webpage_email = webpage_info.get('webpage_email', '')
                final_email = api_email or webpage_email  # 优先使用 API 的邮箱
                
                api_twitter = profile.get('twitter_username') or ''
                webpage_twitter = webpage_info.get('webpage_twitter', '')
                final_twitter = api_twitter or webpage_twitter
                
                api_blog = profile.get('blog') or ''
                webpage_website = webpage_info.get('webpage_website', '')
                final_website = api_blog or webpage_website
                
                info = {
                    'login': username,
                    'name': profile.get('name') or '',
                    'contributions': contributions,
                    'location': profile.get('location') or '',
                    'company': profile.get('company') or '',
                    'email': final_email,
                    'email_source': 'API' if api_email else ('Webpage' if webpage_email else ''),
                    'blog': final_website,
                    'twitter': final_twitter,
                    'linkedin': webpage_info.get('webpage_linkedin', ''),
                    'bio': (profile.get('bio') or '')[:100],
                    'github_url': f"https://github.com/{username}",
                    'followers': profile.get('followers', 0),
                    'reason': reason
                }
                chinese_contributors.append(info)
                
                email_display = f"📧 {final_email}" if final_email else "无邮箱"
                print(f"  ✅ [{i}] {username:20} | {contributions:4}次 | {email_display}")
            else:
                if i % 10 == 0:
                    print(f"  ⏳ [{i}/{len(top_contributors)}] 已处理... (API 剩余: {remaining})")
        
        time.sleep(0.8)  # 避免限流
    
    # 保存结果
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if chinese_contributors:
        # CSV
        csv_file = os.path.join(output_dir, f"langchain_chinese_enhanced_{timestamp}.csv")
        fieldnames = ['login', 'name', 'contributions', 'location', 'company', 
                      'email', 'email_source', 'blog', 'twitter', 'linkedin',
                      'github_url', 'followers', 'reason']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for c in chinese_contributors:
                row = {k: c.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        print(f"\n💾 CSV 结果已保存到: {csv_file}")
        
        # JSON
        json_file = os.path.join(output_dir, f"langchain_chinese_enhanced_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(chinese_contributors, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON 结果已保存到: {json_file}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 结果摘要")
    print("=" * 60)
    print(f"分析的贡献者数: {len(top_contributors)}")
    print(f"发现的中国贡献者数: {len(chinese_contributors)}")
    
    # 统计邮箱获取情况
    with_email = [c for c in chinese_contributors if c.get('email')]
    print(f"成功获取邮箱: {len(with_email)}/{len(chinese_contributors)}")
    
    if chinese_contributors:
        print("\n🏆 中国贡献者列表 (含联系方式):")
        print("-" * 100)
        print(f"{'#':3} | {'GitHub ID':20} | {'贡献':5} | {'邮箱':25} | {'位置/公司'}")
        print("-" * 100)
        for i, c in enumerate(chinese_contributors, 1):
            loc_or_company = c.get('company') or c.get('location') or ''
            email = c.get('email', '')[:25] or '(未获取)'
            print(f"{i:3} | {c['login']:20} | {c['contributions']:5} | {email:25} | {loc_or_company[:30]}")
    
    print("\n✅ 任务完成!")


if __name__ == "__main__":
    main()
