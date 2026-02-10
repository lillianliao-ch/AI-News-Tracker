# 项目定位澄清 - 南大学生深度挖掘系统

**日期**: 2025-01-27
**核心目标**: 从南大学生列表中发现和评估优质 AI 人才

---

## 🎯 项目本质对比

### GitHub Miner vs LAMDA Scraper

| 维度 | GitHub Miner | LAMDA Scraper (你的项目) |
|------|-------------|------------------------|
| **起点** | GitHub 用户 (Neal12332) | 南大学生列表 |
| **发现路径** | GitHub → Following → 评分 | 学生主页 → 深度挖掘 → 评分 |
| **核心目标** | ⭐ **发现 AI 人才** | ⭐ **评估学生质量** |
| **数据源** | GitHub API | 个人网站 + 多源数据 |
| **关键信息** | 技术栈、活跃度 | 研究方向、论文、联系方式 |
| **最终输出** | Tier A/B/C 候选人 | Tier A/B/C 候选人 |

### 核心洞察 ⭐⭐⭐

**两个项目的目标完全一样**：发现和评估优质 AI 人才！

只是**起点不同**，但**需要的能力高度重叠**：
1. ✅ 多源数据整合
2. ✅ 综合评分系统
3. ✅ 候选人分层分类
4. ✅ 联系方式收集

---

## 📊 你真正需要的信息

### 完整的候选人画像

