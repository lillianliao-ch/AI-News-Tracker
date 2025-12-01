-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('platform_admin', 'company_admin', 'consultant', 'soho');

-- CreateEnum
CREATE TYPE "UserStatus" AS ENUM ('pending', 'active', 'suspended', 'inactive');

-- CreateEnum
CREATE TYPE "CompanyStatus" AS ENUM ('pending', 'approved', 'rejected', 'suspended');

-- CreateEnum
CREATE TYPE "JobStatus" AS ENUM ('open', 'paused', 'closed');

-- CreateEnum
CREATE TYPE "SubmissionStatus" AS ENUM ('submitted', 'resume_approved', 'resume_rejected', 'interview_scheduled', 'interview_passed', 'interview_failed', 'offer_extended', 'offer_accepted', 'offer_rejected', 'hired');

-- CreateEnum
CREATE TYPE "NotificationType" AS ENUM ('job_shared', 'job_closed', 'submission_status_changed', 'maintainer_change_request', 'system_announcement');

-- CreateEnum
CREATE TYPE "SettlementStatus" AS ENUM ('pending', 'calculated', 'confirmed', 'paid', 'disputed');

-- CreateEnum
CREATE TYPE "MaintainerChangeStatus" AS ENUM ('pending', 'approved', 'rejected');

-- CreateTable
CREATE TABLE "companies" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" VARCHAR(255) NOT NULL,
    "business_license" VARCHAR(100),
    "industry" VARCHAR(100),
    "scale" VARCHAR(50),
    "contact_name" VARCHAR(100),
    "contact_phone" VARCHAR(20),
    "contact_email" VARCHAR(255),
    "address" TEXT,
    "status" "CompanyStatus" NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "companies_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "users" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "username" VARCHAR(100) NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "phone" VARCHAR(20) NOT NULL,
    "password" VARCHAR(255) NOT NULL,
    "role" "UserRole" NOT NULL,
    "status" "UserStatus" NOT NULL DEFAULT 'pending',
    "company_id" UUID,
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "company_clients" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" VARCHAR(255) NOT NULL,
    "industry" VARCHAR(100),
    "size" VARCHAR(50),
    "contact_name" VARCHAR(100) NOT NULL,
    "contact_phone" VARCHAR(20) NOT NULL,
    "contact_email" VARCHAR(255),
    "location" VARCHAR(255),
    "tags" JSON,
    "maintainer_id" UUID NOT NULL,
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "company_clients_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "jobs" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "title" VARCHAR(255) NOT NULL,
    "industry" VARCHAR(100),
    "location" VARCHAR(255),
    "salary_min" INTEGER,
    "salary_max" INTEGER,
    "description" TEXT NOT NULL,
    "requirements" TEXT NOT NULL,
    "benefits" TEXT,
    "urgency" VARCHAR(50),
    "report_to" VARCHAR(100),
    "status" "JobStatus" NOT NULL DEFAULT 'open',
    "publisher_share_pct" DECIMAL(5,2) NOT NULL,
    "referrer_share_pct" DECIMAL(5,2) NOT NULL,
    "platform_share_pct" DECIMAL(5,2) NOT NULL,
    "publisher_id" UUID NOT NULL,
    "company_client_id" UUID NOT NULL,
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "jobs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "job_permissions" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "job_id" UUID NOT NULL,
    "granted_to_user_id" UUID,
    "granted_to_company_id" UUID,
    "granted_by_id" UUID NOT NULL,
    "granted_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP(6),

    CONSTRAINT "job_permissions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "candidates" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" VARCHAR(100) NOT NULL,
    "phone" VARCHAR(20) NOT NULL,
    "email" VARCHAR(255),
    "tags" JSON,
    "maintainer_id" UUID NOT NULL,
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "candidates_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "candidate_submissions" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "candidate_id" UUID NOT NULL,
    "job_id" UUID NOT NULL,
    "submitter_id" UUID NOT NULL,
    "resume_url" TEXT,
    "custom_resume" TEXT,
    "submit_reason" TEXT,
    "match_explanation" TEXT,
    "notes" TEXT,
    "status" "SubmissionStatus" NOT NULL DEFAULT 'submitted',
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "candidate_submissions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "candidate_status_history" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "submission_id" UUID NOT NULL,
    "from_status" "SubmissionStatus",
    "to_status" "SubmissionStatus" NOT NULL,
    "comment" TEXT,
    "changed_by_id" UUID NOT NULL,
    "changed_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "candidate_status_history_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "maintainer_change_requests" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "candidate_id" UUID NOT NULL,
    "current_maintainer_id" UUID NOT NULL,
    "requested_maintainer_id" UUID NOT NULL,
    "requester_id" UUID NOT NULL,
    "reason" TEXT NOT NULL,
    "status" "MaintainerChangeStatus" NOT NULL DEFAULT 'pending',
    "reviewed_by_id" UUID,
    "reviewed_at" TIMESTAMP(6),
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "maintainer_change_requests_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "notifications" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "recipient_id" UUID NOT NULL,
    "type" "NotificationType" NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "content" TEXT NOT NULL,
    "related_id" UUID,
    "is_read" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "settlements" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "job_id" UUID NOT NULL,
    "candidate_submission_id" UUID NOT NULL,
    "total_amount" DECIMAL(12,2) NOT NULL,
    "publisher_amount" DECIMAL(12,2) NOT NULL,
    "referrer_amount" DECIMAL(12,2) NOT NULL,
    "platform_amount" DECIMAL(12,2) NOT NULL,
    "status" "SettlementStatus" NOT NULL DEFAULT 'pending',
    "confirmed_at" TIMESTAMP(6),
    "paid_at" TIMESTAMP(6),
    "created_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "settlements_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "companies_name_idx" ON "companies"("name");

