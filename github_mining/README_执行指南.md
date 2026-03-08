# 🚀 GitHub Mining 快速指南

## 📊 项目状态

> **最后更新**: 2026-03-08  
> **数据库**: 24,225 人（GitHub: 16,120，已富化: 8,315）

**快速查看**: [GITHUB_MINING_STATUS.md](GITHUB_MINING_STATUS.md) - 完整项目状态总览

---

## ⚡ 最新任务（2026-03-08）

### ✅ 已完成：1,105 人 LLM 富化

**结果**:
- 成功富化: 1,033 人 (93.5%)
- 新增候选人: 10 人
- 高质量: 208 人 (20.1%)
- 总耗时: 2小时35分钟

**详细报告**: [ENRICHMENT_1105_COMPLETE_0308.md](ENRICHMENT_1105_COMPLETE_0308.md)

---

## 🎯 常用任务

### 查看数据库统计

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

sqlite3 data/headhunter_dev.db "
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN source = 'github' THEN 1 ELSE 0 END) as github,
    SUM(CASE WHEN extracted_work_history IS NOT NULL 
              AND extracted_work_history != '' 
              AND extracted_work_history != '[]' 
         THEN 1 ELSE 0 END) as enriched
FROM candidates;
"
```

### 查看高质量候选人

```bash
sqlite3 data/headhunter_dev.db "
SELECT 
    name,
    github_url,
    website_quality_score,
    extracted_skills
FROM candidates
WHERE talent_labels LIKE '%LLM高质量%'
ORDER BY website_quality_score DESC
LIMIT 20;
"
```

### 导入新的 GitHub 候选人

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

# 导入脚本
python3 import_github_candidates.py \
  --file ../github_mining/scripts/github_mining/YOUR_FILE.json

# 只导入前 20 人（测试）
python3 import_github_candidates.py \
  --file ../github_mining/scripts/github_mining/YOUR_FILE.json \
  --top 20
```

### 添加质量标签

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter

# 为已富化的候选人添加标签
python3 add_llm_quality_tags_0308.py
```

---

## 📁 文件组织

### 数据文件（带时间戳）

```
github_mining/
├── scripts/github_mining/
│   ├── phase4_final_enriched.json          # Phase 3.5 输出（11,976 人）
│   ├── phase45_missing_1105_0308.json      # 待富化候选人（1,105 人）
│   └── phase45_missing_1105_enriched_0308.json  # 富化结果（1,033 人）
└── phase4_5_llm_enriched.json              # 旧版输出（已废弃）
```

### 脚本文件

```
github_mining/scripts/
├── identify_missing_candidates.py          # 识别缺失候选人
├── enrich_missing_1105.py                  # LLM 富化
├── run_phase4_5_llm_enrichment.py          # Phase 4.5 主脚本
└── check_1105_progress.sh                  # 进度监控
```

### 文档文件

```
github_mining/
├── GITHUB_MINING_STATUS.md                 # 📊 项目状态总览（主要文档）
├── ENRICHMENT_1105_COMPLETE_0308.md        # 1,105 人富化完成报告
├── README_执行指南.md                       # 本文档
└── scripts/github_mining/
    ├── batch_audit_20260308.md             # 批次梳理报告
    ├── phase4_5_code_review.md             # 代码审查
    └── p0_fixes_verified.md                # P0 问题修复
```

---

## 🔧 配置文件

### GitHub Token
```bash
# 配置文件
github_mining/scripts/github_hunter_config.py

# 已配置 3 个 token，总计 15,000 次/小时
# 无需修改，直接使用
```

### LLM API
```bash
# 通义千问 API Key
# 已配置在 github_hunter_config.py
# 无需修改，直接使用
```

---

## 📋 常见问题

### Q: 如何查看最新的富化结果？

**A**: 查看状态总览文档
```bash
cat /Users/lillianliao/notion_rag/github_mining/GITHUB_MINING_STATUS.md
```

### Q: 如何验证富化质量？

**A**: 随机抽样检查
```bash
sqlite3 data/headhunter_dev.db "
SELECT 
    name,
    extracted_work_history,
    extracted_education,
    website_quality_score
FROM candidates
WHERE talent_labels LIKE '%LLM高质量%'
ORDER BY RANDOM()
LIMIT 10;
"
```

### Q: 文件命名规则是什么？

**A**: 所有输出文件都带时间戳（月日格式）
- 格式: `YYYYMMDD` 或 `MMDD`
- 示例: `phase45_missing_1105_0308.json` (2026-03-08)

### Q: 如何找到特定的批次数据？

**A**: 按时间戳搜索
```bash
# 查找所有 0308 批次的文件
find . -name "*0308*.json" -type f
```

---

## 🎯 快速链接

- [📊 项目状态总览](GITHUB_MINING_STATUS.md) - **主要文档**
- [📝 1,105 人富化完成报告](ENRICHMENT_1105_COMPLETE_0308.md)
- [🔍 批次梳理报告](scripts/github_mining/batch_audit_20260308.md)
- [🚀 AI 项目扩展流程](AI_EXPANSION_README.md)

---

**准备好了吗？查看状态总览开始吧！🎯**
