// 脉脉消息列表增强诊断脚本 v2
// 请确保在脉脉招聘消息页面运行此脚本

(function() {
    console.log('🔍 脉脉消息列表增强诊断 v2\n');
    console.log('当前页面:', window.location.href);
    console.log('页面标题:', document.title);
    console.log('');

    // 1. 基础检查
    console.log('1️⃣ 基础信息:');
    console.log('  - readyState:', document.readyState);
    console.log('  - body 子元素数量:', document.body.children.length);
    console.log('  - document 高度:', document.body.scrollHeight);
    console.log('  - 所有 div 数量:', document.querySelectorAll('div').length);
    console.log('');

    // 2. 等待页面完全加载
    if (document.readyState !== 'complete') {
        console.log('⚠️  页面未完全加载，请等待页面完全加载后再试');
        return;
    }

    // 3. 检查是否在正确的页面
    const isImPage = window.location.href.includes('/im') ||
                     window.location.href.includes('message') ||
                     window.location.href.includes('chat');

    console.log('2️⃣ 页面类型:', isImPage ? '✅ IM/消息页面' : '❌ 不是IM页面');

    if (!isImPage) {
        console.log('\n❌ 请确保在脉脉招聘消息页面运行此脚本');
        return;
    }

    console.log('');

    // 4. 检查 Shadow DOM
    console.log('3️⃣ 检查 Shadow DOM:');
    const allElements = document.querySelectorAll('*');
    let shadowCount = 0;
    const shadowHosts = [];

    allElements.forEach(el => {
        if (el.shadowRoot) {
            shadowCount++;
            shadowHosts.push({
                tagName: el.tagName,
                className: el.className,
                id: el.id
            });
        }
    });

    if (shadowCount > 0) {
        console.log(`  ✅ 找到 ${shadowCount} 个 Shadow DOM:`);
        shadowHosts.slice(0, 5).forEach((host, i) => {
            console.log(`    ${i + 1}. ${host.tagName}.${host.className} #${host.id}`);
        });
    } else {
        console.log('  - 未使用 Shadow DOM');
    }

    console.log('');

    // 5. 检查 iframe
    console.log('4️⃣ 检查 iframe:');
    const iframes = document.querySelectorAll('iframe');
    console.log(`  - 找到 ${iframes.length} 个 iframe`);

    if (iframes.length > 0) {
        iframes.forEach((frame, i) => {
            console.log(`  ${i + 1}. src="${frame.src.substring(0, 100)}"`);
        });
    }

    console.log('');

    // 6. 查找所有包含消息相关文本的元素
    console.log('5️⃣ 查找包含消息/会话相关文本的元素:');

    const messageKeywords = ['消息', '会话', '聊天', '对话', '联系人', '候选人'];
    const foundByText = [];

    messageKeywords.forEach(keyword => {
        const xpath = `//*[contains(text(), '${keyword}')][not(ancestor-or-self::script)]`;
        const elements = document.evaluate(xpath, document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);

        if (elements.snapshotLength > 0) {
            console.log(`  ✅ 找到包含"${keyword}"的元素: ${elements.snapshotLength}个`);
            for (let i = 0; i < Math.min(3, elements.snapshotLength); i++) {
                const el = elements.snapshotItem(i);
                console.log(`    - ${el.tagName}.${el.className} "${el.textContent.substring(0, 50)}..."`);
                foundByText.push(el);
            }
        }
    });

    console.log('');

    // 7. 从找到的文本元素向上查找容器
    if (foundByText.length > 0) {
        console.log('6️⃣ 从消息文本元素向上查找可能的容器:');

        foundByText.slice(0, 2).forEach((textEl, idx) => {
            console.log(`\n  从元素 ${idx + 1} 向上查找:`);
            let parent = textEl.parentElement;
            let level = 1;

            while (parent && level <= 15) {
                const info = {
                    level,
                    tagName: parent.tagName,
                    className: parent.className ? parent.className.substring(0, 80) : '(无)',
                    id: parent.id || '(无)',
                    childCount: parent.children.length,
                    scrollHeight: parent.scrollHeight,
                    clientHeight: parent.clientHeight
                };

                console.log(`    第${level}级:`, info);

                // 如果这个元素有多个子元素，可能是列表容器
                if (parent.children.length >= 5) {
                    console.log(`      🎯 这可能是列表容器!`);
                    console.log(`      建议选择器: ${parent.id ? '#' + parent.id : (parent.className ? '.' + parent.className.split(' ')[0] : parent.tagName.toLowerCase())}`);

                    // 显示前3个子元素
                    console.log(`      子元素示例:`);
                    Array.from(parent.children).slice(0, 3).forEach((child, i) => {
                        const childText = child.textContent?.trim().substring(0, 30);
                        console.log(`        ${i + 1}. ${child.tagName}.${child.className?.substring(0, 50)} "${childText || '(空)'}"`);
                    });

                    break;
                }

                parent = parent.parentElement;
                level++;
            }
        });

        console.log('');
    }

    // 7. 查找所有可能包含头像的容器（脉脉消息通常有头像）
    console.log('7️⃣ 查找包含多个头像的容器:');

    const avatarSelectors = [
        'img[src*="avatar"]',
        'img[src*="avatar"]',
        'img[class*="avatar"]',
        'img[class*="Avatar"]',
        'img[alt*="头像"]',
        '.avatar',
        '.user-avatar',
        '[class*="user-avatar"]',
        '[class*="UserAvatar"]'
    ];

    let avatarElements = [];
    avatarSelectors.forEach(selector => {
        try {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                console.log(`  ✅ "${selector}": ${elements.length}个`);
                avatarElements = avatarElements.concat(Array.from(elements).slice(0, 10));
            }
        } catch (e) {
            // 忽略无效选择器
        }
    });

    if (avatarElements.length > 0) {
        console.log(`\n  找到 ${avatarElements.length} 个头像元素，向上查找容器:`);

        avatarElements.slice(0, 2).forEach((avatarEl, idx) => {
            console.log(`\n  从头像 ${idx + 1} 向上查找:`);
            let parent = avatarEl.parentElement;
            let level = 1;

            while (parent && level <= 10) {
                if (parent.children.length >= 5) {
                    console.log(`    第${level}级: 🎯 可能的列表容器`);
                    console.log(`      - ${parent.tagName}.${parent.className ? parent.className.substring(0, 80) : '(无)'}`);
                    console.log(`      - 子元素数: ${parent.children.length}`);
                    console.log(`      - 建议选择器: ${parent.id ? '#' + parent.id : (parent.className ? '.' + parent.className.split(' ')[0] : parent.tagName.toLowerCase())}`);
                    break;
                }
                parent = parent.parentElement;
                level++;
            }
        });
    }

    console.log('');

    // 8. 查找所有可能包含时间戳的元素
    console.log('8️⃣ 查找包含时间戳的元素:');

    const timePatterns = [
        '刚刚', '分钟前', '小时前', '昨天', '前天',
        /\d{1,2}:\d{2}/,  // 12:09
        /\d{1,2}\/\d{1,2}/  // 03/25
    ];

    const timeElements = [];

    allElements.forEach(el => {
        const text = el.textContent?.trim();
        if (!text || text.length > 50) return;

        const isTime = timePatterns.some(pattern => {
            if (typeof pattern === 'string') {
                return text === pattern || text.includes(pattern);
            } else {
                return pattern.test(text);
            }
        });

        if (isTime) {
            timeElements.push(el);
        }
    });

    console.log(`  找到 ${timeElements.length} 个时间元素`);

    if (timeElements.length > 0) {
        console.log('\n  前3个时间元素:');
        timeElements.slice(0, 3).forEach((el, i) => {
            console.log(`    ${i + 1}. "${el.textContent.trim()}"`);
            console.log(`       - 父级: ${el.parentElement?.tagName}.${el.parentElement?.className?.substring(0, 50) || '(无)'}`);
        });

        // 从第一个时间元素向上查找
        const firstTimeEl = timeElements[0];
        console.log('\n  从第一个时间元素向上查找容器:');

        let parent = firstTimeEl.parentElement;
        let level = 1;

        while (parent && level <= 15) {
            if (parent.children.length >= 5) {
                console.log(`    第${level}级: 🎯 可能的列表容器`);
                console.log(`      - ${parent.tagName}.${parent.className ? parent.className.substring(0, 80) : '(无)'}`);
                console.log(`      - 子元素数: ${parent.children.length}`);
                console.log(`      - 建议选择器: ${parent.id ? '#' + parent.id : (parent.className ? '.' + parent.className.split(' ')[0] : parent.tagName.toLowerCase())}`);
                break;
            }
            parent = parent.parentElement;
            level++;
        }
    }

    console.log('');

    // 9. 查找所有较大的、有滚动条的 div
    console.log('9️⃣ 查找所有有滚动条的容器:');

    const scrollableDivs = Array.from(document.querySelectorAll('div')).filter(el => {
        const style = window.getComputedStyle(el);
        const hasScroll = el.scrollHeight > el.clientHeight;
        const overflowStyle = style.overflowY === 'auto' ||
                             style.overflowY === 'scroll' ||
                             style.overflow === 'auto' ||
                             style.overflow === 'scroll';

        return hasScroll && overflowStyle && el.children.length >= 3;
    });

    console.log(`  找到 ${scrollableDivs.length} 个有滚动条的容器`);

    scrollableDivs.slice(0, 5).forEach((el, i) => {
        console.log(`\n  容器 ${i + 1}:`);
        console.log(`    - className: "${el.className ? el.className.substring(0, 100) : '(无)'}"`);
        console.log(`    - id: "${el.id || '(无)'}"`);
        console.log(`    - 子元素数: ${el.children.length}`);
        console.log(`    - 滚动高度: ${el.scrollHeight}`);
        console.log(`    - 可见高度: ${el.clientHeight}`);
        console.log(`    - 建议选择器: ${el.id ? '#' + el.id : (el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase())}`);

        // 显示前3个子元素
        console.log(`    - 前3个子元素:`);
        Array.from(el.children).slice(0, 3).forEach((child, j) => {
            const childText = child.textContent?.trim().substring(0, 30);
            console.log(`      ${j + 1}. ${child.tagName}.${child.className?.substring(0, 50) || '(无)'} "${childText || '(空)'}"`);
        });
    });

    console.log('\n');

    // 10. 尝试找到所有重复的元素（可能是列表项）
    console.log('🔟 查找重复的元素模式（可能是列表项）:');

    const allDivs = Array.from(document.querySelectorAll('div'));
    const classNameCounts = {};

    allDivs.forEach(div => {
        if (div.className) {
            const classes = div.className.split(' ').filter(c => c.length > 3);
            classes.forEach(cls => {
                if (!classNameCounts[cls]) {
                    classNameCounts[cls] = 0;
                }
                classNameCounts[cls]++;
            });
        }
    });

    // 找出出现次数最多的 class（可能是列表项）
    const sortedClasses = Object.entries(classNameCounts)
        .sort((a, b) => b[1] - a[1])
        .filter(([cls, count]) => count >= 5 && count <= 100); // 过滤掉太少或太多的

    console.log(`  找到 ${sortedClasses.length} 个可能的列表项 class:`);

    sortedClasses.slice(0, 10).forEach(([cls, count], i) => {
        console.log(`    ${i + 1}. .${cls} (${count}次)`);

        // 查找第一个使用这个 class 的元素
        const firstEl = document.querySelector(`.${cls}`);
        if (firstEl) {
            console.log(`       - 示例: ${firstEl.tagName} "${firstEl.textContent?.trim().substring(0, 30)}..."`);

            // 向上查找父容器
            let parent = firstEl.parentElement;
            let level = 1;
            while (parent && level <= 5) {
                if (parent.children.length >= 5) {
                    console.log(`       - 可能的父容器 (第${level}级): .${parent.className?.split(' ')[0] || parent.tagName.toLowerCase()}`);
                    break;
                }
                parent = parent.parentElement;
                level++;
            }
        }
    });

    console.log('\n');

    // 11. 最终建议
    console.log('🎯 诊断建议:');

    if (scrollableDivs.length > 0) {
        console.log('  ✅ 找到了有滚动条的容器，这很可能是消息列表!');
        console.log('  💡 请查看上面的"容器 1"、"容器 2"等信息');
        console.log('  💡 记录 className 或 id，然后反馈给开发者');
    } else if (sortedClasses.length > 0) {
        console.log('  ✅ 找到了重复的元素模式');
        console.log('  💡 请查看上面的"找到 X 个可能的列表项 class"部分');
        console.log('  💡 记录出现次数最多的 className');
    } else {
        console.log('  ❌ 未找到明确的容器元素');
        console.log('  💡 可能的原因:');
        console.log('     1. 页面还在加载中，请等待几秒后重试');
        console.log('     2. 需要滚动页面才能加载消息列表');
        console.log('     3. 消息列表在 Shadow DOM 或 iframe 中');
        console.log('     4. 页面结构发生了根本性变化');
    }

    console.log('\n');

    // 12. 保存结果到全局变量
    window.diagnosticResults = {
        url: window.location.href,
        title: document.title,
        readyState: document.readyState,
        bodyChildrenCount: document.body.children.length,
        allDivsCount: allDivs.length,
        shadowHosts: shadowHosts,
        iframeCount: iframes.length,
        scrollableDivs: scrollableDivs.map(el => ({
            className: el.className,
            id: el.id,
            childCount: el.children.length,
            scrollHeight: el.scrollHeight,
            clientHeight: el.clientHeight,
            suggestedSelector: el.id ? '#' + el.id : (el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase())
        })),
        repeatingClasses: sortedClasses.slice(0, 10).map(([cls, count]) => ({ className: cls, count })),
        timeElementsCount: timeElements.length,
        avatarElementsCount: avatarElements.length,
    };

    console.log('💾 诊断结果已保存到 window.diagnosticResults');
    console.log('💡 可以通过以下方式查看:');
    console.log('   window.diagnosticResults.scrollableDivs');
    console.log('   window.diagnosticResults.repeatingClasses');
    console.log('   window.diagnosticResults.shadowHosts');

    console.log('\n✅ 诊断完成！');

})();
