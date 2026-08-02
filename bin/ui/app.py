"""Shell state machine + top-level GUI window (Setup / Live / Done).

``ShellController`` is plain Python and always importable. The CTk-backed
``AuditApp`` class needs Tk/customtkinter, which is not available on every
platform/CI runner (e.g. Ubuntu without Tcl/Tk). Its construction is deferred
to ``_build_audit_app_class`` and exposed lazily via module ``__getattr__``
(PEP 562) so ``import ui.app`` stays safe everywhere; only touching the
``AuditApp`` attribute requires a working Tk.
"""

from __future__ import annotations

import os
import threading
import webbrowser
from typing import Optional

from app_paths import ensure_runtime_dirs, get_app_base_dir, get_bin_dir
from cancel import AuditCancelled
from load_safety import needs_full_load_confirm
from orchestrator import AuditResultPaths, run_audit
from pdf_export import PdfExportError, html_file_to_pdf
from ui.presets import Preset, set_last_preset_name

STATES = ("setup", "live", "done")


class ShellController:
    """Pure state tracker for Setup/Live/Done — no widgets, easy to unit test."""

    def __init__(self) -> None:
        self.state: str = "setup"

    def begin_run(self) -> None:
        self.state = "live"

    def finish_run(self) -> None:
        self.state = "done"

    def cancel_to_setup(self) -> None:
        self.state = "setup"


def _build_audit_app_class() -> type:
    """Build the ``AuditApp`` class. Only called once Tk/CTk is actually needed."""
    from tkinter import messagebox

    import customtkinter as ctk

    from ui.screens.done import MODE_LABELS, DoneScreen
    from ui.screens.live import LiveScreen
    from ui.screens.setup import PROFILE_LABELS, SetupScreen
    from ui.theme import COLORS, apply_appearance

    class AuditApp(ctk.CTk):
        def __init__(self) -> None:
            super().__init__()

            apply_appearance()

            self.title("HostPulse")
            self.geometry("960x600")
            self.minsize(860, 560)
            self.configure(fg_color=COLORS["bg"])

            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)

            self._controller = ShellController()
            self._cancel_event = threading.Event()
            self._worker_thread: Optional[threading.Thread] = None
            self._last_result: Optional[AuditResultPaths] = None

            self._build_layout()
            self.show_setup()

        # --- layout ---

        def _build_layout(self) -> None:
            container = ctk.CTkFrame(self, fg_color=COLORS["bg"])
            container.grid(row=0, column=0, sticky="nsew")
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)

            self.setup_screen = SetupScreen(container, on_start=self._start)
            self.live_screen = LiveScreen(container, on_cancel=self._cancel)
            self.done_screen = DoneScreen(
                container,
                on_open_report=self._open_report,
                on_export_pdf=self._export_pdf,
                on_new_run=self.show_setup,
            )

            for screen in (self.setup_screen, self.live_screen, self.done_screen):
                screen.grid(row=0, column=0, sticky="nsew")

        # --- state transitions (public API) ---

        def show_setup(self) -> None:
            self._controller.cancel_to_setup()
            self.setup_screen.refresh_presets()
            self.setup_screen.tkraise()

        def show_live(self) -> None:
            self._controller.begin_run()
            self.live_screen.tkraise()

        def show_done(self, result: AuditResultPaths) -> None:
            self._last_result = result
            self._controller.finish_run()
            self.done_screen.show_result(result)
            self.done_screen.tkraise()

        # --- start/cancel handlers ---

        def _start(self, preset: Preset) -> None:
            if needs_full_load_confirm(preset.profile, preset.production_safe):
                ok = messagebox.askyesno(
                    "Carico pieno su server",
                    "Profilo Application/DB Server senza «Esecuzione in produzione».\n\n"
                    "Il benchmark a pieno carico può stressare CPU e disco sulla VM cliente.\n"
                    "Continuare comunque?\n\n"
                    "(Consigliato: attiva «Esecuzione in produzione (carico ridotto)».)",
                )
                if not ok:
                    return

            try:
                set_last_preset_name(preset.name)
            except (OSError, ValueError) as exc:
                messagebox.showerror("Preset", f"Impossibile salvare l'ultimo preset:\n{exc}")

            self._cancel_event.clear()

            profile_label = PROFILE_LABELS.get(preset.profile, preset.profile)
            mode = "production-safe" if preset.production_safe else ("quick" if preset.quick else "full")
            mode_label = MODE_LABELS.get(mode, mode)
            summary = f"{preset.name} · {profile_label} · {mode_label}"

            self.show_live()
            self.live_screen.reset(summary)

            self._worker_thread = threading.Thread(
                target=self._run_audit_worker,
                args=(preset,),
                daemon=True,
            )
            self._worker_thread.start()

        def _cancel(self) -> None:
            self._cancel_event.set()
            self.live_screen.set_progress("Annullamento...", None)
            self.live_screen.append_log("Annullamento richiesto: stop cooperativo in corso...")

        # --- background worker ---

        def _run_audit_worker(self, preset: Preset) -> None:
            try:
                ensure_runtime_dirs()
                root_dir = str(get_app_base_dir())
                bin_dir = str(get_bin_dir())

                def on_progress(status: str, step: int, log: str) -> None:
                    self.after(0, self.live_screen.set_progress, status, step)
                    self.after(0, self.live_screen.append_log, log)

                result = run_audit(
                    root_dir=root_dir,
                    bin_dir=bin_dir,
                    profile=preset.profile,
                    quick=preset.quick,
                    production_safe=preset.production_safe,
                    compare=preset.compare,
                    cancel_event=self._cancel_event,
                    on_progress=on_progress,
                )
                self.after(0, self.show_done, result)
            except AuditCancelled:
                self.after(0, self._on_audit_cancelled)
            except Exception as exc:  # noqa: BLE001
                self.after(0, self._on_audit_error, exc)

        def _on_audit_cancelled(self) -> None:
            self.show_setup()
            self.setup_screen.set_status_message("Analisi annullata.")

        def _on_audit_error(self, exc: Exception) -> None:
            messagebox.showerror("Errore durante l'analisi", f"Si è verificato un errore:\n{exc}")
            self.show_setup()

        # --- done screen actions ---

        def _open_report(self) -> None:
            result = self._last_result
            if result is None or not os.path.isfile(result.html_path):
                messagebox.showwarning("Report", "Nessun report disponibile. Eseguire prima un'analisi completa.")
                return
            try:
                webbrowser.open(f"file:///{result.html_path.replace(os.sep, '/')}")
            except OSError:
                messagebox.showerror("Errore", f"Impossibile aprire il report:\n{result.html_path}")

        def _export_pdf(self) -> None:
            result = self._last_result
            if result is None or not os.path.isfile(result.html_path):
                messagebox.showwarning("PDF", "Nessun report HTML disponibile.")
                return
            try:
                pdf_path = html_file_to_pdf(result.html_path)
                messagebox.showinfo("PDF", f"PDF creato:\n{pdf_path}")
            except PdfExportError as exc:
                messagebox.showerror("PDF", str(exc))

    return AuditApp


_AuditApp: Optional[type] = None


def __getattr__(name: str):
    if name == "AuditApp":
        global _AuditApp
        if _AuditApp is None:
            _AuditApp = _build_audit_app_class()
        return _AuditApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
