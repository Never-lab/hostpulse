"""AuditResult contract shared by engine, reporter, and on-disk JSON."""

from __future__ import annotations

from typing import Any

from version import __version__

# Bump when removing/renaming fields consumers rely on.
SCHEMA_VERSION = 1

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "engine_version",
    "meta",
    "sys_info",
    "virtualization",
    "ram_hw",
    "disk_hw",
    "health",
    "benchmark",
    "app_server",
)


def stamp_audit(data: dict[str, Any], *, quick: bool = False, production_safe: bool = False) -> dict[str, Any]:
    """Attach schema/engine versions and run-mode flags. Mutates and returns ``data``."""
    data["schema_version"] = SCHEMA_VERSION
    data["engine_version"] = __version__
    meta = data.setdefault("meta", {})
    meta["quick"] = bool(quick)
    meta["production_safe"] = bool(production_safe)
    return data
