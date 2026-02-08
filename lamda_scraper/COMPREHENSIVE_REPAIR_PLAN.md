# LAMDA Scraper 系统性修复计划

## 🎯 总体目标

将数据完整性从当前的低水平提升到生产可用标准：
- **邮箱获取率**: 5.8% → **30%+**
- **GitHub数据完整率**: 18.4% → **80%+**
- **公司信息获取率**: 10.4% → **40%+**
- **整体数据质量评分**: D → **A**

---

## 📊 当前问题诊断

### 数据流完整度分析

```
总记录: 462 条
│
├─ GitHub 链接: 91 (19.7%) ← 80.3% 缺失 ❌
│  ├─ 有效 GitHub: 89 (19.3%)
│  ├─ 用户名提取: 89 (100%)
│  └─ Profile 获取: 85 (95.5%)
│
├─ 邮箱信息: 27 (5.8%) ← 94.2% 缺失 ❌
│  ├─ 原始邮箱: 27
│  └─ 网站邮箱: 24
│
├─ 公司信息: 48 (10.4%) ← 89.6% 缺失 ❌
│  └─ 大部分为空或不准确
│
└─ 研究方向: 0 (0%) ← 100% 标记为 incomplete ❌
```

### 关键错误点

#### 1. GitHub URL 提取失败 (80.3%)
**问题**:
- ❌ 无法识别 `pages.github.com` 格式
- ❌ 无法从页面内容中提取 GitHub 链接
- ❌ URL 解析规则过于简单

**案例**: 陈雄辉
- 数据库: `https://pages.github.com/` (无效)
- 实际: `https://github.com/xionghuichen`

#### 2. 邮箱提取严重不足 (94.2% 缺失)
**问题**:
- ❌ Cloudflare 邮件保护未解码
- ❌ 网站抓取失败率太高
- ❌ GitHub API 无权限访问邮箱
- ❌ 原始邮箱未正确保存

**案例**: 杨嘉祺
- 网站: `https://academic.thyrixyang.com`
- 问题: Cloudflare 保护未解码
- 已解决: thyrixyang@gmail.com ✅

**案例**: 陈雄辉
- 实际邮箱: xionghui.cxh@alibaba-inc.com
- 问题: 未从个人主页提取
- 状态: 待修复 ❌

#### 3. 研究方向提取失败 (100%)
**问题**:
- ❌ 462 条记录全部标记 "incomplete"
- ❌ 提取规则不完善
- ❌ 未利用论文/项目信息

#### 4. 公司信息大量缺失 (89.6%)
**问题**:
- ❌ 未从个人主页提取
- ❌ 未从 LinkedIn 提取
- ❌ 未从 GitHub 公司字段提取

---

## 🚀 修复计划

### Phase 1: 紧急修复 (P0) - 立即实施

#### 1.1 修复 GitHub URL 识别 ✅ 部分完成

**问题**: 无法正确提取 GitHub 用户名

**解决方案**:
```python
def extract_github_username(github_url):
    """增强版 GitHub 用户名提取"""
    if not github_url:
        return None

    # 处理 pages.github.com 格式
    if 'pages.github.com' in github_url:
        # 需要访问页面找到真实链接
        real_url = find_real_github_from_pages(github_url)
        return extract_github_username(real_url)

    # 处理标准格式
    patterns = [
        r'github\.com/([^/]+)/?$',
        r'github\.com/([^/]+)',
        r'github\.io/([^/.]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, github_url)
        if match:
            username = match.group(1)
            # 排除无效用户名
            if username not in ['pages', 'about', 'repo', 'gist']:
                return username

    return None
```

**文件**: `lamda_scraper.py`

#### 1.2 多层次邮箱提取 ✅ 已完成

**已完成**: `github_email_enricher.py`

**测试结果**:
- 杨嘉祺: `thyrixyang@gmail.com` ✅
- 陈雄辉: `xionghui.cxh@alibaba-inc.com` (待验证)

**下一步**: 对所有候选人批量提取

```bash
cd /Users/lillianliao/notion_rag/lamda_scraper
python3 batch_extract_emails.py
```

#### 1.3 个人主页深度抓取

**问题**: Cloudflare 保护 + GitHub Pages 未解析

