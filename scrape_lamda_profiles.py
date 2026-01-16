#!/usr/bin/env python3
"""
LAMDA 人才信息爬虫
从 Excel 中读取链接，爬取教授和学生个人信息
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re
from datetime import datetime
import json

class LamdaScraper:
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

    def scrape_page(self, url, person_type, name=None, professor=None):
        """
        爬取个人信息页面
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
            response.encoding = response.apparent_encoding

            if response.status_code != 200:
                print(f"  ❌ 状态码: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取页面文本内容
            # 移除 script 和 style 标签
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # 尝试提取常见信息
            info = {
                'url': url,
                'type': person_type,
                'name': name if name else '',
                'professor': professor if professor else '',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success',
                'raw_content': text[:5000]  # 限制长度
            }

            # 提取邮箱
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            if emails:
                info['email'] = emails[0]

            # 提取电话
            phones = re.findall(r'(?:\+?86)?[-\s]?1[3-9]\d{9}', text)
            if phones:
                info['phone'] = phones[0]

            print(f"  ✓ 成功提取内容 (长度: {len(text)})")
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
                'error': str(e)
            }

    def scrape_all(self):
        """爬取所有链接"""
        df = self.load_excel()

        print(f"\n{'='*60}")
        print(f"开始爬取 LAMDA 人才信息")
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

    def save_results(self, output_format='excel'):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_format == 'excel':
            # 保存为 Excel
            output_file = f'LAMDA_profiles_scraped_{timestamp}.xlsx'
            df = pd.DataFrame(self.results)

            # 保存完整数据
            df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"\n✓ 结果已保存到: {output_file}")

            # 保存简化版本（只保留关键信息）
            summary_df = df[['url', 'type', 'name', 'professor', 'status', 'scraped_at']].copy()
            summary_file = f'LAMDA_profiles_summary_{timestamp}.xlsx'
            summary_df.to_excel(summary_file, index=False, engine='openpyxl')
            print(f"✓ 摘要已保存到: {summary_file}")

        elif output_format == 'json':
            output_file = f'LAMDA_profiles_scraped_{timestamp}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 结果已保存到: {output_file}")

        # 打印统计信息
        self.print_statistics()

    def print_statistics(self):
        """打印统计信息"""
        total = len(self.results)
        success = len([r for r in self.results if r['status'] == 'success'])
        error = len([r for r in self.results if r['status'] == 'error'])
        professors = len([r for r in self.results if r['type'] == 'professor'])
        students = len([r for r in self.results if r['type'] == 'student'])

        print(f"\n{'='*60}")
        print("【爬取统计】")
        print(f"{'='*60}")
        print(f"总计: {total} 个页面")
        print(f"成功: {success} 个")
        print(f"失败: {error} 个")
        print(f"教授: {professors} 个")
        print(f"学生: {students} 个")
        print(f"{'='*60}\n")


def main():
    # 使用方式
    scraper = LamdaScraper('LAMDA.xlsx')
    scraper.scrape_all()
    scraper.save_results(output_format='excel')


if __name__ == '__main__':
    main()
