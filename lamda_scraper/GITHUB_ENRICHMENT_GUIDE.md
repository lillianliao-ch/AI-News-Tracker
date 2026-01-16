# 🚀 LAMDA 猎头系统 - GitHub 信息挖掘完整指南

## ✅ 已完成的功能

### 1. **GitHub 信息深度挖掘工具** (`github_enricher.py`)

自动从候选人的 GitHub 链接中提取：
- ✅ 基本信息（位置、公司、Bio、邮箱）
- ✅ 活跃度指标（仓库数、更新频率、账号年限）
- ✅ 影响力指标（Stars、Followers、Forks）
- ✅ 技术栈识别（机器学习、深度学习、NLP、CV等）
- ✅ 编程语言统计
- ✅ Top 10 仓库详情
- ✅ **技术能力评分 (0-100分)**

---

## 📊 测试结果（10人样本）

### ✅ 成功案例

| 姓名 | GitHub用户 | 总分 | 活跃度 | 影响力 | 质量 | 仓库数 | Stars | 技术栈 |
|------|-----------|------|--------|--------|------|--------|-------|--------|
| 杨嘉祺 | ThyrixYang | **79** | 40/40 | 29/30 | 10/30 | 26 | 1037 | CV/ML/Python |
| 庞竟成 | lafmdp | **75** | 40/40 | 20/30 | 15/30 | 26 | 778 | NLP/RL/Python |
| 李新春 | lxcnju | **73** | 40/40 | 23/30 | 10/30 | 29 | 544 | ML/JS/Python |
| 罗凡明 | FanmingL | **67** | 40/40 | 17/30 | 10/30 | 27 | 84 | DL/NLP/RL/Python |
| 邱梓豪 | zhqiu | **42** | 30/40 | 12/30 | 0/30 | 33 | 33 | Python |

**关键发现:**
- 5/6 成功获取信息 (83%成功率)
- 4/5 被评为高质量 (≥60分)
- 平均 27 个公开仓库/人
- 平均 495 Stars/人

---

## 🎯 快速开始

### **步骤1: 准备 GitHub Token** (推荐但非必须)

**获取 Token:**
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选权限:
   - `public_repo` - 访问公开仓库
   - `read:user` - 读取用户信息
   - `read:org` - 读取组织信息
4. 生成并复制 Token

**设置环境变量:**
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**优势:**
- ✅ 请求限制: 5000次/小时 (vs 60次/小时未认证)
- ✅ 更稳定、更快速

### **步骤2: 运行 GitHub 信息挖掘**

```bash
cd /Users/lillianliao/notion_rag/lamda_scraper

# 方式1: 使用自动化脚本（推荐）
./run_github_enrichment.sh

# 方式2: 手动运行
python3 github_enricher.py \
  --input lamda_candidates_full.csv \
  --output lamda_candidates_github_enhanced.csv
```

**预期时间:**
- 无 Token: ~60-90分钟 (API限流)
- 有 Token: ~5-10分钟

---

## 📈 评分体系详解

### **总分计算 (100分制)**

```
总分 = 活跃度分 (40) + 影响力分 (30) + 质量分 (30)
```

### **1️⃣ 活跃度评分 (0-40分)**

| 指标 | 权重 | 说明 |
|------|------|------|
| 公开仓库数 | 20分 | 2分/仓库，最多20分 |
| 账号年限 | 10分 | 3分/年，最多10分 |
| 最近更新 | 10分 | 30天内更新=10分，90天内=5分 |

**示例:**
```
杨嘉祺: 26个仓库 × 2 + 10年(假设) × 3 + 最近更新 = 40/40分
```

### **2️⃣ 影响力评分 (0-30分)**

| 指标 | 权重 | 说明 |
|------|------|------|
| Followers | 15分 | Followers/10，最多15分 |
| 总 Stars | 10分 | Stars/5，最多10分 |
| 总 Forks | 5分 | Forks/10，最多5分 |

