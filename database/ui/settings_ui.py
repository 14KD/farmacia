import os
import customtkinter as ctk
import re as _re

# Prefijos válidos de República Dominicana
_RD_PREFIXES = ("809", "829", "849")

def _validate_rd_phone(phone: str) -> tuple:
    """
    Valida número de teléfono de República Dominicana.
    Formatos aceptados:
        809-123-4567  |  8091234567  |  +1-809-123-4567
        (809) 123-4567  |  1-809-123-4567
    Retorna (True, numero_limpio) o (False, mensaje_error)
    """
    # Quitar espacios, guiones, paréntesis, el prefijo internacional +1 o 1
    digits = _re.sub(r"[\s\-().+]", "", phone)
    if digits.startswith("1"):
        digits = digits[1:]   # quitar código de país

    if not digits:
        return False, "El teléfono es obligatorio."

    if not digits.isdigit():
        return False, "El teléfono solo debe contener números."

    if len(digits) != 10:
        return False, (
            f"El teléfono debe tener 10 dígitos (tienes {len(digits)}).\n"
            "Ejemplo: 809-123-4567"
        )

    prefix = digits[:3]
    if prefix not in _RD_PREFIXES:
        return False, (
            f"El prefijo '{prefix}' no es válido para República Dominicana.\n"
            "Los prefijos permitidos son: 809, 829, 849."
        )

    # Formatear como 809-123-4567
    formatted = f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return True, formatted
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

CURRENCIES = [
    "RD$  — Peso Dominicano",
    "$    — Dólar Estadounidense",
    "€    — Euro",
    "£    — Libra Esterlina",
    "¥    — Yen Japonés",
    "MXN  — Peso Mexicano",
    "COP  — Peso Colombiano",
    "ARS  — Peso Argentino",
    "CLP  — Peso Chileno",
    "PEN  — Sol Peruano",
    "BRL  — Real Brasileño",
    "GTQ  — Quetzal Guatemalteco",
    "HNL  — Lempira Hondureño",
    "NIO  — Córdoba Nicaragüense",
    "CRC  — Colón Costarricense",
    "PAB  — Balboa Panameño",
    "VES  — Bolívar Venezolano",
    "BOB  — Boliviano",
    "PYG  — Guaraní Paraguayo",
    "UYU  — Peso Uruguayo",
]

# Símbolo real que se guarda (solo el símbolo antes del guion)
def _currency_symbol(full: str) -> str:
    return full.split("—")[0].strip()

def _find_currency_option(symbol: str) -> str:
    for c in CURRENCIES:
        if c.startswith(symbol):
            return c
    return CURRENCIES[0]


