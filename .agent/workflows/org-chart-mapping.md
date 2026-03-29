---
description: 根据候选人履历池，逆向还原任意大厂核心团队的组织架构图谱 (Org Chart Mapping)
---
# Org Chart Mapping Workflow

当用户希望对某个特定大厂（如腾讯、阿里、字节）的某个核心团队（如混元、通义、Seed）进行类似的人才盘点和组织架构逆向工程时，请遵循本标准操作流程。

## 用户触发指令推荐 (Prompt)

每次想跑新的架构图，用户可以直接使用 slash command：
> **/org-chart-mapping** 
> **目标公司**：[例如：阿里巴巴 / Alibaba]
> **目标团队关键词**：[例如：通义 / Qwen / 达摩院 / M6]

## 自动化引擎调用规范 (Execution Steps)

1. **绝对不要再重新写 SQL 或造轮子**
   在2026年3月底的架构升级中，我们已经封装了极度稳定的通用提取器 `generic_extract_org_chart.py`。
   它的绝对路径是：`/Users/lillianliao/notion_rag/skill_research/generic_extract_org_chart.py`

2. **直接传参调用 Generic Extractor**
   你需要帮用户直接在终端调用上述脚本：
   ```bash
   python3 /Users/lillianliao/notion_rag/skill_research/generic_extract_org_chart.py \
     --companies "公司搜索词1,公司搜索词2" \
     --teams "团队词1,团队词2,产品代号" \
     --prefix "生成文件前缀" \
     --desc "一句话描述这个团队的愿景" \
     --title "最后渲染的Markdown大标题"
   ```

3. **批量模式 (Batch Mode)**
   如果用户一次性给出了多个目标（例如：“帮我把大模型剩下的四小龙全跑了”），请参考或直接修改 `/Users/lillianliao/notion_rag/skill_research/run_batch_unicorns.py` 这个守护进程脚本，通过配置字典序列化执行，不要让用户干等。

4. **产出物投递**
   脚本运行完，将产出的 Markdown 文件直接 `cp` 拷贝到当前界面的 Artifacts 目录展示给用户。

## 衍生能力：JD (职位描述) Deep Dive 分析
除了用来反推组织架构，还可以调用 NotebookLM 针对活跃 JD 开展深度商业意图穿透。
配套的 Pitching 话术与业务拆解 Prompt 位于今天生成的 Artifact 资产：`JD_Analysis_NotebookLM_Prompt.md` 中。
