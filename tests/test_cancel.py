from __future__ import annotations

from threading import Event

import pytest

from cancel import AuditCancelled, check_cancel


def test_check_cancel_noop_without_event() -> None:
    check_cancel(None)


def test_check_cancel_raises_when_set() -> None:
    ev = Event()
    ev.set()
    with pytest.raises(AuditCancelled):
        check_cancel(ev, "stop")
