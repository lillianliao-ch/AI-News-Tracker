const { PrismaClient } = require('@prisma/client');
const { hash } = require('bcrypt');

const prisma = new PrismaClient();

async function createConsultant() {
  try {
    // 获取一个现有公司ID
    const company = await prisma.company.findFirst();
    if (!company) {
      console.log('No company found, creating one first');
      return;
    }
    
    console.log('Found company:', company.id);
    
    // 创建consultant用户
    const hashedPassword = await hash('admin123', 10);
    const consultant = await prisma.user.create({
      data: {
        username: 'consultant_test',
        email: 'consultant@test.com', 
        phone: '13800138009',
        password: hashedPassword,
        role: 'consultant',
        status: 'active',
        companyId: company.id,
      },
    });
    
    console.log('Created consultant user:', consultant.email);
    console.log('User ID:', consultant.id);
    console.log('Company ID:', consultant.companyId);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createConsultant();
