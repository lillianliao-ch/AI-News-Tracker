#!/usr/bin/env python3
"""
LAMDA 学生深度信息提取器
从学生主页提取完整的学术、社交和联系信息
"""

import requests
import re
import time
import json
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from redirect_utils import RedirectFollower
from decode_cloudflare import decode_cloudflare_email


class DeepStudentScraper:
    """LAMDA 学生深度信息提取器"""

    def __init__(self, delay: float = 1.0):
        """
        初始化提取器

        Args:
            delay: 请求延迟（秒），避免频繁请求
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        self.delay = delay
        self.redirect_follower = RedirectFollower(max_redirects=5)

        # 统计信息
        self.stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'emails_found': 0,
            'scholar_links': 0,
            'github_links': 0,
            'linkedin_links': 0,
            'research_directions': 0
        }

    def extract_student_info(self, homepage_url: str, name: str = "") -> Dict:
        """
        提取学生完整信息

        Args:
            homepage_url: 学生主页 URL
            name: 学生姓名（可选，用于验证）

        Returns:
            包含所有提取信息的字典
        """
        result = {
            'name': name,
            'homepage_url': homepage_url,
            'final_url': '',
            'basic_info': {},
            'research_info': {},
            'social_links': {},
            'contact_info': {},
            'publications': [],
            'extraction_quality': 0,
            'extraction_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        }

        if not homepage_url:
            result['error'] = 'No homepage URL provided'
            return result

        self.stats['processed'] += 1

        try:
            # 1. 跟随重定向
            redirect_result = self.redirect_follower.follow_redirects(homepage_url)
            final_url = redirect_result['final_url']
            result['final_url'] = final_url

            # 2. 获取页面内容
            resp = self.session.get(final_url, timeout=30, verify=True)
            if resp.status_code != 200:
                result['error'] = f'HTTP {resp.status_code}'
                self.stats['failed'] += 1
                return result

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 3. 提取基本信息
            result['basic_info'] = self._extract_basic_info(soup, resp.text, name)

            # 4. 提取研究方向
            result['research_info'] = self._extract_research_info(soup, resp.text)

            # 5. 提取社交链接
            result['social_links'] = self._extract_social_links(soup, resp.text, final_url)

            # 6. 提取联系信息
            result['contact_info'] = self._extract_contact_info(soup, resp.text)

            # 7. 提取论文列表（如果有）
            result['publications'] = self._extract_publications(soup, resp.text)

            # 8. 计算提取质量分
            result['extraction_quality'] = self._calculate_quality_score(result)

            # 更新统计
            if result['extraction_quality'] > 0:
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1

            if result['contact_info'].get('email'):
                self.stats['emails_found'] += 1
            if result['social_links'].get('google_scholar'):
                self.stats['scholar_links'] += 1
            if result['social_links'].get('github'):
                self.stats['github_links'] += 1
            if result['social_links'].get('linkedin'):
                self.stats['linkedin_links'] += 1
            if result['research_info'].get('directions'):
                self.stats['research_directions'] += 1

        except Exception as e:
            result['error'] = str(e)
            self.stats['failed'] += 1

        # 延迟
        time.sleep(self.delay)

        return result

    def _extract_basic_info(self, soup: BeautifulSoup, text: str, provided_name: str) -> Dict:
        """提取基本信息"""
        info = {
            'name': '',
            'advisor': '',
            'degree': '',
            'enrollment_year': '',
            'affiliation': '',
            'status': ''
        }

        # 1. 提取姓名
        # 优先使用提供的姓名
        if provided_name:
            info['name'] = provided_name
        else:
            # 从 title 标签提取
            title = soup.find('title')
            if title:
                title_text = title.get_text().strip()
                # 通常标题格式是 "Name - Homepage" 或 "Name's Homepage"
                name_match = re.match(r'^([A-Za-z\u4e00-\u9fa5]+)', title_text)
                if name_match:
                    info['name'] = name_match.group(1)

            # 从 h1 标签提取
            if not info['name']:
                h1 = soup.find('h1')
                if h1:
                    info['name'] = h1.get_text().strip()

        # 2. 提取导师信息
        advisor_patterns = [
            r'(?:Advisor|Supervisor|Ph\.?D\.?\s*(?:Advisor|Supervisor))?\s*[:：]\s*([A-Za-z\u4e00-\u9fa5]+\s+[A-Za-z\u4e00-\u9fa5]+)',
            r'(?:导师|指导老师)\s*[:：]?\s*([A-Za-z\u4e00-\u9fa5]+)',
            r'(?:Ph\.?D\.?\s*(?:Student|Candidate))(?:\s+under?\s+(?:the\s+)?supervision\s+(?:of|by)\s+)([A-Za-z\u4e00-\u9fa5\s]+)',
        ]

        for pattern in advisor_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                advisor = match.group(1).strip()
                if len(advisor) < 100:  # 避免匹配过长文本
                    info['advisor'] = advisor
                    break
            if info['advisor']:
                break

        # 3. 提取学位信息
        degree_patterns = [
            r'(Ph\.?D\.?\s*(?:Student|Candidate))',
            r'(Master\'?s\s+Student)',
            r'(Graduate\s+Student)',
            r'(博士(?:生|研究生|候选人))',
            r'(硕士(?:生|研究生))',
        ]

        for pattern in degree_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['degree'] = match.group(1)
                break

        # 4. 提取入学年份
        year_patterns = [
            r'(?:Ph\.?D\.?\s*(?:Student|Candidate).+?(?:since|from|in)\s+(\d{4}))',
            r'(?:入学|Joined|Started)\s*(?:in|:)?\s*(\d{4})',
        ]

        for pattern in year_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                # 验证年份合理性
                if 2000 <= int(year) <= 2030:
                    info['enrollment_year'] = year
                    break

        # 5. 提取所属机构
        affiliation_patterns = [
            r'(?:Affiliation|Institute|Lab|Laboratory)\s*[:：]\s*([^\n,\.]{5,100})',
            r'(?:所属|单位|实验室)\s*[:：]?\s*([^\n,\.]{5,100})',
        ]

        for pattern in affiliation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['affiliation'] = match.group(1).strip()
                break

        return info

    def _extract_research_info(self, soup: BeautifulSoup, text: str) -> Dict:
        """提取研究信息"""
        info = {
            'directions': [],
            'interests': [],
            'keywords': [],
            'summary': ''  # 添加研究概述
        }

        # AI/ML 研究领域关键词库（用于识别）
        ai_keywords = {
            # 机器学习
            'machine learning', 'deep learning', 'neural networks', 'ML', 'DL',
            'reinforcement learning', 'RL', 'supervised learning', 'unsupervised learning',
            'transfer learning', 'meta-learning', 'federated learning', 'online learning',
            'graph neural networks', 'GNN', 'transformer', 'attention mechanism',

            # 计算机视觉
            'computer vision', 'CV', 'image processing', 'object detection',
            'image segmentation', 'video understanding', 'visual recognition',

            # 自然语言处理
            'natural language processing', 'NLP', 'text mining', 'language model',
            'large language model', 'LLM', 'BERT', 'GPT', 'question answering',

            # 优化与理论
            'optimization', 'convex optimization', 'stochastic optimization',
            'bayesian methods', 'causal inference', 'statistical learning',

            # 应用领域
            'recommendation system', 'recommender systems', 'information retrieval',
            'autonomous driving', 'robotics', 'speech recognition',
            'generative model', 'GAN', 'VAE', 'diffusion model',

            # 中文关键词
            '机器学习', '深度学习', '神经网络', '计算机视觉', '自然语言处理',
            '强化学习', '图神经网络', '推荐系统', '优化', '因果推断'
        }

        research_content = ''

        # 方法1: 查找包含 "Research Interest" 的 strong/b 标签
        for tag in soup.find_all(['strong', 'b', 'h1', 'h2', 'h3', 'h4']):
            tag_text = tag.get_text().strip().lower()
            if any(keyword in tag_text for keyword in ['research interest', 'research area', '研究方向', '研究兴趣']):
                # 找到该标签的父元素，然后提取后续内容
                parent = tag.find_parent()
                if parent:
                    # 获取父元素的完整文本
                    research_content = parent.get_text(' ', strip=True)
                    break

        # 方法2: 如果没找到，查找包含研究关键词的段落
        if not research_content:
            # 查找所有段落
            for p in soup.find_all('p'):
                p_text = p.get_text(' ', strip=True)
                # 检查是否包含多个研究关键词
                keyword_count = sum(1 for kw in ai_keywords if kw.lower() in p_text.lower())
                if keyword_count >= 2:  # 至少包含2个研究关键词
                    research_content = p_text
                    break

        # 方法3: 如果还没找到，查找 meta description
        if not research_content:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                research_content = meta_desc['content']

        # 如果找到了研究内容，提取研究方向
        if research_content:
            info['summary'] = research_content[:500]  # 保存摘要

            # 分割并提取研究方向
            # 尝试不同的分割符
            separators = [r'\.+\s+', r',\s+', r';\s+', r'and\s+', r'，\s*', r'、\s*']
            items = []

            for sep in separators:
                items = re.split(sep, research_content)
                if len(items) > 1:
                    break

            # 提取包含研究关键词的项
            for item in items:
                item = item.strip()
                # 清理：移除开头的 "My research focuses on", "I work on" 等
                item = re.sub(r'^(?:my research|I|research|focuses?|work|study|interest|areas?)\s+(?:focuses?\s+on|is|includes?|:)?\s*', '', item, flags=re.IGNORECASE)
                item = item.strip()

                # 检查是否包含研究关键词
                if len(item) > 3 and len(item) < 100:
                    item_lower = item.lower()
                    # 精确匹配关键词
                    for kw in ai_keywords:
                        if kw.lower() in item_lower:
                            formatted_item = item[0].upper() + item[1:] if item else item
                            if formatted_item not in info['directions']:
                                info['directions'].append(formatted_item)
                            break

            # 如果分割失败，尝试从整个文本中提取关键词
            if not info['directions']:
                content_lower = research_content.lower()
                for kw in ai_keywords:
                    if kw.lower() in content_lower:
                        info['directions'].append(kw)

        # 提取关键词标签（从页面中的 tag/keyword 类元素）
        keyword_tags = soup.find_all(['span', 'a', 'li'],
                                     class_=re.compile(r'(tag|keyword|topic|interest)', re.I))

        for tag in keyword_tags:
            tag_text = tag.get_text().strip()
            if 2 < len(tag_text) < 50 and tag_text not in info['keywords']:
                info['keywords'].append(tag_text)

        return info

    def _extract_social_links(self, soup: BeautifulSoup, text: str, base_url: str) -> Dict:
        """提取社交链接"""
        links = {
            'google_scholar': '',
            'github': '',
            'linkedin': '',
            'twitter': '',
            'personal_blog': '',
            'orcid': ''
        }

        # 查找所有链接
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link['href'].strip()
            if not href or href.startswith('javascript:'):
                continue

            # 转换为绝对 URL
            absolute_url = urljoin(base_url, href)

            # Google Scholar
            if 'scholar.google' in href and not links['google_scholar']:
                links['google_scholar'] = absolute_url

            # GitHub
            elif 'github.com' in href and '/user/' not in href:
                # 确保是用户或组织主页，不是特定文件
                if re.match(r'https?://github\.com/[^/]+/?$', absolute_url):
                    links['github'] = absolute_url

            # LinkedIn
            elif 'linkedin.com/in' in href and not links['linkedin']:
                links['linkedin'] = absolute_url

            # Twitter
            elif 'twitter.com' in href and not links['twitter']:
                links['twitter'] = absolute_url

            # ORCID
            elif 'orcid.org' in href and not links['orcid']:
                links['orcid'] = absolute_url

            # 个人博客（排除已经识别的社交网站）
            elif any(keyword in link.get_text().lower()
                    for keyword in ['blog', 'website', 'homepage', 'site']):
                if not any(s in href for s in ['scholar', 'github', 'linkedin', 'twitter']):
                    if not links['personal_blog']:
                        links['personal_blog'] = absolute_url

        return links

    def _extract_contact_info(self, soup: BeautifulSoup, text: str) -> Dict:
        """提取联系信息"""
        contact = {
            'email': '',
            'phone': '',
            'office': '',
            'address': ''
        }

        # 1. 明文邮箱提取
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)

        # 过滤无效邮箱
        valid_emails = []
        for email in emails:
            if (email and
                'noreply' not in email.lower() and
                'github' not in email.lower() and
                'example' not in email.lower() and
                'localhost' not in email.lower() and
                'w3.org' not in email and
                '@2x' not in email and
                'test' not in email.lower().split('@')[0]):
                valid_emails.append(email)

        if valid_emails:
            # 优先使用 .edu 邮箱，然后是 gmail 等
            priority_emails = [e for e in valid_emails if '.edu' in e or '.ac.' in e]
            if priority_emails:
                contact['email'] = priority_emails[0]
            else:
                contact['email'] = valid_emails[0]

        # 2. Cloudflare 保护邮箱
        if not contact['email']:
            cloudflare_links = soup.find_all('a', href=lambda x: x and '/cdn-cgi/l/email-protection' in x)

            for link in cloudflare_links:
                href = link['href']
                # 提取编码的 hex
                hex_match = re.search(r'#([a-f0-9]+)', href)
                if hex_match:
                    encoded_hex = hex_match.group(1)
                    try:
                        decoded = decode_cloudflare_email(encoded_hex)
                        if '@' in decoded and 'Error' not in decoded:
                            contact['email'] = decoded
                            break
                    except:
                        pass

        # 3. 提取电话
        phone_patterns = [
            r'(?:Tel|Phone|Mobile)\s*[:：]?\s*([+\d\s\-\(\)]{7,20})',
            r'(?:电话|手机)\s*[:：]?\s*([+\d\s\-\(\)]{7,20})',
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contact['phone'] = match.group(1).strip()
                break

        # 4. 提取办公室
        office_patterns = [
            r'(?:Office|Room)\s*[:：]?\s*([A-Z0-9\-]+)',
            r'(?:办公室|房间)\s*[:：]?\s*([A-Z0-9\-]+)',
        ]

        for pattern in office_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contact['office'] = match.group(1).strip()
                break

        return contact

    def _extract_publications(self, soup: BeautifulSoup, text: str) -> List[Dict]:
        """提取论文列表"""
        publications = []

        # 查找论文 section
        pub_keywords = ['publications', 'papers', 'research', '论文', '发表']
        pub_sections = []

        for keyword in pub_keywords:
            headers = soup.find_all(['h1', 'h2', 'h3'],
                                   string=re.compile(keyword, re.IGNORECASE))
            pub_sections.extend(headers)

        if not pub_sections:
            return publications

        # 处理第一个论文 section
        section = pub_sections[0]
        current = section.find_next_sibling()

        paper_count = 0
        max_papers = 20  # 最多提取 20 篇

        while current and paper_count < max_papers:
            if current.name in ['h1', 'h2', 'h3', 'h4']:
                break

            # 提取论文信息
            if current.name in ['p', 'li', 'div']:
                text_content = current.get_text(' ', strip=True)

                # 简单的论文识别（包含作者、标题、venue）
                if len(text_content) > 30 and len(text_content) < 500:
                    # 尝试提取 venue（会议/期刊名）
                    venue_match = re.search(r'\b(ICML|NeurIPS|ICLR|AAAI|IJCAI|CVPR|ECCV|ACL|EMNLP|KDD|WWW|SIGIR|TKDE|TPAMI)\b',
                                           text_content, re.IGNORECASE)

                    pub = {
                        'title': text_content[:100],  # 简化处理
                        'venue': venue_match.group(0) if venue_match else '',
                        'year': ''
                    }

                    # 提取年份
                    year_match = re.search(r'\b(20\d{2})\b', text_content)
                    if year_match:
                        pub['year'] = year_match.group(1)

                    publications.append(pub)
                    paper_count += 1

            current = current.find_next_sibling()

        return publications

    def _calculate_quality_score(self, result: Dict) -> float:
        """
        计算提取质量分 (0-100)

        评分标准：
        - 基本信息 (30分): 姓名+导师+学位
        - 研究信息 (30分): 研究方向+论文
        - 社交链接 (20分): Scholar+GitHub+LinkedIn
        - 联系方式 (20分): 邮箱+电话
        """
        score = 0.0

        # 基本信息 (30分)
        basic = result.get('basic_info', {})
        if basic.get('name'):
            score += 10
        if basic.get('advisor'):
            score += 10
        if basic.get('degree') or basic.get('enrollment_year'):
            score += 10

        # 研究信息 (30分)
        research = result.get('research_info', {})
        directions = research.get('directions', [])
        if len(directions) > 0:
            score += min(len(directions) * 5, 15)  # 最多15分
        if result.get('publications'):
            score += 15

        # 社交链接 (20分)
        social = result.get('social_links', {})
        if social.get('google_scholar'):
            score += 8
        if social.get('github'):
            score += 7
        if social.get('linkedin'):
            score += 5

        # 联系方式 (20分)
        contact = result.get('contact_info', {})
        if contact.get('email'):
            score += 15
        if contact.get('phone') or contact.get('office'):
            score += 5

        return round(score, 1)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats['processed']
        if total == 0:
            return self.stats

        return {
            **self.stats,
            'success_rate': round(self.stats['successful'] / total * 100, 1),
            'email_rate': round(self.stats['emails_found'] / total * 100, 1),
            'scholar_rate': round(self.stats['scholar_links'] / total * 100, 1),
            'github_rate': round(self.stats['github_links'] / total * 100, 1),
            'linkedin_rate': round(self.stats['linkedin_links'] / total * 100, 1),
            'research_rate': round(self.stats['research_directions'] / total * 100, 1),
        }


def main():
    """主函数 - 测试深度提取器"""
    print("="*80)
    print("LAMDA 学生深度信息提取器 - 测试")
    print("="*80)
    print()

    scraper = DeepStudentScraper(delay=1.0)

    # 测试案例
    test_cases = [
        {
            'name': '杨嘉祺',
            'url': 'http://www.lamda.nju.edu.cn/yangjq/',
            'expected': {
                'scholar': True,
                'github': True,
                'email': True,
                'research': True
            }
        },
        {
            'name': '陈雄辉',
            'url': 'http://www.lamda.nju.edu.cn/chenxh/',
            'expected': {
                'github': True,
                'research': True
            }
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] 测试: {case['name']}")
        print(f"URL: {case['url']}")
        print()

        result = scraper.extract_student_info(case['url'], case['name'])

        # 显示结果
        if 'error' in result:
            print(f"❌ 错误: {result['error']}")
        else:
            print(f"✅ 成功")
            print(f"最终 URL: {result['final_url']}")
            print(f"质量分: {result['extraction_quality']}/100")
            print()

            # 基本信息
            basic = result['basic_info']
            if basic:
                print("📋 基本信息:")
                if basic.get('name'):
                    print(f"  姓名: {basic['name']}")
                if basic.get('advisor'):
                    print(f"  导师: {basic['advisor']}")
                if basic.get('degree'):
                    print(f"  学位: {basic['degree']}")
                if basic.get('enrollment_year'):
                    print(f"  入学年份: {basic['enrollment_year']}")
                print()

            # 研究信息
            research = result['research_info']
            if research.get('directions'):
                print("🔬 研究方向:")
                for direction in research['directions'][:5]:
                    print(f"  - {direction}")
                print()

            # 社交链接
            social = result['social_links']
            if any(social.values()):
                print("🔗 社交链接:")
                if social.get('google_scholar'):
                    print(f"  Google Scholar: {social['google_scholar']}")
                if social.get('github'):
                    print(f"  GitHub: {social['github']}")
                if social.get('linkedin'):
                    print(f"  LinkedIn: {social['linkedin']}")
                print()

            # 联系方式
            contact = result['contact_info']
            if contact.get('email'):
                print("📧 联系方式:")
                print(f"  邮箱: {contact['email']}")
                print()

            # 论文
            if result.get('publications'):
                print("📚 论文 (前3篇):")
                for pub in result['publications'][:3]:
                    venue_year = f"{pub.get('venue', '')} {pub.get('year', '')}".strip()
                    print(f"  - {pub['title'][:60]}...")
                    if venue_year:
                        print(f"    {venue_year}")
                print()

        print("-"*80)
        print()

    # 统计
    stats = scraper.get_stats()
    print("📊 统计:")
    print(f"  处理: {stats['processed']}")
    print(f"  成功: {stats['successful']} ({stats['success_rate']}%)")
    print(f"  找到邮箱: {stats['emails_found']} ({stats['email_rate']}%)")
    print(f"  Scholar: {stats['scholar_links']} ({stats['scholar_rate']}%)")
    print(f"  GitHub: {stats['github_links']} ({stats['github_rate']}%)")
    print(f"  LinkedIn: {stats['linkedin_links']} ({stats['linkedin_rate']}%)")
    print(f"  研究方向: {stats['research_directions']} ({stats['research_rate']}%)")
    print()


if __name__ == '__main__':
    main()
