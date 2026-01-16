#!/usr/bin/env python3
"""
GitHub 中国贡献者挖掘工具 - 通用版
可用于任意 GitHub 仓库

使用方法:
export GITHUB_TOKEN="your_token"
python3 github_china_scraper.py owner/repo
"""

import requests
import time
import csv
import json
import re
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# GraphQL endpoint
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REST_URL = "https://api.github.com"

# 中国识别关键词
CHINA_LOCATION_KEYWORDS = [
    'china', '中国', 'beijing', 'shanghai', 'hangzhou', 'shenzhen', 
    'guangzhou', 'chengdu', 'nanjing', 'wuhan', 'xian', 'suzhou',
    'tianjin', 'chongqing', 'hefei', 'zhengzhou', 'changsha',
    '北京', '上海', '杭州', '深圳', '广州', '成都', '合肥', '西安',
    'hong kong', 'hongkong', '香港', 'taiwan', '台湾', 'taipei', '台北'
]

CHINA_COMPANY_KEYWORDS = [
    'alibaba', 'bytedance', 'tencent', 'baidu', 'meituan', 'xiaomi',
    'huawei', 'jd', 'didi', 'pinduoduo', 'netease', 'kuaishou',
    'bilibili', 'zilliz', 'pingcap', 'milvus', 'tidb', 'dify',
    '阿里', '腾讯', '百度', '字节', '美团', '小米', '华为', '京东',
    'ant', 'alipay', 'taobao', 'cainiao', 'ele.me', 'feishu', 'lark'
]


