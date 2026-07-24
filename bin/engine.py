import os, psutil, platform, time, multiprocessing, json, ctypes, statistics, random, re, socket, tempfile, hashlib, zlib, subprocess, threading
from datetime import datetime

from app_paths import ensure_runtime_dirs, get_app_base_dir, get_config_dir, get_results_dir
from schema import stamp_audit

_PING_LATENCY_RE = re.compile(
    r"(?:time|tempo|durata)\s*[=<]\s*<?\s*(\d+)",
    re.IGNORECASE,
)
_HIGH_PERF_PLAN_KEYWORDS = (
    "high performance",
    "alte prestazioni",
    "prestazioni elevate",
    "massime prestazioni",
    "ultimate power",
    "maximum performance",
    "prestazioni massime",
)


def _cpu_stress_worker(duration_s):
    """Worker CPU per chaos test. A livello modulo per compatibilità pickle/multiprocessing su Windows."""
    end_t = time.perf_counter() + duration_s
    while time.perf_counter() < end_t:
        hashlib.sha256(os.urandom(1024)).hexdigest()


def _measure_disk_iops(iterations, seq_mb):
    """Misura IOPS su file temporaneo con letture random 4K."""
    sz_mb = max(64, int(seq_mb / 4))
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        path = tf.name
    try:
        data = os.urandom(1024 * 1024)
        with open(path, "wb") as f:
            for _ in range(sz_mb):
                f.write(data)
            f.flush()
            os.fsync(f.fileno())

        block_size = 4096
        latencies = []
        with open(path, "rb") as f:
            file_size = sz_mb * 1024 * 1024
            for _ in range(iterations):
                offset = random.randint(0, max(0, file_size - block_size))
                t0 = time.perf_counter()
                f.seek(offset)
                if not f.read(block_size):
                    break
                t1 = time.perf_counter()
                latencies.append((t1 - t0) * 1000.0)
    finally:
        if os.path.exists(path):
            os.remove(path)

    if not latencies:
        return 0.0
    total_time_s = sum(l / 1000.0 for l in latencies)
    return len(latencies) / total_time_s if total_time_s > 0 else 0.0


