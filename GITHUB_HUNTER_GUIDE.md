# GitHub Hunter - 候选人信息提取工具

> 🎯 **设计理念**: 参考 MediaCrawler 项目架构，采用配置驱动、模块化设计

## 📖 功能概述

从 GitHub URL 清单批量提取候选人信息，包括：
- ✅ 基本信息（姓名、公司、位置、Bio）
- ✅ 邮箱地址（从 Profile 和 Commits 提取）
- ✅ 技术栈（编程语言、框架）
- ✅ 项目经验（Star数、Fork数、贡献度）
- ✅ 活跃度分析（最后活跃时间、贡献模式）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install requests pandas openpyxl
```

### 2. 配置（可选）

编辑 `github_hunter_config.py`：
```python
GITHUB_CONFIG = {
    "token": "your_github_token_here",  # 提升速率限制到5000次/小时
    "request_delay": 1.0,
}
```

**获取 GitHub Token**:
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `public_repo` 权限
4. 复制 token 到配置文件

### 3. 准备数据

创建 Excel/CSV 文件，包含 GitHub URL 列：

| github_url |
|-----------|
| https://github.com/torvalds |
| https://github.com/gvanrossum |
| https://github.com/python/cpython |

### 4. 运行提取

```python
from github_hunter_simple import GitHubHunter
import pandas as pd

# 初始化
hunter = GitHubHunter(token="your_token")  # token可选

# 从文件读取
df = pd.read_excel('github_urls.xlsx')
urls = df['github_url'].tolist()

# 批量提取
results = hunter.batch_analyze(urls, delay=1)

# 保存结果
hunter.save_to_excel(results, 'candidates.xlsx')
hunter.save_to_json(results, 'candidates.json')
```

## 📊 输出格式

### Excel 表格字段

| 字段 | 说明 | 示例 |
|-----|------|------|
| github_url | GitHub 主页 | https://github.com/username |
| username | 用户名 | torvalds |
| name | 姓名 | Linus Torvalds |
| emails | 邮箱（多个用逗号分隔） | email1@example.com, email2@example.com |
| company | 公司 | Linux Foundation |
| location | 位置 | Portland, OR |
| bio | 个人简介 | Creator of Linux |
| primary_languages | 主要语言 | C, Assembly, Shell |
| total_stars | 总 Star 数 | 15000 |
| public_repos | 公开仓库数 | 5 |
| original_repos | 原创仓库数 | 3 |
| fork_repos | Fork 仓库数 | 2 |
| followers | 粉丝数 | 150000 |

### JSON 结构

```json
{
  "github_url": "https://github.com/username",
  "username": "username",
  "name": "User Name",
  "emails": "email1@example.com, email2@example.com",
  "company": "Company Name",
  "location": "Beijing, China",
  "bio": "Software Engineer",
  "primary_languages": "Python, JavaScript, Go",
  "language_count": 8,
  "total_stars": 1234,
  "public_repos": 25,
  "original_repos": 20,
  "fork_repos": 5,
  "followers": 150,
  "following": 50,
  "top_repos": [
    "repo1 (500★)",
    "repo2 (300★)"
  ],
  "created_at": "2015-01-01T00:00:00Z",
  "updated_at": "2024-12-01T00:00:00Z"
}
```

## 🔧 高级用法

### 1. 筛选中国用户

```python
from github_hunter_config import FILTER_CONFIG

def is_chinese_user(candidate):
    """判断是否为中国用户"""
    location = (candidate.get('location') or '').lower()
    company = (candidate.get('company') or '').lower()

    # 检查位置
    for kw in FILTER_CONFIG['china_location_keywords']:
        if kw in location:
            return True

    # 检查公司
    for kw in FILTER_CONFIG['china_company_keywords']:
        if kw in company:
            return True

    return False

# 筛选
chinese_candidates = [c for c in results if is_chinese_user(c)]
```

### 2. 去重合并

```python
def deduplicate_candidates(candidates):
    """去重"""
    seen = set()
    unique = []

    for candidate in candidates:
        # 优先用邮箱去重
        email = candidate.get('emails', '')
        if email and email not in seen:
            seen.add(email)
            unique.append(candidate)
        elif not email:
            # 没有邮箱，用 username
            username = candidate['username']
            if username not in seen:
                seen.add(username)
                unique.append(candidate)

    return unique

unique_candidates = deduplicate_candidates(results)
```

### 3. 评分排序

```python
def score_candidate(candidate):
    """简单评分算法"""
    score = 0

    # 活跃度
    score += min(candidate['public_repos'] * 2, 20)
    score += min(candidate['followers'] / 100, 20)

    # 质量
    score += min(candidate['total_stars'] / 100, 30)
    score += min(candidate['original_repos'] * 3, 20)

    # 经验
    score += min(candidate['language_count'] * 2, 10)

    return score

# 评分并排序
for candidate in results:
    candidate['score'] = score_candidate(candidate)

