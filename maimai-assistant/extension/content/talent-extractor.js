// 人才库提取器 - 处理沟通管理页面的人才详情面板
// 与 detail-extractor.js (好友列表) 不同的 DOM 结构

class TalentPanelExtractor {
    constructor() {
        this.API_BASE = 'http://localhost:8502';
        this.panelContainer = null;
    }

    // 查找人才详情面板容器
    findTalentPanel() {
        // 人才库面板通常是一个 drawer 或 modal
        const selectors = [
            '.ant-drawer-body',
            '.ant-modal-body',
            '[class*="drawer"]',
            '[class*="modal"]'
        ];

        for (const selector of selectors) {
            const panel = document.querySelector(selector);
            if (panel && panel.querySelector('.showNameStyle___zGjrf')) {
                console.log('  找到人才面板:', selector);
                this.panelContainer = panel;
                return panel;
            }
        }

        // 备用：直接在 document 中查找
        if (document.querySelector('.showNameStyle___zGjrf')) {
            console.log('  使用 document.body 作为容器');
            this.panelContainer = document.body;
            return document.body;
        }

        return null;
    }

    // 从人才库详情面板提取数据
    extractFromTalentPanel() {
        console.log('📋 开始从人才库面板提取数据...');

        const panel = this.findTalentPanel();
        if (!panel) {
            console.log('  ⚠️ 未找到人才面板');
            return null;
        }

        const data = {
            name: this.extractName(),
            location: this.extractLocation(),
            experienceYears: this.extractExperienceYears(),
            education: this.extractEducation(),
            gender: this.extractGender(),
            currentCompany: '',
            currentPosition: '',
            workExperiences: this.extractWorkExperiences(),
            educations: this.extractEducations(),
            projects: this.extractProjects(),
            skills: this.extractSkills(),
            statusTags: this.extractStatusTags()
        };

        // 从工作经历中提取当前公司和职位
        if (data.workExperiences.length > 0) {
            const current = data.workExperiences[0];
            data.currentCompany = current.company;
            data.currentPosition = current.position;
        }

        console.log('  提取结果:', data);
        return data;
    }

    // 提取姓名
    extractName() {
        const container = this.panelContainer || document.body;
        const nameEl = container.querySelector('.showNameStyle___zGjrf, .font_title___1dWcC');
        if (nameEl) {
            return nameEl.textContent.trim();
        }
        return '';
    }

    // 提取位置
    extractLocation() {
        const container = this.panelContainer || document.body;
        const lineEl = container.querySelector('.lineContentStyle___ZqltN');
        if (lineEl) {
            const spans = lineEl.querySelectorAll('span');
            for (const span of spans) {
                const text = span.textContent.trim();
                // 匹配城市名
                if (text && !text.includes('年') && !text.includes('士') && !text.includes('男') && !text.includes('女') && text.length > 1 && text.length < 10) {
                    return text;
                }
            }
        }
        return '';
    }

    // 提取工作年限
    extractExperienceYears() {
        const container = this.panelContainer || document.body;
        const lineEl = container.querySelector('.lineContentStyle___ZqltN');
        if (lineEl) {
            const text = lineEl.textContent;
            const match = text.match(/(\d+)年/);
            if (match) {
                return parseInt(match[1]);
            }
        }
        return 0;
    }

    // 提取学历
    extractEducation() {
        const container = this.panelContainer || document.body;
        const lineEl = container.querySelector('.lineContentStyle___ZqltN');
        if (lineEl) {
            const text = lineEl.textContent;
            if (text.includes('博士')) return '博士';
            if (text.includes('硕士')) return '硕士';
            if (text.includes('本科')) return '本科';
            if (text.includes('专科')) return '专科';
        }
        return '';
    }

    // 提取性别
    extractGender() {
        const container = this.panelContainer || document.body;
        const lineEl = container.querySelector('.lineContentStyle___ZqltN');
        if (lineEl) {
            const text = lineEl.textContent;
            if (text.includes('男')) return '男';
            if (text.includes('女')) return '女';
        }
        return '';
    }

    // 提取状态标签
    extractStatusTags() {
        const tags = [];
        const container = this.panelContainer || document.body;

        // 状态标签
        const tag2Els = container.querySelectorAll('.tag2___3V1gO');
        tag2Els.forEach(el => {
            tags.push(el.textContent.trim());
        });

        // 人脉标签
        const tag1Els = container.querySelectorAll('.tag1___1rOh_');
        tag1Els.forEach(el => {
            tags.push(el.textContent.trim());
        });

        return tags;
    }

