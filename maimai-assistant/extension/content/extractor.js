// Maimai Assistant - 数据提取器 (v4 - 修复语法)
class MaimaiExtractor {
    constructor() {
        this.selectors = MAIMAI_CONSTANTS.SELECTORS;
    }

    // 查找候选人卡片
    findCandidateCards() {
        console.log('🔍 查找候选人卡片...');

        // 方法1: 通过沟通类按钮定位（覆盖更多场景）
        let cards = this.findCardsByContactButton();
        if (cards.length > 0) {
            console.log(`✅ 方法1(沟通按钮): 找到 ${cards.length} 个卡片`);
            return cards;
        }

        // 方法2: 通过选择器
        cards = MaimaiUtils.findAllElements(this.selectors.CANDIDATE_CARD);
        if (cards.length > 0) {
            console.log(`✅ 方法2(选择器): 找到 ${cards.length} 个卡片`);
            return cards;
        }

        console.log('⚠️ 未找到候选人卡片');
        return [];
    }

    // 通过沟通类按钮定位卡片（精确匹配 + DOM 顺序排序）
    findCardsByContactButton() {
        const cards = [];
        const seenElements = new Set();

        // 查找所有包含「立即沟通」文字的按钮（使用 includes 避免嵌套元素导致精确匹配失败）
        const allBtns = document.querySelectorAll('button, span, div, a');
        const contactBtns = [];
        for (const el of allBtns) {
            const text = el.textContent?.trim();
            // 精确文字为「立即沟通」，但 DOM 中可能有图标子元素导致 textContent 含其他内容
            // 只取叶子节点或直接文字节点包含「立即沟通」的元素
            if (text && text.includes('立即沟通') && text.length < 20) {
                // 避免重复（父子关系）
                let dominated = false;
                for (const existing of contactBtns) {
                    if (existing.contains(el) || el.contains(existing)) {
                        dominated = true;
                        break;
                    }
                }
                if (!dominated) {
                    contactBtns.push(el);
                }
            }
        }

        console.log(`🔍 找到 ${contactBtns.length} 个「立即沟通」按钮`);

        contactBtns.forEach(btn => {
            let parent = btn.parentElement;
            for (let i = 0; i < 15 && parent; i++) {
                const textLength = parent.textContent?.length || 0;
                const hasInfo = parent.textContent?.match(/\d+年|\d+岁|本科|硕士|博士/);

                // 卡片特征：文本足够长 + 包含个人信息
                if (textLength > 80 && hasInfo) {
                    // 使用 Set 去重（避免 includes 检查对大列表性能差）
                    if (!seenElements.has(parent)) {
                        seenElements.add(parent);
                        cards.push(parent);
                    }
                    break;
                }
                parent = parent.parentElement;
            }
        });

        // 按 DOM 位置从上到下排序，确保处理顺序与页面显示一致
        cards.sort((a, b) => {
            const rectA = a.getBoundingClientRect();
            const rectB = b.getBoundingClientRect();
            return rectA.top - rectB.top;
        });

        // 再做一次去重：移除互相包含的元素（保留较小的子元素）
        // 以及位置重叠的元素（同一个候选人的不同区域被识别为不同卡片）
        const uniqueCards = [];
        for (const card of cards) {
            let dominated = false;
            const cardRect = card.getBoundingClientRect();
            for (let j = 0; j < uniqueCards.length; j++) {
                const existing = uniqueCards[j];
                // DOM 包含关系去重
                if (existing.contains(card) || card.contains(existing)) {
                    dominated = true;
                    // 如果 card 更小（更精确），替换
                    if (card.contains(existing)) {
                        // existing 是 card 的子元素，保留 existing
                    } else {
                        // card 是 existing 的子元素，用 card 替换
                        uniqueCards[j] = card;
                    }
                    break;
                }
                // 位置重叠去重（Y 坐标相差 < 20px 视为同一候选人）
                const existingRect = existing.getBoundingClientRect();
                if (Math.abs(cardRect.top - existingRect.top) < 20) {
                    dominated = true;
                    break;
                }
            }
            if (!dominated) {
                uniqueCards.push(card);
            }
        }

        console.log(`✅ 去重后共 ${uniqueCards.length} 个卡片（原始: ${cards.length}）`);
        return uniqueCards;
    }

