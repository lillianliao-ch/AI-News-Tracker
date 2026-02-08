---
description: 从飞书文档批量导入字节跳动职位到猎头系统
---

# 字节跳动JD批量导入工作流

本工作流用于从字节跳动HR分享的飞书文档中批量提取职位信息，并导入到 personal-ai-headhunter 系统。

## 适用场景

- HR通过飞书文档分享职位列表
- 文档包含职位表格和外部JD链接（job.toutiao.com 或 jobs.bytedance.com）
- 需要批量导入职位并获取完整JD内容

## 前置条件

1. 飞书文档链接（需要有访问权限）
2. personal-ai-headhunter 系统已部署
3. 数据库已初始化

---

## 第一阶段：从飞书文档提取职位列表

### 1.1 访问飞书文档

飞书文档的职位表格通常是 **Canvas 渲染**，无法通过常规 DOM 选择器提取。需要使用特殊方法。

### 1.2 提取职位链接的方法

**核心技术**：飞书表格使用 SVG `<text>` 元素渲染，可以通过解析 SVG 的 `transform` 属性中的坐标来关联职位名称和链接。

```javascript
// 在浏览器控制台执行，提取职位名称与JD链接的映射
(() => {
  const html = document.documentElement.innerHTML;
  const textRegex = /<text transform="matrix\(1 0 0 1 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)\)"[^>]*>([^<]+)<\/text>/g;
  
  const elements = [];
  let match;
  while ((match = textRegex.exec(html)) !== null) {
    elements.push({
      x: parseFloat(match[1]),
      y: parseFloat(match[2]),
      content: match[3].trim()
    });
  }
  
  // 筛选链接和其他文本
  const linkMatches = elements.filter(el => 
    el.content.includes('http://job.toutiao.com') || 
    el.content.includes('jobs.bytedance.com')
  );
  const otherMatches = elements.filter(el => !el.content.includes('http'));
  
  // 按Y坐标匹配同一行的职位名称和链接
  const mapping = [];
  linkMatches.forEach(link => {
    const rowElements = otherMatches.filter(t => Math.abs(t.y - link.y) < 2);
    // 职位名称通常在 X≈285 的位置
    let titleCandidate = rowElements.find(t => Math.abs(t.x - 285) < 50);
    if (!titleCandidate) {
      titleCandidate = rowElements.filter(t => t.x > 200 && t.x < 600)
        .sort((a,b) => b.content.length - a.content.length)[0];
    }
    if (titleCandidate) {
      mapping.push({ 
        title: titleCandidate.content, 
        url: link.content 
      });
    }
  });
  
  return mapping;
})()
```

### 1.3 提取结果示例

```json
[
  {
    "title": "AI Coding产品经理-Trae",
    "url": "http://job.toutiao.com/society/position/detail/7360527198607395109"
  },
  {
    "title": "高级全栈开发工程师-AI编程助手",
    "url": "http://job.toutiao.com/society/position/detail/7439660623468841234"
  }
]
```

---

## 第二阶段：获取完整JD内容

### 2.1 字节跳动招聘页面特点

- **URL格式**：
  - 旧格式：`http://job.toutiao.com/society/position/detail/{job_id}`
  - 新格式：`https://jobs.bytedance.com/experienced/position/{job_id}/detail`
  - 两种格式会自动重定向到同一页面

- **页面渲染**：JavaScript动态渲染，无法用 `requests` 直接获取
- **必须使用浏览器**：需要通过 browser_subagent 访问

### 2.2 批量获取JD的策略

由于每个页面需要等待加载，建议**分批处理**（每批5个职位）：

```
批次1: ID 1-5
批次2: ID 6-10
...
```

### 2.3 浏览器获取JD内容的指令模板

```
批量获取5个职位的JD内容。

按顺序访问以下链接，每个链接：
1. 打开页面，等待3秒加载
2. 读取页面完整内容，提取职位描述和职位要求

链接列表：
1. ID=xxx: http://job.toutiao.com/society/position/detail/xxx
2. ID=xxx: http://job.toutiao.com/society/position/detail/xxx
...

返回JSON格式结果，如果职位已下线则标注"职位已下线"
```

### 2.4 JD内容结构

```json
{
  "job_id": 123,
  "title": "AI Coding产品经理-Trae",
  "job_description": "1、负责...\n2、参与...",
  "job_requirements": "1、本科及以上...\n2、熟悉..."
}
```

---

## 第三阶段：导入数据库

### 3.1 导入脚本模板

