# Changelog

## Unreleased

- Live GUI: Setup → Live → Done shell, report-aligned dark theme, Never-lab presets (+ custom in config)
- Report HTML: layout commerciale (hero, score ring, KPI con stato, metriche raggruppate)
- Grafico CPU: assi etichettati, griglia 0–100%, media/picco/min, pannello MHz separato
- Windows EXE: onedir (no UPX), version resource, SHA256.txt, firma Authenticode opzionale — [docs/WINDOWS_AV.md](docs/WINDOWS_AV.md)

## 0.1.2 — Linux venv bootstrap (PEP 668)

- Linux `hostpulse.sh`: auto-bootstrap local `.venv` on first run (Debian/Ubuntu externally-managed-environment)

## 0.1.1 — Linux client package + dual-asset release

- Linux client package: `hostpulse.sh` launcher + `build_linux.sh` → `HostPulse-linux.zip`
- Release workflow publishes both Windows EXE and Linux zip on tag `v*`
- `scripts/verify_local.sh` for Linux/WSL; CI smoke on Ubuntu

## 0.1.0 — first public release

- Commercial offline HTML report + optional PDF (Edge/Chrome headless)
- Versioned `AuditResult` schema (`schema_version` / `engine_version`)
- GUI (CustomTkinter) + headless CLI (`python bin/cli.py run …`)
- Cooperative cancel, production-safe / quick modes, app/db profiles
- Platform adapters: Windows production path, Linux best-effort (`docs/PLATFORM.md`)
- CI, Dependabot, Windows EXE release asset via tag `v*`
