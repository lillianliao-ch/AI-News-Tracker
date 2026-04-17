// 脉脉消息列表深度诊断脚本
// 请确保在脉脉招聘消息页面运行此脚本

(function() {
    console.log('🔍 脉脉消息列表深度诊断\n');
    console.log('当前页面:', window.location.href);
    console.log('页面标题:', document.title);
    console.log('');

    // 1. 检查页面是否完全加载
    console.log('1️⃣ 页面加载状态:');
    console.log('  - readyState:', document.readyState);
    console.log('  - body 子元素数量:', document.body.children.length);
    console.log('  - document 高度:', document.body.scrollHeight);
    console.log('');

    // 2. 等待页面加载
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
        console.log('');
        console.log('❌ 请确保在脉脉招聘消息页面运行此脚本');
        console.log('   正确的URL应该包含: /im');
        console.log('   请导航到: https://maimai.cn/ent/v41/im');
        return;
    }

    console.log('');

    // 4. 检查是否有任何 div
    const allDivs = document.querySelectorAll('div');
    console.log('3️⃣ 页面元素统计:');
    console.log('  - 总 div 数量:', allDivs.length);
    console.log('  - 总 ul 数量:', document.querySelectorAll('ul').length);
    console.log('  - 总 li 数量:', document.querySelectorAll('li').length);
    console.log('');

    // 5. 查找所有可能包含消息的容器
    console.log('4️⃣ 查找消息相关元素:');

    const messageKeywords = [
        'message', 'msg', 'chat', 'conversation', 'dialogue', 'im',
        'session', 'talk', 'contact', 'candidate', 'talent'
    ];

    const messageElements = [];
    messageKeywords.forEach(keyword => {
        const elements = document.querySelectorAll(`[class*="${keyword}"], [id*="${keyword}"]`);
        if (elements.length > 0) {
            console.log(`  ✅ 找到包含 "${keyword}" 的元素: ${elements.length} 个`);
            messageElements.push(...Array.from(elements).slice(0, 2)); // 只保存前2个
        }
    });

    if (messageElements.length === 0) {
        console.log('  ❌ 未找到任何消息相关元素');
    }

    console.log('');

    // 6. 检查是否有 Shadow DOM
    console.log('5️⃣ 检查 Shadow DOM:');
    const shadowHosts = document.querySelectorAll('*');
    let shadowCount = 0;
    shadowHosts.forEach(el => {
        if (el.shadowRoot) {
            shadowCount++;
            console.log(`  ✅ 找到 Shadow DOM:`, el.tagName, el.className);
        }
    });

    if (shadowCount === 0) {
        console.log('  - 未使用 Shadow DOM');
    }

    console.log('');

    // 7. 检查是否有 iframe
    console.log('6️⃣ 检查 iframe:');
    const iframes = document.querySelectorAll('iframe');
    console.log(`  - 找到 ${iframes.length} 个 iframe`);

    if (iframes.length > 0) {
        iframes.forEach((frame, i) => {
            console.log(`  ${i + 1}. src="${frame.src}"`);
        });
    }

    console.log('');

    // 8. 查找所有较大的 div（可能是容器）
    console.log('7️⃣ 查找可能的容器元素:');

    const largeDivs = Array.from(document.querySelectorAll('div')).filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.height > 200 && el.children.length >= 3;
    });

    console.log(`  - 找到 ${largeDivs.length} 个大型 div`);

    largeDivs.slice(0, 5).forEach((el, i) => {
        console.log(`\n  容器 ${i + 1}:`);
        console.log(`    - class: "${el.className.substring(0, 100)}${el.className.length > 100 ? '...' : ''}"`);
        console.log(`    - id: "${el.id || '(无)'}"`);
        console.log(`    - 子元素数: ${el.children.length}`);
        console.log(`    - 高度: ${el.getBoundingClientRect().height}`);

        // 显示前3个子元素
        console.log(`    - 前3个子元素:`);
        Array.from(el.children).slice(0, 3).forEach((child, j) => {
            const childText = child.textContent?.trim().substring(0, 50);
            console.log(`      ${j + 1}. ${child.tagName}.${child.className || '(无class)'} "${childText || '(空)'}"`);
        });
    });

    console.log('\n');

    // 9. 查找所有文本内容，看是否有"消息"、"聊天"等
    console.log('8️⃣ 搜索页面文本内容:');

    const bodyText = document.body.textContent || '';
    const keywords = ['消息', '聊天', '对话', '沟通', '联系人', '候选人'];

    keywords.forEach(keyword => {
        if (bodyText.includes(keyword)) {
            console.log(`  ✅ 页面包含: "${keyword}"`);
        }
    });

    console.log('\n');

    // 10. 最终建议
    console.log('9️⃣ 诊断建议:');

    if (largeDivs.length === 0) {
        console.log('  ❌ 未找到任何容器元素');
        console.log('  💡 可能的原因:');
        console.log('     1. 页面还在加载中，请等待几秒后重试');
        console.log('     2. 需要滚动页面才能加载消息列表');
        console.log('     3. 页面结构发生了根本性变化');
    } else {
        console.log('  ✅ 找到了一些容器元素');
        console.log('  💡 建议:');
        console.log('     1. 查看上面的"容器 1"、"容器 2"等信息');
        console.log('     2. 找到包含多个子元素的容器');
        console.log('     3. 记录该容器的 class 名称');
        console.log('     4. 将该 class 名称反馈给开发者');
    }

    console.log('\n');

    // 11. 尝试触发页面滚动
    console.log('🔧 尝试自动滚动页面以加载更多内容...');

    let scrollCount = 0;
    const maxScrolls = 3;

    const scrollInterval = setInterval(() => {
        if (scrollCount >= maxScrolls) {
            clearInterval(scrollInterval);
            console.log('✅ 滚动完成，请重新运行诊断脚本');
            return;
        }

        window.scrollBy(0, 500);
        scrollCount++;

        console.log(`  滚动 ${scrollCount}/${maxScrolls}...`);

        // 检查是否有新内容加载
        setTimeout(() => {
            const newDivCount = document.querySelectorAll('div').length;
            if (newDivCount > allDivs.length) {
                console.log(`  ✅ 检测到新内容加载! (div: ${allDivs.length} → ${newDivCount})`);
            }
        }, 1000);

    }, 2000);

    // 保存结果到全局变量
    window.diagnosticResults = {
        url: window.location.href,
        title: document.title,
        readyState: document.readyState,
        bodyChildrenCount: document.body.children.length,
        allDivsCount: allDivs.length,
        largeDivs: largeDivs.map(el => ({
            className: el.className,
            id: el.id,
            childCount: el.children.length,
            height: el.getBoundingClientRect().height,
        })),
        messageElementsCount: messageElements.length,
    };

    console.log('\n💾 诊断结果已保存到 window.diagnosticResults');
    console.log('💡 可以通过以下方式查看:');
    console.log('   window.diagnosticResults.largeDivs');
    console.log('   window.diagnosticResults.messageElementsCount');

})();
