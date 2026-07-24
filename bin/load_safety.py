"""Guards for full-load runs on sensitive profiles."""
from __future__ import annotations

SENSITIVE_PROFILES = frozenset({"app_server", "db_server"})


def needs_full_load_confirm(profile: str, production_safe: bool) -> bool:
    """True when app/db profile is about to run without production-safe."""
    return profile in SENSITIVE_PROFILES and not production_safe


CLI_FULL_LOAD_WARN = (
    "WARNING: profile is Application/DB Server without --production-safe. "
    "Full load may stress the customer VM. Prefer --production-safe."
)
