"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fastify_1 = __importDefault(require("fastify"));
const cors_1 = __importDefault(require("@fastify/cors"));
const client_1 = require("@prisma/client");
const hunter_auth_1 = require("./routes/hunter-auth");
const hunter_posts_1 = require("./routes/hunter-posts");
const prisma = new client_1.PrismaClient();
const fastify = (0, fastify_1.default)({
    logger: true
});
// CORS配置
const allowedOrigins = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:3002',
    process.env.CORS_ORIGIN || '',
].filter(Boolean);
fastify.register(cors_1.default, {
    origin: allowedOrigins,
    credentials: true
});
// 健康检查
fastify.get('/health', async (request, reply) => {
    return { status: 'ok', timestamp: new Date().toISOString() };
});
// 注册路由
fastify.register(hunter_auth_1.hunterAuthRoutes, { prefix: '/api/hunter-auth' });
fastify.register(hunter_posts_1.hunterPostsRoutes, { prefix: '/api/hunter-posts' });
// 启动服务器
const start = async () => {
    try {
        const port = parseInt(process.env.PORT || '4000', 10);
        const host = process.env.HOST || '0.0.0.0';
        await fastify.listen({ port, host });
        console.log(`🚀 Server running on http://${host}:${port}`);
        console.log(`📊 Health check: http://${host}:${port}/health`);
    }
    catch (err) {
        fastify.log.error(err);
        process.exit(1);
    }
};
// 优雅关闭
const gracefulShutdown = async () => {
    console.log('\n🛑 Shutting down gracefully...');
    try {
        await prisma.$disconnect();
        await fastify.close();
        console.log('✅ Server closed successfully');
        process.exit(0);
    }
    catch (err) {
        console.error('❌ Error during shutdown:', err);
        process.exit(1);
    }
};
process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);
start();
//# sourceMappingURL=index.js.map