# Platform support

HostPulse core (`engine`, reporter, CLI) is OS-portable. OS-specific probes live in `bin/plat.py`.

| Capability | Windows | Linux | Other (macOS, *BSD, …) |
|------------|---------|-------|------------------------|
| Adapter | `WindowsAdapter` | `LinuxAdapter` | `GenericAdapter` |
| Elevated privileges | `IsUserAnAdmin` | `geteuid() == 0` | best-effort / **n/d** |
| Power / perf plan | `powercfg` via PowerShell | CPU scaling governor (`/sys`) or INFO gap | **n/d** |
| NUMA nodes | WMI | `/sys/devices/system/node` | **n/d** |
| Processor queue length | Perf counter | **n/d** (INFO gap + hover) | **n/d** |
| Context switches/sec | Perf counter | `/proc/stat` ctxt delta (approx) | **n/d** |
| RAM speed MHz | CIM / WMIC | `dmidecode` (often root) or **n/d** + hover | **n/d** |
| VM detect | Hyper-V release + WMI manufacturer | `systemd-detect-virt` / DMI | **n/d** |
| Ping | `ping -n` | `ping -c` | best-effort `ping` |
| Disk test path | `DISK_TEST_PATH` or system temp | same | same |

Missing capability → metric shown as **n/d** in the HTML report with hover tooltip from health **INFO** `PLATFORM_*_NA` or `PLATFORM_UNSUPPORTED` (never crash; never fake a Windows-only value as `0`).

Windows remains the production-quality path. Linux is best-effort for Phase 2; RAM MHz may appear when `dmidecode` works (typically root). **Other** OSes use `GenericAdapter` in `bin/plat.py` — same n/d contract, no fake metrics.
