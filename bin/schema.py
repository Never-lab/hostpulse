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

REQUIRED_META_KEYS = (
    "hostname",
    "date",
    "timestamp",
    "is_admin",
    "profile",
    "quick",
    "production_safe",
)

REQUIRED_BENCHMARK_KEYS = (
    "cpu_consistency",
    "cpu_real",
    "cpu_series",
    "disk",
    "ram_perf",
    "net",
    "chaos",
)

REQUIRED_DISK_KEYS = (
    "seq_write_mb",
    "seq_read_mb",
    "iops",
    "latency_p99_ms",
    "db_sim_latency_ms",
)

REQUIRED_CHAOS_KEYS = (
    "active",
    "disk_iops_under_load",
    "impact_pct",
)

REQUIRED_HEALTH_EVENT_KEYS = (
    "level",
    "code",
    "message",
    "timestamp",
)


def missing_structure(data: dict[str, Any]) -> list[str]:
    """Return dotted paths missing from a structural AuditResult (v1)."""
    missing: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            missing.append(key)

    meta = data.get("meta")
    if isinstance(meta, dict):
        for key in REQUIRED_META_KEYS:
            if key not in meta:
                missing.append(f"meta.{key}")
    elif "meta" in data:
        missing.append("meta")

    health = data.get("health")
    if isinstance(health, dict):
        if "events" not in health or not isinstance(health["events"], list):
            missing.append("health.events")
        else:
            for i, event in enumerate(health["events"]):
                if not isinstance(event, dict):
                    missing.append(f"health.events[{i}]")
                    continue
                for key in REQUIRED_HEALTH_EVENT_KEYS:
                    if key not in event:
                        missing.append(f"health.events[{i}].{key}")
    elif "health" in data:
        missing.append("health")

    benchmark = data.get("benchmark")
    if isinstance(benchmark, dict):
        for key in REQUIRED_BENCHMARK_KEYS:
            if key not in benchmark:
                missing.append(f"benchmark.{key}")
        disk = benchmark.get("disk")
        if isinstance(disk, dict):
            for key in REQUIRED_DISK_KEYS:
                if key not in disk:
                    missing.append(f"benchmark.disk.{key}")
        elif "disk" in benchmark:
            missing.append("benchmark.disk")
        chaos = benchmark.get("chaos")
        if isinstance(chaos, dict):
            for key in REQUIRED_CHAOS_KEYS:
                if key not in chaos:
                    missing.append(f"benchmark.chaos.{key}")
        elif "chaos" in benchmark:
            missing.append("benchmark.chaos")
    elif "benchmark" in data:
        missing.append("benchmark")

    if "app_server" in data:
        app = data["app_server"]
        if not isinstance(app, dict) or "ports" not in app or not isinstance(app["ports"], dict):
            missing.append("app_server.ports")

    return missing


def stamp_audit(data: dict[str, Any], *, quick: bool = False, production_safe: bool = False) -> dict[str, Any]:
    """Attach schema/engine versions and run-mode flags. Mutates and returns ``data``."""
    data["schema_version"] = SCHEMA_VERSION
    data["engine_version"] = __version__
    meta = data.setdefault("meta", {})
    meta["quick"] = bool(quick)
    meta["production_safe"] = bool(production_safe)
    return data
