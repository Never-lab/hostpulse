from __future__ import annotations

import os
import sys
import threading
import webbrowser

if getattr(sys, "frozen", False):
    sys.path.insert(0, getattr(sys, "_MEIPASS", ""))

from deps_check import require_dependencies

require_dependencies(frozen=getattr(sys, "frozen", False))

import customtkinter as ctk
from tkinter import messagebox

from app_paths import ensure_runtime_dirs, get_app_base_dir, get_bin_dir
from cancel import AuditCancelled
from load_safety import needs_full_load_confirm
from orchestrator import run_audit
from pdf_export import PdfExportError, html_file_to_pdf


class AuditApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("HostPulse")
        self.geometry("900x560")
        self.minsize(780, 480)

        self._build_layout()

        self._worker_thread: threading.Thread | None = None
        self._running = False
        self._last_report_path: str | None = None
        self._last_pdf_path: str | None = None
        self._cancel_event = threading.Event()

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
            text="HostPulse",
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

        self.export_pdf_button = ctk.CTkButton(
            buttons_frame,
            text="Esporta PDF",
            command=self._on_export_pdf_click,
            corner_radius=24,
            height=34,
            fg_color=("gray70", "#14532d"),
            state="disabled",
        )
        self.export_pdf_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        # Barra di avanzamento
        progress_label = ctk.CTkLabel(
            left_card,
            text="Stato analisi",
            font=ctk.CTkFont("Segoe UI", size=11, weight="bold"),
        )
        progress_label.grid(row=8, column=0, sticky="w", padx=18, pady=(0, 4))

        self.progress = ctk.CTkProgressBar(
            left_card,
            height=10,
            corner_radius=999,
        )
        self.progress.grid(row=9, column=0, sticky="ew", padx=18)
        self.progress.set(0)

        self.progress_label = ctk.CTkLabel(
            left_card,
            text="In attesa di avvio...",
            font=ctk.CTkFont("Segoe UI", size=10),
            text_color=("#4b5563", "#9ca3af"),
        )
        self.progress_label.grid(row=10, column=0, sticky="w", padx=18, pady=(4, 18))

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
        self.export_pdf_button.configure(state="normal")

    # --- Event handlers ---

    def _on_start_click(self) -> None:
        if self._running:
            return

        compare = self.compare_var.get()
        quick = self.quick_var.get()
        production_safe = self.production_safe_var.get()
        profile_display = self.profile_var.get()
        profile = self._profile_value_map.get(profile_display, "generic")

        if needs_full_load_confirm(profile, production_safe):
            ok = messagebox.askyesno(
                "Carico pieno su server",
                "Profilo Application/DB Server senza «Esecuzione in produzione».\n\n"
                "Il benchmark a pieno carico può stressare CPU e disco sulla VM cliente.\n"
                "Continuare comunque?\n\n"
                "(Consigliato: attiva «Esecuzione in produzione (carico ridotto)».)",
            )
            if not ok:
                return

        self.log_text.delete("1.0", "end")
        self.progress.set(0)
        self._cancel_event.clear()

        load_mode = "production-safe" if production_safe else ("quick" if quick else "full load")
        self._set_running_state(True)
        self._append_log(
            f"Avvio analisi... profilo={profile} modo={load_mode} compare={compare}"
        )

        self._worker_thread = threading.Thread(
            target=self._run_audit_worker,
            args=(compare, quick, production_safe, profile),
            daemon=True,
        )
        self._worker_thread.start()

    def _on_cancel_click(self) -> None:
        if not self._running:
            return
        self._cancel_event.set()
        self._append_log("Annullamento richiesto: stop cooperativo in corso...")
        self._set_status("Annullamento...", None)

    def _on_open_report_click(self) -> None:
        if not self._last_report_path or not os.path.isfile(self._last_report_path):
            messagebox.showwarning("Report", "Nessun report disponibile. Eseguire prima un'analisi completa.")
            return
        try:
            webbrowser.open(f"file:///{self._last_report_path.replace(os.sep, '/')}")
        except Exception:
            messagebox.showerror("Errore", f"Impossibile aprire il report:\n{self._last_report_path}")

    def _on_export_pdf_click(self) -> None:
        if not self._last_report_path or not os.path.isfile(self._last_report_path):
            messagebox.showwarning("PDF", "Nessun report HTML disponibile.")
            return
        try:
            pdf_path = html_file_to_pdf(self._last_report_path)
            self._last_pdf_path = str(pdf_path)
            self._append_log(f"PDF esportato: {pdf_path}")
            messagebox.showinfo("PDF", f"PDF creato:\n{pdf_path}")
        except PdfExportError as exc:
            messagebox.showerror("PDF", str(exc))

    # --- Lavoro in background ---

    def _run_audit_worker(self, compare: bool, quick: bool, production_safe: bool, profile: str) -> None:
        try:
            ensure_runtime_dirs()
            benchmark_root = str(get_app_base_dir())
            bin_dir = str(get_bin_dir())

            def on_progress(status: str, step: int, log: str) -> None:
                self.after(0, self._set_status, status, step)
                self.after(0, self._append_log, log)

            result = run_audit(
                root_dir=benchmark_root,
                bin_dir=bin_dir,
                profile=profile,
                quick=quick,
                production_safe=production_safe,
                compare=compare,
                cancel_event=self._cancel_event,
                on_progress=on_progress,
            )
            self.after(0, lambda p=result.html_path: self._set_last_report(p))
            self.after(
                0,
                lambda: messagebox.showinfo(
                    "Analisi completata",
                    f"Analisi completata con successo.\n\nReport generato:\n{result.html_path}",
                ),
            )
        except AuditCancelled:
            self.after(0, self._append_log, "Analisi annullata.")
            self.after(0, self._set_status, "Annullata", 0)
            self.after(
                0,
                lambda: messagebox.showinfo(
                    "Annullata",
                    "Analisi interrotta. File temporanei ripuliti dove possibile.",
                ),
            )
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._append_log, f"ERRORE: {exc}")
            self.after(
                0,
                lambda err=exc: messagebox.showerror(
                    "Errore durante l'analisi",
                    f"Si è verificato un errore:\n{err}",
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
