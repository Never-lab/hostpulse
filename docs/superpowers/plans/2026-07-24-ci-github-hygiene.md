# CI + GitHub hygiene Implementation Plan

> **For agentic workers:** execute task-by-task. Issues: #1 #5 #6 #7.

**Goal:** Minimal correct GitHub hygiene — LICENSE, smoke tests, CI on push, versioned releases.

**Architecture:** Flat `bin/` stays; tests use `PYTHONPATH=bin`. CI on Ubuntu + Windows. Release builds Windows EXE on tag `v*`.

**Tech Stack:** pytest, ruff, GitHub Actions, PyInstaller (release only), MIT license.

## Global Constraints

- No Co-authored-by Cursor in commits
- Ponytail: no extra frameworks, no package rename rewrite
- Windows-only probes must skip/xfail on Linux in tests
- Do not block on full product-direction phase 1

---

### Task 1: LICENSE + README (#1)
- [ ] Add MIT `LICENSE`
- [ ] README: License + CI badge placeholders

### Task 2: Dev deps + version (#5/#7 prep)
- [ ] `requirements-dev.txt` (pytest, ruff)
- [ ] `pyproject.toml` with version `0.1.0` + ruff config
- [ ] `bin/version.py` reading single source (or constant matching pyproject)

### Task 3: Smoke tests (#5)
- [ ] `tests/fixtures/minimal_audit.json`
- [ ] test app_paths (non-frozen)
- [ ] test engine `_init_data_structure` / config load from example
- [ ] test ReportGenerator.render() produces HTML without CDN requirement check later
- [ ] Run pytest green locally

### Task 4: CI workflow (#6)
- [ ] `.github/workflows/ci.yml` — push/PR: ruff + pytest, matrix ubuntu/windows
- [ ] README CI badge

### Task 5: Release (#7)
- [ ] `.github/workflows/release.yml` on `v*` tags → Windows build → zip asset
- [ ] README Download latest link

### Task 6: GitHub polish
- [ ] Dependabot for Actions
- [ ] Minimal PR template
- [ ] Push, verify Actions, close issues with comments
