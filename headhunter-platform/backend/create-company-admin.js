const { PrismaClient } = require('@prisma/client');
const { hash } = require('bcrypt');

const prisma = new PrismaClient();

async function createCompanyAdmin() {
  try {
    // 获取公司ID
    const company = await prisma.company.findFirst();
    
    // 创建company_admin用户
    const hashedPassword = await hash('admin123', 10);
    const companyAdmin = await prisma.user.create({
      data: {
        username: 'company_admin_test',
        email: 'company_admin@test.com', 
        phone: '13800138008',
        password: hashedPassword,
        role: 'company_admin',
        status: 'active',
        companyId: company.id,
      },
    });
    
    console.log('Created company admin user:', companyAdmin.email);
    console.log('User ID:', companyAdmin.id);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createCompanyAdmin();
