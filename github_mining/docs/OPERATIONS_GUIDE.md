# GitHub Mining 实战操作指南

**最后更新**: 2026-03-11

---

## 📋 目录

1. [快速开始](#快速开始)
2. [完整批次流程](#完整批次流程)
3. [批次管理](#批次管理)
4. [常见操作场景](#常见操作场景)
5. [数据验证](#数据验证)
6. [操作检查清单](#操作检查清单)

---

## 🚀 快速开始

### 环境准备

```bash
# 1. 检查 Python 版本
python3 --version  # 需要 3.8+

# 2. 检查磁盘空间
df -h  # 需要至少 10GB 可用空间

# 3. 检查工作目录
cd /Users/lillianliao/notion_rag/github_mining/scripts
pwd
```

### Token 配置

```bash
# 编辑配置文件
vim github_hunter_config.py

# 配置内容
GITHUB_TOKENS = [
    "ghp_xxxxx",  # Token 1
    "ghp_yyyyy",  # Token 2
]
DASHSCOPE_API_KEY = "sk-xxxxx"
```

### 第一次运行

```bash
# 运行一个小批次测试（10 人）
python3 batch_runner.py \
  --input test_input_50.json \
  --phases prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update \
  --batch-name "first_test"
```

---

## 📊 完整批次流程

### 从头开始跑批次

```bash
# 1. 准备输入文件
# 确保输入文件存在
ls -lh github_mining/phase5_expanded_latest.json

# 2. 启动批次（后台运行）
nohup python3 batch_runner.py \
  --input github_mining/phase5_expanded_latest.json \
  --phases prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update \
  --batch-name "production_$(date +%Y%m%d)" \
  > batch.log 2>&1 &

# 3. 记录 PID
echo $! > batch.pid
echo "批次已启动，PID: $(cat batch.pid)"
```

### 监控进度

```bash
# 方法1: 查看日志
tail -f batch.log

# 方法2: 查看批次状态
python3 batch_runner.py --list

# 方法3: 查看输出文件大小
watch -n 30 'ls -lh runs/*/outputs/*.json'

# 方法4: 查看已处理人数
python3 -c "
import json
from pathlib import Path
latest_batch = sorted(Path('runs').glob('*'))[-1]
phase3_file = latest_batch / 'outputs' / 'phase3_enriched.json'
if phase3_file.exists():
    data = json.load(open(phase3_file))
    print(f'Phase 3 已处理: {len(data)} 人')
"
```

### 验证结果

```bash
# 1. 检查批次是否完成
cat runs/*/batch_meta.json | grep status

# 2. 查看统计信息
cat runs/*/batch_meta.json | jq '.lineage'

# 3. 查看 Rich Summary
cat runs/*/batch_meta.json | jq '.rich_summary'

# 4. 验证数据库
sqlite3 ../../personal-ai-headhunter/data/headhunter_dev.db \
  "SELECT COUNT(*) FROM candidates WHERE source='github' AND DATE(created_at) = DATE('now');"
```

---

## 🗂️ 批次管理

### 批次隔离系统

**目录结构**:
```
runs/
└── 20260311_104622_phase5_production/
    ├── batch_meta.json          # 批次元数据
    ├── inputs/                  # 输入文件副本
    │   └── phase5_expanded_latest.json
    ├── outputs/                 # 输出文件
    │   ├── pre_filtered.json
    │   ├── db_deduped.json
    │   ├── phase3_enriched.json
    │   ├── phase3_5_enriched.json
    │   └── phase45_final.json
    └── logs/                    # 日志文件
        ├── phase3_104623.log
        ├── phase3_5_104830.log
        └── phase4_5_105200.log
```

### 自动备份机制

**同一批次内多次运行会自动备份**:
```
outputs/
├── phase3_enriched.json              # 当前版本
├── phase3_enriched_backup_104623.json  # 第一次备份
└── phase3_enriched_backup_110530.json  # 第二次备份
```

### 断点续传

```bash
# 批次中断后，使用 --resume-batch 继续
python3 batch_runner.py \
  --resume-batch runs/20260311_104622_phase5_production
```

**工作原理**:
- 读取 `batch_meta.json` 查看已完成的阶段
- 跳过已完成的阶段
- 从中断的地方继续执行

---

## 🎯 常见操作场景

### 场景1: 只跑某几个阶段

```bash
# 只跑 Phase 3 和 Phase 3.5
python3 batch_runner.py \
  --input db_deduped.json \
  --phases phase3,phase3_5 \
  --batch-name "phase3_only"
```

### 场景2: 跳过某个阶段

```bash
# 跳过 Pre-filter（不推荐）
python3 batch_runner.py \
  --input phase5_expanded_latest.json \
  --phases db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update \
  --skip-prefilter \
  --batch-name "no_prefilter"
```

### 场景3: 重跑失败的批次

```bash
# 1. 找到失败的批次
python3 batch_runner.py --list | grep error

# 2. 使用 --resume-batch 重跑
python3 batch_runner.py \
  --resume-batch runs/20260311_104622_failed_batch
```

### 场景4: 测试小批次

```bash
# 创建小输入文件
python3 -c "
import json
data = json.load(open('github_mining/phase5_expanded_latest.json'))
with open('test_input_50.json', 'w') as f:
    json.dump(data[:50], f, indent=2)
"

# 运行测试
python3 batch_runner.py \
  --input test_input_50.json \
  --phases prefilter,db_dedup,phase3,phase3_5,phase4_5,db_import,tier_update \
  --batch-name "test_50"
```

---

## ✅ 数据验证

### 验证 Pre-filter 效果

```bash
# 查看过滤统计
cat runs/*/batch_meta.json | jq '.lineage.prefilter'

# 预期输出
{
  "input_count": 28242,
  "org_filtered": 22,
  "foreign_filtered": 12748,
  "chinese": 7982,
  "unknown": 7490,
  "output_count": 15472
}
```

### 验证 DB Dedup 效果

```bash
# 查看去重统计
cat runs/*/batch_meta.json | jq '.lineage.db_dedup'

# 预期输出
{
  "input_count": 15472,
  "existing_in_db": 4975,
  "output_count": 10497
}
```

### 验证入库结果

```bash
# 查看入库统计
cat runs/*/batch_meta.json | jq '.lineage.db_import'

# 查询数据库
sqlite3 ../../personal-ai-headhunter/data/headhunter_dev.db "
SELECT
  COUNT(*) as total,
  COUNT(CASE WHEN talent_tier='S' THEN 1 END) as S,
  COUNT(CASE WHEN talent_tier='A' THEN 1 END) as A,
  COUNT(CASE WHEN talent_tier='B' THEN 1 END) as B,
  COUNT(CASE WHEN talent_tier='C' THEN 1 END) as C
FROM candidates
WHERE source='github'
  AND DATE(created_at) = DATE('now');
"
```

### 验证评级分布

```bash
# 查看评级统计
cat runs/*/batch_meta.json | jq '.rich_summary.tiers_actual'

# 预期输出
{
  "S": 10,
  "A+": 5,
  "A": 20,
  "B+": 50,
  "B": 100,
  "C": 50,
  "D": 5
}
```

---

## 📋 操作检查清单

### ✅ 跑批前检查清单

- [ ] **Token 是否有效**
  ```bash
  curl -H "Authorization: token ghp_xxxxx" https://api.github.com/user
  ```

- [ ] **磁盘空间是否充足**（> 10GB）
  ```bash
  df -h | grep /Users
  ```

- [ ] **上次批次是否已完成**
  ```bash
  python3 batch_runner.py --list | tail -1
  ```

- [ ] **输入文件是否存在**
  ```bash
  ls -lh github_mining/phase5_expanded_latest.json
  ```

- [ ] **数据库是否可访问**
  ```bash
  sqlite3 ../../personal-ai-headhunter/data/headhunter_dev.db "SELECT COUNT(*) FROM candidates;"
  ```

### ✅ 跑批后检查清单

- [ ] **批次是否完成**（status: done）
  ```bash
  cat runs/*/batch_meta.json | grep status
  ```

- [ ] **输出文件是否生成**
  ```bash
  ls -lh runs/*/outputs/phase45_final.json
  ```

- [ ] **数据是否入库**
  ```bash
  sqlite3 ../../personal-ai-headhunter/data/headhunter_dev.db \
    "SELECT COUNT(*) FROM candidates WHERE DATE(created_at) = DATE('now');"
  ```

- [ ] **评级是否正确**
  ```bash
  cat runs/*/batch_meta.json | jq '.lineage.tier_update'
  ```

- [ ] **更新 BATCH_HISTORY.md**
  ```bash
  # 手动添加批次记录到 docs/BATCH_HISTORY.md
  ```

- [ ] **如有问题，更新 TROUBLESHOOTING.md**
  ```bash
  # 记录遇到的问题和解决方案
  ```

---

## 🎓 学术流水线 (Academic Pipeline)

### 环境变量

```bash
# Semantic Scholar API Key (加速 S2 查询，避免限流)
export S2_API_KEY="your_key_here"

# DashScope API Key (LLM 富化)
# 已在 github_hunter_config.py 中配置
```

### 完整流程

```
Phase A: 论文采集 (OpenReview/ACL/DBLP)
Phase B: 去重 + 国籍过滤
Phase C: S2 作者富化 (h-index/引用/主页/GitHub)    ← 需要 S2_API_KEY
Phase D: Serper 搜索 (主页/联系方式/homepage_text)
Phase E: PDF 邮箱提取
Phase F: 深度富化 (主页爬取 + LLM)                   ← 必须并行
Phase G: 数据库入库
```

### Phase C: S2 富化

```bash
# 必须带 S2_API_KEY 运行，否则限流严重
S2_API_KEY=xxx nohup ./run_all_conferences.sh --resume > .../logs/run_serial.log 2>&1 &
```

### Phase F: 深度富化 (三步)

**Step 1: 主页爬取 (必须用 --workers 并行)**
```bash
nohup python3 scripts/academic_deep_enrich.py \
  --input .../all_conf_2025_full.json \
  --serper-cache .../_serper_cache.json \
  --output-dir .../outputs/ \
  --mode homepage \
  --workers 10 \
  > .../logs/deep_homepage.log 2>&1 &
```

> ⚠️ **不加 --workers 默认 10 并发。串行 (workers=1) 需要 ~24h，10 并发 ~2.5h**

**Step 2: GitHub commit email**
```bash
nohup python3 scripts/academic_deep_enrich.py \
  --input .../all_conf_2025_full.json \
  --serper-cache .../_serper_cache.json \
  --output-dir .../outputs/ \
  --mode github-commit \
  > .../logs/deep_github.log 2>&1 &
```

**Step 3: LLM 富化**
```bash
nohup python3 scripts/academic_llm_enrich.py \
  --deep-cache .../_deep_cache.json \
  --serper-cache .../_serper_cache.json \
  --input .../all_conf_2025_full.json \
  --workers 5 \
  > .../logs/llm_enrich.log 2>&1 &
```

### 监控命令

```bash
# 所有进程
ps aux | grep academic | grep -v grep

# 主页爬取进度
tail -5 .../logs/deep_homepage.log

# S2 进度
tail -5 .../logs/run_serial.log

# LLM 富化进度
tail -5 .../logs/llm_enrich.log
```

---

## 🔗 相关文档

- [主文档 - 路线图](../../.agent/workflows/github-network-mining.md)
- [参考文档 - 技术标准](../../.agent/workflows/github-mining-reference.md)
- [学术流水线设计](./academic_sourcing_design.md)
- [故障排查手册](./TROUBLESHOOTING.md)
- [批次执行历史](./BATCH_HISTORY.md)

---

**最后更新**: 2026-03-14
**维护者**: GitHub Mining Team
