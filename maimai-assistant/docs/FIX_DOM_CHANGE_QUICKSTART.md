# 🔧 脉脉 DOM 变化快速修复指南

## 问题确认

✅ **问题根源已找到**: 脉脉网站的 DOM 结构已变化，`.virtualized-message-list` 选择器失效。

---

## 🚀 立即修复（3个步骤）

### 步骤 1: 运行诊断脚本

1. 打开脉脉招聘消息页面: `https://maimai.cn/ent/v41/im`
2. 按 `F12` 打开开发者工具
3. 切换到 **Console** 标签
4. 复制并粘贴以下代码：

```javascript
// 快速诊断脚本
(function() {
    console.log('🔍 开始诊断...');

    // 方法1: 查找所有可能的列表容器
    const allDivs = Array.from(document.querySelectorAll('div'));
    const likelyContainers = allDivs.filter(el =>
        el.children.length >= 5 &&
        el.scrollHeight > el.clientHeight &&
        el.scrollHeight > 100
    );

    console.log(`找到 ${likelyContainers.length} 个可能的列表容器:`);

    likelyContainers.slice(0, 5).forEach((el, i) => {
        console.log(`\n${i + 1}. className: "${el.className}"`);
        console.log(`   - id: "${el.id}"`);
        console.log(`   - children: ${el.children.length}`);
        console.log(`   - scrollHeight: ${el.scrollHeight}`);
        console.log(`   - 查看子元素:`, el.children[0]?.className);
    });

    // 方法2: 查找包含消息时间戳的元素
    const timeElements = Array.from(document.querySelectorAll('*')).filter(el => {
        const text = el.textContent?.trim();
        return text && (text.includes('分钟前') || text.includes('小时前') || text === '刚刚' || text === '昨天' || /^\d{1,2}:\d{2}$/.test(text));
    });

    console.log(`\n找到 ${timeElements.length} 个包含时间戳的元素`);

    if (timeElements.length > 0) {
        const timeEl = timeElements[0];
        console.log('\n时间元素示例:', timeEl.textContent.trim());

        // 向上查找列表容器
        let parent = timeEl.parentElement;
        for (let i = 1; i <= 10 && parent; i++) {
            if (parent.children.length >= 5) {
                console.log(`\n🎯 可能的列表容器 (第${i}级):`);
                console.log(`   - className: "${parent.className}"`);
                console.log(`   - tagName: ${parent.tagName}`);
                console.log(`   - id: "${parent.id}"`);
                console.log(`   - children: ${parent.children.length}`);

                // 生成建议的选择器
                if (parent.id) {
                    console.log(`   - 💡 建议选择器: #${parent.id}`);
                } else if (parent.className) {
                    const firstClass = parent.className.split(' ')[0];
                    if (firstClass) {
                        console.log(`   - 💡 建议选择器: .${firstClass}`);
                    }
                }
                break;
            }
            parent = parent.parentElement;
        }
    }

    // 方法3: 查找脉脉特定的类名
    const maimaiElements = Array.from(document.querySelectorAll('[class*="maimai"], [class*="recruit"], [class*="im-"], [class*="chat-"]'));
    console.log(`\n找到 ${maimaiElements.length} 个脉脉相关元素`);

    maimaiElements.slice(0, 3).forEach((el, i) => {
        console.log(`${i + 1}. ${el.className}`);
    });

    console.log('\n✅ 诊断完成！');
})();
```

5. 按 `Enter` 执行

### 步骤 2: 查找新的选择器

从控制台输出中，找到类似这样的信息：

```
🎯 可能的列表容器 (第3级):
   - className: "xyz-list-container message-list-new"
   - tagName: DIV
   - 💡 建议选择器: .xyz-list-container
```

记下 `💡 建议选择器` 中的内容（例如：`.xyz-list-container`）

### 步骤 3: 更新代码

打开文件：`extension/content/im-processor.js`

找到第 89 行左右，将建议的选择器添加到列表中：

```javascript
const selectors = [
    '.virtualized-message-list',
    '.ReactVirtualized__Grid',
    '.ReactVirtualized__List',
    '[class*="message-list"]',
    '[class*="session-list"]',
    '[class*="conversation-list"]',
    '[class*="chat-list"]',
    '[class*="im-list"]',
    '[class*="dialogue-list"]',
    '[class*="message"]',
    'ul[role*="list"]',
    'div[role*="list"]',
    '[class*="List"]',
    '[class*="Container"]',
    '[class*="Wrapper"]',
    '.xyz-list-container',        // ← 添加你找到的新选择器
];
```

保存文件，然后在 Chrome 中重新加载扩展：
1. 打开 `chrome://extensions/`
2. 找到 "Maimai Assistant"
3. 点击 🔄 重新加载

---

## 🧪 验证修复

1. 刷新脉脉招聘消息页面
2. 打开浏览器控制台 (F12)
3. 点击 "▶️ 自动助理：开始过筛消息" 按钮
4. 查看控制台输出

**期望输出**:
```
[ImProcessor] ✅ 找到容器，使用选择器: .xyz-list-container
[ImProcessor] 找到消息列表容器...
```

---

## 🆘 如果还是找不到

### 方法 A: 直接查看页面 HTML

1. 在脉脉招聘消息页面
2. 右键点击一个消息会话
3. 选择 "检查" 或 "审查元素"
4. 在开发者工具中，向上滚动查看 DOM 树
5. 找到包含所有消息的容器（通常是一个 `div` 或 `ul`）
6. 记录它的 `class` 或 `id`

### 方法 B: 使用完整的诊断脚本

我已创建了完整的诊断脚本：`scripts/diagnose_maimai_dom.js`

在浏览器 Console 中运行：
```javascript
// 复制 diagnose_maimai_dom.js 的内容，粘贴到 Console 执行
```

---

## 📝 反馈信息

请将以下信息反馈给我：

1. **诊断脚本输出的关键信息**：
   - 🎯 可能的列表容器信息
   - 💡 建议选择器

2. **页面 HTML 片段**：
   - 在消息列表区域右键 → 检查
   - 截图或复制 HTML 结构

3. **脉脉页面 URL**：
   - 确认你是在哪个页面测试的
   - 例如：`https://maimai.cn/ent/v41/im`

---

## 🔮 长期解决方案

我可以帮你实现一个更智能的 DOM 选择器，它能：

1. 自动适应脉脉的 DOM 变化
2. 使用多种策略（时间戳、滚动条、子元素数量）
3. 动态学习和缓存选择器

需要我实现这个功能吗？
