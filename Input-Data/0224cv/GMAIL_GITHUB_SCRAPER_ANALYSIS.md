# 🔍 Gmail + GitHub 猎头信息挖掘方案分析

## 📊 两个项目的核心功能

### 项目1: `langchain_scraper` - GitHub 贡献者挖掘
### 项目2: `gmail-resume-parser` - Gmail 简历解析

---

## 🎯 核心思路

通过 **Gmail 邮件** + **GitHub API** 组合，挖掘候选人的深度信息。

---

## 📋 项目1: langchain_scraper 详解

### **工作流程**

```
GitHub API (LangChain贡献者)
    ↓
获取 Top 100 贡献者
    ↓
筛选中国用户 (位置/公司/Bio)
    ↓
补充个人信息 (访问个人网站)
    ↓
生成候选人名单
```

### **实现细节**

#### **Step 1: 获取贡献者列表**

```python
# 从 GitHub API 获取贡献者
url = f"{GITHUB_API_BASE}/repos/langchain-ai/langchain/contributors"
response = requests.get(url, headers=headers)

# 返回数据结构
{
    "login": "ZhangShenao",
    "id": 12345678,
    "contributions": 42,
    "html_url": "https://github.com/ZhangShenao",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
    ...
}
```

**关键点:**
- 使用 GitHub API v3
- 按贡献数排序
- 支持分页（每页100条）
- 自动处理 API 限流

#### **Step 2: 筛选中国用户**

```python
# 中国识别关键词
CHINA_LOCATION_KEYWORDS = [
    'china', '中国', 'beijing', 'shanghai', 'hangzhou',
    'shenzhen', 'chengdu', '北京', '上海', '杭州', '深圳', ...
]

CHINA_COMPANY_KEYWORDS = [
    'alibaba', 'bytedance', 'tencent', 'baidu', 'meituan',
    '阿里', '腾讯', '字节', '美团', ...
]

def is_chinese_user(profile):
    """判断是否中国用户"""
    location = profile.get('location', '').lower()
    company = profile.get('company', '').lower()
    bio = profile.get('bio', '')

    # 1. 检查位置
    for kw in CHINA_LOCATION_KEYWORDS:
        if kw in location:
            return True

    # 2. 检查公司
    for kw in CHINA_COMPANY_KEYWORDS:
        if kw in company:
            return True

    # 3. 检查 Bio 中的中文
    if contains_chinese(bio):
        return True

    return False
```

**筛选逻辑:**
1. 位置匹配（北京/上海/深圳等）
2. 公司匹配（阿里/腾讯/字节等）
3. Bio 包含中文
4. 网址包含 .cn

#### **Step 3: 补充个人信息**

```python
# 访问个人网站获取更多信息
def scrape_personal_website(github_profile):
    url = github_profile.get('blog', '')
    if not url:
        return None

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取信息
    info = {
        'email': extract_email(soup),
        'linkedin': extract_linkedin(soup),
        'research_interests': extract_research(soup),
        'publications': extract_papers(soup),
        ...
    }

    return info
```

### **输出结果**

发现的 10 位中国贡献者：

| 排名 | GitHub ID | 贡献数 | 姓名 | 位置/公司 |
|------|-----------|--------|------|-----------|
| 1 | ZhangShenao | 42 | ZhangShenao | Beijing |
| 2 | liugddx | 36 | Guangdong Liu | Hefei |
| 3 | chyroc | 35 | chyroc | China |
| 7 | openvino-dev-samples | 12 | Ethan Yang | Shanghai, Intel |
| 8 | zc277584121 | 11 | Cheney Zhang | Hangzhou, @zilliztech |

---

## 📧 项目2: gmail-resume-parser 详解

### **工作流程**

```
Gmail API (搜索简历邮件)
    ↓
提取 Boss 直聘简历链接
    ↓
访问简历页面解析内容
    ↓
提取结构化数据
    ↓
导出到 Excel
```

### **实现细节**

#### **Step 1: Gmail API 认证**

```python
class GmailClient:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def _authenticate(self):
        # OAuth 2.0 认证流程
        flow = InstalledAppFlow.from_client_config(
            client_config, self.SCOPES
        )
        creds = flow.run_local_server(port=8080)

        # 保存 token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

        # 构建 Gmail 服务
        self.service = build('gmail', 'v1', credentials=creds)
```

**配置要求:**
- Google Cloud Console 创建项目
- 启用 Gmail API
- 创建 OAuth 2.0 凭证（桌面应用）
- 配置重定向 URI: `http://127.0.0.1:8080/`

#### **Step 2: 搜索邮件**

```python
def search_emails(self, query, max_results=100):
    """
    搜索邮件

    Gmail 搜索语法:
    - subject:"推荐了简历候选人"
    - from:cv@notice.zhipin.com
    - newer_than:7d

    组合查询:
    subject:"推荐了简历候选人" from:cv@notice.zhipin.com newer_than:7d
    """
    results = self.service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    return messages
```