-- CreateIndex
CREATE INDEX "companies_status_idx" ON "companies"("status");

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "users_phone_key" ON "users"("phone");

-- CreateIndex
CREATE INDEX "users_email_idx" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_phone_idx" ON "users"("phone");

-- CreateIndex
CREATE INDEX "users_company_id_idx" ON "users"("company_id");

-- CreateIndex
CREATE INDEX "users_role_status_idx" ON "users"("role", "status");

-- CreateIndex
CREATE INDEX "company_clients_name_idx" ON "company_clients"("name");

-- CreateIndex
CREATE INDEX "company_clients_industry_idx" ON "company_clients"("industry");

-- CreateIndex
CREATE INDEX "company_clients_maintainer_id_idx" ON "company_clients"("maintainer_id");

-- CreateIndex
CREATE INDEX "jobs_publisher_id_idx" ON "jobs"("publisher_id");

-- CreateIndex
CREATE INDEX "jobs_status_idx" ON "jobs"("status");

-- CreateIndex
CREATE INDEX "jobs_industry_idx" ON "jobs"("industry");

-- CreateIndex
CREATE INDEX "jobs_location_idx" ON "jobs"("location");

-- CreateIndex
CREATE INDEX "jobs_salary_min_salary_max_idx" ON "jobs"("salary_min", "salary_max");

-- CreateIndex
CREATE INDEX "job_permissions_job_id_idx" ON "job_permissions"("job_id");

-- CreateIndex
CREATE INDEX "job_permissions_granted_to_user_id_idx" ON "job_permissions"("granted_to_user_id");

-- CreateIndex
CREATE INDEX "job_permissions_granted_to_company_id_idx" ON "job_permissions"("granted_to_company_id");

-- CreateIndex
CREATE INDEX "candidates_name_idx" ON "candidates"("name");

-- CreateIndex
CREATE INDEX "candidates_phone_idx" ON "candidates"("phone");

-- CreateIndex
CREATE INDEX "candidates_maintainer_id_idx" ON "candidates"("maintainer_id");

-- CreateIndex
CREATE UNIQUE INDEX "candidates_name_phone_key" ON "candidates"("name", "phone");

-- CreateIndex
CREATE INDEX "candidate_submissions_candidate_id_idx" ON "candidate_submissions"("candidate_id");

-- CreateIndex
CREATE INDEX "candidate_submissions_job_id_idx" ON "candidate_submissions"("job_id");

-- CreateIndex
CREATE INDEX "candidate_submissions_submitter_id_idx" ON "candidate_submissions"("submitter_id");

-- CreateIndex
CREATE INDEX "candidate_submissions_status_idx" ON "candidate_submissions"("status");

