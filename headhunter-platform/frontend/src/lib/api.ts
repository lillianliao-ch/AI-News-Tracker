const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      ...options.headers,
    };

    // Don't set Content-Type for FormData - let the browser set it with boundary
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      console.log('🔥 DEBUGGING: Setting application/json header')
    } else {
      console.log('🔥 DEBUGGING: FormData detected, NOT setting Content-Type header')
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Network error' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request<{ token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(data: {
    username: string;
    email: string;
    phone: string;
    password: string;
    role: string;
    companyName?: string;
    businessLicense?: string;
  }) {
    return this.request<{ message: string; userId: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getProfile() {
    return this.request<any>('/auth/profile');
  }

  // User management endpoints
  async getPendingUsers() {
    return this.request<{ users: any[] }>('/auth/pending-users');
  }

  async approveUser(userId: string, action: 'approve' | 'reject', reason?: string) {
    return this.request<{ message: string; user: any }>(`/auth/approve-user/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({ action, reason }),
    });
  }

  // Consultant management endpoints (for company admins)
  async getPendingConsultants() {
    return this.request<{ users: any[] }>('/users/pending-consultants');
  }

  async approveConsultant(userId: string, action: 'approve' | 'reject', reason?: string) {
    return this.request<{ message: string; user: any }>(`/users/approve-consultant/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({ action, reason }),
    });
  }

  // Company endpoints
  async getCompanies(params?: {
    page?: number;
    limit?: number;
    status?: string;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.status) searchParams.set('status', params.status);
    if (params?.search) searchParams.set('search', params.search);

    const queryString = searchParams.toString();
    return this.request<any>(`/companies${queryString ? `?${queryString}` : ''}`);
  }

  async getPendingCompanies() {
    return this.request<{ companies: any[] }>('/companies/pending');
  }

  async getCompany(companyId: string) {
    return this.request<any>(`/companies/${companyId}`);
  }

  async updateCompany(companyId: string, data: any) {
    return this.request<any>(`/companies/${companyId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getCompanyStats(companyId: string) {
    return this.request<any>(`/companies/${companyId}/stats`);
  }

  async approveCompany(companyId: string, action: 'approve' | 'reject', reason?: string) {
    return this.request<{ message: string; company: any }>(`/companies/${companyId}/approve`, {
      method: 'PATCH',
      body: JSON.stringify({ action, reason }),
    });
  }

  // Company Clients endpoints
  async getCompanyClients(params?: {
    page?: number;
    limit?: number;
    industry?: string;
    location?: string;
    search?: string;
    maintainerId?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.industry) searchParams.set('industry', params.industry);
    if (params?.location) searchParams.set('location', params.location);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.maintainerId) searchParams.set('maintainerId', params.maintainerId);

    const queryString = searchParams.toString();
    return this.request<any>(`/company-clients${queryString ? `?${queryString}` : ''}`);
  }

  // Resume Matching endpoints
  async findMatchingJobs(candidateId: string, config?: any) {
    return this.request<any>('/resume-matching/jobs-for-candidate', {
      method: 'POST',
      body: JSON.stringify({ candidateId, config }),
    });
  }

  async findMatchingCandidates(jobId: string, config?: any) {
    return this.request<any>('/resume-matching/candidates-for-job', {
      method: 'POST',
      body: JSON.stringify({ jobId, config }),
    });
  }

  async getAvailableJobs() {
    return this.request<any>('/resume-matching/available-jobs');
  }

  async getAvailableCandidates() {
    return this.request<any>('/resume-matching/available-candidates');
  }

  // Candidate management endpoints
  async getCandidates(params?: {
    page?: number;
    limit?: number;
    search?: string;
    tags?: string[];
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.search) searchParams.set('search', params.search);
    if (params?.tags && params.tags.length > 0) searchParams.set('tags', params.tags.join(','));

    const queryString = searchParams.toString();
    return this.request<any>(`/candidates${queryString ? `?${queryString}` : ''}`);
  }

  async getCandidate(candidateId: string) {
    return this.request<any>(`/candidates/${candidateId}`);
  }

  async createCandidate(data: {
    name: string;
    phone: string;
    email?: string;
    tags?: string[];
  }) {
    return this.request<any>('/candidates', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async submitCandidateToJob(candidateId: string, data: {
    jobId: string;
    resumeUrl?: string;
    customResume?: string;
    submitReason?: string;
    matchExplanation?: string;
    notes?: string;
  }) {
    return this.request<any>(`/candidates/${candidateId}/submit`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Job Management endpoints
  async getManagementJobs(params?: {
    page?: number;
    limit?: number;
    assignmentStatus?: string;
    jobName?: string;
    companyLocation?: string;
    jobCategory?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.assignmentStatus) searchParams.set('assignmentStatus', params.assignmentStatus);
    if (params?.jobName) searchParams.set('jobName', params.jobName);
    if (params?.companyLocation) searchParams.set('companyLocation', params.companyLocation);
    if (params?.jobCategory) searchParams.set('jobCategory', params.jobCategory);

    const queryString = searchParams.toString();
    return this.request<any>(`/job-management/management${queryString ? `?${queryString}` : ''}`);
  }

  async getProgressionJobs() {
    return this.request<any>('/job-management/progression');
  }

  async assignPM(jobId: string, pmUserId: string, notes?: string) {
    return this.request<any>(`/job-management/${jobId}/assign-pm`, {
      method: 'POST',
      body: JSON.stringify({ pmUserId, notes }),
    });
  }

  async assignJobToConsultant(jobId: string, consultantId: string, consultantRole: string, notes?: string) {
    const assigneeType = consultantRole.toUpperCase() === 'SOHO' ? 'soho' : 'consultant';
    return this.request<any>(`/job-management/${jobId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ 
        assigneeId: consultantId, 
        assigneeType,
        notes 
      }),
    });
  }

  async updateCandidateStatus(submissionId: string, status: string, notes?: string) {
    return this.request<any>(`/job-management/submissions/${submissionId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    });
  }

  async getConsultants() {
    return this.request<any>('/users/consultants');
  }

  async removeJobAssignment(jobId: string, userId: string) {
    return this.request<any>(`/job-management/${jobId}/assignments/${userId}`, {
      method: 'DELETE',
    });
  }

  // Generic HTTP methods
  async get<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // File upload methods
  async uploadResume(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('resume', file);
    return this.request<any>('/upload/resume', {
      method: 'POST',
      body: formData,
    });
  }

  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.request<any>('/upload/file', {
      method: 'POST',
      body: formData,
    });
  }

  async uploadAvatar(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('avatar', file);
    return this.request<any>('/upload/avatar', {
      method: 'POST',
      body: formData,
    });
  }
}

export const apiClient = new ApiClient();
export const api = apiClient;