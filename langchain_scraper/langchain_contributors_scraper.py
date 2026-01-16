#!/usr/bin/env python3
"""
LangChain Contributors Scraper
用于获取 LangChain 项目的贡献者信息，并筛选出中国贡献者
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


def get_github_token() -> Optional[str]:
    """获取 GitHub Token（从环境变量）"""
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return token
    # 尝试从常见配置文件读取
    token_file = os.path.expanduser('~/.github_token')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return None


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
        remaining = int(resp.headers.get('X-RateLimit-Remaining', 0))
        
        if resp.status_code == 200:
            return resp.json(), remaining
        elif resp.status_code == 403 and remaining == 0:
            reset_time = int(resp.headers.get('X-RateLimit-Reset', 0))
            wait_time = reset_time - int(time.time()) + 1
            print(f"⚠️ Rate limit exceeded. Waiting {wait_time} seconds...")
            time.sleep(max(wait_time, 60))
            return make_request(url, token)  # Retry
        else:
            print(f"❌ Request failed: {resp.status_code} - {url}")
            return None, remaining
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None, 0


def get_all_contributors(token: Optional[str] = None, min_contributions: int = 5) -> List[Dict]:
    """获取所有贡献者（按贡献数排序）"""
    contributors = []
    page = 1
    
    print("📥 正在获取 LangChain 贡献者列表...")
    
    while True:
        url = f"{GITHUB_API_BASE}/repos/{REPO}/contributors?per_page=100&page={page}"
        data, remaining = make_request(url, token)
        
        if not data:
            break
        
        # 只保留贡献数 >= min_contributions 的用户
        filtered = [c for c in data if c.get('contributions', 0) >= min_contributions]
        contributors.extend(filtered)
        
        print(f"  📄 第 {page} 页: 获取 {len(data)} 个贡献者, 保留 {len(filtered)} 个 (贡献>={min_contributions})")
        
        if len(data) < 100:
            break
        
        page += 1
        time.sleep(0.5)  # 避免限流
    
    print(f"✅ 共获取 {len(contributors)} 个贡献者 (贡献>={min_contributions})")
    return contributors


def get_user_profile(username: str, token: Optional[str] = None) -> Optional[Dict]:
    """获取用户详细信息"""
    url = f"{GITHUB_API_BASE}/users/{username}"
    data, _ = make_request(url, token)
    return data


def contains_chinese(text: str) -> bool:
    """检查文本是否包含中文字符"""
    if not text:
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def is_chinese_user(profile: Dict) -> Tuple[bool, str]:
    """
    判断用户是否可能是中国用户
    返回: (是否中国用户, 判断依据)
    """
    if not profile:
        return False, ""
    
    location = (profile.get('location') or '').lower()
    company = (profile.get('company') or '').lower()
    name = profile.get('name') or ''
    bio = profile.get('bio') or ''
    
    reasons = []
    
    # 1. 检查位置
    for kw in CHINA_LOCATION_KEYWORDS:
        if kw.lower() in location:
            reasons.append(f"Location: {profile.get('location')}")
            break
    
    # 2. 检查公司
    for kw in CHINA_COMPANY_KEYWORDS:
        if kw.lower() in company:
            reasons.append(f"Company: {profile.get('company')}")
            break
    
    # 3. 检查中文姓名
    if contains_chinese(name):
        reasons.append(f"Name has Chinese: {name}")
    
    # 4. 检查中文简介
    if contains_chinese(bio):
        reasons.append(f"Bio has Chinese")
    
    is_china = len(reasons) > 0
    return is_china, "; ".join(reasons)


def analyze_contributors(contributors: List[Dict], token: Optional[str] = None) -> List[Dict]:
    """分析贡献者，筛选中国用户"""
    chinese_contributors = []
    total = len(contributors)
    
    print(f"\n🔍 正在分析 {total} 个贡献者的用户画像...")
    
    for i, c in enumerate(contributors, 1):
        username = c['login']
        contributions = c['contributions']
        
        profile = get_user_profile(username, token)
        if not profile:
            continue
        
        is_china, reason = is_chinese_user(profile)
        
        if is_china:
            contributor_info = {
                'login': username,
                'name': profile.get('name') or '',
                'contributions': contributions,
                'location': profile.get('location') or '',
                'company': profile.get('company') or '',
                'email': profile.get('email') or '',
                'blog': profile.get('blog') or '',
                'twitter': profile.get('twitter_username') or '',
                'bio': (profile.get('bio') or '')[:200],  # 限制长度
                'github_url': f"https://github.com/{username}",
                'followers': profile.get('followers', 0),
                'reason': reason
            }
            chinese_contributors.append(contributor_info)
            print(f"  ✅ [{i}/{total}] {username} - 🇨🇳 中国用户 ({reason[:50]}...)")
        else:
            if i % 20 == 0:
                print(f"  ⏳ [{i}/{total}] 已处理...")
        
        time.sleep(0.3)  # 避免限流
    
    print(f"\n✅ 筛选完成: 共发现 {len(chinese_contributors)} 个中国贡献者")
    return chinese_contributors


def save_to_csv(contributors: List[Dict], filename: str):
    """保存结果到 CSV"""
    if not contributors:
        print("⚠️ 没有数据可保存")
        return
    
    fieldnames = ['login', 'name', 'contributions', 'location', 'company', 
                  'email', 'blog', 'twitter', 'bio', 'github_url', 'followers', 'reason']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(contributors)
    
    print(f"💾 结果已保存到: {filename}")


def save_to_json(contributors: List[Dict], filename: str):
    """保存结果到 JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(contributors, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON 结果已保存到: {filename}")


def main():
    """主函数"""
    print("=" * 60)
    print("🦜 LangChain 中国贡献者挖掘工具")
    print("=" * 60)
    
    # 获取 Token
    token = get_github_token()
    if token:
        print("✅ 已使用 GitHub Token (5000 requests/hour)")
    else:
        print("⚠️ 未设置 GitHub Token，API 限流为 60 requests/hour")
        print("   设置方法: export GITHUB_TOKEN='your_token'")
    
    # 输出目录
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 阶段 1 & 2: 获取贡献者列表
    contributors = get_all_contributors(token, min_contributions=5)
    
    # 保存原始贡献者列表
    raw_file = os.path.join(output_dir, f"langchain_contributors_raw_{timestamp}.json")
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(contributors, f, ensure_ascii=False, indent=2)
    print(f"💾 原始贡献者列表已保存到: {raw_file}")
    
    # 阶段 3: 分析并筛选中国用户
    chinese_contributors = analyze_contributors(contributors, token)
    
    # 按贡献数排序
    chinese_contributors.sort(key=lambda x: x['contributions'], reverse=True)
    
    # 保存结果
    csv_file = os.path.join(output_dir, f"langchain_chinese_contributors_{timestamp}.csv")
    json_file = os.path.join(output_dir, f"langchain_chinese_contributors_{timestamp}.json")
    
    save_to_csv(chinese_contributors, csv_file)
    save_to_json(chinese_contributors, json_file)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 结果摘要")
    print("=" * 60)
    print(f"总贡献者数: {len(contributors)}")
    print(f"中国贡献者数: {len(chinese_contributors)}")
    
    if chinese_contributors:
        print("\n🏆 Top 10 中国贡献者:")
        print("-" * 60)
        for i, c in enumerate(chinese_contributors[:10], 1):
            print(f"{i:2}. {c['login']:20} | {c['contributions']:4}次 | {c['name'][:15]:15} | {c['company'][:20]}")
    
    print("\n✅ 任务完成!")


if __name__ == "__main__":
    main()