```python
{
  # ========== 基本信息 ==========
  "基本信息": {
    "姓名": "张三",
    "南大身份": "博士生/硕士生/校友",
    "入学年份": "2019",
    "导师": "周志华教授",
    "实验室": "LAMDA"
  },

  # ========== 研究方向 (最重要) ==========
  "研究方向": {
    "主要方向": ["机器学习", "深度学习", "强化学习"],
    "具体领域": ["大模型训练", "推理优化", "模型压缩"],
    "研究兴趣": "如何高效训练和部署大规模语言模型",
    "来源": "个人主页 / 论文 / 导师描述"
  },

  # ========== 学术成果 (关键指标) ==========
  "学术成果": {
    "论文列表": [
      {
        "标题": "Efficient LLM Training with ...",
        "作者": "张三, 李四, ...",
        "发表年份": 2023,
        "发表 venue": "NeurIPS",
        "venue 类型": "顶会 (CCF-A)",
        "引用数": 156,
        "链接": "https://..."
      },
      ...
    ],
    "总论文数": 15,
    "顶会论文数": 5,  # NeurIPS/ICML/ICLR/ACL/EMNLP
    "一作论文数": 3,
    "h-index": 8,
    "Google Scholar 链接": "https://scholar.google.com/...",
    "DBLP 链接": "https://dblp.org/..."
  },

  # ========== 技术能力 (GitHub) ==========
  "技术能力": {
    "GitHub": "https://github.com/zhangsan",
    "GitHub 用户名": "zhangsan",
    "public_repos": 25,
    "total_stars": 1234,
    "followers": 234,
    "主要项目": [
      {
        "name": "fast-llm",
        "description": "高效的 LLM 训练框架",
        "stars": 567,
        "forks": 89,
        "language": "Python",
        "topics": ["deep-learning", "llm", "training"]
      },
      ...
    ],
    "技术栈": ["Python", "PyTorch", "CUDA", "C++"],
    "贡献质量": "高（有知名项目）"
  },

  # ========== 联系方式 (关键) ==========
  "联系方式": {
    "邮箱（优先级1）": [
      {
        "邮箱": "zhangsan@nju.edu.cn",
        "来源": "个人主页",
        "类型": "学校邮箱",
        "有效性": "✅ 已验证"
      },
      {
        "邮箱": "zhangsan@gmail.com",
        "来源": "GitHub",
        "类型": "个人邮箱",
        "有效性": "✅ 已验证"
      }
    ],
    "LinkedIn（优先级2）": "https://linkedin.com/in/zhangsan",
    "个人网站（优先级3）": "https://zhangsan.xyz",
    "GitHub（优先级4）": "https://github.com/zhangsan",
    "其他": ["Twitter", "知乎", "豆瓣"]
  },

  # ========== 职业经历（如果有）==========
  "职业经历": [
    {
      "公司": "字节跳动",
      "职位": "算法工程师实习生",
      "时间": "2023.06 - 2023.09",
      "部门": "AI Lab"
    },
    {
      "公司": "微软亚洲研究院",
      "职位": "研究实习生",
      "时间": "2022.07 - 2022.12",
      "导师": "..."
    }
  ],

  # ========== 综合评分 ==========
  "综合评分": {
    "总分": 87.5,
    "等级": "A",
    "学术能力": {
      "得分": 28/30,
      "细分": {
        "顶会论文": 10/10,  # 5篇 NeurIPS
        "h-index": 8/10,
        "引用数": 7/10,
        "研究活跃度": 3/10
      }
    },
    "技术能力": {
      "得分": 23/25,
      "细分": {
        "开源影响力": 12/15,  # stars > 1000
        "技术栈深度": 8/10,
        "项目质量": 3/5
      }
    },
    "实践经验": {
      "得分": 18/20,
      "细分": {
        "实习经历": 10/12,  # 字节+MSRA
        "项目经验": 8/8
      }
    },
    "可联系性": {
      "得分": 14/15,
      "细分": {
        "联系方式完整性": 10/10,  # 邮箱+LinkedIn+网站
        "响应度": 4/5
      }
    },
    "发展潜力": {
      "得分": 9/10,
      "细分": {
        "导师声誉": 5/5,
        "研究方向热度": 4/5
      }
    }
  },

  # ========== 推荐理由 ==========
  "推荐理由": [
    "⭐ NeurIPS 2023 一作论文",
    "⭐ GitHub 项目 stars > 1000",
    "⭐ 字节跳动 + MSRA 实习经历",
    "⭐ 导师为周志华（LAMDA 主任）",
    "⭐ 研究方向：大模型训练优化（当前热点）"
  ],

  # ========== 匹配建议 ==========
  "匹配建议": {
    "适合职位": [
      {
        "职位": "LLM 工程师",
        "匹配度": 95%,
        "推荐公司": ["字节跳动", "阿里巴巴", "腾讯"]
      },
      {
        "职位": "AI 研究员",
        "匹配度": 90%,
        "推荐公司": ["微软亚洲研究院", "Google DeepMind", "OpenAI"]
      }
    ],
    "不适合职位": [
      {
        "职位": "前端工程师",
        "原因": "技术栈不匹配"
      }
    ]
  }
}
```

---

## 🔧 关键能力需求

### 1. 深度信息提取 ⭐⭐⭐

#### 从个人主页提取

