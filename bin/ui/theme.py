"""Dark UI tokens aligned to commercial HTML report CSS / STATUS_COLORS."""

from __future__ import annotations

# Keep in sync with bin/reporter_generator.py STATUS_COLORS + :root --brand/--accent
COLORS: dict[str, str] = {
    "bg": "#0f172a",
    "card": "#1e293b",
    "ink": "#f8fafc",
    "muted": "#94a3b8",
    "border": "#334155",
    "brand": "#0c4a6e",
    "accent": "#0284c7",
    "ok": "#16a34a",
    "warn": "#d97706",
    "crit": "#dc2626",
}


def status_color(status: str) -> str:
    return {
        "ok": COLORS["ok"],
        "warn": COLORS["warn"],
        "crit": COLORS["crit"],
        "info": COLORS["accent"],
        "na": COLORS["muted"],
    }.get(status, COLORS["muted"])


def apply_appearance() -> None:
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    # Do NOT call set_default_color_theme("green")