**示例:**
```
杨嘉祺: 142 followers × 0.1 + 1037 stars × 0.2 = 14 + 20 = 34/30 (限制为30分)
```

### **3️⃣ 质量评分 (0-30分)**

| 指标 | 分数 | 说明 |
|------|------|------|
| 有 Bio | 5分 | 展示专业形象 |
| 有公司信息 | 5分 | 就业状态 |
| Hireable | 10分 | 寻求机会 |
| 有邮箱 | 5分 | 联系方式 |
| 仓库质量 | 5分 | 平均Stars≥10 |

---

## 💡 技术栈自动识别

工具会自动检测候选人的技术栈：

### **检测规则**

1. **从 Bio 检测**
   - Bio 包含 "machine learning" → `machine_learning`
   - Bio 包含 "computer vision" → `computer_vision`

2. **从仓库名/描述检测**
   - 仓库名 "pytorch-xxx" → `deep_learning`
   - 描述 "NLP toolkit" → `nlp`

3. **从编程语言统计**
   - Python ≥ 3个仓库 → `python`
   - JavaScript ≥ 3个仓库 → `javascript`

### **技术栈类别**

| 类别 | 关键词 |
|------|--------|
| `python` | python, django, flask, fastapi |
| `machine_learning` | tensorflow, pytorch, scikit-learn |
| `deep_learning` | neural, cnn, rnn, transformer, bert |
| `computer_vision` | opencv, detection, segmentation |
| `nlp` | nlp, text, tokenizer, gpt, llm |
| `reinforcement_learning` | reinforcement, rl, agent |
| `data_science` | pandas, numpy, visualization |

---

## 🎯 猎头应用价值

### **传统方式 vs GitHub 增强**

| 维度 | 传统方式 | GitHub 增强 |
|------|---------|-------------|
| 技术能力评估 | 简历/口头描述 | ✅ 实际代码质量 |
| 项目经验 | 声称的项目 | ✅ 公开可验证 |
| 技术栈 | 自述 | ✅ 代码统计 |
| 影响力 | 难以判断 | ✅ Stars/Followers量化 |
| 学习能力 | 学历/论文 | ✅ 开源贡献活跃度 |
| 代码质量 | 不知道 | ✅ 可直接审查 |

### **实际应用场景**

#### **场景1: 快速筛选技术强者**

**筛选条件:**
```
github_score >= 70 AND github_stars >= 100
```

**结果:**
- 杨嘉祺 (79分, 1037 Stars) - CV/ML专家
- 庞竟成 (75分, 778 Stars) - NLP/RL专家
- 李新春 (73分, 544 Stars) - ML/全栈

**推荐职位:**
- 高级算法工程师
- 研究科学家
- 技术Lead

#### **场景2: 识别特定技术栈候选人**

**NLP工程师:**
```
github_tech_stack LIKE '%nlp%'
AND github_stars >= 50
```

**结果:**
- 庞竟成 - NLP/RL, 778 Stars
- 罗凡明 - DL/NLP/RL, 84 Stars

#### **场景3: 代码质量评估**

**访问候选人 GitHub:**
1. 查看 Top Repos
2. 阅读代码
3. 检查文档质量
4. 查看提交记录
5. 评估 Issue 回应

---

## 📋 输出字段说明

运行后会生成新的 CSV 文件，包含以下新字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `github_username` | GitHub 用户名 | ThyrixYang |
| `github_score` | 总分 (0-100) | 79 |
| `github_activity` | 活跃度分 (0-40) | 40 |
| `github_influence` | 影响力分 (0-30) | 29 |
| `github_quality` | 质量分 (0-30) | 10 |
| `github_repos` | 公开仓库数 | 26 |
| `github_stars` | 总 Stars 数 | 1037 |
| `github_followers` | Followers 数 | 142 |
| `github_bio` | 个人简介 | - |
| `github_company` | 公司信息 | 南京大学 |
| `github_location` | 位置 | Nanjing |
| `github_tech_stack` | 技术栈 | ml;dl;cv;python |
| `github_languages` | 编程语言统计 | Python×10; C++×5 |
| `github_top_repos` | Top 10 仓库 (JSON) | [{"name": "...", "stars": 100}] |

