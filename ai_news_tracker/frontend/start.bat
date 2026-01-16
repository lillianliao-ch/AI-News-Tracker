@echo off
REM AI News Tracker - Windows 前端启动脚本

echo ==================================================
echo 🚀 AI News Tracker - 前端启动脚本
echo ==================================================
echo.

REM 进入frontend目录
cd /d "%~dp0"
set FRONTEND_DIR=%cd%
echo 📂 工作目录: %FRONTEND_DIR%
echo.

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Node.js
    echo 请先安装 Node.js 18+
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✅ Node.js 版本: %NODE_VERSION%
echo.

REM 检查npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 npm
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo ✅ npm 版本: %NPM_VERSION%
echo.

REM 检查依赖
if not exist "node_modules" (
    echo 📦 未找到 node_modules，正在安装依赖...
    npm install
    echo ✅ 依赖安装完成
    echo.
)

REM 检查端口占用
set PORT=4321
netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  端口 %PORT% 已被占用
    echo 正在尝试关闭现有进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 1 >nul
    echo ✅ 端口已释放
    echo.
)

REM 启动前端
echo ==================================================
echo 🚀 启动 Astro 开发服务器...
echo ==================================================
echo.
echo 📍 前端地址: http://localhost:%PORT%
echo.
echo 按 Ctrl+C 停止服务器
echo ==================================================
echo.

REM 启动Astro
npm run dev