**Gmail 搜索语法示例:**
```
# 基础搜索
subject:"简历"

# 指定发件人
from:cv@notice.zhipin.com

# 时间范围
newer_than:7d     # 最近7天
newer_than:30d    # 最近30天

# 组合条件
subject:"推荐了简历候选人" from:cv@notice.zhipin.com newer_than:7d
```

#### **Step 3: 提取邮件内容**

```python
def get_email_content(self, message_id):
    """获取邮件完整内容"""
    message = self.service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'  # 获取完整内容
    ).execute()

    # 提取邮件头
    headers = message['payload'].get('headers', [])
    subject = self._get_header(headers, 'Subject')
    from_addr = self._get_header(headers, 'From')

    # 提取正文（支持嵌套 parts）
    body_text, body_html = self._extract_body(message['payload'])

    return {
        'subject': subject,
        'from': from_addr,
        'body': body_text,
        'html_body': body_html
    }
```

**邮件结构解析:**
```
邮件 (MIME 格式)
├── headers (Subject, From, Date, ...)
└── payload
    ├── mimeType: multipart/mixed
    └── parts[]
        ├── part 1: text/plain (纯文本)
        └── part 2: text/html (HTML 格式)
```

#### **Step 4: 提取 Boss 直聘链接**

```python
def extract_boss_zhipin_links(self, email_content):
    """从邮件中提取简历链接"""
    text = email_content.get('html_body', '')

    # 正则匹配
    pattern = r'https://[mw]\.zhipin\.com/[^\s<>"\'\)]+'
    links = re.findall(pattern, text)

    # 去重
    links = list(set(links))

    return links
```

**链接示例:**
```
https://m.zhipin.com/mpa/html/weijd/weijd-preview/abc123?...
```

#### **Step 5: 解析简历页面（历史功能，已失效）**

```python
# ⚠️ 注意：Boss 直聘已改用 Canvas 渲染，此方法不再可用

def parse_resume_page(self, resume_url):
    """解析简历页面"""
    # 方式1: requests + BeautifulSoup (旧版有效)
    response = requests.get(resume_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取信息
    name = soup.find('div', class_='name').text
    position = soup.find('div', class_='position').text

    # 方式2: Selenium (处理 JavaScript)
    driver = webdriver.Chrome()
    driver.get(resume_url)
    content = driver.page_source

    return {
        'name': name,
        'position': position,
        'age': extract_age(soup),
        'education': extract_education(soup),
        'work_experience': extract_work(soup),
        ...
    }
```

**⚠️ 当前问题:**
Boss 直聘改用 **Canvas + WebAssembly** 渲染：
```html
<iframe src="/web/frame/c-resume">
    <canvas id="resume"></canvas>  <!-- 内容渲染成图像 -->
</iframe>
```

**解决方案:**
1. **API 拦截**（推荐）- 捕获网络请求获取 JSON
2. **OCR 识别** - 截图后提取文字（准确率低）
3. **手动处理** - 暂停自动化

---

## 🚀 组合应用：Gmail + GitHub 信息挖掘

### **核心思路**

利用 Gmail 作为数据源，通过 GitHub API 补充候选人信息。

### **实现流程**

```
┌─────────────────────────────────────────────────────────────┐
│  1. Gmail 搜索                                            │
│     - 查找候选人相关邮件                                   │
│     - 提取姓名、邮箱、GitHub 链接                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. GitHub API                                            │
│     - 根据邮箱/GitHub用户名获取详细信息                    │
│     - 获取: 位置、公司、贡献数、项目列表                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. 个人网站爬取                                          │
│     - 访问个人主页/GitHub Pages                            │
│     - 提取: 研究方向、论文、联系方式                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 数据整合                                              │
│     - 合并所有来源的信息                                   │
│     - 生成完整候选人档案                                   │
└─────────────────────────────────────────────────────────────┘
```

### **代码示例**

```python
# 完整的信息挖掘流程

class CandidateMiner:
    def __init__(self):
        self.gmail_client = GmailClient(
            'config/credentials.json',
            'data/token.json'
        )
        self.github_token = os.environ.get('GITHUB_TOKEN')

    def mine_from_gmail(self, query):
        """从 Gmail 挖掘候选人"""
        # 1. 搜索邮件
        emails = self.gmail_client.search_emails(query)

        candidates = []
        for email_msg in emails:
            content = self.gmail_client.get_email_content(email_msg['id'])

            # 2. 提取 GitHub 链接
            github_links = self.extract_github_links(content)

            for github_url in github_links:
                username = self.extract_username(github_url)

                # 3. 获取 GitHub 信息
                profile = self.get_github_profile(username)

                # 4. 补充个人信息
                personal_info = self.scrape_personal_website(profile)

                # 5. 整合数据
                candidate = {
                    'name': content.get('from'),
                    'email': self.extract_email(content),
                    'github_username': username,
                    'github_contributions': profile.get('public_repos'),
                    'location': profile.get('location'),
                    'company': profile.get('company'),
                    'bio': profile.get('bio'),
                    'personal_website': personal_info.get('website'),
                    'research_interests': personal_info.get('interests'),
                    'publications': personal_info.get('papers'),
                    'linkedin': personal_info.get('linkedin'),
                }

                candidates.append(candidate)

        return candidates

    def extract_github_links(self, email_content):
        """从邮件中提取 GitHub 链接"""
        text = email_content.get('body', '')
        pattern = r'https://github\.com/[\w-]+'
        return re.findall(pattern, text)

    def get_github_profile(self, username):
        """获取 GitHub 个人资料"""
        url = f"{GITHUB_API_BASE}/users/{username}"
        response = requests.get(url, headers={
            'Authorization': f'token {self.github_token}'
        })
        return response.json()

    def scrape_personal_website(self, profile):
        """爬取个人网站"""
        blog_url = profile.get('blog')
        if not blog_url:
            return {}

        response = requests.get(blog_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        return {
            'website': blog_url,
            'interests': self.extract_research_interests(soup),
            'papers': self.extract_publications(soup),
            'linkedin': self.extract_linkedin(soup),
        }
```

