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
        this.activeJobs = []; // 活跃JD列表
        this.selectedJobId = null; // 选中的JD
        this.lastGeneratedMessage = ''; // 最近生成的消息
        this.lastCandidate = null; // 最近的候选人
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
        <!-- 1️⃣ 导入/查看（最顶部） -->
        <div class="panel-section" style="padding-bottom: 8px;">
          <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 6px;">
            <button class="action-btn" id="importFriendsBtn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; flex: 1; margin: 0; font-size: 10px; padding: 6px 4px;">
              📥 好友页导入
            </button>
            <button class="action-btn" id="importTalentBtn" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border: none; color: white; flex: 1; margin: 0; font-size: 10px; padding: 6px 4px;">
              📥 人才库导入
            </button>
            <button class="refresh-btn" id="refreshBtn" title="刷新检测" style="flex-shrink: 0;">🔄</button>
          </div>
          <div style="font-size: 10px; color: #888; text-align: center;">
            检测到 <span class="detection-count" id="detectedCount" style="color: #667eea; font-weight: 600;">0</span> 位候选人
          </div>
        </div>
        
        <!-- 2️⃣ AI 个性化消息（核心功能） -->
        <div class="panel-section ai-section" style="border-top: 1.5px solid #667eea; padding-top: 10px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 13px; font-weight: 600; color: #667eea;">✨ AI 个性化消息</span>
            <button id="refreshJobsBtn" style="font-size: 10px; color: #999; background: none; border: none; cursor: pointer;">🔄 刷新JD</button>
          </div>
          <select id="jobSelect" style="width: 100%; padding: 5px 8px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 11px; background: white; cursor: pointer; margin-bottom: 8px;">
            <option value="auto">🎯 自动匹配（紧急JD优先）</option>
          </select>
          <button class="action-btn" id="aiGenerateBtn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; font-weight: 600;">
            <span class="btn-icon">🤖</span> AI 生成个性化消息
          </button>
          <div id="aiGenerateStatus" style="font-size: 11px; color: #999; margin-top: 4px; display: none;"></div>
        </div>
        
        <!-- 生成的消息显示区 -->
        <div class="panel-section message-result-section" id="messageResultSection" style="display: none; background: linear-gradient(135deg, #f5f7ff 0%, #f0f4ff 100%); border-radius: 8px; padding: 10px; border: 1px solid #e0e6ff;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 11px; font-weight: 600; color: #333;">📨 AI 消息</span>
            <div>
              <button class="copy-btn" id="copyMsgBtn" style="font-size: 10px; padding: 2px 6px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer; margin-right: 4px;">📋 复制</button>
              <button class="copy-btn" id="fillMsgBtn" style="font-size: 10px; padding: 2px 6px; border: 1px solid #667eea; border-radius: 4px; background: #667eea; color: white; cursor: pointer;">📝 填入对话框</button>
            </div>
          </div>
          <div id="generatedMessage" style="font-size: 12px; line-height: 1.5; color: #333; white-space: pre-wrap; word-break: break-all; max-height: 120px; overflow-y: auto; background: white; padding: 8px; border-radius: 6px; border: 1px solid #e0e0e0;"></div>
          <div style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 10px; color: #999;">
              <span id="candidateName" style="color: #667eea;"></span>
            </span>
            <span style="font-size: 10px; color: #999;">
              <span id="charCount"></span>字
              <span id="jobUsed" style="color: #764ba2; margin-left: 4px;"></span>
            </span>
          </div>
        </div>

        <!-- 3️⃣ 批量操作（折叠） -->
        <details class="panel-section" style="margin-top: 6px;">
          <summary style="font-size: 11px; color: #999; cursor: pointer; padding: 4px 0;">⚡ 批量操作</summary>
          <div style="margin-top: 8px;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
              <label style="font-size: 11px; color: #666; white-space: nowrap;">数量:</label>
              <input type="number" id="batchCount" class="batch-input" value="10" min="1" max="100" style="width: 60px;" />
              <span style="font-size: 11px; color: #999;">条</span>
            </div>
            <button class="action-btn primary" id="batchAddFriendsBtn" style="margin-bottom: 6px;">
              <span class="btn-icon">🤝</span> 批量加好友
            </button>
            <button class="action-btn warning" id="batchSendMsgBtn" style="margin-bottom: 6px;">
              <span class="btn-icon">💬</span> 批量发消息
            </button>
            <div style="display: flex; gap: 6px; margin-bottom: 6px;">
              <button class="action-btn" id="extractBtn" style="flex: 1;">
                <span class="btn-icon">📋</span> 提取信息
              </button>
            </div>
            <details style="margin-top: 4px;">
              <summary style="font-size: 10px; color: #bbb; cursor: pointer;">📝 消息模板</summary>
              <textarea id="messageTemplate" class="template-textarea" 
                placeholder="您好{name}，我是XX公司的HR..."></textarea>
              <div class="template-hint" style="font-size: 10px;">变量: {name} {company} {position} {experience}</div>
            </details>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px; padding-top: 6px; border-top: 1px solid #eee;">
              <div style="display: flex; gap: 4px;">
                <button class="action-btn success" id="exportCsvBtn" style="font-size: 10px; padding: 3px 6px; width: auto;">📄 CSV</button>
                <button class="action-btn" id="exportJsonBtn" style="font-size: 10px; padding: 3px 6px; width: auto;">📋 JSON</button>
              </div>
              <div style="font-size: 10px; color: #999;">
                今日 <span id="todayCount" style="color: #667eea; font-weight: 600;">${this.stats.today}</span> · 
                总计 <span id="totalCount" style="color: #667eea; font-weight: 600;">${this.stats.total}</span>
              </div>
            </div>
          </div>
        </details>
        
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
          <button class="action-btn danger small" id="stopBtn" style="margin-top: 6px;">
            ⏹ 停止
          </button>
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

        // 好友页导入
        this.panel.querySelector('#importFriendsBtn')?.addEventListener('click', async () => {
            if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                await extractor.importOrView();
            } else {
                MaimaiUtils.showNotification('好友详情提取器未加载', 'error');
            }
        });

        // 人才库导入
        this.panel.querySelector('#importTalentBtn')?.addEventListener('click', async () => {
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                await extractor.importOrView();
            } else {
                MaimaiUtils.showNotification('人才库提取器未加载', 'error');
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

        // AI 生成个性化消息
        this.panel.querySelector('#aiGenerateBtn')?.addEventListener('click', async () => {
            await this.handleAIGenerateMessage();
        });

        // 刷新JD列表
        this.panel.querySelector('#refreshJobsBtn')?.addEventListener('click', async () => {
            await this.loadActiveJobs();
        });

        // 复制消息
        this.panel.querySelector('#copyMsgBtn')?.addEventListener('click', () => {
            this.handleCopyMessage();
        });

        // 填入对话框
        this.panel.querySelector('#fillMsgBtn')?.addEventListener('click', () => {
            this.handleFillMessage();
        });

        // 初始加载JD列表
        this.loadActiveJobs();

        // 拖拽
        this.bindDragEvents();

        // 双击折叠
        this.panel.querySelector('.panel-header')?.addEventListener('dblclick', () => this.toggle());
    }

    // AI 生成个性化消息（调用后端 LLM API）
    async handleAIGenerateMessage() {
        console.log('🤖 开始AI生成个性化消息...');
        const btn = this.panel.querySelector('#aiGenerateBtn');
        const statusEl = this.panel.querySelector('#aiGenerateStatus');

        // 提取当前候选人信息
        let candidateData = null;

        // 方法1: 从人才库面板提取
        if (window.TalentPanelExtractor) {
            const extractor = new TalentPanelExtractor();
            candidateData = extractor.extractFromTalentPanel();
        }

        // 方法2: 从招聘页候选人卡片提取（立即沟通弹窗上方的信息）
        if (!candidateData || !candidateData.name) {
            candidateData = this._extractFromRecruitPage();
        }

        if (!candidateData || !candidateData.name) {
            MaimaiUtils.showNotification('未能提取到候选人信息，请先打开候选人详情面板', 'warning');
            return;
        }

        // 获取选中的JD
        const jobSelect = this.panel.querySelector('#jobSelect');
        const selectedValue = jobSelect?.value;
        const jobId = (selectedValue && selectedValue !== 'auto') ? parseInt(selectedValue) : null;

        // 显示加载状态
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="btn-icon">⏳</span> AI 正在思考...';
        }
        if (statusEl) {
            statusEl.style.display = 'block';
            statusEl.textContent = `正在为 ${candidateData.name} 生成个性化消息...`;
        }

        try {
            const apiUrl = `${MaimaiConfig.api.baseUrl}/api/generate-message`;
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate: candidateData,
                    job_id: jobId
                }),
                signal: AbortSignal.timeout(MaimaiConfig.api.timeout)
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `API错误: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.lastGeneratedMessage = result.message;
                this.lastCandidate = candidateData;

                // 显示生成的消息
                const msgSection = this.panel.querySelector('#messageResultSection');
                const msgEl = this.panel.querySelector('#generatedMessage');
                const nameEl = this.panel.querySelector('#candidateName');
                const charCountEl = this.panel.querySelector('#charCount');
                const jobUsedEl = this.panel.querySelector('#jobUsed');

                if (msgSection && msgEl) {
                    msgSection.style.display = 'block';
                    msgEl.textContent = result.message;
                }
                if (nameEl) {
                    nameEl.textContent = `${candidateData.name} - ${candidateData.currentCompany || ''} ${candidateData.currentPosition || ''}`;
                }
                if (charCountEl) {
                    charCountEl.textContent = `${result.char_count || result.message.length}/300`;
                    charCountEl.style.color = (result.char_count || result.message.length) > 300 ? '#ff4d4f' : '#52c41a';
                }
                if (jobUsedEl && result.job_used) {
                    jobUsedEl.textContent = `📌 ${result.job_used.company} · ${result.job_used.title}`;
                }

                MaimaiUtils.showNotification(`✨ 已为 ${candidateData.name} 生成AI个性化消息`, 'success');
                console.log('  候选人:', candidateData);
                console.log('  消息:', result.message);
                console.log('  关联JD:', result.job_used);
            } else {
                throw new Error(result.error || '生成失败');
            }
        } catch (error) {
            console.error('❌ AI消息生成失败:', error);
            MaimaiUtils.showNotification(`AI消息生成失败: ${error.message}`, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<span class="btn-icon">🤖</span> AI 生成个性化消息';
            }
            if (statusEl) {
                statusEl.style.display = 'none';
            }
        }
    }

    // 从招聘搜索页提取候选人信息（立即沟通弹窗）
    _extractFromRecruitPage() {
        // 试图从立即沟通弹窗提取
        const dialog = document.querySelector('.recruit-direct-dialog, .ant-modal-content, [class*="dialog"]');
        if (dialog) {
            const name = dialog.querySelector('.name, [class*="name"]')?.textContent?.trim();
            const desc = dialog.querySelector('.desc, [class*="desc"]')?.textContent?.trim();
            if (name) {
                return { name, currentCompany: desc || '', currentPosition: '' };
            }
        }

        // 试图从当前选中/悬停的候选人卡片提取
        const cards = document.querySelectorAll('.talent-card, [class*="talent-card"], [class*="candidate-card"]');
        for (const card of cards) {
            const nameEl = card.querySelector('.name, [class*="name"]');
            const name = nameEl?.textContent?.trim();
            if (!name) continue;

            // 获取工作信息
            const workInfo = card.querySelector('.work-info, [class*="work"]')?.textContent?.trim() || '';
            const eduInfo = card.querySelector('.edu-info, [class*="edu"]')?.textContent?.trim() || '';
            const tagsEls = card.querySelectorAll('.tag, [class*="tag"]');
            const skills = Array.from(tagsEls).map(t => t.textContent.trim()).filter(Boolean);

            return {
                name,
                currentCompany: workInfo.split(/[·,，]/)[0] || '',
                currentPosition: workInfo.split(/[·,，]/)[1] || '',
                education: eduInfo,
                skills
            };
        }

        return null;
    }

    // 填入对话框
    handleFillMessage() {
        if (!this.lastGeneratedMessage) {
            MaimaiUtils.showNotification('请先生成消息', 'warning');
            return;
        }

        // 查找立即沟通对话框的输入区域
        const selectors = [
            'textarea[placeholder*="沟通"]',
            'textarea[placeholder*="打招呼"]',
            '.recruit-direct-dialog textarea',
            '.ant-modal-content textarea',
            '[class*="dialog"] textarea',
            '[class*="modal"] textarea',
            'textarea',
        ];

        let textarea = null;
        for (const sel of selectors) {
            textarea = document.querySelector(sel);
            if (textarea) break;
        }

        if (textarea) {
            // 设置值并触发事件
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(textarea, this.lastGeneratedMessage);
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));

            MaimaiUtils.showNotification('消息已填入对话框', 'success');

            // 记录沟通日志
            this._recordCommLog();
        } else {
            // 回退：复制到剪贴板
            navigator.clipboard.writeText(this.lastGeneratedMessage).then(() => {
                MaimaiUtils.showNotification('未找到对话框，已复制到剪贴板', 'warning');
                this._recordCommLog();
            });
        }
    }

    // 记录沟通日志到后端DB
    async _recordCommLog() {
        if (!this.lastCandidate) return;

        const jobSelect = this.panel.querySelector('#jobSelect');
        const jobId = jobSelect?.value !== 'auto' ? parseInt(jobSelect.value) : null;

        try {
            const apiUrl = `${MaimaiConfig.api.baseUrl}/api/comm-log`;
            await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_name: this.lastCandidate.name,
                    message: this.lastGeneratedMessage,
                    channel: 'maimai_direct',
                    job_id: jobId,
                    candidate_company: this.lastCandidate.currentCompany || '',
                    candidate_position: this.lastCandidate.currentPosition || '',
                })
            });
            console.log('📝 沟通日志已记录');
        } catch (e) {
            console.warn('记录沟通日志失败:', e);
        }
    }

    // 加载活跃JD列表
    async loadActiveJobs() {
        try {
            const apiUrl = `${MaimaiConfig.api.baseUrl}/api/jobs/active?limit=30`;
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`API错误: ${response.status}`);

            const result = await response.json();
            if (result.success) {
                this.activeJobs = result.jobs;
                this._renderJobSelect();
                console.log(`📋 已加载 ${result.count} 个活跃JD`);
            }
        } catch (e) {
            console.warn('加载JD列表失败:', e);
        }
    }

    // 渲染JD下拉选择
    _renderJobSelect() {
        const select = this.panel?.querySelector('#jobSelect');
        if (!select) return;

        // 保留第一个auto选项
        select.innerHTML = '<option value="auto">🎯 自动匹配（紧急JD优先）</option>';

        for (const job of this.activeJobs) {
            const opt = document.createElement('option');
            opt.value = job.id;
            const urgencyIcon = job.urgency >= 2 ? '🔴' : (job.urgency >= 1 ? '🟡' : '');
            const hc = job.headcount ? ` HC:${job.headcount}` : '';
            opt.textContent = `${urgencyIcon} ${job.company} · ${job.title}${hc}`;
            select.appendChild(opt);
        }
    }

    // 复制消息
    handleCopyMessage() {
        const msgEl = this.panel.querySelector('#generatedMessage');
        if (msgEl && msgEl.textContent) {
            navigator.clipboard.writeText(msgEl.textContent).then(() => {
                MaimaiUtils.showNotification('消息已复制到剪贴板', 'success');
                this._recordCommLog();
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
            countEl.textContent = `${this.detectedCount}`;
            countEl.style.color = this.detectedCount > 0 ? '#667eea' : '#999';
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
