Continuing conversation 13b37372...
Answer:
这是一份由 **Intelligence Researcher** 顶级猎头团队通过深度挖掘数百份 Google（含 DeepMind/Gemini 
核心团队）候选人履历，利用“草蛇灰线”逆向拼凑出的 **Google AI 技术研发架构核心组织架构报告**。

### **Google (DeepMind/Gemini) 核心 AI 研发架构逆向工程报告**

通过对最近半年候选人项目经历的穿透式分析，我们发现 Google 在 2023 年完成 Google Brain 与 DeepMind 
的合并后，已形成了一个以 **Gemini** 为轴心，极度扁平化且高度跨组协作的网状架构 [1-3]。

---

#### **一、 核心组织架构（Org Chart）逆向还原**

根据履历中提及的 Reporting Line 和项目协作方 [1, 4-6]，我们拼凑出以下五大核心支柱：

1.  **Gemini 核心模型阵列 (Core Gemini Group)**：这是目前的“曼哈顿计划”中心。其下细分为：
    *   **基础预训练组 (Pretraining)**：负责超大规模模型的数据清洗、分词及算力调度优化 [7, 8]。
    *   **后训练与推理组 (Post-training & Reasoning)**：目前最神秘且权重最高的部门，专注于 
SFT、RLHF（强化学习）以及提升模型的推理（Reasoning）深度 [5, 9, 10]。
    *   **多模态感知组 (Multimodal)**：负责视觉（Vision）、音频（Audio）、3D 及其与语言模型的原生融合 
[11-13]。
2.  **前沿 AI 探索部 (Frontier AI Research / Legacy DeepMind)**：
    *   **机器人实验室 (Robotics)**：专注于具身智能，将 LLM 转化为物理世界的行动力 [14-16]。
    *   **AI for Science**：利用模型解决蛋白质折叠、量子电路设计及物理仿真等科学难题 [17-19]。
    *   **机械可解释性组 (Mechanistic Interpretability)**：负责拆解黑盒，确保模型的可控与安全 [20, 21]。
3.  **AI 基础设施与框架部 (ML Systems & Infra)**：
    *   **JAX/XLA 软件栈**：负责构建支撑万卡集群的高性能编程框架 [22, 23]。
    *   **Pathways & Runtime**：负责大规模分布式任务的调度与运行时优化 [4]。
    *   **TPU 硬件协同组 (TPU Architecture)**：负责芯片与算法的 codesign 协同设计 [24]。
4.  **智能体与应用平台 (Agents & Cloud AI)**：
    *   **Computer-Using Agent (CUA)**：开发能像人类一样操作 PC/操作系统的自动化智能体 [6, 25, 26]。
    *   **Cloud AI Research**：负责将 Gemini 转化为企业级 API 和 Vertex AI 上的落地产品 [27-29]。
5.  **业务落地与商业化阵列 (Monetization & Vertical Apps)**：
    *   **Search Quality & Ads**：将 AI 深度集成至搜索、广告出价和 YouTube 推荐系统中 [4, 30-32]。

---

#### **二、 层级树状图矩阵 (Org Tree)**

*   **Google DeepMind 总部 (London/Mountain View)**
    *   **Research Director / Principal Scientist** (核心决策层)
        *   **Candidate 7020** (Principal Scientist & Research Director) [33]
        *   **Candidate 93481** (Principal Scientist, Director, 专注 Deep Retrieval & Efficient LLMs) [34]
    *   **Gemini Core Model Pillar** (Gemini 核心支柱)
        *   **Gemini Pretraining Lead (?)**
            *   **Candidate 13027** (Research Engineer, Gemini Pretraining 核心成员) [7]
        *   **Gemini Post-training & Reasoning Team** (后训练与推理)
            *   **Candidate 5580** (Research Scientist, Gemini Deep Think/Reasoning 核心贡献者) [5]
            *   **Candidate 60502** (Member of Technical Staff, 曾贡献 Gemini v1.1.5 Post-training) [9]
            *   **Candidate 669** (算法研究员, 专注于长文本扩增预训练) [10]
        *   **Multimodal Team** (多模态)
            *   **Candidate 14647** (Gemini Audio Research 成员) [11]
            *   **Candidate 5226** (Senior Research Engineer, 专注 CV/3D/Gemini) [12]
            *   **Candidate 10307** (Research Scientist, 专注 Multimodal LLMs) [35]
    *   **Infrastructure & Systems Pillar** (基建与系统支柱)
        *   **LLM Systems Tech Lead (TL)**
            *   **Candidate 1111** (ex-Google TL, 负责 Gemini SFT/RL/Inference on GPUs) [1, 4, 36]
        *   **JAX / XLA Frameworks Team**
            *   **Candidate 8410** (ML Researcher, JAX 共同作者) [23]
            *   **Candidate 13275** (SWE, 专注于 JAX 核心开发) [22]
        *   **TPU / Hardware Codesign**
            *   **Candidate 99169** (TPU Architect) [24]
    *   **Frontier Research Pillar** (前沿探索支柱)
        *   **Robotics Team**
            *   **Candidate 13296** (Research Scientist, Robotics @ Brain) [14]
            *   **Candidate 411** (Researcher, Google DeepMind Robotics) [15]
        *   **Interpretability Team**
            *   **Candidate 8490** (Mechanistic Interpretability Researcher) [20]
    *   **Product & Vertical Integration Pillar** (产品与业务集成)
        *   **Search & Ads Quality Team**
            *   **Candidate 603** (SWE, 搜索基础架构与数据索引) [30]
            *   **Candidate 660** (SWE, 广告平台 OpenBidding 后端负责人) [37]
        *   **Cloud AI / Vertex AI**
            *   **Candidate 12949** (Research Scientist, Google Cloud AI Research) [27]
            *   **Candidate 40095** (Research Scientist, Cloud AI Research) [28]
        *   **Android / Pixel Integration**
            *   **Candidate 12113** (Android 系统级 AI 模型开发 TL) [38]

