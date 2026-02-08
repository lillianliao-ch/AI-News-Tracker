---
description: 从 CSV/Excel 文件批量导入职位到猎头系统
---

# 批量导入职位工作流 (CSV/Excel)

本工作流用于从 Job Scraper 扩展抓取的 CSV/Excel 文件批量导入职位到 personal-ai-headhunter 系统。

## 适用场景

- 使用 Job Scraper 扩展从阿里、字节（飞书）、小红书等平台抓取的职位数据
- 数据已导出为 CSV 或 Excel 文件
- 需要批量导入职位并提取标签

## 数据存放位置

```
/Users/lillianliao/notion_rag/数据输入/
```

---

## 第一阶段：数据文件准备

### 1.1 支持的文件格式

| 格式 | 来源 | 说明 |
|------|------|------|
| `job_ali_*.xlsx` | 阿里猎头平台 | headhunter.alibaba.com |
| `job_ali_*.csv` | 阿里猎头平台 | CSV导出 |
| `job_feishu_*.csv` | 飞书招聘 | hire.feishu.cn |
| `job_xiaohongshu_*.csv` | 小红书 | hunter.xiaohongshu.com |

### 1.2 标准字段

```
职位名称, 公司, 部门, 工作地点, 学历要求, 工作年限, 岗位层级, 
岗位描述, 岗位要求, 招聘人数, HR, 发布日期, 更新日期, 有效日期, 职位状态, 职位链接
```

---

## 第二阶段：执行导入

### 2.1 导入脚本位置

```
/Users/lillianliao/notion_rag/personal-ai-headhunter/import_jd_batch.py
```

### 2.2 修改待导入文件列表

编辑 `import_jd_batch.py`，修改 `FILES_TO_IMPORT` 列表：

```python
FILES_TO_IMPORT = [
    'job_ali_2026-02-04_112043.xlsx',
    'job_feishu_2026-02-04_104144.csv',
    'job_feishu_2026-02-04_103644.csv',
]
```

### 2.3 执行导入

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
// turbo
python3 import_jd_batch.py
```

### 2.4 导入结果示例

```
📊 现有职位数: 400
📂 处理文件: job_ali_2026-02-04_112043.xlsx
  ✅ 导入: [ALI222] 钉钉-总裁助理/项目管理...
  ✅ 导入: [ALI223] 业务技术-大模型算法工程师...
  ⏭️ 跳过 (已存在): 高德-前端开发工程师...

==================================================
📊 导入统计:
   处理总数: 136
   跳过 (已存在): 6
   新增导入: 130
==================================================
```

---

## 第三阶段：提取结构化标签

### 3.1 运行标签提取

导入JD后，需要使用AI生成结构化标签用于候选人匹配：

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
// turbo
python3 extract_tags.py jobs
```

### 3.2 标签体系

| 标签字段 | 说明 | 类型 |
|:---|:---|:---|
| `tech_domain` | 技术方向（大模型/LLM, Agent, NLP, 多模态等） | 多选 |
| `core_specialty` | 核心专长（代码生成, RAG, Agent开发等） | 多选 |
| `tech_skills` | 技术技能（SFT微调, 预训练, Prompt工程等） | 多选 |
| `role_type` | 岗位类型（算法工程师, 产品经理, 后端工程师等） | 单选 |
| `role_orientation` | 角色定位（偏研究, 偏工程, 偏业务等） | 多选 |
| `tech_stack` | 技术栈（Python, Go, PyTorch等） | 多选 |
| `seniority` | 职级层次（初级, 中级, 高级, 专家, 管理层） | 单选 |
| `industry_exp` | 行业背景（互联网大厂, AI独角兽等） | 多选 |

### 3.3 强制重新生成标签

如需重新生成所有标签（包括已有标签的）：

```bash
python3 extract_tags.py jobs --force
```

---

## 第四阶段：验证结果

### 4.1 在 Dashboard 中查看

启动应用后，在 Dashboard 页面可以看到：
- JD发布公司分布
- 职位大类分布
- 技术方向分布

### 4.2 SQL验证