    // 提取工作经历
    extractWorkExperiences() {
        const experiences = [];
        const seenKeys = new Set();
        const container = this.panelContainer || document.body;

        // 查找工作经历区域
        const facets = container.querySelectorAll('.facet___2Ak8o');
        let workSection = null;

        for (const facet of facets) {
            const title = facet.querySelector('.font_title___1dWcC');
            if (title && title.textContent.includes('工作经历')) {
                workSection = facet;
                break;
            }
        }

        if (!workSection) {
            console.log('  未找到工作经历区域');
            return experiences;
        }

        // 解析每个工作条目
        const cards = workSection.querySelectorAll('.card___2U2pq');
        console.log('  找到工作条目:', cards.length, '条');

        cards.forEach(card => {
            const exp = this.parseWorkCard(card);
            if (exp.company || exp.position) {
                const key = `${exp.company}|${exp.position}|${exp.startDate}`;
                if (!seenKeys.has(key)) {
                    seenKeys.add(key);
                    experiences.push(exp);
                }
            }
        });

        return experiences;
    }

    // 解析单个工作条目
    parseWorkCard(card) {
        const result = {
            company: '',
            position: '',
            startDate: '',
            endDate: '',
            duration: '',
            description: ''
        };

        // 公司名 - .line1___9Pe0z
        const line1 = card.querySelector('.line1___9Pe0z');
        if (line1) {
            result.company = line1.textContent.trim();
        }

        // 职位 - .line2___2BjZN
        const line2 = card.querySelector('.line2___2BjZN');
        if (line2) {
            result.position = line2.textContent.trim();
        }

        // 时间 - .line3___YTbkm (格式: "2023-02-01至今" 或 "2021-07至2023-01")
        const line3 = card.querySelector('.line3___YTbkm');
        if (line3) {
            const timeText = line3.textContent.trim();
            const match = timeText.match(/(\d{4}-\d{2}(?:-\d{2})?)(至|-)(.+)/);
            if (match) {
                result.startDate = match[1];
                result.endDate = match[3];
            }
        }

        // 描述 - .line4___178ur
        const line4 = card.querySelector('.line4___178ur');
        if (line4) {
            // 获取纯文本，排除"展开"按钮
            const descSpans = line4.querySelectorAll('span[style*="color: rgb(21, 22, 31)"]');
            const descTexts = [];
            descSpans.forEach(span => {
                if (!span.querySelector('.spread_button___1ln7r')) {
                    descTexts.push(span.textContent.trim());
                }
            });
            result.description = descTexts.join(' ').substring(0, 500);
        }

        return result;
    }

    // 提取技能标签
    extractSkills() {
        const skills = [];
        const container = this.panelContainer || document.body;

        // 从工作经历卡片中提取技能标签
        const skillEls = container.querySelectorAll('[class*="bg-[#6E727A]"] span span, .flex.items-center div[class*="bg-"] span');
        skillEls.forEach(el => {
            const text = el.textContent.trim();
            if (text && text.length < 20 && !text.includes('该段经历来自') && !skills.includes(text)) {
                skills.push(text);
            }
        });

        // 从页面文本中提取常见技能
        const pageText = container.textContent || '';
        const techSkills = ['Python', 'Java', 'C++', 'PyTorch', 'TensorFlow', 'LLM', '大模型', 'NLP', 'CV', '深度学习', 'AI'];
        for (const skill of techSkills) {
            if (pageText.includes(skill) && !skills.includes(skill)) {
                skills.push(skill);
            }
        }

        return [...new Set(skills)].slice(0, 15);
    }

    // 提取教育经历
    extractEducations() {
        const educations = [];
        const seenKeys = new Set();
        const container = this.panelContainer || document.body;

        // 查找教育经历区域
        const facets = container.querySelectorAll('.facet___2Ak8o');
        let eduSection = null;

        for (const facet of facets) {
            const title = facet.querySelector('.font_title___1dWcC');
            if (title && title.textContent.includes('教育经历')) {
                eduSection = facet;
                break;
            }
        }

        if (!eduSection) {
            console.log('  未找到教育经历区域');
            return educations;
        }

        // 解析每个教育条目
        const cards = eduSection.querySelectorAll('.card___2U2pq');
        console.log('  找到教育条目:', cards.length, '条');

        cards.forEach(card => {
            const edu = this.parseEducationCard(card);
            if (edu.school) {
                const key = `${edu.school}|${edu.degree}|${edu.startYear}`;
                if (!seenKeys.has(key)) {
                    seenKeys.add(key);
                    educations.push(edu);
                }
            }
        });

        return educations;
    }

