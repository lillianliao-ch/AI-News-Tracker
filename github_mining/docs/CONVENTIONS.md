# 脚本与数据规范 (CONVENTIONS)

> ⚠️ **AI 开发者必读** — 编写或修改任何脚本前，必须遵守以下规范。  
> 违反规范已导致多次生产事故，详见 [事件记录](#历史事件)。

---

## 🚨 零号规则：禁止直接写新脚本

**在写任何新脚本或新文件之前，必须先执行以下检查，缺一不可：**

```
步骤 1: ls scripts/*.sh scripts/*.py | cat           ← 列出所有现有脚本
步骤 2: 阅读最相关的脚本（至少读 --help 和头部注释）
步骤 3: 问自己：能否只改参数/路径/变量直接用现有脚本？
步骤 4: 如果现有脚本有硬编码路径 → 参数化它，而不是复制一份
步骤 5: 只有现有脚本结构上无法满足需求时，才允许写新文件
```

**已验证的可复用脚本清单（优先使用）**：

| 任务 | 脚本 | 关键参数 |
|------|------|---------|
| Serper 联系方式提取 | `run_serper_all_tiers.sh` | 修改头部 KEY/INPUT/OUTPUT_DIR |
| 学术管道（采集→S2→入库）| `academic_pipeline.sh` | `--year --phase --run-dir` |
| GitHub 网络挖掘批次 | `batch_runner.py` | `--input --phases --batch-name` |
| 进度监控 | `check_pipeline_status.sh` | 无需改动 |
| Telegram 通知 | `telegram_notifier.py` `notify()` | 直接 import |

> ❌ **违规示例（已发生）**：  
> 有 `run_serper_all_tiers.sh` 的情况下，写了 `auto_serper_relay.sh` 和 `run_serper_2019_2022.sh`  
> 正确做法：直接修改 `run_serper_all_tiers.sh` 的头部变量，或给它加 `$1` 参数支持

---

## 1. 文件命名规范

### 规则：所有输出文件必须包含 `{年份}` 和 `{时间戳}`

```
✅ 正确:
all_conf_2024_20260314_174059_full.json
serper_cache_2025_20260315.json
deep_cache_2024_20260315_145635.json
llm_enrichment_2024_20260315.json

❌ 错误:
_serper_cache.json          ← 无年份，无法区分批次
_deep_cache.json            ← 多年份共用，导致覆盖
enrichment_cache.json       ← 不知道属于哪次运行
```

### 命名模板

```
{类型}_{年份}_{YYYYMMDD_HHMMSS}.json
```

| 类型 | 示例 |
|------|------|
| 论文数据 | `all_conf_2024_20260314_174059_full.json` |
| Serper 缓存 | `serper_cache_2024_20260315.json` |
| Deep 缓存 | `deep_cache_2024_20260315.json` |
| LLM 结果 | `llm_enrichment_2024_20260315.json` |
| PDF 缓存 | `enrichment_cache_2024_20260315.json` |

---

## 2. 缓存字段名统一

### 规则：所有缓存文件使用相同的字段名

| 字段 | 标准名 | ❌ 不要用 |
|------|--------|----------|
| 主页 URL | `homepage` | `homepage_url`, `personal_website` |
| 邮箱列表 | `emails` | `all_emails`, `email` |
| 匹配邮箱 | `matched_email` | — |
| GitHub | `github` | `github_url` |
| LinkedIn | `linkedin` | `linkedin_url` |
| 主页文本 | `homepage_text` | — |

### 缓存 key 规范

```
✅ 标准: 直接用 name 作为 key
   "Jun Chen": { "homepage": "...", "emails": [...] }

❌ 不要: 加前缀
   "serper::Jun Chen": { ... }
   "deep_homepage::Jun Chen::https://...": { ... }
```

> 已有的旧缓存暂不改动，但**新脚本必须遵守此规范**。  
> 分析代码读取旧缓存时，必须处理前缀兼容（参见 `find_cache` 函数）。

---

## 3. 目录隔离规范

### 规则：不同年份使用独立的 run 目录

```
✅ 正确:
data/academic/runs/
├── pipeline_2025_20260314_225620/
│   └── outputs/
│       ├── all_conf_2025_..._full.json
│       ├── serper_cache_2025_....json
│       └── deep_cache_2025_....json
├── pipeline_2024_20260315_070000/
│   └── outputs/
│       └── ...
└── pipeline_2023_20260315_070407/
    └── outputs/
        └── ...

❌ 错误:
data/academic/runs/conference_full_20260311_131547/
└── outputs/
    ├── all_conf_2025_..._full.json    ← 2025 和 2024 混在一起
    ├── all_conf_2024_..._full.json
    ├── _serper_cache.json             ← 不知道属于哪年
    └── _deep_cache.json
```

### 共用目录的风险
- `find_cache` 找到错误年份的缓存文件
- Deep 爬取跳过了目标年份的人（**2024 事故原因**）
- 缓存互相覆盖

---

## 4. 脚本开发规范

### 4.1 环境变量

| 变量 | 用途 | 必须显式设置 |
|------|------|:---:|
| `DB_PATH` | 数据库路径 | ✅ 必须 |
| `S2_API_KEY` | Semantic Scholar | ✅ |
| `SERPER_API_KEY` | Serper 搜索 | ✅ |

> ⚠️ **绝对不要**依赖 CWD 推断 DB 路径，必须显式指定。

### 4.2 入库规则

1. **跨源绝不更新** — 不同渠道 (academic/github/脉脉) 的记录只能 INSERT，不能 UPDATE
2. **同源用 s2_id 匹配** — academic 记录用 `s2_id` 精确匹配，不用 `name`
3. **生产库操作前必须 `--dry-run`** — 先看报告再决定

### 4.3 输出要求

- 每个脚本运行必须输出**处理摘要**（总数、成功、失败、跳过）
- 长时间任务必须输出**进度信息**（每 N 条或每 M 秒）
- 出错时必须输出**详细错误信息**，不能静默失败

---

## 5. Pipeline 规范

### 5.1 `academic_pipeline.sh` 使用规则

```bash
# 新年份：从头开始，自动创建独立目录
./scripts/academic_pipeline.sh --year 2023 --phase all

# 续跑：必须指定 --run-dir 明确目录
./scripts/academic_pipeline.sh --year 2024 --phase deep \
  --run-dir data/academic/runs/pipeline_2024_20260315

# ❌ 不要：不同年份指向同一个 run-dir
```

### 5.2 缓存查找优先级

`find_cache` 在 `$CACHE_DIR` 中按以下优先级查找，**必须确保同一目录下不会有多年份的同名文件**：

1. `serper_cache_${YEAR}.json` (新规范)
2. `_serper_cache.json` (旧命名，兼容)
3. `all_conf_${YEAR}_contact_cache.json` (旧命名，兼容)

---

## 历史事件

| 日期 | 事件 | 原因 | 影响 |
|------|------|------|------|
| 2026-03-14 | 跨源污染 | `--update` 按 name 匹配，academic 覆盖 github 记录 | 242 条记录被污染 |
| 2026-03-14 | 影子 DB | CWD 不对，写入了错误的 DB 文件 | 数据丢失 |
| 2026-03-15 | 分析字段名错误 | Serper 用 `homepage`，分析代码查 `homepage_url` | 得出完全相反的结论 |
| 2026-03-15 | **2024 Deep 跳过** | 多年份共用目录 + `_serper_cache.json` 无年份标识 | 11,378 人未被处理 |

---

**最后更新**: 2026-03-15  
**维护者**: Academic Pipeline Team
