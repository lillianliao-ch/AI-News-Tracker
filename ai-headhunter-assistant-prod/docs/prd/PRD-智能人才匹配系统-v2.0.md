# 智能人才匹配系统 PRD v2.0

> **基于**: AI 自动筛选简历系统 MVP v1.0  
> **扩展目标**: 自动获取 JD + 智能人才匹配 + 全流程自动化  
> **创建时间**: 2025-11-15  
> **状态**: 规划中

---

## 📋 目录

1. [产品总览](#1-产品总览)
2. [系统架构演进](#2-系统架构演进)
3. [功能模块详解](#3-功能模块详解)
4. [技术实现方案](#4-技术实现方案)
5. [开发路线图](#5-开发路线图)
6. [数据库设计](#6-数据库设计)
7. [API 设计](#7-api-设计)

---

## 1. 产品总览

### 1.1 产品目标

这是一个 **自动获取人才 + 自动获取岗位 + 自动结构化 + 自动匹配 + 自动报告** 的智能匹配系统，用于：

- ✅ 大幅提升猎头团队效率（80%+ 时间节省）
- ✅ 提供更加专业、数据化的人才推荐报告
- ✅ 以技术手段扩大人才库规模（100-500人/天）
- ✅ 为客户提供准确、可靠、可解释的人才评估

### 1.2 核心能力

#### ✔ 1. 自动获取数据
- 自动抓取企业官网 JD
- 自动抓取招聘平台人才资料（Boss/LinkedIn/GitHub）

#### ✔ 2. 自动结构化标签
- 将 JD / 简历解析成结构化标签体系（Skills, Scenario, Background…）

#### ✔ 3. 自动匹配
- 根据标签、权重、向量算法计算匹配评分
- 输出岗位<->人才双向推荐结果

#### ✔ 4. 自动报告输出
- 自动生成专业级 PDF
- 支持 JSON、CSV、Dashboard

### 1.3 核心使用场景

| 场景 | 描述 | 价值 |
|------|------|------|
| **场景 1** | 客户给了大量 JD 需要快速分析 | 5 分钟完成原本 3 小时工作 |
| **场景 2** | 每天自动从 Boss/LinkedIn 抓 100～500+ 人才 | 自动画像化 → 匹配到合适岗位 |
| **场景 3** | 企业做市场人才 Mapping | 自动抓取行业内公司岗位 → 人才能力需求趋势 |
| **场景 4** | AIoT/DePIN 等新行业快速全球找人才 | 人才库与能力图谱工具 |
| **场景 5** | 扩充猎头团队，统一系统 | 标签统一、评分统一、报告统一 |

### 1.4 业务流程

```
【输入层】
  - 自动抓 JD（企业官网）
  - 自动抓人才（Boss/LinkedIn/GitHub）
  - 上传简历（PDF/图片/Word）

【解析层】
  - LLM 解析 JD → Job Tags
  - LLM 解析 Resume → Talent Tags
  - 标签标准化（Tag Normalize）

【匹配层】
  - One-hot / Embedding 向量化
  - 权重评分算法
  - 输出匹配矩阵（N 人 × M 岗）

【推荐层】
  - 候选人 Top3 岗位
  - 岗位 Top3 候选人

【报告层】
  - PDF
  - JSON/CSV
  - Dashboard（后续）

【存储层】
  - job_tags
  - talent_tags
  - matching_results
```

---

## 2. 系统架构演进

### 2.1 当前系统（MVP v1.0）

```
┌─────────────────────────────────────────┐
│         Chrome 插件（前端）              │
├─────────────────────────────────────────┤
│ - Boss 直聘候选人采集                    │
│ - 简历详情提取                           │
│ - 简历截图                               │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         FastAPI 后端                     │
├─────────────────────────────────────────┤
│ - AI 简历解析（通义千问）                │
│ - 匹配度评估（固定 JD）                  │
│ - 飞书集成                               │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         飞书多维表格                     │
├─────────────────────────────────────────┤
│ - 候选人信息                             │
│ - 简历截图                               │
│ - AI 评估结果                            │
└─────────────────────────────────────────┘
```

**限制**：
- ❌ 只支持单一 JD（硬编码）
- ❌ 无法批量管理多个岗位
- ❌ 无法自动获取 JD
- ❌ 匹配逻辑简单
- ❌ 无专业报告输出

---

### 2.2 目标系统（v2.0）

```
┌─────────────────────────────────────────────────────────────┐
│                    前端（Chrome 插件 + Web 管理后台）          │
├─────────────────────────────────────────────────────────────┤
│ - JD 采集模块 ⭐                                             │
│ - 候选人采集模块（已有）                                      │
│ - 智能匹配控制台 ⭐                                          │
│ - 报告生成器 ⭐                                              │
│ - 寻访策略生成器 ⭐                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    后端 API（FastAPI）                        │
├─────────────────────────────────────────────────────────────┤
│ - JD Spider（自动抓取岗位）⭐                                │
│ - Talent Spider（自动抓人才）⭐                              │
│ - JD Tag Extractor（JD 解析）⭐                              │
│ - Talent Tag Extractor（人才解析）✅                         │
│ - Tag Normalizer（标签标准化）⭐                             │
│ - Sourcing Strategy Generator（寻访策略）⭐                  │
│ - Boolean Search Builder（搜索语句）⭐                       │
│ - Matching Engine（匹配引擎）⭐                              │
│ - Report Engine（报告生成）⭐                                │
│ - Contact Enrichment（联系方式补全）⭐                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据层（飞书多维表格 + PostgreSQL）         │
├─────────────────────────────────────────────────────────────┤
│ - JD 库（job_tags）⭐                                        │
│ - 人才库（talent_tags）✅                                    │
│ - 匹配记录（matching_results）⭐                             │
│ - 公司库（company_knowledge）⭐                              │
│ - 标签字典（skills_dictionary）⭐                            │
└─────────────────────────────────────────────────────────────┘
```

**新增能力**：
- ✅ 多 JD 管理
- ✅ 自动 JD 采集
- ✅ 智能标签体系
- ✅ 高级匹配算法
- ✅ 专业报告输出
- ✅ 寻访策略自动生成

---

## 3. 功能模块详解

### 3.1 JD Spider（自动抓取岗位）⭐ 新增

#### 功能描述
从企业官网、招聘平台自动抓取 JD 列表 & 内容。

#### 支持的数据源
1. **企业官网** - 自动识别招聘页面
2. **Boss 直聘** - 职位搜索
3. **LinkedIn Jobs** - API 或爬虫
4. **猎聘** - Playwright
5. **手动输入** - 用户粘贴 JD

#### 支持的页面类型
- 静态 HTML
- 动态渲染（JS）
- 分页 / 滑动加载
- 需登录页面（Cookie）

#### 技术方案
```python
# 使用 Playwright
from playwright.async_api import async_playwright

async def scrape_jd(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        
        # 自动滚动加载
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_load_state("networkidle")
        
        # 提取 JD 内容
        jd_text = await page.locator(".job-description").inner_text()
        
        return {
            "url": url,
            "title": await page.title(),
            "content": jd_text,
            "scraped_at": datetime.now()
        }
```

#### 输出格式
```json
{
  "jd_id": "JD_20251115_001",
  "source": "boss/linkedin/website",
  "url": "https://...",
  "title": "AI产品经理",
  "company": "字节跳动",
  "location": "北京",
  "salary_range": "40-80K",
  "raw_content": "完整JD文本...",
  "scraped_at": "2025-11-15 14:00:00"
}
```

---

### 3.2 Talent Spider（自动抓人才）⭐ 新增

#### 功能描述
批量从多个平台自动抓取候选人信息。

#### 支持的数据源
1. **Boss 直聘** - 关键词搜索 + 公司筛选
2. **LinkedIn** - Search API / 爬虫
3. **GitHub** - 按语言/项目/关键字
4. **猎聘** - Playwright
5. **脉脉** - Playwright

#### 抓取策略
```python
# 示例：Boss 直聘批量抓取
async def batch_scrape_boss(
    keywords: List[str],
    companies: List[str],
    limit: int = 100
) -> List[dict]:
    results = []
    
    for keyword in keywords:
        for company in companies:
            # 构建搜索 URL
            search_url = f"https://www.zhipin.com/web/geek/job?query={keyword}&company={company}"
            
            # 抓取候选人列表
            candidates = await scrape_candidate_list(search_url, limit=20)
            results.extend(candidates)
            
            # 限流
            await asyncio.sleep(random.uniform(3, 5))
    
    return results[:limit]
```

#### 附加功能
- ✅ IP 代理池（避免封禁）
- ✅ 限流策略（随机延迟）
- ✅ 验证码 OCR（自动识别）
- ✅ Cookie 管理（保持登录）

#### 输出格式
```json
{
  "candidate_id": "CAND_20251115_001",
  "source": "boss/linkedin/github",
  "name": "张先生",
  "current_company": "字节跳动",
  "current_position": "AI工程师",
  "work_years": 5,
  "education": "硕士",
  "skills": ["Python", "LLM", "RAG"],
  "raw_profile": "完整简历文本...",
  "scraped_at": "2025-11-15 14:00:00"
}
```

---

### 3.3 JD Tag Extractor（JD 解析）⭐ 新增

#### 功能描述
使用 LLM 将 JD 文本解析为结构化标签。

#### 标签体系（六大类）

```python
JOB_TAG_SCHEMA = {
    "skills": {
        "description": "技术技能要求",
        "examples": ["Python", "Kubernetes", "RAG", "LLM"]
    },
    "system": {
        "description": "系统/平台经验",
        "examples": ["AWS", "微服务", "分布式系统"]
    },
    "ai_tags": {
        "description": "AI 相关标签",
        "examples": ["NLP", "CV", "推荐系统", "模型训练"]
    },
    "scenario": {
        "description": "应用场景",
        "examples": ["金融风控", "智能客服", "文档问答"]
    },
    "experience": {
        "description": "经验要求",
        "examples": ["3-5年", "大厂背景", "创业经验"]
    },
    "soft": {
        "description": "软技能",
        "examples": ["沟通能力", "领导力", "学习能力"]
    }
}
```

#### Prompt 设计

```python
JD_EXTRACTION_PROMPT = """
你是一个专业的 HR 助手，请从以下 JD 中提取结构化标签。

JD 原文：
{jd_content}

请按照以下格式输出 JSON：
{{
  "skills": ["技能1", "技能2", ...],
  "system": ["系统1", "系统2", ...],
  "ai_tags": ["AI标签1", "AI标签2", ...],
  "scenario": ["场景1", "场景2", ...],
  "experience": ["经验1", "经验2", ...],
  "soft": ["软技能1", "软技能2", ...]
}}

要求：
1. 提取所有明确提到的技能和要求
2. 推断隐含的技能（如"熟悉推荐系统" → ["推荐算法", "协同过滤"]）
3. 标准化技能名称（如"py" → "Python"）
4. 每个类别至少 3 个标签
"""
```

#### 实现代码

```python
async def extract_jd_tags(jd_content: str) -> dict:
    """使用 LLM 提取 JD 标签"""
    
    prompt = JD_EXTRACTION_PROMPT.format(jd_content=jd_content)
    
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    tags = json.loads(response.choices[0].message.content)
    
    # 标签标准化
    tags = await normalize_tags(tags)
    
    return tags
```

---

### 3.4 Talent Tag Extractor（人才解析）✅ 已有

#### 功能描述
将简历解析为结构化标签（已在 MVP v1.0 实现）。

#### 标签体系（五大类）

```python
TALENT_TAG_SCHEMA = {
    "skills": ["Python", "Kubernetes", ...],
    "scenario": ["金融风控", "推荐系统", ...],
    "background": {
        "companies": ["字节跳动", "腾讯", ...],
        "education": "硕士",
        "school": "清华大学"
    },
    "soft": ["沟通能力", "领导力", ...],
    "domain_strength": {
        "AI": 9,
        "Backend": 7,
        "Frontend": 3
    }
}
```

#### 优化方向
- ✅ 支持 PDF/图片 OCR
- ✅ 项目经历提取
- ✅ 技能深度评估
- ⭐ 与 JD 标签体系对齐

---

### 3.5 Tag Normalizer（标签标准化）⭐ 新增

#### 功能描述
解决标签不一致问题，统一标签命名。

#### 问题示例
```
python / py / Py / Python3 → Python
k8s / Kubernetes / kube → Kubernetes
RAG / retrieval-augmented-generation → RAG
NLP / 自然语言处理 / Natural Language Processing → NLP
```

#### 技术方案

**方案 1：标签字典（Skills Dictionary）**
```python
SKILLS_DICTIONARY = {
    "Python": ["python", "py", "Python3", "python3"],
    "Kubernetes": ["k8s", "kube", "kubernetes", "K8S"],
    "RAG": ["rag", "retrieval-augmented-generation", "检索增强生成"],
    "NLP": ["nlp", "自然语言处理", "natural language processing"]
}

def normalize_tag(tag: str) -> str:
    """标准化单个标签"""
    tag_lower = tag.lower().strip()
    
    for standard_name, aliases in SKILLS_DICTIONARY.items():
        if tag_lower in [a.lower() for a in aliases]:
            return standard_name
    
    return tag.title()  # 首字母大写
```

**方案 2：LLM 自动扩展**
```python
async def expand_skills_dictionary(new_tags: List[str]) -> dict:
    """使用 LLM 自动扩展标签字典"""
    
    prompt = f"""
    请为以下技能标签找出所有可能的同义词和缩写：
    {new_tags}
    
    输出 JSON 格式：
    {{
      "标准名称": ["同义词1", "同义词2", ...]
    }}
    """
    
    # 调用 LLM
    response = await call_llm(prompt)
    
    # 更新字典
    return json.loads(response)
```

---

### 3.6 Sourcing Strategy Generator（寻访策略生成）⭐ 新增

#### 功能描述
基于 JD 自动生成完整的寻访策略，包括：
- 理想候选人画像
- 标准候选人画像
- 备选候选人画像
- 目标公司清单（分层）
- 推荐搜索平台
- 搜索关键词集
- Boolean 搜索语句

#### 输出格式

```json
{
  "jd_id": "JD_20251115_001",
  "ideal_persona": {
    "work_years": "3-5年",
    "skills": ["NLP", "RAG", "LLM"],
    "scenario": ["法律文档", "金融文档"],
    "background": ["大厂", "AI独角兽"],
    "soft": ["领导力", "沟通能力"]
  },
  "standard_persona": {
    "work_years": "2-3年",
    "skills": ["NLP", "Python"],
    "scenario": ["文档处理"],
    "background": ["互联网公司"]
  },
  "optional_persona": {
    "work_years": "1-2年",
    "skills": ["Python", "机器学习"],
    "scenario": ["数据分析"],
    "background": ["任何"]
  },
  "target_company_list": {
    "tier1": ["MiniMax", "智谱AI", "月之暗面"],
    "tier2": ["字节跳动", "阿里巴巴", "腾讯"],
    "tier3": ["金融IT公司", "互联网大厂"]
  },
  "recommended_channels": [
    "Boss直聘",
    "LinkedIn",
    "GitHub",
    "猎聘"
  ],
  "recommended_keywords": [
    "NLP工程师",
    "RAG工程师",
    "LLM工程师",
    "AI工程师"
  ],
  "boolean_queries": [
    "(\"NLP Engineer\" OR \"RAG Engineer\" OR \"LLM Engineer\") AND (Python OR Transformer) AND (\"MiniMax\" OR \"ByteDance\" OR \"Moonshot\")"
  ],
  "recommended_spider_actions": [
    "Boss: 搜索 'NLP工程师' + 公司筛选 'MiniMax'",
    "LinkedIn: Boolean搜索 + 地区筛选 '北京'",
    "GitHub: 搜索 'RAG' + 'LLM' 相关项目贡献者"
  ]
}
```

#### 实现代码

```python
async def generate_sourcing_strategy(jd_tags: dict) -> dict:
    """基于 JD 标签生成寻访策略"""
    
    prompt = f"""
    基于以下 JD 标签，生成完整的寻访策略：
    
    JD 标签：
    {json.dumps(jd_tags, ensure_ascii=False, indent=2)}
    
    请输出 JSON 格式的寻访策略，包括：
    1. 理想/标准/备选候选人画像
    2. 目标公司清单（Tier 1/2/3）
    3. 推荐搜索平台
    4. 搜索关键词
    5. Boolean 搜索语句
    6. 抓取脚本建议
    """
    
    response = await call_llm(prompt, model="gpt-4")
    strategy = json.loads(response)
    
    # 自动补充公司库
    strategy["target_company_list"] = await enrich_company_list(
        strategy["target_company_list"]
    )
    
    return strategy
```

---

### 3.7 Target Company Tiering Engine（目标公司分层）⭐ 新增

#### 功能描述
自动生成目标公司名单，并按竞争力分层。

#### 分层逻辑

```python
COMPANY_TIERS = {
    "tier1": {
        "description": "直接竞争对手",
        "criteria": ["同行业", "同产品", "同规模"],
        "examples": ["MiniMax", "智谱AI", "月之暗面"]
    },
    "tier2": {
        "description": "同类领域公司",
        "criteria": ["AI/大模型", "推荐系统", "平台"],
        "examples": ["字节跳动", "阿里巴巴", "腾讯"]
    },
    "tier3": {
        "description": "可迁移经验公司",
        "criteria": ["金融IT", "互联网大厂", "技术驱动"],
        "examples": ["蚂蚁金服", "京东", "美团"]
    }
}
```

#### 实现方式

**方式 1：LLM + 公司知识库**
```python
async def tier_companies(jd_tags: dict, company_db: List[dict]) -> dict:
    """基于 JD 标签对公司分层"""
    
    prompt = f"""
    JD 标签：{jd_tags}
    
    公司库：{company_db}
    
    请将公司分为 3 层：
    - Tier 1：直接竞争对手
    - Tier 2：同类领域
    - Tier 3：可迁移经验
    """
    
    response = await call_llm(prompt)
    return json.loads(response)
```

**方式 2：手动配置 + 自动扩展**
```python
# 手动配置核心公司
CORE_COMPANIES = {
    "AI": ["OpenAI", "Anthropic", "MiniMax", "智谱AI"],
    "推荐系统": ["字节跳动", "快手", "小红书"],
    "金融科技": ["蚂蚁金服", "微众银行", "京东数科"]
}

# LLM 自动扩展
async def expand_company_list(core_companies: List[str]) -> List[str]:
    prompt = f"请列出与以下公司类似的其他公司：{core_companies}"
    response = await call_llm(prompt)
    return parse_company_list(response)
```

---

### 3.8 Boolean Search Builder（搜索语句生成）⭐ 新增

#### 功能描述
基于 JD 标签自动生成 Boolean 搜索语句，适用于 LinkedIn/Boss/猎聘。

#### 输出示例

```
("NLP Engineer" OR "RAG Engineer" OR "LLM Engineer")
AND (Python OR Transformer OR PyTorch)
AND ("MiniMax" OR "ByteDance" OR "Moonshot" OR "Zhipu")
AND ("北京" OR "Beijing")
```

#### 实现代码

```python
def build_boolean_query(jd_tags: dict, target_companies: List[str]) -> str:
    """构建 Boolean 搜索语句"""
    
    # 职位关键词
    job_titles = [
        f'"{skill} Engineer"' for skill in jd_tags["skills"][:3]
    ]
    title_query = f'({" OR ".join(job_titles)})'
    
    # 技能关键词
    skills = jd_tags["skills"][:5]
    skill_query = f'({" OR ".join(skills)})'
    
    # 公司关键词
    companies = [f'"{company}"' for company in target_companies[:5]]
    company_query = f'({" OR ".join(companies)})'
    
    # 组合
    boolean_query = f"{title_query} AND {skill_query} AND {company_query}"
    
    return boolean_query
```

---

### 3.9 Matching Engine（匹配引擎）⭐ 核心

#### 功能描述
基于标签和权重计算候选人与 JD 的匹配度。

#### 评分公式

```python
total_score = (
    0.45 * skill_score +
    0.30 * scenario_score +
    0.15 * background_score +
    0.10 * soft_score
)
```

#### 各维度计算

**1. 技能匹配（45%）**
```python
def calculate_skill_score(jd_skills: List[str], talent_skills: List[str]) -> float:
    """技能匹配度"""
    
    # 交集数量
    matched_skills = set(jd_skills) & set(talent_skills)
    
    # 基础分数
    base_score = (len(matched_skills) / len(jd_skills)) * 100
    
    # 加权（核心技能权重更高）
    core_skills = jd_skills[:3]  # 前3个为核心技能
    core_matched = set(core_skills) & set(talent_skills)
    bonus = (len(core_matched) / len(core_skills)) * 20
    
    return min(base_score + bonus, 100)
```

**2. 场景匹配（30%）**
```python
def calculate_scenario_score(jd_scenarios: List[str], talent_scenarios: List[str]) -> float:
    """场景匹配度"""
    
    # 直接匹配
    direct_match = set(jd_scenarios) & set(talent_scenarios)
    direct_score = (len(direct_match) / len(jd_scenarios)) * 70
    
    # 语义相似度（使用 Embedding）
    semantic_score = await calculate_semantic_similarity(
        jd_scenarios, talent_scenarios
    ) * 30
    
    return direct_score + semantic_score
```

**3. 背景匹配（15%）**
```python
COMPANY_TIER_SCORES = {
    "外企": 100,
    "独角兽": 90,
    "大厂": 80,
    "中型公司": 60,
    "小公司": 40
}

def calculate_background_score(talent_background: dict) -> float:
    """背景匹配度"""
    
    # 公司背景
    company_score = max([
        COMPANY_TIER_SCORES.get(classify_company(company), 40)
        for company in talent_background["companies"]
    ])
    
    # 学历加分
    education_bonus = {
        "博士": 20,
        "硕士": 10,
        "本科": 0
    }.get(talent_background["education"], 0)
    
    return min(company_score + education_bonus, 100)
```

**4. 软技能匹配（10%）**
```python
async def calculate_soft_score(jd_soft: List[str], talent_soft: List[str]) -> float:
    """软技能匹配度（LLM 评估）"""
    
    prompt = f"""
    JD 要求的软技能：{jd_soft}
    候选人的软技能：{talent_soft}
    
    请评估匹配度（0-10分）并说明理由。
    """
    
    response = await call_llm(prompt)
    score = extract_score(response)
    
    return score * 10  # 转换为 0-100
```

#### 完整实现

```python
async def calculate_matching_score(
    jd_tags: dict,
    talent_tags: dict
) -> dict:
    """计算完整匹配分数"""
    
    # 各维度分数
    skill_score = calculate_skill_score(
        jd_tags["skills"], talent_tags["skills"]
    )
    
    scenario_score = await calculate_scenario_score(
        jd_tags["scenario"], talent_tags["scenario"]
    )
    
    background_score = calculate_background_score(
        talent_tags["background"]
    )
    
    soft_score = await calculate_soft_score(
        jd_tags["soft"], talent_tags["soft"]
    )
    
    # 加权总分
    total_score = (
        0.45 * skill_score +
        0.30 * scenario_score +
        0.15 * background_score +
        0.10 * soft_score
    )
    
    # 推荐等级
    recommend_level = "强推" if total_score >= 85 else \
                     "推荐" if total_score >= 70 else \
                     "一般" if total_score >= 50 else \
                     "不推荐"
    
    return {
        "total_score": round(total_score, 2),
        "skill_score": round(skill_score, 2),
        "scenario_score": round(scenario_score, 2),
        "background_score": round(background_score, 2),
        "soft_score": round(soft_score, 2),
        "recommend_level": recommend_level,
        "matched_skills": list(set(jd_tags["skills"]) & set(talent_tags["skills"])),
        "missing_skills": list(set(jd_tags["skills"]) - set(talent_tags["skills"]))
    }
```

---

### 3.10 Report Engine（报告生成）⭐ 新增

#### 功能描述
自动生成专业级人才推荐报告（PDF/CSV/JSON）。

#### 报告类型

**1. PDF 专业报告**
- 封面
- Executive Summary
- 岗位画像
- 人才画像
- 匹配矩阵
- Top 推荐
- 雷达图

**2. CSV 数据报告**
- 候选人列表
- 匹配分数
- 关键标签

**3. JSON API**
- 结构化数据
- 供其他系统调用

#### PDF 报告结构

```python
PDF_REPORT_STRUCTURE = {
    "封面": {
        "title": "人才推荐报告",
        "jd_title": "AI产品经理",
        "company": "字节跳动",
        "date": "2025-11-15",
        "logo": "company_logo.png"
    },
    "Executive Summary": {
        "total_candidates": 50,
        "recommended": 15,
        "avg_match_score": 72.5,
        "top3_highlights": [...]
    },
    "岗位画像": {
        "skills": [...],
        "scenario": [...],
        "experience": [...]
    },
    "人才画像": {
        "ideal_persona": {...},
        "standard_persona": {...}
    },
    "匹配矩阵": {
        "table": [...],  # N人 × M岗
        "heatmap": "heatmap.png"
    },
    "Top 推荐": [
        {
            "rank": 1,
            "name": "张先生",
            "match_score": 92,
            "highlights": [...],
            "risks": [...]
        },
        ...
    ],
    "雷达图": {
        "skills_radar": "skills_radar.png",
        "comparison": "comparison.png"
    }
}
```

#### 实现代码

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

async def generate_pdf_report(
    jd_tags: dict,
    matching_results: List[dict],
    output_path: str
) -> str:
    """生成 PDF 报告"""
    
    # 创建 PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 1. 封面
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "人才推荐报告")
    c.setFont("Helvetica", 14)
    c.drawString(100, height - 150, f"岗位：{jd_tags['title']}")
    c.drawString(100, height - 180, f"日期：{datetime.now().strftime('%Y-%m-%d')}")
    c.showPage()
    
    # 2. Executive Summary
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, "Executive Summary")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 150, f"总候选人数：{len(matching_results)}")
    c.drawString(100, height - 180, f"推荐候选人：{len([r for r in matching_results if r['recommend_level'] == '推荐'])}")
    c.showPage()
    
    # 3. 岗位画像
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, "岗位画像")
    y = height - 150
    for skill in jd_tags["skills"][:10]:
        c.drawString(120, y, f"• {skill}")
        y -= 20
    c.showPage()
    
    # 4. Top 推荐
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, "Top 推荐候选人")
    y = height - 150
    for i, result in enumerate(matching_results[:5], 1):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, y, f"{i}. {result['name']} - {result['total_score']}%")
        c.setFont("Helvetica", 10)
        y -= 20
        c.drawString(120, y, f"技能匹配：{result['skill_score']}%")
        y -= 15
        c.drawString(120, y, f"场景匹配：{result['scenario_score']}%")
        y -= 30
    c.showPage()
    
    # 5. 雷达图
    radar_chart = generate_radar_chart(matching_results[0])
    c.drawImage(radar_chart, 100, height - 500, width=400, height=300)
    
    c.save()
    
    return output_path


def generate_radar_chart(matching_result: dict) -> str:
    """生成雷达图"""
    
    categories = ['技能', '场景', '背景', '软技能']
    values = [
        matching_result['skill_score'],
        matching_result['scenario_score'],
        matching_result['background_score'],
        matching_result['soft_score']
    ]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    
    chart_path = "/tmp/radar_chart.png"
    plt.savefig(chart_path)
    plt.close()
    
    return chart_path
```

---

### 3.11 Contact Enrichment（联系方式补全）⭐ 新增

#### 功能描述
自动补全候选人的联系方式（邮箱/手机号）。

#### 数据源
1. **GitHub Public Email**
2. **LinkedIn**
3. **ContactOut API**（付费）
4. **Clearbit**（可选）
5. **Boss 页面解析**

#### 实现代码

```python
async def enrich_contact(candidate: dict) -> dict:
    """补全联系方式"""
    
    contact_info = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None
    }
    
    # 1. GitHub
    if candidate.get("github_username"):
        github_email = await get_github_email(candidate["github_username"])
        if github_email:
            contact_info["email"] = github_email
    
    # 2. LinkedIn
    if candidate.get("linkedin_url"):
        linkedin_data = await scrape_linkedin(candidate["linkedin_url"])
        contact_info["email"] = linkedin_data.get("email")
        contact_info["phone"] = linkedin_data.get("phone")
    
    # 3. ContactOut API
    if not contact_info["email"]:
        contactout_data = await query_contactout(
            name=candidate["name"],
            company=candidate["current_company"]
        )
        contact_info.update(contactout_data)
    
    # 4. Boss 页面
    if candidate.get("boss_url"):
        boss_data = await scrape_boss_contact(candidate["boss_url"])
        contact_info.update(boss_data)
    
    return {
        **candidate,
        **contact_info
    }
