#!/usr/bin/env python3
"""
LAMDA Lab 人才数据采集工具
采集南京大学LAMDA实验室的校友和博士生信息

数据来源:
- 校友: https://www.lamda.nju.edu.cn/CH.previous_people_alumni.ashx
- 博士生: https://www.lamda.nju.edu.cn/CH.PhD_student.ashx
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import csv
import time
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from urllib.parse import urljoin
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 请求配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

BASE_URL = "https://www.lamda.nju.edu.cn"

# 数据URLs
URLS = {
    'alumni': f"{BASE_URL}/CH.previous_people_alumni.ashx",
    'phd': f"{BASE_URL}/CH.PhD_student.ashx",
    'msc': f"{BASE_URL}/CH.MSc_students.ashx",
    'faculty': f"{BASE_URL}/CH.People.ashx",
}


@dataclass
class Candidate:
    """候选人数据结构"""
    # 基础信息
    name_cn: str
    name_en: Optional[str] = None
    source_type: str = "alumni"  # alumni, phd, msc
    homepage_url: Optional[str] = None
    
    # 研究方向
    research_interests: List[str] = field(default_factory=list)
    
    # 导师信息
    supervisor: Optional[str] = None
    supervisor_url: Optional[str] = None
    
    # 教育经历
    phd_school: Optional[str] = None
    phd_year_start: Optional[int] = None
    phd_year_end: Optional[int] = None
    bachelor_school: Optional[str] = None
    overseas_experience: List[str] = field(default_factory=list)
    
    # 工作经历
    current_position: Optional[str] = None
    current_company: Optional[str] = None
    work_start_date: Optional[str] = None
    work_history: List[str] = field(default_factory=list)
    
    # 学术成果
    publications: List[str] = field(default_factory=list)
    top_venues: List[str] = field(default_factory=list)  # ICML, NeurIPS, CVPR等
    citation_count: Optional[int] = None
    
    # 荣誉
    honors: List[str] = field(default_factory=list)
    
    # 联系方式
    email: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    google_scholar: Optional[str] = None
    
    # 元数据
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    data_quality: str = "partial"  # full, partial, minimal


class LAMDAScraper:
    """LAMDA实验室数据采集器"""
    
    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay  # 请求间隔，避免被封
        self.candidates: List[Candidate] = []
        
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """获取并解析网页"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            time.sleep(self.delay)
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse_list_page(self, url: str, source_type: str) -> List[dict]:
        """解析列表页，提取姓名和主页链接"""
        soup = self.fetch_page(url)
        if not soup:
            return []
        
        people = []
        # 查找所有人员链接
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 过滤条件：链接指向个人主页
            if not text:
                continue
            if any(skip in href.lower() for skip in ['mainpage', 'people.ashx', '#', 'javascript']):
                continue
            if 'lamda.nju.edu.cn' in href or 'github.io' in href or href.startswith('/'):
                # 处理相对链接
                if href.startswith('/'):
                    href = urljoin(BASE_URL, href)
                
                people.append({
                    'name_cn': text,
                    'homepage_url': href,
                    'source_type': source_type
                })
        
        logger.info(f"Found {len(people)} people from {source_type}")
        return people
    
    def parse_personal_homepage(self, url: str) -> dict:
        """解析个人主页，提取详细信息"""
        info = {}
        
        # 处理重定向到GitHub Pages的情况
        soup = self.fetch_page(url)
        if not soup:
            return info
        
        # 检查是否有重定向
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            match = re.search(r'url=(.+)', content, re.I)
            if match:
                new_url = match.group(1).strip()
                logger.info(f"Following redirect to: {new_url}")
                soup = self.fetch_page(new_url)
                if not soup:
                    return info
                info['redirected_url'] = new_url
        
        # 提取文本内容
        text_content = soup.get_text(separator='\n', strip=True)
        
        # 提取英文名
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            # 常见格式: "Wei Jiang" 或 "姓名 - LAMDA"
            if not any(c in title_text for c in ['LAMDA', '南京', '大学']):
                info['name_en'] = title_text.split('-')[0].strip()
        
        # 提取研究方向
        research_section = self._extract_section(text_content, 
            ['Research Interest', 'Research Area', '研究方向', '研究兴趣'])
        if research_section:
            info['research_interests'] = [r.strip() for r in re.split(r'[,，、;；\n]', research_section) if r.strip()]
        
        # 提取工作经历
        work_section = self._extract_section(text_content, 
            ['Working Experience', 'Work Experience', '工作经历', 'Employment'])
        if work_section:
            info['work_history'] = work_section
            # 尝试提取当前职位（第一条或最新的）
            work_match = re.search(r'(\d{4})[.\-年]?\s*(\d{1,2})?[月]?\s*[-–~至now现在]+\s*(?:now|present|现在|至今)?\s*[,，]?\s*(.+?)(?:\.|。|\n|$)', 
                                   work_section, re.I)
            if work_match:
                info['work_start_date'] = f"{work_match.group(1)}.{work_match.group(2) or '01'}"
                position_info = work_match.group(3)
                if position_info:
                    info['current_position_raw'] = position_info.strip()
        
        # 提取教育经历
        edu_section = self._extract_section(text_content,
            ['Education', '教育经历', '教育背景', 'Academic Background'])
        if edu_section:
            # 尝试提取博士信息
            phd_match = re.search(r'(\d{4})[.\-年]?\s*\d*[月]?\s*[-–~至]+\s*(\d{4})[.\-年]?\s*\d*[月]?\s*[,，]?\s*(?:Ph\.?D\.?|博士|Doctor)', edu_section, re.I)
            if phd_match:
                info['phd_year_start'] = int(phd_match.group(1))
                info['phd_year_end'] = int(phd_match.group(2))
            
            # 提取学校
            if '南京大学' in edu_section or 'Nanjing University' in edu_section:
                info['phd_school'] = '南京大学'
        
        # 提取导师信息
        supervisor_patterns = [
            r'[Ss]upervisor[:\s]+(?:Prof(?:essor)?\.?\s*)?([^,\n\(]+)',
            r'导师[:\s：]+([^,\n\(]+)',
            r'Advisor[:\s]+(?:Prof(?:essor)?\.?\s*)?([^,\n\(]+)',
        ]
        for pattern in supervisor_patterns:
            match = re.search(pattern, text_content)
            if match:
                info['supervisor'] = match.group(1).strip()
                break
        
        # 提取论文/发表
        pub_venues = []
        for venue in ['ICML', 'NeurIPS', 'ICLR', 'CVPR', 'ICCV', 'ECCV', 'ACL', 'EMNLP', 'NAACL', 
                      'AAAI', 'IJCAI', 'KDD', 'WWW', 'SIGIR', 'TPAMI', 'JMLR', 'TIP', 'TKDE']:
            count = len(re.findall(rf'\b{venue}\b', text_content, re.I))
            if count > 0:
                pub_venues.append(f"{venue}×{count}")
        if pub_venues:
            info['top_venues'] = pub_venues
        
        # 提取荣誉
        honors_section = self._extract_section(text_content,
            ['Honor', 'Award', '荣誉', '奖励', '获奖'])
        if honors_section:
            # 查找国奖等关键词
            if '国家奖学金' in honors_section or 'National Scholarship' in honors_section:
                info['has_national_scholarship'] = True
        
        # 提取联系方式
        email_match = re.search(r'[\w.+-]+@[\w.-]+\.\w+', text_content)
        if email_match:
            info['email'] = email_match.group(0)
        
        # 提取社交链接
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            if 'linkedin.com' in href:
                info['linkedin'] = link.get('href')
            elif 'github.com' in href and 'github.io' not in href:
                info['github'] = link.get('href')
            elif 'scholar.google' in href:
                info['google_scholar'] = link.get('href')
        
        return info
    
    def _extract_section(self, text: str, headers: List[str]) -> Optional[str]:
        """从文本中提取特定章节内容"""
        for header in headers:
            pattern = rf'{re.escape(header)}[:\s]*(.+?)(?=\n[A-Z]|\n[一-龥]{{2,}}|\n##|\Z)'
            match = re.search(pattern, text, re.I | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]  # 限制长度
        return None
    
    def scrape_all(self, include_phd: bool = True, include_msc: bool = False, 
                   limit: int = None) -> None:
        """执行完整采集"""
        all_people = []
        
        # 采集校友
        logger.info("=== Scraping Alumni ===")
        alumni = self.parse_list_page(URLS['alumni'], 'alumni')
        all_people.extend(alumni)
        
        # 采集博士生
        if include_phd:
            logger.info("=== Scraping PhD Students ===")
            phd = self.parse_list_page(URLS['phd'], 'phd')
            all_people.extend(phd)
        
        # 采集硕士生（可选）
        if include_msc:
            logger.info("=== Scraping MSc Students ===")
            msc = self.parse_list_page(URLS['msc'], 'msc')
            all_people.extend(msc)
        
        # 去重
        seen = set()
        unique_people = []
        for p in all_people:
            key = (p['name_cn'], p['homepage_url'])
            if key not in seen:
                seen.add(key)
                unique_people.append(p)
        
        logger.info(f"Total unique candidates: {len(unique_people)}")
        
        # 限制数量（用于测试）
        if limit:
            unique_people = unique_people[:limit]
            logger.info(f"Limited to {limit} candidates for testing")
        
        # 采集详细信息
        for i, person in enumerate(unique_people, 1):
            logger.info(f"[{i}/{len(unique_people)}] Processing: {person['name_cn']}")
            
            # 创建候选人对象
            candidate = Candidate(
                name_cn=person['name_cn'],
                homepage_url=person['homepage_url'],
                source_type=person['source_type']
            )
            
            # 采集详细信息
            if person['homepage_url']:
                details = self.parse_personal_homepage(person['homepage_url'])
                
                # 更新候选人信息
                if details.get('name_en'):
                    candidate.name_en = details['name_en']
                if details.get('research_interests'):
                    candidate.research_interests = details['research_interests']
                if details.get('supervisor'):
                    candidate.supervisor = details['supervisor']
                if details.get('phd_year_start'):
                    candidate.phd_year_start = details['phd_year_start']
                if details.get('phd_year_end'):
                    candidate.phd_year_end = details['phd_year_end']
                if details.get('phd_school'):
                    candidate.phd_school = details['phd_school']
                if details.get('current_position_raw'):
                    candidate.current_position = details['current_position_raw']
                if details.get('work_start_date'):
                    candidate.work_start_date = details['work_start_date']
                if details.get('top_venues'):
                    candidate.top_venues = details['top_venues']
                if details.get('email'):
                    candidate.email = details['email']
                if details.get('linkedin'):
                    candidate.linkedin = details['linkedin']
                if details.get('github'):
                    candidate.github = details['github']
                if details.get('google_scholar'):
                    candidate.google_scholar = details['google_scholar']
                
                # 标记数据质量
                quality_score = sum([
                    bool(candidate.research_interests),
                    bool(candidate.supervisor),
                    bool(candidate.phd_year_end),
                    bool(candidate.current_position),
                    bool(candidate.email),
                    bool(candidate.top_venues),
                ])
                if quality_score >= 4:
                    candidate.data_quality = 'full'
                elif quality_score >= 2:
                    candidate.data_quality = 'partial'
                else:
                    candidate.data_quality = 'minimal'
            
            self.candidates.append(candidate)
        
        logger.info(f"Completed scraping {len(self.candidates)} candidates")
    
    def export_csv(self, filepath: str) -> None:
        """导出为CSV文件"""
        if not self.candidates:
            logger.warning("No candidates to export")
            return
        
        # 准备扁平化数据
        rows = []
        for c in self.candidates:
            row = {
                '姓名': c.name_cn,
                '英文名': c.name_en or '',
                '类型': c.source_type,
                '主页': c.homepage_url or '',
                '研究方向': '; '.join(c.research_interests) if c.research_interests else '',
                '导师': c.supervisor or '',
                '博士毕业年份': c.phd_year_end or '',
                '博士学校': c.phd_school or '',
                '当前职位': c.current_position or '',
                '入职时间': c.work_start_date or '',
                '顶会顶刊': '; '.join(c.top_venues) if c.top_venues else '',
                'Email': c.email or '',
                'LinkedIn': c.linkedin or '',
                'GitHub': c.github or '',
                'Scholar': c.google_scholar or '',
                '数据质量': c.data_quality,
                '采集时间': c.scraped_at,
            }
            rows.append(row)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"Exported {len(rows)} candidates to {filepath}")
    
    def export_json(self, filepath: str) -> None:
        """导出为JSON文件"""
        data = [asdict(c) for c in self.candidates]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Exported {len(data)} candidates to {filepath}")
    
    def get_statistics(self) -> dict:
        """获取采集统计"""
        if not self.candidates:
            return {}
        
        stats = {
            'total': len(self.candidates),
            'by_type': {},
            'by_quality': {},
            'with_email': 0,
            'with_publications': 0,
            'with_current_job': 0,
        }
        
        for c in self.candidates:
            # 按类型统计
            stats['by_type'][c.source_type] = stats['by_type'].get(c.source_type, 0) + 1
            # 按质量统计
            stats['by_quality'][c.data_quality] = stats['by_quality'].get(c.data_quality, 0) + 1
            # 联系方式
            if c.email:
                stats['with_email'] += 1
            # 发表
            if c.top_venues:
                stats['with_publications'] += 1
            # 当前工作
            if c.current_position:
                stats['with_current_job'] += 1
        
        return stats


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LAMDA Lab Talent Scraper')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of candidates (for testing)')
    parser.add_argument('--include-msc', action='store_true', help='Include MSc students')
    parser.add_argument('--output', type=str, default='lamda_candidates', help='Output filename (without extension)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    # 创建采集器
    scraper = LAMDAScraper(delay=args.delay)
    
    # 执行采集
    scraper.scrape_all(
        include_phd=True,
        include_msc=args.include_msc,
        limit=args.limit
    )
    
    # 导出结果
    scraper.export_csv(f"{args.output}.csv")
    scraper.export_json(f"{args.output}.json")
    
    # 打印统计
    stats = scraper.get_statistics()
    print("\n===== Scraping Statistics =====")
    print(f"Total candidates: {stats.get('total', 0)}")
    print(f"By type: {stats.get('by_type', {})}")
    print(f"By quality: {stats.get('by_quality', {})}")
    print(f"With email: {stats.get('with_email', 0)}")
    print(f"With publications: {stats.get('with_publications', 0)}")
    print(f"With current job: {stats.get('with_current_job', 0)}")


if __name__ == '__main__':
    main()
