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
        this._expOpen = { work: true, edu: true }; // 记录折叠状态
    }

    // --- Utils ---
    _esc(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
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
      <div class="panel-header" style="background: white; padding: 16px 20px; border-bottom: 1px solid #dadce0; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;">
        <h3 class="panel-title" style="margin: 0; font-size: 16px; font-weight: 600; color: #191919; display: flex; align-items: center; gap: 8px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0a66c2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            Talent CRM
        </h3>
        <button class="panel-toggle" id="panelToggle" style="background: none; border: none; font-size: 24px; color: #666; cursor: pointer; padding: 0;">&times;</button>
      </div>
      <div class="panel-tab-bar" style="margin: 12px 16px 0 16px; display: flex; background: #f0f0f0; border-radius: 8px; padding: 3px; flex-shrink: 0;">
          <button class="panel-tab" data-tab="batch" style="flex: 1; border: none; background: transparent; padding: 8px; font-size: 13px; font-weight: 500; color: #666; cursor: pointer; border-radius: 6px; transition: all 0.2s;">⚡ 批量作业</button>
          <button class="panel-tab active" data-tab="profile" style="flex: 1; border: none; background: #fff; border-radius: 6px; padding: 8px; font-size: 13px; font-weight: 600; color: #191919; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: all 0.2s;">👤 单人档案</button>
      </div>
      
      <div class="panel-content" style="padding: 16px; background: #f8f9fa; flex: 1; overflow-y: auto;">
        
        <!-- Tab 1: 批量作业 -->
        <div id="tabBatch" style="display: none;">
            <div style="background: white; border: 1px solid #dadce0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size: 14px; font-weight: 600; color: #191919; margin-bottom: 16px; display: flex; align-items: center; gap: 6px;">
                    ⚡ 全局批量作业
                </div>
                
                <div>
                    <div style="display: flex; gap: 8px; margin-bottom: 16px; align-items: center;">
                        <input type="number" id="batchCount" value="30" min="1" max="100" style="width: 60px; padding: 6px 8px; border: 1px solid #dadce0; border-radius: 6px; font-size: 13px; outline: none;" />
                        <span style="font-size: 13px; color: #666;">人/页</span>
                        <input type="number" id="batchPages" value="1" min="1" max="50" style="width: 50px; padding: 6px 8px; border: 1px solid #dadce0; border-radius: 6px; font-size: 13px; margin-left: 8px; outline: none;" />
                        <span style="font-size: 13px; color: #666;">页数</span>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <button id="batchAddFriendsBtn" style="width: 100%; padding: 10px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                            🤝 批量加好友
                        </button>
                        <button id="batchSendMsgBtn" style="width: 100%; padding: 10px; background: white; color: #333; border: 1px solid #dadce0; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                            💬 批量沟通
                        </button>
                        <button id="batchImportTalentBtn" style="width: 100%; padding: 10px; background: #0a66c2; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;">
                            📥 批量导入
                        </button>
                    </div>

                    <!-- Progress Section -->
                    <div id="progressSection" style="display: none; margin-top: 16px; padding: 16px; background: #f0f7ff; border-radius: 8px; border: 1px solid #c2d7f0;">
                        <div style="height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; margin-bottom: 8px;">
                            <div id="progressFill" style="height: 100%; width: 0%; background: #0a66c2; transition: width 0.3s ease;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #0a66c2; margin-bottom: 8px;">
                            <span id="progressText">0/0</span>
                            <span id="progressPercent">0%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 500;">
                            <span style="color: #057642;">✓ <span id="successCount">0</span> 成功</span>
                            <span style="color: #d11124;">✗ <span id="failedCount">0</span> 失败</span>
                        </div>
                        <button id="stopBtn" style="width: 100%; margin-top: 12px; padding: 8px; background: white; color: #d11124; border: 1px solid #f8b4b4; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer;">
                            ⏹ 停止当前作业
                        </button>
                    </div>
                </div>
            </div>

            <!-- Metadata footer -->
            <div style="margin-top: 16px; padding: 0 4px; text-align: right; font-size: 11px; color: #999;">
                <div>今日处理 <span id="todayCount" style="color: #0a66c2; font-weight: 600;">${this.stats.today}</span> | 历史总计 <span id="totalCount" style="color: #333;">${this.stats.total}</span></div>
            </div>
        </div>

        <!-- Tab 2: 单人档案 (CRM) -->
        <div id="tabProfile" style="display: block;" class="crm-container">
            <!-- 状态头：提取到名字时显示 -->
            <div id="crmProfileHeader" class="crm-card" style="padding: 10px 14px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div id="crmName" class="crm-title" style="font-size: 15px; margin-bottom: 2px;">未获取姓名</div>
                    <div id="crmTitle" class="crm-subtitle" style="font-size: 11px;">-</div>
                </div>
                <div id="crmEvalScore" class="crm-eval-score" style="margin: 0; padding: 3px 8px; font-size: 11px;">AI 适配度: 暂无</div>
            </div>

            <!-- State 2: 找到人但未入库 (Not Imported) -->
            <div id="crmStateNotImportedFull" style="display: none;">
                <div id="crmImportStateContainer" style="padding: 24px; text-align: center; border-radius: 8px; margin-bottom: 8px;">
                    <div style="font-size: 42px; color: #64748b; margin-bottom: 12px;">👤</div>
                    <div style="font-size: 15px; font-weight: 500; color: #334155; margin-bottom: 4px;">此人才尚未导入系统</div>
                    <div style="font-size: 13px; color: #64748b; margin-bottom: 16px;">点击下方按钮提取并导入</div>
                    <button class="crm-btn crm-btn-primary" id="crmBigImportBtn" style="width: 100%; padding: 10px; font-size: 13px; border-radius: 6px;">📥 导入人才信息</button>
                </div>
            </div>

            <!-- SHARED State 1 & 2: Quick Actions -->
            <div id="crmQuickActionsContainer" style="display: none;">
                <div class="crm-card" style="padding: 14px;">
                    <div class="crm-section-title" style="margin-bottom: 12px;">✨ 快速操作</div>
                    <div class="crm-action-grid" style="grid-template-columns: 1fr; gap: 8px;">
                        <button class="crm-btn crm-btn-outline" id="crmQuickGenerateMsgBtn" style="width: 100%; color: #333; border-color: #d1d5db; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.05); padding: 8px; font-size: 13px;">✨ 快速生成消息</button>
                    </div>
                </div>
            </div>

            <!-- State 3: 已入库，满状态面板 -->
            <div id="crmAdvancedActions" style="display: none;">
                <!-- 1. AI 评估 -->
                <div class="crm-card">
                    <div class="crm-section-title" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0;">
                        <span>🧠 AI 评估</span>
                        <span id="crmEvalEmptyText" style="display:none; color: #999; font-size: 11px; font-weight: normal; font-style: italic;">尚未评估。</span>
                    </div>
                    <div id="crmEvalContent" class="crm-ul" style="margin-top: 8px;"></div>
                </div>

                <!-- 2. 联系方式 -->
                <div class="crm-card">
                    <div class="crm-section-title" style="justify-content: space-between;">
                        <span>📇 联系方式</span>
                        <button class="crm-btn crm-btn-outline" style="padding: 4px 10px; font-size: 11px;" id="crmUpdatePhoneBtn">从剪贴板更新</button>
                    </div>
                    <div class="crm-contact-grid">
                        <div class="crm-contact-chip"><span style="font-size:13px;">✉️</span> <span id="crmEmail">-</span></div>
                        <div class="crm-contact-chip"><span style="font-size:13px;">📞</span> <span id="crmPhone">-</span></div>
                        <div class="crm-contact-chip"><span style="font-size:13px;">💬</span> <span id="crmWechat">-</span></div>
                    </div>
                </div>

                <!-- 3. 操作区 -->
                <div class="crm-card">
                    <div class="crm-section-title" style="margin-bottom: 8px;">⚡ 操作</div>
                    <div class="crm-action-grid" style="grid-template-columns: 1fr 1fr; gap: 6px;">
                        <button class="crm-btn crm-btn-primary" id="crmImportTalentBtn">同步更新(搜索)</button>
                        <button class="crm-btn crm-btn-primary" style="background: #057642;" id="crmImportFriendBtn">收录好友(好友页)</button>
                        <button class="crm-btn crm-btn-outline" id="crmDbEnhanceBtn" style="color: #7c3aed; border-color: #ddd6fe; background: #f5f3ff;">✨ DB增强消息</button>
                    </div>
                </div>

                <!-- 4. 触达状态 -->
                <div class="crm-card">
                    <div class="crm-status-bar" style="margin-bottom: 8px; justify-content: space-between;">
                        <div class="crm-section-title" style="margin: 0;">🤝 触达状态</div>
                        <div class="crm-status-badge" id="crmStatusBadge">未触达</div>
                    </div>
                    <div class="crm-outreach-actions" id="crmOutreachActions">
                        <button class="crm-outreach-btn" id="crmMarkContactedBtn" style="flex: 1;">📤 标记触达</button>
                        <button class="crm-outreach-btn" id="crmMarkRepliedBtn" style="flex: 1;">✅ 标记已回复</button>
                    </div>
                </div>

                <!-- 5. 标签 -->
                <div class="crm-card">
                    <div class="crm-section-title">🏷️ 标签</div>
                    <div class="crm-tags-wrap" id="crmTagsGroup" style="min-height: 24px; margin-bottom: 8px;">
                        <div style="color: #999; font-size: 12px; font-style: italic;">暂无标签</div>
                    </div>
                    <div style="border-top:1px solid #f0f0f0;padding-top:8px;">
                        <div style="font-size:10px;color:#999;margin-bottom:6px;">人才标签（点击切换）</div>
                        <div class="crm-tags-wrap" id="crmInteractiveLabels">
                            <button class="crm-label-toggle" data-label="正在看机会">正在看机会</button>
                            <button class="crm-label-toggle" data-label="高潜">高潜</button>
                            <button class="crm-label-toggle" data-label="重点关注">重点关注</button>
                            <button class="crm-label-toggle" data-label="主动求职">主动求职</button>
                            <button class="crm-label-toggle" data-label="被动人才">被动人才</button>
                            <button class="crm-label-toggle" data-label="精准匹配">精准匹配</button>
                        </div>
                    </div>
                </div>

                <!-- 6. 工作经历 & 教育经历 (动态挂载点) -->
                <div id="crmExperienceContainer"></div>
                
                <!-- 8. 备注 -->
                <div class="crm-card" style="margin-top: 16px;">
                    <div class="crm-section-title">📝 备注</div>
                    <textarea class="crm-notes-area" id="crmNotesArea" placeholder="添加备注..." style="height: 60px;"></textarea>
                </div>

                <!-- 9. 沟通记录 (动态挂载点) -->
                <div id="crmCommLogContainer" style="margin-top: 16px;"></div>

            </div> <!-- End crmAdvancedActions -->
        </div>

      </div>
    `;
    }

    bindEvents() {
        if (!this.panel) return;

        // Tab 切换逻辑
        const tabs = this.panel.querySelectorAll('.panel-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                tabs.forEach(t => t.classList.remove('active'));
                const target = e.currentTarget;
                target.classList.add('active');
                
                const tabName = target.getAttribute('data-tab');
                this.panel.querySelector('#tabBatch').style.display = tabName === 'batch' ? 'block' : 'none';
                this.panel.querySelector('#tabProfile').style.display = tabName === 'profile' ? 'block' : 'none';
            });
        });

        this.panel.querySelector('#aiExtractBtn')?.addEventListener('click', async () => {
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                await extractor.importOrView();
                this._lastDbCheckedCandidateName = null;
                setTimeout(() => { this.syncCurrentProfile(); }, 800);
            } else {
                MaimaiUtils.showNotification('未找到招聘版提取器', 'warning');
            }
        });

        this.panel.querySelector('#aiExtractFriendBtn')?.addEventListener('click', async () => {
            if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                await extractor.importOrView();
                this._lastDbCheckedCandidateName = null;
                setTimeout(() => { this.syncCurrentProfile(); }, 800);
            } else {
                MaimaiUtils.showNotification('未找到好友详情页面', 'warning');
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

        this.panel.querySelector('#crmImportTalentBtn')?.addEventListener('click', async () => {
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                await extractor.importOrView();
                this._lastDbCheckedCandidateName = null;
                setTimeout(() => { this.syncCurrentProfile(); }, 800);
            } else { MaimaiUtils.showNotification('人才库提取器未加载', 'error'); }
        });

        this.panel.querySelector('#crmImportFriendBtn')?.addEventListener('click', async () => {
            if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                await extractor.importOrView();
                this._lastDbCheckedCandidateName = null;
                setTimeout(() => { this.syncCurrentProfile(); }, 800);
            } else { MaimaiUtils.showNotification('好友详情提取器未加载', 'error'); }
        });

        // Tab 2: 一键巨屏导入按钮（智能查收对应页面的数据抽取器）
        this.panel.querySelector('#crmBigImportBtn')?.addEventListener('click', async () => {
            let extracted = false;
            let btn = this.panel.querySelector('#crmBigImportBtn');
            const originalText = btn ? btn.textContent : '';
            if (btn) { btn.disabled = true; btn.textContent = '📥 正在收录...'; }
            
            try {
                // 明确区分当前是好友页还是招聘库搜索页 (使用URL强检测)
                const url = window.location.href.toLowerCase();
                const isFriendsPage = url.includes('/groups') || url.includes('/contact') || url.includes('/friend') || document.querySelector('.asideHeaderRight___2X0_x, .friend-detail-wrapper, #myIframe, .contact_detail_normal_card') !== null;

                if (isFriendsPage && window.DetailPanelExtractor) {
                    const extractor = new DetailPanelExtractor();
                    if (extractor.extractFromDetailPanel()?.name) {
                        await extractor.importOrView();
                        extracted = true;
                    }
                } else if (!isFriendsPage && window.TalentPanelExtractor) {
                    const extractor = new TalentPanelExtractor();
                    if (extractor.extractFromTalentPanel()?.name) {
                        await extractor.importOrView();
                        extracted = true;
                    }
                }
                
                // 兜底策略：如果上面的主干没名字，再交叉尝试一次
                if (!extracted) {
                    if (window.DetailPanelExtractor) {
                        const extractor = new DetailPanelExtractor();
                        if (extractor.extractFromDetailPanel()?.name) {
                            await extractor.importOrView();
                            extracted = true;
                        }
                    }
                }
                if (!extracted) {
                    if (window.TalentPanelExtractor) {
                        const extractor = new TalentPanelExtractor();
                        if (extractor.extractFromTalentPanel()?.name) {
                            await extractor.importOrView();
                            extracted = true;
                        }
                    }
                }

                if (!extracted) {
                    MaimaiUtils.showNotification('未能提取到姓名等关键信息，请确保页面右侧已完全展开候选卡片！', 'error');
                } else {
                    // 入库成功，强行清空缓存短路判断，主动刷新单人画像
                    this._lastDbCheckedCandidateName = null;
                    setTimeout(() => { this.syncCurrentProfile(); }, 800);
                }
            } finally {
                if (btn) { btn.disabled = false; btn.textContent = originalText; }
            }
        });

        this.panel.querySelector('#crmDbEnhanceBtn')?.addEventListener('click', async () => {
            await this.handleAIGenerateMessage(true); // 传入 isCrm=true 标志
        });

        this.panel.querySelector('#crmUpdatePhoneBtn')?.addEventListener('click', async () => {
            this.handleUpdatePhoneFromClipboard();
        });

        this.panel.querySelector('#crmMarkRepliedBtn')?.addEventListener('click', async () => {
            this.handleMarkReplied();
        });

        this.panel.querySelector('#crmMarkContactedBtn')?.addEventListener('click', async () => {
            this.handleMarkContacted();
        });

        this.panel.querySelectorAll('.crm-label-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleToggleLabel(e.target.dataset.label);
            });
        });

        this.panel.querySelector('#crmFillMsgBtn')?.addEventListener('click', () => {
            this.handleFillMessage();
        });

        this.panel.querySelector('#crmCopyMsgBtn')?.addEventListener('click', () => {
            this.handleCopyMessage();
        });

        const stubButtons = ['#crmDownloadCvBtn', '#crmReEvaluateBtn', '#crmRetagBtn'];
        stubButtons.forEach(selector => {
            this.panel.querySelector(selector)?.addEventListener('click', () => {
                MaimaiUtils.showNotification('该功能依赖下周后端接口排期，敬请期待', 'info');
            });
        });

        // 初始加载JD列表
        this.loadActiveJobs();

        // 拖拽
        this.bindDragEvents();

        // 双击折叠
        this.panel.querySelector('.panel-header')?.addEventListener('dblclick', () => this.toggle());
    }

    // AI 生成个性化消息（调用后端 LLM API）
    async handleAIGenerateMessage(isCrm = false) {
        console.log('🤖 开始AI生成个性化消息...', { isCrm });
        const btn = isCrm ? this.panel.querySelector('#crmDbEnhanceBtn') : this.panel.querySelector('#aiGenerateBtn');
        const statusEl = isCrm ? null : this.panel.querySelector('#aiGenerateStatus');

        // 提取当前候选人信息
        let candidateData = null;

        if (isCrm && this.activeDbData) {
            // 全新逻辑: DB增强消息直接从数据库实体投影数据，不再依赖前端页面抽取，告别“未能提取信息”报错！
            candidateData = {
                name: this.activeDbData.name,
                currentCompany: this.activeDbData.current_company,
                currentPosition: this.activeDbData.current_title,
                workExperiences: this.activeDbData.work_experiences ? this.activeDbData.work_experiences.map(w => ({
                    company: w.company, position: w.title || w.position, duration: w.period || w.time, description: w.description
                })) : [],
                educationDetails: this.activeDbData.education_details ? this.activeDbData.education_details.map(e => ({
                    school: e.school, degree: e.degree, major: e.major
                })) : [],
                skills: this.activeDbData.talent_labels || [],
                aiSummary: this.activeDbData.ai_summary,
                notes: this.activeDbData.notes
            };
        } else {
            // 方法1: 从人才库面板提取
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                candidateData = extractor.extractFromTalentPanel();
            }

            // 方法2: 从招聘页候选人卡片提取（立即沟通弹窗上方的信息）
            if (!candidateData || !candidateData.name) {
                candidateData = this._extractFromRecruitPage();
            }
        }

        if (!candidateData || !candidateData.name) {
            MaimaiUtils.showNotification(isCrm ? '未能找到当前用户的数据库画像，请先进行收录操作' : '未能提取到候选人信息，请先打开候选人详情面板', 'warning');
            return;
        }

        // 获取选中的JD
        const jobSelect = this.panel.querySelector('#jobSelect');
        const selectedValue = jobSelect?.value;
        const jobId = (selectedValue && selectedValue !== 'auto') ? parseInt(selectedValue) : null;

        // 显示加载状态
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = isCrm ? '<span class="btn-icon">⏳</span> 生成中...' : '<span class="btn-icon">⏳</span> AI 正在思考...';
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

                if (isCrm) {
                    const crmMsgContainer = this.panel.querySelector('#crmDbMessageContainer');
                    const crmMsgEl = this.panel.querySelector('#crmGeneratedMessage');
                    const crmCharCountEl = this.panel.querySelector('#crmMsgCharCount');
                    
                    if (crmMsgContainer && crmMsgEl) {
                        crmMsgContainer.style.display = 'block';
                        crmMsgEl.textContent = aiResult.message;
                    }
                    if (crmCharCountEl) {
                        crmCharCountEl.textContent = `${aiResult.char_count || aiResult.message.length}/300`;
                        crmCharCountEl.style.color = (aiResult.char_count || aiResult.message.length) > 300 ? '#d11124' : '#666';
                    }
                } else {
                    // 显示生成的消息 (Tab 1)
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
                btn.innerHTML = isCrm ? '✨ DB增强消息' : '<span class="btn-icon">🤖</span> AI 生成个性化消息';
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

    async handleMarkContacted() {
        console.log('✅ 尝试标记当前候选人为已触达...');
        try {
            let candidateData = null;
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                candidateData = extractor.extractFromTalentPanel();
            } else if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                candidateData = extractor.extractFromDetailPanel();
            }

            if (!candidateData || !candidateData.name) {
                candidateData = this.lastCandidate;
            }

            if (!candidateData || !candidateData.name) {
                MaimaiUtils.showNotification('请先在脉脉打开要标记的候选人详情面板', 'warning');
                return;
            }

            let apiBase = 'http://localhost:8502';
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                try {
                    const result = await chrome.storage.local.get(['apiBaseUrl']);
                    if (result.apiBaseUrl) apiBase = result.apiBaseUrl;
                } catch (e) { console.warn('读取 API 地址失败', e); }
            }

            const response = await fetch(`${apiBase}/api/candidate/maimai-sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...candidateData,
                    markContacted: true 
                })
            });

            if (response.ok) {
                const resJson = await response.json();
                if (resJson.success) {
                    MaimaiUtils.showNotification(`✅ 已成功标记 ${candidateData.name} 为已触达状态`, 'success');
                    const badge = this.panel.querySelector('#crmStatusBadge');
                    if (badge) {
                        badge.textContent = '📤 已触达';
                        badge.style.background = '#fef3c7';
                        badge.style.color = '#92400e';
                    }
                } else {
                    throw new Error(resJson.error || '后端返回操作失败');
                }
            } else {
                throw new Error(`HTTP Error: ${response.status}`);
            }

        } catch (error) {
            console.error('❌ 标记已触达失败:', error);
            MaimaiUtils.showNotification('标记失败: ' + error.message, 'error');
        }
    }

    async handleToggleLabel(label) {
        if (!this._lastSyncedCandidateId || !this.activeDbData) return MaimaiUtils.showNotification('请先系统录入人才', 'warning');
        
        let activeLabels = Array.isArray(this.activeDbData.talent_labels) 
          ? [...this.activeDbData.talent_labels] 
          : [];
        
        if (activeLabels.includes(label)) {
          activeLabels = activeLabels.filter(l => l !== label);
        } else {
          activeLabels.push(label);
        }

        try {
          const btn = this.panel?.querySelector(`.crm-label-toggle[data-label="${label}"]`);
          if (btn) btn.style.opacity = '0.5';

          let apiBase = 'http://localhost:8502';
          if (chrome && chrome.storage) {
            const res = await chrome.storage.local.get(['apiBaseUrl']);
            if (res.apiBaseUrl) apiBase = res.apiBaseUrl;
          }

          const resp = await fetch(`${apiBase}/api/candidate/${this._lastSyncedCandidateId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ talent_labels: activeLabels })
          });
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          
          this.activeDbData.talent_labels = activeLabels;
          
          if (btn) {
            btn.style.opacity = '1';
            btn.classList.toggle('active');
          }
          
          const tagsGroup = this.panel.querySelector('#crmTagsGroup');
          if (tagsGroup && activeLabels.length > 0) {
              tagsGroup.innerHTML = '';
              activeLabels.forEach(t => {
                  tagsGroup.innerHTML += `<span class="crm-tag" style="background: #e0e7ff; color: #4f46e5; border-color: #c7d2fe; display: inline-flex; align-items: center; gap: 3px; padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: 500;">${t}</span>`;
              });
          } else if (tagsGroup) {
              tagsGroup.innerHTML = `<div style="color: #999; font-size: 12px; font-style: italic;">暂无标签</div>`;
          }
          MaimaiUtils.showNotification('标签已更新', 'success');

        } catch (e) {
          MaimaiUtils.showNotification(`更新标签失败: ${e.message}`, 'error');
          const btn = this.panel?.querySelector(`.crm-label-toggle[data-label="${label}"]`);
          if (btn) btn.style.opacity = '1';
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
        setTimeout(() => {
            this.detectCandidates();
            this.syncCurrentProfile();
        }, 1000);

        // Tab 2: 绑定快速操作区按钮
        this.panel.querySelector('#crmQuickGenerateMsgBtn')?.addEventListener('click', () => this.handleAIGenerateMessage(false));

        // 监听页面变化，自动更新
        const observer = new MutationObserver(() => {
            clearTimeout(this._detectTimeout);
            this._detectTimeout = setTimeout(() => {
                this.detectCandidates();
                this.syncCurrentProfile();
            }, 500);
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

    // 实时同步当前查看的候选人档案到 CRM Tab
    syncCurrentProfile() {
        let candidateData = null;

        // 1. 尝试从搜索详情面板提取
        if (window.TalentPanelExtractor) {
            const extractor = new TalentPanelExtractor();
            candidateData = extractor.extractFromTalentPanel();
        }
        
        // 2. 尝试从好友详情面板提取
        if (!candidateData || !candidateData.name) {
            if (window.DetailPanelExtractor) {
                const extractor = new DetailPanelExtractor();
                candidateData = extractor.extractFromDetailPanel();
            }
        }
        
        // 3. 尝试从直接弹出框提取
        if (!candidateData || !candidateData.name) {
            candidateData = this._extractFromRecruitPage();
        }

        this.updateProfileTabUI(candidateData);
    }

    updateProfileTabUI(candidateData) {
        if (!this.panel) return;

        const nameEl = this.panel.querySelector('#crmName');
        const titleEl = this.panel.querySelector('#crmTitle');
        const crmProfileHeader = this.panel.querySelector('#crmProfileHeader');
        const crmStateNotImportedFull = this.panel.querySelector('#crmStateNotImportedFull');
        const crmQuickActionsContainer = this.panel.querySelector('#crmQuickActionsContainer');
        const crmAdvancedActions = this.panel.querySelector('#crmAdvancedActions');

        if (!candidateData || !candidateData.name) {
            // State 1: 没有检测到具体人才，重置为空白状态，只保留快速操作
            if (nameEl) nameEl.textContent = '未获取姓名';
            if (titleEl) titleEl.textContent = '-';
            
            if (crmProfileHeader) crmProfileHeader.style.display = 'none';
            if (crmStateNotImportedFull) crmStateNotImportedFull.style.display = 'none';
            if (crmAdvancedActions) crmAdvancedActions.style.display = 'none';
            if (crmQuickActionsContainer) crmQuickActionsContainer.style.display = 'block';
            return;
        } else {
            if (crmProfileHeader) crmProfileHeader.style.display = 'flex';
        }

        // 检测到人才，填充数据
        this.lastCandidate = candidateData;
        
        // 更新 Tab 1 (批量作业 -> 焦点候选人) 的名字
        const focusNameEl = this.panel.querySelector('#candidateName');
        if (focusNameEl) {
            focusNameEl.textContent = `${candidateData.name}`;
        }

        // 更新 Tab 2 (单人档案) 的基本信息
        if (nameEl) nameEl.textContent = candidateData.name;
        
        const company = candidateData.currentCompany || '';
        const position = candidateData.currentPosition || '';
        const titleText = company && position ? `${company} ${position}` : (company || position || '未填写职级');
        if (titleEl) titleEl.textContent = titleText;

        // 提取并填充标签
        const tagsGroup = this.panel.querySelector('#crmTagsGroup');
        const skills = candidateData.skills || candidateData.statusTags || [];
        if (tagsGroup && skills.length > 0) {
            tagsGroup.innerHTML = '';
            skills.slice(0, 5).forEach(skill => {
                const tagDiv = document.createElement('div');
                tagDiv.className = 'crm-tag active';
                tagDiv.textContent = skill;
                tagsGroup.appendChild(tagDiv);
            });
        }

        // 调用后端检查是否在数据库中
        this._checkCandidateDbStatus(candidateData);
    }

    async _checkCandidateDbStatus(candidateData) {
        if (!this.panel) return;
        
        // 防闪烁优化：如果当前人已经查过库并渲染了，则直接跳过冗余的 DOM 刷新
        if (this._lastDbCheckedCandidateName === candidateData.name && this.activeDbData) {
            return;
        }

        const crmStateNotImportedFull = this.panel.querySelector('#crmStateNotImportedFull');
        const crmQuickActionsContainer = this.panel.querySelector('#crmQuickActionsContainer');
        const crmAdvancedActions = this.panel.querySelector('#crmAdvancedActions');

        if (!candidateData || !candidateData.name) {
            if (crmStateNotImportedFull) crmStateNotImportedFull.style.display = 'none';
            if (crmAdvancedActions) crmAdvancedActions.style.display = 'none';
            if (crmQuickActionsContainer) crmQuickActionsContainer.style.display = 'block';
            return;
        }

        // 构建请求payload
        const companies = [];
        if (candidateData.currentCompany) companies.push(candidateData.currentCompany);
        if (candidateData.workExperiences) {
            candidateData.workExperiences.forEach(exp => {
                 if (exp.company && !companies.includes(exp.company)) companies.push(exp.company);
            });
        }
        
        let schoolStr = '';
        if (candidateData.educations && candidateData.educations.length > 0) {
            schoolStr = candidateData.educations[0].school || '';
        }

        const payload = {
            name: candidateData.name,
            companies: companies,
            school: schoolStr
            // 可以加入 maimaiUserId 如果未来抽取器支持提取 maimai id
        };

        try {
            const result = await (chrome.storage ? chrome.storage.local.get(['apiBaseUrl']) : {apiBaseUrl: 'http://localhost:8502'});
            const apiBase = result.apiBaseUrl || 'http://localhost:8502';
            const apiUrl = `${apiBase}/api/candidate/check`;
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const checkResult = await response.json();
            
            if (checkResult.exists) {
                // State 3: 已入库，显示操作区，隐藏引导和外部快速操作
                if (crmStateNotImportedFull) crmStateNotImportedFull.style.display = 'none';
                if (crmQuickActionsContainer) crmQuickActionsContainer.style.display = 'none';
                if (crmAdvancedActions) crmAdvancedActions.style.display = 'block';

                // 同时，如果是好友页打开的，隐藏 “同步更新(搜索页)”，反之亦然
                const url = window.location.href.toLowerCase();
                const isFriendsPage = url.includes('/groups') || url.includes('/contact') || url.includes('/friend') || document.querySelector('.asideHeaderRight___2X0_x, .friend-detail-wrapper, #myIframe, .contact_detail_normal_card') !== null;
                const crmImportTalentBtn = this.panel.querySelector('#crmImportTalentBtn');
                const crmImportFriendBtn = this.panel.querySelector('#crmImportFriendBtn');
                
                if (crmImportTalentBtn) crmImportTalentBtn.style.display = isFriendsPage ? 'none' : 'block';
                if (crmImportFriendBtn) crmImportFriendBtn.style.display = isFriendsPage ? 'block' : 'none';

                // 获取后端完整档案数据以填充 CRM 面板
                try {
                    const detailResp = await fetch(`${apiBase}/api/candidate/${checkResult.candidateId}`);
                    if (detailResp.ok) {
                        const dbData = await detailResp.json();
                        
                        // 保存核心状态供快速操作使用
                        this._lastSyncedCandidateId = checkResult.candidateId;
                        this.activeDbData = dbData;
                        this._lastDbCheckedCandidateName = candidateData.name;

                        // 1. Tags (使用后端真实的 talent_labels)
                        const tagsGroup = this.panel.querySelector('#crmTagsGroup');
                        if (tagsGroup && dbData.talent_labels && dbData.talent_labels.length > 0) {
                            tagsGroup.innerHTML = '';
                            dbData.talent_labels.forEach(tag => {
                                tagsGroup.innerHTML += `<span class="crm-tag" style="background: #e0e7ff; color: #4f46e5; border-color: #c7d2fe; display: inline-flex; align-items: center; gap: 3px; padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: 500;">${tag}</span>`;
                            });
                        }

                        // update interactive buttons
                        const interactiveLabels = this.panel.querySelectorAll('.crm-label-toggle');
                        interactiveLabels.forEach(btn => {
                            const label = btn.dataset.label;
                            if (dbData.talent_labels && dbData.talent_labels.includes(label)) {
                                btn.classList.add('active');
                            } else {
                                btn.classList.remove('active');
                            }
                        });
                        
                        // 2. AI Eval
                        const evalContent = this.panel.querySelector('#crmEvalContent');
                        const evalEmptyText = this.panel.querySelector('#crmEvalEmptyText');
                        
                        if (evalEmptyText) evalEmptyText.style.display = 'none';
                        if (evalContent) {
                            evalContent.style.display = 'block';
                            evalContent.innerHTML = '';
                        }
                        
                        if (dbData.ai_summary) {
                            if (evalContent) evalContent.innerHTML = `<div style="font-size: 13px; line-height: 1.5; color: #333; white-space: pre-wrap;">${dbData.ai_summary}</div>`;
                        } else {
                            if (evalContent) evalContent.style.display = 'none';
                            if (evalEmptyText) evalEmptyText.style.display = 'inline';
                        }
                        
                        const evalScore = this.panel.querySelector('#crmEvalScore');
                        if (evalScore) {
                            evalScore.textContent = dbData.talent_tier ? `AI 适配度: ${dbData.talent_tier}` : `AI 适配度: 暂无`;
                            evalScore.style.background = dbData.talent_tier === 'S' ? '#f59e0b' : 
                                                         dbData.talent_tier === 'A' ? '#10b981' :
                                                         dbData.talent_tier === 'B' ? '#3b82f6' :
                                                         dbData.talent_tier === 'C' ? '#6b7280' : 'rgba(0,0,0,0.05)';
                            evalScore.style.color = dbData.talent_tier === 'S' ? '#000' : 
                                                    dbData.talent_tier ? '#fff' : '#666';
                            evalScore.style.borderRadius = '12px';
                            evalScore.style.fontWeight = '600';
                            evalScore.style.display = 'inline-block';
                        }
                        
                        // 3. Contact Info
                        const emailEl = this.panel.querySelector('#crmEmail');
                        const phoneEl = this.panel.querySelector('#crmPhone');
                        const wechatEl = this.panel.querySelector('#crmWechat');
                        if (emailEl) emailEl.textContent = dbData.email || '-';
                        if (phoneEl) phoneEl.textContent = dbData.phone || '-';
                        if (wechatEl) wechatEl.textContent = dbData.wechat || dbData.personal_website || '-';
                        
                        // 4. Notes
                        const notesArea = this.panel.querySelector('#crmNotesArea');
                        if (notesArea) {
                            notesArea.value = dbData.notes || '';
                        }
                        
                        // 5. Status Badge & Actions
                        const statusBadge = this.panel.querySelector('#crmStatusBadge');
                        const outreachActions = this.panel.querySelector('#crmOutreachActions');
                        if (statusBadge) {
                            if (dbData.is_friend) {
                                statusBadge.textContent = '🤝 已添加好友';
                                statusBadge.style.background = '#e6f4ea';
                                statusBadge.style.color = '#1e8e3e';
                                if (outreachActions) outreachActions.style.display = 'none';
                            } else {
                                if (outreachActions) outreachActions.style.display = 'flex';
                                if (dbData.replied_at || dbData.last_communication_at) {
                                    statusBadge.textContent = '💬 已沟通过';
                                    statusBadge.style.background = '#e8f0fe';
                                    statusBadge.style.color = '#1a73e8';
                                } else {
                                    statusBadge.textContent = '📥 待沟通';
                                    statusBadge.style.background = '#f3f2ef';
                                    statusBadge.style.color = '#666';
                                }
                            }
                        }
                        
                        // 6. Experience & Education (完全复刻 LinkedIn 机制)
                        const expContainer = this.panel.querySelector('#crmExperienceContainer');
                        if (expContainer) {
                            expContainer.innerHTML = this._renderExperience(dbData);
                        }
                        
                        // 7. Comm Logs
                        const commContainer = this.panel.querySelector('#crmCommLogContainer');
                        if (commContainer) {
                            commContainer.innerHTML = this._renderCommLogs(dbData);
                        }
                        
                        // 绑定这些新生成的动态交互事件
                        this._bindDynamicCRMEvents(checkResult.candidateId, apiBase, dbData);
                        
                    }
                } catch (err) {
                    console.error('Failed to load full candidate details', err);
                }

            } else {
                // State 2: 页面提取到了人，但数据库不存在
                if (crmAdvancedActions) crmAdvancedActions.style.display = 'none';
                if (crmStateNotImportedFull) crmStateNotImportedFull.style.display = 'block';
                if (crmQuickActionsContainer) crmQuickActionsContainer.style.display = 'block';
                
                // 好友页动态文案
                const url = window.location.href.toLowerCase();
                const isFriendsPage = url.includes('/groups') || url.includes('/contact') || url.includes('/friend') || document.querySelector('.asideHeaderRight___2X0_x, .friend-detail-wrapper, #myIframe, .contact_detail_normal_card') !== null;
                const crmBigImportBtn = this.panel.querySelector('#crmBigImportBtn');
                if (crmBigImportBtn) {
                    crmBigImportBtn.textContent = isFriendsPage ? '📥 收录当前好友 (好友页用)' : '📥 导入人才信息';
                }
            }
        } catch (e) {
            console.error("未能连接到后台数据库校验存在性", e);
            // 请求失败时，降级显示到 State 2
            if (crmAdvancedActions) crmAdvancedActions.style.display = 'none';
            if (crmStateNotImportedFull) crmStateNotImportedFull.style.display = 'block';
            if (crmQuickActionsContainer) crmQuickActionsContainer.style.display = 'block';
        }
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

    // ================== 完全复刻 LinkedIn CRM 组件逻辑 ==================

    _renderExperience(c) {
        // Work experience
        let workItems = [];
        try {
            const workRaw = typeof c.work_experiences === 'string'
                ? JSON.parse(c.work_experiences || '[]')
                : (c.work_experiences || []);
            workItems = Array.isArray(workRaw) ? workRaw : [];
        } catch (e) { workItems = []; }

        const workHtml = workItems.length > 0
            ? workItems.map((w, i) => `
          <div class="crm-exp-item" style="position:relative; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #eee;">
            <button class="crm-exp-delete" data-type="work" data-index="${i}" title="删除此条" style="position:absolute; right:0; top:0; background:none; border:none; cursor:pointer; color:#999; font-size:12px;">✕</button>
            <div class="crm-exp-company" style="font-weight: 600; font-size: 13px; color: #191919;">${this._esc(w.company || w.Company || '')}</div>
            <div class="crm-exp-role" style="font-size: 12px; color: #666; margin-top: 2px;">${this._esc(w.position || w.title || w.Position || '')}</div>
            <div class="crm-exp-period" style="font-size: 11px; color: #999; margin-top: 2px;">${this._esc(w.period || w.time || [w.start_date || w.startDate, w.end_date || w.endDate].filter(Boolean).join(' - ') || '')}</div>
            ${w.description ? `<div class="crm-exp-desc" style="font-size: 11px; color: #666; margin-top: 6px; line-height: 1.4;">${this._esc(w.description).substring(0, 150)}${w.description.length > 150 ? '...' : ''}</div>` : ''}
          </div>
        `).join('')
            : '<div style="color:#999;font-size:11px;padding:4px 0;">暂无工作经历</div>';

        // Education
        let eduItems = [];
        try {
            const eduRaw = typeof c.education_details === 'string'
                ? JSON.parse(c.education_details || '[]')
                : (c.education_details || []);
            eduItems = Array.isArray(eduRaw) ? eduRaw : [];
        } catch (e) { eduItems = []; }

        const eduHtml = eduItems.length > 0
            ? eduItems.map((e, i) => `
          <div class="crm-exp-item" style="position:relative; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #eee;">
            <button class="crm-exp-delete" data-type="edu" data-index="${i}" title="删除此条" style="position:absolute; right:0; top:0; background:none; border:none; cursor:pointer; color:#999; font-size:12px;">✕</button>
            <div class="crm-exp-company" style="font-weight: 600; font-size: 13px; color: #191919;">${this._esc(e.school || e.School || '')}</div>
            <div class="crm-exp-role" style="font-size: 12px; color: #666; margin-top: 2px;">${this._esc([e.degree || e.Degree || '', e.major || e.field || ''].filter(Boolean).join(' · '))}</div>
            <div class="crm-exp-period" style="font-size: 11px; color: #999; margin-top: 2px;">${this._esc(e.period || [e.start_date || e.startDate || e.startYear, e.end_date || e.endDate || e.endYear].filter(Boolean).join(' - ') || '')}</div>
          </div>
        `).join('')
            : '<div style="color:#999;font-size:11px;padding:4px 0;">暂无教育经历</div>';

        return `
      <div class="crm-card">
        <div class="crm-card-title crm-exp-toggle" data-section="work" style="justify-content: space-between; cursor: pointer;">
          <span>💼 工作经历 (${workItems.length})</span>
          <span class="toggle-arrow" style="font-size: 10px; color: #999; transform: ${this._expOpen.work ? 'rotate(90deg)' : 'none'}; transition: transform 0.2s;">▶</span>
        </div>
        <div class="crm-exp-list" id="workExpList" style="display: ${this._expOpen.work ? 'block' : 'none'}; margin-top: 12px;">
          ${workHtml}
        </div>
      </div>
      <div class="crm-card" style="margin-top: 16px;">
        <div class="crm-card-title crm-exp-toggle" data-section="edu" style="justify-content: space-between; cursor: pointer;">
          <span>🎓 教育经历 (${eduItems.length})</span>
          <span class="toggle-arrow" style="font-size: 10px; color: #999; transform: ${this._expOpen.edu ? 'rotate(90deg)' : 'none'}; transition: transform 0.2s;">▶</span>
        </div>
        <div class="crm-exp-list" id="eduExpList" style="display: ${this._expOpen.edu ? 'block' : 'none'}; margin-top: 12px;">
          ${eduHtml}
        </div>
      </div>
    `;
    }

    _renderCommLogs(c) {
        const logs = c.communication_logs || [];

        const logsHtml = logs.length > 0
            ? logs.map((log, i) => `
          <div class="crm-comm-item" style="background: #f8f9fa; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
            <div class="crm-comm-header" style="display: flex; justify-content: space-between; margin-bottom: 6px;">
              <div>
                <span class="crm-comm-time" style="font-size: 11px; color: #999;">${this._esc(log.time || '未知时间')}</span>
                <span class="crm-comm-channel" style="font-size: 11px; font-weight: 500; color: #0a66c2; margin-left: 6px;">${this._esc(log.channel || log.action || '未知')}</span>
                ${log.direction ? `<span class="crm-comm-dir" style="font-size: 11px; color: #666;">(${this._esc(log.direction)})</span>` : ''}
              </div>
              <button class="crm-comm-delete" data-index="${i}" title="删除此条" style="background:none; border:none; cursor:pointer; color:#999; font-size:12px; padding:0;">✕</button>
            </div>
            <div class="crm-comm-content" style="font-size: 12px; color: #333; line-height: 1.5; white-space: pre-wrap;">${this._esc(log.content || log.message || '(无内容)')}</div>
          </div>
        `).join('')
            : '<div style="color:#999;font-size:11px;text-align:center;padding:12px;">暂无沟通记录</div>';

        return `
      <div class="crm-card">
        <div class="crm-card-title"><span>💬</span> 沟通记录 (${logs.length})</div>
        <div class="crm-comm-input" style="margin-bottom:12px;">
          <textarea id="commLogInput" placeholder="输入沟通内容... (Ctrl+Enter 保存)" rows="2"
            style="width:100%;padding:8px;border:1px solid #dadce0;border-radius:6px;font-size:12px;font-family:inherit;resize:vertical;box-sizing:border-box;"></textarea>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
            <select id="commLogChannel" style="padding:4px 8px;border:1px solid #dadce0;border-radius:4px;font-size:11px; color:#333; background: #fff;">
              <option value="maimai">脉脉</option>
              <option value="wechat">微信</option>
              <option value="linkedin">LinkedIn</option>
              <option value="email">邮件</option>
              <option value="phone">电话</option>
            </select>
            <button class="crm-btn crm-btn-outline" id="addCommLogBtn" style="padding:4px 12px;font-size:12px;">💾 保存记录</button>
          </div>
        </div>
        <div class="crm-comm-list" style="max-height:240px;overflow-y:auto; border-top: 1px solid #eee; padding-top: 12px;">
          ${logsHtml}
        </div>
        <div id="commLogStatus" class="crm-status-msg" style="margin-top: 6px; font-size: 11px;"></div>
      </div>
      <div style="height:20px;"></div>
    `;
    }

    // --- Dynamic Events Binder ---
    _bindDynamicCRMEvents(candidateId, apiBase, cData) {
        if (!this.panel) return;

        // Helper to refresh the sub-panels cleanly without blinking the master state
        const refreshDynamicPanels = async () => {
            try {
                const updatedResp = await fetch(`${apiBase}/api/candidate/${candidateId}`);
                if (updatedResp.ok) {
                    const freshData = await updatedResp.json();
                    const expContainer = this.panel.querySelector('#crmExperienceContainer');
                    const commContainer = this.panel.querySelector('#crmCommLogContainer');
                    if (expContainer) expContainer.innerHTML = this._renderExperience(freshData);
                    if (commContainer) commContainer.innerHTML = this._renderCommLogs(freshData);
                    this._bindDynamicCRMEvents(candidateId, apiBase, freshData);
                }
            } catch (err) {
                console.error("Failed to refresh dynamic panels", err);
            }
        };

        const quickEdit = async (data) => {
            const resp = await fetch(`${apiBase}/api/candidate/${candidateId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return await resp.json();
        };

        // 1. Experience Toggles
        this.panel.querySelectorAll('.crm-exp-toggle').forEach(toggle => {
            toggle.addEventListener('click', () => {
                const section = toggle.dataset.section;
                const listId = section === 'work' ? 'workExpList' : 'eduExpList';
                const list = this.panel.querySelector(`#${listId}`);
                const arrow = toggle.querySelector('.toggle-arrow');
                if (list && arrow) {
                    const isOpen = list.style.display !== 'none';
                    list.style.display = isOpen ? 'none' : 'block';
                    arrow.style.transform = isOpen ? 'none' : 'rotate(90deg)';
                    this._expOpen[section] = !isOpen;
                }
            });
        });

        // 2. Experience Deletes
        this.panel.querySelectorAll('.crm-exp-delete').forEach(btn => {
            const handler = async (e) => {
                e.stopPropagation();
                const type = btn.dataset.type;
                const index = parseInt(btn.dataset.index);
                const fieldName = type === 'work' ? 'work_experiences' : 'education_details';
                if (!confirm(`确定删除这条${type === 'work' ? '工作' : '教育'}经历吗？`)) return;

                btn.disabled = true;
                btn.textContent = '...';
                try {
                    const raw = cData[fieldName];
                    let items = typeof raw === 'string' ? JSON.parse(raw || '[]') : (raw || []);
                    if (!Array.isArray(items)) items = [];
                    items.splice(index, 1);
                    await quickEdit({ [fieldName]: JSON.stringify(items) });
                    refreshDynamicPanels();
                } catch (e) {
                    MaimaiUtils.showNotification(`删除失败: ${e.message}`, 'error');
                }
            };
            // Ensure we remove old listeners on re-bind
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', handler);
        });

        // 3. Add Comm Log
        const addCommLogBtn = this.panel.querySelector('#addCommLogBtn');
        const commLogInput = this.panel.querySelector('#commLogInput');
        const commLogChannel = this.panel.querySelector('#commLogChannel');
        const commLogStatus = this.panel.querySelector('#commLogStatus');
        
        const addLogHandler = async () => {
            const content = commLogInput?.value?.trim();
            if (!content) return;
            const channel = commLogChannel?.value || 'maimai';
            
            if (addCommLogBtn) {
                addCommLogBtn.disabled = true;
                addCommLogBtn.textContent = '⏳';
            }
            try {
                const resp = await fetch(`${apiBase}/api/candidate/${candidateId}/quick-comm-log`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ channel, content }),
                });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                commLogInput.value = '';
                refreshDynamicPanels();
            } catch (e) {
                if (commLogStatus) {
                    commLogStatus.textContent = `❌ ${e.message}`;
                    commLogStatus.style.color = '#dc2626';
                    setTimeout(() => commLogStatus.textContent = '', 3000);
                }
            } finally {
                if (addCommLogBtn) {
                    addCommLogBtn.disabled = false;
                    addCommLogBtn.textContent = '💾 保存记录';
                }
            }
        };

        if (addCommLogBtn && commLogInput) {
            const newAddBtn = addCommLogBtn.cloneNode(true);
            addCommLogBtn.parentNode.replaceChild(newAddBtn, addCommLogBtn);
            newAddBtn.addEventListener('click', addLogHandler);
            
            // Add Ctrl+Enter shortcut (but must ensure no duplicate DOM listeners)
            const newInput = commLogInput.cloneNode(true);
            newInput.value = commLogInput.value;
            commLogInput.parentNode.replaceChild(newInput, commLogInput);
            newInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    addLogHandler();
                }
            });
        }

        // 4. Delete Comm Log
        this.panel.querySelectorAll('.crm-comm-delete').forEach(btn => {
            const handler = async (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                if (!confirm('确定删除这条沟通记录吗？')) return;
                
                btn.disabled = true;
                try {
                    const resp = await fetch(`${apiBase}/api/candidate/${candidateId}/comm-log/${index}`, {
                        method: 'DELETE',
                    });
                    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                    refreshDynamicPanels();
                } catch (e) {
                    MaimaiUtils.showNotification(`删除失败: ${e.message}`, 'error');
                }
            };
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', handler);
        });
    }
}

if (typeof window !== 'undefined') {
    window.AssistantPanel = AssistantPanel;
}
