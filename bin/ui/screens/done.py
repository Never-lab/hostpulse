"""Done screen: final score, grade and export actions."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ui.theme import COLORS, status_color
from ui.screens.setup import PROFILE_LABELS
from orchestrator import AuditResultPaths

MODE_LABELS: dict[str, str] = {
    "full": "completa",
    "quick": "rapida",
    "production-safe": "produzione (carico ridotto)",
}


class DoneScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        *,
        on_open_report: Callable[[], None],
        on_export_pdf: Callable[[], None],
        on_new_run: Callable[[], None],
    ) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])

        self._on_open_report = on_open_report
        self._on_export_pdf = on_export_pdf
        self._on_new_run = on_new_run

        self._build_layout()

    # --- layout ---

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0)

        self.grade_label = ctk.CTkLabel(
            center,
            text="—",
            font=ctk.CTkFont("Segoe UI", size=48, weight="bold"),
            text_color=COLORS["muted"],
        )
        self.grade_label.grid(row=0, column=0, pady=(0, 4))

        self.score_label = ctk.CTkLabel(
            center,
            text="—/100",
            font=ctk.CTkFont("Segoe UI", size=16),
            text_color=COLORS["ink"],
        )
        self.score_label.grid(row=1, column=0, pady=(0, 8))

        self.meta_label = ctk.CTkLabel(
            center,
            text="",
            font=ctk.CTkFont("Segoe UI", size=11),
            text_color=COLORS["muted"],
        )
        self.meta_label.grid(row=2, column=0, pady=(0, 24))

        buttons_row = ctk.CTkFrame(center, fg_color="transparent")
        buttons_row.grid(row=3, column=0)

        self.open_report_button = ctk.CTkButton(
            buttons_row,
            text="Apri report",
            command=self._handle_open_report,
            corner_radius=24,
            height=38,
            fg_color=COLORS["accent"],
            hover_color=COLORS["brand"],
        )
        self.open_report_button.grid(row=0, column=0, sticky="w")

        self.export_pdf_button = ctk.CTkButton(
            buttons_row,
            text="Esporta PDF",
            command=self._handle_export_pdf,
            corner_radius=24,
            height=34,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["ink"],
            hover_color=COLORS["border"],
        )
        self.export_pdf_button.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.new_run_button = ctk.CTkButton(
            buttons_row,
            text="Nuova analisi",
            command=self._handle_new_run,
            corner_radius=24,
            height=34,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["ink"],
            hover_color=COLORS["border"],
        )
        self.new_run_button.grid(row=0, column=2, sticky="w", padx=(10, 0))

        self.path_label = ctk.CTkLabel(
            center,
            text="",
            font=ctk.CTkFont("Segoe UI", size=9),
            text_color=COLORS["muted"],
            wraplength=560,
        )
        self.path_label.grid(row=4, column=0, pady=(16, 0))

    # --- public API (Task 5 interface) ---

    def show_result(self, result: AuditResultPaths) -> None:
        color = status_color(result.status)
        self.grade_label.configure(text=result.grade, text_color=color)
        self.score_label.configure(text=f"{result.overall_score:.0f}/100")

        profile_label = PROFILE_LABELS.get(result.profile, result.profile)
        mode_label = MODE_LABELS.get(result.mode, result.mode)
        self.meta_label.configure(
            text=f"{result.hostname} · {profile_label} · {mode_label}"
        )
        self.path_label.configure(text=result.html_path)

    # --- internal handlers ---

    def _handle_open_report(self) -> None:
        self._on_open_report()

    def _handle_export_pdf(self) -> None:
        self._on_export_pdf()

    def _handle_new_run(self) -> None:
        self._on_new_run()
