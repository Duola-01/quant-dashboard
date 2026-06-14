@echo off
cd /d "%~dp0"
echo ==============================
echo   量化策略监控台
echo   前端: http://localhost:8501
echo   关闭此窗口即可停止服务
echo ==============================
start http://localhost:8501
python -m streamlit run app.py --server.port 8501 --server.headless true
pause
