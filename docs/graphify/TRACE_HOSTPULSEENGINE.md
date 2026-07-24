# Trace: why `HostPulseEngine` is a cross-community bridge

**Question (from `GRAPH_REPORT.md`):**  
Why does `HostPulseEngine` connect *Benchmark Engine* to *Platform Adapter Tests*, *CLI Paths & Argparse*, *Orchestrator & Cancel*, and *Schema & Versioning*?

**Answer in one line:**  
It is the shared runtime core: orchestrator/GUI/CLI construct it, it stamps the schema, it loads OS adapters and paths, and tests hit it to prove those contracts.

## Graph facts

| | |
|---|---|
| Node | `HostPulseEngine` (`bin_engine_hostpulseengine`) |
| Source | `bin/engine.py` ~L67 |
| Home community | **0 — Benchmark Engine** (methods: CPU/RAM/disk/net/chaos) |
| Degree | 30 |

Direct neighbors outside community 0 (from `docs/graphify/graph.json`):

| Community | Why the edge exists |
|-----------|---------------------|
| **6 Orchestrator & Cancel** | `run_audit()` **calls** the engine; `AuditResultPaths` **uses** it as the pipeline subject |
| **7 Schema & Versioning** | `.save_results()` / `__init__` path to `stamp_audit()`; schema tests construct the engine |
| **5 CLI Paths & Argparse** | `__init__` **calls** `get_app_base_dir` / `get_config_dir` / `get_results_dir` / `ensure_runtime_dirs` (clustered with CLI because CLI shares `app_paths`) |
| **10 Platform Adapter Tests** | `test_net_benchmark_uses_adapter_ping()` **calls** the engine while mocking `plat.ping_argv` |

Also (file-level, often 1 hop via `engine.py` or `__init__`):

- `engine.py` **imports_from** `plat.py` → OS adapters community  
- `__init__` **calls** `get_adapter()`; `.net_benchmark()` **calls** `parse_ping_latencies_ms()`  
- `_check_cancel()` **calls** `check_cancel()` → cancel/orchestrator community  

## Execution path (source-verified)

```text
GUI AuditApp._run_audit_worker  ──┐
CLI  main()                       ├──►  orchestrator.run_audit()
                                  │         │
                                  │         ▼
                                  │    HostPulseEngine(...)
                                  │         │
                                  ├─────────┼── app_paths (dirs)
                                  ├─────────┼── plat.get_adapter()  (Windows/Linux probes)
                                  ├─────────┼── schema.stamp_audit()  (schema_version / flags)
                                  └─────────┼── cancel.check_cancel()  (cooperative stop)
                                            ▼
                                     benchmarks → save_results → ReportGenerator
```

Shortest graph path engine → reporter (INFERRED):  
`HostPulseEngine` ←uses— `AuditResultPaths` —uses→ `ReportGenerator`  
(Real flow: `run_audit` builds both engine results and the reporter; prefer that mental model.)

## What this means for contributors / AI

1. **Change benchmarks** → stay in `bin/engine.py` (+ tests under `tests/test_engine_*`).
2. **Change OS probes** → `bin/plat.py` only; engine should keep calling `self.plat.*`.
3. **Change run sequence / progress / cancel** → `bin/orchestrator.py` (+ GUI/CLI thin wrappers).
4. **Change JSON contract** → `bin/schema.py` + `docs/SCHEMA.md`; engine only calls `stamp_audit`.
5. **Do not** re-introduce PowerShell/ctypes in the engine — that breaks the plat bridge.

## Honesty notes

- Some engine methods (`__init__`, `_apply_quick_mode`) were **clustered into community 5** by Louvain even though they live in `engine.py`. Treat community labels as navigation aids, not package ownership.
- Several cross edges are **INFERRED** (test→engine calls). Verify against source when refactoring; EXTRACTED `imports_from` / `method` edges are stronger.

## How this note was produced

```bash
graphify query "Why does HostPulseEngine connect …"
graphify explain HostPulseEngine
graphify path HostPulseEngine ReportGenerator
# plus adjacency analysis of docs/graphify/graph.json
```

Rebuild the graph after large structural moves, then refresh this file if the bridge story changes.
