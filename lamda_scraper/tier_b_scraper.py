#!/usr/bin/env python3
"""
LAMDA Tier B候选人深度采集工具
专门针对高优先级候选人提取:
1. 当前公司和职位
2. 完整工作经历
3. 多种联系方式（公司邮箱、个人邮箱、LinkedIn、Twitter等）
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import csv
import time
from datetime import datetime
from typing import Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 知名公司列表（用于识别）
KNOWN_COMPANIES = [
    # 大厂
    'ByteDance', '字节跳动', '抖音', 'TikTok',
    'Alibaba', '阿里巴巴', '阿里', 'Taobao', '淘宝', 'DAMO', '达摩院', 'Qwen', '通义',
    'Tencent', '腾讯', 'WeChat',
    'Huawei', '华为',
    'Baidu', '百度',
    'Meituan', '美团',
    'JD', '京东',
    'Xiaomi', '小米',
    'NetEase', '网易',
    # 外企
    'Google', 'Microsoft', '微软', 'Meta', 'Facebook', 'Amazon', 'Apple', 'NVIDIA',
    'OpenAI', 'DeepMind', 'Anthropic',
    # AI公司
    'SenseTime', '商汤',
    'Megvii', '旷视',
    'Zhipu', '智谱', 'GLM',
    'Moonshot', '月之暗面',
    'Baichuan', '百川',
    'MiniMax',
    '零一万物', '01.AI',
    # 高校
    'University', 'Institute', '大学', '研究院', '研究所',
    'Professor', 'Researcher', '教授', '研究员', '讲师',
]


def fetch_page(url: str, session: requests.Session, delay: float = 1.0, verify_ssl: bool = True) -> Optional[BeautifulSoup]:
    """获取并解析网页，处理重定向，支持 SSL 容错"""
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        logger.info(f"Fetching: {url}")
        # 首次尝试使用 SSL 验证
        try:
            response = session.get(url, timeout=30, allow_redirects=True, verify=verify_ssl)
        except requests.exceptions.SSLError:
            logger.warning(f"SSL error for {url}, retrying without SSL verification")
            response = session.get(url, timeout=30, allow_redirects=True, verify=False)
        
        response.raise_for_status()
        response.encoding = 'utf-8'
        time.sleep(delay)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 检查 meta refresh 重定向
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            match = re.search(r'url=(.+)', content, re.I)
            if match:
                new_url = match.group(1).strip()
                # 处理相对 URL
                if not new_url.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    new_url = urljoin(url, new_url)
                logger.info(f"Following redirect to: {new_url}")
                try:
                    response = session.get(new_url, timeout=30, verify=verify_ssl)
                except requests.exceptions.SSLError:
                    response = session.get(new_url, timeout=30, verify=False)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                time.sleep(delay)
        
        return soup
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def extract_work_experience(soup: BeautifulSoup, text_content: str) -> Dict:
    """增强版工作经历提取 - V2"""
    result = {
        'current_company': None,
        'current_position': None,
        'current_location': None,
        'work_start_date': None,
        'work_history': [],
        'is_academic': False,
    }
    
    # 更多工作模式匹配
    work_patterns = [
        # 标准格式: 时间 - present/now, 职位, 公司, 地点
        r'(\d{4})[.\-/年]?\s*(\d{1,2})?[月]?\s*[-–—~至]+\s*(?:present|now|现在|至今)[,，]?\s*([^,，\n]+?)[,，]\s*\[?([^\],\n]+?)\]?(?:[,，]\s*([^\n]+?))?(?:\n|$)',
        # 格式: 职位 at/@ 公司 (时间)
        r'(?:I am|Currently|现在|目前)[^.。]*?(?:at|@|在|working\s+at|work\s+at)\s*\[?([^\],]+?)\]?[^.。]*?(?:since|from|自)?\s*(\d{4})',
        # 格式: Researcher/Engineer at Company
        r'(Researcher|Engineer|Scientist|研究员|工程师|算法|Developer|专家)[^.。]*?(?:at|@|在)\s*\[?([^\],]+?)\]?(?:\s*Team)?',
        # 格式: I joined [Company] in [Year]
        r'(?:I\s+)?(?:joined|join)\s+\[?([^\]]+?)\]?\s+(?:in|since)\s+(\d{4})',
        # 格式: Currently working at [Company]
        r'(?:Currently|Now|Presently)\s+(?:working|employed|at)\s+(?:at|with)?\s*\[?([^\],\.]+?)\]?',
        # 格式: [Position] @ [Company] (Year - Present)
        r'([A-Za-z\s]+)\s*[@|at]\s*([^\(\)\n]+?)\s*\(?\s*(\d{4})\s*[-–—]\s*(?:present|now|至今)',
        # 格式: Joined Alibaba DAMO Academy
        r'(?:joined|join|working\s+at|work\s+at)\s+([A-Za-z\u4e00-\u9fff]+(?:\s+[A-Za-z\u4e00-\u9fff]+){0,3})',
    ]
    
    for pattern in work_patterns:
        match = re.search(pattern, text_content, re.I)
        if match:
            groups = match.groups()
            if len(groups) >= 4:  # 标准格式
                result['work_start_date'] = f"{groups[0]}.{groups[1] or '01'}"
                result['current_position'] = groups[2].strip() if groups[2] else None
                result['current_company'] = groups[3].strip() if groups[3] else None
                result['current_location'] = groups[4].strip() if len(groups) > 4 and groups[4] else None
            elif len(groups) >= 2:
                # 判断哪个是公司
                for g in groups:
                    if g:
                        g = g.strip()
                        for known in KNOWN_COMPANIES:
                            if known.lower() in g.lower():
                                result['current_company'] = g
                                break
                        if result['current_company']:
                            break
            elif len(groups) == 1 and groups[0]:
                result['current_company'] = groups[0].strip()
            if result['current_company']:
                break
    
    # 从 HTML 结构提取（查找 strong/b 标签中的公司名）
    if not result['current_company']:
        for tag in soup.find_all(['strong', 'b', 'em']):
            text = tag.get_text(strip=True)
            for company in KNOWN_COMPANIES:
                if company.lower() in text.lower():
                    result['current_company'] = text[:100]
                    break
            if result['current_company']:
                break
    
    # 模式: 从"Work Experience"部分提取
    work_section_patterns = [
        r'(?:Work|Working|Professional)\s*Experience[s]?[:\s]+(.+?)(?=Education|Publication|Honor|Award|Research|Selected|\Z)',
        r'(?:工作经历|工作经验|职业经历)[:\s：]+(.+?)(?=教育|发表|荣誉|研究|\Z)',
        r'(?:Experience|Employment)[:\s]+(.+?)(?=Education|Publication|Project|\Z)',
    ]
    
    for pattern in work_section_patterns:
        match = re.search(pattern, text_content, re.I | re.DOTALL)
        if match:
            work_text = match.group(1)
            entries = re.findall(
                r'(\d{4})[.\-/年]\s*(\d{1,2})?[月]?\s*[-–—~至]+\s*(?:(\d{4})[.\-/年]\s*(\d{1,2})?[月]?|present|now|现在|至今)[,，\s]+([^\n]+)',
                work_text, re.I
            )
            for entry in entries:
                start_year, start_month, end_year, end_month, details = entry
                work_entry = {
                    'start': f"{start_year}.{start_month or '01'}",
                    'end': f"{end_year}.{end_month or '01'}" if end_year else 'present',
                    'details': details.strip()[:200]
                }
                result['work_history'].append(work_entry)
                
                if not result['current_company'] and (not end_year or end_year == 'present'):
                    result['work_start_date'] = work_entry['start']
                    for company in KNOWN_COMPANIES:
                        if company.lower() in details.lower():
                            result['current_company'] = company
                            break
            break
    
    # 检测知名公司关键词（带上下文验证）
    if not result['current_company']:
        for company in KNOWN_COMPANIES:
            if company.lower() in text_content.lower():
                context_patterns = [
                    rf'(?:present|now|currently|现在|目前|at\s+)[^.。]*{re.escape(company)}',
                    rf'{re.escape(company)}[^.。]*(?:present|now|currently|现在|目前)',
                    rf'(?:joined|join|work|working)[^.。]*{re.escape(company)}',
                ]
                for ctx_pattern in context_patterns:
                    if re.search(ctx_pattern, text_content, re.I):
                        result['current_company'] = company
                        break
                if result['current_company']:
                    break
    
    # 检测是否在学术界
    academic_keywords = ['Professor', 'Researcher', 'University', 'Institute', 'Faculty', 'Lecturer',
                         '教授', '研究员', '大学', '研究院', '副教授', '讲师', 'Ph.D. candidate']
    if result['current_company']:
        for kw in academic_keywords:
            if kw.lower() in result['current_company'].lower():
                result['is_academic'] = True
                break
    
    # 如果主页文本提到学术职位，也标记为学术界
    if not result['is_academic']:
        academic_position_pattern = r'(?:I am|Currently)\s+(?:a\s+)?(?:Professor|Researcher|Ph\.?D\.?\s*(?:student|candidate)|博士|研究员|教授)'
        if re.search(academic_position_pattern, text_content, re.I):
            result['is_academic'] = True
    
    return result


def extract_contacts(soup: BeautifulSoup, text_content: str) -> Dict:
    """增强版联系方式提取 - V2"""
    result = {
        'emails': [],
        'email_company': None,
        'email_personal': None,
        'email_academic': None,
        'linkedin': None,
        'twitter': None,
        'github': None,
        'google_scholar': None,
        'zhihu': None,
        'weibo': None,
        'researchgate': None,
        'orcid': None,
    }
    
    # 从 mailto: 链接提取邮箱
    mailto_emails = []
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0].strip()
            if '@' in email:
                mailto_emails.append(email)
    
    # 从文本提取邮箱
    email_pattern = r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}'
    text_emails = re.findall(email_pattern, text_content)
    
    # 合并去重
    all_emails = list(set(mailto_emails + text_emails))
    # 过滤无效邮箱
    all_emails = [e for e in all_emails if not e.endswith('.png') and not e.endswith('.jpg') and len(e) < 100]
    result['emails'] = all_emails
    
    # 扩展的域名分类
    company_domains = [
        'alibaba-inc.com', 'bytedance.com', 'tencent.com', 'huawei.com', 
        'baidu.com', 'meituan.com', 'jd.com', 'xiaomi.com', 'netease.com',
        'microsoft.com', 'google.com', 'meta.com', 'apple.com', 'nvidia.com',
        'sensetime.com', 'megvii.com', 'amazon.com', 'openai.com', 'anthropic.com',
        'deepmind.com', 'zhipuai.cn', 'moonshot.cn', 'baichuan-ai.com', 'minimax.chat'
    ]
    personal_domains = [
        'gmail.com', 'outlook.com', 'hotmail.com', 'qq.com', '163.com', 'foxmail.com', 
        'yahoo.com', 'icloud.com', 'proton.me', 'protonmail.com', 'me.com', 'live.com',
        'sina.com', 'sohu.com', '126.com', 'yeah.net'
    ]
    academic_domains = [
        'edu.cn', 'edu.hk', 'edu.sg', 'edu.au', 'edu.uk', 'ac.uk', 'ac.jp',
        'edu', 'ac.cn', 'nju.edu.cn', 'tsinghua.edu.cn', 'pku.edu.cn', 'zju.edu.cn', 
        'ustc.edu.cn', 'fudan.edu.cn', 'sjtu.edu.cn', 'hit.edu.cn', 'buaa.edu.cn',
        'riken.jp', 'mila.quebec', 'berkeley.edu', 'stanford.edu', 'mit.edu', 'cmu.edu',
        'ethz.ch', 'epfl.ch', 'ox.ac.uk', 'cam.ac.uk', 'u-tokyo.ac.jp'
    ]
    
    for email in all_emails:
        email_lower = email.lower()
        # 公司邮箱
        if not result['email_company']:
            for domain in company_domains:
                if domain in email_lower:
                    result['email_company'] = email
                    break
        # 个人邮箱
        if not result['email_personal']:
            for domain in personal_domains:
                if domain in email_lower:
                    result['email_personal'] = email
                    break
        # 学校邮箱
        if not result['email_academic']:
            for domain in academic_domains:
                if domain in email_lower:
                    result['email_academic'] = email
                    break
    
    # 从 <a> 标签提取社交链接
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        href_lower = href.lower()
        
        if 'linkedin.com' in href_lower and not result['linkedin']:
            result['linkedin'] = href
        elif ('twitter.com' in href_lower or 'x.com' in href_lower) and not result['twitter']:
            result['twitter'] = href
        elif 'github.com' in href_lower and 'github.io' not in href_lower and not result['github']:
            result['github'] = href
        elif 'scholar.google' in href_lower and not result['google_scholar']:
            result['google_scholar'] = href
        elif 'zhihu.com' in href_lower and not result['zhihu']:
            result['zhihu'] = href
        elif 'weibo.com' in href_lower and not result['weibo']:
            result['weibo'] = href
        elif 'researchgate.net' in href_lower and not result['researchgate']:
            result['researchgate'] = href
        elif 'orcid.org' in href_lower and not result['orcid']:
            result['orcid'] = href
    
    # 从文本中正则提取社交链接（处理非 <a> 标签的情况）
    social_patterns = {
        'linkedin': r'https?://(?:www\.)?linkedin\.com/in/[\w-]+/?',
        'twitter': r'https?://(?:www\.)?(?:twitter|x)\.com/[\w-]+/?',
        'github': r'https?://(?:www\.)?github\.com/[\w-]+/?(?![\w-]*\.io)',
        'google_scholar': r'https?://scholar\.google\.com/citations\?[^\s"<>]+',
        'zhihu': r'https?://(?:www\.)?zhihu\.com/people/[\w-]+/?',
    }
    
    for key, pattern in social_patterns.items():
        if not result[key]:
            match = re.search(pattern, text_content, re.I)
            if match:
                result[key] = match.group(0)
    
    return result


def process_tier_b_candidates(input_json: str, output_csv: str):
    """处理Tier B候选人，深度采集"""
    
    # 读取分析结果，筛选Tier B
    with open(input_json, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    
    # 读取分析结果获取Tier B名单
    tier_b_names = set()
    try:
        with open('lamda_analysis.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Tier') == 'B':
                    tier_b_names.add(row.get('姓名'))
    except:
        logger.warning("No analysis file found, processing all candidates with publications")
        # 如果没有分析文件，选择有论文的
        tier_b_names = {c['name_cn'] for c in candidates if c.get('top_venues')}
    
    logger.info(f"Found {len(tier_b_names)} Tier B candidates to process")
    
    # 筛选需要处理的候选人
    tier_b_candidates = [c for c in candidates if c['name_cn'] in tier_b_names]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    results = []
    
    for i, candidate in enumerate(tier_b_candidates, 1):
        name = candidate['name_cn']
        url = candidate.get('homepage_url')
        
        logger.info(f"[{i}/{len(tier_b_candidates)}] Deep processing: {name}")
        
        row = {
            '姓名': name,
            '英文名': candidate.get('name_en', ''),
            '主页': url,
            '导师': candidate.get('supervisor', ''),
            '顶会顶刊': '; '.join(candidate.get('top_venues', [])) if isinstance(candidate.get('top_venues'), list) else candidate.get('top_venues', ''),
            '当前公司': '',
            '当前职位': '',
            '工作地点': '',
            '入职时间': '',
            '是否学术界': '',
            '工作经历': '',
            '公司邮箱': '',
            '个人邮箱': '',
            '学校邮箱': candidate.get('email', ''),
            'LinkedIn': candidate.get('linkedin', ''),
            'Twitter': '',
            'GitHub': candidate.get('github', ''),
            'Scholar': candidate.get('google_scholar', ''),
            '知乎': '',
            '采集时间': datetime.now().isoformat(),
        }
        
        if url:
            soup = fetch_page(url, session)
            if soup:
                text_content = soup.get_text(separator='\n', strip=True)
                
                # 提取工作经历
                work_info = extract_work_experience(soup, text_content)
                row['当前公司'] = work_info.get('current_company', '')
                row['当前职位'] = work_info.get('current_position', '')
                row['工作地点'] = work_info.get('current_location', '')
                row['入职时间'] = work_info.get('work_start_date', '')
                row['是否学术界'] = '是' if work_info.get('is_academic') else '否'
                row['工作经历'] = json.dumps(work_info.get('work_history', []), ensure_ascii=False)
                
                # 提取联系方式
                contact_info = extract_contacts(soup, text_content)
                row['公司邮箱'] = contact_info.get('email_company', '')
                row['个人邮箱'] = contact_info.get('email_personal', '')
                if contact_info.get('email_academic'):
                    row['学校邮箱'] = contact_info.get('email_academic', '')
                if contact_info.get('linkedin'):
                    row['LinkedIn'] = contact_info.get('linkedin', '')
                row['Twitter'] = contact_info.get('twitter', '')
                if contact_info.get('github'):
                    row['GitHub'] = contact_info.get('github', '')
                if contact_info.get('google_scholar'):
                    row['Scholar'] = contact_info.get('google_scholar', '')
                row['知乎'] = contact_info.get('zhihu', '')
        
        results.append(row)
    
    # 导出CSV
    if results:
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Exported {len(results)} enhanced profiles to {output_csv}")
    
    # 统计
    stats = {
        'total': len(results),
        'with_company': sum(1 for r in results if r['当前公司']),
        'with_company_email': sum(1 for r in results if r['公司邮箱']),
        'with_personal_email': sum(1 for r in results if r['个人邮箱']),
        'with_linkedin': sum(1 for r in results if r['LinkedIn']),
        'in_academia': sum(1 for r in results if r['是否学术界'] == '是'),
    }
    
    print("\n===== Enhanced Extraction Stats =====")
    print(f"Total Tier B candidates: {stats['total']}")
    print(f"With current company: {stats['with_company']}")
    print(f"With company email: {stats['with_company_email']}")
    print(f"With personal email: {stats['with_personal_email']}")
    print(f"With LinkedIn: {stats['with_linkedin']}")
    print(f"In academia: {stats['in_academia']}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced LAMDA Tier B Scraper')
    parser.add_argument('--input', type=str, default='lamda_candidates_full.json', help='Input JSON file')
    parser.add_argument('--output', type=str, default='tier_b_enhanced.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    process_tier_b_candidates(args.input, args.output)


if __name__ == '__main__':
    main()
