# LAMDA 猎头 - 快速参考卡

## 🚀 一键启动

```bash
cd /Users/lillianliao/notion_rag/lamda_scraper
./headhunter_workflow.sh
```

---

## 📊 评分速查表

### Tier 分类

| 总分 | Tier | 说明 | 猎头策略 |
|------|------|------|---------|
| ≥70 | A | 顶级人才 | 立即联系，重点维护 |
| 45-69 | B | 优质人才 | 近期联系，培养关系 |
| <45 | C | 普通人才 | 长期追踪，按需联系 |

### 优先级分类

| 时机 | 分数 | 优先级 | 联系时机 |
|------|------|--------|---------|
| 即将/刚毕业 | 15 | 🔥 Hot | 本周内 |
| 工作2-3年 | 15 | 🔥 Hot | 本周内 |
| 毕业1-2年 | 12 | Hot | 本月内 |
| 工作3-4年 | 10 | Warm | 2-4周内 |
| 工作1年内 | 8 | Warm | 1-2月内 |
| 在读/稳定 | 5-8 | Pool | 长期追踪 |

### 学术分速算

**顶会权重:**
```
ICML/NeurIPS/CVPR/ACL: 5分/篇
ICLR/ICCV/EMNLP/KDD/WWW: 4分/篇
AAAI/IJCAI/NAACL: 3分/篇
TPAMI: 6分/篇 | JMLR: 5分/篇
```

**导师加分:**
```
周志华: +20分 | 俞扬: +15分
张利军/姜远: +12分
其他核心导师: +10分
```

### 职业分速算

**公司分级:**
```
OpenAI/DeepMind: 25分
Google/Microsoft/Meta: 18-20分
字节/阿里/腾讯: 15分
华为/商汤/旷视: 12分
教授/研究员: 10分
```

### 触达分速算

**联系方式:**
```
公司邮箱: 15分 | 学校邮箱: 10分
LinkedIn: 8分 | GitHub: 3分
Scholar: 2分
```

---

## 🎯 猎头实战公式

### 优先级判断公式

```
优先级分数 = Tier分 × 2 + 时机分

Tier A = 10分 | Tier B = 6分 | Tier C = 3分
Hot = 15分 | Warm = 8分 | Pool = 5分

示例:
Tier A + Hot = 10×2 + 15 = 35分 → 立即联系
Tier B + Hot = 6×2 + 15 = 27分 → 近期联系
Tier A + Warm = 10×2 + 8 = 28分 → 本月联系
Tier B + Warm = 6×2 + 8 = 20分 → 培养关系
```

### 回复率预估

```
基础回复率 = Hot(60%) 或 Warm(40%) 或 Pool(20%)

加成:
+ 个性化消息: +20%
+ 公司邮箱: +15%
+ 提及论文: +10%
+ 提及导师: +10%

最终回复率 = 基础 + 加成 (最高80%)

示例:
Hot + 个性化 + 公司邮箱 + 提及论文
= 60% + 20% + 15% + 10% = 85% (实际限制80%)
```

---

## 📧 联系模板

### 模板1: Hot + Tier A（高优先级）

**主题:** AI人才机会 - [公司名] - [具体职位]

```
您好 [姓名]，

我是[公司]的猎头[名字]，关注到您在[会议名]发表的[论文方向]论文，
非常认同您的研究。

了解到您目前在[当前公司]，我们正在为[知名客户]寻找[具体职位]，
这与您在[具体方向]的专长高度契合。

[可选] 您的导师[导师名]在[领域]的贡献我也非常敬佩。

是否方便本周进行10分钟简短交流？

祝好，
[你的名字]
[LinkedIn]
[手机]
```

### 模板2: Warm + Tier B（中期联系）

**LinkedIn 消息:**
```
Hi [英文名],

I came across your publications at [会议名] on [方向] and was impressed.

I'm a tech recruiter specializing in AI/ML. I'd love to connect and share
opportunities that align with your background in [具体方向].

Best regards,
[你的名字]
```

### 模板3: 跟进消息（3-7天后）

**主题:** Re: 上次沟通 - [职位名称]

```
[姓名] 您好，

感谢上次关注。想和您同步一下：

[职位亮点1]
- [具体信息]
[职位亮点2]
- [具体信息]

团队还在扩充，如果您还在考虑机会，我们可以深入聊聊。

或者，如果您有朋友也在看机会，也欢迎推荐！

祝好，
[你的名字]
```

---

## ⚡ 快速决策树

```
候选人
  ├─ 有公司邮箱?
  │   ├─ 是 → 工作2-3年? → 是 → 🔥 立即联系
  │   │   │              └─ 否 → 📅 本周联系
  │   │   └─ 刚入职(<6月)? → 是 → ⏸️ 暂缓
  │   │                        └─ 否 → 🔥 立即联系
  │   └─ 否 → 有LinkedIn? → 是 → 📧 建立联系
  │                      └─ 否 → 📋 长期追踪
  │
  ├─ Tier A?
  │   ├─ 是 → 优先级最高
  │   └─ 否 → Tier B? → 是 → 次优先
  │                      └─ 否 → 按需联系
  │
  └─ 有顶会论文?
      ├─ ≥5篇 → 重点考虑
      ├─ 3-4篇 → 可以考虑
      └─ 1-2篇 → 辅助判断
```

---

## 📈 效果指标

**联系目标 (每月):**
- Hot 候选人: 20-30人
- Warm 候选人: 30-50人
- Pool 候选人: 按需

**转化目标:**
- 回复率: ≥40%
- 意向率: ≥15%
- 成功率: ≥10%

**投入时间:**
- 首次联系: 10分钟/人（消息定制）
- 电话沟通: 30分钟/人
- 面试辅导: 1-2小时/人

---

## 🔧 常用命令

```bash
# 启动工作流
./headhunter_workflow.sh

# 单独运行采集
python3 lamda_scraper.py --output [name] --delay 1.5

# 单独运行分析
python3 talent_analyzer.py --input [name].json --output [name]_scored.csv

# 深度采集
python3 tier_b_scraper.py --input [name].json --output priority.csv

# 查看帮助
python3 lamda_scraper.py --help
python3 talent_analyzer.py --help
```

---

## 📱 文件说明

| 文件 | 用途 | 打开方式 |
|------|------|---------|
| `*_scored.csv` | 评分结果 | Excel/Numbers |
| `priority_contacts.csv` | 优先联系人 | Excel/Numbers |
| `*_full.csv` | 原始数据 | Excel/Numbers |
| `HEADHUNTER_GUIDE.md` | 完整指南 | Markdown编辑器 |
| `QUICK_REFERENCE.md` | 本文件 | Markdown编辑器 |

---

## 💡 实战技巧

**高转化率组合:**
1. Hot 优先级
2. 有公司邮箱
3. 个性化消息（提及论文）
4. 提及导师（建立信任）

**低转化率组合:**
1. Pool 优先级
2. 无联系方式
3. 通用模板消息
4. 不了解候选人背景

**最佳实践:**
- ✅ 每天联系 5-10 个 Hot 候选人
- ✅ 每周跟进 20-30 个 Warm 候选人
- ✅ 每月更新一次人才库
- ✅ 定期分享行业资讯
- ❌ 避免群发通用消息
- ❌ 避免频繁联系 Pool 候选人

---

**最后更新:** 2026-01-07
**版本:** v1.0
