// 脉脉消息列表终极诊断脚本
// 专门用于处理不在传统 DOM 中的消息

(function() {
    console.log('🔍 脉脉消息列表终极诊断\n');
    console.log('当前页面:', window.location.href);
    console.log('页面标题:', document.title);
    console.log('');

    // 1. 基础信息
    console.log('1️⃣ 基础 DOM 统计:');
    console.log('  - 所有 div:', document.querySelectorAll('div').length);
    console.log('  - 所有 ul:', document.querySelectorAll('ul').length);
    console.log('  - 所有 li:', document.querySelectorAll('li').length);
    console.log('  - 所有 iframe:', document.querySelectorAll('iframe').length);
    console.log('');

    // 2. 检查所有 iframe
    console.log('2️⃣ 检查 iframe 内容:');
    const iframes = document.querySelectorAll('iframe');
    console.log(`  找到 ${iframes.length} 个 iframe`);

    iframes.forEach((frame, i) => {
        console.log(`\n  iframe ${i + 1}:`);
        console.log(`    - src: "${frame.src.substring(0, 100)}"`);
        console.log(`    - id: "${frame.id}"`);
        console.log(`    - class: "${frame.className}"`);

        try {
            const frameDoc = frame.contentDocument || frame.contentWindow.document;
            console.log(`    - 可访问: ✅`);
            console.log(`    - 内部 div 数量: ${frameDoc.querySelectorAll('div').length}`);
            console.log(`    - 内部 ul 数量: ${frameDoc.querySelectorAll('ul').length}`);
            console.log(`    - 内部 li 数量: ${frameDoc.querySelectorAll('li').length}`);

            // 查找可能的列表容器
            const frameDivs = frameDoc.querySelectorAll('div');
            const largeFrameDivs = Array.from(frameDivs).filter(el => el.children.length >= 5);

            if (largeFrameDivs.length > 0) {
                console.log(`    - ✅ 找到 ${largeFrameDivs.length} 个大型容器:`);
                largeFrameDivs.slice(0, 3).forEach((el, j) => {
                    console.log(`        ${j + 1}. ${el.className ? el.className.substring(0, 50) : '(无class)'} (${el.children.length} 个子元素)`);
                });
            }
        } catch (e) {
            console.log(`    - 可访问: ❌ (跨域限制)`);
        }
    });

    console.log('');

    // 3. 深度检查 Shadow DOM
    console.log('3️⃣ 深度检查 Shadow DOM:');
    let shadowCount = 0;
    const shadowHosts = [];

    // 检查所有元素
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
        if (el.shadowRoot) {
            shadowCount++;
            const hostInfo = {
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                shadowChildren: el.shadowRoot.children.length,
                shadowDivs: el.shadowRoot.querySelectorAll('div').length,
                shadowUls: el.shadowRoot.querySelectorAll('ul').length,
            };
            shadowHosts.push(hostInfo);
            console.log(`  ✅ Shadow Host ${shadowCount}:`, hostInfo);

            // 检查 Shadow Root 内部的大型容器
            const shadowDivs = el.shadowRoot.querySelectorAll('div');
            const largeShadowDivs = Array.from(shadowDivs).filter(d => d.children.length >= 5);

            if (largeShadowDivs.length > 0) {
                console.log(`      → 内部有 ${largeShadowDivs.length} 个大型容器:`);
                largeShadowDivs.slice(0, 3).forEach((d, j) => {
                    console.log(`        ${j + 1}. ${d.className ? d.className.substring(0, 50) : '(无class)'} (${d.children.length} 个子元素)`);
                });
            }
        }
    });

    if (shadowCount === 0) {
        console.log('  - 未找到 Shadow DOM');
    }

    console.log('');

    // 4. 检查全局变量（React/Vue 数据）
    console.log('4️⃣ 检查全局变量和数据:');

    // 检查 React
    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
        console.log('  ✅ 检测到 React DevTools');
        const renderers = window.__REACT_DEVTOOLS_GLOBAL_HOOK__.renderers;
        if (renderers && renderers.size > 0) {
            console.log(`    - React renderers: ${renderers.size}`);
            renderers.forEach((renderer, id) => {
                console.log(`      Renderer ${id}:`, renderer);
            });
        }
    }

    // 检查 Vue
    if (window.__VUE__) {
        console.log('  ✅ 检测到 Vue');
    }

    // 检查常见的全局数据对象
    const commonGlobalKeys = [
        '__INITIAL_STATE__',
        '__INITIAL_STATE',
        'initialState',
        '__STATE__',
        '__NEXT_DATA__',
        '__NUXT__',
        'app',
        'store',
        'state',
        'messages',
        'chatData',
        'imData',
        'sessionData',
        'conversationData',
    ];

    commonGlobalKeys.forEach(key => {
        if (window[key] !== undefined) {
            const value = window[key];
            console.log(`  ✅ 找到 window.${key}:`);
            console.log(`    - 类型: ${typeof value}`);
            console.log(`    - 内容:`, typeof value === 'object' ? JSON.stringify(value).substring(0, 200) : value);
        }
    });

    console.log('');

    // 5. 检查所有 script 标签中的数据
    console.log('5️⃣ 检查 script 标签中的数据:');
    const scripts = document.querySelectorAll('script');
    console.log(`  找到 ${scripts.length} 个 script 标签`);

    scripts.forEach((script, i) => {
        const text = script.textContent;
        if (text && text.length > 100 && text.length < 50000) {
            // 查找可能包含消息数据的模式
            if (text.includes('message') || text.includes('chat') || text.includes('session') || text.includes('conversation')) {
                console.log(`\n  Script ${i + 1} (长度: ${text.length}):`);

                // 尝试提取 JSON 数据
                const jsonMatches = text.match(/\{[\s\S]*\}/g);
                if (jsonMatches) {
                    console.log(`    - 找到 ${jsonMatches.length} 个 JSON 对象`);
                    jsonMatches.slice(0, 2).forEach((json, j) => {
                        try {
                            const obj = JSON.parse(json);
                            if (obj.messages || obj.chats || obj.sessions || obj.conversations || obj.data) {
                                console.log(`    - JSON ${j + 1}:`, Object.keys(obj));
                            }
                        } catch (e) {
                            // 忽略解析错误
                        }
                    });
                }
            }
        }
    });

    console.log('');

    // 6. 检查所有可能的数据属性
    console.log('6️⃣ 检查元素的 data-* 属性:');

    const allElementsWithData = document.querySelectorAll('[data-*]');
    const elementsWithDataProps = [];

    allElements.forEach(el => {
        const dataProps = [];
        for (let attr of el.attributes) {
            if (attr.name.startsWith('data-')) {
                dataProps.push({ name: attr.name, value: attr.value });
            }
        }

        if (dataProps.length > 0) {
            elementsWithDataProps.push({
                tagName: el.tagName,
                className: el.className,
                dataProps: dataProps
            });
        }
    });

    console.log(`  找到 ${elementsWithDataProps.length} 个有 data-* 属性的元素`);

    if (elementsWithDataProps.length > 0) {
        console.log('\n  前5个:');
        elementsWithDataProps.slice(0, 5).forEach((el, i) => {
            console.log(`    ${i + 1}. ${el.tagName}.${el.className ? el.className.substring(0, 30) : '(无)'}`);
            el.dataProps.forEach(prop => {
                const valuePreview = prop.value.length > 50 ? prop.value.substring(0, 50) + '...' : prop.value;
                console.log(`       - ${prop.name}: "${valuePreview}"`);
            });
        });
    }

    console.log('');

    // 7. 检查是否有 Web Components
    console.log('7️⃣ 检查 Web Components:');

    const allCustomElements = Array.from(allElements).filter(el => {
        return el.tagName.includes('-');
    });

    console.log(`  找到 ${allCustomElements.length} 个自定义元素`);

    if (allCustomElements.length > 0) {
        console.log('\n  前10个:');
        allCustomElements.slice(0, 10).forEach((el, i) => {
            console.log(`    ${i + 1}. ${el.tagName} (class: "${el.className || '(无)'}")`);
        });
    }

    console.log('');

    // 8. 检查事件监听器
    console.log('8️⃣ 尝试查找有事件监听器的元素:');

    let elementsWithListeners = 0;
    allElements.forEach(el => {
        try {
            const events = getEventListeners ? getEventListeners(el) : null;
            if (events && Object.keys(events).length > 0) {
                elementsWithListeners++;
            }
        } catch (e) {
            // 忽略
        }
    });

    console.log(`  找到 ${elementsWithListeners} 个有事件监听器的元素`);

    console.log('');

    // 9. 最终建议
    console.log('9️⃣ 诊断总结和建议:');

    if (iframes.length > 0) {
        console.log('  ✅ 找到 iframe，消息可能在 iframe 中');
        console.log('  💡 如果 iframe 可访问，使用 contentDocument 访问其内容');
        console.log('  💡 如果 iframe 不可访问（跨域），需要使用 chrome.webNavigation 或 background script');
    } else if (shadowHosts.length > 0) {
        console.log('  ✅ 找到 Shadow DOM，消息可能在 Shadow Root 中');
        console.log('  💡 使用 element.shadowRoot 访问 Shadow DOM 内容');
        console.log('  💡 可能需要递归检查多层 Shadow DOM');
    } else {
        console.log('  ❌ 未找到 iframe 或 Shadow DOM');
        console.log('  💡 消息可能:');
        console.log('     1. 存储在 JavaScript 全局变量中（如 __INITIAL_STATE__）');
        console.log('     2. 使用 Canvas/WebGL 渲染（不传统但可能）');
        console.log('     3. 动态加载，需要滚动或点击才渲染');
        console.log('     4. 使用 Web Components（自定义元素）');
    }

    console.log('');
    console.log('🔧 下一步操作:');

    if (typeof getEventListeners !== 'undefined') {
        console.log('  1. 在页面滚动或点击后，再次运行此脚本');
        console.log('  2. 检查是否有新的元素出现');
    }

    console.log('  3. 打开 React DevTools 或 Vue DevTools 查看组件树');
    console.log('  4. 在 Console 中输入: Object.keys(window).filter(k => window[k] && typeof window[k] === "object")');
    console.log('  5. 检查 Network 标签，查看是否有 API 请求返回消息数据');

    console.log('\n');

    // 10. 尝试触发内容加载
    console.log('🚀 尝试触发内容加载...');

    // 滚动页面
    window.scrollBy(0, 500);
    console.log('  - 已向下滚动 500px');

    // 等待 2 秒后检查
    setTimeout(() => {
        console.log('\n⏰ 2秒后再次检查...');
        console.log(`  - div 数量: ${document.querySelectorAll('div').length} (之前: ${document.querySelectorAll('div').length - elementsWithListeners})`);
        console.log(`  - ul 数量: ${document.querySelectorAll('ul').length}`);
        console.log(`  - li 数量: ${document.querySelectorAll('li').length}`);

        if (document.querySelectorAll('div').length > 100) {
            console.log('\n✅ 检测到新的 div 元素！请重新运行诊断脚本');
        }
    }, 2000);

    // 保存结果
    window.ultimateDiagnosticResults = {
        url: window.location.href,
        hasIframes: iframes.length > 0,
        iframeCount: iframes.length,
        hasShadowDOM: shadowHosts.length > 0,
        shadowHostCount: shadowHosts.length,
        shadowHosts: shadowHosts,
        hasReact: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
        hasVue: !!window.__VUE__,
        customElementCount: allCustomElements.length,
        customElements: allCustomElements.slice(0, 20).map(el => el.tagName),
    };

    console.log('\n💾 结果已保存到 window.ultimateDiagnosticResults');

})();
