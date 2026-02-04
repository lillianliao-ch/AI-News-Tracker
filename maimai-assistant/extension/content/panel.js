// Maimai Assistant - 持久悬浮面板 UI (v2 - 自动检测候选人)
class AssistantPanel {
    constructor() {
        this.panel = null;
        this.assistant = null;
        this.isVisible = false;
        this.isCollapsed = false;
        this.stats = { today: 0, total: 0 };
        this.extractedData = [];
        this.detectedCount = 0; // 检测到的候选人数量
    }

    async init() {
        try {
            console.log('🎨 初始化 Maimai Assistant 悬浮面板...');

            this.removeExistingPanel();
            this.createPanel();
            this.render();
            this.bindEvents();
            this.show();
            await this.loadStats();

            // 自动检测候选人
            this.startAutoDetection();

            console.log('✅ 悬浮面板初始化完成');
        } catch (error) {
            console.error('❌ 悬浮面板初始化失败:', error);
        }
    }

    removeExistingPanel() {
        const existing = document.getElementById('maimai-assistant-panel');
        if (existing) existing.remove();
    }

    createPanel() {
        this.panel = document.createElement('div');
        this.panel.id = 'maimai-assistant-panel';
        this.panel.className = 'maimai-assistant-panel';
        document.body.appendChild(this.panel);
    }

    // 新版面板 - 支持指定批量数量
    render() {
        if (!this.panel) return;

        this.panel.innerHTML = `
      <div class="panel-header">
        <h3 class="panel-title">🎯 Maimai Assistant</h3>
        <button class="panel-toggle" id="panelToggle">−</button>
      </div>
      
      <div class="panel-content">
        <!-- 检测状态 -->
        <div class="panel-section detection-section">
          <div class="detection-row">
            <span>📊 检测到候选人:</span>
            <span class="detection-count" id="detectedCount">0 人</span>
            <button class="refresh-btn" id="refreshBtn" title="刷新检测">🔄</button>
          </div>
        </div>
        
        <!-- 批量数量设置 -->
        <div class="panel-section batch-config">
          <label class="config-label">批量处理数量:</label>
          <div class="batch-input-row">
            <input type="number" id="batchCount" class="batch-input" value="10" min="1" max="100" />
            <span class="batch-hint">条</span>
          </div>
        </div>
        
        <!-- 批量操作按钮 -->
        <div class="panel-section">
          <button class="action-btn import-btn" id="importViewBtn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; margin-bottom: 8px;">
            <span class="btn-icon">📥</span>
            导入/查看候选人
          </button>
          <button class="action-btn primary" id="batchAddFriendsBtn">
            <span class="btn-icon">🤝</span>
            批量加好友
          </button>
          <button class="action-btn warning" id="batchSendMsgBtn">
            <span class="btn-icon">💬</span>
            批量发消息
          </button>
          <button class="action-btn" id="extractBtn">
            <span class="btn-icon">📋</span>
            提取信息
          </button>
        </div>
        
        <!-- 人才库功能 (沟通管理页面) -->
        <div class="panel-section talent-section" style="border-top: 1px dashed #e0e0e0; padding-top: 12px; margin-top: 12px;">
          <div style="font-size: 12px; color: #666; margin-bottom: 8px;">📌 人才库功能：</div>
          <button class="action-btn" id="generateMsgBtn" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border: none; color: white;">
            <span class="btn-icon">📝</span>
            生成沟通消息
          </button>
        </div>
        
        <!-- 生成的消息显示区 -->
        <div class="panel-section message-result-section" id="messageResultSection" style="display: none; background: #f9f9f9; border-radius: 8px; padding: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 12px; font-weight: 600; color: #333;">📨 生成的消息：</span>
            <button class="copy-btn" id="copyMsgBtn" style="font-size: 11px; padding: 2px 8px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer;">复制</button>
          </div>
          <div id="generatedMessage" style="font-size: 13px; line-height: 1.5; color: #333; white-space: pre-wrap; word-break: break-all; max-height: 120px; overflow-y: auto; background: white; padding: 8px; border-radius: 4px; border: 1px solid #e0e0e0;"></div>
          <div style="margin-top: 8px; font-size: 11px; color: #999;">
            候选人: <span id="candidateName" style="color: #667eea; font-weight: 500;"></span>
          </div>
        </div>
        
        <!-- 消息模板 -->
        <div class="panel-section template-section">
          <label class="template-label">消息模板：</label>
          <textarea id="messageTemplate" class="template-textarea" 
            placeholder="您好{name}，我是XX公司的HR，看到您的简历很优秀，想和您聊聊..."></textarea>
          <div class="template-hint">变量: {name} 姓名, {company} 公司, {position} 职位, {experience} 年限</div>
        </div>
        
        <!-- 进度显示 -->
        <div class="panel-section progress-section" id="progressSection">
          <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
          </div>
          <div class="progress-text">
            <span id="progressText">0/0</span>
            <span id="progressPercent">0%</span>
          </div>
          <div class="progress-stats">
            <span class="success">✓ <span id="successCount">0</span></span>
            &nbsp;|&nbsp;
            <span class="failed">✗ <span id="failedCount">0</span></span>
          </div>
          <button class="action-btn danger small" id="stopBtn" style="margin-top: 8px;">
            ⏹ 停止
          </button>
        </div>
        
        <!-- 导出区 -->
        <div class="panel-section">
          <div class="action-row">
            <button class="action-btn success" id="exportCsvBtn">
              📄 导出 CSV
            </button>
            <button class="action-btn" id="exportJsonBtn">
              📋 JSON
            </button>
          </div>
        </div>
        
        <!-- 统计 -->
        <div class="panel-section stats-section">
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-number" id="todayCount">${this.stats.today}</div>
              <div class="stat-label">今日</div>
            </div>
            <div class="stat-item">
              <div class="stat-number" id="totalCount">${this.stats.total}</div>
              <div class="stat-label">总计</div>
            </div>
          </div>
        </div>
      </div>
    `;
    }

