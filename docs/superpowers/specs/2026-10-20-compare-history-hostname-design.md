# HostPulse — Compare mode: current run + same-hostname history

**Date:** 2026-10-20  
**Status:** Approved for planning  
**Issues:** #42, #43  
**Approach:** Fix in `get_history` + orchestrator (no `ReportGenerator` API change)

## Context

With `compare=True`, the orchestrator builds the report from `engine.get_history()`, which today:

1. Loads every `*.json` under `results/` (all hosts)
2. Does not sort by timestamp
3. Relies on `ReportGenerator.main_d = data_list[-1]`, so the Health Score / scorecard can point at an arbitrary past audit

Technicians often keep multi-client audits on one laptop → wrong score + cross-customer data in the comparative HTML.

## Goals

- Scorecard / Health Score always reflect the **current run**
- Compare history is scoped to the **same `meta.hostname`** by default (orchestrator path)
- History ordered by `meta.timestamp` (ascending); current run is always last in the list passed to the reporter
- Tests cover multi-json same host and two-hostname isolation
- One-line doc note on compare semantics

## Non-goals

- New CLI flags or UI copy beyond a SCHEMA/DEPLOY one-liner
- Changing `ReportGenerator` constructor (`main=` param deferred)
- Filtering history when `get_history()` is called with no `hostname` (callers that want all hosts keep that)
- Renaming HTML “Comparativa host” strings (optional follow-up)
- Issue #49 (slides default) or other audit issues

## Architecture

```
save_results()
    → get_history(hostname=current_hostname)
         filter meta.hostname == hostname
         sort by meta.timestamp ascending
    → drop entries with same meta.timestamp as current
    → append engine.data
    → ReportGenerator(history)   # main_d = data_list[-1] == current
```

Without `compare`: unchanged (`ReportGenerator(engine.data)`).

### `HostPulseEngine.get_history(hostname: str | None = None)`

| Behavior | Detail |
|----------|--------|
| Load | All `*.json` in `results_dir`; skip malformed / missing `meta` (existing) |
| Filter | If `hostname` is not `None` and not empty: keep only exact `meta.hostname` match |
| Sort | Ascending by `str(meta.timestamp or "")` |
| No hostname | Return all hosts, still sorted by timestamp |

### `orchestrator.run_audit` (`compare=True` only)

```python
host = str(engine.data["meta"].get("hostname") or "")
history = engine.get_history(hostname=host) if host else []
cur_ts = engine.data["meta"].get("timestamp")
history = [h for h in history if h.get("meta", {}).get("timestamp") != cur_ts]
history.append(engine.data)
reporter = ReportGenerator(history, reference=ref, style="corporate")
```

**Empty hostname:** do not call unfiltered `get_history()` — start from `[]`, then append `engine.data` (single-audit report).
## Error handling

- Corrupt JSON: skip (unchanged)
- No prior audits for that host: list length 1 → single-run report (valid)
- Timestamp collision with an older file: older entry dropped by dedupe; current in-memory object wins

## Testing

New file `tests/test_compare_history.py` (tmp `results_dir`):

1. **Same host, order + main:** three fixtures, different timestamps; after orchestrator-style build, last item is current; timestamps non-decreasing before append
2. **Two hostnames:** files for `A` and `B`; `get_history(hostname="A")` returns only `A`
3. **Reporter main:** `ReportGenerator(history).main_d` hostname/timestamp match current

Optional: unit-test `get_history` sort without full `run_audit`.

## Docs

Add a short note under compare / history in `docs/SCHEMA.md` (preferred) or `DEPLOY.md`:

> Compare mode loads prior audits from `results/` for the **same hostname** only, ordered by `meta.timestamp`. The Health Score always uses the run just completed.

## Success criteria (issue DoD)

- [ ] Current run is always `main_d` / Health Score (#42)
- [ ] History sorted by `meta.timestamp` (#42)
- [ ] Default compare scope = same hostname (#43)
- [ ] Documented (#43)
- [ ] Tests: multi-json tmp results + two hostnames (#42, #43)
