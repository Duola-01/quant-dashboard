"""
量化策略监控台 — 桌面启动器
===========================
双击此脚本或运行 `python run_app.py`：
  1. 启动 Streamlit 前端服务器
  2. 自动打开默认浏览器到监控台页面
  3. 关闭此窗口即可停止服务

依赖：pip install streamlit pandas requests
"""

import subprocess
import webbrowser
import time
import sys
import os
import signal

# ---- 配置 ----
HOST = "localhost"
PORT = 8501
APP_FILE = os.path.join(os.path.dirname(__file__), "app.py")
URL = f"http://{HOST}:{PORT}"


def main():
    print("=" * 50)
    print("  量化策略监控台")
    print(f"  前端地址: {URL}")
    print("  关闭此窗口即可停止服务")
    print("=" * 50)

    # 启动 Streamlit
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", APP_FILE,
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.serverAddress", HOST,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 等 Streamlit 启动完成后打开浏览器
    print("\n正在启动 Streamlit 服务...")
    time.sleep(3)

    print(f"正在打开浏览器: {URL}")
    webbrowser.open(URL)

    print("\n服务运行中。按 Ctrl+C 停止。\n")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        proc.terminate()
        proc.wait()
        print("已停止。")


if __name__ == "__main__":
    main()
