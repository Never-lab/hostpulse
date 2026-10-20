# Compare history hostname scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix compare mode so Health Score uses the current run and history is same-hostname only (#42, #43).

**Architecture:** Extend `get_history(hostname=)` with filter + timestamp sort; orchestrator dedupes by timestamp and appends `engine.data` last; `ReportGenerator.main_d = data_list[-1]` unchanged.

**Tech Stack:** Python 3, pytest, existing `HostPulseEngine` / `orchestrator` / `ReportGenerator`.

## Global Constraints

- No `ReportGenerator` API change
- Empty hostname → `[]` then append current (never unfiltered `get_history`)
- Surgical diffs only; EN commit messages

---

### Task 1: `get_history` filter + sort

**Files:**
- Modify: `bin/engine.py` (`get_history`)
- Create: `tests/test_compare_history.py`
- Modify: `docs/SCHEMA.md` (one note)
- Modify: `bin/orchestrator.py` (compare branch)
- Modify: `tests/test_orchestrator_result_fields.py` (`get_history` accepts `hostname`)

- [ ] **Step 1:** Failing tests for sort, hostname filter, orchestrator-style main last, reporter `main_d`
- [ ] **Step 2:** Implement `get_history(hostname=None)` + orchestrator compare path
- [ ] **Step 3:** SCHEMA one-liner; run `pytest tests/test_compare_history.py tests/test_orchestrator_result_fields.py -v`
- [ ] **Step 4:** Commit on branch; open PR linking #42 #43
