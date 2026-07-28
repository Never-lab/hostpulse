from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_build_linux_script_exists() -> None:
    assert (ROOT / "build_linux.sh").is_file()


def test_hostpulse_launcher_exists() -> None:
    launcher = ROOT / "scripts" / "hostpulse.sh"
    assert launcher.is_file()
    text = launcher.read_text(encoding="utf-8")
    assert "bin/cli.py" in text
    assert "production-safe" in text


def test_build_linux_produces_package() -> None:
    """Run build_linux.sh and assert layout (uses real dist/ under repo)."""
    import subprocess

    subprocess.run(["bash", "-n", str(ROOT / "scripts" / "hostpulse.sh")], check=True)
    subprocess.run(["bash", "-n", str(ROOT / "build_linux.sh")], check=True)
    subprocess.run(["bash", str(ROOT / "build_linux.sh")], cwd=ROOT, check=True)

    pkg = ROOT / "dist" / "linux" / "HostPulse"
    assert (pkg / "hostpulse.sh").is_file()
    assert (pkg / "bin" / "cli.py").is_file()
    assert (pkg / "config" / "config.json").is_file()
    assert (pkg / "requirements.txt").is_file()
    assert (ROOT / "dist" / "HostPulse-linux.zip").is_file()
