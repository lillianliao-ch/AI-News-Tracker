# 部署指南

本文档提供完整的部署步骤，包括开发环境、生产环境和Docker部署。

---

## 📋 前置要求

### 必需软件

| 软件 | 最低版本 | 推荐版本 | 用途 |
|------|---------|---------|------|
| Node.js | 18.x | 20.x | 运行环境 |
| npm | 9.x | 10.x | 包管理器 |
| PostgreSQL | 14.x | 14.x | 数据库 |
| Docker | 20.x | 24.x | 容器化（可选） |
| Git | 2.x | 2.x | 版本控制 |

### 系统要求

**开发环境**:
- CPU: 2核心+
- 内存: 4GB+
- 磁盘: 10GB+

**生产环境**:
- CPU: 4核心+
- 内存: 8GB+
- 磁盘: 50GB+
- 带宽: 10Mbps+

---

## 🚀 快速开始（开发环境）

### 1. 克隆项目

```bash
# 克隆仓库
git clone <repository-url>
cd hunter-share-mobile
```

### 2. 启动数据库

#### 方式1: 使用Docker（推荐）

```bash
# 启动PostgreSQL容器
docker run -d \
  --name hunter-share-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=hunter_share_mobile \
  -p 5433:5432 \
  postgres:14-alpine

# 验证容器运行
docker ps | grep hunter-share-postgres
```

#### 方式2: 本地PostgreSQL

```bash
# macOS (使用Homebrew)
brew install postgresql@14
brew services start postgresql@14

# 创建数据库
createdb hunter_share_mobile

# Ubuntu/Debian
sudo apt-get install postgresql-14
sudo systemctl start postgresql
sudo -u postgres createdb hunter_share_mobile
```

### 3. 配置环境变量

#### 后端配置

```bash
cd backend
cp .env.example .env  # 如果有示例文件

# 编辑 .env
cat > .env << EOF
DATABASE_URL="postgresql://postgres:postgres@localhost:5433/hunter_share_mobile"
JWT_SECRET="hunter-share-jwt-secret-dev"
PORT=5000
NODE_ENV=development
EOF
```

#### 前端配置

```bash
cd ../frontend
cp .env.local.example .env.local  # 如果有示例文件

# 编辑 .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:5000/api
EOF
```

### 4. 安装依赖

```bash
# 后端
cd backend
npm install

# 前端
cd ../frontend
npm install
```

### 5. 初始化数据库

```bash
cd backend

# 应用数据库迁移
npm run db:migrate:deploy

# 或使用开发模式的迁移（会提示确认）
npm run db:migrate

# 可选：填充种子数据
npm run db:seed
```

### 6. 启动服务

#### 终端1: 启动后端

```bash
cd backend
npm run dev

# 输出应显示:
# 🚀 Backend server running at http://localhost:5000
# ✅ Database connected
```

#### 终端2: 启动前端

```bash
cd frontend
PORT=4000 npm run dev

# 输出应显示:
# ✓ Ready on http://localhost:4000
```

### 7. 验证部署

**浏览器访问**:
- 前端: http://localhost:4000
- 后端健康检查: http://localhost:5000/health

**API测试**:
```bash
# 测试API连通性
curl http://localhost:5000/api/hunter-posts

# 应该返回:
# {"success":true,"data":[],...}
```

---

## 🐳 Docker 部署（推荐）

### 1. 准备 Docker 环境

```bash
# 确保Docker和Docker Compose已安装
docker --version
docker-compose --version

# 启动Docker服务（如未启动）
# macOS: 打开 Docker Desktop
# Linux: sudo systemctl start docker
```

### 2. 配置环境变量

```bash
# 创建 .env 文件（根目录）
cat > .env << EOF
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=hunter_share_mobile

# Backend
DATABASE_URL=postgresql://postgres:your_secure_password_here@postgres:5432/hunter_share_mobile
JWT_SECRET=your_jwt_secret_here_change_in_production
PORT=5000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:5000/api
EOF
```

⚠️ **安全提示**: 生产环境请更改默认密码和密钥！

### 3. 构建镜像

```bash
# 构建所有服务
docker-compose build

# 或单独构建
docker-compose build backend
docker-compose build frontend
```

### 4. 启动服务

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. 初始化数据库