---

#### **三、 技术攻坚方向窥探：Google 的“当下押注”**

通过对履历中近半年“项目经历”的聚类分析，我们锁定了 Google 正在秘密攻克的四大高地：

1.  **“Deep Think” 推理范式转型**：
    从 Candidate 5580 和 60502 的经历看，团队正在复现甚至超越类 OpenAI o1 的推理路径 [5, 
9]。他们不再单纯追求参数量，而是通过 **Agentic RL (智能体强化学习)** 提升模型在 
ICPC（竞赛编程）和数学竞赛中的长链条思考能力 [5, 9, 10]。
2.  **Computer-Use Agent (CUA) 级自动化**：
    这是目前内部极高优先级的项目 [6, 25]。Google 试图让 Gemini 
直接接管操作系统，在像素级别理解屏幕内容，并完成跨 App 的复杂指令，这涉及到底层 NPU/GPU 的极度能效比优化 [6, 
25, 26, 39]。
3.  **原生多模态“感知-行动”闭环**：
    不仅仅是看图说话。Candidate 5226 和 14647 的项目显示，Gemini 正在深度融合 **NeRF (神经辐射场)** 和 **3D 
视觉**，旨在让模型具备物理世界的空间感 [12, 13, 40]。同时，Gemini Audio 
已进入独立研究阶段，目标是全感官实时交互 [11]。
4.  **万卡集群的软件栈极端压榨**：
    面对 GPU 算力的瓶颈，JAX 团队（Candidate 8410 等）正在进行 **GPU 
软件栈的全量重构**，实现单机到多机、模型并行到流水线并行的无缝化 [1, 4, 23]。这表明 Google 
正在通过框架层（Software Stack）的效率提升来对冲算力成本 [4]。

---

#### **四、 合理推演与补齐 (?)**

1.  **Gemini 4.0 (?) / 次世代模型研发部**：
    虽然履历主要提及 Gemini 2.5/3 [5]，但根据 Principal Scientist 
级别的人才流向判断，必然存在一个代号为“下一代基础模型”的独立实体，负责突破 Transformer 架构的限制 (?)。
2.  **全球数据“主权”运营部 (?)**：
    由于 Candidate 633 提到了高度自动化的评测和数据清洗链路 [41, 42]，我们推断 Google 
内部有一个极其庞大的数据策略组（Data Ops），专门负责全球合规数据的合板与合成 (?)。
3.  **垂直领域“冷启动”小组 (?)**：
    频繁出现的“冷启动数据构建” [43, 44] 
揭示了内部存在多个敏捷反应小组，专门负责在模型能力出现短板时，通过极少量高质量专家数据快速补齐垂直领域（如法务
、医疗、金融）的认知 (?)。

**猎头总评**：Google 已经彻底从“科学家乐园”转型为“战时 AI 机器”。内部架构正以前所未有的速度向 
**推理、Agent、多模态原生化** 聚拢。对于贵司而言，Candidate **5580 (Reasoning)** 和 **1111 (Systems Infra)** 
是具有战略打击力的顶尖挖角目标。

Resumed conversation: 13b37372-68b4-48ba-af26-0cb0410be6f7
