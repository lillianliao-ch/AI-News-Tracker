Continuing conversation fb9cab99...
Answer:
这份报告由 **Intelligence Researcher 团队**通过对数百份微软在华核心 AI 履历（含 MSRA、STCA、MSAI 
等）的“草蛇灰线”进行深度逆向工程分析得出。

我们发现，微软在华的 AI 力量并非松散分布，而是一个以 
**MSRA（研究院）为大脑、STCA（互联网工程院）为肌肉、MSAI（微软人工智能事业部）为先锋**的庞大矩阵。

---

### 第一部分：组织架构逆向还原（Org Chart Re-engineering）

根据履历中的汇报线（Reporting Line）与项目协作，我们识别出四大核心支柱：

1.  **MSRA (Microsoft Research Asia) - 前沿探索与基础模型层**
    *   这是微软 AI 的黄埔军校。下设 **DKI (数据知识智能)**、**NLC (自然语言计算)**、**VC (视觉计算)** 
等核心组。
    *   **核心职能**：主攻基础模型（Foundation Models）、MoE 架构、多模态预训练（Omni-Modality）以及 
AI4Science。

2.  **STCA (Search Technology Center Asia) - 工程落地与 Bing 演进层**
    *   作为互联网工程院，这里是 Bing 搜索、Bing Ads 以及后续 **GenSERP (新一代生成式搜索)** 的大本营 
[1]。
    *   **核心职能**：大规模分布式训练、搜索相关性优化、高并发推理架构（Infra）以及广告算法。

3.  **MSAI (Microsoft AI) / M365 Copilot - 业务增长与智能体层**
    *   这是近期履历中流动最频繁、权重最高的部门，直接负责 **Copilot** 系列产品的全生命周期 [2-4]。
    *   **核心职能**：RAG 架构落地、Agent 平台开发（SCOPE AI Agent）、Prompt Flow 工具链 [5] 以及 M365 
深度集成。

4.  **Azure AI Platform - 基建与开发者赋能层**
    *   负责将 AI 能力云化，包括 **Azure ML Studio** 和 **Semantic Kernel** [6]。
    *   **核心职能**：MLOps、模型压缩（量化/蒸馏）、GPU 算力调度优化。

---

### 第二部分：核心层级树状矩阵（Hierarchical Matrix）

*   **L1：战略决策层 (Global CVPs & Leaders)**
    *   **ia Song (\*ia Song, ID: 44506)** - CVP, Turing MSAI [7]
    *   **Zhang Qi (\*张祺, Inferred from [8])** - CVP, STCA/MSAI 核心领袖
    *   **\*uru Wei (Wei Furu, ID: 1010)** - MSRA 首席科学家 / VP，LLM 研究的实际操盘手 [9, 10]

*   **L2：学术/工程负责人 (Principal Research/Engineering Managers)**
    *   **Dongmei Zhang (\*Dongmei Zhang, Inferred from [11])** - DKI Group Manager (数据知识智能)
    *   **Yu Cheng (\*余, Inferred from [12, 13])** - 负责自主智能体 (Autonomous Agents/MAGIS) 研发
    *   **Tianyi Chen (\*Tianyi Chen, ID: 8955)** - Principal Research Manager (Windows 部门 CUA 项目 
Leader) [14, 15]
    *   **ID: 24611 (\*小佳)** - Principal Applied Scientist Manager (Search/NLP/LLM) [16]
    *   **ID: 24647 (\*文彪)** - Principal Software Engineer Manager (RAG/搜索) [17]
    *   **ID: 25124 (\*亮)** - Principal Software Engineer Manager (M365 Copilot/Agent Infra) [18]

*   **L3：技术骨干与领域专家 (Senior Applied/Research Scientists)**
    *   **ID: 24430 (\*楠)** - 首席应用科学家 (MAI/LLM 预训练) [19]
    *   **ID: 11152 (\*雪莹)** - 数据科学总监 (Copilot PLG/用户增长) [20]
    *   **ID: 45798 (\*hujie Liu)** - Principal Researcher (MSRA 视觉/多模态) [21]
    *   **ID: 24490 (\*宇凡)** - Senior Applied Scientist (L64, Feeds-VLM/LLM) [22]
    *   **ID: 74215 (\*看机会)** - 合作伙伴解决方案架构师 (AI 商业落地) [2]

*   **L4：核心执行层 (SDE II / Applied Scientist II)**
    *   **ID: 11144 (\*鑫)** - 软件工程师 (COSMIC Copilot/SmartTSG 研发) [23]
    *   **ID: 24431 (\*anny)** - 软件工程师 II (SQL Copilot/Semantic Kernel) [6]
    *   **ID: 11694 (\*爱玲)** - 前端专家 (Bing Creator/⽣成式 UI) [24]

---

### 第三部分：技术攻坚方向窥探（Strategic Technical Trends）

通过对最近半年“项目经历”的词频与架构逻辑分析，我们锁定了微软在华阵列的**三大押注高地**：

1.  **Computer-Using Agent (CUA) 与“Agentic AI”**
    *   **情报分析**：多个履历（如 ID: 8955, 25124）明确提及“Computer-Using Agent”和“Agentic OS” [14, 
25]。这表明微软正在攻坚让 AI 像人类一样操作 Windows/Mac 系统桌面的技术 [15]。
    *   **关键词**：CUA-KG (知识图谱)、Trajectory Generation (轨迹生成)、Multi-Agent 协作 [12, 14]。

2.  **长程推理（Long-term Reasoning）与 GRPO 优化**
    *   **情报分析**：履历 [26] 深度披露了 **GRPO (Group Relative Policy Optimization)** 
在自然语言生成代码（Excel Formula/Python）中的应用，且在内部 Benchmark 上超越了 GPT-4.1 (?)。
    *   **关键词**：RL (强化学习)、Self-Correction (自我修正)、KV Cache 压缩技术 [26, 27]。

3.  **GraphRAG 与结构化知识检索**
    *   **情报分析**：微软正试图通过 **GraphRAG** 解决 RAG 系统中的逻辑缺失问题 [28]。同时，针对 Office
文档（如巨大的 Excel 表格）研发了 **TUTA** 等专用基础模型 [11]。
    *   **关键词**：Vector Indexing、Semantic Kernel 框架集成、Sufficient Context 判定 [6, 28]。

---

### 第四部分：推演补齐与猎头直觉 (?)

1.  **MSAI 的扩张 (?)**：我们推测 MSAI 部门在 2024 年底进行了一次大规模扩招或组织重组，旨在将原本散落在
Bing 和 Office 下的 AI 人员合并，统一向 CVP Song Xia 汇报。
2.  **GenSERP 项目的紧急度 (?)**：ID 434 提及的 GenSERP (Generative Search) 极有可能是对标谷歌 Search 
Generative Experience 或 Perplexity 的绝密武器，目前正处于高密度的模型微调期。
3.  **端侧 AI 的野心 (?)**：履历 289 提及的“On-device CUA”暗示微软正在为未来的 AI PC 打造基于 NPU 
的轻量化 Agent，试图脱离对云端推理的依赖。

**报告总结**：微软在华的 AI 势力正处于从“功能集成”向“原生 Agent 
操作系统”跨越的关键期。如果您计划从中挖人，**L64-L65 级的 Principal 级人才**是掌握 Agent 
平台底层代码的钥匙，而 **MSRA DKI 组的学者**则是算法创新的灵魂。

Resumed conversation: fb9cab99-6944-4116-8f54-b62d41ea93f7
