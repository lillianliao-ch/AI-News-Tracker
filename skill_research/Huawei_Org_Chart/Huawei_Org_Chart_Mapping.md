Continuing conversation 84a89dbf...
Answer:
这份报告基于对数百份华为（Huawei）核心AI人才履历的深度脱敏分析，为您揭秘其“盘古大模型、诺亚方舟实验室与
2012实验室”交织构成的复杂AI帝国版图。

---

# 🕵️‍♂️ 华为核心AI架构逆向工程报告报告

作为顶级 Intelligence Researcher，我通过分析候选人的工作代码（如 
**ADS**、**ModelArts**、**DME**）、汇报线（**TMT PO**、**SEG 
Leader**）及物理驻地（**松山湖**、**慕尼黑**、**俄研所**），拼凑出了这张“深不可测”的组织网。

---

## 1. 核心AI及业务部门组织逻辑
华为的AI布局并非简单的线性，而是**“研究（诺亚）+ 底座（2012）+ 平台（云）+ 
垂直入口（终端/车）”**的四位一体结构：

*   **诺亚方舟实验室 (Noah's Ark 
Lab)**：前沿AI的“尖刀”，负责从0到1的算法突破，侧重于因果推理、具身智能和强化学习。
*   **2012实验室 (2012 
Labs)**：技术“黑土地”，下设中央研究院、中央软件院、中央媒体技术院等，负责将AI算法工程化，并与自研芯片（
昇腾/海思）进行深度软硬协同设计。
*   **华为云 (Huawei 
Cloud)**：大模型商用化“引擎”，盘古大模型（Pangu）的孵化地，侧重于MaaS（模型即服务）和工业落地。
*   **各业务BG (Consumer/Auto/ICT)**：AI落地的“战场”，如小艺助手（Xiaoyi）、智驾系统（ADS）。

---

## 2. 【核心】华为AI帝国层级树状矩阵 (Org Chart)

以下架构根据履历草蛇灰线拼凑，部分层级及汇报关系包含猎头直觉推演。

*   **华为AI战略决策层 (?)**
    *   **首席AI科学家**：Candidate 43694 (Chief AI Scientist @ CBG, 原云首席) [1]
    *   **AI理论实验室负责人**：Candidate 40159 (Director, AI Theory Lab) [2]
    *   **AI for Science 首席科学家**：Candidate 1120 (Chief Scientist in AI4Sci) [3, 4]

