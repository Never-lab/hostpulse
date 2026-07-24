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

Source of truth for stamping: `bin/schema.py` (`stamp_audit`).  
Reporter and GUI should read this shape only.
