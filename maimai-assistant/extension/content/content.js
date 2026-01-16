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

    // 批量添加好友
    async batchAddFriends(count = 10) {
        const cards = this.extractor.findCandidateCards();
        if (cards.length === 0) {
            MaimaiUtils.showNotification('未检测到候选人', 'warning');
            return;
        }

        const targetCards = cards.slice(0, count);

        this.batchState = {
            isRunning: true,
            currentIndex: 0,
            total: targetCards.length,
            successful: 0,
            failed: 0
        };

        console.log(`🤝 开始批量添加好友，共 ${targetCards.length} 人`);
        MaimaiUtils.showNotification(`开始批量添加 ${targetCards.length} 人`, 'info');
        this.panel.updateProgress(this.batchState);

        for (let i = 0; i < targetCards.length; i++) {
            if (!this.batchState.isRunning) break;

            this.batchState.currentIndex = i + 1;
            this.panel.updateProgress(this.batchState);

            try {
                await this.addFriendForCard(targetCards[i]);
                this.batchState.successful++;
                console.log(`✅ 第 ${i + 1}/${targetCards.length} 个添加成功`);
            } catch (error) {
                this.batchState.failed++;
                console.error(`❌ 第 ${i + 1}/${targetCards.length} 个添加失败:`, error.message);
            }

            if (i < targetCards.length - 1 && this.batchState.isRunning) {
                const delay = 5000 + Math.random() * 5000;
                await MaimaiUtils.delay(delay);
            }
        }

        this.batchState.isRunning = false;
        this.panel.updateProgress(this.batchState);
        MaimaiUtils.showNotification(
            `批量添加完成！成功: ${this.batchState.successful}, 失败: ${this.batchState.failed}`,
            this.batchState.failed > 0 ? 'warning' : 'success'
        );
    }

    // 为单个卡片添加好友
    async addFriendForCard(card) {
        console.log('==========================================');
        console.log('🔍 开始为卡片添加好友...');

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

    // 批量发送消息
    async batchSendMessages(messageTemplate, count = 10) {
        const cards = this.extractor.findCandidateCards();
        if (cards.length === 0) {
            MaimaiUtils.showNotification('未检测到候选人', 'warning');
            return;
        }

        if (!messageTemplate) {
            MaimaiUtils.showNotification('请输入消息内容', 'warning');
            return;
        }

        const targetCards = cards.slice(0, count);

        this.batchState = {
            isRunning: true,
            currentIndex: 0,
            total: targetCards.length,
            successful: 0,
            failed: 0
        };

        console.log(`💬 开始批量发送消息，共 ${targetCards.length} 人`);
        this.panel.updateProgress(this.batchState);

        for (let i = 0; i < targetCards.length; i++) {
            if (!this.batchState.isRunning) break;

            this.batchState.currentIndex = i + 1;
            this.panel.updateProgress(this.batchState);

            try {
                const name = this.extractor.extractName(targetCards[i]);
                const msg = messageTemplate.replace(/{name}/g, name || '您');
                await this.sendMessageForCard(targetCards[i], msg);
                this.batchState.successful++;
            } catch (error) {
                this.batchState.failed++;
                console.error(`❌ 发送失败:`, error.message);
            }

            if (i < targetCards.length - 1 && this.batchState.isRunning) {
                await MaimaiUtils.delay(5000 + Math.random() * 5000);
            }
        }

        this.batchState.isRunning = false;
        this.panel.updateProgress(this.batchState);
        MaimaiUtils.showNotification(`发送完成！成功: ${this.batchState.successful}`, 'success');
    }

    // 发送消息
    async sendMessageForCard(card, message) {
        const contactBtn = Array.from(card.querySelectorAll('button, div')).find(el =>
            el.textContent?.includes('立即沟通')
        );

        if (!contactBtn) throw new Error('未找到立即沟通按钮');

        contactBtn.click();
        await MaimaiUtils.delay(1500);

        const inputBox = document.querySelector('textarea, [contenteditable="true"]');
        if (!inputBox) {
            const closeBtn = document.querySelector('[class*="close"]');
            if (closeBtn) closeBtn.click();
            throw new Error('未找到输入框');
        }

        inputBox.focus();
        if (inputBox.tagName === 'TEXTAREA') {
            inputBox.value = message;
        } else {
            inputBox.textContent = message;
        }
        inputBox.dispatchEvent(new Event('input', { bubbles: true }));
        await MaimaiUtils.delay(400);

        const sendBtn = Array.from(document.querySelectorAll('button')).find(el =>
            el.textContent?.includes('发送')
        );
        if (sendBtn) {
            sendBtn.click();
            await MaimaiUtils.delay(800);
        }

        const closeBtn = document.querySelector('[class*="close"]');
        if (closeBtn) closeBtn.click();
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

    // 停止批量操作
    stopBatchOperation() {
        this.batchState.isRunning = false;
        MaimaiUtils.showNotification('批量操作已停止', 'info');
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
