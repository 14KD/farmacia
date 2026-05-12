import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
import config

BG           = "#0F1117"
CARD         = "#1A1D27"
CARD_BORDER  = "#252836"
ACCENT       = "#3DD68C"
CYAN         = "#22D3EE"
TEXT         = "#FFFFFF"
SUBTEXT      = "#8B8FA8"
WARNING      = "#FFA94D"
INPUT_BG     = "#23263A"
INPUT_BORDER = "#2E3148"


class SettingsUI:

    def __init__(self, parent):
        self.parent = parent
        self.cfg    = config.load()

        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── Encabezado ──
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="⚙  Ajustes del Sistema",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ScrollFrame para todo el contenido
        scroll = ctk.CTkScrollableFrame(container, fg_color=BG, corner_radius=0,
                                         scrollbar_button_color="#252836",
                                         scrollbar_button_hover_color="#3A3D52")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ══════════════════════════════════════
        # 1. INFORMACIÓN DE LA FARMACIA
        # ══════════════════════════════════════
        self._section(scroll, "🏥  Información de la Farmacia")

        ph = self.cfg["pharmacy"]
        grid1 = self._grid(scroll)
        self.ph_name    = self._entry(grid1, "Nombre de la Farmacia", ph["name"],        0, 0, colspan=2)
        self.ph_phone   = self._entry(grid1, "Teléfono",              ph["phone"],       1, 0)
        self.ph_rnc     = self._entry(grid1, "RNC / RUC",             ph["rnc"],         1, 1)
        self.ph_address = self._entry(grid1, "Dirección",             ph["address"],     2, 0, colspan=2)

        # Logo
        logo_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=10,
                                  border_width=1, border_color=CARD_BORDER)
        logo_card.pack(fill="x", padx=20, pady=(0, 16))
        logo_row = ctk.CTkFrame(logo_card, fg_color="transparent")
        logo_row.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(logo_row, text="Logo de la farmacia (PNG/JPG):",
                     font=("Arial", 12), text_color=SUBTEXT).pack(side="left")

        self.logo_lbl = ctk.CTkLabel(logo_row,
                                      text=ph["logo_path"] or "Sin logo seleccionado",
                                      font=("Arial", 11), text_color=SUBTEXT if not ph["logo_path"] else ACCENT)
        self.logo_lbl.pack(side="left", padx=(12, 0), expand=True, fill="x")

        ctk.CTkButton(logo_row, text="📁  Seleccionar", height=34, width=130,
                      corner_radius=8, fg_color="#1A3A2A", hover_color="#2EBF7A",
                      text_color=ACCENT, font=("Arial", 12),
                      command=self._pick_logo).pack(side="right")

        ctk.CTkButton(logo_row, text="✖", height=34, width=36,
                      corner_radius=8, fg_color="#2E1A1A", hover_color="#DC2626",
                      text_color="#EF4444", font=("Arial", 12),
                      command=self._clear_logo).pack(side="right", padx=(0, 6))

        # ══════════════════════════════════════
        # 2. FACTURACIÓN
        # ══════════════════════════════════════
        self._section(scroll, "🖨  Facturación")

        bl = self.cfg["billing"]
        grid2 = self._grid(scroll)
        self.bl_footer   = self._entry(grid2, "Mensaje pie de factura", bl["footer"],   0, 0, colspan=2)
        self.bl_currency = self._entry(grid2, "Moneda (ej. RD$, $, €)", bl["currency"], 1, 0)
        self.bl_tax      = self._entry(grid2, "Impuesto ITBIS %",        str(bl["tax_rate"]), 1, 1)

        # ══════════════════════════════════════
        # 3. INVENTARIO
        # ══════════════════════════════════════
        self._section(scroll, "📦  Inventario")

        inv = self.cfg["inventory"]
        grid3 = self._grid(scroll)
        self.inv_threshold = self._entry(grid3, "Umbral de stock bajo (unidades)",
                                          str(inv["low_stock_threshold"]), 0, 0)
        self.inv_expiry    = self._entry(grid3, "Alertar si vence en menos de (días)",
                                          str(inv["expiry_alert_days"]),   0, 1)

        # ══════════════════════════════════════
        # 4. NOTIFICACIONES
        # ══════════════════════════════════════
        self._section(scroll, "🔔  Notificaciones al Iniciar")

        notif = self.cfg["notifications"]
        notif_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=10,
                                   border_width=1, border_color=CARD_BORDER)
        notif_card.pack(fill="x", padx=20, pady=(0, 16))
        notif_inner = ctk.CTkFrame(notif_card, fg_color="transparent")
        notif_inner.pack(fill="x", padx=16, pady=14)

        self.notif_stock_var  = ctk.BooleanVar(value=notif["alert_low_stock"])
        self.notif_expiry_var = ctk.BooleanVar(value=notif["alert_expiry"])

        ctk.CTkCheckBox(notif_inner,
                        text="Mostrar alerta de productos con stock crítico al iniciar",
                        variable=self.notif_stock_var,
                        font=("Arial", 13), text_color=TEXT,
                        fg_color=ACCENT, hover_color="#2EBF7A",
                        checkmark_color="#0F1117").pack(anchor="w", pady=(0, 10))

        ctk.CTkCheckBox(notif_inner,
                        text="Mostrar alerta de productos próximos a vencer al iniciar",
                        variable=self.notif_expiry_var,
                        font=("Arial", 13), text_color=TEXT,
                        fg_color=ACCENT, hover_color="#2EBF7A",
                        checkmark_color="#0F1117").pack(anchor="w")

        # ══════════════════════════════════════
        # 5. APARIENCIA
        # ══════════════════════════════════════
        self._section(scroll, "🎨  Apariencia")

        theme_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=10,
                                   border_width=1, border_color=CARD_BORDER)
        theme_card.pack(fill="x", padx=20, pady=(0, 16))
        theme_row = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(theme_row, text="Tema:", font=("Arial", 13), text_color=TEXT).pack(side="left")

        ctk.CTkButton(theme_row, text="🌙  Oscuro", height=36, width=120,
                      corner_radius=8, fg_color="#1A1D27", hover_color="#252836",
                      text_color=CYAN, font=("Arial", 12),
                      command=lambda: ctk.set_appearance_mode("dark")).pack(side="left", padx=(16, 8))

        ctk.CTkButton(theme_row, text="☀  Claro", height=36, width=120,
                      corner_radius=8, fg_color="#E8EAF0", hover_color="#D0D3DC",
                      text_color="#1A1D27", font=("Arial", 12),
                      command=lambda: ctk.set_appearance_mode("light")).pack(side="left")

        # ── Botón Guardar ──
        ctk.CTkFrame(scroll, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(8, 16))

        save_row = ctk.CTkFrame(scroll, fg_color="transparent")
        save_row.pack(fill="x", padx=20, pady=(0, 24))

        ctk.CTkButton(save_row, text="💾  Guardar Cambios",
                      height=48, corner_radius=10,
                      fg_color=ACCENT, hover_color="#2EBF7A",
                      text_color="#0F1117", font=("Arial", 14, "bold"),
                      command=self.save_settings).pack(side="right")

        ctk.CTkButton(save_row, text="↺  Restablecer Defaults",
                      height=48, corner_radius=10,
                      fg_color=INPUT_BG, hover_color="#2E3148",
                      text_color=SUBTEXT, font=("Arial", 13),
                      command=self.reset_defaults).pack(side="right", padx=(0, 10))

    # ─── Helpers de UI ─────────────────────────

    def _section(self, parent, title):
        ctk.CTkLabel(parent, text=title,
                     font=("Arial", 13, "bold"), text_color=SUBTEXT).pack(anchor="w", padx=20, pady=(8, 6))

    def _grid(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                             border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=20, pady=(0, 16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        inner.columnconfigure((0, 1), weight=1)
        return inner

    def _entry(self, parent, label, value, row, col, colspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=colspan,
                   padx=(0, 10 if col == 0 and colspan == 1 else 0),
                   pady=(0, 10), sticky="ew")
        ctk.CTkLabel(frame, text=label, font=("Arial", 11), text_color=SUBTEXT).pack(anchor="w")
        ef = ctk.CTkFrame(frame, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        ef.pack(fill="x", pady=(4, 0))
        entry = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                              height=40, font=("Arial", 13), text_color=TEXT)
        entry.insert(0, value)
        entry.pack(fill="x", padx=8)
        return entry

    # ─── Logo ──────────────────────────────────

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if path:
            self.cfg["pharmacy"]["logo_path"] = path
            name = os.path.basename(path)
            self.logo_lbl.configure(text=name, text_color=ACCENT)

    def _clear_logo(self):
        self.cfg["pharmacy"]["logo_path"] = ""
        self.logo_lbl.configure(text="Sin logo seleccionado", text_color=SUBTEXT)

    # ─── Guardar ───────────────────────────────

    def save_settings(self):
        try:
            tax = float(self.bl_tax.get().strip() or 0)
            threshold = int(self.inv_threshold.get().strip() or 10)
            expiry_days = int(self.inv_expiry.get().strip() or 30)
            if not (0 <= tax <= 100): raise ValueError("ITBIS debe estar entre 0 y 100")
            if threshold < 0: raise ValueError("El umbral no puede ser negativo")
            if expiry_days < 0: raise ValueError("Los días no pueden ser negativos")
        except ValueError as e:
            messagebox.showerror("Error de validación", str(e)); return

        self.cfg["pharmacy"]["name"]      = self.ph_name.get().strip()
        self.cfg["pharmacy"]["phone"]     = self.ph_phone.get().strip()
        self.cfg["pharmacy"]["rnc"]       = self.ph_rnc.get().strip()
        self.cfg["pharmacy"]["address"]   = self.ph_address.get().strip()

        self.cfg["billing"]["footer"]     = self.bl_footer.get().strip()
        self.cfg["billing"]["currency"]   = self.bl_currency.get().strip()
        self.cfg["billing"]["tax_rate"]   = tax

        self.cfg["inventory"]["low_stock_threshold"] = threshold
        self.cfg["inventory"]["expiry_alert_days"]   = expiry_days

        self.cfg["notifications"]["alert_low_stock"] = self.notif_stock_var.get()
        self.cfg["notifications"]["alert_expiry"]    = self.notif_expiry_var.get()

        if config.save(self.cfg):
            messagebox.showinfo("Guardado", "✔  Configuración guardada correctamente.\n\nAlgunos cambios se aplicarán en el próximo inicio.")
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración.")

    def reset_defaults(self):
        if not messagebox.askyesno("Confirmar", "¿Restablecer todos los ajustes a los valores por defecto?"): return
        config.save(config.DEFAULTS)
        messagebox.showinfo("Restablecido", "Ajustes restablecidos. Recarga la pantalla para ver los cambios.")