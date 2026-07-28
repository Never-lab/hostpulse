# Changelog

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
