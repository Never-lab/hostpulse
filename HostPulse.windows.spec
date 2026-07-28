# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Windows onedir (meno falsi positivi AV vs onefile+UPX).
# Build: pyinstaller --clean --noconfirm --distpath dist/windows HostPulse.windows.spec

import os
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)
version_file = root / "scripts" / "windows_version_info.txt"

extra_datas = [("config/config.example.json", "config")]
try:
    from PyInstaller.utils.hooks import collect_data_files

    extra_datas += collect_data_files("customtkinter")
    extra_datas += collect_data_files("matplotlib")
except Exception:
    pass

a = Analysis(
    ["bin/ui_benchmark.py"],
    pathex=["bin"],
    binaries=[],
    datas=extra_datas,
    hiddenimports=[
        "app_paths",
        "cancel",
        "cli",
        "engine",
        "orchestrator",
        "pdf_export",
        "reporter_generator",
        "schema",
        "version",
        "customtkinter",
        "PIL._tkinter_finder",
        "matplotlib.backends.backend_agg",
        "seaborn",
        "pandas",
        "numpy",
        "psutil",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=os.environ.get("HOSTPULSE_EXE_NAME", "HostPulse"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    version=str(version_file) if version_file.is_file() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=os.environ.get("HOSTPULSE_EXE_NAME", "HostPulse"),
)
