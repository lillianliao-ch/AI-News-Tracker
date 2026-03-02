// 社区搜索页 - 批量搜索引擎（两阶段状态机：搜索→详情→下一个）
class SearchEngine {
    constructor() {
        this.extractor = new SearchExtractor();
        this.state = {
            list: [],
            index: 0,
            running: false,
            results: [],
            mode: 'first',
            addFriend: false,
            exportMode: 'excel',
            phase: 'idle',            // idle | search | detail
            currentDetailUrl: null,   // 当前要跳转的详情页 URL
            pendingDetailUrls: [],    // "所有结果"模式：待访问的详情页队列
        };
        this._loadState();
    }

    _loadState() {
        try {
            const saved = localStorage.getItem('maimai_search_engine_state');
            if (saved) {
                const parsed = JSON.parse(saved);
                Object.assign(this.state, parsed);
            }
        } catch (e) { }
    }

    _saveState() {
        try {
            localStorage.setItem('maimai_search_engine_state', JSON.stringify(this.state));
        } catch (e) { }
    }

    // 开始批量搜索
    async start(keywords, mode = 'first', addFriend = false, exportMode = 'excel') {
        if (!keywords || keywords.length === 0) {
            console.log('[搜索引擎] 无关键词');
            return;
        }

        this.state = {
            list: keywords,
            index: 0,
            running: true,
            results: [],
            mode,
            addFriend,
            exportMode,
            phase: 'search',
            currentDetailUrl: null,
            pendingDetailUrls: [],
        };
        this._saveState();

        console.log(`[搜索引擎] 🚀 开始搜索 ${keywords.length} 个关键词, 模式=${mode}, 加好友=${addFriend}`);

        this._emitProgress();
        this._navigateToSearch(keywords[0]);
    }

    stop() {
        this.state.running = false;
        this.state.phase = 'idle';
        this._saveState();
        console.log('[搜索引擎] 已停止');
    }

    clearData() {
        this.state = {
            list: [],
            index: 0,
            running: false,
            results: [],
            mode: 'first',
            addFriend: false,
            exportMode: 'excel',
            phase: 'idle',
            currentDetailUrl: null,
            pendingDetailUrls: [],
        };
        localStorage.removeItem('maimai_search_engine_state');
    }

    // === 核心状态机：页面加载后恢复执行 ===
    resumeIfRunning() {
        if (!this.state.running) return;

        const url = window.location.href;
        const phase = this.state.phase;

        console.log(`[搜索引擎] 恢复执行 phase=${phase}, index=${this.state.index}/${this.state.list.length}`);
        console.log(`[搜索引擎] 当前URL: ${url}`);

        this._emitProgress();

        if (phase === 'search' && url.includes('/web/search_center')) {
            // 在搜索结果页 → 等待加载后提取 + 跳详情
            setTimeout(() => this._handleSearchPage(), 3000);
        } else if (phase === 'detail' && (
            url.includes('/profile/detail') ||
            url.includes('/contact/') ||
            url.includes('/card/')
        )) {
            // 在详情页 → 提取完整信息
            setTimeout(() => this._handleDetailPage(), 2000);
        } else if (phase === 'search' && (
            url.includes('/profile/detail') ||
            url.includes('/contact/') ||
            url.includes('/card/')
        )) {
            // phase 是 search 但已经在详情页了（通过点击卡片跳转）
            this.state.phase = 'detail';
            this._saveState();
            setTimeout(() => this._handleDetailPage(), 2000);
        } else {
            console.log('[搜索引擎] 当前页面与状态不匹配，等待用户操作');
        }
    }

    // 导航到搜索页
    _navigateToSearch(query) {
        const searchUrl = `https://maimai.cn/web/search_center?type=contact&query=${encodeURIComponent(query)}&highlight=true`;
        console.log(`[搜索引擎] 跳转搜索: ${query}`);
        this.state.phase = 'search';
        this._saveState();
        window.location.href = searchUrl;
    }

