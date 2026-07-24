# Phase 1 (#12 + #13) Implementation Plan

> **For agentic workers:** execute task-by-task. Issues: #12 then #13. Spec: `docs/superpowers/specs/2026-07-24-hostpulse-product-direction-design.md`

**Goal:** Versioned `AuditResult` JSON + client-sendable offline HTML report.

**Architecture:** Engine stamps `schema_version` / `engine_version` on every result; reporter consumes that contract and emits self-contained HTML (no CDN).

**Tech Stack:** Python, existing `bin/engine.py` + `bin/reporter_generator.py`, pytest.

## Global Constraints

- No `Co-authored-by: Cursor`
- Ponytail: no package rename, no GUI rewrite, no PDF
- Keep Windows production path; schema portable for Linux later
- TDD where practical; `.\scripts\verify_local.ps1` green before done

---

### Task 1: Schema module + engine stamp (#12)

**Files:**
- Create: `bin/schema.py`
- Modify: `bin/engine.py` (`_init_data_structure`, `save_results`)
- Modify: `tests/fixtures/minimal_audit.json`
- Create: `tests/test_schema.py`
- Create: `docs/SCHEMA.md` (short)

**Produces:** `SCHEMA_VERSION = 1`, `stamp_audit(data) -> data` with versions + documented keys.

- [ ] Failing tests for missing `schema_version` on new engine data / save payload
- [ ] Implement `bin/schema.py` + stamp in engine init/save
- [ ] Update fixture; add `docs/SCHEMA.md`
- [ ] `pytest -q` green; commit

### Task 2: Offline commercial HTML (#13)

**Files:**
- Modify: `bin/reporter_generator.py` (`render` + small helpers)
- Modify: `tests/test_reporter_smoke.py`, `tests/test_reporter_score.py`
- Create: `tests/test_reporter_offline.py`

**Produces:** HTML without `cdn.jsdelivr` / `fonts.googleapis`; header flags; grade legend; “How to read”; CPU chart via inline SVG or table fallback.

- [ ] Failing test: rendered HTML must not contain CDN hostnames
- [ ] Replace Chart.js/Google Fonts with inline CSS + SVG sparkline from `cpu_series`
- [ ] Add legend + how-to-read + quick/production_safe in header when present in meta
- [ ] `pytest -q` + manual open fixture HTML; commit

### Task 3: Close issues

- [ ] Comment + close #12 and #13 with evidence
- [ ] Push; CI green

---

**Execution:** inline in this session (user asked to start developing).
