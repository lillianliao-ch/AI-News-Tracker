# 调研报告：notebooklm-py

**调研日期**: 2026-03-27
**项目地址**: https://github.com/teng-lin/notebooklm-py
**标签**: RAG, 数据提取, 多模态, Claude-Skill

## 1. 核心定位
`notebooklm-py` 是一个 Google NotebookLM 的非官方 Python API。它填补了官方只有 Web UI 的空白。
更重要的是，它自带了兼容 Claude Code / OpenClaw 的 `SKILL.md`，可以做到“开箱即用”地被 Agent 调用。

## 2. 独家高级功能 (超出网页端界面)
- **数据结构化提取**：可以将 NotebookLM 生成的 Data Tables 直接导出为 CSV，把测试题/闪卡导出为 JSON。
- **思维导图数据化**：可以直接导出 Mind Map JSON 数据。
- **批量导出**：下载多模态播客（Audio Overviews MP3/MP4）、编辑版 PPTX（突破官方的 PDF 限制）。
- **零点击管理**：自动化创建 Notebook，上传超大长文本或 URL/Drive。

## 3. 业务落地脑爆场景 (核心价值分析)

### 场景一：分析 多模API 与 JD 异同（对标分析）
- 把十几个竞品的 JD 丢进去，用 NotebookLM 直接跨文档对比他们的核心技术栈偏好、团队文化、业务重点（ToB vs ToC），输出结构化对标 CSV。

### 场景二：公司组织架构图还原 (Organization Mapping)
- 提取单一公司的几百份简历（合成为大段 Markdown 作为 Source），利用大模型 100万 Token 的超长上下文全局理解能力，反演出汇报关系和部门树状结构，通过专属 API 抽取为 Mind Map JSON，生成可视化架构化。

### 场景三：核心人物“二度人脉”关联圈 (Social Graph)
- **突破向量库(Vector DB)瓶颈**：把某技术大牛的 GitHub 仓、顶会论文和一堆模糊简历丢给它。不需要专门的实体识别 NER 算法，NotebookLM 会自己做高阶推理（比如根据工作年限、项目吻合度）找出哪些简历背后的匿别人，其实就在该大牛手里打工，或者互相共事过。

### 场景四：自动播客与内容流水线 (AI News Tracker 拓展)
- 用 `notebooklm-py` 程序化生成 NotebookLM 最出圈的双人对话播客（Audio Overviews）。将每天汇聚的新闻/RSS、投递人的亮点履历一键转为高质量多模态内容对外分发。

## 4. 与本地 `chroma_db` 的生态位互补
- **当前本地 ChromaDB（向量库）**：用于“大浪淘沙”式宽筛。秒级找出符合若干关键词（或者具有某种潜台词）技能范围的海量人选。
- **notebooklm-py（1M Token全量RAG）**：用于“定点攻坚”和“深钻”。把那百十号核心候选人的所有料（甚至几十页几十篇论文全本）灌进去，进行深层次的图谱推导和能力对齐，产出详尽的推荐背书或架构图。

## 5. 结论建议
值得部署并尝试作为我们猎头流程的“深钻外挂大脑”，或 AI 资讯系统的多模态生成引擎。

---

## 6. 核心实战落地成果 (2026-03 存档)

在随后的实战演练中，我们将上述脑爆场景彻底工程化并落地：

### 落地套件 A：大厂与大模型独角兽架构逆向工程 (Org Chart Mapping)
- **实现方案**: 编写了 `generic_extract_org_chart.py` 通用提取器与 `run_batch_unicorns.py` 批处理并发守护进程。通过数据库 SQL 提取特定团队候选人经历，切分为 10-15 人的 Mega-Chunk 扔进 NotebookLM 提问重构。
- **已攻克名录 (共 13 家顶尖 AI 机构)**：
  - **传统大厂战区**: 字节跳动 (Seed), 腾讯 (Hunyuan/AI Lab), 小红书 (星光), 阿里 (Qwen/达摩院), 百度 (ERNIE), 华为 (盘古/诺亚方舟), 快手 (可图), 美团 (光年之外)。
  - **海外战区**: Microsoft (MSRA), Nvidia (Megatron), Meta (FAIR), Google (DeepMind)。
  - **大模型“六只独角兽”满贯**: DeepSeek (深度求索), 月之暗面 (Moonshot), 智谱 (Zhipu), 百川智能 (Baichuan), 零一万物 (01.AI), 阶跃星辰 (StepFun)。
- **资产沉淀**: 上述所有大厂的深度架构 Markdown 还原图谱均已固化，对应的全自动调用链路也已固化至 `/org-chart-mapping` 快捷工作流规范中。

### 落地套件 B：海量活跃职位深探 (JD Deep Analysis)
- **实现方案**: 开发了脚本脱水过滤 1171 份活跃高职级 JD 并上传建立专门的大型职场分析外挂大脑。
- **使用场景**: 搭配 `JD_Analysis_NotebookLM_Prompt.md` 的业务穿透话术，可以秒级看透大厂背后的真实用人痛点，并自动拉出顶尖猎头的话术模板（Pitching Framework）。

### 落地套件 C：全域分发矩阵拓展 (微信公众号推送落地)
作为 NotebookLM/Qwen 驱动的 AI 新闻内容流水线下游，我们在 `universal_content_orchestrator` 中引入了基于 Playwright CDP 的物理级微信推送闭环。
- **突破点一**：跨越了微信官方苛刻的 API 限制与限权，开发了 `WeChatPublisher` 类，并在本地 `9224` 端口开启调试 Chrome，利用底层控制直接塞入 Markdown 转换数据。
- **突破点二**：完美攻坚了 UEditor 富文本防御。我们由脚本将生成的 2.35:1 宽幅海报转化成 Base64 流，并依靠向内存派发真实 `ClipboardEvent('paste')`，骗过系统完成自动配图，通过 `run_single_wechat_test.py` 成功完成全自动化直接落锁草稿箱验证。
- **双轨探索与协同**：目前同时在主导推进基于接口派发的方案 `md2wechat-skill`，并在对比这两套架构谁能更方便地部署上云端托管、融合进入我们的 Agent 工具链体系中。
