# Live Shell UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dense CustomTkinter form with a modular Setup → Live → Done shell that matches the commercial report palette, exposes Never-lab presets (+ custom save), and shows grade/score on Done before opening HTML.

**Architecture:** New `bin/ui/` package (theme, presets, app state machine, three screens). Thin `bin/ui_benchmark.py` entry. Extend `AuditResultPaths` so Done consumes score from `ReportGenerator.overall` without a second scoring path. Config gains additive `UI_PRESETS` / `UI_LAST_PRESET` only.

**Tech Stack:** Python 3.12, CustomTkinter, existing `orchestrator.run_audit` / `cancel` / `pdf_export`, pytest, PyInstaller `HostPulse.windows.spec`.

## Global Constraints

- Keep CustomTkinter + `run_audit` / cooperative cancel / PDF — no web/.NET
- Italian UI copy for technicians
- Dark theme only (v1); no `ctk.set_default_color_theme("green")`
- Palette tokens must match report: bg `#0f172a`, card `#1e293b`, ink `#f8fafc`, muted `#94a3b8`, border `#334155`, brand `#0c4a6e`, accent `#0284c7`, ok `#16a34a`, warn `#d97706`, crit `#dc2626`
- Built-in presets: `DB prod-safe`, `App full`, `Quick smoke` (not deletable)
- Additive config keys only; do not break engine keys
- No `Co-authored-by: Cursor` in commits
- Piece-check: GUI starts; Start enabled; `python -m pytest -q` green; update spec hiddenimports if packaging touched
- Spec source of truth: `docs/superpowers/specs/2026-08-02-live-shell-ui-design.md`

## File map

| Path | Role |
|------|------|
| `bin/ui/__init__.py` | Package marker (empty or version note) |
| `bin/ui/theme.py` | Color/font tokens + helpers for CTk kwargs |
| `bin/ui/presets.py` | Builtin + load/save custom presets |
| `bin/ui/app.py` | `AuditApp` root + state machine |
| `bin/ui/screens/__init__.py` | Re-exports |
| `bin/ui/screens/setup.py` | Setup frame |
| `bin/ui/screens/live.py` | Live frame |
| `bin/ui/screens/done.py` | Done frame |
| `bin/ui_benchmark.py` | Entry only: deps → `AuditApp.mainloop` |
| `bin/orchestrator.py` | Extend `AuditResultPaths` + populate fields |
| `config/config.example.json` | Document `UI_*` keys |
| `HostPulse.windows.spec` | `hiddenimports` for `ui.*` |
| `tests/test_ui_theme.py` | Token smoke |
| `tests/test_ui_presets.py` | Preset roundtrip |
| `tests/test_orchestrator.py` | Assert new path fields when mocked/completed |
| `tests/test_imports.py` | Add `ui` / `ui.presets` / `ui.theme` |

---

### Task 1: Theme tokens

**Files:**
- Create: `bin/ui/__init__.py`
- Create: `bin/ui/theme.py`
- Create: `tests/test_ui_theme.py`
- Modify: `tests/test_imports.py` (add `ui`, `ui.theme`)

**Interfaces:**
- Produces: `COLORS: dict[str, str]`, `status_color(status: str) -> str`, `apply_appearance() -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_theme.py
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from ui.theme import COLORS, status_color  # noqa: E402


def test_colors_match_report_palette() -> None:
    assert COLORS["bg"] == "#0f172a"
    assert COLORS["accent"] == "#0284c7"
    assert COLORS["brand"] == "#0c4a6e"
    assert COLORS["ok"] == "#16a34a"
    assert COLORS["warn"] == "#d97706"
    assert COLORS["crit"] == "#dc2626"


def test_status_color_maps() -> None:
    assert status_color("ok") == COLORS["ok"]
    assert status_color("warn") == COLORS["warn"]
    assert status_color("crit") == COLORS["crit"]
    assert status_color("na") == COLORS["muted"]
    assert status_color("unknown") == COLORS["muted"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui_theme.py -v`  
