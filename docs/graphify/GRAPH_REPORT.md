# Graph Report - .  (2026-07-24)

## Corpus Check
- Corpus is ~15,253 words - fits in a single context window. You may not need a graph.

## Summary
- 294 nodes · 485 edges · 17 communities (16 shown, 1 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Benchmark Engine
- HTML Report Generator
- Product Docs & Agents
- PDF Export & Load Safety
- OS Platform Adapters
- CLI Paths & Argparse
- Orchestrator & Cancel
- Schema & Versioning
- Deps Check & Hardening
- CI Packaging & Release
- Platform Adapter Tests
- Docker EXE Builder
- Community 15

## God Nodes (most connected - your core abstractions)
1. `ReportGenerator` - 34 edges
2. `HostPulseEngine` - 30 edges
3. `AuditApp` - 16 edges
4. `get_app_base_dir()` - 12 edges
5. `run_audit()` - 12 edges
6. `ensure_runtime_dirs()` - 11 edges
7. `html_file_to_pdf()` - 9 edges
8. `LinuxAdapter` - 9 edges
9. `main()` - 8 edges
10. `AuditResult` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_net_benchmark_uses_adapter_ping()` --calls--> `HostPulseEngine`  [INFERRED]
  tests/test_plat.py → bin/engine.py
- `test_new_engine_data_is_stamped()` --calls--> `HostPulseEngine`  [INFERRED]
  tests/test_schema.py → bin/engine.py
- `test_save_results_writes_versions()` --calls--> `HostPulseEngine`  [INFERRED]
  tests/test_schema.py → bin/engine.py
- `psutil` --conceptually_related_to--> `HostPulseEngine`  [INFERRED]
  requirements.txt → CLAUDE.md
- `test_run_audit_respects_cancel()` --calls--> `get_app_base_dir()`  [INFERRED]
  tests/test_orchestrator.py → bin/app_paths.py

## Import Cycles
- None detected.

## Communities (17 total, 1 thin omitted)

### Community 0 - "Benchmark Engine"
Cohesion: 0.08
Nodes (18): _cpu_stress_worker(), HostPulseEngine, _measure_disk_iops(), Aggiunge un evento di health classificato (OK/WARN/CRIT)., Worker CPU per chaos test. A livello modulo per compatibilità pickle/multiproces, Misura IOPS su file temporaneo con letture random 4K., Misura una stima di bandwidth di copia RAM (GB/s)., Ping semplice per stimare latenza media e jitter. (+10 more)

### Community 1 - "HTML Report Generator"
Cohesion: 0.11
Nodes (9): ReportGenerator, test_html_has_no_external_cdn(), test_html_includes_commercial_sections(), _load(), test_analyses_include_core_disk_metrics(), test_db_profile_tightens_latency_thresholds(), test_html_contains_executive_and_recommendations(), test_overall_score_present_and_graded() (+1 more)

### Community 2 - "Product Docs & Agents"
Cohesion: 0.08
Nodes (30): 0.1.0 first public release, CustomTkinter GUI, FABLE+POWERS, HostPulseEngine, ReportGenerator, PRODUCTION_SAFE, Machine profiles, Platform adapters (+22 more)

### Community 3 - "PDF Export & Load Safety"
Cohesion: 0.10
Nodes (18): needs_full_load_confirm(), Guards for full-load runs on sensitive profiles., True when app/db profile is about to run without production-safe., _candidate_browsers(), find_browser(), html_file_to_pdf(), PdfExportError, Path (+10 more)

### Community 4 - "OS Platform Adapters"
Cohesion: 0.11
Nodes (10): GenericAdapter, get_adapter(), InfraSnapshot, LinuxAdapter, PlatformAdapter, OS adapters — Windows production path, Linux best-effort.  PowerShell / WMI /, Platform-specific infra fields. None = unsupported / unknown., Two-sample /proc/stat ctxt delta over ~0.2s. (+2 more)

### Community 5 - "CLI Paths & Argparse"
Cohesion: 0.15
Nodes (18): ArgumentParser, ensure_runtime_dirs(), get_app_base_dir(), get_bin_dir(), get_bundle_dir(), get_config_dir(), get_config_path(), get_results_dir() (+10 more)

### Community 6 - "Orchestrator & Cancel"
Cohesion: 0.13
Nodes (17): AuditCancelled, check_cancel(), Event, Cooperative cancel for long-running audits., Raised when the user/CLI requests stop between or inside audit phases., AuditResultPaths, _load_baseline(), Any (+9 more)

### Community 7 - "Schema & Versioning"
Cohesion: 0.13
Nodes (8): Any, AuditResult contract shared by engine, reporter, and on-disk JSON., Attach schema/engine versions and run-mode flags. Mutates and returns ``data``., stamp_audit(), Single source of truth for HostPulse version (keep in sync with pyproject.toml)., test_new_engine_data_is_stamped(), test_save_results_writes_versions(), test_stamp_audit_idempotent()

### Community 8 - "Deps Check & Hardening"
Cohesion: 0.18
Nodes (10): missing_packages(), Explicit dependency check — no silent pip install., Raise SystemExit with install hint if packages are missing (source runs only)., require_dependencies(), MonkeyPatch, Hardening: mktemp removal, deps message, production-safe warn (#3 #4 #8)., test_missing_packages_empty_when_present(), test_missing_packages_reports_absent() (+2 more)

### Community 9 - "CI Packaging & Release"
Cohesion: 0.22
Nodes (8): PyInstaller packaging, CI + GitHub hygiene plan, CI workflow, Release workflow, Windows EXE release, pytest, ruff, psutil

### Community 10 - "Platform Adapter Tests"
Cohesion: 0.18
Nodes (7): parse_ping_latencies_ms(), Extract latency ms from ping stdout (Windows/Linux locales)., MonkeyPatch, Platform adapters (#15)., test_linux_collect_infra_emits_gaps(), test_net_benchmark_uses_adapter_ping(), test_parse_ping_latencies()

### Community 11 - "Docker EXE Builder"
Cohesion: 0.60
Nodes (4): main(), Path, run_docker(), CompletedProcess

## Knowledge Gaps
- **7 isolated node(s):** `hostpulse`, `schema_version`, `engine_version`, `stamp_audit`, `quick mode` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HostPulseEngine` connect `Benchmark Engine` to `Platform Adapter Tests`, `CLI Paths & Argparse`, `Orchestrator & Cancel`, `Schema & Versioning`?**
  _High betweenness centrality (0.251) - this node is a cross-community bridge._
- **Why does `ReportGenerator` connect `HTML Report Generator` to `Orchestrator & Cancel`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `run_audit()` connect `Orchestrator & Cancel` to `Benchmark Engine`, `HTML Report Generator`, `CLI Paths & Argparse`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `ReportGenerator` (e.g. with `AuditResultPaths` and `run_audit()`) actually correct?**
  _`ReportGenerator` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `HostPulseEngine` (e.g. with `AuditResultPaths` and `run_audit()`) actually correct?**
  _`HostPulseEngine` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AuditApp` (e.g. with `AuditCancelled` and `PdfExportError`) actually correct?**
  _`AuditApp` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `get_app_base_dir()` (e.g. with `main()` and `.__init__()`) actually correct?**
  _`get_app_base_dir()` has 4 INFERRED edges - model-reasoned connections that need verification._