#!/usr/bin/env python3
"""
优先级邮箱提取器
优先处理真正需要邮箱的候选人
"""

import csv
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict
from redirect_utils import RedirectFollower


class PriorityEmailExtractor:
    """优先级邮箱提取器"""

    def __init__(self):
        self.redirect_follower = RedirectFollower()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def score_candidate_priority(self, candidate: Dict) -> int:
        """
        评分候选人处理优先级

        Returns:
            优先级分数 (0-100)，分数越高越优先
        """
        score = 0

        # 1. 无邮箱 → 最高优先级
        if not candidate.get('Email'):
            score += 50

        # 2. 无公司信息 → 加分
        if not candidate.get('公司'):
            score += 20

        # 3. 有 LAMDA 主页 → 可以尝试提取
        lamda_homepage = candidate.get('主页', '')
        if lamda_homepage and 'lamda.nju.edu.cn' in lamda_homepage:
            score += 15

        # 4. 有其他个人网站 → 可以尝试提取
        website = candidate.get('contact_blog', '')
        if website and 'github.com' not in website:
            score += 10

        # 5. 有 GitHub → 可以尝试提取
        if candidate.get('GitHub'):
            score += 5

        return score

    def extract_from_lamda_homepage(self, candidate: Dict) -> Dict:
        """从 LAMDA 主页深度提取联系信息"""
        result = {
            'email': '',
            'company': '',
            'position': '',
            'source': 'lamda_homepage',
            'final_url': '',
            'redirect_count': 0
        }

        lamda_url = candidate.get('主页', '')
        if not lamda_url or 'lamda.nju.edu.cn' not in lamda_url:
            return result

        try:
            # 跟随重定向
            redirect_result = self.redirect_follower.follow_redirects(lamda_url)
            final_url = redirect_result['final_url']

            result['final_url'] = final_url
            result['redirect_count'] = redirect_result['redirect_count']

            # 获取页面内容
            resp = self.session.get(final_url, timeout=30, verify=True)

            if resp.status_code != 200:
                return result

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 1. 提取邮箱
            if not candidate.get('Email'):  # 只有在原有邮箱为空时才提取
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                all_emails = re.findall(email_pattern, resp.text)

                valid_emails = [
                    e for e in all_emails
                    if 'noreply' not in e and
                       'github' not in e and
                       'example' not in e and
                       'localhost' not in e and
                       'test' not in e.lower() and
                       'w3.org' not in e and
                       '@2x' not in e
                ]

                if valid_emails:
                    # 去重，选择第一个
                    unique_emails = list(set(valid_emails))
                    result['email'] = unique_emails[0]

            # 2. 提取公司信息（如果还没有）
            if not candidate.get('公司'):
                text = soup.get_text()

                # 查找现任职信息
                patterns = [
                    r'(?:现任|目前|当前).{0,30}?([A-Z][A-Za-z\s&\-\.]{5,60})',
                    r'(?:现为|目前为).{0,30}?([A-Z][A-Za-z\s&\-\.]{5,60})',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        company = matches[0].strip()
                        if len(company) < 100:
                            result['company'] = company
                            break

        except Exception as e:
            print(f"    错误: {e}")

        return result

    def extract_from_personal_website(self, candidate: Dict) -> Dict:
        """从个人网站提取联系信息"""
        result = {
            'email': '',
            'company': '',
            'position': '',
            'source': 'personal_website',
            'final_url': '',
            'redirect_count': 0
        }

        website = candidate.get('contact_blog', '')
        if not website or 'github.com' in website:
            return result

        try:
            # 跟随重定向
            redirect_result = self.redirect_follower.follow_redirects(website)
            final_url = redirect_result['final_url']

            result['final_url'] = final_url
            result['redirect_count'] = redirect_result['redirect_count']

            # 获取页面内容
            resp = self.session.get(final_url, timeout=30, verify=True)

            if resp.status_code != 200:
                return result

            # 1. 提取邮箱
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            all_emails = re.findall(email_pattern, resp.text)

            valid_emails = [
                e for e in all_emails
                if 'noreply' not in e and
                   'github' not in e and
                   'example' not in e and
                   'localhost' not in e and
                   'test' not in e.lower() and
                   'w3.org' not in e
            ]

            if valid_emails:
                unique_emails = list(set(valid_emails))
                result['email'] = unique_emails[0]

            # 2. 提取公司信息
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 从 meta 标签
            meta_keywords = ['author', 'organization', 'company', 'affiliation']
            for meta_name in meta_keywords:
                meta_elem = soup.find('meta', {'name': meta_name})
                if meta_elem:
                    content = meta_elem.get('content', '').strip()
                    if content and len(content) < 100:
                        result['company'] = content
                        break

        except Exception as e:
            print(f"    错误: {e}")

        return result

    def process_candidates(self, input_csv: str, output_csv: str, limit: int = 50):
        """处理候选人，按优先级提取邮箱"""
        print("="*80)
        print("优先级邮箱提取")
        print("="*80)
        print()

        # 读取候选人
        candidates = []
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            candidates = list(reader)

        print(f"总候选人: {len(candidates)}")

        # 计算优先级分数
        for candidate in candidates:
            candidate['priority_score'] = self.score_candidate_priority(candidate)

        # 按优先级排序
        candidates.sort(key=lambda x: x['priority_score'], reverse=True)

        # 筛选高优先级候选人
        high_priority = [c for c in candidates if c['priority_score'] > 0]

        print(f"需要提取信息的候选人: {len(high_priority)}")
        print()

        # 统计
        stats = {
            'processed': 0,
            'emails_found': 0,
            'companies_found': 0,
            'lamda_homepage_extracted': 0,
            'personal_website_extracted': 0
        }

        # 处理高优先级候选人
        process_limit = limit if limit else len(high_priority)

        for i, candidate in enumerate(high_priority[:process_limit], 1):
            name = candidate['姓名']
            score = candidate['priority_score']

            print(f"[{i}/{process_limit}] {name} | 优先级: {score}")
            print(f"  现有邮箱: {candidate.get('Email') or '无'}")
            print(f"  现有公司: {candidate.get('公司') or '无'}")

            # 1. 从 LAMDA 主页提取
            lamda_homepage = candidate.get('主页', '')
            if lamda_homepage and 'lamda.nju.edu.cn' in lamda_homepage:
                print(f"  → 从 LAMDA 主页提取")
                lamda_result = self.extract_from_lamda_homepage(candidate)

                if lamda_result['email']:
                    candidate['email_priority'] = lamda_result['email']
                    candidate['email_priority_source'] = lamda_result['source']
                    stats['emails_found'] += 1
                    print(f"    ✓ 邮箱: {lamda_result['email']}")

                if lamda_result['company']:
                    candidate['公司_priority'] = lamda_result['company']
                    stats['companies_found'] += 1
                    print(f"    ✓ 公司: {lamda_result['company']}")

                stats['lamda_homepage_extracted'] += 1

            # 2. 从个人网站提取
            website = candidate.get('contact_blog', '')
            if website and 'github.com' not in website:
                print(f"  → 从个人网站提取")
                web_result = self.extract_from_personal_website(candidate)

                if web_result['email'] and not candidate.get('email_priority'):
                    candidate['email_priority'] = web_result['email']
                    candidate['email_priority_source'] = web_result['source']
                    stats['emails_found'] += 1
                    print(f"    ✓ 邮箱: {web_result['email']}")

                if web_result['company'] and not candidate.get('公司_priority'):
                    candidate['公司_priority'] = web_result['company']
                    stats['companies_found'] += 1
                    print(f"    ✓ 公司: {web_result['company']}")

                stats['personal_website_extracted'] += 1

            stats['processed'] += 1
            print()

        # 保存结果
        print("="*80)
        print("保存结果...")
        print()

        # 保存新字段到现有字段
        for c in candidates:
            # 将优先级提取的结果合并到主字段
            if c.get('email_priority') and not c.get('Email'):
                c['Email'] = c['email_priority']

            if c.get('公司_priority') and not c.get('公司'):
                c['公司'] = c['公司_priority']

            # 移除临时字段
            c.pop('priority_score', None)
            c.pop('email_priority', None)
            c.pop('email_priority_source', None)
            c.pop('公司_priority', None)
            c.pop('Email_source', None)  # 移除如果不存在

        fieldnames = list(candidates[0].keys())
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)

        # 打印统计
        print("="*80)
        print("提取统计")
        print("="*80)
        print(f"处理候选人: {stats['processed']}")
        print(f"找到邮箱: {stats['emails_found']}")
        print(f"找到公司: {stats['companies_found']}")
        print(f"LAMDA 主页提取: {stats['lamda_homepage_extracted']}")
        print(f"个人网站提取: {stats['personal_website_extracted']}")
        print()

        # 显示新找到的邮箱
        new_emails = [c for c in candidates if c.get('email_priority')]
        if new_emails:
            print("🏆 新提取的邮箱:")
            for c in new_emails[:10]:
                source = c.get('email_priority_source', 'unknown')
                email = c.get('email_priority', '')
                print(f"  • {c['姓名']:15s} | {email:30s} | {source}")

            if len(new_emails) > 10:
                print(f"  ... 还有 {len(new_emails) - 10} 个")

        print()
        print(f"✓ 结果已保存到: {output_csv}")
        print()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='优先级邮箱提取器')
    parser.add_argument('--input', type=str, default='lamda_candidates_final_enriched.csv',
                       help='输入 CSV 文件')
    parser.add_argument('--output', type=str, default='lamda_candidates_priority_enriched.csv',
                       help='输出 CSV 文件')
    parser.add_argument('--limit', type=int, default=None,
                       help='处理数量限制（默认：全部）')

    args = parser.parse_args()

    extractor = PriorityEmailExtractor()
    extractor.process_candidates(args.input, args.output, args.limit)


if __name__ == '__main__':
    main()
