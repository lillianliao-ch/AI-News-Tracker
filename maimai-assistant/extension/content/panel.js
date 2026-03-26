// Maimai Assistant - 持久悬浮面板 UI (v3 - Tab切换：招聘+社区)
class AssistantPanel {
    constructor() {
        this.panel = null;
        this.assistant = null;
        this.isVisible = false;
        this.isCollapsed = false;
        this.stats = { today: 0, total: 0 };
        this.extractedData = [];
        this.detectedCount = 0;
        this.activeJobs = [];
        this.selectedJobId = null;
        this.lastGeneratedMessage = '';
        this.lastCandidate = null;
        this.activeTab = this._detectTab(); // 'recruit' | 'search'
        this.searchEngine = null;
    }

    _detectTab() {
        const url = window.location.href;
        // 搜索页或搜索引擎导航到的详情页 → 社区 tab
        if (url.includes('search_center') ||
            url.includes('/profile/detail') ||
            url.includes('/contact/') ||
            url.includes('/card/')) {

            // 但如果是从招聘页面进的详情页，保持 recruit tab
            // 通过检查是否有正在运行的搜索引擎状态来判断
            try {
                const saved = localStorage.getItem('maimai_search_engine_state');
                if (saved) {
                    const state = JSON.parse(saved);
                    if (state.running && state.phase === 'detail') {
                        return 'search';
                    }
                }
            } catch (e) { }

            if (url.includes('search_center')) return 'search';
            // 详情页默认用 recruit（当没有搜索引擎运行时）
            return 'recruit';
        }
        return 'recruit';
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

    // 新版面板 - Tab切换
    render() {
        if (!this.panel) return;

        const isRecruit = this.activeTab === 'recruit';
        const isSearch = this.activeTab === 'search';

        this.panel.innerHTML = `
      <div class="panel-header" style="background: white; padding: 16px 20px; border-bottom: 1px solid #dadce0; display: flex; align-items: center; justify-content: space-between;">
        <h3 class="panel-title" style="margin: 0; font-size: 16px; font-weight: 600; color: #191919; display: flex; align-items: center; gap: 8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0a66c2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            Talent CRM
        </h3>
        <button class="panel-toggle" id="panelToggle" style="background: none; border: none; font-size: 24px; color: #666; cursor: pointer; padding: 0;">&times;</button>
      </div>
      
      <div class="panel-content" style="padding: 16px; background: #f8f9fa; flex: 1; overflow-y: auto;">
        
        <!-- Tab 切换 -->
        <div class="panel-tab-bar" style="display: flex; background: white; border: 1px solid #dadce0; border-radius: 8px; padding: 4px; margin-bottom: 16px;">
          <button class="panel-tab ${isRecruit ? 'active' : ''}" data-tab="recruit" style="flex: 1; padding: 6px 0; border: none; border-radius: 6px; background: ${isRecruit ? '#f0f7ff' : 'transparent'}; color: ${isRecruit ? '#0a66c2' : '#666'}; font-weight: ${isRecruit ? '600' : '500'}; font-size: 13px; cursor: pointer; transition: all 0.2s;">Talent Profiling</button>
          <button class="panel-tab ${isSearch ? 'active' : ''}" data-tab="search" style="flex: 1; padding: 6px 0; border: none; border-radius: 6px; background: ${isSearch ? '#f0f7ff' : 'transparent'}; color: ${isSearch ? '#0a66c2' : '#666'}; font-weight: ${isSearch ? '600' : '500'}; font-size: 13px; cursor: pointer; transition: all 0.2s;">Community Search</button>
        </div>

        <!-- ========== TAB 1: 招聘 ========== -->
        <div class="tab-content" id="tabRecruit" style="display: ${isRecruit ? 'block' : 'none'};">
            
            <!-- White Card 1: 焦点候选人 Focus Candidate Operations -->
            <div style="background: white; border: 1px solid #dadce0; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size: 14px; font-weight: 600; color: #191919; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                    Focus Candidate
                    <div style="display: flex; gap: 8px;">
                        <span style="padding: 2px 8px; background: #e8f0fe; color: #1a73e8; border-radius: 12px; font-size: 11px; font-weight: 500;"><span id="detectedCount">0</span> Detected</span>
                        <button id="refreshBtn" title="🔄 Refresh Target" style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 0;">🔄</button>
                    </div>
                </div>

                <!-- Primary Action: AI Generate -->
                <div style="margin-bottom: 12px;">
                    <select id="jobSelect" style="width: 100%; padding: 8px 12px; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; color: #333; margin-bottom: 8px; appearance: auto; background: white; cursor: pointer; outline: none;">
                        <option value="auto">🎯 Auto Match Priority JD</option>
                    </select>
                    <button id="aiGenerateBtn" style="width: 100%; padding: 10px; background: #0a66c2; color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px;">
                        <span class="btn-icon">🤖</span> Generate Outreach Message
                    </button>
                    <div id="aiGenerateStatus" style="font-size: 12px; color: #666; margin-top: 6px; display: none; text-align: center;"></div>
                </div>

                <!-- Generated Message Result Area -->
                <div id="messageResultSection" style="display: none; background: #f8f9fa; border: 1px solid #e1e3e6; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-size: 12px; font-weight: 600; color: #191919; display: flex; align-items: center; gap: 4px;">
                            <span id="candidateName" style="color: #0a66c2;"></span>
                            <span id="jobUsed" style="color: #666; font-weight: 400; font-size: 11px;"></span>
                        </div>
                        <div style="font-size: 11px; color: #666;"><span id="charCount"></span></div>
                    </div>
                    <div id="generatedMessage" style="font-size: 13px; line-height: 1.5; color: #333; white-space: pre-wrap; word-break: break-all; max-height: 160px; overflow-y: auto; background: white; padding: 10px; border-radius: 6px; border: 1px solid #dadce0; margin-bottom: 8px;"></div>
                    
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <button id="fillMsgBtn" style="flex: 1; padding: 6px 12px; background: #f0f7ff; color: #0a66c2; border: 1px solid #c2d7f0; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s;">
                            Inject to Chat
                        </button>
                        <button id="copyMsgBtn" style="padding: 6px 12px; background: white; color: #666; border: 1px solid #dadce0; border-radius: 6px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                            📋 Copy
                        </button>
                        <label style="font-size: 12px; color: #666; display: flex; align-items: center; gap: 4px; cursor: pointer; width: 100%;">
                            <input type="checkbox" id="sendRequestCb" checked style="accent-color: #0a66c2;"> Track as Connection Request
                        </label>
                    </div>
                </div>

                <!-- Secondary Actions: Save & Update -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <button class="action-btn" id="importTalentBtn" style="width: 100%; padding: 8px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                        📥 Save to CRM
                    </button>
                    <button class="action-btn" id="markRepliedBtn" style="width: 100%; padding: 8px; background: white; color: #057642; border: 1px solid #b2d5c3; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                        ✅ Mark Replied
                    </button>
                    <button class="action-btn" id="updatePhoneBtn" style="grid-column: span 2; padding: 8px; background: white; color: #666; border: 1px dashed #dadce0; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                        📞 Update Phone from Clipboard
                    </button>
                    <button class="action-btn" id="importFriendsBtn" style="grid-column: span 2; padding: 8px; background: white; color: #666; border: 1px dashed #dadce0; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s; display: none;">
                        好友页导入
                    </button>
                </div>
            </div>

            <!-- White Card 2: 批量作业 Global Operations -->
            <details style="background: white; border: 1px solid #dadce0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <summary style="font-size: 14px; font-weight: 600; color: #191919; cursor: pointer; display: flex; align-items: center; gap: 6px; list-style: none;">
                    Global Batch Operations
                    <span style="margin-left: auto; color: #666; font-size: 12px;">▼</span>
                </summary>
                
                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0;">
                    <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center;">
                        <input type="number" id="batchCount" value="30" min="1" max="100" style="width: 60px; padding: 4px 8px; border: 1px solid #dadce0; border-radius: 6px; font-size: 12px; outline: none;" />
                        <span style="font-size: 12px; color: #666;">Cands/Page</span>
                        <input type="number" id="batchPages" value="1" min="1" max="50" style="width: 50px; padding: 4px 8px; border: 1px solid #dadce0; border-radius: 6px; font-size: 12px; margin-left: 8px; outline: none;" />
                        <span style="font-size: 12px; color: #666;">Pages</span>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <button id="batchAddFriendsBtn" style="width: 100%; padding: 8px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                            🤝 Batch Connect
                        </button>
                        <button id="batchSendMsgBtn" style="width: 100%; padding: 8px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                            💬 Batch Nurture (AI Message)
                        </button>
                        <button id="batchImportTalentBtn" style="width: 100%; padding: 8px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                            📥 Batch Save to CRM
                        </button>
                        <button id="extractBtn" style="width: 100%; padding: 8px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; display: none;">
                            提取信息
                        </button>
                        <div style="display: flex; gap: 6px;">
                            <button id="exportCsvBtn" style="flex: 1; padding: 4px; background: white; color: #666; border: 1px solid #dadce0; border-radius: 6px; font-size: 11px; cursor: pointer;">📄 CSV</button>
                            <button id="exportJsonBtn" style="flex: 1; padding: 4px; background: white; color: #666; border: 1px solid #dadce0; border-radius: 6px; font-size: 11px; cursor: pointer;">📋 JSON</button>
                        </div>
                    </div>

                    <!-- Progress Section -->
                    <div id="progressSection" style="display: none; margin-top: 12px; padding: 12px; background: #f0f7ff; border-radius: 8px; border: 1px solid #c2d7f0;">
                        <div style="height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; margin-bottom: 8px;">
                            <div id="progressFill" style="height: 100%; width: 0%; background: #0a66c2; transition: width 0.3s ease;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 11px; color: #0a66c2; margin-bottom: 6px;">
                            <span id="progressText">0/0</span>
                            <span id="progressPercent">0%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 500;">
                            <span style="color: #057642;">✓ <span id="successCount">0</span></span>
                            <span style="color: #d11124;">✗ <span id="failedCount">0</span></span>
                        </div>
                        <button id="stopBtn" style="width: 100%; margin-top: 8px; padding: 6px; background: white; color: #d11124; border: 1px solid #f8b4b4; border-radius: 6px; font-size: 12px; cursor: pointer;">
                            ⏹ Stop Operation
                        </button>
                    </div>
                </div>
            </details>

            <!-- Metadata footer -->
            <div style="margin-top: 16px; padding: 0 4px; display: flex; align-items: flex-start; justify-content: space-between; font-size: 11px; color: #999;">
                <label style="display: flex; align-items: center; gap: 4px; cursor: pointer; width: 60%;">
                    <input type="checkbox" id="forceCreateCheckbox" style="accent-color: #0a66c2; flex-shrink: 0;"> Ignore Dups (Force create instead of update)
                </label>
                <div style="text-align: right;">Today <span id="todayCount" style="color: #0a66c2; font-weight: 600;">${this.stats.today}</span><br>Total <span id="totalCount" style="color: #333;">${this.stats.total}</span></div>
            </div>

        </div><!-- /tabRecruit -->

        <!-- ========== TAB 2: 社区搜索 ========== -->
        <div class="tab-content" id="tabSearch" style="display: ${isSearch ? 'block' : 'none'};">
            <div style="background: white; border: 1px solid #dadce0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size: 14px; font-weight: 600; color: #191919; margin-bottom: 12px;">Community Search List</div>
                <textarea id="searchKeywords" class="search-textarea" placeholder="Keywords (one per line)" style="width: 100%; height: 80px; padding: 10px; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; margin-bottom: 12px; outline: none;"></textarea>
                
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    <select id="searchMode" style="flex: 1; padding: 8px; border: 1px solid #dadce0; border-radius: 6px; font-size: 13px; background: white; outline: none;">
                        <option value="first">First Result Only</option>
                        <option value="all">Collect All</option>
                    </select>
                    <label style="display: flex; align-items: center; gap: 4px; font-size: 13px; color: #333; cursor: pointer; padding: 0 8px;">
                        <input type="checkbox" id="searchAddFriend" style="accent-color: #0a66c2;"> Connect
                    </label>
                </div>
                
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    <button id="searchStartBtn" style="flex: 1; padding: 8px; background: #0a66c2; color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer;">▶ Start Auto Search</button>
                    <button id="searchExportBtn" style="flex: 1; padding: 8px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;">📥 Export</button>
                </div>
                
                <div style="display: flex; align-items: center; gap: 12px; font-size: 12px; color: #666; margin-bottom: 12px;">
                    Export as:
                    <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;"><input type="radio" name="exportMode" value="excel" checked style="accent-color: #0a66c2;"> Excel/CSV</label>
                    <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;"><input type="radio" name="exportMode" value="api" style="accent-color: #0a66c2;"> Cloud API</label>
                </div>
                
                <div style="font-size: 12px; color: #666; text-align: center;">
                    Collected <span id="searchResultCount" style="color: #0a66c2; font-weight: 600;">0</span> records
                </div>

                <!-- 搜索进度 -->
                <div id="searchProgressSection" style="display: none; margin-top: 16px; padding: 12px; background: #f0f7ff; border-radius: 8px; border: 1px solid #c2d7f0;">
                    <div style="height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; margin-bottom: 8px;">
                        <div id="searchProgressFill" style="height: 100%; width: 0%; background: #0a66c2; transition: width 0.3s ease;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #0a66c2; margin-bottom: 6px;">
                        <span id="searchProgressText">0/0</span>
                        <span id="searchProgressPercent">0%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 500;">
                        <span style="color: #057642;">✓ <span id="searchSuccessCount">0</span></span>
                        <span style="color: #d11124;">✗ <span id="searchFailedCount">0</span></span>
                    </div>
                    <button id="searchStopBtn" style="width: 100%; margin-top: 8px; padding: 6px; background: white; color: #d11124; border: 1px solid #f8b4b4; border-radius: 6px; font-size: 12px; cursor: pointer;">⏹ Stop</button>
                </div>
            </div>
        </div><!-- /tabSearch -->

      </div>
    `;
    }

    bindEvents() {
        if (!this.panel) return;

        // === Tab 切换 ===
        this.panel.querySelectorAll('.panel-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                this.activeTab = target;

                // 更新 Tab 高亮
                this.panel.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // 切换内容
                const recruitTab = this.panel.querySelector('#tabRecruit');
                const searchTab = this.panel.querySelector('#tabSearch');
                if (recruitTab) recruitTab.style.display = target === 'recruit' ? 'block' : 'none';
                if (searchTab) searchTab.style.display = target === 'search' ? 'block' : 'none';
            });
        });

        // === 搜索 Tab 事件 ===
        this._initSearchEngine();

        this.panel.querySelector('#searchStartBtn')?.addEventListener('click', () => {
            const textarea = this.panel.querySelector('#searchKeywords');
            const keywords = (textarea?.value || '').split('\n').map(s => s.trim()).filter(Boolean);
            if (keywords.length === 0) {
                MaimaiUtils.showNotification('请输入关键词', 'warning');
                return;
            }

            const mode = this.panel.querySelector('#searchMode')?.value || 'first';
            const addFriend = this.panel.querySelector('#searchAddFriend')?.checked || false;
            const exportMode = this.panel.querySelector('input[name="exportMode"]:checked')?.value || 'excel';

            const section = this.panel.querySelector('#searchProgressSection');
            if (section) section.classList.add('show');

            this.searchEngine?.start(keywords, mode, addFriend, exportMode);
        });

        this.panel.querySelector('#searchStopBtn')?.addEventListener('click', () => {
            this.searchEngine?.stop();
            MaimaiUtils.showNotification('搜索已停止', 'info');
        });

        this.panel.querySelector('#searchExportBtn')?.addEventListener('click', async () => {
            if (!this.searchEngine || this.searchEngine.state.results.length === 0) {
                MaimaiUtils.showNotification('暂无数据可导出', 'warning');
                return;
            }

            const exportMode = this.panel.querySelector('input[name="exportMode"]:checked')?.value || 'excel';

            if (exportMode === 'excel') {
                const csv = this.searchEngine.exportToCSV();
                if (csv) {
                    const ts = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
                    MaimaiUtils.downloadAsFile(csv, `脉脉搜索结果_${ts}.csv`, 'text/csv;charset=utf-8');
                    MaimaiUtils.showNotification(`已导出 ${this.searchEngine.state.results.length} 条`, 'success');
                }
            } else {
                const result = await this.searchEngine.exportToAPI();
                MaimaiUtils.showNotification(`API导入完成: 成功${result.success}, 失败${result.failed}`, result.failed > 0 ? 'warning' : 'success');
            }
        });

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

        // 从剪贴板更新电话
        this.panel.querySelector('#updatePhoneBtn')?.addEventListener('click', async () => {
            this.handleUpdatePhoneFromClipboard();
        });

        // 标记已回复
        this.panel.querySelector('#markRepliedBtn')?.addEventListener('click', async () => {
            this.handleMarkReplied();
        });

        // 批量导入当前页
        this.panel.querySelector('#batchImportTalentBtn')?.addEventListener('click', () => {
            const count = this.getBatchCount();
            const pages = this.getBatchPages();
            this.showProgress();
            this.assistant?.batchImportTalents(count, pages);
        });

        // 批量加好友
        this.panel.querySelector('#batchAddFriendsBtn')?.addEventListener('click', () => {
            const count = this.getBatchCount();
            const pages = this.getBatchPages();
            this.showProgress();
            this.assistant?.batchAddFriends(count, pages);
        });

        // 批量立即沟通（AI个性化消息）
        this.panel.querySelector('#batchSendMsgBtn')?.addEventListener('click', () => {
            const count = this.getBatchCount();
            const pages = this.getBatchPages();
            this.showProgress();
            this.assistant?.batchDirectChat(count, pages);
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
            const result = await chrome.storage.local.get(['apiBaseUrl']);
            const apiBase = result.apiBaseUrl || 'http://localhost:8502';
            const apiUrl = `${apiBase}/api/generate-message`;
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

            const aiResult = await response.json();

            if (aiResult.success) {
                this.lastGeneratedMessage = aiResult.message;
                this.lastCandidate = candidateData;

                // 显示生成的消息
                const msgSection = this.panel.querySelector('#messageResultSection');
                const msgEl = this.panel.querySelector('#generatedMessage');
                const nameEl = this.panel.querySelector('#candidateName');
                const charCountEl = this.panel.querySelector('#charCount');
                const jobUsedEl = this.panel.querySelector('#jobUsed');

                if (msgSection && msgEl) {
                    msgSection.style.display = 'block';
                    msgEl.textContent = aiResult.message;
                }
                if (nameEl) {
                    nameEl.textContent = `${candidateData.name} - ${candidateData.currentCompany || ''} ${candidateData.currentPosition || ''}`;
                }
                if (charCountEl) {
                    charCountEl.textContent = `${aiResult.char_count || aiResult.message.length}/300`;
                    charCountEl.style.color = (aiResult.char_count || aiResult.message.length) > 300 ? '#ff4d4f' : '#52c41a';
                }
                if (jobUsedEl && aiResult.job_used) {
                    jobUsedEl.textContent = `📌 ${aiResult.job_used.company} · ${aiResult.job_used.title}`;
                }

                MaimaiUtils.showNotification(`✨ 已为 ${candidateData.name} 生成AI个性化消息`, 'success');
                console.log('  候选人:', candidateData);
                console.log('  消息:', aiResult.message);
                console.log('  关联JD:', aiResult.job_used);
            } else {
                throw new Error(aiResult.error || '生成失败');
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

    // 从剪贴板读取电话并更新当前候选人
    async handleUpdatePhoneFromClipboard() {
        try {
            // 1. 读取剪贴板
            const text = await navigator.clipboard.readText();
            if (!text) {
                MaimaiUtils.showNotification('剪贴板为空，请先复制电话号码', 'warning');
                return;
            }

            // 2. 提取连续的11位数字 (以1开头)
            const cleanText = text.replace(/[\s-]/g, '');
            const match = cleanText.match(/1[3-9]\d{9}/);
            if (!match) {
                MaimaiUtils.showNotification('剪贴板中未检测到有效的手机号码', 'warning');
                return;
            }
            const phoneStr = match[0];

            // 3. 提取当前面板上的候选人信息
            let candidateData = null;
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                // 设置一个标志位告诉 extractor 不要再强行抓电话，只取名字和公司
                candidateData = extractor.extractFromTalentPanel();
            } else if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                candidateData = extractor.extractFromDetailPanel();
            }

            if (!candidateData || !candidateData.name) {
                MaimaiUtils.showNotification('请先在脉脉打开要更新的候选人详情面板', 'warning');
                return;
            }

            // 4. 发送给后端更新
            candidateData.phone = phoneStr; // 强制覆盖
            console.log(`📞 准备更新 ${candidateData.name} 的电话为: ${phoneStr}`);

            // 💡 安全检查：防止扩展上下文丢失导致的 chrome.storage 未定义错误
            let apiBase = 'http://localhost:8502';
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                try {
                    const result = await chrome.storage.local.get(['apiBaseUrl']);
                    if (result.apiBaseUrl) apiBase = result.apiBaseUrl;
                } catch (e) {
                    console.warn('⚠️ 读取 chrome.storage 失败，使用默认 API 地址:', e);
                }
            } else {
                console.warn('⚠️ chrome.storage 不可用，很有可能插件已自动更新，请刷新页面后重试。');
            }

            // 使用复用的 maimai-sync 接口
            const response = await fetch(`${apiBase}/api/candidate/maimai-sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...candidateData,
                    markReplied: true // 💡 核心需求：从剪贴板更新电话时，标记为已回复
                })
            });

            if (response.ok) {
                const resJson = await response.json();
                if (resJson.success) {
                    MaimaiUtils.showNotification(`✅ 成功更新 ${candidateData.name} 的电话: ${phoneStr}`, 'success');
                    console.log('✅ 电话更新结果:', resJson);
                } else {
                    throw new Error(resJson.error || '后端返回操作失败');
                }
            } else {
                throw new Error(`请求失败状态码: ${response.status}`);
            }

        } catch (error) {
            console.error('❌ 更新电话失败:', error);
            // 提示用户必须授权剪贴板读取或者其他错误
            if (error.name === 'NotAllowedError') {
                MaimaiUtils.showNotification('请允许网页读取剪贴板权限，或手动输入', 'error');
            } else {
                MaimaiUtils.showNotification(`更新失败: ${error.message}`, 'error');
            }
        }
    }

    // 💡 新增：标记当前人为已回复
    async handleMarkReplied() {
        console.log('✅ 尝试标记当前候选人为已回复...');

        try {
            // 1. 获取当前页面选中的候选人
            let candidateData = null;
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                candidateData = extractor.extractFromTalentPanel();
            } else if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                candidateData = extractor.extractFromDetailPanel();
            }

            if (!candidateData || !candidateData.name) {
                // 回退：尝试使用 lastCandidate
                candidateData = this.lastCandidate;
            }

            if (!candidateData || !candidateData.name) {
                MaimaiUtils.showNotification('请先在脉脉打开要标记的候选人详情面板', 'warning');
                return;
            }

            // 2. 获取 API Base
            let apiBase = 'http://localhost:8502';
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                try {
                    const result = await chrome.storage.local.get(['apiBaseUrl']);
                    if (result.apiBaseUrl) apiBase = result.apiBaseUrl;
                } catch (e) { console.warn('读取 API 地址失败', e); }
            }

            // 3. 调用同步接口，强制标记已回复
            const response = await fetch(`${apiBase}/api/candidate/maimai-sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...candidateData,
                    markReplied: true // 核心：标记已回复
                })
            });

            if (response.ok) {
                const resJson = await response.json();
                if (resJson.success) {
                    MaimaiUtils.showNotification(`✅ 已成功标记 ${candidateData.name} 为已回复状态`, 'success');
                    console.log('✅ 标记已回复成功:', resJson);
                } else {
                    throw new Error(resJson.error || '后端返回操作失败');
                }
            } else {
                throw new Error(`HTTP Error: ${response.status}`);
            }

        } catch (error) {
            console.error('❌ 标记已回复失败:', error);
            MaimaiUtils.showNotification('标记失败: ' + error.message, 'error');
        }
    }

    // 记录沟通日志到后端DB
    async _recordCommLog() {
        if (!this.lastCandidate) return;

        const jobSelect = this.panel.querySelector('#jobSelect');
        const jobId = jobSelect?.value !== 'auto' ? parseInt(jobSelect.value) : null;

        try {
            const result = await chrome.storage.local.get(['apiBaseUrl']);
            const apiBase = result.apiBaseUrl || 'http://localhost:8502';
            const apiUrl = `${apiBase}/api/comm-log`;
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
                    candidate_profile: this.lastCandidate // 用于后端自动建档
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
            const storageResult = await chrome.storage.local.get(['apiBaseUrl']);
            const apiBase = storageResult.apiBaseUrl || 'http://localhost:8502';
            const apiUrl = `${apiBase}/api/jobs/active?limit=30`;
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

                // 如果勾选了"发申请"，同时记录触达
                const sendRequestCb = this.panel.querySelector('#sendRequestCb');
                if (sendRequestCb && sendRequestCb.checked) {
                    this._recordOutreach();
                }
            }).catch(() => {
                MaimaiUtils.showNotification('复制失败', 'error');
            });
        }
    }

    // 记录触达(发申请)到后端 outreach_records
    async _recordOutreach() {
        if (!this.lastCandidate) return;

        const jobSelect = this.panel.querySelector('#jobSelect');
        const jobId = jobSelect?.value !== 'auto' ? parseInt(jobSelect.value) : null;

        try {
            const result = await chrome.storage.local.get(['apiBaseUrl']);
            const apiBase = result.apiBaseUrl || 'http://localhost:8502';
            const apiUrl = `${apiBase}/api/comm-log`;
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
                    create_outreach: true,
                    outreach_type: 'friend_request',
                    candidate_profile: this.lastCandidate // 用于后端自动建档
                })
            });
            console.log('📨 触达记录(发申请)已记录');
        } catch (e) {
            console.warn('记录触达失败:', e);
        }
    }

    // 获取批量处理数量
    getBatchCount() {
        const input = this.panel?.querySelector('#batchCount');
        const count = parseInt(input?.value) || 10;
        return Math.min(count, this.detectedCount || 100);
    }

    // 获取批量处理页数
    getBatchPages() {
        const input = this.panel?.querySelector('#batchPages');
        return parseInt(input?.value) || 1;
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

        // 自动同步批量操作数量为检测到的候选人数
        const batchInput = this.panel?.querySelector('#batchCount');
        if (batchInput && this.detectedCount > 0) {
            batchInput.value = this.detectedCount;
        }

        console.log(`📊 检测到 ${this.detectedCount} 个候选人卡片`);
    }

    // 初始化搜索引擎
    _initSearchEngine() {
        if (!window.SearchEngine) {
            console.log('⚠️ SearchEngine 未加载，跳过搜索初始化');
            return;
        }

        this.searchEngine = new SearchEngine();

        // 从保存的状态恢复 UI 表单字段
        const s = this.searchEngine.state;
        if (s.list && s.list.length > 0) {
            const textarea = this.panel?.querySelector('#searchKeywords');
            if (textarea) textarea.value = s.list.join('\n');
        }
        const modeSelect = this.panel?.querySelector('#searchMode');
        if (modeSelect && s.mode) modeSelect.value = s.mode;
        const addFriendCb = this.panel?.querySelector('#searchAddFriend');
        if (addFriendCb) addFriendCb.checked = !!s.addFriend;
        const exportRadio = this.panel?.querySelector(`input[name="exportMode"][value="${s.exportMode || 'excel'}"]`);
        if (exportRadio) exportRadio.checked = true;

        // 如果正在运行，显示进度区域
        if (s.running) {
            const section = this.panel?.querySelector('#searchProgressSection');
            if (section) section.classList.add('show');
        }

        // 进度回调
        this.searchEngine.onProgress((state) => {
            const { currentIndex, total, successful, failed, resultCount } = state;
            const percent = total > 0 ? Math.round((currentIndex / total) * 100) : 0;

            const fill = this.panel?.querySelector('#searchProgressFill');
            if (fill) fill.style.width = `${percent}%`;

            const text = this.panel?.querySelector('#searchProgressText');
            if (text) text.textContent = `${currentIndex}/${total}`;

            const pct = this.panel?.querySelector('#searchProgressPercent');
            if (pct) pct.textContent = `${percent}%`;

            const suc = this.panel?.querySelector('#searchSuccessCount');
            if (suc) suc.textContent = successful;

            const fail = this.panel?.querySelector('#searchFailedCount');
            if (fail) fail.textContent = failed;

            const count = this.panel?.querySelector('#searchResultCount');
            if (count) count.textContent = resultCount;
        });

        // 完成回调
        this.searchEngine.onComplete((results) => {
            MaimaiUtils.showNotification(`搜索完成，共 ${results.length} 条结果`, 'success');
            setTimeout(() => {
                const section = this.panel?.querySelector('#searchProgressSection');
                if (section) section.classList.remove('show');
            }, 3000);
        });

        // 恢复正在进行的搜索
        this.searchEngine.resumeIfRunning();

        // 更新结果计数
        const count = this.panel?.querySelector('#searchResultCount');
        if (count) count.textContent = this.searchEngine.state.results.length;
    }

    bindDragEvents() {
        // Disabled drag events for fixed right-anchored sidebar design
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
        if (text) {
            const pageInfo = (state.totalPages && state.totalPages > 1) ? ` (第${state.currentPage}/${state.totalPages}页)` : '';
            text.textContent = `${currentIndex}/${total}${pageInfo}`;
        }

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
            this.panel.style.display = 'flex';
            setTimeout(() => {
                this.panel.classList.add('show');
                document.body.style.width = 'calc(100% - 360px)';
                document.body.style.transition = 'width 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
            }, 10);
            this.isVisible = true;
        }
    }

    toggle() {
        this.isCollapsed ? this.expand() : this.collapse();
    }

    collapse() {
        if (this.panel) {
            this.panel.classList.add('collapsed');
            this.panel.classList.remove('show');
            document.body.style.width = '100%';
            this.panel.querySelector('#panelToggle').textContent = '+';
            this.isCollapsed = true;
        }
    }

    expand() {
        if (this.panel) {
            this.panel.classList.remove('collapsed');
            this.panel.classList.add('show');
            document.body.style.width = 'calc(100% - 360px)';
            this.panel.querySelector('#panelToggle').textContent = '−';
            this.isCollapsed = false;
        }
    }

    destroy() {
        if (this.panel) {
            document.body.style.width = '100%';
            this.panel.remove();
            this.panel = null;
        }
    }
}

if (typeof window !== 'undefined') {
    window.AssistantPanel = AssistantPanel;
}
