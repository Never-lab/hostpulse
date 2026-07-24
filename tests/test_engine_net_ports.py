from __future__ import annotations

from unittest.mock import MagicMock, patch

from engine import HostPulseEngine, _PING_LATENCY_RE


def test_ping_latency_regex_english_and_italian() -> None:
    samples = [
        "Reply from 8.8.8.8: bytes=32 time=12ms TTL=117",
        "Risposta da 8.8.8.8: byte=32 durata=8ms TTL=54",
        "time=4ms",
        "tempo=15 ms",
    ]
    times = []
    for line in samples:
        m = _PING_LATENCY_RE.search(line)
        assert m, line
        times.append(int(m.group(1)))
    assert times == [12, 8, 4, 15]


def test_check_app_port_open_and_closed() -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)

    with patch("engine.socket.socket") as sock_cls:
        sock = MagicMock()
        sock_cls.return_value.__enter__.return_value = sock
        sock.connect.return_value = None
        engine.check_app_port(8080)
        assert engine.data["app_server"]["ports"]["8080"] is True

    engine2 = HostPulseEngine(quick=True, production_safe=True)
    with patch("engine.socket.socket") as sock_cls:
        sock = MagicMock()
        sock_cls.return_value.__enter__.return_value = sock
        sock.connect.side_effect = ConnectionRefusedError()
        engine2.check_app_port(9999)
        assert engine2.data["app_server"]["ports"]["9999"] is False
        codes = [e["code"] for e in engine2.data["health"]["events"]]
        assert "APP_PORT_CLOSED" in codes


def test_check_app_port_noop_without_config() -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    engine.config["APP_PORT_CHECK"] = None
    engine.check_app_port()
    assert engine.data["app_server"]["ports"] == {}
