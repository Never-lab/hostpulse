from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import webbrowser

if getattr(sys, "frozen", False):
    sys.path.insert(0, getattr(sys, "_MEIPASS", ""))

# Installazione automatica dipendenze mancanti (solo esecuzione da sorgente)
_REQUIRED_PACKAGES = ["psutil", "customtkinter", "matplotlib", "seaborn", "pandas", "numpy"]


def _ensure_dependencies() -> None:
    """Installa con pip i pacchetti mancanti prima di importarli."""
    if getattr(sys, "frozen", False):
        return
    for pkg in _REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError:
                pass  # ignora errori di rete/permessi; l'import successivo fallirà


_ensure_dependencies()

import customtkinter as ctk
from tkinter import messagebox

from app_paths import ensure_runtime_dirs, get_app_base_dir, get_bin_dir
from engine import ExtremeAuditEngine
from reporter_generator import ReportGenerator


class AuditApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("Extreme Audit v5")
        self.geometry("900x560")
        self.minsize(780, 480)

        self._build_layout()

        self._worker_thread: threading.Thread | None = None
        self._running = False
        self._last_report_path: str | None = None

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # contenitore principale "card"
        outer = ctk.CTkFrame(self, corner_radius=18)
        outer.grid(row=0, column=0, padx=24, pady=24, sticky="nsew")
        outer.grid_rowconfigure(2, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 6))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Extreme Audit v5",
            font=ctk.CTkFont("Segoe UI", size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Benchmark completo di sistema, con design 2026: pulito, leggibile, zero terminale.",
            font=ctk.CTkFont("Segoe UI", size=11),
            text_color=("#4b5563", "#9ca3af"),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Riga centrale: opzioni + azioni da un lato, log dall'altro
        center = ctk.CTkFrame(outer, fg_color="transparent")
        center.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 12))
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(0, weight=0)
        center.grid_columnconfigure(1, weight=1)

        # Colonna sinistra (opzioni + progress)
        left_card = ctk.CTkFrame(center, corner_radius=16)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_card.grid_columnconfigure(0, weight=1)

        options_label = ctk.CTkLabel(
            left_card,
            text="Configurazione analisi",
            font=ctk.CTkFont("Segoe UI", size=12, weight="bold"),
        )
        options_label.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))

        profile_label = ctk.CTkLabel(left_card, text="Contesto:", font=ctk.CTkFont("Segoe UI", size=11))
        profile_label.grid(row=1, column=0, sticky="w", padx=18, pady=(6, 0))
        self.profile_var = ctk.StringVar(value="Generico")
        self._profile_value_map = {"Generico": "generic", "Application Server": "app_server", "DB Server": "db_server"}
        self.profile_menu = ctk.CTkOptionMenu(
            left_card,
            values=["Generico", "Application Server", "DB Server"],
            variable=self.profile_var,
            width=180,
        )
        self.profile_menu.grid(row=2, column=0, sticky="w", padx=18, pady=(2, 4))

        self.compare_var = ctk.BooleanVar(value=False)
        self.quick_var = ctk.BooleanVar(value=False)
        self.production_safe_var = ctk.BooleanVar(value=False)

        compare_cb = ctk.CTkCheckBox(
            left_card,
            text="Confronta con esecuzioni precedenti",
            variable=self.compare_var,
        )
        compare_cb.grid(row=3, column=0, sticky="w", padx=18, pady=(8, 0))

        quick_cb = ctk.CTkCheckBox(
            left_card,
            text="Modalità rapida (se supportata)",
            variable=self.quick_var,
        )
        quick_cb.grid(row=4, column=0, sticky="w", padx=18, pady=(4, 0))

        production_safe_cb = ctk.CTkCheckBox(
            left_card,
            text="Esecuzione in produzione (carico ridotto)",
            variable=self.production_safe_var,
        )
        production_safe_cb.grid(row=5, column=0, sticky="w", padx=18, pady=(4, 12))

        # Pulsanti principali
        buttons_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        buttons_frame.grid(row=6, column=0, sticky="ew", padx=18, pady=(4, 16))
        buttons_frame.grid_columnconfigure(0, weight=1)

        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="Avvia analisi completa",
            command=self._on_start_click,
            corner_radius=24,
            height=38,
        )
        self.start_button.grid(row=0, column=0, sticky="ew")

        self.cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Annulla",
            command=self._on_cancel_click,
            corner_radius=24,
            height=34,
            fg_color=("gray80", "#111827"),
            text_color=("black", "#e5e7eb"),
            hover_color=("gray70", "#1f2937"),
            state="disabled",
        )
        self.cancel_button.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.open_report_button = ctk.CTkButton(
            buttons_frame,
            text="Apri report",
            command=self._on_open_report_click,
            corner_radius=24,
            height=34,
            fg_color=("gray75", "#1e3a5f"),
            state="disabled",
        )
        self.open_report_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        # Barra di avanzamento
        progress_label = ctk.CTkLabel(
            left_card,
            text="Stato analisi",
            font=ctk.CTkFont("Segoe UI", size=11, weight="bold"),
        )
        progress_label.grid(row=7, column=0, sticky="w", padx=18, pady=(0, 4))

        self.progress = ctk.CTkProgressBar(
            left_card,
            height=10,
            corner_radius=999,
        )
        self.progress.grid(row=8, column=0, sticky="ew", padx=18)
        self.progress.set(0)

        self.progress_label = ctk.CTkLabel(
            left_card,
            text="In attesa di avvio...",
            font=ctk.CTkFont("Segoe UI", size=10),
            text_color=("#4b5563", "#9ca3af"),
        )
        self.progress_label.grid(row=9, column=0, sticky="w", padx=18, pady=(4, 18))

        # Colonna destra (log)
        right_card = ctk.CTkFrame(center, corner_radius=16)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_card.grid_rowconfigure(1, weight=1)
        right_card.grid_columnconfigure(0, weight=1)

        log_label = ctk.CTkLabel(
            right_card,
            text="Dettagli esecuzione",
            font=ctk.CTkFont("Segoe UI", size=12, weight="bold"),
        )
        log_label.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))

        self.log_text = ctk.CTkTextbox(
            right_card,
            corner_radius=10,
            font=ctk.CTkFont("Consolas", size=10),
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=18, pady=(2, 18))

    # --- UI helpers ---

    def _append_log(self, text: str) -> None:
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def _set_status(self, text: str, step: int | None = None) -> None:
        # customtkinter usa "configure" invece di "config"
        self.progress_label.configure(text=text)
        if step is not None:
            # progress bar customtkinter va da 0.0 a 1.0
            try:
                self.progress.set(max(0.0, min(1.0, float(step) / 4.0)))
            except Exception:
                self.progress.set(0.0)
        self.update_idletasks()

    def _set_running_state(self, running: bool) -> None:
        self._running = running
        if running:
            self.start_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
        else:
            self.start_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")

    def _set_last_report(self, path: str) -> None:
        self._last_report_path = path
        self.open_report_button.configure(state="normal")

    # --- Event handlers ---

    def _on_start_click(self) -> None:
        if self._running:
            return
        self.log_text.delete("1.0", "end")
        self.progress.set(0)

        compare = self.compare_var.get()
        quick = self.quick_var.get()
        production_safe = self.production_safe_var.get()
        profile_display = self.profile_var.get()
        profile = self._profile_value_map.get(profile_display, "generic")

        self._set_running_state(True)
        self._append_log("Avvio analisi...")

        self._worker_thread = threading.Thread(
            target=self._run_audit_worker,
            args=(compare, quick, production_safe, profile),
            daemon=True,
        )
        self._worker_thread.start()

    def _on_cancel_click(self) -> None:
        if not self._running:
            return
        # Non interrompiamo brutalmente i benchmark, ma segnaliamo l'annullamento.
        messagebox.showinfo(
            "Annulla",
            "Al momento non è possibile interrompere un benchmark in corso.\n"
            "La funzione di stop sicuro verrà aggiunta in una versione futura.",
        )

    def _on_open_report_click(self) -> None:
        if not self._last_report_path or not os.path.isfile(self._last_report_path):
            messagebox.showwarning("Report", "Nessun report disponibile. Eseguire prima un'analisi completa.")
            return
        try:
            webbrowser.open(f"file:///{self._last_report_path.replace(os.sep, '/')}")
        except Exception:
            messagebox.showerror("Errore", f"Impossibile aprire il report:\n{self._last_report_path}")

    # --- Lavoro in background ---

    def _run_audit_worker(self, compare: bool, quick: bool, production_safe: bool, profile: str) -> None:
        try:
            self.after(0, self._set_status, "Preparazione motore analisi...", 0)
            ensure_runtime_dirs()
            benchmark_root = str(get_app_base_dir())
            engine = ExtremeAuditEngine(
                root_dir=benchmark_root,
                quick=quick,
                profile=profile,
                production_safe=production_safe,
            )
            hostname = engine.data["meta"]["hostname"]

            self.after(
                0,
                self._append_log,
                f"Target: {hostname} | Admin: {engine.data['meta']['is_admin']}",
            )

            # 1/4 – Sistema & CPU
            self.after(0, self._set_status, "Analisi sistema & CPU...", 1)
            self.after(0, self._append_log, "[1/4] Raccolta informazioni di sistema...")
            engine.collect_sys_info()

            if profile == "app_server" and engine.config.get("APP_PORT_CHECK") is not None:
                self.after(0, self._append_log, "[1/4] Verifica porta applicativa...")
                engine.check_app_port()

            self.after(0, self._append_log, "[1/4] CPU benchmark in corso...")
            engine.cpu_benchmark_suite()

            self.after(0, self._append_log, "[1/4] CPU real-world test...")
            engine.cpu_real_world()
            self.after(0, self._append_log, "[1/4] CPU: completato.")

            # RAM & rete
            self.after(0, self._append_log, "[1/4] RAM bandwidth test...")
            engine.ram_benchmark()

            self.after(0, self._append_log, "[1/4] Network latency test...")
            engine.net_benchmark()

            # 2/4 – Storage
            self.after(0, self._set_status, "Benchmark storage (Seq & IOPS)...", 2)
            self.after(0, self._append_log, "[2/4] Benchmark disco in corso...")
            engine.disk_benchmarks()
            self.after(0, self._append_log, "[2/4] Storage: completato (MB/s, IOPS, latenze).")

            if not production_safe and not engine.skip_chaos:
                self.after(0, self._append_log, "[2/4] Chaos test (IOPS sotto carico CPU)...")
                engine.chaos_disk_under_load()
                chaos = engine.data["benchmark"]["chaos"]
                if chaos.get("active"):
                    self.after(
                        0,
                        self._append_log,
                        f"[2/4] Chaos: impatto IOPS {chaos.get('impact_pct', 0)}%.",
                    )
                else:
                    self.after(0, self._append_log, "[2/4] Chaos: completato (nessun degrado significativo).")

            # 3/4 – Salvataggio
            self.after(0, self._set_status, "Salvataggio risultati...", 3)
            self.after(0, self._append_log, "[3/4] Salvataggio risultati su disco...")
            json_path = engine.save_results()
            self.after(0, self._append_log, f"Risultati salvati in: {json_path}")

            # 4/4 – Reportistica
            self.after(0, self._set_status, "Generazione report...", 4)
            self.after(0, self._append_log, "[4/4] Generazione report & asset...")

            if compare:
                history = engine.get_history()
                baseline_path = os.path.join(benchmark_root, "config", "baseline.json")
                ref = None
                if os.path.isfile(baseline_path):
                    try:
                        with open(baseline_path, "r", encoding="utf-8") as bf:
                            ref = json.load(bf)
                    except (json.JSONDecodeError, OSError):
                        ref = None
                reporter = ReportGenerator(history, reference=ref, style="corporate")
            else:
                baseline_path = os.path.join(benchmark_root, "config", "baseline.json")
                ref = None
                if os.path.isfile(baseline_path):
                    try:
                        with open(baseline_path, "r", encoding="utf-8") as bf:
                            ref = json.load(bf)
                    except (json.JSONDecodeError, OSError):
                        ref = None
                reporter = ReportGenerator(engine.data, reference=ref, style="corporate")

            # Export asset
            bin_dir = str(get_bin_dir())
            export_dir = os.path.join(bin_dir, "exports", "slides")
            os.makedirs(export_dir, exist_ok=True)
            reporter.export_presentation_assets(export_dir)

            report_html = f"REPORT_{engine.data['meta']['hostname']}.html"
            report_path = os.path.join(bin_dir, report_html)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(reporter.render())

            self.after(
                0,
                self._append_log,
                f"Processo completato! Report HTML: {report_path}",
            )
            self.after(0, lambda p=report_path: self._set_last_report(p))
            self.after(
                0,
                lambda: messagebox.showinfo(
                    "Analisi completata",
                    f"Analisi completata con successo.\n\nReport generato:\n{report_path}",
                ),
            )
        except Exception as exc:  # noqa: BLE001
            self.after(
                0,
                self._append_log,
                f"ERRORE: {exc}",
            )
            self.after(
                0,
                lambda: messagebox.showerror(
                    "Errore durante l'analisi",
                    f"Si è verificato un errore:\n{exc}",
                ),
            )
        finally:
            self.after(0, self._set_running_state, False)


def main() -> None:
    ensure_runtime_dirs()
    app = AuditApp()
    app.mainloop()


if __name__ == "__main__":
    main()