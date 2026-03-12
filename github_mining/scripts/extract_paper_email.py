#!/usr/bin/env python3
"""
学术联系方式提取工具 (Academic Contact Extractor)

- 从个人主页提取强混淆的 Email (例如: first . last at domain dot edu)
- 提取 GitHub URL (排除无关注册链接)
- 提取 Twitter/LinkedIn/Google Scholar 链接
- [后续扩展] 从 PDF 中提取通讯邮箱
"""

import re
import urllib.parse
from typing import Dict, List, Set

from bs4 import BeautifulSoup


def extract_academic_contacts(html: str, base_url: str = "") -> Dict[str, any]:
    """提取增强版的学术联系方式"""
    result = {
        "emails": [],
        "github": None,
        "linkedin": None,
        "twitter": None,
        "scholar": None,
        "homepage": base_url
    }
    
    if not html:
        return result

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    # 1. ==== Twitter / LinkedIn / Scholar ====
    all_links = [a.get('href', '') for a in soup.find_all('a', href=True)]
    
    linkedin = [l for l in all_links if 'linkedin.com/in/' in l]
    if linkedin: result['linkedin'] = linkedin[0]
        
    twitter = [l for l in all_links if 'twitter.com/' in l or 'x.com/' in l]
    if twitter: result['twitter'] = twitter[0]
        
    scholar = [l for l in all_links if 'scholar.google' in l]
    if scholar: result['scholar'] = scholar[0]

    # 2. ==== GitHub 提取 ====
    # 策略 1: 直接找 a 标签里的链接
    github_links = [l for l in all_links if 'github.com/' in l]
    for link in github_links:
        parsed = urllib.parse.urlparse(link)
        path_parts = [p for p in parsed.path.split('/') if p]
        if path_parts:
            username = path_parts[0]
            # 排除非用户链接
            if username.lower() not in ('orgs', 'topics', 'collections', 'sponsors', 'about', 'pricing', 'features', 'login', 'join'):
                result['github'] = f"https://github.com/{username}"
                break
    
    # 3. ==== Email 提取 (学术圈重度混淆) ====
    emails: Set[str] = set()
    
    # 3.1 mailto: 链接 (最准确)
    mailto_links = [urllib.parse.unquote(a['href'].replace('mailto:', '').strip()) 
                   for a in soup.find_all('a', href=True) if 'mailto:' in a['href']]
    emails.update(mailto_links)
    
    # 3.2 标准正则匹配纯文本
    standard_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails.update(re.findall(standard_pattern, text))
    
    # 3.3 混淆替换: [at], (at), {at}, at, [dot], (dot), dot
    obfuscated_pattern = r'([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|{at}|\s+at\s+)\s*([A-Za-z0-9.-]+)\s*(?:\[dot\]|\(dot\)|{dot}|\s+dot\s+)\s*([A-Za-z]{2,})'
    for match in re.finditer(obfuscated_pattern, text, re.IGNORECASE):
        user, domain, tld = match.groups()
        emails.add(f"{user.strip()}@{domain.strip()}.{tld.strip()}".lower())
        
    # 3.4 域名后置暗示: Email: first.last (at) domain.edu
    # TODO: 更复杂的NLP匹配，但先用正则
    at_dot_pattern = r'([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\s+at\s+)\s*([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
    for match in re.finditer(at_dot_pattern, text, re.IGNORECASE):
        user, domain = match.groups()
        emails.add(f"{user.strip()}@{domain.strip()}".lower())

    # 过滤无效邮箱
    clean_emails = []
    for e in emails:
        e = e.strip().lower()
        if 'noreply' in e or 'example.com' in e or 'domain.com' in e:
            continue
        # 简单校验
        if re.match(r'^[^@]+@[^@]+\.[^@]+$', e):
            clean_emails.append(e)
            
    result['emails'] = list(set(clean_emails))
    return result

if __name__ == "__main__":
    # Test cases
    test_html = """
    <html>
        <body>
            <a href="https://github.com/AndrewNg">My Github</a>
            <a href="https://twitter.com/AndrewYNg">Twitter</a>
            <p>Contact me at andrew.ng [at] stanford [dot] edu</p>
            <p>Or personal email: andrew(at)gmail.com</p>
        </body>
    </html>
    """
    res = extract_academic_contacts(test_html, "http://andrewng.org")
    import json
    print(json.dumps(res, indent=2))
