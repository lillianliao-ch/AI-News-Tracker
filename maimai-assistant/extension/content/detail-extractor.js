// Maimai Assistant - 详情面板数据提取器
// 用于从右侧详情面板提取候选人完整信息

class DetailPanelExtractor {
    constructor() {
        this.API_BASE = 'http://localhost:8502';  // 默认值，会被 init() 覆盖
        this.STREAMLIT_BASE = 'http://localhost:8501';  // Streamlit 应用
        this._initApiBase();
    }

    async _initApiBase() {
        if (typeof getApiBase === 'function') {
            this.API_BASE = await getApiBase();
        }
    }

    // 检测详情面板是否已打开
    isDetailPanelOpen() {
        // 方法1: 查找包含"工作经历"的容器
        const workHeader = Array.from(document.querySelectorAll('div'))
            .find(el => el.textContent.trim() === '工作经历');
        if (workHeader) return true;

        // 方法2: 查找包含电话号码的元素（详情面板通常显示电话）
        const phoneEl = Array.from(document.querySelectorAll('div, span'))
            .find(el => /^1[3-9]\d{9}$/.test(el.textContent.trim()));
        if (phoneEl) return true;

        // 方法3: 查找右侧面板特征 - 包含姓名和职位的组合
        const hasNameAndTitle = document.querySelector('[class*="nameRow"]') ||
            document.querySelector('[class*="profileCard"]') ||
            document.querySelector('[class*="detailPanel"]') ||
            document.querySelector('[class*="drawer"]');
        if (hasNameAndTitle) return true;

        // 方法4: 查找"存入本机通讯录"按钮
        const saveBtn = Array.from(document.querySelectorAll('button, div'))
            .find(el => el.textContent.includes('存入本机通讯录'));
        if (saveBtn) return true;

        // 方法5: 查找"前往公开档案"链接
        const archiveLink = Array.from(document.querySelectorAll('span, div'))
            .find(el => el.textContent.includes('前往公开档案'));
        if (archiveLink) return true;

        return false;
    }

    // 查找右侧详情面板容器 - 支持 iframe
    findDetailPanelContainer() {
        // 关键: 详情面板可能在 iframe 中
        const iframe = document.querySelector('#myIframe');
        if (iframe) {
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                if (iframeDoc && iframeDoc.body) {
                    console.log('✅ 找到详情面板容器 (iframe 内部)');
                    this.isIframe = true;
                    return iframeDoc.body;
                }
            } catch (e) {
                console.log('⚠️ 无法访问 iframe 内容 (跨域限制):', e.message);
            }
        }

        // 备用方法1: 在主页面查找 ant-drawer
        const drawer = document.querySelector('.ant-drawer-body');
        if (drawer) {
            console.log('✅ 找到详情面板容器 (ant-drawer-body)');
            return drawer;
        }

        // 备用方法2: 查找包含候选人信息的容器
        const contactCard = document.querySelector('.contact_detail_normal_card');
        if (contactCard) {
            console.log('✅ 找到详情面板容器 (contact_detail_normal_card)');
            return contactCard;
        }

        // 备用方法3: 查找包含"前往公开档案"的容器
        const archiveBtn = Array.from(document.querySelectorAll('span, div, a'))
            .find(el => el.textContent.includes('前往公开档案'));
        if (archiveBtn) {
            let parent = archiveBtn;
            for (let i = 0; i < 10 && parent; i++) {
                parent = parent.parentElement;
                if (parent && parent.offsetWidth > 300) {
                    console.log('✅ 找到详情面板容器 (通过前往公开档案)');
                    return parent;
                }
            }
        }

