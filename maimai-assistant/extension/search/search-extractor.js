// 社区搜索页 - 数据提取器（从 maimai-scraper 迁移 + 模块化）
class SearchExtractor {
    constructor() {
        this.processedItems = new Set();
    }

    // 提取搜索结果卡片的唯一标识
    extractUniqueId(element) {
        // 方法1: 链接href
        const link = element.querySelector('a[href*="/gongsi/"], a[href*="/n/"], a[href*="mmid="]');
        if (link) return link.href;

        // 方法2: 名字+描述组合
        const name = element.querySelector('a')?.textContent?.trim();
        const desc = element.querySelector('[class*="desc"]')?.textContent?.trim();
        if (name && desc) return `${name}_${desc}`;

        // 方法3: 文本哈希
        const text = element.textContent?.trim()?.substring(0, 100);
        if (text) return text;

        return null;
    }

    // 获取当前页面搜索结果
    getCurrentPageResults() {
        const selectors = [
            '.search-list .list-item',
            '[class*="search"] [class*="item"]',
            '[class*="result"] [class*="card"]',
            '.list-wrap .list-cell',
        ];

        let results = [];
        for (const sel of selectors) {
            results = document.querySelectorAll(sel);
            if (results.length > 0) break;
        }
        return Array.from(results);
    }

    // 提取搜索结果中单个卡片的基础信息
    extractCardInfo(element) {
        const info = {
            name: '',
            company: '',
            position: '',
            profileUrl: '',
        };

        // 提取名字
        const nameLink = element.querySelector('a');
        if (nameLink) {
            const text = nameLink.textContent?.trim();
            if (text && text.length < 30) {
                info.name = text;
            }
            if (nameLink.href && nameLink.href.includes('maimai.cn')) {
                info.profileUrl = nameLink.href;
            }
        }

        // 提取公司和职位
        const descEl = element.querySelector('[class*="desc"], [class*="info"]');
        if (descEl) {
            const desc = descEl.textContent?.trim() || '';
            const parts = desc.split(/[·,，\s]+/);
            if (parts.length >= 2) {
                info.company = parts[0];
                info.position = parts[1];
            } else if (parts.length === 1) {
                info.company = parts[0];
            }
        }

        return info;
    }

    // 提取详情页完整信息 - 直接使用原始 maimai-scraper 的久经考验的逻辑
    extractDetailInfo() {
        const info = {
            name: '',
            company: '',
            position: '',
            workHistory: [],
            education: [],
        };

        try {
            console.log('[搜索助手] 开始提取详情页信息...');

            // 获取页面所有文本
            const bodyText = document.body.textContent;

            // 提取姓名 - 尝试多个选择器
            const nameCandidates = [
                document.querySelector('h1'),
                document.querySelector('[class*="name"]'),
                document.querySelector('[class*="title"]'),
                ...Array.from(document.querySelectorAll('*')).filter(el => {
                    const text = el.textContent?.trim() || '';
                    return text.length > 2 && text.length < 30 &&
                        el.children.length === 0 &&
                        !text.includes('工作') && !text.includes('教育');
                }).slice(0, 5),
            ];

            for (let el of nameCandidates) {
                if (el && el.textContent) {
                    const text = el.textContent.trim();
                    if (text && text.length > 1 && text.length < 50) {
                        info.name = text;
                        break;
                    }
                }
            }

            // ========== 提取工作经历 ==========
            const workHeaders = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, div, span, p')).filter(el => {
                const text = el.textContent?.trim() || '';
                return (text === '工作经历' || text === '工作经历：') && text.length < 20;
            });