    // 阶段1: 处理搜索结果页
    async _handleSearchPage() {
        const query = this.state.list[this.state.index];
        console.log(`[搜索引擎] 📋 搜索页处理: "${query}" (${this.state.index + 1}/${this.state.list.length})`);

        // 如果 pendingDetailUrls 已有待处理的URL（从详情页返回的情况），直接跳转下一个
        if (this.state.pendingDetailUrls && this.state.pendingDetailUrls.length > 0) {
            const nextUrl = this.state.pendingDetailUrls[0];
            console.log(`[搜索引擎] 📋 队列中还有 ${this.state.pendingDetailUrls.length} 个结果待处理`);
            this.state.phase = 'detail';
            this.state.currentDetailUrl = nextUrl;
            this._saveState();
            setTimeout(() => {
                window.location.href = nextUrl;
            }, 1500);
            return;
        }

        // 切到"people"标签（人脉tab）
        await this._ensurePeopleTab();

        // 等待搜索结果
        await new Promise(r => setTimeout(r, 2000));

        // 获取搜索结果
        const results = this._findSearchResults();
        console.log(`[搜索引擎] 找到 ${results.length} 个搜索结果`);

        if (results.length === 0) {
            // 无结果 → 记录并跳下一个
            this.state.results.push({
                query,
                name: query,
                found: 0,
                company: '',
                position: '',
                workHistory: [],
                education: [],
                profileUrl: '',
                time: new Date().toLocaleString(),
            });
            this._advanceToNext();
            return;
        }

        // 根据模式决定处理多少结果
        const targetResults = this.state.mode === 'all' ? results : [results[0]];

        // 收集所有结果卡片的详情页 URL
        const allUrls = [];
        for (const card of targetResults) {
            const url = this._extractProfileUrl(card);
            if (url) {
                allUrls.push(url);
            } else {
                console.log('[搜索引擎] ⚠️ 某个卡片未提取到URL，跳过');
            }
        }

        console.log(`[搜索引擎] 🔗 共提取到 ${allUrls.length} 个详情页URL (模式: ${this.state.mode})`);

        if (allUrls.length === 0) {
            // 尝试点击第一个卡片（fallback）
            console.log('[搜索引擎] ⚠️ 未找到任何URL，尝试点击第一个卡片...');
            this.state.phase = 'detail';
            this.state.currentDetailUrl = 'CLICKED_CARD';
            this.state.pendingDetailUrls = [];
            this._saveState();

            const clickable = results[0].querySelector('.media-left, .cursor-pointer, a, .media-body') || results[0];
            clickable.click();

            setTimeout(() => {
                if (window.location.href.includes('/web/search_center')) {
                    console.log('[搜索引擎] ❌ 点击5秒后未跳转，跳过');
                    this.state.results.push({
                        query,
                        name: query,
                        found: 0,
                        note: '点击后未能跳转',
                        time: new Date().toLocaleString(),
                    });
                    this._advanceToNext();
                }
            }, 5000);
            return;
        }

        // 取第一个URL跳转，其余存入队列
        const firstUrl = allUrls.shift();
        this.state.pendingDetailUrls = allUrls;
        this.state.phase = 'detail';
        this.state.currentDetailUrl = firstUrl;
        this._saveState();

        console.log(`[搜索引擎] ✅ 跳转第1个详情页, 队列剩余 ${allUrls.length} 个`);
        setTimeout(() => {
            window.location.href = firstUrl;
        }, 1000);
    }

    // 阶段2: 处理详情页
    async _handleDetailPage() {
        const query = this.state.list[this.state.index];
        console.log(`[搜索引擎] 📄 详情页提取: "${query}"`);

        // 等待页面完全加载
        await new Promise(r => setTimeout(r, 2000));

        // 如果开启了加好友，先执行
        if (this.state.addFriend) {
            console.log('[搜索引擎] 🤝 尝试添加好友...');
            await this.extractor.tryAddFriendOnDetailPage();
            await new Promise(r => setTimeout(r, 3000));
        }

        // 提取详情信息
        const info = this.extractor.extractDetailInfo();
        console.log(`[搜索引擎] 提取到: name=${info.name}, work=${info.workHistory.length}条, edu=${info.education.length}条`);

        // 提取 dstu 作为 profileUrl
        const dstu = new URLSearchParams(window.location.search).get('dstu');
        const profileUrl = dstu
            ? `https://maimai.cn/profile/detail?dstu=${dstu}`
            : window.location.href;

        // 保存结果
        this.state.results.push({
            query,
            found: 1,
            name: info.name || query,
            company: info.company || '',
            position: info.position || '',
            workHistory: info.workHistory || [],
            education: info.education || [],
            profileUrl,
            time: new Date().toLocaleString(),
        });

        this.state.currentDetailUrl = null;
        this._saveState();

        this._emitProgress();

        // 检查队列中是否还有待处理的详情页
        if (this.state.pendingDetailUrls && this.state.pendingDetailUrls.length > 0) {
            const nextUrl = this.state.pendingDetailUrls.shift();
            console.log(`[搜索引擎] ➡️ 跳转下一个详情页, 队列剩余 ${this.state.pendingDetailUrls.length} 个`);
            this.state.phase = 'detail';
            this.state.currentDetailUrl = nextUrl;
            this._saveState();

            const delay = 2000 + Math.random() * 3000;
            setTimeout(() => {
                window.location.href = nextUrl;
            }, delay);
        } else {
            // 当前关键词所有结果处理完毕，跳到下一个关键词
            this._advanceToNext();
        }
    }

