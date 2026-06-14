"""
远程隧道 — 将本地监控台暴露到公网
===================================
支持多种隧道后端，在外面用手机也能访问。

使用方法：
    python tunnel.py              # 自动选择可用后端
    python tunnel.py --ngrok      # 强制用 ngrok（需先 pip install pyngrok）
    python tunnel.py --bore       # 强制用 bore（开源，无需注册）

依赖（按需安装）：
    pip install pyngrok           # ngrok 后端
    或下载 cloudflared.exe        # Cloudflare Tunnel（免费，稳定）
    或 pip install bore           # bore 开源隧道
"""

import subprocess
import sys
import time
import os

LOCAL_PORT = 8501  # Streamlit 端口


def try_cloudflared():
    """Cloudflare Tunnel — 免费、稳定、无需注册域名即可用 trycloudflare.com"""
    exe = "cloudflared.exe" if sys.platform == "win32" else "cloudflared"
    # 检查是否已安装
    if subprocess.run(["where", exe], capture_output=True, shell=True).returncode != 0:
        return None

    print("[cloudflared] 启动 Cloudflare Tunnel...")
    proc = subprocess.Popen(
        [exe, "tunnel", "--url", f"http://localhost:{LOCAL_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # 等待隧道 URL 出现
    deadline = time.time() + 30
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            continue
        print(f"  {line.strip()}")
        if "trycloudflare.com" in line:
            # 提取 URL
            import re
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if m:
                return m.group(0)
    proc.terminate()
    return None


def try_ngrok():
    """ngrok — 需 pip install pyngrok 并配置 authtoken"""
    try:
        from pyngrok import ngrok
    except ImportError:
        print("[ngrok] pyngrok 未安装。运行: pip install pyngrok")
        return None

    try:
        tunnel = ngrok.connect(LOCAL_PORT, "http")
        url = tunnel.public_url
        print(f"[ngrok] 隧道已建立: {url}")
        return url
    except Exception as e:
        print(f"[ngrok] 连接失败: {e}")
        print("[ngrok] 需要先注册免费账号并设置 authtoken:")
        print("  https://dashboard.ngrok.com/get-started/your-authtoken")
        print("  ngrok config add-authtoken <你的token>")
        return None


def try_bore():
    """bore — 开源隧道，pip install bore"""
    try:
        import bore
    except ImportError:
        print("[bore] 未安装。运行: pip install bore")
        return None

    # bore 用自己的方式启动
    print("[bore] 暂不支持命令行自动启动，请手动运行:")
    print(f"  bore local {LOCAL_PORT} --to bore.pub")
    return None


def main():
    backend = sys.argv[1] if len(sys.argv) > 1 else "auto"

    print("=" * 50)
    print("  量化监控台 — 远程隧道")
    print(f"  本地端口: {LOCAL_PORT}")
    print("=" * 50)

    url = None

    if backend == "auto":
        print("\n自动检测隧道后端...\n")
        url = try_cloudflared()
        if not url:
            url = try_ngrok()
        if not url:
            url = try_bore()
    elif backend == "--cloudflared":
        url = try_cloudflared()
    elif backend == "--ngrok":
        url = try_ngrok()
    elif backend == "--bore":
        url = try_bore()

    if url:
        print(f"\n✅ 公网地址: {url}")
        print("   用手机浏览器打开此地址，然后「添加到主屏幕」即可。")
        print("\n   按 Ctrl+C 停止隧道。")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n隧道已停止。")
    else:
        print("\n❌ 未能建立隧道。")
        print("   请安装以下任一工具后重试：")
        print("   1. cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        print("   2. ngrok: pip install pyngrok && ngrok config add-authtoken <token>")


if __name__ == "__main__":
    main()
