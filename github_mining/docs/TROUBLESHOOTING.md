# GitHub Mining 故障排查手册

**最后更新**: 2026-03-11

---

## 📋 目录

1. [快速诊断](#快速诊断)
2. [数据问题](#数据问题)
3. [API 问题](#api-问题)
4. [进程问题](#进程问题)
5. [数据库问题](#数据库问题)
6. [批次问题](#批次问题)

---

## 🔍 快速诊断

### 批次卡住了？

```bash
# 1. 检查进程是否在运行
ps aux | grep batch_runner | grep -v grep

# 2. 检查日志最后更新时间
ls -lt batch*.log | head -1

# 3. 检查输出文件是否在增长
watch -n 10 'ls -lh runs/*/outputs/phase3_enriched.json'

# 4. 检查 Phase 子进程
ps aux | grep github_network_miner | grep -v grep
```

**常见原因**:
- Phase 3 处理大量数据（正常，需要等待）
- API 限流（检查日志中的 429 错误）
- 进程崩溃（检查日志中的错误信息）

---

### 数据丢失了？

```bash
# 1. 检查备份文件
ls -lh runs/*/outputs/*_backup_*

# 2. 检查归档目录
ls -lh runs/archive/

# 3. 检查其他批次
ls -lht runs/ | head -10

# 4. 检查 Git 历史（如果有版本控制）
git log --all --full-history -- "*.json"
```

---

### 日志文件为空？

```bash
# 1. 检查日志文件
ls -lh runs/*/logs/*.log

# 2. 检查进程是否还在运行
ps aux | grep phase3 | grep -v grep
```

**原因**: `batch_runner.py` 使用 `subprocess.run()` 等待进程完成后才写入日志

**解决方案**: 查看输出文件大小变化来监控进度

---

### 如何查看实时进度？

```bash
# 方法1: 查看输出文件人数
python3 -c "
import json
from pathlib import Path
latest = sorted(Path('runs').glob('*'))[-1]
phase3 = latest / 'outputs' / 'phase3_enriched.json'
if phase3.exists():
    data = json.load(open(phase3))
    print(f'已处理: {len(data)} 人')
"

# 方法2: 查看文件大小变化
watch -n 30 'ls -lh runs/*/outputs/phase3_enriched.json'

# 方法3: 查看进程 CPU 使用率
top -pid $(pgrep -f github_network_miner)
```

---

## 💾 数据问题

### 问题1: 数据被覆盖

**症状**: 运行批次后，之前的数据丢失

**原因**:
- 使用了固定文件名
- 没有时间戳
- 没有批次隔离

**解决方案**:
```bash
# ✅ 使用 batch_runner.py（自动批次隔离）
python3 batch_runner.py --input xxx.json --batch-name "unique_name"

# ❌ 不要直接运行 github_network_miner.py
```

**验证**:
```bash
# 检查是否有多个批次目录
ls -lht runs/ | head -5

# 每个批次应该有独立的目录
```

---

### 问题2: 数据重复

**症状**: 数据库中有重复的候选人

**原因**:
- 跳过了 DB Dedup 阶段
- 导入脚本的去重逻辑失效

**解决方案**:
```bash
# 1. 检查是否跳过了 DB Dedup
cat runs/*/batch_meta.json | jq '.phases'

# 2. 查询重复记录
sqlite3 ../../personal-ai-headhunter/data/headhunter_dev.db "
SELECT github_url, COUNT(*) as cnt
FROM candidates
WHERE source='github'
GROUP BY github_url
HAVING cnt > 1;
"

# 3. 删除重复记录（保留最新的）
# 注意：先备份数据库！
```

---

### 问题3: 外国人混入

**症状**: 数据库中有很多外国人

**原因**:
- 跳过了 Pre-filter 阶段
- Pre-filter 的国籍检测不准确

**解决方案**:
```bash
# 1. 检查是否跳过了 Pre-filter
cat runs/*/batch_meta.json | jq '.lineage.prefilter'

# 2. 查询外国人数量
sqlite3 ../../personal-ai-headhunter/data/headhunter_dev.db "
SELECT COUNT(*) FROM candidates
WHERE source='github'
  AND (name GLOB '*[A-Z][a-z]* [A-Z][a-z]*'
       OR location LIKE '%USA%'
       OR location LIKE '%UK%');
"

# 3. 下次运行时不要跳过 Pre-filter
```

---

### 问题4: 机构账户混入

**症状**: 数据库中有机构账户（如 "Microsoft", "Google"）

**原因**:
- Phase 5 数据缺少 `type` 字段
- Pre-filter 无法准确过滤机构账户

**解决方案**:
```bash
# 1. 查询机构账户
sqlite3 ../../personal-ai-headhunter/data/headhunter_dev.db "
SELECT name, github_url FROM candidates
WHERE source='github'
  AND (name IN ('Microsoft', 'Google', 'Facebook', 'Amazon')
       OR name LIKE '%Inc%'
       OR name LIKE '%Corp%');
"

# 2. 手动删除机构账户
# 注意：先备份数据库！

# 3. 改进：在 Phase 5 保存 type 字段
```

---

## 🌐 API 问题

### 问题1: API 限流（429 错误）

**症状**: 日志中出现 "429 Too Many Requests"

**原因**:
- GitHub API 限流（5000 次/小时）
- Token 失效或配额用完

**解决方案**:
```bash
# 1. 检查 Token 剩余配额
curl -H "Authorization: token ghp_xxxxx" \
  https://api.github.com/rate_limit

# 2. 等待配额恢复（每小时重置）
# 或使用另一个 Token

# 3. 配置多个 Token 轮换
vim github_hunter_config.py
# GITHUB_TOKENS = ["token1", "token2", "token3"]
```

---

### 问题2: Token 失效

**症状**: 401 Unauthorized

**原因**:
- Token 过期
- Token 权限不足

**解决方案**:
```bash
# 1. 测试 Token
curl -H "Authorization: token ghp_xxxxx" \
  https://api.github.com/user

# 2. 生成新 Token
# 访问: https://github.com/settings/tokens
# 权限: repo, user, read:org

# 3. 更新配置
vim github_hunter_config.py
```

---

### 问题3: 网络超时

**症状**: "Connection timeout" 或 "Read timeout"

**原因**:
- 网络不稳定
- GitHub API 响应慢

**解决方案**:
```bash
# 1. 检查网络连接
ping api.github.com

# 2. 使用断点续传
python3 batch_runner.py --resume-batch runs/xxx

# 3. 增加超时时间（修改代码）
# requests.get(url, timeout=30)  # 默认 10 秒
```

---

## 🔄 进程问题

### 问题1: 进程卡住

**症状**: 进程在运行，但没有输出

**原因**:
- 正在处理大量数据（正常）
- 等待 API 响应
- 死锁或无限循环（罕见）

**诊断**:
```bash
# 1. 检查进程状态
ps aux | grep batch_runner

# 2. 检查 CPU 使用率
top -pid $(pgrep -f batch_runner)

# 3. 检查输出文件是否在增长
watch -n 10 'ls -lh runs/*/outputs/*.json'

# 4. 如果确认卡住，强制终止
kill -9 $(pgrep -f batch_runner)
```

---

### 问题2: 内存不足

**症状**: "MemoryError" 或 "Killed: 9"

**原因**:
- 处理的数据量太大
- 内存泄漏

**解决方案**:
```bash
# 1. 检查内存使用
top -o MEM

# 2. 分批处理
# 将大文件拆分成小文件

# 3. 增加 swap 空间（临时）
sudo sysctl -w vm.swappiness=60
```

---

### 问题3: 进程意外终止

**症状**: 进程突然消失，没有错误信息

**原因**:
- 系统杀死进程（OOM Killer）
- 用户误操作
- 系统重启

**解决方案**:
```bash
# 1. 检查系统日志
dmesg | grep -i kill

# 2. 使用断点续传恢复
python3 batch_runner.py --resume-batch runs/xxx

# 3. 使用 nohup 防止终端关闭导致进程终止
nohup python3 batch_runner.py ... > batch.log 2>&1 &
```

---

## 💾 数据库问题

### 问题1: 导入失败

**症状**: "FileNotFoundError" 或 "Database is locked"

**原因**:
- 输出文件不存在
- 数据库被其他进程占用

**解决方案**:
```bash
# 1. 检查输出文件
ls -lh runs/*/outputs/phase45_final.json

# 2. 检查数据库锁
lsof ../../personal-ai-headhunter/data/headhunter_dev.db

# 3. 等待其他进程完成，或重启数据库连接
```

---

### 问题2: 评级错误

**症状**: 所有人都是 C 级，或评级分布不合理

**原因**:
- 评级脚本未执行
- 评级标准配置错误

**解决方案**:
```bash
# 1. 检查是否执行了 tier_update
cat runs/*/batch_meta.json | jq '.lineage.tier_update'

# 2. 手动运行评级
cd ../../personal-ai-headhunter
python3 batch_update_tiers.py

# 3. 检查评级配置
cat data/company_tier_config.json
```

---

## 📦 批次问题

### 问题1: 批次目录混乱

**症状**: runs/ 目录下有很多批次，不知道哪个是最新的

**解决方案**:
```bash
# 1. 列出所有批次（按时间排序）
python3 batch_runner.py --list

# 2. 查看最新批次
ls -lht runs/ | head -5

# 3. 清理失败的批次
rm -rf runs/*_failed_*
```

---

### 问题2: 软链接失效

**症状**: `phase3_enriched_latest.json` 指向不存在的文件

**解决方案**:
```bash
# 1. 检查软链接
ls -lh github_mining/phase3_enriched_latest.json

# 2. 重新创建软链接
ln -sf runs/latest_batch/outputs/phase3_enriched.json \
  github_mining/phase3_enriched_latest.json
```

---

## 📞 获取帮助

### 常见问题速查

| 症状 | 可能原因 | 快速解决 |
|------|---------|---------|
| 批次卡住 | 正在处理数据 | 等待或查看进度 |
| 数据丢失 | 文件被覆盖 | 检查备份文件 |
| API 限流 | Token 配额用完 | 等待或换 Token |
| 进程终止 | 内存不足 | 分批处理 |
| 导入失败 | 文件不存在 | 检查输出文件 |

### 诊断流程

```
遇到问题
  ↓
检查进程状态 (ps aux)
  ↓
检查日志文件 (tail -f)
  ↓
检查输出文件 (ls -lh)
  ↓
查看本手册对应章节
  ↓
尝试解决方案
  ↓
仍未解决？更新本文档
```

---

**最后更新**: 2026-03-11
**维护者**: GitHub Mining Team
