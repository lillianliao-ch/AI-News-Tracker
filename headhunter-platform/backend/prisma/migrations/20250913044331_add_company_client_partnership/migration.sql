/*
  Warnings:

  - Added the required column `partner_company_id` to the `company_clients` table without a default value. This is not possible if the table is not empty.

*/
-- Add the column as nullable first
ALTER TABLE "company_clients" ADD COLUMN "partner_company_id" UUID;

-- Update existing records: set partner_company_id to the maintainer's company_id
UPDATE "company_clients" 
SET "partner_company_id" = (
  SELECT "company_id" 
  FROM "users" 
  WHERE "users"."id" = "company_clients"."maintainer_id"
)
WHERE "partner_company_id" IS NULL;

-- For any records where maintainer has no company, we need to handle this
-- First, let's find the first available company to use as default
UPDATE "company_clients" 
SET "partner_company_id" = (
  SELECT "id" 
  FROM "companies" 
  WHERE "status" = 'approved' 
  LIMIT 1
)
WHERE "partner_company_id" IS NULL;

-- Now make the column NOT NULL
ALTER TABLE "company_clients" ALTER COLUMN "partner_company_id" SET NOT NULL;

-- CreateIndex
CREATE INDEX "company_clients_partner_company_id_idx" ON "company_clients"("partner_company_id");

-- AddForeignKey
ALTER TABLE "company_clients" ADD CONSTRAINT "company_clients_partner_company_id_fkey" FOREIGN KEY ("partner_company_id") REFERENCES "companies"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
