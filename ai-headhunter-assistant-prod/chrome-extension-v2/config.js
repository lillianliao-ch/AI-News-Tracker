/**
 * AI猎头助手 - 配置文件
 * 
 * 使用方法：
 * 1. 开发环境：将 API_BASE_URL 改为 'http://localhost:8001'
 * 2. 生产环境：将 API_BASE_URL 改为 'http://localhost:8000'
 */

// ========== 环境配置 ==========
const ENV = 'production'; // 'development' 或 'production'

const ENVIRONMENTS = {
  development: {
    API_BASE_URL: 'http://localhost:8001',
    NAME: 'AI猎头助手 [开发版]',
    COLOR: '#f59e0b' // 橙色
  },
  production: {
    API_BASE_URL: 'http://localhost:8000',
    NAME: 'AI猎头助手',
    COLOR: '#667eea' // 紫色
  }
};

// 当前环境配置
const CURRENT_ENV = ENVIRONMENTS[ENV];

// ========== 导出配置 ==========
const CONFIG = {
  API_BASE_URL: CURRENT_ENV.API_BASE_URL,
  APP_NAME: CURRENT_ENV.NAME,
  HEADER_COLOR: CURRENT_ENV.COLOR,
  ENV: ENV,
  
  DEFAULT_JD: {
    position: 'AI产品经理（C端）',
    location: ['北京', '深圳'],
    salary_range: '30-60K',
    work_years: '3-5年',
    education: '本科及以上',
    required_skills: [
      'AI产品经验（2年以上）',
      'C端产品（DAU>100万）',
      '大模型应用（RAG/Agent）'
    ],
    optional_skills: [
      '大厂背景（BAT/字节/美团等）',
      '0-1产品经验',
      'B端+C端复合背景'
    ]
  },
  PROCESSING: {
    delay_min: 2000,
    delay_max: 5000
  }
};

console.log(`%c[AI猎头助手] 当前环境: ${ENV}`, `color: ${CURRENT_ENV.COLOR}; font-weight: bold; font-size: 14px`);
console.log(`%c[AI猎头助手] API地址: ${CURRENT_ENV.API_BASE_URL}`, `color: ${CURRENT_ENV.COLOR}`);
