"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.hunterPostsRoutes = hunterPostsRoutes;
const zod_1 = require("zod");
const client_1 = require("@prisma/client");
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const prisma = new client_1.PrismaClient();
const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-key';
// Schema定义
const createHunterPostSchema = zod_1.z.object({
    type: zod_1.z.enum(['job_seeking', 'talent_recommendation']),
    title: zod_1.z.string().min(1).max(100),
    content: zod_1.z.string().min(1).max(1000)
});
const getHunterPostsSchema = zod_1.z.object({
    type: zod_1.z.enum(['all', 'job_seeking', 'talent_recommendation']).default('all'),
    page: zod_1.z.coerce.number().min(1).default(1),
    limit: zod_1.z.coerce.number().min(1).max(50).default(10),
    status: zod_1.z.enum(['pending', 'approved', 'rejected']).optional()
});
const approvePostSchema = zod_1.z.object({
    action: zod_1.z.enum(['approve', 'reject']),
    reason: zod_1.z.string().optional()
});
// 权限检查函数
function getUserPermissions(userStatus) {
    switch (userStatus) {
        case 'guest':
            return { viewDays: 1, maxPosts: 3, canPublish: false };
        case 'registered':
            return { viewDays: 3, maxPosts: 10, canPublish: false };
        case 'verified':
            return { viewDays: 90, maxPosts: -1, canPublish: true };
        default:
            return { viewDays: 0, maxPosts: 0, canPublish: false };
    }
}
// 认证中间件
async function authenticateUser(request, reply) {
    try {
        const authHeader = request.headers.authorization;
        if (!authHeader) {
            // 游客用户
            request.user = { id: null, status: 'guest', role: null };
            return;
        }
        const token = authHeader.replace('Bearer ', '');
        try {
            const decoded = jsonwebtoken_1.default.verify(token, JWT_SECRET);
            const user = await prisma.user.findUnique({
                where: { id: decoded.id }
            });
            if (user) {
                request.user = { id: user.id, status: user.status, role: user.role };
            }
            else {
                request.user = { id: null, status: 'guest', role: null };
            }
        }
        catch (jwtError) {
            request.user = { id: null, status: 'guest', role: null };
        }
    }
    catch (error) {
        request.user = { id: null, status: 'guest', role: null };
    }
}
// 猎头信息分享路由
async function hunterPostsRoutes(fastify) {
    // GET /api/hunter-posts - 获取信息列表
    fastify.get('/', {
        preHandler: authenticateUser
    }, async (request, reply) => {
        try {
            const query = getHunterPostsSchema.parse(request.query);
            const { type, page, limit, status } = query;
            const user = request.user;
            const permissions = getUserPermissions(user.status);
            const offset = (page - 1) * limit;
            // 计算查看时间限制
            const viewCutoff = new Date();
            viewCutoff.setDate(viewCutoff.getDate() - permissions.viewDays);
            // 构建查询条件
            const where = {
                status: status || 'approved',
                createdAt: permissions.viewDays > 0 ? { gte: viewCutoff } : undefined
            };
            if (type !== 'all') {
                where.type = type;
            }
            // 查询数据
            const [posts, total] = await Promise.all([
                prisma.hunterPost.findMany({
                    where,
                    include: {
                        publisher: {
                            select: {
                                id: true,
                                username: true,
                                phone: true
                            }
                        }
                    },
                    orderBy: [
                        { urgency: 'desc' }, // 紧急的在前
                        { createdAt: 'desc' }
                    ],
                    skip: offset,
                    take: permissions.maxPosts > 0 ? Math.min(limit, permissions.maxPosts - offset) : limit
                }),
                prisma.hunterPost.count({ where })
            ]);
            // 格式化返回数据
            const formattedPosts = posts.map(post => ({
                id: post.id,
                type: post.type,
                title: post.title,
                content: post.content,
                publisherName: post.publisher.username,
                viewCount: post.viewCount || 0,
                createdAt: post.createdAt
            }));
            return reply.send({
                success: true,
                data: formattedPosts,
                pagination: {
                    page,
                    limit,
                    total,
                    totalPages: Math.ceil(total / limit),
                    hasMore: offset + formattedPosts.length < total
                },
                userPermissions: {
                    status: user.status,
                    canPublish: permissions.canPublish,
                    viewDays: permissions.viewDays,
                    remainingPosts: permissions.maxPosts > 0 ?
                        Math.max(0, permissions.maxPosts - offset - formattedPosts.length) : -1
                }
            });
        }
        catch (error) {
            fastify.log.error('Get hunter posts error:', error);
            return reply.status(500).send({
                success: false,
                error: '获取信息失败'
            });
        }
    });
    // POST /api/hunter-posts - 发布信息
    fastify.post('/', {
        preHandler: authenticateUser
    }, async (request, reply) => {
        try {
            const body = createHunterPostSchema.parse(request.body);
            const user = request.user;
            // 检查发布权限 - 允许已注册用户发布
            if (!user.id) {
                return reply.status(403).send({
                    success: false,
                    error: '请先登录后发布信息'
                });
            }
            // 创建信息
            const post = await prisma.hunterPost.create({
                data: {
                    type: body.type,
                    title: body.title,
                    content: body.content,
                    publisherId: user.id,
                    status: 'approved', // 直接通过审核
                    urgency: 'normal', // 设置默认紧急程度
                    // 设置过期时间（30天后）
                    expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
                },
                include: {
                    publisher: {
                        select: {
                            username: true,
                            phone: true
                        }
                    }
                }
            });
            return reply.send({
                success: true,
                data: {
                    id: post.id,
                    type: post.type,
                    title: post.title,
                    content: post.content,
                    status: post.status,
                    publisherName: post.publisher.username,
                    viewCount: post.viewCount || 0,
                    createdAt: post.createdAt
                },
                message: '信息发布成功，已在首页显示'
            });
        }
        catch (error) {
            fastify.log.error('Create hunter post error:', error);
            return reply.status(500).send({
                success: false,
                error: `发布失败: ${error instanceof Error ? error.message : JSON.stringify(error)}`
            });
        }
    });
    // GET /api/hunter-posts/pending - 获取待审核信息（管理员用）
    fastify.get('/pending', {
        preHandler: authenticateUser
    }, async (request, reply) => {
        try {
            const user = request.user;
            // 检查管理员权限
            if (!user.id || (user.role !== 'platform_admin' && user.role !== 'company_admin')) {
                return reply.status(403).send({
                    success: false,
                    error: '权限不足'
                });
            }
            const pendingPosts = await prisma.hunterPost.findMany({
                where: { status: 'pending' },
                include: {
                    publisher: {
                        select: {
                            id: true,
                            username: true,
                            phone: true,
                            status: true
                        }
                    }
                },
                orderBy: [
                    { urgency: 'desc' },
                    { createdAt: 'asc' }
                ]
            });
            const formattedPosts = pendingPosts.map(post => ({
                id: post.id,
                type: post.type,
                title: post.title,
                content: post.content,
                company: post.company,
                location: post.location,
                urgency: post.urgency,
                publisherName: post.publisher.username,
                publisherPhone: post.publisher.phone,
                publisherStatus: post.publisher.status,
                createdAt: post.createdAt
            }));
            return reply.send({
                success: true,
                data: formattedPosts
            });
        }
        catch (error) {
            fastify.log.error('Get pending posts error:', error);
            return reply.status(500).send({
                success: false,
                error: '获取待审核信息失败'
            });
        }
    });
    // PATCH /api/hunter-posts/:id/approve - 审核信息
    fastify.patch('/:id/approve', {
        preHandler: authenticateUser
    }, async (request, reply) => {
        try {
            const { id } = request.params;
            const body = approvePostSchema.parse(request.body);
            const user = request.user;
            // 检查管理员权限
            if (!user.id || (user.role !== 'platform_admin' && user.role !== 'company_admin')) {
                return reply.status(403).send({
                    success: false,
                    error: '权限不足'
                });
            }
            // 检查信息是否存在
            const post = await prisma.hunterPost.findUnique({
                where: { id },
                include: {
                    publisher: { select: { username: true } }
                }
            });
            if (!post) {
                return reply.status(404).send({
                    success: false,
                    error: '信息不存在'
                });
            }
            if (post.status !== 'pending') {
                return reply.status(400).send({
                    success: false,
                    error: '信息已经审核过了'
                });
            }
            // 更新状态
            const updatedPost = await prisma.hunterPost.update({
                where: { id },
                data: {
                    status: body.action === 'approve' ? 'approved' : 'rejected',
                    approvedBy: user.id,
                    approvedAt: new Date(),
                    rejectionReason: body.action === 'reject' ? body.reason : null
                }
            });
            return reply.send({
                success: true,
                data: {
                    id: updatedPost.id,
                    status: updatedPost.status,
                    approvedAt: updatedPost.approvedAt
                },
                message: body.action === 'approve' ? '信息已通过审核' : '信息已拒绝'
            });
        }
        catch (error) {
            fastify.log.error('Approve post error:', error);
            return reply.status(500).send({
                success: false,
                error: '审核失败'
            });
        }
    });
    // PATCH /api/hunter-posts/:id/view - 增加浏览量
    fastify.patch('/:id/view', async (request, reply) => {
        try {
            const { id } = request.params;
            await prisma.hunterPost.update({
                where: { id },
                data: {
                    viewCount: {
                        increment: 1
                    }
                }
            });
            return reply.send({
                success: true,
                message: '浏览量已更新'
            });
        }
        catch (error) {
            // 浏览量更新失败不影响主要功能
            return reply.send({
                success: true
            });
        }
    });
    // GET /api/hunter-posts/my - 获取当前用户的发布信息
    fastify.get('/my', {
        preHandler: authenticateUser
    }, async (request, reply) => {
        try {
            const user = request.user;
            // 检查用户是否登录
            if (!user.id) {
                return reply.status(401).send({
                    success: false,
                    error: '请先登录'
                });
            }
            // 查询当前用户发布的信息
            const myPosts = await prisma.hunterPost.findMany({
                where: {
                    publisherId: user.id
                },
                include: {
                    publisher: {
                        select: {
                            id: true,
                            username: true,
                            phone: true
                        }
                    }
                },
                orderBy: [
                    { createdAt: 'desc' }
                ]
            });
            // 格式化返回数据
            const formattedPosts = myPosts.map(post => ({
                id: post.id,
                type: post.type,
                title: post.title,
                content: post.content,
                viewCount: post.viewCount || 0,
                createdAt: post.createdAt
            }));
            return reply.send({
                success: true,
                data: formattedPosts
            });
        }
        catch (error) {
            fastify.log.error('Get my posts error:', error);
            return reply.status(500).send({
                success: false,
                error: '获取我的发布失败'
            });
        }
    });
    // GET /api/hunter-posts/stats - 获取统计信息
    fastify.get('/stats', {
        preHandler: authenticateUser
    }, async (request, reply) => {
        try {
            const user = request.user;
            // 检查管理员权限
            if (!user.id || (user.role !== 'platform_admin' && user.role !== 'company_admin')) {
                return reply.status(403).send({
                    success: false,
                    error: '权限不足'
                });
            }
            const [totalPosts, pendingPosts, approvedPosts, rejectedPosts, urgentPosts, todayPosts] = await Promise.all([
                prisma.hunterPost.count(),
                prisma.hunterPost.count({ where: { status: 'pending' } }),
                prisma.hunterPost.count({ where: { status: 'approved' } }),
                prisma.hunterPost.count({ where: { status: 'rejected' } }),
                prisma.hunterPost.count({ where: { urgency: 'urgent', status: 'approved' } }),
                prisma.hunterPost.count({
                    where: {
                        createdAt: {
                            gte: new Date(new Date().setHours(0, 0, 0, 0))
                        }
                    }
                })
            ]);
            return reply.send({
                success: true,
                data: {
                    total: totalPosts,
                    pending: pendingPosts,
                    approved: approvedPosts,
                    rejected: rejectedPosts,
                    urgent: urgentPosts,
                    today: todayPosts
                }
            });
        }
        catch (error) {
            fastify.log.error('Get stats error:', error);
            return reply.status(500).send({
                success: false,
                error: '获取统计信息失败'
            });
        }
    });
}
//# sourceMappingURL=hunter-posts.js.map