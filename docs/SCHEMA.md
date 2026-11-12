# AuditResult schema (HostPulse)

On-disk and in-memory audit payloads use a versioned contract.

- `schema_version` (int): bump when removing/renaming fields. Current: **1**
- `engine_version` (str): from `bin/version.py` / `pyproject.toml`

## Top-level keys (v1)

| Key | Role |
|-----|------|
| `schema_version` | Contract version |
| `engine_version` | HostPulse release that produced the file |
| `meta` | hostname, date, timestamp, is_admin, profile, `quick`, `production_safe` |
| `sys_info` | OS / CPU / power plan / NUMA / uptime |
| `virtualization` | VM flag, hypervisor, queue length, ctx switches |
| `ram_hw` | capacity / usage / swap |
| `disk_hw` | capacity / free / usage |
| `health.events[]` | `{level, code, message, timestamp}` |
| `benchmark.*` | cpu_consistency, cpu_real, cpu_series, disk, ram_perf, net, chaos |
| `app_server.ports` | map port → bool |

### Nested keys checked in tests (v1)

| Path | Required keys |
|------|----------------|
| `meta` | hostname, date, timestamp, is_admin, profile, quick, production_safe |
| `benchmark.disk` | seq_write_mb, seq_read_mb, iops, latency_p99_ms, db_sim_latency_ms |
| `benchmark.chaos` | active, disk_iops_under_load, impact_pct |

`cpu_consistency.stability_score` is optional until the CPU suite runs (init has jitter_score + avg_task_ms only).

Source of truth: `bin/schema.py` (`stamp_audit`, `missing_structure`, required-key tuples).  
Reporter and GUI should read this shape only.

## Compare mode

Compare loads prior audits from `results/` for the **same `meta.hostname`** only, ordered by `meta.timestamp`. The Health Score / scorecard always uses the run just completed (`ReportGenerator.main_d`).
