# ☀️ 早上好！准备开始扩展GitHub人才库

## 🎯 目标

将现有 **1,057人** 扩大到 **2,500+人**（预计新增 **1,500人**）

---

## 🚀 一键执行（选一个）

### 方式1: 最简单 ⭐ 推荐

```bash
cd /Users/lillianliao/notion_rag/github_mining
bash START_EXPANSION.sh
```

然后按照提示选择模式即可！

---

### 方式2: 直接运行

```bash
cd /Users/lillianliao/notion_rag/github_mining

# 测试模式（3个项目，~10分钟）
bash scripts/run_ai_repo_expansion.sh --test

# 标准模式（10个项目，~40分钟）⭐ 推荐
bash scripts/run_ai_repo_expansion.sh --full

# 完整模式（20个项目，~1小时）
bash scripts/run_ai_repo_expansion.sh --repos 20
```

---

## 📋 执行流程（全自动，无需干预）

```
Step 1: 从AI项目获取用户
  ├─ 获取20个顶级AI项目的star用户
  ├─ 获取项目的contributors
  └─ 去重 + 质量过滤
  输出: ~6,000 用户

Step 2: Phase 3 深度富化
  ├─ 获取每个用户的repos详情
  ├─ 提取技术栈和语言偏好
  └─ 计算star数和项目质量
  输出: ~3,000 用户（过滤后）

Step 3: Phase 4.5 LLM富化
  ├─ 通义千问AI分析
  ├─ 生成候选人画像
  ├─ 提取触达话题
  └─ 识别国籍
  输出: ~2,000 高质量用户

Step 4: 合并到主库
  ├─ 与现有1,057人去重
  └─ 生成完整人才库
  输出: ~2,500 用户
```

---

## 📊 预期结果

| 指标 | 当前 | 扩展后 | 增长 |
|------|------|--------|------|
| 总人数 | 1,057 | ~2,500 | +136% |
| S级 | 2 | ~32 | +1500% |
| A+级 | 33 | ~183 | +455% |
| A级 | 132 | ~582 | +341% |

---

## ⏱️ 时间估算

| 模式 | 项目数 | 预计时间 | 预计新增 |
|------|--------|----------|----------|
| 测试 | 3个 | ~10分钟 | ~200人 |
| 标准 | 10个 | ~40分钟 | ~800人 |
| 完整 | 20个 | ~1小时 | ~1,500人 |

**建议**: 选择标准模式（10个项目），40分钟完成，新增800人。

---

## 📁 输出文件位置

```
github_mining/ai_repo_users.json                  # Step 1输出
github_mining/phase3_from_ai_repos.json           # Step 2输出
github_mining/phase4_5_from_ai_repos.json         # Step 3输出
github_mining/phase4_5_llm_enriched_merged.json   # 最终结果 ⭐
```

---

## ✅ 完成后验证

```bash
# 查看最终人数
python3 << 'EOF'
import json
with open('github_mining/phase4_5_llm_enriched_merged.json') as f:
    data = json.load(f)
print(f"✅ 总用户: {len(data):,} 人")
EOF
```

---

## 🎯 完成后的下一步

### 1. 导入数据库
```bash
cd personal-ai-headhunter
python3 import_github_candidates.py \
  --file ../github_mining/phase4_5_llm_enriched_merged.json
```

### 2. Tier评级
```bash
python3 scripts/batch_update_tiers.py
```

### 3. 生成触达邮件
```bash
python3 scripts/batch_ai_outreach.py \
  --tiers S,A+,A \
  --output outreach_emails/
```

---

## 🔧 配置已就绪

✅ GitHub Token: 3个，总计15,000次/小时
✅ 通义千问API: 已配置
✅ 数据库: 已准备
✅ 脚本: 已测试

**无需任何配置，直接运行即可！**

---

## 📞 如果遇到问题

查看详细文档：
```bash
cat github_mining/AI_EXPANSION_README.md
```

---

**准备好了吗？开始执行吧！🚀**

```bash
cd /Users/lillianliao/notion_rag/github_mining
bash START_EXPANSION.sh
```
