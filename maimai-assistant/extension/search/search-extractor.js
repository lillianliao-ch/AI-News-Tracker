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

    // 提取详情页完整信息
    extractDetailInfo() {
        const info = {
            name: '',
            company: '',
            position: '',
            workHistory: [],
            education: [],
        };

        try {
            console.log('[搜索助手] 提取详情页信息...');

            // 提取姓名
            const nameCandidates = [
                document.querySelector('h1'),
                document.querySelector('[class*="name"]'),
            ];
            for (let el of nameCandidates) {
                if (el?.textContent) {
                    const text = el.textContent.trim();
                    if (text && text.length > 1 && text.length < 50) {
                        info.name = text;
                        break;
                    }
                }
            }

            // 提取工作经历
            this._extractSection(info, '工作经历', 'workHistory');
            // 提取教育经历
            this._extractSection(info, '教育经历', 'education');

        } catch (e) {
            console.error('[搜索助手] 提取失败:', e);
        }

        return info;
    }

    // 通用段落提取
    _extractSection(info, sectionTitle, targetKey) {
        const headers = Array.from(
            document.querySelectorAll('h1, h2, h3, h4, h5, h6, div, span, p')
        ).filter(el => {
            const text = el.textContent?.trim() || '';
            return (text === sectionTitle || text === `${sectionTitle}：`) && text.length < 20;
        });

        if (headers.length === 0) return;

        const header = headers[0];
        let currentEl = header.nextElementSibling;
        let iterations = 0;

        // 处理列表元素
        if (currentEl && (currentEl.tagName === 'UL' || currentEl.tagName === 'OL')) {
            const items = currentEl.querySelectorAll('li') || currentEl.children;
            Array.from(items).forEach(item => {
                const text = item.textContent?.trim() || '';
                if (text.length > 15 && text.length < 2000) {
                    if (!info[targetKey].some(e => e.substring(0, 30) === text.substring(0, 30))) {
                        info[targetKey].push(text);
                    }
                }
            });
            return;
        }

        // 遍历兄弟元素
        const stopWords = ['教育经历', '自我介绍', '个人信息', '工作经历'];
        while (currentEl && iterations < 10) {
            iterations++;
            const text = currentEl.textContent?.trim() || '';

            if (stopWords.some(s => text === s) && text !== sectionTitle) break;

            const hasKeyword = /公司|有限|科技|至今|\d{4}/.test(text);
            if (text.length > 15 && text.length < 800 && !text.startsWith(sectionTitle) && hasKeyword) {
                if (!info[targetKey].some(e => e.substring(0, 30) === text.substring(0, 30))) {
                    info[targetKey].push(text);
                }
            }

            currentEl = currentEl.nextElementSibling;
        }
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