    bindEvents() {
        if (!this.panel) return;

        // 折叠/展开
        this.panel.querySelector('#panelToggle')?.addEventListener('click', () => this.toggle());

        // 刷新检测
        this.panel.querySelector('#refreshBtn')?.addEventListener('click', () => this.detectCandidates());

        // 导入/查看候选人
        this.panel.querySelector('#importViewBtn')?.addEventListener('click', async () => {
            if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                await extractor.importOrView();
            } else {
                MaimaiUtils.showNotification('详情提取器未加载', 'error');
            }
        });

        // 批量加好友
        this.panel.querySelector('#batchAddFriendsBtn')?.addEventListener('click', () => {
            const count = this.getBatchCount();
            this.showProgress();
            this.assistant?.batchAddFriends(count);
        });

        // 批量发消息
        this.panel.querySelector('#batchSendMsgBtn')?.addEventListener('click', () => {
            const template = this.panel.querySelector('#messageTemplate')?.value;
            if (!template) {
                MaimaiUtils.showNotification('请先输入消息模板', 'warning');
                return;
            }
            const count = this.getBatchCount();
            this.showProgress();
            this.assistant?.batchSendMessages(template, count);
        });

        // 提取信息
        this.panel.querySelector('#extractBtn')?.addEventListener('click', () => {
            const count = this.getBatchCount();
            this.handleExtract(count);
        });

        // 停止
        this.panel.querySelector('#stopBtn')?.addEventListener('click', () => {
            this.assistant?.stopBatchOperation();
        });

        // 导出
        this.panel.querySelector('#exportCsvBtn')?.addEventListener('click', () => this.handleExport('csv'));
        this.panel.querySelector('#exportJsonBtn')?.addEventListener('click', () => this.handleExport('json'));

        // 生成沟通消息 (人才库功能)
        this.panel.querySelector('#generateMsgBtn')?.addEventListener('click', async () => {
            await this.handleGenerateMessage();
        });

        // 复制消息
        this.panel.querySelector('#copyMsgBtn')?.addEventListener('click', () => {
            this.handleCopyMessage();
        });

        // 拖拽
        this.bindDragEvents();

