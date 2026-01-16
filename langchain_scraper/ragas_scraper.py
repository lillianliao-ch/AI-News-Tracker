#!/usr/bin/env python3
"""
GitHub Contributors Analyzer for vibrantlabsai/ragas
Identifies Chinese contributors and exports to CSV/JSON
"""

import requests
import time
import csv
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'
GITHUB_REST_URL = 'https://api.github.com'
REPO = 'vibrantlabsai/ragas'

CHINA_LOCATION_KEYWORDS = [
    'china', '中国', 'beijing', 'shanghai', 'hangzhou', 'shenzhen', 
    'guangzhou', 'chengdu', 'nanjing', 'wuhan', 'xian', 'suzhou',
    'tianjin', 'chongqing', 'hefei', 'zhengzhou', 'changsha',
    '北京', '上海', '杭州', '深圳', '广州', '成都', '合肥', 'taiwan', '台湾', 'hongkong', 'hong kong', '香港'
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
            'User-Agent': 'GitHub-Contributor-Scraper'
        }
        self.rest_headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Contributor-Scraper'
        }
    
    def graphql_query(self, query: str, variables: Dict = None) -> Optional[Dict]:
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        try:
            resp = requests.post(GITHUB_GRAPHQL_URL, headers=self.headers, 
                               json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if 'errors' in data:
                    print(f'GraphQL errors: {data["errors"]}')
                    return None
                return data.get('data')
            else:
                print(f'GraphQL request failed: {resp.status_code}')
                return None
        except Exception as e:
            print(f'GraphQL request error: {e}')
            return None
    
    def get_user_details(self, username: str) -> Optional[Dict]:
        query = '''
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
        '''
        
        result = self.graphql_query(query, {'login': username})
        if result and result.get('user'):
            return result['user']
        return None
    
    def get_contributors(self, min_contributions: int = 1) -> List[Dict]:
        contributors = []
        page = 1
        
        print(f'📥 Getting contributors for {REPO}...')
        
        while True:
            url = f'{GITHUB_REST_URL}/repos/{REPO}/contributors?per_page=100&page={page}'
            try:
                resp = requests.get(url, headers=self.rest_headers, timeout=30)
                if resp.status_code != 200:
                    print(f'❌ REST API failed: {resp.status_code}')
                    break
                
                data = resp.json()
                if not data:
                    break
                
                filtered = [c for c in data if c.get('contributions', 0) >= min_contributions]
                contributors.extend(filtered)
                
                print(f'  📄 Page {page}: {len(data)} contributors, keeping {len(filtered)}')
                
                if len(data) < 100:
                    break
                
                page += 1
                time.sleep(0.3)
            except Exception as e:
                print(f'❌ Error: {e}')
                break
        
        print(f'✅ Total: {len(contributors)} contributors (contributions >= {min_contributions})')
        return contributors
    
    def is_chinese_user(self, user: Dict) -> Tuple[bool, str]:
        location = (user.get('location') or '').lower()
        company = (user.get('company') or '').lower()
        name = user.get('name') or ''
        bio = user.get('bio') or ''
        
        reasons = []
        
        for kw in CHINA_LOCATION_KEYWORDS:
            if kw.lower() in location:
                reasons.append(f'Location: {user.get("location")}')
                break
        
        for kw in CHINA_COMPANY_KEYWORDS:
            if kw.lower() in company:
                reasons.append(f'Company: {user.get("company")}')
                break
        
        if re.search(r'[\u4e00-\u9fff]', name):
            reasons.append(f'Name: {name}')
        
        if re.search(r'[\u4e00-\u9fff]', bio or ''):
            reasons.append('Bio has Chinese')
        
        return len(reasons) > 0, '; '.join(reasons)
    
    def scrape_chinese_contributors(self, min_contributions: int = 1) -> List[Dict]:
        contributors = self.get_contributors(min_contributions)
        
        chinese_users = []
        total = len(contributors)
        
        print(f'\n🔍 Analyzing {total} contributors...')
        
        for i, c in enumerate(contributors, 1):
            username = c['login']
            contributions = c['contributions']
            
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
                    'github_url': f'https://github.com/{username}',
                    'followers': user.get('followers', {}).get('totalCount', 0),
                    'reason': reason
                }
                chinese_users.append(info)
                
                email_status = f'📧 {info["email"]}' if info['email'] else '无邮箱'
                print(f'  ✅ [{i}/{total}] {username:20} | {contributions:4} commits | {email_status}')
            else:
                if i % 20 == 0:
                    print(f'  ⏳ Progress [{i}/{total}]...')
            
            time.sleep(0.2)
        
        return chinese_users


def main():
    print('=' * 60)
    print(f'🔍 GitHub Chinese Contributors Analyzer')
    print(f'📦 Repository: {REPO}')
    print('=' * 60)
    
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('❌ ERROR: GITHUB_TOKEN not set!')
        print('\n📝 设置方法:')
        print('   1. 访问 https://github.com/settings/tokens')
        print("   2. 点击 'Generate new token (classic)'")
        print("   3. 勾选 'read:user' 和 'user:email' 权限")
        print("   4. 运行: export GITHUB_TOKEN='ghp_xxxxxx'")
        return
    
    print(f'✅ GitHub Token detected (length: {len(token)})')
    
    scraper = GitHubAuthenticatedScraper(token)
    chinese_users = scraper.scrape_chinese_contributors(min_contributions=1)
    
    if not chinese_users:
        print('⚠️ No Chinese contributors found')
        return
    
    chinese_users.sort(key=lambda x: x['contributions'], reverse=True)
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    repo_slug = REPO.replace('/', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    csv_file = os.path.join(output_dir, f'{repo_slug}_chinese_{timestamp}.csv')
    fieldnames = ['login', 'name', 'contributions', 'email', 'location', 
                  'company', 'blog', 'twitter', 'linkedin', 'github_url', 
                  'followers', 'reason']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in chinese_users:
            row = {k: c.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    print(f'\n💾 CSV saved: {csv_file}')
    
    json_file = os.path.join(output_dir, f'{repo_slug}_chinese_{timestamp}.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(chinese_users, f, ensure_ascii=False, indent=2)
    print(f'💾 JSON saved: {json_file}')
    
    print('\n' + '=' * 60)
    print('📊 Results Summary')
    print('=' * 60)
    
    with_email = [u for u in chinese_users if u.get('email')]
    print(f'🇨🇳 Chinese contributors found: {len(chinese_users)}')
    print(f'📧 With email: {len(with_email)}/{len(chinese_users)} ({len(with_email)/len(chinese_users)*100:.0f}%)')
    
    print('\n🏆 Chinese Contributors List:')
    print('-' * 100)
    print(f'{"#":3} | {"GitHub":20} | {"Commits":7} | {"Email":30} | {"Company/Location"}')
    print('-' * 100)
    for i, u in enumerate(chinese_users, 1):
        email = u.get('email', '')[:30] or '(none)'
        loc = u.get('company') or u.get('location') or ''
        print(f'{i:3} | {u["login"]:20} | {u["contributions"]:7} | {email:30} | {loc[:25]}')
    
    print('\n✅ Task completed!')


if __name__ == '__main__':
    main()
