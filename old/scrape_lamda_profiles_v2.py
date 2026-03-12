#!/usr/bin/env python3
"""
LAMDA 人才信息爬虫 - 改进版
从 Excel 中读取链接，爬取教授和学生个人信息
单独提取联系方式，更好地处理结构化数据
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re
from datetime import datetime
import json

class LamdaScraperV2:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def load_excel(self):
        """加载 Excel 文件"""
        df = pd.read_excel(self.excel_path)
        return df

    def extract_contact_info(self, soup, text):
        """提取联系方式"""
        contact = {
            'email': '',
            'phone': '',
            'office': '',
            'address': '',
            'other_contact': ''
        }

        # 提取邮箱
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            # 优先选择 lamda.nju.edu.cn 或 nju.edu.cn 的邮箱
            nju_emails = [e for e in emails if 'lamda.nju.edu.cn' in e or 'nju.edu.cn' in e]
            contact['email'] = nju_emails[0] if nju_emails else emails[0]

        # 提取电话（中国手机号）
        phones = re.findall(r'(?:\+?86[-\s]?)?1[3-9]\d{9}', text)
        if phones:
            contact['phone'] = phones[0]

        # 提取办公室信息
        office_patterns = [
            r'Office[:\s]*(.*?)(?:\n|$)',
            r'办公室[:\s]*(.*?)(?:\n|$)',
            r'Room[:\s]*([A-Z]?\d+[^\n]*)',
        ]
        for pattern in office_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contact['office'] = match.group(1).strip()
                break

        # 提取地址
        address_keywords = ['Address', '地址', 'Location', '位置']
        for keyword in address_keywords:
            pattern = f'{keyword}[:\\s]*(.*?)(?:\\n|$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contact['address'] = match.group(1).strip()
                break

        return contact

    def detect_language(self, text):
        """检测文本主要是中文还是英文"""
        if not text:
            return 'unknown'

        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in text if c.isalpha() and ord(c) < 128])

        if chinese_chars > english_chars:
            return 'chinese'
        elif english_chars > chinese_chars:
            return 'english'
        else:
            return 'mixed'

    def extract_biography(self, soup, text):
        """提取个人简介（支持中英文）"""
        biography = {
            'biography': '',
            'biography_en': '',
            'biography_zh': '',
            'research_interests': '',
            'research_interests_en': '',
            'research_interests_zh': '',
            'education': '',
            'experience': ''
        }

        # 提取英文 Biography
        bio_en_patterns = [r'Biography[:\s]*(.*?)(?=##|Research Interests|研究兴趣|$)',
                          r'About[:\s]*(.*?)(?=##|$)']

        for pattern in bio_en_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                bio_text = match.group(1).strip()
                bio_text = re.sub(r'\s+', ' ', bio_text)
                if len(bio_text) > 50:  # 确保不是空内容
                    biography['biography_en'] = bio_text[:1000]
                    break

        # 提取中文简介
        bio_zh_patterns = [r'简介[:\s]*(.*?)(?=##|研究兴趣|Research Interests|$)',
                          r'个人简介[:\s]*(.*?)(?=##|$)',
                          r'关于我[:\s]*(.*?)(?=##|$)']

        for pattern in bio_zh_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                bio_text = match.group(1).strip()
                bio_text = re.sub(r'\s+', ' ', bio_text)
                if len(bio_text) > 20:  # 确保不是空内容
                    biography['biography_zh'] = bio_text[:1000]
                    break

        # 决定默认显示哪个版本
        if biography['biography_zh']:
            biography['biography'] = biography['biography_zh']
        elif biography['biography_en']:
            biography['biography'] = biography['biography_en']

        # 提取英文研究兴趣
        interest_en_patterns = [r'Research Interests?[:\s]*(.*?)(?=##|Publications|发表论文|$)',
                               r'Interest[:\s]*(.*?)(?=##|$)']

        for pattern in interest_en_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                interests = match.group(1).strip()
                interests = re.sub(r'\s+', ' ', interests)
                if len(interests) > 20:
                    biography['research_interests_en'] = interests[:500]
                    break

        # 提取中文研究兴趣
        interest_zh_patterns = [r'研究兴趣[:\s]*(.*?)(?=##|发表论文|Publications|$)',
                               r'研究方向[:\s]*(.*?)(?=##|$)']

        for pattern in interest_zh_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                interests = match.group(1).strip()
                interests = re.sub(r'\s+', ' ', interests)
                if len(interests) > 10:
                    biography['research_interests_zh'] = interests[:500]
                    break

        # 决定默认显示哪个版本
        if biography['research_interests_zh']:
            biography['research_interests'] = biography['research_interests_zh']
        elif biography['research_interests_en']:
            biography['research_interests'] = biography['research_interests_en']

        return biography

    def extract_publications(self, soup, text):
        """提取发表的论文"""
        publications = []

        # 查找 Publications 部分
        pub_pattern = r'(?:Publications|发表论文|Selected Publications)[:\s]*(.*?)(?=##|$)'
        match = re.search(pub_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            pub_text = match.group(1).strip()
            # 尝试按行分割论文
            lines = re.split(r'\n(?=\d+\.|\w+\.,)', pub_text)

            for line in lines[:10]:  # 只取前10篇
                line = line.strip()
                if len(line) > 50:  # 过滤掉太短的行
                    publications.append(line[:200])  # 限制每篇论文长度

        return '; '.join(publications) if publications else ''

    def scrape_page(self, url, person_type, name=None, professor=None):
        """
        爬取个人信息页面 - 改进版
        person_type: 'professor' 或 'student'
        """
        if not url or pd.isna(url):
            return None

        # 过滤无效 URL
        if url == 'Ming' or not str(url).startswith('http'):
            return None

        try:
            print(f"正在爬取: {url}")
            response = self.session.get(url, timeout=10)

            # 智能检测编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'

            if response.status_code != 200:
                print(f"  ❌ 状态码: {response.status_code}")
                return {
                    'url': url,
                    'type': person_type,
                    'name': name if name else '',
                    'professor': professor if professor else '',
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': f'error_{response.status_code}',
                    'error': f'HTTP {response.status_code}'
                }

            # 尝试多种编码方式解析
            try:
                soup = BeautifulSoup(response.content, 'html.parser')
            except:
                soup = BeautifulSoup(response.text, 'html.parser')

            # 移除 script 和 style 标签
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # 提取结构化信息
            contact_info = self.extract_contact_info(soup, text)
            bio_info = self.extract_biography(soup, text)
            publications = self.extract_publications(soup, text)

            # 构建结果字典
            info = {
                'url': url,
                'type': person_type,
                'name': name if name else '',
                'professor': professor if professor else '',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success',

                # 联系方式（单独列）
                'email': contact_info['email'],
                'phone': contact_info['phone'],
                'office': contact_info['office'],
                'address': contact_info['address'],

                # 个人信息
                'biography': bio_info['biography'],
                'research_interests': bio_info['research_interests'],
                'publications': publications,

                # 原始内容（保留）
                'raw_content': text[:3000]
            }

            print(f"  ✓ 成功 (邮箱: {'有' if contact_info['email'] else '无'})")
            return info

        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
            return {
                'url': url,
                'type': person_type,
                'name': name if name else '',
                'professor': professor if professor else '',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'error',
                'error': str(e),
                'email': '', 'phone': '', 'office': '', 'address': '',
                'biography': '', 'research_interests': '', 'publications': '', 'raw_content': ''
            }

    def scrape_all(self):
        """爬取所有链接"""
        df = self.load_excel()

        print(f"\n{'='*60}")
        print(f"开始爬取 LAMDA 人才信息 (改进版)")
        print(f"{'='*60}\n")

        # 爬取教授信息
        print("【第一部分：爬取教授信息】\n")
        prof_df = df[['Professor', 'Professor_URL']].drop_duplicates()
        prof_df = prof_df.dropna(subset=['Professor_URL'])

        for idx, row in prof_df.iterrows():
            professor_name = row['Professor']
            professor_url = row['Professor_URL']

            result = self.scrape_page(professor_url, 'professor', name=professor_name)
            if result:
                self.results.append(result)

            time.sleep(1)  # 礼貌延迟

        # 爬取学生信息
        print(f"\n{'='*60}")
        print("【第二部分：爬取学生信息】\n")
        student_df = df[['Student_Name', 'Student_URL', 'Professor']].dropna(subset=['Student_URL'])

        for idx, row in student_df.iterrows():
            student_name = row['Student_Name']
            student_url = row['Student_URL']
            professor_name = row['Professor']

            result = self.scrape_page(student_url, 'student', name=student_name, professor=professor_name)
            if result:
                self.results.append(result)

            time.sleep(0.5)  # 礼貌延迟

        return self.results

    def save_results(self):
        """保存结果 - 改进版（优先中文）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建 DataFrame
        df = pd.DataFrame(self.results)

        # 重新排列列的顺序，优先显示中文内容
        columns_order = [
            'url', 'type', 'name', 'professor',
            'email', 'phone', 'office', 'address',  # 联系方式
            'biography_zh', 'biography_en', 'biography',  # 简介（中文优先）
            'research_interests_zh', 'research_interests_en', 'research_interests',  # 研究兴趣（中文优先）
            'publications',  # 发表论文
            'status', 'scraped_at', 'raw_content'  # 元信息
        ]

        # 只保留存在的列
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]

        # 保存完整版 Excel（中文优先）
        output_file = f'LAMDA_profiles_zh_first_{timestamp}.xlsx'
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n✓ 完整结果（中文优先）已保存到: {output_file}")

        # 保存联系方式专用文件
        contact_cols = ['name', 'type', 'professor', 'email', 'phone', 'office', 'address', 'url']
        contact_cols = [col for col in contact_cols if col in df.columns]
        contact_df = df[contact_cols].copy()
        contact_df = contact_df[contact_df['email'] != '']  # 只保留有邮箱的
        contact_file = f'LAMDA_contacts_only_{timestamp}.xlsx'
        contact_df.to_excel(contact_file, index=False, engine='openpyxl')
        print(f"✓ 联系方式已保存到: {contact_file}")

        # 保存中文简介专用文件
        bio_cols = ['name', 'type', 'professor', 'biography_zh', 'research_interests_zh', 'url']
        bio_cols = [col for col in bio_cols if col in df.columns]
        bio_df = df[bio_cols].copy()
        if 'biography_zh' in bio_df.columns:
            bio_df = bio_df[bio_df['biography_zh'] != '']  # 只保留有中文简介的
        bio_file = f'LAMDA_biographies_zh_{timestamp}.xlsx'
        bio_df.to_excel(bio_file, index=False, engine='openpyxl')
        print(f"✓ 中文简介已保存到: {bio_file}")

        # 打印统计信息
        self.print_statistics(df)

    def print_statistics(self, df=None):
        """打印统计信息"""
        if df is None:
            df = pd.DataFrame(self.results)

        total = len(df)
        success = len(df[df['status'] == 'success'])
        error = len(df[df['status'].astype(str).str.startswith('error', na=False)])
        professors = len(df[df['type'] == 'professor'])
        students = len(df[df['type'] == 'student'])
        has_email = len(df[df['email'] != ''])
        has_bio_zh = len(df[df.get('biography_zh', '') != '']) if 'biography_zh' in df.columns else 0
        has_bio_en = len(df[df.get('biography_en', '') != '']) if 'biography_en' in df.columns else 0

        print(f"\n{'='*60}")
        print("【爬取统计】")
        print(f"{'='*60}")
        print(f"总计: {total} 个页面")
        print(f"成功: {success} 个 | 失败: {error} 个")
        print(f"教授: {professors} 个 | 学生: {students} 个")
        print(f"有邮箱: {has_email} 个 ({has_email/total*100:.1f}%)")
        print(f"有中文简介: {has_bio_zh} 个 ({has_bio_zh/total*100:.1f}%)")
        print(f"有英文简介: {has_bio_en} 个 ({has_bio_en/total*100:.1f}%)")
        print(f"{'='*60}\n")


def main():
    # 使用方式
    scraper = LamdaScraperV2('LAMDA.xlsx')
    scraper.scrape_all()
    scraper.save_results()


if __name__ == '__main__':
    main()
