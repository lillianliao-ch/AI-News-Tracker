#!/usr/bin/env python3
"""
LAMDA 顶级人才分析 - 使用 Semantic Scholar Author API
正确使用 Author API 来获取作者和论文信息
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import json
from collections import defaultdict

class LamdaAuthorAPIAnalyzer:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.api_base = "https://api.semanticscholar.org/graph/v1"

        # 顶级会议/期刊
        self.top_venues = [
            'NeurIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI',
            'CVPR', 'ICCV', 'ECCV', 'KDD', 'WWW', 'SIGIR',
            'ACL', 'EMNLP', 'NAACL',
            'JMLR', 'Machine Learning',
            'Artificial Intelligence', 'IEEE Transactions on Pattern Analysis',
            'Nature', 'Science', 'Nature Machine Intelligence'
        ]

    def load_professors(self):
        """加载教授列表"""
        df = pd.read_excel(self.excel_path)
        prof_df = df[['Professor', 'Professor_URL']].drop_duplicates()
        prof_df = prof_df.dropna(subset=['Professor_URL'])

        professors = []
        for _, row in prof_df.iterrows():
            if pd.notna(row['Professor_URL']) and str(row['Professor_URL']).startswith('http'):
                professors.append({
                    'name': row['Professor'],
                    'url': row['Professor_URL']
                })

        return professors

    def search_author_id(self, author_name, affiliation="Nanjing University"):
        """
        搜索作者的 Author ID
        使用 Author Search API
        """
        try:
            url = f"{self.api_base}/author/search"

            params = {
                'query': f'{author_name} {affiliation}',
                'fields': 'authorId,name,papers,hIndex,citationCount',
                'limit': 5
            }

            print(f"  搜索作者: {author_name}")
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                authors = data.get('data', [])

                if authors:
                    # 返回第一个匹配的作者
                    return authors[0]
                else:
                    print(f"    ⚠️ 未找到匹配的作者")
                    return None

            elif response.status_code == 429:
                print(f"    ⚠️ API 限流，等待 10 秒...")
                time.sleep(10)
                return self.search_author_id(author_name, affiliation)

            else:
                print(f"    ⚠️ API 错误: {response.status_code}")
                return None

        except Exception as e:
            print(f"    ❌ 错误: {str(e)}")
            return None

    def get_author_papers(self, author_id, years=5):
        """
        获取作者的论文列表
        使用 Author API 的 papers 字段
        """
        try:
            url = f"{self.api_base}/author/{author_id}"

            params = {
                'fields': 'papers.title,papers.year,papers.venue,papers.citationCount,papers.authors,papers.publicationTypes',
                'limit': 100  # 最多100篇论文
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                papers = data.get('papers', [])

                # 过滤近5年的论文
                current_year = datetime.now().year
                recent_papers = [
                    p for p in papers
                    if p.get('year') and p.get('year') >= (current_year - years)
                ]

                return recent_papers

            else:
                print(f"    ⚠️ 获取论文失败: {response.status_code}")
                return []

        except Exception as e:
            print(f"    ❌ 获取论文出错: {str(e)}")
            return []

    def extract_top_papers(self, papers):
        """提取顶级会议/期刊的论文"""
        top_papers = []

        for paper in papers:
            venue = paper.get('venue', '')
            if not venue:
                continue

            # 检查是否是顶级刊物
            is_top_venue = any(
                top_venue.lower() in str(venue).lower()
                for top_venue in self.top_venues
            )

            if is_top_venue:
                top_papers.append({
                    'title': paper.get('title', ''),
                    'year': paper.get('year'),
                    'venue': venue,
                    'citationCount': paper.get('citationCount', 0),
                    'authors': paper.get('authors', [])
                })

        # 按引用数排序
        top_papers.sort(key=lambda x: x['citationCount'], reverse=True)

        return top_papers

    def analyze_student_contributions(self, top_papers, professor_name):
        """
        分析学生的贡献
        从顶级论文中提取学生作者
        """
        student_data = defaultdict(lambda: {
            'papers': [],
            'total_citations': 0,
            'venues': set()
        })

        for paper in top_papers:
            authors = paper.get('authors', [])

            for author_info in authors:
                author_name = author_info.get('name', '')
                author_id = author_info.get('authorId', '')

                # 排除教授本人
                if professor_name.lower() not in author_name.lower():
                    # 记录学生贡献
                    student_data[author_name]['papers'].append({
                        'title': paper['title'],
                        'year': paper['year'],
                        'venue': paper['venue'],
                        'citationCount': paper['citationCount']
                    })
                    student_data[author_name]['total_citations'] += paper['citationCount']
                    student_data[author_name]['venues'].add(paper['venue'])

        # 转换为排序的列表
        sorted_students = sorted(
            student_data.items(),
            key=lambda x: (len(x[1]['papers']), x[1]['total_citations']),
            reverse=True
        )

        return sorted_students

    def analyze_professor(self, professor):
        """分析单个教授"""
        print(f"\n{'='*60}")
        print(f"分析教授: {professor['name']}")
        print(f"{'='*60}")

        # 1. 搜索作者 ID
        author_info = self.search_author_id(professor['name'])

        if not author_info:
            return None

        author_id = author_info.get('authorId')
        print(f"  ✓ 找到 Author ID: {author_id}")

        # 2. 获取论文
        papers = self.get_author_papers(author_id, years=5)

        if not papers:
            print(f"  ⚠️ 未找到近5年的论文")
            return None

        print(f"  ✓ 找到 {len(papers)} 篇近5年的论文")

        # 3. 提取顶级论文
        top_papers = self.extract_top_papers(papers)

        if not top_papers:
            print(f"  ⚠️ 未找到顶级会议/期刊论文")
            return None

        print(f"  ✓ 其中顶级论文: {len(top_papers)} 篇")

        # 显示部分论文
        print(f"\n  部分顶级论文:")
        for paper in top_papers[:5]:
            print(f"    - ({paper['year']}) {paper['venue']} - {paper['title'][:80]}...")
            print(f"      引用: {paper['citationCount']}, 作者数: {len(paper['authors'])}")

        # 4. 分析学生贡献
        student_contributions = self.analyze_student_contributions(top_papers, professor['name'])

        if not student_contributions:
            print(f"\n  ⚠️ 未识别出合作学生")
            return None

        # 5. 显示前3名学生
        print(f"\n  顶级合作学生 (Top 3):")
        top_students = student_contributions[:3]

        student_data = []
        for idx, (student_name, info) in enumerate(top_students, 1):
            paper_count = len(info['papers'])
            total_citations = info['total_citations']
            venues = ', '.join(sorted(info['venues']))

            print(f"\n  #{idx} {student_name}")
            print(f"     论文数: {paper_count}")
            print(f"     总引用: {total_citations}")
            print(f"     会议/期刊: {venues}")
            print(f"     代表作:")
            for paper in info['papers'][:3]:
                print(f"       - ({paper['year']}) {paper['venue']} [{paper['citationCount']} 引用]")
                print(f"         {paper['title'][:100]}...")

            student_data.append({
                'rank': idx,
                'name': student_name,
                'paper_count': paper_count,
                'total_citations': total_citations,
                'venues': venues,
                'papers': json.dumps(info['papers'], ensure_ascii=False)
            })

        return {
            'professor': professor['name'],
            'professor_url': professor['url'],
            'author_id': author_id,
            'h_index': author_info.get('hIndex', 0),
            'citation_count': author_info.get('citationCount', 0),
            'total_papers_5years': len(papers),
            'top_papers_count': len(top_papers),
            'top_students': student_data
        }

    def analyze_all_professors(self):
        """分析所有教授"""
        professors = self.load_professors()

        print(f"\n{'='*80}")
        print(f"LAMDA 顶级人才分析（使用 Semantic Scholar Author API）")
        print(f"{'='*80}")
        print(f"\n总共 {len(professors)} 位教授")

        results = []

        for idx, professor in enumerate(professors, 1):
            print(f"\n进度: [{idx}/{len(professors)}]")

            try:
                result = self.analyze_professor(professor)
                if result:
                    results.append(result)

                # 礼貌延迟
                time.sleep(5)

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
            h_index = result['h_index']
            total_citations = result['citation_count']
            total_papers = result['total_papers_5years']
            top_papers_count = result['top_papers_count']
            students = result['top_students']

            for student in students:
                summary_data.append({
                    'professor': professor,
                    'professor_h_index': h_index,
                    'professor_total_citations': total_citations,
                    'professor_papers_5years': total_papers,
                    'professor_top_papers': top_papers_count,
                    'student_rank': student['rank'],
                    'student_name': student['name'],
                    'student_paper_count': student['paper_count'],
                    'student_citations': student['total_citations'],
                    'venues': student['venues'],
                    'papers_detail': student['papers']
                })

        # 保存结果
        if summary_data:
            df = pd.DataFrame(summary_data)
            output_file = f'LAMDA_author_api_analysis_{timestamp}.xlsx'
            df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"\n✓ 分析结果已保存到: {output_file}")

            # 保存简化版（不含论文详情）
            readable_df = df.drop(columns=['papers_detail'])
            readable_file = f'LAMDA_author_api_summary_{timestamp}.xlsx'
            readable_df.to_excel(readable_file, index=False, engine='openpyxl')
            print(f"✓ 简化报告已保存到: {readable_file}")

        # 打印统计
        self.print_summary(summary_data)

    def print_summary(self, summary_data):
        """打印分析汇总"""
        if not summary_data:
            return

        df = pd.DataFrame(summary_data)

        print(f"\n{'='*80}")
        print("【分析汇总】")
        print(f"{'='*80}")
        print(f"分析教授数: {len(df.groupby('professor'))}")
        print(f"识别出的顶级学生: {len(summary_data)}")

        # 全局 Top 10 学生（按论文数）
        print(f"\n🏆 全局 Top 10 学生 (按顶级论文数):")
        top_10 = df.nlargest(10, 'student_paper_count')
        for idx, row in top_10.iterrows():
            print(f"  {row['student_paper_count']} 篇 - {row['student_name']}")
            print(f"    导师: {row['professor']}")
            print(f"    总引用: {row['student_citations']}")
            print(f"    会议/期刊: {row['venues']}")

        # 按导师统计
        print(f"\n📊 按导师统计:")
        prof_stats = df.groupby('professor').agg({
            'student_paper_count': 'sum',
            'student_citations': 'sum',
            'student_name': 'count'
        }).rename(columns={'student_name': 'student_count'})

        prof_stats = prof_stats.sort_values('student_paper_count', ascending=False)

        for prof, row in prof_stats.head(5).iterrows():
            print(f"\n  {prof}:")
            print(f"    顶级学生数: {int(row['student_count'])}")
            print(f"    总顶级论文: {int(row['student_paper_count'])}")
            print(f"    总引用: {int(row['student_citations'])}")

        print(f"\n{'='*80}\n")


def main():
    analyzer = LamdaAuthorAPIAnalyzer('LAMDA.xlsx')
    results = analyzer.analyze_all_professors()
    analyzer.save_results(results)


if __name__ == '__main__':
    main()
