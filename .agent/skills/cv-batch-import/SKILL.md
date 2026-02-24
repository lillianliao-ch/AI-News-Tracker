---
description: 批量导入脉脉CV简历到AI猎头系统，支持智能去重、数据合并、自动标签生成和等级评估
---

# 批量导入脉脉CV简历

本技能用于将脉脉下载的CV简历批量导入到AI猎头系统，自动进行：
- PDF解析（文本版）
- AI结构化提取
- 候选人智能去重识别
- 数据智能合并
- 自动生成结构化标签
- 自动评估人才等级

## 前置条件

1. AI猎头系统已部署
2. 数据库已初始化
3. 依赖已安装：`PyPDF2`, `PyMuPDF`（可选，用于OCR）
4. API配置正确（config.env或.env.local）

## 核心功能

### 智能去重识别

多层级候选人识别策略：

1. **邮箱匹配**（最准确）
   - 通过邮箱地址精确匹配
   - 适用于有完整联系方式的候选人

2. **姓名 + 公司**（精确匹配）
   - 通过姓名和当前公司同时匹配
   - 适用于姓名准确的情况

3. **姓名key + 公司**（模糊匹配）
   - 提取姓名关键标识（首名 + 姓氏首字母）
   - 处理姓名变体：如 "Zora Wang" vs "ZORA (ZHIRUO) W ANG"
   - 适用于英文名有不同写法的情况

4. **姓名key全局唯一匹配**
   - 当只有一个候选人拥有相同姓名key时匹配
   - 适用于相对罕见的姓名

5. **姓名精确匹配**
   - 完全相同的姓名匹配
   - 作为最后的备选方案

### 数据合并策略

- **基础信息**：新数据优先（CV可能更准确）
  - 姓名、邮箱、电话、年龄
  - 工作年限、学历
  - 当前公司、职位

- **工作经历**：合并去重
  - 公司+职位+时间都相同视为重复
  - 新经历追加到现有经历中

- **教育背景**：合并去重
  - 学校+学位+专业相同视为重复
  - 新教育背景追加

- **技能标签**：合并去重
  - 新技能追加，重复技能只保留一个

- **原始简历**：拼接保留历史
  - 用分隔符区分不同来源的简历
  - 记录更新时间

## 使用方法

### 基础用法

```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 batch_import_cv_with_update.py --source "/path/to/cv/directory"
```

### 高级用法

#### 1. Dry-run模式（模拟运行）

在正式导入前，建议先用dry-run模式测试：

```bash
python3 batch_import_cv_with_update.py \
  --source "/path/to/cv/directory" \
  --dry-run
```

dry-run模式会：
- 扫描所有PDF文件
- 尝试提取文本和AI解析
- 识别候选人是否已存在
- **不会实际写入数据库**

#### 2. 指定文件模式

只导入特定模式的文件：

```bash
# 只导入工作4年的候选人
python3 batch_import_cv_with_update.py \
  --source "/path/to/cv/directory" \
  --pattern "*工作4年*.pdf"

# 只导入特定姓氏的候选人
python3 batch_import_cv_with_update.py \
  --source "/path/to/cv/directory" \
  --pattern "张*.pdf"
```

#### 3. 详细日志

查看详细的处理过程：

```bash
python3 batch_import_cv_with_update.py \
  --source "/path/to/cv/directory" \
  --verbose
```

详细日志会显示：
- PDF解析方法和提取的字符数
- AI解析结果
- 候选人识别方法
- 数据合并详情

## 参数说明

| 参数 | 说明 | 默认值 | 必需 |
|-----|------|--------|------|
| `--source` | CV文件所在目录 | - | ✅ |
| `--pattern` | 文件匹配模式（glob） | `*.pdf` | ❌ |
| `--dry-run` | 模拟运行，不实际写入 | False | ❌ |
| `--verbose` | 显示详细日志 | False | ❌ |

## 导入流程

### 1. 文件扫描

```
扫描目录 → 过滤PDF文件 → 排除非简历文件
```

支持的文件格式：
- `.pdf` 文本版PDF
- `.pdf` 扫描版PDF（需要PyMuPDF）

自动排除：
- 论文（paper、论文）
- 报告（report、文档）
- 其他非简历文件

### 2. PDF文本提取

```
PDF文件 → PyPDF2提取 → PyMuPDF提取(备选) → 文本内容
```

- 优先使用PyPDF2（速度快）
- 失败时使用PyMuPDF（支持OCR）
- 验证文本长度（>500字符）

### 3. AI结构化解析

```
文本内容 → AIService.parse_resume() → 结构化数据
```

提取字段：
- 基本信息：姓名、邮箱、电话、年龄
- 当前职位：公司、职位、工作年限
- 工作经历：公司、职位、时间、描述
- 教育背景：学校、学位、专业、时间
- 技能标签：技术栈、工具
- AI摘要：个人总结

### 4. 候选人识别

```
结构化数据 → 多层级匹配 → 已存在/新建
```

识别优先级：
1. 邮箱匹配
2. 姓名+公司
3. 姓名key+公司
4. 姓名key全局
5. 姓名精确

### 5. 数据处理

**已存在候选人**：
- 智能合并新旧数据
- 更新时间戳
- 保留来源历史

**新候选人**：
- 创建候选人记录
- 设置来源为"脉脉CV"

### 6. 自动化处理

