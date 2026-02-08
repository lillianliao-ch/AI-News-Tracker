---
description: 从 CSV/Excel 文件批量导入职位到猎头系统
---

# 批量导入职位工作流

详细文档请参考：
`/Users/lillianliao/notion_rag/personal-ai-headhunter/.agent/workflows/jd-batch-import.md`

## 快速命令

```bash
# 1. 编辑待导入文件列表
# 修改 import_jd_batch.py 中的 FILES_TO_IMPORT

# 2. 执行导入
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 import_jd_batch.py

# 3. 提取标签
python3 extract_tags.py jobs
```

## 数据位置

- 数据文件：`/Users/lillianliao/notion_rag/数据输入/`
- 导入脚本：`/Users/lillianliao/notion_rag/personal-ai-headhunter/import_jd_batch.py`

## 编号规则

| 公司 | 前缀 |
|------|------|
| 阿里系 | ALI |
| 字节跳动 | BT |
| 小红书 | XHS |
| MiniMax | MMX |
