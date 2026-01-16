# 调试步骤 - 按钮未显示

## 请按照以下步骤操作

### 步骤 1：打开开发者工具

1. 在 LinkedIn 个人资料页面（https://www.linkedin.com/in/kejiazhou/）
2. 按 `F12` 打开开发者工具
3. 切换到 **Console** 标签

### 步骤 2：检查扩展是否加载

在 Console 中查找这些日志：
```
LinkedIn-Atlas Analyzer: Content script loaded
Initializing LinkedIn analyzer
```

**如果看到这些日志**：说明扩展已加载，但按钮注入失败
**如果没有看到**：说明 content script 根本没有运行

### 步骤 3：手动检查 DOM

在 Console 中运行以下命令：

```javascript
// 1. 检查按钮是否存在
console.log('Button exists:', !!document.getElementById('ai-analyze-button'));

// 2. 检查可能的容器
console.log('pv-top-card:', document.querySelector('.pv-top-card'));
console.log('scaffold-layout__main:', document.querySelector('.scaffold-layout__main'));

// 3. 列出所有可能的容器
document.querySelectorAll('[class*="top-card"]').forEach((el, i) => {
  console.log(`Container ${i}:`, el.className);
});
```

### 步骤 4：手动注入按钮（临时测试）

如果扩展已加载但按钮没出现，在 Console 运行：

```javascript
// 手动创建按钮
const button = document.createElement('button');
button.id = 'ai-analyze-button-test';
button.style.cssText = `
  position: fixed;
  top: 100px;
  right: 20px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
`;
button.textContent = '🎯 Test Button';
document.body.appendChild(button);
console.log('Test button created!');
```

这会在页面右上角创建一个测试按钮。如果能看到这个按钮，说明问题在于 DOM 选择器。

### 步骤 5：截图并发送

请截图包含：
1. **浏览器地址栏**（显示 URL）
2. **Console 标签**（显示所有日志）
3. **LinkedIn 页面**（显示是否有测试按钮）

发给我后，我可以根据实际情况修复代码。

---

## 可能的问题和解决方案

### 问题 A：扩展未加载

**症状**：Console 中没有任何 "LinkedIn-Atlas Analyzer" 日志

**解决方案**：
1. 访问 `chrome://extensions/`
2. 找到 "LinkedIn-Atlas Candidate Analyzer"
3. 点击 "重新加载" 按钮（刷新图标）
4. 回到 LinkedIn 页面，按 `Ctrl+Shift+R` 强制刷新

### 问题 B：DOM 选择器不匹配

**症状**：有日志但没有 "Analyze button injected"

**解决方案**：需要更新 DOM 选择器以匹配新的 LinkedIn 页面结构

### 问题 C：CSS 未加载

**症状**：按钮存在但看不见

**解决方案**：检查 styles.css 是否正确加载

---

## 快速诊断命令

复制粘贴到 Console 运行：

```javascript
// 完整诊断
console.log('=== LinkedIn-Atlas Analyzer 诊断 ===');
console.log('1. URL:', window.location.href);
console.log('2. URL 匹配:', window.location.href.includes('/in/'));
console.log('3. 按钮存在:', !!document.getElementById('ai-analyze-button'));
console.log('4. 扩展已加载:', typeof chrome !== 'undefined' && typeof chrome.runtime !== 'undefined');
console.log('5. Content script 变量:', typeof injectAnalyzeButton);

// 查找可能的容器
const containers = {
  'pv-top-card': document.querySelector('.pv-top-card'),
  'scaffold-layout__main': document.querySelector('.scaffold-layout__main'),
  'pv-top-card-v2-ctas': document.querySelector('.pv-top-card-v2-ctas'),
  'pvs-profile-actions': document.querySelector('.pvs-profile-actions')
};

console.log('6. 容器检查:');
Object.entries(containers).forEach(([name, el]) => {
  console.log(`   ${name}:`, el ? '✓ 找到' : '✗ 未找到');
});

console.log('=== 诊断完成 ===');
```
