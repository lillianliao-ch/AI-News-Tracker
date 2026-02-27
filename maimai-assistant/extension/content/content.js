// Maimai Assistant - 入口控制器 (v3 - 修复语法)
class MaimaiAssistant {
    constructor() {
        this.panel = null;
        this.extractor = null;
        this.isInitialized = false;
        this.batchState = {
            isRunning: false,
            currentIndex: 0,
            total: 0,
            successful: 0,
            failed: 0
        };
    }

    async init() {
        try {
            console.log('🚀 Maimai Assistant 启动中...');
            await this.waitForPageReady();

            this.extractor = new MaimaiExtractor();
            this.panel = new AssistantPanel();
            this.panel.assistant = this;
            await this.panel.init();

            this.setupPageChangeListener();
            this.setupMessageListeners();

            this.isInitialized = true;
            console.log('✅ Maimai Assistant 初始化完成!');
        } catch (error) {
            console.error('❌ 初始化失败:', error);
        }
    }

    async waitForPageReady() {
        return new Promise((resolve) => {
            if (document.readyState === 'complete') {
                setTimeout(resolve, 1000);
            } else {
                window.addEventListener('load', () => setTimeout(resolve, 1000));
            }
        });
    }

    // 批量添加好友（支持多页）
    async batchAddFriends(count = 10, pages = 1) {
        this.batchState = {
            isRunning: true,
            currentIndex: 0,
            total: 0,
            successful: 0,
            failed: 0,
            currentPage: 1,
            totalPages: pages
        };

        for (let page = 1; page <= pages; page++) {
            if (!this.batchState.isRunning) break;

            this.batchState.currentPage = page;
            console.log(`\n📄 ========== 第 ${page}/${pages} 页 ==========`);
            MaimaiUtils.showNotification(`第 ${page}/${pages} 页 - 开始批量加好友`, 'info');

            // 重新检测当前页候选人
            const cards = this.extractor.findCandidateCards();
            if (cards.length === 0) {
                MaimaiUtils.showNotification(`第 ${page} 页未检测到候选人`, 'warning');
                break;
            }

            const targetCards = cards.slice(0, count);
            this.batchState.total += targetCards.length;
            this.panel.updateProgress(this.batchState);

            for (let i = 0; i < targetCards.length; i++) {
                if (!this.batchState.isRunning) break;

                this.batchState.currentIndex++;
                this.panel.updateProgress(this.batchState);

                try {
                    await this.addFriendForCard(targetCards[i], i);
                    this.batchState.successful++;
                } catch (error) {
                    this.batchState.failed++;
                    console.error(`❌ 第 ${this.batchState.currentIndex} 个添加失败:`, error.message);
                }

                if (i < targetCards.length - 1 && this.batchState.isRunning) {
                    const delay = 5000 + Math.random() * 5000;
                    await MaimaiUtils.delay(delay);
                }
            }

            // 如果还有下一页，点击翻页
            if (page < pages && this.batchState.isRunning) {
                const navigated = await this.clickNextPage();
                if (!navigated) {
                    MaimaiUtils.showNotification(`已到最后一页，翻页结束`, 'info');
                    break;
                }
            }
        }

        this.batchState.isRunning = false;
        this.panel.updateProgress(this.batchState);
        MaimaiUtils.showNotification(
            `批量加好友完成！成功: ${this.batchState.successful}, 失败: ${this.batchState.failed} (共${this.batchState.currentPage}页)`,
            this.batchState.failed > 0 ? 'warning' : 'success'
        );
    }

