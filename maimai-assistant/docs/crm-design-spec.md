# Maimai Assistant: 轻量级 CRM (V4 Hybrid Architecture) 设计规范

> Status: design-intent doc
> Use this document for: the intended CRM interaction model, panel layout, and premium workflow direction.
> Do not treat every section here as proof that the full runtime behavior is already implemented exactly as described; verify against `extension/*` code.

## 1. 架构目标 (Architecture Goal)
基于用户反馈，Maimai Assistant 插件从原有的全局覆盖模型（破坏了宿主页面的布局）升级为 **Hybrid 双轨架构**：
1.  **外部框架稳定**：保留原生的右侧边缘悬浮面板 (`position: fixed; right: 0; width: 360px`)，**坚决不遮挡脉脉主网页内容**。
2.  **内部沉浸式 CRM**：在 360px 的安全区内，通过双 Tab 分离“全局列表页批量操作”与“单个人才精细化归档操作”。

## 2. 核心模块设计 (Modules)

## 2. 核心功能全景图 (Feature Capabilities)

### Tab 1: 批量作业区 (Batch Operations & Search Parsing)
专门用于搜索列表页 (`/ent/v41/recruit/talents`) 或群组列表页的横向扫街：
*   **当前焦点感知**：自动捕捉当前脉脉页面的选中人才，支持一键基于本地模版生成基础的打招呼破冰话术。
*   **自动化流水线**：集成后台挂机级的【批量加好友】、【批量打招呼】功能，并带有防封禁延迟策略。
*   **批量提取建库**：以列表模式深度解析整页候选人脱敏数据，构建初步的人才库。

### Tab 2: 单人档案高级 CRM (Single Profile Premium CRM)
专为单个高质量候选人设计的纵向沉浸式作业台，完全对齐顶配商业版（LinkedIn）插件体验：

#### 1. 智能双擎环境自适应 (Dual-Engine Routing)
*   **动态环境识别**：实时切分路由，识别位于「搜索流弹窗页」或是独立的「好友资料页」。
*   **无缝提取策略**：针对性使用对应的 DOM 选择器执行解析。
*   **按钮互斥系统**：根据所处页面自动挂载互斥的抓取按钮（展示【🔄 同步更新】或【📥 收录好友】）。

#### 2. 即时头部情报与意向监控 (Header & Intent Tracker)
*   **核心身份展示**：自动呈现高净值职级、公司、及算法打出的「AI 适配度」等级标签。
*   **客观意向监控 (`status_tags`)**：如果 DB 记录中包含“正在看机会”或“近期有动向”，直接在姓名旁以醒目动态胶囊 (Chip) 展示。

#### 3. 🧠 原生 AI 评估折叠工作台 (AI Assessment System)
*   读取大模型产出的六大维度评估报告（职业画像、背景亮点、市场定位等）。
*   **长文本溢出控制**：复刻 LinkedIn 高级交互，对超 100 字符的评估内容采取 `max-height: 80px` 高度锁定 + 白色渐变遮罩。
*   **展开/收起联动**：通过 `展开全部 ▾` 按钮原生地切换视图状态。

#### 4. 📞 内联私有联系方式管理器 (Inline Contact Editor)
*   直观显示已绑定的手机、Email、微信及 GitHub/Twitter 等多维账号。
*   **下拉新建面板**：点击“✏️ 新增联系”直接就地展开原生小表单，填写完毕发送 `PUT` 接口强制覆写至云端，拒绝路由跳转，实现零阻力数据治理。

#### 5. ⚡ 2x2 深度操作核心区 (Action Grid Matrix)
提供严苛对称美学的 4 大核心战术指令：
*   **【同步更新/收录好友】**: 入库数据的基础触发器。
*   **【🚀 DB增强消息】**: 弃用基础的本地模版替换法则，转而请求后端的纯大模型生成链路，基于该候选人的详尽经历（或甚至附加的 GitHub/Paper 数据）提炼高度个性化的邀约信息。
*   **【🧠 AI画像生成】**: 无需手动从控制台触发，前端发送 `POST` 请求一键让云端执行 AI 理解，成功后界面会自动刷新展示全新评价，且滚动条自定位至评估框。
*   **【📅 预约跟进】**: 点击直接开启下方的日历面板。

#### 6. 📅 原生日历与排期闭环 (Native Schedule Loop)
*   Maimai 插件专属的预约微型 DOM 表单组件。
*   支持填写精确的「预约日期」、「预约时间」与「跟进长备注」。
*   点击保存发起 `PATCH /candidate/{id}/schedule` 后端通信，与 Personal AI Headhunter 主后端的「跟进雷达/待办」系统合二为一。

#### 7. 📝 DB 消息修改工作台 (Message Persistence Editor)
*   在生成 DB 消息后，底部展开大型可编辑化 `textarea` 工作台。
*   支持 HR 二次润色（搭配动态字数监测仪）。
*   **一键归档**: 支持点击【保存入库 (Comm Log)】，以“主动触达”形式永久储存在 DB 的跟进历史轴中，驱动漏斗下漏。

#### 8. 🤝 状态与历史反馈墙 (State & Sync Reflection)
*   **双向触达反馈**：直接绘制 `标记已触达` 或 `标记已回复` 按钮。
*   全盘利用 MutationObserver 进行 `_checkCandidateDbStatus()` 守卫拦截。只要人才资料（例如打标签动作）在主后台中转置或产生异动，插件会在 800ms 内进行无缝局部静默刷新，维持全局单例数据一致性。
