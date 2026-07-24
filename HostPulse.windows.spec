# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec per HostPulse (build Windows)
# Esecuzione: pyinstaller --clean --noconfirm HostPulse.windows.spec

import os

block_cipher = None

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
        "engine",
        "reporter_generator",
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=os.environ.get("HOSTPULSE_EXE_NAME", "HostPulse"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
