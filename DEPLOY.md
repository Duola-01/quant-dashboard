# 量化策略监控台 — 手机 App 指南
# ===================================

## 架构
#   手机 (浏览器/PWA) → 云服务器 (Streamlit) → 你的电脑 (OpenClaw API :8520)
#                         ↑ 免费部署              ↑ cloudflared 隧道

## 部署步骤

### 第一步：在你的电脑上启动 API 隧道
#   打开终端，运行：
#   cloudflared tunnel --url http://localhost:8520
#
#   记下输出的 trycloudflare.com 地址，例如：
#   https://happy-mars.trycloudflare.com

### 第二步：部署 Streamlit 到云端（三选一）

#   A) Streamlit Cloud（推荐，免费）
#      1. 把 quant-monitor/ 文件夹推送到 GitHub 仓库
#      2. 打开 https://share.streamlit.io
#      3. 选择仓库，主文件路径填 app.py
#      4. 高级设置 → 环境变量：
#         API_BASE = https://happy-mars.trycloudflare.com
#      5. 部署 → 拿到网址（如 https://xxx.streamlit.app）

#   B) Hugging Face Spaces（免费）
#      1. 打开 https://huggingface.co/spaces
#      2. Create new Space → Streamlit
#      3. 上传 quant-monitor/ 所有文件
#      4. Settings → Secrets:
#         API_BASE = https://happy-mars.trycloudflare.com

#   C) 自建 VPS
#      git clone && pip install -r requirements.txt
#      API_BASE=https://xxx.trycloudflare.com streamlit run app.py

### 第三步：手机添加
#   手机浏览器打开云端网址 → 菜单 → 「添加到主屏幕」
#   以后就像原生 App 一样直接打开。
