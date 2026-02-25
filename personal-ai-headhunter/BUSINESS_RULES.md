# AI猎头系统 — 业务规则与逻辑

> 单一文档，记录所有数据处理、评级、标准化、匹配的业务规则。
> 最后更新: 2026-02-25

---

## 1. 候选人评级 (Talent Tier)

**脚本**: `batch_update_tiers.py`  
**配置**: `data/company_tier_config.json`  
**Skill**: `.agent/skills/tier-evaluation/SKILL.md`

### 评级优先级: S > A+ > A > D > B+ > B > C

| Tier | 条件 | 说明 |
|------|------|------|
| **S** | AI领域 + (Followers>5000 / Stars>5000 / H-index>30) | 行业领军 |
| **A+** | 3+ 顶会论文 | 顶会多产作者 |
| **A** | 顶尖Lab | FAIR/MSRA/Google Brain 等 |
| **A** | tier1 公司 + 985 Top20 高校 | 一线大厂+顶尖名校 |
| **D** | 非AI方向 (前端/移动端等) 且无AI信号 | 方向不符，提前排除 |
| **B+** | tier1 公司 + 985 高校 (全部) | 一线+名校 |
| **B** | tier1 公司 or 985 高校 | 满足其一 |
| **B** | tier2 公司 | 二线大厂 |
| **B** | Followers > 500 | GitHub 影响力 |
| **C** | 默认 | 无显著信号 |

### 重跑评级

```bash
cd personal-ai-headhunter
python3 batch_update_tiers.py all       # 全量
python3 batch_update_tiers.py github    # GitHub 源
python3 batch_update_tiers.py yesterday # 昨日新增
```

脉脉/LinkedIn 来源需内联脚本，详见 `.agent/skills/tier-evaluation/SKILL.md`。

---

## 2. 公司名标准化 (company_normalized)

**脚本**: `normalize_companies.py`  
**配置**: `data/company_aliases.json`  
**字段**: `candidates.company_normalized`

### 规则

1. 每个候选人有 `current_company` (原始值) 和 `company_normalized` (标准化后)
2. **写入自动触发**: SQLAlchemy `set` event 监听 `current_company`，自动填充 `company_normalized`
3. 搜索和统计优先使用 `company_normalized`

### 匹配策略

| 优先级 | 方法 | 示例 |
|--------|------|------|
| 1 | 精确匹配 (大小写不敏感) | `ByteDance` → `字节跳动` |
| 2 | 子串匹配 (英文用词边界) | `Alibaba Group` → `阿里巴巴` |
| 3 | 未匹配保留原名 | `未知创业公司` → `未知创业公司` |

### ⚠️ 安全规则

> [!CAUTION]
> **禁止使用中文简称做子串匹配**。
> `北大`/`南大`/`浙大`/`阿里`/`字节` 等短别名会导致 `东北大学` → `北京大学` 等误匹配。
> `company_aliases.json` 中只允许**中文全名**和**英文全名/缩写**(如 MSRA, FAIR, NUS)。

### LinkedIn 数据清洗

导入时自动去除后缀: `ByteDance · 正式` → `ByteDance`，`正式 · 4年10个月` → NULL

### 手动操作

```bash
python3 normalize_companies.py          # 增量 (补空)
python3 normalize_companies.py --all    # 全量重跑
python3 normalize_companies.py --stats  # 查看统计
```

---

## 3. 学校名标准化

**存储**: `candidates.education_details` JSON 数组中的 `school` 字段

### 规则

1. 脉脉源数据已是中文全名，通常不需标准化
2. GitHub/LinkedIn 英文学校名通过 `company_aliases.json` 中的大学映射转换
3. **只允许精确全名匹配 + 前缀匹配**，不允许短别名子串匹配
4. 带国家前缀自动去除: `美国卡内基梅隆大学` → `卡内基梅隆大学`

---

## 4. 公司分级配置

**文件**: `data/company_tier_config.json`

| 分类 | 用途 | 示例 |
|------|------|------|
| `tier1_companies` | 一线大厂/核心AI公司 | Google, Meta, 字节跳动, DeepSeek, 月之暗面 |
| `tier2_companies` | 二线大厂/知名科技公司 | AMD, Qualcomm, 联想, 中兴 |
| `top_labs` | 匹配即 A 级的顶尖实验室 | FAIR, MSRA, Google Brain, DeepMind |
| `985_top20` | 985 排名前20 + 海外顶尖 (A级用) | 清华/北大/浙大 + Stanford/MIT/CMU |
| `985_universities` | 全部 985 + 海外名校 (B+/B级用) | 全部39所985 + 港三校/NUS/NTU |

### 更新规则

- 新增公司/学校: 编辑 JSON 后重跑 `batch_update_tiers.py all`
- **中英文都要加**: 如新增一家公司, 必须同时加中文名和英文名
- **不加简称**: 只用全名 (见安全规则)

---

## 5. 批次报告 (batch_runs 表)

**脚本**: `import_batch_report.py`  
**表**: `batch_runs`

### 记录内容

每次 Pipeline 运行自动记录:
- **漏斗**: 输入人数 → 入库人数 → 去重跳过
- **评级分布**: S/A+/A/B+/B/C/D 各多少人
- **可联系覆盖率**: Email/LinkedIn/GitHub/Phone/Website 各多少人
- **DB全局快照**: 当前总候选人/GitHub总数/LinkedIn总数

### 手动操作

```bash
python3 import_batch_report.py --list                                    # 查看所有批次
python3 import_batch_report.py --source github --batch-id "github_0225"  # 按来源快照
python3 import_batch_report.py path/to/batch_report.json                 # 导入JSON
```

---

## 6. 数据来源与渠道

| 来源 | source 字段值 | 特征 |
|------|---------------|------|
| GitHub Mining | `github` | 英文为主，有 GitHub/Email/Website |
| 脉脉 | `脉脉` | 中文为主，有 Phone，少 Email/LinkedIn |
| LinkedIn | `linkedin` | 中英混合，有 LinkedIn |
| 手动录入 | `手动录入(quick/standard)` | 取决于录入者 |
| 简历解析 | `PDF解析`/`图片OCR` | 取决于简历语言 |

---

## 7. 触达与跟进

### Pipeline 阶段

`new` → `contacted` → `following_up` → `replied` → `wechat_connected` → `in_pipeline` → `closed`

### Stop Rule

- 每个候选人最多触达 3 次 (outreach_count)
- 超过 3 次无响应标记为 `no_response`

### 渠道优先级

LinkedIn > 脉脉 > Email > 电话

---

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-02-25 | 评级逻辑: A=tier1+985top20, B+=tier1+985all, B=tier1 or 985all |
| 2026-02-25 | 公司名标准化系统 (company_normalized + SQLAlchemy event) |
| 2026-02-25 | 移除中文简称避免子串误匹配 |
| 2026-02-25 | 批次报告入库 (batch_runs 表) |
| 2026-02-25 | 补充公司中英文对照 (tier1/tier2) |