    // 解析单个教育条目
    parseEducationCard(card) {
        const result = {
            school: '',
            degree: '',
            major: '',
            startYear: '',
            endYear: '',
            tags: [],
            description: ''
        };

        // 学校名 - .line1___9Pe0z 中的 span span
        const line1 = card.querySelector('.line1___9Pe0z .popoverHoverBox___1d_XI span span');
        if (line1) {
            result.school = line1.textContent.trim();
        } else {
            // 备用选择器
            const line1Alt = card.querySelector('.line1___9Pe0z span span');
            if (line1Alt) {
                result.school = line1Alt.textContent.trim();
            }
        }

        // 学历+专业 - .line2___2BjZN (格式: "博士，信息与通信工程")
        const line2 = card.querySelector('.line2___2BjZN');
        if (line2) {
            const text = line2.textContent.trim();
            const parts = text.split(/[，,]/);
            if (parts.length >= 2) {
                result.degree = parts[0].trim();
                result.major = parts[1].trim();
            } else if (parts.length === 1) {
                // 可能只有学历或专业
                const degreeKeywords = ['博士', '硕士', '本科', '专科', 'PhD', 'Master', 'Bachelor'];
                if (degreeKeywords.some(k => text.includes(k))) {
                    result.degree = text;
                } else {
                    result.major = text;
                }
            }
        }

        // 时间 - .line3___YTbkm (格式: "2016-09至2021-06")
        const line3 = card.querySelector('.line3___YTbkm');
        if (line3) {
            const timeText = line3.textContent.trim();
            const match = timeText.match(/(\d{4})-?\d*至(\d{4})/);
            if (match) {
                result.startYear = match[1];
                result.endYear = match[2];
            }
        }

        // 描述 - GPA、研究方向、导师、奖学金等
        // 方法1: .line4___178ur 内的 styled spans
        const line4 = card.querySelector('.line4___178ur');
        if (line4) {
            const descSpans = line4.querySelectorAll('span[style*="color: rgb(21, 22, 31)"]');
            const descTexts = [];
            descSpans.forEach(span => {
                if (!span.querySelector('.spread_button___1ln7r')) {
                    descTexts.push(span.textContent.trim());
                }
            });
            if (descTexts.length > 0) {
                result.description = descTexts.join(' ').substring(0, 300);
            } else {
                // 方法2: 直接取 line4 文本（排除按钮文字）
                let text = line4.textContent.trim();
                text = text.replace(/展开|收起|该段经历来自附件简历/g, '').trim();
                if (text) {
                    result.description = text.substring(0, 300);
                }
            }
        }

        // 方法3: 扫描 card 内所有文本节点，查找 GPA/研究方向/导师等关键信息
        if (!result.description) {
            const cardText = card.textContent || '';
            const descParts = [];
            const patterns = [
                /GPA[:\s]*[\d.]+\/[\d.]+/i,
                /研究方向[:\s：]*[^•\n]+/,
                /导师[:\s：]*[^•\n]+/,
                /排名[:\s：]*[^•\n]+/,
                /奖学金[^•\n]*/,
                /前\d+%/
            ];
            for (const pattern of patterns) {
                const match = cardText.match(pattern);
                if (match) {
                    descParts.push(match[0].trim());
                }
            }
            if (descParts.length > 0) {
                result.description = descParts.join('; ').substring(0, 300);
            }
        }

        // 学校标签 (985, 211)
        const tagEls = card.querySelectorAll('[class*="ml-4"][class*="px-8"]');
        tagEls.forEach(el => {
            const tag = el.textContent.trim();
            if (tag && !result.tags.includes(tag)) {
                result.tags.push(tag);
            }
        });

        return result;
    }

    // 提取项目经历
    extractProjects() {
        const projects = [];
        const container = this.panelContainer || document.body;

        // 查找项目经历区域
        const facets = container.querySelectorAll('.facet___2Ak8o');
        let projSection = null;

        for (const facet of facets) {
            const title = facet.querySelector('.font_title___1dWcC');
            if (title && title.textContent.includes('项目经历')) {
                projSection = facet;
                break;
            }
        }

        if (!projSection) {
            console.log('  未找到项目经历区域');
            return projects;
        }

        // 解析每个项目条目
        const cards = projSection.querySelectorAll('.card___2U2pq');
        console.log('  找到项目条目:', cards.length, '条');

        cards.forEach(card => {
            const proj = this.parseProjectCard(card);
            if (proj.name) {
                projects.push(proj);
            }
        });

        return projects;
    }

