# Batch Runner 改进总结

**日期**: 2026-03-11
**版本**: v1.1

---

## ✅ 已完成的改进

### 1. 自动备份机制（防止同一批次内覆盖）

**问题**: 同一批次内多次运行同一阶段会覆盖之前的输出

**解决方案**:
- 添加 `safe_backup_if_exists()` 函数（line 102-125）
- 在 3 个关键函数中调用备份：
  - `run_phase3()` - line 317
  - `run_phase3_5()` - line 360
  - `run_phase4_5()` - line 402

**效果**:
```
第1次运行: outputs/phase3_enriched.json
第2次运行:
  - 备份: outputs/phase3_enriched_backup_083249.json
  - 新文件: outputs/phase3_enriched.json
第3次运行:
  - 备份: outputs/phase3_enriched_backup_091530.json
  - 新文件: outputs/phase3_enriched.json
```

**测试结果**: ✅ 通过（test_backup.py）

---

### 2. 评级逻辑（Tier Update）

**问题**: 批次流程缺少评级阶段，导入数据库后没有自动评级

**解决方案**:
- 添加 `run_tier_update()` 函数（line 480-520）
- 在批次流程中添加 `tier_update` 阶段（line 638-642）
- 更新默认 phases 参数（line 789）

**完整流程**:
```
prefilter → db_dedup → phase3 → phase3_5 → phase4_5 → db_import → tier_update
```

**评级标准**:
- S: Followers>5k OR Stars>5k OR H-index>30
- A+: 3+ 顶会论文
- A: 顶尖 Lab
- B+: 一线大厂 + 985高校
- B: 一线大厂 OR 985+二线大厂 OR Followers>500
- C: 普通 AI 开发者

---

## 📋 使用方法

### 完整端到端流程

```bash
python3 batch_runner.py \
  --input phase5_pre_filtered_input.json \
  --phases prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update \
  --max-users 30 \
  --batch-name "e2e_validation"
```

### 只运行评级（已导入数据的情况）

```bash
python3 batch_runner.py \
  --input dummy.json \
  --phases tier_update \
  --batch-name "tier_only"
```

### 跳过某些阶段

```bash
# 跳过 prefilter 和 db_dedup
python3 batch_runner.py \
  --input seeds.json \
  --phases phase3,phase3_5,phase4_5,db_import,tier_update \
  --skip-prefilter \
  --skip-db-dedup
```

---

## 🔍 验证方法

### 1. 验证备份机制

```bash
# 运行测试
python3 test_backup.py

# 预期输出
✅ 自动备份成功
✅ 生成了 2 个备份文件
🎉 测试通过！
```

### 2. 验证评级逻辑

```bash
# 运行一个小批次
python3 batch_runner.py \
  --input test_seeds.json \
  --phases db_import,tier_update \
  --max-users 10

# 检查 batch_meta.json
cat runs/*/batch_meta.json | grep tier_update

# 预期输出
"tier_update": {
  "exit_code": 0,
  "total_updated": 10,
  "tier_S": 2,
  "tier_A": 3,
  "tier_B": 5
}
```

### 3. 验证数据库

```bash
# 检查数据库中的评级
sqlite3 personal-ai-headhunter/data/headhunter_dev.db \
  "SELECT tier, COUNT(*) FROM candidates WHERE source='github' GROUP BY tier;"

# 预期输出
S|27
A|76
B+|239
B|130
C|14
```

---

## 📊 批次流程图

```
输入文件 (phase5_pre_filtered_input.json)
    │
    ├─→ prefilter (过滤机构和外国人)
    │       └─→ outputs/pre_filtered.json
    │
    ├─→ db_dedup (数据库去重)
    │       └─→ outputs/db_deduped.json
    │
    ├─→ phase3 (GitHub repos 富化)
    │       └─→ outputs/phase3_enriched.json
    │       └─→ 备份: phase3_enriched_backup_*.json
    │
    ├─→ phase3_5 (个人主页爬取)
    │       └─→ outputs/phase3_5_enriched.json
    │       └─→ 备份: phase3_5_enriched_backup_*.json
    │
    ├─→ phase4_5 (LLM 深度富化)
    │       └─→ outputs/phase45_final.json
    │       └─→ 备份: phase45_final_backup_*.json
    │
    ├─→ db_import (导入数据库)
    │       └─→ 新增/更新候选人
    │
    └─→ tier_update (自动评级) ✨ 新增
            └─→ 更新 tier 字段 (S/A+/A/B+/B/C)
```

---

## 🎯 下一步

### 立即可用
- ✅ 批次隔离完善（零数据丢失）
- ✅ 自动备份机制（防止覆盖）
- ✅ 评级逻辑完整（自动分级）

### 可以开始跑大批次了！

建议的第一个大批次：
```bash
python3 batch_runner.py \
  --input phase5_expanded_latest.json \
  --phases prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update \
  --batch-name "phase5_production" \
  > batch.log 2>&1 &

# 监控进度
tail -f batch.log
```

---

## 📝 文件清单

| 文件 | 说明 |
|------|------|
| `batch_runner.py` | 批次管理器（已更新） |
| `test_backup.py` | 备份机制测试脚本 |
| `personal-ai-headhunter/batch_update_tiers.py` | 评级脚本 |
| `personal-ai-headhunter/data/company_tier_config.json` | 评级配置 |

---

**更新人**: Claude
**测试状态**: ✅ 通过
**生产就绪**: ✅ 是
