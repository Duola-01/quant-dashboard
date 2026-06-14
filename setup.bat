@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =============================================
echo   量化策略监控台 — 安装程序
echo =============================================
echo.
echo 正在安装 Python 依赖...
pip install streamlit pandas requests -q
echo.

:: 检查 cloudflared
where cloudflared >nul 2>nul
if %errorlevel%==0 (
    echo cloudflared 已安装
) else (
    echo.
    echo =============================================
    echo   如需远程访问（在外面用手机看），请安装 cloudflared：
    echo   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    echo   下载后把 cloudflared.exe 放到此目录即可
    echo =============================================
)

echo.
echo 安装完成！
echo.
echo 双击「一键启动.bat」即可运行。
pause