-- CreateIndex
CREATE UNIQUE INDEX "candidate_submissions_candidate_id_job_id_key" ON "candidate_submissions"("candidate_id", "job_id");

-- CreateIndex
CREATE INDEX "candidate_status_history_submission_id_idx" ON "candidate_status_history"("submission_id");

-- CreateIndex
CREATE INDEX "candidate_status_history_changed_at_idx" ON "candidate_status_history"("changed_at");

-- CreateIndex
CREATE INDEX "maintainer_change_requests_candidate_id_idx" ON "maintainer_change_requests"("candidate_id");

-- CreateIndex
CREATE INDEX "maintainer_change_requests_status_idx" ON "maintainer_change_requests"("status");

-- CreateIndex
CREATE INDEX "notifications_recipient_id_is_read_idx" ON "notifications"("recipient_id", "is_read");

-- CreateIndex
CREATE INDEX "notifications_created_at_idx" ON "notifications"("created_at");

-- CreateIndex
CREATE INDEX "settlements_job_id_idx" ON "settlements"("job_id");

-- CreateIndex
CREATE INDEX "settlements_candidate_submission_id_idx" ON "settlements"("candidate_submission_id");

-- CreateIndex
CREATE INDEX "settlements_status_idx" ON "settlements"("status");

-- AddForeignKey
ALTER TABLE "users" ADD CONSTRAINT "users_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "companies"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "company_clients" ADD CONSTRAINT "company_clients_maintainer_id_fkey" FOREIGN KEY ("maintainer_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "jobs" ADD CONSTRAINT "jobs_publisher_id_fkey" FOREIGN KEY ("publisher_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "jobs" ADD CONSTRAINT "jobs_company_client_id_fkey" FOREIGN KEY ("company_client_id") REFERENCES "company_clients"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "job_permissions" ADD CONSTRAINT "job_permissions_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "job_permissions" ADD CONSTRAINT "job_permissions_granted_to_user_id_fkey" FOREIGN KEY ("granted_to_user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "job_permissions" ADD CONSTRAINT "job_permissions_granted_to_company_id_fkey" FOREIGN KEY ("granted_to_company_id") REFERENCES "companies"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "job_permissions" ADD CONSTRAINT "job_permissions_granted_by_id_fkey" FOREIGN KEY ("granted_by_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "candidates" ADD CONSTRAINT "candidates_maintainer_id_fkey" FOREIGN KEY ("maintainer_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "candidate_submissions" ADD CONSTRAINT "candidate_submissions_candidate_id_fkey" FOREIGN KEY ("candidate_id") REFERENCES "candidates"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "candidate_submissions" ADD CONSTRAINT "candidate_submissions_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "jobs"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "candidate_submissions" ADD CONSTRAINT "candidate_submissions_submitter_id_fkey" FOREIGN KEY ("submitter_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "candidate_status_history" ADD CONSTRAINT "candidate_status_history_submission_id_fkey" FOREIGN KEY ("submission_id") REFERENCES "candidate_submissions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "candidate_status_history" ADD CONSTRAINT "candidate_status_history_changed_by_id_fkey" FOREIGN KEY ("changed_by_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "maintainer_change_requests" ADD CONSTRAINT "maintainer_change_requests_candidate_id_fkey" FOREIGN KEY ("candidate_id") REFERENCES "candidates"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "maintainer_change_requests" ADD CONSTRAINT "maintainer_change_requests_current_maintainer_id_fkey" FOREIGN KEY ("current_maintainer_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "maintainer_change_requests" ADD CONSTRAINT "maintainer_change_requests_requested_maintainer_id_fkey" FOREIGN KEY ("requested_maintainer_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "maintainer_change_requests" ADD CONSTRAINT "maintainer_change_requests_requester_id_fkey" FOREIGN KEY ("requester_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "maintainer_change_requests" ADD CONSTRAINT "maintainer_change_requests_reviewed_by_id_fkey" FOREIGN KEY ("reviewed_by_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_recipient_id_fkey" FOREIGN KEY ("recipient_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "settlements" ADD CONSTRAINT "settlements_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "jobs"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "settlements" ADD CONSTRAINT "settlements_candidate_submission_id_fkey" FOREIGN KEY ("candidate_submission_id") REFERENCES "candidate_submissions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