Expected: FAIL (import error / module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# bin/ui/__init__.py
"""HostPulse live shell UI package."""

# bin/ui/theme.py
"""Dark UI tokens aligned to commercial HTML report CSS / STATUS_COLORS."""

from __future__ import annotations

# Keep in sync with bin/reporter_generator.py STATUS_COLORS + :root --brand/--accent
COLORS: dict[str, str] = {
    "bg": "#0f172a",
    "card": "#1e293b",
    "ink": "#f8fafc",
    "muted": "#94a3b8",
    "border": "#334155",
    "brand": "#0c4a6e",
    "accent": "#0284c7",
    "ok": "#16a34a",
    "warn": "#d97706",
    "crit": "#dc2626",
}


def status_color(status: str) -> str:
    return {
        "ok": COLORS["ok"],
        "warn": COLORS["warn"],
        "crit": COLORS["crit"],
        "info": COLORS["accent"],
        "na": COLORS["muted"],
    }.get(status, COLORS["muted"])


def apply_appearance() -> None:
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    # Do NOT call set_default_color_theme("green")
```

Add `"ui"` and `"ui.theme"` to the parametrize list in `tests/test_imports.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ui_theme.py tests/test_imports.py -q`  
Expected: PASS (imports that need CTk may still pass for `ui.theme`)

- [ ] **Step 5: Commit**

```bash
git add bin/ui/__init__.py bin/ui/theme.py tests/test_ui_theme.py tests/test_imports.py
git commit -m "Add UI theme tokens aligned to the HTML report."
```

---

### Task 2: Preset store

**Files:**
- Create: `bin/ui/presets.py`
- Create: `tests/test_ui_presets.py`
- Modify: `config/config.example.json`
- Modify: `tests/test_imports.py` (add `ui.presets`)

**Interfaces:**
- Consumes: `app_paths.get_config_path`
- Produces:
  - `@dataclass Preset`: `name: str`, `profile: str`, `quick: bool`, `production_safe: bool`, `compare: bool`, `builtin: bool`
  - `BUILTINS: list[Preset]`
  - `list_presets(config_path: Path | None = None) -> list[Preset]`
  - `get_preset(name: str, config_path: Path | None = None) -> Preset | None`
  - `save_custom_preset(preset: Preset, config_path: Path | None = None) -> None`
  - `delete_custom_preset(name: str, config_path: Path | None = None) -> None`
  - `get_last_preset_name(config_path: Path | None = None) -> str`
  - `set_last_preset_name(name: str, config_path: Path | None = None) -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_presets.py
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from ui.presets import (  # noqa: E402
    BUILTINS,
    Preset,
    delete_custom_preset,
    get_last_preset_name,
    get_preset,
    list_presets,
    save_custom_preset,
    set_last_preset_name,
)


def test_builtins_three() -> None:
    names = {p.name for p in BUILTINS}
    assert names == {"DB prod-safe", "App full", "Quick smoke"}
    db = get_preset("DB prod-safe")
    assert db is not None
    assert db.profile == "db_server" and db.production_safe is True and db.builtin is True


def test_custom_roundtrip(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")
    custom = Preset(
        name="Mio DB quick",
        profile="db_server",
        quick=True,
        production_safe=True,
        compare=False,
        builtin=False,
    )
    save_custom_preset(custom, config_path=cfg)
    listed = list_presets(config_path=cfg)
    assert any(p.name == "Mio DB quick" and p.quick for p in listed)
    set_last_preset_name("Mio DB quick", config_path=cfg)
    assert get_last_preset_name(config_path=cfg) == "Mio DB quick"
    delete_custom_preset("Mio DB quick", config_path=cfg)
    assert get_preset("Mio DB quick", config_path=cfg) is None


def test_cannot_delete_builtin(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        delete_custom_preset("DB prod-safe", config_path=cfg)


def test_builtin_name_wins_over_custom(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "UI_PRESETS": [
                    {
                        "name": "DB prod-safe",
                        "profile": "generic",
                        "quick": True,
                        "production_safe": False,
                        "compare": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    p = get_preset("DB prod-safe", config_path=cfg)
    assert p is not None
    assert p.profile == "db_server" and p.builtin is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui_presets.py -v`  
Expected: FAIL (module missing)

- [ ] **Step 3: Write minimal implementation**

Implement `bin/ui/presets.py`:

- `BUILTINS` exactly as spec table
- `_read_config(path) -> dict` / `_write_config(path, data)` merge — load JSON object, update only `UI_PRESETS` / `UI_LAST_PRESET`, preserve other keys
- `list_presets`: builtins first, then custom whose names are not in builtin set; skip corrupt entries (missing name/profile or bad types)
- `save_custom_preset`: reject empty name; reject if name matches a builtin; upsert by name in `UI_PRESETS`
- `delete_custom_preset`: raise `ValueError` if builtin; else remove from list
- Default `config_path` = `get_config_path()` from `app_paths`
- `get_last_preset_name`: default `"DB prod-safe"` if missing/unknown

Update `config/config.example.json`:

```json
{
    "CPU_GRAPH_DURATION_SEC": 60,
    "RAM_TEST_SIZE_MB": 1024,
    "DISK_SEQ_MB": 1024,
    "DISK_IOPS_ITERATIONS": 10000,
    "PING_TARGET": "8.8.8.8",
    "PROFILE": "generic",
    "PRODUCTION_SAFE": false,
    "WARN_DB_LATENCY_MS": 10,
    "DISK_TEST_PATH": "",
    "APP_PORT_CHECK": null,
    "UI_LAST_PRESET": "DB prod-safe",
    "UI_PRESETS": []
}
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_ui_presets.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bin/ui/presets.py tests/test_ui_presets.py config/config.example.json tests/test_imports.py
git commit -m "Add UI preset store with Never-lab builtins and config persistence."
```

---

### Task 3: Orchestrator score fields

**Files:**
- Modify: `bin/orchestrator.py` (`AuditResultPaths` + return site ~lines 22–27 and 116–137)
- Modify: `tests/test_orchestrator.py` and/or create `tests/test_orchestrator_result_fields.py`

**Interfaces:**
- Consumes: `ReportGenerator.overall`, `engine.data["meta"]["hostname"]`
- Produces: `AuditResultPaths` with `overall_score: float`, `grade: str`, `status: str`, `hostname: str`, `profile: str`, `mode: str` (plus existing path fields)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_orchestrator_result_fields.py
from __future__ import annotations

import sys
from pathlib import Path
from threading import Event
from unittest.mock import MagicMock

import pytest

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from orchestrator import AuditResultPaths, run_audit  # noqa: E402


def test_audit_result_paths_has_score_fields() -> None:
    fields = {f.name for f in AuditResultPaths.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    for name in ("overall_score", "grade", "status", "hostname", "profile", "mode"):
        assert name in fields


def test_run_audit_populates_overall(monkeypatch, tmp_path: Path) -> None:
    """Stub engine + reporter so run_audit returns score without real benchmarks."""
    import orchestrator as orch

    class FakeEngine:
        def __init__(self, **kwargs):
            self.cancel_event = None
            self.skip_chaos = True
            self.config = {}
            self.data = {
                "meta": {"hostname": "testhost", "is_admin": False},
                "benchmark": {"chaos": {}},
            }

        def collect_sys_info(self): ...
        def cpu_benchmark_suite(self): ...
        def cpu_real_world(self): ...
        def ram_benchmark(self): ...
        def net_benchmark(self): ...
        def disk_benchmarks(self): ...
        def chaos_disk_under_load(self): ...
        def save_results(self):
            return str(tmp_path / "out.json")

        def get_history(self):
            return self.data

    class FakeReporter:
        def __init__(self, *a, **k):
            self.overall = {"score": 88.0, "grade": "A", "status": "ok"}

        def export_presentation_assets(self, d): ...
        def render(self):
            return "<html></html>"

    monkeypatch.setattr(orch, "HostPulseEngine", FakeEngine)
    monkeypatch.setattr(orch, "ReportGenerator", FakeReporter)
    monkeypatch.setattr(orch, "_load_baseline", lambda root: None)

    result = run_audit(
        root_dir=str(tmp_path),
        bin_dir=str(tmp_path),
        profile="db_server",
        quick=True,
        production_safe=True,
        export_slides=False,
        cancel_event=Event(),
    )
    assert result.hostname == "testhost"
    assert result.grade == "A"
    assert result.overall_score == 88.0
    assert result.status == "ok"
    assert result.profile == "db_server"
    assert result.mode == "production-safe"
    assert Path(result.html_path).is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_orchestrator_result_fields.py -v`  
Expected: FAIL on missing fields

- [ ] **Step 3: Implement**

Update dataclass:

```python
@dataclass
class AuditResultPaths:
    json_path: str
    html_path: str
    export_dir: str
    cancelled: bool = False
    overall_score: float = 0.0
    grade: str = "N/A"
    status: str = "na"
    hostname: str = ""
    profile: str = "generic"
    mode: str = "full"
```

Before return in `run_audit`, after `reporter.render()`:

```python
overall = getattr(reporter, "overall", {}) or {}
mode = "production-safe" if production_safe else ("quick" if quick else "full")
return AuditResultPaths(
    json_path=json_path,
    html_path=html_path,
    export_dir=export_dir,
    overall_score=float(overall.get("score", 0) or 0),
    grade=str(overall.get("grade", "N/A")),
    status=str(overall.get("status", "na")),
    hostname=str(engine.data.get("meta", {}).get("hostname", "")),
    profile=profile,
    mode=mode,
)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_orchestrator_result_fields.py tests/test_orchestrator.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bin/orchestrator.py tests/test_orchestrator_result_fields.py
git commit -m "Expose overall score fields on AuditResultPaths for the Done screen."
```

---

### Task 4: Screen frames (Setup / Live / Done)

**Files:**
- Create: `bin/ui/screens/__init__.py`
- Create: `bin/ui/screens/setup.py`
- Create: `bin/ui/screens/live.py`
- Create: `bin/ui/screens/done.py`

**Interfaces:**
- Consumes: `ui.theme.COLORS`, `ui.presets.Preset` / list helpers
- Produces:
  - `SetupScreen(parent, *, on_start: Callable[[Preset], None], on_presets_changed: Callable[[], None] | None = None)`
    - methods: `get_effective_preset() -> Preset`, `refresh_presets()`, `set_status_message(text: str)`
  - `LiveScreen(parent, *, on_cancel: Callable[[], None])`
    - methods: `reset(summary: str)`, `set_progress(status: str, step: int | None)`, `append_log(line: str)`, `set_log_visible(visible: bool)`
  - `DoneScreen(parent, *, on_open_report, on_export_pdf, on_new_run)`
    - methods: `show_result(result: AuditResultPaths)` where result has score fields + `html_path`

Each screen is a `ctk.CTkFrame` that fills the parent; only one is `grid`/`pack` visible at a time (controlled by Task 5).

- [ ] **Step 1: Implement SetupScreen**

Layout (Italian):
- Title `HostPulse` + version from `version.__version__`
- Subtitle one line
- `CTkSegmentedButton` or `CTkOptionMenu` / radio list of preset names from `list_presets()`
- Buttons: **Avvia analisi**, **Salva come preset…**, **Elimina preset** (enabled only if selected custom)
- Collapsible **Avanzate** (`CTkFrame` shown/hidden via toggle): profile OptionMenu (`Generico`/`Application Server`/`DB Server` mapped like current UI), checkboxes quick / production_safe / compare
- Editing avanzate updates internal “draft” flags used by `get_effective_preset()` without renaming selection until save
- **Salva come preset…**: `CTkInputDialog` for name → `Preset(..., builtin=False)` → `save_custom_preset` → `set_last_preset_name` → `refresh_presets`
- **Elimina**: `delete_custom_preset` then refresh
- On select builtin/custom: copy flags into avanzate widgets; `set_last_preset_name`
- Style with `COLORS` (fg_color card/bg, accent buttons)

- [ ] **Step 2: Implement LiveScreen**

- Summary label (preset/profile/mode)
- Six-step hint text matching orchestrator phases
- `CTkProgressBar` accent-colored
- Status label
- **Annulla** button → `on_cancel`
- Log `CTkTextbox` (Consolas 10), expanded by default; toggle button **Nascondi log** / **Mostra log**

- [ ] **Step 3: Implement DoneScreen**

- Large grade label (font ~48) colored via `status_color(result.status)`
- Score `{score}/100`
- Meta line: hostname · profile · mode
- Buttons: **Apri report**, **Esporta PDF**, **Nuova analisi**
- Muted path label for `html_path`

- [ ] **Step 4: Smoke import (Windows)**

Run: `python -c "import sys; sys.path.insert(0,'bin'); from ui.screens.setup import SetupScreen; from ui.screens.live import LiveScreen; from ui.screens.done import DoneScreen; print('ok')"`  
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add bin/ui/screens
git commit -m "Add Setup, Live, and Done screen frames for the live shell."
```

---

### Task 5: AuditApp state machine + entrypoint

**Files:**
- Create: `bin/ui/app.py`
- Modify: `bin/ui_benchmark.py` (thin entry)
- Modify: `tests/test_imports.py` if needed (`ui.app`)
- Create: `tests/test_ui_app_transitions.py` (headless-ish with mocks; skip if no display)

**Interfaces:**
- Consumes: screens, `run_audit`, `needs_full_load_confirm`, `AuditCancelled`, `html_file_to_pdf`
- Produces: `class AuditApp(ctk.CTk)` with `show_setup()`, `show_live()`, `show_done(result)`, `main()` entry still on `ui_benchmark`

- [ ] **Step 1: Write transition test (logic helper preferred)**

Prefer extracting a tiny pure helper if Tk is painful in CI:

```python
# in bin/ui/app.py (or bin/ui/state.py if cleaner)
# STATES = ("setup", "live", "done")
```

If full Tk test is flaky on Linux CI, mark `@pytest.mark.skipif(sys.platform != "win32", ...)` OR test only a `ShellController` class that records `state` without widgets:

```python
# tests/test_ui_app_transitions.py
from ui.app import ShellController  # thin non-Tk controller used by AuditApp

def test_controller_flow():
    c = ShellController()
    assert c.state == "setup"
    c.begin_run()
    assert c.state == "live"
    c.finish_run()
    assert c.state == "done"
    c.cancel_to_setup()
    assert c.state == "setup"
```

Implement `ShellController` used by `AuditApp` for state; widgets react to state.

- [ ] **Step 2: Implement `AuditApp`**

```text
__init__:
  apply_appearance()
  geometry ~960x600; configure bg COLORS["bg"]
  container frame
  setup = SetupScreen(..., on_start=self._start)
  live = LiveScreen(..., on_cancel=self._cancel)
  done = DoneScreen(..., on_open_report=..., on_export_pdf=..., on_new_run=self.show_setup)
  show_setup()

_start(preset):
  if needs_full_load_confirm(...): messagebox; return if no
  set_last_preset_name(preset.name)
  show_live(); live.reset(summary)
  start daemon thread → run_audit(..., on_progress marshalled via after(0,...))
  on success → show_done(result)  # NO completion messagebox (Done IS the celebration)
  on AuditCancelled → show_setup + status message
  on Exception → messagebox + show_setup

_cancel: cancel_event.set()
```

Reuse worker pattern from current `ui_benchmark.py` (`after(0, ...)` marshaling).

- [ ] **Step 3: Thin `ui_benchmark.py`**

```python
from __future__ import annotations
import sys
# frozen path insert as today
from deps_check import require_dependencies
require_dependencies(frozen=getattr(sys, "frozen", False))
from app_paths import ensure_runtime_dirs
from ui.app import AuditApp

def main() -> None:
    ensure_runtime_dirs()
    app = AuditApp()
    app.mainloop()

if __name__ == "__main__":
    main()
```

Keep `AuditApp` importable as `from ui_benchmark import AuditApp` by re-exporting:

```python
from ui.app import AuditApp  # re-export for tests/test_imports.py
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_ui_app_transitions.py tests/test_imports.py -q`  
On Windows also: `python -c "import sys; sys.path.insert(0,'bin'); import ui_benchmark; print(ui_benchmark.AuditApp)"`  
Expected: PASS / class prints

- [ ] **Step 5: Manual piece-check (Windows)**

Run: `python bin/ui_benchmark.py`  
Expected: window opens on Setup; Start enabled; presets visible; theme not green-default

- [ ] **Step 6: Commit**

```bash
git add bin/ui/app.py bin/ui_benchmark.py tests/test_ui_app_transitions.py
git commit -m "Wire Setup/Live/Done state machine into the HostPulse GUI entry."
```

---

### Task 6: Packaging + docs touch-up

**Files:**
- Modify: `HostPulse.windows.spec` (`hiddenimports`)
- Modify: `CHANGELOG.md` under `## Unreleased` (one bullet for live shell)
- Modify: `README.md` only if GUI quickstart wording is wrong (optional one line)

- [ ] **Step 1: Update spec hiddenimports**

Add:

```python
"ui",
"ui.theme",
"ui.presets",
"ui.app",
"ui.screens",
"ui.screens.setup",
"ui.screens.live",
"ui.screens.done",
```

- [ ] **Step 2: CHANGELOG Unreleased**

```markdown
- Live GUI: Setup → Live → Done shell, report-aligned dark theme, Never-lab presets (+ custom in config)
```

- [ ] **Step 3: Full test suite**

Run: `python -m pytest -q`  
Expected: all previous + new tests PASS (skip GUI import on non-Windows as today)

- [ ] **Step 4: Commit**

```bash
git add HostPulse.windows.spec CHANGELOG.md README.md
git commit -m "Register ui package for Windows EXE and note live shell in changelog."
```

---

### Task 7: End-to-end verification

- [ ] **Step 1: Quick smoke preset run (manual)**

Run GUI → select **Quick smoke** → Avvia → confirm Live progress → Done shows grade → Apri report opens HTML → Nuova analisi returns Setup

- [ ] **Step 2: Custom preset**

Avanzate change → Salva come preset → restart GUI → last preset restored

- [ ] **Step 3: Cancel**

Start → Annulla → back to Setup, no Done scorecard

- [ ] **Step 4: Full-load guard**

Select **App full** → Avvia → confirm dialog appears

- [ ] **Step 5: Mark plan tasks complete in this file when done**

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| Modular `bin/ui/` | 1–5 |
| Theme tokens / no green CTk | 1, 5 |
| Presets builtins + custom config | 2 |
| Setup / Live / Done flow | 4–5 |
| Done mini scorecard | 3 + 4 DoneScreen |
| Orchestrator score fields | 3 |
| Full-load confirm | 5 |
| Cancel → Setup | 5 |
| PDF / open report | 5 (reuse existing handlers) |
| Packaging hiddenimports | 6 |
| Italian copy | 4–5 |
| Tests presets/theme/transitions | 1–5 |

No TBD placeholders. Types consistent: `Preset`, `AuditResultPaths` field names used in Done and tests match Task 2–3.
