# 后台服务管理指南

## 📋 概述

这些脚本用于管理 AI Headhunter Assistant 的后台服务，让服务在后台持续运行，不影响你进行其他工作。

## 🚀 快速开始

### 1. 启动服务（后台运行）

```bash
cd /Users/lillianliao/notion_rag/ai-headhunter-assistant
./scripts/start_backend.sh
```

服务将在后台运行，输出日志到 `apps/backend/logs/backend.log`

### 2. 查看服务状态

```bash
./scripts/status_backend.sh
```

### 3. 查看实时日志

```bash
tail -f apps/backend/logs/backend.log
```

### 4. 停止服务

```bash
./scripts/stop_backend.sh
```

## 📁 文件说明

- `start_backend.sh` - 启动后台服务
- `stop_backend.sh` - 停止后台服务
- `status_backend.sh` - 查看服务状态

## 🔧 工作原理

1. **启动脚本**：
   - 检查服务是否已运行
   - 检查并创建 `.env` 文件（如果不存在）
   - 使用 `nohup` 在后台启动服务
   - 保存进程 ID (PID) 到 `apps/backend/backend.pid`
   - 日志输出到 `apps/backend/logs/backend.log`

2. **停止脚本**：
   - 读取 PID 文件
   - 优雅停止进程（SIGTERM）
   - 如果未响应，强制停止（SIGKILL）
   - 清理 PID 文件

3. **状态脚本**：
   - 检查进程是否运行
   - 检查 API 健康状态
   - 显示服务信息

## ⚙️ 配置

首次启动前，请确保：

1. **环境变量配置**：
   ```bash
   cd apps/backend
   cp env.example .env
   # 编辑 .env 文件，填入你的 API Keys
   ```

2. **Python 依赖**：
   ```bash
   cd apps/backend
   pip3 install -r requirements.txt
   ```

## 🌐 访问服务

服务启动后，可以通过以下地址访问：

- **API 地址**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 💡 使用场景

### 场景 1: 开发新项目时保持服务运行

```bash
# 1. 启动后台服务
./scripts/start_backend.sh

# 2. 开始新项目（服务继续在后台运行）
cd /path/to/new-project
# ... 开始你的新项目工作

# 3. 需要时查看服务状态
cd /Users/lillianliao/notion_rag/ai-headhunter-assistant
./scripts/status_backend.sh
```

### 场景 2: 重启服务

```bash
./scripts/stop_backend.sh
./scripts/start_backend.sh
```

### 场景 3: 查看日志排查问题

```bash
# 查看最后 50 行日志
tail -n 50 apps/backend/logs/backend.log

# 实时查看日志
tail -f apps/backend/logs/backend.log
```

## ⚠️ 注意事项

1. **端口占用**：确保 8000 端口未被其他程序占用
2. **环境变量**：首次启动前必须配置 `.env` 文件
3. **日志文件**：日志文件会持续增长，定期清理或配置日志轮转
4. **进程管理**：如果脚本无法停止服务，可以手动查找并终止：
   ```bash
   # 查找进程
   ps aux | grep uvicorn
   # 终止进程（替换 PID）
   kill <PID>
   ```

## 🔍 故障排查

### 问题 1: 启动失败

**检查**：
- Python 依赖是否安装完整
- `.env` 文件是否存在且配置正确
- 8000 端口是否被占用

**解决**：
```bash
# 检查端口占用
lsof -i :8000

# 查看详细错误日志
cat apps/backend/logs/backend.log
```

### 问题 2: 服务意外停止

**检查**：
```bash
./scripts/status_backend.sh
cat apps/backend/logs/backend.log
```

**解决**：
- 查看日志找出错误原因
- 修复问题后重新启动

### 问题 3: 无法停止服务

**解决**：
```bash
# 查找进程
ps aux | grep uvicorn

# 强制终止（替换 PID）
kill -9 <PID>

# 清理 PID 文件
rm apps/backend/backend.pid
```

## 📝 下一步

服务启动后，你可以：

1. ✅ 继续开发新项目（服务在后台运行）
2. ✅ 使用 Chrome 扩展连接服务
3. ✅ 通过 API 文档测试接口
4. ✅ 查看日志监控服务状态

---

**提示**：服务在后台运行不会占用你的终端，你可以随时开始新项目！