class SettingsUI:

    def __init__(self, parent):
        self.parent = parent
        self.cfg    = config.load()

        # Frame principal sin scroll propio (el dashboard ya tiene scroll)
        container = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Encabezado ──────────────────────────
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="⚙  Ajustes del Sistema",
                     font=("Arial", 22, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(10, 16))

        # ══════════════════════════════════════
        # 1. INFORMACIÓN DE LA FARMACIA
        # ══════════════════════════════════════
        self._section_label(container, "🏥  Información de la Farmacia")

        ph    = self.cfg["pharmacy"]
        card1 = self._card(container)

        r0 = self._row(card1)
        r0.columnconfigure(0, weight=1)
        self.ph_name = self._lbl_entry(r0, "Nombre de la Farmacia", ph["name"], 0, 0, span=1)

        r1 = self._row(card1)
        r1.columnconfigure((0, 1), weight=1)
        self.ph_phone   = self._lbl_entry(r1, "Teléfono",  ph["phone"], 0, 0)
        self.ph_phone.bind("<FocusOut>", self._on_phone_focusout)
        self.ph_rnc     = self._lbl_entry(r1, "RNC", ph["rnc"],   0, 1)

        r2 = self._row(card1)
        r2.columnconfigure(0, weight=1)
        self.ph_address = self._lbl_entry(r2, "Dirección", ph["address"], 0, 0, span=1)

        # Logo
        logo_row = ctk.CTkFrame(card1, fg_color="transparent")
        logo_row.pack(fill="x", padx=14, pady=(4, 14))
        ctk.CTkLabel(logo_row, text="Logo (PNG/JPG):",
                     font=("Arial", 11), text_color=SUBTEXT).pack(side="left")
        self.logo_lbl = ctk.CTkLabel(logo_row,
                                      text=os.path.basename(ph["logo_path"]) if ph["logo_path"] else "Sin logo",
                                      font=("Arial", 11),
                                      text_color=ACCENT if ph["logo_path"] else SUBTEXT)
        self.logo_lbl.pack(side="left", padx=(10, 0), expand=True, fill="x")
        ctk.CTkButton(logo_row, text="✖", width=32, height=30, corner_radius=6,
                      fg_color="#2E1A1A", hover_color="#DC2626", text_color="#EF4444",
                      command=self._clear_logo).pack(side="right", padx=(4, 0))
        ctk.CTkButton(logo_row, text="📁 Seleccionar", width=130, height=30, corner_radius=6,
                      fg_color="#1A3A2A", hover_color="#2EBF7A", text_color=ACCENT,
                      font=("Arial", 11), command=self._pick_logo).pack(side="right")

        # ══════════════════════════════════════
        # 2. FACTURACIÓN
        # ══════════════════════════════════════
        self._section_label(container, "🖨  Facturación")

        bl    = self.cfg["billing"]
        card2 = self._card(container)

        r3 = self._row(card2)
        r3.columnconfigure(0, weight=1)
        self.bl_footer = self._lbl_entry(r3, "Mensaje pie de factura", bl["footer"], 0, 0, span=1)

        r4 = self._row(card2)
        r4.columnconfigure((0, 1), weight=1)

        # Moneda con dropdown
        cur_frame = ctk.CTkFrame(r4, fg_color="transparent")
        cur_frame.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(cur_frame, text="Moneda", font=("Arial", 11), text_color=SUBTEXT).pack(anchor="w")
        self.currency_var = ctk.StringVar(value=_find_currency_option(bl["currency"]))
        ctk.CTkOptionMenu(
            cur_frame,
            values=CURRENCIES,
            variable=self.currency_var,
            width=280, height=40,
            fg_color=INPUT_BG,
            button_color="#2A2D3A",
            button_hover_color="#3A3D52",
            dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22",
            dropdown_text_color=TEXT,
            text_color=TEXT,
            font=("Arial", 12),
            dynamic_resizing=False
        ).pack(fill="x", pady=(4, 0))

        self.bl_tax = self._lbl_entry(r4, "Impuesto ITBIS %", str(bl["tax_rate"]), 0, 1)

        # ══════════════════════════════════════
        # 3. INVENTARIO
        # ══════════════════════════════════════
        self._section_label(container, "📦  Inventario")

        inv   = self.cfg["inventory"]
        card3 = self._card(container)
        r5    = self._row(card3)
        r5.columnconfigure((0, 1), weight=1)
        self.inv_threshold = self._lbl_entry(r5, "Umbral de stock bajo (unidades)",
                                              str(inv["low_stock_threshold"]), 0, 0)
        self.inv_expiry    = self._lbl_entry(r5, "Alertar si vence en menos de (días)",
                                              str(inv["expiry_alert_days"]),   0, 1)

        # ══════════════════════════════════════
        # 4. NOTIFICACIONES
        # ══════════════════════════════════════
        self._section_label(container, "🔔  Notificaciones al Iniciar")

        notif = self.cfg["notifications"]
        card4 = self._card(container)
        n_row = ctk.CTkFrame(card4, fg_color="transparent")
        n_row.pack(fill="x", padx=14, pady=14)

        self.notif_stock_var  = ctk.BooleanVar(value=notif["alert_low_stock"])
        self.notif_expiry_var = ctk.BooleanVar(value=notif["alert_expiry"])

        ctk.CTkCheckBox(n_row, text="Mostrar alerta de productos con stock crítico al iniciar",
                        variable=self.notif_stock_var, font=("Arial", 13), text_color=TEXT,
                        fg_color=ACCENT, hover_color="#2EBF7A",
                        checkmark_color="#0F1117").pack(anchor="w", pady=(0, 12))
        ctk.CTkCheckBox(n_row, text="Mostrar alerta de productos próximos a vencer al iniciar",
                        variable=self.notif_expiry_var, font=("Arial", 13), text_color=TEXT,
                        fg_color=ACCENT, hover_color="#2EBF7A",
                        checkmark_color="#0F1117").pack(anchor="w")

        # ══════════════════════════════════════
        # 5. APARIENCIA
        # ══════════════════════════════════════
        self._section_label(container, "🎨  Apariencia")

        card5  = self._card(container)
        th_row = ctk.CTkFrame(card5, fg_color="transparent")
        th_row.pack(fill="x", padx=14, pady=14)
        ctk.CTkLabel(th_row, text="Tema:", font=("Arial", 13), text_color=TEXT).pack(side="left")

        ctk.CTkButton(th_row, text="🌙  Oscuro", height=38, width=130,
                      corner_radius=8, fg_color="#1E2130", hover_color="#252836",
                      text_color=CYAN, font=("Arial", 12, "bold"),
                      command=self._set_dark).pack(side="left", padx=(16, 8))

        ctk.CTkButton(th_row, text="☀  Claro", height=38, width=130,
                      corner_radius=8, fg_color="#E8EAF0", hover_color="#D0D3DC",
                      text_color="#1A1D27", font=("Arial", 12, "bold"),
                      command=self._set_light).pack(side="left")

        # ── Botones guardar ──────────────────
        ctk.CTkFrame(container, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=20, pady=(16, 12))
        save_row = ctk.CTkFrame(container, fg_color="transparent")
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

    # ══════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════

    def _section_label(self, parent, text):
        ctk.CTkLabel(parent, text=text,
                     font=("Arial", 13, "bold"), text_color=SUBTEXT).pack(
            anchor="w", padx=20, pady=(12, 6))

    def _card(self, parent):
        f = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=CARD_BORDER)
        f.pack(fill="x", padx=20, pady=(0, 14))
        return f

    def _row(self, parent):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=14, pady=(10, 0))
        return r

    def _lbl_entry(self, parent, label, value, row, col, span=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        if span:
            frame.grid(row=row, column=col, columnspan=span,
                       padx=(0, 0), pady=(0, 10), sticky="ew")
        else:
            frame.grid(row=row, column=col,
                       padx=(0, 10) if col == 0 else (0, 0),
                       pady=(0, 10), sticky="ew")
        ctk.CTkLabel(frame, text=label, font=("Arial", 11),
                     text_color=SUBTEXT).pack(anchor="w")
        ef = ctk.CTkFrame(frame, fg_color=INPUT_BG, corner_radius=8,
                           border_width=1, border_color=INPUT_BORDER)
        ef.pack(fill="x", pady=(4, 0))
        e = ctk.CTkEntry(ef, border_width=0, fg_color="transparent",
                         height=40, font=("Arial", 13), text_color=TEXT)
        e.insert(0, value)
        e.pack(fill="x", padx=8)
        return e

    # ══════════════════════════════════════════
    # LOGO
    # ══════════════════════════════════════════

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp")]
        )
        if path:
            self.cfg["pharmacy"]["logo_path"] = path
            self.logo_lbl.configure(text=os.path.basename(path), text_color=ACCENT)

    def _clear_logo(self):
        self.cfg["pharmacy"]["logo_path"] = ""
        self.logo_lbl.configure(text="Sin logo", text_color=SUBTEXT)

    # ══════════════════════════════════════════
    # APARIENCIA
    # ══════════════════════════════════════════

    def _set_dark(self):
        ctk.set_appearance_mode("dark")
        # Refrescar colores del frame principal
        self._refresh_colors(dark=True)

    def _set_light(self):
        ctk.set_appearance_mode("light")
        self._refresh_colors(dark=False)

    def _refresh_colors(self, dark: bool):
        """Fuerza el refresco visual de la ventana raíz."""
        try:
            root = self.parent.winfo_toplevel()
            root.update_idletasks()
        except Exception:
            pass

    # ══════════════════════════════════════════
    # GUARDAR
    # ══════════════════════════════════════════

    def _on_phone_focusout(self, event=None):
        """Valida el teléfono al salir del campo y muestra ayuda visual."""
        phone_raw = self.ph_phone.get().strip()
        if not phone_raw:
            return
        ok, result = _validate_rd_phone(phone_raw)
        if ok:
            # Auto-formatear
            self.ph_phone.delete(0, "end")
            self.ph_phone.insert(0, result)
            self.ph_phone.configure(border_color="#3DD68C")   # verde = OK
        else:
            self.ph_phone.configure(border_color="#EF4444")   # rojo = error

    def save_settings(self):
        try:
            tax       = float(self.bl_tax.get().strip() or 0)
            threshold = int(self.inv_threshold.get().strip() or 10)
            exp_days  = int(self.inv_expiry.get().strip() or 30)
            if not (0 <= tax <= 100):    raise ValueError("ITBIS debe estar entre 0 y 100.")
            if threshold < 0:            raise ValueError("El umbral no puede ser negativo.")
            if exp_days  < 0:            raise ValueError("Los días no pueden ser negativos.")
        except ValueError as e:
            messagebox.showerror("Error de validación", str(e)); return

        # Validar teléfono RD
        phone_raw = self.ph_phone.get().strip()
        if phone_raw:
            ok, phone_result = _validate_rd_phone(phone_raw)
            if not ok:
                messagebox.showerror("Teléfono inválido", phone_result)
                return
            # Auto-formatear el número
            self.ph_phone.delete(0, "end")
            self.ph_phone.insert(0, phone_result)
        else:
            phone_result = ""

        self.cfg["pharmacy"].update({
            "name":    self.ph_name.get().strip(),
            "phone":   phone_result,
            "rnc":     self.ph_rnc.get().strip(),
            "address": self.ph_address.get().strip(),
        })
        self.cfg["billing"].update({
            "footer":   self.bl_footer.get().strip(),
            "currency": _currency_symbol(self.currency_var.get()),
            "tax_rate": tax,
        })
        self.cfg["inventory"].update({
            "low_stock_threshold": threshold,
            "expiry_alert_days":   exp_days,
        })
        self.cfg["notifications"].update({
            "alert_low_stock": self.notif_stock_var.get(),
            "alert_expiry":    self.notif_expiry_var.get(),
        })

        if config.save(self.cfg):
            messagebox.showinfo("Guardado",
                                "✔  Configuración guardada correctamente.\n"
                                "Algunos cambios se aplican al reiniciar.")
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración.")

    def reset_defaults(self):
        if not messagebox.askyesno("Confirmar",
                                    "¿Restablecer todos los ajustes a los valores por defecto?"): return
        config.save(config.DEFAULTS)
        messagebox.showinfo("Restablecido",
                            "Ajustes restablecidos.\nRecarga la pantalla para ver los cambios.")