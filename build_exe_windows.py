#!/usr/bin/env python3
"""Build EXE Windows da Linux/macOS tramite Docker (cdrx/pyinstaller-windows)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_docker(root: Path, image: str) -> subprocess.CompletedProcess:
    build_cmd = (
        ". /root/.bashrc && cd /src && "
        "python scripts/generate_version_info.py && "
        "python -m pip install --upgrade pip && "
        "pip install -r requirements.windows-build.txt && "
        "pyinstaller --clean -y --distpath ./dist/windows --workpath /tmp HostPulse.windows.spec && "
        "chown -R --reference=. ./dist/windows 2>/dev/null || true"
    )
    cmd = [
        "docker",
        "run",
        "--rm",
        "-e",
        "HOSTPULSE_EXE_NAME=HostPulse",
        "-v",
        f"{root}:/src/",
        "--entrypoint",
        "sh",
        image,
        "-c",
        build_cmd,
    ]
    print("> " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def main() -> int:
    if shutil.which("docker") is None:
        print("Docker non trovato nel PATH.", flush=True)
        return 1

    root = Path(__file__).resolve().parent
    os.chdir(root)

    subprocess.run([sys.executable, "scripts/generate_version_info.py"], check=True)

    preferred = os.environ.get("PYI_WIN_IMAGE", "").strip()
    images = [img for img in [preferred or None, "cdrx/pyinstaller-windows:python3", "cdrx/pyinstaller-windows"] if img]

    last: subprocess.CompletedProcess | None = None
    for image in images:
        print(f"Tentativo build con immagine: {image}", flush=True)
        proc = run_docker(root, image)
        last = proc
        if proc.stdout:
            print(proc.stdout, end="", flush=True)
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr, flush=True)
        if proc.returncode == 0:
            break
        merged = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if "pull access denied" in merged or "error from registry: denied" in merged:
            print(f"Immagine non accessibile: {image}", flush=True)
            continue
        return proc.returncode

    if last is None or last.returncode != 0:
        print("Build Docker fallita.", flush=True)
        return 1

    release_dir = root / "dist" / "windows" / "HostPulse"
    exe_path = release_dir / "HostPulse.exe"
    if not exe_path.is_file():
        print("EXE non trovato in dist/windows/HostPulse/. Contenuto dist/:", flush=True)
        dist = root / "dist"
        if dist.exists():
            for p in dist.rglob("*"):
                print(f"  {p.relative_to(root)}", flush=True)
        return 1

    cfg_dir = release_dir / "config"
    cfg_dir.mkdir(exist_ok=True)
    example = root / "config" / "config.example.json"
    target_cfg = cfg_dir / "config.json"
    if example.is_file():
        shutil.copy2(example, target_cfg)
    (release_dir / "results").mkdir(exist_ok=True)

    print(f"Build completata: {exe_path}", flush=True)
    print(f"Pacchetto distribuzione: {release_dir} (onedir + _internal/)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
