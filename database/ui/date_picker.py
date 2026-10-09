"""
date_picker.py — Widget de selección de fecha para customtkinter.
Muestra un botón con la fecha y abre un calendario popup al hacer clic.
"""
import calendar
import customtkinter as ctk
from datetime import date, datetime

BG          = "#0F1117"
CARD        = "#1A1D27"
CARD_BORDER = "#252836"
ACCENT      = "#3DD68C"
TEXT        = "#FFFFFF"
SUBTEXT     = "#8B8FA8"
INPUT_BG    = "#23263A"
DANGER      = "#EF4444"

MONTHS_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
DAYS_ES = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]


class DatePickerWidget(ctk.CTkFrame):
    """
    Frame que contiene un botón con la fecha seleccionada.
    Al hacer clic abre un calendario popup.
    Expone .get() y .set(value) para integración con el código existente.
    """

    def __init__(self, parent, initial_value="", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._value = ""
        self._popup = None

        # Intentar parsear fecha inicial
        if initial_value:
            try:
                datetime.strptime(initial_value, "%Y-%m-%d")
                self._value = initial_value
            except ValueError:
                pass

        # Botón principal que muestra la fecha
        self._btn = ctk.CTkButton(
            self,
            text=self._display_text(),
            height=42,
            corner_radius=8,
            fg_color=INPUT_BG,
            hover_color="#2E3148",
            border_width=1,
            border_color=CARD_BORDER,
            text_color=TEXT if self._value else SUBTEXT,
            font=("Arial", 13),
            anchor="w",
            command=self._toggle_popup
        )
        self._btn.pack(fill="x")

        # Botón limpiar (×)
        self._clear_btn = ctk.CTkButton(
            self,
            text="×",
            width=32,
            height=32,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#2E1A1A",
            text_color=DANGER,
            font=("Arial", 16),
            command=self.clear
        )
        self._clear_btn.place(relx=1.0, rely=0.5, anchor="e", x=-4)

    def _display_text(self):
        if not self._value:
            return "  📅  Seleccionar fecha de vencimiento"
        try:
            d = datetime.strptime(self._value, "%Y-%m-%d")
            return f"  📅  {d.day:02d} / {MONTHS_ES[d.month]} / {d.year}"
        except Exception:
            return f"  📅  {self._value}"

    def get(self) -> str:
        return self._value

    def set(self, value: str):
        self._value = value
        self._btn.configure(
            text=self._display_text(),
            text_color=TEXT if value else SUBTEXT
        )

    def delete(self, *args):
        """Compatibilidad con la interfaz CTkEntry."""
        self.clear()

    def insert(self, index, value: str):
        """Compatibilidad con la interfaz CTkEntry."""
        self.set(value)

    def clear(self):
        self._value = ""
        self._btn.configure(text=self._display_text(), text_color=SUBTEXT)

    def _toggle_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
        else:
            self._open_popup()

    def _open_popup(self):
        # Determinar año/mes inicial
        if self._value:
            try:
                d = datetime.strptime(self._value, "%Y-%m-%d")
                init_year, init_month, init_day = d.year, d.month, d.day
            except Exception:
                today = date.today()
                init_year, init_month, init_day = today.year, today.month, today.day
        else:
            today = date.today()
            init_year, init_month, init_day = today.year, today.month, today.day

        # Posición popup bajo el botón
        self.update_idletasks()
        x = self._btn.winfo_rootx()
        y = self._btn.winfo_rooty() + self._btn.winfo_height() + 4

        popup = ctk.CTkToplevel()
        popup.overrideredirect(True)   # sin borde de ventana
        popup.configure(fg_color=CARD)
        popup.geometry(f"300x320+{x}+{y}")
        popup.grab_set()
        popup.focus_set()
        self._popup = popup

        # Detectar clic fuera del popup
        def _click_outside(event):
            try:
                wx = popup.winfo_rootx()
                wy = popup.winfo_rooty()
                ww = popup.winfo_width()
                wh = popup.winfo_height()
                mx, my = event.x_root, event.y_root
                if not (wx <= mx <= wx + ww and wy <= my <= wy + wh):
                    popup.destroy()
                    self._popup = None
            except Exception:
                pass

        # Bind en la ventana raíz para detectar clics fuera
        root = self.winfo_toplevel()
        root.bind("<Button-1>", _click_outside, add="+")

        def _cleanup():
            try:
                root.unbind("<Button-1>")
            except Exception:
                pass

        popup.bind("<Destroy>", lambda e: _cleanup())

        # Variables de estado
        self._cal_year  = ctk.IntVar(value=init_year)
        self._cal_month = ctk.IntVar(value=init_month)
        self._cal_day   = init_day

        self._build_calendar(popup)

        # Cerrar al hacer clic fuera del popup
        popup.bind("<FocusOut>", lambda e: self._on_focus_out(e, popup))
        # También cerrar con Escape
        popup.bind("<Escape>", lambda e: popup.destroy())

    def _on_focus_out(self, event, popup):
        """Cierra el popup si el foco sale completamente de él."""
        try:
            # Verificar si el nuevo widget con foco está dentro del popup
            new_focus = popup.focus_get()
            if new_focus is None:
                popup.after(100, lambda: self._delayed_close(popup))
        except Exception:
            pass

    def _delayed_close(self, popup):
        """Verifica después de un breve delay si el popup debe cerrarse."""
        try:
            if not popup.winfo_exists():
                return
            focused = popup.focus_get()
            if focused is None:
                popup.destroy()
                self._popup = None
        except Exception:
            try:
                popup.destroy()
            except Exception:
                pass

    def _build_calendar(self, popup):
        # Limpiar popup
        for w in popup.winfo_children():
            w.destroy()

        year  = self._cal_year.get()
        month = self._cal_month.get()

        # ── Header: mes/año ──
        header = ctk.CTkFrame(popup, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkButton(header, text="◀", width=28, height=28, corner_radius=6,
                      fg_color="#1E2130", hover_color="#1A2E22",
                      text_color=ACCENT, font=("Arial", 13),
                      command=lambda: self._nav(-1, popup)).pack(side="left")

        ctk.CTkLabel(header, text=f"{MONTHS_ES[month]}  {year}",
                     font=("Arial", 13, "bold"), text_color=TEXT).pack(side="left", expand=True)

        ctk.CTkButton(header, text="▶", width=28, height=28, corner_radius=6,
                      fg_color="#1E2130", hover_color="#1A2E22",
                      text_color=ACCENT, font=("Arial", 13),
                      command=lambda: self._nav(1, popup)).pack(side="right")

        # ── Selector rápido de año ──
        year_row = ctk.CTkFrame(popup, fg_color="transparent")
        year_row.pack(fill="x", padx=12, pady=(0, 6))

        years = [str(y) for y in range(date.today().year - 5, date.today().year + 20)]
        year_menu = ctk.CTkOptionMenu(
            year_row,
            values=years,
            fg_color="#1E2130",
            button_color="#2A2D3A",
            button_hover_color="#3A3D52",
            dropdown_fg_color="#1A1D27",
            dropdown_hover_color="#1A2E22",
            text_color=TEXT,
            font=("Arial", 12),
            height=30,
            command=lambda v: self._set_year(int(v), popup)
        )
        year_menu.set(str(year))
        year_menu.pack(fill="x")

        # ── Días de la semana ──
        days_row = ctk.CTkFrame(popup, fg_color="#1E2130", corner_radius=6)
        days_row.pack(fill="x", padx=12, pady=(0, 4))
        for d in DAYS_ES:
            ctk.CTkLabel(days_row, text=d, font=("Arial", 10, "bold"),
                         text_color=SUBTEXT, width=34).pack(side="left", expand=True)

        # ── Días del mes ──
        cal_frame = ctk.CTkFrame(popup, fg_color="transparent")
        cal_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        cal = calendar.monthcalendar(year, month)
        today = date.today()

        for week in cal:
            week_row = ctk.CTkFrame(cal_frame, fg_color="transparent")
            week_row.pack(fill="x")
            for day in week:
                if day == 0:
                    ctk.CTkLabel(week_row, text="", width=34, height=34).pack(side="left", expand=True)
                else:
                    is_today    = (day == today.day and month == today.month and year == today.year)
                    is_selected = (day == self._cal_day and month == self._cal_month.get()
                                   and year == self._cal_year.get())

                    fg = ACCENT   if is_selected else ("#1A2E22" if is_today else "#1E2130")
                    tc = "#0F1117" if is_selected else (ACCENT if is_today else TEXT)

                    ctk.CTkButton(
                        week_row, text=str(day), width=34, height=34,
                        corner_radius=6, fg_color=fg, hover_color="#1A2E22",
                        text_color=tc, font=("Arial", 11),
                        command=lambda d=day: self._select_day(d, popup)
                    ).pack(side="left", expand=True, padx=1, pady=1)

    def _nav(self, direction: int, popup):
        month = self._cal_month.get() + direction
        year  = self._cal_year.get()
        if month > 12:
            month = 1; year += 1
        elif month < 1:
            month = 12; year -= 1
        self._cal_month.set(month)
        self._cal_year.set(year)
        self._build_calendar(popup)

    def _set_year(self, year: int, popup):
        self._cal_year.set(year)
        self._build_calendar(popup)

    def _select_day(self, day: int, popup):
        self._cal_day = day
        year  = self._cal_year.get()
        month = self._cal_month.get()
        self.set(f"{year:04d}-{month:02d}-{day:02d}")
        popup.destroy()
        self._popup = None