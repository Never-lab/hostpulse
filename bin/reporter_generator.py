from __future__ import annotations

import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

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
            f'<span class="badge badge-{status}" style="color:{color};background:{bg}">{text}</span>'
        )

    def _status_counts(self):
        counts = {"ok": 0, "warn": 0, "crit": 0, "info": 0, "na": 0}
        for a in self.analyses:
            counts[a["status"]] = counts.get(a["status"], 0) + 1
        return counts

    def _verdict_headline(self):
        grade = self.overall["grade"]
        score = self.overall["score"]
        crits = sum(1 for a in self.analyses if a["status"] == "crit")
        warns = sum(1 for a in self.analyses if a["status"] == "warn")
        if grade == "A":
            return "Infrastruttura in ottime condizioni", "ok"
        if grade == "B":
            return "Infrastruttura solida, margini di ottimizzazione limitati", "ok"
        if grade == "C":
            return f"Prestazioni accettabili con {warns} area/e da monitorare", "warn"
        if crits:
            return f"Intervento consigliato: {crits} criticità rilevate", "crit"
        return f"Prestazioni sotto soglia (score {score}/100)", "crit"

    def _score_ring_svg(self):
        score = float(self.overall["score"])
        grade = self.overall["grade"]
        status = self.overall["status"]
        color = STATUS_COLORS.get(status, "#0284c7")
        r = 52
        c = 2 * 3.14159 * r
        offset = c * (1.0 - max(0.0, min(100.0, score)) / 100.0)
        return f"""<svg class="score-ring" viewBox="0 0 120 120" width="132" height="132" role="img" aria-label="Health score {score}">
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="#e2e8f0" stroke-width="9"/>
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="{color}" stroke-width="9"
    stroke-dasharray="{c:.1f}" stroke-dashoffset="{offset:.1f}"
    transform="rotate(-90 60 60)" stroke-linecap="round"/>
  <text x="60" y="54" text-anchor="middle" font-size="30" font-weight="700" fill="{color}">{grade}</text>
  <text x="60" y="74" text-anchor="middle" font-size="12" fill="#64748b">{score}/100</text>
</svg>"""

    def _analysis_map(self):
        return {a["key"]: a for a in self.analyses}

    def _kpi_cards_html(self, bench):
        amap = self._analysis_map()
        cards = [
            ("disk_write", "Scrittura disco", bench.get("disk", {}).get("seq_write_mb", 0), "MB/s"),
            ("disk_read", "Lettura disco", bench.get("disk", {}).get("seq_read_mb", 0), "MB/s"),
            ("disk_iops", "IOPS random", bench.get("disk", {}).get("iops", 0), ""),
            ("cpu_jitter", "CPU jitter", bench.get("cpu_consistency", {}).get("jitter_score", 0), "%"),
            ("ram_bw", "Bandwidth RAM", bench.get("ram_perf", {}).get("copy_speed_gb", 0), "GB/s"),
            ("net_latency", "Latenza rete", bench.get("net", {}).get("avg_ms", 0) or "n/d", "ms"),
        ]
        html = ""
        for key, label, val, unit in cards:
            st = amap.get(key, {}).get("status", "na")
            suffix = f' <span class="kpi-unit">{unit}</span>' if unit and val != "n/d" else ""
            html += f"""
            <div class="kpi-card kpi-{st}">
              <div class="kpi-label">{label}</div>
              <div class="kpi-val">{val}{suffix}</div>
            </div>"""
        return html

    def _grouped_metrics_html(self):
        categories = [
            ("Storage & I/O", ["disk_write", "disk_read", "disk_iops", "db_latency", "db_p99", "chaos", "disk_used"]),
            ("CPU", ["cpu_jitter", "cpu_stability", "crypto", "compress", "cpu_queue"]),
            ("Memoria", ["ram_bw", "ram_used", "swap_used"]),
            ("Rete", ["net_latency", "net_jitter"]),
        ]
        amap = self._analysis_map()
        html = ""
        for title, keys in categories:
            rows = [amap[k] for k in keys if k in amap]
            if not rows:
                continue
            body = ""
            for m in rows:
                ref_cell = (
                    f'<span class="ref-tag">Target {m["ref_display"]}</span>'
                    if m.get("ref_display") is not None
                    else '<span class="ref-tag muted">—</span>'
                )
                body += f"""
                <tr class="row-{m['status']}">
                  <td><span class="metric-name" title="{m['tooltip']}">{m['label']}</span></td>
                  <td class="metric-val"><strong>{m['display']}</strong>{self._delta_html(m.get('delta_pct'))}</td>
                  <td>{self._badge(m['status'], m['verdict'])}</td>
                  <td class="ref-col">{ref_cell}</td>
                </tr>"""
            html += f"""
            <div class="metric-group">
              <h4>{title}</h4>
              <table>
                <thead><tr><th>Metrica</th><th>Valore</th><th>Valutazione</th><th>Baseline</th></tr></thead>
                <tbody>{body}</tbody>
              </table>
            </div>"""
        return html

    def _delta_html(self, delta):
        if delta is None:
            return ""
        cls = "delta-up" if delta >= 0 else "delta-down"
        sign = "+" if delta > 0 else ""
        return f'<div class="delta {cls}">{sign}{delta}% vs ref</div>'

    def _run_flags_label(self, meta):
        flags = []
        if meta.get("quick"):
            flags.append("Quick")
        if meta.get("production_safe"):
            flags.append("Production-safe")
        return " · ".join(flags) if flags else "Full load"

    def _how_to_read(self, profile):
        profile_note = {
            "db_server": "Profilo DB Server: soglie più strette su latenza/IOPS disco (workload transazionale).",
            "app_server": "Profilo Application Server: oltre alle metriche host, verifica porte applicative se configurate.",
            "generic": "Profilo Generico: soglie bilanciate per una VM generica.",
        }.get(profile, "Profilo personalizzato.")
        return (
            "<ul>"
            f"<li>{profile_note}</li>"
            "<li><b>Health Score</b> aggrega le metriche scorable (OK/WARN/CRIT) in un voto 0–100 e una classe A–D.</li>"
            "<li>I badge verde/arancio/rosso confrontano il valore misurato con soglie interne (e con la baseline se presente).</li>"
            "<li>Gli eventi Health sono segnali contestuali (piano energetico, VM, porte chiuse, ecc.), non un secondo score.</li>"
            "<li>Questo HTML è self-contained: si apre offline anche su Server senza accesso Internet.</li>"
            "</ul>"
        )

    def _downsample_series(self, times, usage, freq, max_pts=150):
        n = len(times)
        if n <= max_pts:
            return times, usage, freq
        idx = [int(round(i * (n - 1) / (max_pts - 1))) for i in range(max_pts)]
        return [times[i] for i in idx], [usage[i] for i in idx], [freq[i] for i in idx]

    def _nice_step(self, span, target_ticks=6):
        if span <= 0:
            return 1.0
        raw = span / target_ticks
        mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
        norm = raw / mag
        if norm <= 1:
            nice = 1
        elif norm <= 2:
            nice = 2
        elif norm <= 5:
            nice = 5
        else:
            nice = 10
        return nice * mag

    def _cpu_series_svg(self, series, width=820, height=300):
        times = list(series.get("time") or [])
        usage = [float(u) for u in (series.get("usage") or [])]
        freq = [float(f) for f in (series.get("freq") or [])]
        n = min(len(times), len(usage))
        if n < 2:
            return "<p class='muted'>Nessuna serie CPU disponibile per questo run.</p>"

        times, usage, freq = self._downsample_series(times[:n], usage[:n], (freq + [0.0] * n)[:n])
        n = len(times)
        t0, t1 = float(times[0]), float(times[-1])
        span = max(t1 - t0, 1e-6)

        avg_u = sum(usage) / n
        max_u = max(usage)
        min_u = min(usage)
        max_i = usage.index(max_u)

        pad_l, pad_r, pad_t, pad_b = 54, 20, 52, 44
        plot_w = width - pad_l - pad_r
        plot_h = height - pad_t - pad_b

        def x_at(t):
            return pad_l + ((float(t) - t0) / span) * plot_w

        def y_usage(u):
            return pad_t + (1.0 - max(0.0, min(100.0, float(u))) / 100.0) * plot_h

        usage_pts = " ".join(f"{x_at(t):.1f},{y_usage(u):.1f}" for t, u in zip(times, usage))
        area_pts = f"{pad_l},{pad_t + plot_h} {usage_pts} {pad_l + plot_w},{pad_t + plot_h}"

        grid_lines = ""
        for pct in (0, 25, 50, 75, 100):
            y = y_usage(pct)
            grid_lines += f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + plot_w}" y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1"/>'
            grid_lines += (
                f'<text x="{pad_l - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="10" fill="#94a3b8">{pct}%</text>'
            )

        x_step = self._nice_step(span, 5)
        x_tick = t0
        x_labels = ""
        while x_tick <= t1 + 0.01:
            x = x_at(x_tick)
            x_labels += f'<line x1="{x:.1f}" y1="{pad_t + plot_h}" x2="{x:.1f}" y2="{pad_t + plot_h + 4}" stroke="#cbd5e1"/>'
            x_labels += (
                f'<text x="{x:.1f}" y="{pad_t + plot_h + 16}" text-anchor="middle" font-size="10" fill="#94a3b8">{x_tick:.0f}s</text>'
            )
            x_tick += x_step

        peak_x, peak_y = x_at(times[max_i]), y_usage(max_u)
        dots = ""
        if n <= 24:
            for t, u in zip(times, usage):
                dots += f'<circle cx="{x_at(t):.1f}" cy="{y_usage(u):.1f}" r="3.5" fill="#0284c7" stroke="#fff" stroke-width="1.5"/>'

        avg_y = y_usage(avg_u)
        freq_panel = ""
        freq_vals = [f for f in freq if f > 0]
        if len(freq_vals) >= 2 and (max(freq_vals) - min(freq_vals)) >= 50:
            fmin, fmax = min(freq_vals), max(freq_vals)
            fspan = max(fmax - fmin, 1.0)
            fh = 88
            fy0 = height + 28
            def y_freq(f):
                return fy0 + (1.0 - (float(f) - fmin) / fspan) * (fh - 20)

            freq_pts = " ".join(
                f"{x_at(t):.1f},{y_freq(f):.1f}" for t, f in zip(times, freq) if f > 0
            )
            f_mid = int((fmin + fmax) / 2)
            freq_panel = f"""
<g transform="translate(0,{height + 8})">
  <text x="{pad_l}" y="14" font-size="12" font-weight="600" fill="#475569">Frequenza CPU</text>
  <text x="{pad_l + plot_w}" y="14" text-anchor="end" font-size="11" fill="#94a3b8">{fmin:.0f}–{fmax:.0f} MHz</text>
  <rect x="{pad_l}" y="22" width="{plot_w}" height="{fh}" fill="#f8fafc" stroke="#e2e8f0" rx="6"/>
  <text x="{pad_l - 8}" y="{22 + 14}" text-anchor="end" font-size="9" fill="#94a3b8">{fmax:.0f}</text>
  <text x="{pad_l - 8}" y="{22 + fh - 6}" text-anchor="end" font-size="9" fill="#94a3b8">{fmin:.0f}</text>
  <text x="{pad_l - 8}" y="{22 + fh/2 + 4}" text-anchor="end" font-size="9" fill="#94a3b8">{f_mid}</text>
  <line x1="{pad_l}" y1="{22 + fh/2}" x2="{pad_l + plot_w}" y2="{22 + fh/2}" stroke="#e2e8f0" stroke-dasharray="4 4"/>
  <polyline fill="none" stroke="#f59e0b" stroke-width="2" points="{freq_pts}"/>
</g>"""
            total_h = height + 8 + fh + 36
        else:
            total_h = height

        return f"""
<svg viewBox="0 0 {width} {total_h}" width="100%" height="{total_h}" role="img" aria-label="CPU load during stress test" class="cpu-chart">
  <defs>
    <linearGradient id="cpuFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0284c7" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.04"/>
    </linearGradient>
  </defs>
  <text x="{pad_l}" y="20" font-size="13" font-weight="700" fill="#0f172a">Utilizzo CPU durante stress test</text>
  <text x="{pad_l + plot_w}" y="20" text-anchor="end" font-size="11" fill="#64748b">
    Media <tspan font-weight="700" fill="#0284c7">{avg_u:.0f}%</tspan>
    · Picco <tspan font-weight="700" fill="#dc2626">{max_u:.0f}%</tspan>
    · Min <tspan font-weight="700">{min_u:.0f}%</tspan>
  </text>
  <rect x="{pad_l}" y="{pad_t}" width="{plot_w}" height="{plot_h}" fill="#fff" stroke="#e2e8f0" rx="8"/>
  {grid_lines}
  <line x1="{pad_l}" y1="{avg_y:.1f}" x2="{pad_l + plot_w}" y2="{avg_y:.1f}" stroke="#0284c7" stroke-width="1" stroke-dasharray="6 5" opacity="0.55"/>
  <polygon fill="url(#cpuFill)" points="{area_pts}"/>
  <polyline fill="none" stroke="#0284c7" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" points="{usage_pts}"/>
  {dots}
  <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="5" fill="#dc2626" stroke="#fff" stroke-width="2"/>
  <text x="{peak_x:.1f}" y="{max(peak_y - 10, pad_t + 12):.1f}" text-anchor="middle" font-size="10" font-weight="700" fill="#dc2626">{max_u:.0f}%</text>
  {x_labels}
  <text x="{pad_l + plot_w / 2:.1f}" y="{pad_t + plot_h + 32}" text-anchor="middle" font-size="11" fill="#64748b">Tempo (secondi)</text>
  {freq_panel}
</svg>"""

    def render(self):
        data = self.main_d
        meta = data.get("meta", {})
        sys_info = data.get("sys_info", {})
        ram = data.get("ram_hw", {})
        disk_hw = data.get("disk_hw", {})
        virt = data.get("virtualization", {})
        bench = data.get("benchmark", {})
        profile = meta.get("profile", "generic")

        hostname = meta.get("hostname", "N/A")
        ref_mode = "Baseline attiva" if self.ref else (
            f"Comparativa {len(self.data_list)} host" if len(self.data_list) > 1 else "Singola esecuzione"
        )
        run_flags = self._run_flags_label(meta)
        cpu_svg = self._cpu_series_svg(bench.get("cpu_series", {}))
        headline, headline_st = self._verdict_headline()
        counts = self._status_counts()

        summary_html = "".join(f"<li>{b}</li>" for b in self._executive_summary())
        recs_html = "".join(f"<li>{r}</li>" for r in self._recommendations())
        how_html = self._how_to_read(profile)
        kpi_html = self._kpi_cards_html(bench)
        metrics_html = self._grouped_metrics_html()
        score_ring = self._score_ring_svg()

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
                    <td><code class="ev-code">{ev.get('code', '')}</code></td>
                    <td>{ev.get('message', '')}</td>
                    <td class="muted">{ev.get('timestamp', '')}</td>
                </tr>"""
            health_html = f"""
            <section class="card alert-card">
                <h3>Eventi Health ({len(health_events)})</h3>
                <table><thead><tr><th>Livello</th><th>Codice</th><th>Messaggio</th><th>Ora</th></tr></thead>
                <tbody>{ev_rows}</tbody></table>
            </section>"""

        ports = data.get("app_server", {}).get("ports", {})
        ports_html = ""
        if ports:
            pr = ""
            for port, ok in ports.items():
                pr += f"<tr><td>{port}</td><td>{self._badge('ok' if ok else 'crit', 'OPEN' if ok else 'CLOSED')}</td></tr>"
            ports_html = f"""
            <section class="card side-card"><h3>Porte applicative</h3>
            <table><thead><tr><th>Porta</th><th>Stato</th></tr></thead><tbody>{pr}</tbody></table></section>"""

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
            <section class="card"><h3>Comparativa host ({len(self.data_list)})</h3>
            <table><thead><tr><th>Host</th><th>Write</th><th>Read</th><th>IOPS</th><th>CPU Stab.</th><th>Chaos</th></tr></thead>
            <tbody>{comp_rows}</tbody></table></section>"""

        ram_speed = ram.get("speed_mhz") or 0
        ram_speed_txt = f"{ram_speed} MHz" if ram_speed else "n/d"
        schema_v = data.get("schema_version", "?")
        engine_v = data.get("engine_version", "?")
        headline_color = STATUS_COLORS.get(headline_st, "#0284c7")

        return f"""<!DOCTYPE html>
<html lang="it"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HostPulse — {hostname}</title>
<style>
:root {{
  --bg:#f1f5f9; --card:#fff; --ink:#0f172a; --muted:#64748b; --border:#e2e8f0;
  --brand:#0c4a6e; --accent:#0284c7; --ok:#16a34a; --warn:#d97706; --crit:#dc2626;
}}
* {{ box-sizing:border-box; }}
body {{ font-family:Segoe UI,system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--ink); margin:0; line-height:1.55; }}
.container {{ max-width:1140px; margin:0 auto; padding:0 20px 40px; }}
.hero {{ background:linear-gradient(135deg,#0c4a6e 0%,#0369a1 55%,#0ea5e9 100%); color:#fff; padding:28px 0 32px; margin-bottom:24px; }}
.hero-inner {{ max-width:1140px; margin:0 auto; padding:0 20px; }}
.brand {{ font-size:12px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; opacity:.85; }}
.hero h1 {{ margin:6px 0 4px; font-size:28px; font-weight:700; }}
.hero-meta {{ font-size:14px; opacity:.92; }}
.hero-meta b {{ font-weight:600; }}
.pill {{ display:inline-block; background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.25); border-radius:999px; padding:2px 10px; font-size:12px; margin-right:6px; }}
.verdict-row {{ display:grid; grid-template-columns:160px 1fr; gap:24px; align-items:center; margin:-20px 0 20px; }}
@media (max-width:720px) {{ .verdict-row {{ grid-template-columns:1fr; }} }}
.verdict-card {{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:20px 24px; box-shadow:0 8px 24px rgba(15,23,42,.08); display:flex; gap:20px; align-items:center; }}
.verdict-text h2 {{ margin:0 0 6px; font-size:20px; color:{headline_color}; }}
.verdict-text p {{ margin:0; color:var(--muted); font-size:14px; }}
.status-bar {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }}
.status-chip {{ font-size:12px; font-weight:600; padding:4px 10px; border-radius:8px; background:#f8fafc; border:1px solid var(--border); }}
.status-chip.ok {{ color:var(--ok); border-color:#bbf7d0; background:#f0fdf4; }}
.status-chip.warn {{ color:var(--warn); border-color:#fde68a; background:#fffbeb; }}
.status-chip.crit {{ color:var(--crit); border-color:#fecaca; background:#fef2f2; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:20px; }}
.kpi-card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px 16px; border-left:4px solid var(--border); }}
.kpi-card.kpi-ok {{ border-left-color:var(--ok); }}
.kpi-card.kpi-warn {{ border-left-color:var(--warn); }}
.kpi-card.kpi-crit {{ border-left-color:var(--crit); }}
.kpi-card.kpi-info {{ border-left-color:var(--accent); }}
.kpi-label {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); font-weight:700; }}
.kpi-val {{ font-family:Consolas,ui-monospace,monospace; font-size:24px; font-weight:700; margin-top:4px; }}
.kpi-unit {{ font-size:13px; font-weight:500; color:var(--muted); }}
.layout {{ display:grid; grid-template-columns:1.55fr 1fr; gap:18px; align-items:start; }}
@media (max-width:960px) {{ .layout {{ grid-template-columns:1fr; }} }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px 22px; box-shadow:0 1px 2px rgba(15,23,42,.04); margin-bottom:18px; }}
.side-card {{ margin-bottom:18px; }}
.alert-card {{ border-left:4px solid var(--crit); }}
h3 {{ margin:0 0 14px; font-size:17px; color:var(--ink); }}
h4 {{ margin:0 0 10px; font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
.sys-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px 18px; font-size:13px; }}
.sys-grid div {{ padding:8px 0; border-bottom:1px solid #f1f5f9; }}
.sys-grid b {{ color:var(--muted); font-weight:600; font-size:11px; text-transform:uppercase; display:block; margin-bottom:2px; }}
.metric-group {{ margin-bottom:18px; }}
.metric-group:last-child {{ margin-bottom:0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:10px 8px; border-bottom:1px solid #f1f5f9; text-align:left; vertical-align:middle; }}
th {{ font-size:10px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); font-weight:700; }}
.metric-name {{ border-bottom:1px dotted #cbd5e1; cursor:help; }}
.metric-val strong {{ font-family:Consolas,ui-monospace,monospace; }}
.ref-col {{ text-align:right; }}
.ref-tag {{ font-size:11px; color:var(--muted); }}
.ref-tag.muted {{ opacity:.5; }}
.row-crit {{ background:#fff5f5; }}
.row-warn {{ background:#fffbeb; }}
.badge {{ display:inline-block; padding:3px 9px; border-radius:6px; font-size:10px; font-weight:700; white-space:nowrap; }}
.delta {{ font-size:11px; font-weight:600; margin-top:2px; }}
.delta-up {{ color:var(--ok); }}
.delta-down {{ color:var(--crit); }}
.muted {{ color:var(--muted); font-size:12px; }}
.ev-code {{ font-size:11px; background:#f1f5f9; padding:2px 6px; border-radius:4px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:8px; }}
.legend .badge {{ margin:0; }}
.help-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
@media (max-width:720px) {{ .help-grid {{ grid-template-columns:1fr; }} }}
ul {{ margin:8px 0 0 18px; padding:0; }}
li {{ margin-bottom:7px; }}
.rec-list li {{ margin-bottom:10px; }}
.footer {{ color:var(--muted); font-size:11px; text-align:center; padding-top:8px; }}
.cpu-chart {{ display:block; border-radius:8px; }}
@media print {{
  .hero {{ background:#0c4a6e !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  .card, .kpi-card, .verdict-card {{ break-inside:avoid; box-shadow:none; }}
}}
</style></head><body>
<header class="hero"><div class="hero-inner">
  <div class="brand">HostPulse</div>
  <h1>Report Audit Infrastruttura</h1>
  <div class="hero-meta">
    <b>{hostname}</b> · {meta.get('date','N/A')} ·
    <span class="pill">{PROFILE_LABELS.get(profile, profile)}</span>
    <span class="pill">{run_flags}</span>
    <span class="pill">{'Admin' if meta.get('is_admin') else 'Utente standard'}</span>
    <span class="pill">{ref_mode}</span>
  </div>
</div></header>

<div class="container">
<section class="verdict-row">
  <div class="verdict-card">
    {score_ring}
    <div class="verdict-text">
      <div class="kpi-label">Health Score</div>
      <h2>{headline}</h2>
      <p>Classe <b>{self.overall['grade']}</b> · {self.overall['score']}/100 punti</p>
      <div class="status-bar">
        <span class="status-chip ok">{counts.get('ok',0)} OK</span>
        <span class="status-chip warn">{counts.get('warn',0)} WARN</span>
        <span class="status-chip crit">{counts.get('crit',0)} CRIT</span>
      </div>
    </div>
  </div>
</section>

<section class="card">
  <h3>Executive Summary</h3>
  <ul>{summary_html}</ul>
</section>

<section class="kpi-grid">{kpi_html}</section>

<section class="card">
  <h3>Inventario host</h3>
  <div class="sys-grid">
    <div><b>CPU</b>{sys_info.get('cpu_model','N/A')}<br><span class="muted">{sys_info.get('cores','N/A')}</span></div>
    <div><b>Sistema operativo</b>{sys_info.get('os','N/A')}<br><span class="muted">Uptime {sys_info.get('uptime','N/A')}</span></div>
    <div><b>Memoria</b>{ram.get('total_gb',0)} GB · {ram.get('percent_used',0)}% usata<br><span class="muted">{ram_speed_txt}</span></div>
    <div><b>Disco</b>{disk_hw.get('free_gb',0)}/{disk_hw.get('total_gb',0)} GB liberi<br><span class="muted">{disk_hw.get('percent_used',0)}% usato</span></div>
    <div><b>Virtualizzazione</b>{'VM' if virt.get('is_vm') else 'Bare metal'}{(' · ' + virt.get('hypervisor','')) if virt.get('is_vm') else ''}<br><span class="muted">NUMA {sys_info.get('numa_nodes',1)}</span></div>
    <div><b>Energia / contesto</b>{sys_info.get('power_plan','N/A')}<br><span class="muted">Ctx/s {virt.get('ctx_switches_sec',0)} · Queue {virt.get('cpu_queue_length',0)}</span></div>
  </div>
</section>

{health_html}
{comparison_section}

<div class="layout">
  <section class="card">
    <h3>Analisi metriche</h3>
    {metrics_html}
  </section>
  <div>
    {ports_html}
    <section class="card side-card">
      <h3>Dettaglio workload</h3>
      <table>
        <tr><td>Swap</td><td><b>{ram.get('swap_percent',0)}%</b></td></tr>
        <tr><td>Crypto hash/s</td><td><b>{bench.get('cpu_real',{}).get('crypto_hash_rate',0)}</b></td></tr>
        <tr><td>Compressione</td><td><b>{bench.get('cpu_real',{}).get('compress_mb_s',0)} MB/s</b></td></tr>
        <tr><td>Chaos IOPS sotto carico</td><td><b>{bench.get('chaos',{}).get('disk_iops_under_load',0)}</b></td></tr>
        <tr><td>CPU avg task</td><td><b>{bench.get('cpu_consistency',{}).get('avg_task_ms',0)} ms</b></td></tr>
        <tr><td>Stability score</td><td><b>{bench.get('cpu_consistency',{}).get('stability_score','n/d')}</b></td></tr>
      </table>
    </section>
    <section class="card side-card">
      <h3>Raccomandazioni</h3>
      <ul class="rec-list">{recs_html}</ul>
    </section>
  </div>
</div>

<section class="card">
  <h3>Stress test CPU</h3>
  {cpu_svg}
</section>

<section class="card">
  <div class="help-grid">
    <div>
      <h3>Come leggere questo report</h3>
      {how_html}
    </div>
    <div>
      <h3>Legenda score</h3>
      <div class="legend">
        <span>{self._badge('ok', 'A ≥ 85')}</span>
        <span>{self._badge('ok', 'B ≥ 70')}</span>
        <span>{self._badge('warn', 'C ≥ 55')}</span>
        <span>{self._badge('crit', 'D &lt; 55')}</span>
      </div>
      <p class="muted">OK = nella norma · WARN = da monitorare · CRIT = intervento consigliato · INFO = contesto</p>
    </div>
  </div>
</section>

<div class="footer">HostPulse engine {engine_v} · schema v{schema_v} · report offline self-contained</div>
</div></body></html>"""
