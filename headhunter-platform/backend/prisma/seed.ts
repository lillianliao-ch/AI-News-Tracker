import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('Starting database seeding...');

  // Create platform admin user
  const adminPassword = await bcrypt.hash('admin123456', 10);
  const platformAdmin = await prisma.user.upsert({
    where: { email: 'admin@headhunter-platform.com' },
    update: {},
    create: {
      username: 'Platform Admin',
      email: 'admin@headhunter-platform.com',
      phone: '+8613800000000',
      password: adminPassword,
      role: 'platform_admin',
      status: 'active',
    },
  });
  console.log('✅ Created platform admin user');

  // Create test company
  const testCompany = await prisma.company.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440001' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440001',
      name: 'Test Headhunting Company',
      businessLicense: 'BL123456789',
      industry: 'Human Resources',
      scale: 'medium',
      contactName: 'John Doe',
      contactPhone: '+8613800000001',
      contactEmail: 'contact@testhunter.com',
      address: '123 Business Street, Shanghai',
      status: 'approved',
    },
  });
  console.log('✅ Created test company');

  // Create company admin user
  const companyAdminPassword = await bcrypt.hash('admin123456', 10);
  const companyAdmin = await prisma.user.upsert({
    where: { email: 'admin@testhunter.com' },
    update: {},
    create: {
      username: 'Company Admin',
      email: 'admin@testhunter.com',
      phone: '+8613800000001',
      password: companyAdminPassword,
      role: 'company_admin',
      status: 'active',
      companyId: testCompany.id,
    },
  });
  console.log('✅ Created company admin user');

  // Create consultant user
  const consultantPassword = await bcrypt.hash('consultant123', 10);
  const consultant = await prisma.user.upsert({
    where: { email: 'consultant@testhunter.com' },
    update: {},
    create: {
      username: 'Senior Consultant',
      email: 'consultant@testhunter.com',
      phone: '+8613800000002',
      password: consultantPassword,
      role: 'consultant',
      status: 'active',
      companyId: testCompany.id,
    },
  });
  console.log('✅ Created consultant user');

  // Create SOHO user
  const sohoPassword = await bcrypt.hash('soho123456', 10);
  const sohoUser = await prisma.user.upsert({
    where: { email: 'soho@example.com' },
    update: {},
    create: {
      username: 'SOHO Consultant',
      email: 'soho@example.com',
      phone: '+8613800000003',
      password: sohoPassword,
      role: 'soho',
      status: 'active',
    },
  });
  console.log('✅ Created SOHO user');

  // Create test company client
  const companyClient = await prisma.companyClient.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440002' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440002',
      name: 'Tech Startup Inc.',
      industry: 'Technology',
      size: 'startup',
      contactName: 'Jane Smith',
      contactPhone: '+8613800000010',
      contactEmail: 'hr@techstartup.com',
      location: 'Beijing',
      tags: ['technology', 'ai', 'startup'],
      maintainerId: consultant.id,
      partnerCompanyId: testCompany.id,
      status: 'active',
    },
  });
  console.log('✅ Created test company client');

  // Create test job
  const testJob = await prisma.job.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440003' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440003',
      title: 'Senior Full-Stack Developer',
      industry: 'Technology',
      location: 'Beijing, Shanghai',
      salaryMin: 300000,
      salaryMax: 500000,
      description: 'We are looking for a senior full-stack developer to join our growing team. The ideal candidate should have extensive experience with React, Node.js, and cloud technologies.',
      requirements: '- 5+ years of experience in full-stack development\n- Proficient in React, Node.js, TypeScript\n- Experience with cloud platforms (AWS, Alibaba Cloud)\n- Strong problem-solving skills\n- Bachelor\'s degree in Computer Science or related field',
      benefits: 'Competitive salary, stock options, flexible working hours, remote work options, comprehensive health insurance.',
      urgency: 'urgent',
      reportTo: 'CTO',
      status: 'open',
      publisherSharePct: 60.00,
      referrerSharePct: 35.00,
      platformSharePct: 5.00,
      publisherId: consultant.id,
      companyClientId: companyClient.id,
    },
  });
  console.log('✅ Created test job');

  // Create test candidates
  const candidate1 = await prisma.candidate.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440004' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440004',
      name: 'Alice Wang',
      phone: '+8613900000001',
      email: 'alice.wang@example.com',
      tags: ['react', 'nodejs', 'fullstack', 'senior'],
      maintainerId: consultant.id,
    },
  });

  const candidate2 = await prisma.candidate.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440005' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440005',
      name: 'Bob Chen',
      phone: '+8613900000002',
      email: 'bob.chen@example.com',
      tags: ['javascript', 'typescript', 'cloud', 'architecture'],
      maintainerId: sohoUser.id,
    },
  });
  console.log('✅ Created test candidates');

  // Create test candidate submission
  const submission = await prisma.candidateSubmission.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440006' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440006',
      candidateId: candidate1.id,
      jobId: testJob.id,
      submitterId: consultant.id,
      submitReason: 'Perfect match for the full-stack position. Has extensive React and Node.js experience.',
      matchExplanation: 'Alice has 6 years of full-stack experience with strong React and Node.js skills. She has worked on similar projects in tech startups.',
      notes: 'Very responsive candidate, available for immediate start.',
      status: 'submitted',
    },
  });
  console.log('✅ Created test candidate submission');

  // Create job permission (share job with SOHO user)
  await prisma.jobPermission.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440007' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440007',
      jobId: testJob.id,
      grantedToUserId: sohoUser.id,
      grantedById: consultant.id,
    },
  });
  console.log('✅ Created job permission');

  // Create test notification
  await prisma.notification.upsert({
    where: { id: '550e8400-e29b-41d4-a716-446655440008' },
    update: {},
    create: {
      id: '550e8400-e29b-41d4-a716-446655440008',
      recipientId: sohoUser.id,
      type: 'job_shared',
      title: 'New Job Opportunity Shared',
      content: `A new job "${testJob.title}" has been shared with you by ${consultant.username}. Commission split: ${testJob.referrerSharePct}%`,
      relatedId: testJob.id,
      isRead: false,
    },
  });
  console.log('✅ Created test notification');

  console.log('Database seeding completed! 🌱');
  console.log('\n📋 Test Accounts:');
  console.log('Platform Admin: admin@headhunter-platform.com / admin123456');
  console.log('Company Admin: admin@testhunter.com / admin123456');
  console.log('Consultant: consultant@testhunter.com / consultant123');
  console.log('SOHO: soho@example.com / soho123456');
}

main()
  .catch((e) => {
    console.error('Error during seeding:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });