"""OS adapters — Windows production path, Linux best-effort.

PowerShell / WMI / ctypes live only here. Engine calls get_adapter().
"""
from __future__ import annotations

import os
import platform
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class InfraSnapshot:
    """Platform-specific infra fields. None = unsupported / unknown."""

    elevated: bool = False
    power_plan: str | None = None
    numa_nodes: int | None = None
    cpu_queue_length: float | None = None
    ctx_switches_sec: float | None = None
    ram_speed_mhz: int | None = None
    is_vm: bool = False
    hypervisor: str | None = None
    # (health_code, message) for INFO/WARN when a capability is N/A
    gaps: list[tuple[str, str]] = field(default_factory=list)


class PlatformAdapter(Protocol):
    name: str

    def is_elevated(self) -> bool: ...

    def collect_infra(self) -> InfraSnapshot: ...

    def ping_argv(self, target: str, count: int = 6) -> list[str]: ...


def get_adapter() -> PlatformAdapter:
    system = platform.system().lower()
    if system == "windows":
        return WindowsAdapter()
    if system == "linux":
        return LinuxAdapter()
    return GenericAdapter(system)


# --- Windows -----------------------------------------------------------------


class WindowsAdapter:
    name = "windows"

    def is_elevated(self) -> bool:
        return self._is_elevated()

    def collect_infra(self) -> InfraSnapshot:
        snap = InfraSnapshot(elevated=self.is_elevated())
        plan = self._run_ps(
            "(powercfg /GETACTIVESCHEME) -match '\\((.+)\\)' | Out-Null; $matches[1]"
        )
        if plan:
            snap.power_plan = plan.strip()

        numa_raw = self._run_ps("(Get-WmiObject -Class Win32_NumaNode | Measure-Object).Count")
        if numa_raw and numa_raw.strip().isdigit():
            snap.numa_nodes = int(numa_raw.strip())

        qlen_raw = self._run_ps(
            "(Get-Counter '\\\\System\\\\Processor Queue Length').CounterSamples[0].CookedValue"
        )
        if qlen_raw is not None:
            try:
                snap.cpu_queue_length = float(qlen_raw)
            except ValueError:
                pass

        ctx_raw = self._run_ps(
            "(Get-Counter '\\\\System\\\\Context Switches/sec').CounterSamples[0].CookedValue"
        )
        if ctx_raw is not None:
            try:
                snap.ctx_switches_sec = float(ctx_raw)
            except ValueError:
                pass

        snap.ram_speed_mhz = self._ram_speed()

        release = platform.uname().release.lower()
        if "microsoft" in release or "hyper-v" in release:
            snap.is_vm = True
            snap.hypervisor = "Hyper-V/WSL"

        mfr = self._run_ps("(Get-WmiObject Win32_ComputerSystem).Manufacturer")
        if mfr and any(x in mfr.lower() for x in ("vmware", "qemu", "kvm", "xen", "microsoft", "virtual")):
            snap.is_vm = True
            snap.hypervisor = (snap.hypervisor or mfr.strip())

        return snap

    def ping_argv(self, target: str, count: int = 6) -> list[str]:
        return ["ping", "-n", str(count), "-w", "1000", target]

    @staticmethod
    def _is_elevated() -> bool:
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
        except Exception:
            return False

    @staticmethod
    def _run_ps(cmd: str) -> str | None:
        try:
            full = f'powershell -NoProfile -Command "{cmd}"'
            return subprocess.check_output(
                full, shell=True, text=True, stderr=subprocess.STDOUT, timeout=5
            ).strip()
        except Exception:
            return None

    def _ram_speed(self) -> int | None:
        try:
            ps_out = self._run_ps(
                "(Get-CimInstance Win32_PhysicalMemory | "
                "Where-Object { $_.Speed -gt 0 } | "
                "Measure-Object -Property Speed -Maximum).Maximum"
            )
            if ps_out and ps_out.strip().isdigit():
                return int(ps_out.strip())
            wmic = subprocess.run(
                "wmic memorychip get speed",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            speeds = [int(s) for s in wmic.stdout.split() if s.isdigit() and int(s) > 0]
            return max(speeds) if speeds else None
        except Exception:
            return None


# --- Linux -------------------------------------------------------------------


class LinuxAdapter:
    name = "linux"

    def is_elevated(self) -> bool:
        return os.geteuid() == 0

    def collect_infra(self) -> InfraSnapshot:
        snap = InfraSnapshot(elevated=self.is_elevated())
        snap.power_plan = self._cpu_governor()
        if snap.power_plan is None:
            snap.gaps.append(
                (
                    "PLATFORM_POWER_PLAN_NA",
                    "Piano energetico / governor CPU non disponibile su questo host Linux.",
                )
            )

        snap.numa_nodes = self._numa_nodes()
        snap.cpu_queue_length = None  # no stable portable equivalent of Processor Queue Length
        snap.gaps.append(
            (
                "PLATFORM_CPU_QUEUE_NA",
                "Processor Queue Length non supportato su Linux (metrica N/A).",
            )
        )

        snap.ctx_switches_sec = self._ctx_switches_approx()
        if snap.ctx_switches_sec is None:
            snap.gaps.append(
                (
                    "PLATFORM_CTX_SWITCHES_NA",
                    "Context switches/sec non disponibili (/proc).",
                )
            )

        snap.ram_speed_mhz = None
        snap.gaps.append(
            (
                "PLATFORM_RAM_SPEED_NA",
                "Velocità RAM (MHz) non esposta in modo affidabile su Linux (metrica N/A).",
            )
        )

        is_vm, hyper = self._detect_vm()
        snap.is_vm = is_vm
        snap.hypervisor = hyper
        return snap

    def ping_argv(self, target: str, count: int = 6) -> list[str]:
        return ["ping", "-c", str(count), "-W", "1", target]

    @staticmethod
    def _cpu_governor() -> str | None:
        roots = Path("/sys/devices/system/cpu")
        if not roots.is_dir():
            return None
        governors: list[str] = []
        for gov in roots.glob("cpu[0-9]*/cpufreq/scaling_governor"):
            try:
                governors.append(gov.read_text(encoding="utf-8").strip())
            except OSError:
                continue
        if not governors:
            return None
        # Most common governor label
        return max(set(governors), key=governors.count)

    @staticmethod
    def _numa_nodes() -> int | None:
        node_dir = Path("/sys/devices/system/node")
        if not node_dir.is_dir():
            return None
        nodes = list(node_dir.glob("node[0-9]*"))
        return len(nodes) if nodes else None

    @staticmethod
    def _ctx_switches_approx() -> float | None:
        """Two-sample /proc/stat ctxt delta over ~0.2s."""
        import time

        def read_ctxt() -> int | None:
            try:
                text = Path("/proc/stat").read_text(encoding="utf-8")
            except OSError:
                return None
            for line in text.splitlines():
                if line.startswith("ctxt "):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1])
            return None

        a = read_ctxt()
        if a is None:
            return None
        time.sleep(0.2)
        b = read_ctxt()
        if b is None or b < a:
            return None
        return (b - a) / 0.2

    @staticmethod
    def _detect_vm() -> tuple[bool, str | None]:
        try:
            out = subprocess.check_output(
                ["systemd-detect-virt"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=2,
            ).strip()
            if out and out != "none":
                return True, out
        except Exception:
            pass

        for path in (Path("/sys/class/dmi/id/sys_vendor"), Path("/sys/class/dmi/id/product_name")):
            try:
                val = path.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            low = val.lower()
            if any(x in low for x in ("vmware", "qemu", "kvm", "xen", "virtualbox", "microsoft", "bochs")):
                return True, val
        return False, None


# --- Other OS ----------------------------------------------------------------


class GenericAdapter:
    def __init__(self, system: str) -> None:
        self.name = system or "unknown"

    def is_elevated(self) -> bool:
        return False

    def collect_infra(self) -> InfraSnapshot:
        return InfraSnapshot(
            elevated=False,
            gaps=[
                (
                    "PLATFORM_UNSUPPORTED",
                    f"OS '{self.name}' non supportato: metriche infrastrutturali N/A.",
                )
            ],
        )

    def ping_argv(self, target: str, count: int = 6) -> list[str]:
        # Best-effort BSD/mac style
        return ["ping", "-c", str(count), target]


_PING_MS_RE = re.compile(r"(?:time|tempo|durata)\s*[=<]\s*<?\s*(\d+(?:\.\d+)?)", re.I)


def parse_ping_latencies_ms(output: str) -> list[float]:
    """Extract latency ms from ping stdout (Windows/Linux locales)."""
    out: list[float] = []
    for line in output.splitlines():
        m = _PING_MS_RE.search(line)
        if m:
            out.append(float(m.group(1)))
    return out
