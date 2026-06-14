"""
PyInstaller 打包配置 — 构建量化监控台 .exe
==========================================
使用方法：
    cd quant-monitor
    pip install pyinstaller
    pyinstaller build_app.spec

输出：dist/量化监控台/量化监控台.exe
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()

a = Analysis(
    [str(HERE / "run_app.py")],
    pathex=[str(HERE)],
    binaries=[],
    datas=[
        (str(HERE / "app.py"), "."),
        (str(HERE / "api_client.py"), "."),
        (str(HERE / "version.txt"), "."),
        (str(HERE / "static" / "manifest.json"), "static"),
        (str(HERE / "static" / "sw.js"), "static"),
        (str(HERE / "static" / "icon-192.png"), "static"),
        (str(HERE / "static" / "icon-512.png"), "static"),
    ],
    hiddenimports=[
        "streamlit",
        "streamlit.web.bootstrap",
        "streamlit.runtime",
        "streamlit.runtime.scriptrunner",
        "pandas",
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "pyarrow",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="量化监控台",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
