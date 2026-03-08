# GitHub人才库扩大 - 从AI项目获取用户

> **创建时间**: 2026-03-06
> **执行方式**: 端到端无人值守
> **预计收益**: +2,000 ~ +5,000 高质量AI人才

---

## 🚀 快速开始

### 一键执行（推荐）

```bash
# 进入项目目录
cd /Users/lillianliao/notion_rag/github_mining

# 方式1: 测试模式（3个项目，约10分钟）
bash scripts/run_ai_repo_expansion.sh --test

# 方式2: 完整模式（10个项目，约30-40分钟）
bash scripts/run_ai_repo_expansion.sh --full

# 方式3: 自定义项目数量（20个项目，约1小时）
bash scripts/run_ai_repo_expansion.sh --repos 20
```

---

## 📋 执行流程

### Step 1: 从AI项目获取用户（~20分钟）

- 获取20个顶级AI项目的**star用户**（每个项目300个）
- 获取项目的**contributors**（每个项目100个）
- 去重 + 质量过滤
- 输出：`github_mining/ai_repo_users.json`

**目标项目**：
```
大模型框架:
  - huggingface/transformers (163k stars)
  - pytorch/pytorch (82k stars)
  - tensorflow/tensorflow

AI应用框架:
  - langchain-ai/langchain (91k stars)
  - microsoft/semantic-kernel
  - openai/gym

中国团队:
  - langgenius/dify (AI应用平台)
  - 其他...
```

### Step 2: Phase 3 深度富化（~15分钟）

- 获取每个用户的**repos详情**
- 提取**技术栈**和**语言偏好**
- 计算**star数**和**项目质量**
- 输出：`github_mining/phase3_from_ai_repos.json`

### Step 3: Phase 4.5 LLM富化（~20分钟）

- 使用通义千问LLM进行**深度分析**
- 生成**候选人画像**（技术方向、背景偏好）
- 提取**talking points**（触达话题）
- 识别**国籍**（排除外国人）
- 输出：`github_mining/phase4_5_from_ai_repos.json`

### Step 4: 合并到主库

- 与现有1057人**去重**
- 合并为**完整人才库**
- 输出：`github_mining/phase4_5_llm_enriched_merged.json`

---

## 📊 预期结果

### 数据量
```
AI项目用户:       ~6,000 人  (stars + contributors)
Phase 3过滤后:    ~3,000 人  (去除低质量)
Phase 4.5富化后:  ~2,000 人  (LLM分析)
去重后新增:       ~1,500 人  (排除重复)
```

### 质量提升
```
现有库: 1,057 人
  S级:   2 人
  A+级: 33 人
  A级: 132 人
  B级: 622 人

预计新增: ~1,500 人
  S级:   ~30 人  (顶级项目maintainer)
  A+级:  ~150 人
  A级:   ~450 人
  B级:   ~870 人

总计: ~2,500 人
  S/A+级: ~215 人  (提升6倍！)
```

---

## 🔧 配置说明

### GitHub Token
已配置3个token，总计**15,000次/小时**

```
github_mining/scripts/github_hunter_config.py
  → GITHUB_CONFIG["token"]
  → 已有3个token，无需修改
```

### LLM API
已配置通义千问API

```
github_mining/scripts/github_hunter_config.py
  → DASHSCOPE_API_KEY
  → 已配置，无需修改
```

---

## 📂 输出文件

### 中间文件
```
github_mining/ai_repo_users.json              # Step 1输出
github_mining/phase3_from_ai_repos.json       # Step 2输出
github_mining/phase4_5_from_ai_repos.json     # Step 3输出
```

### 最终文件
```
github_mining/phase4_5_llm_enriched_merged.json  # 合并后主库
github_mining/phase4_5_llm_enriched.json.bak      # 原库备份
```

---

## ⏱️ 时间估算

| 模式 | 项目数 | 预计时间 | 预计新增 |
|------|--------|----------|----------|
| 测试 | 3个 | ~10分钟 | ~200人 |
| 标准 | 10个 | ~40分钟 | ~800人 |
| 完整 | 20个 | ~1小时 | ~1,500人 |

---

## 🎯 完成后下一步

### 1. 查看结果
```bash
cd github_mining

# 查看新增用户
python3 << 'EOF'
import json
with open('phase4_5_llm_enriched_merged.json') as f:
    data = json.load(f)
print(f"总用户: {len(data)} 人")
EOF
```

### 2. 导入数据库
```bash
cd personal-ai-headhunter

python3 import_github_candidates.py \
  --file ../github_mining/phase4_5_llm_enriched_merged.json
```

### 3. Tier评级
```bash
python3 scripts/batch_update_tiers.py
```

### 4. 生成触达邮件
```bash
python3 scripts/batch_ai_outreach.py \
  --tiers S,A+,A \
  --output outreach_emails/
```

---

## 🐛 故障排查

### Token配额不足
```bash
# 查看剩余配额
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit
```

### LLM调用失败
```bash
# 检查API key
grep DASHSCOPE_API_KEY github_mining/scripts/github_hunter_config.py
```

### 中断后恢复
脚本会自动保存进度，重新运行即可从上次断点继续。

---

## 📞 支持与反馈

如有问题，查看日志文件：
```bash
# 日志位置
tail -f github_hunter.log
```

---

**预祝扩展成功！🎉**
