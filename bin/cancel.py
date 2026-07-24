"""Cooperative cancel for long-running audits."""

from __future__ import annotations

from typing import Optional
from threading import Event


class AuditCancelled(Exception):
    """Raised when the user/CLI requests stop between or inside audit phases."""


def check_cancel(event: Optional[Event], message: str = "Audit cancelled") -> None:
    if event is not None and event.is_set():
        raise AuditCancelled(message)
