from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from datetime import datetime

try:
    from app_paths import get_config_dir
except ImportError:
    get_config_dir = None  # type: ignore

PROFILE_LABELS = {
    "generic": "Generico",
    "app_server": "Application Server",
    "db_server": "DB Server",
}

STATUS_COLORS = {"ok": "#16a34a", "warn": "#d97706", "crit": "#dc2626", "info": "#0284c7", "na": "#94a3b8"}
STATUS_BG = {"ok": "#dcfce7", "warn": "#fef3c7", "crit": "#fee2e2", "info": "#e0f2fe", "na": "#f1f5f9"}


class ReportGenerator:
    def __init__(self, data_list, reference=None, style="corporate"):
        if isinstance(data_list, dict):
            self.data_list = [data_list]
        else:
            self.data_list = data_list

        self.ref = reference or self._load_default_baseline()
        self.style = style
        self.colors = self._set_theme()
        self.main_d = self.data_list[-1]
        self.analyses = self._build_analyses(self.main_d)
        self.overall = self._compute_overall_score(self.analyses)

    def _set_theme(self):
        if self.style == "dark_tech":
            plt.style.use("dark_background")
            sns.set_palette("viridis")
            return {
                "p1": "#38bdf8",
                "p2": "#fb7185",
                "p3": "#34d399",
                "bg": "#0f172a",
                "text": "#f8fafc",
                "border": "#334155",
            }
        sns.set_theme(style="whitegrid")
        sns.set_palette("muted")
        return {
            "p1": "#0284c7",
            "p2": "#e11d48",
            "p3": "#10b981",
            "bg": "#ffffff",
            "text": "#1e293b",
            "border": "#e2e8f0",
        }

    def _get_val(self, source, keys, default=0):
        try:
            curr = source
            for k in keys:
                curr = curr[k]
            return curr
        except (KeyError, TypeError, IndexError):
            return default

    def _load_default_baseline(self):
        candidates = []
        if get_config_dir:
            candidates.append(get_config_dir() / "baseline.json")
        candidates.append(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
                "baseline.json",
            )
        )
        for path in candidates:
            path_str = str(path)
            if os.path.isfile(path_str):
                try:
                    with open(path_str, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass
        return None

    def _classify(self, value, good, warn, higher_is_better=True):
        if value is None or value == "" or (isinstance(value, (int, float)) and value == 0 and good > 0):
            return "na", "Dato non disponibile"
        try:
            v = float(value)
        except (TypeError, ValueError):
            return "na", "Valore non numerico"

        if higher_is_better:
            if v >= good:
                return "ok", "Nella norma / ottimo"
            if v >= warn:
                return "warn", "Sotto la soglia ideale"
            return "crit", "Critico: prestazioni insufficienti"
        if v <= good:
            return "ok", "Nella norma / ottimo"
        if v <= warn:
            return "warn", "Al limite accettabile"
        return "crit", "Critico: valore elevato"

    def _pct_vs_ref(self, current, ref_val, lower_is_better=False):
        try:
            c = float(current)
            r = float(ref_val)
        except (TypeError, ValueError):
            return None
        if r == 0:
            return None
        if lower_is_better:
            pct = ((r - c) / r) * 100.0
        else:
            pct = ((c - r) / r) * 100.0
        return round(pct, 1)

    def _ref_val(self, keys):
        if not self.ref:
            return None
        return self._get_val(self.ref, keys, default=None)

    def _metric_row(self, key, label, keys, unit, tooltip, good, warn, higher_is_better=True, fmt=None):
        value = self._get_val(self.main_d, keys, default=0)
        ref_value = self._ref_val(keys)
        status, verdict = self._classify(value, good, warn, higher_is_better=higher_is_better)

        if fmt:
            display = fmt(value)
        elif unit:
            display = f"{value} {unit}".strip()
        else:
            display = str(value)

        ref_display = None
        delta = None
        if ref_value is not None:
            ref_display = f"{ref_value} {unit}".strip() if unit else str(ref_value)
            delta = self._pct_vs_ref(value, ref_value, lower_is_better=not higher_is_better)

        return {
            "key": key,
            "label": label,
            "tooltip": tooltip,
            "value": value,
            "display": display,
            "unit": unit,
            "status": status,
            "verdict": verdict,
            "ref_display": ref_display,
            "delta_pct": delta,
            "good": good,
            "warn": warn,
            "higher_is_better": higher_is_better,
        }

    def _build_analyses(self, data):
        profile = data.get("meta", {}).get("profile", "generic")
        rows = []

        if profile == "db_server":
            db_good, db_warn = 3, 10
            iops_good, iops_warn = 8000, 3000
        else:
            db_good, db_warn = 5, 15
            iops_good, iops_warn = 5000, 2000

        rows.append(
            self._metric_row(
                "disk_write",
                "Disk Write Seq",
                ["benchmark", "disk", "seq_write_mb"],
                "MB/s",
                "Velocità scrittura sequenziale. Indica throughput massimo del volume testato.",
                250,
                100,
            )
        )
        rows.append(
            self._metric_row(
                "disk_read",
                "Disk Read Seq",
                ["benchmark", "disk", "seq_read_mb"],
                "MB/s",
                "Velocità lettura sequenziale. Importante per avvio app e lettura file grandi.",
                400,
                150,
            )
        )
        rows.append(
            self._metric_row(
                "disk_iops",
                "Disk Random IOPS",
                ["benchmark", "disk", "iops"],
                "IO/s",
                "Operazioni random 4K al secondo. Metrica chiave per database e workload transazionali.",
                iops_good,
                iops_warn,
            )
        )
        rows.append(
            self._metric_row(
                "db_latency",
                "Latenza DB simulata",
                ["benchmark", "disk", "db_sim_latency_ms"],
                "ms",
                "Latenza media su letture random 4K. Proxy per risposta storage su query DB.",
                db_good,
                db_warn,
                higher_is_better=False,
            )
        )
        rows.append(
            self._metric_row(
                "db_p99",
                "Latenza P99 disco",
                ["benchmark", "disk", "latency_p99_ms"],
                "ms",
                "Percentile 99 delle latenze disco. Picchi che impattano le transazioni lente.",
                db_good * 2,
                db_warn * 2,
                higher_is_better=False,
            )
        )
        rows.append(
            self._metric_row(
                "cpu_jitter",
                "CPU Jitter Score",
                ["benchmark", "cpu_consistency", "jitter_score"],
                "%",
                "Coerenza tempi CPU sotto carico ripetuto. 100% = jitter minimo.",
                90,
                75,
            )
        )
        stability = self._get_val(data, ["benchmark", "cpu_consistency", "stability_score"], default=0)
        if stability:
            rows.append(
                self._metric_row(
                    "cpu_stability",
                    "CPU Stability",
                    ["benchmark", "cpu_consistency", "stability_score"],
                    "%",
                    "Stabilità CPU nel tempo (varianza usage/frequenza durante stress test).",
                    80,
                    60,
                )
            )
        rows.append(
            self._metric_row(
                "crypto",
                "Crypto Hash Rate",
                ["benchmark", "cpu_real", "crypto_hash_rate"],
                "hash/s",
                "Hash SHA256 al secondo. Proxy per carico crittografico / elaborazione CPU.",
                3000,
                1500,
            )
        )
        rows.append(
            self._metric_row(
                "compress",
                "Compressione CPU",
                ["benchmark", "cpu_real", "compress_mb_s"],
                "MB/s",
                "Throughput compressione zlib. Indica capacità CPU su payload reali.",
                25,
                12,
            )
        )
        rows.append(
            self._metric_row(
                "ram_bw",
                "RAM Bandwidth",
                ["benchmark", "ram_perf", "copy_speed_gb"],
                "GB/s",
                "Velocità copia in memoria. Utile per cache, sorting e buffer applicativi.",
                2.0,
                1.0,
            )
        )
        net_avg = self._get_val(data, ["benchmark", "net", "avg_ms"], default=0)
        if net_avg > 0:
            rows.append(
                self._metric_row(
                    "net_latency",
                    "Latenza rete",
                    ["benchmark", "net", "avg_ms"],
                    "ms",
                    "Ping medio verso target configurato (es. gateway / DNS).",
                    20,
                    80,
                    higher_is_better=False,
                )
            )
            rows.append(
                self._metric_row(
                    "net_jitter",
                    "Jitter rete",
                    ["benchmark", "net", "jitter_ms"],
                    "ms",
                    "Varianza latenza ping. Valori alti indicano instabilità di rete.",
                    3,
                    15,
                    higher_is_better=False,
                )
            )

        chaos_active = self._get_val(data, ["benchmark", "chaos", "active"], default=False)
        chaos_impact = self._get_val(data, ["benchmark", "chaos", "impact_pct"], default=0)
        if chaos_active:
            if chaos_impact <= 0:
                status, verdict = "info", "Nessun degrado misurato (possibile cache OS)"
            elif chaos_impact < 15:
                status, verdict = "ok", "Degrado IOPS contenuto sotto stress CPU"
            elif chaos_impact < 35:
                status, verdict = "warn", "Degrado IOPS moderato sotto stress CPU"
            else:
                status, verdict = "crit", "Forte degrado IOPS quando la CPU è sotto carico"
            rows.append(
                {
                    "key": "chaos",
                    "label": "Chaos Impact",
                    "tooltip": "Calo IOPS disco misurato mentre un worker satura la CPU.",
                    "value": chaos_impact,
                    "display": f"{chaos_impact} %",
                    "unit": "%",
                    "status": status,
                    "verdict": verdict,
                    "ref_display": self._ref_val(["benchmark", "chaos", "impact_pct"]),
                    "delta_pct": None,
                    "good": 15,
                    "warn": 35,
                    "higher_is_better": False,
                }
            )

        cpu_q = self._get_val(data, ["virtualization", "cpu_queue_length"], default=0)
        if cpu_q > 0:
            rows.append(
                self._metric_row(
                    "cpu_queue",
                    "CPU Queue Length",
                    ["virtualization", "cpu_queue_length"],
                    "tasks",
                    "Processi in attesa di CPU. >2 per core suggerisce contenzione.",
                    2,
                    6,
                    higher_is_better=False,
                )
            )

        ram_used = self._get_val(data, ["ram_hw", "percent_used"], default=0)
        if ram_used:
            rows.append(
                self._metric_row(
                    "ram_used",
                    "Utilizzo RAM",
                    ["ram_hw", "percent_used"],
                    "%",
                    "Percentuale RAM in uso al momento del test.",
                    75,
                    90,
                    higher_is_better=False,
                )
            )

        swap_used = self._get_val(data, ["ram_hw", "swap_percent"], default=0)
        if swap_used > 0:
            rows.append(
                self._metric_row(
                    "swap_used",
                    "Utilizzo Swap",
                    ["ram_hw", "swap_percent"],
                    "%",
                    "Uso swap/pagefile: indica pressione memoria oltre la RAM fisica.",
                    10,
                    40,
                    higher_is_better=False,
                )
            )

        disk_used = self._get_val(data, ["disk_hw", "percent_used"], default=0)
        if disk_used:
            rows.append(
                self._metric_row(
                    "disk_used",
                    "Spazio disco usato",
                    ["disk_hw", "percent_used"],
                    "%",
                    "Riempimento volume di sistema / test.",
                    75,
                    90,
                    higher_is_better=False,
                )
            )

        return rows

    def _compute_overall_score(self, analyses):
        scorable = [a for a in analyses if a["status"] != "na"]
        if not scorable:
            return {"score": 0, "grade": "N/A", "status": "na"}

        weights = {"ok": 100, "info": 90, "warn": 55, "crit": 20}
        score = sum(weights.get(a["status"], 50) for a in scorable) / len(scorable)
        score = round(score, 1)

        if score >= 85:
            grade, status = "A", "ok"
        elif score >= 70:
            grade, status = "B", "ok"
        elif score >= 55:
            grade, status = "C", "warn"
        else:
            grade, status = "D", "crit"
        return {"score": score, "grade": grade, "status": status}

    def _executive_summary(self):
        data = self.main_d
        profile = data.get("meta", {}).get("profile", "generic")
        bullets = []
        crits = [a for a in self.analyses if a["status"] == "crit"]
        warns = [a for a in self.analyses if a["status"] == "warn"]
        oks = [a for a in self.analyses if a["status"] == "ok"]

        bullets.append(
            f"Punteggio complessivo <b>{self.overall['score']}/100</b> (classe <b>{self.overall['grade']}</b>) "
            f"su profilo <b>{PROFILE_LABELS.get(profile, profile)}</b>."
        )
        if oks:
            top = sorted(oks, key=lambda x: x.get("value", 0), reverse=True)[:2]
            bullets.append(
                "Punti di forza: "
                + ", ".join(f"<b>{m['label']}</b> ({m['display']})" for m in top[:2])
                + "."
            )
        if crits:
            bullets.append(
                "<span style='color:#dc2626'>Criticità:</span> "
                + ", ".join(f"<b>{m['label']}</b> — {m['verdict']}" for m in crits[:3])
                + "."
            )
        elif warns:
            bullets.append(
                "<span style='color:#d97706'>Attenzione:</span> "
                + ", ".join(f"<b>{m['label']}</b>" for m in warns[:3])
                + " da monitorare."
            )
        else:
            bullets.append("Nessuna criticità rilevata sulle metriche benchmarkate.")

        events = data.get("health", {}).get("events", [])
        if events:
            bullets.append(f"Rilevati <b>{len(events)}</b> eventi health (vedi sezione dedicata).")

        if profile == "db_server":
            lat = self._get_val(data, ["benchmark", "disk", "db_sim_latency_ms"], default=0)
            if lat and lat > 5:
                bullets.append(
                    f"Per un DB server la latenza storage simulata ({lat} ms) andrebbe idealmente sotto 5 ms."
                )
        elif profile == "app_server":
            ports = data.get("app_server", {}).get("ports", {})
            closed = [p for p, ok in ports.items() if not ok]
            if closed:
                bullets.append(f"Porte applicative non raggiungibili: <b>{', '.join(closed)}</b>.")

        return bullets

    def _recommendations(self):
        data = self.main_d
        profile = data.get("meta", {}).get("profile", "generic")
        recs = []

        for a in self.analyses:
            if a["status"] == "crit":
                if a["key"] == "db_latency":
                    recs.append("Verificare storage (SAN/volume dati), driver, policy cache e antimalware on-access sul percorso DB.")
                elif a["key"] == "disk_iops":
                    recs.append("Valutare upgrade storage o spostamento workload I/O su volume più performante.")
                elif a["key"] == "cpu_queue":
                    recs.append("CPU satura: verificare affinity, numero vCPU VM, processi in background e piano energetico.")
                elif a["key"] == "chaos":
                    recs.append("Forte interferenza CPU/I/O: ridurre carico concorrente o separare volumi OS e dati.")
                elif a["key"] == "ram_used" or a["key"] == "swap_used":
                    recs.append("Memoria sotto pressione: aumentare RAM VM o ridurre footprint applicativo / heap JVM.")
                elif a["key"] == "disk_used":
                    recs.append("Spazio disco in esaurimento: pianificare pulizia log, backup e resize volume.")

        for ev in data.get("health", {}).get("events", []):
            code = ev.get("code", "")
            if code == "POWER_PLAN_NOT_HIGH_PERF":
                recs.append("Impostare piano energetico 'Alte prestazioni' su server produzione.")
            elif code == "APP_PORT_CLOSED":
                recs.append("Verificare che il servizio applicativo (Tomcat/IIS) sia avviato e in ascolto.")
            elif code == "DB_LATENCY_HIGH":
                recs.append("Latenza disco elevata per profilo DB: controllare LUN, RAID, queue depth e antivirus.")
            elif code == "NET_PING_FAILED":
                recs.append("Ping fallito: verificare firewall, routing e connettività verso il target configurato.")

        if profile == "db_server" and not recs:
            recs.append("Profilo DB: monitorare latenza storage e mantenere il test su DISK_TEST_PATH = volume dati.")
        if profile == "app_server" and not recs:
            recs.append("Profilo App: ripetere il test con servizio attivo e APP_PORT_CHECK configurato.")

        if not recs:
            recs.append("Sistema allineato alle soglie attuali. Ripetere il benchmark dopo cambi infrastrutturali.")
        return recs[:8]

    def _prepare_dataframe(self):
        self.flat_df = pd.json_normalize(self.data_list)
        rows = []
        for d in self.data_list:
            rows.append(
                {
                    "Host": d.get("meta", {}).get("hostname", "N/A"),
                    "Disk Write (MB/s)": self._get_val(d, ["benchmark", "disk", "seq_write_mb"]),
                    "Disk Read (MB/s)": self._get_val(d, ["benchmark", "disk", "seq_read_mb"]),
                    "IOPS": self._get_val(d, ["benchmark", "disk", "iops"]),
                    "Lat. DB (ms)": self._get_val(d, ["benchmark", "disk", "db_sim_latency_ms"]),
                    "CPU Stability (%)": self._get_val(d, ["benchmark", "cpu_consistency", "jitter_score"]),
                    "Chaos Impact (%)": self._get_val(d, ["benchmark", "chaos", "impact_pct"]),
                    "Net Latency (ms)": self._get_val(d, ["benchmark", "net", "avg_ms"]),
                }
            )
        return pd.DataFrame(rows)

    def export_presentation_assets(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        df = self._prepare_dataframe()
        self._plot_bar_comparison(
            df,
            ["Disk Read (MB/s)", "Disk Write (MB/s)"],
            "Analisi Throughput Storage",
            os.path.join(output_dir, "01_comparison_disk.png"),
        )
        self._plot_bar_comparison(
            df,
            ["IOPS"],
            "Performance Transazionali (IOPS)",
            os.path.join(output_dir, "02_comparison_iops.png"),
        )
        self._plot_bar_comparison(
            df,
            ["Chaos Impact (%)"],
            "Degrado Performance sotto Carico",
            os.path.join(output_dir, "03_comparison_chaos.png"),
        )
        if len(self.data_list) > 1:
            self._plot_radar_comparison(os.path.join(output_dir, "04_radar_comparison.png"))
        self._plot_cpu_thermal_analysis(self.main_d, os.path.join(output_dir, "05_thermal_analysis.png"))
        self._plot_scorecard(output_dir)

    def _plot_scorecard(self, output_dir):
        labels = [a["label"][:18] for a in self.analyses if a["status"] != "na"][:12]
        scores = []
        status_map = {"ok": 100, "info": 90, "warn": 55, "crit": 20, "na": 0}
        for a in self.analyses:
            if a["status"] == "na":
                continue
            scores.append(status_map.get(a["status"], 50))
            if len(scores) >= 12:
                break
        if not labels:
            return
        plt.figure(figsize=(10, max(4, len(labels) * 0.35)))
        colors = [STATUS_COLORS.get(a["status"], "#94a3b8") for a in self.analyses if a["status"] != "na"][:12]
        plt.barh(labels, scores, color=colors)
        plt.xlabel("Score qualitativo")
        plt.title(f"Scorecard metriche — {self.main_d.get('meta', {}).get('hostname', 'N/A')}")
        plt.xlim(0, 105)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "06_scorecard.png"), dpi=300)
        plt.close()

    def _plot_bar_comparison(self, df, metrics, title, path):
        df_melted = df.melt(id_vars="Host", value_vars=metrics, var_name="Metrica", value_name="Valore")
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(data=df_melted, x="Host", y="Valore", hue="Metrica")
        plt.title(title, fontsize=14, fontweight="bold", pad=20)
        plt.xticks(rotation=15)
        for p in ax.patches:
            if p.get_height() > 0:
                ax.annotate(
                    f"{p.get_height():.1f}",
                    (p.get_x() + p.get_width() / 2.0, p.get_height()),
                    ha="center",
                    va="center",
                    fontsize=9,
                    xytext=(0, 7),
                    textcoords="offset points",
                    fontweight="bold",
                )
        plt.tight_layout()
        plt.savefig(path, dpi=300, transparent=(self.style == "dark_tech"))
        plt.close()

    def _plot_cpu_thermal_analysis(self, data, path):
        series = data.get("benchmark", {}).get("cpu_series", {})
        if not series.get("time"):
            return
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.set_xlabel("Secondi")
        ax1.set_ylabel("CPU Usage %", color=self.colors["p1"])
        ax1.plot(series["time"], series.get("usage", []), color=self.colors["p1"], linewidth=2)
        ax1.fill_between(series["time"], series.get("usage", []), color=self.colors["p1"], alpha=0.1)
        ax1.set_ylim(0, 105)
        ax2 = ax1.twinx()
        ax2.set_ylabel("Clock (MHz)", color=self.colors["p2"])
        ax2.plot(series["time"], series.get("freq", []), color=self.colors["p2"], linestyle="--")
        hostname = data.get("meta", {}).get("hostname", "N/A")
        plt.title(f"Thermal / Stability Check: {hostname}")
        fig.tight_layout()
        plt.savefig(path, dpi=300)
        plt.close()

    def _plot_radar_comparison(self, path):
        categories = ["Disk", "IOPS", "CPU", "Chaos", "Net"]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        for d in self.data_list:
            seq_w = self._get_val(d, ["benchmark", "disk", "seq_write_mb"])
            iops = self._get_val(d, ["benchmark", "disk", "iops"])
            jitter = self._get_val(d, ["benchmark", "cpu_consistency", "jitter_score"])
            chaos_pct = self._get_val(d, ["benchmark", "chaos", "impact_pct"])
            net_ms = self._get_val(d, ["benchmark", "net", "avg_ms"])
            values = [
                min(100, (seq_w / 5) if seq_w else 0),
                min(100, (iops / 150) if iops else 0),
                jitter,
                max(0, 100 - max(0, chaos_pct)),
                max(0, 100 - net_ms) if net_ms else 50,
            ]
            values += values[:1]
            ax.plot(angles, values, linewidth=2, label=d.get("meta", {}).get("hostname", "N/A"))
            ax.fill(angles, values, alpha=0.1)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        plt.xticks(angles[:-1], categories)
        plt.title("Performance Balance Matrix", pad=20, fontweight="bold")
        plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
        plt.savefig(path, dpi=300)
        plt.close()

    def _badge(self, status, text):
        color = STATUS_COLORS.get(status, "#94a3b8")
        bg = STATUS_BG.get(status, "#f1f5f9")
        return (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;'
            f'font-size:11px;font-weight:700;color:{color};background:{bg}">{text}</span>'
        )

    def _delta_html(self, delta):
        if delta is None:
            return ""
        color = "#16a34a" if delta >= 0 else "#dc2626"
        sign = "+" if delta > 0 else ""
        return f'<div style="color:{color};font-size:11px;font-weight:bold;">{sign}{delta}% vs Ref</div>'

    def render(self):
        data = self.main_d
        meta = data.get("meta", {})
        sys_info = data.get("sys_info", {})
        ram = data.get("ram_hw", {})
        disk_hw = data.get("disk_hw", {})
        virt = data.get("virtualization", {})
        bench = data.get("benchmark", {})
        profile = meta.get("profile", "generic")

        c_series = bench.get("cpu_series", {})
        c_time = json.dumps(c_series.get("time", []))
        c_usage = json.dumps(c_series.get("usage", []))
        c_freq = json.dumps(c_series.get("freq", []))

        hostname = meta.get("hostname", "N/A")
        ref_mode = "ACTIVE (vs baseline)" if self.ref else ("COMPARE (" + str(len(self.data_list)) + " host)" if len(self.data_list) > 1 else "SINGLE RUN")

        summary_html = "".join(f"<li>{b}</li>" for b in self._executive_summary())
        recs_html = "".join(f"<li>{r}</li>" for r in self._recommendations())

        metric_rows = ""
        for m in self.analyses:
            ref_cell = (
                f'<div style="color:#94a3b8;font-size:10px;">Target: {m["ref_display"]}</div>'
                if m.get("ref_display") is not None
                else ""
            )
            metric_rows += f"""
            <tr>
                <td><span title="{m['tooltip']}" style="border-bottom:1px dotted #94a3b8;cursor:help;">{m['label']}</span></td>
                <td>
                    <b>{m['display']}</b>
                    {self._delta_html(m.get('delta_pct'))}
                    <div style="margin-top:4px;">{self._badge(m['status'], m['verdict'])}</div>
                </td>
                <td style="text-align:right">{ref_cell}</td>
            </tr>"""

        health_events = data.get("health", {}).get("events", [])
        health_html = ""
        if health_events:
            ev_rows = ""
            for ev in health_events:
                lvl = ev.get("level", "INFO").lower()
                st = "crit" if lvl == "crit" else ("warn" if lvl == "warn" else "info")
                ev_rows += f"""
                <tr>
                    <td>{self._badge(st, ev.get('level', 'INFO'))}</td>
                    <td><code>{ev.get('code', '')}</code></td>
                    <td>{ev.get('message', '')}</td>
                    <td style="font-size:11px;color:#64748b">{ev.get('timestamp', '')}</td>
                </tr>"""
            health_html = f"""
            <div class="card alert-card">
                <h3>Eventi Health ({len(health_events)})</h3>
                <table><thead><tr><th>Livello</th><th>Codice</th><th>Messaggio</th><th>Ora</th></tr></thead>
                <tbody>{ev_rows}</tbody></table>
            </div>"""

        ports = data.get("app_server", {}).get("ports", {})
        ports_html = ""
        if ports:
            pr = ""
            for port, ok in ports.items():
                pr += f"<tr><td>{port}</td><td>{self._badge('ok' if ok else 'crit', 'OPEN' if ok else 'CLOSED')}</td></tr>"
            ports_html = f"""
            <div class="card"><h3>Porte applicative</h3>
            <table><thead><tr><th>Porta</th><th>Stato</th></tr></thead><tbody>{pr}</tbody></table></div>"""

        comp_rows = ""
        if len(self.data_list) > 1:
            for d in self.data_list:
                h = d.get("meta", {}).get("hostname", "N/A")
                comp_rows += f"""<tr>
                    <td>{h}</td>
                    <td>{self._get_val(d, ['benchmark','disk','seq_write_mb'])} MB/s</td>
                    <td>{self._get_val(d, ['benchmark','disk','seq_read_mb'])} MB/s</td>
                    <td>{self._get_val(d, ['benchmark','disk','iops'])}</td>
                    <td>{self._get_val(d, ['benchmark','cpu_consistency','jitter_score'])}%</td>
                    <td>{self._get_val(d, ['benchmark','chaos','impact_pct'])}%</td>
                </tr>"""

        comparison_section = ""
        if comp_rows:
            comparison_section = f"""
            <div class="card"><h3>Comparativa host ({len(self.data_list)})</h3>
            <table><thead><tr><th>Host</th><th>Write</th><th>Read</th><th>IOPS</th><th>CPU Stab.</th><th>Chaos</th></tr></thead>
            <tbody>{comp_rows}</tbody></table></div>"""

        ram_speed = ram.get("speed_mhz") or 0
        ram_speed_txt = f"{ram_speed} MHz" if ram_speed else "n/d"

        score_status = self.overall["status"]
        return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>Audit — {hostname}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#f8fafc; --card:#fff; --primary:#0284c7; --border:#e2e8f0; --muted:#64748b; }}