class HostPulseEngine:
    def __init__(self, root_dir=None, quick=False, profile=None, production_safe=False):
        ensure_runtime_dirs()
        self.base_path = root_dir or str(get_app_base_dir())
        self.config_dir = str(get_config_dir())
        self.results_dir = str(get_results_dir())
        self.quick = quick
        self.skip_chaos = False

        self.config = self._load_config()
        if self.quick:
            self._apply_quick_mode()
        self.production_safe = bool(production_safe) or bool(self.config.get("PRODUCTION_SAFE", False))
        if self.production_safe:
            self._apply_production_safe()
        self.profile = profile if profile is not None else (self.config.get("PROFILE") or "generic")
        if self.profile not in ("generic", "app_server", "db_server"):
            self.profile = "generic"
        self.data = self._init_data_structure()
        self.data["meta"]["profile"] = self.profile
        stamp_audit(self.data, quick=self.quick, production_safe=self.production_safe)

    def _init_data_structure(self):
        return {
            "meta": {
                "hostname": platform.node(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": int(time.time()),
                "is_admin": self._is_admin(),
            },
            "sys_info": {
                "power_plan": "N/A",
                "numa_nodes": 1,
                "os": "",
                "cpu_model": "",
                "cores": "",
                "uptime": "",
            },
            "virtualization": {
                "is_vm": False,
                "hypervisor": "",
                "cpu_queue_length": 0,
                "ctx_switches_sec": 0,
            },
            "ram_hw": {
                "total_gb": 0,
                "speed_mhz": 0,
                "percent_used": 0,
                "swap_percent": 0,
            },
            "disk_hw": {
                "total_gb": 0,
                "free_gb": 0,
                "percent_used": 0,
            },
            "health": {"events": []},
            "benchmark": {
                "cpu_consistency": {"jitter_score": 0, "avg_task_ms": 0},
                "cpu_real": {"crypto_hash_rate": 0, "compress_mb_s": 0},
                "cpu_series": {"time": [], "usage": [], "freq": []},
                "disk": {
                    "seq_write_mb": 0,
                    "seq_read_mb": 0,
                    "iops": 0,
                    "latency_p99_ms": 0,
                    "db_sim_latency_ms": 0,
                },
                "ram_perf": {"copy_speed_gb": 0},
                "net": {"avg_ms": 0, "jitter_ms": 0},
                "chaos": {
                    "active": False,
                    "disk_iops_under_load": 0,
                    "impact_pct": 0,
                },
            },
            "app_server": {"ports": {}},
        }

    def _is_admin(self):
        """Restituisce True se l'utente ha privilegi elevati. Solo Windows; su altri OS ritorna False."""
        try:
            if platform.system() != "Windows":
                return False
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
        except Exception:
            return False

    def _load_config(self):
        default = {
            "CPU_GRAPH_DURATION_SEC": 300,
            "RAM_TEST_SIZE_MB": 512,
            "DISK_SEQ_MB": 512,
            "DISK_IOPS_ITERATIONS": 10000,
            "PING_TARGET": "8.8.8.8",
            "WARN_CPU_QUEUE_LENGTH": 4,
            "WARN_CTX_SWITCHES_SEC": 50000,
            "PROFILE": "generic",
            "PRODUCTION_SAFE": False,
            "WARN_DB_LATENCY_MS": 10,
            "DISK_TEST_PATH": "",
            "APP_PORT_CHECK": None,
        }
        # Prova prima in config_dir (es. bin/config), poi nella cartella padre (benchmark/config)
        for config_dir in (self.config_dir, os.path.join(os.path.dirname(self.base_path), "config")):
            path = os.path.join(config_dir, "config.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        default.update(json.load(f))
                except Exception:
                    pass
                break
        return default

    def _apply_quick_mode(self):
        """Riduce durata e iterazioni per una analisi rapida."""
        self.config["CPU_GRAPH_DURATION_SEC"] = min(15, self.config.get("CPU_GRAPH_DURATION_SEC", 300))
        self.config["RAM_TEST_SIZE_MB"] = min(256, self.config.get("RAM_TEST_SIZE_MB", 512))
        self.config["DISK_SEQ_MB"] = min(128, self.config.get("DISK_SEQ_MB", 512))
        self.config["DISK_IOPS_ITERATIONS"] = min(2000, self.config.get("DISK_IOPS_ITERATIONS", 10000))

    def _apply_production_safe(self):
        """Riduce carico per esecuzione su VM in produzione (meno I/O, meno CPU, no chaos)."""
        self.config["CPU_GRAPH_DURATION_SEC"] = min(30, self.config.get("CPU_GRAPH_DURATION_SEC", 300))
        self.config["RAM_TEST_SIZE_MB"] = min(256, self.config.get("RAM_TEST_SIZE_MB", 512))
        self.config["DISK_SEQ_MB"] = min(256, self.config.get("DISK_SEQ_MB", 512))
        self.config["DISK_IOPS_ITERATIONS"] = min(3000, self.config.get("DISK_IOPS_ITERATIONS", 10000))
        self.skip_chaos = True

    def run_ps(self, cmd):
        try:
            full_cmd = f'powershell -NoProfile -Command "{cmd}"'
            return subprocess.check_output(full_cmd, shell=True, text=True, stderr=subprocess.STDOUT, timeout=5).strip()
        except Exception:
            return None

    # --- METODI DI TEST (Logica v5 Originale) ---

    def _push_health(self, level, code, message):
        """Aggiunge un evento di health classificato (OK/WARN/CRIT)."""
        self.data["health"]["events"].append(
            {
                "level": level,
                "code": code,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    def collect_sys_info(self):
        info = self.data["sys_info"]
        info["os"] = f"{platform.system()} {platform.release()}"
        info["cpu_model"] = platform.processor()
        info["cores"] = f"{psutil.cpu_count(logical=False)} P / {psutil.cpu_count(logical=True)} L"
        info["uptime"] = str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())).split('.')[0]
        
        ram = psutil.virtual_memory()
        self.data["ram_hw"] = {
            "total_gb": round(ram.total / (1024**3), 2),
            "speed_mhz": self._get_ram_speed(),
            "percent_used": ram.percent,
            "swap_percent": psutil.swap_memory().percent if hasattr(psutil, "swap_memory") else 0,
        }
        du = psutil.disk_usage(self.base_path)
        self.data["disk_hw"] = {
            "total_gb": round(du.total / (1024**3), 2),
            "free_gb": round(du.free / (1024**3), 2),
            "percent_used": du.percent,
        }

        # Arricchimento campi infrastrutturali specifici Windows
        if platform.system().lower().startswith("win"):
            # Power plan attivo
            try:
                plan = self.run_ps("(powercfg /GETACTIVESCHEME) -match '\\((.+)\\)' | Out-Null; $matches[1]")
                if plan:
                    info["power_plan"] = plan.strip()
            except Exception:
                pass

            # Numero di nodi NUMA (se disponibile)
            try:
                numa_raw = self.run_ps("(Get-WmiObject -Class Win32_NumaNode | Measure-Object).Count")
                if numa_raw and numa_raw.strip().isdigit():
                    info["numa_nodes"] = int(numa_raw.strip())
            except Exception:
                pass

            virt = self.data["virtualization"]
            # Performance counters: System Processor Queue Length e Context Switches/sec
            try:
                qlen_raw = self.run_ps("(Get-Counter '\\\\System\\\\Processor Queue Length').CounterSamples[0].CookedValue")
                if qlen_raw is not None:
                    virt["cpu_queue_length"] = float(qlen_raw)
            except Exception:
                pass

            try:
                ctx_raw = self.run_ps("(Get-Counter '\\\\System\\\\Context Switches/sec').CounterSamples[0].CookedValue")
                if ctx_raw is not None:
                    virt["ctx_switches_sec"] = float(ctx_raw)
            except Exception:
                pass

        # Soglie di health di base
        warn_disk = int(self.config.get("WARN_DISK_PERCENT", 85))
        warn_ram = int(self.config.get("WARN_RAM_PERCENT", 85))
        warn_swap = int(self.config.get("WARN_SWAP_PERCENT", 50))

        if du.percent >= warn_disk:
            self._push_health(
                "WARN",
                "DISK_HIGH_USAGE",
                f"Disco quasi pieno: {du.percent}% utilizzato su {self.data['disk_hw']['total_gb']} GB.",
            )
        if ram.percent >= warn_ram:
            self._push_health(
                "WARN",
                "RAM_HIGH_USAGE",
                f"RAM quasi satura: {ram.percent}% utilizzata.",
            )
        swap_p = self.data["ram_hw"]["swap_percent"]
        if swap_p >= warn_swap:
            self._push_health(
                "WARN",
                "SWAP_HIGH_USAGE",
                f"Swap utilizzata al {swap_p}%.",
            )

        # Health rules legate ai nuovi campi infrastrutturali (solo se significativi)
        if platform.system().lower().startswith("win"):
            plan = info.get("power_plan", "") or ""
            plan_lower = plan.lower()
            if plan and not any(x in plan_lower for x in _HIGH_PERF_PLAN_KEYWORDS):
                self._push_health(
                    "WARN",
                    "POWER_PLAN_NOT_HIGH_PERF",
                    f"Piano energetico attivo non ad alte prestazioni: '{plan}'.",
                )

            virt = self.data["virtualization"]
            cpu_q = float(virt.get("cpu_queue_length", 0) or 0)
            ctx_s = float(virt.get("ctx_switches_sec", 0) or 0)

            warn_q = float(self.config.get("WARN_CPU_QUEUE_LENGTH", 4))
            warn_ctx = float(self.config.get("WARN_CTX_SWITCHES_SEC", 50000))

            if cpu_q >= warn_q:
                self._push_health(
                    "WARN",
                    "CPU_QUEUE_LENGTH_HIGH",
                    f"System Processor Queue Length elevato: {cpu_q:.1f} (soglia {warn_q}).",
                )
            if ctx_s >= warn_ctx:
                self._push_health(
                    "WARN",
                    "CTX_SWITCHES_HIGH",
                    f"Context Switches/sec elevati: {int(ctx_s)} (soglia {int(warn_ctx)}).",
                )

        # Rilevazione base virtualizzazione / hypervisor
        virt = self.data["virtualization"]
        try:
            system = platform.uname().system.lower()
            release = platform.uname().release.lower()
            if "microsoft" in release or "hyper-v" in release:
                virt["is_vm"] = True
                virt["hypervisor"] = "Hyper-V/WSL"
            # quick check via system manufacturer (wmic)
            out = self.run_ps("(Get-WmiObject Win32_ComputerSystem).Manufacturer")
            if out and any(x in out.lower() for x in ["vmware", "qemu", "kvm", "xen"]):
                virt["is_vm"] = True
                virt["hypervisor"] = out.strip()
        except Exception:
            pass

        if virt.get("is_vm"):
            hypervisor = virt.get("hypervisor") or "sconosciuto"
            self._push_health(
                "INFO",
                "VM_DETECTED",
                f"VM rilevata (hypervisor: {hypervisor}). Verificare risorse dedicate e memoria (ballooning).",
            )

    def _get_ram_speed(self):
        """Velocità RAM in MHz (solo Windows). Su altri OS ritorna 0."""
        try:
            if platform.system() != "Windows":
                return 0
            ps_out = self.run_ps(
                "(Get-CimInstance Win32_PhysicalMemory | "
                "Where-Object { $_.Speed -gt 0 } | "
                "Measure-Object -Property Speed -Maximum).Maximum"
            )
            if ps_out and ps_out.strip().isdigit():
                return int(ps_out.strip())
            wmic = subprocess.run(
                "wmic memorychip get speed",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            speeds = [int(s) for s in wmic.stdout.split() if s.isdigit() and int(s) > 0]
            return max(speeds) if speeds else 0
        except Exception:
            return 0

    def cpu_benchmark_suite(self):
        # Carico CPU pesante per misurare jitter e coerenza (molte iterazioni, lavoro consistente)
        all_times = []
        for _ in range(8):
            times = [
                (time.perf_counter(), sum(i * i for i in range(60000)), time.perf_counter())
                for _ in range(60)
            ]
            all_times.append(statistics.mean([(t[2] - t[0]) * 1000 for t in times]))
            time.sleep(0.02)
        jitter_score = round(max(0, 100 - (statistics.stdev(all_times) * 10)), 1)
        self.data["benchmark"]["cpu_consistency"]["jitter_score"] = jitter_score
        self.data["benchmark"]["cpu_consistency"]["avg_task_ms"] = round(statistics.mean(all_times), 2)

        # Serie temporale CPU con random spike: carico variabile nel tempo per testare stabilità/thermal
        duration = self.config.get("CPU_GRAPH_DURATION_SEC", 60)
        interval = 1.0
        points = max(5, int(duration / interval))

        cpu_series = self.data["benchmark"]["cpu_series"]
        cpu_series["time"].clear()
        cpu_series["usage"].clear()
        cpu_series["freq"].clear()

        # Thread che genera spike casuali di carico (randomizza il carico nel tempo)
        stop_spike = threading.Event()

        def random_spike_load():
            for _ in range(points):
                if stop_spike.is_set():
                    break
                spike = random.uniform(0.25, 1.0)  # frazione del secondo a 100% CPU
                end_t = time.perf_counter() + interval
                burn_until = time.perf_counter() + spike
                while time.perf_counter() < burn_until and not stop_spike.is_set():
                    hashlib.sha256(os.urandom(1024)).hexdigest()
                remaining = end_t - time.perf_counter()
                if remaining > 0:
                    time.sleep(remaining)

        spike_thread = threading.Thread(target=random_spike_load, daemon=True)
        spike_thread.start()

        psutil.cpu_percent(interval=None)
        start = time.perf_counter()
        try:
            for _ in range(points):
                usage = psutil.cpu_percent(interval=interval)
                freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
                t_rel = time.perf_counter() - start
                cpu_series["time"].append(round(t_rel, 1))
                cpu_series["usage"].append(usage)
                cpu_series["freq"].append(int(freq))
        finally:
            stop_spike.set()

        # Metriche di stabilità nel tempo basate sulla serie raccolta
        if len(cpu_series["usage"]) >= 5:
            try:
                usage_jitter = statistics.pstdev(cpu_series["usage"])
                freqs = [f for f in cpu_series["freq"] if f > 0]
                freq_jitter = statistics.pstdev(freqs) if len(freqs) >= 5 else 0.0

                # Score semplice 0–100: più bassa è la varianza, più alto è lo score.
                normalized = (usage_jitter / 5.0) + (freq_jitter / 250.0)
                stability_score = max(0.0, 100.0 - normalized * 20.0)
                self.data["benchmark"]["cpu_consistency"]["stability_score"] = round(stability_score, 1)
            except statistics.StatisticsError:
                pass

    def cpu_real_world(self):
        data = os.urandom(256 * 1024)
        start = time.perf_counter()
        count = 0
        while time.perf_counter() - start < 1.0:
            hashlib.sha256(data).hexdigest()
            count += 1
        self.data["benchmark"]["cpu_real"]["crypto_hash_rate"] = count
        
        data_1mb = os.urandom(1024 * 1024)
        start = time.perf_counter()
        zlib.compress(data_1mb, level=6)
        self.data["benchmark"]["cpu_real"]["compress_mb_s"] = round(1.0 / (time.perf_counter() - start), 1)

    def disk_benchmarks(self):
        sz_mb = self.config["DISK_SEQ_MB"]
        disk_test_path = self.config.get("DISK_TEST_PATH") or ""
        if disk_test_path and os.path.isdir(disk_test_path):
            try:
                tf = tempfile.NamedTemporaryFile(delete=False, dir=disk_test_path, prefix="hostpulse_temp_", suffix=".tmp")
                path = tf.name
                tf.close()
            except (OSError, PermissionError):
                path = tempfile.mktemp(prefix="hostpulse_", suffix=".tmp")
                self._push_health(
                    "WARN",
                    "DISK_TEST_PATH_INVALID",
                    f"Percorso disco test non scrivibile: {disk_test_path}. Usato temp di sistema.",
                )
        else:
            if disk_test_path and not os.path.isdir(disk_test_path):
                self._push_health(
                    "WARN",
                    "DISK_TEST_PATH_INVALID",
                    f"Percorso disco test inesistente: {disk_test_path}. Usato temp di sistema.",
                )
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                path = tf.name
        try:
            data = os.urandom(1024*1024)
            start = time.perf_counter()
            with open(path, "wb") as f:
                for _ in range(sz_mb): f.write(data)
                f.flush(); os.fsync(f.fileno())
            self.data["benchmark"]["disk"]["seq_write_mb"] = round(sz_mb/(time.perf_counter() - start), 2)
            
            # Read sequenziale
            with open(path, "rb") as f:
                start = time.perf_counter()
                while f.read(1024*1024): pass
                self.data["benchmark"]["disk"]["seq_read_mb"] = round(sz_mb/(time.perf_counter() - start), 2)

            # IOPS e latenze su blocchi piccoli (simulazione workload DB)
            iterations = self.config.get("DISK_IOPS_ITERATIONS", 10000)
            block_size = 4096
            latencies = []
            total_bytes = 0
            with open(path, "rb") as f:
                file_size = sz_mb * 1024 * 1024
                for _ in range(iterations):
                    offset = random.randint(0, max(0, file_size - block_size))
                    t0 = time.perf_counter()
                    f.seek(offset)
                    chunk = f.read(block_size)
                    t1 = time.perf_counter()
                    if not chunk:
                        break
                    latencies.append((t1 - t0) * 1000.0)
                    total_bytes += len(chunk)

            if latencies:
                total_time_s = sum(l / 1000.0 for l in latencies)
                iops = len(latencies) / total_time_s if total_time_s > 0 else 0
                p99 = sorted(latencies)[int(len(latencies) * 0.99) - 1] if len(latencies) >= 100 else max(latencies)
                avg_ms = statistics.mean(latencies)
                self.data["benchmark"]["disk"]["iops"] = int(iops)
                self.data["benchmark"]["disk"]["latency_p99_ms"] = round(p99, 2)
                self.data["benchmark"]["disk"]["db_sim_latency_ms"] = round(avg_ms, 2)

                if self.profile == "db_server":
                    warn_ms = float(self.config.get("WARN_DB_LATENCY_MS", 10))
                    if avg_ms > warn_ms:
                        self._push_health(
                            "WARN",
                            "DB_LATENCY_HIGH",
                            f"Latenza disco elevata per workload DB: {avg_ms:.2f} ms (soglia {warn_ms} ms).",
                        )
        finally:
            if os.path.exists(path): os.remove(path)

    def ram_benchmark(self):
        """Misura una stima di bandwidth di copia RAM (GB/s)."""
        size_mb = int(self.config.get("RAM_TEST_SIZE_MB", 512))
        size_bytes = size_mb * 1024 * 1024
        try:
            buf = bytearray(os.urandom(min(size_bytes, 64 * 1024 * 1024)))
            # Se il buffer è più piccolo del richiesto, copiamo più volte
            iterations = max(8, size_bytes // len(buf))
        except MemoryError:
            # Fallback su dimensione più piccola
            buf = bytearray(os.urandom(16 * 1024 * 1024))
            iterations = 16
            size_bytes = len(buf) * iterations

        start = time.perf_counter()
        total_bytes = 0
        for _ in range(iterations):
            _ = buf[:]  # copia
            total_bytes += len(buf)
        elapsed = time.perf_counter() - start
        if elapsed > 0:
            gb_s = total_bytes / (1024**3) / elapsed
            self.data["benchmark"]["ram_perf"]["copy_speed_gb"] = round(gb_s, 2)

    def net_benchmark(self):
        """Ping semplice per stimare latenza media e jitter."""
        target = self.config.get("PING_TARGET", "8.8.8.8")
        try:
            # -n (Windows) numero pacchetti, -w timeout ms
            cmd = ["ping", "-n", "6", "-w", "1000", target]
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        except Exception as exc:
            self._push_health(
                "WARN",
                "NET_PING_FAILED",
                f"Ping verso {target} fallito: {exc}",
            )
            return

        times = []
        for line in out.splitlines():
            m = _PING_LATENCY_RE.search(line)
            if m:
                times.append(int(m.group(1)))

        if times:
            avg = statistics.mean(times)
            jitter = statistics.pstdev(times) if len(times) > 1 else 0
            self.data["benchmark"]["net"]["avg_ms"] = round(avg, 1)
            self.data["benchmark"]["net"]["jitter_ms"] = round(jitter, 1)

            limit_ms = float(self.config.get("WARN_LATENCY_MS", 80))
            if avg >= limit_ms:
                self._push_health(
                    "WARN",
                    "NET_HIGH_LATENCY",
                    f"Latenza media verso {target} elevata: {avg:.1f} ms (soglia {limit_ms} ms).",
                )

    def check_app_port(self, port=None):
        """
        Verifica se una porta TCP è in ascolto (es. 8080, 443).
        Se port è None, usa APP_PORT_CHECK da config (numero o lista).
        Salva risultato in data["app_server"]["ports"] e push WARN se porta chiusa.
        """
        ports_to_check = []
        if port is not None:
            ports_to_check = [int(port)]
        else:
            cfg = self.config.get("APP_PORT_CHECK")
            if cfg is None:
                return
            if isinstance(cfg, (list, tuple)):
                ports_to_check = [int(p) for p in cfg]
            else:
                ports_to_check = [int(cfg)]
        for p in ports_to_check:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect(("127.0.0.1", p))
                self.data["app_server"]["ports"][str(p)] = True
            except (socket.error, OSError, ValueError):
                self.data["app_server"]["ports"][str(p)] = False
                self._push_health(
                    "WARN",
                    "APP_PORT_CLOSED",
                    f"Porta {p} non raggiungibile (127.0.0.1). Verificare che il servizio applicativo sia attivo.",
                )

    def chaos_disk_under_load(self):
        """
        Esegue un piccolo chaos test: misura IOPS disco baseline e sotto carico CPU,
        calcolando l'impatto percentuale. Saltato se production_safe o skip_chaos.
        """
        if self.skip_chaos:
            return
        chaos = self.data["benchmark"]["chaos"]
        chaos["active"] = False

        # baseline IOPS riutilizzando la logica di disk_benchmarks ma con meno iterazioni
        baseline_cfg = dict(self.config)
        baseline_cfg["DISK_IOPS_ITERATIONS"] = max(2000, int(self.config.get("DISK_IOPS_ITERATIONS", 10000) / 4))

        iterations = baseline_cfg["DISK_IOPS_ITERATIONS"]
        seq_mb = int(self.config.get("DISK_SEQ_MB", 512))
        baseline_iops = _measure_disk_iops(iterations, seq_mb)

        stress_duration = 10
        stress_proc = multiprocessing.Process(target=_cpu_stress_worker, args=(stress_duration,))
        stress_proc.start()
        try:
            under_load_iops = _measure_disk_iops(iterations, seq_mb)
        finally:
            stress_proc.terminate()
            stress_proc.join(timeout=5)
            if stress_proc.is_alive():
                stress_proc.kill()
                stress_proc.join(timeout=2)

        if baseline_iops > 0 and under_load_iops >= 0:
            impact = max(0.0, (baseline_iops - under_load_iops) / baseline_iops * 100.0)
            chaos["active"] = True
            chaos["disk_iops_under_load"] = int(under_load_iops)
            chaos["impact_pct"] = round(impact, 1)

            if impact >= float(self.config.get("WARN_CHAOS_IMPACT_PCT", 25)):
                self._push_health(
                    "WARN",
                    "CHAOS_HIGH_IMPACT",
                    f"Impatto IOPS sotto caos elevato: -{impact:.1f}% rispetto al baseline.",
                )

    def save_results(self):
        # Re-stamp so on-disk JSON always carries current contract versions.
        stamp_audit(self.data, quick=self.quick, production_safe=self.production_safe)
        filename = f"audit_{self.data['meta']['hostname']}_{self.data['meta']['timestamp']}.json"
        target = os.path.join(self.results_dir, filename)
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)
        return target

    def get_history(self):
        """Carica tutti gli audit JSON dalla cartella results; salta file malformati."""
        history = []
        for f in os.listdir(self.results_dir):
            if not f.endswith(".json"):
                continue
            path = os.path.join(self.results_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as j:
                    data = json.load(j)
                if isinstance(data, dict) and "meta" in data:
                    history.append(data)
            except (json.JSONDecodeError, OSError):
                pass  # file corrotto o non leggibile: saltato
        return history