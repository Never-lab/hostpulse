# Platform support

HostPulse core (`engine`, reporter, CLI) is OS-portable. OS-specific probes live in `bin/plat.py`.

| Capability | Windows | Linux |
|------------|---------|-------|
| Elevated privileges | `IsUserAnAdmin` | `geteuid() == 0` |
| Power / perf plan | `powercfg` via PowerShell | CPU scaling governor (`/sys`) or INFO gap |
| NUMA nodes | WMI | `/sys/devices/system/node` |
| Processor queue length | Perf counter | **n/d** (INFO gap + hover) |
| Context switches/sec | Perf counter | `/proc/stat` ctxt delta (approx) |
| RAM speed MHz | CIM / WMIC | `dmidecode` configured/rated speed (often root) or **n/d** + hover |
| VM detect | Hyper-V release + WMI manufacturer | `systemd-detect-virt` / DMI |
| Ping | `ping -n` | `ping -c` |
| Disk test path | `DISK_TEST_PATH` or system temp | same |

Missing capability → metric shown as **n/d** in the HTML report with hover tooltip from health **INFO** `PLATFORM_*_NA` (never crash; never fake a Windows-only value as `0`).

Windows remains the production-quality path. Linux is best-effort for Phase 2; RAM MHz may appear when `dmidecode` works (typically root).
