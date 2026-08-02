"""Setup screen: pick a preset, tweak advanced options, start the audit."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ui.theme import COLORS
from ui.presets import (
    Preset,
    delete_custom_preset,
    get_last_preset_name,
    get_preset,
    list_presets,
    save_custom_preset,
    set_last_preset_name,
)
from version import __version__

PROFILE_LABELS: dict[str, str] = {
    "generic": "Generico",
    "app_server": "Application Server",
    "db_server": "DB Server",
}
PROFILE_VALUES: dict[str, str] = {label: value for value, label in PROFILE_LABELS.items()}


class SetupScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        *,
        on_start: Callable[[Preset], None],
        on_presets_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])

        self._on_start = on_start
        self._on_presets_changed = on_presets_changed
        self._presets: list[Preset] = []
        self._selected_name: str = ""
        self._advanced_visible = False

        self._build_layout()
        self.refresh_presets()

    # --- layout ---

    def _build_layout(self) -> None:
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 6))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="HostPulse",
            font=ctk.CTkFont("Segoe UI", size=26, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=f"v{__version__} · benchmark hardware/OS per VM cliente",
            font=ctk.CTkFont("Segoe UI", size=10),
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            header,
            text="Scegli un preset e avvia l'analisi. Nessun terminale richiesto.",
            font=ctk.CTkFont("Segoe UI", size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        card = ctk.CTkFrame(self, corner_radius=16, fg_color=COLORS["card"])
        card.grid(row=1, column=0, sticky="ew", padx=32, pady=(12, 0))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Preset",
            font=ctk.CTkFont("Segoe UI", size=12, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 4))

        self.preset_menu = ctk.CTkOptionMenu(
            card,
            values=[],
            command=self._on_preset_selected,
            width=260,
            fg_color=COLORS["brand"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent"],
        )
        self.preset_menu.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        buttons_row = ctk.CTkFrame(card, fg_color="transparent")
        buttons_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 18))

        self.start_button = ctk.CTkButton(
            buttons_row,
            text="Avvia analisi",
            command=self._handle_start,
            corner_radius=24,
            height=38,
            fg_color=COLORS["accent"],
            hover_color=COLORS["brand"],
        )
        self.start_button.grid(row=0, column=0, sticky="w")

        self.save_button = ctk.CTkButton(
            buttons_row,
            text="Salva come preset…",
            command=self._handle_save_preset,
            corner_radius=24,
            height=34,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["ink"],
            hover_color=COLORS["border"],
        )
        self.save_button.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.delete_button = ctk.CTkButton(
            buttons_row,
            text="Elimina preset",
            command=self._handle_delete_preset,
            corner_radius=24,
            height=34,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["crit"],
            text_color=COLORS["crit"],
            hover_color=COLORS["border"],
            state="disabled",
        )
        self.delete_button.grid(row=0, column=2, sticky="w", padx=(10, 0))

        self.advanced_toggle = ctk.CTkButton(
            card,
            text="▸ Avanzate",
            command=self._toggle_advanced,
            corner_radius=8,
            height=28,
            width=120,
            fg_color="transparent",
            text_color=COLORS["muted"],
            hover_color=COLORS["border"],
            anchor="w",
        )
        self.advanced_toggle.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 6))

        self.advanced_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.advanced_frame.grid_columnconfigure(0, weight=1)
        self._build_advanced(self.advanced_frame)

        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont("Segoe UI", size=10),
            text_color=COLORS["muted"],
        )
        self.status_label.grid(row=2, column=0, sticky="w", padx=36, pady=(10, 0))

    def _build_advanced(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            parent,
            text="Contesto:",
            font=ctk.CTkFont("Segoe UI", size=11),
            text_color=COLORS["muted"],
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))

        self._profile_var = ctk.StringVar(value=PROFILE_LABELS["generic"])
        self.profile_menu = ctk.CTkOptionMenu(
            parent,
            values=list(PROFILE_LABELS.values()),
            variable=self._profile_var,
            width=200,
            fg_color=COLORS["brand"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent"],
        )
        self.profile_menu.grid(row=1, column=0, sticky="w", padx=20, pady=(2, 8))

        self._quick_var = ctk.BooleanVar(value=False)
        self._production_safe_var = ctk.BooleanVar(value=False)
        self._compare_var = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(
            parent,
            text="Modalità rapida (carico ridotto)",
            variable=self._quick_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["brand"],
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(2, 0))

        ctk.CTkCheckBox(
            parent,
            text="Esecuzione in produzione (carico ridotto)",
            variable=self._production_safe_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["brand"],
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(2, 0))

        ctk.CTkCheckBox(
            parent,
            text="Confronta con esecuzioni precedenti",
            variable=self._compare_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["brand"],
        ).grid(row=4, column=0, sticky="w", padx=20, pady=(2, 16))

    # --- public API (Task 5 interface) ---

    def get_effective_preset(self) -> Preset:
        original = get_preset(self._selected_name) if self._selected_name else None
        builtin = bool(original.builtin) if original is not None else False
        return Preset(
            name=self._selected_name or "Personalizzato",
            profile=PROFILE_VALUES.get(self._profile_var.get(), "generic"),
            quick=self._quick_var.get(),
            production_safe=self._production_safe_var.get(),
            compare=self._compare_var.get(),
            builtin=builtin,
        )

    def refresh_presets(self) -> None:
        self._presets = list_presets()
        names = [preset.name for preset in self._presets]
        self.preset_menu.configure(values=names)

        wanted = self._selected_name or get_last_preset_name()
        if wanted not in names and names:
            wanted = names[0]

        if wanted in names:
            self.preset_menu.set(wanted)
            self._apply_preset(wanted)

    def set_status_message(self, text: str) -> None:
        self.status_label.configure(text=text)

    # --- internal handlers ---

    def _find_preset(self, name: str) -> Optional[Preset]:
        for preset in self._presets:
            if preset.name == name:
                return preset
        return None

    def _apply_preset(self, name: str) -> None:
        preset = self._find_preset(name)
        if preset is None:
            return
        self._selected_name = name
        self._profile_var.set(PROFILE_LABELS.get(preset.profile, "Generico"))
        self._quick_var.set(preset.quick)
        self._production_safe_var.set(preset.production_safe)
        self._compare_var.set(preset.compare)
        self.delete_button.configure(state="disabled" if preset.builtin else "normal")

    def _on_preset_selected(self, name: str) -> None:
        self._apply_preset(name)
        set_last_preset_name(name)

    def _toggle_advanced(self) -> None:
        self._advanced_visible = not self._advanced_visible
        if self._advanced_visible:
            self.advanced_toggle.configure(text="▾ Avanzate")
            self.advanced_frame.grid(row=4, column=0, sticky="ew")
        else:
            self.advanced_toggle.configure(text="▸ Avanzate")
            self.advanced_frame.grid_forget()

    def _handle_start(self) -> None:
        self._on_start(self.get_effective_preset())

    def _handle_save_preset(self) -> None:
        dialog = ctk.CTkInputDialog(
            text="Nome del nuovo preset:",
            title="Salva come preset",
        )
        name = dialog.get_input()
        if not name or not name.strip():
            return
        name = name.strip()

        preset = self.get_effective_preset()
        preset.name = name
        preset.builtin = False
        try:
            save_custom_preset(preset)
        except ValueError as exc:
            self.set_status_message(str(exc))
            return

        set_last_preset_name(name)
        self._selected_name = name
        self.refresh_presets()
        if self._on_presets_changed:
            self._on_presets_changed()
        self.set_status_message(f"Preset «{name}» salvato.")

    def _handle_delete_preset(self) -> None:
        preset = self._find_preset(self._selected_name)
        if preset is None or preset.builtin:
            return
        delete_custom_preset(preset.name)
        self._selected_name = ""
        self.refresh_presets()
        if self._on_presets_changed:
            self._on_presets_changed()
        self.set_status_message(f"Preset «{preset.name}» eliminato.")