    // 解析单个项目条目
    parseProjectCard(card) {
        const result = {
            name: '',
            time: '',
            description: ''
        };

        // 项目名 - .line1___9Pe0z
        const line1 = card.querySelector('.line1___9Pe0z');
        if (line1) {
            result.name = line1.textContent.trim();
        }

        // 时间 - .line3___YTbkm
        const line3 = card.querySelector('.line3___YTbkm');
        if (line3) {
            result.time = line3.textContent.trim();
        }

        // 描述 - .line4___178ur
        const line4 = card.querySelector('.line4___178ur');
        if (line4) {
            const descSpans = line4.querySelectorAll('span[style*="color: rgb(21, 22, 31)"]');
            const descTexts = [];
            descSpans.forEach(span => {
                descTexts.push(span.textContent.trim());
            });
            result.description = descTexts.join(' ').substring(0, 300);
        }

        return result;
    }

    // 生成沟通消息
    generateMessage(candidateData, template) {
        if (!template) {
            template = '您好{name}，我是XX公司的HR，看到您的简历很优秀，想和您聊聊{company}的机会，方便吗？';
        }

        let message = template;

        // 替换变量
        message = message.replace(/{name}/g, candidateData.name || '');
        message = message.replace(/{company}/g, candidateData.currentCompany || '');
        message = message.replace(/{position}/g, candidateData.currentPosition || '');
        message = message.replace(/{location}/g, candidateData.location || '');
        message = message.replace(/{experience}/g, candidateData.experienceYears ? `${candidateData.experienceYears}年` : '');
        message = message.replace(/{education}/g, candidateData.education || '');

        // 处理技能列表
        const skillsStr = (candidateData.skills || []).slice(0, 3).join('、');
        message = message.replace(/{skills}/g, skillsStr);

        return message.trim();
    }

    // 提取并生成消息
    async extractAndGenerateMessage(template) {
        const candidateData = this.extractFromTalentPanel();
        if (!candidateData || !candidateData.name) {
            return { success: false, error: '未能提取到候选人信息' };
        }

        const message = this.generateMessage(candidateData, template);

        return {
            success: true,
            candidate: candidateData,
            message: message
        };
    }

    // 同步候选人到系统（新建或更新）
    async syncCandidate(candidateData) {
        try {
            const response = await fetch(`${this.API_BASE}/api/candidate/maimai-sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(candidateData)
            });
            if (response.ok) {
                return await response.json();
            }
            const error = await response.text();
            return { success: false, error };
        } catch (e) {
            console.error('同步候选人失败:', e);
            return { success: false, error: e.message };
        }
    }

    // 一键导入或更新候选人
    async importOrView(silent = false) {
        if (!silent) console.log('🚀 [TalentPanel] 开始一键导入/更新...');

        // 1. 提取数据
        const candidateData = this.extractFromTalentPanel();

        if (!candidateData || !candidateData.name) {
            if (!silent) MaimaiUtils.showNotification('未能提取到候选人信息，请先打开候选人详情', 'warning');
            return { success: false, error: '未能提取信息' };
        }

        // 2. 补充 source 信息
        candidateData.source = 'maimai';
        candidateData.sourceUrl = window.location.href;
        candidateData.extractedAt = new Date().toISOString();

        // 3. 调用 sync 端点（自动判断新建/更新）
        if (!silent) MaimaiUtils.showNotification(`正在同步 ${candidateData.name}...`, 'info');
        const result = await this.syncCandidate(candidateData);

        if (!result.success) {
            if (!silent) MaimaiUtils.showNotification(`同步失败: ${result.error}`, 'error');
            return result;
        }

        // 4. 根据 action 显示不同通知
        if (!silent) {
            switch (result.action) {
                case 'created':
                    MaimaiUtils.showNotification(`✅ ${candidateData.name} 导入成功！(ID: ${result.candidateId})`, 'success');
                    break;
                case 'updated':
                    const fields = result.updatedFields || [];
                    MaimaiUtils.showNotification(`🔄 ${candidateData.name} 已更新 ${fields.length} 个字段 (ID: ${result.candidateId})`, 'success');
                    break;
                case 'unchanged':
                    MaimaiUtils.showNotification(`📋 ${candidateData.name} 已在库中，无新数据 (ID: ${result.candidateId})`, 'info');
                    break;
                default:
                    MaimaiUtils.showNotification(`${result.message || '同步完成'}`, 'success');
            }
        }
        return result;
    }
}

// 导出到全局
if (typeof window !== 'undefined') {
    window.TalentPanelExtractor = TalentPanelExtractor;
}

console.log('✅ Talent Panel Extractor 加载完成');
