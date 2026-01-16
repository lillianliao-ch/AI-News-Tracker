// Maimai Assistant - 数据提取器 (v4 - 修复语法)
class MaimaiExtractor {
    constructor() {
        this.selectors = MAIMAI_CONSTANTS.SELECTORS;
    }

    // 查找候选人卡片
    findCandidateCards() {
        console.log('🔍 查找候选人卡片...');

        // 方法1: 通过"立即沟通"按钮定位
        let cards = this.findCardsByContactButton();
        if (cards.length > 0) {
            console.log(`✅ 方法1(立即沟通按钮): 找到 ${cards.length} 个卡片`);
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

    // 通过"立即沟通"按钮定位卡片
    findCardsByContactButton() {
        const cards = [];

        const contactBtns = Array.from(document.querySelectorAll('button, span, div')).filter(el =>
            el.textContent?.trim() === '立即沟通'
        );

        console.log(`🔍 找到 ${contactBtns.length} 个"立即沟通"按钮`);

        contactBtns.forEach(btn => {
            let parent = btn.parentElement;
            for (let i = 0; i < 15 && parent; i++) {
                const textLength = parent.textContent?.length || 0;
                const hasMoreBtn = parent.querySelector('[class*="more___"]') !== null;
                const hasInfo = parent.textContent?.match(/\d+年|\d+岁|本科|硕士|博士/);

                if (textLength > 100 && hasMoreBtn && hasInfo) {
                    if (!cards.includes(parent)) {
                        cards.push(parent);
                        console.log(`✅ 找到卡片 #${cards.length}, 包含 more___ 按钮`);
                    }
                    break;
                }
                parent = parent.parentElement;
            }
        });

        return cards;
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
