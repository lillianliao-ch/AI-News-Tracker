# 学术渠道扩展设计方案

**日期**: 2026-03-11  
**状态**: 设计阶段  
**项目**: 扩展现有 `github_mining` 项目，新增学术来源渠道

---

## 一、目标

在现有 GitHub 社交网络挖猎管道之外，**新增一条学术渠道**，直接从顶级 AI 学术会议和论文数据库中挖掘高质量华人AI人才。

### 核心诉求
1. **找到 AI 领域顶级华人学者**（发表过 NeurIPS/ICML/ICLR/ACL/CVPR 论文）
2. **拿到联系方式**：邮箱（优先）、GitHub URL、个人网页
3. **有 GitHub URL 的直接接驳现有管道**，无 GitHub 的也能直接入库

### 与现有渠道的互补性

| | GitHub 挖猎（现有） | 学术渠道（新增） |
|--|--|--|
| 覆盖人群 | 工程活跃、代码贡献者 | 论文发表者、研究员 |
| 质量信号 | Followers、Stars | h-index、引用数、顶会录用 |
| 联系方式 | commit 邮箱、bio | 论文邮箱、机构主页 |
| 盲区 | 不写代码的学者 | 不发论文的工程师 |

两条管道通过 `github_url` / `email` 在数据库自然去重，互不干扰。

---

## 二、数据来源（按优先级）

| 来源 | 获取方式 | 难度 | 数据质量 | AI 纯度 |
|------|---------|------|---------|--------|
| **ICLR** | OpenReview 官方 JSON API | ⭐ 最简单 | 极高（录用即质量保证） | 🟢 99% — 纯深度学习/表示学习 |
| **ACL** | aclanthology.org 结构化页面 | ⭐⭐ 简单 | 极高 | 🟢 95% — NLP 为主 |
| **NeurIPS** | 会议 Proceedings 页面 | ⭐⭐ 中等 | 极高 | 🟡 90% — 少量纯统计/优化/神经科学 |
| **ICML** | 会议 Proceedings 页面 | ⭐⭐ 中等 | 极高 | 🟡 90% — 少量运筹/博弈论 |
| **CVPR** | 会议 Proceedings 页面 | ⭐⭐ 中等 | 极高 | 🟢 95% — 纯计算机视觉 |
| **Semantic Scholar** | 官方免费 API | ⭐ 最简单 | 高（有 h-index、引用数） | — 辅助工具 |
| **arXiv** | 官方 API（XML） | ⭐⭐ 中等 | 中（预印本质量参差） | ⚠️ 需按 cs.AI/cs.LG 子类过滤 |

> **结论**：当前 5 大顶会天然是 AI 领域的黄金筛选器，不需要额外做 AI 过滤。
> 未来扩展到 AAAI/IJCAI（方向较杂）或 ArXiv 监控时，才需要加一层 AI 子领域过滤。
---

## 三、AI 学术人才挖掘全景图 (Sourcing Landscape)

要全面覆盖 AI 学术圈，除了目前规划的这几个顶会，完整的渠道版图应该包含四个维度（按转化价值排序）：

### 维度 1：顶级学术会议 (Top Conferences) - 核心主力
*当前已覆盖/规划的最核心渠道。*
1. **大模型/机器学习基座**: ICLR, NeurIPS, ICML (最高优)
2. **自然语言处理 (NLP)**: ACL, EMNLP, NAACL (最高优)
3. **计算机视觉 (CV)**: CVPR, ICCV, ECCV (最高优)
4. **数据挖掘与信息检索**: KDD, WWW, SIGIR (可扩展补充)
5. **综合人工智能**: AAAI, IJCAI (可扩展补充，但规模极大，需严格把控质量分)
6. **机器人 (Embodied AI)**: ICRA, IROS, CoRL (视特定岗位需求补充)

### 维度 2：教授门派挖猎 (Professor-Student Sourcing) - 极高精准度
*非常适合挖掘「高潜力但还未大量发paper」的 Ph.D. 和 Postdoc。*
- **方法**：系统已有现成的 `/professor-student-sourcing` workflow。
- **思路**：锁定全球 Top 100 华人 AI 教授（如 Andrew Ng, 宋韩, 何恺明, 李飞飞, 贾扬清, 张钹 等），定向爬取他们实验室 (Lab) 主页的 `People / Alumni` 页面。
- **优势**：能直接拿到这批最聪明大脑的下落和邮箱，完全不需要通过论文作为中间媒介。