---

## 💡 实战应用建议

### **场景1: 挖掘 LAMDA 候选人的 GitHub 信息**

```python
# 假设从 LAMDA 官网获得了邮箱列表
emails = [
    'jiangw@lamda.nju.edu.cn',
    'xionghui.cxh@alibaba-inc.com',
    ...
]

for email in emails:
    # 1. Gmail 搜索是否有相关邮件
    query = f'from:{email} OR to:{email}'
    emails_found = gmail_client.search_emails(query, max_results=10)

    for email_msg in emails_found:
        content = gmail_client.get_email_content(email_msg['id'])

        # 2. 提取 GitHub 链接
        github_links = extract_github_links(content)

        if github_links:
            # 3. 获取 GitHub 信息
            for github_url in github_links:
                username = extract_username(github_url)
                profile = get_github_profile(username)

                # 补充信息
                print(f"✓ {email} -> GitHub: {username}")
                print(f"  位置: {profile.get('location')}")
                print(f"  公司: {profile.get('company')}")
                print(f"  公开项目: {profile.get('public_repos')}")
                print(f"  Bio: {profile.get('bio')}")
```

### **场景2: 从 GitHub 贡献者反向查找邮箱**

```python
# 已知 GitHub 用户名，想找到邮箱
github_usernames = [
    'ZhangShenao',
    'liugddx',
    ...
]

for username in github_usernames:
    # 1. 获取 GitHub 信息
    profile = get_github_profile(username)

    # 2. Gmail 搜索相关邮件
    # 策略1: 搜索 @github.com 相关邮件
    query = f'from:{username}@users.noreply.github.com'
    emails = gmail_client.search_emails(query)

    # 策略2: 搜索用户真名
    if profile.get('name'):
        query = f'"{profile["name"]}"'
        emails = gmail_client.search_emails(query)

    # 3. 提取邮箱
    for email_msg in emails:
        content = gmail_client.get_email_content(email_msg['id'])
        email_addr = extract_email_from_body(content['body'])
        print(f"✓ {username} -> {email_addr}")
```

---

## 🎯 总结与建议

### **两个项目的价值**

| 项目 | 数据源 | 适用场景 | 优势 |
|------|--------|---------|------|
| **langchain_scraper** | GitHub API | 挖掘开源贡献者 | - 技术能力强<br>- 有公开代码<br>- 社区活跃度高 |
| **gmail-resume-parser** | Gmail 邮件 | 解析招聘平台简历 | - 信息全面<br>- 意向明确<br>- 联系方式直接 |

### **组合使用效果**

**Gmail + GitHub 组合:**
- ✅ 交叉验证候选人信息
- ✅ 补充技术能力和兴趣
- ✅ 发现更多联系方式
- ✅ 评估实际代码水平

### **实施建议**

**第一步: 使用 Gmail 收集初步信息**
```bash
cd gmail-resume-parser
python src/main.py
# 搜索包含简历的邮件
# 提取候选人基本信息
```

**第二步: 使用 GitHub API 补充技术信息**
```python
# 根据邮箱/姓名搜索 GitHub
# 获取公开项目和贡献记录
# 评估技术栈和能力
```

**第三步: 访问个人网站深度挖掘**
```python
# 爬取个人主页
# 提取研究兴趣、论文、博客
# 了解技术观点和深度
```

---

## ⚠️ 注意事项

### **Gmail API 限制**
- 每日配额限制（通常 10 亿 单位）
- 大量采集需分批处理
- 建议添加 `newer_than` 过滤时间范围

### **GitHub API 限制**
- 未认证: 60 次/小时
- 使用 Token: 5000 次/小时
- 建议设置环境变量 `GITHUB_TOKEN`

### **Boss 直聘 Canvas 问题**
- 当前无法自动解析
- 需要手动复制或使用 OCR
- 或者使用 Boss 直聘 API（如果有权限）

---

**最后更新:** 2026-01-08
**适用场景:** 猎头信息挖掘、候选人深度分析
