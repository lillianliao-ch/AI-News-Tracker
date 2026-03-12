# GitHub Mining 关键问题解决方案

本文档记录 GitHub Mining 项目中遇到的重大问题及其永久性解决方案，防止再次发生。

**最后更新**: 2026-03-10
**状态**: ✅ 已解决并验证

---

## 🔥 问题 #1: 数据被覆盖 (CRITICAL)

### 发生时间
2026-03-09

### 问题描述
Phase 5 多次运行导致数据被覆盖：
- 第一次运行发现 **27,483** 用户
- 第二次运行只发现 **62** 用户
- 第一次的数据完全丢失

### 根本原因
1. **固定文件名**：
   ```python
   # ❌ 错误代码
   output_file = BASE_DIR / "phase5_expanded.json"
   ```

2. **交互式检查失效**：
   ```python
   # ❌ 在自动重启时无法工作
   choice = input("是否覆盖？ =>
   ```

3. **mv 命令失败**：
   ```bash
   # 路径错误导致失败
   mv scripts/github_mining/phase5_expanded.json github_mining/xxx.json
   ```

### 永久解决方案

#### 1. 带时间戳的文件命名

```python
def generate_output_filename(seeds_file):
    """生成唯一文件名，防止覆盖"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    seeds_name = Path(seeds_file).stem
    # 格式: phase5_expanded_phase4_round2_seeds_0308_20260309_175912.json
    output_filename = f"phase5_expanded_{seeds_name}_{timestamp}.json"
    return BASE_DIR / output_filename
```

#### 2. 自动归档系统

```python
def archive_existing_data(output_file, timestamp, seeds_name):
    """自动归档，不依赖交互"""
    archive_base = BASE_DIR / "archive" / "phase5_expanded" / datetime.now().strftime('%Y%m')
    archive_base.mkdir(parents=True, exist_ok=True)

    archive_name = f"phase5_expanded_{seeds_name}_{timestamp}.json"
    archive_path = archive_base / archive_name

    shutil.copy2(output_file, archive_path)
    return archive_path
```

#### 3. 双重保存机制

```python
# 保存到带时间戳的文件（永久）
miner._save_json(expanded, output_file)

# 同时保存到 latest 副本（方便使用）
latest_link = BASE_DIR / "phase5_expanded_latest.json"
miner._save_json(expanded, latest_link)
```

### 验证方法

```bash
# 检查是否有历史文件
ls -lht scripts/github_mining/phase5_expanded_*.json

# 应该看到多个文件，而不是只有一个
```

### 文档
- 详细指南: [end_to_end_workflow_guide.md](./end_to_end_workflow_guide.md)
- 实现位置: `scripts/run_phase5_expansion.py:65-112`

---

## ⚠️ 问题 #2: 断点续传不完整

### 发生时间
2026-03-09

### 问题描述
- 进度文件存在，但重启时未能正确恢复
- 导致重复处理已处理的种子

### 根本原因
进度文件保存不完整，缺少必要的状态信息。

### 永久解决方案

```python
# 完整的进度信息
progress = {
    "processed_seeds": i + 1,
    "total_new_users": len(cooccurrence),
    "high_cooccurrence": len([v for v in cooccurrence.values() if v >= min_cooccurrence]),
    "timestamp": datetime.now().isoformat()
}
```

### 验证方法

```bash
# 查看进度文件
cat scripts/github_mining/phase5_progress.json

# 重新开始（如果需要）
rm scripts/github_mining/phase5_progress.json
```

---

## 🔧 问题 #3: 端到端流程中断

### 发生时间
2026-03-10

### 问题描述
- Phase 5 完成后没有自动执行后续阶段
- 需要手动干预

### 根本原因
缺少统一的端到端脚本。

### 永久解决方案

创建端到端脚本：
```bash
# 完整流程脚本
run_phase5_end_to_end.sh

# 使用方法
nohup bash run_phase5_end_to_end.sh > phase5_e2e.log 2>&1 &
```

**关键特性**：
1. ✅ `set -e` - 遇到错误立即退出
2. ✅ 每个阶段验证输出文件
3. ✅ 详细的日志记录
4. ✅ 支持后台运行

### 文档
- 模板脚本: `run_phase5_end_to_end.sh`
- 详细指南: [end_to_end_workflow_guide.md](./end_to_end_workflow_guide.md)

---

## 📋 检查清单

在创建新的端到端流程前，必须确认：

### 文件命名
- [ ] 所有输出文件带时间戳
- [ ] 文件名包含来源标识
- [ ] 使用绝对路径或明确的相对路径

### 数据安全
- [ ] 实现自动备份机制
- [ ] 实现自动归档机制
- [ ] 保留 latest 副本供后续使用

### 断点续传
- [ ] 定期保存进度（每50/100个单位）
- [ ] 进度文件包含所有必要状态
- [ ] 重启时能正确恢复

### 错误处理
- [ ] 每个阶段验证输出文件
- [ ] 遇到错误立即退出 (set -e)
- [ ] 详细的错误日志

### 文档
- [ ] 更新本文档记录新问题
- [ ] 更新端到端流程指南
- [ ] 创建使用说明

---

## 🔍 问题回顾

### 已解决 ✅

1. ✅ 数据覆盖问题 - 通过时间戳命名 + 归档
2. ✅ 交互检查失效 - 通过自动备份
3. ✅ 端到端中断 - 通过统一脚本

### 待解决 ⏳

1. ⏳ 批次管理系统完全集成
2. ⏳ 种子文件自动保存
3. ⏳ 批次总结报告自动生成

---

**维护者**: GitHub Mining Team
**最后更新**: 2026-03-10
**下次审查**: 2026-03-17