```sql
-- 查看最近导入的职位
SELECT job_code, title, company 
FROM jobs 
ORDER BY id DESC 
LIMIT 10;

-- 查看标签是否生成
SELECT job_code, title, structured_tags 
FROM jobs 
WHERE structured_tags IS NOT NULL 
ORDER BY id DESC 
LIMIT 5;
```

---

## 职位编号规则

### 公司前缀映射

编号规则定义在：
```
/Users/lillianliao/notion_rag/personal-ai-headhunter/data/company_prefix_map.json
```

| 公司 | 前缀 | 示例 |
|------|------|------|
| 阿里系（淘天、钉钉、高德、平头哥等） | ALI | ALI001 |
| 阿里云 | AY | AY001 |
| 字节跳动 | BT | BT001 |
| 小红书 | XHS | XHS001 |
| MiniMax | MMX | MMX001 |
| 腾讯 | TX | TX001 |
| 百度 | BD | BD001 |
| 美团 | MT | MT001 |

### 编号格式

- 格式：`{前缀}{3位数字}`
- 示例：`ALI001`, `BT029`, `XHS015`
- 规则：自动递增，去重

---

## 公司名称规范化

### 统一公司名称

导入后需要统一公司名称，避免同一公司有多种写法：

```sql
-- 统一字节跳动
UPDATE jobs SET company = '字节跳动' WHERE company LIKE '%bytedance%' COLLATE NOCASE;

-- 统一 MiniMax
UPDATE jobs SET company = 'MiniMax' WHERE company LIKE '%minimax%' COLLATE NOCASE;

-- 统一阿里健康
UPDATE jobs SET company = '阿里健康' WHERE company LIKE '阿里健康%';

-- 统一淘天集团
UPDATE jobs SET company = '淘天集团' WHERE company LIKE '淘天集团%';
```

### 公司名称映射规则

| 原始名称 | 统一后 |
|---------|--------|
| ByteDance, bytedance | 字节跳动 |
| MINIMAX, MiniMax, minimax | MiniMax |
| 阿里健康-医生平台, 阿里健康-研发中心... | 阿里健康 |
| 淘天集团-业务技术, 淘天集团-天猫事业部... | 淘天集团 |

---

## Dashboard 公司分组展示

### 阿里系公司分组

在 Dashboard 的"JD发布公司"图表中，阿里系公司合并为一个组显示：

**阿里系公司关键词**：
- 阿里云, 云智能集团
- 阿里集团（高德、钉钉、平头哥、通义、优酷等）
- 淘天集团
- 阿里健康

**展示效果**：
```
🏛️ 阿里集团+阿里云 (432)
  ├─ 阿里云 (198)
  ├─ 阿里集团-高德 (67)
  ├─ 淘天集团 (43)
  ├─ 阿里集团-钉钉 (37)
  └─ ...
小红书 (167)
字节跳动 (87)
MiniMax (14)
...
```

**代码位置**：`app.py` 第 740-790 行，`ALIBABA_KEYWORDS` 定义了阿里系关键词

---

## 完整工作流总结

```
1️⃣ 准备数据文件 → 放入 /数据输入/ 目录
      ↓
2️⃣ 修改导入脚本 → 更新 FILES_TO_IMPORT 列表
      ↓
3️⃣ 执行导入 → python3 import_jd_batch.py
      ↓
4️⃣ 生成标签 → python3 extract_tags.py jobs
      ↓
5️⃣ 验证结果 → 刷新 Dashboard 查看
```

---

## 相关脚本

| 脚本 | 用途 |
|:---|:---|
| `import_jd_batch.py` | 批量导入CSV/Excel职位 |
| `import_ali_jobs.py` | 阿里职位专用导入（旧版） |
| `extract_tags.py` | 生成结构化标签 |
| `update_all_jd.py` | 批量更新JD内容 |

---

## 快速命令参考

```bash
# 导入职位
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 import_jd_batch.py

# 提取标签
python3 extract_tags.py jobs

# 查看导入结果
sqlite3 data/headhunter_dev.db "SELECT job_code, title FROM jobs ORDER BY id DESC LIMIT 10"
```
