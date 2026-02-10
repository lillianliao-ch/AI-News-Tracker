# Headhunter Agent — 开发路线图

> **最后更新**：2026-02-08
> **愿景**：构建一个 AI Headhunter Agent，自主完成sourcing→触达→匹配→跟进全流程，你只处理高价值人际交互。
> **路径**：以终为始，每一个工具都是Agent的一个能力模块。工具+Agent-Lite并行推进，逐步进化为Full Agent。

---

## 〇、终局：Headhunter Agent 完整形态

```
┌─────────────────────────────────────────────────────────┐
│                  Headhunter Agent                        │
│                                                          │
│  🧠 大脑（调度+规划层）                                    │
│  ├─ 每日分析JD管道、候选人状态、市场信号                      │
│  ├─ 自主决定：sourcing/触达/跟进/匹配 的优先级               │
│  └─ 学习闭环：哪些行动产生了结果 → 优化策略                   │
│                                                          │
│  👁 感知层              🦾 执行层            📊 记忆层      │
│  ├─ 新JD录入            ├─ 多渠道sourcing    ├─ 候选人DB   │
│  ├─ 公司动态监控         ├─ 个性化触达        ├─ JD DB      │
│  ├─ 实验室/GitHub监控    ├─ JD智能匹配        ├─ 交互历史   │
│  ├─ 顶会论文监控         ├─ 候选人跟进        └─ 效果数据   │
│  └─ 候选人状态变化       ├─ Talent Mapping                 │
│                         └─ 反馈收集                        │
└─────────────────────────────────────────────────────────┘

  你的角色：审批关键决策 + 面试沟通 + offer谈判 + 播客/沙龙人脉经营
```

**每个开发任务在下面都标注了它对应Agent的哪个模块 → 🧠/👁/🦾/📊**

---

## 一、战略框架

### Sourcing渠道分层

| 层级 | 渠道 | 竞争 | 策略 |
|------|------|------|------|
| **红海** | 脉脉/LinkedIn按公司找 | 万人竞争 | 维持+自动化，不加码 |
| **蓝海** | 播客/沙龙/交大校友网络 | 只有你 | **重点投入** |
| **深水** | 学术溯源/GitHub/顶会 | 极少人做 | 系统化建设 |
| **暗流量** | 知乎/即刻/Twitter/竞赛 | 少数人做 | 日常留意+播客转化 |

### 演进路线

```
Phase 1 (W1-5)     Phase 2 (W6-9)      Phase 3 (W10-12+)
工具+Agent-Lite  →  工具接入Agent    →   Full Agent
                    半自动模式           自主模式
```

---

## 二、开发进度追踪

### Phase 1: 基建 + Agent-Lite（W1-5）

- [x] 🧠 **Agent-Lite 每日工作台** `daily_planner.py` ✅
  - Agent大脑的MVP：读DB状态 → LLM分析 → 输出"今日行动建议"
  - 你审批执行，每天的判断都在训练未来Agent的决策规则
  - 技术：Python + SQLite(现有DB) + Qwen API

- [x] 🦾 **脉脉个性化消息生成** `maimai-assistant` ✅
  - Agent执行层能力：个性化触达
  - 抓取profile → AI生成加好友理由 → 自动填入 + 状态记录
  - 技术：Chrome Extension + LLM API

- [x] 🦾📊 **候选人反馈闭环** `job-share-service` ✅
  - Agent执行层+记忆层：JD推送 + 收集候选人反馈 → 回写数据库
  - 候选人标记兴趣/不合适 → 管理后台汇总（门户转化漏斗看板）
  - VIP门户系统：随机码+IP限流+暗色主题+名片卡+自动创建
  - 技术：Railway部署 + FastAPI + Pillow名片卡 + Plotly漏斗图

- [ ] 👁 **交大实验室溯源扩展** `lamda_scraper` 扩展
  - Agent感知层能力：学术人才发现
  - 适配交大APEX/SJTU-NLP → 交叉检索 → 录入候选人系统
  - 优先交大（校友优势），然后清华THUNLP/北大

- [ ] 👁 **GitHub贡献者扫描** 新工具
  - Agent感知层能力：开源人才发现
  - GitHub API → 目标仓库(vLLM/LangChain等) → 筛选中国区 → 录入系统

### Phase 2: 工具接入Agent（W6-9）

- [ ] 📊🦾 **候选人智能跟进** `personal-ai-headhunter`
  - Agent记忆层+执行层：触达状态管理 + 自动生成待跟进名单
  - 结合AI News Tracker内容做跟进由头

