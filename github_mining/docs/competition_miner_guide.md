# 竞赛获奖者挖掘 — 使用指南

## 采集目标

| 平台 | 目标人群 | 岗位相关性 | 所需 API Key |
|------|---------|-----------|-------------|
| **Codeforces** | International Master 及以上 (Rating ≥ 2200) | AI Infra, 算法 | ❌ 无需 |
| **NOI** | 全国信息学奥林匹克 金牌得主 2019-2024 | 基础架构, 算法 | ❌ 无需 |
| **ICPC** | ACM-ICPC 亚洲区域赛 金奖 | 算法, 系统 | ❌ 无需 |
| **Kaggle** | AI 竞赛 Top-N | CV, NLP, 推荐 | ✅ 需要 |

无 API Key 时也可跑 Codeforces + NOI + ICPC，Kaggle 则有限制。

---

## 快速开始

### 1. 配置环境变量（可选）

```bash
# Kaggle API Key（https://www.kaggle.com/settings/account → Create New Token）
export KAGGLE_USERNAME="your_username"
export KAGGLE_KEY="your_api_key"

# Serper API Key（https://serper.dev/）用于 GitHub/邮箱补充
export SERPER_API_KEY="your_serper_key"
```

### 2. 运行

```bash
cd /Users/lillianliao/notion_rag/github_mining/scripts

# 全量（Kaggle + Codeforces + NOI + ICPC）
./run_competition_pipeline.sh

# 只跑 Codeforces（无需 Key，速度最快）
./run_competition_pipeline.sh --codeforces

# 只跑 NOI + ICPC（国内竞赛，无需 Key）
./run_competition_pipeline.sh --noi

# 只跑 Kaggle（需 API Key）
./run_competition_pipeline.sh --kaggle

# 恢复上次中断
./run_competition_pipeline.sh --resume
```

### 3. 直接调用 Python 脚本（更多参数控制）

```bash
# Codeforces：只要 Grandmaster 以上 (≥2500)，最多 200 人
python3 competition_miner.py --competition codeforces --min-rating 2500 --max-users 200

# NOI 只取近两年
python3 competition_miner.py --competition noi --year 2023,2024

# Kaggle 指定单个比赛
python3 competition_miner.py --competition kaggle \
  --slug imagenet-object-localization-challenge --top-n 50

# 跳过 Serper 搜索（快速测试）
python3 competition_miner.py --competition codeforces --no-serper
```

---

## 输出文件

每次运行在 `data/competition/runs/<batch_name>/` 下生成：

| 文件 | 说明 |
|------|------|
| `comp_*_full.json` | 完整字段（调试/备查） |
| `comp_*_direct_import.json` | ✅ 可直接导入猎头系统 |
| `comp_*_github_pipeline.json` | 有 GitHub URL 的子集，送 `github_network_miner` 继续扩展 |

---

## 导入到猎头系统

```bash
# 导入到 headhunter_dev.db（复用 academic_import.py）
cd /Users/lillianliao/notion_rag/github_mining/scripts
python3 academic_import.py \
  --input data/competition/runs/<batch>/comp_*_direct_import.json \
  --dry-run   # 先预览

python3 academic_import.py \
  --input data/competition/runs/<batch>/comp_*_direct_import.json
```

---

## Codeforces Rating 分级对照

| Rating | CF 称号 | 建议导入 |
|--------|---------|---------|
| ≥ 3000 | Legendary Grandmaster | ✅ S 级 |
| 2700-3000 | International Grandmaster | ✅ A+ 级 |
| 2500-2700 | Grandmaster | ✅ A+ 级 |
| 2400-2500 | International Master | ✅ A 级 |
| 2200-2400 | Master | ✅ B+ 级（默认起点） |

---

## 扩展：添加新竞赛来源

在 `competition_miner.py` 中的 `KAGGLE_AI_COMPETITIONS` 列表添加新比赛 slug：

```python
KAGGLE_AI_COMPETITIONS = [
    "imagenet-object-localization-challenge",
    "your-new-competition-slug",  # 从 kaggle.com URL 复制
    ...
]
```

或者实现新的 `collect_xxx()` 函数并在 `main()` 中调用。