    // 为单个卡片添加好友
    async addFriendForCard(card, index) {
        console.log('==========================================');
        console.log(`🤝 [${index + 1}] 开始为卡片添加好友...`);

        // ① 提取候选人信息（为了自动导入）
        // 滚动到卡片并点击触发右侧面板负载
        card.scrollIntoView({ behavior: 'instant', block: 'center' });
        await MaimaiUtils.delay(500);

        const safeClickTargets = ['[class*="baseInfo"]', '[class*="expect"]', '[class*="tag"]', '[class*="status"]'];
        let clickTarget = null;
        for (const sel of safeClickTargets) {
            clickTarget = card.querySelector(sel);
            if (clickTarget && !clickTarget.closest('a')) break;
            clickTarget = null;
        }
        if (!clickTarget) clickTarget = card;
        clickTarget.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));

        console.log(`⏳ 等待详情面板加载...`);
        let candidateData = null;
        for (let attempt = 0; attempt < 5; attempt++) {
            await MaimaiUtils.delay(1000);
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                candidateData = extractor.extractFromTalentPanel();
                if (candidateData && candidateData.name) break;
            }
        }

        if (candidateData && candidateData.name) {
            console.log(`✅ 已提取候选人: ${candidateData.name}，同步记录中...`);
            // 记录触达日志（这会触发后端自动建档）
            try {
                await fetch(`${MaimaiConfig.api.baseUrl}/api/comm-log`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        candidate_name: candidateData.name,
                        message: '批量加好友申请',
                        channel: 'maimai_friend',
                        candidate_company: candidateData.currentCompany || '',
                        candidate_position: candidateData.currentPosition || '',
                        create_outreach: true,
                        outreach_type: 'friend_request',
                        candidate_profile: candidateData // 关键：传回完整信息用于建档
                    })
                });
            } catch (e) {
                console.warn('记录批量触达日志失败:', e);
            }
        }

        // ② 执行原本按钮点击逻辑
        // 找到更多按钮
        const moreBtn = this.extractor.findMoreButton(card);
        if (!moreBtn) {
            throw new Error('未找到更多按钮');
        }

        console.log('✅ 找到更多按钮:', moreBtn.className);

        // 滚动到可见位置
        moreBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
        await MaimaiUtils.delay(300);

        // 模拟真实点击
        console.log('🖱️ 点击更多按钮...');
        const rect = moreBtn.getBoundingClientRect();
        const clickX = rect.left + rect.width / 2;
        const clickY = rect.top + rect.height / 2;

        // 完整的鼠标事件序列
        moreBtn.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        await MaimaiUtils.delay(100);

        moreBtn.dispatchEvent(new MouseEvent('mousedown', {
            bubbles: true, cancelable: true, view: window,
            clientX: clickX, clientY: clickY
        }));
        await MaimaiUtils.delay(50);

        moreBtn.dispatchEvent(new MouseEvent('mouseup', {
            bubbles: true, cancelable: true, view: window,
            clientX: clickX, clientY: clickY
        }));
        await MaimaiUtils.delay(50);

        moreBtn.dispatchEvent(new MouseEvent('click', {
            bubbles: true, cancelable: true, view: window,
            clientX: clickX, clientY: clickY
        }));

        console.log('✅ 已触发点击事件');

        // 等待下拉菜单出现
        await MaimaiUtils.delay(1500);

        // 查找加好友选项
        console.log('🔍 查找加好友选项...');
        let addFriendOption = null;

        // 方法1: 遍历所有元素查找精确文本
        const allElements = document.querySelectorAll('*');
        for (const el of allElements) {
            const text = el.textContent?.trim();
            if (text === '加好友') {
                const elRect = el.getBoundingClientRect();
                if (elRect.width > 0 && elRect.height > 0 && elRect.top > 0) {
                    console.log(`  找到候选: ${el.tagName}.${el.className}`);
                    addFriendOption = el;
                    break;
                }
            }
        }

        // 方法2: 打印调试信息
        if (!addFriendOption) {
            console.log('🔍 打印所有可见菜单项...');
            document.querySelectorAll('div, li, span').forEach(el => {
                const text = el.textContent?.trim();
                const elRect = el.getBoundingClientRect();
                if (text && text.length < 15 &&
                    elRect.width > 0 && elRect.height > 10 &&
                    elRect.top > 0 && elRect.left > 0) {
                    if (text.includes('加') || text.includes('好友') ||
                        text.includes('关注') || text.includes('备注')) {
                        console.log(`  菜单项: "${text}"`);
                    }
                }
            });
        }

        if (!addFriendOption) {
            document.body.click();
            await MaimaiUtils.delay(200);
            throw new Error('未找到加好友选项');
        }

        // 点击加好友
        console.log('🖱️ 点击加好友选项');
        addFriendOption.click();
        await MaimaiUtils.delay(800);

        document.body.click();
        console.log('✅ 添加好友完成');
    }

    // 批量立即沟通（支持多页）
    async batchDirectChat(count = 10, pages = 1) {
        this.batchState = {
            isRunning: true,
            currentIndex: 0,
            total: 0,
            successful: 0,
            failed: 0,
            currentPage: 1,
            totalPages: pages
        };

        // 获取选中的JD
        const jobSelect = this.panel?.panel?.querySelector('#jobSelect');
        const selectedValue = jobSelect?.value;
        const jobId = (selectedValue && selectedValue !== 'auto') ? parseInt(selectedValue) : null;

        for (let page = 1; page <= pages; page++) {
            if (!this.batchState.isRunning) break;

            this.batchState.currentPage = page;
            console.log(`\n📄 ========== 第 ${page}/${pages} 页 ==========`);
            MaimaiUtils.showNotification(`第 ${page}/${pages} 页 - 开始批量立即沟通`, 'info');

            const cards = this.extractor.findCandidateCards();
            if (cards.length === 0) {
                MaimaiUtils.showNotification(`第 ${page} 页未检测到候选人`, 'warning');
                break;
            }

            const targetCards = cards.slice(0, count);
            this.batchState.total += targetCards.length;
            this.panel.updateProgress(this.batchState);

            let lastCandidateName = null;

            for (let i = 0; i < targetCards.length; i++) {
                if (!this.batchState.isRunning) break;

                this.batchState.currentIndex++;
                this.panel.updateProgress(this.batchState);

                try {
                    lastCandidateName = await this.directChatForCard(targetCards[i], i, jobId, lastCandidateName);
                    this.batchState.successful++;
                } catch (error) {
                    this.batchState.failed++;
                    console.error(`❌ 第 ${this.batchState.currentIndex} 个沟通失败:`, error.message);
                    MaimaiUtils.showNotification(`第 ${this.batchState.currentIndex} 个失败: ${error.message}`, 'warning');
                }

                if (i < targetCards.length - 1 && this.batchState.isRunning) {
                    const delay = 5000 + Math.random() * 5000;
                    console.log(`⏳ 等待 ${Math.round(delay / 1000)}s 再处理下一个...`);
                    await MaimaiUtils.delay(delay);
                }
            }

            // 如果还有下一页，点击翻页
            if (page < pages && this.batchState.isRunning) {
                const navigated = await this.clickNextPage();
                if (!navigated) {
                    MaimaiUtils.showNotification(`已到最后一页，翻页结束`, 'info');
                    break;
                }
            }
        }

        this.batchState.isRunning = false;
        this.panel.updateProgress(this.batchState);
        MaimaiUtils.showNotification(
            `批量沟通完成！成功: ${this.batchState.successful}, 失败: ${this.batchState.failed} (共${this.batchState.currentPage}页)`,
            this.batchState.failed > 0 ? 'warning' : 'success'
        );
    }

    // 对单个卡片执行：点击卡片 → 提取信息 → AI生成消息 → 点击立即沟通 → 填入消息 → 发送
    // 返回本次候选人名字，供下次验证面板是否已切换
    async directChatForCard(card, index, jobId, lastCandidateName) {
        console.log(`==========================================`);
        console.log(`💬 [${index + 1}] 开始处理候选人沟通... (上一个: ${lastCandidateName || '无'})`);

        // ① 点击卡片加载右侧详情面板
        card.scrollIntoView({ behavior: 'instant', block: 'center' });
        await MaimaiUtils.delay(500);

        const safeClickTargets = [
            '[class*="baseInfo"]', '[class*="expect"]',
            '[class*="tag"]', '[class*="status"]',
        ];
        let clickTarget = null;
        for (const sel of safeClickTargets) {
            clickTarget = card.querySelector(sel);
            if (clickTarget && !clickTarget.closest('a')) break;
            clickTarget = null;
        }
        if (!clickTarget) clickTarget = card;
        clickTarget.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));

        // ② 等待右侧面板刷新 — 验证面板显示了不同于上一个候选人的名字
        console.log(`⏳ 等待右侧面板切换...`);
        let candidateData = null;
        let panelReady = false;

        for (let attempt = 0; attempt < 6; attempt++) {
            await MaimaiUtils.delay(1500);
            if (window.TalentPanelExtractor) {
                const extractor = new TalentPanelExtractor();
                candidateData = extractor.extractFromTalentPanel();
                if (candidateData && candidateData.name) {
                    // 第一个候选人（没有上一个名字）：只要有名字就OK
                    // 后续候选人：验证面板名字和上一个不同
                    if (!lastCandidateName || candidateData.name !== lastCandidateName) {
                        panelReady = true;
                        break;
                    } else {
                        console.log(`⚠️ 面板仍显示上一个候选人 ${lastCandidateName}，等待切换... (${attempt + 1}/6)`);
                    }
                }
            }
        }

        if (!panelReady || !candidateData || !candidateData.name) {
            throw new Error(`面板未能切换到新候选人（仍显示: ${candidateData?.name || '空'}），无法提取信息`);
        }
        console.log(`✅ 面板已切换到: ${candidateData.name}`);

        // ③ 调用 AI 生成个性化消息
        console.log(`🤖 为 ${candidateData.name} 生成AI消息...`);
        const apiUrl = `${MaimaiConfig.api.baseUrl}/api/generate-message`;
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                candidate: candidateData,
                job_id: jobId,
                platform: "maimai"
            }),
            signal: AbortSignal.timeout(MaimaiConfig.api.timeout)
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `AI API错误: ${response.status}`);
        }

        const aiResult = await response.json();
        if (!aiResult.success) {
            throw new Error(aiResult.error || 'AI 消息生成失败');
        }
        const message = aiResult.message;
        console.log(`✨ AI消息生成完成 (${message.length}字)`);

        // ④ 点击右侧面板的「立即沟通」或「沟通」按钮
        // 按钮 DOM 结构: <div class="mui-btn mui-btn-primary ...">立即沟通</div>
        // 已沟通的候选人按钮文字变为「沟通」
        let chatBtn = null;

        // 辅助方法：判断是否为沟通按钮（排除"电话沟通"）
        const isChatButton = (text) => {
            if (!text) return false;
            text = text.trim();
            if (text.includes('电话')) return false;  // 排除「电话沟通」
            if (text.length > 10) return false;
            return text.includes('沟通');  // 匹配「立即沟通」和「沟通」
        };

        // 方法1: 精确匹配 mui-btn-primary 类
        const primaryBtns = document.querySelectorAll('.mui-btn.mui-btn-primary');
        for (const btn of primaryBtns) {
            if (isChatButton(btn.textContent)) {
                const rect = btn.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && !btn.closest('#maimai-assistant-panel')) {
                    chatBtn = btn;
                    break;
                }
            }
        }

        // 方法2: 回退 - 在右侧面板区域查找
        if (!chatBtn) {
            const viewportWidth = window.innerWidth;
            const panelMinX = viewportWidth * 0.4;
            chatBtn = Array.from(document.querySelectorAll('button, div, a')).find(el => {
                if (!isChatButton(el.textContent)) return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0 && rect.left > panelMinX &&
                    !el.closest('#maimai-assistant-panel');
            });
        }

        if (!chatBtn) {
            throw new Error('未找到右侧面板的「立即沟通」按钮');
        }

        console.log(`🖱️ 点击「立即沟通」按钮...`);
        chatBtn.click();
        await MaimaiUtils.delay(2500);

        // ⑤ 找到对话框容器，再找其中的 textarea 和发送按钮
        // 关键策略：先找到【发送后留在此页】按钮 → 向上找到对话框容器 → 在容器内找 textarea
        let dialogContainer = null;
        let sendBtn = null;

        const findDialogElements = () => {
            const allElements = Array.from(document.querySelectorAll('button, div, span'));
            for (const el of allElements) {
                const text = el.textContent?.trim();
                const rect = el.getBoundingClientRect();
                if (text && rect.width > 0 && rect.height > 0 && text === '发送后留在此页') {
                    sendBtn = el;
                    // 向上查找对话框容器
                    let parent = el.parentElement;
                    for (let depth = 0; depth < 15 && parent; depth++) {
                        parent = parent.parentElement;
                        if (!parent) break;
                        // 对话框通常有 fixed/absolute 定位的遮罩层
                        const style = window.getComputedStyle(parent);
                        if (style.position === 'fixed' || style.position === 'absolute') {
                            const pRect = parent.getBoundingClientRect();
                            if (pRect.width > 200 && pRect.height > 200) {
                                dialogContainer = parent;
                                break;
                            }
                        }
                    }
                    if (dialogContainer) break;
                }
            }
        };

        // 第一次尝试
        findDialogElements();

        // 如果没找到，等久一点再试
        if (!dialogContainer || !sendBtn) {
            console.log('⏳ 对话框未立即出现，再等待2.5秒...');
            await MaimaiUtils.delay(2500);
            findDialogElements();
        }

        if (!sendBtn) {
            throw new Error('未找到对话框的「发送后留在此页」按钮，对话框可能未弹出');
        }

        // 在对话框容器内找 textarea（如果找到了容器），否则在 sendBtn 附近找
        let textarea = null;
        if (dialogContainer) {
            textarea = dialogContainer.querySelector('textarea');
            console.log(`📦 找到对话框容器，内含 textarea: ${!!textarea}`);
        }

        // 回退：在发送按钮的祖先中找 textarea
        if (!textarea) {
            let ancestor = sendBtn.parentElement;
            for (let depth = 0; depth < 10 && ancestor; depth++) {
                textarea = ancestor.querySelector('textarea');
                if (textarea) break;
                ancestor = ancestor.parentElement;
            }
            console.log(`📦 从发送按钮祖先中找到 textarea: ${!!textarea}`);
        }

        if (!textarea) {
            throw new Error('在对话框中未找到输入框');
        }

        // 设置值并触发事件（React 兼容）
        textarea.focus();
        await MaimaiUtils.delay(200);

        // 先清空
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(textarea, '');
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        await MaimaiUtils.delay(100);

        // 写入消息
        nativeInputValueSetter.call(textarea, message);
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.dispatchEvent(new Event('change', { bubbles: true }));

        // 验证填入成功
        const filledValue = textarea.value;
        if (!filledValue || filledValue.length < 10) {
            console.warn(`⚠️ textarea.value 验证: "${filledValue?.substring(0, 30)}..."`);
            // 再试一次用 textContent
            textarea.textContent = message;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }

        console.log(`📝 消息已填入对话框 (${textarea.value.length}字)`);
        await MaimaiUtils.delay(500);

        // ⑥ 点击「发送后留在此页」按钮（已在上面找到）
        console.log(`📨 点击「${sendBtn.textContent.trim()}」`);
        sendBtn.click();
        await MaimaiUtils.delay(2000);

        // ⑦ 关闭对话框 + 清理页面状态
        // 注意：不使用 Escape 键（会把焦点移到搜索框导致下拉菜单弹出）
        // 「发送后留在此页」通常已经关闭了对话框

        // 如果对话框还在，尝试点击对话框的关闭按钮（X）
        const dialogX = document.querySelector('[class*="recruit-direct"] [class*="close"], [class*="dialog"] [class*="close"]');
        if (dialogX) {
            const rect = dialogX.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                dialogX.click();
                await MaimaiUtils.delay(500);
            }
        }

        // 关键：移除所有焦点，防止搜索框下拉菜单弹出
        if (document.activeElement) {
            document.activeElement.blur();
        }
        await MaimaiUtils.delay(800);

        MaimaiUtils.showNotification(`✅ ${candidateData.name} 沟通消息已发送`, 'success');
        console.log(`✅ ${candidateData.name} 处理完成`);
        return candidateData.name; // 返回名字供下次验证面板是否已切换
    }

    // 批量提取信息
    async batchExtractInfo(count = 10) {
        const candidates = this.extractor.extractCandidates(count);
        if (candidates.length === 0) {
            MaimaiUtils.showNotification('未找到候选人', 'warning');
            return [];
        }
        return candidates;
    }

    // 批量导入候选人到人才库（支持多页）
    async batchImportTalents(count = 10, pages = 1) {
        this.batchState = {
            isRunning: true,
            currentIndex: 0,
            total: 0,
            successful: 0,
            failed: 0,
            currentPage: 1,
            totalPages: pages
        };

        for (let page = 1; page <= pages; page++) {
            if (!this.batchState.isRunning) break;

            this.batchState.currentPage = page;
            console.log(`\n📄 ========== 第 ${page}/${pages} 页 ==========`);
            MaimaiUtils.showNotification(`第 ${page}/${pages} 页 - 开始批量导入`, 'info');

            const cards = this.extractor.findCandidateCards();
            if (cards.length === 0) {
                MaimaiUtils.showNotification(`第 ${page} 页未检测到候选人`, 'warning');
                break;
            }

            const targetCards = cards.slice(0, count);
            this.batchState.total += targetCards.length;
            this.panel.updateProgress(this.batchState);

            for (let i = 0; i < targetCards.length; i++) {
                if (!this.batchState.isRunning) break;

                this.batchState.currentIndex++;
                this.panel.updateProgress(this.batchState);

                try {
                    await this.importTalentFromCard(targetCards[i], i);
                    this.batchState.successful++;
                } catch (error) {
                    this.batchState.failed++;
                    console.error(`❌ 第 ${this.batchState.currentIndex} 个导入失败:`, error.message);
                }

                if (i < targetCards.length - 1 && this.batchState.isRunning) {
                    const delay = 3000 + Math.random() * 2000;
                    await MaimaiUtils.delay(delay);
                }
            }

            // 如果还有下一页，点击翻页
            if (page < pages && this.batchState.isRunning) {
                const navigated = await this.clickNextPage();
                if (!navigated) {
                    MaimaiUtils.showNotification(`已到最后一页，翻页结束`, 'info');
                    break;
                }
            }
        }

        this.batchState.isRunning = false;
        this.panel.updateProgress(this.batchState);
        MaimaiUtils.showNotification(
            `批量导入完成！成功: ${this.batchState.successful}, 失败: ${this.batchState.failed} (共${this.batchState.currentPage}页)`,
            this.batchState.failed > 0 ? 'warning' : 'success'
        );
    }

    // 从候选人卡片导入信息
    async importTalentFromCard(card, index) {
        console.log(`==========================================`);
        console.log(`🔍 [${index + 1}] 开始从卡片提取并导入...`);

        // 1. 滚动到卡片并点击使其在右侧加载详情
        card.scrollIntoView({ behavior: 'instant', block: 'center' });
        await MaimaiUtils.delay(500);

        // 点击卡片的非链接区域，触发右侧面板加载
        // 注意：不能点击 <a> 标签（候选人名字），否则会导致页面跳转
        console.log(`🖱️  点击卡片加载详情...`);

        // 优先点击卡片中的描述/信息区域（非链接），避免页面跳转
        const safeClickTargets = [
            '[class*="baseInfo"]',
            '[class*="expect"]',
            '[class*="tag"]',
            '[class*="status"]',
        ];

        let clickTarget = null;
        for (const sel of safeClickTargets) {
            clickTarget = card.querySelector(sel);
            if (clickTarget && !clickTarget.closest('a')) break;
            clickTarget = null;
        }

        // 如果没找到安全区域，就点卡片本身，但阻止默认行为
        if (!clickTarget) {
            clickTarget = card;
        }

        const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
        clickTarget.dispatchEvent(clickEvent);

        // 2. 等待右侧面板数据加载完成
        const waitTime = window.TalentPanelExtractor ? 3000 : 2000;
        console.log(`⏳ 等待 ${waitTime}ms 加载右侧面板...`);
        await MaimaiUtils.delay(waitTime);

        // 3. 执行提取与同步
        if (window.TalentPanelExtractor) {
            const extractor = new TalentPanelExtractor();
            const result = await extractor.importOrView(false); // 每个人都显示通知，保持和单条导入一致

            if (!result || !result.success) {
                throw new Error(result?.error || '提取失败');
            }
        } else {
            throw new Error('TalentPanelExtractor 未加载');
        }
    }

    // 翻页：点击「跳转至下一页」按钮
    async clickNextPage() {
        console.log('📄 正在查找翻页按钮...');

        // 方法1: 精确匹配文字 "跳转至下一页"
        let nextPageBtn = null;
        const allElements = document.querySelectorAll('a, button, div, span');
        for (const el of allElements) {
            const text = el.textContent?.trim();
            if (text && (text === '跳转至下一页' || text === '下一页')) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && !el.closest('#maimai-assistant-panel')) {
                    nextPageBtn = el;
                    break;
                }
            }
        }

        // 方法2: 查找分页组件中的 next 按钮
        if (!nextPageBtn) {
            nextPageBtn = document.querySelector('[class*="next"]:not([class*="disabled"]), [class*="pagination"] [class*="next"]');
            if (nextPageBtn) {
                const rect = nextPageBtn.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) nextPageBtn = null;
            }
        }

        if (!nextPageBtn) {
            console.log('⚠️ 未找到翻页按钮，可能已是最后一页');
            return false;
        }

        console.log(`🖱️ 点击翻页按钮: "${nextPageBtn.textContent?.trim()}"`);
        nextPageBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
        await MaimaiUtils.delay(500);
        nextPageBtn.click();

        // 等待页面加载新内容
        console.log('⏳ 等待新页面加载...');
        await MaimaiUtils.delay(3000);

        // 验证：检查候选人卡片已刷新
        const newCards = this.extractor.findCandidateCards();
        if (newCards.length > 0) {
            console.log(`✅ 翻页成功，新页面检测到 ${newCards.length} 个候选人`);
            // 更新面板检测数
            this.panel?.detectCandidates();
            return true;
        } else {
            // 可能加载较慢，再等一会
            await MaimaiUtils.delay(2000);
            const retryCards = this.extractor.findCandidateCards();
            if (retryCards.length > 0) {
                console.log(`✅ 翻页成功（延迟），检测到 ${retryCards.length} 个候选人`);
                this.panel?.detectCandidates();
                return true;
            }
            console.log('⚠️ 翻页后未检测到候选人');
            return false;
        }
    }

    // 停止批量操作
    stopBatchOperation() {
        this.batchState.isRunning = false;
        this.panel.updateProgress(this.batchState);
        MaimaiUtils.showNotification('批量操作已主动停止', 'info');
    }

    // 监听页面变化
    setupPageChangeListener() {
        let lastUrl = location.href;
        const observer = new MutationObserver(() => {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
                setTimeout(() => this.panel?.detectCandidates(), 2000);
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // 消息监听
    setupMessageListeners() {
        // 检查 chrome.runtime 是否可用（可能在某些上下文中不可用）
        if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.onMessage) {
            console.log('⚠️ chrome.runtime 不可用，跳过消息监听器设置');
            return;
        }

        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            switch (message.type) {
                case 'EXTRACT_INFO':
                    this.batchExtractInfo(message.count || 10).then(data =>
                        sendResponse({ success: true, data })
                    );
                    return true;
                case 'STOP_BATCH':
                    this.stopBatchOperation();
                    sendResponse({ success: true });
                    break;
            }
        });
    }
}

// 初始化
if (!window.maimaiAssistant) {
    window.maimaiAssistant = new MaimaiAssistant();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => window.maimaiAssistant.init(), 500);
        });
    } else {
        setTimeout(() => window.maimaiAssistant.init(), 500);
    }
}

console.log('✅ Maimai Assistant Content Script 加载完成');