**解决方案**:
```python
def scrape_personal_homepage(url):
    """深度抓取个人主页"""
    # 1. 跟随重定向
    response = requests.get(url, allow_redirects=True, timeout=15)
    final_url = response.url

    # 2. 如果是 GitHub Pages
    if 'github.io' in final_url or 'pages.github.com' in final_url:
        # 提取真实 GitHub 用户名
        github_match = re.search(r'github\.io/([^/]+)', final_url)
        if github_match:
            github_username = github_match.group(1)
            return {
                'github_username': github_username,
                'github_url': f'https://github.com/{github_username}',
                'emails': extract_emails_from_github_pages(final_url)
            }

    # 3. 提取邮箱（包括 Cloudflare）
    emails = extract_emails_with_cloudflare(response.text)

    # 4. 提取公司信息
    company = extract_company_from_homepage(response.text)

    return {
        'emails': emails,
        'company': company,
        'position': extract_position(response.text)
    }
```

**文件**: 新建 `scrape_websites_v2.py`

---

### Phase 2: 核心增强 (P1) - 本周完成

#### 2.1 GitHub Token 管理

**问题**: API 限流严重

**解决方案**:
```python
class GitHubTokenManager:
    def __init__(self):
        self.tokens = os.environ.get('GITHUB_TOKENS', '').split(',')
        self.current_index = 0
        self.rate_limit_reset = time.time() + 3600

    def get_next_token(self):
        """轮换 token 避免 API 限流"""
        token = self.tokens[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.tokens)
        return token

    def check_rate_limit(self, response):
        """检查并处理 API 限流"""
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if remaining < 100:
            # 切换 token
            return self.get_next_token()
        return None
```

**配置**: `.env`
```
GITHUB_TOKENS=token1,token2,token3
```

#### 2.2 错误重试和恢复

**问题**: 网络错误无重试

**解决方案**:
```python
def retry_with_backoff(func, max_retries=3):
    """带退避的重试装饰器"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # 指数退避
                time.sleep(wait_time)
    return wrapper
```

#### 2.3 数据质量监控

**问题**: 无法识别低质量数据

**解决方案**:
```python
def calculate_data_quality_score(candidate):
    """计算数据质量分数 (0-100)"""
    score = 0

    # 必需字段 (40分)
    if candidate.get('姓名'): score += 10
    if candidate.get('个人主页'): score += 15
    if candidate.get('GitHub'): score += 15

    # 联系信息 (30分)
    if candidate.get('邮箱'): score += 20
    elif candidate.get('website_email'): score += 10

    # 职业信息 (20分)
    if candidate.get('公司'): score += 10
    if candidate.get('职位'): score += 5
    if candidate.get('LinkedIn'): score += 5

    # 学术信息 (10分)
    if candidate.get('top_venues'): score += 5
    if candidate.get('publications'): score += 5

    return score
```

---

### Phase 3: 质量提升 (P2) - 下周完成

#### 3.1 研究方向智能提取

**问题**: 100% 标记为 incomplete

**解决方案**:
```python
def extract_research_interests(candidate):
    """多源提取研究方向"""
    interests = []

    # 1. 从个人主页提取
    homepage = candidate.get('个人主页')
    if homepage:
        interests.extend(extract_from_homepage(homepage))

    # 2. 从 GitHub bio 提取
    github_bio = candidate.get('github_bio')
    if github_bio:
        interests.extend(parse_bio_for_research(github_bio))

    # 3. 从论文标题提取
    if candidate.get('publications'):
        interests.extend(extract_from_papers(candidate['publications']))

    # 4. 从项目描述提取
    github_repos = candidate.get('github_top_repos')
    if github_repos:
        interests.extend(extract_from_repos(github_repos))

    return list(set(interests))
```

#### 3.2 公司信息智能提取

**多源策略**:
1. GitHub profile.company 字段
2. 个人主页 "Current Position" 部分
3. LinkedIn 当前职位
4. 简历/CV 中的工作经历

#### 3.3 数据验证和清洗

**使用 Pydantic 进行验证**:
```python
from pydantic import BaseModel, EmailStr, HttpUrl, validator

class CandidateModel(BaseModel):
    name_cn: str
    email: Optional[EmailStr] = None
    github_url: Optional[HttpUrl] = None
    homepage: Optional[HttpUrl] = None

    @validator('github_url')
    def validate_github(cls, v):
        if v and 'pages.github.com' in str(v):
            raise ValueError('Invalid GitHub pages URL')
        return v

    @validator('email')
    def validate_email(cls, v):
        if v:
            # 验证邮箱格式
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
                raise ValueError('Invalid email format')
        return v
```

---

## 📋 实施清单

