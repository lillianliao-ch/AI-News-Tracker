# 🚀 猎头联盟网站部署指南

## 📋 部署选项

### 1. 局域网部署（推荐用于内部使用）

#### 快速部署
```bash
./deploy.sh
```
选择选项3（局域网模式）

#### 手动部署
```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动服务器（允许局域网访问）
python3 app.py
```

#### 访问地址
- **本机访问**: http://localhost:8080
- **局域网访问**: http://[您的IP地址]:8080

### 2. 生产环境部署

#### 使用Gunicorn（推荐）
```bash
# 安装Gunicorn
pip3 install gunicorn

# 启动生产服务器
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

#### 使用Nginx反向代理
```bash
# 安装Nginx
sudo apt-get install nginx  # Ubuntu/Debian
# 或
brew install nginx  # macOS

# 配置Nginx
sudo nano /etc/nginx/sites-available/headhunter
```

Nginx配置示例：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Docker部署

#### 创建Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
```

#### 构建和运行
```bash
# 构建镜像
docker build -t headhunter-alliance .

# 运行容器
docker run -d -p 8080:8080 --name headhunter headhunter-alliance
```

## 🌐 网络配置

### 获取本机IP地址
```bash
# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1

# Linux
hostname -I

# Windows
ipconfig
```

### 防火墙配置
```bash
# Ubuntu/Debian
sudo ufw allow 8080

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
```

## 🔧 环境变量配置

### 创建.env文件
```bash
# 创建环境变量文件
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///headhunter_alliance.db
EOF
```

### 生产环境变量
```bash
export FLASK_ENV=production
export SECRET_KEY=your-super-secret-key-here
export DATABASE_URL=sqlite:///headhunter_alliance.db
```

## 📊 数据库配置

### SQLite（默认，适合小型部署）
```python
# 默认配置，无需额外设置
SQLALCHEMY_DATABASE_URI = 'sqlite:///headhunter_alliance.db'
```

### MySQL（推荐用于生产环境）
```bash
# 安装MySQL
sudo apt-get install mysql-server

# 创建数据库
mysql -u root -p
CREATE DATABASE headhunter_alliance;
CREATE USER 'headhunter'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON headhunter_alliance.* TO 'headhunter'@'localhost';
FLUSH PRIVILEGES;
```

更新配置：
```python
SQLALCHEMY_DATABASE_URI = 'mysql://headhunter:your_password@localhost/headhunter_alliance'
```

### PostgreSQL（企业级选择）
```bash
# 安装PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres psql
CREATE DATABASE headhunter_alliance;
CREATE USER headhunter WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE headhunter_alliance TO headhunter;
```

更新配置：
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://headhunter:your_password@localhost/headhunter_alliance'
```

## 🔒 安全配置

### 1. 更新SECRET_KEY
```python
import secrets
print(secrets.token_hex(32))
```

### 2. 启用HTTPS
```bash
# 使用Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 配置CORS（如果需要）
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'https://your-domain.com'])
```

## 📈 性能优化

### 1. 使用Gunicorn多进程
```bash
gunicorn -w 4 -b 0.0.0.0:8080 --timeout 120 app:app
```

### 2. 配置Redis缓存
```bash
# 安装Redis
sudo apt-get install redis-server

# 安装Python Redis
pip3 install redis
```

### 3. 静态文件优化
```bash
# 压缩静态文件
pip3 install flask-compress
```

## 🐳 Docker Compose部署

创建`docker-compose.yml`：
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped
```

运行：
```bash
docker-compose up -d
```

## 📱 移动端访问

### 1. 响应式设计
网站已经支持移动端访问，无需额外配置。

### 2. PWA支持（可选）
```bash
# 安装PWA支持
pip3 install flask-pwa
```

## 🔍 监控和日志

### 1. 日志配置
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/headhunter.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('猎头联盟网站启动')
```

### 2. 健康检查
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow()}
```

## 🚀 快速部署命令

### 局域网部署（一键启动）
```bash
./deploy.sh
```

### 生产环境部署
```bash
# 1. 安装依赖
pip3 install -r requirements.txt gunicorn

# 2. 设置环境变量
export FLASK_ENV=production
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 3. 启动服务器
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## 📞 故障排除

### 常见问题
1. **端口被占用**: 修改`config.py`中的PORT配置
2. **数据库连接失败**: 检查数据库配置和权限
3. **静态文件404**: 确保static目录存在
4. **权限问题**: 检查文件权限和防火墙设置

### 日志查看
```bash
# 查看应用日志
tail -f logs/headhunter.log

# 查看系统日志
sudo journalctl -u headhunter -f
```

---

**🎉 部署完成！您的猎头联盟网站现在可以被其他人访问了！** 