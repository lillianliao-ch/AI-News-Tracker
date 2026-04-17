// 脉脉消息列表针对性诊断脚本
// 基于原始工作版本的对比分析

(function() {
    console.log('🔍 脉脉消息列表针对性诊断\n');
    console.log('当前页面:', window.location.href);
    console.log('页面标题:', document.title);
    console.log('');

    // ============ 关键检查 1: 页面是否真的加载完成 ============
    console.log('1️⃣ 页面加载状态检查:');

    // 检查脉脉的 React 应用是否已挂载
    const rootElement = document.querySelector('#root, #app, [data-reactroot], [data-reactroot]');
    console.log('  - React Root 元素:', rootElement ? '✅ 找到' : '❌ 未找到');

    if (rootElement) {
        console.log('  - Root HTML 长度:', rootElement.innerHTML.length);
        console.log('  - Root 子元素数:', rootElement.children.length);

        // 检查 root 的前5个子元素
        console.log('  - Root 前5个子元素:');
        Array.from(rootElement.children).slice(0, 5).forEach((child, i) => {
            console.log(`    ${i + 1}. ${child.tagName}.${child.className?.substring(0, 50) || '(无class)'}`);
        });
    }

    console.log('');

    // ============ 关键检查 2: 检查原始选择器 ============
    console.log('2️⃣ 原始选择器检查 (这些是3月29日工作时的选择器):');

    const originalSelectors = [
        '.virtualized-message-list',
        '.ReactVirtualized__Grid',
        '.ReactVirtualized__List',
        '[class*="message-list"]'
    ];

    originalSelectors.forEach(selector => {
        try {
            const element = document.querySelector(selector);
            if (element) {
                console.log(`  ✅ "${selector}": 找到!`);
                console.log(`     - 子元素数: ${element.children.length}`);
                console.log(`     - 滚动高度: ${element.scrollHeight}`);
                console.log(`     - 可见高度: ${element.clientHeight}`);
            } else {
                console.log(`  ❌ "${selector}": 未找到`);
            }
        } catch (e) {
            console.log(`  ⚠️  "${selector}": 错误 - ${e.message}`);
        }
    });

    console.log('');

    // ============ 关键检查 3: 检查是否在正确的页面 ============
    console.log('3️⃣ 页面类型检查:');

    const url = window.location.href;
    const isImPage = url.includes('/im') || url.includes('message') || url.includes('chat');
    const isMaimai = url.includes('maimai.cn');

    console.log('  - 是否脉脉网站:', isMaimai ? '✅' : '❌');
    console.log('  - 是否IM页面:', isImPage ? '✅' : '❌');
    console.log('  - URL 路径:', window.location.pathname);

    // 检查是否有消息相关的标识
    const bodyClass = document.body.className;
    console.log('  - Body class:', bodyClass || '(无)');

    if (bodyClass) {
        const hasImClass = bodyClass.includes('im') || bodyClass.includes('message') || bodyClass.includes('chat');
        console.log('  - Body class 包含 IM 关键词:', hasImClass ? '✅' : '❌');
    }

    console.log('');

    // ============ 关键检查 4: 检查页面 DOM 的完整度 ============
    console.log('4️⃣ 页面 DOM 完整度检查:');

    const allDivs = document.querySelectorAll('div');
    const allUl = document.querySelectorAll('ul');
    const allLi = document.querySelectorAll('li');
    const allSpans = document.querySelectorAll('span');
    const allButtons = document.querySelectorAll('button');

    console.log('  - div 数量:', allDivs.length);
    console.log('  - ul 数量:', allUl.length);
    console.log('  - li 数量:', allLi.length);
    console.log('  - span 数量:', allSpans.length);
    console.log('  - button 数量:', allButtons.length);

    // 判断 DOM 是否过于简单
    if (allDivs.length < 100) {
        console.log('  ⚠️  DOM 元素数量异常少！页面可能:');
        console.log('     1. 还在加载中');
        console.log('     2. 使用了虚拟化 (只有可见的元素)');
        console.log('     3. 使用了 Shadow DOM 或 iframe');
        console.log('     4. 页面结构发生了重大变化');
    } else {
        console.log('  ✅ DOM 元素数量正常');
    }

    console.log('');

    // ============ 关键检查 5: 检查是否有 React Virtualized ============
    console.log('5️⃣ React Virtualized 检查:');

    // 检查是否有 React Virtualized 的特征
    const reactVirtualizedElements = document.querySelectorAll('[class*="ReactVirtualized"]');
    console.log('  - ReactVirtualized 元素:', reactVirtualizedElements.length);

    if (reactVirtualizedElements.length > 0) {
        console.log('  ✅ 找到 React Virtualized 元素:');
        reactVirtualizedElements.slice(0, 3).forEach((el, i) => {
            console.log(`    ${i + 1}. ${el.className}`);
        });
    } else {
        console.log('  ❌ 未找到 React Virtualized 元素');
        console.log('  💡 这可能意味着:');
        console.log('     1. 脉脉不再使用 React Virtualized');
        console.log('     2. 使用了其他虚拟化库');
        console.log('     3. 页面结构发生了根本性变化');
    }

    console.log('');

    // ============ 关键检查 6: 检查页面内容 ============
    console.log('6️⃣ 页面内容检查:');

    // 检查页面文本
    const bodyText = document.body.textContent || '';
    const hasMessageKeywords = bodyText.includes('消息') || bodyText.includes('会话') || bodyText.includes('聊天');
    const hasContactKeywords = bodyText.includes('联系人') || bodyText.includes('候选人');

    console.log('  - 包含"消息"/"会话"/"聊天":', hasMessageKeywords ? '✅' : '❌');
    console.log('  - 包含"联系人"/"候选人":', hasContactKeywords ? '✅' : '❌');

    // 检查是否有时间相关的文本
    const timePattern = /刚刚|分钟前|小时前|昨天|前天|\d{1,2}:\d{2}|\d{1,2}\/\d{1,2}/;
    const hasTimeText = timePattern.test(bodyText);
    console.log('  - 包含时间文本:', hasTimeText ? '✅' : '❌');

    if (!hasMessageKeywords && !hasContactKeywords) {
        console.log('  ⚠️  页面可能没有加载任何消息内容！');
    }

    console.log('');

    // ============ 关键检查 7: 检查是否有加载指示器 ============
    console.log('7️⃣ 加载状态检查:');

    // 查找加载相关的元素
    const loadingKeywords = ['loading', 'spinner', '正在加载', '加载中', '请稍候'];
    let foundLoading = false;

    loadingKeywords.forEach(keyword => {
        const elements = document.querySelectorAll(`[class*="${keyword}"], [id*="${keyword}"]`);
        if (elements.length > 0) {
            console.log(`  ⚠️  找到加载相关元素: "${keyword}" (${elements.length}个)`);
            foundLoading = true;
        }
    });

    // 检查是否有全屏遮罩
    const overlays = document.querySelectorAll('[class*="overlay"], [class*="mask"], [class*="modal"]');
    if (overlays.length > 0) {
        console.log(`  ⚠️  找到 ${overlays.length} 个遮罩层，可能阻止了页面加载`);
    }

    if (!foundLoading && overlays.length === 0) {
        console.log('  ✅ 没有明显的加载指示器或遮罩');
    }

    console.log('');

    // ============ 关键检查 8: 检查网络请求 ============
    console.log('8️⃣ 网络请求检查:');

    // 检查 Performance API
    if (window.performance && window.performance.getEntriesByType) {
        const resources = window.performance.getEntriesByType('resource');
        const apiRequests = resources.filter(r => r.name.includes('api') || r.name.includes('data'));

        console.log('  - 总请求数:', resources.length);
        console.log('  - API 请求数:', apiRequests.length);

        if (apiRequests.length > 0) {
            console.log('  - 最近的 API 请求:');
            apiRequests.slice(-3).forEach(req => {
                console.log(`    • ${req.name.substring(0, 80)}`);
            });
        }
    }

    console.log('');

    // ============ 最终诊断 ============
    console.log('9️⃣ 最终诊断:\n');

    let issues = [];
    let recommendations = [];

    // 分析 DOM 数量
    if (allDivs.length < 100) {
        issues.push('DOM 元素数量异常少');
        recommendations.push('等待页面完全加载后再试');
        recommendations.push('检查是否有网络问题导致内容加载失败');
        recommendations.push('尝试刷新页面 (F5)');
    }

    // 分析选择器
    const allFound = originalSelectors.every(sel => {
        try {
            return document.querySelector(sel) === null;
        } catch (e) {
            return true;
        }
    });

    if (allFound) {
        issues.push('所有原始选择器都失效');
        recommendations.push('运行 enhanced_diagnose_maimai.js 获取更详细的分析');
        recommendations.push('检查脉脉是否更新了页面结构');
        recommendations.push('提供当前页面的截图或 HTML 结构');
    }

    // 分析内容
    if (!hasMessageKeywords && !hasContactKeywords) {
        issues.push('页面没有消息相关内容');
        recommendations.push('确认是否在正确的页面 (招聘消息页面)');
        recommendations.push('检查是否需要登录才能查看消息');
        recommendations.push('尝试手动滚动页面，看是否能触发内容加载');
    }

    if (issues.length > 0) {
        console.log('  ⚠️  发现问题:');
        issues.forEach(issue => console.log(`     • ${issue}`));

        console.log('\n  💡 建议:');
        recommendations.forEach(rec => console.log(`     • ${rec}`));
    } else {
        console.log('  ✅ 未发现明显问题');
        console.log('  💡 可能的原因:');
        console.log('     1. 页面使用了动态渲染，需要等待或交互');
        console.log('     2. 消息在 Shadow DOM 或 iframe 中');
        console.log('     3. 需要运行更详细的诊断脚本');
    }

    console.log('\n');

    // ============ 保存结果 ============
    window.targetedDiagnosticResults = {
        url: window.location.href,
        title: document.title,
        domCounts: {
            div: allDivs.length,
            ul: allUl.length,
            li: allLi.length,
            span: allSpans.length,
            button: allButtons.length
        },
        selectorsFound: originalSelectors.map(sel => {
            try {
                return { selector: sel, found: document.querySelector(sel) !== null };
            } catch (e) {
                return { selector: sel, found: false, error: e.message };
            }
        }),
        hasReactRoot: !!rootElement,
        hasReactVirtualized: reactVirtualizedElements.length > 0,
        hasMessageContent: hasMessageKeywords || hasContactKeywords,
        issues: issues,
        recommendations: recommendations
    };

    console.log('💾 诊断结果已保存到 window.targetedDiagnosticResults');

})();
