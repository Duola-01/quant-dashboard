@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =============================================
echo   量化策略监控台
echo =============================================
echo.

:: 检查依赖
pip show streamlit >nul 2>nul || (
    echo [安装] pip install streamlit pandas requests...
    pip install -q streamlit pandas requests
)

echo [启动] Streamlit 服务...
start "量化监控台" python -m streamlit run app.py --server.port 8501 --server.headless true --server.enableStaticServing true

:: 等待 Streamlit 启动
timeout /t 4 /nobreak >nul

:: 打开浏览器
start http://localhost:8501

echo.
echo   本地访问: http://localhost:8501
echo   局域网: http://172.27.153.241:8501

:: 检查 cloudflared
where cloudflared >nul 2>nul || if exist "%~dp0cloudflared.exe" set PATH=%PATH%;%~dp0
where cloudflared >nul 2>nul && (
    echo.
    echo [隧道] 启动 cloudflared...
    start "量化监控台-隧道" cloudflared tunnel --url http://localhost:8501
    echo   等待公网地址出现（约 10 秒）...
    echo   注意看弹出的 cloudflared 窗口中的 trycloudflare.com 地址
)

echo.
echo =============================================
echo   关闭此窗口或按 Ctrl+C 停止所有服务
echo =============================================
pause >nul