body {{ font-family:'Inter',sans-serif; background:var(--bg); color:#1e293b; margin:0; padding:32px; line-height:1.5; }}
.container {{ max-width:1200px; margin:auto; }}
.header {{ display:flex; justify-content:space-between; gap:20px; border-bottom:2px solid var(--border); padding-bottom:20px; margin-bottom:24px; }}
h1 {{ margin:0 0 6px; font-size:26px; color:#0f172a; }}
.sub {{ color:var(--muted); font-size:14px; }}
.sys-box {{ background:#f1f5f9; border:1px solid var(--border); border-radius:8px; padding:12px 14px; font-size:12px; margin-top:12px; }}
.score-box {{ text-align:center; min-width:120px; padding:12px 16px; border-radius:12px; border:1px solid var(--border); background:#fff; }}
.score-val {{ font-family:'Roboto Mono',monospace; font-size:34px; font-weight:700; color:{STATUS_COLORS.get(score_status,'#0284c7')}; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-bottom:20px; }}
.grid-2 {{ display:grid; grid-template-columns:1.4fr 1fr; gap:16px; margin-bottom:20px; }}
@media (max-width:900px) {{ .grid-2 {{ grid-template-columns:1fr; }} .header {{ flex-direction:column; }} }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,.05); margin-bottom:16px; }}
.alert-card {{ border-left:5px solid #dc2626; }}
h3 {{ margin:0 0 12px; font-size:16px; color:#0f172a; border-bottom:1px solid var(--border); padding-bottom:8px; }}
.label {{ font-size:11px; text-transform:uppercase; color:var(--muted); font-weight:700; letter-spacing:.4px; }}
.val {{ font-family:'Roboto Mono',monospace; font-size:26px; font-weight:600; color:#0f172a; }}
.desc {{ font-size:11px; color:var(--muted); margin-top:6px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:10px 8px; border-bottom:1px solid #f1f5f9; text-align:left; vertical-align:top; }}
th {{ font-size:11px; text-transform:uppercase; color:var(--muted); }}
.chart-box {{ height:340px; }}
ul {{ margin:8px 0 0 18px; padding:0; }}
li {{ margin-bottom:6px; }}
</style></head><body><div class="container">
<div class="header">
  <div>
    <h1>Extreme Audit v5 — Report Tecnico</h1>
    <div class="sub"><b>{hostname}</b> · {meta.get('date','N/A')} · Admin: {'Sì' if meta.get('is_admin') else 'No'}</div>
    <div class="sys-box">
      <div><b>CPU:</b> {sys_info.get('cpu_model','N/A')} ({sys_info.get('cores','N/A')})</div>
      <div><b>OS:</b> {sys_info.get('os','N/A')} · Uptime: {sys_info.get('uptime','N/A')}</div>
      <div><b>RAM:</b> {ram.get('total_gb',0)} GB ({ram.get('percent_used',0)}% usata, {ram_speed_txt}) ·
           <b>Disco:</b> {disk_hw.get('free_gb',0)}/{disk_hw.get('total_gb',0)} GB liberi ({disk_hw.get('percent_used',0)}% usato)</div>
      <div><b>VM:</b> {'Sì' if virt.get('is_vm') else 'No'}{(' · ' + virt.get('hypervisor','')) if virt.get('is_vm') else ''} ·
           <b>NUMA:</b> {sys_info.get('numa_nodes',1)} · <b>Power:</b> {sys_info.get('power_plan','N/A')}</div>
      <div><b>Profilo:</b> {PROFILE_LABELS.get(profile, profile)} · <b>Ctx switches/s:</b> {virt.get('ctx_switches_sec',0)} · <b>CPU queue:</b> {virt.get('cpu_queue_length',0)}</div>
    </div>
  </div>
  <div>
    <div class="sub" style="text-align:right;font-weight:600;">{ref_mode}</div>
    <div class="score-box">
      <div class="label">Health Score</div>
      <div class="score-val">{self.overall['score']}</div>
      <div class="label">Classe {self.overall['grade']}</div>
    </div>
  </div>
</div>

<div class="card">
  <h3>Executive Summary</h3>
  <ul>{summary_html}</ul>
</div>

<div class="grid">
  <div class="card"><div class="label">Disk Write</div><div class="val" style="color:var(--primary)">{bench.get('disk',{}).get('seq_write_mb',0)} <small style="font-size:14px">MB/s</small></div></div>
  <div class="card"><div class="label">Disk Read</div><div class="val">{bench.get('disk',{}).get('seq_read_mb',0)} <small style="font-size:14px">MB/s</small></div></div>
  <div class="card"><div class="label">IOPS</div><div class="val">{bench.get('disk',{}).get('iops',0)}</div></div>
  <div class="card"><div class="label">CPU Jitter</div><div class="val">{bench.get('cpu_consistency',{}).get('jitter_score',0)}%</div></div>
  <div class="card"><div class="label">RAM BW</div><div class="val">{bench.get('ram_perf',{}).get('copy_speed_gb',0)} <small style="font-size:14px">GB/s</small></div></div>
  <div class="card"><div class="label">Net Latency</div><div class="val">{bench.get('net',{}).get('avg_ms',0) or 'n/d'} <small style="font-size:14px">ms</small></div></div>
</div>

{health_html}
{comparison_section}

<div class="grid-2">
  <div class="card">
    <h3>Analisi metriche</h3>
    <table><thead><tr><th>Metrica</th><th>Valore / Valutazione</th><th style="text-align:right">Baseline</th></tr></thead>
    <tbody>{metric_rows}</tbody></table>
  </div>
  <div>
    {ports_html}
    <div class="card">
      <h3>Infrastructure snapshot</h3>
      <table>
        <tr><td>Swap</td><td><b>{ram.get('swap_percent',0)}%</b></td></tr>
        <tr><td>Crypto hash/s</td><td><b>{bench.get('cpu_real',{}).get('crypto_hash_rate',0)}</b></td></tr>
        <tr><td>Compressione</td><td><b>{bench.get('cpu_real',{}).get('compress_mb_s',0)} MB/s</b></td></tr>
        <tr><td>Chaos IOPS sotto carico</td><td><b>{bench.get('chaos',{}).get('disk_iops_under_load',0)}</b></td></tr>
        <tr><td>CPU avg task</td><td><b>{bench.get('cpu_consistency',{}).get('avg_task_ms',0)} ms</b></td></tr>
        <tr><td>Stability score</td><td><b>{bench.get('cpu_consistency',{}).get('stability_score','n/d')}</b></td></tr>
      </table>
    </div>
    <div class="card">
      <h3>Raccomandazioni</h3>
      <ul>{recs_html}</ul>
    </div>
  </div>
</div>

<div class="card">
  <h3>CPU Load vs Frequenza (stress test)</h3>
  <div class="chart-box"><canvas id="cpuChart"></canvas></div>
</div>

<script>
const ctx = document.getElementById('cpuChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {c_time},
    datasets: [
      {{ label: 'CPU %', data: {c_usage}, borderColor: '#dc2626', backgroundColor: 'rgba(220,38,38,0.06)', fill: true, tension: 0.3, pointRadius: 0 }},
      {{ label: 'MHz', data: {c_freq}, borderColor: '#64748b', borderDash: [5,5], pointRadius: 0, yAxisID: 'y1' }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    scales: {{
      y: {{ min: 0, max: 100, title: {{ display: true, text: 'CPU %' }} }},
      y1: {{ position: 'right', grid: {{ display: false }}, title: {{ display: true, text: 'MHz' }} }}
    }}
  }}
}});
</script>
</div></body></html>"""
