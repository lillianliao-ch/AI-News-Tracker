#!/usr/bin/env python3
"""
LangChain Contributors Scraper - Quick Mode
用于快速获取 LangChain 项目的中国贡献者信息
"""

import requests
import time
import csv
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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


def make_request(url: str, token: Optional[str] = None) -> Tuple[Optional[Dict], int]:
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
            print(f"❌ Request failed: {resp.status_code} - {url}")
            return None, remaining
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None, 0


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
    """主函数 - 快速模式"""
    print("=" * 60)
    print("🦜 LangChain 中国贡献者挖掘工具 (快速模式)")
    print("=" * 60)
    
    token = os.environ.get('GITHUB_TOKEN')
    
    # 获取前 100 个贡献者
    print("\n📥 获取 Top 100 贡献者...")
    url = f"{GITHUB_API_BASE}/repos/{REPO}/contributors?per_page=100&page=1"
    contributors, remaining = make_request(url, token)
    
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
        
        # 获取用户详情
        user_url = f"{GITHUB_API_BASE}/users/{username}"
        profile, remaining = make_request(user_url, token)
        
        if remaining <= 5:
            print(f"⚠️ API 限额即将用完 ({remaining} 剩余)，停止分析")
            break
        
        if profile:
            is_china, reason = is_chinese_user(profile)
            
            if is_china:
                info = {
                    'login': username,
                    'name': profile.get('name') or '',
                    'contributions': contributions,
                    'location': profile.get('location') or '',
                    'company': profile.get('company') or '',
                    'email': profile.get('email') or '',
                    'blog': profile.get('blog') or '',
                    'twitter': profile.get('twitter_username') or '',
                    'bio': (profile.get('bio') or '')[:100],
                    'github_url': f"https://github.com/{username}",
                    'followers': profile.get('followers', 0),
                    'reason': reason
                }
                chinese_contributors.append(info)
                print(f"  ✅ [{i}] {username:20} | {contributions:4}次 | 🇨🇳 {reason[:40]}")
            else:
                if i % 10 == 0:
                    print(f"  ⏳ [{i}/{len(top_contributors)}] 已处理... (API 剩余: {remaining})")
        
        time.sleep(0.8)  # 避免限流
    
    # 保存结果
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if chinese_contributors:
        # CSV
        csv_file = os.path.join(output_dir, f"langchain_chinese_contributors_{timestamp}.csv")
        fieldnames = ['login', 'name', 'contributions', 'location', 'company', 
                      'email', 'blog', 'twitter', 'github_url', 'followers', 'reason']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for c in chinese_contributors:
                row = {k: c.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        print(f"\n💾 CSV 结果已保存到: {csv_file}")
        
        # JSON
        json_file = os.path.join(output_dir, f"langchain_chinese_contributors_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(chinese_contributors, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON 结果已保存到: {json_file}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 结果摘要")
    print("=" * 60)
    print(f"分析的贡献者数: {len(top_contributors)}")
    print(f"发现的中国贡献者数: {len(chinese_contributors)}")
    
    if chinese_contributors:
        print("\n🏆 中国贡献者列表:")
        print("-" * 80)
        print(f"{'#':3} | {'GitHub ID':20} | {'贡献':5} | {'姓名':15} | {'公司/位置'}")
        print("-" * 80)
        for i, c in enumerate(chinese_contributors, 1):
            loc_or_company = c.get('company') or c.get('location') or ''
            print(f"{i:3} | {c['login']:20} | {c['contributions']:5} | {c['name'][:15]:15} | {loc_or_company[:30]}")
    
    print("\n✅ 任务完成!")


if __name__ == "__main__":
    main()
