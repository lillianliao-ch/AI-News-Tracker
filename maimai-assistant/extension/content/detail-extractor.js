// Maimai Assistant - 详情面板数据提取器
// 用于从右侧详情面板提取候选人完整信息

class DetailPanelExtractor {
    constructor() {
        this.API_BASE = 'http://localhost:8502';
    }

    // 检测详情面板是否已打开
    isDetailPanelOpen() {
        // 查找详情面板特征：包含"工作经历"或"教育经历"的容器
        const workHeader = Array.from(document.querySelectorAll('div'))
            .find(el => el.textContent.trim() === '工作经历');
        return !!workHeader;
    }

    // 从详情面板提取完整候选人信息
    extractFromDetailPanel() {
        console.log('📋 开始从详情面板提取数据...');

        const data = {
            extractedAt: new Date().toISOString(),
            source: 'maimai',
            sourceUrl: window.location.href
        };

        // 1. 提取姓名
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

    // 提取姓名
    extractName() {
        // 方法1: 查找 name___ 类名
        const nameEl = document.querySelector('[class*="name___"]');
        if (nameEl) {
            const text = nameEl.textContent.trim();
            // 过滤掉非姓名内容
            if (text && text.length <= 10 && !text.includes('·')) {
                return text;
            }
        }

        // 方法2: 查找 nameRow 中的第一个链接或文本
        const nameRow = document.querySelector('[class*="nameRow"]');
        if (nameRow) {
            const link = nameRow.querySelector('a');
            if (link) {
                const text = link.textContent.trim();
                if (text && text.length <= 10) {
                    return text;
                }
            }
        }

        // 方法3: 从标题中提取
        const headerEl = document.querySelector('[class*="header___"], [class*="profile___"]');
        if (headerEl) {
            const text = headerEl.textContent.trim();
            const match = text.match(/^([\u4e00-\u9fa5]{2,4}|[a-zA-Z]+)/);
            if (match) {
                return match[1];
            }
        }

        return '';
    }

    // 提取当前职位和公司
    extractCurrentJob() {
        const result = { company: '', position: '' };

        // 查找格式 "公司·职位" 的文本
        const allElements = document.querySelectorAll('div, span');
        for (const el of allElements) {
            const text = el.textContent.trim();
            // 匹配 "公司·职位" 格式
            if (text.includes('·') && text.length < 50 && el.children.length === 0) {
                const parts = text.split('·');
                if (parts.length >= 2) {
                    result.company = parts[0].trim();
                    result.position = parts[1].trim();
                    break;
                }
            }
        }

        // 如果没找到，从工作经历第一条提取
        if (!result.company) {
            const works = this.extractWorkExperiences();
            if (works.length > 0) {
                result.company = works[0].company || '';
                result.position = works[0].position || '';
            }
        }

        return result;
    }

    // 提取地点
    extractLocation() {
        const locationPatterns = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉',
            '西安', '南京', '苏州', '天津', '重庆', '合肥', '郑州'];

        // 查找包含城市名的元素
        const allElements = document.querySelectorAll('div, span');
        for (const el of allElements) {
            const text = el.textContent.trim();
            if (text.length < 20) {
                for (const city of locationPatterns) {
                    if (text.includes(city)) {
                        return city;
                    }
                }
            }
        }
        return '';
    }

