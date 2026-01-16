#!/usr/bin/env python3
"""
LAMDA 顶级人才分析
通过 Semantic Scholar API 查找教授的顶级论文，识别顶尖学生
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import json
from collections import Counter

class LamdaTopTalentAnalyzer:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.semantic_scholar_api = "https://api.semanticscholar.org/graph/v1"
        self.results = []

        # 顶级 AI 会议和期刊列表
        self.top_venues = [
            # 顶级会议
            'NeurIPS', 'NeurIPS',
            'ICML',
            'ICLR',
            'AAAI',
            'IJCAI',
            'ACL',
            'EMNLP',
            'CVPR',
            'ICCV',
            'ECCV',
            'KDD',
            'WWW',
            'SIGIR',

            # 顶级期刊
            'Journal of Machine Learning Research',
            'Machine Learning',
            'IEEE Transactions on Pattern Analysis and Machine Intelligence',
            'Artificial Intelligence',
            'Journal of Artificial Intelligence Research',
            'Nature Machine Intelligence',
            'Science',
            'Nature'
        ]

    def load_professors(self):
        """从 Excel 加载教授信息"""
        df = pd.read_excel(self.excel_path)

        # 提取教授信息
        prof_df = df[['Professor', 'Professor_URL']].drop_duplicates()
        prof_df = prof_df.dropna(subset=['Professor_URL'])

        professors = []
        for _, row in prof_df.iterrows():
            # 过滤无效 URL
            if pd.notna(row['Professor_URL']) and str(row['Professor_URL']).startswith('http'):
                professors.append({
                    'name': row['Professor'],
                    'url': row['Professor_URL']
                })

        return professors

    def search_papers_by_author(self, author_name, years=5, max_retries=3):
        """
        通过 Semantic Scholar API 搜索作者论文
        years: 最近多少年
        max_retries: 最大重试次数
        """
        for attempt in range(max_retries):
            try:
                # 构建查询 - 添加 Nanjing University 提高准确性
                query = f'"{author_name}" Nanjing University'
                url = f"{self.semantic_scholar_api}/paper/search"

                params = {
                    'query': query,
                    'fields': 'paperId,title,authors,year,venue,citationCount,publicationTypes',
                    'limit': 100,
                    'year': f"{datetime.now().year - years}-"
                }

                print(f"  查询 {author_name} 的论文... (尝试 {attempt + 1}/{max_retries})")
                response = requests.get(url, params=params, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    papers = data.get('data', [])

                    # 过滤顶级刊物的论文
                    top_papers = []
                    for paper in papers:
                        venue = paper.get('venue', '')
                        year = paper.get('year', 0)
                        citation_count = paper.get('citationCount', 0)

                        # 检查是否是顶级刊物
                        is_top_venue = any(top_venue.lower() in str(venue).lower()
                                         for top_venue in self.top_venues)

                        if is_top_venue and year >= (datetime.now().year - years):
                            top_papers.append({
                                'paperId': paper.get('paperId'),
                                'title': paper.get('title'),
                                'year': year,
                                'venue': venue,
                                'citationCount': citation_count,
                                'authors': paper.get('authors', [])
                            })

                    return top_papers

                elif response.status_code == 429:
                    # 限流，等待更长时间
                    wait_time = (attempt + 1) * 5
                    print(f"    ⚠️ API 限流，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue

                else:
                    print(f"    ⚠️ API 请求失败: {response.status_code}")
                    return []

            except Exception as e:
                print(f"    ❌ 查询出错: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return []

        return []

    def extract_student_authors(self, papers, professor_name):
        """
        从论文中提取学生作者（排除教授本人）
        返回学生及其贡献统计
        """
        student_data = {}

        for paper in papers:
            authors = paper.get('authors', [])
            year = paper.get('year')
            venue = paper.get('venue')
            title = paper.get('title')
            citation_count = paper.get('citationCount', 0)

            for author_info in authors:
                author_name = author_info.get('name', '')

                # 排除教授本人
                if professor_name.lower() not in author_name.lower():
                    # 初始化或更新该学生的统计
                    if author_name not in student_data:
                        student_data[author_name] = {
                            'papers': 0,
                            'citations': 0,
                            'details': []
                        }

                    # 统计该学生的贡献
                    student_data[author_name]['papers'] += 1
                    student_data[author_name]['citations'] += citation_count
                    student_data[author_name]['details'].append({
                        'title': title,
                        'year': year,
                        'venue': venue,
                        'citationCount': citation_count
                    })

        # 转换为排序的列表
        sorted_students = sorted(
            student_data.items(),
            key=lambda x: (x[1]['papers'], x[1]['citations']),
            reverse=True
        )

        return sorted_students

    def get_author_details(self, author_name):
        """
        获取作者的详细信息（包括学位状态）
        """
        # 这里可以进一步扩展，查询作者的个人页面
        # 目前先返回基础信息
        return {
            'name': author_name,
            'degree_status': 'Unknown',  # PhD/Master/Unknown
            'institution': 'Unknown'
        }

    def analyze_professor(self, professor):
        """分析单个教授的顶级论文和学生"""
        print(f"\n{'='*60}")
        print(f"分析教授: {professor['name']}")
        print(f"{'='*60}")

        # 1. 搜索该教授的顶级论文
        papers = self.search_papers_by_author(professor['name'], years=5)

        if not papers:
            print(f"  ⚠️ 未找到近5年的顶级刊物论文")
            return None

        print(f"  ✓ 找到 {len(papers)} 篇顶级刊物论文")

        # 显示部分论文
        print(f"\n  部分论文:")
        for paper in papers[:5]:
            print(f"    - {paper['title']} ({paper['year']}) - {paper['venue']}")
            print(f"      引用: {paper['citationCount']}, 作者: {[a['name'] for a in paper['authors'][:5]]}")

        # 2. 提取学生作者
        student_contributions = self.extract_student_authors(papers, professor['name'])

        if not student_contributions:
            print(f"\n  ⚠️ 未识别出合作学生")
            return None

        # 3. 找出贡献最大的前3名学生
        top_students = student_contributions[:3]

        print(f"\n  顶级合作学生 (Top 3):")
        student_data = []

        for idx, (student_name, contribution) in enumerate(top_students, 1):
            # 计算总贡献
            total_papers = contribution['papers']
            total_citations = contribution['citations']

            print(f"\n  #{idx} {student_name}")
            print(f"     论文数: {total_papers}")
            print(f"     总引用: {total_citations}")
            print(f"     代表作:")
            for detail in contribution['details'][:3]:
                print(f"       - {detail['title']} ({detail['year']}) - {detail['venue']} [{detail['citationCount']} 引用]")

            student_data.append({
                'rank': idx,
                'student_name': student_name,
                'professor': professor['name'],
                'total_papers': total_papers,
                'total_citations': total_citations,
                'papers': json.dumps(contribution['details'], ensure_ascii=False)
            })

        return {
            'professor': professor['name'],
            'professor_url': professor['url'],
            'total_papers': len(papers),
            'top_students': student_data
        }

    def analyze_all_professors(self):
        """分析所有教授"""
        professors = self.load_professors()

        print(f"\n{'='*80}")
        print(f"LAMDA 顶级人才分析")
        print(f"{'='*80}")
        print(f"\n总共 {len(professors)} 位教授")

        all_results = []

        for idx, professor in enumerate(professors, 1):
            print(f"\n进度: [{idx}/{len(professors)}]")

            try:
                result = self.analyze_professor(professor)
                if result and result.get('top_students'):
                    all_results.append(result)

                # 礼貌延迟
                time.sleep(5)

            except Exception as e:
                print(f"  ❌ 分析出错: {str(e)}")
                continue

        return all_results

    def save_results(self, results):
        """保存分析结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if not results:
            print("\n⚠️ 没有结果可保存")
            return

        # 1. 创建汇总报告
        all_students = []

        for result in results:
            professor = result['professor']
            professor_url = result['professor_url']
            total_papers = result['total_papers']

            for student in result['top_students']:
                all_students.append({
                    'rank_in_professor': student['rank'],
                    'professor': professor,
                    'professor_url': professor_url,
                    'professor_total_papers': total_papers,
                    'student_name': student['student_name'],
                    'total_papers': student['total_papers'],
                    'total_citations': student['total_citations'],
                    'papers_detail': student['papers']
                })

        # 2. 保存完整结果
        df = pd.DataFrame(all_students)
        output_file = f'LAMDA_top_talents_analysis_{timestamp}.xlsx'
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n✓ 分析结果已保存到: {output_file}")

        # 3. 保存可读性更好的版本（不含论文详情）
        readable_df = df.drop(columns=['papers_detail'])
        readable_file = f'LAMDA_top_talents_summary_{timestamp}.xlsx'
        readable_df.to_excel(readable_file, index=False, engine='openpyxl')
        print(f"✓ 简化报告已保存到: {readable_file}")

        # 4. 打印汇总统计
        self.print_summary(all_students)

    def print_summary(self, all_students):
        """打印分析汇总"""
        print(f"\n{'='*80}")
        print("【分析汇总】")
        print(f"{'='*80}")

        # 按总引用数排序，找出全局顶级学生
        df = pd.DataFrame(all_students)

        print(f"\n总共识别出 {len(all_students)} 位顶级合作学生")
        print(f"来自 {len(df)} 位教授")

        # 全局 Top 10 学生（按总引用）
        print(f"\n🏆 全局 Top 10 学生 (按总引用):")
        top_10 = df.nlargest(10, 'total_citations')
        for idx, row in top_10.iterrows():
            print(f"  {row['student_name']}: {row['total_citations']} 引用, {row['total_papers']} 篇论文")
            print(f"    导师: {row['professor']}")

        print(f"\n{'='*80}\n")


def main():
    # 使用方式
    analyzer = LamdaTopTalentAnalyzer('LAMDA.xlsx')
    results = analyzer.analyze_all_professors()
    analyzer.save_results(results)


if __name__ == '__main__':
    main()