```python
# deep_scraper.py

class DeepScraper:
    """深度信息提取器"""

    def scrape_student_homepage(self, url):
        """深度挖掘学生个人主页"""
        # 1. 基本信息
        basic_info = self.extract_basic_info(url)

        # 2. 研究方向
        research_interests = self.extract_research_interests(url)

        # 3. 论文列表（从主页链接到 Google Scholar）
        papers = self.extract_papers_from_homepage(url)

        # 4. 社交媒体链接
        social_links = self.extract_social_links(url)

        # 5. 联系方式
        contact_info = self.extract_contact_info(url)

        return {
            'basic_info': basic_info,
            'research_interests': research_interests,
            'papers': papers,
            'social_links': social_links,
            'contact_info': contact_info
        }

    def extract_research_interests(self, url):
        """提取研究方向"""
        soup = self.get_soup(url)

        # 研究方向通常在以下位置：
        locations = [
            soup.find('div', class_='research-interests'),
            soup.find('section', id='research'),
            soup.find('div', class_='bio'),
            soup.find_all('div', class_='interest')
        ]

        interests = []

        for location in locations:
            if location:
                text = location.get_text()
                # 提取关键词
                keywords = self.extract_keywords(text)
                interests.extend(keywords)

        return list(set(interests))

    def extract_papers_from_homepage(self, url):
        """从主页提取论文"""
        soup = self.get_soup(url)

        papers = []

        # 1. 查找 Google Scholar 链接
        scholar_links = soup.find_all('a', href=lambda x: x and 'scholar.google' in x)

        if scholar_links:
            scholar_url = scholar_links[0]['href']
            # 从 Google Scholar 提取论文
            papers.extend(self.extract_from_google_scholar(scholar_url))

        # 2. 查找论文列表 section
        papers_section = soup.find('div', class_='publications')
        if papers_section:
            paper_items = papers_section.find_all('li', class_='paper')
            for item in paper_items:
                papers.append(self.parse_paper_item(item))

        # 3. 查找 DBLP 链接
        dblp_links = soup.find_all('a', href=lambda x: x and 'dblp.org' in x)
        if dblp_links:
            dblp_url = dblp_links[0]['href']
            papers.extend(self.extract_from_dblp(dblp_url))

        return papers

    def extract_social_links(self, url):
        """提取社交媒体链接"""
        soup = self.get_soup(url)

        links = {}

        # LinkedIn
        linkedin = soup.find('a', href=lambda x: x and 'linkedin.com' in x)
        if linkedin:
            links['linkedin'] = linkedin['href']

        # GitHub
        github = soup.find('a', href=lambda x: x and 'github.com' in x)
        if github:
            links['github'] = github['href']

        # Twitter
        twitter = soup.find('a', href=lambda x: x and 'twitter.com' in x)
        if twitter:
            links['twitter'] = twitter['href']

        # 知乎
        zhihu = soup.find('a', href=lambda x: x and 'zhihu.com' in x)
        if zhihu:
            links['zhihu'] = zhihu['href']

        return links

    def extract_contact_info(self, url):
        """提取联系方式"""
        soup = self.get_soup(url)

        contacts = {
            'emails': [],
            'phones': []
        }

        # 1. 明文邮箱
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, soup.get_text())

        # 过滤
        valid_emails = [
            e for e in emails
            if 'noreply' not in e and 'github' not in e
        ]
        contacts['emails'] = list(set(valid_emails))

        # 2. Cloudflare 保护邮箱
        cloudflare_links = soup.find_all('a', href=lambda x: x and '/cdn-cgi/l/email-protection' in x)
        for link in cloudflare_links:
            decoded = self.decode_cloudflare(link['href'])
            if decoded:
                contacts['emails'].append(decoded)

        return contacts
```

### 2. Google Scholar 提取 ⭐⭐⭐

