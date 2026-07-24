"""Platform adapters (#15)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))


def test_engine_has_no_windows_only_apis() -> None:
    src = (BIN / "engine.py").read_text(encoding="utf-8")
    assert "powershell" not in src.lower()
    assert "ctypes" not in src
    assert "wmic" not in src.lower()
    assert "IsUserAnAdmin" not in src
    assert "from plat import" in src


def test_get_adapter_windows() -> None:
    import plat

    with patch.object(plat.platform, "system", return_value="Windows"):
        ad = plat.get_adapter()
    assert ad.name == "windows"
    assert ad.ping_argv("1.1.1.1") == ["ping", "-n", "6", "-w", "1000", "1.1.1.1"]


def test_get_adapter_linux() -> None:
    import plat

    with patch.object(plat.platform, "system", return_value="Linux"):
        ad = plat.get_adapter()
    assert ad.name == "linux"
    assert ad.ping_argv("1.1.1.1")[1] == "-c"


def test_linux_collect_infra_emits_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    import plat

    monkeypatch.setattr(plat.LinuxAdapter, "is_elevated", lambda self: False)
    monkeypatch.setattr(plat.LinuxAdapter, "_cpu_governor", staticmethod(lambda: None))
    monkeypatch.setattr(plat.LinuxAdapter, "_numa_nodes", staticmethod(lambda: None))
    monkeypatch.setattr(plat.LinuxAdapter, "_ctx_switches_approx", staticmethod(lambda: None))
    monkeypatch.setattr(plat.LinuxAdapter, "_detect_vm", staticmethod(lambda: (False, None)))

    snap = plat.LinuxAdapter().collect_infra()
    codes = [c for c, _ in snap.gaps]
    assert "PLATFORM_RAM_SPEED_NA" in codes
    assert "PLATFORM_CPU_QUEUE_NA" in codes
    assert snap.ram_speed_mhz is None
    assert snap.elevated is False


def test_parse_ping_latencies() -> None:
    from plat import parse_ping_latencies_ms

    text = "\n".join(
        [
            "Reply from 8.8.8.8: bytes=32 time=12ms TTL=117",
            "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=8.42 ms",
            "tempo=15 ms",
        ]
    )
    assert parse_ping_latencies_ms(text) == [12.0, 8.42, 15.0]


def test_net_benchmark_uses_adapter_ping() -> None:
    from engine import HostPulseEngine

    engine = HostPulseEngine(quick=True, production_safe=True)
    engine.plat = MagicMock()
    engine.plat.ping_argv.return_value = ["ping", "-c", "6", "8.8.8.8"]
    fake = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=50 time=10.0 ms\n" * 4
    with patch("engine.subprocess.check_output", return_value=fake):
        engine.net_benchmark()
    engine.plat.ping_argv.assert_called_once()
    assert engine.data["benchmark"]["net"]["avg_ms"] == 10.0
