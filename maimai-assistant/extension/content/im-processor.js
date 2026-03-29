// Maimai Assistant - 消息处理引擎 (IM Processor)
class ImProcessor {
    constructor(assistant) {
        this.assistant = assistant;
        this.isRunning = false;
        this.processedCandidates = new Set();
        this.stats = { total: 0, current: 0, success: 0, fail: 0 };
    }

    logUi(msg, type = 'info') {
        console.log(`[ImProcessor UI] ${msg}`);
        if (window.assistantInstance && window.assistantInstance.panel && typeof window.assistantInstance.panel.appendAiLog === 'function') {
            window.assistantInstance.panel.appendAiLog(msg, type);
        }
    }

    async dispatchAgentLog(actionType, message, candidateName = null) {
        try {
            const apiBase = (await chrome.storage.local.get(['apiBaseUrl'])).apiBaseUrl || 'http://localhost:8502';
            await fetch(`${apiBase}/api/agent-logs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    platform: 'maimai',
                    action_type: actionType,
                    message: message,
                    candidate_name: candidateName
                })
            }).catch(e => console.warn('[ImProcessor] Failed to dispatch agent log (network):', e));
        } catch (e) {
            console.warn('[ImProcessor] Failed to dispatch agent log:', e);
        }
    }

    // 解析脉脉的时间字符串，计算距离今天的天数
    parseDaysAgo(dateStr) {
        if (!dateStr) return 0;
        dateStr = dateStr.trim();
        
        // 包含冒号，通常是今天 (e.g., "12:09", "昨天 12:09")
        if (dateStr === '刚刚' || dateStr.includes('分钟前') || dateStr.includes('小时前') || (/^\d{1,2}:\d{2}$/.test(dateStr))) {
            return 0;
        }
        if (dateStr.includes('昨天')) return 1;
        if (dateStr.includes('前天')) return 2;
        
        // "03/25", "03-25" 格式
        const dateMatch = dateStr.match(/(\d{1,2})[-/](\d{1,2})/);
        if (dateMatch) {
            const now = new Date();
            const month = parseInt(dateMatch[1], 10);
            const day = parseInt(dateMatch[2], 10);
            let year = now.getFullYear();
            
            // 如果包含了年份 "2023-03-25"
            const yearMatch = dateStr.match(/(\d{4})[-/]/);
            if (yearMatch) {
                year = parseInt(yearMatch[1], 10);
            } else if (month > now.getMonth() + 1) {
                // 如果月份大于当前月份，说明是去年的
                year--;
            }
            
            const targetDate = new Date(year, month - 1, day);
            const diffTime = Math.abs(now - targetDate);
            return Math.floor(diffTime / (1000 * 60 * 60 * 24));
        }
        
        // 默认按今天算，防止误判被过滤
        return 0;
    }

    async run(targetDays, onProgress) {
        console.log(`[ImProcessor] 开始处理近 ${targetDays} 天的消息`);
        this.isRunning = true;
        this.stats = { total: 0, current: 0, success: 0, fail: 0 };
        this.onProgress = onProgress;
        this.reportProgress();
        this.imDoc = window.document; // Default to main document

        try {
            this.logUi(`开始扫描历史消息, 目标范围: 近 ${targetDays} 天...`, 'system');
            await MaimaiUtils.delay(1000);
            
            // 找到消息列表容器
            // 已从用户提供的 HTML 确认使用的是 react-virtualized
            // 加入对 iframe 潜入的支持（脉脉企业版模块可能是独立 iframe）
            let listContainer = null;
            const selectors = ['.virtualized-message-list', '.ReactVirtualized__Grid', '.ReactVirtualized__List', '[class*="message-list"]'];
            
            for (const selector of selectors) {
                listContainer = window.document.querySelector(selector);
                if (listContainer) break;
            }

            if (!listContainer) {
                // 搜索所有的 iframe
                const iframes = Array.from(window.document.querySelectorAll('iframe'));
                for (const frame of iframes) {
                    try {
                        const innerDoc = frame.contentDocument || frame.contentWindow.document;
                        if (!innerDoc) continue;
                        for (const selector of selectors) {
                            const found = innerDoc.querySelector(selector);
                            if (found) {
                                listContainer = found;
                                this.imDoc = innerDoc;
                                console.log('[ImProcessor] 成功在 iframe 中锁定 IM 容器');
                                break;
                            }
                        }
                        if (listContainer) break;
                    } catch (e) { /* ignore cross origin */ }
                }
            }

            // 如果取到的是外层包裹器(只有overflow:hidden)，要找到有 overflow: auto 的层
            if (listContainer) {
                const scrollableCandidate = this.imDoc.querySelector('.ReactVirtualized__Grid[style*="overflow: auto"]');
                if (scrollableCandidate) {
                    listContainer = scrollableCandidate;
                }
            }
            
            if (!listContainer) {
                // 暴力查找包含时间的列表项，以此推断容器
                const timeNodes = Array.from(this.imDoc.querySelectorAll('span, div, p')).filter(el => {
                    const txt = el.textContent?.trim();
                    if (!txt) return false;
                    // 匹配：昨天，12:09，03/25，03-25 等脉脉常见时间
                    return (txt === '昨天' || txt === '前天' || /^\d{2}:\d{2}$/.test(txt) || /^\d{2}\/\d{2}$/.test(txt) || /^\d{2}-\d{2}$/.test(txt));
                });
                
                if (timeNodes.length > 0) {
                    // 向上找带有滚动条或者是ul的父级，或者子元素数量大于3的div
                    let parent = timeNodes[0].parentElement;
                    for (let i = 0; i < 8; i++) {
                        if (!parent) break;
                        if (parent.tagName === 'UL' || parent.getAttribute('role') === 'list') {
                            listContainer = parent;
                            break;
                        }
                        if (parent.children.length >= 3 && parent.scrollHeight > parent.clientHeight) {
                            listContainer = parent;
                            break;
                        }
                        parent = parent.parentElement;
                    }
                    if (!listContainer && timeNodes[0].parentElement) {
                        // 回退方案：硬取上3级作为容器
                        listContainer = timeNodes[0].parentElement.parentElement.parentElement;
                    }
                }
            }

            if (!listContainer) {
                console.error("[ImProcessor] Debug DOM Dump (Main):", window.document.body.innerHTML.substring(0, 3000));
                throw new Error("未能找到消息列表容器，请确保在招聘消息页面！(详情见控制台日志)");
            }

            console.log(`[ImProcessor] 找到消息列表容器`, listContainer);
            this.logUi(`消息列表容器锁定成功`, 'success');
            MaimaiUtils.showNotification('AI 消息处理引擎已启动', 'info');

            let processedCountThisRun = 0;
            let noNewItemsCount = 0; // 记录连续没有发现新候选人的滚动次数

            while (this.isRunning) {
                // 动态获取当前列表所有项，支持虚拟列表（DOM 节点被复用）
                const items = Array.from(listContainer.querySelectorAll('li, [class*="session-item"], [class*="list-item"], [class*="message-item"], [class*="message-detail"], [class*="ListItem"]'));
                
                if (items.length === 0) {
                    throw new Error("列表容器内未发现任何可辨识的会话项！");
                }
                
                let foundNewInCurrentView = false;
                let shouldBreakGlobal = false;

                for (const item of items) {
                    if (!this.isRunning) break;

                    // 1. 名字
                    const nameEl = item.querySelector('[class*="name"], .title');
                    const name = nameEl ? nameEl.textContent.trim() : null;
                    if (!name) continue; // 可能是复用的空壳节点
                    
                    // 2. 时间
                    const timeEl = item.querySelector('[class*="time"], [class*="date"]');
                    let timeStr = '';
                    if (timeEl) {
                        timeStr = timeEl.textContent.trim();
                    } else {
                        const spans = Array.from(item.querySelectorAll('span, div'));
                        for (const span of spans) {
                            const txt = span.textContent?.trim();
                            if (txt && (txt === '昨天' || txt.includes(':') || /^\d{2}-\d{2}$/.test(txt))) {
                                timeStr = txt;
                                break;
                            }
                        }
                    }

                    const daysAgo = this.parseDaysAgo(timeStr);
                    
                    if (daysAgo > targetDays) {
                        console.log(`[ImProcessor] 发现超过 ${targetDays} 天的消息 (${timeStr}, ${daysAgo}天前)，停止遍历。`);
                        shouldBreakGlobal = true;
                        break;
                    }

                    // 核心控制区：判断是否去处理该候选人
                    if (this.processedCandidates.has(name)) {
                        continue; // 此人在当前生命周期或之前的滚动中已处理过
                    }

                    // 发现新候选人
                    foundNewInCurrentView = true;
                    noNewItemsCount = 0; // reset 滚动计数
                    

                    this.stats.total++;
                    this.stats.current++;
                    this.reportProgress();

                    try {
                        this.logUi(`👉 开始处理: ${name} (${timeStr})`, 'action');
                        item.scrollIntoView({ behavior: 'instant', block: 'center' });
                        item.click();
                        
                        // 等待右侧聊天记录加载
                        await MaimaiUtils.delay(2500);

                        // 在右侧窗体中进行策略分发
                        await this.processCurrentChat(name);
                        
                        this.processedCandidates.add(name);
                        this.stats.success++;
                        
                        processedCountThisRun++;
                        
                        // 疲劳控制
                        if (processedCountThisRun >= 30) {
                            this.logUi(`防风控策略触发：连续处理30人，休眠 3 分钟...`, 'warning');
                            MaimaiUtils.showNotification('防限制触发，暂停 3 分钟...', 'warning');
                            for(let t=0; t<180; t++) {
                                if (!this.isRunning) break;
                                await MaimaiUtils.delay(1000);
                            }
                            processedCountThisRun = 0;
                        } else {
                            // 随机拟人延迟
                            const delay = 5000 + Math.random() * 7000;
                            console.log(`[ImProcessor] 等待 ${Math.round(delay/1000)}s...`);
                            await MaimaiUtils.delay(delay);
                        }

                    } catch (err) {
                        this.logUi(`处理 ${name} 失败: ${err.message}`, 'error');
                        await this.dispatchAgentLog('ERROR', `插件执行异常: ${err.message}`, name);
                        this.stats.fail++;
                        // 依然标记为已处理以防无限循环
                        this.processedCandidates.add(name);
                    }

                    this.reportProgress();
                }

                if (shouldBreakGlobal) {
                    break;
                }

                // 当前视窗内的所有人要么都已处理，要么没有新元素。向下滚动半页。
                if (!foundNewInCurrentView) {
                    noNewItemsCount++;
                    if (noNewItemsCount > 3) {
                        console.log('[ImProcessor] 连续3次滚动未发现新数据，视作触底。');
                        break; 
                    }
                }
                
                const prevHeight = listContainer.scrollHeight;
                listContainer.scrollTop += listContainer.clientHeight * 0.8; // 每次滚动当前视窗的 80% 高度
                await MaimaiUtils.delay(2000);
                
                if (listContainer.scrollTop + listContainer.clientHeight >= listContainer.scrollHeight - 10 && prevHeight === listContainer.scrollHeight) {
                    // 彻底触底
                    console.log(`[ImProcessor] 已抵达列表物理底部`);
                    break;
                }
            }

            if (this.isRunning) {
                MaimaiUtils.showNotification(`处理完毕：共跟进 ${this.stats.success} 个候选人`, 'success');
            }
        } catch (e) {
            console.error('[ImProcessor] 异常:', e);
            MaimaiUtils.showNotification(`处理异常: ${e.message}`, 'error');
        } finally {
            this.isRunning = false;
            this.reportProgress();
        }
    }

    async processCurrentChat(candidateName) {
        const msgs = this.imDoc.querySelectorAll('[class*="message-item"], [class*="msg-item"], [class*="chat-item"]');
        // 核心修复: 严格提取【右侧】的主聊天界面气泡，通过【物理屏幕坐标】避免抓到左侧联系人列表
        const rawItems = Array.from(this.imDoc.querySelectorAll('[class*="message-item"], [class*="msg-item"], [class*="chat-item"]'));
        const winWidth = window.innerWidth || this.imDoc.documentElement.clientWidth;
        
        // 核心修复: 左侧联系人列表通常在屏幕左边 0% - 30% 区域
        const chatMsgs = rawItems.filter(el => {
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return false;
            if (rect.left < winWidth * 0.35) return false;
            return true;
        });
        
        // --- 新增：尝试全局提取前端简历档案 ---
        let frontendProfile = null;
        if (window.TalentPanelExtractor) {
            const syncExtractor = new TalentPanelExtractor();
            frontendProfile = syncExtractor.extractFromTalentPanel();
            if (frontendProfile && frontendProfile.name) {
                // 如果是纯简历页面(比如投递页)，右侧不一定有聊天气泡
                // 我们必须保证前端档案被大模型看到。
            } else {
                frontendProfile = null;
            }
        }

        if (chatMsgs.length === 0) {
            if (frontendProfile) {
                this.logUi(`🤖 右侧无聊天气泡，但检测到纯简历档案面板，触发静默初筛...`, 'info');
                // 伪造一条系统提示，让 LLM 假装收到了简历
                chatMsgs.push({
                    textContent: "简历附件或详细档案已加载在界面上，请猎头审阅并决定是否匹配此候选人",
                    className: "system-message"
                });
            } else {
                console.log(`[ImProcessor] 右侧无历史消息且无档案，跳过`);
                return;
            }
        }

        // 获取整个聊天框的纯文本引用作为备份兜底，顺便查是否包含关键系统字眼
        const rightPanel = chatMsgs[0].closest('[class*="panel"], [class*="record"], [class*="chat"]') || this.imDoc.body;
        const rightPanelText = rightPanel.textContent || "";

        const lastMsgText = chatMsgs[chatMsgs.length - 1].textContent?.trim() || "";

        const recentMsgs = chatMsgs.slice(-15).map(m => {
            const isMine = m.className.includes('right') || m.className.includes('mine') || !!m.querySelector('[class*="right"]') || !!m.querySelector('[class*="mine"]');
            const isSystem = m.className.includes('system') || m.className.includes('time') || m.textContent.includes('已阅读您的消息') || m.textContent.includes('对方回复之前') || m.textContent.includes('交换手机号');
            const speaker = isMine ? '我' : (isSystem ? '系统提示' : '候选人');
            const text = m.textContent.trim().replace(/\s+/g, ' ');
            return `${speaker}: ${text}`;
        });
        
        const isNewFriend = lastMsgText.includes('我已通过了好友请求') || lastMsgText.includes('通过了你的好友请求');
        
        this.logUi(`🤖 呼叫大模型统筹中心推演聊天流...`, 'action');
        
        let decision = { action: 'SKIP', reason: '请求失败', crm_stage_update: 'UNTOUCHED' };
        try {
            const apiBase = (await chrome.storage.local.get(['apiBaseUrl'])).apiBaseUrl || 'http://localhost:8502';
            const response = await fetch(`${apiBase}/api/agent/decide-action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    candidate_name: candidateName, 
                    platform: 'maimai', 
                    chat_history: recentMsgs, 
                    system_hints: [], // 已废弃，LLM直接阅读对话流
                    is_new_friend: isNewFriend,
                    frontend_profile: frontendProfile
                })
            });
            decision = await response.json();
            this.logUi(`🧠 决策命令: ${decision.action} [阶段: ${decision.crm_stage_update}]`, 'highlight');
        } catch (e) {
             console.error('[ImProcessor] LLM API Failed:', e);
        }

        // ================= 此刻起，前端插件化身纯物理执行终端 =================
        switch (decision.action) {
            case 'SKIP':
                this.logUi(`⚡️ 静默跳过: ${decision.reason}`, 'info');
                await this.dispatchAgentLog('SKIP', `[状态:${decision.crm_stage_update}] ${decision.reason}\n\n========== 📝 现场聊天流 (供Debug复核) ==========\n${recentMsgs.join('\n')}`, candidateName);
                break;
                
            case 'REPLY_AND_EXTRACT_PROFILE':
                await this.handleFriend(candidateName); // 包含资料入库
                if (decision.payload_text) {
                    await this.replyInChat(decision.payload_text);
                    await this.markAsReplied(candidateName); // 核心: 自动标记CRM为「已回复」
                    this.logUi(`💬 发送破冰: ${decision.payload_text.substring(0, 20)}...`, 'success');
                    await this.dispatchAgentLog('SEND_MESSAGE', `[阶段:${decision.crm_stage_update}] 💬 ${decision.payload_text}\n\n📝 AI判定理由: ${decision.reason}`, candidateName);
                }
                break;
                
            case 'REPLY':
            case 'REPLY_TEXT':
                if (decision.payload_text) {
                    await this.replyInChat(decision.payload_text);
                    await this.markAsReplied(candidateName);
                    this.logUi(`💬 发送交互: ${decision.payload_text.substring(0, 20)}...`, 'success');
                    await this.dispatchAgentLog('SEND_MESSAGE', `[阶段:${decision.crm_stage_update}] 💬 ${decision.payload_text}\n\n📝 AI判定理由: ${decision.reason}\n\n========== 📝 现场聊天流 ==========\n${recentMsgs.join('\n')}`, candidateName);
                }
                break;
                
            case 'CLICK_PASS_RESUME':
            case 'PASS_RESUME':
                this.logUi(`简历初筛: 投递通过`, 'highlight');
                this.clickButtonByText('通过初筛');
                this.clickButtonByText('恢复初筛'); // 防御性点击，有时文案不同
                await this.dispatchAgentLog('RESUME_EVALUATE', `🤖 [AI初筛] 判定通过\n📌 理由: ${decision.reason}\n\n========== 📝 现场聊天流 ==========\n${recentMsgs.join('\n')}`, candidateName);
                break;

            case 'CLICK_REJECT_RESUME':
                this.logUi(`简历初筛: 判定不匹配，标为拒绝`, 'warning');
                // 静默模式：不要点不合适，而是加标签
                const tagGroup = document.getElementById('crmInteractiveLabels');
                if (tagGroup) { tagGroup.innerHTML += `<button class="crm-label-toggle temp-ai-reject" style="background:#fff1f0;border-color:#ffa39e;color:#cf1322;" disabled>🤖 AI判丢</button>`; }
                await this.dispatchAgentLog('RESUME_EVALUATE', `🤖 [AI初筛] 判定拒绝 (静默不反馈)\n📌 理由: ${decision.reason}\n\n========== 📝 现场聊天流 ==========\n${recentMsgs.join('\n')}`, candidateName);
                break;
                
            default:
                this.logUi(`未知指令: ${decision.action}`, 'warning');
                break;
        }
    }

    async handleFriend(candidateName) {
        // 打开人才页面
        await this.openTalentProfile();
        // 执行入库同步
        if (window.TalentPanelExtractor) {
            const syncExtractor = new TalentPanelExtractor();
            const syncResult = await syncExtractor.importOrView(); 
            if (syncResult?.success) {
                this.logUi(`📥 自动补全档案完成: ${candidateName}`, 'success');
                await this.dispatchAgentLog('IMPORT_FRIEND', `📥 自动提取简历并入库`, candidateName);
                MaimaiUtils.showNotification(`📥 [自动归档] 已成功同步好友: ${candidateName}`, 'success');
            } else {
                const fallback = this.extractChatGenericCard();
                if (fallback && window.assistantInstance) {
                    fallback.name = candidateName;
                    fallback.source = 'maimai';
                    fallback.isFriend = true;
                    this.logUi(`📥 右侧面板缺失，触发「聊天卡片」兜底数据提取`, 'warning');
                    await window.assistantInstance.handleSingleCandidateExtractAndSave(fallback, null);
                    MaimaiUtils.showNotification(`📥 [兜底归档] 已成功同步好友: ${candidateName}`, 'success');
                }
            }
        } else {
            console.warn("[ImProcessor] TalentPanelExtractor 未加载");
        }
    }

    async handleResume(candidateName, msgText) {
        // 打开人才详情
        await this.openTalentProfile();
        let resumePayload = null;
        if (window.TalentPanelExtractor) {
            const syncExtractor = new TalentPanelExtractor();
            resumePayload = syncExtractor.extractFromTalentPanel();
            
            if (!resumePayload || Object.keys(resumePayload).length === 0 || !resumePayload.name) {
                console.log(`[ImProcessor] 简历详情面板未就绪，使用聊天卡片兜底提取`);
                const fallback = this.extractChatGenericCard();
                if (fallback) {
                    resumePayload = { ...fallback, name: candidateName, source: 'maimai' };
                }
            } else {
                // Optional: auto import it first
                await syncExtractor.importOrView(true);
            }
        }

        if (!resumePayload) {
            console.warn(`[ImProcessor] 无法提取简历信息，跳过 AI 初筛`);
            return;
        }

        // 请求 AI 接口进行判别 (Shadow Mode)
        try {
            const apiBase = (await chrome.storage.local.get(['apiBaseUrl'])).apiBaseUrl || 'http://localhost:8502';
            console.log(`[ImProcessor] 正在请求后端 /api/evaluate-resume ...`);
            MaimaiUtils.showNotification(`🤖 正在发送 ${candidateName} 的简历给 AI 评估...`, 'info');
            const response = await fetch(`${apiBase}/api/evaluate-resume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ candidate: resumePayload }),
                signal: AbortSignal.timeout(15000)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log(`[ImProcessor] AI初筛结果:`, result);
                if (result.decision === 'PASS') {
                    // 自动点击通过初筛
                    this.clickButtonByText('通过初筛');
                    this.clickButtonByText('恢复初筛'); // 防御性点击，有时文案不同
                    MaimaiUtils.showNotification(`🤖 [AI初筛] ${candidateName} 已通过`, 'success');
                    this.logUi(`🤖 [AI初筛] 认定匹配，已点击通过`, 'success');
                    await this.dispatchAgentLog('RESUME_EVALUATE', `🤖 [AI初筛] 判定通过\n📌 理由: ${result.reason || '匹配画像'}\n\n========== 📝 初筛参考信息 ==========\n${resumePayload.current_company} / ${resumePayload.current_title}`, candidateName);
                } else if (result.decision === 'REJECT') {
                    // 静默模式：不要点不合适，而是加标签
                    console.log(`[ImProcessor] AI判定不匹配: ${result.reason}。启用静默模式，前端标记为不通过`);
                    const tagGroup = document.getElementById('crmInteractiveLabels');
                    if (tagGroup) {
                        tagGroup.innerHTML += `<button class="crm-label-toggle temp-ai-reject" style="background:#fff1f0;border-color:#ffa39e;color:#cf1322;" disabled>🤖 AI判丢: ${result.reason.substring(0,6)}</button>`;
                    }
                    MaimaiUtils.showNotification(`🤖 [AI初筛] ${candidateName} 判定丢弃: ${result.reason || ''}`, 'warning');
                    this.logUi(`🤖 [AI初筛] 判定丢弃: ${result.reason || ''}`, 'warning');
                    await this.dispatchAgentLog('RESUME_EVALUATE', `🤖 [AI初筛] 判定丢弃 (静默不反馈)\n📌 理由: ${result.reason || ''}`, candidateName);
                }
            } else {
                console.warn(`[ImProcessor] LLM接口 /api/evaluate-resume 返回错误 (${response.status})，后端可能未实现此路由`);
            }
        } catch (e) {
            console.warn(`[ImProcessor] 请求 /api/evaluate-resume 失败，请确保后端服务正常: ${e.message}`);
        }
    }


    async openTalentProfile() {
        // 如果右侧还没有展示人才详情卡片，尝试点击顶部名字旁边的 "人才档案" 或者 ">" 按钮
        const profileBtn = Array.from(this.imDoc.querySelectorAll('button, span, a, div, i')).find(el => {
            const txt = el.textContent?.trim();
            if (txt === '前往公开档案' || txt === '人才档案' || txt === '查看简历' || txt === '展开详情') return true;
            if (el.tagName === 'I' && typeof el.className === 'string') {
                return el.className.includes('icon-right') || el.className.includes('right-icon');
            }
            return false;
        });
        if (profileBtn) {
            console.log(`[ImProcessor] 点击展开人才档案面板:`, profileBtn);
            profileBtn.click();
            await MaimaiUtils.delay(2000); // 留足时间让右侧划出面板加载
        } else {
            console.log(`[ImProcessor] 未找到面板展开按钮，尝试继续`);
        }
    }

    // 针对那些没有成功展开右侧详情页，或者本身就在对话流里的名片，做一个基础的 fallback 提取兜底
    extractChatGenericCard() {
        const card = this.imDoc.querySelector('.generic-card-center');
        if (!card) return null;
        
        const fallbackData = {
            workExperience: [],
            education: [],
            skills: []
        };
        
        const desc = card.querySelector('.generic-card-center-desc')?.textContent?.trim() || '';
        // 例: "在陕西 | 硕士 | 6年经验 | 在职·正在找工作"
        const parts = desc.split('|').map(s => s.trim());
        if (parts.length > 0) {
            fallbackData.location = parts[0];
            fallbackData.education = parts.length > 1 ? [{ school: parts[1], degree: parts[1] }] : [];
            if (parts[2]) fallbackData.workYears = parts[2];
        }

        const expLines = card.querySelectorAll('.generic-card-center-periods-line');
        expLines.forEach(line => {
            const companyRole = line.querySelector('.generic-card-center-periods-left')?.textContent?.trim();
            const dateStr = line.querySelector('.generic-card-center-periods-right')?.textContent?.trim();
            if (companyRole) {
                const parts = companyRole.split('·');
                fallbackData.workExperience.push({
                    company: parts[0] || '未知公司',
                    position: parts[1] || '未知职位',
                    date: dateStr || ''
                });
            }
        });
        
        const tags = Array.from(card.querySelectorAll('.generic-card-center-tags-item')).map(el => el.textContent?.trim());
        if (tags.length > 0) fallbackData.skills = tags;
        
        return fallbackData;
    }

    clickButtonByText(text) {
        const btns = Array.from(this.imDoc.querySelectorAll('button, div[class*="btn"]'));
        for (const b of btns) {
            if (b.textContent?.trim() === text) {
                b.click();
                return true;
            }
        }
        return false;
    }

    async replyInChat(text) {
        const textarea = this.imDoc.querySelector('textarea, [contenteditable="true"]');
        if (!textarea) return;
        
        textarea.focus();
        await MaimaiUtils.delay(200);

        if (textarea.tagName === 'TEXTAREA') {
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeSetter.call(textarea, text);
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
            textarea.textContent = text;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }

        await MaimaiUtils.delay(500);
        
        // 查找发送按钮
        const sendBtn = Array.from(this.imDoc.querySelectorAll('button, div')).find(el => el.textContent?.trim() === '发送');
        if (sendBtn) {
            sendBtn.click();
            console.log(`[ImProcessor] 已自动发送消息: "${text}"`);
        }
    }

    async markAsReplied(name) {
        try {
            const apiBase = (await chrome.storage.local.get(['apiBaseUrl'])).apiBaseUrl || 'http://localhost:8502';
            await fetch(`${apiBase}/api/comm-log`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_name: name,
                    message: "[AI Processor] 检测到实际回复并已自动跟进",
                    channel: 'maimai',
                    outreach_type: 'replied'
                })
            });
        } catch(e) {
            console.warn(`[ImProcessor] 标记已回复状态失败:`, e);
        }
    }

    reportProgress() {
        if (this.onProgress) {
            this.onProgress(this.stats);
        }
    }

    stop() {
        this.isRunning = false;
        MaimaiUtils.showNotification('已发送停止指令，将在当前周期结束后停止。', 'info');
    }
}
window.ImProcessor = ImProcessor;
