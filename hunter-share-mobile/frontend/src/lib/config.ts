// API配置
export const API_CONFIG = {
  // 使用相对路径，Next.js会代理到后端
  BASE_URL: '',
    
  // 前端URL配置
  FRONTEND_URL: typeof window !== 'undefined' 
    ? `${window.location.protocol}//${window.location.host}`
    : 'http://localhost:3002'
}

// API端点
export const API_ENDPOINTS = {
  SHARE: {
    TRACK: '/api/share/track',
    GENERATE_LINK: '/api/share/generate-link',
    QUICK_REGISTER: '/api/share/quick-register',
    STATS: '/api/share/stats'
  },
  AUTH: {
    LOGIN: '/api/auth/login'
  },
  JOBS: {
    SHARE: '/api/jobs/share'
  }
}

// 获取完整的API URL
export function getApiUrl(endpoint: string): string {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}