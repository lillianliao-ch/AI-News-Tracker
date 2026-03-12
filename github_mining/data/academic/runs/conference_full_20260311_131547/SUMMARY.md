# 顶会人才全量挖掘批次记录
- **批次编号**: conference_full_20260311_131547
- **启动时间**: 2026-03-11 13:15:47
- **安全隔离目录**: /Users/lillianliao/notion_rag/github_mining/scripts/../data/academic/runs/conference_full_20260311_131547

## 运行特性
1. **无人值守**: 采用 `nohup` 后台挂机运行，关闭终端不影响拉取。
2. **断点续传**: 
   - 依赖底层 `_s2_cache.json` 和 `_contact_cache.json`。
   - 就算进程被杀，只要再次用相同的 `--output-dir` 启动，脚本就能秒秒钟恢复所有已查过的记录，不会丢失任何一条 API 查询！
3. **数据备份隔离**: 每次执行都会新建独立的时间戳目录，历史数据绝对安全，0 覆盖风险。

## 实时监控清单
执行以下命令随时查看进度：
- 2024年: `tail -f /Users/lillianliao/notion_rag/github_mining/scripts/../data/academic/runs/conference_full_20260311_131547/logs/run_2024.log`
- 2023年: `tail -f /Users/lillianliao/notion_rag/github_mining/scripts/../data/academic/runs/conference_full_20260311_131547/logs/run_2023.log`
- 2022年: `tail -f /Users/lillianliao/notion_rag/github_mining/scripts/../data/academic/runs/conference_full_20260311_131547/logs/run_2022.log`
