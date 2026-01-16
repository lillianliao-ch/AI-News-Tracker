// Maimai Assistant - 常量定义
const MAIMAI_CONSTANTS = {
    // 页面类型
    PAGE_TYPES: {
        TALENTS: 'talents',    // 人才搜索页
        OTHER: 'other'
    },

    // 消息类型
    MESSAGE_TYPES: {
        EXTRACT_CANDIDATES: 'extract_candidates',
        SAVE_DATA: 'save_data',
        EXPORT_DATA: 'export_data',
        GET_STATS: 'get_stats',
        CLEAR_DATA: 'clear_data'
    },

    // 存储键名
    STORAGE_KEYS: {
        CANDIDATES: 'maimai_candidates',
        SETTINGS: 'maimai_settings',
        STATS: 'maimai_stats'
    },

    // DOM 选择器 (使用属性匹配避免动态哈希问题)
    SELECTORS: {
        // 候选人列表容器
        CONTAINER: [
            '#recruit_talents',
            '[class*="recruitTalentsContainer"]',
            '[class*="talentList"]'
        ],

        // 单个候选人卡片
        CANDIDATE_CARD: [
            '[class*="talentCard"]',
            '[class*="candidateCard"]',
            '[class*="talent-item"]'
        ],

        // 候选人信息字段
        NAME: [
            '[class*="name___"]',
            '[class*="talentName"]',
            '.name-text'
        ],

        STATUS: [
            '[class*="activeStatus"]',
            '[class*="statusTag"]',
            '[class*="求职状态"]'
        ],

        BASE_INFO: [
            '[class*="baseInfo___"]',
            '[class*="basicInfo"]'
        ],

        EXPECT_INFO: [
            '[class*="expectInfo___"]',
            '[class*="expectation"]'
        ],

        WORK_EXPERIENCE: [
            '[class*="workExperience___"]',
            '[class*="work-history"]'
        ],

        EDUCATION: [
            '[class*="educationExperience___"]',
            '[class*="education-history"]'
        ],

        TAGS: [
            '[class*="talentTag"]',
            '[class*="skillTag"]',
            '.mui-tag'
        ],

        // 操作按钮
        CONTACT_BTN: [
            '[class*="立即沟通"]',
            'button:contains("立即沟通")'
        ]
    },

    // 延迟配置
    DELAYS: {
        PAGE_LOAD: 2000,
        BETWEEN_EXTRACTIONS: 500,
        ANIMATION: 300
    },

    // 导出格式
    EXPORT_FORMATS: {
        CSV: 'csv',
        JSON: 'json'
    },

    // 面板配置
    PANEL: {
        WIDTH: 260,
        MIN_HEIGHT: 150,
        POSITION: {
            BOTTOM: 20,
            LEFT: 20
        },
        Z_INDEX: 99999
    }
};

// 导出到全局
if (typeof window !== 'undefined') {
    window.MAIMAI_CONSTANTS = MAIMAI_CONSTANTS;
}
