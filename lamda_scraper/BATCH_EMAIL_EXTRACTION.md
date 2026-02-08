# LAMDA 候选人 GitHub 邮箱批量提取

## 🎯 任务

为 `lamda_candidates_final.csv` 中的所有候选人通过 GitHub 提取邮箱。

## 📊 预期规模

- **总候选人**: ~462 人
- **有 GitHub**: 预计 ~200-300 人
- **预计处理时间**: 10-30 分钟（取决于网络和 API 限流）
- **预计邮箱获取**: 20-50 个新增邮箱

## 🔧 提取方法

### 多源提取策略

1. **GitHub API** - 直接返回的公开邮箱
2. **个人网站** - 包括 Cloudflare 邮件保护解码 ⭐
3. **Public Commits** - 从提交记录中提取
4. **README 文件** - 从项目说明中提取

### 关键技术

**Cloudflare 邮件解码**:
```python
# 成功案例: 杨嘉祺
# GitHub: https://github.com/ThyrixYang
# 网站: https://academic.thyrixyang.com
# 结果: thyrixyang@gmail.com ✅

key = data[0]
decoded = chr(byte ^ key) for byte in data[1:]
```

## 📝 输出文件

### 主文件
- `lamda_candidates_with_emails.csv` - 增强版候选人数据
  - 新增字段:
    - `github_email` - 提取的邮箱
    - `email_source` - 来源（API/网站/Commits/README）
    - `email_extraction_details` - 详细信息

### 日志文件
- `email_extraction.log` - 完整处理日志

## ⏱️ 当前进度

任务正在后台运行中...

你可以查看实时进度:
```bash
cd /Users/lillianliao/notion_rag/lamda_scraper
tail -f email_extraction.log
```

或者查看统计:
```bash
grep "找到邮箱" email_extraction.log | wc -l
```

## 📈 预期结果

### 修复前
- 总候选人: 462
- 有邮箱: 27 (5.8%)
- 主要来源: LAMDA 实验室主页

### 修复后（预期）
- 总候选人: 462
- 有邮箱: 47-77 (10-17%)
- **新增: 20-50 个邮箱**
- **新增来源**: GitHub + 个人网站

## 🎓 重点案例

### 已验证案例
1. **杨嘉祺 (ThyrixYang)**
   - GitHub: https://github.com/ThyrixYang
   - 邮箱: thyrixyang@gmail.com
   - 来源: 个人网站 (Cloudflare 解码)

### 待发现案例
- 所有有 GitHub 但邮箱为空的候选人
- 使用 Cloudflare 保护的学术网站
- Public commits 中有邮箱的开发者

## 🚀 完成后的步骤

1. **验证结果**
   ```bash
   # 查看新增邮箱
   cut -d',' -f2 lamda_candidates_with_emails.csv | grep '@' | sort -u
   ```

2. **更新评分**
   ```bash
   # 重新运行评分系统
   python3 talent_analyzer.py
   ```

3. **导出优先列表**
   ```bash
   # 导出有邮箱的候选人
   python3 export_contacts.py
   ```

4. **对比分析**
   ```bash
   # 对比修复前后
   diff lamda_candidates_final.csv lamda_candidates_with_emails.csv
   ```

## 💡 后续优化

1. **添加更多邮箱来源**
   - LinkedIn API
   - Google Scholar
   - DBLP
   - 个人博客 RSS

2. **改进验证**
   - 邮箱有效性检查
   - 格式标准化
   - 去重和合并

3. **缓存机制**
   - 避免重复请求
   - 本地缓存已提取的邮箱
   - 增量更新

---

**状态**: 🔄 运行中
**开始时间**: 2025-01-26 21:49
**预计完成**: 2025-01-26 22:00-22:30

✅ 任务完成后，你将得到一个包含更多邮箱的候选人列表！
