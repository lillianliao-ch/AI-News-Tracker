#!/usr/bin/env python3
"""
测试 Semantic Scholar Author API
"""

import requests
import json

def test_author_api():
    """测试 Author API"""

    # 测试周志华教授
    author_name = "Zhi-Hua Zhou"

    # 1. 搜索作者
    search_url = "https://api.semanticscholar.org/graph/v1/author/search"

    params = {
        'query': f'{author_name} Nanjing University',
        'fields': 'authorId,name,papers,hIndex,citationCount,aliases',
        'limit': 5
    }

    print(f"搜索作者: {author_name}")
    response = requests.get(search_url, params=params, timeout=15)

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n找到 {len(data.get('data', []))} 个匹配的作者")

        for author in data.get('data', []):
            print(f"\nAuthor ID: {author.get('authorId')}")
            print(f"Name: {author.get('name')}")
            print(f"Aliases: {author.get('aliases', [])}")
            print(f"H-Index: {author.get('hIndex')}")
            print(f"Citation Count: {author.get('citationCount')}")

            # 获取该作者的论文
            author_id = author.get('authorId')
            if author_id:
                print(f"\n获取 {author_id} 的论文...")

                papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
                papers_params = {
                    'fields': 'papers.title,papers.year,papers.venue,papers.citationCount,papers.authors,papers.publicationTypes,papers.journal',
                    'limit': 20
                }

                papers_response = requests.get(papers_url, params=papers_params, timeout=15)

                if papers_response.status_code == 200:
                    papers_data = papers_response.json()
                    papers = papers_data.get('papers', [])

                    # 过滤近5年的顶级论文
                    top_venues = ['NeurIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI', 'KDD']

                    top_papers = []
                    for paper in papers[:10]:
                        venue = paper.get('venue', '')
                        year = paper.get('year')
                        if venue and year and year >= 2020:
                            if any(v.lower() in venue.lower() for v in top_venues):
                                top_papers.append(paper)

                    print(f"\n找到 {len(top_papers)} 篇近5年的顶级论文:")
                    for paper in top_papers[:5]:
                        print(f"  - ({paper.get('year')}) {paper.get('venue')}")
                        print(f"    {paper.get('title', '')[:80]}...")
                        print(f"    引用: {paper.get('citationCount', 0)}")

                        # 显示作者
                        authors = paper.get('authors', [])
                        author_names = [a.get('name', '') for a in authors[:5]]
                        print(f"    作者: {', '.join(author_names)}")
                        print()

    else:
        print(f"错误: {response.text}")

if __name__ == '__main__':
    test_author_api()
