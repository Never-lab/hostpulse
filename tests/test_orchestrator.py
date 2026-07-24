from __future__ import annotations

from threading import Event

import pytest

from cancel import AuditCancelled
from orchestrator import run_audit


def test_run_audit_respects_cancel(tmp_path, monkeypatch) -> None:
    # Point engine paths at tmp via monkeypatch of app_paths used inside engine init
    from app_paths import get_app_base_dir

    root = get_app_base_dir()
    ev = Event()
    ev.set()
    with pytest.raises(AuditCancelled):
        run_audit(
            root_dir=str(root),
            bin_dir=str(tmp_path),
            quick=True,
            production_safe=True,
            export_slides=False,
            cancel_event=ev,
        )
