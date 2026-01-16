# ============================================================
# AI News Tracker Frontend - Dockerfile
# Astro SSR with Node.js
# ============================================================

FROM node:20-alpine

WORKDIR /app

# 复制 package files
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production=false

# 复制源代码
COPY . .

# 构建 Astro 应用
RUN npm run build

# 暴露端口
EXPOSE 4321

# 设置环境变量
ENV HOST=0.0.0.0
ENV PORT=4321

# 启动命令
CMD ["node", "./dist/server/entry.mjs"]
