# GitHub Mining 端到端流程指南

## 📋 概述

本文档记录 GitHub Mining 项目中端到端流程的完整经验、问题解决和最佳实践。

**最后更新**: 2026-03-10

---

## 🎯 完整的端到端流程

一个标准的 GitHub Mining 端到端流程包含以下阶段：

```
种子准备 → Phase 5 扩展 → Phase 3 富化 → Phase 3.5 爬取 → Phase 4.5 LLM → 导入数据库
```

### 各阶段说明

| 阶段 | 输入 | 输出 | 预计时间 | 说明 |
|------|------|------|----------|------|
| **种子准备** | Phase 4.5 数据 | 种子 JSON | 5分钟 | 筛选高质量种子用户 |
| **Phase 5** | 种子 JSON | `phase5_expanded_*.json` | 10-12小时 | 社交网络扩展 |
| **Phase 3** | Phase 5 输出 | `phase3_from_*.json` | 30-45分钟 | 获取 repos 详情 |
| **Phase 3.5** | Phase 3 输出 | `phase35_from_*.json` | 1-2小时 | 爬取个人网站 |
| **Phase 4.5** | Phase 3.5 输出 | `phase45_*_final.json` | 2-3小时 | LLM 结构化提取 |
| **导入** | Phase 4.5 输出 | 数据库 | 5-10分钟 | 入库 |

**总计**: ~14-18 小时（无人值守）

---

## ⚠️ 关键问题与解决方案

### 问题 1: 数据覆盖 ❌

**问题**：
- 多次运行使用相同文件名 `phase5_expanded.json`
- 27,483 用户数据被覆盖丢失

**原因**：
```python
# 错误做法：固定文件名
output_file = BASE_DIR / "phase5_expanded.json"
```

**解决方案**：
```python
# ✅ 正确做法：带时间戳 + 种子标识
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
seeds_name = Path(seeds_file).stem
output_filename = f"phase5_expanded_{seeds_name}_{timestamp}.json"
```

**验证**：
```bash
# 检查是否有历史文件
ls -lht scripts/github_mining/phase5_expanded_*.json
```

---

### 问题 2: 交互式检查在自动化中失效 ❌

**问题**：
```python
# ⚠️ 这种检查在自动重启时会失效
choice = input("是否覆盖？ =>
if choice != 'y':
    return None
```

**解决方案**：
```python
# ✅ 自动备份 + 归档
def archive_existing_data(output_file, timestamp, seeds_name):
    """自动归档旧数据，不依赖交互"""
    archive_base = BASE_DIR / "archive" / "phase5_expanded" / datetime.now().strftime('%Y%m')
    archive_path = archive_base / f"phase5_expanded_{seeds_name}_{timestamp}.json"
    shutil.copy2(output_file, archive_path)
```

---

### 问题 3: 进度恢复机制 ⚠️

**实现方式**：
```python
# 每 50 个种子保存一次进度
if (i + 1) % 50 == 0:
    progress = {
        "processed_seeds": i + 1,
        "total_new_users": len(cooccurrence),
        "high_cooccurrence": len([v for v in cooccurrence.values() if v >= min_cooccurrence]),
        "timestamp": datetime.now().isoformat()
    }
    json.dump(progress, open(progress_file, 'w'))
```

**验证**：
```bash
# 查看进度文件
cat scripts/github_mining/phase5_progress.json

# 如果需要重新开始，删除进度文件
rm scripts/github_mining/phase5_progress.json
```

---

## 📝 端到端脚本模板

### 完整模板

```bash
#!/bin/bash
# 项目名称端到端流程
set -e  # 遇到错误立即退出

echo "=========================================="
echo "🚀 项目完整流程"
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

cd /path/to/project

# Phase 1: XXX
echo "▶️  Step 1/4: Phase XXX..."
python3 script1.py \
  --input data/input.json \
  --output data/output1.json

# 验证输出
if [ ! -f "data/output1.json" ]; then
    echo "❌ Phase 1 失败"
    exit 1
fi

# Phase 2: XXX
echo "▶️  Step 2/4: Phase XXX..."
python3 script2.py \
  --input data/output1.json \
  --output data/output2.json

# 验证输出
if [ ! -f "data/output2.json" ]; then
    echo "❌ Phase 2 失败"
    exit 1
fi

# ... 其他阶段 ...

echo "✅ 流程完成！"
```

### 后台运行

```bash
# 使用 nohup 运行，防止终端断开
nohup bash run_xxx_end_to_end.sh > phase_xxx_e2e.log 2>&1 &

# 监控进度
tail -f phase_xxx_e2e.log

# 检查进程
ps aux | grep run_xxx_end_to_end
```

---

## 🔍 数据验证检查点

每个阶段完成后必须验证：

### 1. 文件存在性
```bash
# 检查输出文件
ls -lh path/to/output.json
```

### 2. 数据完整性
```python
# 快速检查
python3 -c "import json; print(len(json.load(open('output.json'))))"
```