```python
#!/usr/bin/env python3
"""
批量导入字节跳动职位
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, Job
from sqlalchemy import text
import re

# HR信息
HR_XIA = "夏丹伦 (xiadanlun@bytedance.com)"
HR_ZHANG = "张宇 (zhangyu.vicky@bytedance.com)"

# 职位数据
JOBS = [
    {
        "title": "职位名称",
        "department": "部门",
        "location": "北京/上海",
        "seniority_level": "3-1",
        "hr": HR_XIA,
        "jd_link": "http://job.toutiao.com/society/position/detail/xxx",
        "jd_text": "完整JD内容..."
    },
    # ... 更多职位
]

def generate_job_code(db, prefix="BT"):
    """生成职位编号 BT001, BT002..."""
    result = db.execute(text(
        f"SELECT job_code FROM jobs WHERE job_code LIKE '{prefix}%' "
        f"ORDER BY job_code DESC LIMIT 1"
    )).fetchone()
    
    if result and result[0]:
        match = re.search(r'(\d+)$', result[0])
        next_num = int(match.group(1)) + 1 if match else 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:03d}"

def main():
    db = next(get_db())
    
    for job_data in JOBS:
        # 按标题+公司去重
        existing = db.query(Job).filter(
            Job.title == job_data["title"],
            Job.company == "字节跳动"
        ).first()
        
        if existing:
            print(f"⏭️ 跳过 (已存在): {job_data['title']}")
            continue
        
        job_code = generate_job_code(db)
        
        new_job = Job(
            job_code=job_code,
            title=job_data["title"],
            company="字节跳动",
            department=job_data["department"],
            location=job_data["location"],
            seniority_level=job_data["seniority_level"],
            hr_contact=job_data["hr"],
            jd_link=job_data["jd_link"],
            raw_jd_text=job_data["jd_text"],
        )
        
        db.add(new_job)
        db.commit()
        print(f"✅ 导入: {job_code} | {job_data['title']}")

if __name__ == "__main__":
    main()
```

### 3.2 更新已有职位的JD内容

```python
# 批量更新JD内容
JD_CONTENTS = {
    421: "完整JD内容...",
    422: "完整JD内容...",
}

def update_jd():
    db = next(get_db())
    for job_id, content in JD_CONTENTS.items():
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.raw_jd_text = content
            db.commit()
            print(f"✅ 更新 ID={job_id}")
```

---

## 关键经验总结

### ✅ 成功要点

1. **飞书表格是Canvas渲染**：必须解析SVG text元素的坐标
2. **字节招聘页面需要JS渲染**：必须用浏览器访问
3. **分批处理避免超时**：每批5个职位
4. **职位可能下线**：需要处理404情况
5. **URL格式兼容**：旧格式和新格式都能工作

### ⚠️ 常见问题

| 问题 | 解决方案 |
|:---|:---|
| 飞书表格无法选中 | 使用SVG坐标解析法 |
| requests获取不到内容 | 必须用浏览器 |
| 职位已下线 | 标记状态，联系HR确认 |
| 浏览器页面过多 | 分批处理，复用页面 |

### 🗂️ 相关脚本

| 脚本 | 用途 |
|:---|:---|
| `import_bytedance_ai_coding.py` | 批量导入职位基础信息 |
| `update_all_jd.py` | 批量更新JD完整内容 |
| `test_import_one.py` | 单条测试导入 |
| `extract_tags.py` | 生成结构化标签 |

---

## 第四阶段：生成JD标签

导入JD后，需要使用AI生成结构化标签用于候选人匹配。

### 4.1 标签体系

系统使用以下标签维度进行匹配：

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

### 4.2 生成标签命令

```bash
# 为所有缺少标签的JD生成标签
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 extract_tags.py jobs

# 强制重新生成所有JD标签（包括已有标签的）
python3 extract_tags.py jobs --force
```

### 4.3 标签生成原理

- 使用**通义千问**（Qwen）模型
- 输入：职位名称 + 公司 + JD全文
- 输出：JSON格式的结构化标签
- 自动保存到数据库的 `structured_tags` 字段

### 4.4 验证标签

```sql
-- 查看最近导入职位的标签
SELECT job_code, title, structured_tags 
FROM jobs 
WHERE company = '字节跳动' 
ORDER BY id DESC LIMIT 5;
```

---

## 完整工作流总结

```
1️⃣ 获取飞书文档 → 用浏览器访问
      ↓
2️⃣ 执行JS提取职位列表 → 获得职位名称+链接
      ↓
3️⃣ 分批访问JD链接 → 每批5个，获取完整JD
      ↓
4️⃣ 修改导入脚本 → 更新JOBS列表
      ↓
5️⃣ 执行导入 → 运行Python脚本
      ↓
6️⃣ 生成标签 → python3 extract_tags.py jobs
      ↓
7️⃣ 验证结果 → 刷新应用查看
```

---

## 快速复用指南

1. **获取飞书文档链接** → 用浏览器访问
2. **执行JS提取职位列表** → 获得职位名称+链接
3. **分批访问JD链接** → 每批5个，获取完整JD
4. **修改导入脚本** → 更新JOBS列表
5. **执行导入** → 运行Python脚本
6. **验证结果** → 刷新应用查看