    // 推进到下一个关键词
    _advanceToNext() {
        this.state.index++;
        this.state.currentDetailUrl = null;
        this.state.pendingDetailUrls = [];
        this._saveState();

        this._emitProgress();

        if (this.state.index >= this.state.list.length) {
            // 全部完成
            this.state.running = false;
            this.state.phase = 'idle';
            this._saveState();
            this._onComplete?.(this.state.results);
            return;
        }

        // 延迟后搜索下一个（防反爬）
        const delay = 3000 + Math.random() * 4000;
        console.log(`[搜索引擎] 等待 ${(delay / 1000).toFixed(1)} 秒后搜索下一个...`);
        setTimeout(() => {
            this._navigateToSearch(this.state.list[this.state.index]);
        }, delay);
    }

    // 确保在"people"标签页
    async _ensurePeopleTab() {
        const tabs = document.querySelectorAll('[class*="tab"], [role="tab"]');
        for (const tab of tabs) {
            const text = tab.textContent?.trim() || '';
            if (text === '人脉' || text.includes('人脉')) {
                tab.click();
                await new Promise(r => setTimeout(r, 1000));
                console.log('[搜索引擎] 切换到人脉tab');
                return;
            }
        }
    }

    // 查找搜索结果卡片
    _findSearchResults() {
        const selectors = [
            '.list-group-item',
            '[data-testid="search-result-item"]',
            '.search-result-item',
            '.contact-item',
            '.user-item',
        ];

        for (const sel of selectors) {
            const els = document.querySelectorAll(sel);
            const filtered = Array.from(els).filter(el => {
                const text = el.textContent?.trim() || '';
                return text.length > 10 && !text.includes('推广');
            });
            if (filtered.length > 0) return filtered;
        }

        return [];
    }