### 3. 数据质量
```python
# 检查关键字段
python3 << 'EOF'
import json
data = json.load(open('output.json'))
with_field = sum(1 for u in data if u.get('company'))
print(f"有公司信息: {with_field}/{len(data)}")
EOF
```

---

## 📁 文件命名规范

### 输入文件
- `phase4_round2_seeds_0308.json` - 包含日期标识
- `phase5_seed_usernames_sb.json` - 包含来源标识

### 输出文件
- `phase5_expanded_{seeds}_{timestamp}.json` - 包含种子和时间戳
- `phase3_from_phase5.json` - 包含来源标识
- `phase45_phase5_final.json` - 包含来源和阶段标识

### 备份和归档
```
archive/
  phase5_expanded/
    202603/
      phase5_expanded_seeds_20260309_175912.json
```

---

## 🎯 最佳实践

### DO ✅

1. **所有输出文件带时间戳**
   ```python
   timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
   ```

2. **自动备份旧数据**
   ```python
   shutil.copy2(old_file, backup_path)
   ```

3. **使用相对路径或绝对路径**
   ```python
   # 明确路径
   BASE_DIR = Path(__file__).parent / "github_mining"
   output_file = BASE_DIR / f"output_{timestamp}.json"
   ```

4. **每个阶段验证输出**
   ```bash
   if [ ! -f "output.json" ]; then
       echo "❌ 输出文件不存在"
       exit 1
   fi
   ```

5. **记录详细日志**
   ```bash
   nohup bash script.sh > log_$(date +%Y%m%d_%H%M%S).log 2>&1 &
   ```

### DON'T ❌

1. **不要使用固定文件名**
   ```python
   # ❌ 错误
   output = "results.json"

   # ✅ 正确
   output = f"results_{timestamp}.json"
   ```

2. **不要依赖交互式输入**
   ```python
   # ❌ 错误
   choice = input("Continue? =>

   # ✅ 正确
   print("Auto-continuing...")
   ```

3. **不要假设文件存在**
   ```python
   # ❌ 错误
   with open('output.json') as f:
       data = json.load(f)

   # ✅ 正确
   if Path('output.json').exists():
       with open('output.json') as f:
           data = json.load(f)
   ```

4. **不要在脚本中硬编码路径**
   ```python
   # ❌ 错误
   file = "/Users/lillianliao/notion_rag/data.json"

   # ✅ 正确
   file = BASE_DIR / "data.json"
   ```

---

## 🔄 断点续传实现

### 进度文件结构

```json
{
  "processed_seeds": 4050,
  "total_new_users": 121928,
  "high_cooccurrence": 35863,
  "timestamp": "2026-03-09T19:57:02.574242"
}
```

### 恢复逻辑

```python
progress_file = BASE_DIR / "phase5_progress.json"
start_index = 0

if progress_file.exists():
    with open(progress_file) as f:
        progress = json.load(f)
    start_index = progress.get('processed_seeds', 0)
    print(f"🔄 从进度恢复: {start_index} 个种子")

for i, seed in enumerate(seeds[start_index:], start=start_index):
    # 处理种子...

    # 定期保存
    if (i + 1) % 50 == 0:
        json.dump({
            "processed_seeds": i + 1,
            "timestamp": datetime.now().isoformat()
        }, open(progress_file, 'w'))
```

---

## 📊 监控和调试

### 实时监控
```bash
# 查看日志
tail -f script.log

# 查看进程
ps aux | grep script_name

# 查看文件大小变化
watch -n 10 'ls -lh output.json'
```

### 进度检查
```bash
# Phase 5 进度
cat scripts/github_mining/phase5_progress.json

# 当前用户数
jq 'length' scripts/github_mining/phase5_expanded_latest.json

# 数据增长
watch -n 30 'jq length scripts/github_mining/phase5_expanded_latest.json'
```

---

## 🚨 常见错误处理

### 错误 1: GitHub API 限流

```bash
# 症状：HTTP 403, 429
# 解决：增加 token 数量或降低请求频率
```

### 错误 2: 进程被杀死

```bash
# 症状：Killed: 9
# 原因：内存不足
# 解决：分批处理或增加 swap
```

### 错误 3: mv 命令失败

```bash
# 症状：mv: rename ... No such file or directory
# 原因：路径错误
# 解决：检查工作目录和相对路径
```

---

## 📚 相关文档

- [批次管理系统设计](../personal-ai-headhunter/docs/batch_management_system.md)
- [数据归档策略](../personal-ai-headhunter/docs/data_archive_strategy.md)
- [Phase 5 扩展说明](./phase5_expansion_guide.md)

---

## 📝 更新日志

### 2026-03-10
- 创建文档
- 记录 Phase 5 数据覆盖问题及解决方案
- 添加端到端流程最佳实践

---

**维护者**: GitHub Mining Team
**最后审查**: 2026-03-10
