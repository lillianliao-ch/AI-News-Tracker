/**
 * Maimai Job Poster - 职位发布自动化
 * 从 personal-ai-headhunter 获取 JD 数据，自动填写脉脉发布职位表单
 */

class MaimaiJobPoster {
    constructor() {
        this.config = {
            apiBaseUrl: 'http://localhost:8502',
            receiveEmail: ''
        };
        this.jobs = [];
        this.selectedJob = null;
        this.isMinimized = false;
        this.panel = null;
    }

    async init() {
        console.log('🚀 Maimai Job Poster 启动中...');

        // 加载配置
        await this.loadConfig();

        // 等待页面加载完成
        await this.waitForPageReady();

        // 创建 UI
        this.createPanel();

        // 自动加载职位列表
        await this.fetchJobs();

        console.log('✅ Maimai Job Poster 初始化完成');
    }

    async loadConfig() {
        try {
            // 优先从 chrome.storage.sync 读取（与 popup 设置一致）
            if (chrome.storage && chrome.storage.sync) {
                const syncResult = await chrome.storage.sync.get(['apiBaseUrl']);
                if (syncResult.apiBaseUrl) {
                    this.config.apiBaseUrl = syncResult.apiBaseUrl.replace(/\/+$/, '');
                }
            }
            // 再读 local 配置（邮箱等）
            const result = await chrome.storage.local.get(['mjp_config']);
            if (result.mjp_config) {
                const localConfig = result.mjp_config;
                // 邮箱从 local 读取，API URL 以 sync 为准
                if (localConfig.receiveEmail) {
                    this.config.receiveEmail = localConfig.receiveEmail;
                }
            }
        } catch (e) {
            console.log('⚠️ 加载配置失败，使用默认配置');
        }
    }

    async saveConfig() {
        try {
            await chrome.storage.local.set({ mjp_config: this.config });
        } catch (e) {
            console.error('❌ 保存配置失败:', e);
        }
    }

    waitForPageReady() {
        return new Promise(resolve => {
            if (document.readyState === 'complete') {
                setTimeout(resolve, 1500);
            } else {
                window.addEventListener('load', () => setTimeout(resolve, 1500));
            }
        });
    }

    createPanel() {
        // 移除旧面板
        const oldPanel = document.querySelector('.maimai-job-poster-panel');
        if (oldPanel) oldPanel.remove();

        const oldMinimized = document.querySelector('.maimai-job-poster-minimized');
        if (oldMinimized) oldMinimized.remove();

        // 创建面板
        this.panel = document.createElement('div');
        this.panel.className = 'maimai-job-poster-panel';
        this.panel.innerHTML = this.getPanelHTML();
        document.body.appendChild(this.panel);

        // 绑定事件
        this.bindEvents();

        // 使面板可拖拽
        this.makeDraggable();
    }

    getPanelHTML() {
        return `
            <div class="mjp-header">
                <div class="mjp-title">职位发布助手</div>
                <button class="mjp-close" title="最小化">−</button>
            </div>
            <div class="mjp-body">
                <div class="mjp-config-toggle" id="mjp-config-toggle">
                    <span>⚙️ 配置</span>
                    <span class="mjp-toggle-arrow" id="mjp-toggle-arrow">▶</span>
                </div>
                <div class="mjp-api-config" id="mjp-api-config" style="display: none;">
                    <label>API 服务地址</label>
                    <input type="text" class="mjp-api-input" id="mjp-api-url" 
                           placeholder="http://localhost:8502" 
                           value="${this.config.apiBaseUrl}">
                    <label style="margin-top: 12px;">接收简历邮箱</label>
                    <input type="email" class="mjp-api-input" id="mjp-email" 
                           placeholder="your@email.com" 
                           value="${this.config.receiveEmail}">
                </div>
                
                <div class="mjp-job-list">
                    <div class="mjp-job-list-header">
                        <span class="mjp-job-list-title">选择要发布的职位</span>
                        <button class="mjp-refresh-btn" id="mjp-refresh">🔄 刷新</button>
                    </div>
                    <div class="mjp-search-box">
                        <input type="text" class="mjp-search-input" id="mjp-search" 
                               placeholder="🔍 搜索职位 (ID 或名称)">
                    </div>
                    <div id="mjp-jobs-container">
                        <div class="mjp-loading">
                            <div class="mjp-spinner"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mjp-actions">
                <button class="mjp-btn mjp-btn-secondary" id="mjp-preview">👁️ 预览</button>
                <button class="mjp-btn mjp-btn-primary" id="mjp-fill" disabled>✨ 自动填写</button>
                <button class="mjp-btn mjp-btn-success" id="mjp-mark-published" disabled>✅ 已发布</button>
            </div>
        `;
    }

    bindEvents() {
        // 关闭/最小化
        this.panel.querySelector('.mjp-close').addEventListener('click', () => this.minimize());

        // API URL 变更
        const apiInput = this.panel.querySelector('#mjp-api-url');
        apiInput.addEventListener('change', (e) => {
            this.config.apiBaseUrl = e.target.value.trim();
            this.saveConfig();
        });

        // 邮箱变更
        const emailInput = this.panel.querySelector('#mjp-email');
        emailInput.addEventListener('change', (e) => {
            this.config.receiveEmail = e.target.value.trim();
            this.saveConfig();
        });

        // 配置折叠
        this.panel.querySelector('#mjp-config-toggle').addEventListener('click', () => {
            const config = this.panel.querySelector('#mjp-api-config');
            const arrow = this.panel.querySelector('#mjp-toggle-arrow');
            if (config.style.display === 'none') {
                config.style.display = 'block';
                arrow.textContent = '▼';
            } else {
                config.style.display = 'none';
                arrow.textContent = '▶';
            }
        });

        // 刷新按钮
        this.panel.querySelector('#mjp-refresh').addEventListener('click', () => this.fetchJobs());

        // 搜索框
        this.panel.querySelector('#mjp-search').addEventListener('input', (e) => {
            this.filterJobs(e.target.value.trim());
        });

        // 预览按钮
        this.panel.querySelector('#mjp-preview').addEventListener('click', () => this.previewJob());

        // 填写按钮
        this.panel.querySelector('#mjp-fill').addEventListener('click', () => this.fillForm());

        // 标记已发布按钮
        this.panel.querySelector('#mjp-mark-published').addEventListener('click', () => this.markPublished());
    }

