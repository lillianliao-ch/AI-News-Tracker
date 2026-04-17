// 脉脉消息列表容器诊断脚本
// 在脉脉招聘消息页面的浏览器 Console 中运行此脚本

console.log('🔍 开始诊断脉脉消息列表 DOM 结构...\n');

// 1. 查找所有可能的列表容器
const possibleContainers = [
    // 常见的列表容器类名
    '[class*="message-list"]',
    '[class*="session-list"]',
    '[class*="conversation-list"]',
    '[class*="chat-list"]',
    '[class*="im-list"]',
    '[class*="message"]',
    '[class*="list"]',

    // React Virtualized 相关
    '.ReactVirtualized__Grid',
    '.ReactVirtualized__List',
    '[class*="Virtualized"]',

    // 通用容器
    'ul[role*="list"]',
    'div[role*="list"]',
    '[class*="List"]',

    // 特定于脉脉
    '[class*="maimai"]',
    '[class*="recruit"]',
];

console.log('📋 尝试找到消息列表容器...\n');

const foundContainers = new Map();

possibleContainers.forEach(selector => {
    try {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
            elements.forEach((el, index) => {
                const key = `${selector}[${index}]`;
                foundContainers.set(key, el);

                // 分析元素特征
                const info = {
                    selector: key,
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id,
                    childCount: el.children.length,
                    hasScroll: el.scrollHeight > el.clientHeight,
                    rect: el.getBoundingClientRect(),
                    parent: el.parentElement?.className,
                };

                console.log(`✅ 找到:`, info);
            });
        }
    } catch (e) {
        // 忽略无效选择器
    }
});

// 2. 查找包含时间的元素（脉脉消息特征）
console.log('\n⏰ 查找包含时间戳的元素...');
const timePatterns = [
    '刚刚',
    '分钟前',
    '小时前',
    '昨天',
    '前天',
    /^\d{1,2}:\d{2}$/,  // 12:09
    /^\d{1,2}\/\d{1,2}$/,  // 03/25
];

const timeElements = Array.from(document.querySelectorAll('span, div, p, time')).filter(el => {
    const text = el.textContent?.trim();
    if (!text) return false;

    return timePatterns.some(pattern => {
        if (typeof pattern === 'string') {
            return text === pattern || text.includes(pattern);
        } else {
            return pattern.test(text);
        }
    });
});

console.log(`找到 ${timeElements.length} 个包含时间的元素`);

if (timeElements.length > 0) {
    console.log('\n前5个时间元素:');
    timeElements.slice(0, 5).forEach((el, i) => {
        console.log(`${i + 1}. "${el.textContent.trim()}"`);
        console.log(`   - 父级: ${el.parentElement?.className || el.parentElement?.tagName}`);
        console.log(`   - 祖父级: ${el.parentElement?.parentElement?.className || el.parentElement?.parentElement?.tagName}`);
    });

    // 3. 从时间元素向上查找列表容器
    console.log('\n🔺 尝试从时间元素向上查找列表容器...');

    const timeElement = timeElements[0];
    let current = timeElement.parentElement;

    for (let level = 1; level <= 10 && current; level++) {
        const info = {
            level,
            tagName: current.tagName,
            className: current.className,
            childCount: current.children.length,
            hasScroll: current.scrollHeight > current.clientHeight,
        };

        console.log(`第 ${level} 级:`, info);

        // 如果这个元素有多个子元素且有滚动条，可能是列表容器
        if (current.children.length >= 3 && current.scrollHeight > current.clientHeight) {
            console.log(`🎯 可能的列表容器 (第 ${level} 级):`, {
                tagName: current.tagName,
                className: current.className,
                id: current.id,
                childCount: current.children.length,
                hasScroll: true,
                selector: current.id ? `#${current.id}` : (current.className ? `.${current.className.split(' ')[0]}` : current.tagName.toLowerCase()),
            });
            break;
        }

        current = current.parentElement;
    }
}

// 4. 查找所有具有滚动条的 div
console.log('\n📜 查找所有具有滚动条的容器...');
const scrollableDivs = Array.from(document.querySelectorAll('div')).filter(el => {
    const style = window.getComputedStyle(el);
    return (
        el.scrollHeight > el.clientHeight &&
        (style.overflowY === 'auto' || style.overflowY === 'scroll' || style.overflow === 'auto' || style.overflow === 'scroll')
    );
});

console.log(`找到 ${scrollableDivs.length} 个可滚动 div`);
scrollableDivs.slice(0, 5).forEach((el, i) => {
    console.log(`${i + 1}.`, {
        tagName: el.tagName,
        className: el.className.substring(0, 100),  // 限制长度
        id: el.id,
        childCount: el.children.length,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
    });
});

// 5. 导出结果到全局变量，方便后续调试
window.diagnosticResults = {
    foundContainers: Array.from(foundContainers.entries()).map(([key, el]) => ({
        selector: key,
        tagName: el.tagName,
        className: el.className,
        id: el.id,
        childCount: el.children.length,
        hasScroll: el.scrollHeight > el.clientHeight,
    })),
    timeElements: timeElements.map(el => ({
        text: el.textContent,
        parentClass: el.parentElement?.className,
        parentTag: el.parentElement?.tagName,
    })),
    scrollableDivs: scrollableDivs.map(el => ({
        className: el.className.substring(0, 100),
        id: el.id,
        childCount: el.children.length,
    })),
};

console.log('\n✅ 诊断完成！');
console.log('💡 结果已保存到 window.diagnosticResults，可以访问查看');
console.log('💡 例如: window.diagnosticResults.foundContainers');
