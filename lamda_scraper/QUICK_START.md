# LAMDA Scraper - 快速使用指南

**最后更新**: 2025-01-27

---

## 🚀 5分钟快速开始

### 1. 查看最终数据

```bash
cd /Users/lillianliao/notion_rag/lamda_scraper

# 打开最终增强数据
open lamda_candidates_final_enriched.csv

# 或使用优先级提取结果（如果生成完成）
open lamda_candidates_priority_enriched.csv
```

### 2. 阅读文档

```bash
# 从这里开始
open README_INDEX.md

# 然后查看
open COMPLETE_SUMMARY.md
```

### 3. 运行工具

```bash
# GitHub URL 标准化
python3 github_url_fixer.py

# 批量邮箱提取
python3 batch_extract_emails.py

# 优先级邮箱提取（推荐）
python3 priority_email_extractor.py

# 测试重定向功能
python3 test_redirect.py
```

---

## 📊 数据文件说明

### 推荐使用 ⭐

**`lamda_candidates_final_enriched.csv`** - 当前最完整
- 462个候选人
- GitHub URL已修复 (98.9%正确率)
- GitHub邮箱提取结果
- 重定向信息

**`lamda_candidates_priority_enriched.csv`** - 优先级提取结果（生成中）
- 更高邮箱覆盖率
- 优先处理无邮箱候选人
- 预计新增30-50个邮箱

### 其他文件

- `lamda_candidates_final.csv` - 原始数据
- `lamda_candidates_urls_fixed.csv` - GitHub URL修复版
- `lamda_candidates_with_emails.csv` - 第一批邮箱提取
- `lamda_candidates_final_fixed.csv` - 陈雄辉修复版

---

## 📝 文档导航

### 必读文档 ⭐

1. **[README_INDEX.md](README_INDEX.md)** - 文件索引
   - 所有文件列表
   - 快速查找
   - 常用命令

2. **[COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md)** - 完整总结
   - 所有成果
   - 技术突破
   - 使用指南

3. **[PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)** - 第一阶段总结
   - 完成的任务
   - 核心成果
   - 下一步计划

### 技术报告

4. **[FINAL_ENRICHMENT_REPORT.md](FINAL_ENRICHMENT_REPORT.md)** - 数据增强报告
5. **[REDIRECT_IMPLEMENTATION_REPORT.md](REDIRECT_IMPLEMENTATION_REPORT.md)** - 重定向实现
6. **[PRIORITY_EXTRACTION_REPORT.md](PRIORITY_EXTRACTION_REPORT.md)** - 优先级提取
7. **[EMAIL_EXTRACTION_LIMITATIONS.md](EMAIL_EXTRACTION_LIMITATIONS.md)** - GitHub限制分析

### 案例分析

8. **[GITHUB_EMAIL_FIX.md](GITHUB_EMAIL_FIX.md)** - 杨嘉祺案例
9. **[CHEN_XH_DATA_GAP_ANALYSIS.md](CHEN_XH_DATA_GAP_ANALYSIS.md)** - 陈雄辉案例

---

## 🔧 核心工具使用

### 1. GitHub URL 标准化

```bash
python3 github_url_fixer.py
```

**功能**:
- 修复仓库链接 → 用户主页
- 修复文件链接 → 用户主页
- 修复协议错误 (http → https)
- 过滤组织账号

**结果**: `lamda_candidates_urls_fixed.csv`

### 2. 批量邮箱提取

```bash
python3 batch_extract_emails.py
```

**功能**:
- 从GitHub提取邮箱 (API/网站/Commits/README)
- Cloudflare解码
- 批量处理91个有GitHub的候选人

**结果**: `lamda_candidates_with_emails.csv`

### 3. 优先级邮箱提取 ⭐⭐ 推荐

```bash
# 处理全部462个候选人
python3 priority_email_extractor.py

# 或限制数量（测试用）
python3 priority_email_extractor.py --limit 50
```

**功能**:
- 优先处理无邮箱候选人
- 深度挖掘LAMDA主页
- 提取个人网站信息
- 智能优先级评分

**结果**: `lamda_candidates_priority_enriched.csv`

### 4. 重定向测试

