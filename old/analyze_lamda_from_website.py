#!/usr/bin/env python3
"""
LAMDA 顶级人才分析 - 基于网站信息
直接从 LAMDA 网站提取论文和学生信息
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
from datetime import datetime

class LamdaWebsiteAnalyzer:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # 顶级会议/期刊关键词
        self.top_venue_keywords = [
            'NeurIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI',
            'Nature', 'Science', 'JMLR', 'Machine Learning',
            'Artificial Intelligence', 'IEEE TPAMI'
        ]

    def load_data(self):
        """加载已爬取的数据"""
        df = pd.read_excel('LAMDA_profiles_zh_first_20260105_112233.xlsx')
        return df

    def analyze_professor_page(self, url, professor_name):
        """分析教授页面，提取学生和论文信息"""
        try:
            response = self.session.get(url, timeout=10)
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'

            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找所有包含中文的名字（通常是学生）
            text = soup.get_text()

            # 提取学生名字
            # 模式：中文名 + (英文拼音) 的形式
            student_pattern = r'([一-龥]{2,3})\s*\(([A-Za-z\s\-]+)\)'
            students = re.findall(student_pattern, text)

            # 去重
            unique_students = list(set([f"{zh} ({en.strip()})" for zh, en in students]))

            # 查找顶级论文
            publications_text = soup.get_text()
            top_papers = []

            for venue in self.top_venue_keywords:
                # 简单的匹配 - 查找包含顶级会议/期刊名字的行
                pattern = f'.*{venue}.*'
                matches = re.findall(pattern, publications_text, re.IGNORECASE)
                for match in matches[:5]:  # 每个会议最多5篇
                    if len(match.strip()) > 20 and len(match.strip()) < 300:
                        top_papers.append({
                            'venue': venue,
                            'text': match.strip()
                        })

            return {
                'students': unique_students[:10],  # 最多10个学生
                'top_papers': top_papers[:10],  # 最多10篇顶级论文
                'raw_content': text[:2000]
            }

        except Exception as e:
            print(f"    ❌ 错误: {str(e)}")
            return None

    def analyze_all_professors(self):
        """分析所有教授"""
        df = self.load_data()

        # 获取所有教授
        professors = df[df['type'] == 'professor'][['name', 'url']].copy()
        professors = professors.dropna(subset=['url'])

        print(f"\n{'='*80}")
        print(f"LAMDA 教授分析（基于网站信息）")
        print(f"{'='*80}\n")

        results = []

        for idx, row in professors.iterrows():
            professor_name = row['name']
            professor_url = row['url']

            print(f"[{idx+1}/{len(professors)}] 分析: {professor_name}")

            # 跳过无法访问的 URL
            if not str(professor_url).startswith('http'):
                print(f"  ⚠️ 跳过无效 URL")
                continue

            analysis = self.analyze_professor_page(professor_url, professor_name)

            if analysis:
                print(f"  ✓ 找到 {len(analysis['students'])} 个学生")
                print(f"  ✓ 找到 {len(analysis['top_papers'])} 篇顶级论文")

                results.append({
                    'professor': professor_name,
                    'url': professor_url,
                    'students': analysis['students'],
                    'top_papers_count': len(analysis['top_papers']),
                    'top_papers': analysis['top_papers']
                })

        return results

    def save_results(self, results):
        """保存分析结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if not results:
            print("\n⚠️ 没有结果可保存")
            return

        # 创建汇总
        summary_data = []

        for result in results:
            professor = result['professor']
            students = result['students']
            papers_count = result['top_papers_count']
            papers = result['top_papers']

            # 为每个学生创建一行
            for student in students:
                summary_data.append({
                    'professor': professor,
                    'student_name': student,
                    'professor_top_papers_count': papers_count,
                    'professor_top_papers': '; '.join([p['text'][:100] for p in papers[:3]])
                })

        # 保存结果
        df = pd.DataFrame(summary_data)
        output_file = f'LAMDA_professors_students_analysis_{timestamp}.xlsx'
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n✓ 分析结果已保存到: {output_file}")

        # 打印统计
        print(f"\n{'='*80}")
        print("【分析汇总】")
        print(f"{'='*80}")
        print(f"分析教授数: {len(results)}")
        print(f"总学生数: {len(summary_data)}")

        # 找出顶级论文最多的教授
        print(f"\n🏆 顶级论文最多的 Top 5 教授:")
        sorted_results = sorted(results, key=lambda x: x['top_papers_count'], reverse=True)
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"  {i}. {result['professor']}: {result['top_papers_count']} 篇顶级论文")
            print(f"     学生数: {len(result['students'])}")
            if result['students']:
                print(f"     学生: {', '.join(result['students'][:5])}")

        print(f"\n{'='*80}\n")


def main():
    analyzer = LamdaWebsiteAnalyzer('LAMDA.xlsx')
    results = analyzer.analyze_all_professors()
    analyzer.save_results(results)


if __name__ == '__main__':
    main()
