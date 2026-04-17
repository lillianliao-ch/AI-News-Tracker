# Maimai Assistant - AI消息处理中心问题诊断报告

**日期**: 2026-04-09
**问题**: "AI消息处理中心"之前可以工作，今天不能工作了

---

## 代码历史分析

### 功能添加时间

**3月29日** (提交 fafa87cf): "AI消息处理中心"功能首次添加
- 新增文件：`extension/content/im-processor.js` (652行)
- 修改文件：`extension/content/panel.js` (添加UI和事件处理)
- 修改文件：`extension/content/content.js` (添加 `batchProcessImMessages` 方法)

**结论**: 用户提到的"3月27日"可能是记错了日期，功能实际上是在3月29日添加的。

### 自3月29日以来的代码变化

```bash
# im-processor.js - 无变化
git log fafa87cf..HEAD --oneline -- extension/content/im-processor.js
# 输出: (空)

# content.js - batchProcessImMessages 方法无变化
git diff fafa87cf HEAD -- extension/content/content.js | grep batchProcessImMessages
# 输出: (空)

# panel.js - 事件处理器无变化
git diff fafa87cf HEAD -- extension/content/panel.js | grep batchProcessImBtn
# 输出: (显示新增时的事件处理器，后续无修改)
```

---

## 代码结构分析

### 文件加载顺序 (manifest.json)

```json
"js": [
    "shared/config.js",
    "shared/constants.js",
    "shared/utils.js",
    "content/extractor.js",
    "content/detail-extractor.js",
    "content/talent-extractor.js",
    "search/search-extractor.js",
    "search/search-engine.js",
    "content/panel.js",           ← 第6个加载
    "content/im-processor.js",     ← 第7个加载 ✅
    "content/content.js"           ← 第8个加载
]
```

**加载顺序正确**: `im-processor.js` 在 `content.js` 之前加载

### 类导出方式

**im-processor.js** (最后一行):
```javascript
window.ImProcessor = ImProcessor;
```

**content.js** (使用方式):
```javascript
async batchProcessImMessages(days = 3) {
    if (!this.imProcessor) {
        this.imProcessor = new ImProcessor(this);  // ← 使用 window.ImProcessor
    }
    ...
}
```

---

## 可能的问题原因

### 1. **浏览器缓存问题** ⭐ (最可能)

Chrome 扩展的 content script 可能被缓存了旧版本。

**解决方法**:
```bash
# 1. 在 Chrome 中重新加载扩展
chrome://extensions/ → Maimai Assistant → 🔄 重新加载

# 2. 或者完全删除扩展后重新安装
```

### 2. **脉脉网站 DOM 结构变化**

脉脉可能更新了招聘消息页面的 DOM 结构，导致选择器失效。

**检查方法**:
1. 打开脉脉招聘消息页面: `https://maimai.cn/ent/v41/im`
2. 按 F12 打开开发者工具
3. 在 Console 中输入:
```javascript
document.querySelector('.virtualized-message-list')
```

**期望结果**: 应该返回一个 DOM 元素
**实际结果**: 如果返回 `null`，说明 DOM 结构已变化

### 3. **API 服务器连接问题**

`im-processor.js` 需要连接到 `http://localhost:8502` 的 API 服务器。

**检查方法**:
```bash
# 检查 API 服务器是否运行
curl http://localhost:8502/api/candidates?page=1&page_size=1
```

**解决方法**: 如果服务器未运行，启动 API 服务器
```bash
cd personal-ai-headhunter
nohup uvicorn api_server:app --host 0.0.0.0 --port 8502 --reload &
```

### 4. **JavaScript 错误**

可能是运行时 JavaScript 错误导致功能中断。

**检查方法**:
1. 打开脉脉招聘消息页面
2. 按 F12 打开开发者工具
3. 切换到 Console 标签
4. 点击"▶️ 自动助理：开始过筛消息"按钮
5. 查看是否有红色错误信息

---

## 调试步骤

### 第1步: 检查浏览器控制台

```javascript
// 在脉脉招聘消息页面的 Console 中执行

// 1. 检查 ImProcessor 类是否已加载
console.log('ImProcessor:', typeof window.ImProcessor);

// 2. 检查 MaimaiAssistant 是否已初始化
console.log('Assistant:', window.maimaiAssistant);

// 3. 检查面板是否已创建
console.log('Panel:', window.maimaiAssistant?.panel);
```

**期望输出**:
```
ImProcessor: function
Assistant: MaimaiAssistant {...}
Panel: AssistantPanel {...}
```

### 第2步: 手动调用功能

```javascript
// 在 Console 中手动触发消息处理
const days = 3;
window.maimaiAssistant.batchProcessImMessages(days);
```

**观察**: 是否有任何输出或错误

### 第3步: 检查 DOM 选择器

```javascript
// 检查消息列表容器是否存在
const selectors = [
    '.virtualized-message-list',
    '.ReactVirtualized__Grid',
    '.ReactVirtualized__List'
];

selectors.forEach(sel => {
    const el = document.querySelector(sel);
    console.log(`${sel}:`, el ? '✅ 找到' : '❌ 未找到');
});
```

### 第4步: 检查 API 连接

```javascript
// 检查 API 配置
chrome.storage.local.get(['apiBaseUrl'], (result) => {
    console.log('API Base URL:', result.apiBaseUrl || 'http://localhost:8502');
});
```

---

## 快速修复尝试

### 方案 1: 强制刷新扩展

1. 打开 `chrome://extensions/`
2. 找到 "Maimai Assistant"
3. 点击 🔄 刷新按钮
4. 重新加载脉脉页面

### 方案 2: 清除浏览器缓存

1. 打开脉脉招聘消息页面
2. 按 `Ctrl+Shift+Delete` (Windows) 或 `Cmd+Shift+Delete` (Mac)
3. 选择"缓存的图像和文件"
4. 点击"清除数据"
5. 重新加载页面

### 方案 3: 检查 API 服务器

```bash
# 确保 API 服务器正在运行
cd /Users/lillianliao/notion_rag/personal-ai-headhunter
nohup uvicorn api_server:app --host 0.0.0.0 --port 8502 --reload &
```

### 方案 4: 重新安装扩展

1. 打开 `chrome://extensions/`
2. 找到 "Maimai Assistant"
3. 点击"移除"
4. 重新加载扩展（从 `extension/` 文件夹）

---

## 下一步建议

1. **优先检查**: 浏览器控制台是否有 JavaScript 错误
2. **验证环境**: API 服务器是否运行在 `localhost:8502`
3. **检查 DOM**: 脉脉网站的 DOM 结构是否有变化
4. **回滚测试**: 如果需要，可以回滚到3月29日的版本测试

---

**需要用户提供的信息**:
1. 浏览器控制台的错误信息（如果有）
2. 点击按钮后的具体行为（无反应/报错/卡死）
3. API 服务器是否正在运行
4. 是否可以手动在 Console 中调用 `window.maimaiAssistant.batchProcessImMessages(3)`