导入完成后自动执行：
- ✅ 重新生成结构化标签
- ✅ 重新评估人才等级（S/A/B+/B/C）
- ✅ 更新时间戳

## 测试指南

### 单个文件测试

使用测试脚本验证导入流程：

```bash
# 测试单个文件（dry-run）
python3 test_cv_import_single.py \
  --file "/path/to/cv.pdf" \
  --dry-run

# 测试单个文件（实际导入）
python3 test_cv_import_single.py \
  --file "/path/to/cv.pdf"
```

### 验证导入结果

```bash
# 查看候选人详细信息
python3 -c "
from database import SessionLocal, Candidate
db = SessionLocal()
c = db.query(Candidate).filter(Candidate.name.like('%姓名%')).first()
if c:
    print(f'ID: {c.id}')
    print(f'姓名: {c.name}')
    print(f'公司: {c.current_company}')
    print(f'职位: {c.current_title}')
    print(f'邮箱: {c.email}')
    print(f'来源: {c.source}')
    print(f'更新时间: {c.updated_at}')
    print(f'人才等级: {c.talent_tier}')
db.close()
"
```

### 小批量测试

```bash
# 先测试5个文件
python3 batch_import_cv_with_update.py \
  --source "/path/to/cv/directory" \
  --pattern "*.pdf" \
  --dry-run

# 检查结果后，实际导入
python3 batch_import_cv_with_update.py \
  --source "/path/to/cv/directory" \
  --pattern "*.pdf"
```

## 输出格式

### 成功导入

```
[1/80] Alexdan-工作4年-【脉脉招聘】.pdf
    📝 PDF解析成功: 3542字符 (PyPDF2)
  ✅ 更新成功 (方法:email)

[2/80] DeepDream-工作4年-【脉脉招聘】.pdf
    📝 PDF解析成功: 4121字符 (PyPDF2)
  ✅ 创建成功

...

============================================================
📊 导入汇总
============================================================
✅ 新建: 60 人
🔄 更新: 15 人
⏭️ 跳过: 0 人
❌ 失败: 5 人
📦 总计: 80 个文件
============================================================
```

### 失败情况

```
[10/80] xxx-工作3年-【脉脉招聘】.pdf
  ❌ PDF文本过短或无法解析 (2字符, 方法:none)

[25/80] yyy-工作5年-【脉脉招聘】.pdf
  ❌ AI解析失败: API timeout
```

## 常见问题

### Q1: "PDF文本过短"错误

**原因**：PDF是扫描版，PyPDF2无法提取文本

**解决方案**：
```bash
# 安装PyMuPDF（支持OCR）
pip install PyMuPDF
```

### Q2: AI解析超时

**原因**：
- 网络连接问题
- API调用频率过高
- PDF文本过长

**解决方案**：
- 检查网络连接
- 分批导入，避免一次性处理过多文件
- 系统已配置自动重试（3次）

### Q3: 候选人重复

**原因**：去重策略未匹配到

**解决方案**：
- 检查候选人邮箱是否正确
- 检查姓名+公司是否匹配
- 查看verbose日志了解匹配过程

### Q4: 数据没有更新

**原因**：
- 使用了--dry-run模式
- 数据库权限问题

**解决方案**：
- 移除--dry-run参数
- 检查数据库文件权限

### Q5: 扫描版PDF无法解析

**原因**：需要OCR功能

**解决方案**：
```bash
# 安装PyMuPDF
pip install PyMuPDF

# 或使用其他OCR工具
# 如：tesseract-ocr, pdf2image
```

### Q6: 姓名匹配不准确

**原因**：文件名可能是昵称，AI解析出真实姓名

**示例**：
- 文件名：`张紫陌-工作7年-【脉脉招聘】.pdf`
- AI解析：`肖雨薇`
- 去重：通过邮箱 `xiaoyuwei1201@163.com` 匹配

**解决方案**：邮箱是最准确的匹配方式

## 注意事项

### 数据安全

1. **备份数据库**：大批量导入前建议备份数据库
   ```bash
   cp data/headhunter_dev.db data/headhunter_dev.db.backup
   ```

2. **先用dry-run测试**：避免意外覆盖数据

3. **分批导入**：建议每批10-20个文件

### 性能考虑

1. **处理速度**：每个文件约30-60秒
   - PDF解析：1-2秒
   - AI解析：20-40秒
   - 数据库操作：1-2秒

2. **API限制**：注意API调用频率
   - 系统已配置自动重试
   - 避免并发导入

3. **大批量导入**：80个文件预计40-80分钟

### 数据质量

1. **AI解析准确性**：依赖于PDF文本质量
   - 文本版PDF：准确率90%+
   - 扫描版PDF：需要OCR

2. **数据合并**：智能合并但可能需要人工审核
   - 工作经历可能重复
   - 技能标签可能需要整理

3. **人才等级**：自动评估仅供参考
   - 可能需要人工调整
   - 基于工作年限、教育、公司背景

## 相关文件

- **主脚本**：`batch_import_cv_with_update.py`
- **测试脚本**：`test_cv_import_single.py`
- **数据库**：`data/headhunter_dev.db`
- **AI服务**：`ai_service.py`
- **数据模型**：`database.py`

## 后续步骤

导入完成后：

1. **验证数据**：检查导入的候选人数据是否正确
2. **人工审核**：审核人才等级是否准确
3. **补充信息**：添加缺失的联系信息
4. **开始联系**：使用outreach功能联系候选人
