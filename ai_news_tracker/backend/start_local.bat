@echo off
REM AI News Tracker - Windows 快速启动脚本

echo ==================================================
echo 🚀 AI News Tracker - 本地启动脚本
echo ==================================================
echo.

REM 进入backend目录
cd /d "%~dp0"
set BACKEND_DIR=%cd%
echo 📂 工作目录: %BACKEND_DIR%
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python
    echo 请先安装 Python 3.10+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python 版本: %PYTHON_VERSION%
echo.

REM 检查.env文件
if not exist ".env" (
    echo ⚠️  未找到 .env 文件
    echo 正在从 .env.example 创建 .env...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo ✅ 已创建 .env 文件
        echo.
        echo ⚠️  请编辑 .env 文件，设置你的 API Keys:
        echo    - OPENAI_API_KEY
        echo    - OPENAI_BASE_URL
        echo.
        pause
    ) else (
        echo ❌ 错误: 未找到 .env.example 文件
        pause
        exit /b 1
    )
)

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 未找到虚拟环境，正在创建...
    python -m venv venv
    echo ✅ 虚拟环境创建完成
    echo.
)

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate.bat
echo ✅ 虚拟环境已激活
echo.

REM 安装/更新依赖
echo 📥 检查依赖...
if not exist "venv\.installed" (
    echo 正在安装依赖（首次运行，可能需要几分钟）...
    python -m pip install --upgrade pip --quiet
    python -m pip install -r requirements.txt --quiet
    type nul > venv\.installed
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已安装
)
echo.

REM 运行数据库迁移（如果需要）
if exist "migrate_add_language.py" (
    echo 🗄️  检查数据库迁移...
    python migrate_add_language.py 2>nul || echo 数据库已是最新版本
    echo.
)

REM 启动应用
echo ==================================================
echo 🚀 启动 AI News Tracker...
echo ==================================================
echo.
echo 📍 API 地址: http://localhost:4321
echo 📍 API 文档: http://localhost:4321/docs
echo 📍 健康检查: http://localhost:4321/health
echo.
echo 按 Ctrl+C 停止服务器
echo ==================================================
echo.

REM 启动uvicorn
python -m uvicorn main:app --host 0.0.0.0 --port 4321 --reload