    // 提取工作经历
    extractWorkExperiences() {
        const experiences = [];

        // 找到"工作经历"标题
        const workHeader = Array.from(document.querySelectorAll('div'))
            .find(el => el.textContent.trim() === '工作经历');

        if (!workHeader) {
            console.log('  未找到工作经历标题');
            return experiences;
        }

        // 获取工作经历的父容器
        let container = workHeader.parentElement;
        if (!container) return experiences;

        // 查找工作条目 - 通常在标题的兄弟元素或子元素中
        const workItems = container.querySelectorAll('[class*="item___"], [class*="experience___"], [class*="workItem"]');

        // 如果没有找到明确的条目类，尝试按结构解析
        if (workItems.length === 0) {
            // 遍历容器的直接子元素
            const children = Array.from(container.children);
            let foundHeader = false;

            for (const child of children) {
                if (child.textContent.trim() === '工作经历') {
                    foundHeader = true;
                    continue;
                }
                if (foundHeader && child.textContent.trim() === '教育经历') {
                    break;
                }
                if (foundHeader) {
                    const exp = this.parseWorkItem(child);
                    if (exp.company) {
                        experiences.push(exp);
                    }
                }
            }
        } else {
            workItems.forEach(item => {
                const exp = this.parseWorkItem(item);
                if (exp.company) {
                    experiences.push(exp);
                }
            });
        }

        // 如果仍然没有解析成功，使用正则从整个容器文本中提取
        if (experiences.length === 0) {
            const containerText = container.textContent;
            // 匹配公司名称模式
            const companyPatterns = [
                /([^\n]+?)\s*(\d{4}\.\d+[-–]\d{4}\.\d+|\d{4}\.\d+[-–]至今)/g,
                /(拼多多|字节跳动|腾讯|阿里巴巴|百度|美团|京东|小红书|华为|网易)[^\n]*?工程师/g
            ];

            // 简单提取公司名
            const knownCompanies = ['拼多多', '字节跳动', '腾讯', '阿里巴巴', '百度', '美团',
                '京东', '小红书', '华为', '网易', 'MiniMax', '智谱'];
            for (const company of knownCompanies) {
                if (containerText.includes(company)) {
                    experiences.push({
                        company: company,
                        position: '',
                        startDate: '',
                        endDate: '',
                        duration: ''
                    });
                }
            }
        }

        return experiences;
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

    // 提取教育经历
    extractEducations() {
        const educations = [];

        // 找到"教育经历"标题
        const eduHeader = Array.from(document.querySelectorAll('div'))
            .find(el => el.textContent.trim() === '教育经历');

        if (!eduHeader) {
            return educations;
        }

        const container = eduHeader.parentElement;
        if (!container) return educations;

        const containerText = container.textContent;

        // 提取学校名
        const schoolPatterns = [
            /([^\n]*大学)[^\n]*/g,
            /([^\n]*学院)[^\n]*/g
        ];

        const schools = new Set();
        for (const pattern of schoolPatterns) {
            let match;
            while ((match = pattern.exec(containerText)) !== null) {
                const school = match[1].trim();
                if (school && school.length < 20) {
                    schools.add(school);
                }
            }
        }

        // 常见大学列表
        const knownSchools = ['清华大学', '北京大学', '南开大学', '复旦大学', '上海交通大学',
            '浙江大学', '中国科学技术大学', '中国计量大学', '哈尔滨工业大学'];
        for (const school of knownSchools) {
            if (containerText.includes(school) && !schools.has(school)) {
                schools.add(school);
            }
        }

        for (const school of schools) {
            educations.push({
                school: school,
                degree: this.extractDegree(containerText, school),
                major: ''
            });
        }

        return educations;
    }

    // 提取学历
    extractDegree(text, school) {
        const schoolIndex = text.indexOf(school);
        const nearText = text.substring(schoolIndex, schoolIndex + 50);

        if (nearText.includes('博士')) return '博士';
        if (nearText.includes('硕士')) return '硕士';
        if (nearText.includes('本科')) return '本科';
        return '';
    }

    // 提取技能标签
    extractSkills() {
        const skills = [];

        // 查找技能相关的容器
        const tagContainers = document.querySelectorAll('[class*="tag___"], [class*="skill___"], [class*="label___"]');

        tagContainers.forEach(container => {
            const text = container.textContent.trim();
            if (text && text.length < 20 && !text.includes('·')) {
                skills.push(text);
            }
        });

        // 从页面文本中提取常见技能
        const pageText = document.body.textContent;
        const techSkills = ['Python', 'Java', 'Go', 'Golang', 'C++', 'JavaScript', 'TypeScript',
            'PyTorch', 'TensorFlow', 'Kubernetes', 'Docker', 'React', 'Vue',
            'LLM', '大模型', 'NLP', '推荐算法', '后端开发', '前端开发', 'AI'];

        for (const skill of techSkills) {
            if (pageText.includes(skill) && !skills.includes(skill)) {
                skills.push(skill);
            }
        }

        // 去重
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
            // 已存在 - 跳转到详情页
            MaimaiUtils.showNotification(`${candidateData.name} 已在系统中，正在打开...`, 'success');
            window.open(`${this.API_BASE}/?page=candidate&id=${checkResult.candidateId}`, '_blank');
        } else {
            // 不存在 - 导入
            MaimaiUtils.showNotification(`正在导入 ${candidateData.name}...`, 'info');
            const importResult = await this.importCandidate(candidateData);

            if (importResult.success) {
                MaimaiUtils.showNotification(`✅ ${candidateData.name} 导入成功！`, 'success');
                // 打开新导入的候选人详情页
                window.open(`${this.API_BASE}/?page=candidate&id=${importResult.candidateId}`, '_blank');
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