### 维度 3：顶级工业界研究院 (Top Industry Labs) - 质量背书
- **目标**：DeepMind, OpenAI, Meta FAIR, MSRA, 阿里达摩院, 腾讯 AI Lab。
- **思路**：直接监控这些实验室发布的公开论文 (Publication Pages) 或技术报告 (Technical Reports)。
- **优势**：这些人既有强学术背景，又有极强的工程落地能力，是企业最喜欢的人才画像。

### 维度 4：最新预印本 (ArXiv Daily) - 抢占先机
- **目标**：每天监控 `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV` 分类下的新提交论文。
- **思路**：通过 arXiv API 每天抓取。
- **优势**：能在顶会出结果前半年，提前锁定爆款论文（如各种开源大模型技术报告）的第一作者。需要配合 Semantic Scholar 看作者历史成绩来降噪。

---

## 四、完整数据流

```
┌─────────────────────────────────────────────┐
│              学术种子采集 Phase A              │
│                                              │
│  ICLR OpenReview API  ─┐                    │
│  ACL Anthology        ─┼→ 作者名单           │
│  NeurIPS/ICML/CVPR    ─┘                    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              华人过滤 + 质量评分              │
│                                             │
│  detect_nationality(name) → 过滤外国人       │
│  Semantic Scholar API → h-index, 引用数      │
│                                             │
│  实际运行数据 (2025+2024 两年五大顶会):       │
│                                             │
│  2025: 30,964 条 → 去重 19,677 人           │
│    华人 12,027 + unknown 433 = 12,460       │
│    (ICLR: 9,515 | CVPR: 12,256)            │
│  2024: 63,595 条 → 去重 33,868 人           │
│    华人 16,983 + unknown 940 = 17,923       │
│    (ICLR: 7,648 | CVPR: 10,312 |           │
│     ICML: 9,798 | NeurIPS: 17,857)         │
│                                             │
│  跨年重复: 9,766 人                          │
│  两年合计唯一: 43,847 人                      │
│  去掉外国人后: ~24,880 华人+unknown           │
│  → S/A+ 高质量预计 ~2,500-3,700 人          │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              联系方式挖掘 Phase C            │
│                                             │
│  ① 论文 PDF → 提取邮箱（成功率 60-70%）      │
│  ② Semantic Scholar homepage → 爬个人主页   │
│     复用现有 _extract_profile_from_page()   │
│  ③ GitHub 关联（搜索、代码仓库链接）          │
│     → 有 GitHub URL：约 30-40% 的人         │
└──────────────┬───────────────┬──────────────┘
               │## 四、与现有管道的零成本对接 (已验证 ✅)

学术源采集中提取到的学者，会走向两条分支，**这两条分支都不需要修改现有核心代码**：

1. **有 GitHub URL 的学者 (`[prefix]_github_pipeline.json`)**
   - 字段已预设对齐现有的 `phase2_enriched` 格式。
   - 直接传给 `batch_runner.py` (从 `phase3` 阶段启动)。
   - Pipeline 会把他们当成普通的 GitHub 种子，去爬他们的 repos、生成 LLM 报告。

2. **只有邮箱/主页的纯学者 (`[prefix]_direct_import.json`)**
   - 现有数据库的 `Candidate.github_url` 字段允许为空 (nullable)。
   - 现有的 `import_github_candidates.py` 脚本支持基于 `email` 或 `name` 进行去重插入。
   - **结论**：直接运行 `import_github_candidates.py` 导入即可，**无需任何代码修改**。

---

## 五、新增文件

```
github_mining/scripts/
├── academic_miner.py          ← 🆕 核心：学术种子采集 + Semantic Scholar 查询
└── extract_paper_email.py     ← 🆕 辅助：主页 / PDF 联系方式提取 (待开发)
```

### `academic_miner.py` 主要功能

```python
class AcademicMiner:
    def phase_a1_collect_authors()   # 从顶会采集作者列表
    def phase_a2_semantic_scholar()  # 查询 h-index、主页、引用数
    def phase_b_filter_chinese()     # 国籍过滤（复用 detect_nationality）
    def phase_b_score()              # 学术质量评分
    def phase_c_extract_contacts()   # 联系方式挖掘（邮箱+GitHub）
    def export_to_batch_runner()     # 输出格式对齐 batch_runner 输入
