"""
量化策略监控台 - API 客户端模块
==============================
所有数据通过 HTTP 向 OpenClaw 端 API 服务请求获取。
本文件不包含任何选股逻辑或模拟数据生成。

容错设计：
  - 网络异常 → 返回空数据结构，不抛异常
  - 字段类型不匹配 → 类型强制转换（字符串→数值、时间戳→可读格式）
  - JSON 结构变化 → 缺失字段自动补默认值
  - 连通性探测 → probe_connection() 用短超时 + 重试，避免多次阻塞等待
"""

import requests
import pandas as pd
import os
import math
import time
from datetime import datetime
from typing import Optional

# ================================================================
#  配置
# ================================================================

# OpenClaw API 地址
API_BASE = os.environ.get("API_BASE", "http://localhost:8520")

# 单次 HTTP 请求超时（秒）— 数据接口用，防止网络卡顿导致界面长时间转圈
REQUEST_TIMEOUT = 5

# 健康检查专用超时（秒）— 端点极轻量，短超时即可
HEALTH_TIMEOUT = 3

# 默认空 DataFrame 列名（用于 API 异常时的降级显示）
EMPTY_TABLE_COLS = ["时间", "股票代码", "股票名称", "当前价格", "信号类型"]
EMPTY_CHART_COLS = ["时间", "模拟价格"]
METRIC_KEYS = ["当前持仓数", "今日信号数", "账户盈亏"]


# ================================================================
#  底层 HTTP 请求
# ================================================================

def _get(endpoint: str, params: Optional[dict] = None) -> dict | list | None:
    """通用 GET 请求。超时 REQUEST_TIMEOUT 秒，异常返回 None。"""
    try:
        resp = requests.get(
            f"{API_BASE}{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def _get_health() -> dict | None:
    """健康检查专用请求，使用较短的 HEALTH_TIMEOUT。"""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=HEALTH_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


# ================================================================
#  连通性探测（短超时 + 重试 → 避免后续数据请求继续阻塞）
# ================================================================

def probe_connection(
    retries: int = 1,
    delay: float = 0.5,
) -> tuple[bool, float | None]:
    """
    连通性探测，带快速重试。

    使用 HEALTH_TIMEOUT（默认 3s）探测 /health 端点。
    失败后延迟 delay 秒重试，最多 retries 次。
    任意一次成功即返回，避免后续 get_metrics/get_table_data/get_chart_data
    在 API 不可达时继续各等 5 秒。

    最坏耗时 ≈ HEALTH_TIMEOUT + retries × (HEALTH_TIMEOUT + delay)
               ≈ 3 + 1 × 3.5 ≈ 6.5 秒

    返回:
        (True, 延迟秒数)   — 连通成功
        (False, None)      — 所有重试均失败
    """
    for attempt in range(retries + 1):
        t0 = time.time()
        if _get_health() is not None:
            latency = round(time.time() - t0, 3)
            return True, latency
        if attempt < retries:
            time.sleep(delay)
    return False, None


def is_api_available() -> bool:
    """单次连通检查（无重试）。推荐用 probe_connection()。"""
    return _get_health() is not None


# ================================================================
#  时间字段兼容转换
# ================================================================

def _normalize_signal_time(val) -> str:
    """
    信号表格的时间字段兼容处理。
    支持：字符串 / Unix 时间戳（秒/毫秒） / None / NaN → 可读字符串。
    """
    if val is None:
        return ""
    if isinstance(val, float) and math.isnan(val):
        return ""
    if isinstance(val, (int, float)):
        if val > 1e12:
            val = val / 1000.0
        try:
            return datetime.fromtimestamp(float(val)).strftime("%H:%M:%S")
        except (ValueError, OSError):
            return str(int(val))
    return str(val)


def _normalize_chart_time(series: pd.Series) -> pd.Series:
    """
    图表时间列转换 → datetime64。
    支持：ISO 字符串 / date 字符串 / Unix 时间戳（秒/毫秒）。
    """
    result = pd.to_datetime(series, errors="coerce")
    if result.isna().all():
        numeric = pd.to_numeric(series, errors="coerce")
        if not numeric.isna().all():
            if numeric.max() > 1e12:
                numeric = numeric / 1000.0
            result = pd.to_datetime(numeric, unit="s", errors="coerce")
    return result


# ================================================================
#  API 数据获取函数
# ================================================================

def get_metrics(strategy: str = "策略 A") -> dict:
    """
    获取指标卡数据。数值字段强制类型转换。
    失败返回 {}。
    """
    data = _get("/metrics", {"strategy": strategy})
    if not isinstance(data, dict):
        return {}

    clean = {}
    for key in METRIC_KEYS:
        val = data.get(key, 0)
        try:
            if key in ("当前持仓数", "今日信号数"):
                clean[key] = int(float(str(val)))
            else:
                clean[key] = round(float(str(val)), 2)
        except (ValueError, TypeError):
            clean[key] = 0
    return clean


def get_table_data(strategy: str = "策略 A", limit: int = 20) -> pd.DataFrame:
    """
    获取信号列表 → DataFrame。时间戳/股票代码自动规范化。
    失败返回带列名的空 DataFrame。
    """
    data = _get("/signals", {"strategy": strategy, "limit": limit})
    if not isinstance(data, list) or len(data) == 0:
        return pd.DataFrame(columns=EMPTY_TABLE_COLS)

    try:
        df = pd.DataFrame(data)
        if "时间" in df.columns:
            df["时间"] = df["时间"].apply(_normalize_signal_time)
        if "股票代码" in df.columns:
            df["股票代码"] = df["股票代码"].astype(str).str.zfill(6)
        for col in EMPTY_TABLE_COLS:
            if col not in df.columns:
                df[col] = ""
        return df[EMPTY_TABLE_COLS]
    except Exception:
        return pd.DataFrame(columns=EMPTY_TABLE_COLS)


def get_chart_data(strategy: str = "策略 A", points: int = 50) -> pd.DataFrame:
    """
    获取走势图数据 → DataFrame。时间多格式兼容，价格强制 float。
    失败返回带列名的空 DataFrame。
    """
    data = _get("/chart", {"strategy": strategy, "points": points})
    if not isinstance(data, list) or len(data) == 0:
        return pd.DataFrame(columns=EMPTY_CHART_COLS)

    try:
        df = pd.DataFrame(data)
        if "时间" in df.columns:
            df["时间"] = _normalize_chart_time(df["时间"])
        if "时间" in df.columns:
            df = df.dropna(subset=["时间"])
        if "模拟价格" not in df.columns:
            df["模拟价格"] = 0.0
        else:
            df["模拟价格"] = (
                pd.to_numeric(df["模拟价格"], errors="coerce").fillna(0.0)
            )
        return df[["时间", "模拟价格"]]
    except Exception:
        return pd.DataFrame(columns=EMPTY_CHART_COLS)
