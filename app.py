"""
量化策略监控台 - 主程序
======================
Streamlit Web App — 纯前端展示层。
支持 PWA（添加到手机主屏幕）、远程隧道、在线更新。

容错设计：
  - API 断开 → 先做连通探测（带重试），失败则跳过数据请求直接使用缓存
  - 探测期间 → 显示「正在重连...」
  - 字段缺失/类型不匹配 → 安全取值 + 类型转换
  - 图表数据异常 → 降级显示「暂无数据」
"""

import streamlit as st
import pandas as pd
import requests
from pathlib import Path
from api_client import (
    get_metrics,
    get_table_data,
    get_chart_data,
    probe_connection,
    API_BASE,
)

# ---- 版本信息 ----
VERSION_FILE = Path(__file__).parent / "version.txt"
REMOTE_VERSION_URL = (
    "https://raw.githubusercontent.com/YOUR_REPO/main/quant-monitor/version.txt"
)


def _current_version() -> str:
    try:
        return VERSION_FILE.read_text().strip()
    except Exception:
        return "0.0.0"


def _remote_version() -> str | None:
    """获取远程最新版本号。失败返回 None。"""
    try:
        resp = requests.get(REMOTE_VERSION_URL, timeout=5)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception:
        pass
    return None


# ---- 页面配置 ----
st.set_page_config(
    page_title="量化策略监控台",
    page_icon="📊",
    layout="wide",
)

# ---- PWA 注入（添加到手机主屏幕） ----
st.markdown(
    """
<script>
(function() {
    if (document.querySelector('link[rel="manifest"]')) return;
    var link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/app/static/manifest.json';
    document.head.appendChild(link);

    var m1 = document.createElement('meta');
    m1.name = 'apple-mobile-web-app-capable';
    m1.content = 'yes';
    document.head.appendChild(m1);

    var m2 = document.createElement('meta');
    m2.name = 'apple-mobile-web-app-status-bar-style';
    m2.content = 'black-translucent';
    document.head.appendChild(m2);

    var m3 = document.createElement('meta');
    m3.name = 'apple-mobile-web-app-title';
    m3.content = '量化监控台';
    document.head.appendChild(m3);

    var m4 = document.createElement('meta');
    m4.name = 'viewport';
    m4.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    document.head.appendChild(m4);

    var m5 = document.createElement('meta');
    m5.name = 'theme-color';
    m5.content = '#0e1117';
    document.head.appendChild(m5);

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/app/static/sw.js');
    }
})();
</script>
""",
    unsafe_allow_html=True,
)

# ---- 初始化 session_state 缓存 ----
if "cached_metrics" not in st.session_state:
    st.session_state.cached_metrics = {}
if "cached_table" not in st.session_state:
    st.session_state.cached_table = pd.DataFrame()
if "cached_chart" not in st.session_state:
    st.session_state.cached_chart = pd.DataFrame()
if "api_connected" not in st.session_state:
    st.session_state.api_connected = True
if "update_checked" not in st.session_state:
    st.session_state.update_checked = False

# ============================================================
#  侧边栏
# ============================================================
with st.sidebar:
    st.title("📊 量化策略监控台")

    strategy = st.selectbox(
        "选择策略",
        options=["策略 A", "策略 B"],
    )

    if st.button("🔄 刷新数据", use_container_width=True):
        st.session_state.cached_metrics = {}
        st.session_state.cached_table = pd.DataFrame()
        st.session_state.cached_chart = pd.DataFrame()
        st.rerun()

    st.divider()

    # ---- 版本与更新 ----
    current_ver = _current_version()
    st.caption(f"版本: {current_ver}")

    if st.button("🔍 检查更新", use_container_width=True):
        with st.spinner("正在检查..."):
            remote_ver = _remote_version()
        if remote_ver is None:
            st.warning("无法连接更新服务器")
        elif remote_ver != current_ver:
            st.success(f"🆕 发现新版本: {remote_ver}")
            st.info("请更新 quant-monitor/ 目录下的文件后刷新页面。")
        else:
            st.info("已是最新版本")

    # 首次进入自动检查一次
    if not st.session_state.update_checked:
        st.session_state.update_checked = True
        remote_ver = _remote_version()
        if remote_ver and remote_ver != current_ver:
            st.warning(f"🆕 有新版本可用: {remote_ver}")

    st.divider()

    # ---- API 连接状态（实时探测，带重试） ----
    with st.status("正在重连...", expanded=False) as status:
        api_ok, latency = probe_connection()
        st.session_state.api_connected = api_ok
        if api_ok:
            status.update(label=f"API 已连接 ({latency:.2f}s)", state="complete")
        else:
            status.update(label="连接断开 — OpenClaw API 不可达", state="error")

    st.caption(f"当前策略：{strategy}")

# ============================================================
#  数据获取（连通失败则跳过所有请求，直接用缓存）
# ============================================================

if st.session_state.api_connected:
    metrics = get_metrics(strategy)
    if metrics:
        st.session_state.cached_metrics = metrics
    else:
        metrics = st.session_state.cached_metrics

    table_data = get_table_data(strategy, limit=20)
    if not table_data.empty:
        st.session_state.cached_table = table_data
    else:
        table_data = st.session_state.cached_table

    chart_data = get_chart_data(strategy, points=50)
    if not chart_data.empty:
        st.session_state.cached_chart = chart_data
    else:
        chart_data = st.session_state.cached_chart
else:
    metrics = st.session_state.cached_metrics
    table_data = st.session_state.cached_table
    chart_data = st.session_state.cached_chart

# ============================================================
#  主页面 - 连接断开提示横幅
# ============================================================
if not st.session_state.api_connected:
    st.warning(
        "⚠️ 连接断开 — 当前显示的是上一次缓存数据。"
        "OpenClaw API 恢复后刷新页面即可自动重连。"
    )


# ============================================================
#  渲染辅助函数（容错）
# ============================================================

def _safe_metric_value(metrics_dict: dict, key: str, default=0):
    if not metrics_dict:
        return default
    val = metrics_dict.get(key)
    if val is None:
        return default
    return val


def _safe_pnl_str(pnl) -> str:
    try:
        return f"¥ {float(pnl):,.2f}"
    except (ValueError, TypeError):
        return f"¥ {pnl}"


def _can_plot(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False
    if "时间" not in df.columns:
        return False
    time_col = df["时间"]
    if time_col.empty or time_col.isna().all():
        return False
    return True


# ============================================================
#  主页面 - 指标卡片
# ============================================================
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="当前持仓数", value=_safe_metric_value(metrics, "当前持仓数"))
with col2:
    st.metric(label="今日信号数", value=_safe_metric_value(metrics, "今日信号数"))
with col3:
    st.metric(
        label="账户盈亏",
        value=_safe_pnl_str(_safe_metric_value(metrics, "账户盈亏")),
    )

# ============================================================
#  主页面 - 信号表格
# ============================================================
st.subheader("📋 最近信号")
if table_data.empty:
    st.info("暂无信号数据")
else:
    st.dataframe(table_data, use_container_width=True, hide_index=True)

# ============================================================
#  主页面 - 走势图
# ============================================================
st.subheader("📈 价格走势")
if not _can_plot(chart_data):
    st.info("暂无走势数据")
else:
    try:
        plot_df = chart_data.set_index("时间")
        if not isinstance(plot_df.index, pd.DatetimeIndex):
            plot_df.index = pd.to_datetime(plot_df.index, errors="coerce")
        st.line_chart(plot_df)
    except Exception:
        st.info("暂无走势数据")