```

### 输出字段（与现有数据库字段对齐）

```json
{
  "name": "Yuxin Fang",
  "email": "2yuxinfang@gmail.com",
  "github_url": "https://github.com/Yuxin-CV",
  "personal_website": "https://yuxinfang.github.io",
  "source": "scholar_iclr_2024",
  "h_index": 15,
  "citation_count": 3200,
  "conference": "ICLR 2024",
  "paper_count": 8,
  "affiliation": "HKU"
}
```

---

## 五、复用现有代码

| 现有函数/模块 | 位置 | 复用场景 |
|-------------|------|---------|
| `detect_nationality()` | `add_nationality_tags.py` | 华人筛选 |
| `_extract_profile_from_page()` | `github_network_miner.py:1272` | 个人主页解析 |
| `_fetch_scholar_data()` | `github_network_miner.py:1398` | Google Scholar 数据（已有实现！） |
| `phase3_5_enrich()` | `github_network_miner.py:1071` | 有 GitHub URL 后的主页爬取 |
| `batch_runner.py` | scripts/ | 批次管理、断点续传、DB 导入 |
| `import_github_candidates.py` | personal-ai-headhunter/ | 最终入库（幂等） |

---

## 六、质量评分标准（学术版）

| 级别 | h-index | 总引用 | 顶会论文 | 单位 |
|------|---------|--------|---------|------|
| **S** | ≥ 30 | ≥ 10,000 | ≥ 10 篇 | 顶级工业 Lab |
| **A+** | 20-29 | 5,000+ | 5-9 篇 | 顶级学校 |
| **A** | 10-19 | 1,000+ | 2-4 篇 | 知名学校 |
| **B** | 5-9 | 200+ | 1 篇 | 普通高校 |

---

## 七、预期产出

> **🎯 主力目标**：2025+2024 两年五大顶会华人 AI 学者，共计约 **24,880 人**。

| 指标 | 原始预估 | 实际 (2025+2024) |
|------|---------|------------------|
| 顶会论文-作者记录 | ~30,000 条 | **94,559 条** |
| 不重复作者 | ~25,000 人 | **43,847 人** |
| 跨年重复 | — | 9,766 人 |
| 华人+Unknown（过滤后） | ~8,000 人 | **~24,880 人** |
| S/A+ 级（h-index≥20） | 500-1,000 人 | 预计 ~2,500-3,700 人 |
| 有邮箱 | 待统计 | 待 S2 采集完成 |
| 有 GitHub URL | 待统计 | 待 S2 采集完成 |

**按会议/年度分布：**

| 会议 | 2025 | 2024 |
|------|-----:|-----:|
| ICLR | 9,515 | 7,648 |
| CVPR | 12,256 | 10,312 |
| ICML | — | 9,798 |
| NeurIPS | — | 17,857 |
| ACL | — | — |

> 实际数据远超原始预估。AI 纯度极高（>90%），不需要额外过滤。
> **S/A+ 比例预计 10-15%**（GitHub 管道约 3-5%），质量显著更高。

---

## 八、实施计划与进度

### Phase 1：数据采集打通（已完成 ✅）
- [x] ICLR OpenReview API v2 采集
- [x] ACL Anthology 作者采集
- [x] Semantic Scholar API 集成（h-index + 主页）
- [x] 华人过滤 + 质量打分
- [x] 验证与现有系统的**零代码修改导入**兼容性

### Phase 2：联系方式提取（基本完成 ✅）
- [x] 个人主页邮箱增强正则提取
- [x] 个人主页 GitHub URL 精准提取
- [ ] PDF 离线解析备用邮箱提取 (`pdfplumber`)（*按需扩展*）

### Phase 3：会议覆盖扩展（已完成 ✅）
- [x] NeurIPS / ICML / CVPR Proceedings 爬虫

### Phase 4：全量采集（🔄 进行中）

**当前批次**: `conference_full_20260311_131547`
**年份策略**: 2025 → 2024（串行，优先最新年份）
**状态**: 2025 年 S2 作者富化进行中（12,460 人）

| 阶段 | 2025 | 2024 |
|------|:----:|:----:|
| 论文采集 | ✅ 30,964 条 | ✅ 63,595 条 |
| 去重+国籍过滤 | ✅ 12,460 人 | ✅ 17,923 人 |
| S2 作者富化 | 🔄 进行中 | ⏳ 排队 (已缓存 740) |
| 联系方式提取 | ⏳ | ⏳ |
| DB 导入 | ⏳ | ⏳ |

> ⚠️ **瓶颈**: S2 API 免费版限流严重（~1 req/35s），已申请 API Key 待批准。
> 预计 2025 年采集完成需 ~8-9 天。

---

## 九、不做的事（边界）

- ❌ 不新建独立项目（直接扩展现有 `github_mining`）
- ❌ 不引入新数据库（全部走现有 SQLite）
- ❌ 不处理付费数据源（只用免费 API）
- ❌ Phase 1 未跑通前不做 Phase 2
