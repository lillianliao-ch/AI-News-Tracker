// 社区搜索页 - 批量搜索引擎（从 maimai-scraper 迁移 + 模块化）
class SearchEngine {
    constructor() {
        this.extractor = new SearchExtractor();
        this.state = {
            list: [],
            index: 0,
            running: false,
            results: [],
            mode: 'first',      // first | all
            addFriend: false,
            exportMode: 'excel', // excel | api
        };
        this._loadState();
    }

    _loadState() {
        try {
            const saved = localStorage.getItem('maimai_search_state');
            if (saved) {
                const parsed = JSON.parse(saved);
                Object.assign(this.state, parsed);
            }
        } catch (e) { }
    }

    _saveState() {
        try {
            localStorage.setItem('maimai_search_state', JSON.stringify(this.state));
        } catch (e) { }
    }

    // 开始批量搜索
    async start(keywords, mode = 'first', addFriend = false, exportMode = 'excel') {
        if (!keywords || keywords.length === 0) {
            console.log('[搜索引擎] 无关键词');
            return;
        }

        this.state.list = keywords;
        this.state.index = 0;
        this.state.running = true;
        this.state.results = [];
        this.state.mode = mode;
        this.state.addFriend = addFriend;
        this.state.exportMode = exportMode;
        this._saveState();

        console.log(`[搜索引擎] 开始搜索 ${keywords.length} 个关键词, 模式=${mode}, 加好友=${addFriend}`);

        this._onProgress?.({
            isRunning: true,
            currentIndex: 0,
            total: keywords.length,
            successful: 0,
            failed: 0,
            resultCount: 0,
        });

        await this._processNext();
    }

    stop() {
        this.state.running = false;
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
        };
        localStorage.removeItem('maimai_search_state');
    }

    // 处理下一个关键词
    async _processNext() {
        if (!this.state.running || this.state.index >= this.state.list.length) {
            this.state.running = false;
            this._saveState();
            this._onComplete?.(this.state.results);
            return;
        }

        const query = this.state.list[this.state.index];
        console.log(`[搜索引擎] 搜索 ${this.state.index + 1}/${this.state.list.length}: "${query}"`);

        // 导航到搜索页
        const searchUrl = `https://maimai.cn/web/search_center?type=contact&query=${encodeURIComponent(query)}&highlight=true`;

        if (!window.location.href.includes(`query=${encodeURIComponent(query)}`)) {
            window.location.href = searchUrl;
            // 页面会重载，后续由 resumeIfRunning() 继续
            return;
        }

        // 等待搜索结果加载
        await new Promise(r => setTimeout(r, 2000));

        const results = this.extractor.getCurrentPageResults();

        if (results.length === 0) {
            // 无结果
            this.state.results.push({
                query,
                name: query,
                company: '',
                position: '',
                workHistory: [],
                education: [],
                profileUrl: '',
                searchStatus: 'no_result',
            });
        } else {
            const mode = this.state.mode;
            const toProcess = mode === 'first' ? [results[0]] : results;

            for (const el of toProcess) {
                const cardInfo = this.extractor.extractCardInfo(el);

                // 尝试加好友
                if (this.state.addFriend) {
                    await this.extractor.tryAddFriend(el);
                    await new Promise(r => setTimeout(r, 1000));
                }

                this.state.results.push({
                    query,
                    ...cardInfo,
                    searchStatus: 'found',
                });
            }
        }

        this.state.index++;
        this._saveState();

        this._onProgress?.({
            isRunning: this.state.running,
            currentIndex: this.state.index,
            total: this.state.list.length,
            successful: this.state.results.filter(r => r.searchStatus === 'found').length,
            failed: this.state.results.filter(r => r.searchStatus === 'no_result').length,
            resultCount: this.state.results.length,
        });

        // 延迟后处理下一个
        const delay = 2000 + Math.random() * 3000;
        await new Promise(r => setTimeout(r, delay));
        await this._processNext();
    }

    // 页面重载后恢复搜索
    resumeIfRunning() {
        if (this.state.running && this.state.index < this.state.list.length) {
            console.log('[搜索引擎] 恢复执行...');

            this._onProgress?.({
                isRunning: true,
                currentIndex: this.state.index,
                total: this.state.list.length,
                successful: this.state.results.filter(r => r.searchStatus === 'found').length,
                failed: this.state.results.filter(r => r.searchStatus === 'no_result').length,
                resultCount: this.state.results.length,
            });

            setTimeout(() => this._processNext(), 3000);
        }
    }

    // 导出为 CSV
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

        // 找最大工作/教育数
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

    // 导出到 API（导入 headhunter DB）
    async exportToAPI() {
        if (this.state.results.length === 0) return { success: 0, failed: 0 };

        const apiUrl = `${MaimaiConfig.api.baseUrl}/api/candidate/import`;
        let success = 0, failed = 0;

        for (const r of this.state.results) {
            if (r.searchStatus !== 'found') continue;

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

                if (resp.ok) {
                    success++;
                } else {
                    failed++;
                }
            } catch (e) {
                failed++;
                console.error('[搜索引擎] API导入失败:', e);
            }
        }

        return { success, failed };
    }

    // 回调设置
    onProgress(fn) { this._onProgress = fn; }
    onComplete(fn) { this._onComplete = fn; }
}

if (typeof window !== 'undefined') {
    window.SearchEngine = SearchEngine;
}

console.log('✅ Search Engine 加载完成');