results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)
```

### 4. 存入数据库

```python
import sqlite3

def save_to_database(candidates, db_path='candidates.db'):
    """存入 SQLite 数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS github_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT,
            emails TEXT,
            company TEXT,
            location TEXT,
            bio TEXT,
            primary_languages TEXT,
            total_stars INTEGER,
            public_repos INTEGER,
            followers INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 插入数据
    for candidate in candidates:
        cursor.execute('''
            INSERT OR REPLACE INTO github_candidates
            (username, name, emails, company, location, bio,
             primary_languages, total_stars, public_repos, followers,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            candidate['username'],
            candidate['name'],
            candidate['emails'],
            candidate['company'],
            candidate['location'],
            candidate['bio'],
            candidate['primary_languages'],
            candidate['total_stars'],
            candidate['public_repos'],
            candidate['followers'],
            candidate['created_at'],
            candidate['updated_at']
        ))

    conn.commit()
    conn.close()

save_to_database(results)
```

## ⚡ 性能优化

### 1. 使用 GitHub Token

```python
# 无 Token: 60 次/小时
hunter = GitHubHunter()

# 有 Token: 5000 次/小时
hunter = GitHubHunter(token="ghp_xxxxxxxxxxxx")
```

### 2. 并发请求（高级）

```python
import asyncio
import aiohttp

async def fetch_user_async(username, token):
    """异步获取用户信息"""
    url = f"https://api.github.com/users/{username}"
    headers = {"Authorization": f"token {token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.json()

# 并发批量获取
async def batch_fetch_async(usernames, token):
    tasks = [fetch_user_async(u, token) for u in usernames]
    return await asyncio.gather(*tasks)

# 使用
results = asyncio.run(batch_fetch_async(usernames, token))
```

### 3. 缓存机制

```python
import pickle
from pathlib import Path

class CachedGitHubHunter(GitHubHunter):
    """带缓存的 GitHub Hunter"""

    def __init__(self, token=None, cache_file='github_cache.pkl'):
        super().__init__(token)
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self):
        """加载缓存"""
        if Path(self.cache_file).exists():
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        return {}

    def save_cache(self):
        """保存缓存"""
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def get_user_profile(self, username):
        """获取用户信息（带缓存）"""
        if username in self.cache:
            print(f"✅ 从缓存读取: {username}")
            return self.cache[username]

        profile = super().get_user_profile(username)
        if profile:
            self.cache[username] = profile
            self.save_cache()

        return profile
```

## 🔒 安全与合规

### 1. 使用建议

✅ **推荐做法**:
- 仅分析公开信息
- 遵守 GitHub API 速率限制
- 尊重用户隐私设置
- 用于合法的人才招聘目的

❌ **禁止行为**:
- 批量爬取非公开信息
- 绕过 GitHub 限制
- 将数据用于非法用途
- 骚扰候选人

### 2. 数据保护

```python
# 敏感数据脱敏
def sanitize_data(candidate):
    """脱敏处理"""
    candidate['emails'] = '***@***.***'  # 生产环境
    return candidate
```

## 📈 扩展方向

### 短期（1-2周）
- [ ] 添加 WebUI 界面（参考 MediaCrawler）
- [ ] 支持多线程/异步处理
- [ ] 添加更多评分维度

### 中期（1-2月）
- [ ] 集成到 personal-ai-headhunter
- [ ] 支持定时任务自动更新
- [ ] 添加邮件验证功能

### 长期（3-6月）
- [ ] 支持 GitLab、Gitee 等平台
- [ ] AI 驱动的深度技术评估
- [ ] 自动化联系候选人（邮件、LinkedIn）

## 🆘 常见问题

### Q1: 速率限制怎么办？
**A**: 添加 GitHub Token，提升到 5000 次/小时

### Q2: 邮箱提取不到？
**A**: 部分用户设置了隐私保护，无法获取主邮箱，尝试从 commits 提取

### Q3: 如何识别高质量候选人？
**A**: 综合考虑 `total_stars`、`original_repos`、`followers` 等指标

### Q4: 数据多久更新一次？
**A**: 建议 1-3 个月更新一次，避免频繁请求

### Q5: 如何与其他系统集成？
**A**: 使用数据库存储，或导出 JSON/Excel 供其他系统读取

## 📞 技术支持

- 项目地址: `/Users/lillianliao/notion_rag/github_hunter_simple.py`
- 配置文件: `/Users/lillianliao/notion_rag/github_hunter_config.py`
- MediaCrawler 参考: https://github.com/NanmiCoder/MediaCrawler

## 📝 更新日志

### v1.0.0 (2025-01-09)
- ✅ 初始版本
- ✅ 支持 GitHub API 提取
- ✅ 支持 Excel/JSON 输出
- ✅ 邮箱提取（Profile + Commits）
- ✅ 技术栈统计
- ✅ 项目经验分析

---

**设计灵感**: MediaCrawler 项目
**开发者**: lillianliao
**许可**: MIT License
