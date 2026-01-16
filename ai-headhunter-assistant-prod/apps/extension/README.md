# Chrome 插件

Boss 直聘候选人采集插件 - 生产版本

## ✅ 迁移状态

- ✅ 插件代码已迁移
- ✅ 图标文件已添加
- ✅ 核心功能完整
- ⏳ 打包脚本待配置
- ⏳ 自动化测试待添加

## 🎯 功能

### 核心功能 (v1.0.3)
- ✅ 候选人列表自动采集
- ✅ 简历详情提取
- ✅ 简历截图（处理 Canvas 加密）
- ✅ AI 评估集成
- ✅ 数据导出（CSV + Markdown + PNG）
- ✅ 两轮处理逻辑（快速筛选 + 深度分析）
- ✅ 控件 UI 优化（尺寸缩小 50%）

### 技术亮点
- ✅ 处理 Boss 直聘 WebAssembly + Canvas 加密
- ✅ Background Service Worker 处理截图
- ✅ Content Script 和 Background Script 消息通信
- ✅ Base64 图片编码
- ✅ 截图前自动隐藏控件

## 📁 文件结构

```
apps/extension/
├── manifest.json          # 插件配置（Manifest V3）
├── content-full.js        # 主逻辑（完整功能）
├── background.js          # 后台服务（截图）
├── simple-test.js         # 测试脚本
├── icons/                 # 图标文件
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── package.json           # npm 脚本配置
├── 快速开始.md            # 快速上手指南
└── README.md              # 本文件
```

## 🚀 快速开始

查看 [快速开始.md](./快速开始.md) 了解详细安装和使用步骤。

### 安装

1. 打开 Chrome：`chrome://extensions/`
2. 启用"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择 `apps/extension/` 目录
5. 完成！

### 使用

1. 访问 https://www.zhipin.com/web/chat/recommend
2. 控制面板会自动显示在左下角
3. 设置处理数量，点击"开始处理"
4. 处理完成后导出结果

## 📊 处理流程

### 第一轮：快速筛选
1. 扫描所有候选人卡片
2. 提取基本信息（姓名、年龄、公司等）
3. 调用后端获取 Mock 评级
4. 保存到 CSV

### 第二轮：深度分析（仅"推荐"候选人）
1. 点击候选人卡片
2. 打开简历详情弹层
3. 提取完整简历文本
4. 截取简历截图
5. 调用后端进行真实 AI 评估
6. 更新 Markdown 和导出 PNG

## 🛠️ 技术栈

- **Manifest**: V3
- **JavaScript**: ES6+
- **Chrome APIs**: tabs, scripting, runtime
- **通信**: Message Passing
- **截图**: captureVisibleTab API

## 📦 导出文件

| 文件 | 内容 | 用途 |
|------|------|------|
| `AI猎头助手-{日期}.csv` | 所有候选人数据表 | Excel 导入，数据分析 |
| `AI猎头助手-{日期}.md` | 详细分析报告 | 阅读，Typora 打开 |
| `{姓名}_简历_{时间戳}.png` | 简历截图 | 飞书上传，存档 |

## 🔧 开发

### 修改后端地址

编辑 `content-full.js`：
```javascript
const API_CONFIG = {
  baseURL: 'http://localhost:8000',  // 修改这里
  timeout: 60000
};
```

### 打包发布

```bash
npm run pack
# 生成 extension.zip
```

### 调试

1. 打开浏览器控制台（F12）
2. 查看 Console 日志
3. 查看 Network 请求

## 🐛 常见问题

### 插件没有显示
- 确认在正确的页面
- 刷新页面
- 检查控制台错误

### 后台服务未连接
- 确认后端已启动
- 访问 http://localhost:8000/health
- 检查 CORS 配置

### 截图失败
- 检查权限是否授予
- 查看控制台日志
- 尝试手动刷新页面

## 📈 版本历史

- **v1.0.3** (2025-11-14)
  - ✅ 控件尺寸优化
  - ✅ 防止重复注入
  - ✅ 截图前隐藏控件

- **v1.0.2** (2025-11-14)
  - ✅ 修复 Canvas 截图问题
  - ✅ 使用 captureVisibleTab API

- **v1.0.1** (2025-11-14)
  - ✅ 两轮处理逻辑
  - ✅ Markdown 和 PNG 导出

- **v1.0.0** (2025-11-13)
  - ✅ 基础功能完成
  - ✅ CSV 导出

## 🔄 下一步

- [ ] 添加设置页面（popup.html）
- [ ] 配置自动化打包
- [ ] 添加 E2E 测试
- [ ] 支持多平台（猎聘、脉脉）
- [ ] 添加数据缓存
- [ ] 优化错误处理

## 📖 相关文档

- [快速开始指南](./快速开始.md)
- [后端 API 文档](../backend/README.md)
- [项目进度](../../docs/mvp/项目进度.md)
- [测试清单](../../docs/mvp/Day3-插件测试清单.md)
