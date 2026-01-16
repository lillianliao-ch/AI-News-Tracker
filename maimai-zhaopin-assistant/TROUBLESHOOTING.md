# 脉脉招聘助手 - 故障排除指南

## 🔧 插件不显示问题解决

### 问题现象
插件安装后在脉脉网站左下角没有显示蓝色控制面板

### 解决步骤

#### 1. 检查插件安装状态
1. 打开 `chrome://extensions/`
2. 确认「脉脉招聘助手」已启用
3. 查看是否有错误提示

#### 2. 检查网站匹配
1. 确保访问的是 `maimai.cn` 域名
2. 刷新页面重新加载插件
3. 尝试清除浏览器缓存

#### 3. 开发者工具调试
1. 在脉脉网站按 `F12` 打开开发者工具
2. 切换到 `Console` 标签
3. 查找以下调试信息：
   ```
   脉脉招聘助手: 开始初始化...
   脉脉招聘助手: 开始创建UI...
   脉脉招聘助手: 创建控制面板...
   脉脉招聘助手: 控制面板创建完成，已添加到页面
   脉脉招聘助手: UI创建成功，插件已加载
   ```

#### 4. 手动查找面板
如果面板创建了但不可见，在Console中运行：
```javascript
// 查找面板元素
const panel = document.getElementById('maimai-assistant-panel');
console.log('面板元素:', panel);

// 强制显示面板
if (panel) {
    panel.style.display = 'block';
    panel.style.position = 'fixed';
    panel.style.bottom = '20px';
    panel.style.left = '20px';
    panel.style.zIndex = '999999';
    panel.style.background = 'white';
    panel.style.border = '2px solid #1890ff';
    console.log('面板已强制显示');
}
```

## 🚨 常见错误及解决方案

### 错误1：插件权限不足
**现象**：Console显示权限错误
**解决**：
1. 重新安装插件
2. 确保选择正确的文件夹（包含manifest.json）

### 错误2：脚本加载失败
**现象**：Console显示脚本错误
**解决**：
1. 检查文件完整性
2. 确保所有文件都在正确位置：
   ```
   maimai-zhaopin-assistant/
   ├── manifest.json
   ├── content.js
   ├── styles.css
   └── ...
   ```

### 错误3：面板样式异常
**现象**：面板显示但样式混乱
**解决**：
1. 检查 styles.css 文件是否存在
2. 在Console中运行强制样式修复：
   ```javascript
   // 强制应用样式
   const panel = document.getElementById('maimai-assistant-panel');
   if (panel) {
       panel.className = 'maimai-assistant';
       const link = document.createElement('link');
       link.rel = 'stylesheet';
       link.href = chrome.runtime.getURL('styles.css');
       document.head.appendChild(link);
   }
   ```

## 📋 完整检查清单

### 安装前检查
- [ ] Chrome版本 ≥ 88
- [ ] 开发者模式已开启
- [ ] 文件夹包含所有必要文件

### 安装后检查
- [ ] 插件在扩展程序页面显示为已启用
- [ ] 访问 maimai.cn 网站
- [ ] F12查看Console无错误信息
- [ ] 左下角显示蓝色控制面板

### 功能测试检查
- [ ] 面板可以折叠/展开
- [ ] 「提取当前人才」按钮可点击
- [ ] 数据预览区显示正常
- [ ] 备注框可以输入内容

## 🔄 重新安装步骤

如果以上方法都无效，建议完全重新安装：

1. **卸载旧版本**
   - 在 chrome://extensions/ 中移除插件
   - 清理浏览器缓存

2. **重新下载文件**
   - 确保所有文件完整
   - 检查文件编码为UTF-8

3. **重新安装**
   - 严格按照INSTALL.md步骤操作
   - 确认每一步都成功完成

## 📞 获取帮助

如仍无法解决问题：

1. **收集调试信息**
   - Console中的完整错误日志
   - 浏览器版本信息
   - 操作系统信息

2. **检查网络环境**
   - 确保网络连接正常
   - 检查是否有代理或防火墙拦截

3. **尝试其他浏览器**
   - 在其他Chrome内核浏览器中测试
   - 确认是否为特定环境问题

---

**最后更新**：2024-12-21  
**适用版本**：v1.0.0