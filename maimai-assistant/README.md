# Maimai Assistant

> 🎯 脉脉招聘助手 - 候选人采集 + 职位发布自动化

脉脉招聘页面的 Chrome 扩展插件，帮助招聘者高效管理候选人，并支持从 AI Headhunter 系统一键发布职位。

## ✨ 核心功能

### 📋 候选人采集
- 🤝 **批量添加好友** - 自动依次点击"加好友"
- 💬 **批量发消息** - 支持消息模板，自动发送招呼语
- 📋 **信息提取** - 批量/单个提取候选人详细信息
- 📤 **数据导出** - 支持 CSV/JSON 格式导出

### 📝 职位发布 (NEW v1.1.0)
- 🔗 **系统联动** - 从 personal-ai-headhunter 系统获取职位列表
- ✨ **自动填写** - 一键填写职位名称、描述等表单字段
- 🎯 **智能适配** - 自动适配脉脉 Ant Design 表单组件

## 🚀 安装方式

1. 下载本项目 `extension` 目录
2. 打开 Chrome，访问 `chrome://extensions/`
3. 开启右上角「开发者模式」
4. 点击「加载已解压的扩展程序」
5. 选择 `extension` 目录

## 📖 使用说明

### 候选人采集

1. 访问 [脉脉招聘页面](https://maimai.cn/ent/v41/recruit/talents?tab=1)
2. 页面左下角会出现持久悬浮面板
3. 勾选要操作的候选人
4. 点击相应操作按钮

### 职位发布 (新功能)

#### 前置条件
1. 确保 personal-ai-headhunter API 服务已启动:
   ```bash
   cd /path/to/personal-ai-headhunter
   python api_server.py
   ```
   默认运行在 `http://localhost:8502`

#### 使用步骤
1. 访问 [脉脉发布职位页面](https://maimai.cn/ent/v41/positions/add)
2. 页面右侧会出现「职位发布助手」面板
3. 配置 API 服务地址和接收简历邮箱
4. 从列表中选择要发布的职位
5. 点击「✨ 自动填写」
6. 手动选择职位类别、经验学历等下拉选项
7. 点击「发布职位」

## 📁 项目结构

```
maimai-assistant/
├── extension/
│   ├── manifest.json       # 扩展配置
│   ├── content/            # 候选人采集脚本
│   │   ├── content.js      # 入口控制器
│   │   ├── extractor.js    # 数据抓取
│   │   ├── panel.js        # 悬浮面板
│   │   └── content.css     # 样式
│   ├── job-poster/         # 职位发布脚本 (NEW)
│   │   ├── job-poster.js   # 发布自动化
│   │   └── job-poster.css  # 面板样式
│   ├── background/
│   │   └── background.js   # 后台服务
│   ├── popup/              # 弹窗界面
│   └── shared/             # 共享模块
│       ├── config.js       # API 配置
│       ├── constants.js    # 常量定义
│       └── utils.js        # 工具函数
└── README.md
```

## 🔌 API 端点

职位发布功能依赖以下 API（由 personal-ai-headhunter 提供）:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/jobs` | GET | 获取职位列表 |
| `/api/jobs/{id}` | GET | 获取职位详情 |
| `/api/jobs/{id}/maimai-form` | GET | 获取脉脉表单数据 |

## ⚠️ 注意事项

- 批量操作间隔 5-10 秒，避免触发平台检测
- 职位类别、行业要求等下拉框需手动选择
- 请合理使用，遵守平台规则
- 数据仅保存在本地，不会上传

## 📝 更新日志

### v2.0.0 (Premium CRM Upgrade)
- 🎨 **全新高级商务 UI 架构**: 取消遮挡式悬浮面板，固定吸附右侧屏幕，统入基于深空灰与领英蓝的商务感双列网格交互。
- ⚡ **DB 增强交互体系**: 深度打通本地 personal-ai-headhunter 后端数据库，新增实时同步判定、提取、新建能力。
- 🧠 **AI画像评价引擎**: 新增一键「AI画像生成」，接入后端大语言模型接口自动打分、提取优势；长文本启用 CSS 渐变折叠与防闪烁交互（对齐 LinkedIn 级交互体感）。
- 📅 **内嵌预约排期表单**: 无需跳出页面，通过原生控件实现日期、时间、备注撰写并快速与私有云行程系统（`PATCH /candidate/{id}/schedule`）打通。
- 📥 **智能路由抓取分发**: 自动识别是处于搜索流还是好友列表，针对不同的 DOM 结构启用不同的提取引擎与对应操作按钮。
- 🏷️ **标签云与意向追踪**: 直接在姓名旁以高亮 Chip 渲染 `status_tags` (如“正在看机会”)，并在操作区自动挂载 `talent_labels`。
- 📞 **内联编辑联动**: 集成「新增联系方式」折叠面板以及「DB增强消息生成的编辑工作台」，所有修改支持原地保存入库，全靠前端无感同步获取。

### v1.1.0
- ✨ 新增职位发布功能
- 🔗 支持与 personal-ai-headhunter 系统联动
- 🎨 全新职位发布助手面板

### v1.0.0
- 🎉 初始版本
- 支持候选人批量操作
- 支持信息提取与导出

## 📝 License

MIT