```python
# google_scholar_extractor.py

class GoogleScholarExtractor:
    """Google Scholar 提取器"""

    def extract_papers(self, scholar_url or name):
        """提取论文列表"""
        # 方法1: 直接从 Scholar URL
        if scholar_url:
            papers = self.scrape_scholar_profile(scholar_url)
        else:
            # 方法2: 通过名字搜索
            papers = self.search_and_extract(name)

        # 3. 补充 DBLP 数据
        papers = self.enrich_with_dblp(papers)

        return papers

    def scrape_scholar_profile(self, scholar_url):
        """抓取 Scholar 个人主页"""
        import requests
        from bs4 import BeautifulSoup

        resp = requests.get(scholar_url)
        soup = BeautifulSoup(resp.text, 'html.parser')

        papers = []

        # 论文条目
        paper_rows = soup.find_all('tr', class_='gsc_a_tr')
        for row in paper_rows:
            paper = {
                '标题': row.find('a', class_='gsc_a_at').get_text(),
                '作者': row.find('div', class_='gs_gray').get_text(),
                '年份': row.find('span', class_='gsc_a_h').get_text(),
                '引用数': row.find('a', class_='gsc_a_ac').get_text(),
                'venue': row.find('span', class_='gsc_a_h').get_text()
            }
            papers.append(paper)

        return papers

    def enrich_with_dblp(self, papers):
        """用 DBLP 数据增强"""
        import requests

        enriched_papers = []

        for paper in papers:
            # 通过标题搜索 DBLP
            search_url = f"https://dblp.org/search?q={paper['标题']}"
            resp = requests.get(search_url)

            # 提取 venue 类型（CCF A/B/C）
            venue_type = self.extract_venue_type(resp.text)

            paper['venue_type'] = venue_type
            enriched_papers.append(paper)

        return enriched_papers

    def extract_venue_type(self, html):
        """提取 venue 类型"""
        # CCF A 类会议
        ccf_a = ['NeurIPS', 'ICML', 'ICLR', 'ACL', 'EMNLP', 'CVPR', 'ICCV', 'AAAI']
        for conf in ccf_a:
            if conf in html:
                return 'CCF-A'

        # CCF B 类会议
        ccf_b = ['IJCAI', 'AAAI', 'ECCV', 'NAACL']
        for conf in ccf_b:
            if conf in html:
                return 'CCF-B'

        return 'Unknown'
```

### 3. GitHub 深度分析 ⭐⭐

```python
# github_deep_analyzer.py

class GitHubDeepAnalyzer:
    """GitHub 深度分析器"""

    def analyze_github_profile(self, github_url):
        """深度分析 GitHub"""
        # 1. 基础信息
        profile = self.get_profile(github_url)

        # 2. 仓库分析
        repos = self.get_repos(github_url)

        # 3. 贡献质量
        contribution_quality = self.assess_contribution_quality(repos)

        # 4. 技术栈
        tech_stack = self.extract_tech_stack(repos)

        # 5. 活跃度
        activity = self.analyze_activity(github_url)

        return {
            'profile': profile,
            'repos': repos,
            'contribution_quality': contribution_quality,
            'tech_stack': tech_stack,
            'activity': activity
        }

    def assess_contribution_quality(self, repos):
        """评估贡献质量"""
        quality_score = 0
        signals = []

        # 总 stars
        total_stars = sum(r.get('stargazers_count', 0) for r in repos)
        if total_stars >= 1000:
            quality_score += 15
            signals.append(f'total_stars > 1000: {total_stars}')
        elif total_stars >= 100:
            quality_score += 10
            signals.append(f'total_stars > 100: {total_stars}')

        # 知名项目
        for repo in repos:
            if repo['stargazers_count'] >= 500:
                quality_score += 10
                signals.append(f'知名项目: {repo["name"]} ({repo["stargazers_count"]} stars)')

        # Forks
        total_forks = sum(r.get('forks_count', 0) for r in repos)
        if total_forks >= 100:
            quality_score += 5
            signals.append(f'total_forks > 100: {total_forks}')

        return {
            'score': min(quality_score, 25),
            'signals': signals
        }

    def extract_tech_stack(self, repos):
        """提取技术栈"""
        languages = Counter()
        topics = Counter()

        for repo in repos:
            # 语言
            lang = repo.get('language')
            if lang:
                languages[lang] += 1

            # Topics
            for topic in repo.get('topics', []):
                topics[topic] += 1

        return {
            'languages': dict(languages.most_common(10)),
            'topics': dict(topics.most_common(20))
        }

    def analyze_activity(self, github_url):
        """分析活跃度"""
        # 最近 30 天的 commits
        recent_commits = self.get_recent_commits(github_url, days=30)

        # 最近一次更新
        latest_update = self.get_latest_update(github_url)

        activity_score = 0

        if len(recent_commits) >= 10:
            activity_score += 5
        elif len(recent_commits) >= 5:
            activity_score += 3

        # 如果最近一周有更新
        days_since_update = (datetime.now() - latest_update).days
        if days_since_update <= 7:
            activity_score += 5
        elif days_since_update <= 30:
            activity_score += 3

        return {
            'score': activity_score,
            'recent_commits': len(recent_commits),
            'days_since_update': days_since_update
        }
```