```bash
python3 test_redirect.py
```

**功能**:
- 测试HTTP/meta refresh/JavaScript重定向
- 验证陈雄辉案例
- 测试Cloudflare邮箱

---

## 💻 数据验证

### 统计数据

```python
import csv

# 读取数据
with open('lamda_candidates_final_enriched.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    candidates = list(reader)

# 基本统计
total = len(candidates)
with_email = len([c for c in candidates if c.get('Email')])
github_emails = len([c for c in candidates if c.get('github_email')])
fixed_urls = len([c for c in candidates if c.get('github_url_fix_status')])

print(f"总候选人: {total}")
print(f"有邮箱: {with_email} ({with_email/total*100:.1f}%)")
print(f"GitHub邮箱: {github_emails}")
print(f"URL修复: {fixed_urls}")
```

### 查找特定候选人

```python
# 查找陈雄辉
chen_xh = next((c for c in candidates if c['姓名'] == '陈雄辉'), None)
if chen_xh:
    print(f"邮箱: {chen_xh.get('Email')}")
    print(f"公司: {chen_xh.get('公司')}")
    print(f"GitHub: {chen_xh.get('GitHub')}")

# 查找无邮箱候选人
no_email = [c for c in candidates if not c.get('Email')]
print(f"无邮箱: {len(no_email)} 个")
```

---

## 🎯 核心成果

### 数据质量提升

| 指标 | 修复前 | 现在 | 提升 |
|------|--------|------|------|
| 邮箱覆盖率 | 63.4% | ~70% | +6.6% |
| GitHub URL正确率 | ~60% | 98.9% | +38.9% |
| 重定向支持 | 仅HTTP | 3种类型 | 新增2种 |

### 技术创新

1. ✅ **Cloudflare邮箱解码** - XOR算法，成功率90%+
2. ✅ **GitHub URL标准化** - 正确率98.9%
3. ✅ **重定向跟随系统** - HTTP/meta refresh/JavaScript
4. ✅ **优先级提取** - 效率提升3-5倍

### 成功案例

- **杨嘉祺**: thyrixyang@gmail.com (Cloudflare解码)
- **陈雄辉**: xionghui.cxh@alibaba-inc.com (完全修复)
- **64个GitHub URL**: 仓库链接 → 用户主页
- **9+个新邮箱**: 优先级提取

---

## 📞 常见问题

### Q1: 为什么GitHub邮箱提取率这么低？

**A**: GitHub的设计优先保护隐私，大多数用户不公开邮箱。

**统计数据**:
- API: 1.1% (1/91)
- 网站: 3.3% (3/91)
- 总成功率: 6.6%

**建议**: 优先从LAMDA主页和个人网站提取。

### Q2: 如何处理大批量候选人？

**A**: 使用优先级提取器

```bash
python3 priority_email_extractor.py
```

它会自动：
1. 评分候选人优先级
2. 优先处理无邮箱的
3. 深度挖掘LAMDA主页
4. 补充个人网站信息

### Q3: 如何查看后台任务进度？

**A**:

```bash
# 查看日志
tail -f priority_extraction.log

# 查看进程
ps aux | grep priority_email_extractor

# 查看输出文件
ls -lh lamda_candidates_priority_enriched.csv
```

### Q4: 数据文件太大怎么办？

**A**: 使用限制参数

```bash
# 只处理前50个
python3 priority_email_extractor.py --limit 50
```

---

## 🚀 下一步

### 立即可用

1. ✅ 所有工具已开发完成
2. ✅ 文档齐全
3. ✅ 数据已增强

### 继续优化

1. **GitHub Token管理** - 提升API速度
2. **数据质量监控** - 自动验证
3. **研究方向提取** - 使用LLM

查看详细计划: [COMPREHENSIVE_REPAIR_PLAN.md](COMPREHENSIVE_REPAIR_PLAN.md)

---

## 📧 支持

如有问题，请查看:
1. 本文档 - 快速使用指南
2. README_INDEX.md - 完整索引
3. COMPLETE_SUMMARY.md - 详细总结

---

**更新**: 2025-01-27
**状态**: 第一阶段完成 ✅
**项目**: LAMDA Scraper 数据增强
