"""Built-in and custom UI benchmark presets persisted in config.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app_paths import get_config_path

DEFAULT_LAST_PRESET = "DB prod-safe"


@dataclass
class Preset:
    name: str
    profile: str
    quick: bool
    production_safe: bool
    compare: bool
    builtin: bool


BUILTINS: list[Preset] = [
    Preset("DB prod-safe", "db_server", False, True, False, True),
    Preset("App full", "app_server", False, False, False, True),
    Preset("Quick smoke", "generic", True, False, False, True),
]

_BUILTIN_NAMES = {p.name for p in BUILTINS}


def _resolve_config_path(config_path: Path | None) -> Path:
    return config_path if config_path is not None else get_config_path()


def _read_config(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_config(path: Path, updates: dict) -> None:
    data = _read_config(path)
    if "UI_PRESETS" in updates:
        data["UI_PRESETS"] = updates["UI_PRESETS"]
    if "UI_LAST_PRESET" in updates:
        data["UI_LAST_PRESET"] = updates["UI_LAST_PRESET"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")


def _preset_from_dict(entry: object) -> Preset | None:
    if not isinstance(entry, dict):
        return None
    name = entry.get("name")
    profile = entry.get("profile")
    if not isinstance(name, str) or not name:
        return None
    if not isinstance(profile, str) or not profile:
        return None
    quick = entry.get("quick")
    production_safe = entry.get("production_safe")
    compare = entry.get("compare")
    if not isinstance(quick, bool):
        return None
    if not isinstance(production_safe, bool):
        return None
    if not isinstance(compare, bool):
        return None
    return Preset(name, profile, quick, production_safe, compare, False)


def _preset_to_dict(preset: Preset) -> dict:
    return {
        "name": preset.name,
        "profile": preset.profile,
        "quick": preset.quick,
        "production_safe": preset.production_safe,
        "compare": preset.compare,
    }


def _custom_presets_from_config(data: dict) -> list[Preset]:
    raw = data.get("UI_PRESETS", [])
    if not isinstance(raw, list):
        return []
    presets: list[Preset] = []
    for entry in raw:
        preset = _preset_from_dict(entry)
        if preset is None or preset.name in _BUILTIN_NAMES:
            continue
        presets.append(preset)
    return presets


def list_presets(config_path: Path | None = None) -> list[Preset]:
    path = _resolve_config_path(config_path)
    return list(BUILTINS) + _custom_presets_from_config(_read_config(path))


def get_preset(name: str, config_path: Path | None = None) -> Preset | None:
    for preset in BUILTINS:
        if preset.name == name:
            return preset
    path = _resolve_config_path(config_path)
    for preset in _custom_presets_from_config(_read_config(path)):
        if preset.name == name:
            return preset
    return None


def save_custom_preset(preset: Preset, config_path: Path | None = None) -> None:
    if not preset.name.strip():
        raise ValueError("Preset name cannot be empty")
    if preset.name in _BUILTIN_NAMES:
        raise ValueError(f"Cannot overwrite built-in preset: {preset.name}")

    path = _resolve_config_path(config_path)
    data = _read_config(path)
    raw = data.get("UI_PRESETS", [])
    if not isinstance(raw, list):
        raw = []

    saved = _preset_to_dict(preset)
    updated: list[dict] = []
    found = False
    for entry in raw:
        if isinstance(entry, dict) and entry.get("name") == preset.name:
            updated.append(saved)
            found = True
        else:
            updated.append(entry)
    if not found:
        updated.append(saved)

    _write_config(path, {"UI_PRESETS": updated})


def delete_custom_preset(name: str, config_path: Path | None = None) -> None:
    if name in _BUILTIN_NAMES:
        raise ValueError(f"Cannot delete built-in preset: {name}")

    path = _resolve_config_path(config_path)
    data = _read_config(path)
    raw = data.get("UI_PRESETS", [])
    if not isinstance(raw, list):
        raw = []

    filtered = [
        entry
        for entry in raw
        if not (isinstance(entry, dict) and entry.get("name") == name)
    ]
    _write_config(path, {"UI_PRESETS": filtered})


def get_last_preset_name(config_path: Path | None = None) -> str:
    path = _resolve_config_path(config_path)
    data = _read_config(path)
    name = data.get("UI_LAST_PRESET")
    if not isinstance(name, str) or not name:
        return DEFAULT_LAST_PRESET
    if get_preset(name, config_path=config_path) is None:
        return DEFAULT_LAST_PRESET
    return name


def set_last_preset_name(name: str, config_path: Path | None = None) -> None:
    path = _resolve_config_path(config_path)
    _write_config(path, {"UI_LAST_PRESET": name})
