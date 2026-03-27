---
name: LinkedIn Premium Frontend Design System
description: 高级商务(LinkedIn)风格前端设计规范。在新建页面或重构React组件时，必须严格遵守此规范，弃用DaisyUI默认的低级/花哨色彩体系。
---

# LinkedIn Premium Frontend Design System

本文档定义了 AI Headhunter (Talent CRM) 项目的全局 UI 规范。在生成或修改 React 组件时，必须严格遵守以下原则，确保界面保持高级、商务、极简的 LinkedIn 风格。

## 1. 核心色彩体系 (Color Palette)
- **品牌主色 (Brand Blue)**: `#0a66c2` (与 LinkedIn 主吸色一致)。已在 `index.css` 中重写 `--color-primary`
- **背景色**: 
  - 全局底层背景: `#f8f9fa` (高级灰)
  - 卡片/内容区背景: `#ffffff` (纯白)
  - 悬浮态(Hover)高亮底色: `#f0f7ff` (极淡的蓝色) 或 `#f1f3f4` (浅灰)
- **文字色**:
  - 主标题/正文: `text-gray-900` 或 `text-gray-800`
  - 次要信息/描述: `text-gray-500`

## 2. 按钮组件规范 (Unified Action Buttons)
**严禁使用**自带强烈色彩冲突的 DaisyUI 默认状态按钮 (如 `btn-success`, `btn-warning`, `btn-error`, `btn-accent`)。所有交互按钮必须遵循统一的“灰/白/蓝”边框逻辑。

- **默认按钮 (次要操作/未激活状态)**:
  `className="flex items-center justify-center gap-1.5 px-3 py-1.5 border border-[#dadce0] rounded-lg bg-white text-xs font-medium text-gray-700 hover:bg-[#f1f3f4] hover:text-[#0a66c2] hover:border-[#0a66c2] transition-all"`
- **高亮按钮 (首要操作/已激活状态)**:
  `className="flex items-center justify-center gap-1.5 px-3 py-1.5 border rounded-lg text-xs font-medium transition-all bg-[#f0f7ff] border-[#c2d7f0] text-[#0a66c2] hover:bg-[#ddeeff]"`
- **危险操作 (删除)**:
  `className="flex items-center justify-center gap-1.5 px-3 py-1.5 border border-[#dadce0] rounded-lg bg-white text-xs font-medium text-gray-400 hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-all"`

## 3. 面板与卡片规范 (Cards & Panels)
界面布局应采用“隐形容器”加“干净卡片”的理念。
- **卡片容器**:
  `className="bg-white rounded-xl shadow-sm border border-[#dadce0] p-4"`
  (注意：避免使用过重的 `shadow-xl`，统一使用 `shadow-sm` 或自定义 `shadow-[0_2px_8px_rgba(0,0,0,0.06)]`)
- **边角弧度**: 统一使用 `rounded-lg` 或 `rounded-xl`，**绝不使用** `rounded-full` (非药丸形状)。

## 4. 信息展示原则 (Information Architecture)
- **去除“标签海”**: 详情或列表页中，不要通过密集堆砌带背景色的 Tag (`badge`) 来展示技能点。如果是文本，直接使用逗号分隔或低对比度的灰色文字展示。
- **避免多余修饰**: 删除不必要的边框颜色、警告底色块。即使是“提醒”类信息，也要融入到白底灰字的布局中，仅通过单一的醒目Icon（如 🔴）提示，不要把整个区块变成红色或黄色。

每次创建新的页面组件时，AI Agent 都必须参考本文件，维持全站体验的一致性和高级感。
