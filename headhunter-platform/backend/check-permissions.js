const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function checkPermissions() {
  try {
    // 检查所有JobPermission记录
    const permissions = await prisma.jobPermission.findMany({
      include: {
        job: {
          select: {
            id: true,
            title: true,
            status: true
          }
        },
        grantedToUser: {
          select: {
            id: true,
            email: true,
            role: true
          }
        },
        grantedToCompany: {
          select: {
            id: true,
            name: true
          }
        },
        grantedBy: {
          select: {
            id: true,
            email: true,
            role: true
          }
        }
      }
    });
    
    console.log('所有JobPermission记录:');
    permissions.forEach(p => {
      console.log(`- Job: ${p.job.title} (${p.job.status})`);
      if (p.grantedToUser) {
        console.log(`  分配给用户: ${p.grantedToUser.email} (${p.grantedToUser.role})`);
      }
      if (p.grantedToCompany) {
        console.log(`  分配给公司: ${p.grantedToCompany.name}`);
      }
      console.log(`  分配者: ${p.grantedBy.email}`);
      console.log('');
    });
    
    // 查找SOHO用户
    const sohoUser = await prisma.user.findUnique({
      where: { email: 'soho@test.com' }
    });
    
    if (sohoUser) {
      const sohoPermissions = await prisma.jobPermission.findMany({
        where: { grantedToUserId: sohoUser.id },
        include: {
          job: {
            select: {
              id: true,
              title: true,
              status: true
            }
          }
        }
      });
      
      console.log(`SOHO用户 (${sohoUser.email}) 的权限:`);
      sohoPermissions.forEach(p => {
        console.log(`- ${p.job.title} (${p.job.status})`);
      });
    }
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

checkPermissions();