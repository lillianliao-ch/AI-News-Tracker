FROM node:20-alpine AS builder

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建Next.js应用
RUN npm run build

# 生产环境镜像
FROM node:20-alpine

WORKDIR /app

# 复制必要文件
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "start"]

