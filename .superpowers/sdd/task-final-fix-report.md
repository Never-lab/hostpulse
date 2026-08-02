# Final review fix — report

Branch: `feat/live-shell-ui`. All Critical + Important items from
`task-final-fix-brief.md` implemented.

## Changes

### 1. Ruff F401 (Critical)
- `tests/test_ui_theme.py`: removed unused `import pytest`.

### 2. Corrupt config must not be clobbered (Important)
- `bin/ui/presets.py`: added `ConfigCorruptError(ValueError)`.
- Split reading into `_read_config_strict` (raises `ConfigCorruptError` when
  `config.json` exists but is invalid JSON; returns `{}` only for a missing
  file) and `_read_config` (safe wrapper used by read/lookup paths —
  `list_presets`, `get_preset`, `get_last_preset_name` — which degrade to
  built-ins-only instead of crashing).
- `_write_config` now calls `_read_config_strict`, so `save_custom_preset`,
  `delete_custom_preset`, `set_last_preset_name` raise `ConfigCorruptError`
  and abort **before** any write — the technician's on-disk engine keys are
  never overwritten with an empty dict.

### 3. Preset/config write failures → messagebox (Important)
- `bin/ui/screens/setup.py`: `_handle_save_preset`, `_handle_delete_preset`,
  and `_on_preset_selected` (last-preset write) now catch
  `(OSError, ValueError)` (covers `ConfigCorruptError`), show an Italian
  `messagebox.showerror`, set a status message, and return without touching
  `self._presets`/state — prior presets are kept as-is.
- `bin/ui/app.py`: `AuditApp._start` wraps `set_last_preset_name` the same
  way; a save failure no longer raises silently and does not block starting
  the audit.

### 4. Modified marker for Avanzate (Important)
- `bin/ui/screens/setup.py`: added `modified_label` next to the "Avanzate"
  toggle; `trace_add("write", ...)` on the four advanced `ctk` variables
  drives `_update_modified_indicator()`, which shows
  "● Modificato rispetto al preset" (Italian) whenever the live widget
  values diverge from the selected preset's stored values.
- `refresh_presets()` now only calls `_apply_preset` (which would overwrite
  widget values) when the resolved preset name actually **changes**. If the
  same preset stays selected (e.g. Setup shown again after cancel/new-run),
  it only refreshes the modified indicator and preserves the technician's
  unsaved draft tweaks, per spec.

### 5. Ubuntu-safe imports (Important)
- Chose option (a): `bin/ui/app.py` no longer imports `customtkinter`/
  `tkinter` or the `ui.screens.*` modules at module scope. `ShellController`
  stays a plain class. The CTk-backed `AuditApp` class is built lazily inside
  `_build_audit_app_class()` and exposed via a module-level `__getattr__`
  (PEP 562), so `import ui.app` / `from ui.app import ShellController` work
  without Tk, while `ui.app.AuditApp` (used by `ui_benchmark.py`) still works
  identically once Tk is available. `ui.theme` and `ui.presets` were already
  CTk-free and remain so.
- Verified by simulating a missing `tkinter`/`customtkinter` environment
  (blocking those imports): `import ui.app` and `ShellController()` succeed;
  only touching `ui.app.AuditApp` raises, as expected.

### 6. EXE build (Critical — explicitly out of scope)
- No packaging/build step was run in this fix. `HostPulse.windows.spec` /
  `build_exe.ps1` / `build_exe_windows.py` untouched. **Packaging piece-check
  remains a human/CI gate**, per the brief.

## Tests re-run

```
$ python -m ruff check bin tests
All checks passed!

$ python -m pytest tests/test_ui_theme.py tests/test_ui_presets.py tests/test_ui_app_transitions.py tests/test_imports.py -q
........................                                                 [100%]
24 passed in 0.54s

$ python -m pytest -q
.............................................s.......................... [ 85%]
............                                                             [100%]
83 passed, 1 skipped in 0.65s
```

Added tests in `tests/test_ui_presets.py`:
- `test_corrupt_config_reads_degrade_to_builtins` — corrupt `config.json`
  read paths degrade to built-ins only, no crash.
- `test_corrupt_config_refuses_writes_and_keeps_file_untouched` — corrupt
  `config.json` write paths (`save_custom_preset`, `delete_custom_preset`,
  `set_last_preset_name`) all raise `ConfigCorruptError` and leave the file
  byte-for-byte unchanged.

Also ran a manual GUI smoke (per `CLAUDE.md` piece-check for
`bin/ui_benchmark.py`): instantiated `AuditApp` on Windows, confirmed it
builds without error, `start_button` is enabled, `delete_button` correctly
disabled for the built-in default preset, then destroyed the window cleanly.

## Concerns / follow-ups

- The "modificato" indicator and preset-write-failure messagebox flows are
  UI-only and not covered by an automated widget test (no CTk headless test
  harness in this repo); verified via manual GUI smoke instantiation only.
- Packaging/EXE build was intentionally skipped — human/CI gate still needed
  before shipping.

## Commit

Single commit on `feat/live-shell-ui` (see SHA reported in the chat reply),
authored without any `Co-authored-by: Cursor` trailer.
