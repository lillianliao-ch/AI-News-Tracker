/**
 * 移动端专用API客户端 - 精简版
 * 从主平台的 api.ts 提取出移动端需要的API方法
 * 
 * 使用方式：
 * import { mobileApiClient } from './lib/mobile-api'
 * 
 * // 认证
 * await mobileApiClient.quickRegister({ name, phone, wechatId, reason })
 * await mobileApiClient.login({ phone, password })
 * 
 * // 信息发布
 * await mobileApiClient.getHunterPosts({ type: 'all', page: 1 })
 * await mobileApiClient.createHunterPost({ type, title, content })
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// ==================== 类型定义 ====================

// 用户相关类型
interface User {
  id: string;
  name: string;
  phone: string;
  role: 'platform_admin' | 'company_admin' | 'consultant' | 'soho';
  status: 'registered' | 'verified' | 'active' | 'suspended';
}

interface UserProfile extends User {
  email?: string;
  wechatId?: string;
  createdAt: string;
  updatedAt: string;
}

// 猎头信息相关类型
interface HunterPost {
  id: string;
  type: 'job_seeking' | 'talent_recommendation';
  title: string;
  content: string;
  publisherName: string;
  viewCount: number;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
}

interface HunterPostDetail extends HunterPost {
  publisherId: string;
  publisherPhone: string;
  urgency: number;
  updatedAt: string;
}

// 请求参数类型
interface QuickRegisterData {
  name: string;
  phone: string;
  wechatId?: string;
  reason: string;
}

interface LoginData {
  phone: string;
  password: string;
}

interface CreateHunterPostData {
  type: 'job_seeking' | 'talent_recommendation';
  title: string;
  content: string;
}

interface GetHunterPostsParams {
  type?: 'all' | 'job_seeking' | 'talent_recommendation';
  page?: number;
  limit?: number;
  status?: 'pending' | 'approved' | 'rejected';
}

// ==================== API客户端类 ====================

class MobileApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    
    // 尝试从localStorage加载token
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('hunter_token');
    }
  }

  /**
   * 设置认证token
   */
  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('hunter_token', token);
      } else {
        localStorage.removeItem('hunter_token');
      }
    }
  }

  /**
   * 获取当前token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * 通用请求方法
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // 添加认证token
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }

  // ==================== 认证相关API ====================

  /**
   * 快速注册
   */
  async quickRegister(data: QuickRegisterData): Promise<ApiResponse<{
    user: User;
    token: string;
    tempPassword?: string;
  }>> {
    const response = await this.request<{
      user: User;
      token: string;
      tempPassword?: string;
    }>('/hunter-auth/quick-register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    // 自动保存token
    if (response.success && response.data?.token) {
      this.setToken(response.data.token);
    }

    return response;
  }

  /**
   * 登录
   */
  async login(data: LoginData): Promise<ApiResponse<{
    user: User;
    token: string;
  }>> {
    const response = await this.request<{
      user: User;
      token: string;
    }>('/hunter-auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    // 自动保存token
    if (response.success && response.data?.token) {
      this.setToken(response.data.token);
    }

    return response;
  }

  /**
   * 登出
   */
  logout() {
    this.setToken(null);
  }

  /**
   * 获取用户资料
   */
  async getProfile(): Promise<ApiResponse<UserProfile>> {
    return this.request<UserProfile>('/hunter-auth/profile', {
      method: 'GET',
    });
  }

  /**
   * 更新用户资料
   */
  async updateProfile(data: Partial<{
    name: string;
    email: string;
    wechatId: string;
  }>): Promise<ApiResponse<UserProfile>> {
    return this.request<UserProfile>('/hunter-auth/profile', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // ==================== 猎头信息相关API ====================

  /**
   * 获取信息列表
   */
  async getHunterPosts(params?: GetHunterPostsParams): Promise<ApiResponse<HunterPost[]>> {
    const searchParams = new URLSearchParams();
    if (params?.type && params.type !== 'all') {
      searchParams.set('type', params.type);
    }
    if (params?.page) {
      searchParams.set('page', params.page.toString());
    }
    if (params?.limit) {
      searchParams.set('limit', params.limit.toString());
    }
    if (params?.status) {
      searchParams.set('status', params.status);
    }

    const queryString = searchParams.toString();
    return this.request<HunterPost[]>(
      `/hunter-posts${queryString ? `?${queryString}` : ''}`,
      { method: 'GET' }
    );
  }

  /**
   * 获取我的发布
   */
  async getMyPosts(): Promise<ApiResponse<HunterPostDetail[]>> {
    return this.request<HunterPostDetail[]>('/hunter-posts/my', {
      method: 'GET',
    });
  }

  /**
   * 创建信息发布
   */
  async createHunterPost(data: CreateHunterPostData): Promise<ApiResponse<HunterPost>> {
    return this.request<HunterPost>('/hunter-posts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * 删除信息发布
   */
  async deleteHunterPost(postId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/hunter-posts/${postId}`, {
      method: 'DELETE',
    });
  }

  /**
   * 获取信息详情
   */
  async getHunterPost(postId: string): Promise<ApiResponse<HunterPostDetail>> {
    return this.request<HunterPostDetail>(`/hunter-posts/${postId}`, {
      method: 'GET',
    });
  }

  // ==================== 管理员相关API ====================

  /**
   * 获取待审核用户列表（管理员）
   */
  async getPendingUsers(): Promise<ApiResponse<User[]>> {
    return this.request<User[]>('/hunter-auth/pending-users', {
      method: 'GET',
    });
  }

  /**
   * 审核用户（管理员）
   */
  async approveUser(
    userId: string,
    action: 'approve' | 'reject',
    reason?: string
  ): Promise<ApiResponse<User>> {
    return this.request<User>(`/hunter-auth/approve-user/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({ action, reason }),
    });
  }

  /**
   * 获取待审核信息列表（管理员）
   */
  async getPendingPosts(): Promise<ApiResponse<HunterPostDetail[]>> {
    return this.getHunterPosts({ status: 'pending' });
  }

  /**
   * 审核信息（管理员）
   */
  async approvePost(
    postId: string,
    action: 'approve' | 'reject',
    reason?: string
  ): Promise<ApiResponse<HunterPost>> {
    return this.request<HunterPost>(`/hunter-posts/${postId}/approve`, {
      method: 'PATCH',
      body: JSON.stringify({ action, reason }),
    });
  }

  // ==================== 分享追踪相关API（可选）====================

  /**
   * 追踪分享链接浏览
   */
  async trackShare(data: {
    jobId?: string;
    consultantId?: string;
    action: 'view' | 'click' | 'register';
    source?: string;
    userAgent?: string;
  }): Promise<ApiResponse<void>> {
    return this.request<void>('/share/track', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * 生成分享链接
   */
  async generateShareLink(data: {
    jobId: string;
    consultantId: string;
  }): Promise<ApiResponse<{
    shortUrl: string;
    fullUrl: string;
    qrCode: string;
  }>> {
    return this.request<{
      shortUrl: string;
      fullUrl: string;
      qrCode: string;
    }>('/share/generate-link', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * 获取分享统计
   */
  async getShareStats(consultantId: string): Promise<ApiResponse<{
    totalViews: number;
    totalClicks: number;
    totalRegistrations: number;
    topJobs: Array<{
      jobId: string;
      title: string;
      views: number;
    }>;
  }>> {
    return this.request(`/share/stats?consultantId=${consultantId}`, {
      method: 'GET',
    });
  }
}

// ==================== 导出实例 ====================

export const mobileApiClient = new MobileApiClient();

// 导出类型以供其他文件使用
export type {
  User,
  UserProfile,
  HunterPost,
  HunterPostDetail,
  QuickRegisterData,
  LoginData,
  CreateHunterPostData,
  GetHunterPostsParams,
  ApiResponse,
};

// 默认导出
export default mobileApiClient;

