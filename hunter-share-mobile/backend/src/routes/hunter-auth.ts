import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify'
import { z } from 'zod'
import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'

const prisma = new PrismaClient()

// Schema定义
const quickRegisterSchema = z.object({
  name: z.string().min(1).max(50),
  phone: z.string().min(10).max(20),
  wechatId: z.string().optional(),
  reason: z.string().min(10).max(500).optional()
})

const loginSchema = z.object({
  phone: z.string(),
  password: z.string()
})

const verifyUserSchema = z.object({
  action: z.enum(['approve', 'reject']),
  reason: z.string().optional()
})

// JWT密钥（实际应该从环境变量获取）
const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-key'

// 生成随机密码
function generateRandomPassword(length: number = 8): string {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// 生成JWT token
function generateToken(userId: string, role: string, status: string): string {
  return jwt.sign(
    { id: userId, role, status },
    JWT_SECRET,
    { expiresIn: '7d' }
  )
}

// 验证JWT token
function verifyToken(token: string): any {
  try {
    return jwt.verify(token, JWT_SECRET)
  } catch (error) {
    return null
  }
}

// 认证中间件
async function authenticateAdmin(request: FastifyRequest, reply: FastifyReply) {
  try {
    const authHeader = request.headers.authorization
    if (!authHeader) {
      return reply.status(401).send({
        success: false,
        error: '未提供认证信息'
      })
    }

    const token = authHeader.replace('Bearer ', '')
    const decoded = verifyToken(token)
    
    if (!decoded) {
      return reply.status(401).send({
        success: false,
        error: '无效的认证信息'
      })
    }

    // 检查管理员权限
    if (decoded.role !== 'platform_admin' && decoded.role !== 'company_admin') {
      return reply.status(403).send({
        success: false,
        error: '权限不足'
      })
    }

    request.user = decoded
  } catch (error) {
    return reply.status(401).send({
      success: false,
      error: '认证失败'
    })
  }
}

// 猎头用户认证路由
export async function hunterAuthRoutes(fastify: FastifyInstance) {

  // POST /api/hunter-auth/quick-register - 快速注册
  fastify.post('/quick-register', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = quickRegisterSchema.parse(request.body)
      const { name, phone, wechatId, reason } = body

      // 检查手机号是否已存在
      const existingUser = await prisma.user.findUnique({
        where: { phone }
      })

      if (existingUser) {
        return reply.status(409).send({
          success: false,
          error: '手机号已注册'
        })
      }

      // 生成临时密码
      const tempPassword = generateRandomPassword()
      const hashedPassword = await bcrypt.hash(tempPassword, 10)

      // 创建用户
      const user = await prisma.user.create({
        data: {
          username: name,
          email: `${phone}@hunter.temp`, // 临时邮箱
          phone: phone,
          password: hashedPassword,
          role: 'soho', // 默认为SOHO角色
          status: 'registered' // 注册状态，需要审核才能变为verified
        }
      })

      // 生成token
      const token = generateToken(user.id, user.role, user.status)

      // 发送通知给管理员（通过notification表）
      const adminUsers = await prisma.user.findMany({
        where: {
          role: { in: ['platform_admin', 'company_admin'] },
          status: 'active'
        },
        select: { id: true }
      })

      for (const admin of adminUsers) {
        await prisma.notification.create({
          data: {
            recipientId: admin.id,
            type: 'system_announcement',
            title: '新用户注册待审核',
            content: JSON.stringify({
              type: 'user_registration',
              userId: user.id,
              userName: name,
              userPhone: phone,
              wechatId: wechatId || '',
              reason: reason || '暂无说明',
              registeredAt: new Date().toISOString()
            })
          }
        })
      }

      return reply.send({
        success: true,
        data: {
          user: {
            id: user.id,
            name: user.username,
            phone: user.phone,
            status: user.status
          },
          token,
          tempPassword
        },
        message: '注册成功，等待管理员审核。临时密码已生成，请记录保存。'
      })

    } catch (error) {
      fastify.log.error('Quick register error:', error)
      return reply.status(500).send({
        success: false,
        error: `注册失败: ${error instanceof Error ? error.message : '未知错误'}`
      })
    }
  })

  // POST /api/hunter-auth/login - 登录
  fastify.post('/login', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = loginSchema.parse(request.body)
      const { phone, password } = body

      // 查找用户
      const user = await prisma.user.findUnique({
        where: { phone }
      })

      if (!user) {
        return reply.status(401).send({
          success: false,
          error: '手机号或密码错误'
        })
      }

      // 验证密码
      const isValidPassword = await bcrypt.compare(password, user.password)
      if (!isValidPassword) {
        return reply.status(401).send({
          success: false,
          error: '手机号或密码错误'
        })
      }

      // 生成token
      const token = generateToken(user.id, user.role, user.status)

      return reply.send({
        success: true,
        data: {
          user: {
            id: user.id,
            name: user.username,
            phone: user.phone,
            role: user.role,
            status: user.status
          },
          token
        },
        message: '登录成功'
      })

    } catch (error) {
      fastify.log.error('Login error:', error)
      return reply.status(500).send({
        success: false,
        error: '登录失败'
      })
    }
  })

  // GET /api/hunter-auth/pending-users - 获取待审核用户（管理员用）
  fastify.get('/pending-users', {
    preHandler: authenticateAdmin
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const pendingUsers = await prisma.user.findMany({
        where: { status: 'registered' },
        select: {
          id: true,
          username: true,
          phone: true,
          createdAt: true
        },
        orderBy: { createdAt: 'asc' }
      })

      // 获取相关的注册通知以获取额外信息
      const userNotifications = await prisma.notification.findMany({
        where: {
          title: '新用户注册待审核',
          content: {
            contains: 'user_registration'
          }
        },
        orderBy: { createdAt: 'desc' }
      })

      // 合并用户信息和注册详情
      const usersWithDetails = pendingUsers.map(user => {
        const notification = userNotifications.find(n => {
          try {
            const content = JSON.parse(n.content)
            return content.userId === user.id
          } catch {
            return false
          }
        })

        let details = {
          wechatId: '',
          reason: '暂无说明'
        }

        if (notification) {
          try {
            const content = JSON.parse(notification.content)
            details.wechatId = content.wechatId || ''
            details.reason = content.reason || '暂无说明'
          } catch {
            // 忽略解析错误
          }
        }

        return {
          ...user,
          ...details
        }
      })

      return reply.send({
        success: true,
        data: usersWithDetails
      })

    } catch (error) {
      fastify.log.error('Get pending users error:', error)
      return reply.status(500).send({
        success: false,
        error: '获取待审核用户失败'
      })
    }
  })

  // PATCH /api/hunter-auth/verify-user/:id - 审核用户
  fastify.patch('/verify-user/:id', {
    preHandler: authenticateAdmin
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const { id } = request.params as { id: string }
      const body = verifyUserSchema.parse(request.body)
      const adminUser = request.user

      // 检查用户是否存在
      const user = await prisma.user.findUnique({
        where: { id }
      })

      if (!user) {
        return reply.status(404).send({
          success: false,
          error: '用户不存在'
        })
      }

      if (user.status !== 'registered') {
        return reply.status(400).send({
          success: false,
          error: '用户状态不正确'
        })
      }

      // 更新用户状态
      const newStatus = body.action === 'approve' ? 'verified' : 'inactive'
      const updatedUser = await prisma.user.update({
        where: { id },
        data: { status: newStatus }
      })

      // 发送通知给用户
      await prisma.notification.create({
        data: {
          recipientId: user.id,
          type: 'system_announcement',
          title: body.action === 'approve' ? '账户审核通过' : '账户审核未通过',
          content: JSON.stringify({
            type: 'user_verification',
            action: body.action,
            reason: body.reason || '',
            verifiedAt: new Date().toISOString(),
            verifiedBy: adminUser.id
          })
        }
      })

      return reply.send({
        success: true,
        data: {
          id: updatedUser.id,
          status: updatedUser.status
        },
        message: body.action === 'approve' ? '用户已通过审核' : '用户审核已拒绝'
      })

    } catch (error) {
      fastify.log.error('Verify user error:', error)
      return reply.status(500).send({
        success: false,
        error: '审核失败'
      })
    }
  })

  // GET /api/hunter-auth/profile - 获取用户信息
  fastify.get('/profile', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const authHeader = request.headers.authorization
      if (!authHeader) {
        return reply.status(401).send({
          success: false,
          error: '未提供认证信息'
        })
      }

      const token = authHeader.replace('Bearer ', '')
      const decoded = verifyToken(token)
      
      if (!decoded) {
        return reply.status(401).send({
          success: false,
          error: '无效的认证信息'
        })
      }

      const user = await prisma.user.findUnique({
        where: { id: decoded.id },
        select: {
          id: true,
          username: true,
          phone: true,
          email: true,
          role: true,
          status: true,
          createdAt: true
        }
      })

      if (!user) {
        return reply.status(404).send({
          success: false,
          error: '用户不存在'
        })
      }

      return reply.send({
        success: true,
        data: user
      })

    } catch (error) {
      fastify.log.error('Get profile error:', error)
      return reply.status(500).send({
        success: false,
        error: '获取用户信息失败'
      })
    }
  })

  // GET /api/hunter-auth/stats - 获取用户统计信息（管理员用）
  fastify.get('/stats', {
    preHandler: authenticateAdmin
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const [
        totalUsers,
        registeredUsers,
        verifiedUsers,
        inactiveUsers,
        todayRegistrations
      ] = await Promise.all([
        prisma.user.count({
          where: { email: { endsWith: '@hunter.temp' } } // 只统计猎头平台用户
        }),
        prisma.user.count({
          where: { 
            status: 'registered',
            email: { endsWith: '@hunter.temp' }
          }
        }),
        prisma.user.count({
          where: { 
            status: 'verified',
            email: { endsWith: '@hunter.temp' }
          }
        }),
        prisma.user.count({
          where: { 
            status: 'inactive',
            email: { endsWith: '@hunter.temp' }
          }
        }),
        prisma.user.count({
          where: {
            email: { endsWith: '@hunter.temp' },
            createdAt: {
              gte: new Date(new Date().setHours(0, 0, 0, 0))
            }
          }
        })
      ])

      return reply.send({
        success: true,
        data: {
          total: totalUsers,
          registered: registeredUsers,
          verified: verifiedUsers,
          inactive: inactiveUsers,
          today: todayRegistrations
        }
      })

    } catch (error) {
      fastify.log.error('Get user stats error:', error)
      return reply.status(500).send({
        success: false,
        error: '获取统计信息失败'
      })
    }
  })
}