```

---

## 4. 技术实现方案

### 4.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **前端** | Chrome Extension + React | 插件 + 管理后台 |
| **后端** | FastAPI + Python 3.11 | 异步高性能 |
| **爬虫** | Playwright + Selenium | 动态页面渲染 |
| **AI** | OpenAI GPT-4 / 通义千问 | LLM 解析 |
| **向量** | OpenAI Embeddings | 语义相似度 |
| **数据库** | PostgreSQL + 飞书 | 结构化 + 协作 |
| **缓存** | Redis | 标签字典缓存 |
| **队列** | Celery + Redis | 异步任务 |
| **报告** | ReportLab + Matplotlib | PDF 生成 |

### 4.2 系统架构图

```
┌──────────────────────────────────────────────────────────┐
│                      前端层                               │
├──────────────────────────────────────────────────────────┤
│  Chrome Extension          │  Web 管理后台（React）      │
│  - JD 采集                 │  - JD 管理                  │
│  - 候选人采集               │  - 匹配结果查看             │
│  - 一键匹配                 │  - 报告下载                 │
└──────────────────────────────────────────────────────────┘
                           ↓ HTTP/WebSocket
┌──────────────────────────────────────────────────────────┐
│                      API 网关层                           │
├──────────────────────────────────────────────────────────┤
│  FastAPI                                                  │
│  - 路由                                                   │
│  - 认证                                                   │
│  - 限流                                                   │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                      业务逻辑层                           │
├──────────────────────────────────────────────────────────┤
│  Spider 模块  │  Parser 模块  │  Matching 模块  │  Report │
│  - JD Spider  │  - JD Parser  │  - Score Calc   │  - PDF  │
│  - Talent     │  - Talent     │  - Ranking      │  - CSV  │
│    Spider     │    Parser     │  - Recommend    │  - JSON │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                      数据访问层                           │
├──────────────────────────────────────────────────────────┤
│  PostgreSQL   │  Redis        │  飞书 API       │  OSS    │
│  - JD Tags    │  - Cache      │  - 多维表格     │  - PDF  │
│  - Talent     │  - Queue      │  - 文档         │  - 截图 │
│    Tags       │               │                 │         │
│  - Matching   │               │                 │         │
└──────────────────────────────────────────────────────────┘
```

### 4.3 核心流程图

#### 流程 1：JD 采集与解析

```
用户输入 JD URL
      ↓
