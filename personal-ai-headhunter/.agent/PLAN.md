# AI 职位匹配系统 - 全量标签更新计划

## 📋 任务概述
更新所有职位和候选人的结构化标签，从旧格式（`specialty`）迁移到新格式（`core_specialty` + `tech_skills`），以充分利用主/辅线权重优化体系。

## 📊 当前状态
- **职位**: 415 条，仅 2 条新格式，需更新 409 条
- **候选人**: 1,189 条，仅 3 条新格式，需更新 1,143 条

---

## ✅ 执行步骤

### Phase 1: 职位标签全量更新
// turbo
- [ ] **Step 1.1**: 运行职位标签更新命令
  ```bash
  cd /Users/lillianliao/notion_rag/personal-ai-headhunter
  python extract_tags.py jobs --force
  ```
  预计耗时: ~40 分钟

- [ ] **Step 1.2**: 验证职位标签更新结果
  ```bash
  python3 -c "
  import sqlite3, json
  conn = sqlite3.connect('data/headhunter_dev.db')
  cur = conn.cursor()
  cur.execute('SELECT COUNT(*) FROM jobs WHERE structured_tags LIKE \"%core_specialty%\"')
  print(f'新格式职位数: {cur.fetchone()[0]} / 415')
  "
  ```

### Phase 2: 候选人标签全量更新
// turbo
- [ ] **Step 2.1**: 运行候选人标签更新命令
  ```bash
  cd /Users/lillianliao/notion_rag/personal-ai-headhunter
  python extract_tags.py candidates --force
  ```
  预计耗时: ~2 小时

- [ ] **Step 2.2**: 验证候选人标签更新结果
  ```bash
  python3 -c "
  import sqlite3, json
  conn = sqlite3.connect('data/headhunter_dev.db')
  cur = conn.cursor()
  cur.execute('SELECT COUNT(*) FROM candidates WHERE structured_tags LIKE \"%core_specialty%\"')
  print(f'新格式候选人数: {cur.fetchone()[0]} / 1189')
  "
  ```

### Phase 3: 功能验证
- [ ] **Step 3.1**: 测试匹配功能（语音合成场景）
  - 候选人: 徐学欣（TTS专家）
  - 验证: #57 语音合成算法专家应排名前 5

- [ ] **Step 3.2**: 测试匹配功能（Agent/对话系统场景）
  - 候选人: 马占宇
  - 验证: #8 AI对话系统算法专家应排名前 3

- [ ] **Step 3.3**: 测试匹配功能（三维重建场景）
  - 候选人: 张行航
  - 验证: #397 3D重建算法工程师应排名前 5

### Phase 4: 同步到生产环境
- [ ] **Step 4.1**: 将更新后的开发数据库复制到生产环境
  ```bash
  cp data/headhunter_dev.db ../personal-ai-headhunter-prod/data/headhunter.db
  ```

- [ ] **Step 4.2**: 同步代码更新（job_search.py, extract_tags.py）
  ```bash
  cp job_search.py ../personal-ai-headhunter-prod/
  cp extract_tags.py ../personal-ai-headhunter-prod/
  ```

### Phase 5: 后续优化（可选）
- [ ] **Step 5.1**: 实现同义词映射系统
- [ ] **Step 5.2**: 优化 Prompt 模板提高准确性
- [ ] **Step 5.3**: 添加标签质量监控脚本

---

## 📝 执行日志

| 时间 | 步骤 | 状态 | 备注 |
|:---|:---|:---:|:---|
| 2026-01-27 09:56 | 计划创建 | ✅ | - |
| 2026-01-27 09:57 | 数据库备份 | ✅ | headhunter_dev_backup_20260127_0957.db |
| 2026-01-27 09:58 | 修改 extract_tags.py | ✅ | 添加 --force 参数支持 |
| 2026-01-27 09:58 | Phase 1: 职位标签更新 | ✅ | 415/415 完成 |
| 2026-01-27 10:20 | Phase 2: 候选人标签更新 | ✅ | 1189/1189 完成 |
| 2026-01-27 11:38 | Phase 3: 功能验证 | ✅ | 3/3 测试用例通过 |
| 2026-01-27 11:39 | Phase 4: 同步到生产 | ✅ | DB + 代码已同步 |

## 🎉 任务完成总结

### 数据更新
- **职位**: 415 条全部更新为新格式 (`core_specialty` + `tech_skills`)
- **候选人**: 1189 条全部更新为新格式
- **总耗时**: ~1小时45分钟

### 验证结果
| 测试用例 | 预期职位 | 排名 | 分数 |
|:---|:---|:---:|:---:|
| 徐学欣 (TTS) | #57 语音合成算法专家 | #1 | 104.10 |
| 马占宇 (Agent) | #8 AI对话系统算法专家 | #1 | 106.00 |
| 张行航 (3D) | #397 3D重建算法工程师 | #1 | 71.30 |

### 同步文件
- `data/headhunter.db` → prod
- `job_search.py` → prod
- `extract_tags.py` → prod

---

## ⚠️ 注意事项
1. 确保 `DASHSCOPE_API_KEY` 环境变量已设置
2. 更新过程中避免修改数据库
3. 建议在更新前备份数据库