*   **诺亚方舟实验室 (Noah's Ark Lab)** —— *前沿技术探索*
    *   **决策与推理实验室**：Candidate 221 (高级研究员), Candidate 212 (具身智能负责人) [5, 6]
    *   **AI应用研究中心 (AIRC)**：Candidate 617 (算法专家), Candidate 5460 (多模态数据治理) [7, 8]
    *   **强化学习与因果推断组**：Candidate 456 (NeurIPS一作), Candidate 527 (刑天框架维护者) [9, 10]
    *   **计算视觉实验室 (俄研所/中研所协作)**：Candidate 509 (俄研CV负责人), Candidate 33 (视觉专家) 
[11, 12]

*   **2012实验室 (2012 Labs)** —— *技术底座与工程中心*
    *   **中央软件院 (Central Software Institute)**
        *   **AI框架与数据技术部 (香港/深圳)**：Candidate 137 (Data+AI 架构师, Data Agent 原型构建者) 
[13]
        *   **MindSpore 创新团队**：Candidate 34 (AI框架工程师, Moe算子Owner) [14]
        *   **分布式并行计算实验室**：Candidate 35 (通算算子编译架构师) [15]
    *   **中央媒体技术院 (CMTI)**
        *   **计算摄影/图像AIGC团队**：Candidate 28 (团队Leader, Diffusion业务研发), Candidate 218 
(AIGC特战队核心) [16, 17]
        *   **视频生成模型组**：Candidate 547 (快手可灵前身核心/2012视觉专家) [18]
    *   **中央硬件工程院 / 高性能计算实验室**
        *   **昇腾/芯片应用架构部**：Candidate 74070 (AI-Infra专家), Candidate 107 
(UB协议/灵衢规范贡献者) [19, 20]
        *   **先进热流技术组**：Candidate 1008 (主任工程师, 负责AI背景下散热攻坚) [21]

*   **华为云 (Huawei Cloud)** —— *盘古模型与算力云*
    *   **Foundation Model Lab (盘古大模型团队)**
        *   **盘古核心研发组**：Candidate 40499 (Lead Engineer in Team Pangu), Candidate 498 
(Pangu-Coder2 负责人) [22, 23]
        *   **EI 算法创新 Lab**：Candidate 583 (AI数策经理), Candidate 1142 (NLP算法专家/带团队) [24, 
25]
    *   **计算产品线 / 昇腾云**
        *   **AI推理Infra组**：Candidate 74071 (首席专家), Candidate 112 (推理优化A) [26, 27]
        *   **ModelArts 平台部**：Candidate 37 (AI产品经理, 负责Agent开发工具链) [28]

*   **业务落地终端 (Xiaoyi / ADS / Industry)**
    *   **终端BG - 小艺助手 (Xiaoyi)**：Candidate 1143 (多模态大模型基座负责人), Candidate 597 
(多模态慢思考数据产线核心) [29, 30]
    *   **车BU - ADS 智驾部门**：Candidate 57 (AI数据与仿真开发部), Candidate 110 (智驾模型SDK负责人) 
[31, 32]
    *   **行业解决方案部 (EBG)**：Candidate 28552 (大数据产品经理/Agentic RAG探索) [33]

---

## 3. 技术攻坚方向窥探：华为在押注什么？

根据履历中“最近半年”的项目密集度，华为正在以下**四个高地**疯狂堆料：

1.  **“慢思考”推理模型 (Reasoning / Scaling Law)**：
    *   **动作**：小艺团队正在构建“多模态慢思考模型后训练数据产线” [30]。
    *   **目标**：通过 Test-time scaling 提升 Agent 的逻辑推理精度，对标 OpenAI 的 o1 系列。
2.  **AI Infra 的“超节点”互联 (Scale-up Network)**：
    *   **动作**：2012实验室正在研发“灵衢 (UB)”协议及高性能 RoCE 网络，支持 384 超节点集群（CloudMatrix
384） [20, 34]。
    *   **目标**：解决万卡集群的通信瓶颈，尤其针对 DeepSeek 类的 MoE 架构进行内存统一编址优化 [35, 
36]。
3.  **Agentic Workflow 与 Data Agent**：
    *   **动作**：多个部门（云、中央软件院、小艺）同步推进 Data Agent 开发，利用 LangGraph 和 MCP 
协议实现自主 SQL 挖掘与决策闭环 [13, 30, 37, 38]。
    *   **目标**：将大模型从“对话框”推向“全自动执行体”。
4.  **AI for Science (AI4Sci)**：
    *   **动作**：成立专门的 AI4Sci Lab，研发 MindChemistry（化学材料套件）和 DNA 基础模型 [39, 40]。
    *   **目标**：利用 AI 模拟第一性原理计算，加速新材料与药物研发。

---

## 4. 战略推演与补齐 (?)

*   **(?) 
跨BG大模型委员会**：鉴于云、终端、诺亚都在做大模型且存在技术重合，华为内部极大概率存在一个横向的“大模型
技术专家组”或“委员会”，负责跨部门的算力调度与模型版本归一。
*   **(?) 俄研所 (Russian Research) 的隐形权重**：履历中多次出现“与俄研所合作” [41, 
42]，推测核心的数学底层算子优化和高性能库（类似 MKL/NCCL 的自研替代）由俄籍数学家团队把关。
*   **(?) 2012 实验室的“天线宝宝”/ 6G 协同**：Candidate 76 提到的“通信感知融合” 
[35]，暗示华为正试图将大模型的能力下沉到基站侧，实现“网络自动驾驶”。

---

**报告总结**：华为的AI布局已跨越了单纯的“模型竞赛”，其核心优势正在从**算法层**（盘古）向下沉淀到**系统
架构层**（RoCE/UB协议/散热）和向上延伸到**Agent生态层**（ModelArts 
Studio/小艺）。对于猎头而言，**2012实验室中央软件院**和**云EI创新Lab**的跨界人才（懂算法+懂硬件底座）是
当前最具价值的“皇冠明珠”。

**Intelligence Researcher**
*数据截止：2026-03-28* [Context]

Resumed conversation: 84a89dbf-94e6-4243-abc2-b7057374f819