JD Spider 抓取
      ↓
原始 JD 文本
      ↓
LLM 解析（GPT-4）
      ↓
结构化标签（6大类）
      ↓
标签标准化
      ↓
存入 JD 库
```

#### 流程 2：候选人采集与解析

```
用户配置搜索条件
      ↓
Talent Spider 批量抓取
      ↓
原始简历数据
      ↓
LLM 解析（GPT-4）
      ↓
结构化标签（5大类）
      ↓
标签标准化
      ↓
联系方式补全
      ↓
存入人才库
```

#### 流程 3：智能匹配

```
选择 JD + 候选人池
      ↓
提取标签
      ↓
计算各维度分数
  - 技能匹配（45%）
  - 场景匹配（30%）
  - 背景匹配（15%）
  - 软技能（10%）
      ↓
加权总分
      ↓
排序推荐
      ↓
生成匹配报告
      ↓
存入匹配记录
```

#### 流程 4：报告生成

```
选择匹配结果
      ↓
生成雷达图
      ↓
生成匹配矩阵
      ↓
组装 PDF 内容
      ↓
ReportLab 渲染
      ↓
上传到 OSS
      ↓
返回下载链接
```

---

## 5. 开发路线图

### Phase 1: 基础设施（2周）

#### Week 1: 数据库 + 标签体系
- [ ] PostgreSQL 数据库设计
- [ ] JD Tags 表结构
- [ ] Talent Tags 表结构
- [ ] Matching Results 表结构
- [ ] Skills Dictionary 初始化
- [ ] Tag Normalizer 实现

#### Week 2: 爬虫基础设施
- [ ] Playwright 环境搭建
- [ ] IP 代理池
- [ ] Cookie 管理
- [ ] 限流策略
- [ ] 验证码 OCR

---

### Phase 2: JD 模块（2周）

#### Week 3: JD 采集
- [ ] JD Spider 实现
  - [ ] 企业官网爬虫
  - [ ] Boss 直聘 JD 爬虫
  - [ ] LinkedIn Jobs 爬虫
  - [ ] 手动输入接口
- [ ] JD 存储
- [ ] JD 管理界面

#### Week 4: JD 解析
- [ ] JD Tag Extractor 实现
- [ ] LLM Prompt 优化
- [ ] 标签标准化集成
- [ ] JD 详情页
- [ ] 批量解析

---

### Phase 3: 人才模块（2周）

#### Week 5: 人才采集
- [ ] Talent Spider 实现
  - [ ] Boss 批量抓取
  - [ ] LinkedIn 抓取
  - [ ] GitHub 抓取
  - [ ] 猎聘抓取
- [ ] 联系方式补全
- [ ] 人才库管理

#### Week 6: 人才解析优化
- [ ] Talent Tag Extractor 优化
- [ ] 与 JD 标签体系对齐
- [ ] 项目经历提取
- [ ] 技能深度评估

---

### Phase 4: 匹配引擎（2周）

#### Week 7: 匹配算法
- [ ] 技能匹配算法
- [ ] 场景匹配算法（Embedding）
- [ ] 背景匹配算法
- [ ] 软技能评估（LLM）
- [ ] 加权总分计算

#### Week 8: 匹配优化
- [ ] 批量匹配
- [ ] 匹配矩阵生成
- [ ] Top N 推荐
- [ ] 匹配结果存储
- [ ] 匹配历史查询

---

### Phase 5: 寻访策略（1周）

#### Week 9: 策略生成
- [ ] Sourcing Strategy Generator
- [ ] Target Company Tiering
- [ ] Boolean Search Builder
- [ ] 目标公司库
- [ ] 策略模板

---

### Phase 6: 报告生成（2周）

#### Week 10: PDF 报告
- [ ] 报告模板设计
- [ ] ReportLab 集成
- [ ] 雷达图生成
- [ ] 匹配矩阵可视化
- [ ] 封面 + Summary

#### Week 11: 多格式报告
- [ ] CSV 导出
- [ ] JSON API
- [ ] Dashboard（可选）
- [ ] 报告管理
- [ ] 批量生成

---

### Phase 7: 集成与测试（2周）

#### Week 12: 系统集成
- [ ] 前后端联调
- [ ] Chrome 插件集成
- [ ] Web 管理后台
- [ ] 飞书集成优化
- [ ] 权限管理

#### Week 13: 测试与优化
- [ ] 功能测试
- [ ] 性能测试
- [ ] 压力测试
- [ ] Bug 修复
- [ ] 文档编写

---

### Phase 8: 上线与迭代（持续）

#### Week 14+: 生产部署
- [ ] 服务器部署
- [ ] 域名配置
- [ ] SSL 证书
- [ ] 监控告警
- [ ] 数据备份

#### 后续迭代
- [ ] 用户反馈收集
- [ ] 功能优化
- [ ] 新数据源接入
- [ ] AI 模型优化
- [ ] 性能优化

---

## 6. 数据库设计

### 6.1 JD 表（job_tags）

```sql
CREATE TABLE job_tags (
    jd_id VARCHAR(50) PRIMARY KEY,
    source VARCHAR(50),  -- boss/linkedin/website/manual
    url TEXT,
    title VARCHAR(200),
    company VARCHAR(200),
    location VARCHAR(100),
    salary_range VARCHAR(50),
    work_years VARCHAR(50),
    education VARCHAR(50),
    
    -- 标签（JSONB）
    skills JSONB,  -- ["Python", "Kubernetes", ...]
    system JSONB,  -- ["AWS", "微服务", ...]
    ai_tags JSONB,  -- ["NLP", "CV", ...]
    scenario JSONB,  -- ["金融风控", ...]
    experience JSONB,  -- ["3-5年", "大厂背景", ...]
    soft JSONB,  -- ["沟通能力", ...]
    
    -- 原始数据
    raw_content TEXT,
    
    -- 元数据
    status VARCHAR(20),  -- active/paused/closed
    scraped_at TIMESTAMP,
    parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_jd_company ON job_tags(company);
CREATE INDEX idx_jd_status ON job_tags(status);
CREATE INDEX idx_jd_skills ON job_tags USING GIN(skills);
```

### 6.2 人才表（talent_tags）

```sql
CREATE TABLE talent_tags (
    candidate_id VARCHAR(50) PRIMARY KEY,
    source VARCHAR(50),  -- boss/linkedin/github/manual
    name VARCHAR(100),
    current_company VARCHAR(200),
    current_position VARCHAR(200),
    work_years INT,
    education VARCHAR(50),
    school VARCHAR(200),
    
    -- 标签（JSONB）
    skills JSONB,  -- ["Python", ...]
    scenario JSONB,  -- ["金融风控", ...]
    background JSONB,  -- {"companies": [...], "education": "..."}
    soft JSONB,  -- ["沟通能力", ...]
    domain_strength JSONB,  -- {"AI": 9, "Backend": 7}
    projects JSONB,  -- [{"name": "...", "skills": [...]}]
    
    -- 联系方式
    email VARCHAR(200),
    phone VARCHAR(50),
    linkedin_url TEXT,
    github_url TEXT,
    
    -- 原始数据
    raw_profile TEXT,
    resume_screenshot TEXT,  -- Base64 或 URL
    
    -- 元数据
    scraped_at TIMESTAMP,
    parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_talent_company ON talent_tags(current_company);
CREATE INDEX idx_talent_skills ON talent_tags USING GIN(skills);
```

### 6.3 匹配记录表（matching_results）

```sql
CREATE TABLE matching_results (
    matching_id VARCHAR(50) PRIMARY KEY,
    jd_id VARCHAR(50) REFERENCES job_tags(jd_id),
    candidate_id VARCHAR(50) REFERENCES talent_tags(candidate_id),
    
    -- 分数
    total_score FLOAT,
    skill_score FLOAT,
    scenario_score FLOAT,
    background_score FLOAT,
    soft_score FLOAT,
    
    -- 推荐等级
    recommend_level VARCHAR(20),  -- 强推/推荐/一般/不推荐
    
    -- 匹配详情
    matched_skills JSONB,
    missing_skills JSONB,
    matched_scenarios JSONB,
    highlights TEXT,  -- 匹配亮点
    risks TEXT,  -- 匹配风险
    
    -- 元数据
    matched_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_matching_jd ON matching_results(jd_id);
CREATE INDEX idx_matching_candidate ON matching_results(candidate_id);
CREATE INDEX idx_matching_score ON matching_results(total_score DESC);
CREATE INDEX idx_matching_level ON matching_results(recommend_level);
```

### 6.4 标签字典表（skills_dictionary）

```sql
CREATE TABLE skills_dictionary (
    standard_name VARCHAR(100) PRIMARY KEY,
    aliases JSONB,  -- ["python", "py", "Python3"]
    category VARCHAR(50),  -- programming/framework/tool/domain
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 初始数据
INSERT INTO skills_dictionary (standard_name, aliases, category) VALUES
('Python', '["python", "py", "Python3", "python3"]', 'programming'),
('Kubernetes', '["k8s", "kube", "kubernetes", "K8S"]', 'tool'),
('RAG', '["rag", "retrieval-augmented-generation", "检索增强生成"]', 'domain'),
('NLP', '["nlp", "自然语言处理", "natural language processing"]', 'domain');
```

### 6.5 公司库表（company_knowledge）

```sql
CREATE TABLE company_knowledge (
    company_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(200),
    tier VARCHAR(20),  -- tier1/tier2/tier3
    industry VARCHAR(100),
    tags JSONB,  -- ["AI", "大模型", ...]
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 初始数据
INSERT INTO company_knowledge (company_id, company_name, tier, industry, tags) VALUES
('minimax', 'MiniMax', 'tier1', 'AI', '["大模型", "AI"]'),
('zhipu', '智谱AI', 'tier1', 'AI', '["大模型", "AI"]'),
('moonshot', '月之暗面', 'tier1', 'AI', '["大模型", "AI"]'),
('bytedance', '字节跳动', 'tier2', '互联网', '["推荐系统", "AI", "大厂"]');
```

---

## 7. API 设计

### 7.1 JD 相关 API

#### POST /api/jd/scrape
抓取 JD

**Request**:
```json
{
  "url": "https://www.example.com/jobs",
  "source": "website"
}
```

**Response**:
```json
{
  "success": true,
  "jd_id": "JD_20251115_001",
  "raw_content": "..."
}
```

---

#### POST /api/jd/parse
解析 JD

**Request**:
```json
{
  "jd_id": "JD_20251115_001"
}
```

**Response**:
```json
{
  "success": true,
  "jd_tags": {
    "skills": ["Python", "Kubernetes"],
    "system": ["AWS", "微服务"],
    "ai_tags": ["NLP", "RAG"],
    "scenario": ["金融风控"],
    "experience": ["3-5年"],
    "soft": ["沟通能力"]
  }
}
```

---

#### GET /api/jd/list
获取 JD 列表

**Query Parameters**:
- `status`: active/paused/closed
- `company`: 公司名
- `page`: 页码
- `limit`: 每页数量

**Response**:
```json
{
  "success": true,
  "total": 100,
  "data": [
    {
      "jd_id": "JD_20251115_001",
      "title": "AI产品经理",
      "company": "字节跳动",
      "status": "active",
      "created_at": "2025-11-15 14:00:00"
    },
    ...
  ]
}
```

---

### 7.2 人才相关 API

#### POST /api/talent/scrape
批量抓取候选人

**Request**:
```json
{
  "source": "boss",
  "keywords": ["NLP工程师", "RAG工程师"],
  "companies": ["MiniMax", "智谱AI"],
  "limit": 100
}
```

**Response**:
```json
{
  "success": true,
  "total_scraped": 95,
  "candidate_ids": ["CAND_001", "CAND_002", ...]
}
```

---

#### POST /api/talent/parse
解析候选人

**Request**:
```json
{
  "candidate_id": "CAND_001"
}
```

**Response**:
```json
{
  "success": true,
  "talent_tags": {
    "skills": ["Python", "LLM"],
    "scenario": ["文档问答"],
    "background": {...},
    "soft": ["沟通能力"]
  }
}
```

---

#### POST /api/talent/enrich
补全联系方式

**Request**:
```json
{
  "candidate_id": "CAND_001"
}
```

**Response**:
```json
{
  "success": true,
  "contact": {
    "email": "zhang@example.com",
    "phone": "138****1234",
    "linkedin": "https://linkedin.com/in/zhang",
    "github": "https://github.com/zhang"
  }
}
```

---

### 7.3 匹配相关 API

#### POST /api/matching/calculate
计算匹配度

**Request**:
```json
{
  "jd_id": "JD_20251115_001",
  "candidate_ids": ["CAND_001", "CAND_002", ...]
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "candidate_id": "CAND_001",
      "total_score": 92.5,
      "skill_score": 95,
      "scenario_score": 88,
      "background_score": 90,
      "soft_score": 85,
      "recommend_level": "强推",
      "matched_skills": ["Python", "LLM"],
      "missing_skills": ["Kubernetes"]
    },
    ...
  ]
}
```

---

#### GET /api/matching/recommend
获取推荐

**Query Parameters**:
- `jd_id`: JD ID
- `top_n`: Top N 候选人
- `min_score`: 最低分数

**Response**:
```json
{
  "success": true,
  "recommendations": [
    {
      "rank": 1,
      "candidate_id": "CAND_001",
      "name": "张先生",
      "total_score": 92.5,
      "highlights": ["5年NLP经验", "大厂背景"],
      "risks": ["薪资预期略高"]
    },
    ...
  ]
}
```

---

### 7.4 报告相关 API

#### POST /api/report/generate
生成报告

**Request**:
```json
{
  "jd_id": "JD_20251115_001",
  "candidate_ids": ["CAND_001", "CAND_002", ...],
  "format": "pdf",  // pdf/csv/json
  "include_radar": true,
  "include_matrix": true
}
```

**Response**:
```json
{
  "success": true,
  "report_id": "REPORT_20251115_001",
  "download_url": "https://oss.example.com/reports/REPORT_20251115_001.pdf",
  "expires_at": "2025-11-22 14:00:00"
}
```

---

#### GET /api/report/download/{report_id}
下载报告

**Response**: PDF 文件流

---

### 7.5 寻访策略 API

#### POST /api/sourcing/strategy
生成寻访策略

**Request**:
```json
{
  "jd_id": "JD_20251115_001"
}
```

**Response**:
```json
{
  "success": true,
  "strategy": {
    "ideal_persona": {...},
    "standard_persona": {...},
    "optional_persona": {...},
    "target_company_list": {
      "tier1": ["MiniMax", "智谱AI"],
      "tier2": ["字节跳动", "阿里巴巴"],
      "tier3": ["金融IT公司"]
    },
    "recommended_channels": ["Boss直聘", "LinkedIn"],
    "recommended_keywords": ["NLP工程师", "RAG工程师"],
    "boolean_queries": ["(\"NLP Engineer\" OR \"RAG Engineer\") AND ..."]
  }
}
```

---

## 8. 下一步行动

### 立即开始（本周）

#### 选项 A：先完成 MVP v1.0 剩余任务
- ✅ Day 8: 飞书集成 - **已完成**
- 🔜 Day 10.1: 批量测试（20-50人）
- 🔜 Day 10.3: 用户手册
- 🟡 Day 9: 自动打招呼（可选）

**优点**: MVP 完整交付，可立即使用  
**时间**: 2-3天

---

#### 选项 B：直接开始 v2.0 开发
- 🔜 Phase 1: 基础设施（数据库 + 标签体系）
- 🔜 Phase 2: JD 模块（采集 + 解析）
- 🔜 Phase 3: 匹配引擎

**优点**: 快速构建核心能力  
**时间**: 2-3周

---

#### 选项 C：混合方案（推荐）
1. **本周**: 完成 MVP v1.0 测试 + 文档（Day 10）
2. **下周开始**: v2.0 Phase 1（基础设施）
3. **持续迭代**: 逐步添加新功能

**优点**: 稳妥推进，MVP 可用 + v2.0 并行  
**时间**: 灵活

---

## 🤔 你的选择？

请告诉我你想：

**A. 先完成 MVP v1.0（测试 + 文档）**  
**B. 直接开始 v2.0 开发**  
**C. 混合方案（推荐）**  

或者告诉我你的想法，我们一起调整计划！ 😊


