# Maimai Assistant: 轻量级 CRM (V4 Hybrid Architecture) 设计规范

## 1. 架构目标 (Architecture Goal)
基于用户反馈，Maimai Assistant 插件从原有的全局覆盖模型（破坏了宿主页面的布局）升级为 **Hybrid 双轨架构**：
1.  **外部框架稳定**：保留原生的右侧边缘悬浮面板 (`position: fixed; right: 0; width: 360px`)，**坚决不遮挡脉脉主网页内容**。
2.  **内部沉浸式 CRM**：在 360px 的安全区内，通过双 Tab 分离“全局列表页批量操作”与“单个人才精细化归档操作”。

## 2. 核心模块设计 (Modules)

### Tab 1: 批量作业区 (Global/Batch Operations)
专门用于搜索列表页 (`/ent/v41/recruit/talents`) 或群组列表页的横向扫街：
*   ✅ **当前焦点**：捕捉当前页面的激活人才，提供一键生成破冰话术的功能。
*   ✅ **全局动作**：支持自动翻页的【批量加好友】、【批量打招呼】、【批量提取建立人才库】。

### Tab 2: 单人档案 CRM (Single Profile CRM)
专门用于针对单个高质量人才（从好友页或搜索弹窗点开时）的纵向深挖。UI 完全对齐高端 LinkedIn CRM 插件的标准：
1.  **Avatar & Header**: 候选人头像、姓名、当前最高职级与公司。
2.  **🧠 AI 评估**: 结构化的核心亮点提炼（例如：精通 PyTorch、多篇顶会、AI 适配度 9.5/10）。
3.  **📇 联系方式**: 显示 Email、Phone、WeChat 标签，支持一键脱敏复制或从剪贴板更新覆写。
4.  **⚡ 核心操作区 (Action Grid)**:
    *   【同步更新 / 加入人才库】：核心入库按钮（区分是否为双向好友）。
    *   【DB增强生成】：挂载深度的个性化 Prompt 生成消息。
    *   【发送邮件】：邮件模版直达。
    *   【标记为已沟通】：写回主系统的 Outreach Log。
    *   【下载简历】 / 【重新评级】 / 【重新打标签】。
5.  **🤝 触达状态**: 显示系统中的跟进阶段（如：未触达、已加好友、已回复）。
6.  **🏷️ 标签库**: 动态高亮标签（高潜、重点关注、被动人才等）。
7.  **主题与备注**: 支持拉取历史追溯和手工修改。

## 3. 前端样式规范 (CSS Framework)
采用独立的命名空间 `.crm-*` 彻底隔离，防止污染外层面板和脉脉原生 CSS：
*   **主色调**：`#0a66c2` (LinkedIn Blue, 核心行动按钮)。
*   **背景色**：主底色 `#f8f9fa`，卡片内景 `#ffffff`，悬浮投影 `box-shadow: 0 4px 12px rgba(0,0,0,0.08)`。
*   **卡片容器**：`.crm-card` 统一使用 `border-radius: 8px; border: 1px solid #e1e3e6`。
*   **字系**：`-apple-system, sans-serif`，标题 `font-weight: 600`，正文 `400`。
*   **操作按钮**：`.crm-btn-primary` 为蓝底白字，`.crm-btn-outline` 为白底蓝边，次要操作为白底灰边。

*(Documentation initialized on 2026-03-27)*