    makeDraggable() {
        const header = this.panel.querySelector('.mjp-header');
        let isDragging = false;
        let offsetX, offsetY;

        header.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('mjp-close')) return;
            isDragging = true;
            offsetX = e.clientX - this.panel.offsetLeft;
            offsetY = e.clientY - this.panel.offsetTop;
            this.panel.style.transition = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            this.panel.style.left = (e.clientX - offsetX) + 'px';
            this.panel.style.top = (e.clientY - offsetY) + 'px';
            this.panel.style.right = 'auto';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            this.panel.style.transition = '';
        });
    }

    minimize() {
        this.panel.style.display = 'none';
        this.isMinimized = true;

        const minimizedBtn = document.createElement('div');
        minimizedBtn.className = 'maimai-job-poster-minimized';
        minimizedBtn.title = '打开职位发布助手';
        minimizedBtn.addEventListener('click', () => {
            minimizedBtn.remove();
            this.panel.style.display = 'block';
            this.isMinimized = false;
        });
        document.body.appendChild(minimizedBtn);
    }

    async fetchJobs() {
        const container = this.panel.querySelector('#mjp-jobs-container');
        container.innerHTML = '<div class="mjp-loading"><div class="mjp-spinner"></div></div>';

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/api/jobs?limit=200`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            this.jobs = data.jobs || [];
            this.renderJobList();
        } catch (error) {
            console.error('❌ 获取职位列表失败:', error);
            container.innerHTML = `
                <div class="mjp-status error">
                    ⚠️ 获取职位失败: ${error.message}
                </div>
                <div class="mjp-empty">
                    <div class="mjp-empty-icon">🔌</div>
                    <div class="mjp-empty-text">请确保 API 服务已启动</div>
                </div>
            `;
        }
    }

    renderJobList() {
        const container = this.panel.querySelector('#mjp-jobs-container');

        if (this.jobs.length === 0) {
            container.innerHTML = `
                <div class="mjp-empty">
                    <div class="mjp-empty-icon">📭</div>
                    <div class="mjp-empty-text">暂无可发布的职位</div>
                </div>
            `;
            return;
        }

        container.innerHTML = this.jobs.map(job => {
            const hasDesc = job.has_description || job.description_length > 0;
            const descBadge = hasDesc
                ? `<span class="mjp-job-tag desc" style="background:#10b981;color:white;">✅ ${job.description_length}字</span>`
                : `<span class="mjp-job-tag desc" style="background:#ef4444;color:white;">❌ 无描述</span>`;

            const channels = Array.isArray(job.published_channels) ? job.published_channels : [];
            // published_channels 可能是字符串数组 ['MM'] 或对象数组 [{channel:'MM', published_at:'...'}]
            const isPublishedMM = channels.some(c => c === 'MM' || (c && c.channel === 'MM'));
            const publishedBadge = isPublishedMM
                ? `<span class="mjp-job-tag" style="background:#8b5cf6;color:white;font-weight:600;">✅ 已发布</span>`
                : '';

            return `
            <div class="mjp-job-card ${hasDesc ? '' : 'no-desc'} ${isPublishedMM ? 'mjp-published' : ''}" data-job-id="${job.id}" data-job-code="${job.job_code || ''}">
                <div class="mjp-job-title">${job.job_code ? `<span class="mjp-job-code">${this.escapeHtml(job.job_code)}</span>` : ''}${this.escapeHtml(job.title)}</div>
                <div class="mjp-job-meta">
                    <span class="mjp-job-tag">${job.company || '未知公司'}</span>
                    ${descBadge}
                    ${publishedBadge}
                    ${job.location ? `<span class="mjp-job-tag location">📍 ${job.location}</span>` : ''}
                </div>
            </div>
        `}).join('');

        // 绑定选择事件
        container.querySelectorAll('.mjp-job-card').forEach(card => {
            card.addEventListener('click', () => this.selectJob(parseInt(card.dataset.jobId)));
        });
    }

    filterJobs(query) {
        const container = this.panel.querySelector('#mjp-jobs-container');
        const cards = container.querySelectorAll('.mjp-job-card');

        if (!query) {
            cards.forEach(card => card.style.display = '');
            return;
        }

        // 先在本地过滤已加载的职位
        const q = query.toLowerCase();
        cards.forEach(card => {
            const jobId = card.dataset.jobId;
            const jobCode = (card.dataset.jobCode || '').toLowerCase();
            const title = card.querySelector('.mjp-job-title')?.textContent?.toLowerCase() || '';
            const company = card.querySelector('.mjp-job-tag')?.textContent?.toLowerCase() || '';
            const match = jobId.includes(q) || jobCode.includes(q) || title.includes(q) || company.includes(q);
            card.style.display = match ? '' : 'none';
        });

        // 只要用户输入超过 2 个字符，始终发起服务端搜索（获取更多结果）
        if (query.length >= 2) {
            this.searchJobsFromAPI(query);
        }
    }

    async searchJobsFromAPI(query) {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/api/jobs?search=${encodeURIComponent(query)}&limit=50`);
            if (!response.ok) return;
            const data = await response.json();
            if (data.jobs && data.jobs.length > 0) {
                // 合并到现有列表（去重）
                const existingIds = new Set(this.jobs.map(j => j.id));
                const newJobs = data.jobs.filter(j => !existingIds.has(j.id));
                this.jobs = [...newJobs, ...this.jobs];
                this.renderJobList();
                // 重新过滤
                const searchInput = this.panel.querySelector('#mjp-search');
                if (searchInput && searchInput.value) {
                    const q = searchInput.value.toLowerCase();
                    const cards = this.panel.querySelectorAll('.mjp-job-card');
                    cards.forEach(card => {
                        const jobCode = (card.dataset.jobCode || '').toLowerCase();
                        const title = card.querySelector('.mjp-job-title')?.textContent?.toLowerCase() || '';
                        const company = card.querySelector('.mjp-job-tag')?.textContent?.toLowerCase() || '';
                        const match = jobCode.includes(q) || title.includes(q) || company.includes(q);
                        card.style.display = match ? '' : 'none';
                    });
                }
            }
        } catch (e) {
            console.warn('⚠️ 服务端搜索失败:', e);
        }
    }

    selectJob(jobId) {
        this.selectedJob = this.jobs.find(j => j.id === jobId);

        // 更新 UI
        this.panel.querySelectorAll('.mjp-job-card').forEach(card => {
            card.classList.toggle('selected', parseInt(card.dataset.jobId) === jobId);
        });

        // 启用填写按钮和发布按钮
        this.panel.querySelector('#mjp-fill').disabled = false;
        const pubBtn = this.panel.querySelector('#mjp-mark-published');
        pubBtn.disabled = false;
        pubBtn.textContent = '✅ 已发布';
        pubBtn.classList.remove('mjp-btn-done');

        this.showToast(`已选择: ${this.selectedJob.title}`);
    }

    async previewJob() {
        if (!this.selectedJob) {
            this.showToast('请先选择一个职位', 'warning');
            return;
        }

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/api/jobs/${this.selectedJob.id}`);
            const data = await response.json();

            if (data.success && data.job) {
                console.log('📋 职位详情:', data.job);
                this.showToast('职位详情已打印到控制台');
            }
        } catch (error) {
            this.showToast('获取详情失败: ' + error.message, 'error');
        }
    }

    async fillForm() {
        if (!this.selectedJob) {
            this.showToast('请先选择一个职位', 'warning');
            return;
        }

        const fillBtn = this.panel.querySelector('#mjp-fill');
        fillBtn.disabled = true;
        fillBtn.textContent = '⏳ 填写中...';

        try {
            // 获取职位详情
            const response = await fetch(`${this.config.apiBaseUrl}/api/jobs/${this.selectedJob.id}`);
            const data = await response.json();

            if (!data.success || !data.job) {
                throw new Error('获取职位详情失败');
            }

            const job = data.job;
            console.log('📝 开始填写表单:', job);

            let filledCount = 0;
            let warnings = [];

            // ========== 01 基本信息 ==========

            // 1. 填写职位名称
            console.log('📝 [1/8] 填写职位名称...');
            if (await this.fillReactInput('#position', job.title)) {
                filledCount++;
            }
            await this.delay(500);

            // 2. 选择职位类别：互联网技术 → 高端技术职位 → 高端技术职位
            console.log('📝 [2/8] 选择职位类别...');
            if (await this.selectPositionCategory()) {
                filledCount++;
            }
            await this.delay(500);

            // 3. 填写职位描述
            console.log('📝 [3/8] 填写职位描述...');
            if (job.description && job.description.trim()) {
                if (await this.fillReactTextarea('#description', job.description)) {
                    filledCount++;
                }
            } else {
                warnings.push('职位描述为空');
            }
            await this.delay(500);

            // ========== 02 职位要求 ==========

            // 4. 选择经验要求
            console.log('📝 [4/9] 选择经验要求...');
            const expText = this.mapExperience(job.required_experience_years);
            console.log(`🎯 目标经验: ${expText}`);
            if (await this.selectExperienceOrEducation(0, expText)) {
                filledCount++;
            }
            await this.delay(600);

            // 5. 选择学历要求
            console.log('📝 [5/9] 选择学历要求...');
            const eduText = this.mapEducation(job.seniority_level);
            console.log(`🎯 目标学历: ${eduText}`);
            if (await this.selectExperienceOrEducation(1, eduText)) {
                filledCount++;
            }
            await this.delay(600);

            // 6. 选择薪资范围
            console.log('📝 [6/9] 选择薪资范围...');
            const salary = this.parseSalary(job.salary_range);
            if (await this.selectSalaryRange(salary.min, salary.max, salary.months)) {
                filledCount++;
            }
            await this.delay(400);

            // 7. 选择行业要求（默认 IT/互联网/游戏）
            console.log('📝 [7/9] 选择行业要求...');
            if (await this.selectIndustry()) {
                filledCount++;
            }
            await this.delay(500);

            // 8. 选择工作地址（使用默认地址）
            console.log('📝 [8/9] 选择工作地址...');
            if (await this.selectDefaultAddress()) {
                filledCount++;
            }
            await this.delay(400);

            // 9. 填写邮箱
            console.log('📝 [9/9] 填写邮箱...');
            if (this.config.receiveEmail) {
                if (await this.fillReactInput('#email', this.config.receiveEmail)) {
                    filledCount++;
                }
            }

            // 10. 切换到普通职位
            await this.selectNormalPosition();

            // 显示结果
            let message = `✅ 已填写 ${filledCount} 个字段`;
            if (warnings.length > 0) {
                message += ` (${warnings.join(', ')})`;
            }

            this.showToast(message, warnings.length > 0 ? 'warning' : 'success');
            console.log('🎉 表单填写完成！');

        } catch (error) {
            console.error('❌ 填写失败:', error);
            this.showToast('填写失败: ' + error.message, 'error');
        } finally {
            fillBtn.disabled = false;
            fillBtn.textContent = '✨ 自动填写';
        }
    }

    /**
     * 标记职位已在脉脉发布（二次发布追踪）
     * - 调用后端 POST /api/jobs/{id}/publish?channel=MM
     * - 与 jd_link（客户原始JD来源）不同，这里记录的是猎头在招聘平台的发布
     * - 流程：用户在脉脉提交职位后 → 手动点击此按钮 → 后端记录渠道+时间
     * - 支持多渠道：MM=脉脉, LI=LinkedIn, BOSS=Boss直聘
     */
    async markPublished() {
        if (!this.selectedJob) {
            this.showToast('请先选择一个职位', 'warning');
            return;
        }

        const btn = this.panel.querySelector('#mjp-mark-published');
        btn.disabled = true;
        btn.textContent = '⏳ 提交中...';

        try {
            // 调用后端 API 标记发布渠道（当前固定为 MM=脉脉）
            const response = await fetch(
                `${this.config.apiBaseUrl}/api/jobs/${this.selectedJob.id}/publish?channel=MM`,
                { method: 'POST' }
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (data.success) {
                // 在内存中更新 published_channels，保持和后端一致的对象格式
                const jobInList = this.jobs.find(j => j.id === this.selectedJob.id);
                if (jobInList) {
                    if (!Array.isArray(jobInList.published_channels)) jobInList.published_channels = [];
                    const alreadyHasMM = jobInList.published_channels.some(c => c === 'MM' || (c && c.channel === 'MM'));
                    if (!alreadyHasMM) {
                        jobInList.published_channels.push({ channel: 'MM', published_at: new Date().toISOString() });
                    }
                }
                // 更新当前卡片的 badge（无需重新渲染整个列表）
                const card = this.panel.querySelector(`.mjp-job-card[data-job-id="${this.selectedJob.id}"]`);
                if (card) {
                    card.classList.add('mjp-published');
                    const meta = card.querySelector('.mjp-job-meta');
                    if (meta && !meta.querySelector('.mjp-published-badge')) {
                        const badge = document.createElement('span');
                        badge.className = 'mjp-job-tag mjp-published-badge';
                        badge.style.cssText = 'background:#8b5cf6;color:white;font-weight:600;';
                        badge.textContent = '✅ 已发布';
                        // 插入在描述字数 badge 后面
                        const descBadge = meta.querySelector('.desc');
                        if (descBadge) descBadge.insertAdjacentElement('afterend', badge);
                        else meta.prepend(badge);
                    }
                }
                // 按钮恢复可点击（允许重新发布），但文本提示已发布
                btn.textContent = '♻️ 重新发布';
                btn.disabled = false;
                btn.classList.add('mjp-btn-done');
                this.showToast(`${this.selectedJob.job_code || this.selectedJob.title} 已标记发布到脉脉`, 'success');
                console.log('✅ 已标记发布:', data.message);
            } else {
                throw new Error(data.detail || '标记失败');
            }
        } catch (e) {
            // 失败：恢复按钮状态，允许重试
            console.error('❌ 标记发布失败:', e);
            btn.textContent = '✅ 已发布';
            btn.disabled = false;
            this.showToast('标记失败: ' + e.message, 'error');
        }
    }

    // ========== 映射函数 ==========

    mapExperience(years) {
        // 脉脉经验选项：1年以内、1-3年、3-5年、5-10年、10年以上、经验不限
        if (!years) return '经验不限';
        if (years <= 1) return '1年以内';
        if (years <= 3) return '1-3年';
        if (years <= 5) return '3-5年';
        if (years <= 10) return '5-10年';
        return '10年以上';
    }

    mapEducation(seniorityLevel) {
        // 脉脉学历选项：学历不限、本科及以上、硕士及以上、博士、专科及以上
        // 根据职级推断学历要求
        if (!seniorityLevel) return '本科及以上';
        const level = seniorityLevel.toUpperCase();
        if (level.includes('P8') || level.includes('P9') || level.includes('专家') || level.includes('SENIOR')) {
            return '硕士及以上';
        }
        if (level.includes('博士') || level.includes('PHD')) {
            return '博士';
        }
        return '本科及以上';
    }

    parseSalary(salaryRange) {
        // 默认值
        const defaultSalary = { min: '35', max: '70', months: '12' };

        if (!salaryRange) return defaultSalary;

        // 尝试解析 "30K-60K" 或 "30k-60k" 格式
        const match = salaryRange.match(/(\d+)[kK]?\s*[-~]\s*(\d+)[kK]?/);
        if (match) {
            return {
                min: match[1],
                max: match[2],
                months: '12'
            };
        }

        return defaultSalary;
    }

    // ========== 选择职位类别（三级联动） ==========

    async selectPositionCategory() {
        try {
            // 点击职位类别输入框，打开弹窗
            const categoryInput = document.querySelector('#position_type');
            if (!categoryInput) {
                console.warn('⚠️ 未找到职位类别输入框');
                return false;
            }

            // 点击打开弹窗
            const selectWrapper = categoryInput.closest('.ant-select');
            if (selectWrapper) {
                selectWrapper.click();
                await this.delay(800);
            }

            // 脉脉的职位类别是自定义三列弹窗
            // 第一列：查找并点击"互联网技术"
            console.log('🔍 查找第一列: 互联网技术');
            const level1 = await this.findCategoryItem('互联网技术');
            if (!level1) {
                console.warn('⚠️ 未找到"互联网技术"选项');
                this.closePopups();
                return false;
            }
            level1.click();
            await this.delay(500);

            // 第二列：查找并点击"高端技术职位"
            console.log('🔍 查找第二列: 高端技术职位');
            const level2 = await this.findCategoryItem('高端技术职位');
            if (!level2) {
                console.warn('⚠️ 未找到"高端技术职位"选项');
                this.closePopups();
                return false;
            }
            level2.click();
            await this.delay(600);

            // 第三列：查找并点击"高端技术职位"
            console.log('🔍 查找第三列: 高端技术职位');
            const level3 = await this.findCategoryItem('高端技术职位', true);
            if (level3) {
                console.log('🖱️ 点击第三列元素:', level3.tagName, level3.className);

                // 尝试多种点击方式
                level3.click();
                await this.delay(200);

                // 如果 click 不起作用，尝试模拟 mousedown/mouseup
                level3.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                level3.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                level3.dispatchEvent(new MouseEvent('click', { bubbles: true }));

                await this.delay(500);
            } else {
                console.warn('⚠️ 未找到第三列选项，尝试点击第一个可见选项');
                // 尝试点击任意第三列选项
                const anyThirdCol = document.querySelector('[class*="col"]:last-child li, [class*="column"]:last-child li');
                if (anyThirdCol) {
                    anyThirdCol.click();
                    await this.delay(300);
                }
            }

            // 强制关闭弹窗
            await this.delay(300);
            this.closePopups();
            await this.delay(300);

            console.log('✅ 职位类别选择完成');
            return true;
        } catch (e) {
            console.error('❌ 选择职位类别失败:', e);
            this.closePopups();
            return false;
        }
    }

    /**
     * 在弹窗中查找分类项
     * 脉脉使用自定义弹窗，需要遍历所有可点击元素
     */
    async findCategoryItem(text, lastColumn = false) {
        await this.delay(200);

        // 打印当前弹窗中的所有可见文本（调试用）
        const allItems = document.querySelectorAll(
            // 尝试多种可能的选择器
            '[class*="modal"] li, ' +
            '[class*="Modal"] li, ' +
            '[class*="popup"] li, ' +
            '[class*="Popup"] li, ' +
            '[class*="menu"] li, ' +
            '[class*="Menu"] li, ' +
            '[class*="cascader"] li, ' +
            '[class*="Cascader"] li, ' +
            '[class*="list"] li, ' +
            '[class*="List"] li, ' +
            '.ant-modal li, ' +
            '[role="listbox"] [role="option"], ' +
            '[class*="option"], ' +
            '[class*="Option"]'
        );

        console.log(`🔍 找到 ${allItems.length} 个候选项`);

        for (const item of allItems) {
            const itemText = item.textContent?.trim();
            // 检查是否可见
            if (item.offsetParent === null) continue;

            // 精确匹配或包含匹配
            if (itemText === text || (!lastColumn && itemText?.startsWith(text))) {
                console.log(`✅ 找到: "${itemText}"`);
                return item;
            }
        }

        // 备选：尝试通过 div/span 查找
        const divItems = document.querySelectorAll('div, span');
        for (const item of divItems) {
            if (item.children.length > 0) continue; // 跳过容器
            const itemText = item.textContent?.trim();
            if (item.offsetParent === null) continue;

            if (itemText === text) {
                console.log(`✅ 通过 div/span 找到: "${itemText}"`);
                return item.closest('li') || item;
            }
        }

        return null;
    }

    closePopups() {
        // 点击遮罩关闭弹窗
        const masks = document.querySelectorAll('.ant-modal-mask, [class*="mask"], [class*="overlay"]');
        masks.forEach(m => m.click());
        document.body.click();
    }

    // ========== 选择经验/学历 ==========

    async selectExperienceOrEducation(index, optionText) {
        // index: 0 = 经验, 1 = 学历
        try {
            console.log(`🔍 查找经验学历表单项... (index=${index}, target=${optionText})`);

            // 找到"经验学历"标签对应的表单项
            const labels = document.querySelectorAll('.ant-legacy-form-item-label label, .ant-form-item-label label, label');
            let formItem = null;

            for (const label of labels) {
                if (label.textContent?.includes('经验学历')) {
                    formItem = label.closest('.ant-row') || label.closest('.ant-form-item') || label.parentElement?.parentElement;
                    break;
                }
            }

            if (!formItem) {
                console.warn('⚠️ 未找到经验学历表单项');
                return false;
            }

            console.log('🔍 找到表单项:', formItem.className);

            // 找到所有下拉框
            const selects = formItem.querySelectorAll('.ant-select');
            console.log(`🔍 找到 ${selects.length} 个下拉框`);

            if (selects.length < index + 1) {
                console.warn(`⚠️ 没有足够的下拉框`);
                return false;
            }

            const targetSelect = selects[index];

            // 点击打开下拉
            console.log(`🖱️ 点击第 ${index + 1} 个下拉框...`);
            const selector = targetSelect.querySelector('.ant-select-selector') || targetSelect;
            selector.click();
            await this.delay(1000);

            // 查找下拉选项 - 在下拉容器中查找
            console.log('🔍 查找下拉容器...');

            // Ant Design 的下拉容器
            const dropdown = document.querySelector('.ant-select-dropdown:not(.ant-select-dropdown-hidden)');
            if (!dropdown) {
                console.warn('⚠️ 未找到下拉容器');
                document.body.click();
                return false;
            }

            console.log('🔍 在下拉容器中查找选项...');
            const dropdownItems = dropdown.querySelectorAll('.ant-select-item-option, .ant-select-item');

            console.log(`📋 找到 ${dropdownItems.length} 个选项:`);
            dropdownItems.forEach((item, i) => {
                const text = item.textContent?.trim();
                console.log(`  ${i}: "${text}"`);
            });

            // 查找匹配的选项
            for (const item of dropdownItems) {
                const text = item.textContent?.trim();
                if (text === optionText) {
                    console.log(`✅ 点击选项: ${text}`);
                    item.click();
                    await this.delay(300);
                    console.log(`✅ 选择成功: ${optionText}`);
                    return true;
                }
            }

            // 未找到，关闭下拉
            console.warn(`⚠️ 未找到选项: ${optionText}`);
            document.body.click();
            return false;
        } catch (e) {
            console.error(`❌ 选择经验/学历失败:`, e);
            return false;
        }
    }

    // ========== 选择下拉框 ==========

    async selectDropdownByLabel(labelText, optionText, index = 0) {
        try {
            // 通过 label 文本找到对应的表单项
            // 尝试多种 label 选择器
            let targetLabel = null;
            const labelSelectors = [
                '.ant-legacy-form-item-label label',
                '.ant-form-item-label label',
                '[class*="form"] label',
                'label'
            ];

            for (const selector of labelSelectors) {
                const labels = document.querySelectorAll(selector);
                for (const label of labels) {
                    if (label.textContent?.includes(labelText)) {
                        targetLabel = label;
                        break;
                    }
                }
                if (targetLabel) break;
            }

            if (!targetLabel) {
                console.warn(`⚠️ 未找到标签: ${labelText}`);
                return false;
            }

            // 找到对应的表单控件区域
            const formItem = targetLabel.closest('.ant-row') ||
                targetLabel.closest('[class*="form-item"]') ||
                targetLabel.closest('[class*="FormItem"]') ||
                targetLabel.parentElement?.parentElement;
            if (!formItem) {
                console.warn(`⚠️ 未找到表单项容器`);
                return false;
            }

            console.log(`🔍 找到表单项:`, formItem.className);

            // 找到所有下拉框
            const selects = formItem.querySelectorAll('.ant-select');
            console.log(`🔍 找到 ${selects.length} 个下拉框`);
            const targetSelect = selects[index];

            if (!targetSelect) {
                console.warn(`⚠️ 未找到第 ${index + 1} 个下拉框`);
                return false;
            }

            // 点击打开下拉
            console.log(`🖱️ 点击下拉框:`, targetSelect.className);
            targetSelect.click();
            await this.delay(600);

            // 打印当前 DOM 中所有可能是下拉选项的元素
            console.log('🔍 查找下拉选项...');
            const allPossibleOptions = document.querySelectorAll(
                '.ant-select-item, .ant-select-item-option, [role="option"], ' +
                '.ant-select-dropdown li, [class*="dropdown"] [class*="item"], ' +
                '.ant-select-dropdown-menu-item, [class*="select-dropdown"] li'
            );
            console.log(`🔍 找到 ${allPossibleOptions.length} 个可能的选项元素`);

            // 打印所有选项用于调试（不管可见性）
            console.log('📋 所有选项内容:');
            allPossibleOptions.forEach((opt, i) => {
                console.log(`  ${i}: "${opt.textContent?.trim()}" visible=${opt.offsetParent !== null}`);
            });

            // 尝试匹配选项（不检查可见性）
            for (const opt of allPossibleOptions) {
                const optText = opt.textContent?.trim();
                if (optText === optionText) {
                    console.log(`✅ 找到匹配选项: "${optText}"`);
                    opt.click();
                    await this.delay(200);
                    console.log(`✅ 选择 ${labelText}[${index}]: ${optionText}`);
                    return true;
                }
            }

            // 关闭下拉
            document.body.click();
            console.warn(`⚠️ 未找到选项: ${optionText}`);
            return false;
        } catch (e) {
            console.error(`❌ 选择 ${labelText} 失败:`, e);
            return false;
        }
    }

    // ========== 选择薪资范围 ==========

    async selectSalaryRange(minK, maxK, months = '12') {
        try {
            // 找到薪资范围的表单项
            const labels = document.querySelectorAll('.ant-legacy-form-item-label label');
            let salaryFormItem = null;

            for (const label of labels) {
                if (label.textContent?.includes('薪资范围')) {
                    salaryFormItem = label.closest('.ant-row');
                    break;
                }
            }

            if (!salaryFormItem) {
                console.warn('⚠️ 未找到薪资范围表单项');
                return false;
            }

            const selects = salaryFormItem.querySelectorAll('.ant-select');

            // 选择最低薪资
            if (selects[0]) {
                selects[0].click();
                await this.delay(300);
                await this.clickOptionByText(`${minK}k`);
                await this.delay(300);
            }

            // 选择最高薪资
            if (selects[1]) {
                selects[1].click();
                await this.delay(300);
                await this.clickOptionByText(`${maxK}k`);
                await this.delay(300);
            }

            // 选择月数
            if (selects[2]) {
                selects[2].click();
                await this.delay(300);
                await this.clickOptionByText(`${months}薪`);
                await this.delay(300);
            }

            console.log(`✅ 薪资范围: ${minK}k-${maxK}k·${months}薪`);
            return true;
        } catch (e) {
            console.error('❌ 选择薪资范围失败:', e);
            return false;
        }
    }

    async clickOptionByText(text) {
        const options = document.querySelectorAll('.ant-select-item-option');
        for (const opt of options) {
            const optText = opt.textContent?.trim().toLowerCase();
            if (optText === text.toLowerCase() || optText?.includes(text.toLowerCase())) {
                opt.click();
                return true;
            }
        }
        document.body.click();
        return false;
    }

    // ========== 选择行业要求 ==========

    async selectIndustry() {
        try {
            console.log('🔍 查找行业要求表单项...');

            // 找到行业要求的表单项
            const labels = document.querySelectorAll('.ant-legacy-form-item-label label, .ant-form-item-label label, label');
            let industryFormItem = null;

            for (const label of labels) {
                if (label.textContent?.includes('行业要求')) {
                    industryFormItem = label.closest('.ant-row') || label.closest('.ant-form-item') || label.parentElement?.parentElement;
                    break;
                }
            }

            if (!industryFormItem) {
                console.warn('⚠️ 未找到行业要求表单项');
                return false;
            }

            console.log('🔍 找到行业要求表单项:', industryFormItem.className);

            // 点击打开行业选择弹窗
            const select = industryFormItem.querySelector('.ant-select');
            if (!select) {
                console.warn('⚠️ 未找到行业选择器');
                return false;
            }

            console.log('🖱️ 点击打开行业弹窗...');
            select.click();
            await this.delay(1000);

            // 第一步：点击左侧"不限行业"（最简单的选择）
            console.log('🔍 查找左侧"不限行业"...');
            const allSpans = document.querySelectorAll('span, div, li');

            for (const item of allSpans) {
                const text = item.textContent?.trim();
                // 精确匹配"不限行业"
                if (text === '不限行业' && item.children.length === 0) {
                    if (item.offsetParent !== null) {
                        console.log('🖱️ 点击: 不限行业');
                        item.click();
                        await this.delay(600);
                        break;
                    }
                }
            }

            // 第二步：点击右边面板的"不限行业"按钮
            console.log('🔍 查找右边面板的"不限行业"...');
            await this.delay(500);

            // 找到弹窗内的蓝色选项按钮
            const modal = document.querySelector('.ant-modal, [class*="modal"], [class*="Modal"]');
            if (modal) {
                const optionBtns = modal.querySelectorAll('span, div');
                for (const btn of optionBtns) {
                    const text = btn.textContent?.trim();
                    if (text === '不限行业' && btn.children.length === 0) {
                        console.log('🖱️ 点击右边: 不限行业');
                        btn.click();
                        await this.delay(400);
                        break;
                    }
                }
            }

            // 第三步：点击"确 定"按钮
            console.log('🔍 查找弹窗内的确定按钮...');
            await this.delay(500);

            // 在弹窗内查找按钮
            const modalForBtn = document.querySelector('.ant-modal, [class*="modal"], [class*="Modal"]');
            if (modalForBtn) {
                const modalButtons = modalForBtn.querySelectorAll('button, span.ant-btn, .ant-btn');
                console.log(`📋 弹窗内找到 ${modalButtons.length} 个按钮`);

                for (const btn of modalButtons) {
                    const btnText = btn.textContent?.trim().replace(/\s+/g, '');
                    console.log(`  弹窗按钮: "${btnText}"`);
                    if (btnText === '确定') {
                        console.log('🖱️ 点击确定按钮');
                        btn.click();
                        await this.delay(300);
                        console.log('✅ 行业要求选择完成');
                        return true;
                    }
                }
            }

            // 关闭弹窗
            console.warn('⚠️ 未找到确定按钮');
            this.closePopups();
            return false;
        } catch (e) {
            console.error('❌ 选择行业要求失败:', e);
            return false;
        }
    }

    // ========== 选择工作地址 ==========

    async selectDefaultAddress() {
        try {
            console.log('🔍 查找工作地址表单项...');

            // 找到工作地址的表单项
            const labels = document.querySelectorAll('.ant-legacy-form-item-label label, .ant-form-item-label label, label');
            let addressFormItem = null;

            for (const label of labels) {
                if (label.textContent?.includes('工作地址')) {
                    addressFormItem = label.closest('.ant-row') || label.closest('.ant-form-item') || label.parentElement?.parentElement;
                    break;
                }
            }

            if (!addressFormItem) {
                console.warn('⚠️ 未找到工作地址表单项');
                return false;
            }

            console.log('🔍 找到工作地址表单项:', addressFormItem.className);

            // 点击打开地址选择弹窗
            const select = addressFormItem.querySelector('.ant-select');
            if (!select) {
                console.warn('⚠️ 未找到地址选择器');
                return false;
            }

            console.log('🖱️ 点击打开地址弹窗...');
            select.click();
            await this.delay(800);

            // 先选中第一个地址（点击 radio）
            console.log('🔍 查找地址选项...');
            const radioSelectors = [
                'input[type="radio"]',
                '.ant-radio-input',
                '.ant-radio',
                '[class*="radio"]'
            ];

            let radioClicked = false;
            for (const selector of radioSelectors) {
                const radio = document.querySelector(selector);
                if (radio) {
                    console.log('🖱️ 点击地址选项:', radio.className);
                    radio.click();
                    radioClicked = true;
                    await this.delay(400);
                    break;
                }
            }

            // 查找并点击"使用该地址"按钮
            console.log('🔍 查找弹窗内的"使用该地址"按钮...');
            await this.delay(500);

            // 在弹窗内查找按钮
            const modal = document.querySelector('.ant-modal, [class*="modal"], [class*="Modal"]');
            if (modal) {
                const modalButtons = modal.querySelectorAll('button, span.ant-btn, .ant-btn');
                console.log(`📋 弹窗内找到 ${modalButtons.length} 个按钮:`);

                for (const btn of modalButtons) {
                    const btnText = btn.textContent?.trim().replace(/\s+/g, '');
                    console.log(`  弹窗按钮: "${btnText}"`);
                    // 查找"使用该地址"
                    if (btnText === '使用该地址') {
                        console.log('🖱️ 点击: 使用该地址');
                        btn.click();
                        await this.delay(300);
                        console.log('✅ 使用默认工作地址');
                        return true;
                    }
                }
            }

            // 如果没找到按钮，关闭弹窗
            console.warn('⚠️ 未找到确认按钮');
            this.closePopups();
            return false;
        } catch (e) {
            console.error('❌ 选择工作地址失败:', e);
            return false;
        }
    }

    async findButtonByText(text) {
        await this.delay(200);
        const buttons = document.querySelectorAll('button, .mui-btn, [role="button"]');
        for (const btn of buttons) {
            if (btn.textContent?.includes(text)) {
                return btn;
            }
        }
        return null;
    }

    // ========== 选择普通职位 ==========

    async selectNormalPosition() {
        try {
            // 查找职位属性区域
            const goldPositionDiv = document.querySelector('.goldPosition___3x4cW');
            if (!goldPositionDiv) {
                console.warn('⚠️ 未找到职位属性区域');
                return false;
            }

            // 找到"普通职位"按钮并点击
            const buttons = goldPositionDiv.querySelectorAll('div');
            for (const btn of buttons) {
                if (btn.textContent?.trim() === '普通职位') {
                    btn.click();
                    console.log('✅ 切换到普通职位');
                    return true;
                }
            }

            return false;
        } catch (e) {
            console.error('❌ 选择职位属性失败:', e);
            return false;
        }
    }

    /**
     * 使用 React 兼容方式填写 Input
     * React 表单会劫持 value setter，需要使用 native setter
     */
    async fillReactInput(selector, value) {
        const input = document.querySelector(selector);
        if (!input) {
            console.warn(`⚠️ 未找到输入框: ${selector}`);
            return false;
        }

        if (!value) {
            console.warn(`⚠️ 值为空: ${selector}`);
            return false;
        }

        // 聚焦
        input.focus();
        await this.delay(100);

        // 使用 native value setter 绑定值 (绕过 React 的 value 拦截)
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(input, value);

        // 触发 React 识别的事件
        input.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
        input.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));

        console.log(`✅ 填写 ${selector}: ${value.substring(0, 50)}...`);
        return true;
    }

    /**
     * 使用 React 兼容方式填写 Textarea
     */
    async fillReactTextarea(selector, value) {
        const textarea = document.querySelector(selector);
        if (!textarea) {
            console.warn(`⚠️ 未找到文本框: ${selector}`);
            return false;
        }

        if (!value) {
            console.warn(`⚠️ 值为空: ${selector}`);
            return false;
        }

        textarea.focus();
        await this.delay(100);

        // 使用 native value setter
        const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
        ).set;
        nativeTextAreaValueSetter.call(textarea, value);

        // 触发事件
        textarea.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
        textarea.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));

        // 失焦以触发验证
        await this.delay(100);
        textarea.dispatchEvent(new Event('blur', { bubbles: true }));

        // 更新字数显示
        const countDisplay = document.querySelector('.descCount___3AdS5');
        if (countDisplay) {
            countDisplay.textContent = `${value.length}/10000`;
        }

        console.log(`✅ 填写 ${selector}: ${value.length} 字符`);
        return true;
    }

    async fillField(selector, value) {
        const input = document.querySelector(selector);
        if (!input) {
            console.warn(`⚠️ 未找到输入框: ${selector}`);
            return false;
        }

        // 聚焦
        input.focus();
        await this.delay(100);

        // 清空并输入
        input.value = value;

        // 触发事件
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));

        // 对于 Ant Design 的 AutoComplete，需要模拟键盘输入
        if (input.classList.contains('ant-select-selection-search-input')) {
            // 模拟键盘输入
            for (const char of value) {
                input.dispatchEvent(new KeyboardEvent('keydown', { key: char, bubbles: true }));
                input.dispatchEvent(new KeyboardEvent('keypress', { key: char, bubbles: true }));
                input.dispatchEvent(new KeyboardEvent('keyup', { key: char, bubbles: true }));
            }
        }

        console.log(`✅ 填写 ${selector}: ${value.substring(0, 50)}...`);
        return true;
    }

    async fillTextarea(selector, value) {
        const textarea = document.querySelector(selector);
        if (!textarea) {
            console.warn(`⚠️ 未找到文本框: ${selector}`);
            return false;
        }

        textarea.focus();
        await this.delay(100);

        textarea.value = value;

        // 触发多种事件确保 React 表单识别
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.dispatchEvent(new Event('change', { bubbles: true }));
        textarea.dispatchEvent(new Event('blur', { bubbles: true }));

        // 更新字数显示
        const countDisplay = document.querySelector('.descCount___3AdS5');
        if (countDisplay) {
            countDisplay.textContent = `${value.length}/10000`;
        }

        console.log(`✅ 填写 ${selector}: ${value.length} 字符`);
        return true;
    }

    async fillSelect(selector, optionText) {
        // Ant Design Select 需要特殊处理
        const selectWrapper = document.querySelector(selector)?.closest('.ant-select');
        if (!selectWrapper) {
            console.warn(`⚠️ 未找到下拉框: ${selector}`);
            return false;
        }

        // 点击打开下拉
        selectWrapper.click();
        await this.delay(500);

        // 查找选项
        const options = document.querySelectorAll('.ant-select-item-option');
        for (const opt of options) {
            if (opt.textContent?.includes(optionText)) {
                opt.click();
                console.log(`✅ 选择 ${selector}: ${optionText}`);
                return true;
            }
        }

        // 关闭下拉
        document.body.click();
        console.warn(`⚠️ 未找到选项: ${optionText}`);
        return false;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    showToast(message, type = 'info') {
        // 移除旧 toast
        const oldToast = document.querySelector('.mjp-toast');
        if (oldToast) oldToast.remove();

        const toast = document.createElement('div');
        toast.className = 'mjp-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
}

// 初始化
if (!window.maimaiJobPoster) {
    window.maimaiJobPoster = new MaimaiJobPoster();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => window.maimaiJobPoster.init(), 500);
        });
    } else {
        setTimeout(() => window.maimaiJobPoster.init(), 500);
    }
}

console.log('✅ Maimai Job Poster 脚本加载完成');
