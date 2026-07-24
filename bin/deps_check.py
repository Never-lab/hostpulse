"""Explicit dependency check — no silent pip install."""
from __future__ import annotations

REQUIRED_PACKAGES = ["psutil", "customtkinter", "matplotlib", "seaborn", "pandas", "numpy"]


def missing_packages(packages: list[str] | None = None) -> list[str]:
    missing: list[str] = []
    for pkg in packages or REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def require_dependencies(*, frozen: bool = False) -> None:
    """Raise SystemExit with install hint if packages are missing (source runs only)."""
    if frozen:
        return
    missing = missing_packages()
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Missing Python packages: {names}\n"
            "Install with: pip install -r requirements.txt"
        )