class GitHubChinaScraper:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo  # format: owner/repo
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'GitHub-China-Contributor-Scraper'
        }
        self.rest_headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-China-Contributor-Scraper'
        }
    
    def graphql_query(self, query: str, variables: Dict = None) -> Optional[Dict]:
        """执行 GraphQL 查询"""
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        try:
            resp = requests.post(GITHUB_GRAPHQL_URL, headers=self.headers, 
                               json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if 'errors' in data:
                    # 跳过 bot 用户等错误，不打印
                    return None
                return data.get('data')
            else:
                print(f"❌ GraphQL failed: {resp.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_user_details(self, username: str) -> Optional[Dict]:
        """获取用户详细信息"""
        query = """
        query($login: String!) {
          user(login: $login) {
            login
            name
            email
            bio
            location
            company
            websiteUrl
            twitterUsername
            followers {
              totalCount
            }
            socialAccounts(first: 10) {
              nodes {
                provider
                url
              }
            }
          }
        }
        """
        result = self.graphql_query(query, {'login': username})
        if result and result.get('user'):
            return result['user']
        return None
    
    def get_contributors(self, min_contributions: int = 5) -> List[Dict]:
        """获取贡献者列表"""
        contributors = []
        page = 1
        
        print(f"📥 获取 {self.repo} 贡献者列表...")
        
        while True:
            url = f"{GITHUB_REST_URL}/repos/{self.repo}/contributors?per_page=100&page={page}"
            try:
                resp = requests.get(url, headers=self.rest_headers, timeout=30)
                if resp.status_code != 200:
                    print(f"❌ REST API failed: {resp.status_code}")
                    break
                
                data = resp.json()
                if not data:
                    break
                
                filtered = [c for c in data if c.get('contributions', 0) >= min_contributions]
                contributors.extend(filtered)
                
                print(f"  📄 第 {page} 页: {len(data)} 人, 保留 {len(filtered)} 人 (贡献>={min_contributions})")
                
                if len(data) < 100:
                    break
                
                page += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print(f"✅ 共获取 {len(contributors)} 个贡献者")
        return contributors
    
    def is_chinese_user(self, user: Dict) -> Tuple[bool, str]:
        """判断是否为中国用户"""
        location = (user.get('location') or '').lower()
        company = (user.get('company') or '').lower()
        name = user.get('name') or ''
        bio = user.get('bio') or ''
        
        reasons = []
        
        for kw in CHINA_LOCATION_KEYWORDS:
            if kw.lower() in location:
                reasons.append(f"Location: {user.get('location')}")
                break
        
        for kw in CHINA_COMPANY_KEYWORDS:
            if kw.lower() in company:
                reasons.append(f"Company: {user.get('company')}")
                break
        
        if re.search(r'[\u4e00-\u9fff]', name):
            reasons.append(f"Name: {name}")
        
        if re.search(r'[\u4e00-\u9fff]', bio or ''):
            reasons.append("Bio has Chinese")
        
        return len(reasons) > 0, "; ".join(reasons)
    
    def scrape(self, min_contributions: int = 5) -> List[Dict]:
        """执行抓取"""
        contributors = self.get_contributors(min_contributions)
        
        chinese_users = []
        total = len(contributors)
        
        print(f"\n🔍 分析 {total} 个贡献者...")
        
        for i, c in enumerate(contributors, 1):
            username = c['login']
            contributions = c['contributions']
            
            # 跳过 bot
            if '[bot]' in username or username.endswith('-bot'):
                continue
            
            user = self.get_user_details(username)
            if not user:
                continue
            
            is_china, reason = self.is_chinese_user(user)
            
            if is_china:
                social = {}
                for acc in user.get('socialAccounts', {}).get('nodes', []):
                    provider = acc.get('provider', '').lower()
                    url = acc.get('url', '')
                    social[provider] = url
                
                info = {
                    'login': username,
                    'name': user.get('name') or '',
                    'contributions': contributions,
                    'email': user.get('email') or '',
                    'location': user.get('location') or '',
                    'company': user.get('company') or '',
                    'blog': user.get('websiteUrl') or '',
                    'twitter': user.get('twitterUsername') or '',
                    'linkedin': social.get('linkedin', ''),
                    'bio': (user.get('bio') or '')[:100],
                    'github_url': f"https://github.com/{username}",
                    'followers': user.get('followers', {}).get('totalCount', 0),
                    'reason': reason
                }
                chinese_users.append(info)
                
                email_status = f"📧 {info['email']}" if info['email'] else "无邮箱"
                print(f"  ✅ [{i}/{total}] {username:25} | {contributions:4}次 | {email_status}")
            else:
                if i % 20 == 0:
                    print(f"  ⏳ [{i}/{total}] 已处理...")
            
            time.sleep(0.15)
        
        return chinese_users


def main():
    # 默认仓库或从命令行参数获取
    if len(sys.argv) > 1:
        repo = sys.argv[1]
    else:
        repo = "langgenius/dify"  # 默认分析 Dify
    
    # 从参数获取最小贡献数
    min_contrib = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print("=" * 70)
    print(f"🚀 GitHub 中国贡献者挖掘工具")
    print(f"   目标仓库: {repo}")
    print("=" * 70)
    
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("\n❌ 未设置 GITHUB_TOKEN！")
        print("   运行: export GITHUB_TOKEN='ghp_xxxxx'")
        return
    
    print(f"✅ GitHub Token 已设置")
    
    scraper = GitHubChinaScraper(token, repo)
    chinese_users = scraper.scrape(min_contributions=min_contrib)
    
    if not chinese_users:
        print("⚠️ 未发现中国贡献者")
        return
    
    chinese_users.sort(key=lambda x: x['contributions'], reverse=True)
    
    # 保存结果
    output_dir = os.path.dirname(os.path.abspath(__file__))
    repo_name = repo.replace('/', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV
    csv_file = os.path.join(output_dir, f"{repo_name}_chinese_{timestamp}.csv")
    fieldnames = ['login', 'name', 'contributions', 'email', 'location', 
                  'company', 'blog', 'twitter', 'linkedin', 'github_url', 
                  'followers', 'reason']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in chinese_users:
            row = {k: c.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    print(f"\n💾 CSV: {csv_file}")
    
    # JSON
    json_file = os.path.join(output_dir, f"{repo_name}_chinese_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(chinese_users, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON: {json_file}")
    
    # 摘要
    print("\n" + "=" * 70)
    print("📊 结果摘要")
    print("=" * 70)
    
    with_email = [u for u in chinese_users if u.get('email')]
    print(f"发现中国贡献者: {len(chinese_users)}")
    print(f"成功获取邮箱: {len(with_email)}/{len(chinese_users)}")
    
    print(f"\n🏆 {repo} 中国贡献者 Top 20:")
    print("-" * 100)
    print(f"{'#':3} | {'GitHub':25} | {'贡献':5} | {'邮箱':30} | {'公司/位置'}")
    print("-" * 100)
    for i, u in enumerate(chinese_users[:20], 1):
        email = u.get('email', '')[:30] or '(无)'
        loc = u.get('company') or u.get('location') or ''
        print(f"{i:3} | {u['login']:25} | {u['contributions']:5} | {email:30} | {loc[:25]}")
    
    print("\n✅ 完成!")


if __name__ == "__main__":
    main()