            if (workHeaders.length > 0) {
                const workHeader = workHeaders[0];
                let currentEl = workHeader.nextElementSibling;

                if (currentEl && (currentEl.tagName === 'UL' || currentEl.tagName === 'OL')) {
                    let listItems = currentEl.querySelectorAll('li');
                    if (listItems.length === 0) {
                        listItems = Array.from(currentEl.children);
                    }

                    if (listItems.length > 0) {
                        listItems.forEach((item) => {
                            const text = item.textContent?.trim() || '';
                            if (text.length > 15 && text.length < 2000 &&
                                (text.includes('公司') || text.includes('有限') || text.includes('科技') ||
                                    text.includes('至今') || text.match(/\d{4}/))) {
                                const isDuplicate = info.workHistory.some(existing =>
                                    existing.substring(0, 30) === text.substring(0, 30)
                                );
                                if (!isDuplicate) info.workHistory.push(text);
                            }
                        });
                    } else {
                        currentEl = currentEl.nextElementSibling;
                        let iterations = 0;
                        while (currentEl && iterations < 10) {
                            iterations++;
                            const text = currentEl.textContent?.trim() || '';
                            if (text === '教育经历' || text === '自我介绍' || text === '个人信息') break;
                            const hasKeyword = text.includes('公司') || text.includes('有限') || text.includes('科技') ||
                                text.includes('至今') || text.match(/\d{4}/);
                            if (text.length > 15 && text.length < 800 && !text.startsWith('工作经历') && hasKeyword) {
                                const isDuplicate = info.workHistory.some(existing =>
                                    existing.substring(0, 30) === text.substring(0, 30)
                                );
                                if (!isDuplicate) info.workHistory.push(text);
                            }
                            currentEl = currentEl.nextElementSibling;
                        }
                    }
                } else {
                    let iterations = 0;
                    while (currentEl && iterations < 10) {
                        iterations++;
                        const text = currentEl.textContent?.trim() || '';
                        if (text === '教育经历' || text === '自我介绍' || text === '个人信息') break;
                        const hasKeyword = text.includes('公司') || text.includes('有限') || text.includes('科技') ||
                            text.includes('至今') || text.match(/\d{4}/);
                        if (text.length > 15 && text.length < 800 && !text.startsWith('工作经历') && hasKeyword) {
                            const isDuplicate = info.workHistory.some(existing =>
                                existing.substring(0, 30) === text.substring(0, 30)
                            );
                            if (!isDuplicate) info.workHistory.push(text);
                        }
                        currentEl = currentEl.nextElementSibling;
                    }
                }
            }

