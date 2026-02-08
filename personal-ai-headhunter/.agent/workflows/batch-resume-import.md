---
description: 批量导入简历文件到AI猎头系统，自动解析并创建候选人
---

# 批量导入简历到AI猎头系统

本技能用于将一个目录下的所有简历文件（PDF/TXT/图片）批量导入到AI猎头系统中，自动进行AI解析并创建候选人记录。

## 前置条件

1. AI猎头系统已部署并运行
2. 后台Worker已启动
3. 安装了必要依赖：`PyPDF2`, `PyMuPDF`, `Pillow`

## 完整流程

### 步骤1：确认源目录

确认要导入的简历文件所在目录：
```bash
ls -la "/path/to/resumes/"
```

支持的文件格式：
- PDF（文本版和扫描版）
- TXT
- JPG/JPEG/PNG/WEBP（图片简历）

### 步骤2：运行批量导入脚本

// turbo
```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 batch_import_resumes.py "/path/to/resumes/"
```

脚本功能：
- 自动过滤非简历文件（论文等）
- 跳过已导入的文件（基于文件名去重）
- 将文件复制到uploads目录并创建处理任务

### 步骤3：确保后台Worker运行

// turbo
```bash
# 检查Worker状态
ps aux | grep resume_worker | grep -v grep

# 如果未运行，启动Worker
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
nohup python3 -u resume_worker.py > worker.log 2>&1 &
```

### 步骤4：监控处理进度

// turbo
```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 resume_worker.py status
```

输出示例：
```
📊 任务队列状态:
   待处理: 10
   处理中: 1
   已完成: 35
   失败:   2
```

### 步骤5：处理失败任务（如有）

查看失败原因：
```bash
python3 -c "
from database import SessionLocal, ResumeTask
db = SessionLocal()
failed = db.query(ResumeTask).filter(ResumeTask.status == 'failed').all()
for t in failed:
    print(f'{t.file_name}: {t.error_message[:80]}')
db.close()
"
```

重置失败任务重试：
```bash
python3 -c "
from database import SessionLocal, ResumeTask
db = SessionLocal()
for t in db.query(ResumeTask).filter(ResumeTask.status == 'failed').all():
    t.status = 'pending'
    t.error_message = None
db.commit()
print('已重置')
db.close()
"
```

### 步骤6：为新候选人提取标签

// turbo
```bash
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
python3 extract_tags.py candidates
```

### 步骤7：复制原始简历到正确位置

确保简历附件可下载：
```bash
python3 -c "
import os
import shutil
from database import SessionLocal, Candidate, ResumeTask

db = SessionLocal()
tasks = db.query(ResumeTask).filter(ResumeTask.status == 'done').all()
RESUMES_DIR = 'data/resumes'
os.makedirs(RESUMES_DIR, exist_ok=True)

for task in tasks:
    if not task.candidate_id:
        continue
    cand = db.query(Candidate).filter(Candidate.id == task.candidate_id).first()
    if not cand or not os.path.exists(task.file_path):
        continue
    dest = os.path.join(RESUMES_DIR, f'{cand.id}_{task.file_name}')
    if not os.path.exists(dest):
        shutil.copy2(task.file_path, dest)
        print(f'✅ {cand.name}')
db.close()
"
```

## 关键脚本说明

### batch_import_resumes.py
- 位置：`/Users/lillianliao/notion_rag/personal-ai-headhunter/batch_import_resumes.py`
- 功能：扫描目录，将简历加入处理队列
- 用法：`python3 batch_import_resumes.py <目录路径>`

### resume_worker.py
- 位置：`/Users/lillianliao/notion_rag/personal-ai-headhunter/resume_worker.py`
- 功能：后台处理简历解析任务
- 用法：
  - `python3 resume_worker.py` - 启动worker
  - `python3 resume_worker.py status` - 查看队列状态
  - `nohup python3 -u resume_worker.py > worker.log 2>&1 &` - 后台运行

### extract_tags.py
- 位置：`/Users/lillianliao/notion_rag/personal-ai-headhunter/extract_tags.py`
- 功能：为候选人提取结构化标签
- 用法：`python3 extract_tags.py candidates`

## 处理能力

- 支持扫描版PDF（自动OCR）
- 支持多页简历
- 自动推算年龄（基于教育经历）
- 自动重试（API超时时最多3次）
- 每个简历处理时间约1-2分钟

## 常见问题

### Q: "文件内容为空"错误
A: PDF是扫描版，需要安装PyMuPDF进行OCR处理：
```bash
pip install PyMuPDF
```

### Q: API超时
A: 系统已配置自动重试（3次，每次间隔5秒）。如仍失败，可手动重置任务重试。

### Q: 候选人重复
A: 批量导入脚本会基于文件名自动去重。如需更新已有候选人，需手动删除后重新导入。

### Q: 新导入的候选人没有出现在"最新导入"列表前面
A: 这是时区问题。数据库默认时间已改为本地时间(datetime.now)。如果之前导入的候选人时间不对，可以手动修正：
```bash
python3 -c "
from database import SessionLocal, Candidate
from datetime import timedelta
db = SessionLocal()
# 修正后台解析导入的候选人时间（加8小时）
for c in db.query(Candidate).filter(Candidate.source.like('%后台解析%')).all():
    if c.created_at:
        c.created_at = c.created_at + timedelta(hours=8)
db.commit()
print('时间已修正')
db.close()
"
```

## 注意事项

1. **时区**：系统使用本地时间(北京时间 UTC+8)存储created_at
2. **去重**：基于文件名去重，同名文件不会重复导入
3. **简历附件**：导入后需执行步骤7将PDF复制到data/resumes/目录才能下载
4. **标签提取**：导入后需执行步骤6才能使用智能匹配功能
