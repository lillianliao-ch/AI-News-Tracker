# GitHub Mining 全流程批次隔离 —— 设计方案 v3

## 一、设计目标

1. 每次跑批产生独立文件夹，input/output 完整保存，批次间绝对隔离
2. 写最终文件前备份旧文件（仅最终写，中间保存不备份）
3. 外国人/机构在 Phase 3 前过滤，节约 API + token；**unknown 国籍继续保留**
4. 批次完整血缘记录：种子名单、following数量、各级过滤统计，供事后分析
5. DB import 天然幂等（按 `github_url` 去重），数据不丢不重
6. 验证全流程端到端无人值守，30人规模，一次通过后即为生产就绪状态

---

| 阶段 | 输入 | 输出 | 说明 |
|------|------|------|------|
| **Pre-filter** | 原始候选人 JSON | `pre_filtered.json` | 机构/明确外国人过滤；零 API；unknown 保留 |
| **DB Dedup** | Pre-filter 输出 | `db_deduped.json` | 查询数据库中 `github_url`，提前过滤重复候选人，节约 token |
| **Phase 3** | DB Dedup 输出 | `phase3_enriched.json` | GitHub repos + 评分（GitHub API） |
| **Phase 3.5** | Phase 3 输出 | `phase3_5_enriched.json` | 个人主页爬取 |
| **Phase 4.5** | Phase 3.5 输出 | `phase45_final.json` | LLM 深度富化（最昂贵） |
| **DB Import** | Phase 4.5 输出 | 数据库 | `--dry-run` 先预览，再正式；天然幂等 |

### Pre-filter & DB Dedup 规则

| 规则 | 依据 | 处置 |
|------|------|------|
| `type == 'Organization'` | GitHub 原始字段 | 排除 |
| 机构黑名单 / `-bot`, `-team` 命名特征 | 本地规则 | 排除 |
| `detect_nationality()` = `foreign` | 姓名 + 公司（非地理位置） | 排除 |
| `detect_nationality()` = `chinese` 或 `unknown` | 同上 | **保留** |

---

## 三、批次目录结构

```
scripts/runs/
└── 20260311_080000_phase5_batch1/
    ├── batch_meta.json          ← 完整血缘 + 各阶段统计（见下）
    ├── inputs/
    │   └── [原始input].json     ← input副本，绝不改动
    ├── outputs/
    │   ├── pre_filtered.json
    │   ├── db_deduped.json
    │   ├── phase3_enriched.json
    │   ├── phase3_5_enriched.json
    │   └── phase45_final.json
    └── logs/
        ├── pre_filter.log
        ├── phase3_[ts].log
        ├── phase3_5_[ts].log
        └── phase4_5_[ts].log
```

### batch_meta.json 内容（完整血缘）

```json
{
  "batch_id": "20260311_080000_phase5_batch1",
  "start_time": "...", "end_time": "...", "status": "done",
  "input_file": "...", "phases": [...],

  "lineage": {
    "seed_users": ["user1", "user2", ...],        // 种子用户名单
    "total_following_found": 28242,                // 所有种子 follow 的人数
    "prefilter": {
      "input_count": 28242,
      "org_filtered": 150,
      "foreign_filtered": 10318,
      "unknown_nationality": 3200,
      "chinese_nationality": 7350,
      "output_count": 10543
    },
    "phase3":   { "input": 10543, "output": 10543, "skipped_resume": 0 },
    "phase3_5": { "input": 10543, "output": 8200, "with_homepage": 5100 },
    "phase4_5": { "input": 8200,  "output": 8200, "llm_success": 7800 },
    "db_import": {
      "dry_run_new": 5000, "dry_run_update": 3200,
      "actual_new": 5000,  "actual_update": 3200,
      "skipped_duplicate": 3200
    }
  }
}
```

---

## 四、各脚本改动

| 脚本 | 改动 | 状态 |
|------|------|------|
| `batch_runner.py` | 全新创建，控制完整流程 | ❌ 待做 |
| `github_network_miner.py` phase3 | `--output` + `_save_json_safe` | ✅ 已做 |
| `github_network_miner.py` phase3_5 | 增加 `--output` 参数 | ❌ 待做 |
| `run_phase4_5_llm_enrichment.py` | `--input` / `--output` 参数 + 最终写备份 | ❌ 待做 |
| `import_github_candidates.py` | 确认幂等性（按 github_url 去重） | 需确认 |

### DB Import 幂等性保证

`import_github_candidates.py` 按以下顺序去重，任一命中则更新而非重复插入：
1. `github_url`（唯一性最高）
2. `email`
3. `name`（非 username 时）

因此可以安全重跑，不会产生重复记录。

---

## 五、断点续传

```bash
# 续传中断批次
python3 batch_runner.py --resume-batch runs/20260311_080000_xxx

# 逻辑：读 batch_meta.json → 对每个 phase：
#   outputs/ 下已有文件 → 传 --resume 续跑
#   没有文件 → 全新运行该阶段
```

---

## 六、验证计划（V1 = 端到端全流程验证）

**目标**：30人规模，无人值守，全流程端到端，一次通过则生产就绪

```bash
nohup python3 batch_runner.py \
  --input phase5_pre_filtered_input.json \
  --phases prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import \
  --max-users 20 \
  --batch-name "e2e_validation_20" \
  --db-dry-run-first \         # 先 dry-run DB import，人工确认后再正式导入
  > runs/e2e_validation_20.log 2>&1 &
```

**检验点**（全部通过才算验证成功）：

| 项 | 检验命令 | 预期 |
|----|---------|------|
| 批次目录完整 | `ls runs/[ts]/inputs outputs logs` | 三个子目录都存在 |
| input 副本存在 | `ls runs/[ts]/inputs/` | 原文件副本 |
| Pre-filter 统计合理 | `cat batch_meta.json | jq .lineage.prefilter` | org+foreign > 0 |
| Phase 3 输出 ≤30 人 | jq len | ≤30 |
| Phase 3.5 有主页爬取标记 | jq `[.[] | select(.homepage_scraped)]` | > 0 人 |
| Phase 4.5 LLM 字段存在 | jq `[.[] | select(.talking_points)]` | > 0 人 |
| DB dry-run 统计合理 | cat batch_meta.json | new + update > 0 |
| 正式导入后无重复 | 重跑 import，skipped_duplicate == 上次 new | 相等 |
| 软链接正确 | `readlink phase3_enriched_latest.json` | 指向本批次 |
| 备份文件存在 | `ls outputs/*.bak_*` | ≥1 个 |

### V2：正式全量（V1 通过且用户确认后）

```bash
python3 batch_runner.py \
  --input phase5_pre_filtered_input.json \
  --phases prefilter,phase3,phase3_5,phase4_5,db_import \
  --batch-name "phase5_production"
```

---

## 七、不做的事（边界）

- ❌ 不动 `_save_json`（高频中间保存，不备份）
- ❌ 不自动清理 `runs/` 目录
- ❌ V1 未通过前不执行 V2
- ❌ 不改动本次范围外的脚本
