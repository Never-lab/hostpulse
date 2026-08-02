"""Live screen: progress, status and streaming log while the audit runs."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ui.theme import COLORS
from orchestrator import PROGRESS_TOTAL

STEP_HINT = "6 passi: sistema → CPU → RAM/rete → disco → salva → report"


class LiveScreen(ctk.CTkFrame):
    def __init__(self, parent, *, on_cancel: Callable[[], None]) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])

        self._on_cancel = on_cancel
        self._log_visible = True

        self._build_layout()

    # --- layout ---

    def _build_layout(self) -> None:
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 6))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Analisi in corso",
            font=ctk.CTkFont("Segoe UI", size=22, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=0, sticky="w")

        self.summary_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont("Segoe UI", size=12),
            text_color=COLORS["muted"],
        )
        self.summary_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        ctk.CTkLabel(
            header,
            text=STEP_HINT,
            font=ctk.CTkFont("Segoe UI", size=10),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, sticky="w", pady=(2, 0))

        progress_card = ctk.CTkFrame(self, corner_radius=16, fg_color=COLORS["card"])
        progress_card.grid(row=1, column=0, sticky="ew", padx=32, pady=(12, 0))
        progress_card.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            progress_card,
            height=10,
            corner_radius=999,
            fg_color=COLORS["border"],
            progress_color=COLORS["accent"],
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            progress_card,
            text="In attesa...",
            font=ctk.CTkFont("Segoe UI", size=11),
            text_color=COLORS["ink"],
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 18))

        actions_row = ctk.CTkFrame(self, fg_color="transparent")
        actions_row.grid(row=2, column=0, sticky="ew", padx=32, pady=(12, 0))

        self.cancel_button = ctk.CTkButton(
            actions_row,
            text="Annulla",
            command=self._handle_cancel,
            corner_radius=24,
            height=34,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["crit"],
            text_color=COLORS["crit"],
            hover_color=COLORS["border"],
        )
        self.cancel_button.grid(row=0, column=0, sticky="w")

        self.log_toggle_button = ctk.CTkButton(
            actions_row,
            text="Nascondi log",
            command=self._toggle_log,
            corner_radius=24,
            height=34,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["ink"],
            hover_color=COLORS["border"],
        )
        self.log_toggle_button.grid(row=0, column=1, sticky="w", padx=(10, 0))

        ctk.CTkLabel(
            self,
            text="Log dettagliato",
            font=ctk.CTkFont("Segoe UI", size=11, weight="bold"),
            text_color=COLORS["muted"],
        ).grid(row=3, column=0, sticky="w", padx=36, pady=(16, 4))

        self.log_text = ctk.CTkTextbox(
            self,
            corner_radius=10,
            font=ctk.CTkFont("Consolas", size=10),
            fg_color=COLORS["card"],
            text_color=COLORS["ink"],
        )
        self.log_text.grid(row=4, column=0, sticky="nsew", padx=32, pady=(0, 24))

    # --- public API (Task 5 interface) ---

    def reset(self, summary: str) -> None:
        self.summary_label.configure(text=summary)
        self.status_label.configure(text="In attesa...")
        self.progress_bar.set(0)
        self.log_text.delete("1.0", "end")
        if not self._log_visible:
            self.set_log_visible(True)

    def set_progress(self, status: str, step: Optional[int]) -> None:
        self.status_label.configure(text=status)
        if step is not None:
            try:
                self.progress_bar.set(max(0.0, min(1.0, float(step) / float(PROGRESS_TOTAL))))
            except (TypeError, ValueError, ZeroDivisionError):
                self.progress_bar.set(0.0)

    def append_log(self, line: str) -> None:
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")

    def set_log_visible(self, visible: bool) -> None:
        self._log_visible = visible
        if visible:
            self.log_text.grid(row=4, column=0, sticky="nsew", padx=32, pady=(0, 24))
            self.log_toggle_button.configure(text="Nascondi log")
        else:
            self.log_text.grid_forget()
            self.log_toggle_button.configure(text="Mostra log")

    # --- internal handlers ---

    def _handle_cancel(self) -> None:
        self._on_cancel()

    def _toggle_log(self) -> None:
        self.set_log_visible(not self._log_visible)
