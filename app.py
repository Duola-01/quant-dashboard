"""
量化策略监控台 v2.1 — 亮色版
============================
+ 亮色主题 · 清爽卡片
+ 双轴走势图：左轴金额 / 右轴收益率 · 从初始值起点
+ 多策略对比 · 信号分布 · 自动刷新
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import requests
from pathlib import Path
from datetime import datetime
from api_client import (
    get_metrics,
    get_table_data,
    get_chart_data,
    probe_connection,
    API_BASE,
)

# ================================================================
#  版本
# ================================================================
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
    try:
        resp = requests.get(REMOTE_VERSION_URL, timeout=5)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception:
        pass
    return None

# ================================================================
#  页面配置
# ================================================================
st.set_page_config(
    page_title="量化策略监控台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
#  自定义 CSS — 亮色主题
# ================================================================
st.markdown("""
<style>
/* === 全局 === */
.main { background: #f5f6f8; }
section[data-testid="stSidebar"] > div { background: #ffffff; border-right: 1px solid #e5e7eb; }
body { color: #1f2937; }

/* === 指标卡片 === */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
div[data-testid="stMetric"] > label {
    color: #6b7280 !important;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
div[data-testid="stMetric"] > div[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
}

/* === Tab 导航 === */
button[data-baseweb="tab"] {
    font-size: 0.9rem !important;
    padding: 6px 16px !important;
    color: #6b7280 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #2563eb !important;
    border-bottom: 2px solid #2563eb !important;
}

/* === 按钮 === */
div[data-testid="stButton"] > button {
    border-radius: 8px;
    font-weight: 500;
    border: 1px solid #d1d5db;
}

/* === 表格 === */
div[data-testid="stDataFrame"] {
    border-radius: 8px;
    border: 1px solid #e5e7eb;
}

/* === 移动端 === */
@media (max-width: 768px) {
    div[data-testid="stMetric"] > div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }
}

/* === Streamlit 默认暗色覆盖 === */
.stApp { background: #f5f6f8; }
</style>
""", unsafe_allow_html=True)

# ================================================================
#  PWA 注入
# ================================================================
st.markdown("""
<script>
(function() {
    if (document.querySelector('link[rel="manifest"]')) return;
    var link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/app/static/manifest.json';
    document.head.appendChild(link);
    var m = document.createElement('meta');
    m.name = 'apple-mobile-web-app-capable';
    m.content = 'yes'; document.head.appendChild(m);
    m = document.createElement('meta');
    m.name = 'apple-mobile-web-app-status-bar-style';
    m.content = 'default'; document.head.appendChild(m);
    m = document.createElement('meta');
    m.name = 'viewport';
    m.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    document.head.appendChild(m);
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/app/static/sw.js');
    }
})();
</script>
""", unsafe_allow_html=True)

# ================================================================
#  初始化 session_state
# ================================================================
defaults = {
    "cached_metrics": {},
    "cached_table": pd.DataFrame(),
    "cached_chart": pd.DataFrame(),
    "cached_metrics_b": {},
    "cached_table_b": pd.DataFrame(),
    "cached_chart_b": pd.DataFrame(),
    "api_connected": True,
    "update_checked": False,
    "auto_refresh": False,
    "refresh_interval": 10,
    "compare_mode": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================================================================
#  自动刷新
# ================================================================
if st.session_state.auto_refresh:
    interval_ms = st.session_state.refresh_interval * 1000
    st.markdown(f"""
    <script>
    (function() {{
        if (window.__autoRefreshSet) return;
        window.__autoRefreshSet = true;
        setTimeout(function() {{ window.location.reload(); }}, {interval_ms});
    }})();
    </script>
    """, unsafe_allow_html=True)

# ================================================================
#  侧边栏
# ================================================================
with st.sidebar:
    st.title("📊 量化策略监控台")
    st.caption(f"v{_current_version()} · 亮色版")
    st.markdown("**策略：全策略**")
    strategies = ["策略 A", "策略 B"]

    st.divider()

    col_ref, col_int = st.columns([1, 1])
    with col_ref:
        st.session_state.auto_refresh = st.toggle("🔄 自动刷新", value=st.session_state.auto_refresh)
    with col_int:
        st.session_state.refresh_interval = st.number_input(
            "间隔(秒)", min_value=5, max_value=300,
            value=st.session_state.refresh_interval, step=5,
            disabled=not st.session_state.auto_refresh,
        )

    if st.button("🔄 立即刷新", use_container_width=True):
        for k in ("cached_metrics", "cached_table", "cached_chart",
                  "cached_metrics_b", "cached_table_b", "cached_chart_b"):
            st.session_state[k] = defaults[k]
        st.rerun()

    st.divider()

    if st.button("🔍 检查更新", use_container_width=True):
        with st.spinner("正在检查..."):
            rv = _remote_version()
        if rv is None:
            st.warning("无法连接更新服务器")
        elif rv != _current_version():
            st.success(f"🆕 新版本: {rv}")
        else:
            st.info("已是最新版本")

    if not st.session_state.update_checked:
        st.session_state.update_checked = True
        rv = _remote_version()
        if rv and rv != _current_version():
            st.warning(f"🆕 有新版本可用: {rv}")

    st.divider()

    with st.status("正在重连...", expanded=False) as status:
        api_ok, latency = probe_connection()
        st.session_state.api_connected = api_ok
        if api_ok:
            status.update(label=f"API 已连接 ({latency:.2f}s)", state="complete")
        else:
            status.update(label="连接断开", state="error")

    if st.session_state.auto_refresh:
        st.caption(f"⏱ 每 {st.session_state.refresh_interval}s 刷新")
    st.caption(f"API: {API_BASE}")

# ================================================================
#  数据获取 — 全策略：同时拉两个策略 + 合并
# ================================================================

def _fetch_all(strat):
    return get_metrics(strat), get_table_data(strat, limit=100), get_chart_data(strat, points=80)

def _merge_metrics(a: dict, b: dict) -> dict:
    """合并两个策略的指标（数值相加）。"""
    result = {}
    for key in ["当前持仓数", "今日信号数", "账户盈亏"]:
        va = a.get(key, 0) or 0
        vb = b.get(key, 0) or 0
        try:
            result[key] = float(va) + float(vb)
            if key in ("当前持仓数", "今日信号数"):
                result[key] = int(result[key])
            else:
                result[key] = round(result[key], 2)
        except (ValueError, TypeError):
            result[key] = va or vb or 0
    return result

def _merge_charts(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """合并两张走势图，按时间排序后叠加价格。"""
    if a.empty:
        return b.copy() if not b.empty else a
    if b.empty:
        return a.copy()
    merged = pd.concat([a, b], ignore_index=True)
    if "时间" in merged.columns:
        if not pd.api.types.is_datetime64_any_dtype(merged["时间"]):
            merged["时间"] = pd.to_datetime(merged["时间"], errors="coerce")
        merged = merged.dropna(subset=["时间"]).sort_values("时间").reset_index(drop=True)
    return merged


# 初始化默认值（作用域外可用）
ma = mb = {}
ta = tb = ca = cb = pd.DataFrame()

if st.session_state.api_connected:
    ma, ta, ca = _fetch_all("策略 A")
    mb, tb, cb = _fetch_all("策略 B")

    # 指标: 相加
    m = _merge_metrics(ma or {}, mb or {})
    st.session_state.cached_metrics = m

    # 信号: 拼接
    ta = ta if not ta.empty else pd.DataFrame()
    tb = tb if not tb.empty else pd.DataFrame()
    t = pd.concat([ta, tb], ignore_index=True) if not (ta.empty and tb.empty) else pd.DataFrame()
    st.session_state.cached_table = t

    # 走势: 合并（关键帧排序）
    c = _merge_charts(ca, cb)
    st.session_state.cached_chart = c
else:
    m = st.session_state.cached_metrics
    t = st.session_state.cached_table
    c = st.session_state.cached_chart

# ================================================================
#  断开横幅
# ================================================================
if not st.session_state.api_connected:
    st.warning("⚠️ 连接断开 — 当前显示缓存数据，API 恢复后自动重连。")

# ================================================================
#  量化指标计算（从走势 + 信号数据推导，不依赖 API 逐项返回）
# ================================================================
import numpy as np

def _calc_metrics(df_chart: pd.DataFrame, df_signal: pd.DataFrame, raw: dict) -> dict:
    """
    从走势图和信号表计算专业量化指标。
    返回 dict，所有值都是格式化好的显示字符串或数值。
    """
    result = {
        "持仓数": 0, "信号数": 0, "盈亏": 0,
        "累计收益率": "—", "最大回撤": "—", "年化波动": "—", "夏普": "—", "胜率": "—",
    }

    # 原始指标
    result["持仓数"] = int(raw.get("当前持仓数", 0) or 0)
    result["信号数"] = int(raw.get("今日信号数", 0) or 0)
    try:
        result["盈亏"] = round(float(raw.get("账户盈亏", 0) or 0), 2)
    except Exception:
        result["盈亏"] = 0

    # ---- 从走势图计算 ----
    if df_chart is not None and not df_chart.empty and "模拟价格" in df_chart.columns:
        price = pd.to_numeric(df_chart["模拟价格"], errors="coerce").dropna()
        if len(price) >= 2:
            p = price.values

            # 累计收益率
            total_ret = (p[-1] / p[0] - 1) * 100
            result["累计收益率"] = f"{total_ret:+.2f}%"

            # 最大回撤
            peak = np.maximum.accumulate(p)
            drawdowns = (p - peak) / peak * 100
            max_dd = float(np.min(drawdowns))
            result["最大回撤"] = f"{max_dd:.2f}%"

            # 年化波动率 & 夏普（需足够数据点）
            if len(p) >= 5:
                daily_ret = np.diff(p) / p[:-1]
                ann_vol = float(np.std(daily_ret, ddof=1) * np.sqrt(252) * 100)
                result["年化波动"] = f"{ann_vol:.1f}%"
                if ann_vol > 0:
                    ann_ret = total_ret  # 简化：用累计收益率当年代化
                    sharpe = (ann_ret - 3) / ann_vol  # 假设无风险 3%
                    result["夏普"] = f"{sharpe:.2f}"
                else:
                    result["夏普"] = "—"

    # ---- 从信号表计算胜率 ----
    if df_signal is not None and not df_signal.empty and "信号类型" in df_signal.columns:
        sig = df_signal["信号类型"]
        buy = int((sig == "买入").sum())
        sell = int((sig == "卖出").sum())
        total = buy + sell
        if total > 0:
            rate = buy / total * 100
            result["胜率"] = f"{rate:.0f}%"
        else:
            result["胜率"] = "—"

    return result


def _safe(val, default=0):
    return default if val is None else val

def _can_plot(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False
    if "时间" not in df.columns:
        return False
    tc = df["时间"]
    return not (tc.empty or tc.isna().all())

def _pnl_color(pnl):
    try:
        return "normal" if float(pnl) >= 0 else "inverse"
    except Exception:
        return "normal"

# ================================================================
#  双轴走势图（matplotlib）
# ================================================================
def _dual_axis_chart(df: pd.DataFrame, title: str = ""):
    """
    双轴走势图：左轴金额，右轴收益率%，起点从底部。
    """
    if df is None or df.empty or "时间" not in df.columns:
        return None

    data = df.copy()
    data = data.dropna(subset=["时间"])

    # 时间轴处理
    if not pd.api.types.is_datetime64_any_dtype(data["时间"]):
        data["时间"] = pd.to_datetime(data["时间"], errors="coerce")
    data = data.dropna(subset=["时间"]).sort_values("时间")

    price = pd.to_numeric(data["模拟价格"], errors="coerce")
    if price.dropna().empty:
        return None

    # 基础值
    initial = price.iloc[0]
    if initial == 0:
        return None
    return_rate = (price / initial - 1) * 100

    # ---- 绘图 ----
    plt.style.use("default")
    fig, ax1 = plt.subplots(figsize=(10, 3.8))
    fig.patch.set_facecolor("#f5f6f8")
    ax1.set_facecolor("#f5f6f8")

    # 左轴：金额
    ax1.plot(
        data["时间"], price,
        color="#2563eb", linewidth=2.0, marker="", zorder=3
    )
    ax1.set_ylabel("金额 (¥)", color="#2563eb", fontsize=10, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#2563eb", labelsize=9)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"¥{x:,.0f}"))

    # y 轴从初始值开始（留少量边距）
    y_min = min(price.min(), initial) * 0.995
    y_max = max(price.max(), initial) * 1.005
    ax1.set_ylim(y_min, y_max)

    # 右轴：收益率
    ax2 = ax1.twinx()
    ax2.plot(
        data["时间"], return_rate,
        color="#059669", linewidth=1.8, linestyle="--", marker="", zorder=2
    )
    ax2.set_ylabel("收益率 (%)", color="#059669", fontsize=10, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#059669", labelsize=9)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:+.1f}%"))

    # 收益率 y 轴也贴近数据，0 始终可见
    r_min = min(return_rate.min(), 0) - 0.5
    r_max = max(return_rate.max(), 0) + 0.5
    r_min = max(r_min, r_max - 20)  # 至少 20 个百分点的范围
    r_max = min(r_max, r_min + 20)
    ax2.set_ylim(r_min, r_max)

    # 0% 参考线
    ax2.axhline(y=0, color="#9ca3af", linewidth=0.8, linestyle=":", zorder=1)

    # 网格
    ax1.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax1.set_xlabel("")
    ax1.tick_params(axis="x", labelsize=8, rotation=30)

    if title:
        ax1.set_title(title, fontsize=12, fontweight="bold", color="#111827", pad=8)

    fig.tight_layout()
    return fig


# ================================================================
#  主页面 - 核心指标（从走势数据推导）
# ================================================================
st.markdown("### 📌 核心指标")

qm = _calc_metrics(c, t, m)

row1_col1, row1_col2, row1_col3, row1_col4, row1_col5, row1_col6 = st.columns(6)

with row1_col1:
    st.metric("累计收益率", qm["累计收益率"],
              delta=None, delta_color="normal" if "+" in str(qm["累计收益率"]) else "inverse")
with row1_col2:
    st.metric("最大回撤", qm["最大回撤"])
with row1_col3:
    st.metric("夏普比率", qm["夏普"])
with row1_col4:
    st.metric("年化波动", qm["年化波动"])
with row1_col5:
    st.metric("胜率", qm["胜率"])
with row1_col6:
    st.metric("信号数", qm["信号数"])

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.metric("当前持仓", qm["持仓数"])
with row2_col2:
    pnl = qm["盈亏"]
    st.metric("账户盈亏", f"¥ {pnl:,.2f}",
              delta=None, delta_color=_pnl_color(pnl))

# ================================================================
#  Tab 视图
# ================================================================
tab_overview, tab_signals, tab_breakdown = st.tabs([
    "📈 账户走势",
    "📋 信号明细",
    "📊 分策略",
])

# ---- Tab 1: 账户走势 ----
with tab_overview:
    left, right = st.columns([3, 1])

    with left:
        st.subheader("账户金额 & 收益率")
        fig = _dual_axis_chart(c, "全策略")
        if fig is not None:
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("暂无走势数据 — 需要至少 2 个有效数据点")

    with right:
        st.subheader("信号分布")
        if t.empty:
            st.info("暂无信号")
        elif "信号类型" in t.columns:
            dist = t["信号类型"].value_counts().reset_index()
            dist.columns = ["类型", "数量"]

            # 转为横表：每类一列，color 按列匹配
            color_map = {"买入": "#2563eb", "卖出": "#dc2626", "持有": "#6b7280"}
            pivot = pd.DataFrame({row["类型"]: [row["数量"]] for _, row in dist.iterrows()})
            cols_ordered = [c for c in ["买入", "卖出", "持有"] if c in pivot.columns]
            pivot = pivot[cols_ordered]
            colors = [color_map[c] for c in cols_ordered]

            st.bar_chart(pivot, color=colors, height=260)

            buy_cnt = int(dist[dist["类型"] == "买入"]["数量"].sum()) if "买入" in dist["类型"].values else 0
            sell_cnt = int(dist[dist["类型"] == "卖出"]["数量"].sum()) if "卖出" in dist["类型"].values else 0
            total = buy_cnt + sell_cnt
            if total > 0:
                ratio = buy_cnt / total * 100
                st.caption(f"买卖: {buy_cnt}:{sell_cnt}  ({ratio:.0f}:{100-ratio:.0f})")

    # 信号时间轴
    st.subheader("⏱ 信号时段分布")
    if t.empty or "时间" not in t.columns:
        st.info("暂无时间轴数据")
    else:
        try:
            timeline = t.copy()
            timeline["时段"] = timeline["时间"].apply(
                lambda x: str(x)[:2] + ":00" if isinstance(x, str) and len(str(x)) >= 2 else "未知"
            )
            hourly = timeline.groupby("时段").size().reset_index()
            hourly.columns = ["时段", "信号数"]
            st.bar_chart(hourly.set_index("时段"), height=200, use_container_width=True)
        except Exception:
            st.info("时段解析失败")

# ---- Tab 2: 信号明细 ----
with tab_signals:
    st.subheader("📋 最近信号")

    if not t.empty and "信号类型" in t.columns:
        sig_types = ["全部"] + sorted(t["信号类型"].unique().tolist())
        filter_type = st.selectbox("筛选信号类型", sig_types, label_visibility="collapsed")

        display_t = t if filter_type == "全部" else t[t["信号类型"] == filter_type]
        st.dataframe(display_t, use_container_width=True, hide_index=True, height=420)
        st.caption(f"共 {len(display_t)} 条信号")
    elif t.empty:
        st.info("暂无信号数据")
    else:
        st.dataframe(t, use_container_width=True, hide_index=True, height=420)

# ---- Tab 3: 分策略视图 ----
with tab_breakdown:
    st.subheader("📊 策略 A  vs  策略 B")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**策略 A**")
        if _can_plot(ca):
            fig_a = _dual_axis_chart(ca, "策略 A")
            if fig_a:
                st.pyplot(fig_a)
                plt.close(fig_a)
            else:
                st.info("暂无走势数据")
        else:
            st.info("暂无走势数据")

        if not ta.empty:
            st.dataframe(ta, use_container_width=True, hide_index=True, height=240)
        else:
            st.info("暂无信号")
    with col_r:
        st.markdown("**策略 B**")
        if _can_plot(cb):
            fig_b = _dual_axis_chart(cb, "策略 B")
            if fig_b:
                st.pyplot(fig_b)
                plt.close(fig_b)
            else:
                st.info("暂无走势数据")
        else:
            st.info("暂无走势数据")

        if not tb.empty:
            st.dataframe(tb, use_container_width=True, hide_index=True, height=240)
        else:
            st.info("暂无信号")

# ================================================================
#  底部状态栏
# ================================================================
st.divider()
now = datetime.now().strftime("%H:%M:%S")
status_text = "🟢 实时" if st.session_state.api_connected else "🔴 离线"
auto_suffix = " · 自动刷新中" if st.session_state.auto_refresh else ""
st.caption(f"{status_text} · 全策略 · {now}{auto_suffix}")
