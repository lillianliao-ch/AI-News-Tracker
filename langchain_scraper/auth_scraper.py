#!/usr/bin/env python3
"""
LangChain Contributors Scraper - Authenticated Version
使用 GitHub Token 认证获取完整联系方式（包括隐藏邮箱）

使用前请先设置环境变量:
export GITHUB_TOKEN="your_personal_access_token"

获取 Token 步骤:
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 "read:user" 和 "user:email" 权限
4. 复制生成的 token
"""

import requests
import time
import csv
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# GraphQL endpoint
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REST_URL = "https://api.github.com"
REPO = "langchain-ai/langchain"

# 中国识别关键词
CHINA_LOCATION_KEYWORDS = [
    'china', '中国', 'beijing', 'shanghai', 'hangzhou', 'shenzhen', 
    'guangzhou', 'chengdu', 'nanjing', 'wuhan', 'xian', 'suzhou',
    'tianjin', 'chongqing', 'hefei', 'zhengzhou', 'changsha',
    '北京', '上海', '杭州', '深圳', '广州', '成都', '合肥'
]

CHINA_COMPANY_KEYWORDS = [
    'alibaba', 'bytedance', 'tencent', 'baidu', 'meituan', 'xiaomi',
    'huawei', 'jd', 'didi', 'pinduoduo', 'netease', 'kuaishou',
    'bilibili', 'zilliz', 'pingcap', 'milvus', 'tidb',
    '阿里', '腾讯', '百度', '字节', '美团', '小米', '华为', '京东'
]


class GitHubAuthenticatedScraper:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'LangChain-Contributor-Scraper'
        }
        self.rest_headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'LangChain-Contributor-Scraper'
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
                    print(f"❌ GraphQL errors: {data['errors']}")
                    return None
                return data.get('data')
            else:
                print(f"❌ GraphQL request failed: {resp.status_code}")
                return None
        except Exception as e:
            print(f"❌ GraphQL request error: {e}")
            return None
    
    def get_user_details(self, username: str) -> Optional[Dict]:
        """使用 GraphQL 获取用户详细信息（包括邮箱）"""
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
    
    def get_contributors(self, min_contributions: int = 10) -> List[Dict]:
        """获取贡献者列表 (REST API)"""
        contributors = []
        page = 1
        
        print("📥 获取贡献者列表...")
        
        while True:
            url = f"{GITHUB_REST_URL}/repos/{REPO}/contributors?per_page=100&page={page}"
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
                
                print(f"  📄 第 {page} 页: {len(data)} 人, 保留 {len(filtered)} 人")
                
                if len(data) < 100:
                    break
                
                page += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print(f"✅ 共获取 {len(contributors)} 个贡献者 (贡献>={min_contributions})")
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
    
    def scrape_chinese_contributors(self, min_contributions: int = 10) -> List[Dict]:
        """完整流程：获取贡献者 -> 筛选中国用户 -> 获取详细信息"""
        
        # 获取贡献者列表
        contributors = self.get_contributors(min_contributions)
        
        chinese_users = []
        total = len(contributors)
        
        print(f"\n🔍 分析 {total} 个贡献者...")
        
        for i, c in enumerate(contributors, 1):
            username = c['login']
            contributions = c['contributions']
            
            # 获取详细信息
            user = self.get_user_details(username)
            if not user:
                continue
            
            is_china, reason = self.is_chinese_user(user)
            
            if is_china:
                # 提取社交账号
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
                print(f"  ✅ [{i}/{total}] {username:20} | {contributions:4}次 | {email_status}")
            else:
                if i % 20 == 0:
                    print(f"  ⏳ [{i}/{total}] 已处理...")
            
            time.sleep(0.2)  # 避免限流
        
        return chinese_users


def main():
    print("=" * 60)
    print("🦜 LangChain 中国贡献者挖掘工具 (认证版)")
    print("   使用 GitHub Token 获取完整联系方式")
    print("=" * 60)
    
    # 检查 Token
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("\n❌ 未设置 GITHUB_TOKEN 环境变量！")
        print("\n📝 设置方法:")
        print("   1. 访问 https://github.com/settings/tokens")
        print("   2. 点击 'Generate new token (classic)'")
        print("   3. 勾选 'read:user' 和 'user:email' 权限")
        print("   4. 运行: export GITHUB_TOKEN='ghp_xxxxxx'")
        print("   5. 重新运行此脚本")
        return
    
    print(f"✅ 已检测到 GitHub Token (长度: {len(token)})")
    
    # 创建 scraper
    scraper = GitHubAuthenticatedScraper(token)
    
    # 执行抓取
    chinese_users = scraper.scrape_chinese_contributors(min_contributions=10)
    
    if not chinese_users:
        print("⚠️ 未发现中国贡献者")
        return
    
    # 按贡献数排序
    chinese_users.sort(key=lambda x: x['contributions'], reverse=True)
    
    # 保存结果
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV
    csv_file = os.path.join(output_dir, f"langchain_chinese_auth_{timestamp}.csv")
    fieldnames = ['login', 'name', 'contributions', 'email', 'location', 
                  'company', 'blog', 'twitter', 'linkedin', 'github_url', 
                  'followers', 'reason']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in chinese_users:
            row = {k: c.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    print(f"\n💾 CSV 已保存: {csv_file}")
    
    # JSON
    json_file = os.path.join(output_dir, f"langchain_chinese_auth_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(chinese_users, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON 已保存: {json_file}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 结果摘要")
    print("=" * 60)
    
    with_email = [u for u in chinese_users if u.get('email')]
    print(f"发现中国贡献者: {len(chinese_users)}")
    print(f"成功获取邮箱: {len(with_email)}/{len(chinese_users)} ({len(with_email)/len(chinese_users)*100:.0f}%)")
    
    print("\n🏆 中国贡献者列表:")
    print("-" * 100)
    print(f"{'#':3} | {'GitHub':20} | {'贡献':5} | {'邮箱':30} | {'公司/位置'}")
    print("-" * 100)
    for i, u in enumerate(chinese_users, 1):
        email = u.get('email', '')[:30] or '(无)'
        loc = u.get('company') or u.get('location') or ''
        print(f"{i:3} | {u['login']:20} | {u['contributions']:5} | {email:30} | {loc[:25]}")
    
    print("\n✅ 任务完成!")


if __name__ == "__main__":
    main()