### 立即执行 (今天)

- [x] 1. 创建 `github_email_enricher.py` ✅
- [x] 2. 实现 Cloudflare 邮件解码 ✅
- [x] 3. 测试杨嘉祺案例 ✅
- [ ] 4. 批量提取所有候选人邮箱
- [ ] 5. 手动修复陈雄辉数据

### 本周完成 (P0)

- [ ] 6. 修复 GitHub URL 识别逻辑
- [ ] 7. 实现重定向跟随
- [ ] 8. 添加 GitHub Token 管理
- [ ] 9. 创建数据质量监控脚本
- [ ] 10. 重新运行完整流程

### 下周完成 (P1)

- [ ] 11. 实现研究方向智能提取
- [ ] 12. 实现公司信息智能提取
- [ ] 13. 添加错误重试机制
- [ ] 14. 完善数据验证
- [ ] 15. 编写单元测试

---

## 📊 预期效果

### 修复前 vs 修复后

| 指标 | 修复前 | 修复后目标 | 提升 |
|------|--------|-----------|------|
| 邮箱获取率 | 5.8% | 30%+ | **5倍** |
| GitHub 数据完整率 | 18.4% | 80%+ | **4.3倍** |
| 公司信息获取率 | 10.4% | 40%+ | **3.8倍** |
| 研究方向完整率 | 0% | 70%+ | **∞** |
| 整体数据质量 | D | A | **3个等级** |

### 可联系候选人数量

- 修复前: 27 人 (5.8%)
- 修复后: 138+ 人 (30%+)
- **增长**: 111+ 人 (**4倍**)

---

## 🎯 成功标准

### 数据质量
- [ ] 90% 的候选人至少有 1 种联系方式
- [ ] 70% 的 GitHub 数据完整
- [ ] 60% 有研究或公司信息

### 系统稳定性
- [ ] API 限流恢复率 < 1%
- [ ] 网络错误恢复率 > 95%
- [ ] 数据丢失率 < 5%

### 可维护性
- [ ] 所有脚本有完整日志
- [ ] 错误处理覆盖率 > 90%
- [ ] 测试覆盖率 > 70%

---

## 📝 风险评估

### 技术风险
- **API 限流**: 通过 token 轮换缓解
- **反爬虫**: 添加延迟和随机化
- **Cloudflare 变更**: 持续监控并更新

### 时间风险
- **重构时间**: 约 2 周
- **测试时间**: 约 3 天
- **总时间**: 约 3 周

### 资源风险
- **GitHub API**: 需要 3-5 个 token
- **服务器**: 需要稳定网络环境
- **人力**: 1 个全职开发者

---

## 🚀 下一步行动

### 立即开始

```bash
cd /Users/lillianliao/notion_rag/lamda_scraper

# 1. 批量提取邮箱（包括陈雄辉）
python3 batch_extract_emails.py

# 2. 验证结果
python3 << 'EOF'
import csv

with open('lamda_candidates_with_emails.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    candidates = list(reader)

# 检查陈雄辉
for c in candidates:
    if '陈雄辉' in c['姓名']:
        print(f"陈雄辉邮箱: {c.get('github_email', '无')}")
        break

# 统计邮箱数量
with_email = [c for c in candidates if c.get('github_email')]
print(f"\n提取到邮箱的人数: {len(with_email)}")
EOF
```

### 优先级排序

**今天必须完成**:
1. ✅ 验证批量邮箱提取完成
2. ⏳ 手动修复陈雄辉数据
3. ⏳ 分析新提取的邮箱质量

**本周必须完成**:
4. ⏳ 修复 GitHub URL 识别
5. ⏳ 实现重定向跟随
6. ⏳ 添加 Token 管理

**下周计划**:
7. ⏳ 研究方向智能提取
8. ⏳ 完善数据验证
9. ⏳ 编写测试

---

## 📈 监控指标

### 关键指标

```python
# 每日监控
metrics = {
    'total_candidates': 462,
    'with_email': 0,
    'with_github': 0,
    'with_company': 0,
    'data_quality_score': 0,
    'extraction_success_rate': 0
}
```

### 周报

每周五生成报告，包括:
- 邮箱获取率变化
- GitHub 数据完整度
- API 使用量和成本
- 错误率和恢复率

---

**状态**: 📋 计划已制定
**下一步**: 开始执行 Phase 1.4 批量邮箱提取
**预计完成**: 2025-02-15 (3周)
**负责人**: [待指定]
