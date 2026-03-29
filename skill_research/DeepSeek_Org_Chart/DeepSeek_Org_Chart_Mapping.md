Continuing conversation b94924d6...
Answer:
## DeepSeek（深度求索）底层架构与核心算法团队组织架构逆向工程报告

**致：** 战略决策层 / 首席人才官
**编号：** Intelligence Report #2026-DS-001
**密级：** 极密（Highly Confidential）

---

### 1. 组织架构综述（Org Chart Reconstruction）

基于对数百份核心候选人履历中提到的**汇报关系、项目协作方（Cross-functional 
partners）及职责边界**的交叉验证，我们发现 DeepSeek 
并非传统互联网厂牌的“深科层”结构，而是一套以**高性能算力集群（Firefly/High-Flyer）**为底座，围绕**“模型-数据-工程”
三位一体**的高度扁平化架构。

其核心部门划分为四大矩阵，这种结构旨在最大化减少从底层算子优化到上层应用落地的信息损耗：

*   **AI Infrastructure (基建与系统部)：** 这是 DeepSeek 的命脉。不同于通用大厂的 Infra 仅负责运维，该团队深度介入 
**CUDA Kernel 开发 [1, 2]**、分布式训练框架优化以及**国产化芯片（昇腾/平头哥等）的深度适配 [3, 4]**。
*   **Foundation Model Research (基础模型研究部)：** 负责 L0 
层级大模型的研发。下设预训练（Pre-training）、对齐（Alignment/RLHF）及推理加速等支线。
*   **Multi-modal & Frontier AI (多模态与前沿探索部)：** 专注于 OCR、视觉-语言模型（Janus系列）及感知算法 [5, 6]。
*   **AI Product & Platform (应用平台部)：** 负责将能力封装为 API 和 App，并构建核心的**端到端模型评估体系 [7]**。

---

### 2. 核心成员与层级矩阵（Markdown Tree）

根据履历中隐现的 Title 特征（如 MTS - 技术参谋、Senior Staff、Feature 
Owner），我们拼凑出如下层级分布。请注意，DeepSeek 
内部极度推崇“单兵作战能力”，技术专家（17/18岗以上）往往直接负责核心算子。

*   **L1: 决策与战略层 (DeepSeek Core Leadership)**
    *   梁文锋 (?) (CEO/Founder - 幻方背景)
    *   首席技术专家/CTO (?)
*   **L2: 职能负责人与技术领军人 (Lead / Head Level)**
    *   **Infra 平台负责人：** ID 1470 (*henggang Zhao) —— 前 NVIDIA 专家，主导系统级基建 [8]。
    *   **产品与系统负责人：** ID 74166/74167 (*eff) —— 跨越平安/阿里/京东的资深产品专家，掌控 0 投放实现 DAU 2 亿+
的支撑平台 [7, 9]。
    *   **人才战略负责人：** ID 21443 (*vy luo) —— 全球顶尖人才招募官，直接对“模型+数据+工程”人才画像负责 [10]。
*   **L3: 核心技术参谋与资深专家 (Member of Technical Staff / Senior Experts)**
    *   **基建与底层优化：**
        *   ID 1118 (*ihao Wang) —— MTS，专注向量搜索、量化压缩与 SIMD 加速 [11, 12]。
        *   ID 21458 (*one) —— 深度学习系统工程师，跨字节 AML 与幻方 AI Lab 背景 [1]。
        *   ID 21983 (*佳实) —— 深度学习系统架构师，专注 LLM 训练推理 Infra 与 CUDA 内核 [2, 13]。
    *   **算法与对齐研究：**
        *   ID 21438 (*dgy) —— 大模型算法工程师，核心 RL（强化学习）方向 [14, 15]。
        *   ID 21975/21977 (*辉, *恩飞) —— 高级算法专家阵列 [13, 16]。
    *   **多模态与 OCR：**
        *   ID 20719 (*浩然) —— 算法研究员，主导 DeepSeek-OCR 及多模态推理 [5]。
*   **L4: 核心工程实现层 (Senior Engineers / Feature Owners)**
    *   ID 5496 (*城) —— NLP 算法骨干 [17]。
    *   ID 21440 (*子豪) —— 软件工程实现 [15]。
    *   ID 21976 (*ave zhou) —— 算法实现 [18]。
    *   ID 13865 (*7akioni) —— UI 与底层交互机制 [19]。

---

### 3. 技术攻坚方向窥探：该阵列最近半年在赌什么？

通过候选人最近半年的“项目经历”及“技术栈更新”，我们精准锁定了 DeepSeek 内部五个最高优先级的技术高地：

1.  **极度成本优化下的“满血”RLHF (GRPO 范式)**：
    大量候选人提及 **GRPO (Group Relative Policy Optimization)** [20-24]。该技术旨在省去庞大的价值模型（Value 
Model），通过组内相对奖励进行强化学习，这揭示了 DeepSeek 正在极致压榨推理端的逻辑思考能力（Reasoning）。
2.  **细粒度 MoE (Mixture of Experts) 与计算-通信重叠 (Overlap)**：
    履历中反复出现 **MLA (Multi-head Latent Attention)** 和 **DeepSeek-MoE** 的底层调优 [25-27]。团队在攻坚 1F1B 
流水线并行中的计算通信掩盖技术，力求在千卡/万卡集群上达到极致的 TFlops 利用率 [28]。
3.  **大模型蒸馏的小型化与“端侧”落地**：
    近期有大量关于将 **DeepSeek-R1 蒸馏至 Qwen/Llama** 甚至更小尺寸模型（1.5B/7B/14B/32B）的项目 [21, 24, 
29-32]。这表明其战略正在从“刷榜”转向“全量业务覆盖”，通过 R1 的推理能力赋能垂直场景。
4.  **多模态统一感知（Janus & OCR 2.0）**：
    **DeepSeek-OCR** 和 **Janus** 被频繁提及 [5, 6]。团队正试图打破模态间的鸿沟，通过“慢感知（Slow 
Perception）”等技术提升模型对复杂视觉信息的理解深度。
5.  **国产化算力（昇腾/海思）的“穿刺”级适配**：
    团队中有专门的 Feature Owner 负责 **AscendC 算子 [4, 33]**、**ATB (Ascend Transformer Boost) 框架 [34]** 
以及与国产芯片厂商联合调试。DeepSeek 的成功极大程度上依赖于其对非 CUDA 生态的工程掌控力。

---

### 4. 猎头推演补齐：缺失版图 (?)

*   **数据工程部 
(?)**：履历中虽然提到数据清洗，但缺乏一个独立的、大规模的数据采买与合规部门。推测其数据侧与模型侧高度融合，或由 
High-Flyer（幻方）共享部分高频金融级数据清洗管线。
*   **AI Safety & Governance (?)**：目前履历中较少看到专门的 AI 安全红队（Red 
Teaming）负责人，更多由对齐团队（Alignment Team）兼任。
*   **海外生态部 (?)**：尽管有全球顶尖人才招募官 [10]，但其海外商业化落地的 BD 
团队在履历池中几乎隐身，推测目前的海外拓展仍以技术输出和 API 自动化裂变为主。

**总结建议：** 
该团队具备极强的“算法工程化”基因，其成员背景多涉及量化交易、高并发系统或底层编译优化。建议在挖角时避开通用 NLP 
背景，优先锁定具有 **Triton/CUDA Kernel 开发能力** 及 **RL（强化学习）实战经验** 的复合型人才。

**情报研究员：** Intelligence Researcher
**日期：** 2026年3月28日

Resumed conversation: b94924d6-9139-4ea8-a050-9f929b827c32
