from __future__ import annotations

from unittest.mock import MagicMock, patch

from engine import HostPulseEngine


def test_net_benchmark_pings_internet_then_gateway() -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    engine.plat = MagicMock()
    engine.plat.default_gateway.return_value = "10.0.0.1"
    engine.plat.ping_argv.side_effect = lambda host, count=6: ["ping", host]

    def fake_out(cmd, **_kwargs):
        host = cmd[-1]
        ms = "10.0" if host == "8.8.8.8" else "2.0"
        return f"64 bytes from {host}: icmp_seq=1 ttl=50 time={ms} ms\n" * 4

    with patch("engine.subprocess.check_output", side_effect=fake_out):
        engine.net_benchmark()

    net = engine.data["benchmark"]["net"]
    assert net["avg_ms"] == 10.0
    assert len(net["targets"]) == 2
    assert net["targets"][0]["role"] == "internet"
    assert net["targets"][0]["host"] == "8.8.8.8"
    assert net["targets"][0]["ok"] is True
    assert net["targets"][1]["role"] == "gateway"
    assert net["targets"][1]["host"] == "10.0.0.1"
    assert net["targets"][1]["avg_ms"] == 2.0
    assert engine.plat.ping_argv.call_count == 2


def test_net_benchmark_without_gateway_keeps_primary() -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    engine.plat = MagicMock()
    engine.plat.default_gateway.return_value = None
    engine.plat.ping_argv.return_value = ["ping", "8.8.8.8"]
    fake = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=50 time=12.0 ms\n" * 4
    with patch("engine.subprocess.check_output", return_value=fake):
        engine.net_benchmark()

    net = engine.data["benchmark"]["net"]
    assert len(net["targets"]) == 1
    assert net["avg_ms"] == 12.0
    codes = [e["code"] for e in engine.data["health"]["events"]]
    assert "NET_GATEWAY_UNKNOWN" in codes


def test_ping_targets_override_skips_auto_gateway() -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    engine.config["PING_TARGETS"] = ["1.1.1.1", "9.9.9.9"]
    engine.plat = MagicMock()
    engine.plat.default_gateway.return_value = "10.0.0.1"
    engine.plat.ping_argv.side_effect = lambda host, count=6: ["ping", host]
    fake = "64 bytes from x: icmp_seq=1 ttl=50 time=5.0 ms\n" * 4
    with patch("engine.subprocess.check_output", return_value=fake):
        engine.net_benchmark()

    hosts = [t["host"] for t in engine.data["benchmark"]["net"]["targets"]]
    assert hosts == ["1.1.1.1", "9.9.9.9"]
    engine.plat.default_gateway.assert_not_called()