---

## 🔧 高级用法

### **1. 筛选高质量候选人**

```python
import pandas as pd

df = pd.read_csv('lamda_candidates_github_enhanced.csv')

# 筛选条件
high_quality = df[
    (df['github_score'] >= 60) &  # 高活跃度
    (df['github_stars'] >= 100) &  # 有影响力
    (df['github_repos'] >= 10)      # 有经验
]

# 排序
high_quality = high_quality.sort_values('github_score', ascending=False)

# 保存
high_quality.to_csv('github_high_quality_candidates.csv', index=False)
```

### **2. 按技术栈分类**

```python
# Python专家
python_experts = df[df['github_tech_stack'].str.contains('python', na=False)]

# 深度学习专家
dl_experts = df[df['github_tech_stack'].str.contains('deep_learning|nlp|computer_vision', na=False)]
```

### **3. 导出详细报告**

```python
# 生成详细的 GitHub 报告
for _, row in df.iterrows():
    if row['github_score'] >= 60:
        print(f"\n{'='*60}")
        print(f"候选人: {row['姓名']}")
        print(f"GitHub: https://github.com/{row['github_username']}")
        print(f"总分: {row['github_score']}")
        print(f"技术栈: {row['github_tech_stack']}")

        # 解析 Top Repos
        import json
        repos = json.loads(row['github_top_repos'])
        print(f"\nTop 3 项目:")
        for repo in repos[:3]:
            print(f"  - {repo['name']} ({repo['stars']}⭐)")
            print(f"    {repo.get('description', 'No description')}")
```

---

## 💡 最佳实践

### **✅ DO's (推荐做法)**

1. **设置 GitHub Token**
   - 提高请求限制
   - 更稳定可靠
   - 避免被封禁

2. **综合评估**
   - GitHub 分数 + 学术分数 (顶会论文)
   - 代码质量 + 论文质量
   - 工程能力 + 研究能力

3. **查看实际代码**
   - 对于高分候选人，访问 GitHub
   - 查看代码风格和文档质量
   - 检查 Issue 和 PR 讨论

4. **技术栈匹配**
   - GitHub 识别的技术栈 vs 职位要求
   - 优先选择完全匹配的

### **❌ DON'Ts (避免做法)**

1. **只看分数**
   - 分数仅供参考
   - 需要结合实际代码审查

2. **忽视低分候选人**
   - 可能只是不活跃在 GitHub
   - 实际能力可能很强

3. **过度依赖自动化**
   - 自动识别可能不准确
   - 需要人工验证

---

## 📊 预期效果

### **完整数据集 (462人)**

**估算:**
- 有 GitHub 链接: ~150-200人
- 成功获取信息: ~120-160人
- 高质量 (≥60分): ~60-80人

**Top 候选人预期:**
- GitHub 分数 70+: 20-30人
- Stars 500+: 10-15人
- 顶级开源贡献者: 5-8人

---

## 🚀 下一步行动

### **立即可用**

```bash
cd /Users/lillianliao/notion_rag/lamda_scraper
./run_github_enrichment.sh
```

### **完整流程**

```bash
# 步骤1: 数据采集 (2-3小时)
./run_full_collection.sh

# 步骤2: 评分分析 (5分钟)
python3 talent_analyzer.py \
  --input lamda_full.json \
  --output lamda_full_scored.csv

# 步骤3: GitHub 信息挖掘 (5-10分钟)
./run_github_enrichment.sh

# 步骤4: 查看最终结果
open lamda_candidates_github_enhanced.csv
```

---

## 📞 需要帮助？

**遇到问题?**
1. 检查网络连接
2. 验证 GitHub Token 是否有效
3. 查看 API 剩余配额

**定制需求?**
- 调整评分权重
- 添加新的技术栈识别
- 集成到其他系统

---

**最后更新:** 2026-01-08
**状态:** ✅ 已测试可用
**版本:** v1.0
