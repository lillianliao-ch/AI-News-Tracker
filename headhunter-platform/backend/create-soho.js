const { PrismaClient } = require('@prisma/client');
const { hash } = require('bcrypt');

const prisma = new PrismaClient();

async function createSoho() {
  try {
    const hashedPassword = await hash('admin123', 10);
    const soho = await prisma.user.create({
      data: {
        username: 'soho_test',
        email: 'soho@test.com', 
        phone: '13800138007',
        password: hashedPassword,
        role: 'soho',
        status: 'active',
      },
    });
    
    console.log('Created SOHO user:', soho.email);
    console.log('User ID:', soho.id);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createSoho();