        // 双击折叠
        this.panel.querySelector('.panel-header')?.addEventListener('dblclick', () => this.toggle());
    }

    // 生成沟通消息
    async handleGenerateMessage() {
        console.log('📝 开始生成沟通消息...');

        if (!window.TalentPanelExtractor) {
            MaimaiUtils.showNotification('人才提取器未加载', 'error');
            return;
        }

        const extractor = new TalentPanelExtractor();
        const template = this.panel.querySelector('#messageTemplate')?.value ||
            '您好{name}，我是XX公司的HR，看到您在{company}的工作经历很优秀，想和您聊聊新的机会，方便吗？';

        const result = await extractor.extractAndGenerateMessage(template);

        if (result.success) {
            // 显示生成的消息
            const msgSection = this.panel.querySelector('#messageResultSection');
            const msgEl = this.panel.querySelector('#generatedMessage');
            const nameEl = this.panel.querySelector('#candidateName');

            if (msgSection && msgEl && nameEl) {
                msgSection.style.display = 'block';
                msgEl.textContent = result.message;
                nameEl.textContent = `${result.candidate.name} - ${result.candidate.currentCompany} ${result.candidate.currentPosition}`;
            }

            MaimaiUtils.showNotification(`已为 ${result.candidate.name} 生成消息`, 'success');
            console.log('  候选人数据:', result.candidate);
            console.log('  生成消息:', result.message);
        } else {
            MaimaiUtils.showNotification(result.error || '生成消息失败', 'error');
        }
    }

    // 复制消息
    handleCopyMessage() {
        const msgEl = this.panel.querySelector('#generatedMessage');
        if (msgEl && msgEl.textContent) {
            navigator.clipboard.writeText(msgEl.textContent).then(() => {
                MaimaiUtils.showNotification('消息已复制到剪贴板', 'success');
            }).catch(() => {
                MaimaiUtils.showNotification('复制失败', 'error');
            });
        }
    }

    // 获取批量处理数量
    getBatchCount() {
        const input = this.panel?.querySelector('#batchCount');
        const count = parseInt(input?.value) || 10;
        return Math.min(count, this.detectedCount || 100);
    }

    // 自动检测候选人
    startAutoDetection() {
        // 初始检测
        setTimeout(() => this.detectCandidates(), 1000);

        // 监听页面变化，自动更新
        const observer = new MutationObserver(() => {
            clearTimeout(this._detectTimeout);
            this._detectTimeout = setTimeout(() => this.detectCandidates(), 500);
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // 检测候选人数量
    detectCandidates() {
        const cards = this.assistant?.extractor?.findCandidateCards() || [];
        this.detectedCount = cards.length;

        const countEl = this.panel?.querySelector('#detectedCount');
        if (countEl) {
            countEl.textContent = `${this.detectedCount} 人`;
            countEl.style.color = this.detectedCount > 0 ? '#52c41a' : '#999';
        }

        console.log(`📊 检测到 ${this.detectedCount} 个候选人卡片`);
    }

    bindDragEvents() {
        const header = this.panel.querySelector('.panel-header');
        if (!header) return;

        let isDragging = false;
        let dragOffset = { x: 0, y: 0 };

        header.addEventListener('mousedown', (e) => {
            if (e.target.tagName === 'BUTTON') return;
            isDragging = true;
            const rect = this.panel.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            header.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const x = e.clientX - dragOffset.x;
            const y = e.clientY - dragOffset.y;
            const maxX = window.innerWidth - this.panel.offsetWidth;
            const maxY = window.innerHeight - this.panel.offsetHeight;
            this.panel.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
            this.panel.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
            this.panel.style.bottom = 'auto';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            header.style.cursor = 'move';
        });
    }

    showProgress() {
        const section = this.panel?.querySelector('#progressSection');
        if (section) section.classList.add('show');
    }

    hideProgress() {
        const section = this.panel?.querySelector('#progressSection');
        if (section) section.classList.remove('show');
    }

    updateProgress(state) {
        const { currentIndex, total, successful, failed, isRunning } = state;

        if (!isRunning && currentIndex === 0) {
            this.hideProgress();
            return;
        }

        this.showProgress();

        const percent = total > 0 ? Math.round((currentIndex / total) * 100) : 0;

        const fill = this.panel?.querySelector('#progressFill');
        if (fill) fill.style.width = `${percent}%`;

        const text = this.panel?.querySelector('#progressText');
        if (text) text.textContent = `${currentIndex}/${total}`;

        const percentEl = this.panel?.querySelector('#progressPercent');
        if (percentEl) percentEl.textContent = `${percent}%`;

        const successEl = this.panel?.querySelector('#successCount');
        if (successEl) successEl.textContent = successful;

        const failedEl = this.panel?.querySelector('#failedCount');
        if (failedEl) failedEl.textContent = failed;

        if (!isRunning) {
            setTimeout(() => this.hideProgress(), 3000);
        }
    }

    async handleExtract(count) {
        console.log(`📋 开始提取 ${count} 个候选人信息...`);

        try {
            const candidates = await this.assistant?.batchExtractInfo(count) || [];

            if (candidates.length === 0) {
                MaimaiUtils.showNotification('未找到候选人', 'warning');
                return;
            }

            this.extractedData = [...this.extractedData, ...candidates];
            this.stats.today += candidates.length;
            this.stats.total += candidates.length;
            this.updateStatsDisplay();

            try {
                await chrome.storage.local.set({
                    maimai_candidates: this.extractedData,
                    maimai_stats: this.stats
                });
            } catch (e) {
                console.log('Storage 保存失败');
            }

            MaimaiUtils.showNotification(`成功提取 ${candidates.length} 个候选人`, 'success');

        } catch (error) {
            console.error('❌ 提取失败:', error);
            MaimaiUtils.showNotification('提取失败: ' + error.message, 'error');
        }
    }

    handleExport(format) {
        if (this.extractedData.length === 0) {
            MaimaiUtils.showNotification('没有可导出的数据', 'warning');
            return;
        }

        const filename = `maimai_candidates_${MaimaiUtils.formatDate()}`;

        if (format === 'csv') {
            const csv = this.convertToCSV(this.extractedData);
            MaimaiUtils.downloadAsFile(csv, `${filename}.csv`, 'text/csv;charset=utf-8');
        } else {
            const json = JSON.stringify(this.extractedData, null, 2);
            MaimaiUtils.downloadAsFile(json, `${filename}.json`, 'application/json');
        }

        MaimaiUtils.showNotification(`已导出 ${this.extractedData.length} 条数据`, 'success');
    }

    convertToCSV(data) {
        const headers = ['姓名', '状态', '年龄', '工作年限', '学历', '所在地', '期望薪资', '标签', '提取时间'];
        const rows = data.map(item => [
            item.name || '',
            item.status || '',
            item.age || '',
            item.experience || '',
            item.education || '',
            item.location || '',
            item.expectedSalary || '',
            (item.tags || []).join('|'),
            item.extractedAt || ''
        ]);

        const BOM = '\uFEFF';
        return BOM + [headers.join(','), ...rows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n');
    }

    updateStatsDisplay() {
        const todayEl = this.panel?.querySelector('#todayCount');
        const totalEl = this.panel?.querySelector('#totalCount');
        if (todayEl) todayEl.textContent = this.stats.today;
        if (totalEl) totalEl.textContent = this.stats.total;
    }

    async loadStats() {
        try {
            const result = await chrome.storage.local.get(['maimai_stats', 'maimai_candidates']);
            if (result.maimai_stats) {
                this.stats = result.maimai_stats;
                this.updateStatsDisplay();
            }
            if (result.maimai_candidates) {
                this.extractedData = result.maimai_candidates;
            }
        } catch (e) {
            console.log('加载统计数据失败');
        }
    }

    show() {
        if (this.panel) {
            this.panel.classList.add('show');
            this.panel.style.display = 'block';
            this.isVisible = true;
        }
    }

    toggle() {
        this.isCollapsed ? this.expand() : this.collapse();
    }

    collapse() {
        if (this.panel) {
            this.panel.classList.add('collapsed');
            this.panel.querySelector('#panelToggle').textContent = '+';
            this.isCollapsed = true;
        }
    }

    expand() {
        if (this.panel) {
            this.panel.classList.remove('collapsed');
            this.panel.querySelector('#panelToggle').textContent = '−';
            this.isCollapsed = false;
        }
    }

    destroy() {
        if (this.panel) {
            this.panel.remove();
            this.panel = null;
        }
    }
}

if (typeof window !== 'undefined') {
    window.AssistantPanel = AssistantPanel;
}
