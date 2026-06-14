@echo off
cd /d "%~dp0"
echo ==============================
echo   量化策略监控台 - 启动中...
echo ==============================
python -m streamlit run app.py --server.port 8501 --server.headless true
pause
