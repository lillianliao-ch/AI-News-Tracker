export interface User {
  id: string;
  username: string;
  email: string;
  phone: string;
  role: UserRole;
  status: UserStatus;
  companyId?: string;
  company?: Company;
  createdAt: Date;
  updatedAt: Date;
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
  createdAt: Date;
  updatedAt: Date;
}

export interface Job {
  id: string;
  title: string;
  industry: string;
  location: string;
  salaryMin: number;
  salaryMax: number;
  description: string;
  requirements: string;
  publisherId: string;
  publisher?: User;
  companyClientId: string;
  companyClient?: CompanyClient;
  status: JobStatus;
  assignmentStatus: AssignmentStatus;
  publisherSharePct: number;
  referrerSharePct: number;
  platformSharePct: number;
  assignedAt?: Date;
  assignedById?: string;
  assignedBy?: User;
  projectManager?: JobProjectManager;
  createdAt: Date;
  updatedAt: Date;
}

export enum JobStatus {
  PENDING_APPROVAL = 'pending_approval',
  APPROVED = 'approved',
  OPEN = 'open',
  PAUSED = 'paused',
  CLOSED = 'closed',
  REJECTED = 'rejected',
}

export interface Candidate {
  id: string;
  name: string;
  phone: string;
  email?: string;
  maintainerId: string;
  maintainer?: User;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
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
  createdAt: Date;
  updatedAt: Date;
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

export interface CompanyClient {
  id: string;
  name: string;
  industry: string;
  contactName: string;
  contactPhone: string;
  contactEmail?: string;
  size?: string;
  location?: string;
  tags: string[];
  status: CompanyClientStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface JobPermission {
  id: string;
  jobId: string;
  job?: Job;
  grantedToUserId?: string;
  grantedToUser?: User;
  grantedToCompanyId?: string;
  grantedToCompany?: Company;
  permissionType: PermissionType;
  grantedAt: Date;
  grantedById: string;
  grantedBy?: User;
  expiresAt?: Date;
}

export interface Notification {
  id: string;
  recipientId: string;
  recipient?: User;
  type: NotificationType;
  title: string;
  content: string;
  relatedId?: string;
  isRead: boolean;
  createdAt: Date;
}

export enum NotificationType {
  JOB_SHARED = 'job_shared',
  JOB_CLOSED = 'job_closed',
  SUBMISSION_STATUS_CHANGED = 'submission_status_changed',
  MAINTAINER_CHANGE_REQUEST = 'maintainer_change_request',
  SYSTEM_ANNOUNCEMENT = 'system_announcement',
}

export interface Settlement {
  id: string;
  jobId: string;
  job?: Job;
  candidateSubmissionId: string;
  candidateSubmission?: CandidateSubmission;
  totalAmount: number;
  publisherAmount: number;
  referrerAmount: number;
  platformAmount: number;
  status: SettlementStatus;
  confirmedAt?: Date;
  paidAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export enum SettlementStatus {
  PENDING = 'pending',
  CALCULATED = 'calculated',
  CONFIRMED = 'confirmed',
  PAID = 'paid',
  DISPUTED = 'disputed',
}

export interface MaintainerChangeRequest {
  id: string;
  candidateId: string;
  candidate?: Candidate;
  currentMaintainerId: string;
  currentMaintainer?: User;
  requestedMaintainerId: string;
  requestedMaintainer?: User;
  reason: string;
  status: MaintainerChangeStatus;
  reviewedById?: string;
  reviewedBy?: User;
  reviewedAt?: Date;
  createdAt: Date;
}

export enum MaintainerChangeStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
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
  assignedAt: Date;
  notes?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
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
  updatedAt: Date;
}