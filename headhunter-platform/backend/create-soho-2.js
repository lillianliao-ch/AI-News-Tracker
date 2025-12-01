const { PrismaClient } = require('@prisma/client');
const { hash } = require('bcrypt');

const prisma = new PrismaClient();

async function createSoho2() {
  try {
    const hashedPassword = await hash('admin123', 10);
    const soho = await prisma.user.create({
      data: {
        username: 'soho_test_2',
        email: 'soho2@test.com', 
        phone: '13800138006',
        password: hashedPassword,
        role: 'soho',
        status: 'active',
      },
    });
    
    console.log('Created SOHO user 2:', soho.email);
    console.log('User ID:', soho.id);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createSoho2();