### 4. 综合评分系统 ⭐⭐⭐

```python
# comprehensive_scorer.py

class ComprehensiveScorer:
    """综合评分系统（适合南大学生）"""

    def calculate_score(self, candidate):
        """计算综合评分"""
        scores = {}

        # 1. 学术能力 (30分) - 南大学生最重要
        scores['academic'] = self.score_academic(candidate)

        # 2. 技术能力 (25分)
        scores['technical'] = self.score_technical(candidate)

        # 3. 实践经验 (20分)
        scores['experience'] = self.score_experience(candidate)

        # 4. 可联系性 (15分)
        scores['contactability'] = self.score_contactability(candidate)

        # 5. 发展潜力 (10分)
        scores['potential'] = self.score_potential(candidate)

        total_score = sum(scores.values())

        # 确定等级
        tier = self.get_tier(total_score)

        # 提取信号
        signals = self.extract_signals(candidate)

        # 生成推荐理由
        reasons = self.generate_recommendation_reasons(signals)

        return {
            'total_score': round(total_score, 2),
            'tier': tier,
            'scores': scores,
            'signals': signals,
            'recommendation_reasons': reasons
        }

    def score_academic(self, candidate):
        """学术能力评分（30分）"""
        score = 0
        signals = []

        # 论文数量和质量
        papers = candidate.get('papers', [])
        total_papers = len(papers)
        top_conf_papers = len([p for p in papers if p.get('venue_type') == 'CCF-A'])

        # 顶会论文 (最重要)
        if top_conf_papers >= 5:
            score += 15
            signals.append(f'顶会论文: {top_conf_papers}篇')
        elif top_conf_papers >= 3:
            score += 12
            signals.append(f'顶会论文: {top_conf_papers}篇')
        elif top_conf_papers >= 1:
            score += 8
            signals.append(f'顶会论文: {top_conf_papers}篇')

        # h-index
        h_index = candidate.get('h_index', 0)
        if h_index >= 10:
            score += 10
            signals.append(f'h-index: {h_index}')
        elif h_index >= 5:
            score += 7
            signals.append(f'h-index: {h_index}')
        elif h_index >= 2:
            score += 4

        # Google Scholar 引用
        citations = candidate.get('total_citations', 0)
        if citations >= 500:
            score += 5
            signals.append(f'引用数: {citations}')

        return min(score, 30), signals

    def score_technical(self, candidate):
        """技术能力评分（25分）"""
        score = 0
        signals = []

        github_data = candidate.get('github_data', {})

        # GitHub 影响
        total_stars = github_data.get('total_stars', 0)
        if total_stars >= 1000:
            score += 12
            signals.append(f'GitHub stars: {total_stars}')
        elif total_stars >= 100:
            score += 8
            signals.append(f'GitHub stars: {total_stars}')

        # 技术栈深度
        tech_stack = github_data.get('tech_stack', {})
        main_language = tech_stack.get('languages', {}).get('Python', 0)

        if main_language >= 10:  # 10个以上 Python 项目
            score += 8
            signals.append('Python 专家')

        # 开源项目质量
        if any(r['stargazers_count'] >= 500 for r in github_data.get('repos', [])):
            score += 5
            signals.append('有知名开源项目')

        return min(score, 25), signals

    def score_experience(self, candidate):
        """实践经验评分（20分）"""
        score = 0
        signals = []

        experiences = candidate.get('experiences', [])

        # 大厂实习
        top_companies = ['字节跳动', '阿里巴巴', '腾讯', '微软', 'Google', 'Meta', 'Amazon']
        for exp in experiences:
            company = exp.get('公司', '')
            for top_company in top_companies:
                if top_company.lower() in company.lower():
                    score += 10
                    signals.append(f'大厂实习: {company}')
                    break

        # 实习数量
        if len(experiences) >= 3:
            score += 5
            signals.append(f'实习经历: {len(experiences)}段')

        # 项目经验
        if candidate.get('has_projects'):
            score += 5
            signals.append('有项目经验')

        return min(score, 20), signals

    def score_contactability(self, candidate):
        """可联系性评分（15分）"""
        score = 0
        signals = []

        contacts = candidate.get('contacts', {})

        # 邮箱（最重要）
        if contacts.get('emails'):
            score += 10
            signals.append(f'邮箱: {len(contacts["emails"])}个')

        # LinkedIn
        if contacts.get('linkedin'):
            score += 3
            signals.append('有 LinkedIn')

        # 个人网站
        if contacts.get('website'):
            score += 2
            signals.append('有个人网站')

        return min(score, 15), signals

    def score_potential(self, candidate):
        """发展潜力评分（10分）"""
        score = 0
        signals = []

        # 导师声誉
        advisor = candidate.get('advisor', '')
        top_advisors = ['周志华', '李航', '周志华', '罗杰', '陈力']
        for top_advisor in top_advisors:
            if top_advisor in advisor:
                score += 5
                signals.append(f'导师: {advisor}')
                break

        # 研究方向热度
        research_interests = candidate.get('research_interests', [])
        hot_topics = ['llm', 'transformer', 'diffusion', 'reinforcement learning', '大模型']

        for hot_topic in hot_topics:
            if any(hot_topic in interest.lower() for interest in research_interests):
                score += 5
                signals.append(f'热点方向: {hot_topic}')
                break

        return min(score, 10), signals

    def generate_tier(self, total_score):
        """生成等级"""
        if total_score >= 85:
            return 'A', '顶尖候选人'
        elif total_score >= 70:
            return 'B', '优秀候选人'
        elif total_score >= 55:
            return 'C', '合格候选人'
        else:
            return 'D', '待观察'
```