            // ========== 提取教育经历 ==========
            const eduHeaders = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, div, span, p')).filter(el => {
                const text = el.textContent?.trim() || '';
                return (text === '教育经历' || text === '教育经历：') && text.length < 20;
            });

            console.log('[搜索助手] 找到教育经历标题:', eduHeaders.length, '个');

            if (eduHeaders.length > 0) {
                const eduHeader = eduHeaders[0];
                let currentEl = eduHeader.nextElementSibling;

                if (currentEl && (currentEl.tagName === 'UL' || currentEl.tagName === 'OL')) {
                    let listItems = currentEl.querySelectorAll('li');
                    if (listItems.length === 0) {
                        listItems = Array.from(currentEl.children);
                    }

                    if (listItems.length > 0) {
                        listItems.forEach((item) => {
                            const text = item.textContent?.trim() || '';
                            if (text.length > 10 && text.length < 500 &&
                                (text.includes('大学') || text.includes('学院') || text.includes('本科') ||
                                    text.includes('硕士') || text.includes('博士') || text.includes('学位') ||
                                    text.match(/\d{4}年/))) {
                                const isDuplicate = info.education.some(existing =>
                                    existing.substring(0, 20) === text.substring(0, 20)
                                );
                                if (!isDuplicate) info.education.push(text);
                            }
                        });
                    } else {
                        currentEl = currentEl.nextElementSibling;
                        let iterations = 0;
                        while (currentEl && iterations < 10) {
                            iterations++;
                            const text = currentEl.textContent?.trim() || '';
                            if (text === '自我介绍' || text === '个人信息' || text === '技能特长') break;
                            const hasKeyword = text.includes('大学') || text.includes('学院') || text.includes('本科') ||
                                text.includes('硕士') || text.includes('博士') || text.includes('学位') ||
                                text.match(/\d{4}年/);
                            if (text.length > 10 && text.length < 500 && !text.startsWith('教育经历') && hasKeyword) {
                                const isDuplicate = info.education.some(existing =>
                                    existing.substring(0, 20) === text.substring(0, 20)
                                );
                                if (!isDuplicate) info.education.push(text);
                            }
                            currentEl = currentEl.nextElementSibling;
                        }
                    }
                } else {
                    let iterations = 0;
                    while (currentEl && iterations < 10) {
                        iterations++;
                        const text = currentEl.textContent?.trim() || '';
                        if (text === '自我介绍' || text === '个人信息' || text === '技能特长') break;
                        const hasKeyword = text.includes('大学') || text.includes('学院') || text.includes('本科') ||
                            text.includes('硕士') || text.includes('博士') || text.includes('学位') ||
                            text.match(/\d{4}年/);
                        if (text.length > 10 && text.length < 500 && !text.startsWith('教育经历') && hasKeyword) {
                            const isDuplicate = info.education.some(existing =>
                                existing.substring(0, 20) === text.substring(0, 20)
                            );
                            if (!isDuplicate) info.education.push(text);
                        }
                        currentEl = currentEl.nextElementSibling;
                    }
                }
            }

            // 从工作经历中提取当前公司和职位
            if (info.workHistory.length > 0) {
                const current = info.workHistory[0];
                const companyMatch = current.match(/([^\s]{2,}公司|[^\s]{2,}有限|[^\s]{2,}科技)/);
                if (companyMatch) {
                    info.company = companyMatch[0];
                }
            }

            console.log('[搜索助手] ✅ 提取完成:', info.name, '| 工作', info.workHistory.length, '条 | 教育', info.education.length, '条');

        } catch (e) {
            console.error('[搜索助手] 提取失败:', e);
        }

        return info;
    }

    // 解析工作经历文本
    parseWorkExperience(text) {
        const result = { title: '', time_range: '', content: text };

        // 提取时间范围：2020.3 - 至今
        const timeMatch = text.match(/(\d{4}[\.\-年]\d{0,2}[\.\-月]?\s*[-–—~]\s*(?:\d{4}[\.\-年]\d{0,2}[\.\-月]?|至今))/);
        if (timeMatch) result.time_range = timeMatch[1];

        // 提取标题（公司+职位）
        const lines = text.split('\n');
        if (lines.length > 0) {
            result.title = lines[0].replace(result.time_range, '').trim();
        }

        return result;
    }

    // 解析教育经历文本
    parseEducation(text) {
        const result = { school: '', time_range: '', major: '' };

        const timeMatch = text.match(/(\d{4}[\.\-年]\d{0,2}[\.\-月]?\s*[-–—~]\s*(?:\d{4}[\.\-年]\d{0,2}[\.\-月]?|至今))/);
        if (timeMatch) result.time_range = timeMatch[1];

        const schools = ['大学', '学院', 'University', 'Institute', 'College'];
        const lines = text.split(/[\n,，·]/);
        for (const line of lines) {
            if (schools.some(s => line.includes(s))) {
                result.school = line.trim();
                break;
            }
        }

        const majors = ['专业', '工程', '计算机', '数学', '物理', '电子', '信息', 'Computer', 'Science', 'Engineering'];
        for (const line of lines) {
            if (majors.some(m => line.includes(m)) && !schools.some(s => line.includes(s))) {
                result.major = line.trim();
                break;
            }
        }

        return result;
    }

    // 尝试添加好友
    async tryAddFriend(element) {
        try {
            console.log('[搜索助手] 尝试加好友...');

            // 找到"加好友"按钮（在搜索结果卡片中）
            const buttons = Array.from(element.querySelectorAll('button, div, span, a'));
            const addBtn = buttons.find(el => {
                const text = el.textContent?.trim();
                return text === '加好友' || text === '添加好友' || text === '+ 好友';
            });

            if (addBtn) {
                addBtn.click();
                await new Promise(r => setTimeout(r, 1000));
                console.log('[搜索助手] ✅ 已点击加好友');
                return true;
            }

            // 备用：通过"..."菜单
            const moreBtn = element.querySelector('[class*="more"]');
            if (moreBtn) {
                moreBtn.click();
                await new Promise(r => setTimeout(r, 800));

                const menuItems = document.querySelectorAll('*');
                for (const item of menuItems) {
                    if (item.textContent?.trim() === '加好友') {
                        const rect = item.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            item.click();
                            await new Promise(r => setTimeout(r, 500));
                            document.body.click();
                            console.log('[搜索助手] ✅ 通过菜单加好友');
                            return true;
                        }
                    }
                }
                document.body.click();
            }

            console.log('[搜索助手] ❌ 未找到加好友按钮');
            return false;
        } catch (e) {
            console.error('[搜索助手] 加好友失败:', e);
            return false;
        }
    }

    // 在详情页尝试添加好友
    async tryAddFriendOnDetailPage() {
        try {
            console.log('[搜索助手] 详情页: 尝试加好友...');

            // 查找页面上的"加好友"按钮
            const buttonSelectors = ['button', '[role="button"]', '.btn', 'div[class*="btn"]', 'a[class*="btn"]'];
            let candidates = [];

            for (const sel of buttonSelectors) {
                const buttons = Array.from(document.querySelectorAll(sel));
                const matching = buttons.filter(btn => {
                    const text = btn.textContent?.trim() || '';
                    return text.length < 30 && (
                        text.includes('加好友') ||
                        text.includes('添加好友') ||
                        text.includes('加为好友') ||
                        text === '+ 加好友' ||
                        text === '＋加好友'
                    );
                });
                candidates.push(...matching);
            }

            if (candidates.length === 0) {
                // 扩大搜索
                const allEls = Array.from(document.querySelectorAll('*'));
                candidates = allEls.filter(el => {
                    const text = el.textContent?.trim() || '';
                    return text.length < 20 && text.length > 0 && (
                        text.includes('加好友') ||
                        text.includes('添加好友') ||
                        text === '+ 加好友' ||
                        text === '＋加好友'
                    );
                });
            }

            console.log(`[搜索助手] 找到 ${candidates.length} 个加好友候选按钮`);

            if (candidates.length > 0) {
                // 按优先级排序
                candidates.sort((a, b) => {
                    const priority = (el) => {
                        let p = 0;
                        const text = el.textContent?.trim() || '';
                        if (text === '＋加好友' || text === '+加好友') p += 100;
                        else if (text.includes('加好友')) p += 80;
                        if (el.tagName === 'BUTTON') p += 50;
                        if (window.getComputedStyle(el).cursor === 'pointer') p += 30;
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) p += 10;
                        return p;
                    };
                    return priority(b) - priority(a);
                });

                const btn = candidates[0];
                console.log(`[搜索助手] 点击: "${btn.textContent?.trim()}" (${btn.tagName})`);
                btn.click();
                await new Promise(r => setTimeout(r, 2000));

                // 检查是否弹出确认对话框 → 自动点击"发送"
                const sendBtns = Array.from(document.querySelectorAll('button, [role="button"]'));
                const sendBtn = sendBtns.find(b => {
                    const t = b.textContent?.trim() || '';
                    return t === '发送' || t === '确认' || t === '确定';
                });
                if (sendBtn) {
                    sendBtn.click();
                    console.log('[搜索助手] ✅ 已点击发送/确认');
                    await new Promise(r => setTimeout(r, 1500));
                }

                // 关闭可能的弹窗
                const closeBtns = document.querySelectorAll('[class*="close"], [class*="modal"] button');
                for (const cb of closeBtns) {
                    const text = cb.textContent?.trim() || '';
                    if (text === '×' || text === '✕' || text === '关闭' || cb.getAttribute('aria-label') === 'Close') {
                        cb.click();
                        break;
                    }
                }

                console.log('[搜索助手] ✅ 详情页加好友流程完成');
                return true;
            }

            console.log('[搜索助手] ❌ 详情页未找到加好友按钮');
            return false;
        } catch (e) {
            console.error('[搜索助手] 详情页加好友失败:', e);
            return false;
        }
    }

    // 滚动加载更多
    async scrollToLoadMore() {
        const scrollContainer = document.querySelector('.search-list, [class*="list-wrap"]') || document.documentElement;
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 1500));
    }
}

if (typeof window !== 'undefined') {
    window.SearchExtractor = SearchExtractor;
}

console.log('✅ Search Extractor 加载完成');
