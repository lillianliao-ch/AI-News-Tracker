#!/bin/bash

echo "🛠️  Starting Personal AI Headhunter - Development Environment"
echo "=================================================="
echo "Branch: $(git branch --show-current)"
echo "Environment: Development"
echo "Database: data/headhunter_dev.db"
echo "Port: 8501"
echo "=================================================="

# 设置数据库路径
export DB_PATH="data/headhunter_dev.db"
export ENV=development

# 确保数据目录存在
mkdir -p data
mkdir -p uploads
mkdir -p uploads/jobs

# 启动简历解析后台Worker
echo ""
echo "🔄 启动后台Workers..."

# 先停止已有的worker进程
pkill -f "resume_worker.py" 2>/dev/null
pkill -f "job_import_worker.py" 2>/dev/null

# 启动简历解析Worker
nohup python3 -u resume_worker.py > resume_worker.log 2>&1 &
RESUME_WORKER_PID=$!
echo "   ✅ 简历解析Worker已启动 (PID: $RESUME_WORKER_PID)"
echo "   📄 日志文件: resume_worker.log"

# 启动职位导入Worker
nohup python3 -u job_import_worker.py > job_import_worker.log 2>&1 &
JOB_WORKER_PID=$!
echo "   ✅ 职位导入Worker已启动 (PID: $JOB_WORKER_PID)"
echo "   📄 日志文件: job_import_worker.log"

# 启动API服务器（供脉脉插件调用）
nohup python3 -u api_server.py > api_server.log 2>&1 &
API_SERVER_PID=$!
echo "   ✅ API服务器已启动 (PID: $API_SERVER_PID, 端口: 8502)"
echo "   📄 日志文件: api_server.log"
echo ""

# 定义清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    pkill -f "resume_worker.py" 2>/dev/null
    pkill -f "job_import_worker.py" 2>/dev/null
    pkill -f "api_server.py" 2>/dev/null
    echo "   ✅ 所有服务已停止"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

echo "=================================================="
echo "🚀 启动 Streamlit 应用..."
echo "=================================================="

# 启动 Streamlit 应用
streamlit run app.py --server.port 8501