        console.log('⚠️ 未找到详情面板容器，使用全局搜索');
        return document.body;
    }

    // 从详情面板提取完整候选人信息
    extractFromDetailPanel() {
        console.log('📋 开始从详情面板提取数据...');

        // 先找到详情面板容器
        this.panelContainer = this.findDetailPanelContainer();
        const panelText = this.panelContainer.textContent || '';

        console.log('📦 面板文本长度:', panelText.length);

        const data = {
            extractedAt: new Date().toISOString(),
            source: 'maimai',
            sourceUrl: window.location.href
        };

        // 1. 提取姓名 - 从面板容器中查找
        data.name = this.extractName();
        console.log('  姓名:', data.name);

        // 2. 提取当前职位和公司
        const currentJob = this.extractCurrentJob();
        data.currentCompany = currentJob.company;
        data.currentPosition = currentJob.position;
        console.log('  当前公司:', data.currentCompany);
        console.log('  当前职位:', data.currentPosition);

        // 3. 提取地点
        data.location = this.extractLocation();
        console.log('  地点:', data.location);

        // 4. 提取工作经历
        data.workExperiences = this.extractWorkExperiences();
        console.log('  工作经历:', data.workExperiences.length, '条');

        // 5. 提取教育经历
        data.educations = this.extractEducations();
        console.log('  教育经历:', data.educations.length, '条');

        // 6. 提取技能标签
        data.skills = this.extractSkills();
        console.log('  技能标签:', data.skills);

        // 7. 获取脉脉用户ID
        data.maimaiUserId = this.extractMaimaiUserId();

        console.log('✅ 详情面板数据提取完成:', data);
        return data;
    }

    // 提取姓名 - 基于真实 DOM 结构
    extractName() {
        const container = this.panelContainer || document.body;

        // 方法1: 精确选择器 - contact_detail_name
        const nameEl = container.querySelector('.contact_detail_name span');
        if (nameEl) {
            const text = nameEl.textContent.trim();
            console.log('  找到姓名 (contact_detail_name):', text);
            return text;
        }

        // 方法2: 备用选择器
        const nameEl2 = container.querySelector('dd.contact_detail_name');
        if (nameEl2) {
            const text = nameEl2.textContent.trim();
            console.log('  找到姓名 (dd.contact_detail_name):', text);
            return text;
        }

        // 方法3: 查找大文字姓名元素
        const allSpans = container.querySelectorAll('span, div');
        for (const el of allSpans) {
            const text = el.textContent.trim();
            // 中文姓名或英文名
            if ((text.match(/^[\u4e00-\u9fa5]{2,4}$/) || text.match(/^[A-Za-z][A-Za-z\.]{1,15}$/)) && el.children.length === 0) {
                const excludeWords = ['首页', '招人', '消息', '职位', '人才', '详情', '申请', '好友', '动态', '点评'];
                if (!excludeWords.some(w => text.includes(w))) {
                    console.log('  找到姓名 (遍历):', text);
                    return text;
                }
            }
        }

        return '';
    }

    // 提取当前职位和公司 - 基于真实 DOM 结构
    extractCurrentJob() {
        const result = { company: '', position: '' };
        const container = this.panelContainer || document.body;

        // 方法1: 查找职位信息 - 在 .font-12.o-hidden.text-muted 中
        const titleElements = container.querySelectorAll('.font-12.o-hidden.text-muted span, dd.font-12 span');
        for (const el of titleElements) {
            const text = el.textContent.trim();
            // 职位通常包含公司名或职位关键词
            if (text.length > 3 && text.length < 50 &&
                (text.includes('专家') || text.includes('工程师') || text.includes('经理') ||
                    text.includes('总监') || text.includes('研究员') || text.includes('架构师'))) {
                // 整个字符串作为职位描述（公司+职位混合）
                result.position = text;

                // 尝试从常见公司列表中提取公司名
                const knownCompanies = ['阿里', '阿里云', '腾讯', '字节跳动', '百度', '美团',
                    '京东', '拼多多', '小红书', '华为', '网易', '快手', 'MiniMax', '智谱',
                    '月之暗面', '零一万物', '商汤', '旷视', '依图', '云从'];
                for (const company of knownCompanies) {
                    if (text.includes(company)) {
                        result.company = company;
                        result.position = text.replace(company, '').trim();
                        break;
                    }
                }
                break;
            }
        }

        // 方法2: 从工作经历中提取更准确的公司信息
        if (!result.company || result.company.length > 10) {
            const works = this.extractWorkExperiences();
            if (works.length > 0 && works[0].company) {
                result.company = works[0].company;
                if (!result.position && works[0].position) {
                    result.position = works[0].position;
                }
            }
        }

        return result;
    }

    // 提取地点 - 基于真实 DOM 结构
    extractLocation() {
        const container = this.panelContainer || document.body;

        // 方法1: 精确选择器 - icon_address_gray
        const locationEl = container.querySelector('.icon_address_gray');
        if (locationEl) {
            const text = locationEl.textContent.trim();
            console.log('  找到地点 (icon_address_gray):', text);
            return text;
        }

        // 方法2: 备用 - 查找包含城市名的短文本
        const locationPatterns = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉',
            '西安', '南京', '苏州', '天津', '重庆', '合肥', '郑州', '广东'];

        const allElements = container.querySelectorAll('span, dd');
        for (const el of allElements) {
            const text = el.textContent.trim();
            if (text.length < 15 && el.children.length === 0) {
                for (const city of locationPatterns) {
                    if (text.includes(city)) {
                        console.log('  找到地点 (遍历):', text);
                        return text;
                    }
                }
            }
        }
        return '';
    }

    // 提取电话号码
    extractPhone() {
        const container = this.panelContainer || document.body;

        // 精确选择器
        const phoneEl = container.querySelector('.icon_phone_gray');
        if (phoneEl) {
            return phoneEl.textContent.trim();
        }

        // 备用 - 正则匹配
        const allElements = container.querySelectorAll('span, dd');
        for (const el of allElements) {
            const text = el.textContent.trim();
            if (/^1[3-9]\d{9}$/.test(text)) {
                return text;
            }
        }
        return '';
    }


    // 提取工作经历
    extractWorkExperiences() {
        const experiences = [];
        const seenKeys = new Set(); // 用于去重
        const container = this.panelContainer || document.body;

        // 方法1: 基于真实 DOM 结构 - 只查找顶层工作条目，避免嵌套重复
        const workItems = container.querySelectorAll('.sc-dymIpo');
        if (workItems.length > 0) {
            console.log('  找到工作条目 (sc-dymIpo):', workItems.length, '条');
            workItems.forEach(item => {
                const exp = this.parseWorkItemNew(item);
                if (exp.company || exp.position) {
                    // 去重：使用公司+职位+开始时间作为唯一标识
                    const key = `${exp.company}|${exp.position}|${exp.startDate}`;
                    if (!seenKeys.has(key)) {
                        seenKeys.add(key);
                        experiences.push(exp);
                    }
                }
            });
        }

        // 方法2: 查找 panel-default 下的工作经历
        if (experiences.length === 0) {
            const panelDefault = container.querySelector('.panel-default');
            if (panelDefault) {
                // 检查是否是工作经历面板（不是教育经历）
                const panelTitle = panelDefault.querySelector('.gray-bg-f2f6f7 span');
                if (panelTitle && panelTitle.textContent.includes('工作经历')) {
                    const items = panelDefault.querySelectorAll('.list-group > div[id]');
                    items.forEach(item => {
                        const exp = this.parseWorkItemNew(item);
                        if (exp.company || exp.position) {
                            const key = `${exp.company}|${exp.position}|${exp.startDate}`;
                            if (!seenKeys.has(key)) {
                                seenKeys.add(key);
                                experiences.push(exp);
                            }
                        }
                    });
                }
            }
        }

        // 方法3: 找到"工作经历"标题后解析
        if (experiences.length === 0) {
            const workHeader = Array.from(container.querySelectorAll('span, div'))
                .find(el => el.textContent.trim() === '工作经历');
            if (workHeader) {
                let parent = workHeader.parentElement?.parentElement;
                if (parent) {
                    const items = parent.querySelectorAll('[id]');
                    items.forEach(item => {
                        if (/^\d+$/.test(item.id)) { // ID 是纯数字
                            const exp = this.parseWorkItemNew(item);
                            if (exp.company || exp.position) {
                                const key = `${exp.company}|${exp.position}|${exp.startDate}`;
                                if (!seenKeys.has(key)) {
                                    seenKeys.add(key);
                                    experiences.push(exp);
                                }
                            }
                        }
                    });
                }
            }
        }

        // 过滤掉可能混入的教育经历（公司名包含"大学"、"学院"等）
        const filteredExperiences = experiences.filter(exp => {
            const company = exp.company || '';
            return !company.includes('大学') && !company.includes('学院') && !company.includes('University');
        });

        console.log('  提取到工作经历:', filteredExperiences.length, '条');
        return filteredExperiences;
    }

    // 基于新 DOM 结构解析工作条目
    parseWorkItemNew(item) {
        const result = {
            company: '',
            position: '',
            startDate: '',
            endDate: '',
            duration: '',
            description: ''
        };

        // 提取职位 - .info-position
        const positionEl = item.querySelector('.info-position');
        if (positionEl) {
            result.position = positionEl.textContent.trim();
        }

        // 提取公司 - .info-text span
        const companyEl = item.querySelector('.info-text span');
        if (companyEl) {
            result.company = companyEl.textContent.trim();
        }

        // 提取时间 - .info-sub-title
        const timeEl = item.querySelector('.info-sub-title');
        if (timeEl) {
            const timeText = timeEl.textContent.trim();
            // 解析时间格式: "2023.12-至今 (2年2个月)"
            const timeMatch = timeText.match(/(\d{4}\.\d+)-(\S+)\s*\(([^)]+)\)/);
            if (timeMatch) {
                result.startDate = timeMatch[1];
                result.endDate = timeMatch[2];
                result.duration = timeMatch[3];
            } else {
                result.duration = timeText;
            }
        }

        // 提取描述 - .des-content
        const descEl = item.querySelector('.des-content');
        if (descEl) {
            result.description = descEl.textContent.trim();
        }

        console.log('    解析工作条目:', result.company, '-', result.position);
        return result;
    }

    // 解析单个工作条目
    parseWorkItem(item) {
        const text = item.textContent || '';
        const result = {
            company: '',
            position: '',
            startDate: '',
            endDate: '',
            duration: ''
        };

        // 提取公司名（通常是较短的文本或链接）
        const links = item.querySelectorAll('a');
        if (links.length > 0) {
            result.company = links[0].textContent.trim();
        }

        // 提取职位
        const positionMatch = text.match(/(工程师|产品经理|研究员|专家|总监|经理|leader|Leader)/);
        if (positionMatch) {
            // 尝试获取完整职位名
            const fullPosMatch = text.match(/([^\n]{0,20}(?:工程师|产品经理|研究员|专家|总监|经理|leader|Leader)[^\n]{0,10})/);
            result.position = fullPosMatch ? fullPosMatch[1].trim() : positionMatch[1];
        }

        // 提取时间
        const dateMatch = text.match(/(\d{4}\.\d+)[-–](\d{4}\.\d+|至今)/);
        if (dateMatch) {
            result.startDate = dateMatch[1];
            result.endDate = dateMatch[2];
        }

        // 提取时长
        const durationMatch = text.match(/\((\d+年\d*个月|\d+个月)\)/);
        if (durationMatch) {
            result.duration = durationMatch[1];
        }

        return result;
    }

    // 提取教育经历 - 基于真实 DOM 结构
    extractEducations() {
        const educations = [];
        const seenSchools = new Set(); // 用于去重
        const container = this.panelContainer || document.body;

        // 方法1: 查找教育经历面板 - 包含"教育经历"标题的 panel-default
        const panels = container.querySelectorAll('.panel-default');
        for (const panel of panels) {
            const title = panel.querySelector('.gray-bg-f2f6f7 span');
            if (title && title.textContent.includes('教育经历')) {
                // 找到教育经历面板，解析其中的条目
                const items = panel.querySelectorAll('.sc-gHboQg, [id]');
                items.forEach(item => {
                    if (item.id && /^\d+$/.test(item.id)) {
                        const edu = this.parseEducationItem(item);
                        if (edu.school && !seenSchools.has(edu.school)) {
                            seenSchools.add(edu.school);
                            educations.push(edu);
                        }
                    }
                });
            }
        }

        // 方法2: 直接查找 .sc-gHboQg 容器中的教育相关条目
        if (educations.length === 0) {
            const allItems = container.querySelectorAll('.sc-gHboQg');
            allItems.forEach(item => {
                // 检查是否是教育经历（学校图标或包含大学/学院）
                const logoImg = item.querySelector('.left-logo');
                const isSchool = logoImg && logoImg.src.includes('/school/');
                const text = item.textContent || '';
                const hasSchoolKeyword = text.includes('大学') || text.includes('学院') || text.includes('University');

                if (isSchool || hasSchoolKeyword) {
                    const edu = this.parseEducationItem(item);
                    if (edu.school && !seenSchools.has(edu.school)) {
                        seenSchools.add(edu.school);
                        educations.push(edu);
                    }
                }
            });
        }

        // 方法3: 备用 - 从文本中提取
        if (educations.length === 0) {
            const containerText = container.textContent || '';
            const knownSchools = ['清华大学', '北京大学', '南开大学', '复旦大学', '上海交通大学',
                '浙江大学', '中国科学技术大学', '南京大学', '哈尔滨工业大学', '上海财经大学',
                '中国人民大学', '北京航空航天大学', '西安交通大学', '华中科技大学', '武汉大学'];
            for (const school of knownSchools) {
                if (containerText.includes(school) && !seenSchools.has(school)) {
                    seenSchools.add(school);
                    educations.push({
                        school: school,
                        degree: this.extractDegreeFromText(containerText, school),
                        major: this.extractMajorFromText(containerText, school),
                        startYear: '',
                        endYear: ''
                    });
                }
            }
        }

        console.log('  提取到教育经历:', educations.length, '条');
        return educations;
    }

    // 解析单个教育条目
    parseEducationItem(item) {
        const result = {
            school: '',
            degree: '',
            major: '',
            startYear: '',
            endYear: ''
        };

        // 提取学校名 - .info-text span
        const schoolEl = item.querySelector('.info-text span');
        if (schoolEl) {
            result.school = schoolEl.textContent.trim();
        }

        // 提取详细信息 - .info-sub-title
        // 格式: "2013年-2015年，工商管理，硕士" 或 "2000年-2004年，计算机科学与技术，本科"
        const subTitleEl = item.querySelector('.info-sub-title');
        if (subTitleEl) {
            const text = subTitleEl.textContent.trim();

            // 解析时间: "2013年-2015年"
            const timeMatch = text.match(/(\d{4})年?[-–](\d{4})年?/);
            if (timeMatch) {
                result.startYear = timeMatch[1];
                result.endYear = timeMatch[2];
            }

            // 解析专业和学历 (格式: "时间，专业，学历")
            const parts = text.split(/[，,]/);
            if (parts.length >= 3) {
                result.major = parts[1].trim();
                result.degree = parts[2].trim();
            } else if (parts.length === 2) {
                // 可能只有专业或学历
                const lastPart = parts[1].trim();
                if (['博士', '硕士', '本科', '专科', 'PhD', 'Master', 'Bachelor'].includes(lastPart)) {
                    result.degree = lastPart;
                } else {
                    result.major = lastPart;
                }
            }
        }

        console.log('    解析教育条目:', result.school, '-', result.degree, '-', result.major);
        return result;
    }

    // 从文本中提取学历
    extractDegreeFromText(text, school) {
        const schoolIndex = text.indexOf(school);
        const nearText = text.substring(schoolIndex, schoolIndex + 80);

        if (nearText.includes('博士')) return '博士';
        if (nearText.includes('硕士')) return '硕士';
        if (nearText.includes('本科')) return '本科';
        if (nearText.includes('专科')) return '专科';
        return '';
    }

    // 从文本中提取专业
    extractMajorFromText(text, school) {
        const schoolIndex = text.indexOf(school);
        const nearText = text.substring(schoolIndex, schoolIndex + 80);

        // 匹配常见专业模式
        const majorMatch = nearText.match(/[，,]([^，,]+?)[，,](博士|硕士|本科|专科)/);
        if (majorMatch) {
            return majorMatch[1].trim();
        }
        return '';
    }

    // 提取技能标签
    extractSkills() {
        const skills = [];
        const container = this.panelContainer || document.body;

        // 方法1: 精确选择器 - .exp_tag_text (工作经历中的技能标签)
        const expTags = container.querySelectorAll('.exp_tag_text, .exp_tag_bg');
        expTags.forEach(tag => {
            const text = tag.textContent.trim();
            if (text && text.length < 20 && !skills.includes(text)) {
                skills.push(text);
            }
        });

        // 方法2: 查找技能相关的容器
        const tagContainers = container.querySelectorAll('[class*="tag___"], [class*="skill___"], [class*="label___"]');
        tagContainers.forEach(tag => {
            const text = tag.textContent.trim();
            if (text && text.length < 20 && !text.includes('·') && !skills.includes(text)) {
                skills.push(text);
            }
        });

        // 方法3: 从页面文本中提取常见技能关键词
        const pageText = container.textContent || '';
        const techSkills = ['Python', 'Java', 'Go', 'Golang', 'C++', 'JavaScript', 'TypeScript',
            'PyTorch', 'TensorFlow', 'Kubernetes', 'Docker', 'React', 'Vue', 'Linux',
            'LLM', '大模型', 'NLP', '推荐算法', '后端开发', '前端开发', 'AI', '架构设计', '系统架构',
            '全栈开发', '研发团队管理'];

        for (const skill of techSkills) {
            if (pageText.includes(skill) && !skills.includes(skill)) {
                skills.push(skill);
            }
        }

        console.log('  提取到技能:', skills.join(', '));
        return [...new Set(skills)].slice(0, 15);
    }

    // 提取脉脉用户ID
    extractMaimaiUserId() {
        // 从URL中提取
        const urlMatch = window.location.href.match(/dstu=(\d+)/);
        if (urlMatch) {
            return urlMatch[1];
        }

        // 从页面链接中提取
        const profileLinks = document.querySelectorAll('a[href*="profile"]');
        for (const link of profileLinks) {
            const match = link.href.match(/dstu=(\d+)/);
            if (match) {
                return match[1];
            }
        }

        return '';
    }

    // 检查候选人是否已存在于系统
    async checkCandidateExists(candidateData) {
        try {
            const response = await fetch(`${this.API_BASE}/api/candidate/check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: candidateData.name,
                    school: candidateData.educations?.[0]?.school || '',
                    companies: candidateData.workExperiences?.map(w => w.company) || [],
                    maimaiUserId: candidateData.maimaiUserId
                })
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('检查候选人失败:', error);
            return { exists: false, error: error.message };
        }
    }

    // 导入候选人到系统
    async importCandidate(candidateData) {
        try {
            const response = await fetch(`${this.API_BASE}/api/candidate/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(candidateData)
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('导入候选人失败:', error);
            return { success: false, error: error.message };
        }
    }

    // 一键导入或查看候选人
    async importOrView() {
        console.log('🚀 开始一键导入/查看...');

        // 1. 检查详情面板是否打开
        if (!this.isDetailPanelOpen()) {
            MaimaiUtils.showNotification('请先点击候选人打开详情面板', 'warning');
            return;
        }

        // 2. 提取数据
        const candidateData = this.extractFromDetailPanel();

        if (!candidateData.name) {
            MaimaiUtils.showNotification('无法提取候选人姓名', 'error');
            return;
        }

        // 3. 检查是否已存在
        MaimaiUtils.showNotification(`正在检查 ${candidateData.name}...`, 'info');
        const checkResult = await this.checkCandidateExists(candidateData);

        if (checkResult.exists) {
            // 已存在 - 显示提示
            MaimaiUtils.showNotification(`${candidateData.name} 已在系统中 (ID: ${checkResult.candidateId})`, 'success');
        } else {
            // 不存在 - 导入
            MaimaiUtils.showNotification(`正在导入 ${candidateData.name}...`, 'info');
            const importResult = await this.importCandidate(candidateData);

            if (importResult.success) {
                MaimaiUtils.showNotification(`✅ ${candidateData.name} 导入成功！(ID: ${importResult.candidateId})`, 'success');
            } else {
                MaimaiUtils.showNotification(`导入失败: ${importResult.error}`, 'error');
            }
        }
    }
}

// 导出到全局
if (typeof window !== 'undefined') {
    window.DetailPanelExtractor = DetailPanelExtractor;
}

console.log('✅ Detail Panel Extractor 加载完成');