```bash
# 应用数据库迁移
docker-compose exec backend npm run db:migrate:deploy

# 可选：填充种子数据
docker-compose exec backend npm run db:seed
```

### 6. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 应该看到所有服务都是 "Up" 状态
# NAME                    STATUS
# hunter-share-frontend   Up
# hunter-share-backend    Up
# hunter-share-postgres   Up

# 测试前端
curl http://localhost:4000

# 测试后端
curl http://localhost:5000/api/hunter-posts
```

### 7. 常用 Docker 命令

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（⚠️ 会删除数据库数据）
docker-compose down -v

# 重启服务
docker-compose restart

# 查看资源使用
docker stats

# 进入容器内部
docker-compose exec backend sh
docker-compose exec frontend sh
docker-compose exec postgres psql -U postgres -d hunter_share_mobile

# 查看容器日志
docker-compose logs --tail=100 backend
```

---

## 🌐 生产环境部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装必要软件
sudo apt-get install -y \
  git \
  curl \
  nginx \
  certbot \
  python3-certbot-nginx

# 安装Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 克隆项目

```bash
# 创建项目目录
sudo mkdir -p /var/www/hunter-share-mobile
sudo chown $USER:$USER /var/www/hunter-share-mobile

# 克隆代码
cd /var/www/hunter-share-mobile
git clone <repository-url> .
```

### 3. 配置环境变量（生产）

```bash
# 创建生产环境变量文件
cat > .env.production << EOF
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=hunter_share_mobile

# Backend
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/hunter_share_mobile
JWT_SECRET=$(openssl rand -base64 64)
PORT=5000
NODE_ENV=production

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api
EOF

# 备份环境变量
cp .env.production .env.production.backup
chmod 600 .env.production
```

### 4. 构建生产镜像

```bash
# 使用生产配置构建
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# 或修改 Dockerfile 添加生产优化
```

### 5. 启动生产服务

```bash
# 启动服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 初始化数据库
docker-compose exec backend npm run db:migrate:deploy
```

### 6. 配置 Nginx 反向代理

```bash
# 创建Nginx配置
sudo nano /etc/nginx/sites-available/hunter-share-mobile

# 配置内容：
```

```nginx
# 前端服务器配置
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL证书（由Certbot自动配置）
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/hunter-share-access.log;
    error_log /var/log/nginx/hunter-share-error.log;

    # 前端代理
    location / {
        proxy_pass http://localhost:4000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location /_next/static/ {
        proxy_pass http://localhost:4000;
        proxy_cache_valid 200 60m;
        proxy_cache_bypass $http_cache_control;
        add_header Cache-Control "public, max-age=3600, immutable";
    }
}

# API服务器配置
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS配置（如需要）
        add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/hunter-share-mobile /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 7. 配置 SSL 证书

```bash
# 使用Certbot获取免费SSL证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo certbot --nginx -d api.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### 8. 配置防火墙

```bash
# UFW配置
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 检查状态
sudo ufw status
```

### 9. 配置进程管理（PM2替代方案）

如果不使用Docker：

```bash
# 安装PM2
sudo npm install -g pm2

# 启动后端
cd backend
pm2 start npm --name "hunter-share-backend" -- run start

# 启动前端
cd frontend
pm2 start npm --name "hunter-share-frontend" -- run start

# 保存配置
pm2 save

# 开机自启
pm2 startup
```

---

## 📊 监控与日志

### 1. 查看日志

```bash
# Docker日志
docker-compose logs -f --tail=100

# Nginx日志
sudo tail -f /var/log/nginx/hunter-share-access.log
sudo tail -f /var/log/nginx/hunter-share-error.log

# 系统日志
journalctl -u nginx -f
```

### 2. 健康检查

```bash
# 创建健康检查脚本
cat > /usr/local/bin/hunter-share-health.sh << 'EOF'
#!/bin/bash

# 检查前端
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000)
echo "Frontend: $FRONTEND"

# 检查后端
BACKEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
echo "Backend: $BACKEND"

# 检查数据库
docker-compose exec -T postgres pg_isready -U postgres
echo "Database: $?"

if [ "$FRONTEND" != "200" ] || [ "$BACKEND" != "200" ]; then
    echo "Services unhealthy, restarting..."
    docker-compose restart
fi
EOF

chmod +x /usr/local/bin/hunter-share-health.sh

# 添加到crontab（每5分钟检查一次）
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/hunter-share-health.sh >> /var/log/hunter-share-health.log 2>&1") | crontab -
```