---

## 🚀 实施建议

### 核心工作流程

```
南大学生列表
    ↓
1. 访问个人主页
    ↓
2. 提取基本信息 + 研究方向
    ↓
3. 查找并提取:
   - Google Scholar (论文)
   - GitHub (代码)
   - LinkedIn (职业)
   - 邮箱 (联系方式)
    ↓
4. 综合评分
    ↓
5. 生成候选人格案
```

### 可以直接复用的 GitHub Miner 代码

1. ✅ **评分系统架构** - 直接套用，调整权重
2. ✅ **分层分类** - Tier A/B/C 完全一样
3. ✅ **信号提取** - 方法通用
4. ✅ **速率限制管理** - 直接复用
5. ✅ **验证系统** - 方法通用

### 需要新增的能力

1. ⭐ **Google Scholar 提取** - GitHub Miner 没有
2. ⭐ **DBLP 提取** - 论文 venue 类型判断
3. ⭐ **深度网站分析** - 从主页提取所有信息
4. ⭐ **多源数据整合** - 合并 Scholar/GitHub/LinkedIn

---

## 💡 立即可以做的事

### 今天就能开始

1. **创建深度爬虫**
   ```python
   # 提取研究方向
   research = extract_from_homepage(url)
   ```

2. **集成 Google Scholar**
   ```python
   # 查找论文
   papers = extract_from_google_scholar(scholar_url)
   ```

3. **实现综合评分**
   ```python
   # 学术能力 + 技术能力 + 实践经验
   score = calculate_comprehensive_score(candidate)
   ```

---

**生成时间**: 2025-01-27
**项目**: 南大学生深度挖掘和评估系统
**核心**: 和 GitHub Miner 目标一致，方法可复用！