    // 在卡片中查找"..."更多按钮
    findMoreButton(card) {
        console.log('🔍 在卡片中查找更多按钮...');

        // 方法1: 精确匹配 more___ 类名
        let moreBtn = card.querySelector('[class*="more___"]');
        if (moreBtn) {
            console.log('✅ 找到 more___ 按钮:', moreBtn.className);
            return moreBtn;
        }

        // 方法2: 查找 "立即沟通" 右侧的小按钮
        const contactBtn = Array.from(card.querySelectorAll('button, div')).find(el =>
            el.textContent?.trim() === '立即沟通'
        );

        if (contactBtn) {
            const contactRect = contactBtn.getBoundingClientRect();
            const allDivs = card.querySelectorAll('div');

            for (const div of allDivs) {
                if (div.querySelector('svg')) {
                    const rect = div.getBoundingClientRect();
                    if (rect.left > contactRect.right - 50 &&
                        rect.width > 0 && rect.width < 60 &&
                        Math.abs(rect.top - contactRect.top) < 30) {
                        console.log('✅ 找到位于立即沟通右侧的按钮');
                        return div;
                    }
                }
            }
        }

        console.log('❌ 未找到更多按钮');
        return null;
    }

    // 提取候选人
    extractCandidates(count = 10) {
        const cards = this.findCandidateCards();
        console.log(`📊 找到 ${cards.length} 个候选人卡片`);

        if (cards.length === 0) return [];

        const targetCards = cards.slice(0, count);
        return targetCards.map((card, index) => this.parseCandidateCard(card, index));
    }

    // 解析候选人卡片
    parseCandidateCard(card, index) {
        const data = {
            id: MaimaiUtils.generateUUID(),
            extractedAt: MaimaiUtils.formatTimestamp(),
            name: this.extractName(card),
            status: this.extractStatus(card),
            ...this.extractBaseInfo(card),
            tags: this.extractTags(card),
            rawText: MaimaiUtils.cleanText(card.textContent).substring(0, 300)
        };
        console.log(`✅ 提取完成: ${data.name || '未知'}`);
        return data;
    }

    extractName(card) {
        const links = card.querySelectorAll('a');
        for (const link of links) {
            const text = MaimaiUtils.cleanText(link.textContent);
            if (text && /^[\u4e00-\u9fa5]{2,4}$/.test(text)) {
                return text;
            }
        }
        const match = card.textContent?.match(/[\u4e00-\u9fa5]{2,4}/);
        return match ? match[0] : '';
    }

    extractStatus(card) {
        const text = card.textContent || '';
        if (text.includes('今日活跃')) return '今日活跃';
        if (text.includes('本周活跃')) return '本周活跃';
        if (text.includes('急求职')) return '急求职';
        return '';
    }

    extractBaseInfo(card) {
        const result = { age: '', experience: '', education: '', location: '' };
        const text = card.textContent || '';

        const ageMatch = text.match(/(\d+)岁/);
        if (ageMatch) result.age = ageMatch[1] + '岁';

        const expMatch = text.match(/(\d+)年/);
        if (expMatch) result.experience = expMatch[1] + '年';

        const eduLevels = ['博士', '硕士', '本科', '大专'];
        for (const edu of eduLevels) {
            if (text.includes(edu)) {
                result.education = edu;
                break;
            }
        }

        const cities = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '西安', '南京', '苏州'];
        for (const city of cities) {
            if (text.includes(city)) {
                result.location = city;
                break;
            }
        }

        return result;
    }

    extractTags(card) {
        const tagEls = MaimaiUtils.findAllElements(this.selectors.TAGS, card);
        return tagEls.map(el => MaimaiUtils.cleanText(el.textContent)).filter(Boolean);
    }
}

if (typeof window !== 'undefined') {
    window.MaimaiExtractor = MaimaiExtractor;
}