### 3. 性能监控

```bash
# 安装监控工具
sudo npm install -g pm2
pm2 install pm2-logrotate

# 监控Docker容器
docker stats

# 系统资源监控
htop
```

---

## 🔄 更新部署

### 1. 代码更新

```bash
# 拉取最新代码
cd /var/www/hunter-share-mobile
git pull origin main

# 查看更新内容
git log --oneline -10
```

### 2. 更新依赖

```bash
# 后端
cd backend
npm install

# 前端
cd ../frontend
npm install
```

### 3. 数据库迁移

```bash
cd backend

# 检查待应用的迁移
npm run db:migrate:status

# 应用新迁移
npm run db:migrate:deploy

# 或在Docker中
docker-compose exec backend npm run db:migrate:deploy
```

### 4. 重启服务

```bash
# Docker方式
docker-compose down
docker-compose up -d --build

# 或滚动更新（零停机）
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend

# PM2方式
pm2 reload all
```

### 5. 验证更新

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f --tail=50

# 测试功能
curl http://localhost:5000/api/hunter-posts
```

---

## 📦 备份与恢复

### 1. 数据库备份

```bash
# 创建备份脚本
cat > /usr/local/bin/backup-hunter-share.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/hunter-share"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose exec -T postgres pg_dump -U postgres hunter_share_mobile > $BACKUP_FILE

# 压缩
gzip $BACKUP_FILE

# 删除30天前的备份
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
EOF

chmod +x /usr/local/bin/backup-hunter-share.sh

# 添加到crontab（每天凌晨2点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-hunter-share.sh >> /var/log/hunter-share-backup.log 2>&1") | crontab -
```

### 2. 数据库恢复

```bash
# 恢复最新备份
LATEST_BACKUP=$(ls -t /var/backups/hunter-share/*.sql.gz | head -1)
gunzip -c $LATEST_BACKUP | docker-compose exec -T postgres psql -U postgres -d hunter_share_mobile

# 恢复指定备份
gunzip -c /var/backups/hunter-share/backup_20241107.sql.gz | \
  docker-compose exec -T postgres psql -U postgres -d hunter_share_mobile
```

---

## 🔧 故障排除

### 服务无法启动

```bash
# 检查端口占用
lsof -ti :4000 | xargs kill -9
lsof -ti :5000 | xargs kill -9
lsof -ti :5433 | xargs kill -9

# 检查Docker资源
docker system df
docker system prune -a  # 清理未使用的镜像

# 查看详细错误
docker-compose logs backend
docker-compose logs frontend
```

### 数据库连接失败

```bash
# 检查数据库状态
docker-compose exec postgres pg_isready -U postgres

# 重启数据库
docker-compose restart postgres

# 检查连接字符串
docker-compose exec backend env | grep DATABASE_URL
```

### 前端无法访问API

```bash
# 检查网络配置
docker-compose exec frontend cat /etc/hosts

# 检查API代理配置
docker-compose exec frontend cat next.config.js

# 测试网络连通性
docker-compose exec frontend curl http://backend:5000/health
```

更多问题请参考 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## 🎯 性能优化

### 1. 数据库优化

```bash
# 分析慢查询
docker-compose exec postgres psql -U postgres -d hunter_share_mobile

# 在psql中执行
\timing on
EXPLAIN ANALYZE SELECT * FROM hunter_posts WHERE status = 'approved';
```

### 2. 缓存配置（未来）

```yaml
# docker-compose.yml 添加Redis
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

### 3. CDN配置

- 静态资源上传到OSS/S3
- 配置CDN加速
- 启用Gzip压缩

---

## 📝 检查清单

### 部署前

- [ ] 代码已测试通过
- [ ] 环境变量已配置
- [ ] 数据库备份已完成
- [ ] SSL证书已配置
- [ ] 防火墙规则已设置
- [ ] 监控脚本已部署

### 部署后

- [ ] 所有服务正常运行
- [ ] API可以正常访问
- [ ] 前端页面加载正常
- [ ] 数据库连接正常
- [ ] HTTPS证书有效
- [ ] 日志记录正常
- [ ] 备份脚本运行正常

---

**文档版本**: v1.0.0  
**最后更新**: 2024-11-07  
**维护者**: 开发团队

