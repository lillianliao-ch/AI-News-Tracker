import { PrismaClient, UserRole, UserStatus, CompanyStatus } from '@prisma/client';
import { hash } from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  // First, clear existing data
  await prisma.user.deleteMany({});
  await prisma.company.deleteMany({});

  // Create a company first
  const company = await prisma.company.create({
    data: {
      name: 'Test Headhunting Company',
      industry: 'Human Resources',
      scale: 'medium',
      contactName: 'Admin User',
      contactPhone: '13800138000',
      contactEmail: 'admin@test.com',
      status: CompanyStatus.approved,
    },
  });

  // Hash the password properly
  const hashedPassword = await hash('admin123', 10);

  // Create an admin user
  const adminUser = await prisma.user.create({
    data: {
      username: 'admin',
      email: 'admin@test.com',
      phone: '13800138000',
      password: hashedPassword,
      role: UserRole.platform_admin,
      status: UserStatus.active,
      companyId: company.id,
    },
  });

  // Create a company admin user
  const companyAdmin = await prisma.user.create({
    data: {
      username: 'company_admin',
      email: 'company@test.com',
      phone: '13800138001',
      password: hashedPassword,
      role: UserRole.company_admin,
      status: UserStatus.active,
      companyId: company.id,
    },
  });

  // Create a test user for the image email
  const testUser = await prisma.user.create({
    data: {
      username: 'testhunter',
      email: 'admin@testhunter.com',
      phone: '13800138002',
      password: hashedPassword,
      role: UserRole.company_admin,
      status: UserStatus.active,
      companyId: company.id,
    },
  });

  console.log('Test data created:');
  console.log('Company:', company.name, company.id);
  console.log('Admin User:', adminUser.email, 'password: admin123');
  console.log('Company Admin:', companyAdmin.email, 'password: admin123');
  console.log('Test Hunter User:', testUser.email, 'password: admin123');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });