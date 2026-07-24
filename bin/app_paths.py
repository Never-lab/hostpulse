"""Percorsi compatibili con esecuzione da sorgente e da EXE PyInstaller."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_bundle_dir() -> Path:
    """Risorse in sola lettura incluse nel bundle (_MEIPASS)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def get_app_base_dir() -> Path:
    """Directory base scrivibile: root progetto in dev, cartella exe se frozen."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_config_dir() -> Path:
    return get_app_base_dir() / "config"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def get_results_dir() -> Path:
    return get_app_base_dir() / "results"


def get_bin_dir() -> Path:
    if is_frozen():
        return get_app_base_dir()
    return Path(__file__).resolve().parent


def ensure_runtime_dirs() -> None:
    """Crea cartelle runtime e copia config di esempio se mancante."""
    get_config_dir().mkdir(parents=True, exist_ok=True)
    get_results_dir().mkdir(parents=True, exist_ok=True)

    cfg = get_config_path()
    if cfg.exists():
        return

    candidates = [
        get_bundle_dir() / "config" / "config.example.json",
        get_bundle_dir() / "config.example.json",
        get_app_base_dir() / "config" / "config.example.json",
    ]
    for example in candidates:
        if example.is_file():
            shutil.copy(example, cfg)
            return
