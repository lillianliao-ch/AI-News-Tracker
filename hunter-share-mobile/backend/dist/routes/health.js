"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.healthCheckRoutes = healthCheckRoutes;
async function healthCheckRoutes(fastify) {
    // 健康检查端点
    fastify.get('/health', async () => {
        return {
            status: 'ok',
            timestamp: new Date().toISOString(),
            service: 'hunter-share-mobile-backend'
        };
    });
    // 就绪检查端点
    fastify.get('/ready', async () => {
        return {
            status: 'ready',
            timestamp: new Date().toISOString()
        };
    });
}
//# sourceMappingURL=health.js.map