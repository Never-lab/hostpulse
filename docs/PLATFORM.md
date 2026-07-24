# Platform support

HostPulse core (`engine`, reporter, CLI) is OS-portable. OS-specific probes live in `bin/plat.py`.

| Capability | Windows | Linux |
|------------|---------|-------|
| Elevated privileges | `IsUserAnAdmin` | `geteuid() == 0` |
| Power / perf plan | `powercfg` via PowerShell | CPU scaling governor (`/sys`) or INFO gap |
| NUMA nodes | WMI | `/sys/devices/system/node` |
| Processor queue length | Perf counter | **N/A** (INFO gap) |
| Context switches/sec | Perf counter | `/proc/stat` ctxt delta (approx) |
| RAM speed MHz | CIM / WMIC | **N/A** (INFO gap) |
| VM detect | Hyper-V release + WMI manufacturer | `systemd-detect-virt` / DMI |
| Ping | `ping -n` | `ping -c` |
| Disk test path | `DISK_TEST_PATH` or system temp | same |

Missing capability → metric left at default/`0` + health **INFO** with `PLATFORM_*_NA` (never crash).

Windows remains the production-quality path. Linux is best-effort for Phase 2.
