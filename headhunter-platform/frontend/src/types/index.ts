export interface User {
  id: string;
  username: string;
  email: string;
  phone: string;
  role: UserRole;
  status: UserStatus;
  companyId?: string;
  company?: Company;
  createdAt: string;
  updatedAt: string;
}

export enum UserRole {
  PLATFORM_ADMIN = 'platform_admin',
  COMPANY_ADMIN = 'company_admin',
  CONSULTANT = 'consultant',
  SOHO = 'soho',
}

export enum UserStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  INACTIVE = 'inactive',
}

export enum CompanyStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  SUSPENDED = 'suspended',
}

export interface Company {
  id: string;
  name: string;
  businessLicense: string;
  contactName: string;
  contactPhone: string;
  contactEmail: string;
  status: CompanyStatus;
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface PaginatedResponse<T> {
  data?: T[];
  companies?: Company[];
  users?: User[];
  pagination?: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export enum CompanyClientStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  TERMINATED = 'terminated',
}

export enum AssignmentStatus {
  PENDING_ASSIGNMENT = 'pending_assignment',
  ASSIGNED = 'assigned',
  COMPLETED = 'completed',
}

export enum PermissionType {
  MANAGEMENT = 'management',
  PROGRESSION = 'progression',
}

export interface JobProjectManager {
  id: string;
  jobId: string;
  job?: Job;
  pmUserId: string;
  pmUser?: User;
  assignedById: string;
  assignedBy?: User;
  assignedAt: string;
  notes?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CandidateStatusLog {
  id: string;
  submissionId: string;
  submission?: CandidateSubmission;
  previousStatus?: string;
  newStatus: string;
  updatedById: string;
  updatedBy?: User;
  notes?: string;
  updatedAt: string;
}

export interface Job {
  id: string;
  title: string;
  industry?: string;
  location?: string;
  salaryMin?: number;
  salaryMax?: number;
  description: string;
  requirements: string;
  benefits?: string;
  urgency?: string;
  reportTo?: string;
  status: JobStatus;
  assignmentStatus: AssignmentStatus;
  publisherId: string;
  publisher?: User;
  companyClientId: string;
  companyClient?: CompanyClient;
  publisherSharePct: number;
  referrerSharePct: number;
  platformSharePct: number;
  assignedAt?: string;
  assignedById?: string;
  assignedBy?: User;
  projectManager?: JobProjectManager;
  candidateSubmissions?: CandidateSubmission[];
  _count?: {
    candidateSubmissions: number;
  };
  createdAt: string;
  updatedAt: string;
}

export enum JobStatus {
  PENDING_APPROVAL = 'pending_approval',
  APPROVED = 'approved',
  OPEN = 'open',
  PAUSED = 'paused',
  CLOSED = 'closed',
  REJECTED = 'rejected',
}

export interface CandidateSubmission {
  id: string;
  candidateId: string;
  candidate?: Candidate;
  jobId: string;
  job?: Job;
  submitterId: string;
  submitter?: User;
  resumeUrl?: string;
  customResume?: string;
  submitReason?: string;
  matchExplanation?: string;
  notes?: string;
  status: SubmissionStatus;
  statusLogs?: CandidateStatusLog[];
  createdAt: string;
  updatedAt: string;
}

export enum SubmissionStatus {
  SUBMITTED = 'submitted',
  RESUME_APPROVED = 'resume_approved',
  RESUME_REJECTED = 'resume_rejected',
  INTERVIEW_SCHEDULED = 'interview_scheduled',
  INTERVIEW_PASSED = 'interview_passed',
  INTERVIEW_FAILED = 'interview_failed',
  OFFER_EXTENDED = 'offer_extended',
  OFFER_ACCEPTED = 'offer_accepted',
  OFFER_REJECTED = 'offer_rejected',
  HIRED = 'hired',
}

export interface Candidate {
  id: string;
  name: string;
  phone: string;
  email?: string;
  maintainerId: string;
  maintainer?: User;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface CompanyClient {
  id: string;
  name: string;
  industry?: string;
  size?: string;
  contactName: string;
  contactPhone: string;
  contactEmail?: string;
  location?: string;
  tags?: string[];
  status: CompanyClientStatus;
  partnerCompanyId: string;
  maintainerId: string;
  createdAt: string;
  updatedAt: string;
}