    // 从卡片中提取详情页 URL
    _extractProfileUrl(element) {
        // 方法1: 找 href 中包含 dstu 的链接
        const links = element.querySelectorAll('a[href]');
        for (const link of links) {
            const href = link.href;
            if (href.includes('profile/detail') || href.includes('dstu=')) {
                return href;
            }
        }

        // 方法2: 从 data 属性中提取 dstu
        const allEls = element.querySelectorAll('*');
        for (const el of allEls) {
            for (const attr of el.attributes || []) {
                if (attr.value && attr.value.includes('dstu=')) {
                    const match = attr.value.match(/dstu=(\d+)/);
                    if (match) {
                        return `https://maimai.cn/profile/detail?dstu=${match[1]}&from=pc_web_search`;
                    }
                }
            }
        }

        // 方法3: 从 React props 中提取 dstu
        for (const el of allEls) {
            for (const key in el) {
                if (key.startsWith('__react')) {
                    try {
                        const propsStr = JSON.stringify(el[key]);
                        if (propsStr.includes('dstu')) {
                            const match = propsStr.match(/dstu['":\s]+(\d+)/);
                            if (match) {
                                return `https://maimai.cn/profile/detail?dstu=${match[1]}&from=pc_web_search`;
                            }
                        }
                    } catch (e) { }
                }
            }
        }

        return null;
    }

    // === 进度 & 回调 ===
    _emitProgress() {
        const s = this.state;
        this._onProgress?.({
            isRunning: s.running,
            currentIndex: s.index,
            total: s.list.length,
            successful: s.results.filter(r => r.found === 1).length,
            failed: s.results.filter(r => r.found === 0).length,
            resultCount: s.results.length,
        });
    }

    onProgress(fn) { this._onProgress = fn; }
    onComplete(fn) { this._onComplete = fn; }

    // === 导出 ===
    exportToCSV() {
        if (this.state.results.length === 0) return null;

        const escapeCSV = (str) => {
            if (!str) return '""';
            return '"' + String(str).replace(/"/g, '""') + '"';
        };

        const parsedResults = this.state.results.map(r => {
            const parsed = { ...r };
            parsed.parsedWork = (r.workHistory || []).map(w => this.extractor.parseWorkExperience(w));
            parsed.parsedEdu = (r.education || []).map(e => this.extractor.parseEducation(e));
            return parsed;
        });

        let csv = '姓名,工作年限';
        let maxWork = 0, maxEdu = 0;
        parsedResults.forEach(r => {
            maxWork = Math.max(maxWork, r.parsedWork.length);
            maxEdu = Math.max(maxEdu, r.parsedEdu.length);
        });

        for (let i = 0; i < maxWork; i++) csv += `,工作${i + 1}-title,工作${i + 1}-time_range`;
        for (let i = 0; i < maxEdu; i++) csv += `,教育${i + 1}-school,教育${i + 1}-time_range,教育${i + 1}-major`;
        csv += ',教育经历,工作经历,简历链接,简历来源\n';

        parsedResults.forEach(r => {
            let row = escapeCSV(r.name || '') + ',' + escapeCSV('');
            for (let i = 0; i < maxWork; i++) {
                const w = r.parsedWork[i] || {};
                row += ',' + escapeCSV(w.title || '') + ',' + escapeCSV(w.time_range || '');
            }
            for (let i = 0; i < maxEdu; i++) {
                const e = r.parsedEdu[i] || {};
                row += ',' + escapeCSV(e.school || '') + ',' + escapeCSV(e.time_range || '') + ',' + escapeCSV(e.major || '');
            }
            const allEdu = r.parsedEdu.map(e => [e.school, e.major, e.time_range ? `(${e.time_range})` : ''].filter(Boolean).join(' ')).join(' | ');
            const allWork = r.parsedWork.map(w => w.content).filter(Boolean).join('\n---\n');
            row += ',' + escapeCSV(allEdu);
            row += ',' + escapeCSV(allWork);
            row += ',' + escapeCSV(r.profileUrl || '');
            row += ',' + escapeCSV('maimai') + '\n';
            csv += row;
        });

        return '\uFEFF' + csv;
    }

    async exportToAPI() {
        if (this.state.results.length === 0) return { success: 0, failed: 0 };

        const result = await chrome.storage.local.get(['apiBaseUrl']);
        const apiBase = result.apiBaseUrl || 'http://localhost:8502';
        const apiUrl = `${apiBase}/api/candidate/import`;
        let success = 0, failed = 0;

        for (const r of this.state.results) {
            if (r.found !== 1) continue;
            try {
                const body = {
                    name: r.name || r.query,
                    currentCompany: r.company || '',
                    currentPosition: r.position || '',
                    location: '',
                    source: 'maimai_search',
                    sourceUrl: r.profileUrl || '',
                    workExperiences: (r.workHistory || []).map(w => {
                        const parsed = this.extractor.parseWorkExperience(w);
                        return {
                            company: parsed.title.split(/[·,，]/)[0] || '',
                            position: parsed.title.split(/[·,，]/)[1] || '',
                            startDate: '',
                            endDate: '',
                            duration: parsed.time_range,
                            description: parsed.content,
                        };
                    }),
                    educations: (r.education || []).map(e => {
                        const parsed = this.extractor.parseEducation(e);
                        return {
                            school: parsed.school,
                            degree: '',
                            major: parsed.major,
                            startYear: '',
                            endYear: '',
                        };
                    }),
                    projects: [],
                    skills: [],
                };

                const resp = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                });
                if (resp.ok) success++;
                else failed++;
            } catch (e) {
                failed++;
                console.error('[搜索引擎] API导入失败:', e);
            }
        }

        return { success, failed };
    }
}

if (typeof window !== 'undefined') {
    window.SearchEngine = SearchEngine;
}

console.log('✅ Search Engine v2 (两阶段状态机) 加载完成');
