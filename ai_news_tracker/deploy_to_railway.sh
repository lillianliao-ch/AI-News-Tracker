#!/bin/bash

# ============================================================
# Railway自动部署脚本
# 用途：一键部署AI News Tracker到Railway平台
# ============================================================

set -e  # 遇到错误立即退出

echo "🚀 AI News Tracker - Railway部署脚本"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查必要的命令
check_requirements() {
    echo -e "${YELLOW}检查环境...${NC}"

    # 检查git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Git已安装${NC}"

    # 检查npm
    if ! command -v npm &> /dev/null; then
        echo -e "${YELLOW}⚠️  NPM未安装，正在安装...${NC}"
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    echo -e "${GREEN}✅ NPM已安装${NC}"
}

# 安装Railway CLI
install_railway_cli() {
    echo -e "${YELLOW}检查Railway CLI...${NC}"

    if command -v railway &> /dev/null; then
        echo -e "${GREEN}✅ Railway CLI已安装${NC}"
        railway --version
    else
        echo -e "${YELLOW}正在安装Railway CLI...${NC}"
        npm install -g @railway/cli
        echo -e "${GREEN}✅ Railway CLI安装成功${NC}"
    fi
}

# 登录Railway
login_railway() {
    echo -e "${YELLOW}登录Railway...${NC}"
    railway login
    echo -e "${GREEN}✅ 登录成功${NC}"
}

# 初始化项目
init_project() {
    echo -e "${YELLOW}初始化Railway项目...${NC}"

    if [ -f ".railway/project.json" ]; then
        echo -e "${YELLOW}项目已存在，跳过初始化${NC}"
    else
        railway init
        echo -e "${GREEN}✅ 项目初始化成功${NC}"
    fi
}

# 配置环境变量
setup_variables() {
    echo -e "${YELLOW}配置环境变量...${NC}"

    # OpenAI API配置
    railway variables set OPENAI_API_KEY=sk-4e2bb9108e1541f9b7dd88855922c7a3
    railway variables set OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

    # 模型配置
    railway variables set CLASSIFY_MODEL=qwen-max
    railway variables set SUMMARY_MODEL=qwen-plus
    railway variables set GENERATE_MODEL=qwen-max

    # 其他配置
    railway variables set LOG_LEVEL=INFO
    railway variables set DEBUG=false

    echo -e "${GREEN}✅ 环境变量配置成功${NC}"
}

# 添加PostgreSQL数据库
add_database() {
    echo -e "${YELLOW}添加PostgreSQL数据库...${NC}"

    # 检查是否已有数据库
    if railway services list | grep -q "PostgreSQL"; then
        echo -e "${YELLOW}数据库已存在，跳过添加${NC}"
    else
        railway add --service postgresql
        echo -e "${GREEN}✅ 数据库添加成功${NC}"
    fi
}

# 配置服务
configure_service() {
    echo -e "${YELLOW}配置服务...${NC}"

    # 设置构建目录
    railway build set backend

    # 设置启动命令
    railway up set "cd backend && uvicorn main:app --host 0.0.0.0 --port \${PORT}"

    echo -e "${GREEN}✅ 服务配置成功${NC}"
}

# 部署到Railway
deploy() {
    echo -e "${YELLOW}开始部署...${NC}"
    echo -e "${YELLOW}这可能需要几分钟时间...${NC}"

    railway up --detach

    echo -e "${GREEN}✅ 部署成功${NC}"
}

# 获取项目信息
get_info() {
    echo ""
    echo "======================================"
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo "======================================"
    echo ""

    # 获取项目URL
    DOMAIN=$(railway domain)
    echo -e "${GREEN}📱 项目URL:${NC} https://$DOMAIN"

    # 获取服务列表
    echo ""
    echo -e "${GREEN}📊 服务列表:${NC}"
    railway services list

    # 获取环境变量
    echo ""
    echo -e "${GREEN}🔧 环境变量:${NC}"
    railway variables list

    echo ""
    echo -e "${YELLOW}💡 提示:${NC}"
    echo "1. 访问 https://railway.app 查看详细日志"
    echo "2. 使用 'railway logs' 查看实时日志"
    echo "3. 使用 'railway open' 在浏览器中打开项目"
    echo ""
}

# 主函数
main() {
    # 检查是否在正确的目录
    if [ ! -f "railway.json" ]; then
        echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
        exit 1
    fi

    # 执行部署步骤
    check_requirements
    install_railway_cli
    login_railway
    init_project
    setup_variables
    add_database
    configure_service
    deploy
    get_info
}

# 运行主函数
main