- [ ] 🧠🦾 **JD驱动智能sourcing** `matching_engine` 扩展
  - Agent大脑+执行层：输入JD → 自动推荐sourcing目标(公司/团队/关键词)
  - 基于JD解构三要素反推

- [ ] 🧠 **Agent升级为半自动模式**
  - Agent大脑接上所有已完成的工具(Tools)
  - 自动执行简单任务（匹配/消息草稿），你审批后一键执行
  - 评估是否引入LangGraph

### Phase 3: Full Agent（W10-12+）

- [ ] 👁 **顶会作者追踪** — Agent感知层：Semantic Scholar API集成
- [ ] 🧠 **自主sourcing + 自主跟进** — Agent大脑完全自主决策
- [ ] 🧠 **反馈学习闭环** — Agent学习：什么行动产生结果 → 优化策略
- [ ] 最终状态：你只处理面试沟通、offer谈判、播客/沙龙人脉经营

---

## 三、非编程行动项（同步推进）

- [ ] **交大校友AI播客**：每两周一期，校友身份建联 → 蓝海渠道 + 播客嘉宾 = 深度候选人关系
- [ ] **闭门校友饭局**：每月1次，4-8人 → 播客嘉宾转化为线下信任
- [ ] **甲方关系管理**：Talent Mapping主动出击 → 争取exclusive JD

> 详见 [播客/沙龙执行手册](/.gemini/antigravity/brain/b1d3f26f-b4f7-4e34-ad36-71dddf73b132/ai_headhunter_execution_playbook.md)

---

## 四、关键原则

1. **以终为始** — 每个工具都是Agent的能力模块，不是孤立的脚本
2. **工具先跑通、再接入Agent** — 没跑通的工具接入Agent只会制造混乱
3. **Agent-Lite是你的"眼睛"** — 帮你看全局，你的判断在训练Agent的决策规则
4. **播客是万能建联工具** — 所有渠道发现的目标人选，通过邀请做嘉宾建立关系
5. **深水渠道是长期护城河** — 学术溯源+GitHub数据越积累越值钱
6. **数据回流** — 所有渠道的新接触人都录入系统，喂养Agent记忆层
7. **70分就发布** — 先做出来，迭代比完美重要

---

## 五、相关文档

- [综合行动方案](/.gemini/antigravity/brain/b1d3f26f-b4f7-4e34-ad36-71dddf73b132/ai_headhunter_comprehensive_plan.md)
- [播客/沙龙执行手册](/.gemini/antigravity/brain/b1d3f26f-b4f7-4e34-ad36-71dddf73b132/ai_headhunter_execution_playbook.md)
- [市场可行性分析](/.gemini/antigravity/brain/b1d3f26f-b4f7-4e34-ad36-71dddf73b132/ai_headhunter_strategy_feasibility.md)
- [Agent人才匹配方法论](/Users/lillianliao/notion_rag/Agent人才匹配方法论.md)

---

## 六、Workflow & Skill 索引

> ⚠️ **查看项目进度时，先查下面的 Workflow**，它们包含各项目最新的任务状态和 Runbook。

### Workflows (`.agent/workflows/`)

| Slash 命令 | 文件 | 对应模块 | 说明 |
|:---|:---|:---|:---|
| `/github-network-mining` | `github-network-mining.md` | 👁 感知层：GitHub 人才发现 | **Phase 1→9 完整路线图 + Runbooks**，当前 Phase 3.5 进行中 |
| `/github-mining-reference` | `github-mining-reference.md` | 👁 (配套参考) | 爬取方法、分级标准(S/A/B/C)、字段映射、评分公式 |
| `/professor-student-sourcing` | `professor-student-sourcing.md` | 👁 感知层：学术人才发现 | 查找知名教授学生 → 当前去向 → 联系方式 |
| `/jd-batch-import` | `jd-batch-import.md` | 📊 记忆层：JD 导入 | CSV/Excel 批量导入职位 |
| `/batch-resume-import` | (外部) | 📊 记忆层：候选人导入 | 批量导入简历并自动解析 |
| `/bytedance-jd-import` | (外部) | 📊 记忆层：JD 导入 | 飞书文档批量导入字节跳动职位 |

### Skills (`.agent/skills/`)

| Skill | 说明 | 触发时机 |
|:---|:---|:---|
| `jd-naming-convention` | 职位编号(job_code)命名规范 | 导入/新建/更新 JD 时自动查阅 |

### 关键执行文档

| 文档 | 位置 | 说明 |
|:---|:---|:---|
| Sourcing 推进记录 | `personal-ai-headhunter/data/sourcing_推进.md` | 脉脉打招呼/加好友每日执行日志 |

