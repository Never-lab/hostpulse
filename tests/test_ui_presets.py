# tests/test_ui_presets.py
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from ui.presets import (  # noqa: E402
    BUILTINS,
    ConfigCorruptError,
    DEFAULT_LAST_PRESET,
    Preset,
    delete_custom_preset,
    get_last_preset_name,
    get_preset,
    list_presets,
    save_custom_preset,
    set_last_preset_name,
)


def test_builtins_three() -> None:
    names = {p.name for p in BUILTINS}
    assert names == {"DB prod-safe", "App full", "Quick smoke"}
    db = get_preset("DB prod-safe")
    assert db is not None
    assert db.profile == "db_server" and db.production_safe is True and db.builtin is True


def test_custom_roundtrip(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")
    custom = Preset(
        name="Mio DB quick",
        profile="db_server",
        quick=True,
        production_safe=True,
        compare=False,
        builtin=False,
    )
    save_custom_preset(custom, config_path=cfg)
    listed = list_presets(config_path=cfg)
    assert any(p.name == "Mio DB quick" and p.quick for p in listed)
    set_last_preset_name("Mio DB quick", config_path=cfg)
    assert get_last_preset_name(config_path=cfg) == "Mio DB quick"
    delete_custom_preset("Mio DB quick", config_path=cfg)
    assert get_preset("Mio DB quick", config_path=cfg) is None


def test_cannot_delete_builtin(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        delete_custom_preset("DB prod-safe", config_path=cfg)


def test_builtin_name_wins_over_custom(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "UI_PRESETS": [
                    {
                        "name": "DB prod-safe",
                        "profile": "generic",
                        "quick": True,
                        "production_safe": False,
                        "compare": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    p = get_preset("DB prod-safe", config_path=cfg)
    assert p is not None
    assert p.profile == "db_server" and p.builtin is True


def test_corrupt_config_reads_degrade_to_builtins(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text("{not valid json", encoding="utf-8")

    assert [p.name for p in list_presets(config_path=cfg)] == [p.name for p in BUILTINS]
    assert get_preset("Nope", config_path=cfg) is None
    assert get_last_preset_name(config_path=cfg) == DEFAULT_LAST_PRESET


def test_corrupt_config_refuses_writes_and_keeps_file_untouched(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    original = "{not valid json"
    cfg.write_text(original, encoding="utf-8")

    custom = Preset(
        name="Nuovo preset",
        profile="generic",
        quick=False,
        production_safe=False,
        compare=False,
        builtin=False,
    )

    with pytest.raises(ConfigCorruptError):
        save_custom_preset(custom, config_path=cfg)
    assert cfg.read_text(encoding="utf-8") == original

    with pytest.raises(ConfigCorruptError):
        delete_custom_preset("Nuovo preset", config_path=cfg)
    assert cfg.read_text(encoding="utf-8") == original

    with pytest.raises(ConfigCorruptError):
        set_last_preset_name("Nuovo preset", config_path=cfg)
    assert cfg.read_text(encoding="utf-8") == original
