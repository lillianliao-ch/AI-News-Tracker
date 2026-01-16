#!/usr/bin/env python3
"""
LAMDA 论文分析 - 基于网站论文列表
直接从教授页面的 Publications 部分提取论文信息
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from collections import defaultdict

class LamdaPaperAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # 顶级会议/期刊（从图片中看到的）
        self.top_venues = {
            'NeurIPS': 'NeurIPS',
            'ICML': 'ICML',
            'ICLR': 'ICLR',
            'AAAI': 'AAAI',
            'IJCAI': 'IJCAI',
            'KDD': 'KDD',
            'CVPR': 'CVPR',
            'ICCV': 'ICCV',
            'ECCV': 'ECCV',
            'ACL': 'ACL',
            'EMNLP': 'EMNLP',
            'WWW': 'WWW',
            'SIGIR': 'SIGIR',
            'JMLR': 'JMLR',
            'Machine Learning': 'Machine Learning',
            'Artificial Intelligence': 'Artificial Intelligence',
            'IEEE TPAMI': 'IEEE TPAMI',
            'Nature': 'Nature',
            'Science': 'Science'
        }

    def load_professors(self):
        """加载教授列表"""
        df = pd.read_excel('LAMDA.xlsx')
        prof_df = df[['Professor', 'Professor_URL']].drop_duplicates()
        prof_df = prof_df.dropna(subset=['Professor_URL'])

        professors = []
        for _, row in prof_df.iterrows():
            if str(row['Professor_URL']).startswith('http'):
                professors.append({
                    'name': row['Professor'],
                    'url': row['Professor_URL']
                })

        return professors

    def extract_papers_from_page(self, url):
        """从教授页面提取论文列表"""
        try:
            response = self.session.get(url, timeout=10)
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'

            soup = BeautifulSoup(response.content, 'html.parser')

            # 获取页面文本
            text = soup.get_text()

            # 查找 Publications 部分
            # 通常在 "Publications" 或 "Selected Publications" 之后
            pub_patterns = [
                r'Publications[:\s]*(.*?)(?=$)',
                r'Selected Publications[:\s]*(.*?)(?=$)',
                r'发表论文[:\s]*(.*?)(?=$)'
            ]

            papers = []

            for pattern in pub_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    pub_text = match.group(1)

                    # 按行分割，每行通常是一篇论文
                    lines = pub_text.split('\n')

                    for line in lines:
                        line = line.strip()
                        if len(line) > 50 and len(line) < 500:  # 合理的论文标题长度
                            # 尝试提取论文信息
                            paper_info = self.parse_paper_line(line)
                            if paper_info:
                                papers.append(paper_info)

                    # 如果找到了论文就停止
                    if papers:
                        break

            return papers

        except Exception as e:
            print(f"    ❌ 提取论文出错: {str(e)}")
            return []

    def parse_paper_line(self, line):
        """解析单行论文信息"""
        # 尝试提取年份
        year_match = re.search(r'\b(20\d{2})\b', line)
        year = int(year_match.group(1)) if year_match else None

        # 检查是否是顶级会议/期刊
        venue = None
        venue_confidence = 0

        for top_venue in self.top_venues:
            if top_venue in line:
                venue = top_venue
                # 完全匹配
                if re.search(rf'\b{top_venue}\b', line, re.IGNORECASE):
                    venue_confidence = 3
                break

        # 如果没有明确匹配，尝试其他常见模式
        if not venue:
            # 查找大写的会议名称（通常是缩写）
            venue_match = re.search(r'\b([A-Z]{2,6})\b', line)
            if venue_match:
                potential_venue = venue_match.group(1)
                if potential_venue not in ['In', 'Proc', 'Of', 'And', 'Or', 'The', 'A', 'An']:
                    venue = potential_venue
                    venue_confidence = 1

        # 提取第一作者（通常是学生）
        # 论文格式通常是：Author1, Author2, ... Title. Venue Year
        author_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+', line)

        paper_info = {
            'raw_text': line,
            'year': year,
            'venue': venue,
            'venue_confidence': venue_confidence,
            'first_author': author_match.group(1) if author_match else None
        }

        return paper_info

    def analyze_professor_papers(self, professor):
        """分析单个教授的论文"""
        print(f"\n{'='*60}")
        print(f"分析: {professor['name']}")
        print(f"URL: {professor['url']}")
        print(f"{'='*60}")

        papers = self.extract_papers_from_page(professor['url'])

        if not papers:
            print("  ⚠️ 未找到论文信息")
            return None

        print(f"\n  ✓ 找到 {len(papers)} 篇论文")

        # 过滤近5年的顶级会议论文
        current_year = datetime.now().year
        recent_top_papers = [
            p for p in papers
            if p['year'] and p['year'] >= (current_year - 5)
            and p['venue'] and p['venue_confidence'] >= 2
        ]

        print(f"  ✓ 其中近5年顶级会议论文: {len(recent_top_papers)} 篇")

        if recent_top_papers:
            print(f"\n  部分论文:")
            for paper in recent_top_papers[:5]:
                print(f"    - {paper['first_author'] if paper['first_author'] else 'Unknown'} et al. ({paper['year']}) - {paper['venue']}")
                print(f"      {paper['raw_text'][:150]}...")

        # 统计第一作者（通常是学生）
        first_authors = defaultdict(lambda: {'papers': [], 'venues': []})

        for paper in recent_top_papers:
            if paper['first_author']:
                first_authors[paper['first_author']]['papers'].append(paper)
                first_authors[paper['first_author']]['venues'].append(paper['venue'])

        # 找出论文数最多的前3名学生
        top_students = sorted(
            first_authors.items(),
            key=lambda x: len(x[1]['papers']),
            reverse=True
        )[:3]

        if top_students:
            print(f"\n  🏆 顶级学生 (按第一作者论文数):")
            for idx, (student_name, info) in enumerate(top_students, 1):
                print(f"\n  #{idx} {student_name}")
                print(f"     第一作者论文数: {len(info['papers'])}")
                print(f"     发表会议: {', '.join(set(info['venues']))}")
                print(f"     代表作:")
                for paper in info['papers'][:3]:
                    print(f"       - ({paper['year']}) {paper['venue']}")
                    print(f"         {paper['raw_text'][:100]}...")

        return {
            'professor': professor['name'],
            'url': professor['url'],
            'total_papers': len(papers),
            'recent_top_papers': len(recent_top_papers),
            'top_students': [
                {
                    'name': name,
                    'paper_count': len(info['papers']),
                    'venues': list(set(info['venues'])),
                    'papers': [p['raw_text'][:200] for p in info['papers'][:3]]
                }
                for name, info in top_students
            ] if top_students else []
        }

    def analyze_all(self):
        """分析所有教授"""
        professors = self.load_professors()

        print(f"\n{'='*80}")
        print(f"LAMDA 论文分析（基于网站论文列表）")
        print(f"{'='*80}")
        print(f"\n总共 {len(professors)} 位教授")

        results = []

        for idx, professor in enumerate(professors, 1):
            print(f"\n进度: [{idx}/{len(professors)}]")

            try:
                result = self.analyze_professor_papers(professor)
                if result:
                    results.append(result)

            except Exception as e:
                print(f"  ❌ 分析出错: {str(e)}")
                continue

        return results

    def save_results(self, results):
        """保存分析结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if not results:
            print("\n⚠️ 没有结果可保存")
            return

        # 创建汇总数据
        summary_data = []

        for result in results:
            professor = result['professor']
            total_papers = result['total_papers']
            top_papers = result['recent_top_papers']
            students = result['top_students']

            for student in students:
                summary_data.append({
                    'professor': professor,
                    'professor_total_papers': total_papers,
                    'professor_recent_top_papers': top_papers,
                    'student_name': student['name'],
                    'student_first_author_papers': student['paper_count'],
                    'venues': ', '.join(student['venues']),
                    'sample_papers': '; '.join(student['papers'])
                })

        # 保存结果
        if summary_data:
            df = pd.DataFrame(summary_data)
            output_file = f'LAMDA_paper_analysis_{timestamp}.xlsx'
            df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"\n✓ 论文分析结果已保存到: {output_file}")

        # 打印统计
        print(f"\n{'='*80}")
        print("【分析汇总】")
        print(f"{'='*80}")
        print(f"分析教授数: {len(results)}")
        print(f"识别出的顶级学生: {len(summary_data)}")

        # 按第一作者论文数排序
        if summary_data:
            df_sorted = df.sort_values('student_first_author_papers', ascending=False)
            print(f"\n🏆 论文数最多的 Top 10 学生:")
            for idx, row in df_sorted.head(10).iterrows():
                print(f"  {row['student_first_author_papers']} 篇 - {row['student_name']} (导师: {row['professor']})")
                print(f"    会议: {row['venues']}")

        print(f"\n{'='*80}\n")


def main():
    analyzer = LamdaPaperAnalyzer()
    results = analyzer.analyze_all()
    analyzer.save_results(results)


if __name__ == '__main__':
    main()
