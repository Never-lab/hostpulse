# HostPulse — hardware/OS benchmark & commercial report

[![CI](https://github.com/Never-lab/hostpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Never-lab/hostpulse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Download latest](https://img.shields.io/github/v/release/Never-lab/hostpulse?label=Download%20latest)](https://github.com/Never-lab/hostpulse/releases/latest)

HostPulse benchmarks a customer VM/host and produces an **offline HTML report** (optional PDF) you can send as a deliverable — plus a live GUI for on-site diagnosis.

## Quickstart

```bash
pip install -r requirements.txt
python bin/ui_benchmark.py
# headless:
python bin/cli.py run --quick --production-safe --out report.html
```

Download ready-made packages from [Releases](https://github.com/Never-lab/hostpulse/releases/latest):

- **Windows** — `HostPulse-windows.zip` (EXE + `config/` + `results/`)
- **Linux** — `HostPulse-linux.zip` (`hostpulse.sh` launcher; first run creates a local `.venv` — needs Python 3.10+ and `python3-venv` on Debian/Ubuntu)

## What it measures

- **CPU** — consistency/jitter, crypto hash rate, compression
- **RAM** — usage, swap, copy-bandwidth estimate (+ MHz speed on Windows)
- **Disk** — sequential throughput, IOPS/latency (`DISK_TEST_PATH` configurable)
- **Network** — ping latency/jitter to a configurable target
- **Chaos** — IOPS impact under CPU load (skipped in production-safe mode)

Profiles: `generic` · `app_server` · `db_server`. Independent flags: `--quick`, `--production-safe`.

## Report

The report includes a health score, plain-language summary, metrics table, and recommendations — opens offline with no CDN.

```text
HostPulse Report · hostname · profile=db_server · production-safe
Health Score  B  ·  VM detected · disk latency OK
…
```

GUI flow: start audit → live log → **Open report** / **Export PDF**.

## Dependencies & development

`pip install -r requirements.txt`  
(missing packages at GUI startup exit with a clear message — no silent `pip install`).

Dev / CI: `pip install -r requirements.txt -r requirements-dev.txt`, then `pytest -q` and `ruff check bin tests`.

Local verify (Windows): `.\scripts\verify_local.ps1`  
With EXE build: `.\scripts\verify_local.ps1 -BuildExe`  
Local verify (Linux / WSL): `./scripts/verify_local.sh`  
With Linux package smoke: `BUILD_LINUX=1 ./scripts/verify_local.sh`

## Config

Copy `config/config.example.json` → `config/config.json` and tune profile / thresholds.

- `PROFILE`: `generic` | `app_server` | `db_server`
- `PRODUCTION_SAFE`: lower load on production VMs

More: [DEPLOY.md](DEPLOY.md) · [docs/SCHEMA.md](docs/SCHEMA.md) · [docs/PLATFORM.md](docs/PLATFORM.md) · [CHANGELOG](CHANGELOG.md).

## Architecture map (for humans & AI)

A **graphify** knowledge graph of this repo lives in [`docs/graphify/`](docs/graphify/). Use it to navigate modules, ask “what calls what?”, and onboard coding agents in forks — see [`docs/graphify/README.md`](docs/graphify/README.md).

## Build release packages

**Windows EXE** — from Windows: `.\build_exe.ps1`  
From Linux (Docker): `python build_exe_windows.py`  
Output: `dist/windows/HostPulse/` (`HostPulse.exe` + `config/` + `results/`).

**Linux client** — from Linux / WSL: `./build_linux.sh`  
Output: `dist/linux/HostPulse/` + `dist/HostPulse-linux.zip` (`hostpulse.sh` + `bin/` + `config/` + `results/`).

On the customer VM (Linux):

```bash
unzip HostPulse-linux.zip && cd HostPulse
./hostpulse.sh run --quick --production-safe --out results/report.html
# first run bootstraps .venv/ automatically
# GUI when a display is available:
./hostpulse.sh gui
```

GitHub Release: tag `vX.Y.Z` → Actions uploads `HostPulse-windows.zip` and `HostPulse-linux.zip` to [Releases](https://github.com/Never-lab/hostpulse/releases/latest).

## Contributors

Thanks to everyone who ships HostPulse.

| | |
|---|---|
| [@Never-lab](https://github.com/Never-lab) (JustKaneki) | Maintainer — product direction, engine, report, releases |

Want to help? See [CONTRIBUTING.md](CONTRIBUTING.md).

1. Read [docs/graphify/](docs/graphify/) so agents (and you) share the same map of the codebase
2. Open an issue or PR against `main`
3. Keep commits in English; chat/docs may be Italian or English
4. Do **not** add `Co-authored-by: Cursor` (or similar) trailers

Contributions of tests, Linux adapter gaps, report polish, and docs are especially welcome.

## License

MIT — see [LICENSE](LICENSE).
